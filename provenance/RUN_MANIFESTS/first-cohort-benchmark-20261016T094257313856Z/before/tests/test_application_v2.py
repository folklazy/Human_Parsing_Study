"""Executable implementation fixtures; no weights or public VAL inference."""
import copy
import itertools
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
import numpy as np

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))
from src.application_v2.policy import load_config, validate_config, fingerprints, digest
from src.application_v2.contracts import validate_identity, native_instance_count, validate_frame, stage_rate, availability
from src.application_v2.evaluation import bbox_iou, clip_bbox, assign, associate_native, confusion, semantic_scores, foreground_counts, evaluate_persons, person_truth, SemanticAccumulator
from src.application_v2.artifacts import commit_packet, resume_packet
from src.application_v2.runner import ConfiguredRunner, run_person_jobs, run_native_frame, ModelSystemFailure, ExternalInfrastructureFailure, UnresolvedFailure
from src.application_v2.taxonomy import project_gt, project_prediction


def identity(origin='YOLO_CONDITIONED'):
    native = origin in {'NATIVE_MODEL', 'NATIVE_AND_YOLO', 'NATIVE_AND_ORACLE'}
    condition = 'YOLO' if origin in {'YOLO_CONDITIONED', 'NATIVE_AND_YOLO'} else 'ORACLE' if origin in {'ORACLE_INPUT', 'NATIVE_AND_ORACLE'} else None
    return {'origin': origin, 'native_identity_supported': native,
            'native_instance_id': 'native:0' if native else None, 'conditioning_source': condition,
            'source_opportunity_id': 'op:0' if condition else None, 'final_person_id': 'final:0'}


def record(origin='YOLO_CONDITIONED'):
    ident = identity(origin)
    return {'schema_version': '2.0', 'mask_grid_space': 'ORIGINAL', 'original_wh': [2, 2],
            'label_catalog': [0, 1, 2], 'study_id': 'fixture', 'run_id': 'r', 'system_id': 's',
            'model_id': 'm', 'image_id': 'i', 'adapter_revision': 'fixture-hash', 'execution_profile': 'CPU',
            'source_commit': 'd' * 40, 'geometry_metadata': {'identity_grid': True},
            'precision_profile': {'parameters': 'NO_MODEL_CPU_FIXTURE'},
            'source_track': 'T3B' if origin == 'NATIVE_AND_YOLO' else 'T1' if origin == 'NATIVE_MODEL' else 'T2' if 'ORACLE' in origin else 'T3A',
            'checkpoint_sha256': 'a' * 64, 'config_sha256': 'b' * 64, 'input_sha256': 'c' * 64,
            'persons': [{'identity': ident, 'score': None}],
            'native_identity_supported': ident['native_identity_supported'],
            'native_instance_ids': ['native:0'] if ident['native_identity_supported'] else None}


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(STUDY / 'configs/application_v2.yaml')
        self.decisions = json.loads((STUDY / self.config['decision_record']).read_text())

    def test_accepted_decisions_validate_without_freeze(self):
        self.assertTrue(validate_config(self.config, self.decisions))
        self.assertEqual(self.config['status'], 'DRAFT_IMPLEMENTATION')

    def test_accepted_binding_conflict_rejected(self):
        self.config['identity']['retain_both_origins'] = False
        with self.assertRaisesRegex(ValueError, 'conflict'): validate_config(self.config, self.decisions)

    def test_decision_tampering_detected(self):
        self.decisions['decisions'][0]['status'] = 'PROPOSED'
        with self.assertRaisesRegex(ValueError, 'fingerprint'): validate_config(self.config, self.decisions)

    def test_benchmark_refused(self):
        with self.assertRaises(ValueError): load_config(STUDY / 'configs/application_v2.yaml', benchmark=True)
        with self.assertRaises(ValueError): ConfiguredRunner(STUDY / 'configs/application_v2.yaml', 'FULL_BENCHMARK')

    def test_config_edit_cannot_grant_execution(self):
        self.config['authorization']['full_benchmark'] = True
        with self.assertRaises(ValueError): validate_config(self.config, self.decisions)

    def test_scoring_change_does_not_change_inference_dependency(self):
        a = fingerprints(self.config, {'RGB': 'h', 'oracle_crop': [0, 0, 2, 2]})
        self.config['evaluation']['threshold'] = .75
        b = fingerprints(self.config, {'RGB': 'h', 'oracle_crop': [0, 0, 2, 2]})
        c = fingerprints(self.config, {'RGB': 'h', 'oracle_crop': [0, 0, 1, 2]})
        self.assertEqual(a['inference'], b['inference']); self.assertNotEqual(a['scoring'], b['scoring'])
        self.assertNotEqual(b['inference'], c['inference'])

    def test_crop_and_ownership_configuration_are_inference_dependencies(self):
        a = fingerprints(self.config, {'RGB': 'h'})
        self.config['bounded_train']['crop_margin_per_side'] = .2
        self.assertNotEqual(a['inference'], fingerprints(self.config, {'RGB': 'h'})['inference'])

    def test_bounded_train_scope_cannot_expand_silently(self):
        self.config['bounded_train']['maximum_frames'] = 30
        with self.assertRaises(ValueError): validate_config(self.config, self.decisions)

    def test_cohort_manifest_hash_verified_by_config_loader(self):
        import yaml
        with TemporaryDirectory() as temp:
            root = Path(temp); (root / 'configs').mkdir(); (root / 'provenance').mkdir()
            (root / self.config['decision_record']).write_text(json.dumps(self.decisions))
            for path_key in ['mapping', 'native_reference', 'sidecars_manifest']:
                target = root / self.config['cohort'][path_key]; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((STUDY / self.config['cohort'][path_key]).read_bytes())
            path = root / 'configs/application_v2.yaml'; path.write_text(yaml.safe_dump(self.config))
            load_config(path)
            (root / self.config['cohort']['sidecars_manifest']).write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Cohort source'): load_config(path)


