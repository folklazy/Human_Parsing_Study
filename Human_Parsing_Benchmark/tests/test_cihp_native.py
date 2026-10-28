"""Independent hand-counted native packet->scorer->serialized-report checks."""
import unittest,tempfile,json
from pathlib import Path
import numpy as np
from cihp_benchmark.evaluation import score_frame,semantic_report,read_packet
class NativeCases(unittest.TestCase):
 def run_case(self,c,h,p,e,scores=None):
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);(d/'packet.json').write_text(json.dumps({'label_space':'CIHP_NATIVE_20'}));np.savez(d/'prediction.npz',person_semantic_masks=np.asarray(p,dtype=np.uint8).reshape(-1,*c.shape),person_extents=np.asarray(e,bool).reshape(-1,*c.shape),person_scores=np.asarray(scores if scores is not None else [1]*len(p),float));meta,a=read_packet(d);r=score_frame(c,h,a['person_semantic_masks'],a['person_extents'],a['person_scores']);(d/'report.json').write_text(json.dumps(r,allow_nan=False));return json.loads((d/'report.json').read_text())
 def test_perfect_wrong_empty_and_rejection_invalid(self):
  c=np.full((2,2),5,np.uint8);h=np.ones((2,2),np.uint8);e=np.ones((2,2),bool)
  r=self.run_case(c,h,[c],[e]);self.assertEqual((r['Q_person_sem_GT'],r['extent_F1']),(1,1))
  for label in [9,0,6]:
   r=self.run_case(c,h,[np.full((2,2),label,np.uint8)],[e]);self.assertEqual((r['Q_person_sem_GT'],r['extent_F1']),(0,1))
  with self.assertRaises(ValueError):self.run_case(c,h,[np.full((2,2),99,np.uint8)],[e])
 def test_missing_and_duplicate(self):
  c=np.full((2,2),5,np.uint8);h=np.ones_like(c);e=np.ones_like(c,bool)
  r=self.run_case(c,h,[],[]);self.assertEqual((r['FN'],r['Q_person_sem_GT'],r['extent_F1']),(1,0,0))
  r=self.run_case(c,h,[c,c],[e,e]);self.assertEqual((r['TP'],r['FP'],r['Q_person_sem_GT']),(1,1,1));self.assertAlmostEqual(r['extent_F1'],2/3)
 def test_missed_one_and_wrong_owner(self):
  h=np.array([[1,1,2,2]],np.uint8);c=np.full(h.shape,5,np.uint8);a=h==1;b=h==2
  p=np.where(a,c,0);q=np.where(b,c,0)
  r=self.run_case(c,h,[p],[a]);self.assertEqual(r['Q_person_sem_GT'],.5);self.assertAlmostEqual(r['extent_F1'],2/3)
  r=self.run_case(c,h,[q,p],[a,b]);self.assertEqual((r['extent_F1'],r['Q_person_sem_GT'],r['contamination_matched']),(1,0,1))
  r2=self.run_case(c,h,[q,p],[b,a]);self.assertEqual(r2['Q_person_sem_GT'],1) # rename/reorder complete records, not wrong owner
 def test_VOID_and_native_dress(self):
  c=np.array([[5,255],[6,6]],np.uint8);h=np.ones_like(c);p=np.array([[5,19],[6,6]],np.uint8)
  r=self.run_case(c,h,[p],[h>0]);self.assertEqual(r['Q_person_sem_GT'],1);self.assertEqual(np.diag(r['histogram']).sum(),3)
 def test_reference_absent_class_convention(self):
  h=np.zeros((20,20),int);h[5,5]=4;r=semantic_report(h);self.assertEqual(r['mIoU_20_including_BG'],.05);self.assertEqual(r['union'][6],0)
 def test_dimension_contract(self):
  with self.assertRaises(ValueError):score_frame(np.zeros((2,2),int),np.ones((2,2),int),np.zeros((1,1,1),np.uint8),np.ones((1,1,1),bool),[1])
if __name__=='__main__':unittest.main()
