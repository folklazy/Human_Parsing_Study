"""Targeted controls: effective identity and complete resource clocks."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_cpi_chunked_continuation as wrapper


class ChunkedControls(unittest.TestCase):
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
