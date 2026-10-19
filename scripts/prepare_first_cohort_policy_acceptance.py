"""Record policy acceptance separately from missing direct channel-order evidence."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import json
import sys
import yaml

S = Path(__file__).resolve().parents[1]
W = S.parent
sys.path.insert(0, str(S))
from src.application_v2.policy import digest, load_config
from src.application_v2.artifacts import file_hash


def main():
    run = S / json.loads((S / 'provenance/FIRST_COHORT_POLICY_ACCEPTANCE_ACTIVE.json').read_text())['run']
    prior = S / json.loads((S / 'provenance/FIRST_COHORT_T3B_SUBMISSION_ACTIVE.json').read_text())['run']
    cfg = load_config(S / 'configs/application_v2_first_cohort_v6.yaml')
    decision = json.loads((S / cfg['decision_record']).read_text())
    checkpoints = json.loads((prior / 'CHECKPOINT_BINDINGS.json').read_text())
    inventory = json.loads((S / 'provenance/CHECKPOINT_INVENTORY_CURRENT_V1.json').read_text())['files']
    frozen = json.loads((S / 'manifests/YOLO26X_SOURCE.json').read_text())
    evidence = dict(schema_version='1.0', status='INDIRECT_ONLY', semantic_binding_eligible=False,
        policy_acceptance_is_channel_verification=False, source_search=str((run / 'CHANNEL_HEADER_SEARCH.json').relative_to(S)),
        user_has_additional_header=False, models={})
    native_specs = {}
    for row in checkpoints:
        model = row['model_id']
        config_file = next(p for p in row['evidence_references'] if p.endswith('.py') and '/configs/' in p)
        checkpoint_path = next(p['path'] for p in inventory if p['sha256'] == row['checkpoint_sha256'] and not p.get('symlink'))
        evidence['models'][model] = dict(status='INDIRECT_ONLY', checkpoint_sha256=row['checkpoint_sha256'],
            source_commit=row['source_commit'], expected_native_class_order=row['native_class_order'],
            indirect_evidence=['Published CIHP checkpoint/config', '20-class strict checkpoint load',
                               'ID-preserving loader', 'Standard CIHP catalog from another implementation'],
            proof_kind=None, document=None, document_sha256=None, provenance_review='NOT_DIRECTLY_VERIFIED',
            release_relationship_evidence=None, semantic_binding_status='BLOCKED_CHANNEL_ORDER')
        native_specs[model] = dict(checkpoint_workspace_relative=checkpoint_path, checkpoint_sha256=row['checkpoint_sha256'],
            source_commit=row['source_commit'], native_config_workspace_relative=config_file,
            native_config_sha256=row['native_config_source_sha256'],
            resolved_config_evidence_sha256=row['resolved_config_sha256'],
            environment_workspace_relative='.venvs/parser-legacy-cu113', native_taxonomy='CIHP',
            score_threshold_source='first_cohort.protocol.matching.native_score_thresholds.' + model)
    evidence_path = run / 'CHANNEL_ORDER_EVIDENCE.json'
    if evidence_path.exists():
        raise FileExistsError(evidence_path)
    evidence_path.write_text(json.dumps(evidence, indent=2) + '\n')
    cohort = cfg['first_cohort']
    protocol = cohort.pop('protocol_proposal')
    protocol['mapping']['display_names'] = {'1': 'Face region'}
    domain = protocol['domain']
    domain.pop('category_positive_human0')
    domain.pop('policy_sha256')
    domain.update(category_positive_human0_global='KEEP_KNOWN_TARGET_ON_SHARED_GLOBAL_SEMANTIC_DOMAIN',
                  category_positive_human0_per_person='VOID_OWNER_UNKNOWN',
                  owner_unknown_scope_clarification_is_policy_change=False)
    domain['policy_sha256'] = digest(domain)
    cohort['protocol'] = protocol
    cohort.update(status='POLICIES_ACCEPTED_CHANNEL_ORDER_BLOCKED_NOT_FROZEN', population_role='ACCEPTED_POLICY',
        channel_order_evidence=dict(required=True, manifest=str(evidence_path.relative_to(S)),
            manifest_sha256=file_hash(evidence_path), required_status='DIRECT_VERIFIED',
            semantic_binding_without_gate='PROHIBITED', policy_acceptance_satisfies_gate=False),
        entrypoint=dict(mode='DRY_RUN_ONLY', script='scripts/first_cohort_entrypoint.py',
            roster_source='first_cohort.models', settings_source='first_cohort.execution_spec',
            legacy_engineering_is_active_roster=False, model_loading=False),
        execution_spec=dict(parser_systems=native_specs,
            dependencies={'YOLO26X_FROZEN': dict(checkpoint_workspace_relative=frozen['checkpoint_workspace_relative'],
                checkpoint_sha256=frozen['sha256'], environment_workspace_relative='.venv',
                settings_source='inference_dependencies.frozen_yolo_engineering_options')},
            precision='FP32', actual_inference_enabled=False),
        target_display_names={'1': 'Face region'})
    cfg['systems']['purpose'] = 'REFERENCE_CATALOG_NOT_FIRST_COHORT_ROSTER'
    cfg['cohort'].update(status='GT_POLICY_ACCEPTED_NATIVE_SEMANTIC_BINDING_BLOCKED',
                         target_display_names={'1': 'Face region'})
    cfg['populations']['roles_accepted'] = True
    cfg['status'] = 'POLICY_ACCEPTED_EVIDENCE_BLOCKED_NOT_FROZEN'
    cfg['pending_score_decisions'] = ['DIRECT_CPI_CHANNEL_ORDER_EVIDENCE', 'ACCEPTED_REAL_PARSER_CONTEXT_MATERIALIZATION']
    cfg['required_freeze_decisions'] = [key for key in cfg['required_freeze_decisions'] if key not in
                                      {'PRIMARY_POPULATION', 'COMMON_TAXONOMY', 'APPLICATION_MATCHING'}]
    accepted_ids = []
    for item in decision['decisions']:
        if item['id'].startswith('FIRST_COHORT_'):
            name = {'FIRST_COHORT_GT_DOMAIN': 'domain', 'FIRST_COHORT_RUNTIME_CLAIM': 'runtime'}.get(item['id'], item['id'].removeprefix('FIRST_COHORT_').lower())
            item.update(status='ACCEPTED_BY_USER',
                reason='User accepted the five policies after document/config review; owner-unknown scope and display name clarified',
                acceptance_scope='POLICY_ONLY_NOT_INDEPENDENT_SOURCE_TEST_OR_SEMANTIC_BINDING_CERTIFICATION',
                bindings={'first_cohort.protocol.' + name: copy.deepcopy(protocol[name])})
            accepted_ids.append(item['id'])
    cfg['required_freeze_decisions'] += accepted_ids
    decision['decisions'].append(dict(id='FIRST_COHORT_CHANNEL_GATE', status='ACCEPTED_BY_USER',
        reason='User explicitly requires direct official header/order evidence before VERIFIED semantic binding',
        bindings={'first_cohort.channel_order_evidence.required': True,
                  'first_cohort.channel_order_evidence.policy_acceptance_satisfies_gate': False,
                  'first_cohort.models': cohort['models'],
                  'first_cohort.track': 'T3B',
                  'first_cohort.entrypoint.mode': 'DRY_RUN_ONLY',
                  'first_cohort.entrypoint.model_loading': False,
                  'first_cohort.execution_spec.actual_inference_enabled': False,
                  'first_cohort.entrypoint.legacy_engineering_is_active_roster': False}))
    decision.update(record_id='FIRST_COHORT_POLICIES_ACCEPTED_EVIDENCE_SEPARATE_20261016_V6',
        supersedes='APPLICATION_V2_DECISIONS_V5',
        source='Explicit user acceptance of all five first-cohort policies, native thresholds and three bounded corrections; no freeze/full benchmark')
    cfg.update(decision_record='provenance/APPLICATION_V2_DECISIONS_V6.json', decision_record_id=decision['record_id'],
               decision_record_sha256=digest(decision))
    outputs = {S / cfg['decision_record']: json.dumps(decision, ensure_ascii=False, indent=2) + '\n',
               S / 'configs/application_v2_first_cohort_v7.yaml': yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False)}
    for path in outputs:
        if path.exists():
            raise FileExistsError(path)
    for path, text in outputs.items():
        path.write_text(text)
    load_config(S / 'configs/application_v2_first_cohort_v7.yaml')
    (run / 'POLICY_ACCEPTANCE.json').write_text(json.dumps(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
        accepted_policy_ids=accepted_ids, user_review_scope='DOCUMENT_AND_CONFIG_REVIEW_ONLY',
        source_tests_independently_certified_by_user=False, channel_order_status='INDIRECT_ONLY',
        model_contexts_created=False, semantic_binding_verified=False, full_benchmark_authorized=False,
        config='configs/application_v2_first_cohort_v7.yaml', decision_record=cfg['decision_record']), indent=2) + '\n')
    print('Five policies accepted; direct channel evidence remains blocked; full benchmark false')


if __name__ == '__main__':
    main()
