"""Prepare one review submission from pinned evidence. No dataset decoding/inference."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import copy
import csv
import io
import json
import sys
import yaml

S = Path(__file__).resolve().parents[1]
W = S.parent
sys.path.insert(0, str(S))
from src.application_v2.policy import digest, load_config
from src.application_v2.artifacts import file_hash


def main():
    run = S / json.loads((S / 'provenance/FIRST_COHORT_T3B_SUBMISSION_ACTIVE.json').read_text())['run']
    old = S / json.loads((S / 'provenance/FIRST_COHORT_READINESS_ACTIVE.json').read_text())['run']
    cfg = load_config(S / 'configs/application_v2_first_cohort_v5.yaml')
    mapping = json.loads((S / cfg['cohort']['mapping']).read_text())
    pops = json.loads((old / 'POPULATION_BINDINGS_DRAFT.json').read_text())
    checkpoints = json.loads((old / 'CHECKPOINT_SUPPORT_BINDINGS_DRAFT.json').read_text())
    structure_path = S / 'provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/FULL_STRUCTURAL_AUDIT.json'
    structure = json.loads(structure_path.read_text())
    source_names = S / 'provenance/RUN_MANIFESTS/stage0e-ccihp-native-20261012T045912Z/archive_documents/README.md'
    cihp_names = W / 'third_party/human_parsing/M2FP/m2fp/data/datasets/register_cihp_parsing.py'
    native = next(ast.literal_eval(node.value) for node in ast.parse(cihp_names.read_text()).body
                  if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CIHP_PARSING_CATEGORIES' for t in node.targets))
    native = {row['id']: row['name'] for row in native if row['id'] < 20}
    with (old / 'CLASS_MAPPING_EVIDENCE_DRAFT.csv').open() as f:
        previous_rows = list(csv.DictReader(f))
    gt_names = {int(row['GT_native_id']): row['GT_declared_name'] for row in previous_rows}
    for row in checkpoints:
        assert row['native_class_order'] == [native[i] for i in range(20)]
    # Verify identity of the manifests already counted; do not recount membership.
    for population in pops['populations'].values():
        assert file_hash(S / population['expected_frame_manifest']) == population['expected_frame_manifest_sha256']
        assert file_hash(S / population['original_person_sidecar']) == population['original_person_sidecar_sha256']
    projection_sha = digest({k: mapping[k] for k in ['target_catalog', 'gt_mapping']})
    assert projection_sha == pops['GT_projection_content_sha256']
    catalog_sha = digest(mapping['target_catalog'])
    native_projection_sha = digest(mapping['prediction_mappings']['CIHP'])
    rows = []
    names_path = str(cihp_names.relative_to(W))
    readme_path = str(source_names.relative_to(S))
    for checkpoint in checkpoints:
        for label in range(20):
            rule = mapping['prediction_mappings']['CIHP'][str(label)]
            notes = {
                0: 'Reference background; no claim that all real people are exhaustively annotated',
                6: 'CIHP Dress -> selected garments; CCIHP GT6 is Face Mask and is VOID, never identity-mapped',
                8: 'Socks included in selected garment union by study design, not exposed leg or footwear',
                11: 'Scarf included in selected garment union; CCIHP also includes ties/bow ties',
                13: 'Declared Face region; no claim of pixel-identical skin/eyewear/face-covering conventions',
                14: 'Merge left/right exposed arm labels; no separate hand metric',
                15: 'Merge left/right exposed arm labels; no separate hand metric',
                16: 'Merge left/right exposed leg labels; socks remain garment',
                17: 'Merge left/right exposed leg labels; socks remain garment',
            }
            rows.append(dict(source_kind='PREDICTION', model_id=checkpoint['model_id'],
                checkpoint_sha256=checkpoint['checkpoint_sha256'], source_id=label, source_class=native[label],
                disposition=rule['disposition'], target_id=rule.get('target_id', ''),
                target= mapping['target_catalog'][str(rule['target_id'])] if 'target_id' in rule else 'OUTSIDE_FIXED_TASK',
                evidence=f'{names_path}; CPI config20/head strict-load + unchanged PNG-ID loader; CHECKPOINT_BINDINGS.json',
                evidence_status='SOURCE_CATALOG_AND_CHECKPOINT_BINDING_DOCUMENTED',
                limitation=notes.get(label, 'Concept-level projection; pixel-level convention equivalence is not claimed'),
                missing_evidence='No CPI training JSON channel-name header locally; standard CIHP order supported indirectly by published variant/config/loader',
                acceptance='PROPOSED_FIXED_TASK_NOT_USER_ACCEPTED'))
    for label in range(23):
        rule = mapping['gt_mapping'][str(label)]
        note = ('Category0/Human0=annotation-relative BG; Category0/Human>0=VOID_UNKNOWN'
                if label == 0 else 'UNRESOLVED source meaning; VOID for every system, raw bytes retained'
                if label == 22 else 'Face Mask lacks a CIHP counterpart; shared VOID, not Dress'
                if label == 6 else 'Documented source concept excluded from this fixed body/clothing/footwear view'
                if rule['disposition'] == 'VOID' else 'Source-declared concept projected to the fixed coarse target')
        rows.append(dict(source_kind='GT', model_id='SHARED_CCIHP_REFERENCE', checkpoint_sha256='', source_id=label,
            source_class=gt_names[label], disposition=rule['disposition'], target_id=rule.get('target_id', ''),
            target=mapping['target_catalog'][str(rule['target_id'])] if 'target_id' in rule else 'VOID_SHARED',
            evidence=readme_path + '; FULL_STRUCTURAL_AUDIT.json',
            evidence_status='UNKNOWN_SOURCE_LABEL' if label == 22 else 'SOURCE_DEFINITION_DOCUMENTED',
            limitation=note, missing_evidence='Author meaning of ID22 remains unknown; not needed to invent a target' if label == 22 else '',
            acceptance='PROPOSED_FIXED_TASK_NOT_USER_ACCEPTED'))
    csv_path = S / 'taxonomy/FIRST_COHORT_CPI_SOURCE_TO_TARGET_V1.csv'
    stream = io.StringIO(); writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    csv_text = stream.getvalue()
    import hashlib
    csv_sha = hashlib.sha256(csv_text.encode()).hexdigest()
    main = pops['populations']['overlap_controlled_source_target']
    ref = pops['populations']['original_source_target']
    proposals = {
        'mapping': dict(mapping=cfg['cohort']['mapping'], mapping_file_sha256=cfg['cohort']['mapping_sha256'],
            target_catalog=mapping['target_catalog'], target_catalog_sha256=catalog_sha,
            GT_projection_sha256=projection_sha, per_checkpoint_native_projections={row['model_id']: native_projection_sha for row in checkpoints},
            evidence_table=str(csv_path.relative_to(S)), evidence_table_sha256=csv_sha,
            groups=mapping['analysis_groups'], excluded_GT_ids=[1, 2, 3, 4, 6, 20, 21, 22],
            policy='FIXED_COMMON_TARGET_WITH_CHECKPOINT_SPECIFIC_NATIVE_PROJECTIONS',
            fine_clothing_or_accessory_quality_claim=False, native_CIHP_equivalence_claim=False),
        'domain': dict(policy_id='CCIHP_RELEASED_ANNOTATION_RELATIVE_CORE_R1',
            reference='RELEASED_CCIHP_CATEGORY_AND_HUMAN_IDS_NOT_EXHAUSTIVE_PHYSICAL_TRUTH',
            category0_human0='KNOWN_NEGATIVE_RELATIVE_TO_RELEASED_ANNOTATION',
            category0_human_positive='VOID_UNKNOWN', unknown22='VOID_SHARED_RAW_PRESERVED',
            known_outside_target='VOID_SHARED', category_positive_human0='VOID_OWNER_UNKNOWN',
            other_known_person_pixels='NEGATIVE_FOR_TARGET_PERSON_WHERE_SHARED_VALID',
            association_uses_GT=False, categorical_resampling='NONE_GT_ORIGINAL_GRID',
            FP_wording='UNMATCHED_PREDICTION_RELATIVE_TO_RELEASED_ANNOTATION_UNDER_THIS_POLICY',
            person_mask='NATIVE_HUMAN_ID_FOREGROUND_ALL_SOURCE_SEMANTICS',
            G_loc='EVERY_POSITIVE_NATIVE_HUMAN_ID_WITH_NONEMPTY_RELEASED_MASK',
            G_sem='G_LOC_SUBSET_WITH_AT_LEAST_ONE_VALID_TARGET_1_TO_6_PIXEL',
            person_semantic_truth='TARGET_LABEL_INSIDE_THIS_HUMAN_ID_ELSE_BG_ON_SHARED_VALID_DOMAIN',
            per_image_GT_domain_binding='SOURCE_MAP_HASHES_PLUS_GT_PROJECTION_DOMAIN_POLICY_AND_G_LOC_G_SEM',
            recipe_hash_is_decoded_mask_hash=False),
        'population': dict(main='overlap_controlled_source_target', reference='original_source_target',
            main_images=main['frames'], main_G_loc=main['G_loc_structural_draft'], main_G_sem=main['G_sem_candidate_draft'],
            reference_images=ref['frames'], reference_G_loc=ref['G_loc_structural_draft'], reference_G_sem=ref['G_sem_candidate_draft'],
            main_manifest=main['expected_frame_manifest'], main_manifest_sha256=main['expected_frame_manifest_sha256'],
            reference_manifest=ref['expected_frame_manifest'], reference_manifest_sha256=ref['expected_frame_manifest_sha256'],
            main_person_sidecar=main['original_person_sidecar'], main_person_sidecar_sha256=main['original_person_sidecar_sha256'],
            reference_person_sidecar=ref['original_person_sidecar'], reference_person_sidecar_sha256=ref['original_person_sidecar_sha256'],
            exclusions='39_VALIDATION_IDS_WITH_EXACT_DECODED_TRAIN_RGB_REUSE_ONLY',
            within_validation_duplicates='RETAIN_SOURCE_MEMBERSHIP_2_IDS_1_GROUP_DISCLOSED',
            near_duplicates='114_PAIRS_RISK_SCREEN_ONLY_NO_NEW_EXCLUSIONS',
            exposure_claim='NOT_TRAINING_EXPOSURE_FREE_OR_ARCHITECTURE_CONTROLLED'),
        'matching': dict(association=copy.deepcopy(cfg['first_cohort']['draft_association']),
            final_prediction_to_GT=dict(threshold=.5, secondary_threshold=.75, geometry='BBOX_XYXY_HALF_OPEN',
                objective='ELIGIBLE_CARDINALITY_THEN_IOU', tie_policy='SORT_IMMUTABLE_IDS_THEN_PINNED_SCIPY_1_15_3',
                evaluation_bbox_source='NATIVE_PARSER_BOX', GT_bbox_source='ORIGINAL_HUMAN_ID_HALF_OPEN_BBOX',
                conditioning_bbox_source='FROZEN_YOLO26X_BOX', class_guided_rematching=False),
            native_unassociated='NOT_FINAL_T3B_OUTPUT_REPORT_NATIVE_ASSOCIATION_DIAGNOSTIC',
            unmatched_YOLO='NO_FINAL_PERSON_RETAIN_OPPORTUNITY_DIAGNOSTIC',
            final_unmatched_GT='LOC_FN_AND_ZERO_QUALITY_IF_G_SEM',
            final_unmatched_prediction='ANNOTATION_RELATIVE_FP',
            semantic_undefined_GT='RETAIN_G_LOC_NEVER_FORCE_SEMANTIC_ZERO_UNION_SCORE',
            zero_YOLO='RUN_NATIVE_AS_CONFIGURED_FINAL_EMPTY_EXECUTION_COMPLETE_IF_NO_FAILURE',
            confidence_policy='KEEP_OFFICIAL_CHECKPOINT_SPECIFIC_NATIVE_DEFAULTS_NO_QUALITY_TUNING',
            native_score_thresholds={'CPI_R50_CIHP': .01, 'CPI_ConvNeXtB_CIHP': .05},
            visualization_threshold_is_metric_filter=False),
        'runtime': dict(claim_scope='QUALITY_ONLY_FIRST_COMPARISON', primary_precision='FP32',
            compare_latency=False, compare_FPS=False, compare_VRAM=False, cost_Pareto=False,
            smoke_profiles='FEASIBILITY_ONLY_NOT_REPEATED_COST_MEASUREMENTS',
            cost_extension='SEPARATE_ACCEPTED_WORKLOAD_RESIDENCY_WARMUPS_SYNCHRONIZATION_CLEAN_REPEATS_REQUIRED'),
    }
    proposals['mapping']['definitions'] = {
        '1': 'Source-declared Face region; not a claim of an independent skin detector',
        '2': 'Torso-skin', '3': 'Union of left/right naked arm regions; hands only if included by source labels',
        '4': 'Union of left/right naked leg regions',
        '5': 'Selected garments: GT5,7,8,9,11,12; CIHP5,6,7,8,9,11,12. Socks/scarf included; headwear/gloves excluded',
        '6': 'Union of left/right shoe labels; no independent bare-foot target',
    }
    proposals['domain']['policy_sha256'] = digest(proposals['domain'])
    # Bind full per-image reference by source recipe, not by a claimed decoded-mask hash.
    first = json.loads((S / main['expected_frame_manifest']).open().readline())
    recipe = dict(image_id=first['image_id'], source_maps=first['source_maps'], original_wh=first['original_wh'],
                  GT_projection_sha256=projection_sha, domain_policy_sha256=proposals['domain']['policy_sha256'])
    example_binding = dict(image_id=first['image_id'], G_loc=first['G_loc'], G_sem=first['G_sem'], GT_domain_recipe_sha256=digest(recipe))
    binding_manifest = dict(status='PROPOSED_REFERENCE_RECIPE_NOT_ACCEPTED_SCORING_CONTEXT',
        common_target_catalog_sha256=catalog_sha, common_GT_projection_sha256=projection_sha,
        common_domain_policy=proposals['domain'], populations=proposals['population'],
        per_image_derivation='Select exact row by image_id from bound manifest; hash source_maps/original_wh/GT_projection_sha256/domain_policy_sha256',
        first_row_example=example_binding, example_recipe=recipe, GT_pixels_redecoded=False, membership_recounted=False,
        native_mapping_may_differ_by_checkpoint=True, domain_and_GT_counts_may_differ_by_image=True,
        same_image_binding_must_equal_across_systems=True)
    bindings = copy.deepcopy(checkpoints)
    for row in bindings:
        row['native_projection_sha256'] = native_projection_sha
        row['target_catalog_sha256'] = catalog_sha
        row['GT_projection_sha256'] = projection_sha
        row['semantic_mapping_review'] = 'EVIDENCE_ASSEMBLED_PROJECTION_PROPOSED_FOR_ACCEPTANCE'
        row['source_channel_order_limit'] = 'CPI dataset reads names from absent training JSON; published CIHP20 variant plus unchanged-ID loader and standard CIHP catalog support order indirectly'
    cfg['first_cohort'].update(status='PROPOSAL_READY_FOR_REVIEW_NOT_FROZEN',
        comparison_id='CCIHP_CORE_CPI_T3B_QUALITY_RELEASED_GT_PROPOSED_R2',
        require_per_image_GT_domain_binding=True, protocol_proposal=proposals,
        runtime_claim='QUALITY_ONLY_NO_LATENCY_FPS_VRAM_COMPARISON')
    cfg['pending_score_decisions'] = ['FIRST_COHORT_MAPPING', 'FIRST_COHORT_GT_DOMAIN', 'FIRST_COHORT_POPULATION',
        'FIRST_COHORT_MATCHING', 'FIRST_COHORT_RUNTIME_CLAIM', 'ACCEPTED_REAL_CONTEXT_MATERIALIZATION']
    cfg['status'] = 'PROPOSED_FOR_POLICY_REVIEW'
    decision = json.loads((S / cfg['decision_record']).read_text())
    decision.update(record_id='FIRST_COHORT_T3B_POLICY_SUBMISSION_20261016_V5',
                    supersedes='APPLICATION_V2_DECISIONS_V4',
                    source='User requested concrete first-cohort proposals; no new protocol acceptance or full benchmark authorization')
    # Existing accepted decisions are preserved; new bindings are proposals only.
    for name in proposals:
        decision['decisions'].append(dict(id='FIRST_COHORT_' + ('GT_DOMAIN' if name == 'domain' else 'RUNTIME_CLAIM' if name == 'runtime' else name.upper()),
            status='PROPOSED', reason='Concrete evidence-backed first-cohort value awaiting user policy review',
            bindings={'first_cohort.protocol_proposal.' + name: proposals[name]}))
    cfg.update(decision_record='provenance/APPLICATION_V2_DECISIONS_V5.json', decision_record_id=decision['record_id'], decision_record_sha256=digest(decision))
    scope = dict(status='TARGETED_SOURCE_REVIEW', mapping_hash='COMMON_BUNDLE_HASH_NOT_EQUAL_NATIVE_PROJECTION_HASH',
        CIHP_ID10=mapping['prediction_mappings']['CIHP']['10'], LIP_ID10=mapping['prediction_mappings']['LIP']['10'],
        distinct_native_rules_in_shared_bundle=True, arbitrary_per_checkpoint_mapping_files='NOT_IMPLEMENTED_NOT_NEEDED_FOR_THIS_CIHP_PAIR',
        domain_policy_common=True, domain_mask_equality_across_images_required=False,
        same_image_GT_domain_binding_now_checked=True, counts_per_image_may_differ=True,
        code_sha256=file_hash(S / 'src/application_v2/contexts.py'), scope='NO_ROSTER_EXPANSION')
    sources = {str(path.relative_to(S)) if path.is_relative_to(S) else '../' + str(path.relative_to(W)): file_hash(path)
        for path in [source_names, cihp_names, structure_path, old / 'POPULATION_BINDINGS_DRAFT.json',
                     old / 'CHECKPOINT_SUPPORT_BINDINGS_DRAFT.json', old / 'live_route/ROUTE_EVIDENCE.json',
                     W / 'third_party/human_parsing/CPI-Parser/mmdet/datasets/pipelines/loading.py',
                     W / 'third_party/human_parsing/CPI-Parser/mmdet/datasets/cihp.py',
                     W / 'third_party/human_parsing/CPI-Parser/utils/eval.py']}
    submission = dict(status='READY_FOR_POLICY_REVIEW_NOT_BENCHMARK_AUTHORIZATION', created_utc=datetime.now(timezone.utc).isoformat(),
        config='configs/application_v2_first_cohort_v6.yaml', decision_record=cfg['decision_record'],
        systems=cfg['first_cohort']['models'], track='T3B', proposals=proposals,
        source_manifest=sources, no_new_population_counts=True, no_new_model_inference=True,
        source_label22_meaning='UNRESOLVED_SHARED_VOID', published_training_channel_order='INDIRECT_EVIDENCE_EXPLICIT_LIMITATION',
        unresolved_points=['User approval of the five concrete policy proposals',
            'Before scoring: materialize accepted checkpoint/image contexts and validate actual GT reconstruction against bound sources',
            'Full benchmark execution requires separate future approval'],
        benchmark_authorized=False, scientific_freeze=False)
    aggregate = structure['aggregate']['Validation']
    submission['reused_validation_warning_counts'] = aggregate['counts']
    outputs = {
        csv_path: csv_text,
        S / 'configs/application_v2_first_cohort_v6.yaml': yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True),
        S / cfg['decision_record']: json.dumps(decision, indent=2, ensure_ascii=False) + '\n',
        run / 'SUBMISSION.json': json.dumps(submission, indent=2, ensure_ascii=False) + '\n',
        run / 'CHECKPOINT_BINDINGS.json': json.dumps(bindings, indent=2) + '\n',
        run / 'PER_IMAGE_BINDING_RECIPE.json': json.dumps(binding_manifest, indent=2) + '\n',
        run / 'CONTEXT_SCOPE_AUDIT.json': json.dumps(scope, indent=2) + '\n',
    }
    for path in outputs:
        if path.exists():
            raise FileExistsError('Preserve prior evidence; choose a new revision: ' + str(path))
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
    loaded = load_config(S / submission['config'])
    assert loaded['authorization']['full_benchmark'] is False and loaded.get('scoring_contexts') is None
    assert len(loaded['first_cohort']['models']) == 2
    print(json.dumps({'status': submission['status'], 'mapping_rows': len(rows), 'config': submission['config'],
                      'population_recounted': False, 'GPU_inference': False}))


if __name__ == '__main__':
    main()
