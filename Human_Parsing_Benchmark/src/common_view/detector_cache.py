"""Lossless adapter for existing binary detector-mask storage, not new ownership."""
import numpy as np


def normalize_detector_masks(masks, count, hw):
    masks = np.asarray(masks)
    if masks.shape != (count, *hw) or masks.dtype.kind not in 'uib':
        raise ValueError('Frozen detector mask grid/dtype mismatch')
    if np.any((masks != 0) & (masks != 1)):
        raise ValueError('Expected cached binary0/1, not thresholdable predictions')
    result = masks.astype(bool, copy=True)
    if not np.array_equal(result.astype(masks.dtype), masks):
        raise ValueError('Lossless detector mask conversion failed')
    return result
