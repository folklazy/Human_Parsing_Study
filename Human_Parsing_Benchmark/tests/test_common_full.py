"""Hand-counted full reporter cases and equivalence to frozen revision2 scorer."""
import sys,unittest
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'src'))
from common_view.core import load_spec,score_packet
from common_view.full import score_people,project_confusion,native_confusion,Accumulator
SPEC=load_spec(P/'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json');SPACE='CIHP_GT_AND_NATIVE_PRED'

class FullCases(unittest.TestCase):
    def fixture(self,c,p,h=None,e=None):
        c=np.array([c],np.uint8);p=np.array([p],np.uint8);h=np.ones(c.shape,np.uint8) if h is None else np.array([h],np.uint8)
        p=p.reshape(-1,*c.shape);e=p>0 if e is None else np.array(e,bool).reshape(p.shape);s=np.ones(len(p),np.float32)
        return c,h,p,e,s
    def test_union_uses_confusion_not_mean_of_native_IoUs(self):
        h=np.zeros((20,20),np.int64);h[5,7]=3;h[7,5]=2;h[13,13]=1
        result=project_confusion(h,SPACE,SPEC)
        self.assertEqual(result[3,3],5);self.assertEqual(result[1,1],1);self.assertEqual(result.sum(),6)
    def test_streaming_complete_perfect_independent_values(self):
        c,h,p,e,s=self.fixture([13,2,5,9],[13,2,7,12]);scores=score_people(c,h,p,e,s,SPACE,SPEC)
        acc=Accumulator(['a']);self.assertIsNone(acc.report()['primary'])
        acc.add('a',scores,native_confusion(c,p,s,SPACE,SPEC),SPACE,SPEC);r=acc.report()
        self.assertEqual(r['primary']['mIoU4'],1.);self.assertEqual(r['primary']['C3_global_mean_only'],1.)
        self.assertEqual(r['person_metrics']['0.5']['Q_C4_GT'],1.)
        self.assertEqual(r['person_metrics']['0.5']['TP'],1)
        with self.assertRaises(ValueError):acc.add('a',scores)
    def test_semantic_empty_extent_missed_duplicate_and_VOID_equivalence(self):
        fixtures=[self.fixture([5,9],[0,0],e=[1,1]),self.fixture([5,9],[9,5]),
                  self.fixture([5,255],[5,0]),
                  (np.array([[5,9]],np.uint8),np.array([[1,2]],np.uint8),
                   np.array([[[5,0]],[[0,9]]],np.uint8),np.ones((2,1,2),bool),np.ones(2,np.float32))]
        for c,h,p,e,s in fixtures:
            actual=score_people(c,h,p,e,s,SPACE,SPEC)
            for t in [.5,.75]:
                expected=score_packet(c,h,p,e,s,SPACE,SPEC,t)
                self.assertTrue(all(expected[k]==v for k,v in actual[str(t)].items()))
    def test_failed_population_has_null_main_even_with_full_global_confusion(self):
        c,h,p,e,s=self.fixture([13,2,5,9],[13,2,5,9]);sc=score_people(c,h,p,e,s,SPACE,SPEC)
        acc=Accumulator(['a','b']);acc.add('a',sc)
        report=acc.report(np.eye(6,dtype=np.int64))
        self.assertIsNone(report['primary']);self.assertIsNone(report['person_metrics']);self.assertEqual(report['missing'],['b'])
    def test_no_person_keeps_GT_denominator_and_zero_Q(self):
        c=np.array([[5]],np.uint8);h=np.ones((1,1),np.uint8)
        sc=score_people(c,h,np.empty((0,1,1),np.uint8),np.empty((0,1,1),bool),np.empty(0,np.float32),SPACE,SPEC)
        self.assertEqual((sc['0.5']['G_sem_C4'],sc['0.5']['FN'],sc['0.5']['Q_C4_GT']),(1,1,0.))
    def test_geometry_tie_is_ID_renaming_invariant_for_distinct_GT(self):
        c=np.array([[5,9]],np.uint8);p=np.array([[[5,0]],[[0,9]]],np.uint8)
        e=np.ones(p.shape,bool);s=np.ones(2,np.float32)
        values=[]
        for h in [np.array([[1,2]],np.uint8),np.array([[2,1]],np.uint8)]:
            r=score_people(c,h,p,e,s,SPACE,SPEC)['0.5']
            values.append(r['Q_C4_GT']);self.assertTrue(r['matching_ambiguity']['alternative_optimum'])
        self.assertEqual(values,[1.,1.])
    def test_C3_face_stays_valid_negative_and_is_global_only(self):
        from common_view.core import semantic_metrics
        h=np.zeros((6,6),np.int64);h[1,2]=1;h[2,2]=1
        r=semantic_metrics(h)
        self.assertEqual(r['IoU'][2],.5);self.assertAlmostEqual(r['C3_global_mean_only'],1/6)
        self.assertNotIn('Q_C3',r)
if __name__=='__main__':unittest.main()
