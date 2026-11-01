"""Independent literal expectations for new ROI/domain/packet contracts."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from types import SimpleNamespace
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(P/'scripts'), str(P.parent/'Human_Parsing_Benchmark/src')]
from controlled_roi_core import select_instance, place, validate_native, counts, face_views, macro_four, reconcile, atomic, letterbox_canvas
from common_view.packets import write_packet, read_packet


class ControlledROICases(unittest.TestCase):
    def test_face_neck_fixed_domain_literal_100_25(self):
        f = np.zeros((5, 30), bool); f.ravel()[:100] = True
        n = np.zeros_like(f); n.ravel()[100:125] = True
        first, second = face_views(f, n, f), face_views(f, n, f | n)
        self.assertEqual(first['FaceDomain']['IoU'], 1)
        self.assertEqual(second['FaceDomain']['IoU'], 1)
        self.assertEqual(first['FaceNeck']['IoU'], .8)
        self.assertEqual(second['FaceNeck']['IoU'], 1)
        leaked = np.ones_like(f)
        self.assertEqual(face_views(f, n, leaked)['FaceDomain']['FP'], 25)
        self.assertEqual(face_views(f, n, leaked)['FaceDomain']['IoU'], .8)
        self.assertIsNone(face_views(f, None, f)['FaceDomain'])

    def test_wrong_person_not_hidden_by_other_person_neck(self):
        f = np.array([[1, 0, 0, 0]], bool); own_n = np.array([[0, 1, 0, 0]], bool)
        wrong = np.array([[0, 0, 1, 1]], bool)
        r = face_views(f, own_n, wrong)['FaceDomain']
        self.assertEqual((r['TP'], r['FP'], r['FN']), (0, 2, 1))

    def test_union_before_counts_other_fp_fn_and_empty(self):
        native = np.array([[5, 7, 6, 0]], np.uint8)
        g = np.array([[1, 1, 1, 0]], bool)
        r = counts(g, np.isin(native, [5, 7]))
        self.assertEqual((r['TP'], r['FP'], r['FN'], r['IoU']), (2, 0, 1, 2/3))
        self.assertEqual(counts(g, np.zeros_like(g))['IoU'], 0)
        self.assertIsNone(counts(np.zeros_like(g), np.zeros_like(g))['IoU'])

    def test_assignment_uses_iou_not_semantics_and_tie_confidence(self):
        boxes = [[0, 0, 2, 2], [0, 0, 2, 2], [8, 8, 9, 9]]
        self.assertEqual(select_instance(boxes, [.2, .9, 1], [0, 0, 2, 2])[0], 1)
        self.assertIsNone(select_instance(boxes, [.2, .9, 1], [4, 4, 5, 5])[0])
        self.assertEqual(select_instance([], [], [0, 0, 2, 2]), (None, []))

    def test_original_grid_asymmetric_placement_and_ownership(self):
        mask = np.array([[2, 5, 7], [13, 9, 12]], np.uint8)
        extent = np.zeros((5, 8), bool); extent[1, 4] = True; extent[2, 5] = True
        raw, owned = place(mask, [3, 1, 6, 3], extent, 20)
        self.assertEqual((raw[1, 3], raw[2, 5], owned[1, 4], owned[2, 5]), (2, 12, 5, 12))
        self.assertEqual(int((owned != 0).sum()), 2)
        with self.assertRaises(ValueError):
            validate_native(np.array([[255]], np.uint8), 29, (1, 1))
        with self.assertRaises(ValueError):
            validate_native(np.array([[29]], np.uint8), 29, (1, 1))

    def test_actual_atomic_packet_to_face_scorer_to_reporter(self):
        face = np.array([[1, 1, 0, 0]], bool); neck = np.array([[0, 0, 1, 0]], bool)
        with tempfile.TemporaryDirectory() as td:
            mask = np.array([[[3, 24, 3, 23]]], np.uint8)
            q = write_packet(Path(td)/'packets', 'fixture', dict(person_semantic_masks=mask), dict(protocol='controlled-fixture'), {})
            meta, arr = read_packet(q)
            scores = face_views(face, neck, np.isin(arr['person_semantic_masks'][0], [3, 24, 25, 26, 27, 28]))
            atomic(Path(td)/'REPORT.json', dict(primary=scores['FaceDomain']['IoU'], missing_target=None))
            report = json.loads((Path(td)/'REPORT.json').read_text())
            self.assertEqual(report['primary'], 1)
            self.assertIsNone(report['missing_target'])
            self.assertEqual(meta['protocol'], 'controlled-fixture')

    def test_lossless_RGB_round_trip(self):
        a = np.array([[[255, 13, 2], [4, 31, 200]], [[77, 9, 111], [1, 2, 3]]], np.uint8)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'crop.png'; Image.fromarray(a).save(p)
            np.testing.assert_array_equal(np.asarray(Image.open(p).convert('RGB')), a)

    def test_asymmetric_letterbox_mean_padding_without_second_crop(self):
        rgb=np.full((2,4,3),[251,13,29],np.uint8)
        canvas,g=letterbox_canvas(rgb,(4,4),[100.,110.,120.])
        self.assertEqual(g['resized_hw'],[2,4])
        self.assertEqual(g['padding_ltrb'],[0,1,0,1])
        np.testing.assert_array_equal(canvas[1:3],rgb)
        np.testing.assert_array_equal(canvas[0,0],[100,110,120])

    def test_qanet_RGB_normalization_and_score_restore(self):
        import torch
        from controlled_roi_models import prepare_qanet_rgb,restore_qanet_probabilities
        cfg=SimpleNamespace(TEST=SimpleNamespace(SCALE=[4,4]),PIXEL_MEANS=[.5,.25,.1],PIXEL_STDS=[.5,.25,.1])
        rgb=np.full((2,4,3),[255,0,0],np.uint8)
        tensor,g=prepare_qanet_rgb(rgb,cfg)
        np.testing.assert_allclose(tensor[0,:,1,0].numpy(),[1,-1,-1],rtol=0,atol=1e-6)
        np.testing.assert_allclose(tensor[0,:,0,0].numpy(),[0,0,0],rtol=0,atol=1e-6)
        probs=torch.zeros((1,20,4,4));probs[:,13]=1;probs[:,:,1:3]=0;probs[:,5,1:3]=1
        np.testing.assert_array_equal(restore_qanet_probabilities(probs,g),np.full((2,4),5,np.uint8))

    def test_CPI_exporter_lossless_png_filename_contract(self):
        from controlled_roi_models import cpi_native_files
        with tempfile.TemporaryDirectory() as td:
            for name in ['crop.png-10.png','crop.png-2.png','crop.png-0.png','other.png-0.png']:
                (Path(td)/name).touch()
            self.assertEqual([p.name for p in cpi_native_files(td,'crop.png')],['crop.png-0.png','crop.png-2.png','crop.png-10.png'])

    def test_all_family_config_overrides_preserve_original(self):
        import yaml
        from controlled_roi_models import derived_config
        with tempfile.TemporaryDirectory() as td:
            w=Path(td);source=w/'native.yaml';original='TEST:\n  AUG:\n    H_FLIP: true\n'
            source.write_text(original)
            for family in ['QANet','RP-R-CNN','M2FP','D2FP','CPI-Parser']:
                result=derived_config(w,dict(family=family,native_config='native.yaml'),w/family)
                self.assertEqual(source.read_text(),original)
                value=yaml.safe_load((w/result).read_text())
                if family=='QANet':self.assertFalse(value['TEST']['AUG']['H_FLIP'])
                elif family=='RP-R-CNN':self.assertFalse(value['TEST']['BBOX_AUG']['ENABLED'])
                elif family in ['M2FP','D2FP']:self.assertFalse(value['TEST']['AUG']['ENABLED'])
                else:self.assertEqual(result,'native.yaml')

    def test_macro_weights_missed_parts_and_strict_complete(self):
        rows = [dict(target=k, IoU=v) for k, v in zip(['Hair', 'FaceDomain', 'Upper', 'Lower'], [1, 0, .5, .5])]
        self.assertEqual(macro_four(rows)['primary'], .5)
        self.assertIsNone(macro_four(rows[:-1])['primary'])
        self.assertTrue(reconcile(['a', 'b'], ['b', 'a'])['strict_complete'])
        self.assertFalse(reconcile(['a', 'b'], ['a', 'a'])['strict_complete'])
        self.assertFalse(reconcile(['a', 'b'], ['a', 'b'], failed=['attempt'])['strict_complete'])


if __name__ == '__main__':
    unittest.main()
