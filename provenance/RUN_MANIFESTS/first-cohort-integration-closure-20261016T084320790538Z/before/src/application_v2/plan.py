"""First-cohort entry-point selection: configuration only, no model imports."""
from pathlib import Path
import hashlib
from .policy import field
from .cohorts import read_channel_gate


def first_cohort_plan(config, study_root):
    study = Path(study_root).resolve()
    workspace = study.parent
    cohort = config['first_cohort']
    entry = cohort['entrypoint']
    if entry['mode'] not in {'DRY_RUN_ONLY', 'DRY_RUN_AND_SAVED_TRAIN_REPLAY'} or entry['model_loading'] or cohort['execution_spec']['actual_inference_enabled']:
        raise ValueError('This entry point supports preparation/saved TRAIN replay only; model execution is disabled')
    if entry['roster_source'] != 'first_cohort.models' or entry['settings_source'] != 'first_cohort.execution_spec':
        raise ValueError('Explicit first-cohort configuration sources required')
    models = field(config, entry['roster_source'])
    spec = field(config, entry['settings_source'])
    if not models or len(models) != len(set(models)) or set(spec['parser_systems']) != set(models):
        raise ValueError('Execution settings must cover the exact first-cohort roster')
    gate = read_channel_gate(config, study)
    parsers = []
    for model in models:
        source = spec['parser_systems'][model]
        checkpoint = workspace / source['checkpoint_workspace_relative']
        native_config = workspace / source['native_config_workspace_relative']
        if not checkpoint.is_file() or not native_config.is_file():
            raise ValueError('Declared parser checkpoint/config is missing')
        if hashlib.sha256(native_config.read_bytes()).hexdigest() != source['native_config_sha256']:
            raise ValueError('Native parser configuration changed')
        threshold = field(config, source['score_threshold_source'])
        parsers.append(dict(system_id=model, **source, native_score_threshold=threshold,
                            checkpoint_hash_source='PRIOR_VERIFIED_INVENTORY_NOT_REHASHED_BY_DRY_RUN',
                            channel_order_status=gate['models'][model]['status']))
    dependencies = []
    for name, source in spec['dependencies'].items():
        if not (workspace / source['checkpoint_workspace_relative']).is_file():
            raise ValueError('Frozen detector dependency is missing')
        dependencies.append(dict(dependency_id=name, **source, settings=field(config, source['settings_source'])))
    return dict(status='DRY_RUN_PLAN_ONLY', roster_source=entry['roster_source'], settings_source=entry['settings_source'],
        track=cohort['track'], parser_systems=parsers, shared_dependencies=dependencies,
        association=cohort['protocol']['matching']['association'],
        GT_matching=cohort['protocol']['matching']['final_prediction_to_GT'],
        evaluator_runtime=config['evaluation'],
        precision=spec['precision'], model_loading=False, full_benchmark=False,
        semantic_scoring=('BLOCKED_CHANNEL_ORDER' if gate['status'] not in cohort['channel_order_evidence'].get('accepted_statuses', ['DIRECT_VERIFIED'])
                          else 'DISABLED_PREPARATION_ONLY' if spec.get('semantic_scoring_enabled') is False
                          else 'REQUIRES_ACCEPTED_CONTEXTS'),
        ignored_legacy_fields={'systems.variants': config['systems']['variants'],
            'bounded_train.models': config['bounded_train']['models'],
            'execution.model_loading': config['execution']['model_loading']},
        legacy_engineering_used_for_roster=False)
