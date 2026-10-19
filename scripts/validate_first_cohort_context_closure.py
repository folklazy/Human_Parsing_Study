"""CPU-only regression and preservation checks for the context registry extension."""
from pathlib import Path
from datetime import datetime, timezone
import difflib
import json
import re
import shutil
import subprocess
import sys

S = Path(__file__).resolve().parents[1]
W = S.parent
sys.path.insert(0, str(S))
from src.application_v2.artifacts import file_hash, resume_packet
from src.application_v2.policy import digest, fingerprints, load_config


def main():
    run = S / json.loads((S / 'provenance/FIRST_COHORT_CONTEXT_CLOSURE_ACTIVE.json').read_text())['run']
    out = run / ('validation_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir()
    suites = []
    for pattern in ['test_application_v2*.py', 'test_mhpv2_stage0.py', 'test_official_mhp_compat.py',
                    'test_dataset_reassessment.py', 'test_ccihp_gt.py', 'test_ccihp_quality.py']:
        command = [sys.executable, '-m', 'unittest', 'discover', '-s', str(S / 'tests'), '-p', pattern]
        done = subprocess.run(command, cwd=S, capture_output=True, text=True, timeout=180)
        text = done.stdout + done.stderr
        log = out / (pattern.replace('*', 'ALL') + '.log')
        log.write_text(text)
        count = re.search(r'Ran (\d+) tests?', text)
        suites.append(dict(command=command, exit_code=done.returncode, tests=int(count[1]) if count else None,
                           log=str(log.relative_to(S))))
    config = load_config(S / 'configs/application_v2_first_cohort_v5.yaml')
    assert config.get('scoring_context') is None and config.get('scoring_contexts') is None
    try:
        load_config(S / 'configs/application_v2_first_cohort_v5.yaml', benchmark=True)
    except ValueError:
        benchmark_guard = 'PASS_REJECTED'
    else:
        raise ValueError('Full benchmark unexpectedly enabled')
    previous = S / json.loads((S / 'provenance/FIRST_COHORT_READINESS_ACTIVE.json').read_text())['run']
    lineage = json.loads((previous / 'V4_TO_V5_LINEAGE.json').read_text())
    packet_checks = []
    for row in lineage['models']:
        expected = fingerprints(config, row['inference_dependencies'])
        record = resume_packet(S / row['canonical_V5_packet'], expected['inference'])
        assert record['fingerprints'] == expected
        packet_checks.append(row['canonical_V5_packet'])
    old = S / json.loads((S / 'provenance/APPLICATION_V2_IMPLEMENTATION_ACTIVE.json').read_text())['run_path']
    baseline = json.loads((old / 'BEFORE.json').read_text())
    protected_changed = [p for p, h in baseline['protected_hashes_before'].items() if file_hash(W / p) != h]
    archive_changes = []
    for name, expected in baseline['original_archive_stats_before'].items():
        stat = (W / name).stat()
        if (stat.st_size, stat.st_mtime_ns) != (expected['size'], expected['mtime_ns']):
            archive_changes.append(name)
    frozen = json.loads((S / 'manifests/YOLO26X_SOURCE.json').read_text())
    yolo_unchanged = file_hash(W / frozen['checkpoint_workspace_relative']) == frozen['sha256']
    before = {row['path']: row for row in json.loads((run / 'BEFORE.json').read_text())}
    paths = [p for directory in ['src/application_v2', 'tests'] for p in (S / directory).glob('*.py')]
    paths.append(Path(__file__).resolve())
    changes, diff = [], []
    snapshot = out / 'source_snapshot'
    for path in paths:
        rel = str(path.relative_to(S))
        copy = snapshot / rel
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copy)
        oldrow = before.get(rel)
        current_hash = file_hash(path)
        if oldrow and current_hash == oldrow['before_sha256']:
            continue
        # Only application tests were part of this continuation's pre-edit snapshot.
        if rel.startswith('tests/') and oldrow is None and not path.name.startswith('test_application_v2'):
            continue
        original = (S / oldrow['archive']).read_text() if oldrow else ''
        changes.append(dict(path=rel, before_sha256=oldrow['before_sha256'] if oldrow else None,
                            after_sha256=current_hash))
        diff.append(''.join(difflib.unified_diff(original.splitlines(True), path.read_text().splitlines(True),
                    fromfile='before/' + rel if oldrow else '/dev/null', tofile=rel)))
    (out / 'SOURCE_CHANGES.json').write_text(json.dumps(changes, indent=2) + '\n')
    (out / 'CHANGES.diff').write_text('\n'.join(diff))
    passed = all(x['exit_code'] == 0 and x['tests'] for x in suites) and not protected_changed and not archive_changes and yolo_unchanged
    result = dict(status='PASS' if passed else 'FAIL', timestamp_utc=datetime.now(timezone.utc).isoformat(),
        suite_results=suites, tests=sum(x['tests'] or 0 for x in suites),
        protected_hashes_checked=len(baseline['protected_hashes_before']), protected_changed=protected_changed,
        original_archive_stat_changes=archive_changes, frozen_YOLO_unchanged=yolo_unchanged,
        benchmark_guard=benchmark_guard, real_scoring_context_accepted=False,
        new_GPU_inference=False, cached_scoring='NOT_IMPLEMENTED_DISABLED',
        source_snapshot=str(snapshot.relative_to(S)), source_revision_sha256=digest({str(p.relative_to(S)): file_hash(p) for p in paths}),
        original_canonical_packet_fingerprints_unchanged=packet_checks, full_benchmark_started=False,
        scientific_freeze=False, fixtures='TWO_SYSTEMS_TWO_IMAGES_SYNTHETIC_TEMP_ACCEPTANCE_ONLY')
    (out / 'VALIDATION.json').write_text(json.dumps(result, indent=2) + '\n')
    (run / 'LATEST_VALIDATION.json').write_text(json.dumps({'path': str((out / 'VALIDATION.json').relative_to(S))}, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['status', 'tests', 'protected_hashes_checked',
                      'protected_changed', 'new_GPU_inference', 'real_scoring_context_accepted']}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
