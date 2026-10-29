"""Targeted controls: effective identity and complete resource clocks."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_cpi_chunked_continuation as wrapper
from run_cpi_memory_diagnostic import diagnostic_scope


class ChunkedControls(unittest.TestCase):
    def test_r50_diagnostic_cannot_use_convnext_ids(self):
        config = {'model_id': 'CPI_R50_CIHP', 'max_model_frame_calls': 3, 'automatic_retries': 0,
                  'calls': [['Training', '0000930'], ['Validation', '0000018'], ['Validation', '0000004']]}
        self.assertEqual(diagnostic_scope(config), ('CPI_R50_CIHP', '0000004'))
        config['calls'] = [['Training', '0000930'], ['Validation', '0003218'], ['Validation', '0001641']]
        with self.assertRaises(ValueError):
            diagnostic_scope(config)

    def test_diagnostic_resources_are_filtered_by_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, mid in [('r50', 'CPI_R50_CIHP'), ('convnext', 'CPI_ConvNeXtB_CIHP')]:
                folder = root / 'outputs/cpi_memory_diagnostics' / name
                folder.mkdir(parents=True)
                (folder / 'RUN.json').write_text(json.dumps({'model_id': mid, 'end_utc': '2026-01-01T00:00:00+00:00'}))
            with patch.object(wrapper, 'P', root), patch.object(wrapper, 'MID', 'CPI_R50_CIHP'):
                records = wrapper.diagnostic_records()
            self.assertEqual([f.parent.name for f in records], ['r50'])

    def test_effective_identity_is_created_after_base_identity(self):
        source = wrapper.expanded(wrapper.MID)
        compile(source, '<bounded-controller-fixture>', 'exec')
        base = source.index('inference_fingerprint=hashlib.sha256')
        effective = source.index("metadata['implementation_fingerprint']=")
        first_commit = source.index("atomic(packet/'packet.json',metadata)")
        self.assertLess(base, effective)
        self.assertLess(effective, first_commit)
        self.assertLess(source.index('install_memory_repair(adapter.model.bbox_head'),
                        source.index('# One non-VAL warmup'))
        self.assertIn("if row['status']!='COMPLETE':break", source)
        self.assertNotIn('reference_prefix=2', source)  # No extra diagnostic work per canonical frame.

    def test_diagnostic_time_is_counted_once_alongside_worker_time(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = []
            for name, end in [('worker', 7), ('diagnostic', 23)]:
                path = root / (name + '.json')
                path.write_text(json.dumps({'start_utc': '2026-01-01T00:00:00+00:00',
                                            'end_utc': f'2026-01-01T00:00:{end:02d}+00:00'}))
                paths.append(path)
            with patch.object(wrapper, 'diagnostic_records', return_value=[paths[1]]), patch.object(wrapper.base, 'W', root):
                seconds, evidence = wrapper.clocks(paths + [paths[0]])
            self.assertEqual(seconds, 30)
            self.assertEqual(len(evidence), 2)


if __name__ == '__main__':
    unittest.main()
