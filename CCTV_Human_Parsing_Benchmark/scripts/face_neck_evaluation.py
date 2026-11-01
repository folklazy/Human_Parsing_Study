"""CPU-only final selected-part views; reuse accepted non-Face calculations.

Unknown Neck is an explicitly bounded GT-only uncertainty region. It never
becomes an absent Neck truth or a Face+Neck delivery score. Source packets and
historical scores remain immutable. No model imports or inference entry point.
"""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import csv
import json
import os
import sys
import traceback
import numpy as np
from PIL import Image
from controlled_roi_core import atomic, read, sha, counts
from controlled_roi_evaluation import project_native
from selected_part_evaluation import final_plane_lookup

P = Path(__file__).resolve().parents[1]
W = P.parent


def score_face(native, family, gt_arrays, record, projection):
    f, n, u, o = [gt_arrays[k] for k in ['Face', 'Neck', 'uncertainty', 'known_occluder']]
    if any(x.dtype != bool or x.shape != f.shape for x in [f,n,u,o]):
        raise ValueError('Boolean original-grid GT arrays required')
    if not f.any() or np.any(f & (n | u | o)) or np.any(n & (u | o)) or np.any(u & o):
        raise ValueError('GT positives/uncertainty/opaque negatives must be disjoint')
    if record['Neck_status'] == 'REGION_UNCERTAIN':
        if n.any() or not u.any() or record['FaceNeck_delivery_eligible']:
            raise ValueError('Unknown Neck cannot become absent/positive delivery GT')
    elif record['Neck_status'] == 'VISIBLE_ANNOTATED':
        if not n.any() or not record['FaceNeck_delivery_eligible']:
            raise ValueError('Visible Neck requires known positive pixels')
    elif record['Neck_status'] == 'VERIFIED_NOT_VISIBLE':
        if n.any() or not record['FaceNeck_delivery_eligible']:
            raise ValueError('Verified invisible Neck contradicts GT arrays')
    else:
        raise ValueError('Unreviewed Neck state')
    candidate = np.zeros(f.shape, bool) if native is None else project_native(native, family, projection)['FaceCandidate']
    face = counts(f, candidate, ~(n | u))
    delivery = counts(f | n, candidate, ~u) if record['FaceNeck_delivery_eligible'] else None
    coverage = float((candidate & n).sum()/n.sum()) if record['FaceNeck_delivery_eligible'] and n.any() else None
    return dict(FaceDomain=face, FaceNeck=delivery, NeckCoverage=coverage,
                known_Neck_TP=int((candidate & n).sum()) if coverage is not None else None,
                known_Neck_pixels=int(n.sum()) if record['FaceNeck_delivery_eligible'] else None)


def aggregate_view(rows, key):
    selected = [r[key] for r in rows if r[key] is not None]
    if any(r['GT_pixels'] <= 0 or r['IoU'] is None for r in selected):
        raise ValueError('Positive GT support required for selected part task')
    tp, fp, fn = (sum(r[k] for r in selected) for k in ['TP','FP','FN'])
    return dict(GT_parts=len(selected), GT_pixels=tp+fn, prediction_pixels=tp+fp, TP=tp, FP=fp, FN=fn,
        union=tp+fp+fn, mean_part_IoU=sum(r['IoU'] for r in selected)/len(selected) if selected else None,
        mean_part_Dice=sum(r['Dice'] for r in selected)/len(selected) if selected else None,
        pooled_IoU=tp/(tp+fp+fn) if tp+fp+fn else None,
        pooled_Dice=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)


def macro_four(non_face_targets, face, complete):
    values = [non_face_targets[t]['mean_part_IoU'] for t in ['Hair','Upper','Lower']] + [face['mean_part_IoU']]
    return sum(values)/4 if complete and all(v is not None for v in values) else None


