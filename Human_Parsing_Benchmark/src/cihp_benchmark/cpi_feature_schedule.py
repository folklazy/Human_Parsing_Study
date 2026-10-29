"""Schedule independent content/context branches with identical operator shapes.

Native source anchors adapted from CPI-Parser d62cae523ba913fec4a7fda5816bc1d96bbf644d,
copyright 2018-2023 OpenMMLab, Apache-2.0. See provenance/licenses/CPI-Parser-APACHE-2.0.txt.
"""
import hashlib
import inspect
import textwrap
import types

import torch

from .cpi_feature_memory import install as install_buffers, private_dynamic_forward

REVISION = 'CPI_FEATURE_BRANCH_SCHEDULE_3'


def install(head, expected_source_sha256, observer=None, reference_prefix=0):
    receipt = install_buffers(head, expected_source_sha256, observer, reference_prefix)
    original = type(head).casual_head_forward
    source = textwrap.dedent(inspect.getsource(original))
    patched = source
    for before, after in [
        ('    parse_feats = torch.cat(parse_feats_list, 1)',
         '    parse_feats = torch.cat(parse_feats_list, 1)\n    del parse_feats_list'),
        ('    inst_preds = F.conv2d(inst_feats,', '    del parse_feats\n    inst_preds = F.conv2d(inst_feats,'),
        ('    cnt_embed = cnt_embed / normalizer[:, : ,None]',
         '    cnt_embed = cnt_embed / normalizer[:, : ,None]\n    del cnt_masks, normalizer'),
    ]:
        if patched.count(before) != 1:
            raise ValueError('Native prefix liveness anchor differs')
        patched = patched.replace(before, after)
    begin = patched.index('    inst_part_feats = inst_feats[:, None, ...].repeat(1, C, 1, 1, 1)')
    end = patched.index('    return cnt_preds, cxt_preds, cnt_feats, cxt_feats', begin)
    end += len('    return cnt_preds, cxt_preds, cnt_feats, cxt_feats')
    scheduled = '''    inst_part_feats = inst_feats[:, None, ...].repeat(1, C, 1, 1, 1)
    inst_part_feats = inst_part_feats.reshape(1, -1, H, W)
    cnt_feats = dynamic_forward(
        inst_part_feats, cnt_weights, cnt_bias, total_pos_num * C, extra_relu=True)
    del inst_part_feats
    cnt_preds = self.cnt_part_parser(cnt_feats.view(N, -1, H, W))
    del cnt_feats

    # Recreate the same copied input: no extra learned/numerical transform.
    inst_part_feats = inst_feats[:, None, ...].repeat(1, C, 1, 1, 1)
    inst_part_feats = inst_part_feats.reshape(1, -1, H, W)
    del inst_feats
    cxt_feats = dynamic_forward(
        inst_part_feats, cxt_weights, cxt_bias, total_pos_num * C, extra_relu=True)
    del inst_part_feats
    cxt_preds = self.cxt_part_parser(cxt_feats.view(N, -1, H, W))
    del cxt_feats
    cnt_preds = torch.cat([inst_preds, cnt_preds], dim=1)
    cxt_preds = torch.cat([inst_preds, cxt_preds], dim=1)
    return cnt_preds, cxt_preds, None, None'''
    patched = patched[:begin] + scheduled + patched[end:]
    namespace = dict(original.__globals__, dynamic_forward=private_dynamic_forward)
    exec(compile(patched, '<CPI-independent-feature-branches-revision3>', 'exec'), namespace)
    compiled = namespace[original.__name__]

    def forward(self, pos_params_list, parse_feats, parse_labels, centers=None):
        if self.training or torch.is_grad_enabled() or parse_feats.dtype != torch.float32:
            raise ValueError('FP32 eval/no_grad inference only')
        count = sum(p.shape[0] for p in pos_params_list)
        channels, height, width = parse_feats.shape[-3:]
        self._cpi_feature_memory_last = {
            'candidate_count': count, 'feature_channels': channels, 'feature_hw': [height, width],
            'parts': self.num_parse_classes - 1,
            'one_expanded_part_buffer_bytes': count * (self.num_parse_classes - 1) * channels * height * width * 4,
            'independent_branches_scheduled_serially': True, 'input_copy_recreated': True,
            'convolution_shapes_unchanged': True, 'within_branch_operator_order_unchanged': True}
        return compiled(self, pos_params_list, parse_feats, parse_labels, centers)

    head.casual_head_forward = types.MethodType(forward, head)
    return dict(receipt, revision=REVISION, buffer_reuse_revision=receipt['revision'],
                scheduled_method_sha256=hashlib.sha256(patched.encode()).hexdigest(),
                branch_schedule='content fully consumed/freed before context; same all-candidate tensors',
                recreated_input='repeat of unchanged inst_feats, no additional float operations')
