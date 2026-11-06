"""Fresh single-model continuation, merging accepted observations across segments.

No frozen source/config is edited. CPI uses the model-local revision3 already
tested by a separate bounded diagnostic; Sapiens scientific behavior is unchanged.
"""
import argparse
import inspect
import json
from pathlib import Path

import continue_controlled_cihp as previous
import finish_controlled_cihp_sapiens1b as finish

H,W=previous.H,previous.W
CPI='CPI_ConvNeXtB_CIHP';SAPIENS='Sapiens2_1b'
HEAD_SHA='85b75e0fe38465ec460107c11111702345a6de091a8ba3d399ca266878ca7573'


def generated_worker():
    text,changes=finish.generated_worker()
    old="effective_implementation='RPR_ROI_EMPTY_OUTPUT_1' if mid=='RPR_CIHP' else 'PARENT_MODEL_BEHAVIOR',"
    new="effective_implementation=config['implementation_revision'], implementation_history=config['implementation_history'],"
    if text.count(old)!=1:raise ValueError('Assembler metadata anchor differs')
    return text.replace(old,new),changes+[(old,new)]


def model_factory(workspace,spec,output):
    model=previous.model_factory(workspace,spec,output)
    if spec['model_id']==CPI:
        from cihp_benchmark.cpi_feature_schedule import install
        receipt=install(model.model.bbox_head,HEAD_SHA)
        model.details['memory_implementation']=receipt
        model.details['revision1_to_revision3']='Model-local; validated diagnostic reference is in CONFIG.json'
        previous.atomic(output/'MODEL_DETAILS.json',model.details)
    return model


def merge_references(inherited,fresh):
    if set(inherited).intersection(fresh):raise ValueError('Duplicate accepted observations across segments')
    return dict(inherited,**fresh)


