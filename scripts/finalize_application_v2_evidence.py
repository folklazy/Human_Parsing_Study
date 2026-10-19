"""Seal source/config/document evidence; never import or execute a model."""
from pathlib import Path
from datetime import datetime, timezone
import json
import re
import shutil
import subprocess
import sys

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))
from src.application_v2.artifacts import file_hash
from src.application_v2.policy import load_config


def main():
    load_config(STUDY / 'configs/application_v2.yaml')
    active = json.loads((STUDY / 'provenance/APPLICATION_V2_IMPLEMENTATION_ACTIVE.json').read_text())
    run = STUDY / active['run_path']; before = json.loads((run / 'BEFORE.json').read_text())
    pointer = json.loads((run / 'FINAL_VALIDATION_POINTER.json').read_text())
    validation = json.loads((STUDY / pointer['validation']).read_text())
    for path, expected in before['protected_hashes_before'].items():
        if file_hash(STUDY.parent / path) != expected: raise ValueError('Protected source/data changed')
    tests = []
    for suite in validation['regression_suites']:
        log = STUDY / suite['log']; text = log.read_text(); count = re.search(r'Ran (\d+) tests?', text)
        if suite['exit_code'] or not count or '\nOK\n' not in text: raise ValueError('Incomplete test evidence')
        tests.append({**suite, 'tests_passed': int(count[1]), 'log_sha256': file_hash(log)})
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    snapshot = run / ('final_source_snapshot_' + timestamp); snapshot.mkdir()
    sources = sorted((STUDY / 'src/application_v2').glob('*.py'))
    sources += [STUDY / 'tests/test_application_v2.py', STUDY / 'configs/application_v2.yaml']
    sources += sorted((STUDY / 'provenance').glob('APPLICATION_V2_DECISIONS_*.json'))
    sources += sorted((STUDY / 'taxonomy').glob('APPLICATION_*.json'))
    sources += [STUDY / 'scripts' / name for name in ['build_application_v2_sidecars.py',
                'build_mhp_application_sidecars.py', 'replay_application_v2_train.py',
                'bounded_train_application_v2.py', 'validate_application_v2.py',
                'audit_application_v2_resources.py', 'finalize_application_v2_evidence.py']]
    rows = []
    for path in sources:
        relative = path.relative_to(STUDY); target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, target)
        rows.append({'source': str(relative), 'snapshot': str(target.relative_to(STUDY)), 'sha256': file_hash(target)})
    archived = STUDY / before['archive_path']; revisions = []
    for name in ['README.md', 'DATA_SCHEMA.md', 'STUDY_STATE.json']:
        revisions.append({'original': name, 'archived': str((archived / name).relative_to(STUDY)),
                          'before_sha256': file_hash(archived / name), 'after_sha256': file_hash(STUDY / name),
                          'reason': 'Add current executable application contracts/evidence; preserve historical Stage 0 records'})
    state = json.loads((STUDY / 'STUDY_STATE.json').read_text())
    old = json.loads((archived / 'STUDY_STATE.json').read_text())
    if any(old[k] != state.get(k) for k in old if k.startswith('ppss')):
        raise ValueError('Historical paused PPSS state changed')
    if state['benchmark_status'] != 'NOT_STARTED': raise ValueError('Benchmark status changed')
    mhp = json.loads((run / 'mhp_native_sidecars/MANIFEST.json').read_text())
    repeated = json.loads((run / 'mhp_native_reproduction_v1/MANIFEST.json').read_text())
    if any(p['sidecar_sha256'] != repeated['populations'][key]['sidecar_sha256'] for key, p in mhp['populations'].items()):
        raise ValueError('MHP native-sidecar reproduction differs')
    resources_path = run / 'EXISTING_PILOT_RESOURCE_REFERENCES.json'
    resources = json.loads(resources_path.read_text())
    for row in resources['variants']:
        if file_hash(STUDY.parent / row['run_manifest_workspace_relative']) != row['run_manifest_sha256']:
            raise ValueError('Pilot resource evidence changed')
    git = {}
    for name, path in [('workspace', STUDY.parent), ('study', STUDY)]:
        result = subprocess.run(['git', 'status', '--short'], cwd=path, text=True, capture_output=True)
        git[name] = {'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    result = {'status': validation['status'], 'sealed_at_utc': datetime.now(timezone.utc).isoformat(),
              'source_snapshots': rows, 'document_revisions': revisions, 'tests': tests,
              'tests_passed': sum(row['tests_passed'] for row in tests), 'validation': pointer['validation'],
              'validation_sha256': file_hash(STUDY / pointer['validation']),
              'report': 'reports/APPLICATION_V2_IMPLEMENTATION_TH.md',
              'report_sha256': file_hash(STUDY / 'reports/APPLICATION_V2_IMPLEMENTATION_TH.md'),
              'protected_hashes_unchanged': len(before['protected_hashes_before']),
              'MHP_native_sidecar_byte_reproduction': 'PASS', 'paused_PPSS_state_preserved': True,
              'existing_pilot_resource_reference': str(resources_path.relative_to(STUDY)),
              'existing_pilot_resource_reference_sha256': file_hash(resources_path),
              'new_bounded_TRAIN_inference': True, 'full_benchmark_started': False,
              'validation_inference': False, 'training_started': False,
              'new_downloads_or_installs': False, 'canonical_YOLO_measured_results_changed': False,
              'original_dataset_modified': False, 'protocol_frozen': False, 'joint_resident_resources_measured': False,
              'git': git, 'commit_or_push': False}
    evidence = snapshot / 'FINAL_EVIDENCE.json'
    evidence.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    pointer = {'evidence': str(evidence.relative_to(STUDY)), 'evidence_sha256': file_hash(evidence),
               'status': result['status'], 'tests_passed': result['tests_passed']}
    (STUDY / 'provenance/APPLICATION_V2_IMPLEMENTATION_FINAL.json').write_text(json.dumps(pointer, indent=2) + '\n')
    print(json.dumps(pointer))


if __name__ == '__main__': main()
