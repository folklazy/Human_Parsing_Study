"""CPU contracts for a new, isolated CCTV person-ROI cohort.

No model loading, original GT mutation, or model-dependent evaluation domains.
"""
from pathlib import Path
import hashlib
import json
import os
import numpy as np


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            digest.update(block)
    return digest.hexdigest()


def atomic(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temp, path)


def read(path):
    return json.loads(Path(path).read_text())


def pixel_sha(array):
    array = np.ascontiguousarray(array)
    prefix = json.dumps([array.dtype.str, list(array.shape)], separators=(',', ':')).encode()
    return hashlib.sha256(prefix + b'\0' + array.tobytes()).hexdigest()


def letterbox_canvas(rgb, input_hw, mean_rgb):
    import cv2
    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError('RGB uint8 input required')
    h, w = rgb.shape[:2]; ih, iw = input_hw
    ratio = min(iw/w, ih/h)
    nw, nh = max(1, round(w*ratio)), max(1, round(h*ratio))
    left, top = (iw-nw)//2, (ih-nh)//2
    mode = cv2.INTER_AREA if ratio < 1 else cv2.INTER_CUBIC
    canvas = np.broadcast_to(np.asarray(mean_rgb, np.float32), (ih, iw, 3)).copy()
    canvas[top:top+nh, left:left+nw] = cv2.resize(rgb, (nw, nh), interpolation=mode)
    return canvas, dict(original_hw=[h, w], input_hw=[ih, iw], resized_hw=[nh, nw],
                        padding_ltrb=[left, top, iw-nw-left, ih-nh-top], preserve_aspect_ratio=True)


def select_instance(boxes, scores, designated_box, threshold=.5):
    """Prediction-only IoU, then confidence/geometry/index; never semantic scores."""
    boxes, scores = np.asarray(boxes, float).reshape(-1, 4), np.asarray(scores, float)
    target = np.asarray(designated_box, float)
    if scores.shape != (len(boxes),) or not np.isfinite(boxes).all() or not np.isfinite(scores).all():
        raise ValueError('Malformed native candidate boxes/scores')
    if target.shape != (4,) or not np.isfinite(target).all() or np.any(target[2:] <= target[:2]):
        raise ValueError('Malformed designated detector box')
    if len(boxes) == 0:
        return None, []
    if np.any(boxes[:, 2:] < boxes[:, :2]):
        raise ValueError('Inverted candidate bbox')
    intersection = np.maximum(0, np.minimum(boxes[:, 2:], target[2:]) - np.maximum(boxes[:, :2], target[:2])).prod(1)
    areas = np.maximum(0, boxes[:, 2:] - boxes[:, :2]).prod(1)
    union = areas + np.prod(target[2:] - target[:2]) - intersection
    overlaps = np.divide(intersection, union, out=np.zeros_like(intersection), where=union > 0)
    eligible = [i for i in range(len(boxes)) if overlaps[i] >= threshold]
    selected = min(eligible, key=lambda i: (-overlaps[i], -scores[i], tuple(boxes[i]), i)) if eligible else None
    return selected, overlaps.tolist()


def validate_native(mask, classes, shape):
    if mask.shape != tuple(shape) or mask.dtype.kind not in 'ui' or (mask.size and (mask.min() < 0 or mask.max() >= classes)):
        raise ValueError('Native integer label/geometry contract failure')


def place(mask, box, extent, classes):
    x0, y0, x1, y1 = box
    validate_native(mask, classes, (y1 - y0, x1 - x0))
    if extent.dtype != bool or extent.ndim != 2 or not (0 <= x0 < x1 <= extent.shape[1] and 0 <= y0 < y1 <= extent.shape[0]):
        raise ValueError('Invalid original-grid extent/placement')
    outside = extent.copy(); outside[y0:y1, x0:x1] = False
    if outside.any():
        raise ValueError('Shared crop lost frozen detector extent')
    raw = np.zeros(extent.shape, np.uint8); raw[y0:y1, x0:x1] = mask
    return raw, np.where(extent, raw, 0).astype(np.uint8)


def counts(gt, prediction, valid=None):
    if gt.shape != prediction.shape or gt.dtype != bool or prediction.dtype != bool:
        raise ValueError('Boolean original-grid masks required')
    if valid is None:
        valid = np.ones(gt.shape, bool)
    if valid.shape != gt.shape or valid.dtype != bool:
        raise ValueError('Fixed boolean GT domain required')
    tp = int(np.count_nonzero(gt & prediction & valid))
    fp = int(np.count_nonzero(~gt & prediction & valid))
    fn = int(np.count_nonzero(gt & ~prediction & valid))
    return dict(TP=tp, FP=fp, FN=fn, GT_pixels=tp+fn, prediction_pixels=tp+fp,
                union=tp+fp+fn, IoU=tp/(tp+fp+fn) if tp+fp+fn else None,
                Dice=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)


def face_views(face, neck, candidate, uncertainty=None):
    if neck is None:
        return dict(status='GT_NECK_NOT_READY', FaceDomain=None, FaceNeck=None, NeckCoverage=None)
    if uncertainty is None:
        uncertainty = np.zeros(face.shape, bool)
    if any(a.shape != face.shape or a.dtype != bool for a in (face, neck, candidate, uncertainty)) or np.any(face & neck):
        raise ValueError('Disjoint, original-grid Face/Neck GT required')
    return dict(status='SCORED', FaceDomain=counts(face, candidate, ~(neck | uncertainty)),
                FaceNeck=counts(face | neck, candidate, ~uncertainty),
                NeckCoverage=float((candidate & neck & ~uncertainty).sum()/(neck & ~uncertainty).sum()) if (neck & ~uncertainty).any() else None)


def macro_four(target_rows):
    names = ('Hair', 'FaceDomain', 'Upper', 'Lower')
    means = {}
    for name in names:
        values = [r['IoU'] for r in target_rows if r['target'] == name and r['IoU'] is not None]
        means[name] = sum(values)/len(values) if values else None
    return dict(per_target=means, primary=sum(means.values())/4 if all(v is not None for v in means.values()) else None)


def reconcile(expected, accepted, failed=(), invalid=()):
    if len(set(expected)) != len(expected):
        raise ValueError('Duplicate expected IDs')
    extra = sorted(set(accepted)-set(expected))
    duplicate = len(accepted)-len(set(accepted))
    missing = sorted(set(expected)-set(accepted))
    complete = not (extra or duplicate or missing or failed or invalid)
    return dict(status='COMPLETE' if complete else 'INCOMPLETE', expected=len(expected), accepted_unique=len(set(accepted)),
                missing=len(missing), missing_ids=missing, duplicate=duplicate, unexpected_ids=extra,
                failed=len(failed), invalid=len(invalid), strict_complete=complete)
