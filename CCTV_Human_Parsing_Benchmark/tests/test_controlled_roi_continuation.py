from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from controlled_roi_continuation import reusable_memory,empty_rpr_prediction


class EmptyNative:
    def __len__(self):return 0
    def has_field(self,name):raise AssertionError('Empty native result must not access parsing field')


class BadNonempty:
    def __len__(self):return 1
    def has_field(self,name):return False


class ContinuationCases(unittest.TestCase):
    def test_owned_cached_memory_is_counted_without_lowering_threshold(self):
        r=reusable_memory(200,2000,12000)
        self.assertEqual(r['effective_available_bytes'],10200)
        self.assertEqual(r['own_reusable_pool_bytes'],10000)
        self.assertFalse(r['contiguous_allocation_guaranteed'])
        self.assertEqual(reusable_memory(500,1000,1000)['effective_available_bytes'],500)
        with self.assertRaises(ValueError):reusable_memory(1,3,2)

    def test_empty_person_native_result_is_valid_background(self):
        masks,boxes,scores=empty_rpr_prediction(EmptyNative(),(3,7))
        self.assertEqual(masks.shape,(0,3,7));self.assertEqual(boxes.shape,(0,4));self.assertEqual(scores.shape,(0,))

    def test_nonempty_missing_parsing_is_still_contract_failure(self):
        with self.assertRaises(ValueError):empty_rpr_prediction(BadNonempty(),(3,7))


if __name__=='__main__':unittest.main()
