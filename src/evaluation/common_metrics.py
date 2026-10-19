"""Study-specific metric primitives, not an official MHP evaluator."""
import numpy as np
from scipy.optimize import linear_sum_assignment


def confusion_matrix(gt, prediction, classes, valid=None, ignore_id=255):
    gt = np.asarray(gt); prediction = np.asarray(prediction)
    if gt.shape != prediction.shape or gt.ndim != 2:
        raise ValueError('Prediction and GT must share an explicit 2D grid')
    valid = np.ones(gt.shape, bool) if valid is None else np.asarray(valid, bool)
    if valid.shape != gt.shape:
        raise ValueError('Invalid evaluation domain')
    valid = valid & (gt != ignore_id)
    if np.any((gt[valid] < 0) | (gt[valid] >= classes)):
        raise ValueError('GT has unsupported labels; approve a shared projection first')
    # An extra column penalizes UNMAPPED predictions; never favorable ignore.
    projected = np.where((prediction >= 0) & (prediction < classes), prediction, classes)
    return np.bincount((classes + 1) * gt[valid].astype(np.int64) + projected[valid].astype(np.int64),
                       minlength=classes * (classes + 1)).reshape(classes, classes + 1)


def scores(histogram, include_background=False):
    histogram = np.asarray(histogram)
    n = histogram.shape[0]
    if histogram.shape != (n, n + 1): raise ValueError('Expected explicit UNMAPPED column')
    true_positive = np.diag(histogram[:, :n]).astype(float)
    gt_support = histogram.sum(1); prediction_support = histogram[:, :n].sum(0)
    union = gt_support + prediction_support - true_positive
    iou = np.divide(true_positive, union, out=np.full(n, np.nan), where=union > 0)
    dice_denominator = gt_support + prediction_support
    dice = np.divide(2 * true_positive, dice_denominator, out=np.full(n, np.nan), where=dice_denominator > 0)
    selected = np.arange(n) if include_background else np.arange(1, n)
    mean_iou = float(np.nanmean(iou[selected])) if np.any(np.isfinite(iou[selected])) else None
    return {'iou':iou.tolist(), 'dice':dice.tolist(), 'miou':mean_iou,
            'gt_support':gt_support.tolist(),'prediction_support':prediction_support.tolist(),
            'pixel_accuracy':float(true_positive.sum()/histogram.sum()) if histogram.sum() else None,
            'unmapped_prediction_pixels':int(histogram[:, n].sum())}


def person_macro(gt_planes, prediction_planes, classes, include_background=False):
    if len(gt_planes) != len(prediction_planes): raise ValueError('Missing persons must be represented explicitly')
    per_person = [scores(confusion_matrix(gt,pred,classes), include_background)['miou']
                  for gt,pred in zip(gt_planes,prediction_planes)]
    defined = [value for value in per_person if value is not None]
    return {'person_macro_miou':float(np.mean(defined)) if defined else None,
            'per_person':per_person,'defined_persons':len(defined),'all_gt_persons':len(gt_planes)}


def mask_iou(a,b,valid=None):
    a=np.asarray(a,bool); b=np.asarray(b,bool)
    if a.shape!=b.shape: raise ValueError('Matching grids differ')
    domain=np.ones(a.shape,bool) if valid is None else np.asarray(valid,bool)
    if domain.shape != a.shape: raise ValueError('Matching valid-domain grid differs')
    union=np.count_nonzero((a|b)&domain)
    return float(np.count_nonzero(a&b&domain)/union) if union else 0.0


def match_persons(gt_masks, predictions, threshold=.5, valid=None):
    """Max eligible cardinality, then IoU; IDs/list order pre-sorted globally.

    Dummy assignments allow unmatched persons. This prevents unconstrained
    Hungarian followed by thresholding from losing an available valid match.
    Threshold is a DRAFT design default, not validation-tuned.
    """
    if not 0 < threshold <= 1: raise ValueError('Positive matching threshold required; empty masks must not match')
    ng,npred=len(gt_masks),len(predictions)
    if not ng or not npred: return {'matches':[], 'unmatched_gt':list(range(ng)), 'unmatched_predictions':list(range(npred))}
    values=np.array([[mask_iou(g,p,valid) for p in predictions] for g in gt_masks])
    size=ng+npred; utility=np.zeros((size,size))
    bonus=min(ng,npred)+1
    utility[:ng,:npred]=np.where(values>=threshold, bonus+values, -bonus)
    rows,columns=linear_sum_assignment(utility,maximize=True)
    matched=[(int(r),int(c),float(values[r,c])) for r,c in zip(rows,columns) if r<ng and c<npred and values[r,c]>=threshold]
    return {'matches':matched,'unmatched_gt':[i for i in range(ng) if i not in {r for r,_,_ in matched}],
            'unmatched_predictions':[i for i in range(npred) if i not in {c for _,c,_ in matched}]}


def target_ownership(semantic, target_mask, neighbor_masks=()):
    """Draft post-parsing ownership, preserving untouched semantic prediction.

    YOLO-only deployment masks may restrict a derived ownership view, never
    RGB preprocessing or native outputs. Ambiguous intersections remain void.
    """
    semantic=np.asarray(semantic); target_mask=np.asarray(target_mask,bool)
    if semantic.shape!=target_mask.shape: raise ValueError('Ownership grid mismatch')
    neighbors=np.zeros(target_mask.shape,bool)
    for mask in neighbor_masks:
        if np.asarray(mask).shape!=target_mask.shape: raise ValueError('Neighbor grid mismatch')
        neighbors|=np.asarray(mask,bool)
    ambiguity=target_mask&neighbors
    owned=np.where(target_mask&~ambiguity,semantic,-1)
    return {'owned_labels':owned,'ambiguous_mask':ambiguity,
            'native_foreground_outside_target_pixels':int(np.count_nonzero((semantic>0)&~target_mask)),
            'status':'DRAFT_REQUIRES_DEVELOPMENT_REVIEW'}
