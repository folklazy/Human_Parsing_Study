"""Bound CPI mask-restoration memory along the independent person axis.

No learned weights, detections, channels, spatial sizes or interpolation settings
change. Native source stays on disk unchanged; installation is model-local.
"""
# Native restoration/anchor adapted from HAG-uestc/CPI-Parser, revision
# d62cae523ba913fec4a7fda5816bc1d96bbf644d, causal_parser_head.py/parser_misc.py.
# Copyright 2018-2023 OpenMMLab. Apache-2.0 terms for these adapted portions:
# ../../provenance/licenses/CPI-Parser-APACHE-2.0.txt (from project root).
import hashlib
import inspect
import textwrap
import types

import numpy as np
import torch
import torch.nn.functional as F


def restore(logits, stride, image_shape, original_shape, rescale, aligned):
    """The native restoration operations, with their original order/settings."""
    if rescale:
        logits = aligned(logits, stride)
        logits = logits[:, :, :image_shape[0], :image_shape[1]]
        if original_shape[0] > 2500 or original_shape[1] > 2500:
            logits = logits.cpu()  # Preserve the existing native branch.
        logits = F.interpolate(logits, size=tuple(original_shape[:2]),
                               mode='bilinear', align_corners=True)
    return logits


def chunked_maps(logits, stride, image_shape, original_shape, rescale, aligned,
                 chunk_size=1, observer=None, reference_prefix=0):
    if logits.ndim != 4 or logits.dtype != torch.float32 or chunk_size < 1:
        raise ValueError('FP32 NCHW logits and a positive person chunk required')
    count, classes, height, width = logits.shape
    if classes != 20:
        raise ValueError('CIHP native20 channel contract required')
    output_hw = tuple(original_shape[:2]) if rescale else (height, width)
    maps = np.empty((count, *output_hw), dtype=np.int64)
    for begin in range(0, count, chunk_size):
        end = min(begin + chunk_size, count)
        restored = restore(logits[begin:end], stride, image_shape, original_shape,
                           rescale, aligned)
        maps[begin:end] = restored.argmax(dim=1).cpu().numpy()
        del restored
    prefix = min(reference_prefix, count)
    if prefix:
        # Bounded actual-input check against native all-person processing of a
        # fixed prefix, never a quality/GT-dependent choice.
        expected = restore(logits[:prefix], stride, image_shape, original_shape,
                           rescale, aligned).argmax(dim=1).cpu().numpy()
        if not np.array_equal(expected, maps[:prefix]):
            raise ValueError('Native-vs-chunked restoration label mismatch')
    if observer is not None:
        observer({'low_resolution_shape': list(logits.shape),
                  'image_shape': list(image_shape), 'original_shape': list(original_shape),
                  'person_chunk_size': chunk_size, 'rescale': bool(rescale),
                  'aligned_stride': int(stride), 'output_shape': list(maps.shape),
                  'native_reference_prefix': prefix, 'reference_labels_equal': True if prefix else None,
                  'full_stride_grid_float_bytes': count * classes * height * stride * width * stride * 4,
                  'chunk_stride_grid_float_bytes': min(chunk_size, count) * classes * height * stride * width * stride * 4})
    return maps


def install(head, expected_source_sha256, observer=None, reference_prefix=0):
    original = type(head)._get_bboxes_single
    source_file = inspect.getsourcefile(original)
    with open(source_file, 'rb') as stream:
        digest = hashlib.sha256(stream.read()).hexdigest()
    if digest != expected_source_sha256:
        raise ValueError('CPI head source binding differs; patch not installed')
    source = textwrap.dedent(inspect.getsource(original))
    begin = source.index('        if rescale:\n            parsing_logits = aligned_bilinear(')
    last = '        parsing_maps = parsing_maps.cpu().numpy()'
    end = source.index(last, begin) + len(last)
    old = source[begin:end]
    expected = '''        if rescale:
            parsing_logits = aligned_bilinear(parsing_logits, self.parse_logit_stride)
            parsing_logits = parsing_logits[:, :, :img_shape[0], :img_shape[1]]
            if ori_shape[0] > 2500 or ori_shape[1] > 2500:
                parsing_logits = parsing_logits.cpu()
            parsing_logits = F.interpolate(
                parsing_logits,
                size=(ori_shape[0], ori_shape[1]),
                mode='bilinear',
                align_corners=True)
        parsing_maps = parsing_logits.argmax(dim=1)
        parsing_maps = parsing_maps.cpu().numpy()'''
    if old != expected:
        raise ValueError('Native restoration anchor differs; patch not installed')
    replacement = '''        parsing_maps = _cpi_chunked_maps(
            parsing_logits, self.parse_logit_stride, img_shape, ori_shape,
            rescale, aligned_bilinear, chunk_size=1,
            observer=_cpi_memory_observer, reference_prefix=_cpi_reference_prefix)'''
    patched = source[:begin] + replacement + source[end:]
    namespace = dict(original.__globals__)
    namespace.update(_cpi_chunked_maps=chunked_maps, _cpi_memory_observer=observer,
                     _cpi_reference_prefix=reference_prefix)
    exec(compile(patched, '<CPI-person-chunk-restoration-revision1>', 'exec'), namespace)
    head._get_bboxes_single = types.MethodType(namespace[original.__name__], head)
    return {'revision': 'CPI_PERSON_CHUNK_RESTORATION_1',
            'original_head_sha256': digest,
            'original_method_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'expanded_method_sha256': hashlib.sha256(patched.encode()).hexdigest(),
            'person_chunk_size': 1, 'native_reference_prefix': reference_prefix,
            'source_file_modified': False, 'scientific_parameters_changed': []}