class IdentityRateTests(unittest.TestCase):
    def test_all_identity_origins(self):
        for origin in ['NATIVE_MODEL', 'YOLO_CONDITIONED', 'ORACLE_INPUT', 'NATIVE_AND_YOLO', 'NATIVE_AND_ORACLE']:
            self.assertTrue(validate_identity(identity(origin)))
            validate_frame(record(origin), np.ones((1, 2, 2), np.uint8))

    def test_external_identity_is_not_native(self):
        i = identity(); i['native_identity_supported'] = True
        with self.assertRaises(ValueError): validate_identity(i)

    def test_t3b_must_keep_both_ids(self):
        i = identity('NATIVE_AND_YOLO'); i['source_opportunity_id'] = None
        with self.assertRaises(ValueError): validate_identity(i)
        i = identity('NATIVE_AND_YOLO'); i['native_instance_id'] = None
        with self.assertRaises(ValueError): validate_identity(i)

    def test_unsupported_differs_from_supported_empty(self):
        self.assertIsNone(native_instance_count(False, None)['value'])
        self.assertEqual(native_instance_count(True, [])['value'], 0)
        with self.assertRaises(ValueError): native_instance_count(False, [])

    def test_inventory_ids_must_be_valid_immutable_strings(self):
        for ids in [[''], [4], ['a', 'a']]:
            with self.assertRaises(ValueError): native_instance_count(True, ids)

    def test_original_grid_and_label_ids(self):
        with self.assertRaises(ValueError): validate_frame(record(), np.ones((1, 1, 2), np.uint8))
        with self.assertRaises(ValueError): validate_frame(record(), np.full((1, 2, 2), 9, np.uint8))
        with self.assertRaises(ValueError): validate_frame(record(), np.zeros((1, 2, 2), np.uint8))

    def test_frame_capability_cannot_drop_native_identity(self):
        r = record(); r['native_identity_supported'] = True; r['native_instance_ids'] = ['native:0']
        with self.assertRaises(ValueError): validate_frame(r, np.ones((1, 2, 2), np.uint8))

    def test_native_complete_zero_opportunities(self):
        frame = run_native_frame('f', [], lambda _: [], skip_if_no_opportunities=False, validate_output=lambda _: True)
        self.assertEqual(frame['native_frame_completion_rate']['value'], 1.)
        self.assertIsNone(stage_rate('opportunity', 'person', [])['value'])

    def test_skipped_is_not_completed_or_failure(self):
        frame = run_native_frame('f', [], lambda _: self.fail('must not run'), skip_if_no_opportunities=True, validate_output=lambda _: True)
        rate = frame['native_frame_completion_rate']
        self.assertEqual(rate['skipped_by_routing'], 1); self.assertEqual(rate['denominator'], 0)
        self.assertIsNone(rate['value']); self.assertEqual(frame['failure_events'], [])

    def test_failed_eligible_unit_stays_denominator(self):
        r = stage_rate('parser', 'person', [{'unit_id': 'a', 'eligible': True, 'status': 'FAILED'}])
        self.assertEqual((r['numerator'], r['denominator'], r['value']), (0, 1, 0.))

    def test_rate_requires_named_stage_unit_and_event_id(self):
        with self.assertRaises(ValueError): stage_rate('', 'person', [])
        with self.assertRaises(ValueError): stage_rate('parser', '', [])
        with self.assertRaises(ValueError): stage_rate('parser', 'person', [{'unit_id': None, 'eligible': True, 'status': 'COMPLETED'}])

    def test_output_and_target_available_differ(self):
        flags = availability(completed=True, native_foreground_nonempty=True, final_emitted=True, target_foreground_nonempty=False)
        self.assertTrue(flags['final_emitted']); self.assertFalse(flags['target_semantic_available'])
        with self.assertRaises(ValueError): availability(completed=False, native_foreground_nonempty=True, final_emitted=True, target_foreground_nonempty=True)


