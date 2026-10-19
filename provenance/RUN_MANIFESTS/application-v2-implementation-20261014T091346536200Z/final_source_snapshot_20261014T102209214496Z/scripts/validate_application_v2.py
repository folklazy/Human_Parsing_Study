"""Finite implementation validation. This entry point never loads models."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import json
import subprocess
import sys

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))
from src.application_v2.policy import load_config
from src.application_v2.artifacts import file_hash, resume_packet


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--all', action='store_true'); parser.parse_args()
    config = load_config(STUDY / 'configs/application_v2.yaml')
    active = json.loads((STUDY / 'provenance/APPLICATION_V2_IMPLEMENTATION_ACTIVE.json').read_text())
    run = STUDY / active['run_path']; results = []
    patterns = ['test_application_v2.py', 'test_mhpv2_stage0.py', 'test_official_mhp_compat.py',
                'test_dataset_reassessment.py', 'test_ccihp_gt.py', 'test_ccihp_quality.py']
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    logs = run / ('cpu_validation_' + timestamp); logs.mkdir()
    for pattern in patterns:
        command = [sys.executable, '-m', 'unittest', 'discover', '-s', str(STUDY / 'tests'), '-p', pattern, '-q']
        completed = subprocess.run(command, cwd=STUDY, capture_output=True, text=True, timeout=120)
        (logs / (pattern + '.log')).write_text(completed.stdout + completed.stderr)
        results.append({'suite': pattern, 'exit_code': completed.returncode,
                        'log': str((logs / (pattern + '.log')).relative_to(STUDY))})
        if completed.returncode: raise RuntimeError(f'Regression failed: {pattern}: {completed.stderr}')
    packet_count = 0
    for marker in run.rglob('COMMITTED.json'):
        packet = marker.parent
        record = json.loads((packet / 'record.json').read_text())
        resume_packet(packet, record['fingerprints']['inference'])
        packet_count += 1
    for folder in ['gt_sidecars', 'mhp_native_sidecars']:
        manifest = json.loads((run / folder / 'MANIFEST.json').read_text())
        for population in manifest['populations'].values():
            source = STUDY / population['sidecar']
            if file_hash(source) != population['sidecar_sha256']: raise ValueError('GT sidecar changed')
            with source.open() as stream:
                count = sum(1 for _ in stream)
            if count != population['G_native']: raise ValueError('Native person denominator changed')
    before = json.loads((run / 'BEFORE.json').read_text())
    for path, expected in before['protected_hashes_before'].items():
        if file_hash(STUDY.parent / path) != expected: raise ValueError(f'Protected artifact changed: {path}')
    for path, expected in before['original_archive_stats_before'].items():
        current = (STUDY.parent / path).stat()
        if (current.st_size, current.st_mtime_ns) != (expected['size'], expected['mtime_ns']):
            raise ValueError('Original dataset archive changed')
    try:
        load_config(STUDY / 'configs/application_v2.yaml', benchmark=True)
    except ValueError:
        blocked = True
    else:
        raise ValueError('Unexpected benchmark authorization')
    bounded = sorted(run.glob('bounded_train_*/VALIDATION.json'))
    result = {'status': 'PASS_IMPLEMENTATION_AND_BOUNDED_TRAIN_WITH_DRAFT_SCIENTIFIC_POLICIES',
              'validated_at_utc': datetime.now(timezone.utc).isoformat(), 'regression_suites': results,
              'packet_integrity_pass': packet_count, 'protected_hashes_unchanged': len(before['protected_hashes_before']),
              'GT_sidecars_integrity': 'PASS', 'config_accepted_decision_consistency': 'PASS',
              'benchmark_execution_guard': 'PASS_BLOCKED_AS_REQUIRED', 'full_benchmark_started': False,
              'new_bounded_TRAIN_inference': bool(bounded), 'parser_training': False,
              'validation_inference': False, 'PPSS_activity': False, 'canonical_measured_values_changed': False,
              'protocol_frozen': False, 'cohort_mappings_accepted': False,
              'bounded_train_evidence': [str(p.relative_to(STUDY)) for p in bounded],
              'not_yet_validated': ['joint_resident_pipeline_timing_and_memory', 'live_CPI_T3b_parser_worker',
                                   'all_20_variant_application_routing', 'accepted_common_taxonomy_and_population_freeze']}
    (logs / 'VALIDATION.json').write_text(json.dumps(result, indent=2) + '\n')
    (run / 'FINAL_VALIDATION_POINTER.json').write_text(json.dumps({'validation': str((logs / 'VALIDATION.json').relative_to(STUDY))}, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'suites': len(results), 'packets': packet_count,
                      'protected_hashes_unchanged': result['protected_hashes_unchanged'], 'full_benchmark_started': False}))


if __name__ == '__main__': main()