def prepare(parentcp,mid,diagnostic=None):
    parentcp=Path(parentcp).resolve(strict=True);parent=previous.base.verify_config(parentcp)
    if mid not in (CPI,SAPIENS):raise ValueError('Out of current scope')
    pr=W/parent['artifact_root'];old=pr/mid;s=previous.read(old/'STATE.json')
    if mid==SAPIENS and s.get('error') not in ('KeyboardInterrupt()',"RuntimeError('RESOURCE_TIME_GUARD')"):
        raise ValueError('Expected operator pause or prior time guard')
    if mid==CPI and 'CUDA out of memory' not in s.get('error',''):
        raise ValueError('Expected retained ConvNeXt OOM evidence')
    direct_frames=sum(1 for _ in (old/'packets').iterdir())
    direct_rois=sum(1 for _ in (old/'roi_packets').iterdir())
    inherited_frames=parent.get('reuse_frames',{}).get(mid,{})
    inherited_rois=parent.get('reuse_ROIs',{}).get(mid,{})
    total_frames=direct_frames+len(inherited_frames);total_rois=direct_rois+len(inherited_rois)
    partial=sum(p.name.startswith(s['current_id']+'_') for p in (old/'roi_packets').iterdir())
    diagnostic_ref=None;diagnostic_seconds=0;diagnostic_bytes=0
    if mid==CPI:
        if diagnostic is None:raise ValueError('Passing model-bound diagnostic required')
        diagnostic=Path(diagnostic).resolve(strict=True);dr=previous.read(diagnostic/'STATE.json');dc=previous.read(diagnostic/'CONFIG.json')
        if dr['status']!='PASS' or dr['calls']!=3 or not dr['known_OOM_ROI_pass']:
            raise ValueError('CPI diagnostic has not passed')
        if dc['checkpoint']!=parent['models'][mid] or dc['parent_config_sha256']!=previous.sha(parentcp):
            raise ValueError('Diagnostic checkpoint/config binding mismatch')
        for path,digest in dc['profile_sources'].items():previous.base.checked(path,digest)
        diagnostic_ref=dict(root=previous.base.rel(diagnostic),state_sha256=previous.sha(diagnostic/'STATE.json'),
                            config_sha256=previous.sha(diagnostic/'CONFIG.json'),calls=3,canonical=False)
        diagnostic_seconds=dr['execution_wall_seconds'];diagnostic_bytes=sum(p.stat().st_size for p in diagnostic.rglob('*') if p.is_file())
    source=inspect.getsource(previous.prepare)
    pairs=[
        ("parentcp = H/'configs/controlled_cihp_quality.json'",'parentcp = PARENT_CONFIG'),
        ("if controller['status'] != 'STOPPED_REQUIRES_RECONCILIATION':","if controller['status'] not in ('STOPPED_REQUIRES_RECONCILIATION','MODEL_RUNNING'):"),
        ("pr/'RPR_CIHP/FAILURE.json'",'pr/MODEL_ID/\'FAILURE.json\''),
        ('failure[\'error\'] != "KeyError(\'parsing\')"','failure[\'error\'] != EXPECTED_ERROR'),
        ("root = H/'outputs'/('cihp-controlled-continuation-'","root = H/'outputs'/('cihp-pending-'+MODEL_ID.lower()+'-'"),
        ("continuation_reason='RPR zero-native-detection decoder repair; known CCTV implementation'","continuation_reason='Operator-authorized sequential completion, accepted cross-segment observations preserved'"),
        ("completed = ['QANet_CIHP_HRNetW48_512x384','M2FP_R101_CIHP','D2FP_R101_CIHP']",'completed = []'),
        ("    mid = 'RPR_CIHP'",'    mid = MODEL_ID'),
        ("config['reuse_frames'][mid]) != 22 or len(config['reuse_ROIs'][mid]) != 149","config['reuse_frames'][mid]) != DIRECT_FRAMES or len(config['reuse_ROIs'][mid]) != DIRECT_ROIS"),
        ("validate_native(arrays['native_crop_mask'],20,crop.shape[:2])","validate_native(arrays['native_crop_mask'],NATIVE_CLASSES,crop.shape[:2])"),
        ('validate_native(value,20,crop.shape[:2])','validate_native(value,NATIVE_CLASSES,crop.shape[:2])'),
        ('successful_frames=22,\n        successful_ROIs=149, attempted_VAL_calls=150','successful_frames=TOTAL_FRAMES,\n        successful_ROIs=TOTAL_ROIS, attempted_VAL_calls=PARENT_STATE[\'ROI_calls\']'),
        ('accepted_frames=22,accepted_ROIs=149','accepted_frames=TOTAL_FRAMES,accepted_ROIs=TOTAL_ROIS'),
        ("partial_frame='0000312',partial_frame_accepted_ROIs=2,missing_ROIs=parent['ROI_count']-149","partial_frame=failure['current_id'],partial_frame_accepted_ROIs=PARTIAL_ROIS,missing_ROIs=parent['ROI_count']-TOTAL_ROIS"),
        ("source_revision='RPR_ROI_EMPTY_OUTPUT_1'","source_revision='OPERATOR_SEQUENTIAL_PENDING_ONLY_1'"),
        ("config['prior_execution_seconds'][mid] = read(old/'STATE.json')['execution_wall_seconds']","config['prior_execution_seconds'][mid] = parent.get('prior_execution_seconds',{}).get(mid,0) + read(old/'STATE.json')['execution_wall_seconds'] + DIAGNOSTIC_SECONDS"),
        ("config['prior_stream_bytes'][mid] = sum(p.stat().st_size for p in old.rglob('*') if p.is_file())","config['prior_stream_bytes'][mid] = parent.get('prior_stream_bytes',{}).get(mid,0) + sum(p.stat().st_size for p in old.rglob('*') if p.is_file()) + DIAGNOSTIC_BYTES"),
    ]
    for old,new in pairs:
        if source.count(old)!=1:raise ValueError('Preparation source binding differs: '+old)
        source=source.replace(old,new)
    old="        if iid not in decoded:\n            decoded[iid] = base.load_frame(frames[iid])"
    if source.count(old)!=1:raise ValueError('Reconciliation cache anchor differs')
    source=source.replace(old,"        if iid not in decoded:\n            decoded.clear()\n            decoded[iid] = base.load_frame(frames[iid])")
    old="    config['parent_failure_sha256'] = sha(old/'FAILURE.json')"
    new="""    config['reuse_frames'][mid] = merge_references(INHERITED_FRAMES, config['reuse_frames'][mid])
    config['reuse_ROIs'][mid] = merge_references(INHERITED_ROIS, config['reuse_ROIs'][mid])
    if len(config['reuse_frames'][mid]) != TOTAL_FRAMES or len(config['reuse_ROIs'][mid]) != TOTAL_ROIS:
        raise ValueError('Cross-segment accepted membership differs')
    for reference in list(INHERITED_FRAMES.values()) + list(INHERITED_ROIS.values()):
        for name, digest in reference['members'].items():
            if sha(W/reference['packet']/name) != digest:
                raise ValueError('Inherited immutable packet member changed')
    config['parent_failure_sha256'] = sha(old/'FAILURE.json')"""
    if source.count(old)!=1:raise ValueError('Merge anchor differs')
    source=source.replace(old,new)
    old='    generated, changes = generated_worker()'
    new="""    config['model_order'] = [mid]
    config['held_models'] = {}
    config['execution_time_limit_enabled'] = False
    config['max_hours'] = None
    config['implementation_revision'] = 'CPI_FEATURE_BRANCH_SCHEDULE_3' if mid == 'CPI_ConvNeXtB_CIHP' else 'PARENT_MODEL_BEHAVIOR'
    config['implementation_history'] = dict(parent_revision='CPI_PERSON_CHUNK_RESTORATION_1' if mid == 'CPI_ConvNeXtB_CIHP' else 'PARENT_MODEL_BEHAVIOR', parent_accepted_ROIs=TOTAL_ROIS, new_revision=config['implementation_revision'])
    config['diagnostic_reference'] = DIAGNOSTIC_REFERENCE
    config['resource_policy_amendment'] = dict(id='OPERATOR_SEQUENTIAL_FINISH_NO_WALL_CAP_1', model_id=mid,
        authority='User requests pause/preparation then Sapiens completion followed by CPI; prior explicit request to finish without artificial time cap',
        authorized_utc=base.utc(), original_time_limit_preserved_in_parent=True, max_hours=None,
        preserved_elapsed_seconds=config['prior_execution_seconds'][mid], other_guards_unchanged=True,
        automatic_model_OOM_retries=0, scientific_parameters_changed=False)
    config['source_hashes'][base.rel(Path(__file__))] = sha(Path(__file__))
    for path in [H/'scripts/finish_controlled_cihp_sapiens1b.py', H/'src/cihp_benchmark/cpi_memory.py', H/'src/cihp_benchmark/cpi_feature_memory.py', H/'src/cihp_benchmark/cpi_feature_schedule.py']:
        config['source_hashes'][base.rel(path)] = sha(path)
    generated, changes = generated_worker()"""
    if source.count(old)!=1:raise ValueError('Worker snapshot anchor differs')
    source=source.replace(old,new)
    ns=dict(vars(previous),generated_worker=generated_worker,__file__=__file__,PARENT_CONFIG=parentcp,
        MODEL_ID=mid,EXPECTED_ERROR=s['error'],DIRECT_FRAMES=direct_frames,DIRECT_ROIS=direct_rois,
        TOTAL_FRAMES=total_frames,TOTAL_ROIS=total_rois,PARTIAL_ROIS=partial,NATIVE_CLASSES=20 if mid==CPI else 29,
        INHERITED_FRAMES=inherited_frames,INHERITED_ROIS=inherited_rois,merge_references=merge_references,
        PARENT_STATE=s,DIAGNOSTIC_REFERENCE=diagnostic_ref,DIAGNOSTIC_SECONDS=diagnostic_seconds,DIAGNOSTIC_BYTES=diagnostic_bytes)
    exec(compile(source,'<cross-segment-pending-prepare>','exec'),ns);ns['prepare']()


