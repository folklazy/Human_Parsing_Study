"""Literal CPU input/map-back expectations, independent of learned predictions."""
from pathlib import Path
import sys
import unittest
import numpy as np
import torch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sapiens_input_variants import letterbox, restore_letterbox, detector_crop, place_roi


class Normalizer:
    mean = torch.tensor([123.675, 116.28, 103.53]).reshape(3, 1, 1)
    std = torch.tensor([58.395, 57.12, 57.375]).reshape(3, 1, 1)

    def __call__(self, data):
        return {'inputs': ((data['inputs'].float()[[2, 1, 0]] - self.mean) / self.std)[None]}


class InputVariantCases(unittest.TestCase):
    def test_aspect_and_zero_padding(self):
        rgb = np.full((4, 8, 3), [255, 0, 0], np.uint8)
        tensor, geom, preview = letterbox(rgb, Normalizer(), (8, 8))
        self.assertEqual(geom['resized_hw'], [4, 8])
        self.assertEqual(geom['padding_ltrb'], [0, 2, 0, 2])
        self.assertEqual(tuple(tensor.shape), (1, 3, 8, 8))
        self.assertTrue(torch.equal(tensor[:, :, :2], torch.zeros((1, 3, 2, 8))))
        np.testing.assert_array_equal(preview[2:6], rgb)

    def test_remove_padding_logits_before_original_grid_argmax(self):
        geom = dict(input_hw=[8, 8], resized_hw=[4, 8], padding_ltrb=[0, 2, 0, 2], original_hw=[4, 8])
        logits = torch.zeros((1, 29, 8, 8), dtype=torch.float32)
        logits[:, 4, :2] = 50; logits[:, 4, 6:] = 50
        logits[:, 3, 2:6] = 10
        np.testing.assert_array_equal(restore_letterbox(logits, geom), np.full((4, 8), 3, np.uint8))

    def test_roi_original_grid_placement_and_frozen_extent(self):
        rgb = np.zeros((4, 9, 3), np.uint8); extent = np.zeros((4, 9), bool)
        extent[1, 5] = True; extent[2, 6] = True
        crop, box = detector_crop(rgb, [5, 1, 7, 3], extent, context=0)
        self.assertEqual(box, [5, 1, 7, 3]); self.assertEqual(crop.shape, (2, 2, 3))
        raw, owned = place_roi(np.full((2, 2), 23, np.uint8), box, extent)
        expected = np.zeros((4, 9), np.uint8); expected[1, 5] = 23; expected[2, 6] = 23
        np.testing.assert_array_equal(owned, expected)
        self.assertEqual(np.count_nonzero(raw), 4)

    def test_extent_outside_bbox_is_preserved_without_GT(self):
        rgb = np.zeros((5, 9, 3), np.uint8); extent = np.zeros((5, 9), bool); extent[0, 2] = True; extent[3, 7] = True
        _, box = detector_crop(rgb, [4, 1, 6, 3], extent, context=0)
        self.assertEqual(box, [2, 0, 8, 4])

    def test_invalid_labels_nonfinite_and_empty_extent_reject(self):
        with self.assertRaises(ValueError):
            place_roi(np.full((2, 2), 255, np.uint8), [0, 0, 2, 2], np.ones((2, 2), bool))
        with self.assertRaises(ValueError):
            detector_crop(np.zeros((2, 2, 3), np.uint8), [0, 0, 2, 2], np.zeros((2, 2), bool))
        logits = torch.zeros((1, 29, 2, 2)); logits[0, 0, 0, 0] = float('nan')
        with self.assertRaises(ValueError):
            restore_letterbox(logits, {})


if __name__ == '__main__':
    unittest.main()
