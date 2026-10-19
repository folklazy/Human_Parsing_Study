"""Executable configuration is authoritative; prose is never parsed by runners."""
import copy
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def field(value, path):
    for part in path.split('.'):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f'Missing configuration binding: {path}')
        value = value[part]
    return value


def validate_config(config, decisions, *, benchmark=False):
    if config.get('schema_version') != '2.0' or decisions.get('schema_version') != '2.0':
        raise ValueError('Unsupported configuration/decision version')
    if config.get('decision_record_id') != decisions.get('record_id'):
        raise ValueError('Configuration references a different decision record')
    if config.get('decision_record_sha256') != digest(decisions):
        raise ValueError('Decision content fingerprint mismatch')
    for decision in decisions['decisions']:
        if decision['status'] == 'ACCEPTED_BY_USER':
            for path, expected in decision['bindings'].items():
                if field(config, path) != expected:
                    raise ValueError(f'Accepted decision conflict: {decision["id"]}: {path}')
        elif decision['status'] != 'PROPOSED':
            raise ValueError('Unknown decision acceptance status')
    if config['authorization']['new_inference'] and not benchmark:
        accepted = {d['id'] for d in decisions['decisions'] if d['status'] == 'ACCEPTED_BY_USER'}
        if not config['authorization'].get('bounded_train_inference') or 'BOUNDED_TRAIN_INTEGRATION' not in accepted:
            raise ValueError('New inference requires accepted bounded TRAIN permission')
        if config['bounded_train']['maximum_frames'] > 3 or config['bounded_train']['maximum_person_jobs'] > 10:
            raise ValueError('Bounded implementation scope exceeded')
    if config['authorization']['full_benchmark']:
        # Execution permission cannot be granted by editing only a draft config.
        if not benchmark:
            raise ValueError('This implementation scope does not authorize a full benchmark')
    if benchmark:
        if config.get('status') != 'FROZEN' or not config['authorization']['full_benchmark']:
            raise ValueError('Benchmark is not authorized/frozen')
        if config.get('pending_score_decisions'):
            raise ValueError('Score-affecting decisions remain pending')
        accepted = {d['id'] for d in decisions['decisions'] if d['status'] == 'ACCEPTED_BY_USER'}
        if not set(config['required_freeze_decisions']) <= accepted:
            raise ValueError('Benchmark decisions have not been accepted')
        if not config.get('readiness_artifact_sha256'):
            raise ValueError('Actual integration/readiness evidence is required')
    return True


def load_config(path, *, benchmark=False):
    import yaml
    path = Path(path).resolve()
    study = path.parents[1]
    config = yaml.safe_load(path.read_text())
    record = (study / config['decision_record']).resolve()
    if not record.is_relative_to(study):
        raise ValueError('Decision record must remain inside the study')
    decisions = json.loads(record.read_text())
    validate_config(config, decisions, benchmark=benchmark)
    for key, path_key in [('mapping_sha256', 'mapping'), ('native_reference_sha256', 'native_reference'),
                          ('sidecars_manifest_sha256', 'sidecars_manifest')]:
        if key in config['cohort']:
            source = study / config['cohort'][path_key]
            if hashlib.sha256(source.read_bytes()).hexdigest() != config['cohort'][key]:
                raise ValueError('Cohort source changed without versioned config fingerprint')
    return config


def fingerprints(config, inference_inputs):
    """GT-derived oracle geometry belongs to inference dependencies, not scoring."""
    inference = {'inputs': inference_inputs, 'systems': config['systems'],
                 'routing': config['routing'], 'execution': config['execution'],
                 'bounded_train': config.get('bounded_train')}
    scoring = {'cohort': config['cohort'], 'evaluation': config['evaluation'],
               'populations': config['populations']}
    return {'inference': digest(inference), 'scoring': digest(scoring)}
