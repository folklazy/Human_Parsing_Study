"""Audit the completed CCTV run and derive annotated-domain diagnostics only.

No model loading/inference, GT edits, or writes to canonical run artifacts.
Public outputs contain aggregate counts/hashes, never CCTV image identifiers.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse
import csv
import hashlib
import json
import math
import sys

import numpy as np

P = Path(__file__).resolve().parents[1]
W = P.parent
TARGETS = ['Face', 'Hair', 'Upper', 'Lower']


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def diagnostic(hist):
    h = np.asarray(hist, dtype=np.int64)
    if h.shape != (6, 6) or np.any(h < 0) or h[[0, 5]].any():
        raise ValueError('Expected positive-annotation-only 6x6 confusion')
    rows = []
    for k, name in enumerate(TARGETS, 1):
        tp = int(h[k, k]); gt = int(h[k].sum()); pred = int(h[:, k].sum())
        union = gt + pred - tp
        rows.append(dict(target=name,GT_pixels=gt,prediction_pixels_in_D=pred,TP=tp,
            FP_in_D=pred-tp,FN_in_D=gt-tp,union_in_D=union,
            IoU_in_D=tp/union if union else None,
            Dice_in_D=2*tp/(gt+pred) if gt+pred else None,
            precision_in_D=tp/pred if pred else None,recall=tp/gt if gt else None))
    return rows


def audit(run_id):
    raw = P/'outputs'/run_id
    c = read(raw/'CONFIG.json'); state = read(P/'STUDY_STATE.json'); audit = read(P/'reports/DATASET_AUDIT.json')
    if sha(raw/'CONFIG.json') != state['config_sha256'] or c['run_id'] != run_id:
        raise ValueError('Accepted config binding changed')
    source_checks = {path: sha(W/path)==digest for path,digest in c['source_hashes'].items()}
    if not all(source_checks.values()):
        raise ValueError('Frozen implementation source changed')
    expected = {m['id'] for m in c['members']}
    if len(expected) != len(c['members']) or len(expected) != 90:
        raise ValueError('Expected exact frozen population of90')
    members = {m['id']:m for m in c['members']}
    gt_hash_checks = 0
    for sample in c['members']:
        for kind,digest in sample['GT_sha256'].items():
            if sha(W/c['dataset_root']/kind/(sample['stem']+'.png')) != digest:
                raise ValueError('GT byte identity changed')
            gt_hash_checks += 1
        if sha(W/c['dataset_root']/'Annotations_canonical'/(sample['stem']+'.json')) != sample['annotation_sha256']:
            raise ValueError('Annotation identity changed')
        gt_hash_checks += 1
    # Hand-counted fixture: IoU=(.5,.25,1,0), macro=.4375, Dice=(2/3,.4,1,0).
    fixture = np.zeros((6,6),np.int64)
    for a,b,n in [(1,1,2),(1,2,1),(2,1,1),(2,2,1),(2,5,1),(3,3,2),(4,0,1)]:
        fixture[a,b]=n
    f = diagnostic(fixture)
    assert [r['IoU_in_D'] for r in f] == [.5,.25,1.,0.]
    assert math.isclose(sum(r['Dice_in_D'] for r in f)/4, (2/3+.4+1)/4)
    assert f[3]['precision_in_D'] is None
    summaries=[]; per_target=[]; evidence={}; per_image_support={}
    for mid in c['models']:
        root = raw/mid; m=read(root/'METRICS.json'); st=read(root/'STATE.json')
        if m['status']!='COMPLETE' or st['status']!='COMPLETE':
            raise ValueError('Incomplete canonical system')
        if sha(root/'METRICS.json')!=state['evidence'][mid]['metrics_sha256'] or sha(root/'FRAMES.jsonl')!=state['evidence'][mid]['ledger_sha256']:
            raise ValueError('Accepted summary/ledger identity changed')
        ledger=[json.loads(line) for line in (root/'FRAMES.jsonl').read_text().splitlines() if line.strip()]
        ids=[row['image_id'] for row in ledger if row['status']=='COMPLETE']
        if len(ids)!=len(set(ids)) or set(ids)!=expected or len(ledger)!=90:
            raise ValueError('Missing, duplicate or failed ledger membership')
        packet_ids={d.name for d in (root/'packets').iterdir() if d.is_dir()}
        if packet_ids!=expected:
            raise ValueError('Partial, orphan or missing packet directory')
        hist={g:np.zeros((6,6),np.int64) for g in ['overall','day','night']}
        for iid in ids:
            packet=root/'packets'/iid; commit=read(packet/'COMMIT.json'); meta=read(packet/'packet.json')
            for name in ['packet.json','score_partial.json']:
                if sha(packet/name)!=commit['members'][name]:
                    raise ValueError('Atomic metadata/scoring hash changed')
            if meta['packet_sha256']!=commit['members']['prediction.npz'] or not (packet/'prediction.npz').is_file():
                raise ValueError('Prediction identity/reference missing')
            sample=members[iid]
            assert meta['model_id']==mid and meta['image_id']==iid
            assert meta['input_sha256']==sample['RGB_sha256'] and meta['original_wh']==sample['wh']
            assert meta['checkpoint_sha256']==c['models'][mid]['checkpoint_sha256']
            assert meta['config_sha256']==state['config_sha256']
            score=read(packet/'score_partial.json'); assert score['GT_sha256']==sample['GT_sha256']
            h=np.array(score['histogram'],np.int64); diagnostic(h)
            support=tuple(int(x) for x in h.sum(1))
            if iid in per_image_support:assert per_image_support[iid]==support
            else:per_image_support[iid]=support
            hist['overall']+=h;hist[sample['condition']]+=h
        assert np.array_equal(hist['overall'],hist['day']+hist['night'])
        for group,h in hist.items():
            assert h.tolist()==m['groups'][group]['histogram']
            rows=diagnostic(h)
            recalls=[r['recall'] for r in rows]
            assert np.allclose(recalls,m['groups'][group]['metrics']['per_target_recall'],atol=1e-15,rtol=0)
            if group=='overall':
                assert [r['GT_pixels'] for r in rows]==[audit['GT_native_pixel_support'][k] for k in [13,2,5,9]]
            summaries.append(dict(model_id=mid,group=group,status='DIAGNOSTIC_ONLY_POST_HOC',images=sum(s['condition']==group or group=='overall' for s in c['members']),
                canonical_macro_recall4=m['groups'][group]['metrics']['macro_recall4'],
                mean_IoU_known_annotation_domain=float(np.mean([r['IoU_in_D'] for r in rows])),
                mean_Dice_known_annotation_domain=float(np.mean([r['Dice_in_D'] for r in rows])),
                annotated_pixels=int(h.sum()),full_image_IoU=None,person_F1=None))
            per_target += [dict(model_id=mid,group=group,**r) for r in rows]
        evidence[mid]=dict(exact_ids=90,atomic_score_and_metadata_hashes_checked=90,
            accepted_metrics_sha256=sha(root/'METRICS.json'),accepted_ledger_sha256=sha(root/'FRAMES.jsonl'),
            per_packet_histograms_reconcile_groups=True,full_NPZ_rehash='NOT_REPEATED; prior packet acceptance reused, bounded replay below')
    # Actual saved masks -> frozen composition/projection -> scorer on one fixed population member,
    # covering ROI, native-instance association and Sapiens full-frame ownership routes.
    sys.path[:0]=[str(W/'Human_Parsing_Benchmark/src'),str(P/'scripts')]
    from common_view.core import load_spec,compose_native,project
    from common_view.packets import read_packet
    from benchmark import partial_confusion
    from PIL import Image
    sample=c['members'][0];spec=load_spec(W/c['projection'])
    category=np.array(Image.open(W/c['dataset_root']/'Category_ids'/(sample['stem']+'.png')))
    sampled=[]
    for mid in ['QANet_CIHP_HRNetW48_512x384','CPI_ConvNeXtB_CIHP','Sapiens2_0.4b']:
        packet=raw/mid/'packets'/sample['id'];meta,arrays=read_packet(packet)
        prediction=project(compose_native(arrays['person_semantic_masks'],arrays['person_scores'],category.shape),meta['label_space'],spec)
        assert partial_confusion(category,prediction).tolist()==read(packet/'score_partial.json')['histogram']
        sampled.append(dict(model_id=mid,packets_replayed=1,NPZ_and_atomic_hashes='PASS',geometry_and_saved_confusion='PASS'))
    csvs={'KNOWN_DOMAIN_DIAGNOSTICS.csv':summaries,'KNOWN_DOMAIN_PER_TARGET.csv':per_target}
    for name,rows in csvs.items():
        path=P/'metrics'/name
        if path.exists():raise FileExistsError('Audit output already exists; do not overwrite')
        with path.open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    known=sum(audit['GT_native_pixel_support'][k] for k in [13,2,5,9]);total=sum(audit['GT_native_pixel_support'])
    report=dict(status='AUDIT_PASS_WITH_GT_SCOPE_LIMITATION',created_utc=datetime.now(timezone.utc).isoformat(),
        run_id=run_id,original_protocol=c['protocol'],derived_metric_scope='POST_HOC_ON_UNCHANGED_POSITIVE_ONLY_DOMAIN_NOT_NEW_FULL_BENCHMARK',
        config_sha256=sha(raw/'CONFIG.json'),audit_script_sha256=sha(Path(__file__)),
        protocol_sha256=sha(P/'PROTOCOL.md'),projection_sha256=sha(W/c['projection']),
        original_source_hashes_verified=source_checks,GT_reference_files_hash_verified=gt_hash_checks,
        membership_per_model=90,models_complete=9,total_image_pixels=total,known_annotated_pixels=known,
        known_fraction=known/total,unknown_pixels=audit['GT_native_pixel_support'][0],GT_people_with_annotated_parts=127,
        evidence=evidence,bounded_packet_replay=sampled,hand_counted_fixture='PASS',
        bulk_NPZ_rehash_or_full_rescore=False,model_calls=0,GT_modified=False,
        canonical_metrics_modified=False,full_image_IoU_identifiable=False,person_extent_F1_identifiable=False,
        limitations=['Outside annotated pixels unknown: false positives there are unmeasured',
            'Human_ids are part unions, not full person silhouettes','Face_Neck proxy and Dress policy unresolved',
            'Global semantics does not prove correct per-person ownership','Diagnostic formula/domain cannot establish overall deployment winner'])
    write(P/'reports/METRIC_AUDIT_EVIDENCE.json',report)
    print(json.dumps(dict(models=9,known_pixels=known,total_pixels=total,known_percent=known/total*100,
        source_bindings='PASS',metadata_scores_checked=810,saved_mask_replays=3,model_calls=0,overall=[r for r in summaries if r['group']=='overall']),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',required=True)
    audit(parser.parse_args().run)
