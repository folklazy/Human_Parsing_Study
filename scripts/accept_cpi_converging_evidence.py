"""Materialize user-accepted evidence revision and bounded TRAIN contexts, no scores."""
from pathlib import Path
import copy
import json
import sys
import yaml

S = Path(__file__).resolve().parents[1]
W = S.parent
sys.path.insert(0, str(S))
from src.application_v2.policy import load_config, digest
from src.application_v2.artifacts import file_hash


def create(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def reference(path):
    return dict(path=str(path.relative_to(S)), sha256=file_hash(path))


def main():
    run = S / json.loads((S / 'provenance/CPI_EVIDENCE_POLICY_ACCEPTANCE_ACTIVE.json').read_text())['run']
    review = json.loads((run / 'TRAIN_BEHAVIORAL_REVIEW.json').read_text())
    if review['status'] != 'COMPLETED' or review['blocking_mapping_contradiction_found']:
        raise ValueError('Resolve the bounded mapping review before acceptance')
    cfg = load_config(S / 'configs/application_v2_first_cohort_v7.yaml')
    decisions = json.loads((S / cfg['decision_record']).read_text())
    old_mapping = json.loads((S / cfg['cohort']['mapping']).read_text())
    old_gate = json.loads((S / cfg['first_cohort']['channel_order_evidence']['manifest']).read_text())
    paper = S / 'provenance/RUN_MANIFESTS/cpi-paper-taxonomy-reassessment-20261016T065136837053Z'
    trace = S / 'provenance/RUN_MANIFESTS/cpi-channel-order-source-investigation-20261016T043120768600Z/SOURCE_TRACE.json'
    policy_id = 'CPI_STANDARD_CIHP_CONVERGING_EVIDENCE_20261016_V1'
    components = {
        'PUBLISHED_PAPER_REPOSITORY_LINK': reference(paper / 'PUBLISHED_ABSTRACT_LINK.json'),
        'OFFICIAL_RELEASE_TABLE': reference(paper / 'PAPER_README_COMPARISON.json'),
        'CHECKPOINT_EMBEDDED_CONFIG': reference(paper / 'EMBEDDED_CONFIG_EVIDENCE.json'),
        'NUMERIC_PROCESSING_SOURCE_TRACE': reference(trace),
        'SAVED_TRAIN_BEHAVIORAL_REVIEW': reference(run / 'TRAIN_BEHAVIORAL_REVIEW.json'),
    }
    gate = dict(schema_version='2.0', status='ACCEPTED_WITH_INDIRECT_EVIDENCE',
        semantic_binding_eligible=True, policy_decision_id=policy_id,
        original_training_header_verified=False, creator_confirmation_received=False,
        all_classes_correct_required=False, models={})
    for model, row in old_gate['models'].items():
        gate['models'][model] = dict(status=gate['status'], checkpoint_sha256=row['checkpoint_sha256'],
            source_commit=row['source_commit'], expected_native_class_order=row['expected_native_class_order'],
            proof_kind='CONVERGING_PAPER_RELEASE_CONFIG_SOURCE_AND_TRAIN_REVIEW',
            provenance_review='ACCEPTED_WITH_INDIRECT_EVIDENCE', policy_decision_id=policy_id,
            original_training_header_verified=False, components=copy.deepcopy(components),
            limitations=['Standard CIHP order inferred from converging release evidence, not direct annotation header',
                         'Visual sanity is not all-class accuracy certification'])
    create(run / 'CHANNEL_ORDER_EVIDENCE_V2.json', gate)
    mapping = copy.deepcopy(old_mapping)
    mapping.update(status='ACCEPTED', semantics_accepted=True, benchmark_eligible=False,
        purpose='Accepted fixed six-target projection for the two CPI CIHP checkpoints; not native CIHP equivalence',
        acceptance_scope=dict(models=cfg['first_cohort']['models'], native_taxonomies=['CIHP'],
                              native_channel_evidence='ACCEPTED_WITH_INDIRECT_EVIDENCE',
                              LIP_projection='RETAINED_DRAFT_OUTSIDE_ACCEPTED_COHORT'),
        evidence_policy_decision=policy_id)
    mapping_path = S / 'taxonomy/APPLICATION_BODY_CLOTHING_CPI_ACCEPTED_V3.json'
    create(mapping_path, mapping)
    # Metadata changes must not alter the accepted task or source projections.
    for key in ['target_catalog', 'gt_mapping', 'prediction_mappings', 'unsupported_targets']:
        if mapping[key] != old_mapping[key]:
            raise ValueError('Numeric/semantic projection changed during evidence acceptance')
    cfg['cohort'].update(mapping=str(mapping_path.relative_to(S)), mapping_sha256=file_hash(mapping_path),
                         status='ACCEPTED_CPI_ONLY_WITH_INDIRECT_CHANNEL_EVIDENCE')
    cohort = cfg['first_cohort']
    cohort['protocol']['mapping'].update(mapping=str(mapping_path.relative_to(S)), mapping_file_sha256=file_hash(mapping_path))
    cohort.update(status='MAPPING_ACCEPTED_TRAIN_CONTEXTS_ONLY_NOT_FROZEN', scoring_context_accepted=True,
        scoring_context_scope='PREDECLARED_TRAIN_ONLY_NOT_MAIN_OR_REFERENCE_VALIDATION',
        channel_order_evidence=dict(required=True, manifest=str((run / 'CHANNEL_ORDER_EVIDENCE_V2.json').relative_to(S)),
            manifest_sha256=file_hash(run / 'CHANNEL_ORDER_EVIDENCE_V2.json'),
            accepted_statuses=['DIRECT_VERIFIED', 'ACCEPTED_WITH_INDIRECT_EVIDENCE'],
            semantic_binding_without_gate='PROHIBITED', policy_acceptance_satisfies_gate=False,
            evidence_policy_decision_id=policy_id))
    cohort['entrypoint']['mode'] = 'DRY_RUN_AND_SAVED_TRAIN_REPLAY'
    cohort['execution_spec'].update(actual_inference_enabled=False, semantic_scoring_enabled=False)
    cohort['engineering'].update(input_ids=copy.deepcopy(cfg['bounded_train']['input_ids']), maximum_frames=3)
    cfg['status'] = 'MAPPING_ACCEPTED_WITH_LIMITATIONS_TRAIN_PREPARATION_NOT_FROZEN'
    cfg['pending_score_decisions'] = ['ACCEPTED_FULL_VALIDATION_CONTEXT_MATERIALIZATION', 'ACTUAL_EXECUTE_READINESS_REVIEW']
    cfg['scoring_capabilities']['live_scoring'] = 'DISABLED_PREPARATION_ONLY'
    cfg['authorization']['full_benchmark'] = False
    pilot = W / 'Human_Parsing_CCIHP_10_Image_Pilot'
    samples = {x['image_id']: x for x in json.loads((pilot / 'configs/TEN_IMAGE_MANIFEST.json').read_text())['images']}
    gt_manifest = S / 'provenance/RUN_MANIFESTS/first-cohort-policy-acceptance-20261016T034543760531Z/GT_TRAIN_RECONSTRUCTION/MANIFEST.json'
    gt = {x['image_id']: x for x in json.loads(gt_manifest.read_text())['images']}
    visual = json.loads((run / 'saved_train_review_v2/MANIFEST.json').read_text())
    visual = {x['image_id']: x for x in visual['images']}
    yolo = S / 'provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/bounded_train_20261014T094329862740Z/YOLO.json'
    context_registry = {}
    frames = []
    for iid in cohort['engineering']['input_ids']:
        sample = samples[iid]
        if sample['split'] != 'Training' or file_hash(pilot / sample['input']) != sample['input_sha256']:
            raise ValueError('Verified TRAIN input required')
        g = gt[iid]
        if file_hash(S / g['artifact']) != g['artifact_sha256']:
            raise ValueError('Previously verified GT cache changed')
        frames.append(dict(image_id=iid, G_loc=g['G_loc'], G_sem=g['G_sem']))
        for model in cohort['models']:
            spec = cohort['execution_spec']['parser_systems'][model]
            binding = dict(checkpoint_sha256=spec['checkpoint_sha256'], config_sha256=spec['native_config_sha256'],
                source_commit=spec['source_commit'], native_class_order=gate['models'][model]['expected_native_class_order'],
                native_taxonomy='CIHP', head_classes=20)
            support = dict(status='VERIFIED', verification_scope='HASH_BINDINGS_AND_ACCEPTED_TARGET_SUPPORT',
                **{k: binding[k] for k in ['checkpoint_sha256', 'config_sha256', 'source_commit']},
                native_class_order_sha256=digest(binding['native_class_order']), mapping_sha256=digest(mapping),
                target_catalog_sha256=digest(mapping['target_catalog']),
                evidence_references=[str((run / 'CHANNEL_ORDER_EVIDENCE_V2.json').relative_to(S))],
                semantic_review='ACCEPTED_WITH_INDIRECT_EVIDENCE', supported_target_ids=[1, 2, 3, 4, 5, 6],
                channel_order_evidence=copy.deepcopy(gate['models'][model]))
            context = dict(status='ACCEPTED', scope='BOUNDED_TRAIN_PREPARATION_NO_MODEL_SCORING',
                mapping_sha256=digest(mapping), model_binding=binding,
                input_binding=dict(status='VERIFIED', image_id=iid, input_sha256=sample['input_sha256'],
                    RGB_source_sha256=sample['rgb_source_sha256'], original_wh=sample['wh'], dataset='CCIHP', split='Training'),
                domain=dict(status='ACCEPTED', evidence='RELEASED_ANNOTATION_RELATIVE_POLICY_AND_PRIOR_HASH_BOUND_GT_CACHE',
                    policy_sha256=cohort['protocol']['domain']['policy_sha256'], image_binding=copy.deepcopy(g['image_binding'])),
                target_support_policy='COMMON_CAPABILITY', failure_policy='STRICT_COMPLETE',
                evaluation_bbox_source='NATIVE_PARSER_BOX', threshold=cfg['evaluation']['threshold'],
                require_checkpoint_specific_support=True, require_channel_order_evidence=True,
                accepted_channel_evidence_statuses=cohort['channel_order_evidence']['accepted_statuses'], support_binding=support)
            context_registry.setdefault(model, {})[iid] = context
    replay = dict(schema_version='1.0', split='Training', input_ids=cohort['engineering']['input_ids'],
        maximum_frames=3, scoring_enabled=False, new_inference=False,
        yolo=dict(path_workspace_relative=str(yolo.relative_to(W)), sha256=file_hash(yolo)),
        images=[dict(image_id=iid, input=samples[iid], GT_cache=gt[iid],
                     parsers=visual[iid]['native_predictions']) for iid in cohort['engineering']['input_ids']])
    create(run / 'SAVED_TRAIN_REPLAY_INPUTS.json', replay)
    cohort['entrypoint']['replay_manifest'] = reference(run / 'SAVED_TRAIN_REPLAY_INPUTS.json')
    cfg['scoring_contexts'] = context_registry
    cfg['scoring_population'] = frames
    cfg['scoring_context'] = None
    create(run / 'TRAIN_CONTEXTS.json', context_registry)
    for row in decisions['decisions']:
        if row['id'] == 'FIRST_COHORT_MAPPING':
            row['bindings'] = {'first_cohort.protocol.mapping': copy.deepcopy(cohort['protocol']['mapping'])}
            row['reason'] += '; metadata-only mapping reference revision, all numeric projections unchanged'
        if row['id'] == 'FIRST_COHORT_CHANNEL_GATE':
            row.update(reason='User accepts converging paper/release/config/numeric-source and bounded TRAIN behavioral evidence without DIRECT_VERIFIED or all-classes-correct requirement',
                supersedes='Direct-header-only requirement in decision V6; V6 remains immutable',
                bindings={'first_cohort.channel_order_evidence': copy.deepcopy(cohort['channel_order_evidence']),
                    'first_cohort.entrypoint': copy.deepcopy(cohort['entrypoint']),
                    'first_cohort.models': copy.deepcopy(cohort['models']), 'first_cohort.track': cohort['track'],
                    'first_cohort.execution_spec.actual_inference_enabled': False,
                    'first_cohort.execution_spec.semantic_scoring_enabled': False})
    decisions['decisions'].append(dict(id='SCORING_CONTEXTS', status='ACCEPTED_BY_USER',
        reason='Materialization of the accepted mapping/domain policies for three predeclared TRAIN inputs only; no semantic scores, no validation benchmark',
        bindings={'scoring_contexts': copy.deepcopy(context_registry), 'scoring_population': copy.deepcopy(frames)}))
    decisions['decisions'].append(dict(id=policy_id, status='ACCEPTED_BY_USER',
        reason='Latest user instruction explicitly accepts standard CIHP mapping from converging evidence and a bounded saved TRAIN sanity review',
        bindings={'cohort.mapping': cfg['cohort']['mapping'], 'cohort.mapping_sha256': cfg['cohort']['mapping_sha256']}))
    decisions.update(record_id='FIRST_COHORT_CONVERGING_EVIDENCE_ACCEPTED_20261016_V7',
                     prior_record='provenance/APPLICATION_V2_DECISIONS_V6.json')
    decision_path = S / 'provenance/APPLICATION_V2_DECISIONS_V7.json'
    create(decision_path, decisions)
    cfg.update(decision_record=str(decision_path.relative_to(S)), decision_record_id=decisions['record_id'],
               decision_record_sha256=digest(decisions))
    path = S / 'configs/application_v2_first_cohort_v8.yaml'
    with path.open('x') as stream:
        yaml.safe_dump(cfg, stream, sort_keys=False, allow_unicode=True)
    load_config(path)
    create(run / 'ACCEPTANCE.json', dict(status='ACCEPTED_WITH_INDIRECT_EVIDENCE_NOT_DIRECT_VERIFIED',
        config=reference(path), decision=reference(decision_path), mapping=reference(mapping_path),
        TRAIN_images=3, TRAIN_contexts=6, GT_reconstruction_reused=True,
        full_validation_contexts_materialized=False, full_benchmark=False, new_inference=False))
    print(json.dumps(dict(status='ACCEPTED_WITH_INDIRECT_EVIDENCE', TRAIN_contexts=6, full_benchmark=False)))


if __name__ == '__main__':
    main()
