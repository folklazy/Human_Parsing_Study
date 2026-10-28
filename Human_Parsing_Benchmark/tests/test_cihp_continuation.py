"""CPU-only continuation acceptance, no model imports or GPU inference."""
from pathlib import Path
import ast,json,sys,tempfile,unittest
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from run_cihp_segment import derive,validate_partition
from reconcile_cihp_continuation import validate_folder

class ContinuationTests(unittest.TestCase):
    def test_partition_no_repeat_no_missing_order(self):
        validate_partition(['a','b','c'],['b','c'],['a'])
        validate_partition(['a','b','c'],[],['a','b','c'])
        for pending,reused in [(['b','b','c'],['a']),(['a','b','c'],['a']),(['b'],['a']),(['c','b'],['a'])]:
            with self.assertRaises(ValueError):validate_partition(['a','b','c'],pending,reused)

    def test_frozen_forward_and_export_unmodified(self):
        original=(P/'scripts/run_cihp_system.py').read_text();expanded=derive(original);ast.parse(expanded)
        for start,end in [("stage='MODEL_INFERENCE'","stage='EXPORT'"),("stage='SCORING';truth", "packet_bytes=sum")]:
            self.assertEqual(original.split(start,1)[1].split(end,1)[0],expanded.split(start,1)[1].split(end,1)[0])
        self.assertEqual(expanded.count("segment['pending_ids']"),4)
        with self.assertRaises(ValueError):derive(original.replace("rows=pop['members'];detector=",'ANCHOR_REMOVED'))

    def test_corrupted_packet_stops_before_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f=root/'model';packet=f/'packets'/'image';packet.mkdir(parents=True)
            (packet/'prediction.npz').write_bytes(b'corrupted bytes')
            (packet/'packet.json').write_text(json.dumps({'packet_sha256':'not_the_hash'}))
            (f/'FRAMES.jsonl').write_text(json.dumps({'image_id':'image','status':'COMPLETE','packet_sha256':'not_the_hash'})+'\n')
            # Source-folder provenance is workspace-relative in production.
            import reconcile_cihp_continuation as r
            previous=r.W;r.W=root
            try:
                with self.assertRaises(AssertionError):validate_folder(f,{'models':{'model':{}}},{'image':{}},{},root/'audit','hash')
                self.assertEqual((packet/'prediction.npz').read_bytes(),b'corrupted bytes')
            finally:r.W=previous

if __name__=='__main__':unittest.main()
