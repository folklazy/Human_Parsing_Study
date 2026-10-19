"""Explicit numeric projection. Draft mappings authorize no benchmark."""
import numpy as np


def validate_mapping(mapping):
    if mapping.get('status') not in {'DRAFT', 'ACCEPTED'}:
        raise ValueError('Mapping status must be explicit')
    catalog = mapping['target_catalog']
    if list(map(int, catalog)) != list(range(len(catalog))):
        raise ValueError('Contiguous target IDs required')
    for section in ['gt_mapping', 'prediction_mapping']:
        for key, rule in mapping[section].items():
            if rule['disposition'] not in {'MAP', 'VOID', 'OUTSIDE_TARGET', 'UNMAPPED'}:
                raise ValueError('Unknown taxonomy disposition')
            if section == 'gt_mapping' and rule['disposition'] in {'OUTSIDE_TARGET', 'UNMAPPED'}:
                raise ValueError('Unsupported GT cannot silently become background')
            if section == 'prediction_mapping' and rule['disposition'] == 'VOID':
                raise ValueError('Prediction cannot change GT domain')
            if rule['disposition'] == 'MAP' and str(rule['target_id']) not in catalog:
                raise ValueError('Mapped target absent from catalog')
    return True


def project_gt(category, human, mapping):
    validate_mapping(mapping)
    category, human = np.asarray(category), np.asarray(human)
    if category.shape != human.shape or category.ndim != 2 or category.dtype.kind not in 'iu' or human.dtype.kind not in 'iu':
        raise ValueError('Original integer GT grids required')
    output = np.zeros_like(category, dtype=np.int16); valid = np.ones(category.shape, bool)
    for label in np.unique(category):
        rule = mapping['gt_mapping'].get(str(int(label)))
        if rule is None:
            raise ValueError(f'Undocumented GT label: {label}')
        region = category == label
        if rule['disposition'] == 'VOID':
            valid[region] = False
        else:
            output[region] = rule['target_id']
    valid[(human > 0) & (category == 0)] = False
    return output, valid


def project_prediction(native, mapping):
    validate_mapping(mapping)
    native = np.asarray(native)
    if native.ndim != 2 or native.dtype.kind not in 'iu':
        raise ValueError('Integer native prediction grid required')
    output = np.zeros(native.shape, np.int16)
    for label in np.unique(native):
        rule = mapping['prediction_mapping'].get(str(int(label)))
        if rule is None:
            raise ValueError(f'Native label not covered by mapping: {label}')
        output[native == label] = (rule['target_id'] if rule['disposition'] == 'MAP' else
                                  -1 if rule['disposition'] == 'UNMAPPED' else 0)
    return output
