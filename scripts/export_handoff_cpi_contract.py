"""Canonical export of fresh TRAIN CPI plus verified saved YOLO association.
No inference or GT-guided association; not a jointly timed live pipeline.
"""
from pathlib import Path
import sys,json,numpy as np
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S))
from src.application_v2.policy import load_config,digest,fingerprints
from src.application_v2.artifacts import file_hash,commit_packet,resume_packet
from src.application_v2.evaluation import associate_native
R=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run'];B=R/'native_smoke';cfg=load_config(S/'configs/application_v2_handoff_v3.yaml')
old=S/json.loads((S/'provenance/APPLICATION_V2_IMPLEMENTATION_ACTIVE.json').read_text())['run_path']
yolo_path=next(old.glob('bounded_train_*/YOLO.json'));yolo=json.loads(yolo_path.read_text());manifest=json.loads((B/'configs/TEN_IMAGE_MANIFEST.json').read_text());sample=manifest['images'][0]
frame=next(r for r in yolo['frames'] if r['image_id']==sample['image_id']);assert frame['input_sha256']==sample['input_sha256'];assert file_hash(yolo_path.parent/frame['artifact'])==frame['artifact_sha256']
results=[]
for path in sorted(B.glob('outputs/cpi_*/RUN.json')):
 native=json.loads(path.read_text());case=native['cases'][0];assert native['status']=='BOUNDED_NATIVE_PASS' and case['image_id']==sample['image_id']
 artifact=B/case['artifact'];assert file_hash(artifact)==case['artifact_sha256']
 with np.load(artifact,allow_pickle=False) as z:boxes=z['bboxes_xyxy_scores'].copy();masks=z['person_semantic_masks'].copy()
 instances=[{'id':f'native:{i}','bbox':b[:4].tolist()} for i,b in enumerate(boxes)]
 association=associate_native(frame['opportunities'],instances,cfg['bounded_train']['association_threshold'])
 for track in ['T1','T3B']:
  rows=[{'native_instance_id':v['id'],'source_opportunity_id':None} for v in instances] if track=='T1' else association['associations']
  persons=[];chosen=[]
  for row in rows:
   i=int(row['native_instance_id'].split(':')[-1])
   if not np.any(masks[i]>0):continue
   chosen.append(masks[i]);persons.append({'identity':{'origin':'NATIVE_MODEL' if track=='T1' else 'NATIVE_AND_YOLO','native_identity_supported':True,'native_instance_id':row['native_instance_id'],'conditioning_source':None if track=='T1' else 'YOLO','source_opportunity_id':row['source_opportunity_id'],'final_person_id':track+':'+row['native_instance_id']},'score':float(boxes[i,4]),'evaluation_bbox':{'xyxy':boxes[i,:4].tolist(),'source':'NATIVE_PARSER_BOX','coordinate_convention':'XYXY_HALF_OPEN','derivation_revision':file_hash(Path(__file__))},'conditioning_bbox':None if track=='T1' else next(o['bbox'] for o in frame['opportunities'] if o['id']==row['source_opportunity_id'])})
  w,h=sample['wh'];final=np.stack(chosen) if chosen else np.empty((0,h,w),np.uint8)
  record={'schema_version':'2.0','mask_grid_space':'ORIGINAL','original_wh':[w,h],'label_catalog':list(range(len(native['native_labels']))),'label_space':'NATIVE','study_id':'human_parsing_mhpv2','run_id':R.name,'system_id':native['model_id']+'_'+track,'model_id':native['model_id'],'image_id':sample['image_id'],'adapter_revision':file_hash(Path(__file__)),'execution_profile':'FRESH_NATIVE_SINGLE_TRAIN_FRAME'+('_SAVED_YOLO_ASSOCIATION' if track=='T3B' else ''),'source_track':track,'source_commit':native['source_commit'],'checkpoint_sha256':native['checkpoint_sha256'],'config_sha256':digest(cfg),'input_sha256':sample['input_sha256'],'geometry_metadata':{'native_artifact_sha256':case['artifact_sha256'],'association':association if track=='T3B' else None,'original_grid_verified_against_input_manifest':True},'precision_profile':{'native':'FP32','joint_pipeline_timing':'NOT_MEASURED'},'native_identity_supported':True,'native_instance_ids':[v['id'] for v in instances],'persons':persons,'dataset_split':'Training'}
  fp=fingerprints(cfg,{'native':case['artifact_sha256'],'yolo':frame['artifact_sha256'] if track=='T3B' else None,'export_adapter_sha256':file_hash(Path(__file__))});dest=R/'canonical_smoke'/record['system_id'];commit_packet(dest,record,final,fp,native_arrays={'native_person_masks':masks,'native_boxes_scores':boxes});resume_packet(dest,fp['inference']);results.append({'model':native['model_id'],'track':track,'persons':len(persons),'packet':str(dest.relative_to(S)),'canonical_contract':'PASS','scoring':'NOT_EXECUTED_DRAFT','live_joint_pipeline':False})
(R/'CANONICAL_SMOKE.json').write_text(json.dumps(results,indent=2));print('Verified canonical packets:',len(results))
