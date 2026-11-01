"""CPU-only, selected-annotated-part evaluation of immutable saved packets.

Private per-person records remain under outputs/. Public exports are aggregate only.
This module never imports a model, writes source GT or modifies native packets.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import argparse
import csv
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment

P = Path(__file__).resolve().parents[1]
W = P.parent
TARGETS = {'Face': (13, 1), 'Hair': (2, 2), 'Upper': (5, 3), 'Lower': (9, 4)}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def counts(gt, pred):
    """Entire person plane: never intersect predictions with GT scope/bbox."""
    if gt.shape != pred.shape or gt.dtype != bool or pred.dtype != bool:
        raise ValueError('Boolean masks on the same original grid required')
    tp = int(np.count_nonzero(gt & pred))
    return tp, int(pred.sum()) - tp, int(gt.sum()) - tp


def measures(tp, fp, fn):
    union = tp + fp + fn
    return dict(IoU=tp / union if union else None,
                Dice=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
                precision=tp / (tp + fp) if tp + fp else None,
                recall=tp / (tp + fn) if tp + fn else None)


def geometry_key(mask):
    yy, xx = np.where(mask)
    return (int(yy.min()), int(xx.min()), int(yy.max()), int(xx.max()),
            len(xx), hashlib.sha256(np.packbits(mask).tobytes()).hexdigest())


def match_gt_to_detector(human, opportunities, threshold=.5):
    """Max cardinality, then bbox coverage; detector-confidence tie resolution.

    GT uses only the union of annotated parts. No parser or target-class score.
    Lexicographically fix each geometry-ordered GT row while preserving the optimal
    cardinality/coverage objective. Identical GT geometry falls back to source ID.
    """
    pids = [int(x) for x in np.unique(human) if x > 0]
    pids.sort(key=lambda k: (geometry_key(human == k), k))
    ops = sorted(opportunities, key=lambda o: (tuple(o['bbox']), o['id']))
    g, n = len(pids), len(ops)
    if not g:
        return {}, []
    k = g + n + 1
    score = np.full((g, n + g), -float(k))
    score[:, n:] = 0
    h, w = human.shape
    for i, pid in enumerate(pids):
        mask = human == pid
        for j, op in enumerate(ops):
            x0, y0, x1, y1 = op['bbox']
            x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
            x1, y1 = min(w, int(np.ceil(x1))), min(h, int(np.ceil(y1)))
            coverage = float(mask[y0:y1, x0:x1].sum()) / int(mask.sum())
            if coverage >= threshold:
                score[i, j] = k + coverage

    def optimum(rows, cols):
        if not rows:
            return 0.
        s = score[np.ix_(rows, cols)]
        a, b = linear_sum_assignment(s, maximize=True)
        return float(s[a, b].sum())

    available = list(range(n + g))
    remaining = optimum(list(range(g)), available)
    result = {}; ambiguities = []
    for i, pid in enumerate(pids):
        viable = []
        for j in available:
            if score[i, j] < 0:
                continue
            other = [c for c in available if c != j]
            value = score[i, j] + optimum(list(range(i + 1, g)), other)
            if abs(value - remaining) <= 1e-9:
                viable.append(j)
        real = [j for j in viable if j < n]
        if len(real) > 1:
            ambiguities.append(pid)
        if real:
            j = min(real, key=lambda v: (-float(ops[v]['score']), tuple(ops[v]['bbox']), ops[v]['id']))
        else:
            j = viable[0]
        result[pid] = ops[j]['id'] if j < n else None
        remaining -= score[i, j]
        available.remove(j)
    return result, ambiguities


def final_plane_lookup(meta, arrays, detector_arrays, opportunities):
    planes, extents, scores = (arrays[k] for k in
        ['person_semantic_masks', 'person_extents', 'person_scores'])
    if planes.ndim != 3 or extents.shape != planes.shape or scores.shape != (len(planes),):
        raise ValueError('Malformed final-person packet')
    if not np.isfinite(scores).all() or not set(np.unique(extents)).issubset({0, 1}):
        raise ValueError('Invalid scores/extents')
    allowed = {o['id'] for o in opportunities}
    if 'associations' in meta:
        associations = meta['associations']
        if len(associations) != len(planes):
            raise ValueError('Final plane / association count mismatch')
        # prediction_index identifies the OLD native array, not this selected array.
        ids = [a['YOLO_opportunity_id'] for a in associations]
    elif meta['label_space'] == 'SAPIENS2_DOME29_PRED':
        if not np.array_equal(extents, detector_arrays['masks']) or not np.array_equal(scores, detector_arrays['scores']):
            raise ValueError('Sapiens detector identity/order mismatch')
        ids = [o['id'] for o in opportunities]
    else:
        raise ValueError('Missing prediction-only association metadata')
    if len(ids) != len(planes) or len(set(ids)) != len(ids) or not set(ids) <= allowed:
        raise ValueError('Duplicate or unknown opportunity identity')
    return dict(zip(ids, range(len(planes))))


def export_csv(path, rows):
    with Path(path).open('w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        wr.writeheader(); wr.writerows(rows)


def prepare(config_path, review_path, out):
    """Freeze GT-only associations and review eligibility, before new scores."""
    c, review = read(config_path), read(review_path)
    run = Path(config_path).parent
    by_image = defaultdict(list)
    for part in review['part_records']:
        by_image[part['image_id']].append(part)
    matches = []; ambiguous = []
    dataset = W / c['dataset_root']
    for m in c['members']:
        human = np.array(Image.open(dataset / 'Human_ids' / (m['stem'] + '.png')))
        ops = read(run / 'YOLO26X/packets' / m['id'] / 'COMMIT.json')['opportunities']
        assigned, ties = match_gt_to_detector(human, ops)
        matches.extend(dict(image_id=m['id'], person_id=pid, YOLO_opportunity_id=op)
                       for pid, op in assigned.items())
        ambiguous.extend(dict(image_id=m['id'], person_id=pid) for pid in ties)
    result = dict(status='FROZEN_BEFORE_SELECTED_PART_SCORES', created_utc=datetime.now(timezone.utc).isoformat(),
        source_config_sha256=sha(config_path), visual_review_sha256=sha(review_path),
        reviewer=review['reviewer'], review_method=review['review_method'],
        matching='max cardinality, then GT-union bbox coverage >=0.5; equal optima use detector confidence, bbox, stable opportunity ID',
        tie_resolution_note='One duplicate-detector ambiguity visually inspected without parser outputs; confidence tie-break is class/model blind',
        matches=matches, equal_objective_persons=ambiguous, part_records=review['part_records'])
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    atomic(out / 'GT_BINDING.json', result)
    print(json.dumps(dict(output=str(out), parts=len(result['part_records']),
        primary_parts=sum(x['primary_eligible'] for x in result['part_records']),
        shared_detector_misses=sum(x['YOLO_opportunity_id'] is None for x in matches),
        ties=len(ambiguous), GT_binding_sha256=sha(out / 'GT_BINDING.json'))))


def evaluate(config_path, binding_path, protocol_path, out):
    c, binding, protocol = read(config_path), read(binding_path), read(protocol_path)
    if sha(config_path) != binding['source_config_sha256'] or sha(binding_path) != protocol['GT_binding_sha256']:
        raise ValueError('Frozen GT/config identity mismatch')
    if sha(protocol_path) != protocol.get('self_hash', sha(protocol_path)):
        raise ValueError('Invalid optional protocol self binding')
    sys.path.insert(0, str(W / 'Human_Parsing_Benchmark/src'))
    from common_view.core import load_spec, project
    spec_path = W / c['projection']
    if sha(spec_path) != protocol['projection_sha256']:
        raise ValueError('Projection changed')
    spec = load_spec(spec_path)
    run, dataset = Path(config_path).parent, W / c['dataset_root']
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    lock = out / 'FROZEN_INPUTS.json'
    atomic(lock, dict(config_sha256=sha(config_path), GT_binding_sha256=sha(binding_path),
        protocol_sha256=sha(protocol_path), scorer_sha256=sha(__file__), model_calls=0))
    matches = {(r['image_id'], r['person_id']): r['YOLO_opportunity_id'] for r in binding['matches']}
    by_image = defaultdict(list)
    for part in binding['part_records']:
        by_image[part['image_id']].append(part)
    expected = [m['id'] for m in c['members']]
    if len(expected) != 90 or len(set(expected)) != 90:
        raise ValueError('Population mismatch')
    aggregate_rows = []; target_rows = []; evidence = {}
    for mid in c['models']:
        root = out / mid; root.mkdir()
        ledger = root / 'FRAMES.jsonl'
        all_rows = []; verified = []; start = datetime.now(timezone.utc).isoformat()
        atomic(out / 'STATUS.json', dict(status='CPU_SCORING', model_id=mid, completed_models=len(evidence), model_calls=0))
        try:
            for m in c['members']:
                packet = run / mid / 'packets' / m['id']
                commit, meta = read(packet / 'COMMIT.json'), read(packet / 'packet.json')
                for name, digest in commit['members'].items():
                    if sha(packet / name) != digest:
                        raise ValueError('Atomic source packet identity changed')
                if any(meta[key] != value for key, value in dict(model_id=mid, image_id=m['id'],
                        original_wh=m['wh'], input_sha256=m['RGB_sha256'],
                        checkpoint_sha256=c['models'][mid]['checkpoint_sha256'],
                        config_sha256=sha(config_path)).items()):
                    raise ValueError('Packet source binding mismatch')
                if meta['packet_sha256'] != commit['members']['prediction.npz']:
                    raise ValueError('NPZ metadata binding mismatch')
                detector = run / 'YOLO26X/packets' / m['id']
                detmeta = read(detector / 'COMMIT.json')
                if sha(detector / 'detector.npz') != meta['detector_sha256'] or meta['detector_sha256'] != detmeta['artifact_sha256']:
                    raise ValueError('Detector identity mismatch')
                catpath, humanpath = [dataset / kind / (m['stem'] + '.png') for kind in ['Category_ids', 'Human_ids']]
                if sha(catpath) != m['GT_sha256']['Category_ids'] or sha(humanpath) != m['GT_sha256']['Human_ids']:
                    raise ValueError('GT binding changed')
                category, human = np.array(Image.open(catpath)), np.array(Image.open(humanpath))
                with np.load(packet / 'prediction.npz', allow_pickle=False) as z:
                    arrays = {k: z[k] for k in ['person_semantic_masks', 'person_extents', 'person_scores']}
                with np.load(detector / 'detector.npz', allow_pickle=False) as z:
                    da = {k: z[k] for k in ['masks', 'scores']}
                lookup = final_plane_lookup(meta, arrays, da, detmeta['opportunities'])
                planes = arrays['person_semantic_masks']
                if planes.shape[1:] != category.shape or category.shape != tuple(m['wh'][::-1]):
                    raise ValueError('Original-grid geometry mismatch')
                mapped = project(planes, meta['label_space'], spec)
                rows = []
                for part in by_image[m['id']]:
                    name = part['target']; native, target = TARGETS[name]
                    gt = (human == part['person_id']) & (category == native)
                    if int(gt.sum()) != part['GT_pixels'] or not gt.any():
                        raise ValueError('Part domain/support changed')
                    opportunity = matches[m['id'], part['person_id']]
                    index = lookup.get(opportunity)
                    pred = mapped[index] == target if index is not None else np.zeros(gt.shape, bool)
                    tp, fp, fn = counts(gt, pred)
                    rows.append(dict(image_id=m['id'], person_id=part['person_id'], target=name,
                        primary_eligible=part['primary_eligible'], condition=m['condition'],
                        GT_pixels=int(gt.sum()), TP=tp, FP=fp, FN=fn,
                        source_packet_sha256=meta['packet_sha256'],
                        prediction_status='DETECTOR_MISS' if opportunity is None else
                            ('NATIVE_ASSOCIATION_MISS' if index is None else 'PRESENT'), **measures(tp, fp, fn)))
                record = dict(image_id=m['id'], status='COMPLETE', source_packet_sha256=meta['packet_sha256'], parts=rows)
                atomic(root / (m['id'] + '.json'), record)
                with ledger.open('a') as f:
                    f.write(json.dumps(dict(image_id=m['id'], status='COMPLETE', record_sha256=sha(root / (m['id'] + '.json')))) + '\n')
                    f.flush(); os.fsync(f.fileno())
                all_rows.extend(rows); verified.append(m['id'])
                atomic(out / 'STATUS.json', dict(status='CPU_SCORING', model_id=mid, images=len(verified), completed_models=len(evidence), model_calls=0))
            if verified != expected or len(all_rows) != 324:
                raise ValueError('STRICT_COMPLETE reconciliation failed')
            for subset in ['QA_PRIMARY', 'ALL_SOURCE_SENSITIVITY']:
                for group in ['overall', 'day', 'night']:
                    selected = [r for r in all_rows if (subset != 'QA_PRIMARY' or r['primary_eligible']) and (group == 'overall' or r['condition'] == group)]
                    targets = []
                    for name in TARGETS:
                        rs = [r for r in selected if r['target'] == name]
                        tp, fp, fn = [sum(r[k] for r in rs) for k in ['TP', 'FP', 'FN']]
                        row = dict(model_id=mid, subset=subset, group=group, target=name, GT_parts=len(rs),
                            present_parts=sum(r['prediction_status'] == 'PRESENT' for r in rs),
                            detector_miss_parts=sum(r['prediction_status'] == 'DETECTOR_MISS' for r in rs),
                            association_miss_parts=sum(r['prediction_status'] == 'NATIVE_ASSOCIATION_MISS' for r in rs),
                            mean_part_IoU=float(np.mean([r['IoU'] for r in rs])) if rs else None,
                            mean_part_Dice=float(np.mean([r['Dice'] for r in rs])) if rs else None,
                            GT_pixels=tp + fn, prediction_pixels=tp + fp, TP=tp, FP=fp, FN=fn,
                            union=tp + fp + fn, **{'pooled_' + k: v for k, v in measures(tp, fp, fn).items()})
                        targets.append(row); target_rows.append(row)
                    aggregate_rows.append(dict(model_id=mid, subset=subset, group=group,
                        status='COMPLETE', input_images=90, contributing_images=len({r['image_id'] for r in selected}),
                        GT_persons=len({(r['image_id'], r['person_id']) for r in selected}), GT_parts=len(selected),
                        macro_mean_selected_part_IoU4=float(np.mean([r['mean_part_IoU'] for r in targets])) if all(r['GT_parts'] for r in targets) else None,
                        macro_mean_selected_part_Dice4=float(np.mean([r['mean_part_Dice'] for r in targets])) if all(r['GT_parts'] for r in targets) else None))
            evidence[mid] = dict(status='COMPLETE', exact_unique_image_ids=len(verified), failed=0, invalid=0, missing=0,
                source_metrics_sha256=sha(run / mid / 'METRICS.json'), source_ledger_sha256=sha(run / mid / 'FRAMES.jsonl'),
                derived_ledger_sha256=sha(ledger), atomic_NPZ_metadata_score_packets_checked=len(verified),
                started_utc=start, ended_utc=datetime.now(timezone.utc).isoformat())
            atomic(root / 'COMPLETION.json', evidence[mid])
        except Exception as exc:
            atomic(out / 'STATUS.json', dict(status='STOPPED_INCOMPLETE', model_id=mid, completed_images=len(verified),
                primary=None, reason=type(exc).__name__ + ': ' + str(exc), model_calls=0))
            raise
    export_csv(out / 'SUMMARY.csv', aggregate_rows)
    export_csv(out / 'PER_TARGET.csv', target_rows)
    atomic(out / 'EVIDENCE.json', dict(status='COMPLETE_9_OF_9', created_utc=datetime.now(timezone.utc).isoformat(),
        **read(lock), population=90, source_part_records=324, QA_primary_parts=315, models=evidence,
        scores_sha256=sha(out / 'SUMMARY.csv'), targets_sha256=sha(out / 'PER_TARGET.csv'),
        original_GT_and_packets_modified=False, full_scene_IoU_or_person_F1_claimed=False))
    atomic(out / 'STATUS.json', dict(status='COMPLETE_9_OF_9', models=9, images_per_model=90, model_calls=0))
    print(str(out / 'EVIDENCE.json'))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['prepare', 'score'])
    ap.add_argument('--config', required=True, type=Path)
    ap.add_argument('--review', type=Path); ap.add_argument('--binding', type=Path)
    ap.add_argument('--protocol', type=Path); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    if a.action == 'prepare':
        prepare(a.config, a.review, a.out)
    else:
        evaluate(a.config, a.binding, a.protocol, a.out)
