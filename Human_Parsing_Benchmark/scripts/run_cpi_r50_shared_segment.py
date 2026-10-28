"""CPI R50 only: reuse reviewed resource control, preserve scientific worker."""
from pathlib import Path
import argparse,hashlib,json
from run_cihp_segment import validate_partition
from run_rpr_shared_segment import derive_shared as derive_resource_template
P=Path(__file__).resolve().parents[1];W=P.parent

def validate_policy(policy,model):
    if model!='CPI_R50_CIHP' or policy['authorized_models']!=['CPI_R50_CIHP']:raise ValueError('CPI R50-only scope required')
    if policy['mode']!='SHARED_GPU_QUALITY_ONLY' or not policy['quality_only'] or policy['timing_ranking_allowed']:raise ValueError('Explicit CPI R50 shared-quality amendment required')

def derive_shared(source):
    text=derive_resource_template(source)
    text=text.replace('RPR native preprocessing/internal detector/parsing/native postprocess/mapback/association','CPI native JPEG decode/preprocessing/internal detection and parsing/native PNG writes and reads/mapback/association')
    text=text.replace('source JPEG read/canonical packet export/GT scoring/global semantic composition/model load; frozen YOLO forward absent','outer source JPEG read/canonical packet export/GT scoring/global semantic composition/model load; CPI internal file I/O IS included, frozen YOLO forward absent')
    return text

def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--segment-manifest',required=True);args,_=parser.parse_known_args();path=Path(args.segment_manifest);s=json.loads(path.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    assert sha(__file__)==s['wrapper_sha256'];assert sha(P/'scripts/run_rpr_shared_segment.py')==s['resource_control_template_sha256'];assert sha(P/'scripts/run_cihp_segment.py')==s['base_segment_wrapper_sha256']
    policy_path=W/s['resource_policy'];assert sha(policy_path)==s['resource_policy_sha256'];policy=json.loads(policy_path.read_text());validate_policy(policy,s['model_id']);assert s['shared_GPU_quality_only'] is True
    original=P/'scripts/run_cihp_system.py';assert sha(original)==s['frozen_worker_sha256'];expanded=derive_shared(original.read_text());assert hashlib.sha256(expanded.encode()).hexdigest()==s['expanded_worker_sha256']
    config=json.loads((W/s['config']).read_text());assert sha(W/s['config'])==s['config_sha256'];assert config['models'][s['model_id']]['family']=='CPI-Parser';ids=[r['id'] for r in json.loads((W/config['dataset']['population']).read_text())['members']];validate_partition(ids,s['pending_ids'],s['reused_ids']);assert s['pending_ids']
    exec(compile(expanded,str(Path(__file__).resolve()),'exec'),{'__name__':'__main__','__file__':str(Path(__file__).resolve()),'segment_bind':sha(path)})

if __name__=='__main__':main()
