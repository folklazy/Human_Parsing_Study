"""Common application metrics. No model-name branches or native AP overrides."""
import numpy as np
from scipy.optimize import linear_sum_assignment


def bbox_iou(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.shape != (4,) or b.shape != (4,) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Finite xyxy half-open boxes required')
    if a[2] <= a[0] or a[3] <= a[1] or b[2] <= b[0] or b[3] <= b[1]:
        return None  # Invalid geometry is never an eligible edge.
    inter = float(np.prod(np.maximum(0, np.minimum(a[2:], b[2:]) - np.maximum(a[:2], b[:2]))))
    union = float(np.prod(a[2:] - a[:2]) + np.prod(b[2:] - b[:2]) - inter)
    return inter / union


def clip_bbox(box, wh):
    box = np.asarray(box, float)
    if box.shape != (4,) or not np.isfinite(box).all() or len(wh) != 2 or min(wh) <= 0:
        raise ValueError('Invalid box/image grid')
    return np.clip(box, [0, 0, 0, 0], [wh[0], wh[1], wh[0], wh[1]]).tolist()


def assign(weights, left_ids, right_ids, threshold):
    """Eligible cardinality first, IoU second; canonical ID order pins ties.

    Tie policy: sort immutable IDs then use pinned SciPy solver. This promises
    permutation invariance for the pinned implementation, not a new universal
    lexicographic optimum across arbitrary future solver revisions.
    """
    if not 0 < threshold <= 1 or not np.isfinite(threshold):
        raise ValueError('Threshold must be positive and <=1')
    if any(not isinstance(v, str) or not v for v in [*left_ids, *right_ids]):
        raise ValueError('Immutable nonempty string IDs required')
    if len(set(left_ids)) != len(left_ids) or len(set(right_ids)) != len(right_ids):
        raise ValueError('Duplicate matching IDs')
    n, m = len(left_ids), len(right_ids)
    values = np.asarray(weights, dtype=float).reshape(n, m)
    if np.any(np.isfinite(values) & ((values < 0) | (values > 1))):
        raise ValueError('Finite matching weights must be IoUs in [0,1]')
    if not n or not m:
        return {'matches': [], 'unmatched_left': sorted(left_ids), 'unmatched_right': sorted(right_ids)}
    li, ri = sorted(range(n), key=lambda i: left_ids[i]), sorted(range(m), key=lambda i: right_ids[i])
    ordered = values[np.ix_(li, ri)]
    eligible = np.isfinite(ordered) & (ordered >= threshold)
    bonus = min(n, m) + 1
    utility = np.zeros((n + m, n + m))
    utility[:n, :m] = np.where(eligible, bonus + ordered, -bonus)
    rows, cols = linear_sum_assignment(utility, maximize=True)
    matches = [(left_ids[li[r]], right_ids[ri[c]], float(ordered[r, c]))
               for r, c in zip(rows, cols) if r < n and c < m and eligible[r, c]]
    return {'matches': matches,
            'unmatched_left': sorted(set(left_ids) - {a for a, _, _ in matches}),
            'unmatched_right': sorted(set(right_ids) - {b for _, b, _ in matches})}


def match_boxes(left, right, threshold):
    weights = [[bbox_iou(a['bbox'], b['bbox']) for b in right] for a in left]
    return assign(weights, [v['id'] for v in left], [v['id'] for v in right], threshold)


def associate_native(opportunities, native_instances, threshold):
    """T3b association accepts only predicted records; GT is not an input."""
    result = match_boxes(opportunities, native_instances, threshold)
    return {'associations': [{'source_opportunity_id': op, 'native_instance_id': native, 'iou': iou}
                             for op, native, iou in result['matches']],
            'unmatched_opportunities': result['unmatched_left'],
            'unmatched_native_instances': result['unmatched_right']}


def confusion(gt, prediction, catalog, valid):
    gt, prediction, valid = np.asarray(gt), np.asarray(prediction), np.asarray(valid)
    if gt.ndim != 2 or gt.shape != prediction.shape or gt.shape != valid.shape or valid.dtype != bool:
        raise ValueError('Matching 2D grids and boolean GT-derived domain required')
    if gt.dtype.kind not in 'iu' or prediction.dtype.kind not in 'iu':
        raise ValueError('Integer categorical labels required')
    if list(catalog) != list(range(len(catalog))) or not catalog:
        raise ValueError('Canonical contiguous target catalog including BG0 required')
    n = len(catalog)
    if not set(map(int, np.unique(gt[valid]))) <= set(catalog):
        raise ValueError('Unsupported GT labels must use a shared GT void policy')
    if not set(map(int, np.unique(prediction))) <= (set(catalog) | {-1}):
        raise ValueError('Invalid decoder ID is a contract failure, not UNMAPPED')
    projected = np.where(prediction[valid] == -1, n, prediction[valid])
    return np.bincount(gt[valid].astype(np.int64) * (n + 1) + projected.astype(np.int64),
                       minlength=n * (n + 1)).reshape(n, n + 1)


def semantic_scores(hist, scored_classes):
    hist = np.asarray(hist)
    if hist.ndim != 2 or hist.dtype.kind not in 'iu':
        raise ValueError('Integer finite confusion counts required')
    n = hist.shape[0]
    if hist.shape != (n, n + 1) or np.any(hist < 0):
        raise ValueError('Confusion matrix requires explicit error column')
    if len(set(scored_classes)) != len(scored_classes) or any(c <= 0 or c >= n for c in scored_classes):
        raise ValueError('Explicit foreground scored class set required')
    gt_support, pred_support = hist.sum(1), hist[:, :n].sum(0)
    tp = np.diag(hist[:, :n]); union = gt_support + pred_support - tp
    ious = [float(tp[c] / union[c]) if union[c] else None for c in range(n)]
    mean = (sum(ious[c] for c in scored_classes) / len(scored_classes)
            if scored_classes and all(ious[c] is not None for c in scored_classes) else None)
    return {'miou_gt_supported': mean, 'scored_classes': list(scored_classes),
            'iou': ious, 'gt_support': gt_support.tolist(), 'prediction_support': pred_support.tolist(),
            'prediction_only_class_fp_pixels': {str(c): int(pred_support[c]) for c in range(1, n)
                                               if not gt_support[c] and pred_support[c]},
            'unmapped_pixels': int(hist[:, n].sum()), 'unmapped_on_known_negative_pixels': int(hist[0, n])}


def foreground_counts(gt, prediction, catalog, valid):
    confusion(gt, prediction, catalog, valid)  # Reject decoder/domain errors.
    truth = np.isin(gt, list(catalog)[1:]) & valid
    output = (np.isin(prediction, list(catalog)[1:]) | (prediction == -1)) & valid
    tp = int(np.count_nonzero(truth & output)); fp = int(np.count_nonzero(output & ~truth))
    fn = int(np.count_nonzero(truth & ~output))
    return {'tp': tp, 'fp': fp, 'fn': fn, 'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tp / (tp + fn) if tp + fn else None, 'iou': tp / (tp + fp + fn) if tp + fp + fn else None}


def validate_person_inputs(gt_persons, predictions, catalog, *, original_wh):
    # Validate actual objects before matching, including unmatched/no-GT outputs.
    if len(original_wh) != 2 or any(type(v) is not int or v <= 0 for v in original_wh):
        raise ValueError('Trusted original image W/H required')
    shape = (original_wh[1], original_wh[0])
    if list(catalog) != list(range(len(catalog))) or not catalog:
        raise ValueError('Contiguous target catalog required')
    for collection, is_gt in ((gt_persons, True), (predictions, False)):
        ids = [r['id'] for r in collection]
        if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
            raise ValueError('Unique nonempty person IDs required')
        for r in collection:
            if bbox_iou(r['bbox'], r['bbox']) is None:
                raise ValueError('Invalid person box')
            if is_gt:
                if type(r['loc_eligible']) is not bool or type(r['sem_eligible']) is not bool:
                    raise ValueError('Explicit boolean GT eligibility required')
                if r['sem_eligible'] and not r['loc_eligible']:
                    raise ValueError('G_sem must be a subset of G_loc')
            elif r.get('score') is not None and (not np.isscalar(r['score']) or not np.isfinite(r['score'])):
                raise ValueError('Finite scalar prediction score required')
            if not is_gt or r['sem_eligible'] or 'semantic' in r:
                mask = np.asarray(r['semantic'])
                if mask.shape != shape or mask.dtype.kind not in 'iu':
                    raise ValueError('Integer masks must match trusted original W/H')
                if not is_gt and not set(map(int, np.unique(mask))) <= set(catalog) | {-1}:
                    raise ValueError('Invalid decoder label before matching')
                if is_gt and r['sem_eligible']:
                    confusion(mask, np.zeros(shape, np.int16), catalog, r['valid'])
    return True


def evaluate_persons(gt_persons, predictions, catalog, threshold, *, original_wh):
    """Pair all G_loc once; score G_sem without class-guided rematching."""
    validate_person_inputs(gt_persons, predictions, catalog, original_wh=original_wh)
    gt = sorted((g for g in gt_persons if g['loc_eligible']), key=lambda g: g['id'])
    pairing = match_boxes(gt, predictions, threshold)
    pred_by_id = {p['id']: p for p in predictions}
    pairs = {g: p for g, p, _ in pairing['matches']}
    rows = []
    for g in gt:
        if not g['sem_eligible']:
            rows.append({'gt_id': g['id'], 'semantic_quality': None, 'semantic_status': 'UNDEFINED_GT',
                         'prediction_id': pairs.get(g['id'])})
            continue
        truth, valid = g['semantic'], g['valid']
        supported = sorted(int(c) for c in np.unique(truth[valid]) if c > 0)
        if not supported:
            raise ValueError('G_sem declared eligible without any target GT support')
        p = pred_by_id.get(pairs.get(g['id']))
        prediction = np.zeros_like(truth) if p is None else p['semantic']
        sem = semantic_scores(confusion(truth, prediction, catalog, valid), supported)
        fg = foreground_counts(truth, prediction, catalog, valid)
        rows.append({'gt_id': g['id'], 'prediction_id': p['id'] if p else None,
                     'semantic_quality': sem['miou_gt_supported'], 'semantic_status': 'DEFINED' if p else 'MISSED',
                     'foreground': fg, 'semantic_diagnostics': sem,
                     'target_available': bool(p is not None and np.isin(prediction, list(catalog)[1:]).any())})
    sem_rows = [r for r in rows if r['semantic_quality'] is not None]
    tp = len(pairing['matches']); emitted = len(predictions)
    return {'matching': pairing, 'per_person': rows, 'G_loc': len(gt), 'G_sem': len(sem_rows),
            'final_precision': tp / emitted if emitted else None, 'final_recall': tp / len(gt) if gt else None,
            'final_fp': len(pairing['unmatched_right']), 'final_fn': len(pairing['unmatched_left']),
            'gt_person_target_availability': sum(r['target_available'] for r in sem_rows) / len(sem_rows) if sem_rows else None,
            'Q_person_sem_GT': sum(r['semantic_quality'] for r in sem_rows) / len(sem_rows) if sem_rows else None,
            'Q_person_fg': sum(r['foreground']['iou'] for r in sem_rows) / len(sem_rows) if sem_rows else None}


def person_truth(global_labels, human_ids, global_valid, person_id):
    """Known neighboring people are negatives; unowned foreground is void."""
    if global_labels.shape != human_ids.shape or global_valid.shape != human_ids.shape:
        raise ValueError('Original GT grids differ')
    valid = global_valid & ~((global_labels > 0) & (human_ids == 0))
    return np.where(human_ids == person_id, global_labels, 0), valid


class SemanticAccumulator:
    """Accumulate confusion first; fixed class set never follows model success."""
    def __init__(self, catalog, scored_classes, groups=None):
        self.catalog = list(catalog); self.scored_classes = list(scored_classes)
        self.histogram = np.zeros((len(catalog), len(catalog) + 1), np.int64)
        self.groups = groups or {}

    def update(self, gt, prediction, valid):
        self.histogram += confusion(gt, prediction, self.catalog, valid)

    def report(self):
        result = semantic_scores(self.histogram, self.scored_classes)
        result['group_scores'] = {name: semantic_scores(self.histogram, [c for c in classes if c in self.scored_classes])['miou_gt_supported']
                                  for name, classes in self.groups.items()}
        return result
