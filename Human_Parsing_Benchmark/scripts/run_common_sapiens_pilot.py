"""One detached Sapiens2 0.4B C4-P pilot. Seven calls maximum; no resume/retry.

Never use this entry point for full validation. All native datasets/results are
read-only. Errors terminate the queue and retain attempts/partial outputs.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,os,sys,time,traceback,subprocess,shutil
import numpy as np
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'));sys.path.insert(0,str(P/'scripts'))
from common_view.core import load_spec,sha_file,score_packet,gt_domains
from common_view.packets import atomic_json,fingerprint,write_packet,read_packet,score_saved_packet,reporter
from common_view.sapiens_route import prepare_rgb,logits_to_native,ownership_planes
from cihp_benchmark.data import read_image


def utc():return datetime.now(timezone.utc).isoformat()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    cp=Path(args.config).resolve();config=json.loads(cp.read_text());raw=W/config['artifact_root'];record=W/config['record_root']
    if (raw/'RUN.json').exists():raise RuntimeError('A pilot attempt already exists; no automatic restart/resume')
    state={'run_id':config['run_id'],'status':'INITIALIZING','pid':os.getpid(),'process_group':os.getpgrp(),
           'start_utc':utc(),'resource_policy':'SHARED_GPU_QUALITY_ONLY','model_id':'Sapiens2_0.4b',
           'model_frame_calls':0,'expected_diagnostic_ids':config['pilot_ids'],'complete_ids':[],
           'failed':0,'invalid':0,'model_retries':0,'fallback_used':False,'full_population_primary':None,
           'launch_command':[sys.executable,str(Path(__file__).relative_to(W)),'--config',str(cp.relative_to(W))],
           'launch_public_commit':subprocess.check_output(['git','-C',str(W/'Human_Parsing_Study_Public'),'rev-parse','HEAD'],text=True).strip(),
           'config_sha256':sha_file(cp),'protocol_sha256':config['protocol_sha256']}
    atomic_json(raw/'RUN.json',state);start=time.monotonic();rows=[];stage='GATE';attempt=None
    ledger=(raw/'EXECUTION.jsonl').open('x',buffering=1)
    model=None
    try:
        readiness=json.loads((raw/'READINESS.json').read_text());cpu=json.loads((raw/'CPU_ACCEPTANCE.json').read_text())
        assert readiness['status']=='PASS_PRE_FORWARD_READINESS' and cpu['status']=='PASS'
        assert readiness['config_sha256']==sha_file(cp)
        assert readiness['CPU_acceptance_sha256']==sha_file(raw/'CPU_ACCEPTANCE.json')
        for f,digest in readiness['source_hashes'].items():assert sha_file(W/f)==digest,f
        assert config['pilot_ids']==['0021448','0006909','0001538','0001413','0027897','0031248']
        assert config['max_model_frame_calls']==7 and not config['full_common_evaluation']
        ck=W/config['model']['checkpoint'];st=ck.stat()
        assert {'size':st.st_size,'mtime_ns':st.st_mtime_ns}==readiness['checkpoint_stat']
        spec=load_spec(W/config['protocol']);assert sha_file(W/config['protocol'])==config['protocol_sha256']
        for f,digest in config['native_preserved'].items():assert sha_file(W/f)==digest,f
        binding={json.loads(l)['image_id']:json.loads(l) for l in (raw/'gt_bindings/BINDINGS.jsonl').read_text().splitlines()}
        assert sha_file(raw/'gt_bindings/BINDINGS.jsonl')==readiness['GT_manifest_sha256']
        pop={r['id']:r for r in json.loads((W/config['native_population']).read_text())['members']}
        detector={r['image_id']:r for r in map(json.loads,(W/config['YOLO']['validation_ledger']).open())}
        tr=json.loads((W/config['YOLO']['training_run']).read_text());train=next(r for r in tr['images'] if r['image_id']==config['warmup_id'])
        sample=json.loads((P/'runs/cihp-native-six-20261028T034103254470Z/presentation-four-20261028T184321049969Z/VISUALIZATION_MANIFEST.json').read_text())
        qanet={r['image_id']:next(p for p in r['packets'] if p['model_id']=='QANet_CIHP_HRNetW48_512x384') for r in sample['records']}
        extent_parity=[]
        import torch
        from safetensors.torch import load_file
        from sapiens.dense.models import init_model
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        stage='MODEL_LOAD'
        model=init_model(W/config['model']['native_config'],checkpoint=None,device='cpu')
        weights=load_file(ck,device='cpu');model.load_state_dict(weights,strict=True);del weights
        model.float().eval().cuda()
        assert not model.training and all(p.dtype==torch.float32 for p in model.parameters())
        assert model.cfg.model_name=='sapiens2_0.4b' and model.cfg.num_classes==29
        assert not torch.is_autocast_enabled('cuda')
        state['parameters']=sum(p.numel() for p in model.parameters());state['strict_load']='PASS'
        atomic_json(raw/'RUN.json',state)

        def guard():
            if sha_file(cp)!=state['config_sha256'] or sha_file(W/config['protocol'])!=state['protocol_sha256']:
                raise RuntimeError('Configuration/protocol changed')
            for f,digest in readiness['source_hashes'].items():assert sha_file(W/f)==digest,f
            current=ck.stat();assert {'size':current.st_size,'mtime_ns':current.st_mtime_ns}==readiness['checkpoint_stat']
            retained=sum(f.stat().st_size for f in raw.rglob('*') if f.is_file())
            if retained>config['max_stream_gib']*2**30:raise RuntimeError('Streamstorage guard')
            if shutil.disk_usage(raw).free<config['minimum_free_gib']*2**30+64*2**20:raise RuntimeError('Free-space guard')
            if time.monotonic()-start>config['max_hours']*3600:raise RuntimeError('Time guard')
            free,_=torch.cuda.mem_get_info(0)
            if free<=0:raise RuntimeError('No free CUDA memory')

        for warmup,iid in [(True,config['warmup_id'])]+[(False,i) for i in config['pilot_ids']]:
            stage='SOURCE_BINDINGS';guard()
            attempt={'image_id':iid,'split':'Training' if warmup else 'Validation','warmup':warmup,
                     'attempt':1,'start_utc':utc(),'status':'STARTED'}
            ledger.write(json.dumps(attempt)+'\n');ledger.flush();os.fsync(ledger.fileno())
            base=W/'datasets/CIHP'/attempt['split'];rgb,imeta=read_image(base/'Images'/(iid+'.jpg'))
            h,w=rgb.shape[:2];d=train if warmup else detector[iid]
            expected_input=d['rgb_source_sha256'] if warmup else pop[iid]['RGB_sha256']
            assert imeta['file_sha256']==expected_input
            assert list(d.get('original_wh',d.get('wh')))==[w,h]
            detpath=W/'Human_Parsing_MHPv2_Study'/d['artifact']
            assert sha_file(detpath)==d['artifact_sha256']
            with np.load(detpath,allow_pickle=False) as z:extents=z['masks'].copy()
            assert extents.dtype==bool and extents.shape==(len(d['opportunities']),h,w)
            keep=[j for j,e in enumerate(extents) if e.any()]
            extents=extents[keep];ops=[d['opportunities'][j] for j in keep]
            confidence=np.array([op['score'] for op in ops],np.float32)
            stage='PREPROCESS'
            tensor,geometry=prepare_rgb(rgb,model.pipeline,model.data_preprocessor)
            tensor=tensor.cuda()
            attempt['geometry']=geometry;state['current_image']=iid;state['current_stage']=stage
            atomic_json(raw/'CURRENT_ATTEMPT.json',attempt)
            stage='MODEL_FORWARD'
            if state['model_frame_calls']>=7:raise RuntimeError('Callbudget exhausted')
            state['model_frame_calls']+=1;state['current_stage']=stage;atomic_json(raw/'RUN.json',state)
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();begin=time.perf_counter()
            with torch.inference_mode():
                logits=model(tensor)
                stage='MAPBACK_CONTRACT'
                native=logits_to_native(logits,(h,w))
            torch.cuda.synchronize();seconds=time.perf_counter()-begin
            memory={'peak_allocated_MiB':torch.cuda.max_memory_allocated()/2**20,
                    'peak_reserved_MiB':torch.cuda.max_memory_reserved()/2**20,
                    'device_free_MiB_after':torch.cuda.mem_get_info(0)[0]/2**20}
            attempt.update(model_forward_and_mapback_seconds_diagnostic=seconds,**memory)
            del tensor,logits
            if warmup:
                attempt.update(status='COMPLETE_WARMUP_NOT_SCORED',end_utc=utc())
                ledger.write(json.dumps(attempt)+'\n');ledger.flush();os.fsync(ledger.fileno())
                state['warmup']='PASS';atomic_json(raw/'WARMUP.json',attempt);atomic_json(raw/'RUN.json',state)
                print('Warmup PASS, model calls',state['model_frame_calls'],flush=True);continue
            stage='SCORING'
            category,cmeta=read_image(base/'Category_ids'/(iid+'.png'),True)
            human,hmeta=read_image(base/'Human_ids'/(iid+'.png'),True)
            assert cmeta['file_sha256']==binding[iid]['GT_sha256']['Category_ids']
            assert hmeta['file_sha256']==binding[iid]['GT_sha256']['Human_ids']
            _,_,_,bound=gt_domains(category,human,spec)
            for key in ['projected_sha256','valid_sha256','person_valid_sha256','G_loc','G_sem_C4']:
                assert bound[key]==binding[iid][key],key
            a=ownership_planes(native,extents,confidence)
            a['bboxes_xyxy']=np.array([op['bbox'] for op in ops],np.float32).reshape(-1,4)
            scores={str(t):score_packet(category,human,a['person_semantic_masks'],extents,confidence,'SAPIENS2_DOME29_PRED',spec,t) for t in (.5,.75)}
            stage='QANET_EXTENT_PARITY'
            qp=W/qanet[iid]['packet'];qmeta,qa=read_packet(qp,{'image_id':iid,'model_id':'QANet_CIHP_HRNetW48_512x384','input_sha256':expected_input},legacy=True)
            assert np.array_equal(qa['person_extents'],extents),'QANet/frozenYOLO extent contract mismatch'
            parity={}
            for t in (.5,.75):
                qsc=score_packet(category,human,qa['person_semantic_masks'],qa['person_extents'],qa['person_scores'],'CIHP_GT_AND_NATIVE_PRED',spec,t)
                fields=['TP','FP','FN','extent_F1','G_loc','G_sem_C4']
                assert all(qsc[k]==scores[str(t)][k] for k in fields),'QANet/common extent metrics differ'
                parity[str(t)]={k:scores[str(t)][k] for k in fields}
            extent_parity.append({'image_id':iid,'identical_cached_extent_arrays':True,'scores':parity,
                                  'QANet_packet_sha256':qmeta['packet_sha256'],'QANet_source_packet':qanet[iid]['packet']})
            stage='ATOMIC_EXPORT'
            bind={'model_id':'Sapiens2_0.4b','checkpoint_sha256':readiness['checkpoint_sha256'],
                  'input_sha256':expected_input,'detector_artifact_sha256':d['artifact_sha256'],
                  'protocol_sha256':config['protocol_sha256'],'config_sha256':state['config_sha256'],
                  'source_hashes':readiness['source_hashes'],'route':config['route'],'precision':config['precision']}
            meta=dict(image_id=iid,model_id='Sapiens2_0.4b',source_commit=config['model']['source_commit'],
                      checkpoint_sha256=readiness['checkpoint_sha256'],input_sha256=expected_input,
                      config_sha256=state['config_sha256'],protocol_sha256=config['protocol_sha256'],
                      inference_fingerprint=fingerprint(bind),scoring_fingerprint=fingerprint(dict(binding=binding[iid],inference=bind)),
                      environment_sha256=readiness['environment_sha256'],detector_artifact_sha256=d['artifact_sha256'],
                      detector_opportunity_ids=[op['id'] for op in ops],native_person_identity_supported=False,
                      native_instance_count=None,person_score_type='FROZEN_YOLO_DETECTOR_CONFIDENCE_NOT_SEMANTIC_PROBABILITY',
                      geometry=geometry,original_wh=[w,h],GT_used_in_prediction=False,label_space='SAPIENS2_DOME29_PRED',
                      resource_policy='SHARED_GPU_QUALITY_ONLY',resource_observation=memory,
                      precision='FP32_NO_AMP_NO_TF32',fallback_used=False)
            packet=write_packet(raw/'packets',iid,a,meta,scores)
            stage='PACKET_READBACK'
            reread=score_saved_packet(packet,category,human,'SAPIENS2_DOME29_PRED',spec,
                                     expected={'protocol_sha256':config['protocol_sha256'],'model_id':'Sapiens2_0.4b'})
            assert reread['scores']==scores,'Saved-mask rescore disagreement'
            rows.append(reread);state['complete_ids'].append(iid)
            attempt.update(status='COMPLETE',packet=str(packet.relative_to(W)),packet_sha256=sha_file(packet/'prediction.npz'),end_utc=utc())
            ledger.write(json.dumps(attempt)+'\n');ledger.flush();os.fsync(ledger.fileno())
            atomic_json(raw/'RUN.json',state);atomic_json(raw/'EXTENT_PARITY.json',extent_parity)
            print('Pilot packet COMPLETE',iid,len(rows),'/6, calls',state['model_frame_calls'],flush=True)
        stage='CLOSURE';assert state['model_frame_calls']==7
        reporter(raw/'METRICS_DIAGNOSTICS.json',rows,config['pilot_ids'])
        from render_common_pilot import render
        figures=render(raw,spec,state['complete_ids'])
        for f,digest in config['native_preserved'].items():assert sha_file(W/f)==digest,f
        assert state['complete_ids']==config['pilot_ids']
        state.update(status='PILOT_PASS',artifact_validation='PASS',saved_mask_rescore='PASS',
                     QANet_extent_parity='PASS_6_IMAGES_BOTH_THRESHOLDS',native_immutability='PASS',figures=len(figures))
    except Exception:
        state.update(status='STOPPED_INCOMPLETE',stop_stage=stage,error=traceback.format_exc())
        state['failed' if stage=='MODEL_FORWARD' else 'invalid']+=1
        if attempt:
            fail=dict(attempt,status='FAILED' if stage=='MODEL_FORWARD' else 'INVALID',failure_stage=stage,
                      error=state['error'],end_utc=utc())
            ledger.write(json.dumps(fail)+'\n');ledger.flush();os.fsync(ledger.fileno())
            atomic_json(raw/'FAILURE.json',fail)
        if rows:reporter(raw/'METRICS_DIAGNOSTICS.json',rows,config['pilot_ids'])
    finally:
        state.update(end_utc=utc(),queue_stopped=True,total_elapsed_seconds=time.monotonic()-start,
                     expected=6,complete=len(state['complete_ids']),not_attempted=6-len(state['complete_ids'])-int(attempt is not None and not attempt.get('warmup',True) and state['status']!='PILOT_PASS'),
                     timing_ranking_allowed=False,next_model_started=False)
        atomic_json(raw/'RUN.json',state);atomic_json(record/'PILOT_COMPLETION.json',state)
        for name in ['METRICS_DIAGNOSTICS.json','EXTENT_PARITY.json']:
            if (raw/name).exists():atomic_json(record/name,json.loads((raw/name).read_text()))
        ledger.close()
        print('Terminal',state['status'],'calls',state['model_frame_calls'],'complete',state['complete'],flush=True)
    return 0 if state['status']=='PILOT_PASS' else 1

if __name__=='__main__':raise SystemExit(main())
