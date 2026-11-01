"""CPU saved-packet evaluation with explicit incomplete Face/Neck GT gating.

Reads original-grid controlled-ROI packets. Never imports a model or writes source
annotations, detector caches, predictions, or historical metrics. Private inputs
and per-person results remain under this experiment's ignored outputs directory.
"""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import argparse
import csv
import json
import os
import sys
import traceback
import numpy as np
from PIL import Image
from controlled_roi_core import atomic, read, sha, counts, face_views, reconcile, validate_native
from selected_part_evaluation import match_gt_to_detector, final_plane_lookup

P = Path(__file__).resolve().parents[1]
W = P.parent
SOURCE_IDS = {'Hair': 2, 'Face': 13, 'Upper': 5, 'Lower': 9}
TARGETS = ('Hair', 'FaceDomain', 'Upper', 'Lower')


def now():
    return datetime.now(timezone.utc).isoformat()


def rel(path):
    return str(Path(path).resolve().relative_to(W))


def project_native(plane, family, protocol):
    """One explicit disposition for every native ID; OTHER is never ignored."""
    table = protocol['native_projection'][family]
    validate_native(plane, len(table), plane.shape)
    if set(table) != {str(i) for i in range(len(table))}:
        raise ValueError('Incomplete or nonconsecutive native projection')
    return {name: np.isin(plane, [int(i) for i, target in table.items() if target == name])
            for name in ('Hair', 'FaceCandidate', 'Upper', 'Lower')}


def summarize(rows, expected_parts, execution_complete, face_gt_complete):
    """Equal mean of per-part IoUs within targets, then equal four-target mean.

    The required Face domain is not replaced by legacy source-Face agreement, and
    no three-target composite silently replaces the four-target primary.
    """
    result = {}
    for target in TARGETS:
        selected = [r for r in rows if r['target'] == target and r['eligible']]
        if any(r['IoU'] is None or r['GT_pixels'] <= 0 for r in selected):
            raise ValueError('Eligible part lacks valid positive GT support')
        tp, fp, fn = (sum(r[k] for r in selected) for k in ('TP', 'FP', 'FN'))
        ready = execution_complete and len(selected) == expected_parts[target] and bool(selected)
        if target == 'FaceDomain':
            ready = ready and face_gt_complete
        result[target] = dict(
            GT_parts=len(selected), expected_GT_parts=expected_parts[target],
            GT_pixels=tp+fn, prediction_pixels=tp+fp, TP=tp, FP=fp, FN=fn,
            union=tp+fp+fn, mean_part_IoU=sum(r['IoU'] for r in selected)/len(selected) if ready else None,
            mean_part_Dice=sum(r['Dice'] for r in selected)/len(selected) if ready else None,
            pooled_IoU=tp/(tp+fp+fn) if ready and tp+fp+fn else None,
            pooled_Dice=2*tp/(2*tp+fp+fn) if ready and 2*tp+fp+fn else None,
            detector_missed_parts=sum(r['detector_miss'] for r in selected), ready=ready)
    ready = execution_complete and face_gt_complete and all(result[t]['ready'] for t in TARGETS)
    return dict(targets=result, primary=sum(result[t]['mean_part_IoU'] for t in TARGETS)/4 if ready else None,
                primary_ready=ready, face_gt_complete=face_gt_complete,
                status='COMPLETE' if ready else 'DIAGNOSTICS_COMPLETE_FACE_GT_PENDING' if execution_complete else 'INCOMPLETE')


