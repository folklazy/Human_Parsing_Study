"""Approved full C4-P batch: one Sapiens GPU worker, one saved-only CPU worker.

No implicit resume, retry, other Sapiens sizes, CPI, or detector inference.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,fcntl,json,os,sys,time,subprocess,shutil,traceback,csv,re
import numpy as np
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'));sys.path.insert(0,str(P/'scripts'))
from common_view.core import sha_file,load_spec,semantic_metrics,array_hash
from common_view.full import Accumulator,score_people,project_confusion,native_confusion
from common_view.packets import atomic_json,read_packet,write_packet,fingerprint
from common_view.detector_cache import normalize_detector_masks
from cihp_benchmark.data import read_image


def utc():return datetime.now(timezone.utc).isoformat()
def emit(stream,row):
    stream.write(json.dumps(row,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
def rawroot(c):return W/c['artifact_root']
def stage_root(c,mid):return rawroot(c)/'models'/mid


def check_bindings(c,cp):
    if sha_file(cp)!=c['_config_sha256']:raise RuntimeError('Frozen full config drift')
    if sha_file(W/c['protocol'])!=c['protocol_sha256']:raise RuntimeError('Protocol drift')
    for f,h in {**c['pilot_scientific_source_hashes'],**c['source_hashes'],**c['native_preserved']}.items():
        if sha_file(W/f)!=h:raise RuntimeError('Source/config binding drift: '+f)


def guard(c,root,start,prior=0):
    if time.monotonic()-start+prior>c['max_hours']*3600:raise RuntimeError('RESOURCE_TIME_STOP')
    if shutil.disk_usage(root).free<(c['minimum_free_gib']+.1)*2**30:raise RuntimeError('RESOURCE_FREE_SPACE_STOP')
    # Model-specific trees are independent; preexisting datasets/weights/GT/native results referenced, not copied.
    retained=sum(f.stat().st_size for f in root.rglob('*') if f.is_file())
    if retained>c['max_stream_gib']*2**30:raise RuntimeError('RESOURCE_STREAM_STORAGE_STOP')


def load_gt(c,iid,bindings):
    b=bindings[iid];base=W/'datasets/CIHP/Validation'
    category,cm=read_image(base/'Category_ids'/(iid+'.png'),True)
    human,hm=read_image(base/'Human_ids'/(iid+'.png'),True)
    if cm['file_sha256']!=b['GT_sha256']['Category_ids'] or hm['file_sha256']!=b['GT_sha256']['Human_ids']:
        raise RuntimeError('Shared GT source binding drift '+iid)
    derived=W/c['GT_binding_root']/(iid+'.npz')
    if sha_file(derived)!=b['derived_sha256']:raise RuntimeError('Shared GT derived binding drift '+iid)
    return category,human


def read_inputs(c):
    bindings={r['image_id']:r for r in map(json.loads,(W/c['GT_binding_root']/'BINDINGS.jsonl').open())}
    if sha_file(W/c['GT_binding_root']/'BINDINGS.jsonl')!=c['GT_manifest_sha256']:raise RuntimeError('GT manifest drift')
    return bindings,load_spec(W/c['protocol'])


def init_state(c,mid):
    root=stage_root(c,mid);root.mkdir(parents=True,exist_ok=False)
    state=dict(run_id=c['run_id'],model_id=mid,status='INITIALIZING',pid=os.getpid(),process_group=os.getpgrp(),
               start_utc=utc(),expected=5000,complete=0,failed=0,invalid=0,reused=0,new_VAL_calls=0,
               model_frame_calls=0,setup_failed=0,resource_policy='SHARED_GPU_QUALITY_ONLY' if mid=='Sapiens2_0.4b' else 'SAVED_ARTIFACTS_CPU_ONLY',
               config_sha256=c['_config_sha256'],protocol_sha256=c['protocol_sha256'],primary=None,queue_stopped=False)
    atomic_json(root/'RUN.json',state);return root,state


def finish(c,root,state,acc,global_native=None):
    report=acc.report(project_confusion(global_native,'CIHP_GT_AND_NATIVE_PRED',load_spec(W/c['protocol'])) if global_native is not None else None,global_native)
    if report['status']=='COMPLETE' and state['failed']==state['invalid']==0:
        assert report['primary']['GT_support']==c['GT_summary']['global_support'],'Global GT denominator drift'
        for values in report['person_metrics'].values():
            assert values['G_loc']==c['GT_summary']['G_loc'] and values['G_sem_C4']==c['GT_summary']['G_sem_C4'],'GT person denominator drift'
    state.update(status=report['status'] if state['failed']==state['invalid']==0 else 'INCOMPLETE',
                 complete=len(acc.ids),missing=len(acc.expected-acc.ids),duplicate=0,end_utc=utc(),queue_stopped=True)
    if state['status']!='COMPLETE':report.update(status='INCOMPLETE',primary=None,person_metrics=None)
    report.update(run_id=c['run_id'],model_id=state['model_id'],config_sha256=c['_config_sha256'],protocol_sha256=c['protocol_sha256'],
                  resource_policy=state['resource_policy'],source_route=c['route'] if state['model_id']=='Sapiens2_0.4b' else c['legacy'][state['model_id']]['source_route'],
                  source_scientific_revision='UNCHANGED_REVISION2',reused=state['reused'],new_VAL_calls=state['new_VAL_calls'],
                  failed=state['failed'],invalid=state['invalid'],end_utc=state['end_utc'])
    atomic_json(root/'METRICS.json',report);atomic_json(root/'RUN.json',state)
    record=W/c['record_root']/state['model_id'];atomic_json(record/'COMPLETION.json',state);atomic_json(record/'METRICS.json',report)
    return report


def cpu_worker(c,cp):
    os.environ.setdefault('OMP_NUM_THREADS','2');os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
    bindings,spec=read_inputs(c)
    population={r['id']:r for r in json.loads((W/c['native_population']).read_text())['members']}
    detector={r['image_id']:r for r in map(json.loads,(W/c['YOLO']['validation_ledger']).open())}
    for mid,s in c['legacy'].items():
        root,state=init_state(c,mid);acc=Accumulator(c['expected_ids']);started=time.monotonic();iid=None
        ledger=(root/'SCORING.jsonl').open('x',buffering=1)
        try:
            check_bindings(c,cp)
            assert sha_file(W/s['input_manifest'])==s['input_manifest_sha256']
            assert sha_file(W/s['confusion'])==s['confusion_sha256']
            sourcehist=np.load(W/s['confusion'],allow_pickle=False)
            entries={r['image_id']:r for r in map(json.loads,(W/s['input_manifest']).open())}
            assert set(entries)==set(c['expected_ids'])
            for index,iid in enumerate(c['expected_ids']):
                if index%25==0:guard(c,root,started);check_bindings(c,cp)
                e=entries[iid];packet=W/e['packet'];emit(ledger,dict(image_id=iid,status='STARTED',start_utc=utc(),attempt=1))
                if sha_file(packet/'packet.json')!=e['metadata_sha256']:raise RuntimeError('Source metadata drift '+iid)
                meta,a=read_packet(packet,dict(model_id=mid,image_id=iid,config_sha256=s['native_config_sha256'],
                    checkpoint_sha256=s['source_model']['checkpoint_sha256'],source_commit=s['source_model']['source_commit'],
                    precision='FP32',label_space='CIHP_NATIVE_20',input_sha256=population[iid]['RGB_sha256'],
                    detector_artifact_sha256=detector[iid]['artifact_sha256']),legacy=True)
                assert meta['packet_sha256']==e['packet_sha256']
                category,human=load_gt(c,iid,bindings)
                sc=score_people(category,human,a['person_semantic_masks'],a['person_extents'],a['person_scores'],'CIHP_GT_AND_NATIVE_PRED',spec,bindings[iid])
                row=dict(image_id=iid,scores=sc,source_packet=e,config_sha256=c['_config_sha256'],protocol_sha256=c['protocol_sha256'])
                path=root/'scores'/(iid+'.json');assert not path.exists();atomic_json(path,row)
                acc.add(iid,sc)
                state.update(status='SCORING',complete=len(acc.ids),current_image=iid)
                emit(ledger,dict(image_id=iid,status='COMPLETE',source_packet=e['packet'],source_packet_sha256=e['packet_sha256'],
                    metadata_sha256=e['metadata_sha256'],score_file=str(path.relative_to(W)),score_sha256=sha_file(path),end_utc=utc()))
                atomic_json(root/'RUN.json',state)
            report=finish(c,root,state,acc,sourcehist)
        except Exception:
            resource=sys.exc_info()[1] is not None and str(sys.exc_info()[1]).startswith('RESOURCE_')
            state.update(status='INCOMPLETE',invalid=0 if resource else 1,resource_stop=resource,error=traceback.format_exc(),failed_image=iid)
            emit(ledger,dict(image_id=iid,status='NOT_ATTEMPTED_RESOURCE_STOP' if resource else 'INVALID',error=state['error'],end_utc=utc()))
            report=finish(c,root,state,acc)
        finally:ledger.close()
        print('CPU terminal',mid,state['status'],state['complete'],flush=True)
        # Each model completion is a meaningful publishable work unit; no score tuning.
        update_report(c,publish=True)


def gpu_worker(c,cp):
    mid='Sapiens2_0.4b';root,state=init_state(c,mid);acc=Accumulator(c['expected_ids']);started=time.monotonic()
    ledger=(root/'EXECUTION.jsonl').open('x',buffering=1);stage='GATE';iid=None;warmup=False
    bindings,spec=read_inputs(c)
    try:
        check_bindings(c,cp)
        from safetensors.torch import load_file
        from sapiens.dense.models import init_model
        import torch
        from common_view.sapiens_route import prepare_rgb,logits_to_native,ownership_planes
        ck=W/c['model']['checkpoint'];assert dict(size=ck.stat().st_size,mtime_ns=ck.stat().st_mtime_ns)==c['checkpoint_stat']
        assert os.environ.get('CUDA_VISIBLE_DEVICES')==c['CUDA_VISIBLE_DEVICES']
        assert os.environ.get('PYTORCH_CUDA_ALLOC_CONF')==c['allocator_environment_preserved']
        detector={r['image_id']:r for r in map(json.loads,(W/c['YOLO']['validation_ledger']).open())}
        pop={r['id']:r for r in json.loads((W/c['native_population']).read_text())['members']}
        stage='REUSE'
        for reused in c['reused']:
            iid=reused['image_id'];meta,a=read_packet(W/reused['packet'],dict(model_id=mid,protocol_sha256=c['protocol_sha256'],environment_sha256=c['environment_sha256']))
            assert meta['packet_sha256']==reused['packet_sha256'] and sha_file(W/reused['packet']/'packet.json')==reused['metadata_sha256']
            cat,hum=load_gt(c,iid,bindings)
            sc=score_people(cat,hum,a['person_semantic_masks'],a['person_extents'],a['person_scores'],'SAPIENS2_DOME29_PRED',spec,bindings[iid])
            nh=native_confusion(cat,a['person_semantic_masks'],a['person_scores'],'SAPIENS2_DOME29_PRED',spec)
            path=root/'scores'/(iid+'.json');atomic_json(path,dict(image_id=iid,scores=sc,source_packet=reused,observation='REUSED_PILOT',config_sha256=c['_config_sha256']))
            acc.add(iid,sc,nh,'SAPIENS2_DOME29_PRED',spec);state.update(reused=len(acc.ids),complete=len(acc.ids))
            emit(ledger,dict(image_id=iid,status='REUSED',packet=reused['packet'],packet_sha256=meta['packet_sha256'],score_file=str(path.relative_to(W)),score_sha256=sha_file(path),end_utc=utc()))
        atomic_json(root/'RUN.json',state)
        stage='MODEL_LOAD';guard(c,root,started,c.get('prior_pilot_operations_seconds',0))
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        model=init_model(W/c['model']['native_config'],checkpoint=None,device='cpu')
        weights=load_file(ck,device='cpu');model.load_state_dict(weights,strict=True);del weights
        model.float().eval().cuda();assert all(p.dtype==torch.float32 for p in model.parameters())
        assert model.cfg.model_name=='sapiens2_0.4b' and model.cfg.num_classes==29 and not model.training
        assert not torch.is_autocast_enabled('cuda')
        training=json.loads((W/c['YOLO']['training_run']).read_text());tr=next(r for r in training['images'] if r['image_id']==c['warmup_id'])
        state.update(status='INFERENCE',strict_load='PASS',parameters=sum(p.numel() for p in model.parameters()))
        atomic_json(root/'RUN.json',state)
        for warmup,iid in [(True,c['warmup_id'])]+[(False,i) for i in c['pending_ids']]:
            guard(c,root,started,c.get('prior_pilot_operations_seconds',0));stage='SOURCE_BINDINGS';check_bindings(c,cp)
            ckstat=ck.stat();assert dict(size=ckstat.st_size,mtime_ns=ckstat.st_mtime_ns)==c['checkpoint_stat']
            split='Training' if warmup else 'Validation';base=W/'datasets/CIHP'/split
            attempt=dict(image_id=iid,warmup=warmup,attempt=1,status='STARTED',start_utc=utc())
            emit(ledger,attempt);rgb,imeta=read_image(base/'Images'/(iid+'.jpg'));h,w=rgb.shape[:2]
            d=tr if warmup else detector[iid];expected=d['rgb_source_sha256'] if warmup else pop[iid]['RGB_sha256']
            assert imeta['file_sha256']==expected
            dp=W/'Human_Parsing_MHPv2_Study'/d['artifact'];assert sha_file(dp)==d['artifact_sha256']
            with np.load(dp,allow_pickle=False) as z:ext=normalize_detector_masks(z['masks'],len(d['opportunities']),(h,w))
            keep=[j for j,e in enumerate(ext) if e.any()];ext=ext[keep];ops=[d['opportunities'][j] for j in keep]
            confidence=np.array([op['score'] for op in ops],np.float32)
            stage='PREPROCESS';tensor,geometry=prepare_rgb(rgb,model.pipeline,model.data_preprocessor);tensor=tensor.cuda()
            geometry.update(detector_mask_conversion='LOSSLESS_BINARY0_1_TO_BOOL_NO_GEOMETRY_CHANGE')
            stage='MODEL_FORWARD'
            if state['model_frame_calls']>=c['max_model_frame_calls']:raise RuntimeError('Call budget exhausted')
            state['model_frame_calls']+=1
            if not warmup:state['new_VAL_calls']+=1
            state['current_image']=iid;atomic_json(root/'RUN.json',state)
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();begin=time.perf_counter()
            with torch.inference_mode():
                logits=model(tensor);stage='MAPBACK_CONTRACT';native=logits_to_native(logits,(h,w))
            torch.cuda.synchronize();duration=time.perf_counter()-begin
            memory=dict(peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,peak_reserved_MiB=torch.cuda.max_memory_reserved()/2**20,
                        device_free_MiB_after=torch.cuda.mem_get_info(0)[0]/2**20)
            del tensor,logits
            if warmup:
                emit(ledger,dict(attempt,status='COMPLETE_WARMUP_NOT_SCORED',end_utc=utc(),geometry=geometry,resource=memory))
                state['warmup']='PASS';atomic_json(root/'RUN.json',state);continue
            stage='ATOMIC_EXPORT'
            a=ownership_planes(native,ext,confidence);a['bboxes_xyxy']=np.array([op['bbox'] for op in ops],np.float32).reshape(-1,4)
            bind=dict(model_id=mid,checkpoint_sha256=c['model']['checkpoint_sha256_from_frozen_registry'],input_sha256=expected,
                      detector_artifact_sha256=d['artifact_sha256'],protocol_sha256=c['protocol_sha256'],config_sha256=c['_config_sha256'],
                      source_hashes=c['pilot_scientific_source_hashes'],route=c['route'],precision=c['precision'])
            meta=dict(image_id=iid,model_id=mid,source_commit=c['model']['source_commit'],checkpoint_sha256=bind['checkpoint_sha256'],
                      input_sha256=expected,config_sha256=c['_config_sha256'],protocol_sha256=c['protocol_sha256'],
                      inference_fingerprint=fingerprint(bind),environment_sha256=c['environment_sha256'],
                      detector_artifact_sha256=d['artifact_sha256'],detector_opportunity_ids=[op['id'] for op in ops],
                      native_person_identity_supported=False,native_instance_count=None,
                      person_score_type='FROZEN_YOLO_DETECTOR_CONFIDENCE_NOT_SEMANTIC_PROBABILITY',geometry=geometry,
                      original_wh=[w,h],GT_used_in_prediction=False,label_space='SAPIENS2_DOME29_PRED',
                      resource_policy='SHARED_GPU_QUALITY_ONLY',resource_observation=memory,precision=c['precision'],fallback_used=False)
            packet=write_packet(root/'packets',iid,a,meta,{})
            # Read committed NPZ before scoring: one saved-mask score pass, not duplicate full rescoring.
            stage='PACKET_READBACK';rmeta,saved=read_packet(packet,dict(image_id=iid,model_id=mid,protocol_sha256=c['protocol_sha256']))
            assert all(np.array_equal(a[k],saved[k]) for k in a)
            stage='SCORING';cat,hum=load_gt(c,iid,bindings)
            sc=score_people(cat,hum,saved['person_semantic_masks'],saved['person_extents'],saved['person_scores'],'SAPIENS2_DOME29_PRED',spec,bindings[iid])
            nh=native_confusion(cat,saved['person_semantic_masks'],saved['person_scores'],'SAPIENS2_DOME29_PRED',spec)
            path=root/'scores'/(iid+'.json');assert not path.exists()
            atomic_json(path,dict(image_id=iid,scores=sc,source_packet=str(packet.relative_to(W)),packet_sha256=rmeta['packet_sha256'],
                                 native_GT_prediction_histogram=nh.tolist(),config_sha256=c['_config_sha256'],protocol_sha256=c['protocol_sha256']))
            acc.add(iid,sc,nh,'SAPIENS2_DOME29_PRED',spec);state['complete']=len(acc.ids)
            emit(ledger,dict(attempt,status='COMPLETE',packet=str(packet.relative_to(W)),packet_sha256=rmeta['packet_sha256'],
                            score_file=str(path.relative_to(W)),score_sha256=sha_file(path),geometry=geometry,resource=memory,
                            forward_mapback_seconds_diagnostic=duration,end_utc=utc()))
            atomic_json(root/'RUN.json',state)
            if len(acc.ids)%25==0:print('Sapiens committed',len(acc.ids),'/5000',flush=True)
        stage='CLOSURE';assert len(acc.ids)==5000 and state['new_VAL_calls']==len(c['pending_ids'])
    except Exception:
        setup=warmup or stage in ['GATE','MODEL_LOAD']
        resource=str(sys.exc_info()[1]).startswith('RESOURCE_')
        state.update(status='INCOMPLETE',setup_failed=int(setup and not resource),resource_stop=resource,failed=1 if not setup and not resource and stage=='MODEL_FORWARD' else 0,invalid=1 if not setup and not resource and stage!='MODEL_FORWARD' else 0,
                     failed_image=iid,stop_stage=stage,error=traceback.format_exc())
        emit(ledger,dict(image_id=iid,warmup=warmup,status='NOT_ATTEMPTED_RESOURCE_STOP' if resource else 'FAILED' if stage=='MODEL_FORWARD' else 'INVALID',failure_stage=stage,error=state['error'],end_utc=utc()))
    finally:
        finish(c,root,state,acc);ledger.close()
        print('GPU terminal',state['status'],state['complete'],flush=True)


def update_report(c,publish=False):
    """Read completed canonical results only; append history, no partial ranking."""
    from zoneinfo import ZoneInfo
    raw=rawroot(c);record=W/c['record_root'];files=[];rows=[];perclass=[];personrows=[];lines=[]
    for mid in c['models']:
        folder=stage_root(c,mid)
        state=json.loads((folder/'RUN.json').read_text()) if (folder/'RUN.json').exists() else dict(status='PENDING',complete=0)
        result=json.loads((folder/'METRICS.json').read_text()) if (folder/'METRICS.json').exists() else {}
        metric=result.get('primary') if result.get('status')=='COMPLETE' else None
        row=dict(run_id=c['run_id'],model_id=mid,status=state['status'],complete=state.get('complete',0),expected=5000,
                 failed=state.get('failed',0),invalid=state.get('invalid',0),missing=5000-state.get('complete',0),
                 mIoU4=metric['mIoU4'] if metric else None,C3_global=metric['C3_global_mean_only'] if metric else None,
                 resource_policy=state.get('resource_policy'),route=c['route'] if mid=='Sapiens2_0.4b' else c['legacy'][mid]['source_route'])
        rows.append(row)
        def fmt(v):return 'null' if v is None else f'{100*v:.3f}'
        lines.append(f"|{mid}|{state['status']}|{row['complete']}/5000|{fmt(row['mIoU4'])}|{fmt(row['C3_global'])}|")
        if metric:
            for j,name in enumerate(['Background','Face proxy','Hair','Upper non-Dress','Lower non-Dress','OTHER']):
                perclass.append(dict(model_id=mid,target_ID=j,target=name,IoU=metric['IoU'][j],GT_support=metric['GT_support'][j],pred_support=metric['pred_support'][j],union=metric['union'][j],zero_union=metric['zero_union'][j]))
            for threshold,values in result['person_metrics'].items():personrows.append(dict(model_id=mid,matching_threshold=threshold,**values))
        for name in ['COMPLETION.json','METRICS.json']:
            f=record/mid/name
            if f.exists():files.append(str(f.relative_to(P)))
    metrics=P/'metrics'/c['run_id'];metrics.mkdir(exist_ok=True)
    for name,data in [('OVERVIEW',rows),('PER_TARGET',perclass),('PERSON_METRICS',personrows)]:
        if data:
            path=metrics/(name+'.csv')
            with path.open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
            files.append(str(path.relative_to(P)))
    atomic_json(record/'OVERVIEW.json',rows);files.append(str((record/'OVERVIEW.json').relative_to(P)))
    report=P/'reports/CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md'
    timestamp=datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Bangkok')).isoformat()
    completed=sum(r['status']=='COMPLETE' for r in rows)
    text=f'''# CIHP–Sapiens C4-P full evaluation — สถานะและผลจริง\n\nอัปเดต {timestamp} Bangkok UTC+07 · run `{c['run_id']}` · **{completed}/5 ระบบ COMPLETE**\n\n## ขอบเขตและวิธีทดลอง\n\nผู้ใช้อนุมัติ QANet/M2FP/D2FP/RP-R-CNN จาก saved artifacts เท่านั้น และ Sapiens2 segmentation 0.4B บน official CIHP validation 5,000 IDs. ใช้ [full config](../configs/cihp_sapiens_c4p_full.json), [revision-2](../protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json), [freeze](../runs/{c['run_id']}/FREEZE.json). ไม่ inference สี่โมเดลหรือ YOLO ใหม่ ไม่เริ่ม CPI/0.8B/1B/training/color/CCTV\n\nNative20 results คงเดิมที่ [รายงานสี่โมเดล](CIHP_FOUR_MODEL_RESULTS_TH.md) ตารางนี้เป็น common view ใหม่ ห้ามเทียบตัวเลขข้ามนิยามโดยตรง. C4-P เฉลี่ย Face proxy/Hair/Upper non-Dress/Lower non-Dress เท่ากัน C3 เป็น global mean Hair/Upper/Lower เท่านั้น ไม่มี Q_C3. Compose native planes ก่อน projection; BG/OTHER valid, GT255 shared VOID, prediction255/unknown เป็น contract failure. Dress/Apparel เป็น OTHER ไม่แบ่งด้วย geometry หรือ void ตามโมเดล.\n\nGlobal CIHP confusion20×20 projected หลังตรวจ pixel equivalence บน fixed ambiguity examples; person metrics คำนวณใหม่จาก saved planes/extents/scores ด้วย geometry-canonical revision2 matcher ทั้ง 0.50/0.75 ไม่คัดลอก scalar native scores. G_loc={c['GT_summary']['G_loc']:,}, G_sem_C4={c['GT_summary']['G_sem_C4']:,} ตรวจจาก bound GT-only manifest; ใช้ fixed GT domain ข้ามระบบ\n\n## สถานะและคะแนนที่มีสิทธิ์\n\nเรียง roster order, IoU ในตารางเป็นเปอร์เซ็นต์; CSV/JSON เก็บ fraction0–1 และ null/ช่องว่างเมื่อยังไม่ครบตาม STRICT_COMPLETE\n\n|ระบบ|สถานะ|Complete/expected|C4-P mIoU4 (%)|C3 global (%)|\n|---|---|---:|---:|---:|\n'''+ '\n'.join(lines)+f'''\n\n[Overview CSV](../metrics/{c['run_id']}/OVERVIEW.csv) · [current canonical overview](../runs/{c['run_id']}/OVERVIEW.json). Per-target IoU/support/union และ person metrics/denominators เพิ่มเมื่อระบบนั้น COMPLETE; ไม่สร้างคะแนน subset เป็นผลชุดเต็ม. Completion counts ต้องผ่าน source/GT/packet/score bindings และ exact5,000 unique IDs. ระบบที่ครบรายงานได้โดยไม่อ้างว่าทั้ง cohort เสร็จ\n\n## Reuse, provenance และทรัพยากร\n\nSapiens reuse หก pilot observations ที่ตรวจ scientific compatibility ก่อน launch เหลือ4,994 pending VAL IDs; process ใหม่ warmup TRAIN0000930 ไม่เกิน1ครั้ง แยกจาก scoring ไม่แก้ fingerprint ของ pilot ย้อนหลัง. [Compatibility](../runs/{c['run_id']}/REUSE_COMPATIBILITY.json) / [resource budget](../runs/{c['run_id']}/RESOURCE_BUDGET.json). Source datasets/checkpoints/native masks/metrics ไม่เขียนทับ. Full config/protocol/source hashes และ launch commit อยู่ใน [launch](../runs/{c['run_id']}/LAUNCH.json) เมื่อเปิดงาน\n\nผลใหม่/attempt ledgers/raw logs/native29 original-grid masks/atomic packet commits/scoring evidence อยู่ `{c['artifact_root']}` ภายนอก Git. CPU สี่โมเดลอ่าน source runs/segments/audit references ตาม full config. แต่ละระบบอาจมาจาก native inference resource regimes ต่างกัน. Shared GPU ของ Sapiens อนุมัติโดยตรง ไม่หยุดเพียง external PID; คง 80GiB ต่อ stream,50GiB free guard,24h ต่อ checkpoint,one attempt,no fallback/retry. 200GiB เป็น planning envelope ไม่ใช่หลักฐานว่าข้อมูลทั้งหมดใช้เท่านั้น\n\n## ภาพและข้อจำกัด\n\n[Gallery reconciliation](../runs/{c['run_id']}/GALLERY_RECONCILIATION.json) ตรวจ PNG ต้นฉบับทั้งหกกับ manifest เดิม ไม่เขียนทับ manifest; ผู้ตรวจรายงานสำเนาที่ส่งมาสี่ไฟล์ไม่ byte-identical แต่ไม่ได้รับ bytes ของสำเนาให้ตรวจอิสระ จึงไม่เดาสาเหตุของช่องทาง. Prediction packets ตรวจแยก ไม่ใช้ภาพ overlay เป็น scientific input. ภาพเปรียบเทียบใช้ 16 IDs เดิมใน CIHP_NATIVE_DIAGNOSTIC_SAMPLE และเก็บ private gallery ใต้ run นี้เมื่อ predictions ที่จำเป็นพร้อม\n\nFace proxy รวม Face_Neck/facial parts จึงไม่รับรอง strict face-only pixel equivalence. Upper/Lower เป็น non-Dress family, Dress/Apparel OTHER ยังคงสร้าง FP/FN ตาม fixed task; native GT×prediction discordance matrix ในผล canonical รองรับการวิเคราะห์ภายหลัง ไม่เปลี่ยน mapping ตามผล. ไม่อ้างว่าทุก taxonomy equivalent. Q_C4_GT ไม่ลงโทษ unmatched predicted persons โดยตรง ต้องอ่าน FP/F1 และ contamination/background leakage พร้อมกัน. Sapiens extents/identity มาจาก YOLO ไม่ใช่ native instance capability.\n\nไม่มี clean parser-only/end-to-end latency/FPS/VRAM-efficiency ranking; forward/map-back/resource observations เป็น shared adapter diagnostics และ native routes เดิมมี conditioning ต่างกัน. ไม่อ้าง architecture causality,ความพร้อม CCTV/สี หรือ statistical significance/uncertainty ที่ไม่ได้คำนวณ. จบรอบแล้วหยุด ไม่เปิดรุ่นอื่นหรือ retry อัตโนมัติ\n'''
    report.write_text(text);files.append(str(report.relative_to(P)))
    archived=record/'REPORT_TH.md'
    def archive_link(match):
        target=match.group(1)
        if target.startswith(('http:','https:','#')):return match.group(0)
        return ']('+os.path.relpath((P/'reports'/target).resolve(),archived.parent)+')'
    archived.write_text(re.sub(r'\]\(([^)]+)\)',archive_link,text));files.append(str(archived.relative_to(P)))
    if publish:
        completed_ids=[r['model_id'] for r in rows if r['status']=='COMPLETE']
        with (P/'WORK_LOG.md').open('a') as log:
            log.write(f'\n## {utc()} UTC — {c["run_id"]}: saved-only CPU completion\n\nCompleted systems: {completed_ids}. Canonical fixed-protocol scores retained, no model inference or post-hoc mapping/settings changes. Remaining workers continue under approved scope.\n')
        files.append('WORK_LOG.md')
        from monitor_cihp_batch import publish as send
        # Existing publisher requires its staged set to equal changed summary files.
        pub=W/'Human_Parsing_Study_Public/Human_Parsing_Benchmark'
        changed=[f for f in dict.fromkeys(files) if not (pub/f).exists() or sha_file(P/f)!=sha_file(pub/f)]
        try:receipt=send(raw,c['run_id']+'-cpu-'+str(len(completed_ids)),changed,
                        scope='Approved common-view CPU work-unit compact results only, no images/raw data',
                        message='results: record common-view saved-only model completion')
        except Exception:receipt=dict(status='PENDING_SYNC',error=traceback.format_exc())
        atomic_json(raw/('PUBLICATION_CPU_'+str(len(completed_ids))+'.json'),receipt)
    return files


def controller(c,cp):
    raw=rawroot(c);raw.mkdir(parents=True,exist_ok=True)
    lock=(P/'outputs/common_view/FULL.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (raw/'LAUNCH.json').exists():raise RuntimeError('Full attempt already launched; no implicit restart')
    check_bindings(c,cp)
    commit=subprocess.check_output(['git','-C',str(W/'Human_Parsing_Study_Public'),'rev-parse','HEAD'],text=True).strip()
    state=dict(run_id=c['run_id'],status='RUNNING',start_utc=utc(),controller_PID=os.getpid(),PGID=os.getpgrp(),SID=os.getsid(0),
               launch_commit=commit,config_sha256=c['_config_sha256'],protocol_sha256=c['protocol_sha256'],workers={},queue_stopped=False)
    atomic_json(raw/'LAUNCH.json',state);atomic_json(W/c['record_root']/'LAUNCH.json',state)
    children={};cpu_started=False
    try:
        for kind in ['gpu']:
            log=(raw/(kind+'.log')).open('x');cmd=[sys.executable,'-u',str(Path(__file__).resolve()),'--config',str(cp),'--worker',kind]
            child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT);children[kind]=(child,log)
            state['workers'][kind]=dict(PID=child.pid,command=cmd,log=str((raw/(kind+'.log')).relative_to(W)))
        atomic_json(raw/'STATE.json',state)
        while any(child.poll() is None for child,_ in children.values()) or not cpu_started:
            gp=stage_root(c,'Sapiens2_0.4b')/'RUN.json';gs=json.loads(gp.read_text()) if gp.exists() else {}
            if not cpu_started and (gs.get('complete',0)>len(c['reused']) or children['gpu'][0].poll() is not None):
                # One CPU process, systems sequential. Low fixed concurrency; no extra GPU workers.
                log=(raw/'cpu.log').open('x');cmd=[sys.executable,'-u',str(Path(__file__).resolve()),'--config',str(cp),'--worker','cpu']
                child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT);children['cpu']=(child,log);cpu_started=True
                state['workers']['cpu']=dict(PID=child.pid,command=cmd,log=str((raw/'cpu.log').relative_to(W)))
                atomic_json(raw/'LAUNCH.json',state);atomic_json(W/c['record_root']/'LAUNCH.json',state)
            state['workers_status']={k:child.poll() for k,(child,_) in children.items()};atomic_json(raw/'STATE.json',state)
            time.sleep(5)
        for child,log in children.values():child.wait();log.close()
        closed=[json.loads((stage_root(c,m)/'RUN.json').read_text()) if (stage_root(c,m)/'RUN.json').exists() else {} for m in c['models']]
        done=sum(s.get('status')=='COMPLETE' for s in closed)
        state.update(status='FINISHED_COMPLETE' if done==5 else 'FINISHED_WITH_INCOMPLETE_SYSTEMS',complete_systems=done,end_utc=utc(),queue_stopped=True)
        if any(child.returncode for child,_ in children.values()):state['status']='FINISHED_WITH_WORKER_ERROR_REQUIRES_RECONCILIATION'
        atomic_json(raw/'STATE.json',state);atomic_json(W/c['record_root']/'BATCH_COMPLETION.json',state)
        files=update_report(c)
        from render_common_full import render
        try:
            render(c);files.append('runs/'+c['run_id']+'/GALLERY_INDEX.json')
        except Exception:atomic_json(raw/'GALLERY_FAILURE.json',dict(error=traceback.format_exc()))
        guards=json.loads((raw/'DOCUMENT_GUARDS.json').read_text())
        if sha_file(P/'STATUS.md')==guards['STATUS.md']:
            (P/'STATUS.md').write_text(f"# Human Parsing Benchmark — current status\n\n**COMMON_C4P_FULL_{state['status']}** · {state['end_utc']} UTC\n\nRun `{c['run_id']}`. [Full common-view report](reports/CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md). [Canonical overview](runs/{c['run_id']}/OVERVIEW.json). Queue stopped; no next model/retry. CPI paused, native results preserved. Shared-GPU diagnostics only. See report for per-system STRICT_COMPLETE state and retained failures.\n");files.append('STATUS.md')
        with (P/'WORK_LOG.md').open('a') as log:log.write(f"\n## {utc()} UTC — {c['run_id']}: batch terminal\n\n{state['status']}; GPU + saved-only CPU workers exited, no next-model launch. Canonical per-system results/strict nulls and immutable attempts under fresh run. Full report updated; no native scientific changes or extra inference.\n")
        files+=['WORK_LOG.md','runs/'+c['run_id']+'/BATCH_COMPLETION.json']
        from monitor_cihp_batch import publish
        pub=W/'Human_Parsing_Study_Public/Human_Parsing_Benchmark'
        files=[f for f in dict.fromkeys(files) if not (pub/f).exists() or sha_file(P/f)!=sha_file(pub/f)]
        try:receipt=publish(raw,c['run_id']+'-closure',files,scope='Approved full C4-P compact results/provenance only, no raw data/images',message='results: close approved CIHP Sapiens C4-P full evaluation')
        except Exception:receipt=dict(status='PENDING_SYNC',error=traceback.format_exc())
        atomic_json(raw/'PUBLICATION.json',receipt)
    except Exception:
        atomic_json(raw/'CONTROLLER_FAILURE.json',dict(status='INTERRUPTED_CONTROLLER_REQUIRES_RECONCILIATION',error=traceback.format_exc(),workers=state['workers'],utc=utc()))
        # Do not silently relaunch/kill a still-running worker; record live child IDs for reconciliation.
        raise


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--worker',choices=['gpu','cpu']);a=parser.parse_args()
    cp=Path(a.config).resolve();c=json.loads(cp.read_text());c['_config_sha256']=sha_file(cp)
    if c['scope']!='CIHP_SAPIENS_C4P_FULL' or c['model']['model_id']!='Sapiens2_0.4b':raise ValueError('Wrong scope')
    if a.worker=='gpu':gpu_worker(c,cp)
    elif a.worker=='cpu':cpu_worker(c,cp)
    else:controller(c,cp)

if __name__=='__main__':main()
