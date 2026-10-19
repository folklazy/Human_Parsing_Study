"""Lossless CCIHP person planes, with no claim of native CIHP equivalence.

Labels are retained as supplied, including unknown IDs and unassigned semantic
pixels. Human masks and categorical planes remain separate. No ownership repair,
resize, class harmonization or evaluator policy is applied here.
"""
import numpy as np


def person_planes(category, human, instance):
    arrays = [np.asarray(x) for x in [category, human, instance]]
    if any(a.ndim != 2 or a.dtype.kind not in 'ui' for a in arrays):
        raise ValueError('GT requires 2D unsigned/integer source grids')
    if any(a.shape != arrays[0].shape for a in arrays) or any(np.any(a < 0) for a in arrays):
        raise ValueError('GT grids/dimensions/IDs invalid')
    category, human, instance = arrays
    result = []
    for person_id in np.unique(human):
        if person_id == 0:
            continue
        support = human == person_id
        yy, xx = np.nonzero(support)
        result.append({'person_id': int(person_id), 'foreground_mask': support,
                       'semantic': np.where(support, category, 0),
                       'attribute_instances': np.where(support, instance, 0),
                       'bbox_xyxy_half_open': [int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)]})
    return {'original_wh': [category.shape[1], category.shape[0]], 'persons': result,
            'unassigned_semantic': np.where(human == 0, category, 0),
            'unassigned_attribute_instances': np.where(human == 0, instance, 0),
            'taxonomy': 'CCIHP_NATIVE_UNHARMONIZED', 'native_CIHP_equivalence': False}


def reconstruct(planes, category_dtype, human_dtype, instance_dtype):
    semantic = np.array(planes['unassigned_semantic'], dtype=category_dtype, copy=True)
    instance = np.array(planes['unassigned_attribute_instances'], dtype=instance_dtype, copy=True)
    human = np.zeros(semantic.shape, dtype=human_dtype)
    for person in planes['persons']:
        support = person['foreground_mask']
        if np.any(human[support] != 0):
            raise ValueError('Overlapping person planes cannot be silently flattened')
        human[support] = person['person_id']
        semantic[support] = person['semantic'][support]
        instance[support] = person['attribute_instances'][support]
    return semantic, human, instance