class GeometryMetricTests(unittest.TestCase):
    def test_half_open_and_threshold(self):
        self.assertEqual(bbox_iou([0, 0, 1, 1], [1, 0, 2, 1]), 0.)
        self.assertEqual(bbox_iou([0, 0, 2, 1], [0, 0, 1, 1]), .5)
        self.assertEqual(clip_bbox([-1, -2, 3, 2], [2, 2]), [0., 0., 2., 2.])
        self.assertIsNone(bbox_iou([0, 0, 0, 1], [0, 0, 1, 1]))
        with self.assertRaises(ValueError): bbox_iou([0, 0, float('nan'), 1], [0, 0, 1, 1])

    def test_eligible_cardinality_before_weight(self):
        r = assign([[.95, .46], [.46, 0]], ['g1', 'g2'], ['p1', 'p2'], .45)
        self.assertEqual(len(r['matches']), 2)
        r = assign([[.9, .49], [.49, 0]], ['g1', 'g2'], ['p1', 'p2'], .5)
        self.assertEqual(len(r['matches']), 1)

    def test_stable_ids_under_permutation_and_ties(self):
        for left in itertools.permutations(['a', 'b']):
            for right in itertools.permutations(['c', 'd']):
                result = assign(np.ones((2, 2)), list(left), list(right), .5)
                self.assertEqual(result['matches'], [('a', 'c', 1.), ('b', 'd', 1.)])

    def test_empty_side_and_invalid_edges(self):
        self.assertEqual(assign([], ['g'], [], .5)['unmatched_left'], ['g'])
        self.assertEqual(assign([[None]], ['g'], ['p'], .5)['matches'], [])
        with self.assertRaises(ValueError): assign([[1]], ['g'], ['p'], 0)

    def test_gt_supported_mean_explicit(self):
        gt = np.array([[1, 0]]); pred = np.array([[1, 2]])
        s = semantic_scores(confusion(gt, pred, [0, 1, 2], np.ones_like(gt, bool)), [1])
        self.assertEqual(s['miou_gt_supported'], 1.)
        self.assertEqual(s['prediction_only_class_fp_pixels'], {'2': 1})
        self.assertEqual(foreground_counts(gt, pred, [0, 1, 2], np.ones_like(gt, bool))['precision'], .5)

    def test_unknown_pred_does_not_void_GT(self):
        gt = np.array([[1, 0]]); pred = np.array([[-1, -1]])
        s = semantic_scores(confusion(gt, pred, [0, 1], np.ones_like(gt, bool)), [1])
        self.assertEqual(s['miou_gt_supported'], 0.); self.assertEqual(s['unmapped_on_known_negative_pixels'], 1)

    def test_predicted_only_neighbor_classes_count_before_composition(self):
        a = np.array([[1, 1, 0, 0]]); b = np.array([[0, 0, 2, 2]])
        gt = [{'id': 'a', 'bbox': [0, 0, 2, 1], 'loc_eligible': True, 'sem_eligible': True, 'semantic': a, 'valid': np.ones_like(a, bool)},
              {'id': 'b', 'bbox': [2, 0, 4, 1], 'loc_eligible': True, 'sem_eligible': True, 'semantic': b, 'valid': np.ones_like(b, bool)}]
        p = [{'id': 'p1', 'bbox': [0, 0, 2, 1], 'semantic': np.maximum(a, b)}, {'id': 'p2', 'bbox': [2, 0, 4, 1], 'semantic': b}]
        r = evaluate_persons(gt, p, [0, 1, 2], .5, original_wh=[4, 1])
        self.assertEqual(r['Q_person_sem_GT'], 1.); self.assertEqual(r['Q_person_fg'], .75)
        self.assertEqual(r['per_person'][0]['foreground']['fp'], 2)
        self.assertEqual(r['per_person'][0]['foreground']['precision'], .5)

    def test_missing_and_unscored_person(self):
        mask = np.ones((2, 2), np.uint8)
        g = [{'id': 'g', 'bbox': [0, 0, 2, 2], 'loc_eligible': True, 'sem_eligible': True, 'semantic': mask, 'valid': np.ones_like(mask, bool)},
             {'id': 'u', 'bbox': [2, 0, 4, 2], 'loc_eligible': True, 'sem_eligible': False}]
        r = evaluate_persons(g, [], [0, 1], .5, original_wh=[2, 2])
        self.assertEqual((r['G_loc'], r['G_sem'], r['Q_person_sem_GT'], r['gt_person_target_availability']), (2, 1, 0., 0.))
        self.assertIsNone(r['final_precision'])
        p = [{'id': 'p1', 'bbox': [2, 0, 4, 2], 'semantic': mask}, {'id': 'p2', 'bbox': [2, 0, 4, 2], 'semantic': mask}]
        self.assertEqual(evaluate_persons(g, p, [0, 1], .5, original_wh=[2, 2])['final_fp'], 1)

    def test_association_keeps_two_sources(self):
        r = associate_native([{'id': 'yo', 'bbox': [0, 0, 1, 1]}], [{'id': 'native', 'bbox': [0, 0, 1, 1]}], .5)
        self.assertEqual(r['associations'][0]['source_opportunity_id'], 'yo')
        self.assertEqual(r['associations'][0]['native_instance_id'], 'native')

    def test_projection_is_shared_and_preserves_source(self):
        mapping = json.loads((STUDY / 'taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V2.json').read_text())
        category = np.array([[13, 22, 0, 0]], np.uint8); human = np.array([[1, 1, 1, 0]], np.uint8)
        before = category.copy(); projected, valid = project_gt(category, human, mapping)
        self.assertEqual(projected[0, 0], 1); self.assertEqual(valid.tolist(), [[True, False, False, True]])
        self.assertTrue(np.array_equal(before, category))
        self.assertEqual(project_prediction(np.array([[6, 13]]), mapping, native_taxonomy="CIHP").tolist(), [[5, 1]])
        with self.assertRaises(ValueError): project_prediction(np.array([[99]]), mapping, native_taxonomy="CIHP")

    def test_unowned_known_semantics_not_assigned_to_person(self):
        target, valid = person_truth(np.array([[1, 2, 1]]), np.array([[1, 2, 0]]), np.ones((1, 3), bool), 1)
        self.assertEqual(target.tolist(), [[1, 0, 0]])
        self.assertEqual(valid.tolist(), [[True, True, False]])

    def test_global_accumulation_and_group_score(self):
        accumulator = SemanticAccumulator([0, 1], [1], {'body': [1], 'unsupported': []})
        accumulator.update(np.ones((1, 100), int), np.ones((1, 100), int), np.ones((1, 100), bool))
        accumulator.update(np.ones((1, 1), int), np.zeros((1, 1), int), np.ones((1, 1), bool))
        self.assertEqual(accumulator.report()['miou_gt_supported'], 100/101)
        self.assertIsNone(accumulator.report()['group_scores']['unsupported'])


