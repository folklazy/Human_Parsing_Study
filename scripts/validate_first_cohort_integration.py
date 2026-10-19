"""Focused integration verification and explicit historical evidence scope accounting."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import difflib
import json
import re
import shutil
import subprocess
import sys

S = Path(__file__).resolve().parents[1]
W = S.parent
sys.path.insert(0,str(S))
from src.application_v2.artifacts import file_hash, resume_packet
from src.application_v2.policy import load_config, digest
from src.application_v2.validation_packages import validate_packages


def write(path,data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def main():
    run = S/json.loads((S/'provenance/FIRST_COHORT_INTEGRATION_ACTIVE.json').read_text())['run']
    config_path = S/'configs/application_v2_first_cohort_v9.yaml'
    cfg = load_config(config_path)
    prior = S/'provenance/RUN_MANIFESTS/first-cohort-policy-acceptance-20261016T034543760531Z'
    recent = S/'provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z'
    old_validation = json.loads((prior/'validation_v2/VALIDATION.json').read_text())
    old126 = json.loads((run/'ORIGINAL_126_BASELINE.json').read_text())
    hashes126 = old126['protected_hashes_before']
    recent37 = json.loads((recent/'PROTECTED_EXISTING_FILES.json').read_text())
    hashes37 = {str(S.name+'/'+r['path']):r['sha256'] for r in recent37}
    # PPSS is paused: do not reopen even its two documentation files.
    paused = [p for p in hashes37 if 'ppss' in p.lower()]
    rechecked37 = {p:h for p,h in hashes37.items() if p not in paused}
    changed126 = [p for p,h in hashes126.items() if file_hash(W/p)!=h]
    changed37 = [p for p,h in rechecked37.items() if file_hash(W/p)!=h]
    archive_stat_changes = []
    for p,row in old126['original_archive_stats_before'].items():
        stat=(W/p).stat()
        if (stat.st_size,stat.st_mtime_ns)!=(row['size'],row['mtime_ns']):archive_stat_changes.append(p)
    foundation_tests = [Path(row['command'][-1]) for row in old_validation['suite_results'][1:]]
    source_snapshot = S/'provenance/RUN_MANIFESTS/first-cohort-context-closure-20261016T030334073358Z/validation_20261016T030838793503Z/source_snapshot'
    test_hash_checks=[]
    for name in foundation_tests:
        p=S/'tests'/name
        old=source_snapshot/'tests'/name
        test_hash_checks.append(dict(path=str(p.relative_to(S)),prior_snapshot=str(old.relative_to(S)),
                                    unchanged=file_hash(p)==file_hash(old)))
    foundation_sources = {p:h for p,h in hashes126.items() if p.startswith(S.name+'/src/')}
    scope = dict(old_full_suite=dict(total=190,application=123,foundation=67,
                 evidence=str((prior/'validation_v2/VALIDATION.json').relative_to(S))),
        recent_application_only=dict(total=131,prior_application=123,added=8,
                 evidence=str((recent/'VALIDATION.json').relative_to(S))),
        old_protected126=dict(total=126,groups={prefix:sum(p.startswith(prefix+'/') for p in hashes126)
                                  for prefix in sorted({p.split('/')[0] for p in hashes126})}),
        recent_protected37=dict(total=37,intersection_with_126=sorted(set(hashes37)&set(hashes126)),
             is_subset_of_126=set(hashes37)<=set(hashes126),rechecked_now=len(rechecked37),
             paused_PPSS_not_reopened=paused,prior_record=str((recent/'PROTECTED_EXISTING_FILES.json').relative_to(S))),
        protected126_changed=changed126,recent_non_PPSS_protected_changed=changed37,
        foundation_test_hash_checks=test_hash_checks,
        foundation_production_source_hashes=foundation_sources,
        foundation_production_changed=[p for p in foundation_sources if p in changed126],
        foundation_test_execution='REUSE_PREVIOUS_67_PASS_NO_PRODUCTION_OR_TEST_CHANGES',
        foundation_not_newly_executed=True,
        original_archive_stat_changes=archive_stat_changes,
        limitation='Hashes protect only named files, not every file in the workspace; archive stats are not new full archive hashes')
    write(run/'EVIDENCE_SCOPE_RECONCILIATION.json',scope)
    log=run/'CPU_APPLICATION_TESTS.log'
    command=[sys.executable,'-m','unittest','discover','-s',str(S/'tests'),'-p','test_application_v2*.py']
    done=subprocess.run(command,cwd=S,capture_output=True,text=True,timeout=180)
    log.write_text(done.stdout+done.stderr)
    count=re.search(r'Ran (\d+) tests?',log.read_text())
    if done.returncode or count is None:raise RuntimeError('Application tests failed: '+str(log))
    package=validate_packages(cfg,S)
    fresh=run/'fresh_train_v1'
    integration=json.loads((fresh/'INTEGRATION.json').read_text())
    if integration['status']!='PASS' or integration['config_sha256']!=digest(cfg):
        raise ValueError('Fresh integration/config mismatch')
    attempts=json.loads((fresh/'PROCESS_ATTEMPTS.json').read_text())
    assert len(attempts)==3 and all(r['exit_code']==0 and r['status']=='PASS' for r in attempts)
    plan=json.loads((fresh/'WORKER_PLAN.json').read_text())
    assert plan['config_sha256']==digest(cfg)
    for process in attempts:
        worker=json.loads((S/process['run_manifest']).read_text())
        assert worker['plan_sha256']==file_hash(fresh/'WORKER_PLAN.json')
        assert worker['worker_sha256']==file_hash(S/'scripts/first_cohort_gpu_worker.py')
        assert worker['checkpoint_loaded'] and worker['precision']=='FP32'
        assert [r['image_id'] for r in worker['images']]==cfg['first_cohort']['engineering']['input_ids']
    packets=[]
    for frame in integration['frames']:
        path=S/frame['packet']
        record=json.loads((path/'record.json').read_text())
        resume_packet(path,record['fingerprints']['inference'])
        assert record['adapter_revision']==file_hash(S/'src/application_v2/first_cohort_fresh.py')
        assert record['config_sha256']==digest(cfg)
        for person in record['persons']:
            assert person['identity']['native_instance_id'] is not None
            assert person['identity']['source_opportunity_id'] is not None
            assert person['evaluation_bbox']['source']=='NATIVE_PARSER_BOX'
        packets.append(str(path.relative_to(S)))
    for view in ['primary','secondary']:
        report=json.loads((fresh/(view.upper()+'_REPORT.json')).read_text())
        frames=json.loads((fresh/(view.upper()+'_FRAME_SCORES.json')).read_text())
        from src.application_v2.runner import ConfiguredRunner
        rebuilt=ConfiguredRunner(config_path,mode='FRESH_TRAIN_INTEGRATION').comparison_report(cfg['scoring_population'],frames,matching_view=view)
        assert rebuilt['systems']==report['systems']
        assert all(row['main_score_eligible'] and row['population']==dict(frames=3,G_loc=7,G_sem=7) for row in report['systems'])
    try:load_config(config_path,benchmark=True)
    except ValueError:guard='PASS_REJECTED'
    else:raise ValueError('Full benchmark unexpectedly enabled')
    before=json.loads((run/'BEFORE.json').read_text())
    revisions=[];diff=[]
    snapshot=run/'source_snapshot'
    oldrows={row['path']:row for row in before}
    paths=[*S.glob('src/application_v2/*.py'),*S.glob('tests/test_application_v2*.py'),
           *[S/p for p in ['scripts/first_cohort_entrypoint.py','scripts/first_cohort_gpu_worker.py',
             'scripts/prepare_first_cohort_integration.py','scripts/validate_first_cohort_integration.py',
             'configs/application_v2_first_cohort_v9.yaml','provenance/APPLICATION_V2_DECISIONS_V8.json']]]
    for p in paths:
        rel=str(p.relative_to(S)); dest=snapshot/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        old=oldrows.get(rel);current=file_hash(p)
        if old and old['before_sha256']==current:continue
        original=(S/old['archive']).read_text() if old else ''
        revisions.append(dict(path=rel,before_sha256=old['before_sha256'] if old else None,after_sha256=current))
        diff.append(''.join(difflib.unified_diff(original.splitlines(True),p.read_text().splitlines(True),fromfile='before/'+rel,tofile=rel)))
    write(run/'SOURCE_REVISIONS.json',revisions)
    (run/'SOURCE.diff').write_text('\n'.join(diff))
    git=[]
    for root in [W,S,*sorted(W.glob('YOLO*'))]:
        if not root.is_dir():continue
        record=subprocess.run(['git','status','--porcelain'],cwd=root,capture_output=True,text=True)
        git.append(dict(path='.' if root==W else str(root.relative_to(W)),is_repository=record.returncode==0,
                        status=record.stdout,error=record.stderr.strip()))
    write(run/'GIT_STATUS_AFTER.json',git)
    passed=not(changed126 or changed37 or archive_stat_changes) and all(r['unchanged'] for r in test_hash_checks)
    validation=dict(status='PASS' if passed else 'FAIL',timestamp_utc=datetime.now(timezone.utc).isoformat(),
        CPU_application_tests=int(count[1]),CPU_test_log=str(log.relative_to(S)),
        reused_foundation_tests=67,foundation_tests_rerun=False,old_126_checked=126,old_126_changed=changed126,
        recent_37_rechecked_excluding_PPSS=len(rechecked37),recent_37_changed=changed37,
        validation_packages=package,fresh_TRAIN_route='PASS',scorer_reporter='PASS_PRIMARY_AND_SECONDARY',
        accepted_TRAIN_contexts=6,TRAIN_frames_per_system=3,G_loc_per_system=7,G_sem_per_system=7,
        protected_original_archive_stats_unchanged=not archive_stat_changes,
        current_source_snapshot=str(snapshot.relative_to(S)),source_changes=str((run/'SOURCE_REVISIONS.json').relative_to(S)),
        frozen_YOLO_checkpoint_verified_by_fresh_worker=True,canonical_YOLO_results_changed=False,
        validation_inference=False,full_benchmark_started=False,scientific_freeze=False,
        benchmark_guard=guard,ranking_generated=False,PPSS_activity=False,downloads=False,
        readiness='BOUNDED_INTEGRATION_CLOSED_READY_FOR_SEPARATE_BENCHMARK_APPROVAL_REVIEW',
        limitations=['Only three TRAIN frames per system; no claim of full-validation completion or capacity',
                     'Current entry point authorizes TRAIN only; validation launch remains disabled',
                     'Mapping accepted with indirect evidence; no new direct-header claim',
                     'Quality-only; no clean repeated latency/VRAM ranking'])
    write(run/'VALIDATION.json',validation)
    print(json.dumps({key:validation[key] for key in ['status','CPU_application_tests','reused_foundation_tests',
        'old_126_checked','recent_37_rechecked_excluding_PPSS','fresh_TRAIN_route','scorer_reporter','full_benchmark_started']}))
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
