"""Receipt validation before any model/evaluator import in isolated YOLO workers."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

S=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('yolo_bootstrap',S/'scripts/first_cohort_yolo_bootstrap_worker.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)


class YoloBootstrapTests(unittest.TestCase):
    def test_receipt_checks_frozen_files_before_model_loading(self):
        with tempfile.TemporaryDirectory(dir=S/'outputs') as directory:
            root=Path(directory);frozen=root/'source.json';frozen.write_text('{}')
            receipt=root/'receipt.json';receipt.write_text(json.dumps(dict(status='APPROVED_FROZEN_CPU_VALIDATED',model_id='YOLO26X_FROZEN',
                frozen_files=[dict(path=str(frozen.relative_to(S)),sha256=worker.sha(frozen))],worker_sha256=worker.sha(S/'scripts/first_cohort_yolo_bootstrap_worker.py'))))
            checksum=worker.sha(receipt);self.assertEqual(worker.verified_receipt(receipt,checksum)['model_id'],'YOLO26X_FROZEN')
            frozen.write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError,'Frozen authorization'):worker.verified_receipt(receipt,checksum)

    def test_receipt_change_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'receipt.json';path.write_text('{}')
            with self.assertRaisesRegex(ValueError,'receipt changed'):worker.verified_receipt(path,'0'*64)
