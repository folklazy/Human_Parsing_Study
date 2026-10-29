"""Independent orchestration fixtures; no model import, forward, or GPU query."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('cpi_continuation', SCRIPTS / 'run_cpi_continuation.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ContinuationCases(unittest.TestCase):
    def audit(self, root, name, ids, failures):
        path = root / name
        path.mkdir()
        hist = [[0] * 20 for _ in range(20)]
        people = {str(t): dict(G_loc=0, G_sem=0, TP=0, FP=0, FN=0, Q_numerator=0.)
                  for t in [.5, .75]}
        (path / 'RECONCILED.json').write_text(json.dumps(dict(
            verified_ids=ids, histogram=hist, native_histogram=hist,
            person_sufficient_statistics=people)))
        (path / 'INVENTORY.json').write_text(json.dumps({'non_complete_ledger': failures}))
        return path

    def test_resolved_failed_ID_preserves_attempt_and_allows_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = self.audit(root, 'old', ['a'], [{'image_id': 'b', 'status': 'FAILED'}])
            new = self.audit(root, 'new', ['b'], [])
            result = module.aggregate([old, new], ['a', 'b'])
            self.assertEqual((result['status'], result['complete'], result['failed']), ('COMPLETE', 2, 0))
            self.assertEqual(len(result['historical_failure_attempts']), 1)

    def test_same_ID_repeated_failure_counted_once_with_null_primary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audits = [self.audit(root, str(i), [], [{'image_id': 'b', 'status': 'FAILED'}])
                      for i in range(2)]
            result = module.aggregate(audits, ['a', 'b'])
            self.assertEqual((result['failed'], result['not_attempted']), (1, 1))
            self.assertIsNone(result['metrics']['primary'])
            self.assertEqual(len(result['historical_failure_attempts']), 2)

    def test_duplicate_success_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audits = [self.audit(root, str(i), ['a'], []) for i in range(2)]
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                module.aggregate(audits, ['a', 'b'])

    def test_invalid_and_failed_same_ID_not_double_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit = self.audit(root, 'a', [], [{'image_id': 'b', 'status': 'FAILED'},
                                               {'image_id': 'b', 'status': 'INVALID'}])
            result = module.aggregate([audit], ['a', 'b'])
            self.assertEqual((result['failed'], result['invalid'], result['not_attempted']), (0, 1, 1))

    def test_output_location_change_only_beyond_existing_shared_wrapper(self):
        for mid in module.MODELS.values():
            source = module.expanded_worker(mid)
            compile(source, '<frozen-worker-with-controls>', 'exec')
            self.assertIn("out.is_relative_to(P/'outputs/cpi_continuations')", source)
            self.assertIn("segment['prior_execution_seconds']", source)
            self.assertIn("segment['prior_retained_bytes']", source)
            self.assertIn("if row['status']!='COMPLETE':break", source)


if __name__ == '__main__':
    unittest.main()
