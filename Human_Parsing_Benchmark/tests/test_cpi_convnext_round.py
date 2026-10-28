"""Targeted CPU checks for new scope, transparent observation and diagnostic gate."""
from pathlib import Path
import ast,json,hashlib,sys,tempfile,types,unittest
from unittest.mock import patch
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import run_cpi_convnext_quality_round as controller
from run_cpi_convnext_shared_segment import MID,validate_policy,derive_shared,install_geometry_observer

class ConvNextRoundTests(unittest.TestCase):
    def test_scope_and_frozen_forward_scoring(self):
        policy=dict(mode='SHARED_GPU_QUALITY_ONLY',authorized_models=[MID],quality_only=True,timing_ranking_allowed=False)
        self.assertEqual(MID,'CPI_ConvNeXtB_CIHP');self.assertEqual(controller.MID,MID);validate_policy(policy,MID)
        with self.assertRaises(ValueError):validate_policy(policy,'CPI_R50_CIHP')
        original=(P/'scripts/run_cihp_system.py').read_text();expanded=derive_shared(original);ast.parse(expanded)
        for start,end in [("stage='MODEL_INFERENCE'","stage='EXPORT'"),("stage='SCORING';truth","packet_bytes=sum")]:self.assertEqual(original.split(start,1)[1].split(end,1)[0],expanded.split(start,1)[1].split(end,1)[0])

    def test_geometry_observer_returns_identical_pipeline_object(self):
        class DC:
            def __init__(self,data):self.data=data
        meta={'ori_shape':(375,500,3),'img_shape':(800,1067,3),'pad_shape':(800,1088,3),'flip':False}
        result={'img_metas':[DC(meta)],'img':object()};api=types.ModuleType('mmdet.apis.inference');api.Compose=lambda *_:lambda _:result
        mmdet=types.ModuleType('mmdet');apis=types.ModuleType('mmdet.apis');mmdet.apis=apis;apis.inference=api;mmcv=types.ModuleType('mmcv');parallel=types.ModuleType('mmcv.parallel');parallel.DataContainer=DC;mmcv.parallel=parallel
        with tempfile.TemporaryDirectory() as tmp,patch.dict(sys.modules,{'mmdet':mmdet,'mmdet.apis':apis,'mmdet.apis.inference':api,'mmcv':mmcv,'mmcv.parallel':parallel}):
            root=Path(tmp);install_geometry_observer(root);self.assertIs(api.Compose([])({'img_info':{'filename':'0000018.jpg'}}),result)
            record=json.loads((root/'INPUT_GEOMETRY.jsonl').read_text());self.assertEqual(record['native_pipeline_geometry'][0]['pad_shape'],[800,1088,3])

    def test_failed_diagnostic_never_enters_canonical_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'round';root.mkdir();parent=Path(tmp)/'parent';parent.mkdir();out=Path(tmp)/'project';out.mkdir();config={'max_system_hours':24,'models':{MID:{'checkpoint_sha256':'checkpoint','environment':'env'}}};(parent/'FROZEN_CONFIG.json').write_text(json.dumps(config));plan={'model_id':MID,'controller_sha256':hashlib.sha256(Path(controller.__file__).read_bytes()).hexdigest(),'prior_execution_seconds':0,'config':'frozen.json','config_sha256':'cfg'};(root/'SEGMENT_PLAN.json').write_text(json.dumps(plan))
            class Child:
                pid=123;returncode=1
                def __init__(self,*args,**kwargs):
                    d=root/'diagnostic'/MID;d.mkdir(parents=True);(d/'RUN.json').write_text(json.dumps({'status':'INCOMPLETE','stop_reason':'CUDA OOM fixture','warmup_images':['0000930']}))
                def wait(self,**kwargs):return 1
            with patch.object(controller,'P',out),patch.object(controller.subprocess,'Popen',Child),patch.object(controller.subprocess,'check_output',return_value='git-head'),patch.object(controller,'report') as report,patch.object(controller,'execute_validation') as validation:
                controller.execute_diagnostic_then_validation(parent,root);validation.assert_not_called();state=report.call_args[0][2];self.assertEqual(state['status'],'BLOCKED_DIAGNOSTIC_FAILED');self.assertEqual(state['complete'],0);self.assertEqual(state['failed'],0);self.assertTrue(state['queue_stopped'])
            diagnostic=json.loads((root/'DIAGNOSTIC_RESULT.json').read_text());self.assertFalse(diagnostic['canonical_eligible']);self.assertEqual(diagnostic['image_id'],'0000018')

    def test_saved_diagnostic_cannot_bypass_identity_or_eligibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);packet=root/'packet';packet.mkdir();(packet/'prediction.npz').write_bytes(b'fixture');audit=root/'audit.json';audit.write_text('{}')
            sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            d=dict(status='PASS',model_id=MID,image_id='0000018',canonical_eligible=False,frozen_config_sha256='cfg',verified_packet_path=str(packet),packet_sha256=sha(packet/'prediction.npz'),audit_state_path=str(audit),audit_state_sha256=sha(audit))
            def write():
                (root/'DIAGNOSTIC_RESULT.json').write_text(json.dumps(d));(root/'SEGMENT_PLAN.json').write_text(json.dumps(dict(validation_after_verified_saved_diagnostic=True,diagnostic_result_sha256=sha(root/'DIAGNOSTIC_RESULT.json'),config_sha256='cfg')))
            write();controller.verify_saved_diagnostic_gate(root)
            d['model_id']='CPI_R50_CIHP';write()
            with self.assertRaises(AssertionError):controller.verify_saved_diagnostic_gate(root)
            d['model_id']=MID;d['canonical_eligible']=True;write()
            with self.assertRaises(AssertionError):controller.verify_saved_diagnostic_gate(root)

if __name__=='__main__':unittest.main()
