"""Instrument a bounded native worker without changing its architecture/precision."""
from pathlib import Path
import os,sys,json,subprocess,runpy,random,hashlib,time
import numpy as np
import torch
S=Path(os.environ['FIRST_COHORT_STUDY']);W=S.parent
B=Path(os.environ['FIRST_COHORT_ROUTE'])
name=sys.argv[1];args=sys.argv[2:];tag=name.removesuffix('.py')+('_'+args[-1] if args else '')
if subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():raise RuntimeError('GPU occupied; leave other jobs untouched')
os.environ['HUMAN_PARSING_WORKSPACE']=str(W);os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
random.seed(20261015);np.random.seed(20261015);torch.manual_seed(20261015)
sys.path.insert(0,str(B/'scripts'));sys.argv=[str(B/'scripts'/name),*args]
profile={'script':name,'args':args,'seed':20261015,'torch':torch.__version__,'cuda_runtime':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'driver':subprocess.check_output(['nvidia-smi','--query-gpu=driver_version','--format=csv,noheader'],text=True).strip(),'python':sys.version,'warmups':0,'rounds':1,'benchmark':False,'worker_timeout_seconds':900,'retries':0,'batch':1,'concurrency':1,'process_device_peak':'N/A_NOT_SAMPLED','canonical_adapter':'NOT_TESTED_NATIVE_ONLY','internal_op_dtype':'NOT_EXHAUSTIVELY_OBSERVED','module_output_dtypes':[],'model_loads':[],'native_worker_sha256':hashlib.sha256((B/'scripts'/name).read_bytes()).hexdigest()}
import importlib.metadata
freeze='\n'.join(sorted(d.metadata['Name']+'=='+d.version for d in importlib.metadata.distributions()));(B/'logs'/(tag+'_freeze.txt')).write_text(freeze);profile['environment_sha256']=hashlib.sha256(freeze.encode()).hexdigest()
dtypes=set();grads=set();autocast=set()
def collect(x):
 if torch.is_tensor(x):dtypes.add(str(x.dtype))
 elif isinstance(x,dict):
  for v in x.values():collect(v)
 elif isinstance(x,(tuple,list)):
  for v in x:collect(v)
def hook(module,inputs,output):collect(output);grads.add(torch.is_grad_enabled());autocast.add(torch.is_autocast_enabled())
handle=torch.nn.modules.module.register_module_forward_hook(hook)
original=torch.nn.Module.load_state_dict
def audited_load(self,state_dict,*a,**kw):
 start=time.perf_counter();result=original(self,state_dict,*a,**kw)
 profile['model_loads'].append({'module':type(self).__name__,'missing_keys':list(result.missing_keys),'unexpected_keys':list(result.unexpected_keys),'strict_argument':kw.get('strict',a[0] if a else True),'seconds':time.perf_counter()-start})
 return result
torch.nn.Module.load_state_dict=audited_load
start=time.perf_counter()
try:runpy.run_path(str(B/'scripts'/name),run_name='__main__');profile['worker_exit']='COMPLETED_CHECK_PER_MODEL_RUN'
except BaseException as exc:profile['worker_exit']=type(exc).__name__+': '+str(exc);raise
finally:
 handle.remove();profile.update(module_output_dtypes=sorted(dtypes),grad_enabled_observed=sorted(grads),autocast_observed=sorted(autocast),tf32_matmul=torch.backends.cuda.matmul.allow_tf32,tf32_cudnn=torch.backends.cudnn.allow_tf32,cudnn_benchmark=torch.backends.cudnn.benchmark,deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),total_worker_seconds=time.perf_counter()-start)
 (B/'logs'/(tag+'_PROFILE.json')).write_text(json.dumps(profile,indent=2))
