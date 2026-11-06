"""CPU-only orchestration contracts, with literal expected requirements."""
from pathlib import Path
import sys
import unittest
H=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(H/'scripts'),str(H/'src'),str(H.parent/'CCTV_Human_Parsing_Benchmark/scripts')]
from resume_controlled_cihp_pending import merge_references,generated_worker
from sequential_cihp_queue import may_advance
from finish_controlled_cihp_sapiens1b import generated_worker as prior_worker


class PendingSequentialQueue(unittest.TestCase):
    def test_merge_keeps_all_accepted_observations(self):
        self.assertEqual(merge_references({'a':1},{'b':2}),{'a':1,'b':2})

    def test_duplicate_reuse_is_rejected(self):
        with self.assertRaises(ValueError):merge_references({'a':1},{'a':2})

    def test_only_assembler_metadata_differs_from_approved_worker(self):
        source,changes=generated_worker();old,_=prior_worker()
        a,b=changes[-1];self.assertEqual(source.replace(b,a),old)

    def test_complete_first_job_allows_next(self):
        self.assertTrue(may_advance({'status':'BATCH_TERMINAL','queue_stopped':True},
            dict(status='COMPLETE',strict_complete=True,unique_frame_ids=5000,missing=0,duplicate=0,failed=0,invalid=0)))

    def test_partial_or_legacy_null_or_running_first_job_blocks_next(self):
        c={'status':'BATCH_TERMINAL','queue_stopped':True}
        good=dict(status='COMPLETE',strict_complete=True,unique_frame_ids=5000,missing=0,duplicate=0,failed=0,invalid=0)
        for key,value in [('strict_complete',False),('unique_frame_ids',4999),('missing',1),('duplicate',1),('failed',1),('invalid',1)]:
            bad=dict(good);bad[key]=value;self.assertFalse(may_advance(c,bad))
        self.assertFalse(may_advance(c,{}))
        self.assertFalse(may_advance({'status':'MODEL_RUNNING','queue_stopped':False},good))


if __name__=='__main__':unittest.main()
