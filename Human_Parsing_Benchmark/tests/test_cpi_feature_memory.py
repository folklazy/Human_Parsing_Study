"""Actual pinned native feature forward as independent numeric reference."""
from pathlib import Path
import hashlib
import sys
import unittest
from unittest.mock import patch

import torch

P = Path(__file__).resolve().parents[1]
W = P.parent
sys.path.insert(0, str(P / 'src'))
sys.path.insert(0, str(W / 'third_party/human_parsing/CPI-Parser'))
from mmcv import Config
from mmdet.models.builder import build_head
from cihp_benchmark.cpi_feature_memory import install

torch.set_num_threads(4)
HEAD_SHA = hashlib.sha256((W / 'third_party/human_parsing/CPI-Parser/mmdet/models/dense_heads/causal_parser_head.py').read_bytes()).hexdigest()


def make_head():
    cfg = Config.fromfile(str(W / 'third_party/human_parsing/CPI-Parser/configs/COSParser/causal_parser_r50_inter_8_135k_cihp.py'))
    head = cfg.model.bbox_head.copy()
    head['train_cfg'] = None  # Match init_detector's inference construction.
    head['test_cfg'] = cfg.model.test_cfg
    model = build_head(head).float().eval()
    torch.nn.init.zeros_(model.part_bias)  # Native constructor leaves it uninitialized until checkpoint load.
    return model


class FeatureBufferAcceptance(unittest.TestCase):
    def test_exact_predictions_inputs_and_parameters(self):
        head = make_head()
        generator = torch.Generator().manual_seed(91)
        features = torch.randn((1, head.parse_head_channels, 3, 5), generator=generator)
        parameters = torch.randn((3, head.total_params), generator=generator) * .01
        labels = torch.ones((3, 19), dtype=torch.bool)
        labels[1] = False  # Native all-invalid context-attention case.
        centers = torch.tensor([[3., 7.], [17., 5.], [9., 11.]])
        snapshots = [v.clone() for v in [features, parameters, labels, centers]]
        pointers = [v.data_ptr() for v in head.parameters()]
        # Native CPU torch.cat chooses channels_last for these coordinate views,
        # while the next native view requires contiguous storage for N>1. Copy
        # coordinates only (same values) for both CPU reference and candidate.
        # GPU diagnostic separately checks the unmodified native CUDA function.
        original = type(head).casual_head_forward
        coordinates = original.__globals__['relative_coordinate_maps']
        def cpu_coordinates(*args, **kwargs):
            return coordinates(*args, **kwargs).contiguous()
        with patch.dict(original.__globals__, relative_coordinate_maps=cpu_coordinates), torch.no_grad():
            expected = head.casual_head_forward([parameters], features, labels, centers)
            self.assertIsNotNone(expected[2])
            install(head, HEAD_SHA)
            actual = head.casual_head_forward([parameters], features, labels, centers)
        self.assertTrue(torch.equal(expected[0], actual[0]))
        self.assertTrue(torch.equal(expected[1], actual[1]))
        self.assertEqual(actual[2:], (None, None))
        for old, new in zip(snapshots, [features, parameters, labels, centers]):
            self.assertTrue(torch.equal(old, new))
        self.assertEqual(pointers, [v.data_ptr() for v in head.parameters()])

    def test_training_or_autograd_are_rejected(self):
        head = make_head(); install(head, HEAD_SHA)
        head.train()
        with torch.no_grad(), self.assertRaises(ValueError):
            head.casual_head_forward([], torch.empty(0), torch.empty(0))
        head.eval()
        with torch.enable_grad(), self.assertRaises(ValueError):
            head.casual_head_forward([], torch.empty(0), torch.empty(0))

    def test_shared_or_changed_intermediates_are_rejected(self):
        head = make_head()
        head.cnt_part_parser[1] = torch.nn.LeakyReLU()
        with self.assertRaises(ValueError):
            install(head, HEAD_SHA)
        head = make_head()
        handle = head.cnt_part_parser[0].register_forward_hook(lambda *args: None)
        with self.assertRaises(ValueError):
            install(head, HEAD_SHA)
        handle.remove()


if __name__ == '__main__':
    unittest.main()
