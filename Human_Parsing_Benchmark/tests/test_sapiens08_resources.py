"""Independent admission/accounting cases; no GPU access or model calls."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from common_view.sapiens08_resources import admission,execution_seconds
class ResourceCases(unittest.TestCase):
    def test_current_free_is_not_sufficient_when_peer_future_peak_is_high(self):
        r=admission(10000,1000,{1:1000},1,2,9000,3000,0,0,0,1000)
        self.assertFalse(r['admitted']);self.assertEqual(r['estimated_combined_MiB'],13000)
    def test_own_residency_is_not_double_counted(self):
        r=admission(15000,7000,{1:2000,2:5000},1,2,3000,6000,0,0,0,1000)
        self.assertTrue(r['admitted']);self.assertEqual(r['estimated_combined_MiB'],10000)
    def test_unknown_other_process_memory_remains_in_budget(self):
        r=admission(15000,13000,{1:2000,2:4000,3:7000},1,2,3000,6000,0,0,0,1000)
        self.assertFalse(r['admitted']);self.assertEqual(r['other_MiB'],7000)
    def test_queue_wait_does_not_extend_execution_cap(self):
        self.assertEqual(execution_seconds(100,40,200),60)
        self.assertEqual(execution_seconds(100,40,240),100)
if __name__=='__main__':unittest.main()
