"""ConvNeXt-B only; frozen scientific worker with explicit shared admission.

Diagnostic output is separate and never eligible for canonical reuse.
"""
from pathlib import Path
import argparse,hashlib,json,sys
from run_cihp_segment import validate_partition
from run_cpi_r50_shared_segment import derive_shared as derive_CPI_resource_control
P=Path(__file__).resolve().parents[1];W=P.parent;MID='CPI_ConvNeXtB_CIHP'

def validate_policy(policy,model):
    if model!=MID or policy['authorized_models']!=[MID]:raise ValueError('ConvNeXt-B-only authority required')
    if policy['mode']!='SHARED_GPU_QUALITY_ONLY' or not policy['quality_only'] or policy['timing_ranking_allowed']:raise ValueError('Explicit shared-quality policy required')

def derive_shared(source):
    text=derive_CPI_resource_control(source)
    anchor="adapter=NativeAdapter(W,spec,out/'adapter');result['model_details']=adapter.details;atomic(out/'RUN.json',result)"
    assert text.count(anchor)==1
    return text.replace(anchor,anchor+"\n  if segment.get('diagnostic_only'):install_geometry_observer(out)")

def install_geometry_observer(out):
    """Observe the actual native loader's metadata; delegate unchanged pipeline."""
    import mmdet.apis.inference as api
    from mmcv.parallel import DataContainer
    original=api.Compose
    def observed_compose(*args,**kwargs):
        pipeline=original(*args,**kwargs)
        def apply(data):
            result=pipeline(data);events=[]
            for meta in result.get('img_metas',[]):
                if isinstance(meta,DataContainer):meta=meta.data
                events.append({k:meta[k].tolist() if hasattr(meta[k],'tolist') else meta[k] for k in ['ori_shape','img_shape','pad_shape','scale_factor','flip'] if k in meta})
            with (out/'INPUT_GEOMETRY.jsonl').open('a') as stream:stream.write(json.dumps({'source':str(data.get('img_info',{}).get('filename')),'native_pipeline_geometry':events})+'\n')
            return result
        return apply
    api.Compose=observed_compose

def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--segment-manifest',required=True);a,_=parser.parse_known_args();path=Path(a.segment_manifest);s=json.loads(path.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    assert sha(__file__)==s['wrapper_sha256'];assert sha(P/'scripts/run_rpr_shared_segment.py')==s['resource_control_template_sha256'];assert sha(P/'scripts/run_cihp_segment.py')==s['base_segment_wrapper_sha256'];assert sha(P/'scripts/run_cpi_r50_shared_segment.py')==s['CPI_resource_template_sha256']
    policy_path=W/s['resource_policy'];assert sha(policy_path)==s['resource_policy_sha256'];validate_policy(json.loads(policy_path.read_text()),s['model_id']);assert s['shared_GPU_quality_only'] is True
    original=P/'scripts/run_cihp_system.py';assert sha(original)==s['frozen_worker_sha256'];expanded=derive_shared(original.read_text());assert hashlib.sha256(expanded.encode()).hexdigest()==s['expanded_worker_sha256']
    cfg=json.loads((W/s['config']).read_text());assert sha(W/s['config'])==s['config_sha256'];assert cfg['models'][MID]['family']=='CPI-Parser'
    ids=[r['id'] for r in json.loads((W/cfg['dataset']['population']).read_text())['members']]
    if s.get('diagnostic_only'):
        assert s['pending_ids']==['0000018'] and not s['reused_ids'] and '0000018' in ids
    else:validate_partition(ids,s['pending_ids'],s['reused_ids'])
    namespace={'__name__':'__main__','__file__':str(Path(__file__).resolve()),'segment_bind':sha(path),'install_geometry_observer':install_geometry_observer}
    try:exec(compile(expanded,str(Path(__file__).resolve()),'exec'),namespace)
    finally:
        if s.get('diagnostic_only') and 'torch' in sys.modules:
            torch=sys.modules['torch'];out=Path(sys.argv[sys.argv.index('--output')+1])
            if out.exists() and torch.cuda.is_initialized():
                (out/'PEAK_MEMORY.json').write_text(json.dumps({'peak_allocated_MiB':torch.cuda.max_memory_allocated()/2**20,'peak_reserved_MiB':torch.cuda.max_memory_reserved()/2**20,'scope':'Last native forward after worker reset; on setup failure may include model load/warmup; shared diagnostics only'},indent=2)+'\n')

if __name__=='__main__':main()
