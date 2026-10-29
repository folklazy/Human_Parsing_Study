"""Freeze exact 0.8B identity and six-image pilot/full authorization, no model forward."""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,sys,struct,subprocess,importlib.metadata,shutil,os,time
import numpy as np
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'))
from common_view.core import sha_file,load_spec
from common_view.packets import atomic_json,fingerprint
from common_view.sapiens_route import make_cpu_pipeline
from common_view.sapiens08_resources import snapshot,peak_from_ledger


def main():
    current=P/'configs/cihp_sapiens_08b_pilot.json'
    if current.exists():raise RuntimeError('0.8B plan exists; inspect state, do not silently create a duplicate')
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:argv=(proc/'cmdline').read_bytes().split(b'\0')
        except FileNotFoundError:continue
        if any(Path(os.fsdecode(a)).name=='run_sapiens08.py' for a in argv if a) and b'--status' not in argv:
            raise RuntimeError('0.8B process already exists '+proc.name)
    parent=P/'configs/cihp_sapiens_c4p_full.json';base=json.loads(parent.read_text())
    row=next(r for r in csv.DictReader((P/'registry/CIHP_SAPIENS_CHECKPOINT_LABEL_BINDINGS.csv').open()) if r['model_id']=='Sapiens2_0.8b')
    print('registry fields',list(row),flush=True)
    ck=W/row['checkpoint'];config=W/row['native_config']
    assert '/0.8b/' in str(ck) and '0.8b_seg' in str(config)
    digest=sha_file(ck);assert digest==row['checkpoint_sha256_from_frozen_registry']
    row['checkpoint_payload_rehashed_this_work_unit']='True'
    assert sha_file(config)==row['native_config_sha256']
    with ck.open('rb') as f:
        header=json.loads(f.read(struct.unpack('<Q',f.read(8))[0]))
    assert header['decode_head.conv_seg.weight']['shape']==[29,64,1,1] and header['decode_head.conv_seg.weight']['dtype']=='F32'
    source=W/'third_party/human_parsing/sapiens2'
    assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()==row['source_commit']
    assert not subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True).strip()
    assert Path(sys.prefix).resolve()==(W/'.venvs/sapiens2-pilot').resolve()
    # Reuse unchanged scorer/route acceptance; inspect only the new model config's pipeline.
    for f,h in {**base['source_hashes'],**base['pilot_scientific_source_hashes'],**base['native_preserved']}.items():assert sha_file(W/f)==h,f
    cfg,pipeline,pre=make_cpu_pipeline(config);assert cfg.model_name=='sapiens2_0.8b' and cfg.num_classes==29
    from sapiens.engine.config import Config
    old=Config.fromfile(str(W/base['model']['native_config']))
    assert cfg.test_pipeline==old.test_pipeline and cfg.data_preprocessor==old.data_preprocessor
    assert cfg.image_size==(1024,768) and cfg.model['decode_head']['num_classes']==29
    gtroot=W/base['GT_binding_root'];assert sha_file(gtroot/'BINDINGS.jsonl')==base['GT_manifest_sha256']
    bindings=[json.loads(l) for l in (gtroot/'BINDINGS.jsonl').open()]
    assert len(bindings)==5000 and sum(r['G_loc'] for r in bindings)==base['GT_summary']['G_loc']
    assert sum(r['G_sem_C4'] for r in bindings)==base['GT_summary']['G_sem_C4']
    pop=json.loads((W/base['native_population']).read_text())['members'];assert sha_file(W/base['native_population'])==base['native_population_sha256']
    ids=[r['id'] for r in pop];assert len(ids)==len(set(ids))==5000
    oldprofile_path=W/'Human_Parsing_CCIHP_10_Image_Pilot/outputs/sapiens2_0.8b-20261012T103543Z/RUN.json';prof=json.loads(oldprofile_path.read_text())
    assert prof['status']=='PILOT_PASS' and prof['checkpoint_sha256']==digest and prof['config_sha256']==row['native_config_sha256']
    assert prof['source_commit']==row['source_commit'] and prof['precision']=='FP32'
    import torch
    assert torch.__version__==prof['torch'] and torch.version.cuda==prof['cuda_runtime'] and torch.cuda.is_available()
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==base['CUDA_VISIBLE_DEVICES'] and os.environ.get('PYTORCH_CUDA_ALLOC_CONF')==base['allocator_environment_preserved']
    free,usable=torch.cuda.mem_get_info(0)
    cards=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,name','--format=csv,noheader'],text=True).strip().splitlines()
    # This workspace exposes one assigned T4; do not use an unassigned device.
    assert len(cards)==1 and 'Tesla T4' in cards[0]
    uuid=cards[0].split(',')[1].strip()
    unit='sapiens08-c4p-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');raw=P/'outputs/common_view'/unit;raw.mkdir(parents=True,exist_ok=False);record=P/'runs'/unit;record.mkdir(parents=True)
    env={d.metadata['Name']:d.version for d in importlib.metadata.distributions()};atomic_json(raw/'ENVIRONMENT.json',env)
    ownpeak=max(r['peak_reserved_vram_mib'] for r in prof['cases']);peerpeak,count=peak_from_ledger(W/base['artifact_root']/'models/Sapiens2_0.4b/EXECUTION.jsonl')
    mapback=max(r['wh'][0]*r['wh'][1]*124/2**20 for r in pop)
    c={k:base[k] for k in ['protocol','protocol_sha256','YOLO','native_population','native_population_sha256','GT_binding_root','GT_manifest_sha256','GT_summary','precision','batch_size','input_hw','route','native_preserved','minimum_free_gib','max_stream_gib','max_hours','CUDA_VISIBLE_DEVICES','allocator_environment_preserved']}
    c.update(run_id=unit,scope='SAPIENS2_08B_C4P_PILOT_THEN_FULL_USER_AUTHORIZED',model=dict(row),model_id='Sapiens2_0.8b',
        artifact_root=str(raw.relative_to(W)),record_root=str(record.relative_to(W)),environment='.venvs/sapiens2-pilot',environment_sha256=sha_file(raw/'ENVIRONMENT.json'),
        checkpoint_stat=dict(size=ck.stat().st_size,mtime_ns=ck.stat().st_mtime_ns),checkpoint_sha256=digest,
        peer04_config=str(parent.relative_to(W)),peer04_config_sha256=sha_file(parent),peer04_artifact_root=base['artifact_root'],
        pilot_ids=['0021448','0006909','0001538','0001413','0027897','0031248'],warmup_id='0000930',
        expected_ids=ids,models=['Sapiens2_0.8b'],max_total_model_calls=5001,max_pilot_model_calls=7,max_warmup_calls=1,
        max_queue_hours=24,queue_poll_seconds=60,minimum_available_RAM_MiB=8192,automatic_model_OOM_retry=0,CPU_fallback=False,
        resource_policy='SHARED_GPU_QUALITY_ONLY',gpu_uuid=uuid,full_after_pilot_authorized=True,
        full_config_path='Human_Parsing_Benchmark/configs/cihp_sapiens_08b_full.json',
        existing_CPU_results='ALL_FOUR_COMPLETE_REUSE_BY_REFERENCE_NO_NEW_SCORING',
        historical08_profile=dict(path=str(oldprofile_path.relative_to(W)),sha256=sha_file(oldprofile_path),parameters=prof['parameters'],peak_reserved_MiB=ownpeak,scope='Resource evidence only; not canonical CIHP C4-P predictions'),
        admission=dict(peer04_peak_reserved_MiB_at_prepare=peerpeak,peer04_peak_samples=count,usable_cuda_total_MiB=usable/2**20,
                       largest_mapback_MiB=mapback,context_allowance_MiB=512,growth_allowance_MiB=1024,global_headroom_MiB=1024),
        resource_budget=dict(prediction_arrays_uncompressed_GiB=8.672606682404876,metadata_logs_refs_GiB=4,atomic_temporary_GiB=1,
                             headroom_GiB=8,estimated_additional_GiB=21.672606682404876,planning_envelope_GiB=200,not_a_global_cap=True,
                             actual_free_disk_GiB=shutil.disk_usage(raw).free/2**30,ETA=None),
        authority='User explicitly authorizes 0.8B pilot6+at most1warmup then full5000 when passed; shared concurrently with04 if resource guards pass; otherwise queue; no other models')
    assert c['resource_budget']['actual_free_disk_GiB']-2*c['resource_budget']['estimated_additional_GiB']>c['minimum_free_gib']
    files=[P/'scripts/prepare_sapiens08.py',P/'scripts/run_sapiens08.py',P/'src/common_view/sapiens08_resources.py',P/'tests/test_sapiens08_resources.py',P/'scripts/run_common_full.py',P/'scripts/monitor_cihp_batch.py',P/'scripts/render_common_pilot.py']
    science_sources={f:h for f,h in base['pilot_scientific_source_hashes'].items() if '/src/common_view/' in f or f.startswith('third_party/')}
    science_sources[str(config.relative_to(W))]=row['native_config_sha256']
    # Avoid carrying the 0.4B model config into the 0.8B scientific identity.
    science_sources.pop(base['model']['native_config'],None)
    c['scientific_source_hashes']=science_sources
    c['execution_source_hashes']={str(f.relative_to(W)):sha_file(f) for f in files}
    identity=dict(model_id=c['model_id'],checkpoint_sha256=digest,native_config_sha256=row['native_config_sha256'],source_commit=row['source_commit'],
                  environment_sha256=c['environment_sha256'],protocol_sha256=c['protocol_sha256'],route=c['route'],precision=c['precision'],
                  input_hw=c['input_hw'],batch_size=1,YOLO=c['YOLO'],source_hashes=science_sources)
    c['scientific_identity']=identity;c['scientific_identity_sha256']=fingerprint(identity)
    samples=[]
    for i in range(3):
        if i:time.sleep(2)
        samples.append(snapshot(c,W,ownpeak))
    atomic_json(record/'RESOURCE_READINESS.json',dict(status='ADMIT_PILOT' if all(r['admitted'] for r in samples) else 'QUEUE_REQUIRED',samples=samples,
        largest_mapback_all5000_MiB=mapback,queue_vs_execution_caps=dict(queue_hours=24,execution_hours=c['max_hours']),remaining_disk_GiB=shutil.disk_usage(raw).free/2**30,
        empirical_bounds_not_all_image_guarantee=True,only_one_visible_assigned_GPU=True))
    atomic_json(record/'READINESS.json',dict(status='PASS_PRE_FORWARD',model_id=c['model_id'],checkpoint_sha256=digest,checkpoint_stat=c['checkpoint_stat'],native_config_sha256=row['native_config_sha256'],
        source_commit=row['source_commit'],native29_head=[29,64,1,1],native29_dtype='F32',environment_sha256=c['environment_sha256'],torch=torch.__version__,CUDA=torch.version.cuda,
        config_pipeline_preprocessor_equivalent_to_04=True,common_scorer_acceptance='UNCHANGED_BINDINGS_REUSE_PREVIOUS23+7_CASES_NO_FULL_RETEST',
        new_resource_fixture_cases=4,strict_state_load_and_pilot='REQUIRED_NOT_YET_EXECUTED',model_calls=0))
    atomic_json(current,c);atomic_json(raw/'PILOT_CONFIG.json',c);atomic_json(record/'PILOT_CONFIG.json',c)
    atomic_json(record/'AUTHORIZATION.json',dict(status='USER_AUTHORIZED',scope=c['scope'],authority=c['authority'],pilot_config_sha256=sha_file(current),
        no04interruption=True,no_other_models=True,no_recompute_existing_four=True,shared_quality=True,model_calls=0))
    print(json.dumps(dict(run_id=unit,pilot_config=str(current.relative_to(W)),admitted=all(r['admitted'] for r in samples),estimated_combined_MiB=samples[-1]['estimated_combined_MiB'],usable_MiB=usable/2**20)),flush=True)
if __name__=='__main__':main()
