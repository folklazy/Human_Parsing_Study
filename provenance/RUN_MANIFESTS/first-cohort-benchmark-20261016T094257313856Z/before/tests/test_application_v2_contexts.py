"""Two-system/two-image CPU integration. Acceptance exists only in temp fixtures."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import tempfile
import unittest
import numpy as np
import yaml

S = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(S))
from src.application_v2.policy import digest, load_config
from src.application_v2.runner import ConfiguredRunner


class ContextRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = load_config(S / 'configs/application_v2_first_cohort_v5.yaml')
        self.decisions = json.loads((S / self.config['decision_record']).read_text())
        self.mapping = json.loads((S / self.config['cohort']['mapping']).read_text())
        self.mapping['status'] = 'ACCEPTED'  # Synthetic temp file, never active study data.
        self.systems = self.config['first_cohort']['models']
        self.population = [{'image_id': 'one', 'G_loc': 1, 'G_sem': 1},
                           {'image_id': 'two', 'G_loc': 1, 'G_sem': 1}]
        self.config['scoring_population'] = copy.deepcopy(self.population)
        self.config['scoring_contexts'] = {}
        for i, system in enumerate(self.systems):
            model = dict(checkpoint_sha256=str(i + 1) * 64, config_sha256='b' * 64,
                         source_commit='c' * 40, native_class_order=list(range(20)),
                         native_taxonomy='CIHP', head_classes=20)
            self.config['scoring_contexts'][system] = {}
            for j, image in enumerate(['one', 'two']):
                support = dict(status='VERIFIED', checkpoint_sha256=model['checkpoint_sha256'],
                               config_sha256=model['config_sha256'], source_commit=model['source_commit'],
                               native_class_order_sha256=digest(model['native_class_order']),
                               mapping_sha256=digest(self.mapping),
                               target_catalog_sha256=digest(self.mapping['target_catalog']),
                               evidence_references=['SYNTHETIC FIXTURE ONLY'], semantic_review='VERIFIED',
                               supported_target_ids=[1, 2, 3, 4, 5, 6])
                self.config['scoring_contexts'][system][image] = dict(
                    status='ACCEPTED', mapping_sha256=digest(self.mapping), model_binding=copy.deepcopy(model),
                    input_binding=dict(status='VERIFIED', image_id=image, input_sha256=str(j + 3) * 64,
                                       original_wh=[2, 2]),
                    domain=dict(status='ACCEPTED', evidence='SYNTHETIC complete GT domain'),
                    target_support_policy='COMMON_CAPABILITY', failure_policy='STRICT_COMPLETE',
                    evaluation_bbox_source='SYNTHETIC_PREDICTED_BOX', threshold=.5,
                    require_checkpoint_specific_support=True, support_binding=support)
        for field in ['mapping', 'native_reference', 'sidecars_manifest']:
            target = self.root / self.config['cohort'][field]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((S / self.config['cohort'][field]).read_bytes())
        target = self.root / self.config['cohort']['mapping']
        target.write_text(json.dumps(self.mapping))
        self.config['cohort']['mapping_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        self.path = self.root / 'configs/fixture.yaml'
        self.path.parent.mkdir(parents=True)

    def load(self, *, accept=True):
        decisions = copy.deepcopy(self.decisions)
        if accept:
            decisions['decisions'].append(dict(id='SCORING_CONTEXTS', status='ACCEPTED_BY_USER',
                reason='SYNTHETIC FIXTURE ONLY, NOT REAL-DATA ACCEPTANCE',
                bindings={name: copy.deepcopy(self.config[name]) for name in ['scoring_contexts', 'scoring_population']}))
        self.config['decision_record_sha256'] = digest(decisions)
        decision_path = self.root / self.config['decision_record']
        decision_path.parent.mkdir(parents=True, exist_ok=True)
        decision_path.write_text(json.dumps(decisions))
        self.path.write_text(yaml.safe_dump(self.config))
        return ConfiguredRunner(self.path)

    def frame(self, runner, system, image, *, empty=False):
        context = self.config['scoring_contexts'][system][image]
        gt = [dict(id='gt', bbox=[0, 0, 2, 2], loc_eligible=True, sem_eligible=True,
                   semantic=np.ones((2, 2), np.int16), valid=np.ones((2, 2), bool))]
        predictions = [] if empty else [dict(id='pred', bbox=[0, 0, 2, 2], score=.9,
            semantic=np.ones((2, 2), np.int16), evaluation_bbox=dict(xyxy=[0, 0, 2, 2],
            source='SYNTHETIC_PREDICTED_BOX', coordinate_convention='XYXY_HALF_OPEN', derivation_revision='fixture'))]
        score = runner.score_frame(self.mapping, context['model_binding'], context['input_binding'],
            gt, predictions, lifecycle={'status': 'COMPLETE'}, system_id=system, image_id=image)
        return dict(system_id=system, image_id=image, execution_status='COMPLETE', score_result=score)

    def test_actual_runner_two_models_two_images_reaches_strict_report(self):
        runner = self.load()
        frames = [self.frame(runner, system, image, empty=image == 'two')
                  for system in self.systems for image in ['one', 'two']]
        report = runner.comparison_report(self.population, frames)
        for row in report['systems']:
            self.assertEqual(row['status'], 'COMPLETE')
            self.assertEqual(row['main_metrics']['Q_person_sem_GT'], .5)
            self.assertEqual(row['main_metrics']['FN'], 1)
            self.assertEqual(row['execution']['denominator'], 2)
        self.assertEqual(len({f['score_result']['scoring_context_sha256'] for f in frames}), 4)

    def test_unaccepted_registry_rejected(self):
        with self.assertRaisesRegex(ValueError, 'accepted decision binding'):
            self.load(accept=False)

    def test_incomplete_context_population_rejected(self):
        del self.config['scoring_contexts'][self.systems[0]]['two']
        with self.assertRaisesRegex(ValueError, 'complete population'):
            self.load()

    def test_per_model_gt_domain_cannot_differ(self):
        self.config['scoring_contexts'][self.systems[1]]['one']['domain']['evidence'] = 'favorable other domain'
        with self.assertRaisesRegex(ValueError, 'share mapping, GT domain'):
            self.load()

    def test_checkpoint_cannot_switch_between_images(self):
        self.config['scoring_contexts'][self.systems[0]]['two']['model_binding']['checkpoint_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'change checkpoint'):
            self.load()

    def test_same_image_must_have_same_input_hash_across_models(self):
        self.config['scoring_contexts'][self.systems[1]]['one']['input_binding']['input_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'same verified source input'):
            self.load()

    def test_wrong_image_identity_rejected(self):
        self.config['scoring_contexts'][self.systems[0]]['one']['input_binding']['image_id'] = 'two'
        with self.assertRaisesRegex(ValueError, 'declared input image ID'):
            self.load()

    def test_threshold_cannot_override_executable_config(self):
        for contexts in self.config['scoring_contexts'].values():
            for context in contexts.values():
                context['threshold'] = .75
        with self.assertRaisesRegex(ValueError, 'executable evaluation/reporting policy'):
            self.load()

    def test_registry_requires_exact_system_and_image_at_scoring(self):
        runner = self.load()
        context = self.config['scoring_contexts'][self.systems[0]]['one']
        with self.assertRaisesRegex(ValueError, 'exact registered'):
            runner.score_frame(self.mapping, context['model_binding'], context['input_binding'], [], [], lifecycle={'status': 'COMPLETE'})

    def test_report_cannot_drop_failing_frame_from_population(self):
        runner = self.load()
        with self.assertRaisesRegex(ValueError, 'predeclared scoring population'):
            runner.comparison_report(self.population[:1], [])

    def test_score_cannot_be_moved_to_other_system_or_image(self):
        runner = self.load()
        frame = self.frame(runner, self.systems[0], 'one')
        frame['image_id'] = 'two'
        with self.assertRaisesRegex(ValueError, 'accepted, bound'):
            runner.comparison_report(self.population, [frame])

    def test_failure_retained_and_valid_empty_counts_as_execution_success(self):
        runner = self.load()
        frames = [self.frame(runner, self.systems[0], 'one', empty=True),
                  dict(system_id=self.systems[0], image_id='two', execution_status='FAILED',
                       failure_events=[{'status': 'MODEL_SYSTEM_FAILURE'}])]
        first, second = runner.comparison_report(self.population, frames)['systems']
        self.assertEqual(first['status'], 'INCOMPLETE')
        self.assertIsNone(first['main_metrics'])
        self.assertEqual(first['execution']['completed'], 1)
        self.assertEqual(first['success_only_diagnostic']['FN'], 1)
        self.assertEqual(second['execution']['not_attempted_or_unscheduled'], 2)

    def test_single_context_and_registry_cannot_coexist(self):
        self.config['scoring_context'] = copy.deepcopy(self.config['scoring_contexts'][self.systems[0]]['one'])
        with self.assertRaisesRegex(ValueError, 'never both'):
            self.load()

    def test_explicit_null_registry_does_not_enable_real_scoring(self):
        self.config['scoring_contexts'] = None
        self.config.pop('scoring_population')
        # No registry exists to accept; null remains a disabled optional field.
        runner = self.load(accept=False)
        with self.assertRaisesRegex(ValueError, 'No accepted scoring context'):
            runner.score_frame(self.mapping, {}, {}, [], [], lifecycle={'status': 'COMPLETE'})

    def bind_image_domains(self):
        self.config['first_cohort']['require_per_image_GT_domain_binding'] = True
        for frames in self.config['scoring_contexts'].values():
            for image, context in frames.items():
                context['domain']['image_binding'] = dict(image_id=image, G_loc=1, G_sem=1,
                    GT_domain_recipe_sha256=digest({'SYNTHETIC_GT_RECIPE': image}))

    def test_image_domains_can_differ_between_images_but_match_across_systems(self):
        self.bind_image_domains()
        # Different images may have different GT counts and masks under one policy.
        self.config['scoring_population'][1].update(G_loc=3, G_sem=2)
        for frames in self.config['scoring_contexts'].values():
            frames['two']['domain']['image_binding'].update(G_loc=3, G_sem=2)
        runner = self.load()
        first = runner.config['scoring_contexts'][self.systems[0]]
        self.assertNotEqual(first['one']['domain']['image_binding'], first['two']['domain']['image_binding'])
        for system in self.systems:
            self.assertEqual(runner.config['scoring_contexts'][system]['two']['domain']['image_binding']['G_sem'], 2)
        # The shared bundle already permits different native taxonomy projections.
        self.assertNotEqual(self.mapping['prediction_mappings']['CIHP']['10'], self.mapping['prediction_mappings']['LIP']['10'])

    def test_same_image_GT_domain_mismatch_or_missing_binding_rejected(self):
        self.bind_image_domains()
        self.config['scoring_contexts'][self.systems[1]]['one']['domain']['image_binding']['GT_domain_recipe_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'same GT/domain binding'):
            self.load()
        self.bind_image_domains()
        del self.config['scoring_contexts'][self.systems[1]]['one']['domain']['image_binding']
        with self.assertRaisesRegex(ValueError, 'Per-image GT/domain binding'):
            self.load()


if __name__ == '__main__':
    unittest.main()
