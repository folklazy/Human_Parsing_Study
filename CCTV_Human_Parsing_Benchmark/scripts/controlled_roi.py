"""One scoped detached CCTV90 ROI batch; preserve all historical experiments.

Prediction collection is GT-independent. New headline scores stay null until a
separate reviewed Face/Neck GT binding is accepted. No automatic model retries.
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
from controlled_roi_core import atomic, read, sha, pixel_sha, place, reconcile

P = Path(__file__).resolve().parents[1]; W = P.parent
sys.path[:0] = [str(W/'Human_Parsing_Benchmark/src'), str(P/'scripts')]
from common_view.packets import write_packet, read_packet


def utc():
    return datetime.now(timezone.utc).isoformat()


def relative(path):
    return str(Path(path).relative_to(W))


def emit(stream, event):
    stream.write(json.dumps(dict(utc=utc(), **event), allow_nan=False)+'\n')
    stream.flush(); os.fsync(stream.fileno())


def prepare(run_id):
    from sapiens_input_variants import detector_crop
    root = P/'outputs'/run_id; root.mkdir(parents=True, exist_ok=False)
    oldcp = P/'outputs/cctv-partial-20261031T1800Z/CONFIG.json'; parent = read(oldcp)
    if len(parent['members']) != 90 or len(parent['models']) != 9:
        raise ValueError('Unexpected approved cohort')
    for path, digest in parent['source_hashes'].items():
        if sha(W/path) != digest:
            raise ValueError('Historical scientific source drift: '+path)
    jobs = []; frames = []
    for member in parent['members']:
        iid = member['id']; image = W/parent['dataset_root']/'Images'/(member['stem']+'.jpg')
        if sha(image) != member['RGB_sha256']:
            raise ValueError('Source image changed')
        rgb = np.asarray(Image.open(image).convert('RGB'))
        detector = oldcp.parent/'YOLO26X/packets'/iid; commit = read(detector/'COMMIT.json')
        if commit['input_sha256'] != member['RGB_sha256'] or commit['original_wh'] != member['wh'] or sha(detector/'detector.npz') != commit['artifact_sha256']:
            raise ValueError('Frozen detector binding changed')
        with np.load(detector/'detector.npz', allow_pickle=False) as data:
            extents, boxes, scores = data['masks'], data['boxes'], data['scores']
        if extents.shape != (len(commit['opportunities']), *rgb.shape[:2]) or not np.isfinite(scores).all():
            raise ValueError('Frozen detector shape/score contract')
        frame_jobs = []
        for j, op in enumerate(commit['opportunities']):
            if op['id'] != iid+':yolo:'+str(j) or not np.array_equal(boxes[j], op['bbox']) or float(scores[j]) != op['score']:
                raise ValueError('Frozen detector order identity changed')
            crop, box = detector_crop(rgb, op['bbox'], extents[j], context=.1)
            job_id = iid+'_roi%03d'%j; path = root/'crops'/(job_id+'.png'); path.parent.mkdir(exist_ok=True)
            Image.fromarray(crop).save(path)
            if not np.array_equal(crop, np.asarray(Image.open(path).convert('RGB'))):
                raise ValueError('Lossless crop roundtrip failed')
            row = dict(job_id=job_id, image_id=iid, opportunity_index=j, opportunity_id=op['id'],
                       crop_xyxy=box, crop_png=relative(path), crop_png_sha256=sha(path), crop_pixel_sha256=pixel_sha(crop),
                       crop_hw=list(crop.shape[:2]), bbox_xyxy=op['bbox'], YOLO_score=op['score'],
                       input_sha256=member['RGB_sha256'], detector_sha256=commit['artifact_sha256'])
            jobs.append(row); frame_jobs.append(job_id)
        frames.append(dict(image_id=iid, original_wh=member['wh'], input_sha256=member['RGB_sha256'],
                           detector_npz=relative(detector/'detector.npz'), detector_sha256=commit['artifact_sha256'], jobs=frame_jobs))
    if len(jobs) != 130 or len({j['job_id'] for j in jobs}) != 130:
        raise ValueError('Frozen opportunity workload changed')
    manifest = root/'INPUT_MANIFEST.json'; atomic(manifest, dict(frames=frames, jobs=jobs))
    raw_arrays=sum(len(f['jobs'])*f['original_wh'][0]*f['original_wh'][1]*3 for f in frames)
    atomic(root/'RESOURCE_PLAN.json',dict(shared_crop_png_bytes=sum((W/j['crop_png']).stat().st_size for j in jobs),
        final_two_label_planes_plus_extent_uncompressed_bytes_per_checkpoint=raw_arrays,
        same_arrays_all_nine_uncompressed_bytes=9*raw_arrays,
        native_candidate_storage='unknown until native crop outputs; measured on largest/smallest pending ROI gates',
        total_storage_guaranteed=False,free_space_guard_GiB=50,per_checkpoint_cap_GiB=80,
        disk_free_at_prepare_GiB=shutil.disk_usage(root).free/2**30,ETA=None))
    # Reuse the latest accepted observational attempt, never choose by score.
    reuse_root = P/'outputs/sapiens-roi-remeasurement-20261101T025855Z'
    reuse = {mid: {} for mid in parent['models']}
    for mid, model in parent['models'].items():
        if model['family'] != 'Sapiens2':
            continue
        for packet in sorted((reuse_root/mid/'packets').iterdir()):
            if not packet.is_dir():
                continue
            frame = next(f for f in frames if f['image_id'] == packet.name)
            meta, arrays = read_packet(packet)
            if any(meta.get(k) != value for k, value in dict(model_id=mid, checkpoint_sha256=model['checkpoint_sha256'],
                    native_config_sha256=model['native_config_sha256'], source_commit=model['source_commit'],
                    input_sha256=frame['input_sha256'], detector_sha256=frame['detector_sha256'], precision='FP32',
                    route='YOLO_ROI_LETTERBOX', original_wh=frame['original_wh']).items()):
                raise ValueError('Potential Sapiens reuse scientific binding mismatch')
            with np.load(W/frame['detector_npz'], allow_pickle=False) as data:
                if not np.array_equal(arrays['person_extents'], data['masks']) or not np.array_equal(arrays['person_scores'], data['scores']):
                    raise ValueError('Potential reuse detector identity mismatch')
            for j, job_id in enumerate(frame['jobs']):
                job = next(x for x in jobs if x['job_id'] == job_id); geometry = meta['geometry'][j]
                if geometry['opportunity_id'] != job['opportunity_id'] or geometry['crop_xyxy'] != job['crop_xyxy'] or geometry['original_hw'] != job['crop_hw']:
                    raise ValueError('Potential reuse shared crop geometry mismatch')
                x0,y0,x1,y1 = job['crop_xyxy']; raw = arrays['native_roi_unowned_semantic_masks'][j]
                if not np.array_equal(np.where(arrays['person_extents'][j], raw, 0), arrays['person_semantic_masks'][j]):
                    raise ValueError('Potential reuse owned/raw consistency failure')
                reuse[mid][job_id] = dict(packet=relative(packet), packet_sha256=meta['packet_sha256'],
                    metadata_sha256=sha(packet/'packet.json'), plane_index=j, original_geometry=geometry)
    if sum(map(len, reuse.values())) != 45:
        raise ValueError('Expected45 accepted Sapiens ROI observations; reconcile before altering scope')
    warmcp = read(W/'Human_Parsing_Benchmark/configs/cihp_native_six.json')
    detector_train = read(W/warmcp['frozen_YOLO']['training_run'])
    warm = next(x for x in detector_train['images'] if x['image_id'] == '0000930')
    from common_view.detector_cache import normalize_detector_masks
    trainpath = W/'datasets/CIHP/Training/Images/0000930.jpg'
    rgb = np.asarray(Image.open(trainpath).convert('RGB'))
    with np.load(W/'Human_Parsing_MHPv2_Study'/warm['artifact'], allow_pickle=False) as z:
        masks = normalize_detector_masks(z['masks'], len(warm['opportunities']), rgb.shape[:2])
    crop, box = detector_crop(rgb, warm['opportunities'][0]['bbox'], masks[0], .1)
    traincrop = root/'TRAIN_WARMUP.png'; Image.fromarray(crop).save(traincrop)
    sources = {**parent['source_hashes']}
    for name in ['controlled_roi.py', 'controlled_roi_core.py', 'controlled_roi_models.py', 'sapiens_input_variants.py']:
        path=P/'scripts'/name; sources[relative(path)]=sha(path)
    cp = root/'CONFIG.json'
    config = dict(protocol='CCTV_CONTROLLED_PERSON_ROI_V1', run_id=run_id, status='FROZEN_PREDICTION_COLLECTION',
        created_utc=utc(), parent_config=relative(oldcp), parent_config_sha256=sha(oldcp),
        artifact_root=relative(root), manifest=relative(manifest), manifest_sha256=sha(manifest),
        models=parent['models'], reuse=reuse, expected_images=90, ROI_jobs_per_model=130,
        expected_reused_ROIs=45, expected_new_ROIs=1125, warmup_calls_per_model=1,
        model_ROI_API_call_budget=1134, external_TTA=False, precision='FP32', batch_size=1, AMP=False, TF32=False,
        crop_context_each_side=.1, preserve_aspect_ratio=True, candidate_bbox_IoU=.5,
        warmup=dict(image=relative(traincrop), png_sha256=sha(traincrop), source_image_sha256=sha(trainpath),
                    source_detector_artifact=warm['artifact'], crop_xyxy=box,
                    designated_box=[warm['opportunities'][0]['bbox'][i]-box[i%2] for i in range(4)]),
        source_hashes=sources, seed=parent['seed'], resource_policy=parent['resource_policy'],
        required_free_MiB=parent['required_free_MiB'], minimum_free_gib=50, max_model_gib=80, max_model_hours=24,
        min_forward_free_MiB=1024, automatic_retry=0, fallback=False,
        GT_readiness='NECK_AND_FULL_OWNER_REVIEW_PENDING', scoring_primary=None,
        GT_operational_amendment='Collect fixed GT-independent predictions now; withhold new headline scores until reviewedGT/scorer acceptance. No predictions used to create GT.',
        failure_policy='stop affected checkpoint and retain attempts; independent checkpoints may continue, never retry failed IDs')
    atomic(cp, config); (P/'outputs/CURRENT_CONTROLLED_ROI.txt').write_text(run_id+'\n')
    atomic(root/'AUTHORIZATION.json', dict(utc=utc(), user_instruction='ได้รันใหม่เลย',
        approved_scope='CCTV90 nine checkpoints, same frozen YOLO person crops; existing accepted Sapiens ROIs may be reused',
        no_YOLO_reinference=True, no_training=True, no_CIHP5000_rerun=True, final_scoring_gate='REVIEWED_GT_REQUIRED'))
    print(json.dumps(dict(run_id=run_id, config=relative(cp), frames=90, ROIs_per_model=130, reused=45, pending=1125)))


def check_sources(config):
    for path, digest in config['source_hashes'].items():
        if sha(W/path) != digest:
            raise ValueError('Source drift: '+path)
    if sha(W/config['manifest']) != config['manifest_sha256'] or sha(W/config['parent_config']) != config['parent_config_sha256']:
        raise ValueError('Input/parent manifest drift')


def worker(cp, mid):
    import torch
    from controlled_roi_models import CropModel
    from common_view.core import validate_prediction
    config = read(cp); root = W/config['artifact_root']; spec = config['models'][mid]
    output = root/mid; output.mkdir(exist_ok=False)
    lock = (P/'outputs/CONTROLLED_ROI_GPU_WORKER.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    start = time.monotonic(); manifest = read(W/config['manifest']); jobs = manifest['jobs']; by_job = {j['job_id']:j for j in jobs}
    frames = {f['image_id']:f for f in manifest['frames']}; reuse = config['reuse'][mid]
    pending = [j for j in jobs if j['job_id'] not in reuse]
    # Two shape-selected pending jobs are engineering gates and retained in full
    # membership. No new validation calls are spent rerunning the pilot outputs.
    ordered = sorted(pending, key=lambda j:(j['crop_hw'][0]*j['crop_hw'][1], j['job_id']))
    gate_ids = [ordered[-1]['job_id'], ordered[0]['job_id']] if ordered else []
    gate_ids = list(dict.fromkeys(gate_ids))
    execution = [by_job[k] for k in gate_ids]+[j for j in pending if j['job_id'] not in gate_ids]
    state = dict(model_id=mid, status='INITIALIZING', pid=os.getpid(), started_utc=utc(),
        model_ROI_API_calls=0, warmup_calls=0, reused_ROIs=0, new_ROIs=0, complete_ROIs=0,
        complete_frames=0, expected_frames=90, expected_ROIs=130, readiness_job_ids=gate_ids,
        primary=None, scoring_status='WAITING_REVIEWED_GT', resource_policy='SHARED_GPU_QUALITY_ONLY')
    ledger = (output/'ATTEMPTS.jsonl').open('x', buffering=1)
    accepted = []; observations = []; packet_paths = {}
    def save(): atomic(output/'STATE.json', state)
    def guard():
        if shutil.disk_usage(root).free < config['minimum_free_gib']*2**30:
            raise RuntimeError('FREE_DISK_GUARD')
        if sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) > config['max_model_gib']*2**30:
            raise RuntimeError('CHECKPOINT_STREAM_DISK_GUARD')
        if time.monotonic()-start > config['max_model_hours']*3600:
            raise RuntimeError('CHECKPOINT_TIME_GUARD')
        check_sources(config)
    def forward(rgb, image, box, purpose, job_id):
        guard()
        if state['model_ROI_API_calls'] >= len(pending)+1:
            raise RuntimeError('MODEL_ROI_API_CALL_BUDGET')
        if torch.cuda.mem_get_info(0)[0] < config['min_forward_free_MiB']*2**20:
            raise RuntimeError('PRE_FORWARD_HEADROOM_GUARD')
        state.update(status=purpose, current_job=job_id); state['model_ROI_API_calls'] += 1; save()
        emit(ledger, dict(event='FORWARD_START', purpose=purpose, job_id=job_id, call=state['model_ROI_API_calls']))
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats(); t=time.monotonic()
        result=model.infer(rgb, image, box)
        torch.cuda.synchronize()
        observation=dict(job_id=job_id,purpose=purpose,adapter_elapsed_seconds=time.monotonic()-t,
                         peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,
                         peak_reserved_MiB=torch.cuda.max_memory_reserved()/2**20)
        observations.append(observation); atomic(output/'RESOURCE_OBSERVATIONS.json', observations)
        emit(ledger, dict(event='FORWARD_END', **observation)); return result
    assembled=set()
    def assemble_frame(frame):
        iid=frame['image_id']
        if iid in assembled or not all(k in packet_paths for k in frame['jobs']): return
        guard();w,h=frame['original_wh']
        if sha(W/frame['detector_npz'])!=frame['detector_sha256']:raise ValueError('Detector cache drift')
        with np.load(W/frame['detector_npz'],allow_pickle=False) as data:
            extents,scores,boxes=data['masks'],data['scores'],data['boxes']
        raw=[];owned=[];references=[]
        for job_id in frame['jobs']:
            job=by_job[job_id];meta,data=read_packet(packet_paths[job_id])
            r,o=place(data['native_crop_mask'],job['crop_xyxy'],extents[job['opportunity_index']],model.classes)
            raw.append(r);owned.append(o);references.append(dict(job_id=job_id,packet=relative(packet_paths[job_id]),packet_sha256=meta['packet_sha256'],opportunity_id=job['opportunity_id']))
        arrays=dict(native_roi_unowned_semantic_masks=np.asarray(raw,np.uint8).reshape(-1,h,w),
            person_semantic_masks=np.asarray(owned,np.uint8).reshape(-1,h,w),person_extents=extents,person_scores=scores,bboxes_xyxy=boxes)
        space='SAPIENS2_DOME29_PRED' if model.classes==29 else 'CIHP_GT_AND_NATIVE_PRED'
        validate_prediction(arrays['person_semantic_masks'],extents,scores,(h,w),space)
        meta=dict(model_id=mid,image_id=iid,original_wh=[w,h],input_sha256=frame['input_sha256'],checkpoint_sha256=spec['checkpoint_sha256'],
            config_sha256=sha(cp),detector_sha256=frame['detector_sha256'],label_space=space,precision='FP32',
            environment_sha256=sha(output/'ENVIRONMENT.json'),model_details_sha256=sha(output/'MODEL_DETAILS.json'),
            protocol=config['protocol'],route='CONTROLLED_YOLO_PERSON_ROI',roi_references=references,
            associations=[dict(YOLO_opportunity_id=by_job[k]['opportunity_id'],prediction_index=j) for j,k in enumerate(frame['jobs'])],
            person_confidence_kind='FROZEN_YOLO_SCORE_NOT_SEMANTIC_CONFIDENCE',GT_used_in_prediction=False)
        packet=write_packet(output/'packets',iid,arrays,meta,{})
        check,data=read_packet(packet)
        if not np.array_equal(data['person_extents'],extents) or not np.array_equal(data['person_semantic_masks'],np.where(extents,data['native_roi_unowned_semantic_masks'],0)):
            raise ValueError('Frame ownership/readback failure')
        assembled.add(iid);state['complete_frames']+=1;save();emit(ledger,dict(event='FRAME_COMMITTED',image_id=iid,packet_sha256=check['packet_sha256']))

    def commit_roi(job, native, candidates, detail, origin):
        from controlled_roi_core import validate_native
        validate_native(native, model.classes, job['crop_hw'])
        metadata=dict(model_id=mid,job_id=job['job_id'],image_id=job['image_id'],opportunity_id=job['opportunity_id'],
            checkpoint_sha256=spec['checkpoint_sha256'], original_native_config_sha256=spec['native_config_sha256'],
            native_source_commit=spec['source_commit'],config_sha256=sha(cp),input_manifest_sha256=config['manifest_sha256'],
            environment_sha256=sha(output/'ENVIRONMENT.json'),model_details_sha256=sha(output/'MODEL_DETAILS.json'),
            crop_pixel_sha256=job['crop_pixel_sha256'],crop_png_sha256=job['crop_png_sha256'],crop_xyxy=job['crop_xyxy'],
            detector_sha256=job['detector_sha256'],protocol=config['protocol'],precision='FP32',native_classes=model.classes,
            native_geometry_and_selection=detail,origin=origin,GT_used_in_prediction=False)
        packet=write_packet(output/'roi_packets',job['job_id'],dict(native_crop_mask=native,native_candidate_masks=candidates),metadata,{})
        meta, arrays=read_packet(packet,dict(config_sha256=sha(cp),crop_pixel_sha256=job['crop_pixel_sha256']))
        if not np.array_equal(arrays['native_crop_mask'],native):raise ValueError('ROI atomic readback mismatch')
        accepted.append(job['job_id']);packet_paths[job['job_id']]=packet
        state['complete_ROIs']=len(accepted);save()
        emit(ledger,dict(event='ROI_COMMITTED',job_id=job['job_id'],origin=origin,packet_sha256=meta['packet_sha256']))
        assemble_frame(frames[job['image_id']])
    save()
    try:
        guard()
        free=float(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).splitlines()[0])
        if free < config['required_free_MiB'][mid]: raise RuntimeError('PRELOAD_FREE_VRAM_GUARD')
        if sha(W/spec['checkpoint'])!=spec['checkpoint_sha256'] or sha(W/spec['native_config'])!=spec['native_config_sha256']:
            raise ValueError('Checkpoint/config identity mismatch')
        if subprocess.check_output(['git','-C',str(W/spec['source']),'rev-parse','HEAD'],text=True).strip()!=spec['source_commit']:
            raise ValueError('Native source revision mismatch')
        torch.set_num_threads(2);torch.manual_seed(config['seed']);np.random.seed(config['seed'])
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        model=CropModel(W,spec,output)
        atomic(output/'ENVIRONMENT.json',dict(python=sys.version,executable=sys.executable,torch=torch.__version__,
            CUDA_runtime=torch.version.cuda,GPU=torch.cuda.get_device_name(0),numpy=np.__version__,FP32=True,AMP=False,TF32=False,
            CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),source_hashes=config['source_hashes']))
        warm=config['warmup'];image=W/warm['image']
        if sha(image)!=warm['png_sha256']:raise ValueError('TRAIN warmup input drift')
        forward(np.asarray(Image.open(image).convert('RGB')),image,warm['designated_box'],'TRAIN_WARMUP','TRAIN0000930')
        state['warmup_calls']=1;save()
        for job in jobs:
            if job['job_id'] not in reuse:continue
            ref=reuse[job['job_id']];meta,arrays=read_packet(W/ref['packet'])
            if meta['packet_sha256']!=ref['packet_sha256'] or sha(W/ref['packet']/'packet.json')!=ref['metadata_sha256']:
                raise ValueError('Reused parent packet drift')
            x0,y0,x1,y1=job['crop_xyxy'];native=arrays['native_roi_unowned_semantic_masks'][ref['plane_index'],y0:y1,x0:x1].copy()
            commit_roi(job,native,native[None],dict(input_geometry=ref['original_geometry'],selection='DESIGNATED_SEMANTIC_ROI',
                reuse_compatibility='same frozen checkpoint/input/crop/preprocess/FP32/native29/YOLO ownership; scoring/population metadata intentionally distinct'),dict(kind='REUSED_PARENT',**ref))
            state['reused_ROIs']+=1;save()
        for job in execution:
            image=W/job['crop_png']
            if sha(image)!=job['crop_png_sha256']:raise ValueError('Crop PNG changed')
            rgb=np.asarray(Image.open(image).convert('RGB'))
            if pixel_sha(rgb)!=job['crop_pixel_sha256']:raise ValueError('Crop decoded pixels changed')
            x0,y0,_,_=job['crop_xyxy'];b=job['bbox_xyxy'];local=[b[0]-x0,b[1]-y0,b[2]-x0,b[3]-y0]
            native,candidates,detail=forward(rgb,image,local,'ROI_READINESS' if job['job_id'] in gate_ids else 'ROI_INFERENCE',job['job_id'])
            commit_roi(job,native,candidates,detail,dict(kind='NEW_INFERENCE'))
            state['new_ROIs']+=1
            if all(k in packet_paths for k in gate_ids):
                state['GPU_readiness']='PASS_OUTPUT_CONTRACT_NOT_QUALITY'
                sizes=[sum(p.stat().st_size for p in packet_paths[k].iterdir() if p.is_file()) for k in gate_ids]
                raw_estimate=read(root/'RESOURCE_PLAN.json')['final_two_label_planes_plus_extent_uncompressed_bytes_per_checkpoint']
                estimate=max(sizes)*130+raw_estimate
                if estimate>config['max_model_gib']*2**30 or estimate>shutil.disk_usage(root).free-config['minimum_free_gib']*2**30:
                    raise RuntimeError('PROJECTED_STORAGE_GUARD')
                atomic(output/'READINESS.json',dict(status=state['GPU_readiness'],job_ids=gate_ids,source_config_sha256=sha(cp),
                    retained_storage_estimate_bytes=estimate,estimate_not_guarantee=True,
                    estimator='max observed gate ROI atomic bytes x130 plus uncompressed final frame arrays; native candidate variation remains guarded',
                    all_observed_forward_peaks=observations))
            save()
        roi_check=reconcile([j['job_id'] for j in jobs],accepted)
        if not roi_check['strict_complete']:raise ValueError('ROI membership reconciliation failed')
        for frame in manifest['frames']:assemble_frame(frame)
        if len(assembled)!=90:raise ValueError('Frame membership reconciliation failed')
        state.update(status='PREDICTIONS_COMPLETE_SCORING_PENDING_GT',ended_utc=utc(),failed=0,invalid=0)
        completion=dict(**roi_check,images=90,roi_jobs=130,reused_ROIs=len(reuse),new_ROIs=len(pending),warmup_calls=1,
            config_sha256=sha(cp),manifest_sha256=config['manifest_sha256'],primary=None,scoring_status='WAITING_REVIEWED_GT',
            timing_scope='SHARED_GPU_ADAPTER_DIAGNOSTICS_NOT_SPEED_RANKING')
        atomic(output/'COMPLETION.json',completion)
    except BaseException:
        state.update(status='STOPPED_INCOMPLETE',ended_utc=utc(),error=traceback.format_exc(),failed=1)
        atomic(output/'FAILURE.json',state)
        atomic(output/'COMPLETION.json',dict(**reconcile([j['job_id'] for j in jobs],accepted,failed=['attempt']),images=state['complete_frames'],primary=None,reason='MODEL_ATTEMPT_FAILED',config_sha256=sha(cp)))
        raise
    finally:
        save();ledger.close()


def controller(cp):
    config=read(cp);root=W/config['artifact_root']
    lock=(P/'outputs/CONTROLLED_ROI_CONTROLLER.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (root/'CONTROLLER.json').exists():raise FileExistsError('Existing controller; never restart automatically')
    state=dict(status='RUNNING',pid=os.getpid(),session_id=os.getsid(0),started_utc=utc(),models={})
    atomic(root/'CONTROLLER.json',state)
    try:
        check_sources(config)
        for mid,spec in config['models'].items():
            if (root/mid).exists():raise FileExistsError('Existing model attempt; explicit reconciliation required')
            command=[str(W/spec['environment']/'bin/python'),'-u',str(Path(__file__)),'--config',str(cp),'--worker',mid]
            env=os.environ.copy();env.setdefault('CUDA_VISIBLE_DEVICES','0');env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
            with (root/(mid+'.log')).open('xb') as log:
                child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=W,env=env,start_new_session=False)
                atomic(root/'CURRENT_WORKER.json',dict(model_id=mid,pid=child.pid,command=command,started_utc=utc()))
                child.wait()
            result=read(root/mid/'STATE.json') if (root/mid/'STATE.json').exists() else dict(status='SETUP_FAILED',returncode=child.returncode)
            effective=result['status'] if child.returncode==0 else 'FAILED_OR_INTERRUPTED_REQUIRES_RECONCILIATION'
            atomic(root/mid/'CONTROLLER_OBSERVATION.json',dict(returncode=child.returncode,recorded_worker_status=result['status'],effective_status=effective,observed_utc=utc()))
            state['models'][mid]=effective;atomic(root/'CONTROLLER.json',state)
        state.update(status='STOPPED_AFTER_APPROVED_NINE',ended_utc=utc(),primary=None,scoring_status='WAITING_REVIEWED_GT')
        atomic(root/'CONTROLLER.json',state)
        atomic(root/'BATCH_COMPLETION.json',dict(**state,expected_models=9,
            prediction_complete_models=sum(v=='PREDICTIONS_COMPLETE_SCORING_PENDING_GT' for v in state['models'].values()),
            automatic_next_experiment=False))
    except BaseException:
        state.update(status='CONTROLLER_STOPPED_REQUIRES_RECONCILIATION',ended_utc=utc(),error=traceback.format_exc());atomic(root/'CONTROLLER.json',state);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare');parser.add_argument('--config',type=Path);parser.add_argument('--worker');args=parser.parse_args()
    if args.prepare:prepare(args.prepare)
    elif args.worker:worker(args.config,args.worker)
    else:controller(args.config)
