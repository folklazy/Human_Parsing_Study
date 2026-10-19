"""Read-only checks of terminal benchmark exports; never load or run a model."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import csv
import json
import re
import subprocess
import sys

STUDY = Path(__file__).resolve().parents[1]
WORKSPACE = STUDY.parent
sys.path.insert(0, str(STUDY))
from src.application_v2.artifacts import file_hash
from src.application_v2.policy import digest, load_config


def read(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    run = STUDY / read(STUDY / 'provenance/FIRST_COHORT_BENCHMARK_ACTIVE.json')['run']
    final = read(run / 'FINAL_BENCHMARK_VALIDATION.json')
    output = run / 'execution_restored_detector_v1'
    freeze = read(run / 'RESTORED_PROFILE_FREEZE.json')
    for key in ['config', 'decision']:
        assert file_hash(STUDY / freeze[key]) == freeze[key + '_sha256'], key
    cfg = load_config(STUDY / freeze['config'], benchmark=True)
    assert read(output / 'BENCHMARK_EXECUTION.json')['config_sha256'] == digest(cfg)
    for path, expected in cfg['validation_launch']['code_hashes'].items():
        assert file_hash(STUDY / path) == expected, path
    roster = cfg['first_cohort']['models']
    assert roster == ['CPI_R50_CIHP', 'CPI_ConvNeXtB_CIHP']
    packages = (STUDY / cfg['validation_context_packages']['manifest']).parent
    images = lines(packages / 'IMAGE_BINDINGS.jsonl')
    ids = [row['image_id'] for row in images]
    assert len(ids) == len(set(ids)) == 5000
    populations = {'main': [r for r in images if r['main']], 'reference': images}
    assert len(populations['main']) == 4961
    metrics = STUDY / 'metrics' / run.name
    for name, expected in final['metrics'].items():
        assert file_hash(metrics / name) == expected, name
    with (metrics / 'QUALITY_RESULTS.csv').open(newline='') as stream:
        quality = list(csv.DictReader(stream))
    assert len(quality) == 8
    keys = [(r['population'], r['matching_view'], r['system_id']) for r in quality]
    assert len(set(keys)) == 8
    checked_reports = []
    for role, members in populations.items():
        member_ids = {r['image_id'] for r in members}
        expected_population = dict(frames=len(members), G_loc=sum(r['G_loc'] for r in members),
                                   G_sem=sum(r['G_sem'] for r in members))
        for view, threshold in [('primary', .50), ('secondary', .75)]:
            source = output / (role.upper() + '_' + view.upper() + '_REPORT.json')
            report = read(source)
            frames = lines(output / (view.upper() + '_FRAME_SCORES.jsonl'))
            assert frames == read(output / (view.upper() + '_FRAME_SCORES.json'))
            assert len(frames) == 10000
            assert len({(r['system_id'], r['image_id']) for r in frames}) == 10000
            assert report['GT_matching_threshold'] == threshold
            assert {r['system_id'] for r in report['systems']} == set(roster)
            for system in report['systems']:
                model = system['system_id']
                row = next(r for r in quality if (r['population'], r['matching_view'], r['system_id']) == (role, view, model))
                counts = Counter(r['execution_status'] for r in frames if r['system_id'] == model and r['image_id'] in member_ids)
                assert sum(counts.values()) == len(members)
                for name, value in expected_population.items():
                    assert system['population'][name] == int(row[name]) == value
                for name, status in [('complete', 'COMPLETE'), ('failed', 'FAILED'), ('invalid', 'INVALID')]:
                    assert int(row['frames_' + name]) == counts[status]
                assert sum(int(row['frames_' + k]) for k in ['complete', 'failed', 'invalid', 'not_attempted']) == len(members)
                assert row['status'] == system['status']
                assert row['main_score_eligible'] == str(system['main_score_eligible'])
                values = system['main_metrics']
                for name in ['Q_person_sem_GT', 'TP', 'FP', 'FN', 'localization_recall', 'localization_precision']:
                    if not system['main_score_eligible']:
                        assert values is None and row[name] == '', (role, model, name)
                    else:
                        assert float(row[name]) == values[name]
            checked_reports.append(dict(path=str(source.relative_to(STUDY)), sha256=file_hash(source)))
    with (metrics / 'FAILURES.csv').open(newline='') as stream:
        failures = list(csv.DictReader(stream))
    components = cfg['validation_launch']['detector_infrastructure_restoration']['native_components']
    directories = {'YOLO26X_FROZEN': output / 'YOLO26X_FROZEN',
                   **{model: (STUDY / spec['manifest']).parent for model, spec in components.items()}}
    expected_failures = set()
    component_counts = {}
    for model, directory in directories.items():
        ledger = lines(directory / 'FRAMES.jsonl')
        assert [r['image_id'] for r in ledger] == ids
        component_counts[model] = dict(Counter(r['status'] for r in ledger))
        expected_failures.update((model, r['image_id'], r['status']) for r in ledger if r['status'] != 'COMPLETE')
    assert {(r['component'], r['image_id'], r['status']) for r in failures} == expected_failures
    assert len(failures) == len(expected_failures)
    assert all(int(r['retries']) == 0 for r in failures)
    for spec in components.values():
        for key in ['manifest', 'ledger']:
            assert file_hash(STUDY / spec[key]) == spec[key + '_sha256']
    baseline_dir = STUDY / 'provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z'
    baseline = read(baseline_dir / 'ORIGINAL_126_BASELINE.json')
    assert all(file_hash(WORKSPACE / p) == h for p, h in baseline['protected_hashes_before'].items())
    assert all(((WORKSPACE / p).stat().st_size, (WORKSPACE / p).stat().st_mtime_ns) == (v['size'], v['mtime_ns'])
               for p, v in baseline['original_archive_stats_before'].items())
    git_results = []
    for item in read(baseline_dir / 'GIT_STATUS_AFTER.json'):
        if not item['is_repository']:
            continue
        process = subprocess.run(['git', 'status', '--porcelain'], cwd=WORKSPACE / item['path'],
                                 capture_output=True, text=True, check=True)
        assert process.stdout == item['status'], item['path']
        git_results.append(dict(path=item['path'], status_unchanged=True))
    index = read(STUDY / 'provenance/CURRENT_STUDY_ARTIFACTS.json')
    report_path = STUDY / index['benchmark_report']
    broken = []
    for document in [report_path, STUDY / 'README.md', STUDY / 'reports/STAGE0_NEXT_ACTIONS.md']:
        for target in re.findall(r'\]\(([^\s)]+)\)', document.read_text()):
            if target.startswith(('https:', 'http:', 'mailto:', '#')):
                continue
            if not (document.parent / target.split('#')[0]).exists():
                broken.append(dict(document=str(document.relative_to(STUDY)), target=target))
    assert not broken, broken
    assert read(STUDY / 'STUDY_STATE.json')['benchmark_status'] == final['status'] == index['benchmark_status']
    result = dict(status='PASS', timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  verifier_sha256=file_hash(Path(__file__)), scope='Export/binding/provenance checks, not successful scientific completion',
                  benchmark_status=final['status'], quality_rows=8, populations={k: len(v) for k, v in populations.items()},
                  strict_complete_null_metrics_verified=True, source_reports=checked_reports,
                  components=component_counts, retained_failures=len(failures), retries=0,
                  protected_files_unchanged=len(baseline['protected_hashes_before']),
                  source_archive_stats_unchanged=True, existing_repository_status=git_results, active_document_links='PASS',
                  inference_performed_by_verifier=False)
    destination = run / 'POST_EXPORT_VERIFICATION.json'
    with destination.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
