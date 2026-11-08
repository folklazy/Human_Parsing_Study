"""Shared positive-person-part IoU3 and GT-box Face-local evaluation.

Separate from frozen C4-P/native scoring. No model calls or prediction mutation.
"""
import numpy as np
from .core import match_geometry, project, validate_prediction

TARGETS = {1: 'Face_local', 2: 'Hair', 3: 'Upper', 4: 'Lower'}


def counts(positive, predicted, valid, local=False):
    if positive.dtype != bool or predicted.dtype != bool or valid.dtype != bool:
        raise ValueError('Boolean original-grid masks required')
    if positive.shape != predicted.shape or positive.shape != valid.shape:
        raise ValueError('Mask geometry mismatch')
    domain = valid
    box = None
    if local:
        y, x = np.where(positive)
        if not len(x):
            raise ValueError('Cannot create Face box without GT positives')
        box = [int(x.min()), int(y.min()), int(x.max())+1, int(y.max())+1]
        domain = np.zeros_like(valid)
        domain[box[1]:box[3],box[0]:box[2]] = True
        domain &= valid
    g, p = positive & domain, predicted & domain
    tp = int((g & p).sum()); fp = int((~g & p).sum()); fn = int((g & ~p).sum())
    if not g.any():
        return None
    return dict(TP=tp, FP=fp, FN=fn, TN=int((domain & ~g & ~p).sum()),
        GT_pixels=tp+fn, prediction_pixels=tp+fp, union=tp+fp+fn,
        IoU=tp/(tp+fp+fn), Dice=2*tp/(2*tp+fp+fn),
        bbox_xyxy=box, ignored_prediction_pixels=int((predicted & ~domain).sum()))


def score_frame(gt, arrays, space, spec, cache=None):
    """GT keys: ids, extents, parts[(GT_id,target_id)], valid, shape.

    Full-frame GT-valid domain for positive C3 person-part tasks; Face is the
    tight *raw* GT-Face box intersected with the same GT-only validity domain.
    """
    planes, extents, scores = (arrays[k] for k in ['person_semantic_masks','person_extents','person_scores'])
    validate_prediction(planes,extents,scores,gt['shape'],space)
    if cache is not None and 'extents' in cache and np.array_equal(cache['extents'],extents):
        matches=cache['matches']
    else:
        matches={}
        for threshold in [.5,.75]:
            pairs,ambiguity=match_geometry(gt['extents'],extents,gt['ids'],threshold)
            matches[str(threshold)]=dict(pairs=pairs,ambiguity=ambiguity)
        if cache is not None:
            cache.update(extents=extents.copy(),matches=matches)
    matched={gt['ids'][i]:j for i,j,_ in matches['0.5']['pairs']}
    mapped=project(planes,space,spec)
    empty=np.zeros(gt['shape'],bool)
    rows=[]
    for (pid,target),positive in sorted(gt['parts'].items()):
        if not np.any(positive & gt['valid']):
            continue
        index=matched.get(pid)
        predicted=(mapped[index]==target) if index is not None else empty
        value=counts(positive,predicted,gt['valid'],local=target==1)
        if value is not None:
            rows.append(dict(gt_id=pid,target=target,unmatched=index is None,**value))
    localization={}
    for threshold,match in matches.items():
        n=len(match['pairs']);g=len(gt['ids']);p=len(planes)
        localization[threshold]=dict(TP=n,FP=p-n,FN=g-n,GT=g,predictions=p,
            ambiguous=int(match['ambiguity']['alternative_optimum']),
            identical_GT_geometry_groups=match['ambiguity']['identical_GT_geometry_groups'])
    return dict(parts=rows,localization=localization)


def summarize(frames, expected_ids):
    """Literal integer aggregation; missing/duplicate membership keeps primary null."""
    seen=[f['image_id'] for f in frames]
    complete=len(seen)==len(expected_ids) and len(set(seen))==len(seen) and set(seen)==set(expected_ids)
    result={}
    for target,name in TARGETS.items():
        rows=[r for f in frames for r in f['parts'] if r['target']==target]
        tp,fp,fn=(sum(r[k] for r in rows) for k in ['TP','FP','FN'])
        n=len(rows)
        result[name]=dict(GT_parts=n,TP=tp,FP=fp,FN=fn,GT_pixels=tp+fn,
            prediction_pixels=tp+fp,union=tp+fp+fn,unmatched_GT_parts=sum(r['unmatched'] for r in rows),
            mean_part_IoU=sum(r['IoU'] for r in rows)/n if complete and n else None,
            mean_part_Dice=sum(r['Dice'] for r in rows)/n if complete and n else None,
            pooled_IoU=tp/(tp+fp+fn) if complete and tp+fp+fn else None,
            precision=tp/(tp+fp) if complete and tp+fp else None,
            recall=tp/(tp+fn) if complete and tp+fn else None,
            F1_Dice=2*tp/(2*tp+fp+fn) if complete and 2*tp+fp+fn else None,
            ignored_prediction_pixels=sum(r['ignored_prediction_pixels'] for r in rows))
    values=[result[t]['mean_part_IoU'] for t in ['Hair','Upper','Lower']]
    loc={}
    for t in ['0.5','0.75']:
        a={k:sum(f['localization'][t][k] for f in frames) for k in ['TP','FP','FN','GT','predictions','ambiguous','identical_GT_geometry_groups']}
        a['F1']=2*a['TP']/(2*a['TP']+a['FP']+a['FN']) if complete and 2*a['TP']+a['FP']+a['FN'] else None
        loc[t]=a
    return dict(strict_complete=complete,expected=len(expected_ids),completed=len(seen),
        missing=len(set(expected_ids)-set(seen)),duplicate=len(seen)-len(set(seen)),
        primary_mIoU3_part_mean=sum(values)/3 if complete and all(v is not None for v in values) else None,
        Face_local_IoU=result['Face_local']['mean_part_IoU'] if complete else None,
        targets=result,localization=loc)
