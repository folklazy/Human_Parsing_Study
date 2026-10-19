"""Fail-closed application scoring boundary. Draft research cannot produce scores.

CPU fixtures may exercise accepted synthetic contexts. Production callers must
provide an accepted, hash-bound scoring policy through executable configuration.
No benchmark permission is granted by this module.
"""
import copy
import numpy as np
from .policy import digest
from .evaluation import evaluate_persons, validate_person_inputs


def check_context(context, mapping, model_binding, trusted_input):
    if context.get('status') != 'ACCEPTED' or mapping.get('status') != 'ACCEPTED':
        raise ValueError('DRAFT/UNKNOWN scoring or mapping is not eligible')
    if context['mapping_sha256'] != digest(mapping):
        raise ValueError('Mapping fingerprint mismatch')
    if context['model_binding'] != model_binding:
        raise ValueError('Checkpoint/config/head/native class order binding mismatch')
    required = {'checkpoint_sha256', 'config_sha256', 'source_commit', 'native_class_order', 'native_taxonomy', 'head_classes'}
    if not required <= set(model_binding):
        raise ValueError('Incomplete model binding')
    if model_binding['head_classes'] != len(model_binding['native_class_order']):
        raise ValueError('Checkpoint head/class order mismatch')
    if context['input_binding'] != trusted_input or trusted_input.get('status') != 'VERIFIED':
        raise ValueError('Trusted image binding mismatch')
    if context['domain']['status'] != 'ACCEPTED' or not context['domain'].get('evidence'):
        raise ValueError('GT domain requires annotation evidence and acceptance')
    mode = context['target_support_policy']
    missing = mapping.get('unsupported_targets', {}).get(model_binding['native_taxonomy'])
    if missing is None:
        raise ValueError('Unknown target representability')
    if mode == 'COMMON_CAPABILITY' and missing:
        raise ValueError('Unsupported cohort targets')
    if mode not in {'COMMON_CAPABILITY', 'FIXED_TASK_EXPLICIT_UNSUPPORTED'}:
        raise ValueError('Explicit target support policy required')
    if context.get('require_checkpoint_specific_support'):
        from .cohorts import validate_support_binding
        validate_support_binding(context, mapping, model_binding)
    if context['failure_policy'] not in {'STRICT_COMPLETE', 'OPERATIONAL_EMPTY_FALLBACK'}:
        raise ValueError('Explicit failure policy required')


def score_frame(context, mapping, model_binding, trusted_input, gt, predictions, *, lifecycle):
    """Score only the actual validated arrays; no prediction-created void domains."""
    check_context(context, mapping, model_binding, trusted_input)
    # Snapshot prevents caller mutation between validation and scoring.
    gt, predictions = copy.deepcopy(gt), copy.deepcopy(predictions)
    for prediction in predictions:
        box = prediction.get('evaluation_bbox')
        if not isinstance(box, dict) or box.get('source') != context['evaluation_bbox_source'] or box.get('coordinate_convention') != 'XYXY_HALF_OPEN' or not box.get('derivation_revision'):
            raise ValueError('Evaluation bbox provenance differs from configured source')
        prediction['bbox'] = box['xyxy']
    kwargs = dict(original_wh=trusted_input['original_wh'])
    catalog = list(map(int, mapping['target_catalog']))
    # Validation precedes failure policy; corrupt outputs cannot become empty fallback.
    validate_person_inputs(gt, predictions, catalog, **kwargs)
    state = lifecycle['status']
    if state not in {'COMPLETE', 'PERSON_PARTIAL', 'MODEL_FRAME_FAILURE', 'LOAD_FAILURE',
                     'CONTRACT_FAILURE', 'SHARED_DATA_ERROR', 'EXTERNAL_INVALID', 'UNSCHEDULED', 'UNRESOLVED'}:
        raise ValueError('Unknown lifecycle state')
    allowed = {'COMPLETE'}
    if context['failure_policy'] == 'OPERATIONAL_EMPTY_FALLBACK':
        allowed |= set(context.get('fallback_states', [])) & {'PERSON_PARTIAL', 'MODEL_FRAME_FAILURE', 'LOAD_FAILURE'}
    if state not in allowed:
        return {'score_eligible': False, 'status': state, 'metrics': None, 'failure_events': lifecycle.get('events', [])}
    if state in {'MODEL_FRAME_FAILURE', 'LOAD_FAILURE'}:
        if predictions:
            raise ValueError('Frame fallback cannot retain partial native output')
    result = evaluate_persons(gt, predictions, catalog, context['threshold'], **kwargs)
    return {'score_eligible': True, 'status': state, 'metrics': result,
            'evaluator_fallback': state in {'MODEL_FRAME_FAILURE', 'LOAD_FAILURE'},
            'failure_events': lifecycle.get('events', []), 'scoring_context_sha256': digest(context)}


def require_retention(capabilities, operation):
    required = {'hard_remap': 'native_hard_labels', 'probability_aggregation': 'native_probabilities',
                'person_scoring': 'native_person_masks_scores'}
    if operation not in required or required[operation] not in capabilities:
        raise ValueError('Retained artifacts cannot support requested re-scoring operation')


def lifecycle_from_person_result(result, failure_scope):
    """Translate runner events once; failures never add localization penalties."""
    failures=result['failure_events']; statuses={e['status'] for e in failures}
    if 'CONTRACT_FAILURE' in statuses: state='CONTRACT_FAILURE'
    elif 'INVALID_ENV' in statuses: state='EXTERNAL_INVALID'
    elif 'UNRESOLVED_EVENT' in statuses: state='UNRESOLVED'
    elif statuses - {'MODEL_SYSTEM_FAILURE'}: state='UNRESOLVED'
    elif failures: state='MODEL_FRAME_FAILURE' if failure_scope=='FRAME' else 'PERSON_PARTIAL'
    elif any(e['status']=='NOT_ATTEMPTED' for e in result['opportunities']): state='UNSCHEDULED'
    elif result['trial_status']!='VALID_OPERATIONAL_TRIAL': state='UNRESOLVED'
    else: state='COMPLETE'
    return {'status':state,'events':copy.deepcopy(failures)}
