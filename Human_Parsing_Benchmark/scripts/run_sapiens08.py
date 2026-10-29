"""Isolated 0.8B scheduler + GPU worker: pilot6 then authorized full5000.

One process/lock owns both roles, detached by launcher. No 0.4B modifications,
model retries, full legacy rescoring, or implicit resume of interrupted attempts.
"""
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import argparse,csv,fcntl,gc,importlib.metadata,json,os,re,shutil,subprocess,sys,time,traceback
import numpy as np
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'));sys.path.insert(0,str(P/'scripts'))
from common_view.core import sha_file,load_spec
from common_view.full import Accumulator,score_people,native_confusion
from common_view.packets import atomic_json,read_packet,write_packet,fingerprint
from common_view.detector_cache import normalize_detector_masks
from common_view.sapiens08_resources import snapshot,execution_seconds
from run_common_full import load_gt,emit
from cihp_benchmark.data import read_image


def utc():return datetime.now(timezone.utc).isoformat()
def thai():return datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Bangkok')).isoformat()


class Run:
    def __init__(self,path):
        self.path=Path(path).resolve();self.c=json.loads(self.path.read_text());self.chash=sha_file(self.path)
        c=self.c
        if c['model_id']!='Sapiens2_0.8b' or c['scope']!='SAPIENS2_08B_C4P_PILOT_THEN_FULL_USER_AUTHORIZED':raise ValueError('Wrong scope')
        self.raw=W/c['artifact_root'];self.record=W/c['record_root'];self.start=time.monotonic();self.wait=0.;self.ownpeak=c['historical08_profile']['peak_reserved_MiB']
        self.spec=load_spec(W/c['protocol']);self.model=None;self.loads=0;self.stage='GATE';self.iid=None;self.warmup=False
        self.bindings={r['image_id']:r for r in map(json.loads,(W/c['GT_binding_root']/'BINDINGS.jsonl').open())}
        self.pop={r['id']:r for r in json.loads((W/c['native_population']).read_text())['members']}
        self.det={r['image_id']:r for r in map(json.loads,(W/c['YOLO']['validation_ledger']).open())}
        training=json.loads((W/c['YOLO']['training_run']).read_text());self.train=next(r for r in training['images'] if r['image_id']==c['warmup_id'])
        self.acc=Accumulator(c['expected_ids']);self.pilot_rows=[];self.phase='pilot';self.execution_config_sha=self.chash
        self.state=dict(run_id=c['run_id'],model_id=c['model_id'],status='PREPARING',controller_PID=os.getpid(),worker_PID=os.getpid(),pid=os.getpid(),
            process_roles='ONE_PROCESS_SCHEDULER_AND_GPU_WORKER',PGID=os.getpgrp(),SID=os.getsid(0),start_utc=utc(),pilot_complete=0,complete=0,expected=5000,
            reused=0,new_VAL_calls=0,model_frame_calls=0,warmup_calls=0,failed=0,invalid=0,setup_failed=0,
            queue_seconds=0.,execution_seconds=0.,queue_stopped=False,resource_policy='SHARED_GPU_QUALITY_ONLY',
            config_sha256=self.chash,protocol_sha256=c['protocol_sha256'],scientific_identity_sha256=c['scientific_identity_sha256'],
            birth_ticks=int(Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]),
            launch_commit=subprocess.check_output(['git','-C',str(W/'Human_Parsing_Study_Public'),'rev-parse','HEAD'],text=True).strip(),primary=None)
        self.ledger=(self.raw/'EXECUTION.jsonl').open('x',buffering=1)

    def save(self):
        self.state.update(queue_seconds=self.wait,execution_seconds=execution_seconds(self.start,self.wait,time.monotonic()),model_loads=self.loads)
        atomic_json(self.raw/'STATE.json',self.state)
        atomic_json(self.raw/'models/Sapiens2_0.8b/RUN.json',self.state)

    def bindings_check(self):
        if sha_file(self.path)!=self.chash:raise RuntimeError('Pilot orchestration config changed')
        c=self.c
        for f,h in {**c['scientific_source_hashes'],**c['execution_source_hashes'],**c['native_preserved']}.items():
            if sha_file(W/f)!=h:raise RuntimeError('Source/config drift '+f)
        assert sha_file(W/c['protocol'])==c['protocol_sha256']
        assert sha_file(W/c['GT_binding_root']/'BINDINGS.jsonl')==c['GT_manifest_sha256']
        assert sha_file(W/c['native_population'])==c['native_population_sha256']
        assert os.environ.get('CUDA_VISIBLE_DEVICES')==c['CUDA_VISIBLE_DEVICES']
        assert os.environ.get('PYTORCH_CUDA_ALLOC_CONF')==c['allocator_environment_preserved']
        ck=W/c['model']['checkpoint'];s=ck.stat();assert dict(size=s.st_size,mtime_ns=s.st_mtime_ns)==c['checkpoint_stat']

    def guard(self):
        c=self.c
        if execution_seconds(self.start,self.wait,time.monotonic())>c['max_hours']*3600:raise RuntimeError('RESOURCE_EXECUTION_TIME_STOP')
        if shutil.disk_usage(self.raw).free<(c['minimum_free_gib']+.1)*2**30:raise RuntimeError('RESOURCE_DISK_FREE_STOP')
        if sum(f.stat().st_size for f in self.raw.rglob('*') if f.is_file())>c['max_stream_gib']*2**30:raise RuntimeError('RESOURCE_STREAM_STORAGE_STOP')

    def await_resources(self,for_phase):
        """Queue before allocation. Successful pilot may release only this model for full queue."""
        self.guard();snap=snapshot(self.c,W,self.ownpeak);atomic_json(self.raw/'RESOURCE_CURRENT.json',snap)
        if snap['admitted']:return
        if self.model is not None:
            self.model=None;gc.collect()
            import torch
            torch.cuda.empty_cache()  # release only this process after successful pilot; never fallback/OOM retry
            emit(self.ledger,dict(status='MODEL_RELEASED_FOR_RESOURCE_QUEUE',phase=for_phase,utc=utc(),no_CPU_inference=True))
        queued=time.monotonic();prior_wait=self.wait;self.state.update(status='QUEUED',queue_for=for_phase,queue_reason=snap);self.save();self.report()
        try:
            with (self.raw/'QUEUE.jsonl').open('a') as log:
                while True:
                    current_wait=prior_wait+time.monotonic()-queued
                    self.state['queue_seconds']=current_wait
                    if current_wait>self.c['max_queue_hours']*3600:raise RuntimeError('RESOURCE_QUEUE_DEADLINE_EXPIRED')
                    snap=snapshot(self.c,W,self.ownpeak);emit(log,snap)
                    if snap['admitted']:
                        self.state.pop('queue_reason',None);return
                    self.state.update(status='QUEUED',queue_for=for_phase,queue_reason=snap)
                    atomic_json(self.raw/'STATE.json',self.state)
                    time.sleep(self.c['queue_poll_seconds'])
        finally:
            self.wait=prior_wait+time.monotonic()-queued
            self.save()

    def load(self):
        if self.model is not None:return
        if self.loads>=2:raise RuntimeError('Bounded model-load budget exhausted; no restart loop')
        self.stage='MODEL_LOAD';self.bindings_check();self.guard();self.loads+=1;self.save()
        from sapiens.dense.models import init_model
        from safetensors.torch import load_file
        import torch
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        model=init_model(W/self.c['model']['native_config'],checkpoint=None,device='cpu')
        weights=load_file(W/self.c['model']['checkpoint'],device='cpu');model.load_state_dict(weights,strict=True);del weights
        model.float().eval().cuda();assert model.cfg.model_name=='sapiens2_0.8b' and model.cfg.num_classes==29 and not model.training
        assert all(p.dtype==torch.float32 for p in model.parameters()) and not torch.is_autocast_enabled('cuda')
        assert sum(p.numel() for p in model.parameters())==self.c['historical08_profile']['parameters']
        self.model=model;self.state.update(strict_load='PASS',parameters=sum(p.numel() for p in model.parameters()));self.save()

    def frame(self,iid,warmup=False):
        import torch
        from common_view.sapiens_route import prepare_rgb,logits_to_native,ownership_planes
        c=self.c;self.iid=iid;self.warmup=warmup;self.stage='RESOURCE_ADMISSION';self.await_resources(self.phase);self.load()
        self.state['status']='PILOT_RUNNING' if self.phase=='pilot' else 'FULL_RUNNING'
        self.stage='SOURCE_BINDINGS';self.guard();self.bindings_check()
        attempt=dict(image_id=iid,phase=self.phase,warmup=warmup,attempt=1,status='STARTED',start_utc=utc());emit(self.ledger,attempt)
        base=W/'datasets/CIHP'/('Training' if warmup else 'Validation');rgb,imeta=read_image(base/'Images'/(iid+'.jpg'));h,w=rgb.shape[:2]
        d=self.train if warmup else self.det[iid];expected=d['rgb_source_sha256'] if warmup else self.pop[iid]['RGB_sha256']
        assert imeta['file_sha256']==expected and list(d.get('original_wh',d.get('wh')))==[w,h]
        dp=W/'Human_Parsing_MHPv2_Study'/d['artifact'];assert sha_file(dp)==d['artifact_sha256']
        with np.load(dp,allow_pickle=False) as z:ext=normalize_detector_masks(z['masks'],len(d['opportunities']),(h,w))
        keep=[j for j,e in enumerate(ext) if e.any()];ext=ext[keep];ops=[d['opportunities'][j] for j in keep];confidence=np.array([op['score'] for op in ops],np.float32)
        self.stage='PREPROCESS';tensor,geometry=prepare_rgb(rgb,self.model.pipeline,self.model.data_preprocessor);tensor=tensor.cuda()
        if self.state['model_frame_calls']>=c['max_total_model_calls']:raise RuntimeError('Forward call budget exhausted')
        if self.phase=='pilot' and self.state['model_frame_calls']>=c['max_pilot_model_calls']:raise RuntimeError('Pilot call budget exhausted')
        if warmup and self.state['warmup_calls']>=1:raise RuntimeError('No extra warmup authorized')
        self.stage='MODEL_FORWARD';self.state['model_frame_calls']+=1
        if warmup:self.state['warmup_calls']+=1
        else:self.state['new_VAL_calls']+=1
        self.state['current_image']=iid;self.save();torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();begin=time.perf_counter()
        with torch.inference_mode():logits=self.model(tensor);self.stage='MAPBACK_CONTRACT';native=logits_to_native(logits,(h,w))
        torch.cuda.synchronize();elapsed=time.perf_counter()-begin
        memory=dict(peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,peak_reserved_MiB=torch.cuda.max_memory_reserved()/2**20,
                    device_free_MiB_after=torch.cuda.mem_get_info(0)[0]/2**20)
        self.ownpeak=max(self.ownpeak,memory['peak_reserved_MiB']);del tensor,logits
        if warmup:
            emit(self.ledger,dict(attempt,status='COMPLETE_WARMUP_NOT_SCORED',end_utc=utc(),geometry=geometry,resource=memory))
            self.state['warmup']='PASS';self.save();return
        self.stage='ATOMIC_EXPORT';a=ownership_planes(native,ext,confidence);a['bboxes_xyxy']=np.array([op['bbox'] for op in ops],np.float32).reshape(-1,4)
        bind=dict(scientific_identity_sha256=c['scientific_identity_sha256'],input_sha256=expected,detector_artifact_sha256=d['artifact_sha256'])
        meta=dict(image_id=iid,model_id=c['model_id'],checkpoint_sha256=c['checkpoint_sha256'],native_config_sha256=c['model']['native_config_sha256'],
            source_commit=c['model']['source_commit'],input_sha256=expected,config_sha256=self.execution_config_sha,protocol_sha256=c['protocol_sha256'],
            environment_sha256=c['environment_sha256'],scientific_identity_sha256=c['scientific_identity_sha256'],inference_fingerprint=fingerprint(bind),
            detector_artifact_sha256=d['artifact_sha256'],detector_opportunity_ids=[op['id'] for op in ops],native_person_identity_supported=False,native_instance_count=None,
            person_score_type='FROZEN_YOLO_DETECTOR_CONFIDENCE_NOT_SEMANTIC_PROBABILITY',original_wh=[w,h],geometry=geometry,GT_used_in_prediction=False,
            label_space='SAPIENS2_DOME29_PRED',scoring_fingerprint=fingerprint(dict(GT=self.bindings[iid],protocol=c['protocol_sha256'],inference=fingerprint(bind))),precision=c['precision'],fallback_used=False,resource_policy=c['resource_policy'],resource_observation=memory)
        packet=write_packet(self.raw/self.phase/'packets',iid,a,meta,{})
        self.stage='PACKET_READBACK';m,saved=read_packet(packet,dict(image_id=iid,model_id=c['model_id'],scientific_identity_sha256=c['scientific_identity_sha256']))
        assert all(np.array_equal(a[k],saved[k]) for k in a)
        self.stage='SCORING';cat,hum=load_gt(c,iid,self.bindings)
        scores=score_people(cat,hum,saved['person_semantic_masks'],saved['person_extents'],saved['person_scores'],'SAPIENS2_DOME29_PRED',self.spec,self.bindings[iid])
        nh=native_confusion(cat,saved['person_semantic_masks'],saved['person_scores'],'SAPIENS2_DOME29_PRED',self.spec)
        path=self.raw/self.phase/'scores'/(iid+'.json')
        row=dict(image_id=iid,scores=scores,native_GT_prediction_histogram=nh.tolist(),packet=str(packet.relative_to(W)),packet_sha256=m['packet_sha256'],
                 config_sha256=self.execution_config_sha,protocol_sha256=c['protocol_sha256'],scientific_identity_sha256=c['scientific_identity_sha256'])
        atomic_json(path,row)
        self.acc.add(iid,scores,nh,'SAPIENS2_DOME29_PRED',self.spec)
        if self.phase=='pilot':self.pilot_rows.append(row);self.state['pilot_complete']=len(self.pilot_rows)
        else:self.state['complete']=len(self.acc.ids)
        emit(self.ledger,dict(attempt,status='COMPLETE',packet=row['packet'],packet_sha256=row['packet_sha256'],score_file=str(path.relative_to(W)),score_sha256=sha_file(path),
                              geometry=geometry,resource=memory,forward_mapback_seconds_diagnostic=elapsed,end_utc=utc()))
        self.save()
        if self.phase=='full' and self.state['complete']%100==0:self.report();print('Full committed',self.state['complete'],'/5000',flush=True)

    def promote(self):
        c=self.c;assert self.state['pilot_complete']==6 and self.state['model_frame_calls']==7 and self.state['failed']==self.state['invalid']==0
        for row in self.pilot_rows:
            meta,a=read_packet(W/row['packet'],dict(model_id=c['model_id'],scientific_identity_sha256=c['scientific_identity_sha256']))
            assert meta['packet_sha256']==row['packet_sha256'] and meta['config_sha256']==self.chash
        from render_common_pilot import render
        render(self.raw/'pilot',self.spec,c['pilot_ids'])
        pilot=Accumulator(c['pilot_ids'])
        for row in self.pilot_rows:pilot.add(row['image_id'],row['scores'],np.array(row['native_GT_prediction_histogram'],np.int64),'SAPIENS2_DOME29_PRED',self.spec)
        result=pilot.report();assert result['status']=='COMPLETE'
        atomic_json(self.record/'PILOT_COMPLETION.json',dict(status='PILOT_PASS',expected=6,complete=6,model_calls=7,warmup=1,
            primary=None,pilot_diagnostics=result['primary'],person_diagnostics=result['person_metrics'],scientific_identity_sha256=c['scientific_identity_sha256'],
            geometry_native29_atomic_readback_GT_scoring='PASS',readiness_not_based_on_quality=True))
        pending=[i for i in c['expected_ids'] if i not in self.acc.ids];assert len(pending)==4994 and len(self.acc.ids)==6
        full=dict(c,scope='SAPIENS2_08B_C4P_FULL_FROZEN_AFTER_PILOT',pilot_config_sha256=self.chash,reused_ids=list(c['pilot_ids']),pending_ids=pending,
                  reused=[{k:r[k] for k in ['image_id','packet','packet_sha256','config_sha256','scientific_identity_sha256']} for r in self.pilot_rows],
                  expected=5000,full_frozen_utc=utc(),no_old_fingerprint_rewrite=True,automatic_full_authorization_from_user=True)
        fp=W/c['full_config_path']
        if fp.exists():raise RuntimeError('Full config already exists; do not overwrite')
        atomic_json(fp,full);atomic_json(self.raw/'FULL_CONFIG.json',full);atomic_json(self.record/'FULL_CONFIG.json',full)
        self.execution_config_sha=sha_file(fp);self.phase='full';self.state.update(reused=6,complete=6,full_config_sha256=self.execution_config_sha,status='FULL_READY')
        atomic_json(self.record/'REUSE_COMPATIBILITY.json',dict(status='PASS',same_scientific_identity=c['scientific_identity_sha256'],pilot_config_sha256=self.chash,
            full_config_sha256=self.execution_config_sha,all_six_atomic_packets_checked=True,reused_ids=c['pilot_ids'],pending_count=4994,old_fingerprints_not_modified=True,score_not_used_for_reuse_choice=True))
        self.save();self.report();self.publish('pilot-pass-full-freeze')
        return pending

    def report(self):
        c=self.c;peerfile=W/c['peer04_artifact_root']/'models/Sapiens2_0.4b/RUN.json';peer=json.loads(peerfile.read_text()) if peerfile.exists() else {}
        metrics=self.acc.report() if self.phase=='full' else None
        if metrics and metrics['status']=='COMPLETE' and not (self.state['failed'] or self.state['invalid'] or self.state['setup_failed']):
            assert metrics['primary']['GT_support']==c['GT_summary']['global_support']
            for values in metrics['person_metrics'].values():assert values['G_loc']==c['GT_summary']['G_loc'] and values['G_sem_C4']==c['GT_summary']['G_sem_C4']
        if metrics and (self.state['failed'] or self.state['invalid'] or self.state['setup_failed']):metrics.update(status='INCOMPLETE',primary=None,person_metrics=None)
        if metrics:
            metrics.update(run_id=c['run_id'],model_id=c['model_id'],protocol_sha256=c['protocol_sha256'],resource_policy=c['resource_policy'],
                           scientific_identity_sha256=c['scientific_identity_sha256'],route=c['route'],reused=6,new_calls=self.state['new_VAL_calls'],failed=self.state['failed'],invalid=self.state['invalid'])
            atomic_json(self.raw/'METRICS.json',metrics)
            if self.state['queue_stopped']:atomic_json(self.record/'METRICS.json',metrics)
        report=P/'reports/CIHP_SAPIENS_08B_C4P_RESULTS_TH.md';quality=metrics.get('primary') if metrics and metrics['status']=='COMPLETE' else None
        table='|Target|IoU (%)|GT support|Prediction support|Union|\n|---|---:|---:|---:|---:|\n'
        if quality:
            for j,name in [(1,'Face proxy'),(2,'Hair'),(3,'Upper non-Dress'),(4,'Lower non-Dress')]:table+=f"|{name}|{100*quality['IoU'][j]:.3f}|{quality['GT_support'][j]}|{quality['pred_support'][j]}|{quality['union'][j]}|\n"
        else:table+='|ผลยังไม่ครบตาม STRICT_COMPLETE|null|N/A|N/A|N/A|\n'
        avg='null' if quality is None else f"{100*quality['mIoU4']:.3f}%"
        text=f'''# Sapiens2 segmentation 0.8B — CIHP C4-P\n\nอัปเดต {thai()} · run `{c['run_id']}` · **{self.state['status']}**\n\n## สถานะและขอบเขต\n\n|ระบบ|สถานะ|Complete/5,000|\n|---|---|---:|\n|Sapiens2 0.4B (รอบเดิม)|{peer.get('status','UNKNOWN')}|{peer.get('complete',0)}/5000|\n|Sapiens2 0.8B|{self.state['status']}|{self.state['complete']}/5000|\n\nPilot0.8B {self.state['pilot_complete']}/6; model-frame callsรวม {self.state['model_frame_calls']}; warmup {self.state['warmup_calls']}; reused {self.state['reused']}; queue {self.state['queue_seconds']:.1f}s แยกจาก execution {self.state['execution_seconds']:.1f}s. ค่า complete ของ0.8Bนับ canonical หลัง pilot ผ่าน/manifestfreezeเท่านั้น. ทั้งสองค่าเวลานี้เป็น operational accounting ไม่ใช่ speed ranking\n\nผู้ใช้อนุมัติ pilotหนึ่งTRAINwarmup+6fixedVAL แล้ว full validation5,000 เมื่อผ่าน โดยไม่ถามซ้ำ; shared-GPU quality-only พร้อม0.4Bได้เมื่อadmissionผ่าน มิฉะนั้นqueueไม่หยุด0.4B. รอคิวสูงสุด24hแยกจากexecution24h,stream80GiB/free50GiBเดิม. ไม่มี1B/CPI/training/color/YOLO inference และไม่คำนวณ common view สี่โมเดลเดิมซ้ำ\n\n## Identity และ protocol\n\nCheckpoint `{c['model']['checkpoint']}` SHA256 `{c['checkpoint_sha256']}`; nativeconfig `{c['model']['native_config']}` SHA256 `{c['model']['native_config_sha256']}`; source `{c['model']['source_commit']}`. Strict model loadingและ827,531,997parameters/native29headตรวจในworkerก่อนforward ไม่ใช้ binding/weights0.4B. Environment `.venvs/sapiens2-pilot` versions/hashของรอบนี้บันทึกแยก\n\n[Pilot config](../configs/cihp_sapiens_08b_pilot.json), [readiness](../runs/{c['run_id']}/READINESS.json), [resource readiness](../runs/{c['run_id']}/RESOURCE_READINESS.json). Full config/compatibilityจะสร้างหลังpilotผ่านโดย scientific identityเดิม ไม่แก้ fingerprintย้อนหลังและไม่เลือก predictions จากคะแนน\n\nใช้ C4-P revision2 SHA256 `{c['protocol_sha256']}` เหมือน0.4B: full-frame semantic29/1024×768/FP32/batch1/eval/inference/noAMP/TF32/extraTTA; native logits map-backก่อนargmax แล้ว frozenYOLOmaskownership; compose nativeก่อนproject. BG/OTHER valid,GT255 sharedVOID,predictionunknown/255fail. Face proxyไม่ใช่strictface-only; Upper/Lower non-Dress; Dress/ApparelOTHER ไม่splitด้วยgeometry. G_loc={c['GT_summary']['G_loc']:,}/G_sem_C4={c['GT_summary']['G_sem_C4']:,} จากexact GTmanifest; geometry-canonical matching0.50/0.75,C3global-only,noQ_C3\n\n## ผลคุณภาพ\n\n**C4-P mIoU4 = {avg}**; ไม่ใช้คะแนน subset แทนชุดเต็ม. ตาราง IoU เป็นเปอร์เซ็นต์ JSONเก็บfraction0–1\n\n{table}\n\nPerson Q_C4_GT/TP/FP/FN/precision/recall/extentF1/contamination/denominators และnativeGT×prediction discordanceอยู่ใน canonical METRICSเมื่อครบเท่านั้น. Qไม่ลงโทษunmatchedpredictionsโดยตรงจึงต้องอ่านFP/F1ร่วม ไม่อ้างoverallwinnerจากQตัวเดียว; extents/IDsมาจากYOLOไม่ใช่nativeinstancecapability. ไม่รวมnative20 tableกับcommon4 scores\n\n## Artifacts, checks และข้อจำกัด\n\nRaw root `{c['artifact_root']}` เก็บ ENVIRONMENT/LAUNCH/STATE/EXECUTION/QUEUE/resource observations, pilot/full native29original-grid NPZ,per-person planes/extents/confidences/geometry,atomicCOMMITและscorehashes. Pilot6ภาพIDsตามที่กำหนด ไม่เลือกตามคะแนน; privategalleryสร้างจากsavedmasks. Fullmanifestreused/pendingต้องdisjointและครบ5,000unique;ไม่ครบmainnull,เก็บfailure/partial/orphanโดยไม่retry/fallbackหรือลดsettings. ข้อมูลภาพ/dataset/weights/bulkoutputsไม่ขึ้นGit\n\nCommon scorer/packet/routeที่ผ่านCPU acceptanceเดิมใช้ต่อเมื่อhashesตรง ไม่รันfulltest suiteซ้ำ. ตรวจเพิ่มเฉพาะ0.8Bcheckpoint/hash/native29header/source/configpipeline/eval strictload,resource-admissionfixturesและ7modelcallsตามpilotbudget. Resource admissionใช้observed0.4peak+historical0.8peak+largestpopulationmapback+context/growth/headroom+หลายsnapshot ไม่ตัดสินจากutilizationหรือfreeVRAMจุดเดียว; empirical budgetไม่รับรองทุกภาพ. Queue/exec clocks/resourcecapsมีledgerแยก\n\nไม่มีclean latency/FPS/VRAM-efficiency ranking, architecture-only causality หรือCCTV/สีข้อยืนยัน. ไม่เปลี่ยนmapping/settingsตามpilot/fullscores. ปัญหาเฉพาะ0.8Bหยุดเฉพาะstreamนี้ เก็บหลักฐาน ไม่หยุด/แก้0.4B. [ผล0.4Bและสี่โมเดลเดิม](CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md) เป็นรายงานแยก ไม่รันซ้ำ\n'''
        report.write_text(text)
        # Archive with correct root-relative navigation.
        def link(m):
            v=m.group(1)
            return m.group(0) if v.startswith(('http','#','/')) else ']('+os.path.relpath((report.parent/v).resolve(),self.record)+')'
        (self.record/'REPORT_TH.md').write_text(re.sub(r'\]\(([^)]+)\)',link,text))
        if quality:
            out=P/'metrics'/c['run_id'];out.mkdir(exist_ok=True)
            with (out/'PER_TARGET.csv').open('w',newline='') as f:
                writer=csv.writer(f,lineterminator='\n');writer.writerow(['target_ID','target','IoU','GT_support','pred_support','union'])
                for j,name in enumerate(['Background','Face proxy','Hair','Upper non-Dress','Lower non-Dress','OTHER']):writer.writerow([j,name,quality['IoU'][j],quality['GT_support'][j],quality['pred_support'][j],quality['union'][j]])
        return report

    def publish(self,phase):
        with (P/'WORK_LOG.md').open('a') as f:f.write(f'\n## {thai()} — {self.c["run_id"]}: {phase}\n\nSapiens0.8B status{self.state["status"]},pilot{self.state["pilot_complete"]}/6,canonical{self.state["complete"]}/5000,calls{self.state["model_frame_calls"]},queue{self.state["queue_seconds"]:.1f}s/execution{self.state["execution_seconds"]:.1f}s. Own checkpoint/native29/source/scientificidentity/GT bindings;no04modification/noexistingfourrescoring/noqualitytuning/retry/fallback. SourceprovenanceandThai reportrecorded.\n')
        files=[str(f.relative_to(P)) for f in self.record.glob('*') if f.is_file() and f.suffix in ['.json','.md']]
        files+=['reports/CIHP_SAPIENS_08B_C4P_RESULTS_TH.md','WORK_LOG.md']
        if (W/self.c['full_config_path']).exists():files.append(self.c['full_config_path'].removeprefix('Human_Parsing_Benchmark/'))
        metrics=P/'metrics'/self.c['run_id']
        if metrics.exists():files += [str(f.relative_to(P)) for f in metrics.glob('*.csv')]
        pub=W/'Human_Parsing_Study_Public/Human_Parsing_Benchmark'
        files=[f for f in dict.fromkeys(files) if not (pub/f).exists() or sha_file(P/f)!=sha_file(pub/f)]
        try:
            from monitor_cihp_batch import publish
            receipt=publish(self.raw,self.c['run_id']+'-'+phase,files,scope='0.8B approved C4-P compact config/report/provenance only, no images/raw datasets',message='results: record Sapiens 0.8B '+phase)
        except Exception:receipt=dict(status='PENDING_SYNC',error=traceback.format_exc())
        atomic_json(self.raw/('PUBLICATION_'+phase+'.json'),receipt)

    def execute(self):
        self.save();atomic_json(self.raw/'LAUNCH.json',self.state);atomic_json(self.record/'LAUNCH.json',self.state)
        try:
            self.bindings_check();self.await_resources('pilot');self.load();self.state['status']='PILOT_RUNNING';self.save()
            self.phase='pilot';self.frame(self.c['warmup_id'],True)
            for iid in self.c['pilot_ids']:self.frame(iid)
            pending=self.promote();self.await_resources('full');self.load();self.state['status']='FULL_RUNNING';self.save()
            for iid in pending:self.frame(iid)
            assert self.acc.ids==set(self.c['expected_ids']) and self.state['model_frame_calls']==5001
            self.state.update(status='COMPLETE',complete=5000,artifact_validation='PASS_ATOMIC_READBACK_AND_SAVED_MASK_SCORING')
        except BaseException:
            resource=str(sys.exc_info()[1]).startswith('RESOURCE_');setup=self.stage in ['GATE','MODEL_LOAD'] or self.warmup
            self.state.update(status='BLOCKED' if resource or setup else 'STOPPED_INCOMPLETE',failed=1 if not setup and self.stage=='MODEL_FORWARD' else 0,
                invalid=1 if not setup and not resource and self.stage!='MODEL_FORWARD' else 0,setup_failed=int(setup and not resource),stop_stage=self.stage,failed_image=self.iid,error=traceback.format_exc())
            emit(self.ledger,dict(status='RESOURCE_STOP' if resource else 'FAILED',image_id=self.iid,phase=self.phase,warmup=self.warmup,stage=self.stage,error=self.state['error'],utc=utc()))
            atomic_json(self.raw/'FAILURE.json',self.state)
        finally:
            self.state.update(end_utc=utc(),queue_stopped=True,next_model_started=False,model_retries=0,fallback_used=False)
            self.save();self.ledger.close()
            try:self.report()
            except Exception:
                self.state.update(status='STOPPED_INCOMPLETE',invalid=1,report_validation_error=traceback.format_exc());self.save();self.report()
            atomic_json(self.record/'COMPLETION.json',self.state)
            self.publish('closure');print('Terminal',self.state['status'],self.state['complete'],flush=True)
        return 0 if self.state['status']=='COMPLETE' else 1


