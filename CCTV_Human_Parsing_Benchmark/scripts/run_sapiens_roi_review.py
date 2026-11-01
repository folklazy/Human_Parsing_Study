"""Sequential, bounded three-size Sapiens measurement review. No full benchmark.

One worker per checkpoint, immutable fresh outputs, no retry or fallback.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback

P=Path(__file__).resolve().parents[1]; W=P.parent


def read(p): return json.loads(Path(p).read_text())


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def utc(): return datetime.now(timezone.utc).isoformat()


def atomic(path,value):
    tmp=Path(str(path)+'.tmp')
    with tmp.open('w') as f:
        json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def worker(cp,mid):
    import numpy as np
    import torch
    from PIL import Image
    sys.path[:0]=[str(W/'Human_Parsing_Benchmark/src'),str(P/'scripts')]
    from common_view.sapiens_route import prepare_rgb,logits_to_native
    from common_view.core import validate_prediction
    from common_view.packets import write_packet,read_packet
    from sapiens_input_variants import letterbox,restore_letterbox,detector_crop,place_roi
    from review_saved_sapiens import confusion_counts,TARGETS,table
    c=read(cp);parent=read(W/c['parent_config']);m=parent['models'][mid];base=W/c['artifact_root'];root=base/mid
    root.mkdir(exist_ok=False);start=time.monotonic();s=dict(model_id=mid,status='INITIALIZING',pid=os.getpid(),started_utc=utc(),model_calls=0,max_model_calls=17,complete_frames=0,expected_frames=6)
    ledger=(root/'ATTEMPTS.jsonl').open('x',buffering=1);scores=[];observations=[]
    def save():atomic(root/'STATE.json',s)
    def event(row):ledger.write(json.dumps(dict(utc=utc(),**row))+'\n');ledger.flush();os.fsync(ledger.fileno())
    def guard():
        if shutil.disk_usage(base).free<50*2**30:raise RuntimeError('FREE_DISK_GUARD')
        if sum(p.stat().st_size for p in base.rglob('*') if p.is_file())>5*2**30:raise RuntimeError('REVIEW_5GiB_GUARD')
        if time.monotonic()-start>3600:raise RuntimeError('MODEL_1h_GUARD')
        if any(sha(W/p)!=h for p,h in c['source_hashes'].items()):raise RuntimeError('SOURCE_DRIFT')
    def forward(t,purpose,iid):
        guard()
        if s['model_calls']>=17:raise RuntimeError('CALL_BUDGET')
        if t.shape!=(1,3,1024,768) or t.dtype!=torch.float32 or not torch.isfinite(t).all():raise ValueError('INPUT_CONTRACT')
        if torch.cuda.mem_get_info(0)[0]<1024*2**20:raise RuntimeError('VRAM_HEADROOM_GUARD')
        assert not model.training and not torch.is_autocast_enabled()
        s.update(status='FORWARD',purpose=purpose,current_id=iid);s['model_calls']+=1;save();event(dict(event='FORWARD_START',call=s['model_calls'],purpose=purpose,image_id=iid))
        torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
        with torch.inference_mode():out=model(t.cuda())
        torch.cuda.synchronize()
        if out.shape[:2]!=(1,29) or out.dtype!=torch.float32 or not torch.isfinite(out).all():raise ValueError('OUTPUT_CONTRACT')
        observations.append(dict(purpose=purpose,peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,peak_reserved_MiB=torch.cuda.max_memory_reserved()/2**20))
        event(dict(event='FORWARD_END',call=s['model_calls'],purpose=purpose,image_id=iid));return out
    save()
    try:
        guard();assert sha(W/c['parent_config'])==c['parent_config_sha256'] and sha(W/c['GT_binding'])==c['GT_binding_sha256']
        free=float(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).splitlines()[0])
        if free<parent['required_free_MiB'][mid]:raise RuntimeError('PRELOAD_FREE_VRAM_GUARD')
        assert sha(W/m['checkpoint'])==m['checkpoint_sha256'] and sha(W/m['native_config'])==m['native_config_sha256']
        assert subprocess.check_output(['git','-C',str(W/m['source']),'rev-parse','HEAD'],text=True).strip()==m['source_commit']
        assert subprocess.check_output(['git','-C',str(W/m['source']),'status','--porcelain'],text=True)==''
        torch.set_num_threads(2);torch.manual_seed(parent['seed']);np.random.seed(parent['seed'])
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        from sapiens.dense.models import init_model
        from safetensors.torch import load_file
        model=init_model(W/m['native_config'],checkpoint=None,device='cpu')
        assert model.cfg.model_name==mid.replace('Sapiens2_','sapiens2_') and model.cfg.num_classes==29
        weights=load_file(W/m['checkpoint'],device='cpu');model.load_state_dict(weights,strict=True);del weights
        model.float().eval().cuda();assert all(p.dtype==torch.float32 for p in model.parameters())
        atomic(root/'ENVIRONMENT.json',dict(python=sys.version,torch=torch.__version__,CUDA=torch.version.cuda,GPU=torch.cuda.get_device_name(0),parameters=sum(p.numel() for p in model.parameters()),AMP=False,TF32=False,model_training=model.training))
        rgb=np.array(Image.open(W/'datasets/CIHP/Training/Images/0000930.jpg').convert('RGB'));t,_=prepare_rgb(rgb,model.pipeline,model.data_preprocessor);out=forward(t,'TRAIN_WARMUP','TRAIN0000930');del t,out
        binding=read(W/c['GT_binding']);matches={(r['image_id'],r['person_id']):r['YOLO_opportunity_id'] for r in binding['matches']}
        oldroot=(W/c['parent_config']).parent
        for index,iid in enumerate(c['image_ids']):
            sample=next(x for x in parent['members'] if x['id']==iid);image=W/parent['dataset_root']/'Images'/(sample['stem']+'.jpg');assert sha(image)==sample['RGB_sha256']
            rgb=np.array(Image.open(image).convert('RGB'));h,w=rgb.shape[:2]
            oldmeta,olda=read_packet(oldroot/mid/'packets'/iid)
            assert oldmeta['checkpoint_sha256']==m['checkpoint_sha256'] and oldmeta['input_sha256']==sample['RGB_sha256']
            if index==0:
                t,g=prepare_rgb(rgb,model.pipeline,model.data_preprocessor);out=forward(t,'FRESH_FULL_FRAME_CONTROL',iid);native=logits_to_native(out,(h,w))
                disagreement=float(np.mean(native!=olda['native_full_frame_semantic_mask']))
                np.save(root/'CONTROL_NATIVE29.npy',native)
                atomic(root/'CONTROL.json',dict(native_disagreement_fraction=disagreement,guard_max_disagreement_fraction=c['control_max_disagreement_fraction'],source_packet_sha256=oldmeta['packet_sha256'],input_geometry=g))
                del out,t
                if disagreement>c['control_max_disagreement_fraction']:raise RuntimeError('FRESH_BASELINE_REPRODUCTION_DRIFT')
            det=oldroot/'YOLO26X/packets'/iid;dm=read(det/'COMMIT.json');assert sha(det/'detector.npz')==oldmeta['detector_sha256']==dm['artifact_sha256']
            with np.load(det/'detector.npz') as z:extents,conf=z['masks'],z['scores']
            assert np.array_equal(extents,olda['person_extents']) and np.array_equal(conf,olda['person_scores'])
            raw=[];owned=[];geometry=[]
            for j,op in enumerate(dm['opportunities']):
                crop,box=detector_crop(rgb,op['bbox'],extents[j],c['ROI_context_each_side']);t,g,preview=letterbox(crop,model.data_preprocessor)
                out=forward(t,'ROI:'+str(j),iid);mask=restore_letterbox(out,g);r,o=place_roi(mask,box,extents[j]);raw.append(r);owned.append(o);geometry.append(dict(opportunity_id=op['id'],crop_xyxy=box,**g));del t,out
            arrays=dict(native_roi_unowned_semantic_masks=np.asarray(raw,np.uint8).reshape(-1,h,w),person_semantic_masks=np.asarray(owned,np.uint8).reshape(-1,h,w),person_extents=extents,person_scores=conf)
            validate_prediction(arrays['person_semantic_masks'],extents,conf,(h,w),'SAPIENS2_DOME29_PRED')
            meta=dict(model_id=mid,image_id=iid,input_sha256=sample['RGB_sha256'],checkpoint_sha256=m['checkpoint_sha256'],native_config_sha256=m['native_config_sha256'],source_commit=m['source_commit'],geometry=geometry,original_wh=[w,h],label_space='SAPIENS2_DOME29_PRED',precision='FP32',route='YOLO_ROI_LETTERBOX',diagnostic_config_sha256=sha(cp),detector_sha256=dm['artifact_sha256'],source_full_frame_packet_sha256=oldmeta['packet_sha256'],GT_used_in_prediction=False)
            packet=write_packet(root/'packets',iid,arrays,meta,{})
            _,a=read_packet(packet)
            catpath,hupath=[W/parent['dataset_root']/k/(sample['stem']+'.png') for k in ['Category_ids','Human_ids']]
            assert sha(catpath)==sample['GT_sha256']['Category_ids'] and sha(hupath)==sample['GT_sha256']['Human_ids']
            cat,human=np.array(Image.open(catpath)),np.array(Image.open(hupath));lookup={op['id']:j for j,op in enumerate(dm['opportunities'])};rr=[]
            for part in binding['part_records']:
                if not part['primary_eligible'] or part['image_id']!=iid:continue
                gt_id,native_ids=TARGETS[part['target']];gt=(human==part['person_id'])&(cat==gt_id);j=lookup.get(matches[iid,part['person_id']]);pred=np.isin(a['person_semantic_masks'][j],native_ids) if j is not None else np.zeros(gt.shape,bool)
                tp,fp,fn=confusion_counts(gt,pred);rawpred=np.isin(a['native_roi_unowned_semantic_masks'][j],native_ids) if j is not None else pred;rtp,rfp,rfn=confusion_counts(gt,rawpred)
                assert rtp>=tp and rfp>=fp
                rr.append(dict(image_id=iid,person_id=part['person_id'],target=part['target'],condition=sample['condition'],GT_pixels=int(gt.sum()),TP=tp,FP=fp,FN=fn,IoU=tp/(tp+fp+fn),Dice=2*tp/(2*tp+fp+fn),detector_miss=j is None,unclipped_ROI_TP=rtp,unclipped_ROI_FP=rfp,unclipped_ROI_FN=rfn,TP_removed_by_YOLO_clipping=rtp-tp,FP_removed_by_YOLO_clipping=rfp-fp))
            atomic(packet/'REVIEW_SCORES.json',dict(parts=rr,GT_sha256=sample['GT_sha256']));scores.extend(rr)
            if mid=='Sapiens2_0.4b':
                earlier=W/c['previous_ROI_04_root']/'YOLO_ROI_LETTERBOX/packets'/iid/'prediction.npz'
                with np.load(earlier) as z:prior=z['person_semantic_masks']
                s.setdefault('ROI_repeatability',[]).append(dict(image_id=iid,changed_owned_pixels=int(((a['person_semantic_masks']!=prior)&extents).sum()),owned_pixels=int(extents.sum())))
            s['complete_frames']+=1;s['status']='FRAME_COMMITTED';save();event(dict(event='FRAME_COMMITTED',image_id=iid))
        if s['model_calls']!=17 or s['complete_frames']!=6 or len(scores)!=31:raise RuntimeError('WORKLOAD_RECONCILIATION')
        rows=[]
        for target in TARGETS:
            r=[x for x in scores if x['target']==target];tp,fp,fn=[sum(x[k] for x in r) for k in ['TP','FP','FN']]
            rows.append(dict(model_id=mid,target=target,GT_parts=len(r),mean_part_IoU=float(np.mean([x['IoU'] for x in r])),mean_part_Dice=float(np.mean([x['Dice'] for x in r])),pooled_part_IoU=tp/(tp+fp+fn),TP=tp,FP=fp,FN=fn,GT_pixels=tp+fn,detector_miss_parts=sum(x['detector_miss'] for x in r),TP_removed_by_YOLO_clipping=sum(x['TP_removed_by_YOLO_clipping'] for x in r),FP_removed_by_YOLO_clipping=sum(x['FP_removed_by_YOLO_clipping'] for x in r)))
        table(root/'PER_TARGET.csv',rows);atomic(root/'RESOURCE_OBSERVATIONS.json',observations)
        atomic(root/'METRICS.json',dict(scope='DIAGNOSTIC_SIX_IMAGES_ONLY',macro_mean_part_IoU4=float(np.mean([r['mean_part_IoU'] for r in rows])),macro_mean_part_Dice4=float(np.mean([r['mean_part_Dice'] for r in rows])),images=6,GT_parts=31,per_target=rows))
        s.update(status='COMPLETE_DIAGNOSTIC',ended_utc=utc(),failed=0,invalid=0)
    except BaseException:
        s.update(status='STOPPED_INCOMPLETE',ended_utc=utc(),error=traceback.format_exc());atomic(root/'FAILURE.json',s);raise
    finally:save();ledger.close()


def controller(cp):
    c=read(cp);root=W/c['artifact_root'];lock=(P/'outputs/SAPIENS_ROI_REVIEW.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (root/'CONTROLLER.json').exists():raise FileExistsError('Existing controller attempt')
    record=dict(status='RUNNING',pid=os.getpid(),started_utc=utc(),completed_models=0)
    atomic(root/'CONTROLLER.json',record)
    for mid in c['models']:
        path=root/mid
        if path.exists():raise FileExistsError('Existing model attempt; reconcile explicitly')
        command=[str(W/'.venvs/sapiens2-pilot/bin/python'),'-u',str(Path(__file__)),'--config',str(cp),'--worker',mid]
        env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (root/(mid+'.log')).open('xb') as log:
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env)
            atomic(root/'CURRENT_WORKER.json',dict(model_id=mid,pid=child.pid,command=command));child.wait()
        state=read(path/'STATE.json') if (path/'STATE.json').exists() else dict(status='SETUP_FAILED',returncode=child.returncode)
        record.setdefault('models',{})[mid]=state['status'];record['completed_models']+=int(state['status']=='COMPLETE_DIAGNOSTIC');atomic(root/'CONTROLLER.json',record)
    record.update(status='STOPPED_AFTER_THREE_SAPIENS',ended_utc=utc());atomic(root/'CONTROLLER.json',record)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--config',type=Path,required=True);ap.add_argument('--worker');ap.add_argument('--status',action='store_true');a=ap.parse_args()
    if a.status:
        c=read(a.config);root=W/c['artifact_root'];print(json.dumps(read(root/'CONTROLLER.json'),indent=2))
        for mid in c['models']:
            f=root/mid/'STATE.json';print(mid,json.dumps(read(f)) if f.exists() else 'NOT_STARTED')
    elif a.worker:worker(a.config,a.worker)
    else:controller(a.config)
