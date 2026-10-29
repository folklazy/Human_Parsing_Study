"""Independent, hand-calculated C4-P acceptance fixtures through packet/scorer/reporter."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'src'))
from common_view.core import load_spec, project, gt_domains, score_packet, match_geometry
from common_view.packets import write_packet, read_packet, score_saved_packet, reporter
from common_view.sapiens_route import make_cpu_pipeline, prepare_rgb, logits_to_native, ownership_planes

SPEC = load_spec(P / 'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json')
SPACE = 'CIHP_GT_AND_NATIVE_PRED'


class CommonViewAcceptance(unittest.TestCase):
    def flow(self, category, planes, extents=None, human=None, space=SPACE):
        c = np.array(category, np.uint8)
        h = np.where((c > 0) & (c < 20), 1, 0).astype(np.uint8) if human is None else np.array(human, np.uint8)
        p = np.array(planes, np.uint8).reshape(-1, *c.shape)
        e = p > 0 if extents is None else np.array(extents, bool).reshape(p.shape)
        scores = np.ones(len(p), np.float32)
        with tempfile.TemporaryDirectory() as temp:
            arrays = dict(person_semantic_masks=p, person_extents=e, person_scores=scores)
            packet = write_packet(Path(temp) / 'packets', 'fixture', arrays,
                                  dict(image_id='fixture', model_id='SYNTHETIC', protocol_sha256='fixture-v2'), {})
            row = score_saved_packet(packet, c, h, space, SPEC,
                                     expected=dict(model_id='SYNTHETIC', protocol_sha256='fixture-v2'))
            report = reporter(Path(temp) / 'REPORT.json', [row], ['fixture'])
            self.assertTrue(report['complete'])
            self.assertIsNone(report['full_population_primary'])
            self.assertEqual(json.loads((Path(temp) / 'REPORT.json').read_text()), report)
            return row['scores']['0.5'], row['scores']['0.75'], report

    def test_binary_cache_representation_not_new_mask_policy(self):
        from common_view.detector_cache import normalize_detector_masks
        a=np.array([[[0,1],[1,0]]],np.uint8)
        b=normalize_detector_masks(a,1,(2,2))
        self.assertEqual(b.dtype,bool);np.testing.assert_array_equal(b,[[[False,True],[True,False]]])
        np.testing.assert_array_equal(a,[[[0,1],[1,0]]])
        with self.assertRaises(ValueError):normalize_detector_masks(np.array([[[255]]],np.uint8),1,(1,1))

    def test_total_native_mapping_expected_literal_values(self):
        np.testing.assert_array_equal(project(np.arange(20,dtype=np.uint8),SPACE,SPEC),
            [0,5,2,5,5,3,5,3,5,4,5,5,4,1,5,5,5,5,5,5])
        np.testing.assert_array_equal(project(np.arange(29,dtype=np.uint8),'SAPIENS2_DOME29_PRED',SPEC),
            [0,5,5,1,2,5,5,5,5,5,5,5,5,4,5,5,5,5,5,5,5,5,5,3,1,1,1,1,1])

    def test_missing_and_duplicate_membership_never_main_score(self):
        from common_view.core import aggregate
        with tempfile.TemporaryDirectory() as temp:
            partial=reporter(Path(temp)/'missing.json',[],['a'])
            self.assertFalse(partial['complete']);self.assertEqual(partial['missing'],['a'])
            self.assertIsNone(partial['diagnostics']);self.assertIsNone(partial['full_population_primary'])
        s,high,_=self.flow([[5]],[[[5]]])
        row=dict(image_id='a',scores={'0.5':s,'0.75':high})
        duplicate=aggregate([row,row],['a'])
        self.assertFalse(duplicate['complete']);self.assertEqual(duplicate['duplicate_ids'],['a'])
        self.assertIsNone(duplicate['diagnostics']);self.assertIsNone(duplicate['full_population_primary'])

    def test_perfect_four_plus_other_background(self):
        s, _, report = self.flow([[13, 2, 5, 9, 1, 0]], [[[13, 2, 5, 9, 1, 0]]])
        self.assertEqual(s['semantic']['mIoU4'], 1.)
        self.assertEqual((s['TP'], s['FP'], s['FN'], s['Q_C4_GT']), (1, 0, 0, 1.))
        self.assertEqual(report['diagnostics']['C3_global_mean_only'], 1.)

    def test_wrong_class(self):
        s, _, _ = self.flow([[13, 2, 5, 9]], [[[13, 2, 9, 5]]])
        self.assertEqual(s['semantic']['IoU'][1:5], [1., 1., 0., 0.])
        self.assertEqual(s['semantic']['mIoU4'], .5)

    def test_union_not_average_old_ious(self):
        s, _, _ = self.flow([[5, 5, 7, 7, 7]], [[[7, 7, 5, 5, 5]]])
        self.assertEqual(s['histogram'][3][3], 5)
        self.assertEqual(s['semantic']['IoU'][3], 1.)
        self.assertEqual(s['semantic']['mIoU4'], .25)

    def test_other_false_positive_and_false_negative(self):
        s, _, _ = self.flow([[6, 5]], [[[5, 6]]])
        self.assertEqual(s['histogram'][5][3], 1)
        self.assertEqual(s['histogram'][3][5], 1)
        self.assertEqual(s['semantic']['IoU'][3], 0.)

    def test_recognized_apparel_and_overlap_preserved(self):
        s, _, _ = self.flow([[5]], [[[23]], [[1]]], [[[1]], [[1]]], space='SAPIENS2_DOME29_PRED')
        # Equal scores: lower packet index wins (Upper); separately check higher-score Apparel.
        self.assertEqual(s['histogram'][3][3], 1)
        c = np.array([[5]], np.uint8);h = np.array([[1]], np.uint8)
        s = score_packet(c, h, np.array([[[23]], [[1]]], np.uint8), np.ones((2,1,1),bool),
                         np.array([.2,.9]), 'SAPIENS2_DOME29_PRED', SPEC)
        self.assertEqual(s['histogram'][3][5], 1)

    def test_semantic_empty_person_still_extent_tp(self):
        for label in (0, 6):
            s, _, _ = self.flow([[5]], [[[label]]], [[[True]]])
            self.assertEqual((s['TP'],s['FP'],s['FN'],s['extent_F1'],s['Q_C4_GT']), (1,0,0,1.,0.))

    def test_no_person_missed_gt(self):
        s, _, _ = self.flow([[5]], [], [])
        self.assertEqual((s['TP'],s['FP'],s['FN'],s['extent_F1'],s['Q_C4_GT']), (0,0,1,0.,0.))

    def test_duplicate(self):
        s, _, _ = self.flow([[5]], [[[5]],[[5]]])
        self.assertEqual((s['TP'],s['FP'],s['FN'],s['Q_C4_GT']), (1,1,0,1.))
        self.assertAlmostEqual(s['extent_F1'], 2/3)
        self.assertTrue(s['matching_ambiguity']['alternative_optimum'])

    def test_merged_two_people_contamination_and_threshold(self):
        s, high, _ = self.flow([[5,5]], [[[5,5]]], human=[[1,2]])
        self.assertEqual((s['TP'],s['FP'],s['FN'],s['Q_C4_GT'],s['contamination']), (1,0,1,.25,.5))
        self.assertEqual(s['semantic']['IoU'][3], 1.)
        self.assertEqual((high['TP'],high['FP'],high['FN'],high['Q_C4_GT']), (0,1,2,0.))

    def test_tie_counterexample_and_geometry_ID_invariance(self):
        from cihp_benchmark.evaluation import score_frame as frozen_native_score
        c = np.array([[5,9]],np.uint8)
        p = np.array([[[5,0]], [[0,9]]],np.uint8)
        e = np.ones((2,1,2),bool);scores=np.ones(2)
        # Independent expected values: two eligible .5 IoUs for each row;
        # (left->P0,right->P1) givesQ1, opposite pairingQ0.
        old = []
        for human in (np.array([[1,2]],np.uint8), np.array([[2,1]],np.uint8)):
            old.append(frozen_native_score(c,human,p,e,scores,.5)['Q_person_sem_GT'])
            sc = score_packet(c,human,p,e,scores,SPACE,SPEC,.5)
            self.assertEqual(sc['Q_C4_GT'], 1.)
            self.assertTrue(sc['matching_ambiguity']['alternative_optimum'])
            self.assertTrue(sc['matching_ambiguity']['ID_renaming_invariance_guaranteed'])
        self.assertEqual(old, [1.,0.])
        # Also verify the new behavior on the complete serialization flow.
        s, _, _ = self.flow([[5,9]], p, e, human=[[2,1]])
        self.assertEqual(s['Q_C4_GT'], 1.)

    def test_identical_geometry_fallback_is_not_unconditional_invariance(self):
        a=np.array([[True]])
        pairs, warning=match_geometry([a,a],[a,a],[2,1],.5)
        self.assertFalse(warning['ID_renaming_invariance_guaranteed'])
        self.assertEqual(warning['identical_GT_geometry_groups'],1)
        self.assertTrue(warning['alternative_optimum'])
        self.assertEqual(pairs[0][:2], (1,0))

    def test_same_extent_semantic_ownership_wrong(self):
        s, _, _ = self.flow([[5,9]], [[[9,0]],[[0,5]]], human=[[10,20]])
        self.assertEqual(s['extent_F1'], 1.)
        self.assertEqual(s['Q_C4_GT'], 0.)

    def test_owner_unknown_global_only(self):
        s, _, _ = self.flow([[13,5]], [[[13,5]]], human=[[0,1]])
        self.assertEqual(s['histogram'][1][1], 1)
        self.assertEqual((s['G_loc'],s['G_sem_C4'],s['Q_C4_GT']), (1,1,1.))
        self.assertEqual(s['GT_binding']['owner_unknown_pixels'],1)

    def test_shared_void(self):
        a,_,_=self.flow([[5]], [[[5]]])
        b,_,_=self.flow([[5,255]], [[[5,13]]], human=[[1,1]])
        self.assertEqual(a['histogram'],b['histogram'])
        self.assertEqual((b['extent_F1'],b['Q_C4_GT']), (1.,1.))

    def test_void_only_extent_and_zero_denominators(self):
        s,_,report=self.flow([[255]], [[[5]]], human=[[1]])
        self.assertEqual(s['void_only_predicted_extents'],1)
        self.assertEqual((s['TP'],s['FP'],s['FN']), (0,0,0))
        self.assertIsNone(s['Q_C4_GT']);self.assertIsNone(s['extent_F1'])
        self.assertIsNone(report['person_C4_diagnostics']['0.5']['Q_C4_GT'])
        self.assertEqual(s['semantic']['mIoU4'],0.)

    def test_C3_face_valid_negative_global_only(self):
        s,_,report=self.flow([[13,2,5,9]], [[[2,2,5,9]]])
        self.assertAlmostEqual(s['semantic']['C3_global_mean_only'], 5/6)
        self.assertEqual(s['histogram'][1][2],1)
        self.assertNotIn('Q_C3',json.dumps(report));self.assertNotIn('G_sem_C3',json.dumps(report))

    def test_unknown_and_negative_ids_invalid(self):
        for space,value in [(SPACE,20),(SPACE,255),('SAPIENS2_DOME29_PRED',29),('SAPIENS2_DOME29_PRED',255)]:
            with self.assertRaises(ValueError):self.flow([[5]], [[[value]]], space=space)
        with self.assertRaises(ValueError):project(np.array([-1]),SPACE,SPEC)
        with self.assertRaises(ValueError):gt_domains(np.array([[22]],np.uint8),np.array([[1]],np.uint8),SPEC)

    def test_cache_orphan_binding_and_null_handling(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);a=dict(person_semantic_masks=np.zeros((0,1,1),np.uint8),person_extents=np.zeros((0,1,1),bool),person_scores=np.zeros(0,np.float32))
            p=write_packet(root,'x',a,dict(image_id='x',protocol_sha256='one',model_id='M'),{})
            with self.assertRaises(ValueError):read_packet(p,{'protocol_sha256':'two'})
            with self.assertRaises(FileExistsError):write_packet(root,'x',a,{}, {})
            with self.assertRaises(ValueError):read_packet(p,{'model_id':'other'})
            (root/'.partial-y').mkdir()
            with self.assertRaises(FileExistsError):write_packet(root,'y',a,{}, {})
            (p/'prediction.npz').write_bytes(b'tampered')
            with self.assertRaises(ValueError):read_packet(p)

    def test_invalid_geometry_nonfinite_or_outside_ownership(self):
        from common_view.core import validate_prediction
        with self.assertRaises(ValueError):validate_prediction(np.ones((1,2,3),np.uint8),np.ones((1,3,2),bool),np.ones(1),(2,3),SPACE)
        with self.assertRaises(ValueError):validate_prediction(np.ones((1,1,1),np.uint8),np.ones((1,1,1),bool),np.array([np.nan]),(1,1),SPACE)
        with self.assertRaises(ValueError):validate_prediction(np.ones((1,1,1),np.uint8),np.zeros((1,1,1),bool),np.ones(1),(1,1),SPACE)

    def test_actual_preprocessor_asymmetric_channels_and_mapback(self):
        import torch
        root=P.parent/'third_party/human_parsing/sapiens2'
        cfg,pipeline,preprocessor=make_cpu_pipeline(root/'sapiens/dense/configs/seg/shutterstock_goliath/sapiens2_0.4b_seg_shutterstock_goliath-1024x768.py')
        rgb=np.empty((8,12,3),np.uint8)
        rgb[:4,:6]=[255,0,0];rgb[:4,6:]=[0,255,0];rgb[4:,:6]=[0,0,255];rgb[4:,6:]=[255,255,0]
        tensor,geometry=prepare_rgb(rgb,pipeline,preprocessor)
        self.assertEqual(geometry['original_wh'],[12,8]);self.assertEqual(geometry['padding'],[0,0,0,0])
        for y,x,color in [(0,0,[255,0,0]),(0,-1,[0,255,0]),(-1,0,[0,0,255]),(-1,-1,[255,255,0])]:
            expected=(np.array(color)-np.array([123.675,116.28,103.53]))/np.array([58.395,57.12,57.375])
            np.testing.assert_allclose(tensor[0,:,y,x].numpy(),expected,atol=1e-5)
        logits=torch.zeros((1,29,4,6),dtype=torch.float32)
        logits[0,3,:2,:3]=10;logits[0,4,:2,3:]=10;logits[0,23,2:,:3]=10;logits[0,13,2:,3:]=10
        native=logits_to_native(logits,(8,12));self.assertEqual([int(native[y,x]) for y,x in [(0,0),(0,-1),(-1,0),(-1,-1)]],[3,4,23,13])
        arrays=ownership_planes(native,np.ones((1,8,12),bool),np.array([.9],np.float32))
        self.assertEqual(arrays['person_semantic_masks'].shape,(1,8,12))
        # Literal expected quadrant GT: independent of the projector/resize code.
        gt=np.array([[13]*6+[2]*6]*4+[[5]*6+[9]*6]*4,np.uint8)
        with tempfile.TemporaryDirectory() as temp:
            packet=write_packet(Path(temp)/'packets','geometry',arrays,dict(image_id='geometry',geometry=geometry,protocol_sha256='geometry-v2'),{})
            meta,_=read_packet(packet,{'protocol_sha256':'geometry-v2'})
            self.assertEqual(meta['geometry']['original_wh'],[12,8])
            row=score_saved_packet(packet,gt,np.ones((8,12),np.uint8),'SAPIENS2_DOME29_PRED',SPEC)
            report=reporter(Path(temp)/'REPORT.json',[row],['geometry'])
            self.assertEqual(report['diagnostics']['mIoU4'],1.)
        self.assertEqual(ownership_planes(native,np.zeros((0,8,12),bool),np.zeros(0,np.float32))['person_extents'].shape,(0,8,12))


if __name__=='__main__':unittest.main(verbosity=2)
