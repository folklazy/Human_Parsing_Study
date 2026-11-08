"""Independent literal oracles for the newly approved reference-part views."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
import numpy as np

P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'src'))
from common_view.reference_parts import counts, score_frame, summarize
from common_view.packets import write_packet, read_packet


class ReferencePartAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=json.loads((P/'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json').read_text())

    def cross(self):
        g=np.zeros((5,5),bool)
        g[1,2]=g[2,1]=g[2,2]=g[2,3]=g[3,2]=True
        return g

    def test_face_box_preserves_in_box_FP_and_ignores_neck_outside(self):
        g=self.cross();p=np.zeros_like(g);p[1:5,1:4]=True
        r=counts(g,p,np.ones_like(g),local=True)
        self.assertEqual((r['TP'],r['FP'],r['FN']),(5,4,0))
        self.assertEqual(r['IoU'],5/9)
        self.assertEqual(r['ignored_prediction_pixels'],3)
        self.assertEqual(r['bbox_xyxy'],[1,1,4,4])

    def test_shared_void_is_not_model_specific_and_box_precedes_void(self):
        g=self.cross();v=np.ones_like(g);v[1,1]=False
        r=counts(g,np.ones_like(g),v,True)
        self.assertEqual((r['TP'],r['FP']),(5,3))
        v[1,2]=False
        self.assertEqual(counts(g,np.ones_like(g),v,True)['bbox_xyxy'],[1,1,4,4])

    def fixture(self,native=None,n=1):
        g=self.cross();e=np.ones_like(g)
        a=dict(person_semantic_masks=np.repeat((g.astype(np.uint8)*13 if native is None else native)[None],n,axis=0),
               person_extents=np.repeat(e[None],n,axis=0),person_scores=np.ones(n,np.float32))
        gt=dict(ids=[7],extents=[e],parts={(7,1):g},valid=e,shape=g.shape)
        return gt,a

    def test_native_taxonomies_get_same_domain_and_counts(self):
        gt,a=self.fixture();r=score_frame(gt,a,'CIHP_GT_AND_NATIVE_PRED',self.spec)
        b={k:v.copy() for k,v in a.items()};b['person_semantic_masks'][b['person_semantic_masks']==13]=3
        s=score_frame(gt,b,'SAPIENS2_DOME29_PRED',self.spec)
        self.assertEqual(r,s)

    def test_missed_person_contributes_zero_without_dropping_GT(self):
        gt,a=self.fixture();a={k:v[:0] for k,v in a.items()}
        r=score_frame(gt,a,'CIHP_GT_AND_NATIVE_PRED',self.spec)
        self.assertEqual((r['parts'][0]['IoU'],r['parts'][0]['FN']),(0,5))
        self.assertEqual(r['localization']['0.5']['FN'],1)

    def test_semantic_empty_is_still_matched_extent(self):
        gt,a=self.fixture(np.zeros((5,5),np.uint8));r=score_frame(gt,a,'CIHP_GT_AND_NATIVE_PRED',self.spec)
        self.assertEqual(r['localization']['0.5']['TP'],1)
        self.assertFalse(r['parts'][0]['unmatched'])
        self.assertEqual(r['parts'][0]['IoU'],0)

    def test_duplicate_prediction_is_localization_FP(self):
        gt,a=self.fixture(n=2);r=score_frame(gt,a,'CIHP_GT_AND_NATIVE_PRED',self.spec)
        self.assertEqual((r['localization']['0.5']['TP'],r['localization']['0.5']['FP']),(1,1))
        self.assertEqual(len(r['parts']),1)

    def test_known_unsupported_is_valid_and_invalid_id_fails(self):
        gt,a=self.fixture(np.full((5,5),6,np.uint8))
        self.assertEqual(score_frame(gt,a,'CIHP_GT_AND_NATIVE_PRED',self.spec)['parts'][0]['IoU'],0)
        a['person_semantic_masks'][:]=255
        with self.assertRaises(ValueError):score_frame(gt,a,'CIHP_GT_AND_NATIVE_PRED',self.spec)

    def test_C3_has_full_valid_domain_and_Face_remains_negative(self):
        g=np.zeros((5,5),bool);g[1,1]=True;p=g.copy();p[4,4]=True
        r=counts(g,p,np.ones_like(g),local=False)
        self.assertEqual((r['TP'],r['FP'],r['IoU']),(1,1,.5))
        self.assertIsNone(r['bbox_xyxy'])

    def test_GT_ID_renaming_does_not_change_geometry_match_quality(self):
        gt,a=self.fixture();r=score_frame(gt,a,'CIHP_GT_AND_NATIVE_PRED',self.spec)
        gt['ids']=[99];gt['parts']={(99,1):self.cross()}
        s=score_frame(gt,a,'CIHP_GT_AND_NATIVE_PRED',self.spec)
        self.assertEqual(r['parts'][0]['IoU'],s['parts'][0]['IoU'])
        self.assertEqual(r['localization'],s['localization'])

    def test_semantic_wrong_class_cannot_choose_a_better_assignment(self):
        gt,a=self.fixture();a['person_semantic_masks'][a['person_semantic_masks']==13]=2
        r=score_frame(gt,a,'CIHP_GT_AND_NATIVE_PRED',self.spec)
        self.assertEqual(r['localization']['0.5']['TP'],1)
        self.assertEqual(r['parts'][0]['IoU'],0)

    def test_actual_packet_scorer_reporter_and_STRICT_COMPLETE(self):
        gt,a=self.fixture()
        with tempfile.TemporaryDirectory() as d:
            p=write_packet(Path(d),'fixture',a,dict(image_id='fixture',model_id='test'),{})
            _,loaded=read_packet(p)
            row=dict(image_id='fixture',**score_frame(gt,loaded,'CIHP_GT_AND_NATIVE_PRED',self.spec))
            yes=summarize([row],['fixture']);no=summarize([row],['fixture','missing'])
            self.assertEqual(yes['Face_local_IoU'],1)
            self.assertIsNone(yes['primary_mIoU3_part_mean'])
            self.assertIsNone(no['Face_local_IoU']);self.assertIn('null',json.dumps(no))
            self.assertFalse(summarize([row,row],['fixture'])['strict_complete'])

    def test_asymmetric_geometry_is_not_transposed(self):
        g=np.zeros((4,7),bool);g[0,5]=g[2,6]=True
        r=counts(g,g,np.ones_like(g),True)
        self.assertEqual((r['bbox_xyxy'],r['TP']),([5,0,7,3],2))
        with self.assertRaises(ValueError):counts(g,g.T,np.ones_like(g),True)

    def test_aggregation_is_mean_parts_not_mean_pixels(self):
        gt,a=self.fixture();row=dict(image_id='a',**score_frame(gt,a,'CIHP_GT_AND_NATIVE_PRED',self.spec))
        second=json.loads(json.dumps(row));second['image_id']='b';part=second['parts'][0]
        part.update(TP=0,FP=0,FN=1,GT_pixels=1,prediction_pixels=0,union=1,IoU=0,Dice=0)
        r=summarize([row,second],['a','b'])['targets']['Face_local']
        self.assertEqual(r['mean_part_IoU'],.5);self.assertEqual(r['pooled_IoU'],5/6)


if __name__=='__main__':unittest.main()
