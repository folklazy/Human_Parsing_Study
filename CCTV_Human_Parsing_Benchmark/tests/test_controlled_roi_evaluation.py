"""Literal CPU requirements for saved ROI diagnostics and the pending-GT gate."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

P = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(P/'scripts'), str(P.parent/'Human_Parsing_Benchmark/src')]
from controlled_roi_evaluation import project_native, summarize, bound_checkpoint
from controlled_roi_core import counts, face_views, atomic, sha
from selected_part_evaluation import match_gt_to_detector, final_plane_lookup
from common_view.packets import write_packet, read_packet


class SavedROIRequirements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads((P/'configs/CONTROLLED_ROI_SCORING_PROTOCOL.json').read_text())

    def test_complete_native_tables_known_other_and_face_candidate(self):
        c = project_native(np.arange(20, dtype=np.uint8)[None], 'CIHP20', self.protocol)
        s = project_native(np.arange(29, dtype=np.uint8)[None], 'SAPIENS29', self.protocol)
        self.assertEqual(np.flatnonzero(c['Upper']).tolist(), [5, 7])
        self.assertEqual(np.flatnonzero(c['Lower']).tolist(), [9, 12])
        self.assertEqual(np.flatnonzero(s['FaceCandidate']).tolist(), [3, 24, 25, 26, 27, 28])
        for value in c.values(): self.assertFalse(value[0, 6])
        for value in s.values(): self.assertFalse(value[0, 1])
        self.assertFalse(s['FaceCandidate'][0, 10])  # Torso skin is not Neck.

    def test_invalid_IDs_are_not_other(self):
        for native in [np.array([[255]], np.uint8), np.array([[-1]], np.int16)]:
            with self.assertRaises(ValueError): project_native(native, 'CIHP20', self.protocol)

    def test_continuation_inherits_checkpoint_from_hash_bound_parent(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); parent = root/'parent.json'
            atomic(parent, dict(models={'synthetic_model': dict(checkpoint_sha256='weights-digest')}))
            child = dict(models=['synthetic_model'], parent_config='parent.json', parent_config_sha256=sha(parent))
            with patch('controlled_roi_evaluation.W', root):
                self.assertEqual(bound_checkpoint(child, 'synthetic_model'), 'weights-digest')
                with self.assertRaises(ValueError): bound_checkpoint(child, 'unknown_model')
                parent.write_text('{}')
                with self.assertRaises(ValueError): bound_checkpoint(child, 'synthetic_model')

    def test_union_and_full_plane_spill_have_literal_counts(self):
        native = np.array([[5, 7, 6, 5]], np.uint8)
        gt = np.array([[1, 1, 1, 0]], bool)
        row = counts(gt, project_native(native, 'CIHP20', self.protocol)['Upper'])
        self.assertEqual((row['TP'], row['FP'], row['FN'], row['IoU']), (2, 1, 1, .5))

    def test_missing_neck_cannot_be_silently_zero_or_three_target_primary(self):
        rows = [dict(target=t, eligible=True, IoU=1., Dice=1., GT_pixels=1,
                     TP=1, FP=0, FN=0, detector_miss=False) for t in ['Hair', 'Upper', 'Lower']]
        summary = summarize(rows, dict(Hair=1, FaceDomain=0, Upper=1, Lower=1), True, False)
        self.assertIsNone(summary['primary'])
        self.assertIsNone(summary['targets']['FaceDomain']['mean_part_IoU'])
        self.assertEqual(summary['targets']['Hair']['mean_part_IoU'], 1)
        gt = np.array([[1, 0]], bool)
        self.assertEqual(face_views(gt, None, gt)['status'], 'GT_NECK_NOT_READY')

    def test_four_target_aggregation_and_execution_gate_literal(self):
        values = [('Hair', 1), ('Hair', 0), ('FaceDomain', .5), ('Upper', .75), ('Lower', .25)]
        rows = [dict(target=t, IoU=v, Dice=2*v/(1+v), GT_pixels=4,
                     TP=int(4*v), FP=0, FN=4-int(4*v), eligible=True, detector_miss=False) for t, v in values]
        expected = dict(Hair=2, FaceDomain=1, Upper=1, Lower=1)
        self.assertEqual(summarize(rows, expected, True, True)['primary'], .5)
        self.assertIsNone(summarize(rows, expected, False, True)['primary'])
        self.assertIsNone(summarize(rows, dict(expected, Hair=3), True, True)['primary'])

    def test_missed_person_kept_zero_and_ID_renaming(self):
        gt = np.array([[0, 5, 5, 0], [0, 0, 0, 9]], np.uint8)
        ops = [dict(id='detector-A', bbox=[1, 0, 3, 1], score=.8)]
        matched, _ = match_gt_to_detector(gt, ops)
        renamed = np.where(gt == 5, 20, np.where(gt == 9, 2, 0)).astype(np.uint8)
        other, _ = match_gt_to_detector(renamed, ops)
        self.assertEqual((matched[5], matched[9]), ('detector-A', None))
        self.assertEqual((other[20], other[2]), ('detector-A', None))
        self.assertEqual(counts(gt == 9, np.zeros(gt.shape, bool))['IoU'], 0)

    def test_fixed_neck_domain_wrong_person_and_uncertainty(self):
        f = np.array([[1, 1, 0, 0, 0]], bool)
        n = np.array([[0, 0, 1, 0, 0]], bool)
        u = np.array([[0, 0, 0, 1, 0]], bool)
        candidate = np.array([[1, 0, 1, 1, 1]], bool)
        r = face_views(f, n, candidate, u)
        self.assertEqual((r['FaceDomain']['TP'], r['FaceDomain']['FP'], r['FaceDomain']['FN']), (1, 1, 1))
        self.assertEqual(r['FaceDomain']['IoU'], 1/3)
        self.assertEqual(r['FaceNeck']['IoU'], .5)
        self.assertEqual(r['NeckCoverage'], 1)

    def test_actual_packet_to_projection_to_report_and_source_immutability(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            plane = np.array([[[2, 5, 7, 6], [13, 0, 9, 12]]], np.uint8)
            extent = np.ones(plane.shape, bool); scores = np.array([.75], np.float32)
            a = dict(person_semantic_masks=plane, person_extents=extent, person_scores=scores)
            meta = dict(associations=[dict(YOLO_opportunity_id='detector-A', prediction_index=99)])
            packet = write_packet(root, 'synthetic', a, meta, {})
            before = {p.name: sha(p) for p in packet.iterdir()}
            m, arrays = read_packet(packet)
            lookup = final_plane_lookup(m, arrays, dict(masks=extent, scores=scores), [dict(id='detector-A')])
            gt = np.array([[0, 1, 1, 1], [0, 0, 0, 0]], bool)
            prediction = project_native(arrays['person_semantic_masks'][lookup['detector-A']], 'CIHP20', self.protocol)['Upper']
            result = counts(gt, prediction)
            self.assertEqual((result['TP'], result['FP'], result['FN']), (2, 0, 1))
            result['unavailable_primary'] = None
            atomic(root/'REPORT.json', result)
            readback = json.loads((root/'REPORT.json').read_text())
            self.assertEqual(readback['IoU'], 2/3)
            self.assertIsNone(readback['unavailable_primary'])
            self.assertEqual(before, {p.name: sha(p) for p in packet.iterdir()})


if __name__ == '__main__': unittest.main()
