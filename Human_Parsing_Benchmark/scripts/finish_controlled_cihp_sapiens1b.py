"""Explicit operator continuation of Sapiens1B to completion, without a time cap.

Only orchestration changes. Frozen scientific inference/scoring and earlier
configs remain untouched. Disk/VRAM/call/contract guards and no-retry policy stay.
"""
import argparse
import inspect
import json
from pathlib import Path

import continue_controlled_cihp as previous
import continue_controlled_cihp_resources as resources

H, W = previous.H, previous.W
MID = 'Sapiens2_1b'
TIME_CONDITION = "if time.monotonic()-started+config['prior_execution_seconds'].get(mid,0) > config['max_hours']*3600:"
AMENDED_TIME_CONDITION = "if config.get('execution_time_limit_enabled', True) and time.monotonic()-started+config['prior_execution_seconds'].get(mid,0) > config['max_hours']*3600:"


def generated_worker():
    source, changes = resources.generated_worker()
    if source.count(TIME_CONDITION) != 1:
        raise ValueError('Frozen time guard source differs')
    source = source.replace(TIME_CONDITION, AMENDED_TIME_CONDITION)
    compile(source, '<sapiens1b-operator-time-waiver>', 'exec')
    return source, changes + [(TIME_CONDITION, AMENDED_TIME_CONDITION)]


def prepare(parentcp):
    parentcp = Path(parentcp).resolve(strict=True)
    parent = previous.base.verify_config(parentcp)
    pr = W / parent['artifact_root']
    state = previous.read(pr/MID/'STATE.json')
    if state['status'] != 'STOPPED_INCOMPLETE' or state['error'] != "RuntimeError('RESOURCE_TIME_GUARD')":
        raise ValueError('Scoped only to the terminal Sapiens1B time-guard stop')
    expected_frames = state['completed']
    expected_rois = sum(1 for _ in (pr/MID/'roi_packets').iterdir())
    partial_rois = sum(p.name.startswith(state['current_id']+'_') for p in (pr/MID/'roi_packets').iterdir())
    source = inspect.getsource(previous.prepare)
    replacements = [
        ("parentcp = H/'configs/controlled_cihp_quality.json'", 'parentcp = PARENT_CONFIG'),
        ("pr/'RPR_CIHP/FAILURE.json'", "pr/'Sapiens2_1b/FAILURE.json'"),
        ('failure[\'error\'] != "KeyError(\'parsing\')"', 'failure[\'error\'] != "RuntimeError(\'RESOURCE_TIME_GUARD\')"'),
        ("root = H/'outputs'/('cihp-controlled-continuation-'", "root = H/'outputs'/('cihp-sapiens1b-finish-'"),
        ("continuation_reason='RPR zero-native-detection decoder repair; known CCTV implementation'", "continuation_reason='User explicitly waives Sapiens1B wall-time cap to finish exact5000; identical scientific worker'"),
        ("completed = ['QANet_CIHP_HRNetW48_512x384','M2FP_R101_CIHP','D2FP_R101_CIHP']", "completed = ['QANet_CIHP_HRNetW48_512x384','M2FP_R101_CIHP','D2FP_R101_CIHP','RPR_CIHP','CPI_R50_CIHP','Sapiens2_0.4b','Sapiens2_0.8b']"),
        ("    mid = 'RPR_CIHP'", "    mid = 'Sapiens2_1b'"),
        ("config['reuse_frames'][mid]) != 22 or len(config['reuse_ROIs'][mid]) != 149", "config['reuse_frames'][mid]) != EXPECTED_FRAMES or len(config['reuse_ROIs'][mid]) != EXPECTED_ROIS"),
        ("validate_native(arrays['native_crop_mask'],20,crop.shape[:2])", "validate_native(arrays['native_crop_mask'],29,crop.shape[:2])"),
        ('validate_native(value,20,crop.shape[:2])', 'validate_native(value,29,crop.shape[:2])'),
        ('successful_frames=22,\n        successful_ROIs=149, attempted_VAL_calls=150', 'successful_frames=EXPECTED_FRAMES,\n        successful_ROIs=EXPECTED_ROIS, attempted_VAL_calls=EXPECTED_ROIS'),
        ('accepted_frames=22,accepted_ROIs=149', 'accepted_frames=EXPECTED_FRAMES,accepted_ROIs=EXPECTED_ROIS'),
        ("partial_frame='0000312',partial_frame_accepted_ROIs=2,missing_ROIs=parent['ROI_count']-149", "partial_frame=failure['current_id'],partial_frame_accepted_ROIs=PARTIAL_ROIS,missing_ROIs=parent['ROI_count']-EXPECTED_ROIS"),
        ("source_revision='RPR_ROI_EMPTY_OUTPUT_1'", "source_revision='SAPIENS1B_OPERATOR_TIME_CAP_REMOVED_1'"),
        ("config['prior_execution_seconds'][mid] = read(old/'STATE.json')['execution_wall_seconds']", "config['prior_execution_seconds'][mid] = parent.get('prior_execution_seconds',{}).get(mid,0) + read(old/'STATE.json')['execution_wall_seconds']"),
        ("config['prior_stream_bytes'][mid] = sum(p.stat().st_size for p in old.rglob('*') if p.is_file())", "config['prior_stream_bytes'][mid] = parent.get('prior_stream_bytes',{}).get(mid,0) + sum(p.stat().st_size for p in old.rglob('*') if p.is_file())"),
    ]
    for old, new in replacements:
        if source.count(old) != 1:
            raise ValueError('Preparation binding differs: '+old)
        source = source.replace(old,new)
    source = source.replace("old = pr/mid", "old = W/parent['completed_sources'][mid]['root'] if mid in parent.get('completed_sources',{}) else pr/mid")
    old = "        if iid not in decoded:\n            decoded[iid] = base.load_frame(frames[iid])"
    if source.count(old) != 1:
        raise ValueError('One-frame reconciliation cache binding differs')
    source = source.replace(old, "        if iid not in decoded:\n            decoded.clear()\n            decoded[iid] = base.load_frame(frames[iid])")
    old = '    generated, changes = generated_worker()'
    amendment = """    config['model_order'] = completed + ['Sapiens2_1b']
    config['held_models'] = dict(parent['held_models'])
    config['execution_time_limit_enabled'] = False
    config['max_hours'] = None
    config['resource_policy_amendment'] = dict(
        id='SAPIENS1B_OPERATOR_TIME_CAP_REMOVED_1', model_id='Sapiens2_1b',
        authorized_utc=base.utc(), authority='Current explicit user instruction',
        instruction='รันต่อทำต่อเลยเรื่องเพดานเวลาอะไร มันไม่จำเป็นหนิ เอาให้มันรันครบเเละสร็จ',
        old_max_hours=parent['max_hours'], new_max_hours=None,
        retained_guards=['VRAM','80GiB cumulative checkpoint stream','50GiB free disk','finite model-call budget','binding/output contract'],
        automatic_model_OOM_retries=0, reset_prior_elapsed=False,
        scientific_settings_changed=False, next_model_after_1b=False)
    config['source_hashes'][base.rel(Path(__file__))] = sha(Path(__file__))
    generated, changes = generated_worker()"""
    if source.count(old) != 1:
        raise ValueError('Generated worker snapshot binding differs')
    source = source.replace(old, amendment)
    namespace = dict(vars(previous),generated_worker=generated_worker,__file__=__file__,
                     PARENT_CONFIG=parentcp,EXPECTED_FRAMES=expected_frames,
                     EXPECTED_ROIS=expected_rois,PARTIAL_ROIS=partial_rois)
    exec(compile(source,'<sapiens1b-finish-prepare>','exec'),namespace)
    namespace['prepare']()


