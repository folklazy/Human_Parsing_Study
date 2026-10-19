"""Bound existing GT/support/checkpoint evidence to the first DRAFT comparison.
No validation pixels are decoded and no predictions are scored.
"""
from pathlib import Path
import sys,json,csv,ast
from collections import defaultdict,Counter
import numpy as np
S=Path(__file__).resolve().parents[1];W=S.parent;sys.path.insert(0,str(S))
from src.application_v2.policy import load_config,digest
from src.application_v2.artifacts import file_hash
from src.application_v2.taxonomy import project_gt
R=S/json.loads((S/'provenance/FIRST_COHORT_READINESS_ACTIVE.json').read_text())['run']
config=load_config(S/'configs/application_v2_first_cohort_v4.yaml')
mapping=json.loads((S/config['cohort']['mapping']).read_text())
oldmapping=json.loads((S/'taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V1.json').read_text())
projection=lambda m:{k:m[k] for k in ['target_catalog','gt_mapping']}
assert projection(mapping)==projection(oldmapping)
manifest_path=S/config['cohort']['sidecars_manifest'];old=json.loads(manifest_path.read_text())
pops=json.loads((S/config['populations']['manifest']).read_text())
image_ledger=S/'provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/IMAGE_AUDIT.jsonl'
images={}
with image_ledger.open() as f:
 for line in f:
  row=json.loads(line)
  if row['split']=='Validation':images[row['image_id']]={'original_wh':row['wh'],'source_maps':row['source_maps']}
outputs={}
for population in pops['populations']:
 key=population['population']
 if key not in old['populations']:continue
 info=old['populations'][key];p=S/info['sidecar'];assert file_hash(p)==info['sidecar_sha256']
 frames={i:{'image_id':i,'G_loc':0,'G_sem':0,**images[i]} for i in population['ids']}
 persons=0;support=Counter();reasons=Counter()
 with p.open() as f:
  for line in f:
   row=json.loads(line);image=row['person_key'][2];assert image in frames
   frames[image]['G_loc']+=int(row['G_loc_structural_draft']);frames[image]['G_sem']+=int(row['G_sem_common_candidate_draft']);persons+=1
   support.update(row['candidate_class_support'])
   if not row['G_sem_common_candidate_draft']:
    reasons['no_candidate_semantic_support']+=1
    reasons['no_native_known_support' if not row['G_sem_native_known_draft'] else 'known_only_outside_candidate']+=1
 assert len(frames)==info['images'] and persons==info['G_native']
 assert sum(f['G_sem'] for f in frames.values())==info['G_sem_common_candidate_draft']
 assert dict(support)==info['candidate_class_support']
 target=R/(key+'_expected_frames.jsonl')
 with target.open('x') as f:
  for key_id in sorted(frames):f.write(json.dumps(frames[key_id],separators=(',',':'))+'\n')
 outputs[key]={'frames':len(frames),'G_loc_structural_draft':persons,'G_sem_candidate_draft':sum(f['G_sem'] for f in frames.values()),'semantic_undefined_reasons':dict(reasons),'target_class_pixel_support':dict(support),'expected_frame_manifest':str(target.relative_to(S)),'expected_frame_manifest_sha256':file_hash(target),'original_person_sidecar':info['sidecar'],'original_person_sidecar_sha256':info['sidecar_sha256'],'role_accepted':False,'physical_person_certification':False}
(R/'POPULATION_BINDINGS_DRAFT.json').write_text(json.dumps({'status':'DERIVED_METADATA_VERIFIED_POPULATION_ROLE_DRAFT','source_population_manifest':config['populations']['manifest'],'source_population_sha256':file_hash(S/config['populations']['manifest']),'GT_projection_content_sha256':digest(projection(mapping)),'V1_V2_GT_projection_identity':True,'new_GT_decoding_on_validation':False,'populations':outputs},indent=2))

source=W/'third_party/human_parsing/CPI-Parser'
class_source=W/'third_party/human_parsing/M2FP/m2fp/data/datasets/register_cihp_parsing.py'
tree=ast.parse(class_source.read_text());native=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CIHP_PARSING_CATEGORIES' for t in n.targets))
labels={str(v['id']):v['name'] for v in native if v['id']<20}
H=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run'];runs=json.loads((H/'SMOKE_SUMMARY.json').read_text());bindings=[]
for model in config['first_cohort']['models']:
 prior=next(r for r in runs if r['model_id']==model);run=json.loads((S/prior['run_manifest']).read_text())
 assert run['native_labels']==labels
 cfgname='causal_parser_'+('r50' if 'R50' in model else 'convnext_b')+'_inter_8_135k_cihp.py';cfg=source/'configs/COSParser'/cfgname
 assert file_hash(cfg)==run['config_source_sha256']
 assert 'num_parse_classes=20' in run['resolved_config'] and run['checkpoint_loaded'] and run['status']=='BOUNDED_NATIVE_PASS'
 packet=H/'canonical_smoke'/(model+'_T3B');record=json.loads((packet/'record.json').read_text())
 assert record['checkpoint_sha256']==run['checkpoint_sha256']
 binding={'model_id':model,'checkpoint_sha256':run['checkpoint_sha256'],'native_config_source_sha256':run['config_source_sha256'],'resolved_config_sha256':digest(run['resolved_config']),'source_commit':run['source_commit'],'head_classes':20,'native_class_order':[labels[str(i)] for i in range(20)],'native_class_order_sha256':digest([labels[str(i)] for i in range(20)]),'mapping_sha256':digest(mapping),'structural_binding':'VERIFIED','semantic_mapping_review':'DRAFT_NOT_ACCEPTED','candidate_representable_target_ids':sorted({int(v['target_id']) for v in mapping['prediction_mappings']['CIHP'].values() if v['disposition']=='MAP' and v['target_id']>0}),'automatic_membership_by_name':False,'benchmark_eligible':False,'evidence_references':[prior['run_manifest'],str(cfg.relative_to(W)),str(class_source.relative_to(W)),str((source/'mmdet/datasets/pipelines/loading.py').relative_to(W))]}
 bindings.append(binding)