def prepare(owner_path, review_path, protocol_path, out):
    """Freeze GT-only eligibility and detector association before reading scores."""
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    owner, review, protocol = read(owner_path), read(review_path), read(protocol_path)
    if review['parser_predictions_used'] or len(review['face_reviews']) != 35:
        raise ValueError('GT-only review is incomplete or used parser predictions')
    source = P/'outputs/cctv-partial-20261031T1800Z/CONFIG.json'
    if sha(source) != owner['source_config_sha256']:
        raise ValueError('Owner/source binding drift')
    config = read(source); by_id = {r['image_id']: r for r in owner['bindings']}
    if set(by_id) != {m['id'] for m in config['members']} or len(by_id) != len(owner['bindings']):
        raise ValueError('GT population mismatch')
    exceptions = {(r['image_id'], r['person_id'], r['target']): r['reason'] for r in review['part_exceptions']}
    if len(exceptions) != len(review['part_exceptions']):
        raise ValueError('Duplicate GT-only exception')
    parts, matches, seen_exceptions, frames = [], [], set(), []
    for member in config['members']:
        binding = by_id[member['id']]
        arrays = {}
        for field, digest in [('Category_ids', 'Category_sha256'), ('Human_ids', 'Human_sha256')]:
            path = W/binding[field]
            if sha(path) != binding[digest]:
                raise ValueError('GT identity drift')
            arrays[field] = np.asarray(Image.open(path))
        category, human = arrays['Category_ids'], arrays['Human_ids']
        if category.shape != human.shape or category.shape != tuple(member['wh'][::-1]):
            raise ValueError('GT original geometry mismatch')
        detpath = source.parent/'YOLO26X/packets'/member['id']
        detector = read(detpath/'COMMIT.json')
        if detector['input_sha256'] != member['RGB_sha256'] or sha(detpath/'detector.npz') != detector['artifact_sha256']:
            raise ValueError('Detector/source binding drift')
        assignments, ambiguities = match_gt_to_detector(human, detector['opportunities'], protocol['matching_GT_union_box_coverage'])
        matches.extend(dict(image_id=member['id'], person_id=pid, opportunity_id=op,
                            equal_objective_ambiguity=pid in ambiguities) for pid, op in assignments.items())
        for pid in assignments:
            for target, native in SOURCE_IDS.items():
                pixels = int(((human == pid) & (category == native)).sum())
                if not pixels:
                    continue
                key = (member['id'], pid, target)
                reason = exceptions.get(key)
                if reason:
                    seen_exceptions.add(key)
                eligible = target != 'Face' and reason is None
                parts.append(dict(image_id=member['id'], person_id=pid, source_target=target,
                    target='FaceDomain' if target == 'Face' else target, source_GT_pixels=pixels,
                    eligible=eligible, QA_reason=reason or ('NECK_ANNOTATION_PENDING' if target == 'Face' else 'GT_ONLY_SCREEN_PASS_NOT_EXPERT_CERTIFIED')))
        frames.append(dict(**binding, condition=member['condition'], original_wh=member['wh'],
            detector_npz=rel(detpath/'detector.npz'), detector_sha256=detector['artifact_sha256'],
            detector_commit_sha256=sha(detpath/'COMMIT.json'), input_sha256=member['RGB_sha256']))
    if seen_exceptions != set(exceptions):
        raise ValueError('Exception does not identify an existing part')
    expected = {t: sum(r['eligible'] and r['target'] == t for r in parts) for t in TARGETS}
    source_counts = dict(Counter(r['source_target'] for r in parts))
    binding = dict(status='NON_FACE_DIAGNOSTIC_BINDING_FROZEN_FACE_GT_PENDING', created_utc=now(),
        source_config=rel(source), source_config_sha256=sha(source), owner_revision=rel(owner_path),
        owner_revision_sha256=sha(owner_path), manual_review=rel(review_path), manual_review_sha256=sha(review_path),
        protocol=rel(protocol_path), protocol_sha256=sha(protocol_path),
        source_parts=source_counts, expected_eligible_parts=expected, part_records=parts, matches=matches, frames=frames,
        Face_Neck_GT_complete=False, Neck_annotations_created=0, expert_certified=False,
        source_modified=False, parser_predictions_used_for_GT=False,
        post_hoc=True, matched_GT_source='owner-corrected source part union, independent of any future Neck contours')
    atomic(out/'GT_BINDING.json', binding)
    summary = dict(status=binding['status'], created_utc=now(), GT_binding_sha256=sha(out/'GT_BINDING.json'),
        protocol_sha256=sha(protocol_path), source_parts=source_counts, expected_eligible_parts=expected,
        owner_corrections=len(owner['corrections']), reviewed_persons=len(matches), source_parts_total=len(parts),
        GT_only_excluded_non_Face_parts=len(exceptions), pending_Face_parts=source_counts['Face'],
        detector_missed_person_records=sum(r['opportunity_id'] is None for r in matches),
        ambiguous_assignments=sum(r['equal_objective_ambiguity'] for r in matches),
        Face_Neck_GT_complete=False, Neck_annotations_created=0, expert_certified=False,
        source_modified=False, parser_predictions_used_for_GT=False, model_calls=0, primary=None)
    atomic(out/'PUBLIC_GT_REVIEW.json', summary)
    return summary