def terminal_report(cp):
    c = previous.read(cp); root = W/c['artifact_root']; out = root/MID
    completion = out/'COMPLETION.json'
    if not completion.exists():
        return
    s = previous.read(completion)
    parent = previous.read(W/c['parent_config'])
    parent_root = W/parent['artifact_root']
    old_failure = parent_root/MID/'FAILURE.json'
    done = set(c['reuse_frames'][MID])
    new = [p.name for p in (out/'packets').iterdir() if p.is_dir()] if (out/'packets').exists() else []
    duplicates = len(done.intersection(new))
    all_ids = done.union(new)
    expected = set(previous.read(W/c['manifest'])['expected_ids'])
    valid_complete = (s.get('strict_complete') is True and len(all_ids)==5000
                      and all_ids==expected and duplicates==0 and s.get('failed')==0
                      and s.get('invalid')==0 and (out/'METRICS.json').is_file()
                      and previous.sha(out/'METRICS.json')==s.get('metrics_sha256'))
    state = previous.read(out/'STATE.json')
    total_seconds = c['prior_execution_seconds'][MID]+state.get('execution_wall_seconds',0)
    closure = dict(status='COMPLETE' if valid_complete else 'STOPPED_INCOMPLETE',
        run_id=c['run_id'],model_id=MID,parent_run=parent['run_id'],
        checked_utc=previous.base.utc(),expected=5000,unique_frame_ids=len(all_ids),
        missing=len(expected-all_ids),duplicate=duplicates,unexpected=len(all_ids-expected),
        reused_frames=len(done),new_frames=len(new),accepted_parent_ROIs=len(c['reuse_ROIs'][MID]),
        new_VAL_calls=state['ROI_calls'],new_TRAIN_calls=state['warmup_calls'],
        failed=s.get('failed'),invalid=s.get('invalid'),strict_complete=valid_complete,
        primary=s.get('primary') if valid_complete else None,
        metrics_path=previous.base.rel(out/'METRICS.json') if valid_complete else None,
        metrics_sha256=s.get('metrics_sha256') if valid_complete else None,
        cumulative_execution_seconds=total_seconds,
        historical_failure=dict(path=previous.base.rel(old_failure),sha256=previous.sha(old_failure),preserved=True),
        execution_time_limit_enabled=False,resource_amendment=c['resource_policy_amendment']['id'],
        speed_ranking_allowed=False,queue_stops_after_1b=True)
    previous.atomic(root/'ROUND_CLOSURE.json',closure)
    text = ('# สรุป continuation Sapiens2 1B\n\n'
            f"สถานะ **{closure['status']}**; ตรวจ UTC {closure['checked_utc']}\n\n"
            f"Run `{c['run_id']}` ต่อจาก `{parent['run_id']}`. ผู้ใช้ยกเลิกเพดานเวลาเฉพาะ1B; checkpoint/FP32/input/ownership/scorerเดิม.\n\n"
            f"ผลรวม {len(all_ids)}/5000 ภาพ; reuse {len(done)}, new {len(new)}, missing {closure['missing']}, duplicate {duplicates}, failed {s.get('failed')}, invalid {s.get('invalid')}.\n\n"
            f"ROIเดิม {closure['accepted_parent_ROIs']}, VAL callsใหม่ {state['ROI_calls']}, TRAIN callsใหม่ {state['warmup_calls']}; เวลาสะสมทุกsegment {total_seconds/3600:.3f}ชั่วโมง.\n\n"
            f"STRICT_COMPLETE={valid_complete}; คะแนนหลัก {json.dumps(closure['primary'],ensure_ascii=False)}.\n\n"
            f"Canonical metrics: `{closure['metrics_path']}`. รายละเอียด exact-ID/hash closure: `ROUND_CLOSURE.json`.\n\n"
            'ผลเป็น YOLO-conditioned application pipeline; Face proxy/Upper-Lower non-Dress ตามC4-P revision2. Timingเป็นdiagnostics ไม่ใช้จัดอันดับความเร็ว. ประวัติtime-guardเดิมและpartial artifactsไม่ถูกลบ. CPIConvNeXtยังพัก;ไม่เปิดโมเดลอื่น.\n')
    (root/'SUMMARY_TH.md').write_text(text)
    if s.get('strict_complete') is True and not valid_complete:
        raise ValueError('Terminal assembled membership/metrics reconciliation failed')


