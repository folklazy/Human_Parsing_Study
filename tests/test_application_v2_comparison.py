"""Accepted strict/cohort policy tests; synthetic data, never a real benchmark."""
from pathlib import Path
import sys, json, copy, unittest
import numpy as np
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S))
from src.application_v2.policy import load_config,validate_config,digest
from src.application_v2.runner import ConfiguredRunner
from src.application_v2.scoring import score_frame
from src.application_v2.cohorts import validate_support_binding

class StrictRunTests(unittest.TestCase):
    def setUp(self):
        self.config=load_config(S/'configs/application_v2_first_cohort_v5.yaml')
        self.runner=ConfiguredRunner(S/'configs/application_v2_first_cohort_v5.yaml')
        self.a,self.b=self.config['first_cohort']['models']
        self.population=[{'image_id':'one','G_loc':1,'G_sem':1},{'image_id':'two','G_loc':1,'G_sem':1}]
    def numerical_report(self,population,frames):
        from src.application_v2.comparison import summarize_comparison
        return summarize_comparison({'comparison_id':'SYNTHETIC_ONLY','definition_sha256':'fixture'},population,[self.a,self.b],frames,self.config['primary_reporting_policy'])
    def frame(self,system,image,*,quality=1,empty=False):
        metrics={'G_loc':1,'G_sem':1,'matching':{'matches':[] if empty else [['g','p',1.0]]},'final_fp':0,'final_fn':1 if empty else 0,'Q_person_sem_GT':0 if empty else quality}
        return {'system_id':system,'image_id':image,'execution_status':'COMPLETE','failure_events':[],
                'score_result':{'score_eligible':True,'status':'COMPLETE','metrics':metrics,'failure_events':[]}}
    def test_incomplete_retained_main_null_diagnostic_labeled(self):
        report=self.numerical_report(self.population,[self.frame(self.a,'one'),{'system_id':self.a,'image_id':'two','execution_status':'FAILED','failure_events':[{'type':'OOM'}]}])
        a,b=report['systems'];self.assertEqual(a['status'],'INCOMPLETE');self.assertIsNone(a['main_metrics']);self.assertEqual(a['execution']['denominator'],2);self.assertEqual(a['execution']['failed'],1)
        self.assertEqual(a['success_only_diagnostic']['Q_person_sem_GT'],1);self.assertEqual(a['success_only_diagnostic']['G_sem_observed'],1)
        self.assertEqual(b['status'],'INCOMPLETE');self.assertEqual(b['execution']['not_attempted_or_unscheduled'],2)
        self.assertEqual(len(report['systems']),2)
    def test_valid_empty_execution_success_but_fn(self):
        frames=[self.frame(s,i,empty=True) for s in [self.a,self.b] for i in ['one','two']]
        a=self.numerical_report(self.population,frames)['systems'][0]
        self.assertEqual(a['status'],'COMPLETE');self.assertEqual(a['execution']['failed'],0)
        self.assertEqual(a['main_metrics']['FN'],2);self.assertEqual(a['main_metrics']['Q_person_sem_GT'],0)
    def test_denominator_cannot_follow_scored_subset(self):
        f=self.frame(self.a,'one');f['score_result']['metrics']['G_sem']=0
        with self.assertRaises(ValueError):self.numerical_report(self.population,[f])
    def test_posthoc_retry_cannot_overwrite_failure(self):
        with self.assertRaises(ValueError):self.numerical_report(self.population,[self.frame(self.a,'one'),self.frame(self.a,'one')])
    def test_failed_frame_cannot_call_itself_complete(self):
        f=self.frame(self.a,'one');f['failure_events']=[{'type':'MODEL_FAILURE'}]
        with self.assertRaises(ValueError):self.numerical_report(self.population,[f])
    def test_real_data_context_not_accepted_by_two_policy_decisions(self):
        rows=[{'system_id':s,'image_id':i,'execution_status':'COMPLETE'} for s in [self.a,self.b] for i in ['one','two']]
        for row in self.numerical_report(self.population,rows)['systems']:
            self.assertEqual(row['status'],'BLOCKED_SCORING_POLICY');self.assertIsNone(row['main_metrics'])
    def test_group_quality_is_person_weighted_not_frame_weighted(self):
        self.population[1].update(G_loc=9,G_sem=9)
        f=self.frame(self.a,'two',quality=0);f['score_result']['metrics'].update(G_loc=9,G_sem=9,final_fn=9,matching={'matches':[]})
        a=self.numerical_report(self.population,[self.frame(self.a,'one'),f])['systems'][0]
        self.assertAlmostEqual(a['main_metrics']['Q_person_sem_GT'],.1)
    def test_actual_runner_rejects_unbound_eligible_metric_payload(self):
        with self.assertRaisesRegex(ValueError,'accepted, bound'):
            self.runner.comparison_report(self.population,[self.frame(self.a,'one')])
    def test_actual_runner_comparison_id_changes_with_population(self):
        before=self.runner.comparison_report(self.population,[])
        modified=copy.deepcopy(self.population);modified[1]['G_loc']=2
        after=self.runner.comparison_report(modified,[])
        self.assertNotEqual(before['comparison']['comparison_id'],after['comparison']['comparison_id'])
    def test_no_semantic_gt_remains_localization_fn(self):
        population=[{'image_id':'one','G_loc':1,'G_sem':0}]
        f=self.frame(self.a,'one',empty=True);f['score_result']['metrics'].update(G_sem=0,Q_person_sem_GT=None)
        a=self.numerical_report(population,[f])['systems'][0]
        self.assertIsNone(a['main_metrics']['Q_person_sem_GT'])
        self.assertEqual(a['main_metrics']['FN'],1)
        self.assertEqual(a['main_metrics']['localization_recall'],0)
    def test_training_scope_cannot_silently_become_validation(self):
        d=json.loads((S/self.config['decision_record']).read_text());self.config['first_cohort']['engineering']['split']='Validation'
        with self.assertRaises(ValueError):validate_config(self.config,d)
    def test_association_and_GT_matching_have_separate_dependencies(self):
        from src.application_v2.policy import fingerprints
        before=fingerprints(self.config,{'native':'fixture'})
        self.config['evaluation']['threshold']=.75
        scoring_only=fingerprints(self.config,{'native':'fixture'})
        self.assertEqual(before['inference'],scoring_only['inference'])
        self.assertNotEqual(before['scoring'],scoring_only['scoring'])
        self.config['inference_dependencies']['prediction_only_association']['threshold']=.75
        self.assertNotEqual(scoring_only['inference'],fingerprints(self.config,{'native':'fixture'})['inference'])
    def test_loaded_runner_cannot_silently_change_accepted_policy(self):
        self.runner.config['primary_reporting_policy']['incomplete_systems_retained']=False
        with self.assertRaisesRegex(ValueError,'mutated'):
            self.runner.comparison_report(self.population,[])
    def test_policy_edit_conflicts_with_accepted_record(self):
        decisions=json.loads((S/self.config['decision_record']).read_text());self.config['primary_reporting_policy']['incomplete_systems_retained']=False
        with self.assertRaises(ValueError):validate_config(self.config,decisions)
    def test_cohort_policy_cannot_be_changed_to_dataset_name(self):
        decisions=json.loads((S/self.config['decision_record']).read_text());self.config['cohort_policy']['dataset_name_implies_eligibility']=True
        with self.assertRaises(ValueError):validate_config(self.config,decisions)
    def test_full_benchmark_guard_stays_closed(self):
        with self.assertRaises(ValueError):load_config(S/'configs/application_v2_first_cohort_v5.yaml',benchmark=True)

