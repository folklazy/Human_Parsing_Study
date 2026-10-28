"""Audit evaluation inputs only; preserve source bytes and report every exception."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,argparse,collections,hashlib,time
P=Path(__file__).resolve().parents[1];W=P.parent;sys.path.insert(0,str(P/'src'))
from cihp_benchmark.data import read_sample,read_image,file_hash
import numpy as np
import PIL
p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();out=Path(args.output);root=W/'datasets/CIHP'
ids={s:(root/s/name).read_text().split() for s,name in [('Training','train_id.txt'),('Validation','val_id.txt'),('Testing','test_id.txt')]}
result={'start_utc':datetime.now(timezone.utc).isoformat(),'decoder':{'Pillow':PIL.__version__,'numpy':np.__version__},'splits':{},'failures':[],'warnings':collections.Counter(),'semantic_values':collections.Counter(),'mask_modes':collections.Counter(),'persons':0,'checked_validation_images':0,'checked_training_images':0,'GT_repaired':False,'split_ID_overlap':{a+'_'+b:sorted(set(ids[a])&set(ids[b])) for a,b in [('Training','Validation'),('Training','Testing'),('Validation','Testing')]}}
for split,keys in ids.items():
 info={'ids':len(keys),'unique':len(set(keys)),'split_list_sha256':file_hash(root/split/({'Training':'train_id.txt','Validation':'val_id.txt','Testing':'test_id.txt'}[split])),'missing':{},'orphan':{}}
 for typ in (['Images'] if split=='Testing' else ['Images','Category_ids','Human_ids','Instance_ids']):
  existing={f.stem for f in (root/split/typ).iterdir()};info['missing'][typ]=sorted(set(keys)-existing);info['orphan'][typ]=sorted(existing-set(keys))
 result['splits'][split]=info
# Reuse intake hashes for exact JPEG-byte duplicate grouping: no Training image decode.
intake=json.loads((P/'manifests/CIHP_NATIVE_IMPORT.json').read_text());inventory=W/intake['file_inventory_workspace_relative'];train=collections.defaultdict(list);val=collections.defaultdict(list)
with inventory.open() as f:
 for line in f:
  row=json.loads(line);parts=Path(row['relative_path']).parts
  if len(parts)==3 and parts[1]=='Images' and parts[0] in ['Training','Validation']:
   (train if parts[0]=='Training' else val)[row['sha256']].append(Path(parts[2]).stem)
result['exact_train_VAL_groups']=[{'sha256':h,'train_ids':train[h],'validation_ids':v} for h,v in val.items() if h in train]
result['exact_within_VAL_groups']=[{'sha256':h,'ids':v} for h,v in val.items() if len(v)>1]
result['exact_overlap_policy']='Keep all official5000 as primary; duplicate/exposure limitation disclosed; no automatic exclusion or re-selection from scores.'
legacy=W/'Human_Parsing_MHPv2_Study/provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/VALIDATION_INPUTS.jsonl';old={r['image_id']:r for r in map(json.loads,legacy.open())};same_old=0;hist=np.zeros(256,np.int64)
cached={};prior=out/'DECODED_INPUTS_ATTEMPT1.jsonl'
if prior.exists():
 for line in prior.open():
  try:r=json.loads(line);cached[(r['split'],r['image_id'])]=r
  except json.JSONDecodeError:pass
result['reused_prior_complete_rows']=0;result['prior_attempt_record']='AUDIT_ATTEMPT1.json';rows=[];start=time.monotonic()
with (out/'DECODED_INPUTS.jsonl').open('x') as sink:
 for split,keylist in [('Training',['0000930','0021834','0001368']),('Validation',ids['Validation'])]:
  for index,iid in enumerate(keylist):
   row={'image_id':iid,'split':split,'status':'READING'}
   try:
    if (split,iid) in cached:
     prev=cached[(split,iid)]
     if prev['status']!='COMPLETE':raise ValueError('Prior decode failure retained: '+prev.get('error',''))
     for kind,extension in [('RGB','.jpg'),('Category_ids','.png'),('Human_ids','.png'),('Instance_ids','.png')]:
      path=root/split/('Images' if kind=='RGB' else kind)/(iid+extension)
      if file_hash(path)!=prev['sources'][kind]['file_sha256']:raise ValueError('Prior decoded source changed')
     c,_=read_image(root/split/'Category_ids'/(iid+'.png'),mask=True);row=prev;meta=row['sources'];rec=collections.Counter(row['flags']);people=row['human_values'];result['reused_prior_complete_rows']+=1
    else:
     arrays,meta=read_sample(root,split,iid);c,h,ins=[arrays[k] for k in ['Category_ids','Human_ids','Instance_ids']];valid=(c<20);people=np.unique(h[h>0]);rec=collections.Counter()
     rec['category_without_human']=int(((c>0)&valid&(h==0)).sum());rec['human_without_category']=int(((h>0)&(c==0)).sum());rec['instance_without_human']=int(((ins>0)&(h==0)).sum());rec['instance_without_category']=int(((ins>0)&(c==0)).sum())
     # Direct association counts, not a speculative conversion of instance IDs.
     hb=int(h.max())+1;cb=256;codes=np.unique(ins.ravel().astype('int64')*cb*hb+c.ravel().astype('int64')*hb+h.ravel());pairs=np.column_stack([codes//(cb*hb),(codes//hb)%cb,codes%hb])
     for iv in np.unique(pairs[:,0]):
      if iv==0:continue
      subset=pairs[pairs[:,0]==iv];rec['part_instances']+=1
      if len(np.unique(subset[:,1]))>1:rec['mixed_class_part_instances']+=1
      if len(np.unique(subset[:,2]))>1:rec['mixed_person_part_instances']+=1
     row.update(status='COMPLETE',wh=meta['wh'],sources=meta,persons=len(people),class_values=np.unique(c).tolist(),human_values=people.tolist(),flags=dict(rec),person_stats=[{'person_id':int(pid),'area':int((h==pid).sum()),'bbox_xyxy':list(map(int,[np.where(h==pid)[1].min(),np.where(h==pid)[0].min(),np.where(h==pid)[1].max()+1,np.where(h==pid)[0].max()+1]))} for pid in people])
    for k in ['Category_ids','Human_ids','Instance_ids']:result['mask_modes'][k+':'+meta[k]['mode']+':'+meta[k]['dtype']]+=1
    if split=='Validation':
     hist+=np.bincount(c.ravel(),minlength=256);result['persons']+=len(people);result['warnings'].update(rec);result['checked_validation_images']+=1;same_old+=int(meta['RGB']['file_sha256']==old.get(iid,{}).get('RGB_sha256') and meta['wh']==old.get(iid,{}).get('wh'))
    else:result['checked_training_images']+=1
   except Exception as e:row.update(status='FAILED',error=repr(e));result['failures'].append(row)
   sink.write(json.dumps(row,default=lambda x:int(x))+'\n');sink.flush()
   if index%250==0:print(split,index,'/',len(keylist),'failures',len(result['failures']),flush=True)
result['semantic_values']={str(i):int(n) for i,n in enumerate(hist) if n};result['all_VAL_same_JPEG_bytes_and_geometry_as_frozen_detector_inputs']=same_old==5000;result['matching_frozen_detector_inputs']=same_old;result['mask_modes']=dict(result['mask_modes']);result['warnings']=dict(result['warnings']);result['status']='DATA_BLOCKED' if result['failures'] or any(result['split_ID_overlap'].values()) else 'DECODE_AND_METADATA_PASS_WITH_REPORTED_LIMITATIONS';result['end_utc']=datetime.now(timezone.utc).isoformat();result['seconds']=time.monotonic()-start
(out/'DATA_READINESS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['exact_train_VAL_groups','semantic_values']},indent=2),flush=True)
