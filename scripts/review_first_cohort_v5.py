"""Validate V5 association/config lineage from saved fresh TRAIN outputs.
No inference and no real-data quality scores. Not a production cached scorer.
"""
from pathlib import Path
import sys,json,copy
import numpy as np
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S))
from src.application_v2.policy import load_config,digest,fingerprints
from src.application_v2.artifacts import file_hash,commit_packet,resume_packet
from src.application_v2.evaluation import associate_native
from src.application_v2.runner import ConfiguredRunner
R=S/json.loads((S/'provenance/FIRST_COHORT_READINESS_ACTIVE.json').read_text())['run'];b=R/'live_route'
a=load_config(S/'configs/application_v2_first_cohort_v4.yaml');c=load_config(S/'configs/application_v2_first_cohort_v5.yaml')
for key in ['bounded_train','primary_reporting_policy','cohort_policy','evaluation','cohort']:
    assert a[key]==c[key]
assert a['first_cohort']['draft_matching']['threshold']==c['first_cohort']['draft_association']['threshold']
y=json.loads((b/'YOLO.json').read_text());assert file_hash(S/y['artifact'])==y['artifact_sha256']
evidence=json.loads((b/'ROUTE_EVIDENCE.json').read_text());rows=[];lineage=[]
for e in evidence:
    record=json.loads((S/e['canonical_packet']/'record.json').read_text());run=json.loads((S/e['native_run']).read_text());case=run['cases'][0]
    artifact=b/case['artifact'];assert file_hash(artifact)==case['artifact_sha256']
    with np.load(artifact,allow_pickle=False) as z:
        boxes=z['bboxes_xyxy_scores'].copy();native_masks=z['person_semantic_masks'].copy()
    native=[{'id':f'native:{i}','bbox':box[:4].tolist()} for i,box in enumerate(boxes)]
    association=associate_native(y['opportunities'],native,c['first_cohort']['draft_association']['threshold'])
    assert association==record['geometry_metadata']['association']
    # Rebuild canonical association packets from retained raw components under V5.
    # Exact native weights/config/source are explicit dependencies, even if two
    # checkpoints happened to produce byte-identical masks.
    output=copy.deepcopy(record)
    output.update(config_sha256=digest(c),adapter_revision=file_hash(Path(__file__)),
                  execution_profile='V5_DERIVED_FROM_ACTUAL_V4_COMPONENT_INFERENCE')
    output['geometry_metadata']['association']=association
    with np.load(S/e['canonical_packet']/'arrays.npz',allow_pickle=False) as z:
        final_masks=z['canonical_semantic_masks'].copy()
    dependencies={'input_sha256':y['input_sha256'],'native_checkpoint_sha256':run['checkpoint_sha256'],
                  'native_source_commit':run['source_commit'],'native_config_source_sha256':run['config_source_sha256'],
                  'native_resolved_config_sha256':digest(run['resolved_config']),
                  'native_class_order_sha256':digest(run['native_labels']),
                  'YOLO_checkpoint_sha256':y['checkpoint_sha256'],'native_artifact_sha256':case['artifact_sha256'],
                  'YOLO_artifact_sha256':y['artifact_sha256'],'adapter_revision':file_hash(Path(__file__))}
    fp=fingerprints(c,dependencies);packet=R/'canonical_v5'/e['model']
    commit_packet(packet,output,final_masks,fp,native_arrays={'native_person_masks':native_masks,'native_boxes_scores':boxes})
    resume_packet(packet,fp['inference'])

    rows.append({'system_id':e['model'],'image_id':e['image_id'],'execution_status':'COMPLETE','failure_events':[],
                 'stage_rates':{'native_frame':{'stage':'native_parser','unit':'frame','numerator':1,'denominator':1},
                                'association':{'stage':'YOLO_opportunity_association','unit':'opportunity','numerator':len(y['opportunities']),'denominator':len(y['opportunities'])}}})
    lineage.append({'model':e['model'],'native_artifact_sha256':case['artifact_sha256'],'YOLO_artifact_sha256':y['artifact_sha256'],
                    'association_identical_to_executed_V4_route':True,'GT_evaluation_threshold_not_used_for_association':True,
                    'old_canonical_packet_reused_as_V5_inference':False,'quality_scores_computed':False,'canonical_V5_packet':str(packet.relative_to(S)),'inference_dependencies':dependencies})
t=json.loads((R/'TRAIN_DOMAIN_REVIEW.json').read_text());population=[{'image_id':t['image_id'],'G_loc':t['G_loc'],'G_sem':t['G_sem']}]
status=ConfiguredRunner(S/'configs/application_v2_first_cohort_v5.yaml').comparison_report(population,rows)
assert all(x['main_metrics'] is None and x['status']=='BLOCKED_SCORING_POLICY' for x in status['systems'])
(R/'COMPARISON_ENGINEERING_STATUS_V5.json').write_text(json.dumps(status,indent=2)+'\n')
(R/'V4_TO_V5_LINEAGE.json').write_text(json.dumps({'current_config':'configs/application_v2_first_cohort_v5.yaml','current_config_sha256':file_hash(S/'configs/application_v2_first_cohort_v5.yaml'),'executed_config':'configs/application_v2_first_cohort_v4.yaml','executed_config_sha256':file_hash(S/'configs/application_v2_first_cohort_v4.yaml'),'GT_projection_unchanged':True,'native_input_and_preprocessing_unchanged':True,'source_outputs_are_actual_inference':True,'derived_analysis_uses_saved_outputs_only':True,'model_inference_rerun_in_this_review':False,'models':lineage},indent=2)+'\n')
print('V5 prediction-only association lineage PASS; real scoring stays blocked')
