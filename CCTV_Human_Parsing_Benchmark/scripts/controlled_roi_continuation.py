"""Bounded engineering continuation; accepted parent ROIs are never inferred again.

Only empty RP-R-CNN decoding and reusable-memory accounting differ. This is not
an automatic model/OOM retry loop and never edits a running parent's source.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import numpy as np
from PIL import Image
from controlled_roi_core import atomic, read, sha, pixel_sha, select_instance, place, reconcile, validate_native

P=Path(__file__).resolve().parents[1];W=P.parent
sys.path[:0]=[str(W/'Human_Parsing_Benchmark/src'),str(P/'scripts')]
from common_view.packets import read_packet,write_packet


def utc():return datetime.now(timezone.utc).isoformat()


def reusable_memory(free, allocated, reserved):
    if min(free,allocated,reserved)<0 or reserved<allocated:
        raise ValueError('Invalid device/process memory accounting')
    return dict(device_free_bytes=int(free),allocated_bytes=int(allocated),reserved_bytes=int(reserved),
                own_reusable_pool_bytes=int(reserved-allocated),effective_available_bytes=int(free+reserved-allocated),
                contiguous_allocation_guaranteed=False)


def empty_rpr_prediction(prediction, hw):
    if len(prediction)==0:
        return np.empty((0,*hw),np.uint8),np.empty((0,4),float),np.empty(0,np.float32)
    if not prediction.has_field('parsing'):
        raise ValueError('Nonempty native RP-R-CNN result lacks parsing: contract failure')
    return None


def continuation_model(workspace, spec, output):
    from controlled_roi_models import CropModel
    class RPREmptySafe(CropModel):
        def infer(self,rgb,image,designated):
            if self.family!='RP-R-CNN':return super().infer(rgb,image,designated)
            from rcnn.core.test import im_detect_bbox,im_detect_parsing
            from rcnn.modeling.parsing_rcnn.inference import parsing_results
            torch=self.torch;h,w=rgb.shape[:2]
            with torch.no_grad():
                boxes,features=im_detect_bbox(self.model,[rgb[:,:,::-1].copy()])
                pred=im_detect_parsing(self.model,boxes,features)[0].to('cpu').resize((w,h))
                empty=empty_rpr_prediction(pred,(h,w))
                if empty is not None:
                    candidates,boxes,scores=empty
                else:
                    parsing=pred.get_field('parsing');parsing=parsing.cpu().numpy() if torch.is_tensor(parsing) else np.asarray(parsing)
                    sem=pred.get_field('semseg') if pred.has_field('semseg') else None
                    if torch.is_tensor(sem):sem=sem.cpu().numpy()
                    candidates=np.asarray(parsing_results(parsing,pred,sem),np.uint8).reshape(-1,h,w)
                    boxes=pred.bbox.numpy();scores=pred.get_field('scores').cpu().numpy()
            usable=[i for i,a in enumerate(candidates) if (a>0).any()]
            chosen,overlaps=select_instance(boxes[usable],scores[usable],designated)
            index=usable[chosen] if chosen is not None else None
            native=candidates[index] if index is not None else np.zeros((h,w),np.uint8)
            validate_native(native,20,(h,w))
            return native,candidates,dict(selection='NATIVE_INSTANCE' if index is not None else 'NATIVE_ASSOCIATION_MISS',
                native_raw_person_count=len(pred),native_selected_index=index,native_boxes=boxes.tolist(),native_scores=scores.tolist(),
                bbox_IoUs=overlaps,implementation='RPR_ROI_EMPTY_OUTPUT_1',empty_is_valid_prediction=True)
    return RPREmptySafe(workspace,spec,output)


def worker(cp,mid):
    import torch
    from common_view.core import validate_prediction
    c=read(cp);parentcp=W/c['parent_config'];parent=read(parentcp);parentroot=W/parent['artifact_root'];root=W/c['artifact_root'];out=root/mid;out.mkdir(exist_ok=False)
    lock=(P/'outputs/CONTROLLED_ROI_GPU_WORKER.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    spec=parent['models'][mid];manifest=read(W/parent['manifest']);jobs={j['job_id']:j for j in manifest['jobs']};accepted={};new=[];observations=[]
    s=dict(model_id=mid,status='RECONCILING_PARENT',pid=os.getpid(),started_utc=utc(),complete_ROIs=0,complete_frames=0,reused_ROIs=0,new_ROIs=0,
        model_ROI_API_calls=0,primary=None,scoring_status='WAITING_REVIEWED_GT')
    log=(out/'ATTEMPTS.jsonl').open('x',buffering=1);start=time.monotonic()
    def save():atomic(out/'STATE.json',s)
    def event(**value):log.write(json.dumps(dict(utc=utc(),**value))+'\n');log.flush();os.fsync(log.fileno())
    def guard():
        for path,digest in c['source_hashes'].items():
            if sha(W/path)!=digest:raise ValueError('Continuation source drift: '+path)
        if sha(parentcp)!=c['parent_config_sha256']:raise ValueError('Parent config changed')
        if sha(W/parent['manifest'])!=parent['manifest_sha256']:raise ValueError('Shared input manifest changed')
        if shutil.disk_usage(root).free<50*2**30:raise RuntimeError('FREE_DISK_GUARD')
        size=sum(p.stat().st_size for d in [parentroot/mid,out] for p in d.rglob('*') if p.is_file())
        if size>80*2**30:raise RuntimeError('AGGREGATE_CHECKPOINT_STREAM_80GiB_GUARD')
        if time.monotonic()-start+c['parent_execution_seconds'][mid]>24*3600:raise RuntimeError('AGGREGATE_CHECKPOINT_24h_GUARD')
    def forward(job_id,rgb,image,box,purpose):
        guard();memory=reusable_memory(torch.cuda.mem_get_info(0)[0],torch.cuda.memory_allocated(),torch.cuda.memory_reserved())
        if memory['effective_available_bytes']<1024*2**20:raise RuntimeError('EFFECTIVE_HEADROOM_1GiB_GUARD')
        if s['model_ROI_API_calls']>=len(pending)+1:raise RuntimeError('CONTINUATION_CALL_CAP')
        s.update(status=purpose,current_job=job_id);s['model_ROI_API_calls']+=1;save();event(event='FORWARD_START',job_id=job_id,purpose=purpose,memory=memory)
        torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
        value=model.infer(rgb,image,box);torch.cuda.synchronize()
        observations.append(dict(job_id=job_id,purpose=purpose,memory_before=memory,peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,peak_reserved_MiB=torch.cuda.max_memory_reserved()/2**20))
        atomic(out/'RESOURCE_OBSERVATIONS.json',observations);event(event='FORWARD_END',job_id=job_id,purpose=purpose);return value
    save()
    try:
        guard();prior=read(parentroot/mid/'FAILURE.json');error=prior['error']
        if not (error.rstrip().endswith("KeyError: 'parsing'") if mid=='RPR_CIHP' else error.rstrip().endswith('RuntimeError: PRE_FORWARD_HEADROOM_GUARD')):
            raise ValueError('Unapproved failure cause: no model/OOM retry')
        for packet in sorted((parentroot/mid/'roi_packets').iterdir()):
            if packet.name.startswith('.'):raise ValueError('Orphan parent ROI; reconcile manually')
            meta,a=read_packet(packet);job=jobs[packet.name]
            if any(meta.get(k)!=v for k,v in dict(model_id=mid,config_sha256=c['parent_config_sha256'],checkpoint_sha256=spec['checkpoint_sha256'],crop_pixel_sha256=job['crop_pixel_sha256'],detector_sha256=job['detector_sha256']).items()):
                raise ValueError('Parent ROI scientific binding mismatch')
            frozen=c['parent_accepted_fingerprints'][mid].get(packet.name)
            if frozen!=dict(packet_sha256=meta['packet_sha256'],metadata_sha256=sha(packet/'packet.json'),commit_sha256=sha(packet/'COMMIT.json')):
                raise ValueError('Parent ROI differs from frozen continuation reconciliation')
            validate_native(a['native_crop_mask'],20,job['crop_hw']);accepted[packet.name]=packet
        reused=set(accepted);pending=[j for j in manifest['jobs'] if j['job_id'] not in reused]
        if reused!=set(c['parent_accepted_fingerprints'][mid]):raise ValueError('Parent reused membership changed')
        s.update(complete_ROIs=len(accepted),reused_ROIs=len(accepted));save()
        atomic(out/'FROZEN_RECONCILIATION.json',dict(reused=sorted(reused),pending=[j['job_id'] for j in pending],
            parent_failure_sha256=sha(parentroot/mid/'FAILURE.json'),source_implementation=c['implementation'][mid],
            original_history_retained=True,automatic_model_OOM_retry=0,max_new_ROI_API_calls=len(pending)+1))
        free=float(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).splitlines()[0])
        if free<parent['required_free_MiB'][mid]:raise RuntimeError('UNCHANGED_PRELOAD_FREE_VRAM_GUARD')
        if sha(W/spec['checkpoint'])!=spec['checkpoint_sha256'] or sha(W/spec['native_config'])!=spec['native_config_sha256']:raise ValueError('Weights/config drift')
        if subprocess.check_output(['git','-C',str(W/spec['source']),'rev-parse','HEAD'],text=True).strip()!=spec['source_commit']:raise ValueError('Native revision drift')
        torch.set_num_threads(2);torch.manual_seed(parent['seed']);np.random.seed(parent['seed']);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        model=continuation_model(W,spec,out)
        atomic(out/'ENVIRONMENT.json',dict(torch=torch.__version__,CUDA=torch.version.cuda,python=sys.version,source_hashes=c['source_hashes'],AMP=False,TF32=False,FP32=True))
        warm=parent['warmup'];image=W/warm['image']
        if sha(image)!=warm['png_sha256']:raise ValueError('Warmup changed')
        forward('TRAIN0000930',np.asarray(Image.open(image).convert('RGB')),image,warm['designated_box'],'TRAIN_WARMUP')
        for job in pending:
            image=W/job['crop_png'];rgb=np.asarray(Image.open(image).convert('RGB'))
            if sha(image)!=job['crop_png_sha256'] or pixel_sha(rgb)!=job['crop_pixel_sha256']:raise ValueError('Crop identity drift')
            x0,y0,_,_=job['crop_xyxy'];b=job['bbox_xyxy'];box=[b[0]-x0,b[1]-y0,b[2]-x0,b[3]-y0]
            native,candidates,details=forward(job['job_id'],rgb,image,box,'ROI_INFERENCE')
            validate_native(native,20,job['crop_hw'])
            meta=dict(model_id=mid,job_id=job['job_id'],image_id=job['image_id'],opportunity_id=job['opportunity_id'],checkpoint_sha256=spec['checkpoint_sha256'],
                config_sha256=sha(cp),parent_config_sha256=c['parent_config_sha256'],crop_pixel_sha256=job['crop_pixel_sha256'],crop_xyxy=job['crop_xyxy'],
                detector_sha256=job['detector_sha256'],precision='FP32',native_classes=20,implementation=c['implementation'][mid],native_geometry_and_selection=details,GT_used_in_prediction=False)
            packet=write_packet(out/'roi_packets',job['job_id'],dict(native_crop_mask=native,native_candidate_masks=candidates),meta,{})
            _,data=read_packet(packet)
            if not np.array_equal(data['native_crop_mask'],native):raise ValueError('Continuation ROI readback')
            accepted[job['job_id']]=packet;new.append(job['job_id']);s.update(complete_ROIs=len(accepted),new_ROIs=len(new));save();event(event='ROI_COMMITTED',job_id=job['job_id'])
        checks=reconcile(list(jobs),list(accepted))
        if not checks['strict_complete']:raise ValueError('Assembled130ROI reconciliation')
        for frame in manifest['frames']:
            guard();w,h=frame['original_wh']
            if sha(W/frame['detector_npz'])!=frame['detector_sha256']:raise ValueError('Detector changed')
            with np.load(W/frame['detector_npz'],allow_pickle=False) as a:extents,scores,boxes=a['masks'],a['scores'],a['boxes']
            raw=[];owned=[];references=[]
            for job_id in frame['jobs']:
                job=jobs[job_id];meta,a=read_packet(accepted[job_id]);r,o=place(a['native_crop_mask'],job['crop_xyxy'],extents[job['opportunity_index']],20)
                raw.append(r);owned.append(o);references.append(dict(job_id=job_id,packet=str(accepted[job_id].relative_to(W)),packet_sha256=meta['packet_sha256'],implementation='PARENT_1' if job_id in reused else c['implementation'][mid]))
            arrays=dict(native_roi_unowned_semantic_masks=np.asarray(raw,np.uint8).reshape(-1,h,w),person_semantic_masks=np.asarray(owned,np.uint8).reshape(-1,h,w),person_extents=extents,person_scores=scores,bboxes_xyxy=boxes)
            validate_prediction(arrays['person_semantic_masks'],extents,scores,(h,w),'CIHP_GT_AND_NATIVE_PRED')
            meta=dict(model_id=mid,image_id=frame['image_id'],original_wh=[w,h],input_sha256=frame['input_sha256'],checkpoint_sha256=spec['checkpoint_sha256'],
                config_sha256=sha(cp),parent_config_sha256=c['parent_config_sha256'],detector_sha256=frame['detector_sha256'],precision='FP32',label_space='CIHP_GT_AND_NATIVE_PRED',
                protocol=parent['protocol'],route='CONTROLLED_YOLO_PERSON_ROI',roi_references=references,GT_used_in_prediction=False,
                associations=[dict(YOLO_opportunity_id=jobs[k]['opportunity_id'],prediction_index=j) for j,k in enumerate(frame['jobs'])])
            packet=write_packet(out/'packets',frame['image_id'],arrays,meta,{});_,a=read_packet(packet)
            if not np.array_equal(a['person_semantic_masks'],np.where(extents,a['native_roi_unowned_semantic_masks'],0)):raise ValueError('Ownership readback')
            s['complete_frames']+=1;save()
        s.update(status='PREDICTIONS_COMPLETE_SCORING_PENDING_GT',ended_utc=utc(),failed=0,invalid=0)
        atomic(out/'COMPLETION.json',dict(**checks,images=90,reused_ROIs=len(reused),new_ROIs=len(new),primary=None,
            historical_parent_failed_attempts=1,historical_failures_retained=True,implementation_counts={'PARENT_1':len(reused),c['implementation'][mid]:len(new)},config_sha256=sha(cp)))
    except BaseException:
        s.update(status='STOPPED_INCOMPLETE',ended_utc=utc(),failed=1,error=traceback.format_exc());atomic(out/'FAILURE.json',s)
        atomic(out/'COMPLETION.json',dict(status='INCOMPLETE',accepted_ROIs=len(accepted),images=s['complete_frames'],primary=None,failed=1,historical_failures_retained=True));raise
    finally:save();log.close()


def controller(cp):
    c=read(cp);root=W/c['artifact_root'];parentcp=W/c['parent_config'];parent=read(parentcp);pr=W/parent['artifact_root']
    lock=(P/'outputs/CONTROLLED_ROI_CONTINUATION.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=dict(status='QUEUED_UNTIL_PARENT_TERMINAL',pid=os.getpid(),started_utc=utc(),models={});atomic(root/'CONTROLLER.json',state);queued=time.monotonic()
    while not (pr/'BATCH_COMPLETION.json').exists():
        ps=read(pr/'CONTROLLER.json')
        try:os.kill(ps['pid'],0)
        except ProcessLookupError:raise RuntimeError('Parent interrupted: reconciliation required, no launch')
        if time.monotonic()-queued>24*3600:raise RuntimeError('QUEUE_24h_DEADLINE')
        time.sleep(20)
    state.update(status='RUNNING',queue_wait_seconds=time.monotonic()-queued);atomic(root/'CONTROLLER.json',state)
    for mid in c['models']:
        command=[str(W/parent['models'][mid]['environment']/'bin/python'),'-u',str(Path(__file__)),'--config',str(cp),'--worker',mid]
        env=os.environ.copy();env.setdefault('CUDA_VISIBLE_DEVICES','0');env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        with (root/(mid+'.log')).open('xb') as log:
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,cwd=W)
            atomic(root/'CURRENT_WORKER.json',dict(model_id=mid,pid=child.pid,command=command));child.wait()
        s=read(root/mid/'STATE.json') if (root/mid/'STATE.json').exists() else dict(status='SETUP_FAILED')
        state['models'][mid]=s['status'] if child.returncode==0 else 'FAILED_REQUIRES_RECONCILIATION';atomic(root/'CONTROLLER.json',state)
    state.update(status='STOPPED_AFTER_SCOPED_CONTINUATION',ended_utc=utc());atomic(root/'CONTROLLER.json',state);atomic(root/'BATCH_COMPLETION.json',state)
    models={}
    for mid in parent['models']:
        origin=root if mid in c['models'] else pr;file=origin/mid/'STATE.json';s=read(file) if file.exists() else dict(status='SETUP_FAILED',complete_frames=0,complete_ROIs=0)
        models[mid]=dict(status=s['status'],frames=s['complete_frames'],ROIs=s['complete_ROIs'],primary=None,packet_root=str((origin/mid/'packets').relative_to(W)))
    atomic(pr/'ASSEMBLED_PREDICTION_INDEX.json',dict(parent_run=parent['run_id'],continuation_run=c['run_id'],models=models,
        prediction_complete_models=sum(s['frames']==90 and s['ROIs']==130 and s['status']=='PREDICTIONS_COMPLETE_SCORING_PENDING_GT' for s in models.values()),
        primary=None,scoring_status='WAITING_REVIEWED_GT'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True);parser.add_argument('--worker');a=parser.parse_args()
    if a.worker:worker(a.config,a.worker)
    else:
        try:controller(a.config)
        except BaseException:
            c=read(a.config);path=W/c['artifact_root']/'CONTROLLER.json';s=read(path) if path.exists() else {}
            s.update(status='STOPPED_REQUIRES_RECONCILIATION',ended_utc=utc(),error=traceback.format_exc());atomic(path,s);raise
