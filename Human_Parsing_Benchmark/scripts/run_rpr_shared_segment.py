"""Explicit RPR-only shared-GPU resource amendment; scientific worker unchanged."""
from pathlib import Path
import argparse,hashlib,json
from run_cihp_segment import derive,validate_partition
P=Path(__file__).resolve().parents[1];W=P.parent

def validate_policy(policy,model):
    if model!='RPR_CIHP' or policy['authorized_models']!=['RPR_CIHP']:raise ValueError('RPR-only scope required')
    if policy['mode']!='SHARED_GPU_QUALITY_ONLY' or not policy['quality_only'] or policy['timing_ranking_allowed']:raise ValueError('Explicit shared quality policy required')

def derive_shared(source):
    text=derive(source)
    old="if busy:raise RuntimeError('EXTERNAL_GPU_BUSY: defer, do not interrupt other jobs')"
    if text.count(old)!=1:raise ValueError('Frozen admission anchor changed')
    text=text.replace(old,"if busy and not segment['shared_GPU_quality_only']:raise RuntimeError('EXTERNAL_GPU_BUSY: defer, do not interrupt other jobs')\n  result.update(actual_resource_mode='SHARED_GPU_QUALITY_ONLY',external_GPU_PIDs_at_admission=busy.split(),resource_policy_sha256=segment['resource_policy_sha256'],timing_ranking_allowed=False)\n  result['timing_scope']={**result['timing_scope'],'profile':'SHARED_GPU_ADAPTER_DIAGNOSTICS','measurement_rank_claim':'NO_CLEAN_SPEED_OR_END_TO_END_RANKING','includes':'RPR native preprocessing/internal detector/parsing/native postprocess/mapback/association','excludes':'source JPEG read/canonical packet export/GT scoring/global semantic composition/model load; frozen YOLO forward absent'}")
    old="metadata.update(parent_run_id=segment['parent_run_id']"
    if text.count(old)!=1:raise ValueError('Metadata anchor changed')
    text=text.replace(old,"metadata.update(actual_resource_mode='SHARED_GPU_QUALITY_ONLY',resource_policy_sha256=segment['resource_policy_sha256'],timing_ranking_allowed=False,parent_run_id=segment['parent_run_id']")
    old="'latency_scope':config['runtime']"
    if text.count(old)!=1:raise ValueError('Latency metadata anchor changed')
    text=text.replace(old,"'latency_scope':result['timing_scope']")
    return text

def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--segment-manifest',required=True);args,_=parser.parse_known_args();path=Path(args.segment_manifest);s=json.loads(path.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    assert sha(__file__)==s['wrapper_sha256']
    policy_path=W/s['resource_policy'];assert sha(policy_path)==s['resource_policy_sha256'];policy=json.loads(policy_path.read_text());validate_policy(policy,s['model_id']);assert s['shared_GPU_quality_only'] is True
    original=P/'scripts/run_cihp_system.py';assert sha(original)==s['frozen_worker_sha256'];assert sha(P/'scripts/run_cihp_segment.py')==s['base_segment_wrapper_sha256']
    expanded=derive_shared(original.read_text());assert hashlib.sha256(expanded.encode()).hexdigest()==s['expanded_worker_sha256']
    config=json.loads((W/s['config']).read_text());assert sha(W/s['config'])==s['config_sha256'];ids=[r['id'] for r in json.loads((W/config['dataset']['population']).read_text())['members']];validate_partition(ids,s['pending_ids'],s['reused_ids']);assert s['pending_ids']
    exec(compile(expanded,str(Path(__file__).resolve()),'exec'),{'__name__':'__main__','__file__':str(Path(__file__).resolve()),'segment_bind':sha(path)})

if __name__=='__main__':main()