(R/'CHECKPOINT_SUPPORT_BINDINGS_DRAFT.json').write_text(json.dumps(bindings,indent=2))

# Explicitly source-backed definitions, without claiming released CIHP/CCIHP masks are equal.
readme=S/'provenance/RUN_MANIFESTS/stage0e-ccihp-native-20261012T045912Z/archive_documents/README.md'
readme_names={1:'Hat',2:'Hair',3:'Glove',4:'Sunglasses/Glasses',5:'UpperClothes',6:'Face Mask',7:'Coat',8:'Socks',9:'Pants',10:'Torso-skin',11:'Scarf',12:'Skirt',13:'Face',14:'Left-arm (naked part)',15:'Right-arm (naked part)',16:'Left-leg (naked part)',17:'Right-leg (naked part)',18:'Left-shoe',19:'Right-shoe',20:'Bag',21:'Others',22:'UNDEFINED_RELEASE_ID_22',0:'Reserved zero; background/unknown policy under review'}
rows=[]
for i in range(23):
 gt=mapping['gt_mapping'][str(i)];pred=mapping['prediction_mappings']['CIHP'].get(str(i))
 rows.append({'GT_native_id':i,'GT_declared_name':readme_names[i],'GT_disposition':gt['disposition'],'GT_target_id':gt.get('target_id'),'CIHP_prediction_name':labels.get(str(i),'NO_NATIVE_CLASS'),'prediction_disposition':pred['disposition'] if pred else 'UNSUPPORTED','prediction_target_id':pred.get('target_id') if pred else None,'scope_note':'Same numeric ID does not imply same semantics; GT6 Face Mask and prediction6 Dress intentionally differ','review_status':'DRAFT_DOCUMENTED_CONCEPTS_NOT_FROZEN'})
with (R/'CLASS_MAPPING_EVIDENCE_DRAFT.csv').open('x') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

pilot=W/'Human_Parsing_CCIHP_10_Image_Pilot';inputs=json.loads((pilot/'configs/TEN_IMAGE_MANIFEST.json').read_text());sample=next(r for r in inputs['images'] if r['image_id']=='0000930');assert sample['split']=='Training';assert file_hash(pilot/sample['input'])==sample['input_sha256']
with np.load(pilot/sample['input'],allow_pickle=False) as z:category=z['category'].copy();human=z['human'].copy()
projected,valid=project_gt(category,human,mapping)
released=valid.copy();envelope=valid&(human>0)
np.savez_compressed(R/'TRAIN_DOMAIN_PROPOSALS.npz',target=projected,released_background_candidate= released,human_envelope_candidate=envelope)
train_persons=[]
for pid in sorted(int(p) for p in np.unique(human) if p>0):
 target_mask=(human==pid)&valid&(projected>0);train_persons.append({'person_id':pid,'G_loc':True,'G_sem':bool(target_mask.any())})
train={'image_id':sample['image_id'],'source_split':'Training','input_sha256':sample['input_sha256'],'original_wh':sample['wh'],'G_loc':len(train_persons),'G_sem':sum(p['G_sem'] for p in train_persons),'persons':train_persons,'domain_candidates':{'released_background_negative':{'valid_pixels':int(released.sum()),'zero_human_zero_category_pixels':int(((human==0)&(category==0)).sum()),'status':'DRAFT_COMPLETENESS_ASSUMPTION_NOT_ESTABLISHED'},'human_envelope_only':{'valid_pixels':int(envelope.sum()),'status':'DRAFT_DIFFERENT_DOMAIN_LIMITS_BACKGROUND_FP_INTERPRETATION'}},'shared_unknown':{'unsupported_or_unresolved_GT_pixels':int((~valid).sum()),'category0_inside_human_pixels':int(((category==0)&(human>0)).sum()),'owner_unknown_target_pixels':int(((projected>0)&(human==0)&valid).sum())},'source_GT':sample['source_gt'],'model_metrics_computed':False}
(R/'TRAIN_DOMAIN_REVIEW.json').write_text(json.dumps(train,indent=2))
(R/'MAPPING_DOMAIN_REVIEW_DRAFT.json').write_text(json.dumps({'status':'DRAFT_REVIEW_REQUIRED','source_definitions_verified':True,'CCIHP_author_README_sha256':file_hash(readme),'CIHP_class_source_sha256':file_hash(class_source),'GT_projection_V1_V2_identical':True,'semantic_questions':['Coarse selected-garment union is intentional and is not native CIHP equivalence','CCIHP category6 Face Mask is VOID; CIHP prediction6 Dress maps to coarse garment','Face/body-part names do not certify every pixel boundary or every physical person','Reserved zero outside Human does not independently prove visible-person annotation completeness','Unknown22 and Category0 inside Human are not silently converted to known background'],'mapping_acceptance':False,'domain_acceptance':False,'primary_population_acceptance':False,'predictions_used_to_select_policy':False},indent=2))
print(json.dumps({'population_metadata':'PASS','V1_V2_GT_projection_identical':True,'checkpoint_structural_bindings':len(bindings),'TRAIN_domain_proposals':2,'real_scoring_context_accepted':False}))
