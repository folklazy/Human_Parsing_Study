"""Resource accounting boundaries; no GPU/model execution."""
from pathlib import Path
import sys
import unittest
H=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(H/'scripts'),str(H/'src'),str(H.parent/'CCTV_Human_Parsing_Benchmark/scripts')]
from continue_controlled_cihp_resources import reusable_memory,generated_worker


class MemoryAccounting(unittest.TestCase):
    def test_own_cache_counts_as_available(self):
        m=reusable_memory(200,2000,12000)
        self.assertEqual(m['effective_available_bytes'],10200)
        self.assertEqual(m['own_reusable_pool_bytes'],10000)
        self.assertFalse(m['contiguous_allocation_guaranteed'])

    def test_live_allocations_never_counted_as_free(self):
        self.assertEqual(reusable_memory(200,12000,12000)['effective_available_bytes'],200)
        with self.assertRaises(ValueError):reusable_memory(200,12001,12000)

    def test_same_threshold_with_real_byte_units(self):
        unit=2**20
        m=reusable_memory(400*unit,700*unit,1500*unit)
        self.assertGreaterEqual(m['effective_available_bytes'],1024*unit)
        m=reusable_memory(400*unit,1200*unit,1500*unit)
        self.assertLess(m['effective_available_bytes'],1024*unit)

    def test_exact_source_change_keeps_guard_and_scoring(self):
        source,changes=generated_worker()
        self.assertEqual(len(changes),12)
        self.assertIn("memory['effective_available_bytes'] < config['min_forward_free_MiB']*2**20",source)
        self.assertIn("raise RuntimeError('RESOURCE_VRAM_HEADROOM_GUARD')",source)
        self.assertIn('evaluation = evaluate(',source)
        self.assertIn("for key, count in config['GT_expected_sums'].items():",source)

if __name__=='__main__':unittest.main()
