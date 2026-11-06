"""Three bounded model calls while Sapiens is operator-paused; no VAL scoring."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import traceback

H=Path(__file__).resolve().parents[1];W=H.parent
sys.path[:0]=[str(H/'src'),str(H/'scripts'),str(W/'CCTV_Human_Parsing_Benchmark/scripts')]
from controlled_roi_core import atomic,read,sha,pixel_sha,validate_native
from common_view.packets import write_packet,read_packet
import controlled_cihp as base

MID='CPI_ConvNeXtB_CIHP'
REVISION='CPI_FEATURE_BRANCH_SCHEDULE_3'
HEAD_SHA='85b75e0fe38465ec460107c11111702345a6de091a8ba3d399ca266878ca7573'


def run(parentcp,root):
    parentcp=Path(parentcp).resolve(strict=True);root=Path(root).resolve()
    import numpy as np
    from PIL import Image
    import torch
    from controlled_roi_models import CropModel
    from controlled_roi_continuation import reusable_memory
    from sapiens_input_variants import detector_crop
    from cihp_benchmark.cpi_feature_schedule import install
    c=base.verify_config(parentcp);pr=W/c['artifact_root'];spec=c['models'][MID]
    root.mkdir(parents=True,exist_ok=False)
    profile={base.rel(p):sha(p) for p in [Path(__file__),H/'src/cihp_benchmark/cpi_memory.py',
        H/'src/cihp_benchmark/cpi_feature_memory.py',H/'src/cihp_benchmark/cpi_feature_schedule.py']}
    f=read(pr/MID/'FAILURE.json')
    if 'CUDA out of memory' not in f['error']:raise ValueError('Expected retained ConvNeXt OOM history')
    manifest=read(W/c['manifest']);frame=next(r for r in manifest['frames'] if r['member']['id']==f['current_id'])
    pending=[j for j in range(len(frame['detector']['opportunities']))
             if not (pr/MID/'roi_packets'/(f['current_id']+'_%03d'%j)).exists()]
    if not pending:raise ValueError('No missing ROI at historical failure')
    j=pending[0]
    cfg=dict(model_id=MID,parent_config=base.rel(parentcp),parent_config_sha256=sha(parentcp),
        checkpoint=spec,profile=REVISION,profile_sources=profile,FP32=True,batch=1,extra_TTA=False,
        diagnostic_ROI=dict(image_id=f['current_id'],index=j),call_limit=3,
        purpose='TRAIN revision1/revision3 hard-mask+candidate parity; retained OOM ROI once; diagnostic never canonical',
        canonical_predictions_reused=False,GT_used_in_prediction=False)
    atomic(root/'CONFIG.json',cfg)
    s=dict(status='INITIALIZING',pid=os.getpid(),started_utc=base.utc(),model_id=MID,calls=0,
           canonical_VAL_calls=0,automatic_retries=0,config_sha256=sha(root/'CONFIG.json'))
    start=time.monotonic();events=[]
    def save():atomic(root/'STATE.json',s)
    def guard():
        if shutil.disk_usage(root).free<50*2**30:raise RuntimeError('RESOURCE_DISK_FREE_GUARD')
        memory=reusable_memory(torch.cuda.mem_get_info()[0],torch.cuda.memory_allocated(),torch.cuda.memory_reserved())
        if memory['effective_available_bytes']<1024*2**20:raise RuntimeError('RESOURCE_VRAM_HEADROOM_GUARD')
        if s['calls']>=3:raise RuntimeError('DIAGNOSTIC_CALL_BUDGET')
    def call(purpose,rgb,path,box):
        guard();s.update(status=purpose,calls=s['calls']+1);save()
        torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();t=time.monotonic()
        with torch.inference_mode():result=model.infer(rgb,path,box)
        torch.cuda.synchronize()
        native,candidates,details=result;validate_native(native,20,rgb.shape[:2])
        for mask in candidates:validate_native(mask,20,rgb.shape[:2])
        packet=write_packet(root/'packets',purpose,dict(native_crop_mask=native,native_candidate_masks=candidates),
            dict(model_id=MID,checkpoint_sha256=spec['checkpoint_sha256'],config_sha256=sha(root/'CONFIG.json'),
                 purpose='DIAGNOSTIC_NOT_CANONICAL',stage=purpose,input_pixel_sha256=pixel_sha(rgb),geometry=details),{})
        read_packet(packet)
        events.append(dict(purpose=purpose,seconds=time.monotonic()-t,input_hw=list(rgb.shape[:2]),
            peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            packet=base.rel(packet),packet_json_sha256=sha(packet/'packet.json')))
        atomic(root/'CALLS.json',events);return result
    save()
    try:
        if torch.cuda.mem_get_info()[0]/2**20<c['required_free_MiB'][MID]:raise RuntimeError('RESOURCE_PRELOAD_FREE_VRAM_GUARD')
        base.checked(spec['checkpoint'],spec['checkpoint_sha256']);base.checked(spec['native_config'],spec['native_config_sha256'])
        if subprocess.check_output(['git','-C',str(W/spec['source']),'rev-parse','HEAD'],text=True).strip()!=spec['source_commit']:
            raise ValueError('Native CPI source revision mismatch')
        torch.set_num_threads(2);torch.manual_seed(c['seed']);np.random.seed(c['seed'])
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        model=CropModel(W,spec,root/'adapter')
        if model.details['memory_implementation']['revision']!='CPI_PERSON_CHUNK_RESTORATION_1':
            raise ValueError('Baseline must be the previously accepted ConvNeXt implementation')
        warm=c['warmup'];path=base.checked(warm['image'],warm['png_sha256']);rgb=np.asarray(Image.open(path).convert('RGB'))
        old=call('TRAIN_REVISION1',rgb,path,warm['designated_box'])
        receipt=install(model.model.bbox_head,HEAD_SHA)
        atomic(root/'IMPLEMENTATION.json',receipt)
        new=call('TRAIN_REVISION3',rgb,path,warm['designated_box'])
        if not np.array_equal(old[0],new[0]) or not np.array_equal(old[1],new[1]):
            raise ValueError('TRAIN native selected/candidate hard-mask parity failure')
        for key in ['native_boxes','native_scores','native_selected_index','nonempty_native_indices']:
            if old[2].get(key)!=new[2].get(key):raise ValueError('TRAIN native association parity failure: '+key)
        _,full,extents,_=base.load_frame(frame);op=frame['detector']['opportunities'][j]
        crop,box=detector_crop(full,op['bbox'],extents[j],.1)
        p=root/'known_oom_roi.png';Image.fromarray(crop).save(p)
        if not np.array_equal(np.asarray(Image.open(p).convert('RGB')),crop):raise ValueError('Probe PNG RGB mismatch')
        designated=[op['bbox'][k]-box[k%2] for k in range(4)]
        call('VAL_KNOWN_OOM_ROI_ONCE',crop,p,designated)
        s.update(status='PASS',TRAIN_native_hardmask_and_candidates_parity=True,
            TRAIN_native_association_parity=True,known_OOM_ROI_pass=True,
            implementation_revision=REVISION,profile_sources=profile,
            parity_scope='One fixed TRAIN ROI and shared-head CPU numeric fixtures; not population bitwise equivalence',
            geometry=dict(image_id=frame['member']['id'],ROI_index=j,crop_xyxy=box,crop_pixel_sha256=pixel_sha(crop)),
            original_scientific_settings_unchanged=True)
    except BaseException as exc:
        s.update(status='STOPPED_DIAGNOSTIC_FAILED',error=repr(exc),traceback=traceback.format_exc())
        raise
    finally:
        s.update(ended_utc=base.utc(),execution_wall_seconds=time.monotonic()-start)
        save()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.parent,a.output)
