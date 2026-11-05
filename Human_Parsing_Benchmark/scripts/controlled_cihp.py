"""Scoped CIHP controlled-ROI batch. Run prepare, acceptance, then detached controller.

Reuses CCTV crop adapters without changing their scientific source. Quality uses
cached YOLO. Clean/live-YOLO speed measurement remains a separately gated phase.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
import traceback

H = Path(__file__).resolve().parents[1]
W = H.parent
sys.path[:0] = [str(H/'src'), str(W/'CCTV_Human_Parsing_Benchmark/scripts')]
import numpy as np
from PIL import Image
from controlled_roi_core import atomic, read, sha, pixel_sha, place, validate_native
from common_view.packets import write_packet, read_packet
from common_view.detector_cache import normalize_detector_masks


def utc():
    return datetime.now(timezone.utc).isoformat()


def rel(path):
    return str(Path(path).relative_to(W))


def emit(stream, **values):
    stream.write(json.dumps(dict(utc=utc(), **values), allow_nan=False)+'\n')
    stream.flush()
    os.fsync(stream.fileno())


def telemetry():
    result = subprocess.run(['nvidia-smi',
        '--query-gpu=uuid,memory.used,memory.free,utilization.gpu,temperature.gpu,clocks.sm,clocks.mem',
        '--format=csv,noheader,nounits'], capture_output=True, text=True)
    processes = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,used_memory',
        '--format=csv,noheader,nounits'], capture_output=True, text=True)
    return dict(utc=utc(), GPU=result.stdout.strip(), compute_processes=processes.stdout.strip(),
                GPU_query_returncode=result.returncode, process_query_returncode=processes.returncode,
                load_average=list(os.getloadavg()))


def checked(path, digest):
    path = W/path
    if sha(path) != digest:
        raise ValueError('SOURCE_BINDING_DRIFT: '+str(path))
    return path


def prepare():
    run = 'cihp-controlled-roi-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    root = H/'outputs'/run
    root.mkdir(parents=True, exist_ok=False)
    parent_path = W/'CCTV_Human_Parsing_Benchmark/outputs/cctv-controlled-roi-20261101T115653Z/CONFIG.json'
    parent = read(parent_path)
    full = read(H/'configs/cihp_sapiens_c4p_full.json')
    population = W/full['native_population']
    checked(full['native_population'], full['native_population_sha256'])
    members = read(population)['members']
    ledger_path = W/full['YOLO']['validation_ledger']
    detector = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    by_id = {row['image_id']: row for row in detector}
    ids = [m['id'] for m in members]
    if len(ids) != 5000 or len(set(ids)) != 5000 or set(ids) != set(by_id) or len(detector) != 5000:
        raise ValueError('Exact detector/population membership mismatch')
    frames = []
    arrays_bytes = 0
    for m in members:
        d = by_id[m['id']]
        if d['status'] != 'COMPLETE' or d['input_sha256'] != m['RGB_sha256'] or d['original_wh'] != m['wh']:
            raise ValueError('Detector input binding mismatch')
        opportunities = d['opportunities']
        if len({op['id'] for op in opportunities}) != len(opportunities):
            raise ValueError('Duplicate detector opportunity')
        arrays_bytes += m['wh'][0]*m['wh'][1]*len(opportunities)*3
        frames.append(dict(member=m, detector=d))
    manifest = root/'INPUTS.json'
    atomic(manifest, dict(frames=frames, expected_ids=ids,
                          ROI_count=sum(len(f['detector']['opportunities']) for f in frames)))
    sources = dict(parent['source_hashes'])
    for path in (H/'src/controlled_ci_hp').glob('*.py'):
        sources[rel(path)] = sha(path)
    for path in [Path(__file__), H/'src/common_view/core.py', H/'src/common_view/packets.py',
                 H/'src/common_view/detector_cache.py', H/'src/common_view/full.py',
                 W/'CCTV_Human_Parsing_Benchmark/scripts/controlled_roi_models.py',
                 W/'CCTV_Human_Parsing_Benchmark/scripts/sapiens_input_variants.py',
                 W/'CCTV_Human_Parsing_Benchmark/scripts/controlled_roi_core.py']:
        sources[rel(path)] = sha(path)
    protocol = H/'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json'
    gt_bindings = W/full['GT_binding_root']
    gt_rows = [json.loads(line) for line in (gt_bindings/'BINDINGS.jsonl').read_text().splitlines()]
    if {row['image_id'] for row in gt_rows} != set(ids) or len(gt_rows) != 5000:
        raise ValueError('GT bindings do not cover expected population')
    expected_parts = {str(c): sum(person['target_support'][c-1]>0 for row in gt_rows for person in row['persons']) for c in range(1,5)}
    config = dict(run_id=run, created_utc=utc(), status='FROZEN_EXECUTION_REVISION1',
        route='CONTROLLED_YOLO_PERSON_ROI', protocol_id='CIHP_CONTROLLED_ROI_C4P_R1',
        protocol=rel(protocol), protocol_sha256=sha(protocol), source_hashes=sources,
        parent_config=rel(parent_path), parent_config_sha256=sha(parent_path),
        population=rel(population), population_sha256=sha(population),
        detector_ledger=rel(ledger_path), detector_ledger_sha256=sha(ledger_path),
        GT_expected_sums={key:sum(row[key] for row in gt_rows) for key in ('G_loc','G_sem_C4')},
        GT_expected_part_counts=expected_parts, GT_binding_root=rel(gt_bindings), GT_binding_manifest_sha256=sha(gt_bindings/'BINDINGS.jsonl'),
        manifest=rel(manifest), manifest_sha256=sha(manifest), artifact_root=rel(root),
        models=parent['models'], model_order=list(parent['models']), warmup=parent['warmup'],
        expected_images=5000, ROI_count=read(manifest)['ROI_count'], seed=parent['seed'],
        FP32=True, AMP=False, TF32=False, external_TTA=False, batch_size=1,
        context_each_side=.1, automatic_retry=0, automatic_recovery=0, fallback=False,
        resource_policy='SHARED_GPU_QUALITY_ONLY', minimum_free_gib=50, max_stream_gib=80,
        planning_envelope_gib=200, max_hours=24, required_free_MiB=parent['required_free_MiB'],
        min_forward_free_MiB=1024, resource_queue_timeout_seconds=600,
        warmup_calls_per_model=2, warmup_purpose='TRAIN baseline then timed equivalence, once each',
        model_call_limit_per_model=read(manifest)['ROI_count']+2,
        scoring='C4P revision2, additional mean GT-person-part IoU at mask matching0.50',
        primary='Global mIoU4; mean-part and Q_GT/person F1 secondary',
        analyze_only_after_batch_terminal=True, live_timing_status='PENDING_SEPARATE_READINESS',
        no_score_based_retry_or_tuning=True,
        storage=dict(final_arrays_uncompressed_per_model_bytes=arrays_bytes,
                     nine_model_uncompressed_bytes=arrays_bytes*9,
                     temporary_and_candidate_peak='MEASURE_TRAIN_BEFORE_VALIDATION',
                     compression_ratio_assumed=None, total_storage_guaranteed=False))
    for mid, spec in config['models'].items():
        path = W/spec['checkpoint']
        stat = path.stat()
        if spec.get('checkpoint_stat') and (stat.st_size != spec['checkpoint_stat']['size'] or stat.st_mtime_ns != spec['checkpoint_stat']['mtime_ns']):
            raise ValueError('Checkpoint stat differs from accepted identity: '+mid)
        checked(spec['native_config'], spec['native_config_sha256'])
    cp = root/'CONFIG.json'
    atomic(cp, config)
    (H/'outputs/CURRENT_CONTROLLED_CIHP.txt').write_text(run+'\n')
    print(json.dumps(dict(config=rel(cp), frames=5000, ROI_count=config['ROI_count'], storage=config['storage'])))


def verify_config(cp):
    config = read(cp)
    for path, digest in config['source_hashes'].items():
        checked(path, digest)
    for path_key, hash_key in [('manifest','manifest_sha256'), ('population','population_sha256'),
                               ('protocol','protocol_sha256'), ('parent_config','parent_config_sha256'),
                               ('detector_ledger','detector_ledger_sha256')]:
        checked(config[path_key], config[hash_key])
    return config


def load_frame(frame):
    m, d = frame['member'], frame['detector']
    image = W/'datasets/CIHP/Validation/Images'/(m['id']+'.jpg')
    checked(rel(image), m['RGB_sha256'])
    rgb = np.asarray(Image.open(image).convert('RGB'))
    if list(rgb.shape[:2][::-1]) != m['wh']:
        raise ValueError('Image geometry drift')
    dp = W/'Human_Parsing_MHPv2_Study'/d['artifact']
    checked(rel(dp), d['artifact_sha256'])
    with np.load(dp, allow_pickle=False) as data:
        extents = normalize_detector_masks(data['masks'], len(d['opportunities']), rgb.shape[:2])
    scores = np.array([op['score'] for op in d['opportunities']], np.float32)
    return image, rgb, extents, scores


def worker(cp, mid):
    import torch
    from controlled_roi_models import CropModel
    from sapiens_input_variants import detector_crop
    from controlled_ci_hp.measurement import Measurements
    from controlled_ci_hp.scoring import evaluate
    from common_view.core import load_spec
    from common_view.full import Accumulator
    import shutil
    config = verify_config(cp)
    root = W/config['artifact_root']
    output = root/mid
    output.mkdir(exist_ok=False)
    lock = (H/'outputs/CONTROLLED_CIHP_GPU.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.monotonic()
    state = dict(model_id=mid, status='INITIALIZING', pid=os.getpid(), started_utc=utc(),
                 completed=0, expected=5000, ROI_calls=0, warmup_calls=0, failed=0, invalid=0,
                 primary=None, speed_ranking_allowed=False)
    spec = config['models'][mid]
    manifest = read(W/config['manifest'])
    accumulator = Accumulator(manifest['expected_ids'])
    part_sums = {str(c): dict(count=0, IoU_sum=0., TP=0, FP=0, FN=0, unmatched=0) for c in range(1,5)}
    bytes_written = 0
    measured_storage = [0, -1]
    ledger = (output/'ATTEMPTS.jsonl').open('x', buffering=1)

    def save():
        atomic(output/'STATE.json', state)

    def guard():
        if shutil.disk_usage(root).free < config['minimum_free_gib']*2**30:
            raise RuntimeError('RESOURCE_DISK_FREE_GUARD')
        if state['completed']//25 != measured_storage[1]:
            measured_storage[0] = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
            measured_storage[1] = state['completed']//25
        if max(bytes_written, measured_storage[0]) > config['max_stream_gib']*2**30:
            raise RuntimeError('RESOURCE_STREAM_DISK_GUARD')
        if time.monotonic()-started > config['max_hours']*3600:
            raise RuntimeError('RESOURCE_TIME_GUARD')
        if torch.cuda.mem_get_info()[0] < config['min_forward_free_MiB']*2**20:
            raise RuntimeError('RESOURCE_VRAM_HEADROOM_GUARD')

    def infer(rgb, path, box, purpose):
        guard()
        calls = state['ROI_calls']+state['warmup_calls']
        if calls >= config['model_call_limit_per_model']:
            raise RuntimeError('MODEL_CALL_BUDGET')
        key = 'warmup_calls' if purpose.startswith('TRAIN') else 'ROI_calls'
        state[key] += 1
        save()
        emit(ledger, event='MODEL_CALL_START', purpose=purpose, image=state.get('current_id'), calls=calls+1)
        measure = Measurements(torch.cuda.synchronize)
        torch.cuda.reset_peak_memory_stats()
        if purpose == 'TRAIN_BASELINE':
            result = model.infer(rgb, path, box)
            torch.cuda.synchronize()
        else:
            result = measure.infer(model, rgb, path, box)
        emit(ledger, event='MODEL_CALL_END', purpose=purpose, measurements=measure.report(),
             allocated_MiB=torch.cuda.max_memory_allocated()/2**20,
             reserved_MiB=torch.cuda.max_memory_reserved()/2**20)
        return result, measure.report()

    save()
    try:
        free = torch.cuda.mem_get_info()[0]/2**20
        if free < config['required_free_MiB'][mid]:
            raise RuntimeError('RESOURCE_PRELOAD_FREE_VRAM_GUARD')
        checked(spec['checkpoint'], spec['checkpoint_sha256'])
        checked(spec['native_config'], spec['native_config_sha256'])
        source_commit = subprocess.check_output(['git','-C',str(W/spec['source']),'rev-parse','HEAD'], text=True).strip()
        if source_commit != spec['source_commit']:
            raise ValueError('Source git revision mismatch')
        torch.set_num_threads(2)
        torch.manual_seed(config['seed'])
        np.random.seed(config['seed'])
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        atomic(output/'RESOURCE_AT_LOAD.json', telemetry())
        before_load = time.monotonic()
        model = CropModel(W, spec, output)
        torch.cuda.synchronize()
        state['model_load_seconds'] = time.monotonic()-before_load
        atomic(output/'ENVIRONMENT.json', dict(python=sys.version, executable=sys.executable,
            torch=torch.__version__, CUDA=torch.version.cuda, GPU=torch.cuda.get_device_name(0),
            CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'), numpy=np.__version__,
            config_sha256=sha(cp), source_commit=source_commit, FP32=True, AMP=False, TF32=False))
        warm = config['warmup']
        path = checked(warm['image'], warm['png_sha256'])
        rgb = np.asarray(Image.open(path).convert('RGB'))
        state['status'] = 'TRAIN_READINESS'
        baseline, _ = infer(rgb, path, warm['designated_box'], 'TRAIN_BASELINE')
        result, timing = infer(rgb, path, warm['designated_box'], 'TRAIN_TIMED_PARITY')
        if not np.array_equal(baseline[0], result[0]) or not np.array_equal(baseline[1], result[1]):
            raise ValueError('INSTRUMENTATION_HARD_MASK_PARITY_FAILURE')
        validate_native(result[0], model.classes, rgb.shape[:2])
        probe = write_packet(output/'readiness', 'TRAIN0000930',
            dict(native_crop_mask=result[0], native_candidate_masks=result[1]),
            dict(config_sha256=sha(cp), checkpoint_sha256=spec['checkpoint_sha256'], timing=timing,
                 geometry=result[2], purpose='TRAIN_NOT_VALIDATION'), {})
        read_packet(probe)
        readiness_bytes = sum(p.stat().st_size for p in probe.iterdir() if p.is_file())
        estimate = (readiness_bytes*config['ROI_count']+config['storage']['final_arrays_uncompressed_per_model_bytes'])*1.25
        if estimate > config['max_stream_gib']*2**30:
            raise RuntimeError('RESOURCE_TRAIN_STORAGE_ESTIMATE_EXCEEDS_STREAM_CAP')
        if shutil.disk_usage(root).free-estimate < config['minimum_free_gib']*2**30:
            raise RuntimeError('RESOURCE_TRAIN_STORAGE_ESTIMATE_EXCEEDS_FREE_DISK')
        atomic(output/'READINESS.json',dict(status='PASS', TRAIN_calls=2,
            original_vs_instrumented_native_hard_masks='IDENTICAL_ON_TRAIN_ROI',
            resource_observation=telemetry(),
            projected_storage_bytes=estimate, estimate_limitation='One TRAIN ROI, larger candidate sets remain guarded',
            native_classes=model.classes, model_details_sha256=sha(output/'MODEL_DETAILS.json')))
        del baseline, result
        space = 'SAPIENS2_DOME29_PRED' if model.classes == 29 else 'CIHP_GT_AND_NATIVE_PRED'
        protocol = load_spec(W/config['protocol'])
        gtroot = W/config['GT_binding_root']
        checked(rel(gtroot/'BINDINGS.jsonl'), config['GT_binding_manifest_sha256'])
        bindings = {b['image_id']: b for b in map(json.loads, (gtroot/'BINDINGS.jsonl').read_text().splitlines())}
        state['status'] = 'VALIDATION_RUNNING'
        save()
        for frame in manifest['frames']:
            guard()
            m, d = frame['member'], frame['detector']
            iid = m['id']
            state['current_id'] = iid
            if state['completed'] % 100 == 0:
                emit(ledger, event='RESOURCE_SNAPSHOT', observations=telemetry())
                verify_config(cp)
            save()
            before_frame = time.monotonic()
            before_input = time.monotonic()
            image, rgb, extents, scores = load_frame(frame)
            input_seconds = time.monotonic()-before_input
            raw, owned, geometry, observations = [], [], [], []
            for j, opportunity in enumerate(d['opportunities']):
                before_crop = time.monotonic()
                crop, box = detector_crop(rgb, opportunity['bbox'], extents[j], .1)
                path = root/'crops'/(iid+'_%03d.png'%j)
                path.parent.mkdir(exist_ok=True)
                if not path.exists():
                    Image.fromarray(crop).save(path)
                if not np.array_equal(np.asarray(Image.open(path).convert('RGB')), crop):
                    raise ValueError('Shared crop RGB mismatch')
                crop_seconds = time.monotonic()-before_crop
                designated = [opportunity['bbox'][k]-box[k%2] for k in range(4)]
                (native, candidates, details), timing = infer(crop, path, designated, 'VAL')
                before_ownership = time.monotonic()
                r, o = place(native, box, extents[j], model.classes)
                ownership_seconds = time.monotonic()-before_ownership
                raw.append(r)
                owned.append(o)
                details.update(opportunity_id=opportunity['id'], crop_xyxy=box,
                               crop_pixel_sha256=pixel_sha(crop), crop_png_sha256=sha(path))
                geometry.append(details)
                before_roi_commit = time.monotonic()
                roi = write_packet(output/'roi_packets', iid+'_%03d'%j,
                    dict(native_crop_mask=native, native_candidate_masks=candidates),
                    dict(config_sha256=sha(cp), model_id=mid, input_sha256=m['RGB_sha256'],
                         checkpoint_sha256=spec['checkpoint_sha256'], geometry=details, timing=timing), {})
                read_packet(roi)
                bytes_written += sum(p.stat().st_size for p in roi.iterdir() if p.is_file())
                observations.append(dict(opportunity_id=opportunity['id'], crop_prepare_seconds=crop_seconds,
                    association_ownership_seconds=ownership_seconds, measurements=timing,
                    roi_export_commit_readback_seconds=time.monotonic()-before_roi_commit))
            h, w = rgb.shape[:2]
            arrays = dict(native_roi_unowned_semantic_masks=np.asarray(raw,np.uint8).reshape(-1,h,w),
                person_semantic_masks=np.asarray(owned,np.uint8).reshape(-1,h,w),
                person_extents=extents, person_scores=scores,
                bboxes_xyxy=np.asarray([op['bbox'] for op in d['opportunities']],np.float32).reshape(-1,4))
            before_export = time.monotonic()
            packet = write_packet(output/'packets', iid, arrays,
                dict(image_id=iid, model_id=mid, original_wh=m['wh'], route=config['route'], label_space=space,
                     checkpoint_sha256=spec['checkpoint_sha256'], input_sha256=m['RGB_sha256'],
                     config_sha256=sha(cp), protocol_sha256=config['protocol_sha256'],
                     detector_sha256=d['artifact_sha256'], geometry=geometry,
                     model_details_sha256=sha(output/'MODEL_DETAILS.json'), environment_sha256=sha(output/'ENVIRONMENT.json'),
                     confidence_kind='FROZEN_YOLO_DETECTION_NOT_PARSING_CONFIDENCE', GT_used_in_prediction=False), {})
            meta, saved = read_packet(packet)
            export_seconds = time.monotonic()-before_export
            frame_wall = time.monotonic()-before_frame
            bytes_written += sum(p.stat().st_size for p in packet.iterdir() if p.is_file())
            before_scoring = time.monotonic()
            category_path = W/'datasets/CIHP/Validation/Category_ids'/(iid+'.png')
            human_path = W/'datasets/CIHP/Validation/Human_ids'/(iid+'.png')
            checked(rel(category_path), m['GT_sha256']['Category_ids'])
            checked(rel(human_path), m['GT_sha256']['Human_ids'])
            evaluation = evaluate(np.asarray(Image.open(category_path)), np.asarray(Image.open(human_path)),
                                  saved, space, protocol)
            binding = bindings[iid]
            checked(rel(gtroot/(iid+'.npz')), binding['derived_sha256'])
            actual = evaluation['scores']['0.5']['GT_binding']
            for key in ['projected_sha256', 'valid_sha256', 'person_valid_sha256', 'G_loc', 'G_sem_C4', 'persons']:
                if actual[key] != binding[key]:
                    raise ValueError('GT-only eligibility/domain binding differs: '+key)
            accumulator.add(iid, evaluation['scores'])
            accumulator.hist += np.asarray(evaluation['scores']['0.5']['histogram'],np.int64)
            for part in evaluation['parts']:
                target = part_sums[str(part['target'])]
                target['count'] += 1
                target['IoU_sum'] += part['IoU']
                for k in ['TP','FP','FN']:
                    target[k] += part[k]
                target['unmatched'] += int(part['unmatched'])
            scorepath = output/'scores'/(iid+'.json')
            atomic(scorepath, dict(image_id=iid, source_packet_sha256=meta['packet_sha256'], **evaluation))
            emit(ledger, event='FRAME_COMMITTED', image_id=iid, packet_sha256=meta['packet_sha256'],
                score_sha256=sha(scorepath), ROI_count=len(extents), input_decode_and_cache_seconds=input_seconds,
                cached_route_wall_seconds=frame_wall, frame_export_commit_readback_seconds=export_seconds,
                scoring_seconds=time.monotonic()-before_scoring, ROI_timings=observations,
                bytes_written=bytes_written)
            state['completed'] += 1
            state['bytes_written'] = bytes_written
            save()
        verify_config(cp)
        result = accumulator.report()
        actual_ids = {p.name for p in (output/'packets').iterdir() if p.is_dir() and not p.name.startswith('.')}
        if actual_ids != set(manifest['expected_ids']) or state['ROI_calls'] != config['ROI_count']:
            raise ValueError('Closure exact image/ROI membership mismatch')
        for key, count in config['GT_expected_sums'].items():
            if result['person_metrics']['0.5'][key] != count:
                raise ValueError('Closure GT person denominator mismatch')
        for target, count in config['GT_expected_part_counts'].items():
            if part_sums[target]['count'] != count:
                raise ValueError('Closure GT part denominator mismatch')
        hist = np.asarray(result['histogram'], np.int64)
        denominator = hist.sum(0)+hist.sum(1)
        result['primary']['F1_Dice'] = [2*int(hist[c,c])/int(denominator[c]) if denominator[c] else None for c in range(6)]
        for values in part_sums.values():
            values['mean_part_IoU'] = values['IoU_sum']/values['count'] if values['count'] else None
            union = values['TP']+values['FP']+values['FN']
            values['pooled_IoU'] = values['TP']/union if union else None
        result.update(scope=config['protocol_id'], parts=part_sums,
            source_config_sha256=sha(cp), source_route=config['route'],
            interpretation='CIHP reference Face proxy; mean GT-person-part uses mask matching0.50',
            timing='Cached route diagnostics, transfer/internal API stages may be inclusive')
        atomic(output/'METRICS.json',result)
        state.update(status='COMPLETE', primary=result['primary'], ended_utc=utc())
        atomic(output/'COMPLETION.json',dict(state, missing=0, duplicate=0, packets=5000,
            metrics_sha256=sha(output/'METRICS.json'), strict_complete=True))
    except BaseException as exc:
        error_kind = 'MODEL_OOM' if 'CUDA out of memory' in str(exc) else 'REQUIRES_RECONCILIATION'
        state.update(status='STOPPED_INCOMPLETE', failed=int(state['ROI_calls']>0),
                     setup_failed=int(state['ROI_calls']==0), invalid=int(isinstance(exc, ValueError)),
                     error_kind=error_kind, error=repr(exc), ended_utc=utc())
        atomic(output/'FAILURE.json',dict(state, traceback=traceback.format_exc(), current_id=state.get('current_id')))
        atomic(output/'COMPLETION.json',dict(state, missing=5000-state['completed'], strict_complete=False))
        raise
    finally:
        state['execution_wall_seconds'] = time.monotonic()-started
        save()
        ledger.close()


def controller(cp):
    config = verify_config(cp)
    config_digest = sha(cp)
    root = W/config['artifact_root']
    lock = (H/'outputs/CONTROLLED_CIHP_CONTROLLER.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (root/'CONTROLLER.json').exists():
        raise FileExistsError('Use controlled reconciliation after prior controller attempt')
    acceptance = read(H/'reports/CONTROLLED_CIHP_CPU_ACCEPTANCE.json')
    if acceptance['status'] != 'PASS' or acceptance['source_hashes'] != {
        rel(p): sha(p) for p in (H/'src/controlled_ci_hp').glob('*.py')}:
        raise ValueError('CPU acceptance source binding mismatch')
    state = dict(status='RUNNING', pid=os.getpid(), started_utc=utc(), models={}, worker_pid=None,
                 analyze_only_after_terminal=True, queue_stopped=False)
    atomic(root/'CONTROLLER.json',state)
    for mid in config['model_order']:
        if sha(cp) != config_digest:
            raise ValueError('Controller config changed during batch')
        state['current_model'] = mid
        state['status'] = 'QUEUED_RESOURCE'
        atomic(root/'CONTROLLER.json',state)
        waiting = time.monotonic()
        while True:
            free = float(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free',
                '--format=csv,noheader,nounits'],text=True).splitlines()[0])
            if free >= config['required_free_MiB'][mid]:
                break
            if time.monotonic()-waiting >= config['resource_queue_timeout_seconds']:
                state.update(status='STOPPED_RESOURCE', queue_stopped=True, free_MiB=free)
                atomic(root/'CONTROLLER.json',state)
                return
            time.sleep(15)
        state['queue_wait_seconds'] = time.monotonic()-waiting
        env = os.environ.copy()
        if config['models'][mid]['family'] == 'Sapiens2':
            env['PYTHONPATH'] = str(W/config['models'][mid]['source'])
        command = [str(W/config['models'][mid]['environment']/'bin/python'), '-u', str(Path(__file__)),
                   'worker', '--config', str(cp), '--model', mid]
        log = (root/(mid+'.log')).open('x')
        process = subprocess.Popen(command, cwd=W, env=env, stdout=log, stderr=subprocess.STDOUT)
        state.update(status='MODEL_RUNNING', worker_pid=process.pid, command=command)
        atomic(root/'CONTROLLER.json',state)
        code = process.wait()
        log.close()
        state['models'][mid] = dict(returncode=code, completed_utc=utc())
        state['worker_pid'] = None
        atomic(root/'CONTROLLER.json',state)
        if code and (root/mid/'FAILURE.json').exists():
            failure = read(root/mid/'FAILURE.json')
            if failure.get('error_kind') == 'MODEL_OOM':
                state['models'][mid]['terminal'] = 'MODEL_OOM_NO_RETRY'
                atomic(root/'CONTROLLER.json', state)
                continue
        if code:
            # Unknown/shared failures stop before another checkpoint.
            state.update(status='STOPPED_REQUIRES_RECONCILIATION', queue_stopped=True)
            atomic(root/'CONTROLLER.json',state)
            return
    terminal = 'BATCH_COMPLETE' if all(m['returncode']==0 for m in state['models'].values()) else 'BATCH_TERMINAL_WITH_INCOMPLETE_SYSTEMS'
    state.update(status=terminal, queue_stopped=True, ended_utc=utc())
    atomic(root/'CONTROLLER.json',state)


def progress(cp):
    config = read(cp)
    root = W/config['artifact_root']
    state = read(root/'CONTROLLER.json') if (root/'CONTROLLER.json').exists() else {'status':'PREPARED'}
    print(config['run_id'], utc(), state['status'])
    print('Controller',state.get('pid'),'Worker',state.get('worker_pid'),'Model',state.get('current_model'))
    for mid in config['model_order']:
        p = root/mid/'STATE.json'
        m = read(p) if p.exists() else {}
        print(mid, m.get('status','NOT_STARTED'), str(m.get('completed',0))+'/5000', 'ROI_calls', m.get('ROI_calls',0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','controller','worker','progress'])
    parser.add_argument('--config',type=Path)
    parser.add_argument('--model')
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'worker':
        worker(args.config,args.model)
    elif args.action == 'controller':
        controller(args.config)
    else:
        cp = args.config
        if cp is None:
            run = (H/'outputs/CURRENT_CONTROLLED_CIHP.txt').read_text().strip()
            cp = H/'outputs'/run/'CONFIG.json'
        progress(cp)

if __name__ == '__main__':
    main()
