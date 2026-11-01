"""Independent literal expected values for the reviewed Face-domain extension."""
from pathlib import Path
import json
import tempfile
import sys
import unittest
import numpy as np

P=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(P/'scripts'),str(P.parent/'Human_Parsing_Benchmark/src')]
from face_neck_evaluation import score_face, aggregate_view, macro_four
from face_neck_gt import polygons_mask
from controlled_roi_core import atomic, sha
from common_view.packets import write_packet, read_packet
from selected_part_evaluation import final_plane_lookup


class FaceDomainAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projection=json.loads((P/'configs/CONTROLLED_ROI_SCORING_PROTOCOL.json').read_text())

    def fixture(self):
        # Two Face pixels, one known Neck, one unknown boundary, one opaque object.
        return {key:np.array([values],bool) for key,values in dict(
            Face=[1,1,0,0,0],Neck=[0,0,1,0,0],uncertainty=[0,0,0,1,0],
            known_occluder=[0,0,0,0,1]).items()}

    def test_known_neck_ignore_and_delivery_are_different(self):
        g=self.fixture();r=dict(Neck_status='VISIBLE_ANNOTATED',FaceNeck_delivery_eligible=True)
        face_only=score_face(np.array([[13,13,0,0,0]],np.uint8),'CIHP20',g,r,self.projection)
        both=score_face(np.array([[13,13,13,0,0]],np.uint8),'CIHP20',g,r,self.projection)
        self.assertEqual(face_only['FaceDomain']['IoU'],1)
        self.assertEqual(both['FaceDomain']['IoU'],1)
        self.assertEqual(face_only['FaceNeck']['IoU'],2/3)
        self.assertEqual(both['FaceNeck']['IoU'],1)
        self.assertEqual((face_only['NeckCoverage'],both['NeckCoverage']),(0,1))

    def test_opaque_occluder_is_valid_negative_not_amodal_neck(self):
        g=self.fixture();r=dict(Neck_status='VISIBLE_ANNOTATED',FaceNeck_delivery_eligible=True)
        actual=score_face(np.full((1,5),13,np.uint8),'CIHP20',g,r,self.projection)
        self.assertEqual((actual['FaceDomain']['TP'],actual['FaceDomain']['FP'],actual['FaceDomain']['FN']),(2,1,0))
        self.assertEqual(actual['FaceDomain']['IoU'],2/3)
        self.assertEqual(actual['FaceNeck']['IoU'],.75)

    def test_unknown_neck_has_face_domain_but_no_fake_delivery_or_coverage(self):
        g=self.fixture();g['Neck'][:]=False;g['uncertainty'][0,2]=True
        r=dict(Neck_status='REGION_UNCERTAIN',FaceNeck_delivery_eligible=False)
        result=score_face(np.array([[13,13,13,13,0]],np.uint8),'CIHP20',g,r,self.projection)
        self.assertEqual(result['FaceDomain']['IoU'],1)
        self.assertIsNone(result['FaceNeck']);self.assertIsNone(result['NeckCoverage'])
        self.assertIsNone(result['known_Neck_pixels'])
        with self.assertRaises(ValueError):score_face(np.zeros((1,5),np.uint8),'CIHP20',g,dict(r,FaceNeck_delivery_eligible=True),self.projection)

    def test_absent_and_unknown_neck_are_not_same_state(self):
        g=self.fixture();g['Neck'][:]=False
        r=dict(Neck_status='VERIFIED_NOT_VISIBLE',FaceNeck_delivery_eligible=True)
        result=score_face(np.array([[13,13,0,0,0]],np.uint8),'CIHP20',g,r,self.projection)
        self.assertEqual(result['FaceNeck']['IoU'],1);self.assertIsNone(result['NeckCoverage'])
        self.assertEqual(result['known_Neck_pixels'],0)
        g['Neck'][0,2]=True
        with self.assertRaises(ValueError):score_face(None,'CIHP20',g,r,self.projection)

    def test_empty_missed_and_wrong_person_predictions(self):
        g=self.fixture();r=dict(Neck_status='VISIBLE_ANNOTATED',FaceNeck_delivery_eligible=True)
        missing=score_face(None,'CIHP20',g,r,self.projection)
        self.assertEqual((missing['FaceDomain']['IoU'],missing['FaceDomain']['FN']),(0,2))
        wrong=score_face(np.array([[0,0,0,0,13]],np.uint8),'CIHP20',g,r,self.projection)
        self.assertEqual((wrong['FaceDomain']['TP'],wrong['FaceDomain']['FP'],wrong['FaceDomain']['FN']),(0,1,2))

    def test_native_union_invalid_IDs_and_asymmetric_geometry(self):
        g={k:np.pad(v,((1,0),(0,0))) for k,v in self.fixture().items()}
        ci=np.array([[0,0,0,0,0],[13,13,13,0,0]],np.uint8)
        sa=np.array([[0,0,0,0,0],[3,25,28,0,0]],np.uint8)
        r=dict(Neck_status='VISIBLE_ANNOTATED',FaceNeck_delivery_eligible=True)
        self.assertEqual(score_face(ci,'CIHP20',g,r,self.projection),score_face(sa,'SAPIENS29',g,r,self.projection))
        ci[1,3]=255  # Invalid even on GT uncertainty.
        with self.assertRaises(ValueError):score_face(ci,'CIHP20',g,r,self.projection)
        with self.assertRaises(ValueError):score_face(sa.T,'SAPIENS29',g,r,self.projection)

    def test_mean_part_is_not_pooled_and_incomplete_never_has_primary(self):
        rows=[dict(FaceDomain=dict(TP=1,FP=0,FN=0,GT_pixels=1,IoU=1,Dice=1)),
              dict(FaceDomain=dict(TP=0,FP=0,FN=3,GT_pixels=3,IoU=0,Dice=0))]
        s=aggregate_view(rows,'FaceDomain')
        self.assertEqual(s['mean_part_IoU'],.5);self.assertEqual(s['pooled_IoU'],.25)
        other={n:dict(mean_part_IoU=v) for n,v in [('Hair',.2),('Upper',.6),('Lower',.7)]}
        self.assertEqual(macro_four(other,s,True),.5)
        self.assertIsNone(macro_four(other,s,False))
        self.assertIsNone(aggregate_view([dict(FaceNeck=None)],'FaceNeck')['mean_part_IoU'])

    def test_manual_original_grid_polygon_and_invalid_geometry(self):
        m=polygons_mask([[[2,1],[4,1],[4,3],[2,3]]],(5,7))
        expected=np.zeros((5,7),bool);expected[1:4,2:5]=True
        self.assertTrue(np.array_equal(m,expected));self.assertEqual(int(m.sum()),9)
        with self.assertRaises(ValueError):polygons_mask([[[0,0],[7,0],[0,1]]],(5,7))
        with self.assertRaises(ValueError):polygons_mask([[[0,0],[1.5,0],[0,1]]],(5,7))

    def test_atomic_packet_to_face_scorer_to_report_preserves_sources_and_null(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);native=np.array([[[13,13,13,0,13]]],np.uint8);extents=np.ones_like(native,bool)
            arrays=dict(person_semantic_masks=native,person_extents=extents,person_scores=np.array([.9],np.float32))
            meta=dict(associations=[dict(YOLO_opportunity_id='synthetic:detector:0',prediction_index=123)])
            packet=write_packet(root,'synthetic',arrays,meta,{})
            before={p.name:sha(p) for p in packet.iterdir()};m,a=read_packet(packet)
            lookup=final_plane_lookup(m,a,dict(masks=extents,scores=arrays['person_scores']),[dict(id='synthetic:detector:0')])
            result=score_face(a['person_semantic_masks'][lookup['synthetic:detector:0']],'CIHP20',self.fixture(),
                              dict(Neck_status='VISIBLE_ANNOTATED',FaceNeck_delivery_eligible=True),self.projection)
            result['unavailable_latency']=None;atomic(root/'REPORT.json',result);back=json.loads((root/'REPORT.json').read_text())
            self.assertEqual(back['FaceDomain']['IoU'],2/3);self.assertEqual(back['FaceNeck']['IoU'],.75)
            self.assertIsNone(back['unavailable_latency']);self.assertEqual(before,{p.name:sha(p) for p in packet.iterdir()})


if __name__=='__main__':unittest.main()
