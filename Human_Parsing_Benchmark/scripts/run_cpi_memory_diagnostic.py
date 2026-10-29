"""One bounded CPI memory-repair diagnostic, never canonical/full evaluation."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback

P = Path(__file__).resolve().parents[1]
W = P.parent
sys.path.insert(0, str(P / 'src'))
from cihp_benchmark.data import file_hash, read_image, read_sample
from reconcile_cihp_continuation import write


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    cfgpath = Path(args.config).resolve()
    cfg = json.loads(cfgpath.read_text())
    if not args.execute:
        print(json.dumps({'status': 'NOT_EXECUTED', 'run_id': cfg['run_id'], 'max_calls': 3}))
        return
    frozen = json.loads((W / cfg['frozen_config']).read_text())
    mid = 'CPI_ConvNeXtB_CIHP'
    spec = frozen['models'][mid]
    if Path(sys.prefix).resolve() != (W / spec['environment']).resolve():
        raise ValueError('Frozen CPI environment required')
    if cfg['model_id'] != mid or cfg['calls'] != [['Training', '0000930'], ['Validation', '0003218'], ['Validation', '0001641']]:
        raise ValueError('Three-call ConvNeXt-only diagnostic scope differs')
    if cfg['max_model_frame_calls'] != 3 or cfg['automatic_retries'] != 0:
        raise ValueError('Diagnostic budget differs')
    with (P / 'outputs/cpi_continuations/CPI.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        from run_cpi_continuation import reject_existing_worker
        reject_existing_worker()
        for rel, expected in cfg['protected_hashes'].items():
            if file_hash(W / rel) != expected:
                raise ValueError('Source/config binding differs: ' + rel)
        if file_hash(W / spec['checkpoint']) != spec['checkpoint_sha256']:
            raise ValueError('Checkpoint differs')
        if subprocess.check_output(['git', '-C', str(W / spec['source']), 'rev-parse', 'HEAD'], text=True).strip() != spec['source_commit']:
            raise ValueError('CPI source revision differs')
        root = W / cfg['artifact_root']
        root.mkdir(exist_ok=False, parents=True)
        rec = P / 'runs' / cfg['run_id']
        state = {'run_id': cfg['run_id'], 'model_id': mid, 'status': 'PREPARING',
                 'PID': os.getpid(), 'SID': os.getsid(0), 'start_utc': now(),
                 'model_frame_calls': 0, 'complete': 0, 'failed': 0,
                 'canonical': False, 'primary': None, 'automatic_retries': 0,
                 'resource_policy': 'SHARED_GPU_QUALITY_ONLY',
                 'config_sha256': file_hash(cfgpath),
                 'launch_commit': subprocess.check_output(['git', '-C', str(W / 'Human_Parsing_Study_Public'), 'rev-parse', 'HEAD'], text=True).strip()}
        began = time.monotonic()
        events = []

        def save():
            write(root / 'RUN.json', state)
            write(rec / 'RUN.json', state)

        def guard():
            if shutil.disk_usage(root).free < frozen['minimum_free_gib'] * 2**30:
                raise RuntimeError('FREE_SPACE_GUARD')
            retained = cfg['prior_retained_bytes'] + sum(f.stat().st_size for f in root.rglob('*') if f.is_file())
            if retained > frozen['max_per_system_artifact_gib'] * 2**30:
                raise RuntimeError('CUMULATIVE_STORAGE_GUARD')
            if cfg['prior_execution_seconds'] + time.monotonic() - began > frozen['max_system_hours'] * 3600:
                raise RuntimeError('CUMULATIVE_TIME_GUARD')

        save()
        try:
            import numpy as np
            import torch
            from cihp_benchmark.adapters import NativeAdapter
            from cihp_benchmark.cpi_memory import install, chunked_maps
            from cihp_benchmark.evaluation import score_frame
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            torch.set_num_threads(4)
            torch.manual_seed(frozen['seed'])
            np.random.seed(frozen['seed'])
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            state['GPU_before'] = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.used,memory.free', '--format=csv,noheader'], text=True).strip()
            guard()
            adapter = NativeAdapter(W, spec, root / 'adapter')
            state['model_details'] = adapter.details
            state['patch'] = install(adapter.model.bbox_head, cfg['head_source_sha256'],
                                     observer=events.append, reference_prefix=2)
            # CUDA checks numerical/geometry equivalence before any model frame.
            native_aligned = type(adapter.model.bbox_head)._get_bboxes_single.__globals__['aligned_bilinear']
            fixture_generator = torch.Generator(device='cuda').manual_seed(719)
            x = torch.rand((7, 20, 3, 5), device='cuda', generator=fixture_generator)
            import torch.nn.functional as F
            reference = native_aligned(x, 8)[:, :, :21, :37]
            reference = F.interpolate(reference, size=(17, 43), mode='bilinear', align_corners=True).argmax(1).cpu().numpy()
            actual = chunked_maps(x, 8, (21, 37, 3), (17, 43, 3), True, native_aligned)
            if not np.array_equal(reference, actual):
                raise ValueError('GPU synthetic restoration equivalence failed')
            del x, reference, actual
            state['GPU_synthetic_native_vs_chunked'] = 'PASS_EXACT_LABELS'
            detector = {r['image_id']: r for r in map(json.loads, (W / frozen['frozen_YOLO']['validation_ledger']).read_text().splitlines())}
            training = json.loads((W / frozen['frozen_YOLO']['training_run']).read_text())
            population = {r['id']: r for r in json.loads((W / frozen['dataset']['population']).read_text())['members']}
            with (root / 'ATTEMPTS.jsonl').open('x') as ledger:
                for split, iid in cfg['calls']:
                    guard()
                    if state['model_frame_calls'] >= 3:
                        raise ValueError('Model-frame budget exhausted')
                    rgbpath = W / 'datasets/CIHP' / split / 'Images' / (iid + '.jpg')
                    rgb, input_meta = read_image(rgbpath)
                    if split == 'Training':
                        d = next(r for r in training['images'] if r['image_id'] == iid)
                        detector_path = W / 'Human_Parsing_MHPv2_Study' / d['artifact']
                    else:
                        d = detector[iid]
                        detector_path = W / d['artifact'] if d['artifact'].startswith('Human_Parsing') else W / 'Human_Parsing_MHPv2_Study' / d['artifact']
                        if input_meta['file_sha256'] != population[iid]['RGB_sha256']:
                            raise ValueError('VAL input identity differs')
                        if file_hash(detector_path) != d['artifact_sha256']:
                            raise ValueError('Frozen detector artifact differs')
                    with np.load(detector_path, allow_pickle=False) as z:
                        ownership = z['masks'].copy()
                    attempt = {'split': split, 'image_id': iid, 'start_utc': now(), 'status': 'STARTED', 'attempt': 1}
                    ledger.write(json.dumps(attempt) + '\n'); ledger.flush()
                    state.update(status='DIAGNOSTIC_RUNNING', current_image=iid)
                    state['model_frame_calls'] += 1
                    save()
                    start_events = len(events)
                    torch.cuda.reset_peak_memory_stats()
                    arrays, metadata = adapter.infer(rgb, rgbpath, d['opportunities'], ownership)
                    torch.cuda.synchronize()
                    observed = events[start_events:]
                    packet = root / 'packets' / split / iid
                    packet.mkdir(parents=True, exist_ok=False)
                    temporary = packet / 'prediction.npz.tmp'
                    with temporary.open('xb') as stream:
                        np.savez_compressed(stream, **arrays)
                    temporary.replace(packet / 'prediction.npz')
                    with np.load(packet / 'prediction.npz', allow_pickle=False) as z:
                        readback = {k: z[k] for k in z.files}
                    if set(arrays) != set(readback) or any(not np.array_equal(arrays[k], readback[k]) for k in arrays):
                        raise ValueError('Packet readback differs')
                    for key, value in arrays.items():
                        if 'semantic' in key and (value.dtype.kind not in 'ui' or np.any(value >= 20) or value.shape[-2:] != rgb.shape[:2]):
                            raise ValueError('Native20/original geometry contract failed')
                    regression = None
                    if iid == '0001641' and split == 'Validation':
                        oldpath = W / cfg['regression_packet']
                        if file_hash(oldpath) != cfg['regression_packet_sha256']:
                            raise ValueError('Saved reference packet changed')
                        with np.load(oldpath, allow_pickle=False) as z:
                            if set(z.files) != set(arrays) or any(not np.array_equal(z[k], arrays[k]) for k in z.files):
                                raise ValueError('Previously successful packet differs from chunked diagnostic')
                        regression = 'ALL_ARRAYS_EXACT_EQUAL_TO_SAVED_NATIVE_PACKET'
                    if split == 'Validation':
                        truth, gtmeta = read_sample(W / 'datasets/CIHP', split, iid)
                        for key in ['Category_ids', 'Human_ids', 'Instance_ids']:
                            if gtmeta[key]['file_sha256'] != population[iid]['GT_sha256'][key]:
                                raise ValueError('GT identity changed')
                        for threshold in [.5, .75]:
                            score = score_frame(truth['Category_ids'], truth['Human_ids'], readback['person_semantic_masks'], readback['person_extents'], readback['person_scores'], threshold)
                            write(packet / ('score_' + str(threshold) + '.json'), score)
                        state['complete'] += 1
                    peak = {'peak_allocated_MiB': torch.cuda.max_memory_allocated() / 2**20,
                            'peak_reserved_MiB': torch.cuda.max_memory_reserved() / 2**20}
                    metadata.update(model_id=mid, image_id=iid, split=split, diagnostic=True,
                                    canonical=False, input_sha256=input_meta['file_sha256'],
                                    checkpoint_sha256=spec['checkpoint_sha256'],
                                    frozen_config_sha256=file_hash(W / cfg['frozen_config']),
                                    config_sha256=file_hash(cfgpath), precision='FP32',
                                    patch=state['patch'], packet_sha256=file_hash(packet / 'prediction.npz'),
                                    memory=peak, decoder_events=observed, regression=regression)
                    write(packet / 'packet.json', metadata)
                    attempt.update(status='COMPLETE', end_utc=now(), memory=peak,
                                   decoder_events=observed, regression=regression,
                                   packet=str(packet.relative_to(W)), packet_sha256=metadata['packet_sha256'])
                    ledger.write(json.dumps(attempt) + '\n'); ledger.flush()
                    state.setdefault('observations', []).append(attempt)
                    save()
                    print(json.dumps(attempt), flush=True)
            state['status'] = 'DIAGNOSTIC_PASS'
        except Exception:
            state.update(status='DIAGNOSTIC_FAILED', failed=1, error=traceback.format_exc())
            write(root / 'FAILURE.json', state)
            print(state['error'], flush=True)
        finally:
            state.update(end_utc=now(), execution_seconds=time.monotonic() - began,
                         no_full_benchmark=True, automatic_restart=False)
            save()
            write(root / 'DECODER_EVENTS.json', events)
            print(json.dumps({k: v for k, v in state.items() if k not in ['model_details', 'observations']}), flush=True)
        return 0 if state['status'] == 'DIAGNOSTIC_PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
