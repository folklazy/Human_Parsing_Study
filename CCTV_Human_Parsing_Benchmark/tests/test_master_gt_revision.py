"""Literal expected geometry/ownership cases; no dataset or model imports."""
import copy
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_master_gt_revision import correct_owners, raster_candidates


def shape(label, pid, points):
    return dict(label=label, group_id=pid, points=points, shape_type="polygon",
                attributes={"cihp_equivalent_classes": [5, 6, 7, 10, 11, 12]})


class MasterGTRevisionAcceptance(unittest.TestCase):
    def annotation(self, shapes):
        return dict(imageWidth=8, imageHeight=5, shapes=shapes)

    def test_known_owner_repair_preserves_vertices_and_source(self):
        points = [[0, 0], [1, 0], [1, 1], [0, 1]]
        source = self.annotation([shape("person", 1, points), shape("face", 2, points)])
        before = copy.deepcopy(source)
        canonical = dict(shapes=[dict(label="p2_face", points=points)])
        out, changes = correct_owners(source, canonical, [dict(shape_index=0, source_label="p2_face",
            proposed_label="p1_face", issue_id="TEST")])
        self.assertEqual(source, before)
        self.assertEqual(out["shapes"][1]["group_id"], 1)
        self.assertEqual(out["shapes"][1]["points"], points)
        self.assertFalse(changes[0]["vertices_changed"])

    def test_geometry_drift_refuses_historical_correction(self):
        a = self.annotation([shape("hair", 1, [[0, 0], [1, 0], [0, 1]])])
        with self.assertRaises(ValueError):
            correct_owners(a, dict(shapes=[dict(label="p1_hair", points=[[0, 0], [2, 0], [0, 1]])]), [])

    def test_extent_is_not_semantic_union_and_unknown_is_not_background(self):
        a = self.annotation([shape("person", 1, [[0, 0], [2, 0], [2, 2], [0, 2]]),
                             shape("hair", 1, [[0, 0], [1, 0], [1, 1], [0, 1]])])
        out, _ = raster_candidates(a)
        self.assertEqual(int(out["person_masks"].sum()), 9)
        self.assertEqual(int(out["part_masks"].sum()), 4)
        self.assertEqual(out["semantic_candidate"][0, 0], 2)
        self.assertEqual(out["semantic_candidate"][2, 2], 255)
        self.assertEqual(out["semantic_candidate"][4, 7], 255)

    def test_multiple_components_union_and_ambiguous_overlap(self):
        a = self.annotation([shape("person", 1, [[0, 0], [1, 0], [1, 1], [0, 1]]),
            shape("person", 1, [[4, 0], [5, 0], [5, 1], [4, 1]]),
            shape("person", 2, [[1, 0], [2, 0], [2, 1], [1, 1]])])
        out, _ = raster_candidates(a)
        self.assertEqual([int(m.sum()) for m in out["person_masks"]], [8, 4])
        self.assertEqual(int(out["person_overlap"].sum()), 2)
        self.assertEqual(out["person_id_candidate"][0, 1], 255)
        self.assertEqual(out["person_id_candidate"][0, 4], 1)
        self.assertEqual(out["part_masks"].shape, (0, 5, 8))

    def test_overlapping_targets_not_resolved_by_last_shape(self):
        square = [[0, 0], [1, 0], [1, 1], [0, 1]]
        a = self.annotation([shape("person", 1, square), shape("hair", 1, square), shape("face", 1, square)])
        out, _ = raster_candidates(a)
        self.assertEqual(int(out["semantic_overlap"].sum()), 4)
        self.assertEqual(out["semantic_candidate"][0, 0], 255)
        self.assertEqual(out["part_masks"].shape[0], 2)

    def test_parts_outside_extent_are_preserved_for_review(self):
        a = self.annotation([shape("person", 1, [[0, 0], [1, 0], [1, 1], [0, 1]]),
            shape("hair", 1, [[4, 0], [5, 0], [5, 1], [4, 1]])])
        out, outside = raster_candidates(a)
        self.assertEqual(outside, 4)
        self.assertEqual(int(out["part_masks"].sum()), 4)
        self.assertEqual(out["person_id_candidate"][0, 4], 0)

    def test_bbox_is_not_a_person_silhouette(self):
        a = self.annotation([dict(label="bbox", group_id=1, points=[[0, 0], [8, 5]], shape_type="rectangle")])
        with self.assertRaises(ValueError):
            raster_candidates(a)

    def test_unknown_id_or_unknown_label_fails_contract(self):
        square = [[0, 0], [1, 0], [1, 1], [0, 1]]
        for label, pid in [("hair", 2), ("mystery", 1)]:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    raster_candidates(self.annotation([shape("person", 1, square), shape(label, pid, square)]))


if __name__ == "__main__":
    unittest.main()