class LifecycleArtifactTests(unittest.TestCase):
    def test_partial_person_retention(self):
        def worker(op):
            if op['id'] == 'c': raise ModelSystemFailure('fixture OOM')
            return op['id']
        r = run_person_jobs('f', [{'id': v} for v in 'abc'], worker, failure_scope='PERSON', validate_output=lambda _: True)
        self.assertEqual(r['outputs'], ['a', 'b']); self.assertEqual(r['opportunity_completion_rate']['value'], 2/3)
        self.assertEqual(len(r['failure_events']), 1)

    def test_frame_failure_discards_outputs(self):
        def worker(op):
            if op['id'] == 'b': raise ModelSystemFailure('fixture OOM')
            return op['id']
        r = run_person_jobs('f', [{'id': v} for v in 'abc'], worker, failure_scope='FRAME', validate_output=lambda _: True)
        self.assertEqual(r['outputs'], []); self.assertEqual(r['opportunity_completion_rate']['denominator'], 3)

    def test_invalid_contract_is_failure(self):
        r = run_person_jobs('f', [{'id': 'a'}], lambda _: 'bad', failure_scope='PERSON', validate_output=lambda _: False)
        self.assertEqual(r['outputs'], []); self.assertEqual(r['opportunity_completion_rate']['numerator'], 0)

    def test_external_or_unresolved_trial_incomplete(self):
        for exception in [ExternalInfrastructureFailure, UnresolvedFailure]:
            def worker(_): raise exception('fixture external event')
            r = run_person_jobs('f', [{'id': 'a'}], worker, failure_scope='PERSON', validate_output=lambda _: True)
            self.assertEqual(r['trial_status'], 'INCOMPLETE_INVALID_TRIAL'); self.assertEqual(r['outputs'], [])

    def test_global_finalizer_failure_does_not_reuse_provisional(self):
        def finalizer(_): raise ModelSystemFailure('global NMS failed')
        r = run_person_jobs('f', [{'id': 'a'}], lambda _: 'a', failure_scope='PERSON', validate_output=lambda _: True, finalizer=finalizer)
        self.assertEqual(r['outputs'], []); self.assertGreaterEqual(r['frame_cost_seconds'], 0)

    def test_global_finalizer_invalid_output_discards_provisional(self):
        r = run_person_jobs('f', [{'id': 'a'}], lambda _: 'good', failure_scope='PERSON',
                            validate_output=lambda p: p == 'good', finalizer=lambda _: ['bad'])
        self.assertEqual(r['outputs'], [])
        self.assertEqual(r['failure_events'][0]['status'], 'CONTRACT_FAILURE')

    def test_configured_runner_uses_policy(self):
        runner = ConfiguredRunner(STUDY / 'configs/application_v2.yaml')
        self.assertEqual(runner.native_frame('f', [], lambda _: [], lambda _: True)['native_frame_completion_rate']['value'], 1.)

    def test_atomic_publish_faults_and_resume_integrity(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp) / 'packet'
            def fault(stage): raise RuntimeError(stage)
            with self.assertRaises(RuntimeError): commit_packet(directory, record(), np.ones((1, 2, 2), np.uint8), {'inference': 'i', 'scoring': 's'}, fault=fault)
            self.assertFalse(directory.exists()); self.assertEqual(list(Path(temp).iterdir()), [])
            commit_packet(directory, record(), np.ones((1, 2, 2), np.uint8), {'inference': 'i', 'scoring': 's'})
            self.assertEqual(resume_packet(directory, 'i')['fingerprints']['scoring'], 's')
            with self.assertRaises(ValueError): resume_packet(directory, 'changed-input')
            with self.assertRaises(FileExistsError): commit_packet(directory, record(), np.ones((1, 2, 2), np.uint8), {'inference': 'i', 'scoring': 's'})
            (directory / 'arrays.npz').write_bytes(b'corruption')
            with self.assertRaises(ValueError): resume_packet(directory, 'i')

    def test_partial_status_packet_roundtrip(self):
        with TemporaryDirectory() as temp:
            r = record('NATIVE_AND_YOLO'); r['opportunity_statuses'] = [{'id': 'op:0', 'status': 'COMPLETED'}, {'id': 'op:1', 'status': 'FAILED'}]
            directory = Path(temp) / 'partial'
            commit_packet(directory, r, np.ones((1, 2, 2), np.uint8), {'inference': 'i', 'scoring': 's'})
            self.assertEqual(len(resume_packet(directory, 'i')['opportunity_statuses']), 2)


if __name__ == '__main__': unittest.main()
