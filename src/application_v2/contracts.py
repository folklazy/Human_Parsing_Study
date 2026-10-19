"""Identity/array contract v2. Native identities and conditioning are independent."""
import math
import numpy as np


ORIGINS = {'NATIVE_MODEL', 'YOLO_CONDITIONED', 'ORACLE_INPUT', 'NATIVE_AND_YOLO', 'NATIVE_AND_ORACLE'}


def validate_identity(identity):
    required = {'origin', 'native_identity_supported', 'native_instance_id',
                'conditioning_source', 'source_opportunity_id', 'final_person_id'}
    if required - set(identity):
        raise ValueError('Incomplete identity provenance')
    origin = identity['origin']
    if origin not in ORIGINS or type(identity['native_identity_supported']) is not bool:
        raise ValueError('Invalid identity origin/capability')
    native = origin in {'NATIVE_MODEL', 'NATIVE_AND_YOLO', 'NATIVE_AND_ORACLE'}
    if native != identity['native_identity_supported']:
        raise ValueError('External identity does not establish native capability')
    if native != (identity['native_instance_id'] is not None):
        raise ValueError('Native identity must be retained exactly when supported')
    expected = {'NATIVE_MODEL': None, 'NATIVE_AND_YOLO': 'YOLO', 'NATIVE_AND_ORACLE': 'ORACLE',
                'YOLO_CONDITIONED': 'YOLO', 'ORACLE_INPUT': 'ORACLE'}[origin]
    if identity['conditioning_source'] != expected:
        raise ValueError('Conditioning source and origin disagree')
    conditioned = expected is not None
    if conditioned != (identity['source_opportunity_id'] is not None):
        raise ValueError('Conditioning opportunity must be retained')
    for key in ['native_instance_id', 'source_opportunity_id', 'final_person_id']:
        value = identity[key]
        if value is not None and (not isinstance(value, str) or not value):
            raise ValueError('Identity IDs must be nonempty strings')
    if identity['final_person_id'] is None:
        raise ValueError('Final person identity required')
    return True


def native_instance_count(supported, native_ids):
    if type(supported) is not bool:
        raise ValueError('Explicit native capability required')
    if not supported:
        if native_ids is not None:
            raise ValueError('Semantic-only native identity list must be null')
        return {'value': None, 'status': 'N/A_UNSUPPORTED'}
    if not isinstance(native_ids, list) or any(not isinstance(v, str) or not v for v in native_ids) or len(native_ids) != len(set(native_ids)):
        raise ValueError('Native instance IDs must be unique')
    return {'value': len(native_ids), 'status': 'DEFINED'}