class CheckpointSupportTests(unittest.TestCase):
    def setUp(self):
        self.mapping=json.loads((S/'taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V2.json').read_text())
        self.mapping['status']='ACCEPTED' # synthetic object only, never changes active mapping
        self.model={'checkpoint_sha256':'a'*64,'config_sha256':'b'*64,'source_commit':'c'*40,'native_class_order':list(range(20)),'native_taxonomy':'CIHP','head_classes':20}
        support={'status':'VERIFIED','checkpoint_sha256':self.model['checkpoint_sha256'],'config_sha256':self.model['config_sha256'],'source_commit':self.model['source_commit'],'native_class_order_sha256':digest(self.model['native_class_order']),'mapping_sha256':digest(self.mapping),'target_catalog_sha256':digest(self.mapping['target_catalog']),'evidence_references':['synthetic source fixture'],'semantic_review':'VERIFIED','supported_target_ids':[1,2,3,4,5,6]}
        self.input={'status':'VERIFIED','original_wh':[2,2],'input_sha256':'d'*64}
        self.context={'status':'ACCEPTED','mapping_sha256':digest(self.mapping),'model_binding':copy.deepcopy(self.model),'input_binding':self.input,'domain':{'status':'ACCEPTED','evidence':'synthetic complete annotation'},'target_support_policy':'COMMON_CAPABILITY','require_checkpoint_specific_support':True,'support_binding':support,'failure_policy':'STRICT_COMPLETE','evaluation_bbox_source':'SYNTHETIC','threshold':.5}
    def score(self):
        return score_frame(self.context,self.mapping,self.model,self.input,[],[],lifecycle={'status':'COMPLETE','events':[]})
    def test_checkpoint_name_does_not_imply_support(self):
        self.context['support_binding']['supported_target_ids'].remove(2)
        with self.assertRaisesRegex(ValueError,'Checkpoint does not support'):self.score()
    def test_same_dataset_other_checkpoint_rejected(self):
        self.context['support_binding']['checkpoint_sha256']='e'*64
        with self.assertRaises(ValueError):self.score()
    def test_semantic_review_pending_rejected(self):
        self.context['support_binding']['semantic_review']='DRAFT'
        with self.assertRaises(ValueError):self.score()
    def test_configured_runner_enforces_checkpoint_support(self):
        import tempfile,hashlib,yaml
        config=load_config(S/'configs/application_v2_first_cohort_v5.yaml')
        decisions=json.loads((S/config['decision_record']).read_text())
        config['scoring_context']=copy.deepcopy(self.context)
        decisions['decisions'].append({'id':'SCORING_CONTEXT','status':'ACCEPTED_BY_USER','bindings':{'scoring_context':config['scoring_context']},'reason':'SYNTHETIC ONLY'})
        config['decision_record_sha256']=digest(decisions)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'configs').mkdir();rec=root/config['decision_record'];rec.parent.mkdir(parents=True);rec.write_text(json.dumps(decisions))
            for field in ['mapping','native_reference','sidecars_manifest']:
                p=root/config['cohort'][field];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((S/config['cohort'][field]).read_bytes())
            p=root/config['cohort']['mapping'];p.write_text(json.dumps(self.mapping));config['cohort']['mapping_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            path=root/'configs/fixture.yaml';path.write_text(yaml.safe_dump(config))
            runner=ConfiguredRunner(path)
            result=runner.score_frame(self.mapping,self.model,self.input,[],[],lifecycle={'status':'COMPLETE'})
            self.assertTrue(result['score_eligible'])
            # A different checkpoint with the same CIHP name is not sufficient.
            wrong=copy.deepcopy(self.model);wrong['checkpoint_sha256']='f'*64
            with self.assertRaises(ValueError):runner.score_frame(self.mapping,wrong,self.input,[],[],lifecycle={'status':'COMPLETE'})
            # Config context and the executable mapping file cannot disagree.
            changed=copy.deepcopy(self.mapping);changed['status']='DRAFT';p.write_text(json.dumps(changed));config['cohort']['mapping_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();path.write_text(yaml.safe_dump(config))
            with self.assertRaisesRegex(ValueError,'accepted executable cohort mapping'):ConfiguredRunner(path)
    def test_verified_support_fixture_passes(self):
        self.assertTrue(self.score()['score_eligible'])
    def test_no_support_binding_is_not_automatic_eligibility(self):
        self.context.pop('support_binding')
        with self.assertRaises(ValueError):self.score()

if __name__=='__main__':unittest.main()
