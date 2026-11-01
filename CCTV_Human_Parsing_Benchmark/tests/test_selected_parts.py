"""Hand-calculated requirements; CPU only, no dataset/model dependencies."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

path = Path(__file__).resolve().parents[1] / 'scripts/selected_part_evaluation.py'
spec = importlib.util.spec_from_file_location('selected_parts', path)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class SelectedPartCases(unittest.TestCase):
    def test_spill_is_false_positive_not_ignored(self):
        g = np.array([[1, 1, 0, 0]], bool)
        p = np.array([[1, 0, 1, 1]], bool)
        self.assertEqual(m.counts(g, p), (1, 2, 1))
        self.assertEqual(m.measures(1, 2, 1), dict(IoU=.25, Dice=.4, precision=1/3, recall=.5))

    def test_perfect_wrong_class_empty_and_unsupported(self):
        g = np.array([[1, 1, 0]], bool)
        self.assertEqual(m.measures(*m.counts(g, g))['IoU'], 1)
        for native_plane in [np.array([[0, 0, 0]]), np.array([[2, 2, 0]]), np.array([[5, 5, 0]])]:
            self.assertEqual(m.measures(*m.counts(g, native_plane == 3))['IoU'], 0)
        self.assertIsNone(m.measures(0, 0, 0)['IoU'])
        self.assertIsNone(m.measures(0, 0, 2)['precision'])

    def test_final_association_array_order_not_old_native_index(self):
        planes = np.array([[[1, 0]], [[0, 2]]], dtype=np.uint8)
        a = dict(person_semantic_masks=planes, person_extents=planes > 0, person_scores=np.array([.8, .7]))
        meta = dict(associations=[dict(prediction_index=8, YOLO_opportunity_id='A'), dict(prediction_index=3, YOLO_opportunity_id='B')])
        lookup = m.final_plane_lookup(meta, a, {}, [dict(id='A'), dict(id='B')])
        self.assertEqual(lookup, {'A': 0, 'B': 1})
        # Unannotated B contributes no pixels to the selected A part.
        self.assertEqual(m.counts(np.array([[1, 0]], bool), planes[lookup['A']] == 1), (1, 0, 0))
        meta['associations'][1]['YOLO_opportunity_id'] = 'A'
        with self.assertRaises(ValueError):
            m.final_plane_lookup(meta, a, {}, [dict(id='A')])

    def test_matching_and_gt_id_renaming(self):
        human = np.array([[3, 0, 5, 5], [3, 0, 0, 0]], np.uint8)
        ops = [dict(id='left', bbox=[0, 0, 1, 2], score=.8), dict(id='right', bbox=[2, 0, 4, 1], score=.7)]
        self.assertEqual(m.match_gt_to_detector(human, ops)[0], {3: 'left', 5: 'right'})
        renamed = np.where(human == 3, 9, np.where(human == 5, 1, 0)).astype(np.uint8)
        self.assertEqual(m.match_gt_to_detector(renamed, ops)[0], {9: 'left', 1: 'right'})
        self.assertEqual(m.match_gt_to_detector(human, ops[:1])[0][5], None)

    def test_duplicate_detection_tie_uses_confidence_not_semantics(self):
        h = np.ones((2, 2), np.uint8)
        ops = [dict(id='low', bbox=[0, 0, 2, 2], score=.2), dict(id='high', bbox=[0, 0, 2, 2], score=.8)]
        matched, ties = m.match_gt_to_detector(h, ops)
        self.assertEqual(matched, {1: 'high'}); self.assertEqual(ties, [1])

    def test_sapiens_identity_validation_and_atomic_null(self):
        ext = np.array([[[1, 0]]], bool); scores = np.array([.8])
        a = dict(person_semantic_masks=np.array([[[3, 0]]], np.uint8), person_extents=ext, person_scores=scores)
        self.assertEqual(m.final_plane_lookup(dict(label_space='SAPIENS2_DOME29_PRED'), a,
            dict(masks=ext, scores=scores), [dict(id='A')]), {'A': 0})
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'score.json'; m.atomic(p, m.measures(0, 0, 0))
            self.assertIsNone(json.loads(p.read_text())['IoU'])
            self.assertFalse(p.with_suffix('.json.tmp').exists())

    def test_saved_npz_to_mapping_counts_and_csv_report(self):
        # Original-grid 2x3 fixture. GT Upper has two pixels; prediction adds a
        # third pixel outside GT. Coat7 + Upper5 union must give IoU2/3, Dice4/5.
        w = path.parents[2]
        import sys
        sys.path.insert(0, str(w / 'Human_Parsing_Benchmark/src'))
        from common_view.core import load_spec, project
        from common_view.packets import write_packet, read_packet
        spec = load_spec(w / 'Human_Parsing_Benchmark/protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json')
        native = np.array([[[5, 7, 5], [0, 0, 0]]], np.uint8)
        with tempfile.TemporaryDirectory() as d:
            packet = write_packet(d, 'fixture', dict(person_semantic_masks=native,
                person_extents=native > 0, person_scores=np.array([.9])),
                dict(associations=[dict(prediction_index=7, YOLO_opportunity_id='A')]), {})
            meta, arrays = read_packet(packet)
            lookup = m.final_plane_lookup(meta, arrays, {}, [dict(id='A')])
            pred = project(arrays['person_semantic_masks'][lookup['A']], 'CIHP_GT_AND_NATIVE_PRED', spec) == 3
            gt = np.array([[1, 1, 0], [0, 0, 0]], bool)
            result = m.measures(*m.counts(gt, pred))
            self.assertEqual(result['IoU'], 2/3); self.assertEqual(result['Dice'], .8)
            out = Path(d) / 'report.csv'; m.export_csv(out, [result])
            import csv
            with out.open() as f:
                row = list(csv.DictReader(f))[0]
            self.assertEqual(float(row['IoU']), 2/3)


if __name__ == '__main__':
    unittest.main()
