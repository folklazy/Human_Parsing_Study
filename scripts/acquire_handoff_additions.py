"""Acquire missing author-folder parser assets; preserve names, versions, and originals."""
from pathlib import Path
import json,requests,gdown,shutil,hashlib,os,time
S=Path(__file__).resolve().parents[1];W=S.parent;R=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run']
folders=json.loads((R/'OFFICIAL_FOLDER_DISCOVERY.json').read_text());old=[row for plan in (W/'Human_Parsing_CCIHP_10_Image_Pilot/configs').glob('CHECKPOINT_DOWNLOAD_PLAN*.json') for row in json.loads(plan.read_text())['checkpoints']]
known={c['url'].split('/d/')[-1].split('/')[0]:c for c in old if '/d/' in c['url']}
# The original config/model association, not basename, identifies duplicate assets.
labels={'145SAx0wTqu8y5JvW2L1TvVP5nczCt1_n':'QANet_CIHP_HRNetW48_512x384','1QRAhtuaDWDidxEoyBCf7wiHrUamKQUb_':'QANet_LIP_HRNetW48_544x416','1uOaQCpNtosIjEL2phQKEdiYd0Td18jNo':'SCHP_OFFICIAL_MULTIPERSON'}
rows=[]
original=requests.sessions.Session.request
def bounded(self,*a,**k):k.setdefault('timeout',(20,90));return original(self,*a,**k)
requests.sessions.Session.request=bounded
for folder in folders:
 for f in folder.get('files',[]):
  if 'imagenet' in f['path'].lower():continue
  # Auxiliary detector explicitly identified, not counted as a parser variant.
  row={'family':folder['family'],'file_id':f['id'],'original_filename':f['path'],'source_folder':folder['url'],'source_url':'https://drive.google.com/file/d/'+f['id']+'/view','status':'DISCOVERED','role':'AUXILIARY_DETECTOR' if 'detectron' in f['path'] else 'CONFIG' if f['path'].endswith('.yaml') else 'PARSER_CHECKPOINT','new_bytes':0}
  if f['id'] in known:
   row.update(status='EXISTING_NO_REDUNDANT_DOWNLOAD',path=known[f['id']]['destination']);rows.append(row);continue
  folderid=folder['url'].split('/')[-1];variant=labels.get(folderid,folder['family']+'_'+folderid)
  row['variant']=variant;row['path']=str(Path('models/human_parsing')/folder['family'].lower().replace('-','_')/variant/f['path'])
  try:
   response=requests.get(row['source_url']);response.raise_for_status();meta=json.JSONDecoder().raw_decode(response.text.split('itemJson: ',1)[1])[0]
   if meta[1]!=f['path']:raise ValueError('Official filename mismatch')
   row['expected_bytes']=int(meta[25][2]);row['metadata_status']='VERIFIED_AUTHOR_LINK_SIZE_NOT_CRYPTOGRAPHIC_AUTHENTICITY'
  except Exception as e:row.update(status='METADATA_BLOCKED',error=str(e),expected_bytes=None)
  rows.append(row)
free=shutil.disk_usage(W).free;estimate=sum(r.get('expected_bytes') or 0 for r in rows if r['status']=='DISCOVERED')
plan={'estimated_missing_bytes_known':estimate,'unknown_size_count':sum(r['status']=='METADATA_BLOCKED' for r in rows),'free_bytes_before':free,'headroom_bytes':20*1024**3,'rows':rows}
(R/'ADDITIONAL_ASSET_PLAN.json').write_text(json.dumps(plan,indent=2));print('known additional bytes',estimate,'free',free,flush=True)
if estimate*2+plan['headroom_bytes']>free:raise RuntimeError('Insufficient storage including temporary/resume/headroom')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
for row in rows:
 if row['status']!='DISCOVERED':continue
 p=W/row['path'];p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.part')
 try:
  if p.exists():row['status']='EXISTING_VERIFICATION_PENDING'
  else:
   if shutil.disk_usage(W).free<row['expected_bytes']*2+plan['headroom_bytes']:raise RuntimeError('Storage headroom unavailable')
   ok=gdown.download(id=row['file_id'],output=str(tmp),quiet=True,resume=True,use_cookies=False)
   if not ok or tmp.stat().st_size!=row['expected_bytes']:raise ValueError('Incomplete or wrong-size download')
   value=sha(tmp)
   # Dedupe against current verified preexisting files, without deleting originals.
   existing=json.loads((R/'LOCAL_CHECKPOINTS.json').read_text())['files'];same=next((x for x in existing if x['sha256']==value),None)
   if same:
    row['duplicate_of']=same['path'];row['status']='DOWNLOADED_IDENTICAL_CONTENT_RETAINED_PENDING_CLEANUP_APPROVAL'
   os.rename(tmp,p);row['new_bytes']=p.stat().st_size
  row.update(status='VERIFIED_LOCAL_FINGERPRINT',bytes=p.stat().st_size,sha256=sha(p),author_checksum=None,loaded=False,inference='NOT_TESTED',execution_eligibility='REQUIRES_VARIANT_SOURCE_LICENSE_BINDING')
 except Exception as e:row.update(status='DOWNLOAD_BLOCKED',error=str(e))
 (R/'ADDITIONAL_ASSET_RESULTS.json').write_text(json.dumps(plan,indent=2));print(row['original_filename'],row['status'],flush=True)
(R/'ADDITIONAL_ASSET_RESULTS.json').write_text(json.dumps(plan,indent=2))