def evaluate(base_results_path, gt_path, protocol_path, out):
    sys.path.insert(0, str(W/'Human_Parsing_Benchmark/src'))
    from common_view.packets import read_packet
    base, gt, protocol = read(base_results_path), read(gt_path), read(protocol_path)
    if sha(base_results_path) != protocol['base_non_Face_result_index_sha256'] or sha(gt_path) != protocol['Face_GT_binding_sha256']:
        raise ValueError('Frozen result/GT identity changed')
    binding_path = W/gt['base_GT_binding']; binding = read(binding_path)
    projection_path = P/protocol['projection_protocol']
    if sha(binding_path) != gt['base_GT_binding_sha256'] or base['GT_binding_sha256'] != gt['base_GT_binding_sha256']:
        raise ValueError('Non-Face/Face GT parent mismatch')
    if sha(projection_path) != protocol['projection_protocol_sha256']:
        raise ValueError('Frozen native projection changed')
    projection = read(projection_path)
    source = read(W/binding['source_config'])
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    frozen = dict(created_utc=datetime.now(timezone.utc).isoformat(), base_results_sha256=sha(base_results_path),
        Face_GT_binding_sha256=sha(gt_path), protocol_sha256=sha(protocol_path), scorer_sha256=sha(__file__),
        projection_protocol_sha256=sha(projection_path), source_helpers={n:sha(P/'scripts'/n) for n in
        ['controlled_roi_core.py','controlled_roi_evaluation.py','selected_part_evaluation.py']}, model_calls=0)
    atomic(out/'FROZEN_INPUTS.json', frozen)
    eligible = [r for r in gt['records'] if r['disposition']=='ELIGIBLE']
    expected_keys = {(r['image_id'], r['person_id']) for r in eligible}
    if len(expected_keys) != gt['expected_eligible_Face_parts'] or len(eligible) != len(expected_keys):
        raise ValueError('Duplicate or missing GT Face eligibility')
    by_image = defaultdict(list)
    for r in eligible: by_image[r['image_id']].append(r)
    frames = {r['image_id']:r for r in binding['frames']}
    assignments = {(r['image_id'],r['person_id']):r['opportunity_id'] for r in binding['matches']}
    results, all_table_rows = {}, []
    for mid, prior in base['models'].items():
        root = out/mid; root.mkdir()
        rows, errors = [], []
        source_packets = W/prior['source_packet_root']
        if sorted(d.name for d in source_packets.iterdir() if d.is_dir() and not d.name.startswith('.')) != sorted(frames):
            raise ValueError('Original 90-frame prediction membership changed')
        old_metrics = W/prior['accepted_metrics_path']
        if sha(old_metrics) != prior['accepted_metrics_sha256'] or not prior['completion']['strict_complete']:
            raise ValueError('Accepted non-Face result changed/incomplete')
        try:
            for iid, records in by_image.items():
                frame = frames[iid]; path = source_packets/iid
                meta, arrays = read_packet(path, expected=dict(model_id=mid,image_id=iid,original_wh=frame['original_wh'],
                    checkpoint_sha256=source['models'][mid]['checkpoint_sha256'], config_sha256=prior['source_run_config_sha256'],
                    input_sha256=frame['input_sha256'],detector_sha256=frame['detector_sha256'],precision='FP32',
                    route='CONTROLLED_YOLO_PERSON_ROI',GT_used_in_prediction=False))
                previous_frame = read(old_metrics.parent/(iid+'.json'))
                if meta['packet_sha256'] != previous_frame['source_packet_sha256'] or sha(path/'COMMIT.json') != previous_frame['source_commit_sha256']:
                    raise ValueError('Face/native source packet differs from accepted non-Face view')
                expected_space = 'SAPIENS2_DOME29_PRED' if prior['family']=='SAPIENS29' else 'CIHP_GT_AND_NATIVE_PRED'
                if meta['label_space'] != expected_space:
                    raise ValueError('Prediction label space mismatch')
                detector_path = W/frame['detector_npz']
                if sha(detector_path) != frame['detector_sha256']:
                    raise ValueError('Frozen detector identity changed')
                dm = read(detector_path.parent/'COMMIT.json')
                with np.load(detector_path,allow_pickle=False) as z: da = {k:z[k] for k in ['masks','scores']}
                lookup = final_plane_lookup(meta, arrays, da, dm['opportunities'])
                plane = arrays['person_semantic_masks']; extent = arrays['person_extents']
                if plane.shape[1:] != tuple(frame['original_wh'][::-1]) or not np.array_equal(extent, da['masks']) or not np.array_equal(arrays['person_scores'],da['scores']):
                    raise ValueError('Original-grid/frozen-ownership parity failure')
                for record in records:
                    gt_mask_path = W/record['masks']
                    if sha(gt_mask_path) != record['masks_sha256']:
                        raise ValueError('Frozen Face/Neck/uncertainty mask changed')
                    with np.load(gt_mask_path,allow_pickle=False) as z: gt_masks={k:z[k] for k in z.files}
                    op = assignments[(iid,record['person_id'])]
                    if op is not None and op not in lookup:
                        raise ValueError('Controlled packet lost detector identity')
                    native = plane[lookup[op]] if op is not None else None
                    if native is not None and np.any(native[~extent[lookup[op]].astype(bool)]):
                        raise ValueError('Owned prediction escaped extent')
                    scored = score_face(native,prior['family'],gt_masks,record,projection)
                    if scored['FaceDomain']['GT_pixels'] != record['Face_pixels']:
                        raise ValueError('GT support after domain changed')
                    rows.append(dict(image_id=iid,person_id=record['person_id'],condition=frame['condition'],
                        detector_unmatched=op is None,GT_masks_sha256=record['masks_sha256'],
                        source_packet_sha256=meta['packet_sha256'],Neck_status=record['Neck_status'],**scored))
                atomic(root/(iid+'.json'),dict(image_id=iid,rows=[r for r in rows if r['image_id']==iid],
                    source_packet_sha256=meta['packet_sha256'],protocol_sha256=sha(protocol_path)))
                with (root/'FRAMES.jsonl').open('a') as stream:
                    stream.write(json.dumps(dict(image_id=iid,record_sha256=sha(root/(iid+'.json'))))+'\n');stream.flush();os.fsync(stream.fileno())
        except Exception:
            errors.append(traceback.format_exc());(root/'FAILURE.txt').write_text(errors[-1])
        complete = (not errors and {(r['image_id'],r['person_id']) for r in rows}==expected_keys
                    and len(rows)==len(expected_keys)
                    and sum(r['FaceNeck'] is not None for r in rows)==gt['expected_FaceNeck_delivery_parts'])
        face = aggregate_view(rows,'FaceDomain'); delivery = aggregate_view(rows,'FaceNeck')
        nrows = [r for r in rows if r['NeckCoverage'] is not None]
        neck = dict(GT_parts=len(nrows),mean_recall=sum(r['NeckCoverage'] for r in nrows)/len(nrows) if nrows else None,
            known_Neck_pixels=sum(r['known_Neck_pixels'] for r in nrows),
            TP=sum(r['known_Neck_TP'] for r in nrows))
        neck['pooled_recall']=neck['TP']/neck['known_Neck_pixels'] if neck['known_Neck_pixels'] else None
        if not complete:
            for view in [face,delivery]:
                for key in ['mean_part_IoU','mean_part_Dice','pooled_IoU','pooled_Dice']: view[key]=None
            neck['mean_recall']=neck['pooled_recall']=None
        result = dict(model_id=mid,status='COMPLETE_ON_REVIEWED_GT' if complete else 'INCOMPLETE',
            original_prediction_images=90,prior_prediction_strict_complete=True,eligible_Face_parts=len(expected_keys),
            scored_Face_parts=len(rows),missing_Face_parts=len(expected_keys-{(r['image_id'],r['person_id']) for r in rows}),
            failed=len(errors),FaceDomain=face,FaceNeck=delivery,NeckCoverage=neck,
            non_Face_targets={t:prior['targets'][t] for t in ['Hair','Upper','Lower']},
            primary=macro_four(prior['targets'],face,complete),model_calls=0,
            detector_unmatched_Face_parts=sum(r['detector_unmatched'] for r in rows),
            source_non_Face_metrics_sha256=prior['accepted_metrics_sha256'],source_non_Face_metrics_path=prior['accepted_metrics_path'],
            Face_GT_binding_sha256=sha(gt_path),protocol_sha256=sha(protocol_path),route='CONTROLLED_YOLO_PERSON_ROI')
        atomic(root/'METRICS.json',result);results[mid]=result
        for group in ['overall','day','night']:
            selected=[r for r in rows if group=='overall' or r['condition']==group]
            for view in ['FaceDomain','FaceNeck']:
                aggregate=aggregate_view(selected,view)
                if not complete:
                    for key in ['mean_part_IoU','mean_part_Dice','pooled_IoU','pooled_Dice']: aggregate[key]=None
                all_table_rows.append(dict(model_id=mid,group=group,view=view,**aggregate,
                    status=result['status'],detector_unmatched_parts=sum(r['detector_unmatched'] for r in selected if r[view] is not None)))
        atomic(out/'STATUS.json',dict(status='CPU_SCORING',complete_models=sum(r['status']=='COMPLETE_ON_REVIEWED_GT' for r in results.values()),finished_models=len(results),model_calls=0))
    report=dict(status='FOUR_TARGET_EVALUATION_COMPLETE_ON_REVIEWED_GT' if all(r['status']=='COMPLETE_ON_REVIEWED_GT' for r in results.values()) and len(results)==9 else 'INCOMPLETE',
        created_utc=datetime.now(timezone.utc).isoformat(),frozen_inputs=frozen,models=results,
        Face_GT_disposition_counts=gt['disposition_counts'],eligible_Face_parts=len(expected_keys),
        FaceNeck_delivery_parts=gt['expected_FaceNeck_delivery_parts'],model_calls=0,
        expert_certified=False,post_hoc=True,full_scene_evaluation=False,deployment_accepted=False)
    atomic(out/'RESULTS.json',report)
    with (out/'FACE_VIEW_METRICS.csv').open('w',newline='') as stream:
        wr=csv.DictWriter(stream,fieldnames=list(all_table_rows[0]),lineterminator='\n');wr.writeheader();wr.writerows(all_table_rows)
    atomic(out/'STATUS.json',dict(status=report['status'],complete_models=sum(r['status']=='COMPLETE_ON_REVIEWED_GT' for r in results.values()),model_calls=0))
    print(json.dumps(read(out/'STATUS.json')))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-results',type=Path,required=True);parser.add_argument('--GT',type=Path,required=True)
    parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();evaluate(args.base_results,args.GT,args.protocol,args.out)
