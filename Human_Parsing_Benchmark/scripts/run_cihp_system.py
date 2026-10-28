"""One isolated FP32 first-six stream. Declared native CIHP inputs only."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,sys,os,time,traceback,hashlib,subprocess,shutil
P=Path(__file__).resolve().parents[1];W=P.parent;sys.path.insert(0,str(P/'src'))
from cihp_benchmark.data import read_image,file_hash

def atomic(path,data):
 path=Path(path);tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');tmp.replace(path)
class ResourceStop(RuntimeError):
 pass

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--model',required=True);parser.add_argument('--phase',choices=['readiness','validation'],required=True);parser.add_argument('--output',required=True);a=parser.parse_args();config=json.loads(Path(a.config).read_text());config_hash=file_hash(a.config)
 if a.model not in config['execution_models']:raise ValueError('Outside authorized six')
 if a.phase=='validation' and (not config['frozen'] or config['freeze_status']!='READY_FROZEN'):raise ValueError('Readiness/freeze gate not closed')
 if a.phase=='readiness' and not config['authorization']['TRAIN_readiness']:raise ValueError('No TRAIN authority')
 if a.phase=='validation' and not config['authorization']['native_validation_six']:raise ValueError('No VAL authority')
 out=Path(a.output).resolve()
 if not out.is_relative_to(W/'Human_Parsing_MHPv2_Study/outputs/cihp_native') or out.exists():raise ValueError('Fresh external artifact directory required')
 out.mkdir(parents=True);os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['OMP_NUM_THREADS']='4'
 result={'run_id':out.parent.parent.name,'model_id':a.model,'phase':a.phase,'start_utc':datetime.now(timezone.utc).isoformat(),'status':'INITIALIZING','config_sha256':config_hash,'model_retries':0,'expected':3 if a.phase=='readiness' else 5000,'complete':0,'failed':0,'invalid':0,'not_attempted':3 if a.phase=='readiness' else 5000,'warmup_images':[],'precision':'FP32','timing_scope':config['runtime'],'artifacts':[]}
 atomic(out/'RUN.json',result)
 try:
  for path,digest in config.get('source_bindings',{}).items():
   if file_hash(W/path)!=digest:raise ValueError('Frozen execution source changed: '+path)
  if file_hash(W/config['authority'])!=config['authority_sha256']:raise ValueError('Adopted authority bytes changed')
  if file_hash(W/config['dataset']['population'])!=config['dataset']['population_sha256']:raise ValueError('Population binding changed')
  busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
  if busy:raise RuntimeError('EXTERNAL_GPU_BUSY: defer, do not interrupt other jobs')
  import numpy as np,torch
  torch.set_num_threads(4);torch.manual_seed(config['seed']);np.random.seed(config['seed']);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
  from cihp_benchmark.adapters import NativeAdapter
  from cihp_benchmark.evaluation import score_frame,semantic_report
  from cihp_benchmark.data import read_sample
  spec=config['models'][a.model]
  if file_hash(W/spec['checkpoint'])!=spec['checkpoint_sha256'] or file_hash(W/spec['native_config'])!=spec['native_config_sha256']:raise ValueError('Checkpoint/nativeconfig hash mismatch')
  if subprocess.check_output(['git','-C',str(W/spec['source']),'rev-parse','HEAD'],text=True).strip()!=spec['source_commit']:raise ValueError('Source commit drift')
  result.update(checkpoint_sha256=spec['checkpoint_sha256'],source_commit=spec['source_commit'],python=sys.version,torch=torch.__version__,CUDA_runtime=torch.version.cuda,GPU=torch.cuda.get_device_name(0),driver=subprocess.check_output(['nvidia-smi','--query-gpu=driver_version','--format=csv,noheader'],text=True).strip(),worker_sha256=file_hash(__file__),adapter_sha256=file_hash(P/'src/cihp_benchmark/adapters.py'),scorer_sha256=file_hash(P/'src/cihp_benchmark/evaluation.py'))
  import importlib.metadata
  freeze='\n'.join(sorted(x.metadata['Name']+'=='+x.version for x in importlib.metadata.distributions()));(out/'ENVIRONMENT.txt').write_text(freeze+'\n');result['environment_sha256']=hashlib.sha256(freeze.encode()).hexdigest()
  adapter=NativeAdapter(W,spec,out/'adapter');result['model_details']=adapter.details;atomic(out/'RUN.json',result)
  if a.phase=='readiness':
   split='Training';ids=['0000930','0021834','0001368'];det=json.loads((W/config['frozen_YOLO']['training_run']).read_text());detector={x['image_id']:dict(x,status='COMPLETE',artifact='Human_Parsing_MHPv2_Study/'+x['artifact']) for x in det['images']};rows=[{'id':i} for i in ids]
  else:
   split='Validation';pop=json.loads((W/config['dataset']['population']).read_text());rows=pop['members'];detector={x['image_id']:x for x in map(json.loads,(W/config['frozen_YOLO']['validation_ledger']).open())}
   # One non-VAL warmup excluded from all validation denominators and latency stats.
   tr=json.loads((W/config['frozen_YOLO']['training_run']).read_text());warm=next(x for x in tr['images'] if x['image_id']=='0000930');rgb,_=read_image(W/'datasets/CIHP/Training/Images/0000930.jpg');z=np.load(W/'Human_Parsing_MHPv2_Study'/warm['artifact'],allow_pickle=False);adapter.infer(rgb,W/'datasets/CIHP/Training/Images/0000930.jpg',warm['opportunities'],z['masks']);result['warmup_images']=['0000930'];torch.cuda.synchronize()
  execution_start=time.monotonic();retained_bytes=sum(f.stat().st_size for f in out.rglob('*') if f.is_file());largest_packet_bytes=1024*1024
  hist=np.zeros((20,20),np.int64);person={str(t):{'G_loc':0,'G_sem':0,'TP':0,'FP':0,'FN':0,'Q_numerator':0.} for t in [.5,.75]};latencies=[];nativehist=np.zeros((20,20),np.int64);lastsave=time.monotonic()
  with (out/'FRAMES.jsonl').open('x') as ledger:
   for index,sample in enumerate(rows):
    iid=sample['id'];row={'image_id':iid,'split':split,'attempt_id':iid+':1','status':'RUNNING','start_utc':datetime.now(timezone.utc).isoformat()};stage='SOURCE_VALIDATION'
    try:
     if file_hash(a.config)!=config_hash:raise ValueError('Execution config changed')
     if shutil.disk_usage(out).free<config['minimum_free_gib']*2**30+2*largest_packet_bytes:raise ResourceStop('RESOURCE_FREE_SPACE_STOP')
     if retained_bytes+2*largest_packet_bytes>config['max_per_system_artifact_gib']*2**30:raise ResourceStop('RESOURCE_STREAM_STORAGE_STOP')
     if time.monotonic()-execution_start>config['max_system_hours']*3600:raise ResourceStop('RESOURCE_TIME_STOP')
     rgb,meta=read_image(W/'datasets/CIHP'/split/'Images'/(iid+'.jpg'));h,w=rgb.shape[:2];d=detector[iid]
     if d.get('status')!='COMPLETE' or list(d.get('original_wh',d.get('wh')))!=[w,h]:raise ValueError('Frozen detector binding invalid')
     if a.phase=='validation' and meta['file_sha256']!=sample['RGB_sha256']:raise ValueError('Native input identity changed')
     dp=W/d['artifact'] if str(d['artifact']).startswith('Human_Parsing') else W/'Human_Parsing_MHPv2_Study'/d['artifact']
     if file_hash(dp)!=d['artifact_sha256']:raise ValueError('Detector artifact hash mismatch')
     with np.load(dp,allow_pickle=False) as det_arrays:ownership=det_arrays['masks'].copy()
     if ownership.shape!=(len(d['opportunities']),h,w):raise ValueError('Detector mask geometry invalid')
     stage='MODEL_INFERENCE';torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter();arrays,metadata=adapter.infer(rgb,W/'datasets/CIHP'/split/'Images'/(iid+'.jpg'),d['opportunities'],ownership);torch.cuda.synchronize();elapsed=time.perf_counter()-start
     row.update(parser_pipeline_seconds=elapsed,ROI_tasks=len(d['opportunities']) if spec['route']=='YOLO_ROI' else None,peak_allocated_MiB=torch.cuda.max_memory_allocated()/2**20,peak_reserved_MiB=torch.cuda.max_memory_reserved()/2**20)
     stage='EXPORT';packet=out/'packets'/iid;packet.mkdir(parents=True,exist_ok=False);tmp=packet/'prediction.npz.tmp'
     with tmp.open('xb') as f:np.savez_compressed(f,**arrays)
     tmp.replace(packet/'prediction.npz');packet_hash=file_hash(packet/'prediction.npz');metadata.update(model_id=a.model,image_id=iid,label_space='CIHP_NATIVE_20',source_track=spec['route'],original_wh=[w,h],checkpoint_sha256=spec['checkpoint_sha256'],source_commit=spec['source_commit'],input_sha256=meta['file_sha256'],config_sha256=config_hash,packet_sha256=packet_hash,inference_fingerprint=hashlib.sha256(json.dumps({'model':spec,'input':meta['file_sha256'],'detector':d['artifact_sha256'],'adapter_sha256':file_hash(P/'src/cihp_benchmark/adapters.py'),'precision':'FP32','ownership':config['ROI_ownership'],'association':config['association']},sort_keys=True).encode()).hexdigest(),precision='FP32',native_output_contract='integer planes and separately retained extents/scores',detector_artifact_sha256=d['artifact_sha256'])
     atomic(packet/'packet.json',metadata)
     stage='SCORING';truth,gtmeta=read_sample(W/'datasets/CIHP',split,iid)
     metadata['evaluation_fingerprint']=hashlib.sha256(json.dumps({'GT':{k:gtmeta[k]['file_sha256'] for k in ['Category_ids','Human_ids','Instance_ids']},'scorer_sha256':file_hash(P/'src/cihp_benchmark/evaluation.py'),'metrics':config['metrics']},sort_keys=True).encode()).hexdigest()
     atomic(packet/'packet.json',metadata)
     if a.phase=='validation':
      for typ in ['Category_ids','Human_ids','Instance_ids']:
       if gtmeta[typ]['file_sha256']!=sample['GT_sha256'][typ]:raise ValueError('GT identity drift')
     for threshold in [.5,.75]:
      sc=score_frame(truth['Category_ids'],truth['Human_ids'],arrays['person_semantic_masks'],arrays['person_extents'],arrays['person_scores'],threshold)
      for k in person[str(threshold)]:person[str(threshold)][k]+=sc[k]
      if threshold==.5:hist+=np.array(sc['histogram'],np.int64)
      atomic(packet/('score_'+str(threshold)+'.json'),sc)
     if spec['native_reference']:
      sc=score_frame(truth['Category_ids'],truth['Human_ids'],arrays['native_person_semantic_masks'],arrays['native_person_extents'],arrays['native_person_scores'],.5);nativehist+=np.array(sc['histogram'],np.int64);atomic(packet/'native_reference_score.json',sc)
     packet_bytes=sum(f.stat().st_size for f in packet.iterdir() if f.is_file());retained_bytes+=packet_bytes;largest_packet_bytes=max(largest_packet_bytes,packet_bytes)
     if spec['family']=='CPI-Parser':
      for folder in ['val_parsing','val_seg','val_parsing_scores']:
       for f in (out/'adapter/native'/folder).glob(iid+'*'):
        if f.is_file():retained_bytes+=f.stat().st_size
     result['retained_artifact_bytes_observed']=retained_bytes
     row.update(status='COMPLETE',packet=str(packet.relative_to(W)),packet_sha256=packet_hash,final_person_count=metadata['final_person_count'],native_entry_count=metadata['native_raw_entry_count']);result['complete']+=1;latencies.append(elapsed)
    except Exception as exc:
     row.update(status='NOT_ATTEMPTED_RESOURCE_STOP' if isinstance(exc,ResourceStop) else 'FAILED' if stage=='MODEL_INFERENCE' else 'INVALID',failure_stage=stage,error=traceback.format_exc())
     if row['status']!='NOT_ATTEMPTED_RESOURCE_STOP':result['failed' if row['status']=='FAILED' else 'invalid']+=1
     result['stop_reason']=repr(exc)
    row['end_utc']=datetime.now(timezone.utc).isoformat();ledger.write(json.dumps(row,allow_nan=False)+'\n');ledger.flush();result['not_attempted']=len(rows)-result['complete']-result['failed']-result['invalid'];atomic(out/'RUN.json',result)
    if row['status']!='COMPLETE':break
    if index%25==0:print(a.model,a.phase,index+1,'/',len(rows),flush=True)
   result['status']='COMPLETE' if result['complete']==len(rows) else 'INCOMPLETE'
  metrics={'population':split,'expected':len(rows),'complete':result['complete'],'failure':result['failed'],'invalid':result['invalid'],'not_attempted':result['not_attempted'],'primary':semantic_report(hist) if result['status']=='COMPLETE' else None,'person_metrics':{},'native_reference_primary':semantic_report(nativehist) if result['status']=='COMPLETE' and spec['native_reference'] else None,'successful_subset_diagnostic_not_main':semantic_report(hist) if result['status']!='COMPLETE' else None,'latency_scope':config['runtime'],'timing_complete_frames':len(latencies),'parser_pipeline_ms_mean':float(np.mean(latencies)*1000) if latencies else None,'parser_pipeline_ms_P50':float(np.median(latencies)*1000) if latencies else None,'parser_pipeline_ms_P95':float(np.percentile(latencies,95)*1000) if latencies else None,'end_to_end_FPS':None,'end_to_end_reason':'cachedYOLO; not measured fresh full-system route'}
  for t,v in person.items():
   v.update(extent_precision=v['TP']/(v['TP']+v['FP']) if v['TP']+v['FP'] else None,extent_recall=v['TP']/v['G_loc'] if v['G_loc'] else None,extent_F1=2*v['TP']/(2*v['TP']+v['FP']+v['FN']) if 2*v['TP']+v['FP']+v['FN'] else None,Q_person_sem_GT=v['Q_numerator']/v['G_sem'] if v['G_sem'] else None)
   metrics['person_metrics'][t]=v if result['status']=='COMPLETE' else None
  atomic(out/'METRICS.json',metrics);np.save(out/'CONFUSION.npy',hist);np.save(out/'NATIVE_REFERENCE_CONFUSION.npy',nativehist)
 except Exception:
  result.update(status='BLOCKED',error=traceback.format_exc())
 result['end_utc']=datetime.now(timezone.utc).isoformat();atomic(out/'RUN.json',result);print(a.model,result['status'],result.get('complete'),flush=True)
 return 0 if result['status']=='COMPLETE' else 1
if __name__=='__main__':raise SystemExit(main())
