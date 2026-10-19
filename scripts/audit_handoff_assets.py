"""Read-only official roster discovery and local checkpoint inventory."""
from pathlib import Path
import json,hashlib,subprocess,re,datetime,shutil
import requests,gdown
W=Path(__file__).resolve().parents[2];S=W/'Human_Parsing_MHPv2_Study'
R=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
files=[]
for p in (W/'models/human_parsing').rglob('*'):
 if p.is_file() and p.suffix in {'.pth','.pt','.safetensors'}:
  files.append(dict(path=str(p.relative_to(W)),bytes=p.stat().st_size,sha256=sha(p),existing_before_this_run=True))
(R/'LOCAL_CHECKPOINTS.json').write_text(json.dumps(dict(files=files,total_bytes=sum(x['bytes'] for x in files),unique_sha256=len(set(x['sha256'] for x in files)),disk_free_bytes=shutil.disk_usage(W).free),indent=2))
records=[]
for family in ['M2FP','CPI-Parser','D2FP','SCHP','QANet','RP-R-CNN','CDGNet','fashn-human-parser','sapiens2']:
 p=W/'third_party/human_parsing'/family
 remote=subprocess.check_output(['git','remote','get-url','origin'],cwd=p,text=True).strip()
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip()
 slug=remote.removesuffix('.git').split('github.com/')[-1]
 r=dict(family=family,remote=remote,local_commit=commit,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 try:
  resp=requests.get('https://api.github.com/repos/'+slug+'/readme',headers={'Accept':'application/vnd.github.raw+json'},timeout=30);resp.raise_for_status();body=resp.text
  (R/(family+'_official_README.txt')).write_text(body)
  r['readme_sha256']=hashlib.sha256(body.encode()).hexdigest()
  rel=requests.get('https://api.github.com/repos/'+slug+'/releases',timeout=30);rel.raise_for_status()
  r['release_assets']=[dict(name=a['name'],bytes=a['size'],url=a['browser_download_url']) for v in rel.json() for a in v['assets']]
  r['drive_folders']=sorted(set(re.findall(r'https://drive.google.com/drive/folders/[A-Za-z0-9_-]+',body)))
  r['checkpoint_links']=sorted(set(re.findall(r'https://[^\s)<>]+',body)))
 except Exception as e:r['error']=str(e)
 records.append(r);(R/'OFFICIAL_ROSTER_DISCOVERY.json').write_text(json.dumps(records,indent=2));print(family,'source checked',flush=True)
# Public metadata only; downloaded files handled by a separate acquisition phase.
folders=[]
original=requests.sessions.Session.request
def bounded(self,*args,**kw):kw.setdefault('timeout',(15,35));return original(self,*args,**kw)
requests.sessions.Session.request=bounded
for row in records:
 for url in row.get('drive_folders',[]):
  item=dict(family=row['family'],url=url)
  try:
   listing=gdown.download_folder(url=url,skip_download=True,quiet=True,use_cookies=False)
   item['files']=[dict(id=x.id,path=x.path) for x in listing] if listing else []
  except Exception as e:item['error']=str(e)
  folders.append(item);(R/'OFFICIAL_FOLDER_DISCOVERY.json').write_text(json.dumps(folders,indent=2));print(row['family'],'folder checked',flush=True)
