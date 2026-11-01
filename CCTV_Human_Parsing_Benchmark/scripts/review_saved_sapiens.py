"""CPU-only independent Sapiens score reconciliation and loss decomposition.

No GT edits, model loading, reranking, remapping or writes to accepted artifacts.
Native pre-ownership diagnostics measure GT-positive coverage, never full-frame FP.
"""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import hashlib
import json
import csv
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]; W = P.parent
TARGETS = {'Face': (13, [3, 24, 25, 26, 27, 28]), 'Hair': (2, [4]),
           'Upper': (5, [23]), 'Lower': (9, [13])}
NAMES = ['Background','Apparel','Eyeglass','Face_Neck','Hair','Left_Foot','Left_Hand',
    'Left_Lower_Arm','Left_Lower_Leg','Left_Shoe','Left_Sock','Left_Upper_Arm',
    'Left_Upper_Leg','Lower_Clothing','Right_Foot','Right_Hand','Right_Lower_Arm',
    'Right_Lower_Leg','Right_Shoe','Right_Sock','Right_Upper_Arm','Right_Upper_Leg',
    'Torso','Upper_Clothing','Lower_Lip','Upper_Lip','Lower_Teeth','Upper_Teeth','Tongue']


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024**2), b''): h.update(b)
    return h.hexdigest()


def confusion_counts(gt, pred):
    if gt.dtype != bool or pred.dtype != bool or gt.shape != pred.shape:
        raise ValueError('Same-grid binary masks required')
    # Independent 2x2 contingency, rather than the accepted intersection helper.
    h = np.bincount((gt.astype(np.uint8) * 2 + pred.astype(np.uint8)).ravel(), minlength=4)
    tn, fp, fn, tp = map(int, h)
    return tp, fp, fn


