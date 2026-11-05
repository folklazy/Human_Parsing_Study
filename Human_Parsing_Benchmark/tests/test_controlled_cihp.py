"""Literal tiny cases and saved-packet integration. No neural inference."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
import numpy as np

H = Path(__file__).resolve().parents[1]
W = H.parent
sys.path[:0] = [str(H/'src'), str(H/'scripts'), str(W/'CCTV_Human_Parsing_Benchmark/scripts')]
from common_view.core import load_spec
from common_view.packets import write_packet, read_packet
from controlled_ci_hp.scoring import evaluate
from controlled_ci_hp.measurement import Measurements
from controlled_roi_core import place

SPEC = load_spec(H/'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json')
SPACE = 'CIHP_GT_AND_NATIVE_PRED'


def packet(planes, extents=None):
    p = np.asarray(planes, np.uint8)
    return dict(person_semantic_masks=p, person_extents=p>0 if extents is None else extents,
                person_scores=np.ones(len(p),np.float32))


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.gt = np.array([[2,2,0],[5,7,0]],np.uint8)
        self.human = np.array([[1,1,0],[1,1,0]],np.uint8)
        self.extent = self.human[None]>0

    def score(self, a, category=None, human=None):
        return evaluate(self.gt if category is None else category, self.human if human is None else human, a, SPACE, SPEC)

    def test_perfect_union_and_report_readback(self):
        a=packet(self.gt[None], self.extent)
        result=self.score(a)
        self.assertEqual(result['scores']['0.5']['Q_C4_GT'],1.)
        self.assertEqual([(p['target'],p['TP'],p['FP'],p['FN']) for p in result['parts']],[(2,2,0,0),(3,2,0,0)])
        with tempfile.TemporaryDirectory() as d:
            p=write_packet(Path(d),'tiny',a,dict(model_id='literal'),result['scores'])
            meta,saved=read_packet(p)
            reloaded=self.score(saved)
            self.assertEqual(result,reloaded)
            self.assertEqual(json.loads((p/'score_0.5.json').read_text())['Q_C4_GT'],1.)

    def test_wrong_class(self):
        p=np.where(self.human>0,9,0).astype(np.uint8)
        result=self.score(packet(p[None],self.extent))
        self.assertEqual(result['scores']['0.5']['Q_C4_GT'],0.)
        self.assertEqual([r['FN'] for r in result['parts']],[2,2])

    def test_semantic_empty_extent(self):
        r=self.score(packet(np.zeros((1,2,3),np.uint8),self.extent))['scores']['0.5']
        self.assertEqual((r['TP'],r['FN'],r['Q_C4_GT']),(1,0,0.))

    def test_no_person(self):
        r=self.score(packet(np.zeros((0,2,3),np.uint8)))
        self.assertEqual((r['scores']['0.5']['TP'],r['scores']['0.5']['FN']),(0,1))
        self.assertTrue(all(p['IoU']==0 and p['unmatched'] for p in r['parts']))

    def test_duplicate(self):
        r=self.score(packet(np.stack([self.gt,self.gt]),np.repeat(self.extent,2,axis=0)))['scores']['0.5']
        self.assertEqual((r['TP'],r['FP'],r['FN']),(1,1,0))
        self.assertEqual(r['Q_C4_GT'],1.)

    def test_other_false_positive_false_negative(self):
        gt=np.array([[5,6,0]],np.uint8);human=np.array([[1,1,0]],np.uint8)
        a=packet(np.array([[[6,5,0]]],np.uint8),np.array([[[1,1,0]]],bool))
        p=self.score(a,gt,human)['parts'][0]
        self.assertEqual((p['TP'],p['FP'],p['FN'],p['IoU']),(0,1,1,0.))

    def test_void_and_invalid_prediction(self):
        gt=self.gt.copy();gt[0,2]=255
        a=packet(self.gt[None],self.extent)
        self.assertEqual(self.score(a,gt)['scores']['0.5']['Q_C4_GT'],1.)
        a['person_semantic_masks'][0,0,0]=255
        with self.assertRaises(ValueError):self.score(a,gt)

    def test_empty_GT_null_json(self):
        r=self.score(packet(np.zeros((0,2,3),np.uint8)),np.zeros((2,3),np.uint8),np.zeros((2,3),np.uint8))
        self.assertIsNone(r['scores']['0.5']['Q_C4_GT'])
        self.assertIn('null',json.dumps(r,allow_nan=False))

    def test_asymmetric_placement_and_ownership(self):
        native=np.array([[2,5,7],[9,13,0]],np.uint8)
        extent=np.zeros((4,6),bool);extent[1:3,2:5]=True;extent[1,3]=False
        raw,owned=place(native,[2,1,5,3],extent,20)
        self.assertEqual(raw[2,3],13)
        self.assertEqual(owned[1,3],0)
        self.assertEqual(raw[1,4],7)

    def test_instrument_wrapper_restores_on_failure(self):
        class Dummy:
            def call(self):raise RuntimeError('literal failure')
        d=Dummy();original=d.call;timer=Measurements()
        with self.assertRaises(RuntimeError):
            with timer.wrap(d,'call','stage'):d.call()
        self.assertEqual(d.call,original)
        self.assertEqual(timer.records[0]['status'],'FAILED')

    def test_saved_packet_geometry_membership_readonly(self):
        config=json.loads((H/'configs/cihp_sapiens_c4p_full.json').read_text())
        reference=config['legacy']['QANet_CIHP_HRNetW48_512x384']
        row=json.loads((W/reference['input_manifest']).read_text().splitlines()[0])
        source=W/row['packet']
        from controlled_roi_core import sha
        before=sha(source/'prediction.npz')
        meta,arrays=read_packet(source,legacy=True)
        iid=row['image_id']
        from PIL import Image
        gt=np.asarray(Image.open(W/'datasets/CIHP/Validation/Category_ids'/(iid+'.png')))
        human=np.asarray(Image.open(W/'datasets/CIHP/Validation/Human_ids'/(iid+'.png')))
        result=evaluate(gt,human,arrays,SPACE,SPEC)
        from common_view.full import score_people
        canonical=score_people(gt,human,arrays['person_semantic_masks'],arrays['person_extents'],arrays['person_scores'],SPACE,SPEC)
        for threshold in ('0.5','0.75'):
            for key in ('TP','FP','FN','Q_C4_GT','G_loc','G_sem_C4'):
                self.assertEqual(result['scores'][threshold][key],canonical[threshold][key])
        self.assertEqual(before,sha(source/'prediction.npz'))

    def test_ID_renaming_and_wrong_ownership(self):
        gt=np.array([[2,2,0,5,5]],np.uint8)
        human=np.array([[1,1,0,2,2]],np.uint8)
        ext=np.array([[[1,1,0,0,0]],[[0,0,0,1,1]]],bool)
        planes=np.array([[[2,2,0,0,0]],[[0,0,0,5,5]]],np.uint8)
        a=packet(planes,ext)
        good=self.score(a,gt,human)['scores']['0.5']
        renamed=np.where(human==1,17,np.where(human==2,4,0)).astype(np.uint8)
        self.assertEqual(self.score(a,gt,renamed)['scores']['0.5']['Q_C4_GT'],1.)
        wrong_planes=np.array([[[5,5,0,0,0]],[[0,0,0,2,2]]],np.uint8)
        wrong=self.score(packet(wrong_planes,ext),gt,human)['scores']['0.5']
        self.assertEqual(good['Q_C4_GT'],1.)
        self.assertEqual(wrong['Q_C4_GT'],0.)
        self.assertEqual(wrong['extent_F1'],1.)

    def test_owner_unknown_and_face_in_C3_domain(self):
        gt=np.array([[13,5]],np.uint8);human=np.array([[0,1]],np.uint8)
        a=packet(np.array([[[2,5]]],np.uint8),np.ones((1,1,2),bool))
        r=self.score(a,gt,human)['scores']['0.5']
        self.assertEqual(r['GT_binding']['owner_unknown_pixels'],1)
        self.assertEqual(r['histogram'][1][2],1)
        self.assertEqual(r['semantic']['IoU'][2],0.)


if __name__=='__main__':unittest.main()
