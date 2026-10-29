"""Independent native-operation reference and asymmetric hard-label oracles."""
# native_aligned mirrors CPI-Parser parser_misc.py at d62cae523ba913fec4a7fda5816bc1d96bbf644d.
# Copyright 2018-2023 OpenMMLab; Apache-2.0, see provenance/licenses/CPI-Parser-APACHE-2.0.txt.
from pathlib import Path
import sys
import unittest

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from cihp_benchmark.cpi_memory import chunked_maps


def native_aligned(x, factor):
    if factor == 1:
        return x
    height, width = x.shape[-2:]
    x = F.pad(x, (0, 1, 0, 1), mode='replicate')
    x = F.interpolate(x, size=(factor * height + 1, factor * width + 1),
                      mode='bilinear', align_corners=True)
    x = F.pad(x, (factor // 2, 0, factor // 2, 0), mode='replicate')
    return x[:, :, :factor * height, :factor * width]


class CPIChunkAcceptance(unittest.TestCase):
    def test_asymmetric_literal_labels_and_ties(self):
        x = torch.full((2, 20, 2, 3), -5.)
        for person in range(2):
            for y in range(2):
                for col in range(3):
                    x[person, person * 6 + y * 3 + col, y, col] = 10
        actual = chunked_maps(x, 1, (2, 3, 3), (2, 3, 3), False, native_aligned)
        np.testing.assert_array_equal(actual, [[[0, 1, 2], [3, 4, 5]], [[6, 7, 8], [9, 10, 11]]])
        x.zero_()
        self.assertTrue((chunked_maps(x, 1, (2, 3), (2, 3), False, native_aligned) == 0).all())

    def test_native_operations_preserve_all_persons_and_geometry(self):
        generator = torch.Generator().manual_seed(719)
        x = torch.rand((7, 20, 3, 5), generator=generator)
        # Reference states native operations directly, without production restore.
        expected = native_aligned(x, 8)[:, :, :21, :37]
        expected = F.interpolate(expected, size=(17, 43), mode='bilinear', align_corners=True)
        for size in (1, 2, 5):
            actual = chunked_maps(x, 8, (21, 37, 3), (17, 43, 3), True,
                                  native_aligned, chunk_size=size)
            np.testing.assert_array_equal(actual, expected.argmax(1).numpy())

    def test_native_large_original_cpu_branch_and_empty(self):
        x = torch.zeros((1, 20, 1, 2)); x[:, 13] = 1
        actual = chunked_maps(x, 1, (1, 2), (1, 2501), True, native_aligned)
        self.assertEqual(actual.shape, (1, 1, 2501))
        self.assertTrue((actual == 13).all())
        empty = chunked_maps(torch.empty((0, 20, 2, 3)), 8, (16, 24), (7, 11), True, native_aligned)
        self.assertEqual(empty.shape, (0, 7, 11))

    def test_contract_and_no_input_mutation(self):
        x = torch.randn((3, 20, 2, 4)); saved = x.clone(); observed = []
        chunked_maps(x, 2, (3, 7), (5, 9), True, native_aligned,
                     observer=observed.append, reference_prefix=2)
        self.assertTrue(torch.equal(x, saved))
        self.assertTrue(observed[0]['reference_labels_equal'])
        self.assertEqual(observed[0]['full_stride_grid_float_bytes'], 3 * observed[0]['chunk_stride_grid_float_bytes'])
        with self.assertRaises(ValueError):
            chunked_maps(x.double(), 1, (2, 4), (2, 4), False, native_aligned)
        with self.assertRaises(ValueError):
            chunked_maps(x[:, :19], 1, (2, 4), (2, 4), False, native_aligned)


if __name__ == '__main__':
    unittest.main()