def terminal_report(cp,mid):
    c=previous.read(cp);root=W/c['artifact_root'];out=root/mid
    if not (out/'COMPLETION.json').exists():return
    s=previous.read(out/'COMPLETION.json');state=previous.read(out/'STATE.json')
    parent_ids=set(c['reuse_frames'][mid]);fresh={p.name for p in (out/'packets').iterdir() if p.is_dir()} if (out/'packets').exists() else set()
    expected=set(previous.read(W/c['manifest'])['expected_ids']);all_ids=parent_ids|fresh
    good=(s.get('strict_complete') is True and all_ids==expected and not parent_ids.intersection(fresh)
          and s.get('failed')==s.get('invalid')==0 and previous.sha(out/'METRICS.json')==s.get('metrics_sha256'))
    r=dict(status='COMPLETE' if good else 'STOPPED_INCOMPLETE',run_id=c['run_id'],model_id=mid,
        checked_utc=previous.base.utc(),expected=5000,unique_frame_ids=len(all_ids),missing=len(expected-all_ids),
        duplicate=len(parent_ids&fresh),unexpected=len(all_ids-expected),reused_frames=len(parent_ids),new_frames=len(fresh),
        accepted_parent_ROIs=len(c['reuse_ROIs'][mid]),new_VAL_calls=state['ROI_calls'],new_TRAIN_calls=state['warmup_calls'],
        failed=s.get('failed'),invalid=s.get('invalid'),strict_complete=good,primary=s.get('primary') if good else None,
        metrics_path=previous.base.rel(out/'METRICS.json') if good else None,metrics_sha256=s.get('metrics_sha256') if good else None,
        cumulative_execution_seconds=c['prior_execution_seconds'][mid]+state.get('execution_wall_seconds',0),
        parent_config=c['parent_config'],historical_failure_sha256=c['parent_failure_sha256'],
        implementation_history=c['implementation_history'],diagnostic_reference=c['diagnostic_reference'],
        execution_time_limit_enabled=False,speed_ranking_allowed=False,automatic_retries=0)
    previous.atomic(root/'ROUND_CLOSURE.json',r)
    (root/'SUMMARY_TH.md').write_text('# สรุป '+mid+'\n\n'+
        f"สถานะ **{r['status']}**, UTC {r['checked_utc']}; {len(all_ids)}/5000unique, missing{r['missing']}, duplicate{r['duplicate']}, failed{r['failed']}, invalid{r['invalid']}.\n\n"+
        f"Reuse {len(parent_ids)}frames/{r['accepted_parent_ROIs']}ROIs; new{len(fresh)}frames/{r['new_VAL_calls']}VALcalls. เวลาสะสม{r['cumulative_execution_seconds']/3600:.3f}ชั่วโมง.\n\n"+
        f"Canonical metrics `{r['metrics_path']}`; primary{json.dumps(r['primary'],ensure_ascii=False)}. ดูROUND_CLOSURE.jsonสำหรับhash/provenanceและประวัติimplementation.\n\n"+
        'YOLO-conditioned application pipeline, C4-P revision2 Face proxy/Upper-Lower non-Dress. Timingเป็นdiagnostics ไม่จัดอันดับความเร็ว;ไม่มีtraining/precision/resolution/threshold/mapping changes. เก็บhistoricalOOM/interruptionsและpartialoutputsครบ.\n')
    if s.get('strict_complete') and not good:raise ValueError('Final assembled membership/hash closure failed')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','worker','controller','progress'])
    p.add_argument('--parent',type=Path);p.add_argument('--model',choices=[CPI,SAPIENS]);p.add_argument('--config',type=Path);p.add_argument('--diagnostic',type=Path)
    a=p.parse_args()
    if a.action=='prepare':prepare(a.parent,a.model,a.diagnostic);return
    if not a.config:raise ValueError('Explicit config required')
    c=previous.read(a.config)
    if a.action=='progress':previous.progress(a.config);return
    if len(c['model_order'])!=1 or c['model_order'][0] not in (CPI,SAPIENS):raise ValueError('Single-model scope required')
    previous.__file__=__file__;previous.generated_worker=generated_worker
    if a.action=='controller':previous.controller(a.config);return
    if a.model!=c['model_order'][0]:raise ValueError('Model differs from continuation scope')
    config=previous.base.verify_config(a.config);source,_=generated_worker()
    if source!=previous.base.checked(config['generated_worker'],config['generated_worker_sha256']).read_text():raise ValueError('Worker snapshot differs')
    if a.model==CPI:
        ref=config['diagnostic_reference'];dr=W/ref['root']
        previous.base.checked(previous.base.rel(dr/'STATE.json'),ref['state_sha256'])
        previous.base.checked(previous.base.rel(dr/'CONFIG.json'),ref['config_sha256'])
    ns=dict(vars(previous.base),model_factory=model_factory,verify_reuse=previous.verify_reuse,accumulate=previous.accumulate)
    exec(compile(source,str(W/config['generated_worker']),'exec'),ns)
    try:ns['worker'](a.config,a.model)
    finally:terminal_report(a.config,a.model)


if __name__=='__main__':main()
