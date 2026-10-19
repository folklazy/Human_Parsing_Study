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
    if config.get('scoring_context') is not None and config.get('scoring_contexts') is not None:
        raise ValueError('Use either a single context or a per-system/image registry, never both')
    for name, decision_id in [('scoring_context', 'SCORING_CONTEXT'), ('scoring_contexts', 'SCORING_CONTEXTS')]:
        if config.get(name) is not None:
            accepted_contexts = [d for d in decisions['decisions'] if d['id'] == decision_id
                                 and d['status'] == 'ACCEPTED_BY_USER']
            if not accepted_contexts or accepted_contexts[0]['bindings'].get(name) != config[name]:
                raise ValueError('Scoring context lacks an accepted decision binding')
            if name == 'scoring_contexts':
                if accepted_contexts[0]['bindings'].get('scoring_population') != config.get('scoring_population'):
                    raise ValueError('Scoring population lacks an accepted decision binding')
                from .contexts import validate_context_registry
                validate_context_registry(config)
    if config['authorization']['new_inference'] and not benchmark:
        accepted = {d['id'] for d in decisions['decisions'] if d['status'] == 'ACCEPTED_BY_USER'}
        if not config['authorization'].get('bounded_train_inference') or 'BOUNDED_TRAIN_INTEGRATION' not in accepted:
            raise ValueError('New inference requires accepted bounded TRAIN permission')
        if config['bounded_train']['maximum_frames'] > 3 or config['bounded_train']['maximum_person_jobs'] > 10:
            raise ValueError('Bounded implementation scope exceeded')
    if config.get('first_cohort'):
        protocol = config['first_cohort'].get('protocol')
        if protocol:
            final = protocol['matching']['final_prediction_to_GT']
            for key in ['threshold', 'secondary_threshold', 'geometry', 'objective']:
                if config['evaluation'][key] != final[key]:
                    raise ValueError('Executable GT matching conflicts with the accepted first-cohort protocol')
            association = protocol['matching']['association']
            for source in [config['first_cohort']['draft_association'],
                           config['inference_dependencies']['prediction_only_association']]:
                if any(source[key] != association[key] for key in
                       ['threshold', 'objective', 'left_bbox_source', 'right_bbox_source', 'uses_GT']):
                    raise ValueError('Executable association conflicts with the accepted first-cohort protocol')
            if config['populations']['CCIHP_primary_candidate'] != protocol['population']['main'] or config['populations']['CCIHP_source_reference'] != protocol['population']['reference']:
                raise ValueError('Executable population roles conflict with the accepted first-cohort protocol')
        engineering = config['first_cohort']['engineering']
        if engineering['split'] != 'Training' or engineering['precision'] != 'FP32':
            raise ValueError('First-cohort engineering must remain TRAIN FP32')
        if not 0 < engineering['maximum_frames'] <= config['native_feasibility']['maximum_frames_per_variant']:
            raise ValueError('First-cohort engineering frame budget exceeded')
        if len(engineering['input_ids']) != engineering['maximum_frames'] or not set(engineering['input_ids']) <= set(config['bounded_train']['input_ids']):
            raise ValueError('First-cohort input manifest exceeds approved TRAIN scope')
        if engineering['full_benchmark'] or engineering['common_metrics_or_ranking'] or engineering['model_retries'] != 0:
            raise ValueError('First-cohort engineering cannot score/rank/retry or start benchmark')
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
    if config.get('first_cohort', {}).get('channel_order_evidence'):
        from .cohorts import read_channel_gate
        read_channel_gate(config, study)
    for key, path_key in [('mapping_sha256', 'mapping'), ('native_reference_sha256', 'native_reference'),
                          ('sidecars_manifest_sha256', 'sidecars_manifest')]:
        if key in config['cohort']:
            source = study / config['cohort'][path_key]
            if hashlib.sha256(source.read_bytes()).hexdigest() != config['cohort'][key]:
                raise ValueError('Cohort source changed without versioned config fingerprint')
    contexts = ([config['scoring_context']] if config.get('scoring_context') is not None else
                [context for frames in (config.get('scoring_contexts') or {}).values() for context in frames.values()])
    if contexts:
        if config.get('first_cohort', {}).get('channel_order_evidence', {}).get('required'):
            from .cohorts import require_config_channel_order
            for context in contexts:
                if not (context.get('require_verified_channel_order') or context.get('require_channel_order_evidence')):
                    raise ValueError('This cohort requires an accepted checkpoint channel-order evidence gate')
                declared = config['first_cohort']['channel_order_evidence'].get('accepted_statuses', ['DIRECT_VERIFIED'])
                if context.get('accepted_channel_evidence_statuses', ['DIRECT_VERIFIED']) != declared:
                    raise ValueError('Context confidence policy differs from executable channel evidence policy')
                require_config_channel_order(config, context['model_binding'], study_root=study)
        mapping = json.loads((study / config['cohort']['mapping']).read_text())
        if mapping.get('status') != 'ACCEPTED' or any(digest(mapping) != context['mapping_sha256'] for context in contexts):
            raise ValueError('Scoring context must bind the accepted executable cohort mapping')
        if config.get('scoring_contexts') is not None:
            from .scoring import check_context
            for context in contexts:
                check_context(context, mapping, context['model_binding'], context['input_binding'])
    if config.get('validation_context_packages'):
        accepted = [d for d in decisions['decisions'] if d['id'] == 'VALIDATION_PACKAGE_PREPARATION_BINDING'
                    and d['status'] == 'ACCEPTED_BY_USER']
        if not accepted or accepted[0]['bindings'].get('validation_context_packages') != config['validation_context_packages']:
            raise ValueError('Validation packages require an accepted preparation binding')
        from .validation_packages import validate_packages
        validate_packages(config, study)
    return config


def fingerprints(config, inference_inputs):
    """GT-derived oracle geometry belongs to inference dependencies, not scoring."""
    inference = {'inputs': inference_inputs, 'systems': config['systems'],
                 'routing': config['routing'], 'execution': config['execution'],
                 'bounded_train': config.get('bounded_train')}
    if config.get('inference_dependencies') is not None:
        inference['explicit_inference_dependencies'] = config['inference_dependencies']
    cohort = config.get('first_cohort', {})
    if cohort.get('execution_spec'):
        spec = copy.deepcopy(cohort['execution_spec'])
        spec.pop('semantic_scoring_enabled', None)
        inference['first_cohort_execution'] = dict(models=cohort['models'], track=cohort['track'], spec=spec,
            native_score_thresholds=cohort.get('protocol', {}).get('matching', {}).get('native_score_thresholds'))
    scoring = {'cohort': config['cohort'], 'evaluation': config['evaluation'],
               'populations': config['populations']}
    for name in ['scoring_context', 'scoring_contexts', 'scoring_population', 'evaluator_revision', 'failure_scoring_policy',
                 'primary_reporting_policy', 'cohort_policy', 'first_cohort']:
        if config.get(name) is not None:
            scoring[name] = config[name]
    return {'inference': digest(inference), 'scoring': digest(scoring)}
