"""Inference-only CPI feature-buffer reuse, with unchanged tensor operators.

Adapted source anchors: CPI-Parser d62cae523ba913fec4a7fda5816bc1d96bbf644d.
Copyright 2018-2023 OpenMMLab. Adapted portions: Apache-2.0; see
provenance/licenses/CPI-Parser-APACHE-2.0.txt. Native files stay unchanged.
"""
import hashlib
import inspect
import textwrap
import types

import torch
import torch.nn.functional as F

from .cpi_memory import install as install_restoration

REVISION = 'CPI_FEATURE_BUFFER_REUSE_2'
DYNAMIC_SOURCE_SHA = 'fb9db85455c6bb25c2b19c01454f3911b505cb5f0e9042416a6c6bf259429f30'


def private_dynamic_forward(features, weights, biases, num_instances, extra_relu=False):
    """Native convolutions, reusing only each newly allocated conv result."""
    if torch.is_grad_enabled() or features.ndim != 4 or not weights or len(weights) != len(biases):
        raise ValueError('Private dynamic buffers require nonempty inference convolutions')
    x = features
    for i, (weight, bias) in enumerate(zip(weights, biases)):
        x = F.conv2d(x, weight, bias=bias, stride=1, padding=0, groups=num_instances)
        if i < len(weights) - 1:
            x = F.relu(x, inplace=True)
    if extra_relu:
        x = F.relu(x, inplace=True)
    return x


def install(head, expected_source_sha256, observer=None, reference_prefix=0):
    if head.training:
        raise ValueError('Feature-buffer reuse requires eval mode')
    parsers = [head.cnt_part_parser, head.cxt_part_parser]
    for parser in parsers:
        if (len(parser) != 3 or not isinstance(parser[0], torch.nn.Conv2d)
                or not isinstance(parser[1], torch.nn.ReLU)
                or not isinstance(parser[2], torch.nn.Conv2d)):
            raise ValueError('Expected private Conv2d-ReLU-Conv2d intermediates')
        if any(m._forward_hooks or m._forward_pre_hooks or m._backward_hooks for m in parser.modules()):
            raise ValueError('Hooked intermediates cannot be reused safely')
    original = type(head).casual_head_forward
    with open(inspect.getsourcefile(original), 'rb') as stream:
        if hashlib.sha256(stream.read()).hexdigest() != expected_source_sha256:
            raise ValueError('Native feature source binding differs')
    caller = inspect.getsource(type(head)._get_bboxes_single)
    call = 'cnt_preds, cxt_preds, _, _ = self.casual_head_forward([det_params], parse_feat, part_labels, det_center)'
    if caller.count(call) != 1:
        raise ValueError('Inference caller must explicitly discard returned features')
    source = textwrap.dedent(inspect.getsource(original))
    dynamic_source = inspect.getsource(original.__globals__['dynamic_forward'])
    if hashlib.sha256(dynamic_source.encode()).hexdigest() != DYNAMIC_SOURCE_SHA:
        raise ValueError('Native dynamic-convolution source binding differs')
    replacements = [
        ('    parse_feats = torch.cat(parse_feats_list, 1)',
         '    parse_feats = torch.cat(parse_feats_list, 1)\n    del parse_feats_list'),
        ('    inst_preds = F.conv2d(inst_feats,',
         '    del parse_feats\n    inst_preds = F.conv2d(inst_feats,'),
        ('    cnt_embed = cnt_embed / normalizer[:, : ,None]',
         '    cnt_embed = cnt_embed / normalizer[:, : ,None]\n    del cnt_masks, normalizer'),
        ('    inst_part_feats = inst_part_feats.reshape(1, -1, H, W)',
         '    inst_part_feats = inst_part_feats.reshape(1, -1, H, W)\n    del inst_feats'),
        ('    cxt_feats = dynamic_forward(\n        inst_part_feats, cxt_weights, cxt_bias, total_pos_num * C, extra_relu=True)',
         '    cxt_feats = dynamic_forward(\n        inst_part_feats, cxt_weights, cxt_bias, total_pos_num * C, extra_relu=True)\n    del inst_part_feats'),
        ('    cnt_preds = self.cnt_part_parser(cnt_feats.view(N, -1, H, W))',
         '    cnt_preds = self.cnt_part_parser(cnt_feats.view(N, -1, H, W))\n    del cnt_feats'),
        ('    cxt_preds = self.cxt_part_parser(cxt_feats.view(N, -1, H, W))',
         '    cxt_preds = self.cxt_part_parser(cxt_feats.view(N, -1, H, W))\n    del cxt_feats'),
        ('    return cnt_preds, cxt_preds, cnt_feats, cxt_feats',
         '    return cnt_preds, cxt_preds, None, None'),
    ]
    patched = source
    for before, after in replacements:
        if patched.count(before) != 1:
            raise ValueError('Native feature liveness anchor changed: ' + before)
        patched = patched.replace(before, after)
    namespace = dict(original.__globals__)
    namespace['dynamic_forward'] = private_dynamic_forward
    exec(compile(patched, '<CPI-inference-feature-buffer-reuse-revision2>', 'exec'), namespace)
    compiled = namespace[original.__name__]

    def feature_forward(self, pos_params_list, parse_feats, parse_labels, centers=None):
        if self.training or torch.is_grad_enabled():
            raise ValueError('Feature-buffer reuse is inference-only, never training/autograd')
        if parse_feats.dtype != torch.float32:
            raise ValueError('FP32 feature contract required')
        count = sum(v.shape[0] for v in pos_params_list)
        channels, height, width = parse_feats.shape[-3:]
        self._cpi_feature_memory_last = {
            'candidate_count': count, 'feature_channels': channels,
            'feature_hw': [height, width], 'parts': self.num_parse_classes - 1,
            'one_expanded_part_buffer_bytes': count * (self.num_parse_classes - 1) * channels * height * width * parse_feats.element_size(),
            'relu_private_buffer_reuse': True, 'discarded_return_features': True,
            'same_operator_shapes_and_order': True}
        return compiled(self, pos_params_list, parse_feats, parse_labels, centers)

    def observe(event):
        event = dict(event, feature_memory=dict(head._cpi_feature_memory_last))
        observer(event)

    receipt = install_restoration(head, expected_source_sha256,
                                  observer=observe if observer else None,
                                  reference_prefix=reference_prefix)
    for parser in parsers:
        parser[1].inplace = True  # Only the private first-convolution output.
    head.casual_head_forward = types.MethodType(feature_forward, head)
    return {'revision': REVISION, 'original_head_sha256': expected_source_sha256,
            'restoration': receipt,
            'feature_original_method_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'feature_expanded_method_sha256': hashlib.sha256(patched.encode()).hexdigest(),
            'native_dynamic_forward_sha256': DYNAMIC_SOURCE_SHA,
            'dynamic_convolution_relu_private_buffer_reuse': True,
            'released_dead_buffers': ['parse_feats_list', 'parse_feats', 'cnt_masks',
                                      'normalizer', 'inst_feats', 'inst_part_feats',
                                      'cnt_feats', 'cxt_feats'],
            'part_parser_relu_inplace': True, 'returned_unused_features': None,
            'source_file_modified': False, 'scientific_parameters_changed': [],
            'training_and_autograd': 'REJECTED'}
