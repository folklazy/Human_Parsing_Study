"""Run an explicit source-preserved synthetic/config suite, never a model or dataset audit."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
MODULES=[
    'test_application_v2', 'test_application_v2_handoff',
    'test_application_v2_contexts', 'test_application_v2_comparison',
    'test_application_v2_acquisition', 'test_application_v2_first_cohort_policy',
    'test_application_v2_cpi_evidence_acceptance', 'test_application_v2_immutable_config',
    'test_application_v2_yolo_bootstrap',
]
ASSET_DEPENDENT_TESTS={
    'test_application_v2_first_cohort_policy.FirstCohortPolicyTests.test_plan_uses_two_CPI_systems_and_frozen_dependency_only',
    'test_application_v2_first_cohort_policy.FirstCohortPolicyTests.test_selector_does_not_fall_back_to_legacy_roster',
}


def cases(suite):
    for case in suite:
        if isinstance(case,unittest.TestSuite):
            yield from cases(case)
        else:
            yield case

if __name__=='__main__':
    # Preserved receipt fixtures write only temporary synthetic data here.
    # Git does not retain empty/ignored runtime directories in a clean clone.
    (ROOT/'outputs').mkdir(exist_ok=True)
    loader=unittest.TestLoader();suite=unittest.TestSuite()
    for module in MODULES:
        loaded=loader.discover(str(ROOT/'tests'),pattern=module+'.py')
        suite.addTests(case for case in cases(loaded) if case.id() not in ASSET_DEPENDENT_TESTS)
    print('PORTABLE CPU SCOPE: '+', '.join(MODULES),flush=True)
    print('EXTERNAL-ASSET TESTS NOT RUN: fresh_integration, validation_launch, original dataset/evaluator suites',flush=True)
    print('EXTERNAL-ASSET PLAN TESTS NOT RUN (not counted as passing): '+', '.join(sorted(ASSET_DEPENDENT_TESTS)),flush=True)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