def table(path, rows):
    with path.open('w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); wr.writeheader(); wr.writerows(rows)


def run(config, binding, out):
    c, b = read(config), read(binding); root = config.parent
    assert sha(config) == b['source_config_sha256']
    out.mkdir(parents=True, exist_ok=False)
    parts = defaultdict(list)
    for r in b['part_records']:
        if r['primary_eligible']: parts[r['image_id']].append(r)
    matches = {(r['image_id'],r['person_id']):r['YOLO_opportunity_id'] for r in b['matches']}
    mids = [k for k in c['models'] if k.startswith('Sapiens2_')]
    rows = defaultdict(list); hist = defaultdict(lambda: np.zeros(29, np.int64))
    checked = defaultdict(int)
    for member in c['members']:
        iid = member['id']; ds = W / c['dataset_root']
        cp, hp = [ds / k / (member['stem'] + '.png') for k in ['Category_ids','Human_ids']]
        assert sha(cp) == member['GT_sha256']['Category_ids'] and sha(hp) == member['GT_sha256']['Human_ids']
        cat, human = np.array(Image.open(cp)), np.array(Image.open(hp))
        detector = root / 'YOLO26X/packets' / iid; dm = read(detector / 'COMMIT.json')
        with np.load(detector / 'detector.npz', allow_pickle=False) as z: masks, scores = z['masks'], z['scores']
        lookup = {op['id']:j for j,op in enumerate(dm['opportunities'])}; any_extent = masks.any(0)
        for mid in mids:
            packet = root / mid / 'packets' / iid; meta = read(packet / 'packet.json')
            assert sha(packet / 'prediction.npz') == meta['packet_sha256']
            assert meta['model_id'] == mid and meta['input_sha256'] == member['RGB_sha256']
            assert meta['checkpoint_sha256'] == c['models'][mid]['checkpoint_sha256']
            assert meta['detector_sha256'] == dm['artifact_sha256']
            with np.load(packet / 'prediction.npz', allow_pickle=False) as z:
                native, planes = z['native_full_frame_semantic_mask'], z['person_semantic_masks']
                assert np.array_equal(z['person_extents'], masks) and np.array_equal(z['person_scores'], scores)
            assert native.shape == cat.shape and native.dtype == np.uint8 and np.all(native < 29)
            assert np.array_equal(planes, np.where(masks, native, 0))
            accepted = read(P / 'outputs/selected-part-scores-20261101' / mid / (iid + '.json'))
            accepted = {(r['person_id'],r['target']):r for r in accepted['parts'] if r['primary_eligible']}
            for part in parts[iid]:
                name = part['target']; gt_id, ids = TARGETS[name]
                gt = (human == part['person_id']) & (cat == gt_id); support = int(gt.sum())
                assert support == part['GT_pixels']
                j = lookup.get(matches[iid,part['person_id']]); e = masks[j] if j is not None else np.zeros(gt.shape,bool)
                pred = np.isin(planes[j], ids) if j is not None else np.zeros(gt.shape,bool)
                tp, fp, fn = confusion_counts(gt, pred); old = accepted[part['person_id'],name]
                assert (tp,fp,fn) == (old['TP'],old['FP'],old['FN'])
                correct = np.isin(native, ids); before = int((gt & correct).sum())
                loss = before - tp
                assert loss >= 0 and fn == support-before+loss
                row = dict(image_id=iid,person_id=part['person_id'],target=name,GT_pixels=support,
                    TP=tp,FP=fp,FN=fn,IoU=tp/(tp+fp+fn),Dice=2*tp/(2*tp+fp+fn),
                    detector_miss=j is None,prediction_empty=not pred.any(),
                    native_correct_before_ownership=before,
                    native_wrong_on_GT=support-before,
                    correct_lost_detector_miss=loss if j is None else 0,
                    correct_lost_matched_YOLO_clipping=loss if j is not None else 0,
                    GT_outside_matched_extent=int((gt & ~e).sum()),
                    GT_inside_only_other_YOLO_extents=int((gt & ~e & any_extent).sum()),
                    source_packet_sha256=meta['packet_sha256'])
                rows[mid].append(row); hist[mid,name] += np.bincount(native[gt],minlength=29)
            checked[mid] += 1
            (out/'STATUS.json').write_text(json.dumps(dict(status='CPU_REVIEW',image_count=sum(checked.values()),expected_packets=270))+'\n')
    per_target = []; summary = []; bins = []; native_hist=[]
    for mid in mids:
        assert checked[mid] == 90 and len(rows[mid]) == 315
        (out/(mid+'_PRIVATE_PARTS.json')).write_text(json.dumps(rows[mid],indent=2)+'\n')
        tm=[]
        for name in TARGETS:
            rr=[r for r in rows[mid] if r['target']==name]
            sums={key:sum(r[key] for r in rr) for key in ['GT_pixels','TP','FP','FN','native_correct_before_ownership','native_wrong_on_GT','correct_lost_detector_miss','correct_lost_matched_YOLO_clipping','GT_outside_matched_extent','GT_inside_only_other_YOLO_extents']}
            tp,fp,fn=[sums[k] for k in ['TP','FP','FN']]
            present=[r for r in rr if not r['detector_miss']]
            row=dict(model_id=mid,target=name,GT_parts=len(rr),detector_miss_parts=sum(r['detector_miss'] for r in rr),
                zero_TP_parts=sum(r['TP']==0 for r in rr),empty_prediction_parts=sum(r['prediction_empty'] for r in rr),
                mean_part_IoU=float(np.mean([r['IoU'] for r in rr])),pooled_part_IoU=tp/(tp+fp+fn),
                mean_IoU_detector_present_diagnostic=float(np.mean([r['IoU'] for r in present])),
                native_positive_recall_before_ownership=sums['native_correct_before_ownership']/sums['GT_pixels'],
                final_positive_recall=tp/sums['GT_pixels'],**sums)
            per_target.append(row);tm.append(row)
            for label,lo,hi in [('under100',0,100),('100to499',100,500),('500to1999',500,2000),('2000plus',2000,float('inf'))]:
                rs=[r for r in rr if lo<=r['GT_pixels']<hi]
                bins.append(dict(model_id=mid,target=name,GT_area_bin_pixels=label,GT_parts=len(rs),
                    mean_part_IoU=float(np.mean([r['IoU'] for r in rs])) if rs else None,
                    detector_miss_parts=sum(r['detector_miss'] for r in rs)))
            for native_id,count in enumerate(hist[mid,name]):
                native_hist.append(dict(model_id=mid,GT_target=name,native_id=native_id,native_name=NAMES[native_id],pixels=int(count),
                    fraction_of_GT_target=float(count/sums['GT_pixels'])))
        summary.append(dict(model_id=mid,input_images=90,GT_parts=315,
            mean_part_IoU4=float(np.mean([r['mean_part_IoU'] for r in tm])),
            mean_pooled_part_IoU4=float(np.mean([r['pooled_part_IoU'] for r in tm])),
            detector_present_mean_IoU4_diagnostic=float(np.mean([r['mean_IoU_detector_present_diagnostic'] for r in tm])),
            detector_miss_parts=sum(r['detector_miss_parts'] for r in tm),
            zero_TP_parts=sum(r['zero_TP_parts'] for r in tm)))
    for name,data in [('SUMMARY',summary),('PER_TARGET',per_target),('GT_SIZE_BINS',bins),('NATIVE_GT_DISAGREEMENT',native_hist)]:table(out/(name+'.csv'),data)
    result=dict(status='SAVED_SAPIENS_REVIEW_COMPLETE',created_utc=datetime.now(timezone.utc).isoformat(),
        source_run=c['run_id'],config_sha256=sha(config),GT_binding_sha256=sha(binding),review_script_sha256=sha(__file__),
        exact_unique_input_images_per_model=90,NPZs_checked=dict(checked),primary_parts_per_model=315,
        independent_2x2_counts_match_accepted=True,owned_planes_equal_native_masked_by_frozen_YOLO=True,
        decomposition='FN = native-wrong-on-GT + native-correct-lost-to-detector-miss + native-correct-lost-to-matched-mask-clipping',
        new_model_calls=0,canonical_scores_or_GT_modified=False,preownership_FP_or_IoU_claimed=False)
    (out/'EVIDENCE.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'STATUS.json').write_text(json.dumps(dict(status='COMPLETE',packets=270,models=3,model_calls=0))+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--config',type=Path,required=True)
    ap.add_argument('--binding',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();run(a.config,a.binding,a.out)