def bound_checkpoint(run_config, mid):
    """Continuation model IDs inherit exact specifications from a hashed parent."""
    if isinstance(run_config['models'], dict):
        return run_config['models'][mid]['checkpoint_sha256']
    if mid not in run_config['models']:
        raise ValueError('Checkpoint not in continuation scope')
    parent = W/run_config['parent_config']
    if sha(parent) != run_config['parent_config_sha256']:
        raise ValueError('Continuation parent specification changed')
    return read(parent)['models'][mid]['checkpoint_sha256']


def evaluate(index_path, binding_path, protocol_path, out, only_models=None):
    sys.path.insert(0, str(W/'Human_Parsing_Benchmark/src'))
    from common_view.packets import read_packet
    binding, protocol, index = read(binding_path), read(protocol_path), read(index_path)
    if binding['Face_Neck_GT_complete']:
        raise ValueError('This version only closes non-Face diagnostics; reviewed Face/Neck packet integration needs its own accepted binding')
    if sha(protocol_path) != binding['protocol_sha256']:
        raise ValueError('Frozen projection/metric protocol changed')
    for path, digest in [(binding['source_config'], binding['source_config_sha256']),
                         (binding['owner_revision'], binding['owner_revision_sha256']),
                         (binding['manual_review'], binding['manual_review_sha256'])]:
        if sha(W/path) != digest:
            raise ValueError('Frozen GT/source review changed')
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    frozen = dict(created_utc=now(), source_index=rel(index_path), source_index_sha256=sha(index_path),
        GT_binding=rel(binding_path), GT_binding_sha256=sha(binding_path),
        protocol=rel(protocol_path), protocol_sha256=sha(protocol_path), scorer_sha256=sha(__file__),
        helper_hashes={name: sha(P/'scripts'/name) for name in ['controlled_roi_core.py', 'selected_part_evaluation.py']}, model_calls=0)
    atomic(out/'FROZEN_INPUTS.json', frozen)
    expected = [f['image_id'] for f in binding['frames']]
    if len(expected) != 90 or len(set(expected)) != 90 or len(index['models']) != 9:
        raise ValueError('Assembled inference population differs')
    source = read(W/binding['source_config'])
    matches = {(r['image_id'], r['person_id']): r['opportunity_id'] for r in binding['matches']}
    by_image = defaultdict(list)
    for part in binding['part_records']:
        by_image[part['image_id']].append(part)
    selected_models = dict(index['models'])
    if only_models:
        if len(set(only_models)) != len(only_models) or not set(only_models) <= set(selected_models):
            raise ValueError('Unknown/duplicate scoring checkpoint scope')
        selected_models = {mid: info for mid, info in selected_models.items() if mid in only_models}
    atomic(out/'SCORING_SCOPE.json', dict(selected_models=list(selected_models),
        full_prediction_models=list(index['models']), inference_calls=0))
    results, target_table = {}, []
    for mid, info in selected_models.items():
        root = out/mid; root.mkdir()
        packet_root = W/info['packet_root']; run_config_path = packet_root.parent.parent/'CONFIG.json'
        run_config = read(run_config_path); model = source['models'][mid]
        accepted, all_rows, error = [], [], None
        family = 'SAPIENS29' if model['family'] == 'Sapiens2' else 'CIHP20'
        space = 'SAPIENS2_DOME29_PRED' if family == 'SAPIENS29' else 'CIHP_GT_AND_NATIVE_PRED'
        packet_ids = sorted(p.name for p in packet_root.iterdir() if p.is_dir() and not p.name.startswith('.'))
        if packet_ids != sorted(expected):
            raise ValueError('Source packets have missing/extra IDs')
        try:
            for frame in binding['frames']:
                iid = frame['image_id']; packet = packet_root/iid
                meta, a = read_packet(packet, expected=dict(model_id=mid, image_id=iid, original_wh=frame['original_wh'],
                    input_sha256=frame['input_sha256'], checkpoint_sha256=model['checkpoint_sha256'],
                    config_sha256=sha(run_config_path), detector_sha256=frame['detector_sha256'],
                    label_space=space, precision='FP32', route='CONTROLLED_YOLO_PERSON_ROI', GT_used_in_prediction=False))
                if bound_checkpoint(run_config, mid) != model['checkpoint_sha256']:
                    raise ValueError('Assembled checkpoint binding mismatch')
                planes, extents = a['person_semantic_masks'], a['person_extents']
                shape = tuple(frame['original_wh'][::-1])
                if planes.ndim != 3 or planes.shape[1:] != shape:
                    raise ValueError('Original-grid geometry failure')
                validate_native(planes, len(protocol['native_projection'][family]), planes.shape)
                for field, digest in [('Category_ids', 'Category_sha256'), ('Human_ids', 'Human_sha256')]:
                    if sha(W/frame[field]) != frame[digest]:
                        raise ValueError('GT drift after eligibility freeze')
                category = np.asarray(Image.open(W/frame['Category_ids']))
                human = np.asarray(Image.open(W/frame['Human_ids']))
                dp = W/frame['detector_npz']
                if sha(dp) != frame['detector_sha256'] or sha(dp.parent/'COMMIT.json') != frame['detector_commit_sha256']:
                    raise ValueError('Frozen detector drift')
                dm = read(dp.parent/'COMMIT.json')
                with np.load(dp, allow_pickle=False) as data:
                    da = {k: data[k] for k in ['masks', 'scores']}
                lookup = final_plane_lookup(meta, a, da, dm['opportunities'])
                ops = {op['id']: j for j, op in enumerate(dm['opportunities'])}
                if set(lookup) != set(ops):
                    raise ValueError('Controlled opportunity identity is incomplete')
                for op, j in lookup.items():
                    if not np.array_equal(extents[j], da['masks'][ops[op]]) or float(a['person_scores'][j]) != float(da['scores'][ops[op]]):
                        raise ValueError('Controlled ownership differs from frozen YOLO')
                    if np.any(planes[j][~extents[j].astype(bool)]):
                        raise ValueError('Owned semantics escaped extent')
                projected = {op: project_native(planes[j], family, protocol) for op, j in lookup.items()}
                rows = []
                for part in by_image[iid]:
                    target = part['target']
                    if target == 'FaceDomain':
                        # Missing anatomical annotation is not an empty Neck GT.
                        continue
                    gt = (human == part['person_id']) & (category == SOURCE_IDS[part['source_target']])
                    if int(gt.sum()) != part['source_GT_pixels']:
                        raise ValueError('Frozen GT part support changed')
                    op = matches[iid, part['person_id']]
                    prediction = projected[op][target] if op is not None else np.zeros(shape, bool)
                    rows.append(dict(image_id=iid, person_id=part['person_id'], target=target,
                        condition=frame['condition'], eligible=part['eligible'], QA_reason=part['QA_reason'],
                        detector_miss=op is None, **counts(gt, prediction)))
                record = dict(image_id=iid, source_packet_sha256=meta['packet_sha256'],
                    source_commit_sha256=sha(packet/'COMMIT.json'), frozen_inputs_sha256=sha(out/'FROZEN_INPUTS.json'), rows=rows)
                atomic(root/(iid+'.json'), record)
                with (root/'FRAMES.jsonl').open('a') as stream:
                    stream.write(json.dumps(dict(image_id=iid, status='SCORED', record_sha256=sha(root/(iid+'.json'))))+'\n')
                    stream.flush(); os.fsync(stream.fileno())
                accepted.append(iid); all_rows.extend(rows)
                atomic(out/'STATUS.json', dict(status='CPU_SCORING', model_id=mid, completed_frames=len(accepted), completed_models=len(results), model_calls=0))
        except Exception:
            error = traceback.format_exc(); (root/'FAILURE.txt').write_text(error)
        completion = reconcile(expected, accepted, failed=[error] if error else [])
        metrics = summarize(all_rows, binding['expected_eligible_parts'], completion['strict_complete'], binding['Face_Neck_GT_complete'])
        metrics.update(model_id=mid, completion=completion, source_packet_root=rel(packet_root),
            source_run_config_sha256=sha(run_config_path), family=family, route='CONTROLLED_YOLO_PERSON_ROI',
            resource_policy='SAVED_SHARED_GPU_QUALITY_ONLY_DIAGNOSTICS_NOT_SPEED_RANKING', model_calls=0)
        atomic(root/'METRICS.json', metrics)
        results[mid] = metrics
        for group in ['overall', 'day', 'night']:
            rs = [r for r in all_rows if group == 'overall' or r['condition'] == group]
            for subset in ['GT_REVIEWED_DIAGNOSTIC', 'ALL_SOURCE_NON_FACE_SENSITIVITY']:
                chosen = rs if subset.startswith('GT_REVIEWED') else [dict(r, eligible=True) for r in rs]
                expected_group = {t: sum(r['eligible'] and r['target'] == t for r in chosen) for t in TARGETS}
                summary = summarize(chosen, expected_group, completion['strict_complete'], False)
                for target, value in summary['targets'].items():
                    target_table.append(dict(model_id=mid, subset=subset, group=group, target=target, **value))
    atomic(out/'RESULTS.json', dict(status='DIAGNOSTICS_COMPLETE_FACE_GT_PENDING' if all(r['completion']['strict_complete'] for r in results.values()) else 'INCOMPLETE',
        created_utc=now(), frozen_inputs=frozen, GT_summary=read(Path(binding_path).parent/'PUBLIC_GT_REVIEW.json'),
        models=results, primary=None, overall_winner=None, model_calls=0))
    with (out/'TARGET_METRICS.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(target_table[0])); writer.writeheader(); writer.writerows(target_table)
    atomic(out/'STATUS.json', dict(status=read(out/'RESULTS.json')['status'], completed_models=len(results),
        exact_90_complete_models=sum(r['completion']['strict_complete'] for r in results.values()), model_calls=0, primary=None))
    print(json.dumps(read(out/'STATUS.json')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    prep = sub.add_parser('prepare'); prep.add_argument('--owner', type=Path, required=True); prep.add_argument('--review', type=Path, required=True)
    score = sub.add_parser('score'); score.add_argument('--index', type=Path, required=True); score.add_argument('--binding', type=Path, required=True); score.add_argument('--models', nargs='+')
    for item in [prep, score]:
        item.add_argument('--protocol', type=Path, required=True); item.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'prepare':
        print(json.dumps(prepare(args.owner, args.review, args.protocol, args.out)))
    else:
        evaluate(args.index, args.binding, args.protocol, args.out, args.models)
