"""Run CPU regressions and preservation checks into a fresh revision evidence dir."""
from pathlib import Path
import sys,json,subprocess,datetime,hashlib,re,difflib
S=Path(__file__).resolve().parents[1];W=S.parent;sys.path.insert(0,str(S))
from src.application_v2.artifacts import file_hash,resume_packet
from src.application_v2.policy import load_config
R=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run'];out=R/('validation_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir()
results=[]
for pattern in ['test_application_v2*.py','test_mhpv2_stage0.py','test_official_mhp_compat.py','test_dataset_reassessment.py','test_ccihp_gt.py','test_ccihp_quality.py']:
 command=[sys.executable,'-m','unittest','discover','-s',str(S/'tests'),'-p',pattern]
 done=subprocess.run(command,cwd=S,capture_output=True,text=True,timeout=180);log=done.stdout+done.stderr;(out/(pattern.replace('*','ALL')+'.log')).write_text(log)
 match=re.search(r'Ran (\d+) tests?',log);results.append(dict(pattern=pattern,command=command,exit_code=done.returncode,tests=int(match[1]) if match else None))
old=S/json.loads((S/'provenance/APPLICATION_V2_IMPLEMENTATION_ACTIVE.json').read_text())['run_path'];before=json.loads((old/'BEFORE.json').read_text())
changed=[p for p,h in before['protected_hashes_before'].items() if file_hash(W/p)!=h]
archives=[]
for p,e in before['original_archive_stats_before'].items():
 st=(W/p).stat()
 if (st.st_size,st.st_mtime_ns)!=(e['size'],e['mtime_ns']):archives.append(p)
packets=[]
for base in [old,R/'canonical_smoke']:
 for p in base.rglob('COMMITTED.json'):
  rec=json.loads((p.parent/'record.json').read_text());resume_packet(p.parent,rec['fingerprints']['inference']);packets.append(str(p.parent.relative_to(S)))
configs=[]
for p in [S/'configs/application_v2.yaml',S/'configs/application_v2_handoff_v3.yaml']:
 load_config(p)
 try:load_config(p,benchmark=True)
 except ValueError:configs.append({'path':str(p.relative_to(S)),'benchmark_guard':'PASS_REJECTED'})
 else:raise ValueError('Benchmark guard failed')
sources={str(p.relative_to(S)):file_hash(p) for root in [S/'src/application_v2',S/'tests'] for p in root.glob('*.py')};sources.update({str(p.relative_to(S)):file_hash(p) for p in [S/'configs/application_v2_handoff_v3.yaml',S/'provenance/APPLICATION_V2_DECISIONS_V3.json',S/'taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V2.json']})
patch=[]
for row in json.loads((R/'BEFORE.json').read_text()):
 p=S/row['path'];oldfile=R/'before'/row['path']
 if p.exists() and file_hash(p)!=row['sha256']:
  try:patch.append(''.join(difflib.unified_diff(oldfile.read_text().splitlines(True),p.read_text().splitlines(True),fromfile='before/'+row['path'],tofile=row['path'])))
  except UnicodeError:pass
(out/'CHANGES.diff').write_text('\n'.join(patch))
value={'status':'PASS' if all(r['exit_code']==0 for r in results) and not changed and not archives else 'FAIL','suite_results':results,'tests':sum(r['tests'] or 0 for r in results),'protected_hashes_checked':len(before['protected_hashes_before']),'protected_changed':changed,'archive_stat_changes':archives,'verified_packets':packets,'configs':configs,'source_hashes':sources,'source_revision_sha256':hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest(),'note':'CPU engineering evidence; not acceptance of scientific policies or all production routes'}
(out/'VALIDATION.json').write_text(json.dumps(value,indent=2));(R/'LATEST_VALIDATION.json').write_text(json.dumps({'path':str((out/'VALIDATION.json').relative_to(S))},indent=2));print(json.dumps({k:value[k] for k in ['status','tests','protected_hashes_checked','protected_changed','source_revision_sha256']}))
if value['status']!='PASS':raise SystemExit(1)
