"""Readiness freeze for one seven-call Sapiens pilot; does not instantiate/forward model."""
import json,os,subprocess,sys,struct,time,shutil,importlib.metadata
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'))
from common_view.core import sha_file
from common_view.packets import atomic_json


def gpu_snapshot():
    return {'GPU':subprocess.check_output(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu','--format=csv'],text=True),
            'apps':subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv'],text=True)}


def main():
    cfgpath=P/'configs/cihp_sapiens_04b_pilot.json';cfg=json.loads(cfgpath.read_text());raw=W/cfg['artifact_root'];record=W/cfg['record_root']
    cpu=json.loads((raw/'CPU_ACCEPTANCE.json').read_text());assert cpu['status']=='PASS'
    for p,h in cpu['source_hashes'].items():assert sha_file(W/p)==h,p
    gtroot=W/cfg.get('GT_binding_root',str((raw/'gt_bindings').relative_to(W)))
    gt=json.loads((gtroot/'SUMMARY.json').read_text());assert gt['count']==5000
    assert gt['protocol_sha256']==cfg['protocol_sha256']==sha_file(W/cfg['protocol'])
    for p,h in cfg['native_preserved'].items():assert sha_file(W/p)==h,p
    ck=W/cfg['model']['checkpoint'];native_cfg=W/cfg['model']['native_config']
    assert cfg['model']['model_id']=='Sapiens2_0.4b' and '/0.4b/' in str(ck)
    assert sha_file(native_cfg)==cfg['model']['native_config_sha256']
    checkpoint_sha=sha_file(ck)
    assert checkpoint_sha==cfg['model']['checkpoint_sha256_from_frozen_registry']
    with ck.open('rb') as f:
        n=struct.unpack('<Q',f.read(8))[0];header=json.loads(f.read(n))
    assert header['decode_head.conv_seg.weight']['shape']==[29,64,1,1]
    assert header['decode_head.conv_seg.weight']['dtype']=='F32'
    source=W/'third_party/human_parsing/sapiens2'
    assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()==cfg['model']['source_commit']
    assert not subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True).strip()
    import torch
    assert torch.cuda.is_available() and torch.cuda.get_device_name(0)=='Tesla T4'
    free,total=torch.cuda.mem_get_info(0)
    assert free>0 and shutil.disk_usage(raw).free>cfg['minimum_free_gib']*2**30
    sources=[*sorted((P/'src/common_view').glob('*.py')),P/'tests/test_common_view.py',
             P/'scripts/run_common_sapiens_pilot.py',P/'scripts/verify_common_view_cpu.py',
             P/'scripts/materialize_common_gt.py',Path(__file__),P/'scripts/render_common_pilot.py']
    pinned=[native_cfg,source/'sapiens/dense/src/models/init_model.py',
            source/'sapiens/dense/src/datasets/transforms/seg_transforms.py',
            source/'sapiens/engine/datasets/data_preprocessors/image_preprocessor.py',
            source/'sapiens/dense/src/datasets/seg/seg_utils.py']
    source_hashes={str(p.relative_to(W)):sha_file(p) for p in sources+pinned}
    environment={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    atomic_json(raw/'ENVIRONMENT.json',environment)
    read={'status':'PASS_PRE_FORWARD_READINESS','created_utc':datetime.now(timezone.utc).isoformat(),
          'config_sha256':sha_file(cfgpath),'protocol_sha256':cfg['protocol_sha256'],
          'source_hashes':source_hashes,'model_id':cfg['model']['model_id'],'checkpoint_sha256':checkpoint_sha,
          'checkpoint_stat':{'size':ck.stat().st_size,'mtime_ns':ck.stat().st_mtime_ns},
          'semantic_head_shape':[29,64,1,1],'strict_model_load_and_warmup':'REQUIRED_IN_PILOT_NOT_YET_RUN',
          'CPU_acceptance_sha256':sha_file(raw/'CPU_ACCEPTANCE.json'),
          'GT_manifest_sha256':gt['manifest_sha256'],'environment_sha256':sha_file(raw/'ENVIRONMENT.json'),
          'python':sys.version,'environment_workspace_relative':'.venvs/sapiens2-pilot',
          'torch':torch.__version__,'CUDA_runtime':torch.version.cuda,
          'CUDA_VISIBLE_DEVICES':os.environ.get('CUDA_VISIBLE_DEVICES'),
          'allocator_environment_preserved':os.environ.get('PYTORCH_CUDA_ALLOC_CONF'),
          'resource_policy':'SHARED_GPU_QUALITY_ONLY','GPU_free_MiB':free/2**20,
          'GPU_total_MiB':total/2**20,'free_disk_GiB':shutil.disk_usage(raw).free/2**30,
          'GPU_snapshot':gpu_snapshot(),'external_PID_alone_is_not_a_blocker':True,
          'maximum_model_frame_calls':7,'model_calls_so_far':0,'OOM_retry':0,'fallback':False}
    atomic_json(raw/'READINESS.json',read)
    # Public compact evidence omits unrelated process command paths.
    public={k:v for k,v in read.items() if k!='GPU_snapshot'}
    public['external_compute_processes_observed']=len(read['GPU_snapshot']['apps'].strip().splitlines())-1
    atomic_json(record/'READINESS.json',public)
    policy={k:cfg[k] for k in ['resource_policy','minimum_free_gib','max_stream_gib','max_hours','max_model_frame_calls','automatic_model_OOM_retry']}
    policy.update(explicit_user_amendment=True,no_other_process_modification=True,no_system_GPU_changes=True,timing_ranking_allowed=False,scope='Sapiens2_0.4b pilot only',reason='Quality/output/scorer/completeness priority; explicit sharing authorization')
    atomic_json(raw/'RESOURCE_POLICY.json',policy);atomic_json(record/'RESOURCE_POLICY.json',policy)
    print(json.dumps({'status':read['status'],'checkpoint_hash_verified':True,'GPU_free_MiB':read['GPU_free_MiB'],'source_bindings':len(source_hashes)}),flush=True)

if __name__=='__main__':main()
