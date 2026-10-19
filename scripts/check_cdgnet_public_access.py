"""Bounded author-share access check using its published code; no access bypass."""
from pathlib import Path
import requests,json,re,datetime
S=Path(__file__).resolve().parents[1];R=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run']
s=requests.Session();base='https://pan.baidu.com';url=base+'/s/1WyifPOOE0SqIzCje-d1kzA?pwd=81la';s.get(url,timeout=25)
v=s.post(base+'/share/verify',params={'surl':'WyifPOOE0SqIzCje-d1kzA','web':'1','channel':'chunlei'},data={'pwd':'81la','vcode':'','vcode_str':''},headers={'Referer':url},timeout=25).json()
result={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'public_code_errno':v.get('errno'),'checkpoint_downloaded':False,'bypass':False}
if v.get('errno')==0:
 if v.get('randsk'):s.cookies.set('BDCLND',v['randsk'],domain='.baidu.com')
 page=s.get(url,timeout=25).text
 patterns=[r'yunData\s*=\s*(\{)',r'locals\.mset\((\{)',r'var\s+yunData\s*=\s*(\{)']
 data=None
 for pattern in patterns:
  match=re.search(pattern,page)
  if match:
   try:data=json.JSONDecoder().raw_decode(page[match.start(1):])[0];break
   except ValueError:pass
 if data is None:result.update(status='PUBLIC_FILE_VERIFIED_CLIENT_DOWNLOAD_PATH_UNRESOLVED',reason='No supported structured public share metadata parser; no login/access bypass attempted')
 else:
  files=data.get('file_list',data.get('filelist',[]));files=files.get('list',[]) if isinstance(files,dict) else files
  result['public_files']=[{k:f[k] for k in ['server_filename','size','fs_id','isdir'] if k in f} for f in files]
  result['public_metadata_fields']=sorted(data)
  if files and all(k in data for k in ['shareid','uk','sign','timestamp']):
   response=s.post(base+'/api/sharedownload',params={'sign':data['sign'],'timestamp':data['timestamp'],'web':'1','channel':'chunlei','clienttype':'0'},data={'encrypt':'0','product':'share','uk':data['uk'],'primaryid':data['shareid'],'fid_list':json.dumps([f['fs_id'] for f in files]),'extra':json.dumps({'sekey':v.get('randsk','')})},headers={'Referer':url},timeout=25)
   try:
    reply=response.json();result['public_download_api']={'http_status':response.status_code,'errno':reply.get('errno'),'errmsg':reply.get('errmsg',reply.get('error_msg')),'direct_link_returned':bool(reply.get('list'))}
   except ValueError:result['public_download_api']={'http_status':response.status_code,'json':False}
  result['status']='PUBLIC_SHARE_VERIFIED_DOWNLOAD_NOT_OBTAINED'
else:result['status']='PUBLIC_CODE_ACCESS_BLOCKED'
(R/'CDGNet_FINAL_ACCESS.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