def validate_frame(record, masks):
    if record.get('schema_version') != '2.0' or record.get('mask_grid_space') != 'ORIGINAL':
        raise ValueError('Canonical v2 masks must declare ORIGINAL coordinates')
    for key in ['study_id', 'run_id', 'system_id', 'model_id', 'image_id',
                'adapter_revision', 'execution_profile', 'source_track']:
        if not isinstance(record.get(key), str) or not record[key]:
            raise ValueError(f'Missing canonical metadata: {key}')
    revision = record.get('source_commit')
    if not isinstance(revision, str) or len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Exact native source revision required')
    if not isinstance(record.get('geometry_metadata'), dict) or not isinstance(record.get('precision_profile'), dict):
        raise ValueError('Native geometry and component precision metadata required')
    for key in ['checkpoint_sha256', 'config_sha256', 'input_sha256']:
        value = record.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError(f'Invalid fingerprint: {key}')
    wh = record.get('original_wh')
    if not isinstance(wh, list) or len(wh) != 2 or any(type(v) is not int or v <= 0 for v in wh):
        raise ValueError('Positive integer original W/H required')
    labels = record['label_catalog']
    if not labels or any(type(v) is not int for v in labels) or len(labels) != len(set(labels)):
        raise ValueError('Explicit unique output label catalog required')
    space = record.get('label_space', 'NATIVE')
    if space not in {'NATIVE', 'COMMON', 'NATIVE_OWNERSHIP_DERIVED'}:
        raise ValueError('Unknown native/common semantic label space')
    if space != 'COMMON' and (0 not in labels or any(v < 0 for v in labels)):
        raise ValueError('Native label inventories must include BG0 and no invented negative IDs')
    masks = np.asarray(masks)
    persons = record['persons']
    if masks.shape != (len(persons), wh[1], wh[0]) or masks.dtype.kind not in 'iu':
        raise ValueError('Declared original coordinate mask grid differs')
    if not set(map(int, np.unique(masks))) <= set(labels):
        raise ValueError('Out-of-range native/canonical labels')
    final_ids, native_ids = [], []
    for index, person in enumerate(persons):
        validate_identity(person['identity'])
        if person['identity']['native_identity_supported'] != record['native_identity_supported']:
            raise ValueError('Final records must preserve the declared native identity interface')
        final_ids.append(person['identity']['final_person_id'])
        if person['identity']['native_instance_id'] is not None:
            native_ids.append(person['identity']['native_instance_id'])
        score = person.get('score')
        if score is not None and (not isinstance(score, (int, float)) or not math.isfinite(score)):
            raise ValueError('Unsupported scores are null; supplied scores must be finite')
        if record.get('label_space', 'NATIVE') == 'NATIVE':
            if not np.any(masks[index] != 0):
                raise ValueError('All-background native parsing cannot fabricate final emission')
        elif person.get('native_foreground_nonempty') is not True:
            raise ValueError('Common-space final emission must retain native foreground provenance')
    if len(final_ids) != len(set(final_ids)) or len(native_ids) != len(set(native_ids)):
        raise ValueError('Duplicate final/native identities in one frame')
    count = native_instance_count(record['native_identity_supported'], record['native_instance_ids'])
    # T3b may gate out native instances; preserve the complete native inventory.
    if record['native_identity_supported'] and not set(native_ids) <= set(record['native_instance_ids']):
        raise ValueError('Final native identities absent from native inventory')
    if not record['native_identity_supported'] and native_ids:
        raise ValueError('Fabricated native instances')
    if record['source_track'] == 'T3B' and any(p['identity']['origin'] != 'NATIVE_AND_YOLO' for p in persons):
        raise ValueError('T3b must preserve both native and YOLO identity')
    if record['source_track'] == 'T3A' and any(p['identity']['conditioning_source'] != 'YOLO' for p in persons):
        raise ValueError('T3a conditioning identity required')
    if record['source_track'] == 'T2' and any(p['identity']['conditioning_source'] != 'ORACLE' for p in persons):
        raise ValueError('Oracle input identity required')
    if record['source_track'] not in {'T1', 'T2', 'T3A', 'T3B'}:
        raise ValueError('Unknown versioned source track')
    return count


def availability(*, completed, native_foreground_nonempty, final_emitted,
                 target_foreground_nonempty):
    if (final_emitted or target_foreground_nonempty) and not completed:
        raise ValueError('Failed contract cannot emit completed output')
    if target_foreground_nonempty and not final_emitted:
        raise ValueError('Target availability requires an emitted person')
    if final_emitted and not native_foreground_nonempty:
        raise ValueError('All-background output cannot fabricate a person')
    return {'execution_completed': bool(completed),
            'native_foreground_nonempty': bool(native_foreground_nonempty),
            'final_emitted': bool(final_emitted),
            'target_semantic_available': bool(target_foreground_nonempty)}


def stage_rate(stage, unit, events):
    """Eligibility is supplied from frozen routing policy, never from success."""
    if not isinstance(stage, str) or not stage or not isinstance(unit, str) or not unit:
        raise ValueError('Named stage and unit required')
    statuses = {'COMPLETED', 'FAILED', 'SKIPPED_BY_ROUTING', 'NOT_ATTEMPTED'}
    seen = set()
    for event in events:
        if not isinstance(event['unit_id'], str) or not event['unit_id'] or event['unit_id'] in seen or type(event['eligible']) is not bool or event['status'] not in statuses:
            raise ValueError('Invalid/duplicate stage unit')
        seen.add(event['unit_id'])
        if not event['eligible'] and event['status'] in {'COMPLETED', 'FAILED'}:
            raise ValueError('Ineligible units must not silently enter execution')
    denominator = sum(e['eligible'] for e in events)
    numerator = sum(e['eligible'] and e['status'] == 'COMPLETED' for e in events)
    return {'stage': stage, 'unit': unit, 'numerator': numerator, 'denominator': denominator,
            'value': numerator / denominator if denominator else None,
            'status': 'DEFINED' if denominator else 'UNDEFINED_ZERO_ELIGIBLE_UNITS',
            'skipped_by_routing': sum(e['status'] == 'SKIPPED_BY_ROUTING' for e in events)}
