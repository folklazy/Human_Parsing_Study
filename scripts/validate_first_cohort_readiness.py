"""CPU tests and bounded-route provenance validation; no model execution."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,subprocess,re,difflib,shutil
S=Path(__file__).resolve().parents[1];W=S.parent;sys.path.insert(0,str(S))
from src.application_v2.policy import load_config,digest,fingerprints
from src.application_v2.artifacts import file_hash,resume_packet
R=S/json.loads((S/'provenance/FIRST_COHORT_READINESS_ACTIVE.json').read_text())['run']
out=R/('validation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
results=[]
for pattern in ['test_application_v2*.py','test_mhpv2_stage0.py','test_official_mhp_compat.py','test_dataset_reassessment.py','test_ccihp_gt.py','test_ccihp_quality.py']:
 command=[sys.executable,'-m','unittest','discover','-s',str(S/'tests'),'-p',pattern]
 done=subprocess.run(command,cwd=S,capture_output=True,text=True,timeout=180);text=done.stdout+done.stderr;log=out/(pattern.replace('*','ALL')+'.log');log.write_text(text);m=re.search(r'Ran (\d+) tests?',text)
 results.append({'command':command,'exit_code':done.returncode,'tests':int(m[1]) if m else None,'log':str(log.relative_to(S))})
config=load_config(S/'configs/application_v2_first_cohort_v5.yaml')
try:load_config(S/'configs/application_v2_first_cohort_v5.yaml',benchmark=True)
except ValueError:guard='PASS_REJECTED'
else:raise ValueError('Unexpected benchmark authorization')
assert json.loads((S/config['cohort']['mapping']).read_text())['status']=='DRAFT'
pops=json.loads((R/'POPULATION_BINDINGS_DRAFT.json').read_text());population_checks=[]
for name,row in pops['populations'].items():
 p=S/row['expected_frame_manifest'];assert file_hash(p)==row['expected_frame_manifest_sha256']
 frames=[json.loads(line) for line in p.open()];assert len(frames)==len({f['image_id'] for f in frames})==row['frames']
 assert sum(f['G_loc'] for f in frames)==row['G_loc_structural_draft'] and sum(f['G_sem'] for f in frames)==row['G_sem_candidate_draft']
 assert all(0<=f['G_sem']<=f['G_loc'] for f in frames)
 population_checks.append({'population':name,'frames':len(frames),'G_loc':row['G_loc_structural_draft'],'G_sem_draft':row['G_sem_candidate_draft'],'status':'PASS_METADATA_ONLY_ROLE_NOT_ACCEPTED'})
lineage=json.loads((R/'V4_TO_V5_LINEAGE.json').read_text());packets=[]
for row in lineage['models']:
 expected=fingerprints(config,row['inference_dependencies']);record=resume_packet(S/row['canonical_V5_packet'],expected['inference']);assert record['fingerprints']==expected
 assert record['checkpoint_sha256']==row['inference_dependencies']['native_checkpoint_sha256'];packets.append(row['canonical_V5_packet'])
comparison=json.loads((R/'COMPARISON_ENGINEERING_STATUS_V5.json').read_text())
assert len(comparison['systems'])==2 and all(x['main_metrics'] is None and x['execution']['completed']==1 for x in comparison['systems'])
old=S/json.loads((S/'provenance/APPLICATION_V2_IMPLEMENTATION_ACTIVE.json').read_text())['run_path'];before=json.loads((old/'BEFORE.json').read_text())
protected_changed=[p for p,h in before['protected_hashes_before'].items() if file_hash(W/p)!=h]
archive_changes=[]
for p,expected in before['original_archive_stats_before'].items():
 st=(W/p).stat()
 if (st.st_size,st.st_mtime_ns)!=(expected['size'],expected['mtime_ns']):archive_changes.append(p)
frozen=json.loads((S/'manifests/YOLO26X_SOURCE.json').read_text());assert file_hash(W/frozen['checkpoint_workspace_relative'])==frozen['sha256']
changes=[];patch=[];baseline={r['path']:r for r in json.loads((R/'BEFORE.json').read_text())}
paths=[p for d in ['src/application_v2','tests'] for p in (S/d).glob('*.py')]
paths += [S/p for p in ['configs/application_v2_first_cohort_v4.yaml','configs/application_v2_first_cohort_v5.yaml','provenance/APPLICATION_V2_DECISIONS_V4.json','scripts/build_first_cohort_evidence.py','scripts/first_cohort_live_route.py','scripts/review_first_cohort_v5.py','scripts/validate_first_cohort_readiness.py']]
snapshot=out/'source_snapshot';snapshot.mkdir()
for p in paths:
 rel=str(p.relative_to(S));h=file_hash(p);oldrow=baseline.get(rel);q=snapshot/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 if oldrow and h==oldrow['sha256']:continue
 original=(R/'before'/rel).read_text() if oldrow else ''
 changes.append({'path':rel,'before_sha256':oldrow['sha256'] if oldrow else None,'after_sha256':h})
 patch.append(''.join(difflib.unified_diff(original.splitlines(True),p.read_text().splitlines(True),fromfile='before/'+rel if oldrow else '/dev/null',tofile=rel)))
(out/'CHANGES.diff').write_text('\n'.join(patch));(out/'SOURCE_CHANGES.json').write_text(json.dumps(changes,indent=2))
value={'status':'PASS' if all(x['exit_code']==0 for x in results) and not protected_changed and not archive_changes else 'FAIL','suite_results':results,'tests':sum(x['tests'] or 0 for x in results),'protected_hashes_checked':len(before['protected_hashes_before']),'protected_changed':protected_changed,'archive_stat_changes':archive_changes,'frozen_YOLO_checkpoint':'PASS','benchmark_guard':guard,'actual_route':'PASS_BOUNDED_TRAIN_ONLY','canonical_V5_packet_dependency_checks':packets,'population_checks':population_checks,'real_scoring_context_accepted':False,'two_user_policies_accepted':True,'scientific_freeze':False,'full_benchmark_started':False,'source_change_manifest':str((out/'SOURCE_CHANGES.json').relative_to(S)),'source_snapshot':str(snapshot.relative_to(S)),'source_revision_sha256':digest({str(p.relative_to(S)):file_hash(p) for p in paths})}
(out/'VALIDATION.json').write_text(json.dumps(value,indent=2));(R/'LATEST_VALIDATION.json').write_text(json.dumps({'path':str((out/'VALIDATION.json').relative_to(S))},indent=2));print(json.dumps({k:value[k] for k in ['status','tests','protected_hashes_checked','protected_changed','actual_route','scientific_freeze','full_benchmark_started']}))
if value['status']!='PASS':raise SystemExit(1)
