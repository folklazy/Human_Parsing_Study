"""CPI evidence-policy revision: preserve confidence, bindings and execution limits."""
from pathlib import Path
import copy
import json
import sys
import unittest

S = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(S))
from src.application_v2.policy import load_config, fingerprints
from src.application_v2.cohorts import read_channel_gate, verify_channel_evidence, require_config_channel_order
from src.application_v2.runner import ConfiguredRunner
from src.application_v2.first_cohort_replay import _native_threshold


class AcceptedCPIEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.path = S / 'configs/application_v2_first_cohort_v8.yaml'
        self.config = load_config(self.path)
        self.model = self.config['first_cohort']['models'][0]
        self.context = self.config['scoring_contexts'][self.model]['0021834']
        self.binding = self.context['model_binding']
        self.record = read_channel_gate(self.config, S)['models'][self.model]

    def test_acceptance_is_explicit_indirect_not_direct_and_unobserved_classes_do_not_block(self):
        self.assertEqual(self.record['status'], 'ACCEPTED_WITH_INDIRECT_EVIDENCE')
        self.assertFalse(self.record['original_training_header_verified'])
        self.assertTrue(require_config_channel_order(self.config, self.binding, study_root=S))
        path = self.record['components']['SAVED_TRAIN_BEHAVIORAL_REVIEW']['path']
        review = json.loads((S / path).read_text())
        self.assertIn('Footwear', review['unobserved_target_groups'])
        self.assertFalse(review['all_classes_correct_required'])

    def test_historical_direct_only_policy_still_rejects_indirect_record(self):
        with self.assertRaisesRegex(ValueError, 'accepted evidence policy'):
            verify_channel_evidence(self.record, self.binding, study_root=S)
        old = load_config(S / 'configs/application_v2_first_cohort_v7.yaml')
        with self.assertRaisesRegex(ValueError, 'Channel order gate blocked'):
            require_config_channel_order(old, self.binding, study_root=S)

    def test_record_cannot_be_promoted_to_direct_or_assigned_to_other_checkpoint(self):
        direct = copy.deepcopy(self.record)
        direct['status'] = 'DIRECT_VERIFIED'
        with self.assertRaises(ValueError):
            verify_channel_evidence(direct, self.binding, study_root=S, accepted_statuses=['DIRECT_VERIFIED'])
        wrong = copy.deepcopy(self.binding)
        wrong['checkpoint_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'checkpoint/source release'):
            verify_channel_evidence(self.record, wrong, study_root=S, accepted_statuses=[self.record['status']])

    def test_missing_or_changed_evidence_components_are_rejected(self):
        bad = copy.deepcopy(self.record)
        del bad['components']['CHECKPOINT_EMBEDDED_CONFIG']
        with self.assertRaisesRegex(ValueError, 'Incomplete converging'):
            verify_channel_evidence(bad, self.binding, study_root=S, accepted_statuses=[bad['status']])
        bad = copy.deepcopy(self.record)
        bad['components']['SAVED_TRAIN_BEHAVIORAL_REVIEW']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'component hash mismatch'):
            verify_channel_evidence(bad, self.binding, study_root=S, accepted_statuses=[bad['status']])

    def test_same_numeric_projection_and_only_six_bounded_train_contexts(self):
        old = load_config(S / 'configs/application_v2_first_cohort_v7.yaml')
        before = json.loads((S / old['cohort']['mapping']).read_text())
        after = json.loads((S / self.config['cohort']['mapping']).read_text())
        for key in ['target_catalog', 'gt_mapping', 'prediction_mappings', 'unsupported_targets']:
            self.assertEqual(before[key], after[key])
        contexts = [c for rows in self.config['scoring_contexts'].values() for c in rows.values()]
        self.assertEqual(len(contexts), 6)
        self.assertEqual({c['input_binding']['split'] for c in contexts}, {'Training'})
        self.assertFalse(self.config['authorization']['full_benchmark'])

    def test_contexts_do_not_enable_model_scoring_or_full_benchmark(self):
        runner = ConfiguredRunner(self.path)
        mapping = json.loads((S / self.config['cohort']['mapping']).read_text())
        with self.assertRaisesRegex(ValueError, 'preparation-only'):
            runner.score_frame(mapping, self.binding, self.context['input_binding'], [], [],
                lifecycle={'status': 'COMPLETE'}, system_id=self.model, image_id='0021834')
        with self.assertRaises(ValueError):
            load_config(self.path, benchmark=True)

    def test_cached_threshold_duplicates_may_agree_but_conflicts_are_rejected(self):
        self.assertEqual(_native_threshold({'resolved_config': 'model=dict(test_cfg=dict(score_thr=.01), head=dict(score_thr=.01))'}), .01)
        with self.assertRaisesRegex(ValueError, 'unambiguous'):
            _native_threshold({'resolved_config': 'model=dict(test_cfg=dict(score_thr=.01), head=dict(score_thr=.1))'})

    def test_first_cohort_native_settings_change_replay_fingerprint_but_confidence_does_not(self):
        before = fingerprints(self.config, {'saved_native': 'fixture'})
        changed = copy.deepcopy(self.config)
        changed['first_cohort']['protocol']['matching']['native_score_thresholds'][self.model] = .1
        self.assertNotEqual(before['inference'], fingerprints(changed, {'saved_native': 'fixture'})['inference'])
        changed = copy.deepcopy(self.config)
        changed['first_cohort']['channel_order_evidence']['manifest_sha256'] = '0' * 64
        self.assertEqual(before['inference'], fingerprints(changed, {'saved_native': 'fixture'})['inference'])
        self.assertNotEqual(before['scoring'], fingerprints(changed, {'saved_native': 'fixture'})['scoring'])


if __name__ == '__main__':
    unittest.main()
