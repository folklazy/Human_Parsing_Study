"""Preparation/execution separation and configured secondary scoring boundaries."""
from pathlib import Path
import copy
import json
import sys
import unittest

S = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(S))
from src.application_v2.policy import load_config, validate_config
from src.application_v2.contexts import select_context, check_report_binding
from src.application_v2.plan import first_cohort_plan
from src.application_v2.validation_packages import validate_packages


class FreshIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config(S/'configs/application_v2_first_cohort_v9.yaml')

    def test_validation_binding_does_not_activate_population(self):
        result = validate_packages(self.config,S)
        self.assertEqual(result['populations']['main']['images'],4961)
        self.assertEqual(result['populations']['reference']['G_sem'],17504)
        self.assertEqual(len(self.config['scoring_population']),3)
        self.assertFalse(self.config['authorization']['full_benchmark'])

    def test_population_count_conflict_fails(self):
        cfg = copy.deepcopy(self.config)
        cfg['validation_context_packages']['populations']['main']['images'] -= 1
        with self.assertRaisesRegex(ValueError,'counts'):
            validate_packages(cfg,S)

    def test_changed_validation_package_hash_fails(self):
        cfg = copy.deepcopy(self.config)
        cfg['validation_context_packages']['manifest_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash'):
            validate_packages(cfg,S)

    def test_validation_execution_permission_rejected(self):
        cfg = copy.deepcopy(self.config)
        cfg['validation_context_packages']['execution_authorized']=True
        with self.assertRaisesRegex(ValueError,'no execution permission'):
            validate_packages(cfg,S)

    def test_dry_run_keeps_models_unloaded_and_exact_roster(self):
        plan = first_cohort_plan(self.config,S)
        self.assertFalse(plan['model_loading'])
        self.assertEqual([r['system_id'] for r in plan['parser_systems']], self.config['first_cohort']['models'])
        self.assertEqual([r['dependency_id'] for r in plan['shared_dependencies']],['YOLO26X_FROZEN'])

    def test_secondary_binding_cannot_supply_primary_report(self):
        from src.application_v2.policy import digest
        model=self.config['first_cohort']['models'][0]
        iid=self.config['scoring_population'][0]['image_id']
        context=select_context(self.config,model,iid,matching_view='secondary')
        self.assertEqual(context['threshold'],.75)
        self.assertEqual(select_context(self.config,model,iid)['threshold'],.5)
        frame=dict(system_id=model,image_id=iid,score_result=dict(score_eligible=True,
            scoring_context_sha256=digest(context),system_id=model,image_id=iid))
        with self.assertRaisesRegex(ValueError,'bound scoring'):
            check_report_binding(self.config,self.config['scoring_population'],[frame])
        check_report_binding(self.config,self.config['scoring_population'],[frame],matching_view='secondary')

    def test_full_benchmark_remains_rejected(self):
        with self.assertRaises(ValueError):
            load_config(S/'configs/application_v2_first_cohort_v9.yaml',benchmark=True)


if __name__=='__main__':unittest.main()
