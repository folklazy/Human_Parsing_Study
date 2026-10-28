"""Progress lifecycle tests only; no model imports or GPU access."""
from pathlib import Path
import sys,tempfile,json,unittest
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from rpr_progress import snapshot

class ProgressTests(unittest.TestCase):
    def test_inference_validation_terminal_are_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'segments/RPR_CIHP';folder.mkdir(parents=True)
            state={'status':'RUNNING','expected':5000,'controller_PID':1,'worker_PID':2};(root/'ROUND_STATUS.json').write_text(json.dumps(state));(folder/'RUN.json').write_text(json.dumps({'status':'INITIALIZING','complete':1250,'failed':0,'invalid':0}));live=lambda *_:True
            s=snapshot(root,live);self.assertEqual(s['phase'],'INFERENCE');self.assertEqual(s['inference_percent'],25.0)
            (folder/'RUN.json').write_text(json.dumps({'status':'COMPLETE','complete':5000}));self.assertEqual(snapshot(root,live)['phase'],'INFERENCE_DONE_AWAITING_VALIDATION')
            state['status']='POSTFLIGHT';(root/'ROUND_STATUS.json').write_text(json.dumps(state));self.assertEqual(snapshot(root,live)['phase'],'VALIDATING_ARTIFACTS');self.assertFalse(snapshot(root,live)['terminal'])
            state.update(status='COMPLETE',queue_stopped=True);(root/'ROUND_STATUS.json').write_text(json.dumps(state));self.assertTrue(snapshot(root,live)['terminal']);self.assertTrue(snapshot(root,live)['queue_stopped'])

    def test_stale_RUNNING_does_not_claim_live_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'ROUND_STATUS.json').write_text(json.dumps({'status':'RUNNING','expected':5000,'controller_PID':1,'worker_PID':2}));s=snapshot(root,lambda *_:False);self.assertEqual(s['phase'],'INTERRUPTED');self.assertFalse(s['controller_alive'])

    def test_continuation_counts_reused_outputs_in_running_and_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'segments/CPI_R50_CIHP';folder.mkdir(parents=True)
            (root/'SEGMENT_PLAN.json').write_text(json.dumps({'reused_ids':['a','b','c']}))
            (root/'ROUND_STATUS.json').write_text(json.dumps({'status':'RUNNING','expected':5000}))
            (folder/'RUN.json').write_text(json.dumps({'complete':2}))
            self.assertEqual(snapshot(root,lambda *_:True,model='CPI_R50_CIHP')['inference_complete'],5)
            (root/'ROUND_STATUS.json').write_text(json.dumps({'status':'INCOMPLETE','expected':5000,'complete':3}))
            (folder/'RUN.json').write_text(json.dumps({'complete':0,'failed':1}))
            s=snapshot(root,lambda *_:False,model='CPI_R50_CIHP')
            self.assertEqual(s['inference_complete'],3);self.assertEqual(s['reused_complete'],3)
            self.assertEqual(s['segment_inference_complete'],0);self.assertEqual(s['artifact_packets_verified'],3)

if __name__=='__main__':unittest.main()
