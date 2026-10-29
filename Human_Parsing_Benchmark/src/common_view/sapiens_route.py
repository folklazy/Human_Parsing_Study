"""Full-frame Sapiens semantic output with frozen YOLO identity, no native IDs.

Torch/native APIs are imported only when explicitly invoked. CPU probes do not
instantiate the model or perform a forward pass.
"""
from pathlib import Path
import numpy as np
from .core import validate_prediction


def make_cpu_pipeline(config_path):
    from sapiens.engine.config import Config
    from sapiens.engine.datasets import Compose
    from sapiens.registry import MODELS
    import sapiens.dense  # registers existing pinned source; no model instantiated
    cfg = Config.fromfile(str(config_path))
    if cfg.num_classes != 29 or cfg.image_size != (1024, 768):
        raise ValueError('Wrong task/size class contract')
    if cfg.test_pipeline[0] != dict(type='SegResize', height=1024, width=768,
                                    keep_ratio=False, test_mode=True):
        raise ValueError('Native resize contract changed')
    return cfg, Compose(cfg.test_pipeline), MODELS.build(cfg.data_preprocessor)


def prepare_rgb(rgb, pipeline, preprocessor):
    import torch
    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError('uint8 RGB input required')
    bgr = rgb[:, :, ::-1].copy()
    result = pipeline(dict(img=bgr))
    tensor = preprocessor(result)['inputs'].float()
    if tuple(tensor.shape) != (1, 3, 1024, 768) or tensor.dtype != torch.float32:
        raise ValueError('Preprocessing shape/dtype mismatch')
    geometry = {'original_wh': [rgb.shape[1], rgb.shape[0]], 'input_hw': [1024, 768],
                'crop': None, 'padding': [0, 0, 0, 0], 'resize': 'STRETCH',
                'source_input_channels': 'BGR', 'model_channels': 'RGB',
                'mean': [123.675, 116.28, 103.53], 'std': [58.395, 57.12, 57.375],
                'keep_ratio': False, 'pad_size_divisor': preprocessor.pad_size_divisor,
                'map_back': 'BILINEAR_ALIGN_CORNERS_FALSE_THEN_NATIVE29_ARGMAX'}
    if preprocessor.pad_size_divisor != 1:
        raise ValueError('Unexpected padding configuration')
    return tensor, geometry


def logits_to_native(logits, original_hw):
    import torch
    if logits.ndim != 4 or logits.shape[:2] != (1, 29) or logits.dtype != torch.float32:
        raise ValueError('Native29 FP32 logits required')
    if not torch.isfinite(logits).all():
        raise ValueError('Nonfinite logits')
    mapped = torch.nn.functional.interpolate(logits, size=original_hw,
                                             mode='bilinear', align_corners=False)
    mask = mapped.argmax(1)[0].cpu().numpy().astype(np.uint8)
    if tuple(mask.shape) != tuple(original_hw):
        raise ValueError('Original-grid restoration failed')
    return mask


def ownership_planes(native, extents, scores):
    extents = np.asarray(extents)
    if native.ndim != 2 or native.dtype != np.uint8 or np.any(native >= 29):
        raise ValueError('Native29 original-grid plane required')
    planes = np.where(extents, native, 0).astype(np.uint8)
    validate_prediction(planes, extents, scores, native.shape, 'SAPIENS2_DOME29_PRED')
    return {'native_full_frame_semantic_mask': native,
            'person_semantic_masks': planes, 'person_extents': extents,
            'person_scores': np.asarray(scores, np.float32)}