def progress(cp):
    previous.progress(cp)
    c = previous.read(cp); root = W/c['artifact_root']; sp = root/MID/'STATE.json'
    if sp.exists():
        s=previous.read(sp)
        print('1B reused_frames',s.get('reused_frames',0),'partial_ROIs',s.get('reused_partial_ROIs',0),
              'time_cap','REMOVED_BY_USER','prior_hours',round(c['prior_execution_seconds'][MID]/3600,3))
    for mid, ref in c['held_models'].items():
        s=previous.read(W/ref['root']/'STATE.json')
        print(mid,'HELD_INCOMPLETE',str(s['completed'])+'/5000',ref['reason'])
    if (root/'ROUND_CLOSURE.json').exists():
        s=previous.read(root/'ROUND_CLOSURE.json')
        print('ROUND_CLOSURE',s['status'],'unique',s['unique_frame_ids'],'missing',s['missing'],'duplicate',s['duplicate'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','worker','controller','progress'])
    p.add_argument('--parent',type=Path)
    p.add_argument('--config',type=Path)
    p.add_argument('--model')
    a=p.parse_args()
    if a.action=='prepare':
        if not a.parent:raise ValueError('Explicit terminal parent config required')
        prepare(a.parent);return
    if not a.config:raise ValueError('Explicit continuation config required')
    if a.action=='progress':progress(a.config);return
    previous.__file__=__file__
    previous.generated_worker=generated_worker
    if a.action=='worker':
        if a.model!=MID:raise ValueError('Only Sapiens2_1b authorized')
        try:previous.worker(a.config,a.model)
        finally:terminal_report(a.config)
    else:
        c=previous.read(a.config)
        if [m for m in c['model_order'] if m not in c['completed_sources']] != [MID]:
            raise ValueError('Queue scope must be Sapiens1B only')
        previous.controller(a.config)


if __name__=='__main__':main()
