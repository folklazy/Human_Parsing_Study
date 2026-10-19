"""Policy acceptance is distinct from channel evidence and execution permission."""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import numpy as np

S = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(S))
from src.application_v2.policy import load_config, validate_config
from src.application_v2.plan import first_cohort_plan
from src.application_v2.cohorts import verify_channel_header, require_config_channel_order
from src.application_v2.runner import ConfiguredRunner
from src.application_v2.taxonomy import project_gt
from src.application_v2.evaluation import person_truth


class FirstCohortPolicyTests(unittest.TestCase):
    def setUp(self):
        self.path = S / 'configs/application_v2_first_cohort_v7.yaml'
        self.config = load_config(self.path)
        self.record = json.loads((S / self.config['decision_record']).read_text())

    def test_five_policies_accepted_without_semantic_or_benchmark_acceptance(self):
        for name in ['MAPPING', 'GT_DOMAIN', 'POPULATION', 'MATCHING', 'RUNTIME_CLAIM']:
            row = next(d for d in self.record['decisions'] if d['id'] == 'FIRST_COHORT_' + name)
            self.assertEqual(row['status'], 'ACCEPTED_BY_USER')
        self.assertFalse(self.config['authorization']['full_benchmark'])
        self.assertIsNone(self.config.get('scoring_contexts'))
        with self.assertRaises(ValueError):
            load_config(self.path, benchmark=True)

    def test_plan_uses_two_CPI_systems_and_frozen_dependency_only(self):
        plan = first_cohort_plan(self.config, S)
        self.assertEqual([p['system_id'] for p in plan['parser_systems']], ['CPI_R50_CIHP', 'CPI_ConvNeXtB_CIHP'])
        self.assertEqual([p['native_score_threshold'] for p in plan['parser_systems']], [.01, .05])
        self.assertEqual([d['dependency_id'] for d in plan['shared_dependencies']], ['YOLO26X_FROZEN'])
        self.assertEqual(plan['GT_matching']['evaluation_bbox_source'], 'NATIVE_PARSER_BOX')
        self.assertEqual(plan['GT_matching']['conditioning_bbox_source'], 'FROZEN_YOLO26X_BOX')
        self.assertFalse(plan['model_loading'])

    def test_selector_does_not_fall_back_to_legacy_roster(self):
        # Selector-only experiment, not a newly accepted configuration.
        self.config['systems']['variants'] = 999
        self.config['bounded_train']['models'] = ['FAKE_LEGACY_MODEL']
        plan = first_cohort_plan(self.config, S)
        self.assertEqual(len(plan['parser_systems']), 2)
        self.assertNotIn('FAKE_LEGACY_MODEL', str(plan['parser_systems']))

    def test_accepted_roster_cannot_be_replaced(self):
        self.config['first_cohort']['models'] = ['FASHN_B4']
        with self.assertRaisesRegex(ValueError, 'Accepted decision conflict'):
            validate_config(self.config, self.record)

    def test_real_config_channel_gate_blocks_scoring_even_after_policy_acceptance(self):
        run = S / json.loads((S / 'provenance/FIRST_COHORT_POLICY_ACCEPTANCE_ACTIVE.json').read_text())['run']
        gate = json.loads((run / 'CHANNEL_ORDER_EVIDENCE.json').read_text())
        row = gate['models']['CPI_R50_CIHP']
        binding = {'checkpoint_sha256': row['checkpoint_sha256'], 'source_commit': row['source_commit'],
                   'native_class_order': row['expected_native_class_order']}
        with self.assertRaisesRegex(ValueError, 'direct official header'):
            require_config_channel_order(self.config, binding)
        with self.assertRaisesRegex(ValueError, 'direct official header'):
            ConfiguredRunner(self.path).score_frame({}, binding, {}, [], [], lifecycle={'status': 'COMPLETE'})

    def test_matching_cannot_diverge_from_accepted_protocol(self):
        self.config['evaluation']['threshold'] = .25
        with self.assertRaisesRegex(ValueError, 'Executable GT matching conflicts'):
            validate_config(self.config, self.record)

    def test_association_cannot_diverge_from_accepted_protocol(self):
        self.config['first_cohort']['draft_association']['threshold'] = .25
        with self.assertRaisesRegex(ValueError, 'Executable association conflicts'):
            validate_config(self.config, self.record)

    def test_owner_unknown_known_target_kept_global_but_void_per_person(self):
        mapping = json.loads((S / self.config['cohort']['mapping']).read_text())
        category = np.array([[13, 13, 0]], np.uint8)
        human = np.array([[0, 1, 0]], np.uint8)
        target, global_valid = project_gt(category, human, mapping)
        self.assertEqual(target[0, 0], 1)
        self.assertTrue(global_valid[0, 0])
        truth, person_valid = person_truth(target, human, global_valid, 1)
        self.assertFalse(person_valid[0, 0])
        self.assertTrue(person_valid[0, 1])
        self.assertEqual(truth[0, 1], 1)
        domain = self.config['first_cohort']['protocol']['domain']
        self.assertIn('KEEP_KNOWN_TARGET', domain['category_positive_human0_global'])
        self.assertEqual(domain['category_positive_human0_per_person'], 'VOID_OWNER_UNKNOWN')

    def test_face_display_name_does_not_change_numeric_catalog(self):
        mapping = json.loads((S / self.config['cohort']['mapping']).read_text())
        self.assertEqual(mapping['target_catalog']['1'], 'Exposed_face')
        self.assertEqual(self.config['cohort']['target_display_names']['1'], 'Face region')

    def test_entrypoint_requires_explicit_dry_run(self):
        command = [sys.executable, str(S / 'scripts/first_cohort_entrypoint.py'), '--config', str(self.path)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--dry-run', result.stderr)


class DirectHeaderValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.names = ['Background', 'SYNTHETIC_CLASS']
        self.model = dict(checkpoint_sha256='a' * 64, source_commit='b' * 40, native_class_order=self.names)
        self.document = self.root / 'fixture.json'
        self.document.write_text(json.dumps({'categories': [{'parsing': self.names}]}))
        self.proof = dict(status='DIRECT_VERIFIED', proof_kind='OFFICIAL_ANNOTATION_JSON_HEADER',
            checkpoint_sha256=self.model['checkpoint_sha256'], source_commit=self.model['source_commit'],
            provenance_review='VERIFIED', official_source_url='https://example.invalid/SYNTHETIC_ONLY',
            release_relationship_evidence='Synthetic unit fixture, not an actual verified release',
            document='fixture.json', document_sha256=hashlib.sha256(self.document.read_bytes()).hexdigest())

    def test_synthetic_direct_header_bytes_order_and_binding(self):
        self.assertTrue(verify_channel_header(self.proof, self.model, study_root=self.root))

    def test_verified_status_alone_is_not_evidence(self):
        with self.assertRaises(ValueError):
            verify_channel_header({'status': 'DIRECT_VERIFIED'}, self.model, study_root=self.root)

    def test_other_checkpoint_header_cannot_satisfy_gate(self):
        self.proof['checkpoint_sha256'] = 'c' * 64
        with self.assertRaisesRegex(ValueError, 'checkpoint/source release'):
            verify_channel_header(self.proof, self.model, study_root=self.root)

    def test_reordered_names_or_changed_source_bytes_rejected(self):
        self.model['native_class_order'] = list(reversed(self.names))
        with self.assertRaisesRegex(ValueError, 'differs from the bound'):
            verify_channel_header(self.proof, self.model, study_root=self.root)
        self.document.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'document hash mismatch'):
            verify_channel_header(self.proof, self.model, study_root=self.root)


if __name__ == '__main__':
    unittest.main()
