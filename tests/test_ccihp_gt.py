import unittest
import numpy as np
from src.data.ccihp_gt import person_planes, reconstruct


class CCIHPGTTests(unittest.TestCase):
    def check_roundtrip(self, c, h, i):
        planes = person_planes(c, h, i)
        for actual, expected in zip(reconstruct(planes, c.dtype, h.dtype, i.dtype), [c,h,i]):
            np.testing.assert_array_equal(actual, expected)
            self.assertEqual(actual.dtype, expected.dtype)
        return planes

    def test_two_people_and_unknown_semantics(self):
        c=np.array([[0,21,22],[0,5,13]],np.uint8)
        h=np.array([[0,7,9],[0,7,9]],np.uint8)
        i=np.array([[0,300,700],[0,301,701]],np.uint16)
        p=self.check_roundtrip(c,h,i)
        self.assertEqual([x['person_id'] for x in p['persons']],[7,9])
        self.assertEqual(p['persons'][0]['bbox_xyxy_half_open'],[1,0,2,2])
        self.assertFalse(p['native_CIHP_equivalence'])

    def test_unassigned_foreground_is_preserved(self):
        c=np.array([[20,5]],np.uint8);h=np.array([[0,1]],np.uint8);i=np.array([[500,7]],np.uint16)
        p=self.check_roundtrip(c,h,i)
        self.assertEqual(p['unassigned_semantic'][0,0],20)

    def test_human_without_semantic_is_preserved(self):
        c=np.array([[0,0]],np.uint8);h=np.array([[1,0]],np.uint8);i=np.zeros_like(c,dtype=np.uint16)
        p=self.check_roundtrip(c,h,i)
        self.assertTrue(p['persons'][0]['foreground_mask'][0,0])

    def test_unknown_255_not_silently_ignored(self):
        c=np.array([[255]],np.uint8);h=np.array([[1]],np.uint8);i=np.array([[65535]],np.uint16)
        p=self.check_roundtrip(c,h,i)
        self.assertEqual(p['persons'][0]['semantic'][0,0],255)

    def test_empty_human_map(self):
        c=np.array([[0,4]],np.uint8);h=np.zeros_like(c);i=np.array([[0,300]],np.uint16)
        self.assertEqual(self.check_roundtrip(c,h,i)['persons'],[])

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):person_planes(np.zeros((2,2),np.uint8),np.zeros((3,2),np.uint8),np.zeros((2,2),np.uint16))

    def test_invalid_float_or_negative_ids(self):
        with self.assertRaises(ValueError):person_planes(np.zeros((1,1)),np.zeros((1,1),np.uint8),np.zeros((1,1),np.uint16))
        with self.assertRaises(ValueError):person_planes(np.array([[-1]]),np.zeros((1,1),np.uint8),np.zeros((1,1),np.uint16))

    def test_overlapping_planes_not_flattened(self):
        c=np.array([[5]],np.uint8);h=np.array([[1]],np.uint8);i=np.array([[300]],np.uint16)
        p=person_planes(c,h,i);p['persons'].append(dict(p['persons'][0],person_id=2))
        with self.assertRaises(ValueError):reconstruct(p,c.dtype,h.dtype,i.dtype)
