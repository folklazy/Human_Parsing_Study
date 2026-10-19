import unittest
import numpy as np
from src.data.ccihp_quality import audit_planes, allocate_strata

class QualityTests(unittest.TestCase):
    def test_consistent(self):
        c=np.array([[0,5,5],[0,13,13]],np.uint8);h=(c>0).astype(np.uint8)
        i=np.array([[0,1,1],[0,2,2]],np.uint16)
        r=audit_planes(c,h,i)
        self.assertEqual(r['person_count'],1);self.assertEqual(r['instance_count'],2)
        self.assertEqual(r['association_conflicts'],[])
    def test_unknown_preserved(self):
        c=np.array([[22]],np.uint8);h=np.array([[1]],np.uint8);i=h.astype(np.uint16)
        r=audit_planes(c,h,i);self.assertEqual(r['unknown_ids'],[22]);self.assertEqual(int(c[0,0]),22)
    def test_mixed_and_unassigned(self):
        c=np.array([[5,5,0]],np.uint8);h=np.array([[1,2,0]],np.uint8);i=np.ones((1,3),np.uint16)
        r=audit_planes(c,h,i);self.assertEqual(r['association_conflicts'][0]['human_labels'],[0,1,2])
        self.assertEqual(r['counts']['instance_without_category'],1)
    def test_noncontiguous(self):
        x=np.array([[0,7]],np.uint8);r=audit_planes(x,x,x.astype(np.uint16))
        self.assertEqual(r['persons'][0]['person_id'],7)
    def test_no_person(self):
        x=np.zeros((2,3),np.uint8);self.assertEqual(audit_planes(x,x,x)['person_count'],0)
    def test_mismatched_grids(self):
        with self.assertRaises(ValueError):audit_planes(np.zeros((2,2),np.uint8),np.zeros((1,2),np.uint8),np.zeros((2,2),np.uint16))
    def test_allocation(self):
        sizes={'a':1,'b':50,'c':100};a=allocate_strata(sizes,20)
        self.assertEqual(sum(a.values()),20);self.assertTrue(all(1<=a[k]<=sizes[k] for k in a))
    def test_float_rejected(self):
        x=np.zeros((2,2));
        with self.assertRaises(ValueError):audit_planes(x,x,x)

if __name__=='__main__':unittest.main()
