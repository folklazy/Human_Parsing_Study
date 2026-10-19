"""Regression tests of real scorer/runner boundaries, using synthetic GT only."""
import copy
import json
from pathlib import Path
import sys
import unittest
import numpy as np
S = Path(__file__).resolve().parents[1]; sys.path.insert(0,str(S))
from src.application_v2.taxonomy import project_prediction, project_gt
from src.application_v2.evaluation import evaluate_persons, person_truth
from src.application_v2.scoring import score_frame, require_retention
from src.application_v2.runner import ConfiguredRunner
from src.application_v2.policy import digest

class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.mapping=json.loads((S/'taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V2.json').read_text())
        self.mapping['status']='ACCEPTED'  # synthetic context only, never written to configuration
        self.binding=dict(checkpoint_sha256='a'*64,config_sha256='b'*64,source_commit='c'*40,native_class_order=list(range(20)),native_taxonomy='CIHP',head_classes=20)
        self.input=dict(status='VERIFIED',image_id='synthetic',input_sha256='d'*64,original_wh=[2,2])
        self.context=dict(status='ACCEPTED',mapping_sha256=digest(self.mapping),model_binding=self.binding.copy(),input_binding=self.input.copy(),domain=dict(status='ACCEPTED',evidence='synthetic explicitly complete GT'),target_support_policy='COMMON_CAPABILITY',failure_policy='STRICT_COMPLETE',threshold=.5,evaluation_bbox_source='SYNTHETIC_PREDICTED_BOX')
        self.gt=[dict(id='g',bbox=[0,0,2,2],loc_eligible=True,sem_eligible=True,semantic=np.ones((2,2),np.int16),valid=np.ones((2,2),bool))]
        self.pred=[dict(id='p',bbox=[0,0,2,2],semantic=np.ones((2,2),np.int16),score=.9)]
    def score(self,gt=None,pred=None,state='COMPLETE'):
        preds=copy.deepcopy(self.pred if pred is None else pred)
        for p in preds:
            p.setdefault('evaluation_bbox',dict(xyxy=p['bbox'],source='SYNTHETIC_PREDICTED_BOX',coordinate_convention='XYXY_HALF_OPEN',derivation_revision='fixture1'))
        return score_frame(self.context,self.mapping,self.binding,self.input,self.gt if gt is None else gt,preds,lifecycle=dict(status=state,events=['retained event']))
    def test_a01_binding_rejected_actual_entry(self):
        self.binding['checkpoint_sha256']='e'*64
        with self.assertRaises(ValueError):self.score()
    def test_a02_lip_support_rejected(self):
        self.binding['native_taxonomy']='LIP';self.context['model_binding']=self.binding.copy()
        with self.assertRaisesRegex(ValueError,'Unsupported'):self.score()
    def test_a03_draft_and_hash_rejected(self):
        self.mapping['status']='DRAFT'
        with self.assertRaises(ValueError):self.score()
        self.mapping['status']='ACCEPTED';self.mapping['purpose']='changed'
        with self.assertRaises(ValueError):self.score()
    def test_a04_wrong_original_shape_no_gt(self):
        self.pred[0]['semantic']=np.ones((1,4),np.int16)
        with self.assertRaises(ValueError):self.score(gt=[])
    def test_a05_invalid_unmatched(self):
        for mask in (np.full((2,2),99),np.ones((2,2),float)):
            self.pred[0]['semantic']=mask
            with self.assertRaises(ValueError):self.score(gt=[])
        self.pred[0]['semantic']=np.ones((2,2),np.int16);self.pred[0]['score']=float('nan')
        with self.assertRaises(ValueError):self.score(gt=[])
    def test_a05_duplicate_ids(self):
        with self.assertRaises(ValueError):self.score(gt=[],pred=self.pred*2)
    def test_a06_no_semantic_still_fn(self):
        self.gt[0]['sem_eligible']=False
        r=self.score(pred=[])['metrics'];self.assertEqual(r['final_fn'],1);self.assertEqual(r['final_recall'],0);self.assertIsNone(r['Q_person_sem_GT'])
    def test_a07_missing_person_denominator(self):
        gs=[];ps=[]
        for i in range(10):
            g=copy.deepcopy(self.gt[0]);g.update(id=f'g{i}',bbox=[i*2,0,i*2+1,1]);gs.append(g)
            if i<8:
                p=copy.deepcopy(self.pred[0]);p.update(id=f'p{i}',bbox=g['bbox']);ps.append(p)
        r=self.score(gt=gs,pred=ps)['metrics'];self.assertEqual(r['G_sem'],10);self.assertEqual(r['Q_person_sem_GT'],.8)
    def test_a08_no_failure_event_double_fn(self):
        self.context.update(failure_policy='OPERATIONAL_EMPTY_FALLBACK',fallback_states=['PERSON_PARTIAL'])
        r=self.score(state='PERSON_PARTIAL');self.assertEqual(r['metrics']['final_fn'],0);self.assertEqual(r['failure_events'],['retained event'])
    def test_a08_a09_real_runner_failure_then_final_matching(self):
        from src.application_v2.runner import run_person_jobs, ModelSystemFailure
        from src.application_v2.scoring import lifecycle_from_person_result
        self.context.update(failure_policy='OPERATIONAL_EMPTY_FALLBACK',fallback_states=['PERSON_PARTIAL'])
        def worker(op):
            if op['id']=='bad':raise ModelSystemFailure('synthetic model failure')
            p=copy.deepcopy(self.pred[0]);p['evaluation_bbox']=dict(xyxy=p['bbox'],source='SYNTHETIC_PREDICTED_BOX',coordinate_convention='XYXY_HALF_OPEN',derivation_revision='fixture1');return p
        result=run_person_jobs('synthetic',[{'id':'good'},{'id':'bad'}],worker,failure_scope='PERSON',validate_output=lambda p:True)
        scored=score_frame(self.context,self.mapping,self.binding,self.input,self.gt,result['outputs'],lifecycle=lifecycle_from_person_result(result,'PERSON'))
        self.assertEqual(scored['metrics']['final_fn'],0);self.assertEqual(len(scored['failure_events']),1)
        self.assertEqual(result['opportunity_completion_rate']['denominator'],2)

    def test_a10_strict_and_operational(self):
        self.assertFalse(self.score(state='PERSON_PARTIAL')['score_eligible'])
        self.context.update(failure_policy='OPERATIONAL_EMPTY_FALLBACK',fallback_states=['MODEL_FRAME_FAILURE'])
        r=self.score(pred=[],state='MODEL_FRAME_FAILURE');self.assertEqual(r['metrics']['final_fn'],1);self.assertTrue(r['evaluator_fallback'])
        for state in ['EXTERNAL_INVALID','UNSCHEDULED','CONTRACT_FAILURE','UNRESOLVED','SHARED_DATA_ERROR']:
            self.assertFalse(self.score(pred=[],state=state)['score_eligible'])
    def test_a11_empty_not_perfect(self):
        r=self.score(gt=[],pred=[])['metrics'];self.assertIsNone(r['Q_person_sem_GT']);self.assertIsNone(r['final_recall'])
    def test_a12_leakage(self):
        g=self.gt[0];g['semantic']=np.array([[1]*100+[0]*900]);g['valid']=np.ones((1,1000),bool)
        p=self.pred[0];p['semantic']=np.array([[1]*100+[2]*900]);self.input['original_wh']=[1000,1];self.context['input_binding']=self.input.copy()
        r=self.score()['metrics'];self.assertEqual(r['Q_person_sem_GT'],1);self.assertEqual(r['Q_person_fg'],.1)
    def test_a13_owner_unknown(self):
        gt,valid=person_truth(np.array([[1,1,0]]),np.array([[1,0,0]]),np.ones((1,3),bool),1)
        self.assertEqual(valid.tolist(),[[True,False,True]])
    def test_a13_known_negative_versus_void_actual_scoring(self):
        self.gt[0]['semantic']=np.array([[1,0],[0,0]],np.int16)
        self.pred[0]['semantic']=np.array([[1,2],[0,0]],np.int16)
        self.assertEqual(self.score()['metrics']['Q_person_fg'],.5)
        self.gt[0]['valid'][0,1]=False
        self.assertEqual(self.score()['metrics']['Q_person_fg'],1)

    def test_finalizer_validator_exception_is_contract_failure(self):
        from src.application_v2.runner import run_person_jobs
        def validator(value):
            if value=='bad':raise ValueError('invalid final decoder ID')
            return True
        result=run_person_jobs('f',[{'id':'p'}],lambda _: 'good',failure_scope='PERSON',validate_output=validator,finalizer=lambda _:['bad'])
        self.assertEqual(result['failure_events'][0]['status'],'CONTRACT_FAILURE')
        self.assertEqual(result['outputs'],[])

    def test_a14_permutation(self):
        gs=[copy.deepcopy(self.gt[0]) for _ in range(2)];gs[1]['id']='h'
        ps=[copy.deepcopy(self.pred[0]) for _ in range(2)];ps[1]['id']='q'
        self.assertEqual(self.score(gt=gs,pred=ps)['metrics'],self.score(gt=gs[::-1],pred=ps[::-1])['metrics'])
    def test_a15_bbox_source(self):
        self.pred[0]['conditioning_bbox']=[100,100,200,200]
        self.assertEqual(self.score()['metrics']['final_recall'],1)
        self.pred[0]['evaluation_bbox']=dict(xyxy=[0,0,2,2],source='WRONG',coordinate_convention='XYXY_HALF_OPEN',derivation_revision='fixture')
        with self.assertRaises(ValueError):self.score()

    def test_a17_probability_unavailable(self):
        with self.assertRaises(ValueError):require_retention(['native_hard_labels'],'probability_aggregation')
        require_retention(['native_hard_labels'],'hard_remap')
    def test_actual_configured_runner_gates(self):
        import tempfile
        import yaml
        from src.application_v2.policy import load_config
        config=load_config(S/'configs/application_v2_handoff_v3.yaml')
        decisions=json.loads((S/config['decision_record']).read_text())
        config['scoring_context']=copy.deepcopy(self.context)
        decisions['decisions'].append({'id':'SCORING_CONTEXT','status':'ACCEPTED_BY_USER',
            'reason':'SYNTHETIC FIXTURE ONLY; never written to active study config',
            'bindings':{'scoring_context':config['scoring_context']}})
        config['decision_record_sha256']=digest(decisions)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'configs').mkdir()
            record=root/config['decision_record'];record.parent.mkdir(parents=True);record.write_text(json.dumps(decisions))
            for field in ['mapping','native_reference','sidecars_manifest']:
                q=root/config['cohort'][field];q.parent.mkdir(parents=True,exist_ok=True)
                q.write_bytes((S/config['cohort'][field]).read_bytes())
            # Bind the synthetic accepted mapping file itself, not a detached context.
            import hashlib
            mapping_path=root/config['cohort']['mapping']
            mapping_path.write_text(json.dumps(self.mapping))
            config['cohort']['mapping_sha256']=hashlib.sha256(mapping_path.read_bytes()).hexdigest()
            path=root/'configs/fixture.yaml';path.write_text(yaml.safe_dump(config))
            runner=ConfiguredRunner(path)
            predictions=copy.deepcopy(self.pred)
            predictions[0]['evaluation_bbox']=dict(xyxy=[0,0,2,2],source='SYNTHETIC_PREDICTED_BOX',coordinate_convention='XYXY_HALF_OPEN',derivation_revision='fixture1')
            score=lambda mapping,binding,preds:runner.score_frame(mapping,binding,self.input,self.gt,preds,lifecycle={'status':'COMPLETE'})
            self.assertEqual(score(self.mapping,self.binding,predictions)['metrics']['final_recall'],1)
            for field,value in [('checkpoint_sha256','e'*64),('config_sha256','e'*64),('head_classes',19),('native_class_order',list(reversed(range(20))))]:
                bad=copy.deepcopy(self.binding);bad[field]=value
                with self.subTest(field=field),self.assertRaises(ValueError):score(self.mapping,bad,predictions)
            for status in ['DRAFT','UNKNOWN']:
                bad=copy.deepcopy(self.mapping);bad['status']=status
                with self.subTest(status=status),self.assertRaises(ValueError):score(bad,self.binding,predictions)
            wrong=copy.deepcopy(predictions);wrong[0]['semantic']=np.ones((1,4),np.int16)
            with self.assertRaises(ValueError):score(self.mapping,self.binding,wrong)
            bad=copy.deepcopy(predictions);bad[0]['semantic'][:]=99
            with self.assertRaises(ValueError):score(self.mapping,self.binding,bad)
            config['scoring_context']['threshold']=.75
            path.write_text(yaml.safe_dump(config))
            with self.assertRaises(ValueError):ConfiguredRunner(path)

    def test_scoring_context_changes_scoring_fingerprint(self):
        from src.application_v2.policy import load_config,fingerprints
        config=load_config(S/'configs/application_v2_handoff_v3.yaml')
        config['scoring_context']=copy.deepcopy(self.context)
        before=fingerprints(config,{'input':'synthetic'})
        config['scoring_context']['failure_policy']='OPERATIONAL_EMPTY_FALLBACK'
        after=fingerprints(config,{'input':'synthetic'})
        self.assertEqual(before['inference'],after['inference'])
        self.assertNotEqual(before['scoring'],after['scoring'])

    def test_actual_runner_draft_closed(self):
        runner=ConfiguredRunner(S/'configs/application_v2.yaml')
        with self.assertRaisesRegex(ValueError,'No accepted scoring context'):
            runner.score_frame(self.mapping,self.binding,self.input,self.gt,self.pred,lifecycle={'status':'COMPLETE'})
    def test_cihp_lip_ten(self):
        self.assertEqual(project_prediction(np.array([[10]]),self.mapping,native_taxonomy='CIHP').item(),2)
        self.assertEqual(project_prediction(np.array([[10]]),self.mapping,native_taxonomy='LIP').item(),5)
    def test_legacy_prediction_rejected_gt_preserved(self):
        old=json.loads((S/'taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V1.json').read_text())
        with self.assertRaises(ValueError):project_prediction(np.array([[10]]),old,native_taxonomy='LIP')
        project_gt(np.array([[10]]),np.array([[1]]),old)
    def test_negative_human_rejected(self):
        with self.assertRaises(ValueError):project_gt(np.array([[13]]),np.array([[-1]]),self.mapping)
    def test_gsem_subset(self):
        self.gt[0]['loc_eligible']=False
        with self.assertRaises(ValueError):self.score()

if __name__=='__main__':unittest.main()
