"""Deterministic evidence summary: no inference, scoring, or source-data writes."""
from pathlib import Path
import json,csv,hashlib,subprocess,datetime,sys
S=Path(__file__).resolve().parents[1];W=S.parent;sys.path.insert(0,str(S))
from src.application_v2.artifacts import file_hash
from src.application_v2.acquisition import verify_asset_set
R=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run'];B=R/'native_smoke'
before=json.loads((R/'LOCAL_CHECKPOINTS.json').read_text());added=json.loads((R/'ADDITIONAL_ASSET_RESULTS.json').read_text())
initial={x['path']:x for x in before['files']};rows=list(initial.values());required=[]
for a in added['rows']:
 if a['status']!='VERIFIED_LOCAL_FINGERPRINT':continue
 p=W/a['path'];required.append({'path':a['path'],'bytes':a['bytes'],'sha256':a['sha256']})
 if p.suffix=='.pth' and a['path'] not in initial:rows.append({'path':a['path'],'bytes':a['bytes'],'sha256':a['sha256'],'existing_before_this_run':False,'role':a['role'],'source_url':a['source_url'],'original_filename':a['original_filename']})
asset_validation=verify_asset_set(W,required)
(R/'ADDITIONAL_ASSET_SET_VALIDATION.json').write_text(json.dumps(asset_validation,indent=2))
inodes={};unique={}
for row in rows:
 p=W/row['path'];st=p.stat();inodes[(st.st_dev,st.st_ino)]=st.st_size;unique[row['sha256']]=row['bytes'];row['symlink']=p.is_symlink();row['local_fingerprint_only']=True
new_weights=[x for x in rows if not x['existing_before_this_run']]
summary={'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checkpoint_path_entries_including_aliases':len(rows),'unique_inode_files':len(inodes),'unique_content_artifacts':len(unique),'unique_checkpoint_content_bytes':sum(unique.values()),'new_checkpoint_artifacts':len(new_weights),'new_parser_checkpoints':sum(x['role']=='PARSER_CHECKPOINT' for x in new_weights),'new_auxiliary_checkpoints':sum(x['role']=='AUXILIARY_DETECTOR' for x in new_weights),'new_checkpoint_bytes':sum(x['bytes'] for x in new_weights),'all_human_parsing_storage_allocated_bytes_including_old_partials':int(subprocess.check_output(['du','-s','-B1',str(W/'models/human_parsing')],text=True).split()[0]),'files':rows,'limits':'Complete relative to the author-linked roster audited here, not every human-parsing model ever published. Old aliases retained. No old partials deleted.'}
(R/'CHECKPOINT_MANIFEST.json').write_text(json.dumps(summary,indent=2))
smokes=[]
for p in sorted(B.glob('outputs/*/RUN.json')):
 d=json.loads(p.read_text());valid=[]
 for case in d['cases']:
  q=B/case['artifact'];assert file_hash(q)==case['artifact_sha256'];valid.append(case['image_id'])
 smokes.append({'model_id':d['model_id'],'status':d['status'],'checkpoint_sha256':d['checkpoint_sha256'],'source_commit':d['source_commit'],'checkpoint_loaded':d.get('checkpoint_loaded',False),'native_class_count':len(d['native_labels']),'native_class_order_sha256':hashlib.sha256(json.dumps(d['native_labels'],sort_keys=True).encode()).hexdigest(),'mode':d.get('source_track',d.get('native_mode')),'input_ids':valid,'precision':d.get('precision'),'cases':len(valid),'peak_allocated_mib':max((c['peak_allocated_vram_mib'] for c in d['cases']),default=None),'peak_reserved_mib':max((c['peak_reserved_vram_mib'] for c in d['cases']),default=None),'run_manifest':str(p.relative_to(S)),'run_manifest_sha256':file_hash(p),'component_only':d.get('not_complete_multi_person_pipeline',False),'canonical_contract':'PASS_T1_AND_T3B_SAVED_YOLO' if d['model_id'].startswith('CPI_') else 'NOT_TESTED_IN_THIS_NATIVE_RUN'})
(R/'SMOKE_SUMMARY.json').write_text(json.dumps(smokes,indent=2))
registry=[]
for d in smokes:
 artifact=next(x for x in rows if x['sha256']==d['checkpoint_sha256']);registry.append({**d,'checkpoint_path':artifact['path'],'checkpoint_bytes':artifact['bytes'],'acquisition_status':'VERIFIED_LOCAL_FINGERPRINT','use_eligibility':'NONCOMMERCIAL_RESEARCH_CONDITIONAL_PRIOR_REVIEW_NO_NEW_COMMERCIAL_CLEARANCE','comparison_ready':False})
for size in ['0.4b','0.8b','1b','5b']:
 a=next(x for x in rows if x['path'].endswith('/'+size+'/sapiens2_'+size+'_seg.safetensors'));registry.append({'model_id':'Sapiens2_'+size,'checkpoint_path':a['path'],'checkpoint_sha256':a['sha256'],'checkpoint_bytes':a['bytes'],'acquisition_status':'VERIFIED_LOCAL_FINGERPRINT_EXISTING','use_eligibility':'USE_RESTRICTED_SURVEILLANCE_RESEARCH','status':'NOT_TESTED_THIS_REVISION','comparison_ready':False})
for mid,reason in [('M2FP_PASCAL','Official model table has no checkpoint link'),('CDGNet_LIP','Official trained weights linked on Baidu; public direct artifact not obtained; no access circumvention'),('QANet_MHPV2','No official trained parser release in audited table'),('QANet_CIHP_ResNet101','Official table row has no download link')]:registry.append({'model_id':mid,'acquisition_status':'NOT_OBTAINED','status':'BLOCKED','reason':reason,'comparison_ready':False})
keys=sorted(set().union(*(r.keys() for r in registry)))
with (S/'provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V4.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in registry)
print(json.dumps({k:v for k,v in summary.items() if k!='files'},indent=2));print('native checkpoint smoke PASS:',sum(r['status']=='BOUNDED_NATIVE_PASS' for r in smokes))
