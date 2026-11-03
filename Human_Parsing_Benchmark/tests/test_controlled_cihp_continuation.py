"""Regression checks for empty-native decoding and exact saved-output reuse."""
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
H = Path(__file__).resolve().parents[1]
sys.path[:0]=[str(H/'scripts'),str(H/'src'),str(H.parent/'CCTV_Human_Parsing_Benchmark/scripts')]
import continue_controlled_cihp as continuation
from common_view.packets import write_packet
from controlled_roi_core import sha


class EmptyPrediction:
    def __len__(self):return 0
    def has_field(self,name):raise AssertionError('Empty prediction must skip parsing access')


class InvalidNonempty:
    def __len__(self):return 1
    def has_field(self,name):return False


class ContinuationChecks(unittest.TestCase):
    def test_empty_native_contract(self):
        masks,boxes,scores=continuation.empty_rpr_prediction(EmptyPrediction(),(3,7))
        self.assertEqual(masks.shape,(0,3,7))
        self.assertEqual(boxes.shape,(0,4))
        self.assertEqual(scores.shape,(0,))
        self.assertEqual(masks.dtype,np.uint8)

    def test_nonempty_missing_field_stays_failure(self):
        with self.assertRaises(ValueError):
            continuation.empty_rpr_prediction(InvalidNonempty(),(3,7))

    def test_generated_source_has_bounded_pending_budget(self):
        source,changes=continuation.generated_worker()
        self.assertEqual(len(changes),11)
        self.assertIn("calls >= config['pending_call_limits'][mid]",source)
        self.assertIn("state['ROI_calls']+reused_ROI_count != config['ROI_count']",source)
        self.assertIn("prior_execution_seconds",source)
        self.assertIn("prior_stream_bytes",source)

    def test_atomic_reuse_rejects_modified_metadata(self):
        # Local temporary packet models an immutable accepted parent observation.
        with tempfile.TemporaryDirectory(dir=H.parent) as directory:
            root=Path(directory)
            p=write_packet(root,'one',{'native_crop_mask':np.zeros((3,7),np.uint8)}, {'model_id':'literal'}, {})
            reference={'packet':str(p.relative_to(H.parent)),
                       'members':{f.name:sha(f) for f in p.iterdir() if f.is_file()}}
            _, arrays=continuation.verify_reuse(reference)
            self.assertEqual(arrays['native_crop_mask'].shape,(3,7))
            (p/'packet.json').write_text('{}')
            with self.assertRaises(ValueError):continuation.verify_reuse(reference)

    def test_aggregate_reused_saved_scores(self):
        # Literal fields verify inclusion of both missed and matched GT parts.
        class Sink:
            def add(self,iid,scores):self.iid=iid
            hist=np.zeros((6,6),np.int64)
        scores={'0.5':{'histogram':np.eye(6,dtype=int).tolist()}}
        rows={'scores':scores,'parts':[dict(target=2,TP=3,FP=1,FN=2,IoU=.5,unmatched=False),
                                      dict(target=2,TP=0,FP=0,FN=4,IoU=0.,unmatched=True)]}
        sums={'2':dict(count=0,IoU_sum=0.,TP=0,FP=0,FN=0,unmatched=0)}
        sink=Sink();continuation.accumulate(rows,'example',sink,sums)
        self.assertEqual(sums['2'],dict(count=2,IoU_sum=.5,TP=3,FP=1,FN=6,unmatched=1))
        self.assertEqual(sink.hist.trace(),6)

if __name__=='__main__':unittest.main()
