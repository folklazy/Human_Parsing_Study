"""Bounded Sapiens0.4B input diagnostic. Separate immutable run, no full benchmark."""
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
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

import numpy as np
from PIL import Image
import torch
import cv2

P = Path(__file__).resolve().parents[1]; W = P.parent
sys.path[:0] = [str(W / 'Human_Parsing_Benchmark/src'), str(P / 'scripts')]
from common_view.core import sha_file, load_spec, project, validate_prediction
from common_view.packets import atomic_json, write_packet, read_packet
from common_view.sapiens_route import prepare_rgb, logits_to_native, ownership_planes
from sapiens_input_variants import letterbox, restore_letterbox, detector_crop, place_roi
from selected_part_evaluation import counts, measures, export_csv, TARGETS

ROUTES = ['FULL_FRAME_STRETCH', 'FULL_FRAME_LETTERBOX', 'YOLO_ROI_LETTERBOX']


def read(path):
    return json.loads(Path(path).read_text())


def utc():
    return datetime.now(timezone.utc).isoformat()


def execute(cp):
    c = read(cp); root = W / c['artifact_root']; parent = read(W / c['parent_config'])
    if (root / 'STATE.json').exists():
        raise FileExistsError('Existing attempt: reconcile, never restart automatically')
    lock = (P / 'outputs/SAPIENS_INPUT_DIAGNOSTIC.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state = dict(status='INITIALIZING', started_utc=utc(), pid=os.getpid(), model_calls=0,
                 max_model_calls=c['max_model_calls'], completed_frames=0, model_id=c['model_id'])
    ledger = (root / 'ATTEMPTS.jsonl').open('x', buffering=1)
    start = time.monotonic(); stats = []; summaries = []; scores_by_route = defaultdict(list)

    def save_state():
        atomic_json(root / 'STATE.json', state)

    def event(row):
        ledger.write(json.dumps(dict(utc=utc(), **row), allow_nan=False) + '\n')
        ledger.flush(); os.fsync(ledger.fileno())

    def guard():
        if shutil.disk_usage(root).free < 50 * 2**30:
            raise RuntimeError('DISK_FREE_GUARD')
        if sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) > 5 * 2**30:
            raise RuntimeError('DIAGNOSTIC_5GiB_GUARD')
        if time.monotonic() - start > 3600:
            raise RuntimeError('DIAGNOSTIC_1h_GUARD')
        if any(sha_file(W / p) != h for p, h in c['source_hashes'].items()):
            raise RuntimeError('FROZEN_SOURCE_DRIFT')

    def forward(tensor, purpose, iid):
        guard()
        if state['model_calls'] >= c['max_model_calls']:
            raise RuntimeError('MODEL_CALL_BUDGET')
        if tensor.shape != (1, 3, 1024, 768) or tensor.dtype != torch.float32 or not torch.isfinite(tensor).all():
            raise ValueError('Actual model input contract failure')
        if torch.cuda.mem_get_info(0)[0] < 1024 * 2**20:
            raise RuntimeError('FREE_VRAM_HEADROOM_GUARD')
        if model.training or torch.is_autocast_enabled() or torch.backends.cuda.matmul.allow_tf32 or torch.backends.cudnn.allow_tf32:
            raise RuntimeError('Precision/eval execution drift')
        state['model_calls'] += 1; state.update(status='FORWARD', purpose=purpose, current_id=iid); save_state()
        event(dict(event='FORWARD_START', call=state['model_calls'], purpose=purpose, image_id=iid))
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
        t0 = time.monotonic()
        with torch.inference_mode():
            output = model(tensor.cuda())
        torch.cuda.synchronize()
        if output.ndim != 4 or output.shape[:2] != (1, 29) or output.dtype != torch.float32 or not torch.isfinite(output).all():
            raise ValueError('Native29 output contract failure')
        row = dict(call=state['model_calls'], purpose=purpose, image_id=iid,
                   diagnostic_seconds=time.monotonic() - t0,
                   peak_allocated_MiB=torch.cuda.max_memory_allocated() / 2**20,
                   peak_reserved_MiB=torch.cuda.max_memory_reserved() / 2**20)
        stats.append(row); event(dict(event='FORWARD_END', **row))
        return output

    save_state()
    try:
        guard(); assert sha_file(W / c['parent_config']) == c['parent_config_sha256']
        assert sha_file(W / c['GT_binding']) == c['GT_binding_sha256']
        free = float(subprocess.check_output(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).splitlines()[0])
        if free < 4608:
            raise RuntimeError('SAPIENS04_READINESS_FREE_VRAM_UNDER_4608MiB')
        m = parent['models'][c['model_id']]
        assert sha_file(W / m['native_config']) == m['native_config_sha256']
        assert sha_file(W / m['checkpoint']) == m['checkpoint_sha256']
        source = W / m['source']
        assert subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() == m['source_commit']
        assert subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True) == ''
        torch.manual_seed(parent['seed']); np.random.seed(parent['seed']); torch.set_num_threads(2)
        torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
        from sapiens.dense.models import init_model
        from safetensors.torch import load_file
        model = init_model(W / m['native_config'], checkpoint=None, device='cpu')
        weights = load_file(W / m['checkpoint'], device='cpu'); model.load_state_dict(weights, strict=True); del weights
        model.float().eval().cuda()
        assert all(p.dtype == torch.float32 for p in model.parameters())
        atomic_json(root / 'ENVIRONMENT.json', dict(python=sys.version, torch=torch.__version__, cuda=torch.version.cuda,
            GPU=torch.cuda.get_device_name(0), OpenCV=cv2.__version__, numpy=np.__version__, parameters=sum(p.numel() for p in model.parameters()),
            model_training=model.training, AMP=False, TF32=False, batch_size=1, automatic_retries=0, CPU_fallback=False,
            CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'), cudnn_benchmark=torch.backends.cudnn.benchmark,
            cudnn_deterministic=torch.backends.cudnn.deterministic))
        warm = W / 'datasets/CIHP/Training/Images/0000930.jpg'
        rgb = np.array(Image.open(warm).convert('RGB')); tensor, _ = prepare_rgb(rgb, model.pipeline, model.data_preprocessor)
        output = forward(tensor, 'TRAIN_WARMUP', 'TRAIN0000930'); del output, tensor
        if c.get('reuse_accepted_full_frame_baselines'):
            for path, digest in c['parent_attempt_evidence'].items():
                if sha_file(W / path) != digest:
                    raise RuntimeError('PARENT_ATTEMPT_EVIDENCE_CHANGED')
            parent_parity = read(W / c['parent_parity_path'])
            if not parent_parity['input_equal'] or not parent_parity['native_mask_equal'] or parent_parity['saved_native_mask_agreement'] != 1.:
                raise RuntimeError('PARENT_MASK_LEVEL_COMPATIBILITY_NOT_ESTABLISHED')
            atomic_json(root / 'REFERENCE_GATE_EVIDENCE.json', dict(raw_logit_allclose_pass=False, mask_level_compatibility=True, parent_evidence=c['parent_attempt_evidence']))
        binding = read(W / c['GT_binding']); spec = load_spec(W / parent['projection'])
        matches = {(r['image_id'], r['person_id']): r['YOLO_opportunity_id'] for r in binding['matches']}
        gt_records = defaultdict(list)
        for r in binding['part_records']:
            if r['primary_eligible']:
                gt_records[r['image_id']].append(r)
        parent_root = (W / c['parent_config']).parent
        source_packets = []
        for index, iid in enumerate(c['image_ids']):
            sample = next(s for s in parent['members'] if s['id'] == iid)
            image = W / parent['dataset_root'] / 'Images' / (sample['stem'] + '.jpg')
            assert sha_file(image) == sample['RGB_sha256']
            rgb = np.array(Image.open(image).convert('RGB')); h, w = rgb.shape[:2]
            old = parent_root / c['model_id'] / 'packets' / iid
            old_meta, old_arrays = read_packet(old)
            assert old_meta['checkpoint_sha256'] == m['checkpoint_sha256'] and old_meta['input_sha256'] == sample['RGB_sha256']
            assert old_meta['config_sha256'] == c['parent_config_sha256']
            det = parent_root / 'YOLO26X/packets' / iid; dm = read(det / 'COMMIT.json')
            assert sha_file(det / 'detector.npz') == old_meta['detector_sha256'] == dm['artifact_sha256']
            with np.load(det / 'detector.npz', allow_pickle=False) as z:
                extents, detector_scores = z['masks'], z['scores']
            opportunities = dm['opportunities']
            assert len(opportunities) == len(extents) == len(detector_scores)
            category_path = W / parent['dataset_root'] / 'Category_ids' / (sample['stem'] + '.png')
            human_path = W / parent['dataset_root'] / 'Human_ids' / (sample['stem'] + '.png')
            assert sha_file(category_path) == sample['GT_sha256']['Category_ids'] and sha_file(human_path) == sample['GT_sha256']['Human_ids']
            # GT is used only for scoring after each independent prediction export.
            category, human = np.array(Image.open(category_path)), np.array(Image.open(human_path))
            lookup = {op['id']: j for j, op in enumerate(opportunities)}
            if c.get('reuse_accepted_full_frame_baselines', False):
                baseline_agreement = None
                predictions = {ROUTES[0]: (old_arrays, old_meta['geometry'])}
            else:
                tensor, geometry = prepare_rgb(rgb, model.pipeline, model.data_preprocessor)
                if index == 0:
                    official = model.data_preprocessor(model.pipeline(dict(img=cv2.imread(str(image)))))['inputs']
                    assert torch.equal(tensor, official)
                    reference_output = forward(official, 'OFFICIAL_FORWARD_REFERENCE', iid)
                    reference_native = logits_to_native(reference_output, (h, w))
                    reference_logits = reference_output.detach().cpu()
                    del reference_output
                    np.save(root / 'REFERENCE_INPUT.npy', official.detach().cpu().numpy())
                    np.save(root / 'REFERENCE_LOGITS.npy', reference_logits.numpy())
                    del official
                logits = forward(tensor, ROUTES[0], iid)
                native = logits_to_native(logits, (h, w))
                baseline_agreement = float(np.mean(native == old_arrays['native_full_frame_semantic_mask']))
                if index == 0:
                    current = logits.detach().cpu()
                    parity = dict(input_equal=True, logits_max_abs_error=float((current - reference_logits).abs().max()),
                        logits_allclose=bool(torch.allclose(current, reference_logits, atol=1e-5, rtol=1e-5)),
                        native_mask_equal=bool(np.array_equal(native, reference_native)),
                        saved_native_mask_agreement=baseline_agreement)
                    atomic_json(root / 'FORWARD_PARITY.json', parity)
                    np.save(root / 'WRAPPER_LOGITS.npy', current.numpy())
                    if not parity['logits_allclose'] or not parity['native_mask_equal']:
                        raise RuntimeError('OFFICIAL_WRAPPER_FORWARD_PARITY_FAILED')
                    del current, reference_logits, reference_native
                if baseline_agreement != 1.:
                    atomic_json(root / 'BASELINE_DISAGREEMENT.json', dict(image_id=iid, agreement=baseline_agreement,
                        source_packet_sha256=old_meta['packet_sha256']))
                    raise RuntimeError('FRESH_BASELINE_DIFFERS_FROM_SAVED_NATIVE_MASK')
                del logits, tensor
                predictions = {ROUTES[0]: (ownership_planes(native, extents, detector_scores), geometry)}
            tensor, geom, preview = letterbox(rgb, model.data_preprocessor)
            logits = forward(tensor, ROUTES[1], iid); native = restore_letterbox(logits, geom)
            predictions[ROUTES[1]] = (ownership_planes(native, extents, detector_scores), geom)
            if index < 2:
                Image.fromarray(preview).save(root / (iid + '_letterbox_input.png'))
            del logits, tensor
            unowned = []; owned = []; roi_geometry = []
            for j, op in enumerate(opportunities):
                crop, box = detector_crop(rgb, op['bbox'], extents[j], context=c['ROI_context_each_side'])
                tensor, geom, preview = letterbox(crop, model.data_preprocessor)
                logits = forward(tensor, ROUTES[2] + ':' + str(j), iid)
                native_crop = restore_letterbox(logits, geom)
                raw, final = place_roi(native_crop, box, extents[j]); unowned.append(raw); owned.append(final)
                roi_geometry.append(dict(opportunity_id=op['id'], crop_xyxy=box, **geom))
                if index < 2:
                    Image.fromarray(preview).save(root / (iid + '_roi_' + str(j) + '_input.png'))
                del logits, tensor
            roi_arrays = dict(native_roi_unowned_semantic_masks=np.asarray(unowned, np.uint8).reshape(-1, h, w),
                person_semantic_masks=np.asarray(owned, np.uint8).reshape(-1, h, w),
                person_extents=extents.copy(), person_scores=detector_scores.copy())
            predictions[ROUTES[2]] = (roi_arrays, roi_geometry)
            for route, (arrays, geom) in predictions.items():
                validate_prediction(arrays['person_semantic_masks'], arrays['person_extents'], arrays['person_scores'], (h, w), 'SAPIENS2_DOME29_PRED')
                assert np.array_equal(arrays['person_extents'], old_arrays['person_extents'])
                assert np.array_equal(arrays['person_scores'], old_arrays['person_scores'])
                metadata = dict(model_id=c['model_id'], image_id=iid, route=route,
                    original_wh=[w, h], input_sha256=sample['RGB_sha256'], checkpoint_sha256=m['checkpoint_sha256'],
                    native_config_sha256=m['native_config_sha256'], source_commit=m['source_commit'],
                    source_packet_sha256=old_meta['packet_sha256'], detector_sha256=dm['artifact_sha256'],
                    diagnostic_config_sha256=sha_file(cp), projection_sha256=parent['projection_sha256'],
                    prediction_disposition='REUSED_ACCEPTED_NATIVE_PACKET' if route == ROUTES[0] and c.get('reuse_accepted_full_frame_baselines') else 'NEW_DIAGNOSTIC_INFERENCE',
                    geometry=geom, precision='FP32', GT_used_in_prediction=False, resource_policy='SHARED_GPU_QUALITY_ONLY')
                packet = write_packet(root / route / 'packets', iid, arrays, metadata, {})
                _, again = read_packet(packet)
                mapped = project(again['person_semantic_masks'], 'SAPIENS2_DOME29_PRED', spec)
                rows = []
                for part in gt_records[iid]:
                    n, k = TARGETS[part['target']]; gt = (human == part['person_id']) & (category == n)
                    assert int(gt.sum()) == part['GT_pixels']
                    j = lookup.get(matches[iid, part['person_id']])
                    pred = mapped[j] == k if j is not None else np.zeros((h, w), bool)
                    tp, fp, fn = counts(gt, pred)
                    rows.append(dict(image_id=iid, person_id=part['person_id'], target=part['target'], condition=sample['condition'],
                        TP=tp, FP=fp, FN=fn, GT_pixels=int(gt.sum()), detector_miss=j is None, **measures(tp, fp, fn)))
                atomic_json(packet / 'DIAGNOSTIC_SCORES.json', dict(parts=rows, original_GT_sha256=sample['GT_sha256']))
                scores_by_route[route].extend(rows)
            source_packets.append(dict(image_id=iid, source_packet_sha256=old_meta['packet_sha256'], baseline_saved_agreement=baseline_agreement, baseline_reused=bool(c.get('reuse_accepted_full_frame_baselines'))))
            state['completed_frames'] += 1; state['status'] = 'FRAME_COMMITTED'; save_state()
            event(dict(event='FRAME_COMMITTED', image_id=iid, routes=ROUTES))
            del predictions, old_arrays, roi_arrays
        for route in ROUTES:
            for group in ['overall', 'day', 'night']:
                rr = [r for r in scores_by_route[route] if group == 'overall' or r['condition'] == group]
                target_metrics = []
                for name in TARGETS:
                    rs = [r for r in rr if r['target'] == name]
                    tp, fp, fn = [sum(r[k] for r in rs) for k in ['TP', 'FP', 'FN']]
                    row = dict(route=route, group=group, target=name, GT_parts=len(rs), GT_pixels=tp+fn,
                        detector_miss_parts=sum(r['detector_miss'] for r in rs), TP=tp, FP=fp, FN=fn,
                        mean_part_IoU=float(np.mean([r['IoU'] for r in rs])) if rs else None,
                        mean_part_Dice=float(np.mean([r['Dice'] for r in rs])) if rs else None,
                        **{'pooled_' + k: v for k, v in measures(tp, fp, fn).items()})
                    summaries.append(row); target_metrics.append(row)
                stats_row = dict(route=route, group=group, frames=sum(s['condition']==group or group=='overall' for s in c['members']),
                    GT_parts=len(rr), macro_mean_part_IoU4=float(np.mean([r['mean_part_IoU'] for r in target_metrics])) if all(r['GT_parts'] for r in target_metrics) else None,
                    macro_mean_part_Dice4=float(np.mean([r['mean_part_Dice'] for r in target_metrics])) if all(r['GT_parts'] for r in target_metrics) else None)
                stats.append(stats_row)
        export_csv(root / 'PER_TARGET.csv', summaries)
        export_csv(root / 'SUMMARY.csv', [r for r in stats if 'macro_mean_part_IoU4' in r])
        atomic_json(root / 'RESOURCE_OBSERVATIONS.json', dict(forwards=[r for r in stats if 'call' in r], timing_scope='Model forward diagnostics only, no speed ranking'))
        atomic_json(root / 'SOURCE_PACKETS.json', source_packets)
        if state['model_calls'] != c['max_model_calls'] or state['completed_frames'] != 6:
            raise RuntimeError('Diagnostic workload reconciliation mismatch')
        state.update(status='DIAGNOSTIC_COMPLETE', ended_utc=utc(), failed=0, invalid=0,
                     PRIMARY_IS_NOT_POPULATION_BENCHMARK=True)
    except BaseException:
        state.update(status='STOPPED_DIAGNOSTIC_INCOMPLETE', ended_utc=utc(), error=traceback.format_exc())
        atomic_json(root / 'FAILURE.json', state)
        raise
    finally:
        save_state(); ledger.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    execute(parser.parse_args().config)