def main():
    a=argparse.ArgumentParser();a.add_argument('--config',default='Human_Parsing_Benchmark/configs/cihp_sapiens_08b_pilot.json');a.add_argument('--status',action='store_true');a.add_argument('--watch',action='store_true');args=a.parse_args()
    if args.watch and not args.status:a.error('--watch requires --status; it never starts inference')
    c=json.loads(Path(args.config).read_text());raw=W/c['artifact_root']
    if args.status:
        try:
            while True:
                s=json.loads((raw/'STATE.json').read_text()) if (raw/'STATE.json').exists() else {}
                peer=json.loads((W/c['peer04_artifact_root']/'models/Sapiens2_0.4b/RUN.json').read_text())
                pid=s.get('pid');alive=False
                if pid:
                    try:
                        proc=Path('/proc')/str(pid);ticks=int((proc/'stat').read_text().rsplit(')',1)[1].split()[19])
                        alive=ticks==s.get('birth_ticks') and b'run_sapiens08.py' in (proc/'cmdline').read_bytes()
                    except FileNotFoundError:pass
                display=s.get('status','PREPARING') if alive or not pid or s.get('queue_stopped') else 'INTERRUPTED_REQUIRES_RECONCILIATION'
                print(thai(),c['run_id'],'\n08B:',display,'pilot',s.get('pilot_complete',0),'/6 canonical',s.get('complete',0),'/5000 reused',s.get('reused',0),'calls',s.get('model_frame_calls',0),
                      'PID',s.get('pid'),'queue seconds',s.get('queue_seconds',0),'\n04B:',peer['status'],peer['complete'],'/5000\nSTATE',raw/'STATE.json',flush=True)
                if not args.watch or s.get('queue_stopped') or (pid and not alive):return 0
                time.sleep(5)
        except KeyboardInterrupt:return 0
    lock=(P/'outputs/common_view/SAPIENS08.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (raw/'LAUNCH.json').exists() or (raw/'EXECUTION.jsonl').exists():raise RuntimeError('Attempt exists; controlled reconciliation required, no implicit restart')
    return Run(args.config).execute()
if __name__=='__main__':raise SystemExit(main())
