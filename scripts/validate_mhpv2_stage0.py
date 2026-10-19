"""Finalize explicit MHP Stage 0 evidence; never opens paused PPSS artifacts.

Rehashes the immutable MHP inventory and protected YOLO files; reruns only the
named synthetic test suite. Dataset failures remain blockers, not repaired data.
"""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from collections import Counter, defaultdict
import ast
import csv
import json
import os
import re
import subprocess
import sys
import yaml


STUDY = Path(__file__).resolve().parents[1]
WORKSPACE = STUDY.parent


def digest(path):
    h = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def command(args, cwd=WORKSPACE):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def main():
    output = STUDY / 'provenance/STAGE0_VALIDATION.json'
    if output.exists():
        raise RuntimeError('Completed validation exists; create a new explicit revision, do not overwrite')
    active = load(STUDY / 'provenance/STAGE0_ACTIVE_RUN.json')
    run = STUDY / 'provenance/RUN_MANIFESTS' / active['run_id']
    checks = {}
    manifest = load(STUDY / 'manifests/DATASET_MANIFEST.json')
    dataset = WORKSPACE / manifest['root_workspace_relative']
    inventory_path = STUDY / manifest['inventory']
    assert digest(inventory_path) == manifest['inventory_sha256']
    inventory = [json.loads(line) for line in inventory_path.open()]
    inventory_by_path = {row['path']: row for row in inventory}
    assert len(inventory_by_path) == len(inventory) == manifest['files_hashed'] == 100134
    actual_paths = {str(path.relative_to(dataset)) for path in dataset.rglob('*') if path.is_file()}
    assert actual_paths == set(inventory_by_path), 'Source inventory changed'

    def verify_file(row):
        path = dataset / row['path']
        return path.stat().st_size == row['bytes'] and digest(path) == row['sha256']

    with ThreadPoolExecutor(max_workers=3) as pool:
        assert all(pool.map(verify_file, inventory)), 'Original MHP dataset SHA256 changed'
    checks['all_100134_original_dataset_file_hashes_unchanged'] = 'PASS'
    print('[STAGE0] immutable dataset hash validation: PASS', flush=True)

    gt_path = STUDY / manifest['canonical_gt_index']
    assert digest(gt_path) == manifest['canonical_gt_index_sha256']
    records = [json.loads(line) for line in gt_path.open()]
    splits = defaultdict(set)
    persons = {}
    bad_rgb = []
    content_groups = defaultdict(list)
    for record in records:
        split, image_id = record['split'], record['image_id']
        assert image_id not in splits[split]
        splits[split].add(image_id)
        assert inventory_by_path[record['image_path']]['sha256'] == record['image_sha256']
        if record.get('decoded_rgb_sha256'):
            content_groups[record['decoded_rgb_sha256']].append((split, image_id))
        else:
            bad_rgb.append((split, image_id))
        ids = [person['person_file_id'] for person in record['persons']]
        assert ids == list(range(1, len(ids) + 1))
        for person in record['persons']:
            key = person['canonical_person_id']
            assert key not in persons and key == f'{image_id}:parsing:{person["person_file_id"]}'
            assert inventory_by_path[person['annotation_path']]['sha256'] == person['source_sha256']
            assert set(person['native_ids']) <= set(range(59)) and person['foreground_area'] > 0
            assert person['lossless_roundtrip'] is True and person['pose_person_key'] is None
            persons[key] = person
    assert {key: len(value) for key, value in splits.items()} == {'train': 15403, 'val': 5000, 'test': 5000}
    assert len(persons) == 54316 and len(records) == 25403
    assert set(bad_rgb) == {('train','1396'),('train','18613'),('train','24328'),('val','17844')}
    for a, b in [('train','val'),('train','test'),('val','test')]:
        assert splits[a].isdisjoint(splits[b])
    for split, filename in [('train','train.txt'),('val','val.txt'),('test','test_all.txt')]:
        ids = (dataset / 'list' / filename).read_text().split()
        assert len(ids) == len(set(ids)) and set(ids) == splits[split]
    for filename, size in [('test_inter_top10.txt',500),('test_inter_top20.txt',1000)]:
        ids = (dataset / 'list' / filename).read_text().split()
        assert len(ids) == len(set(ids)) == size and set(ids) <= splits['test']
    checks['native_instance_index_source_hashes_counts_and_fidelity_records'] = 'PASS'
    checks['official_split_identity_and_auxiliary_test_lists'] = 'PASS'
    checks['required_rgb_readability'] = 'BLOCKED_FOUR_VERIFIED_FAILURES'

    duplicate_groups = [group for group in content_groups.values() if len(group) > 1]
    train_val = [group for group in duplicate_groups if {'train','val'} <= {split for split,_ in group}]
    overlapping_val = {i for group in train_val for split,i in group if split == 'val'}
    leakage = load(STUDY / 'manifests/LEAKAGE_AUDIT.json')
    assert len(duplicate_groups) == leakage['all_exact_duplicate_groups'] == 2267
    assert len(train_val) == leakage['train_validation_groups'] == 628
    assert overlapping_val == set(leakage['validation_ids_with_exact_train_overlap']) and len(overlapping_val) == 652
    checks['exact_content_leakage_bookkeeping'] = 'PASS_FINDING_REQUIRES_REVIEW'

    manifest_hash = digest(STUDY / 'manifests/DATASET_MANIFEST.json')
    development = load(STUDY / 'manifests/DEVELOPMENT_SET.json')
    final = load(STUDY / 'manifests/FINAL_VALIDATION_SET.json')
    assert set(development['image_ids']) <= splits['train']
    assert set(development['smoke_image_ids']) <= set(development['image_ids'])
    assert len(development['smoke_image_ids']) == 3 and development['execution_authorized_now'] is False
    assert set(final['image_ids']) == splits['val'] and len(final['image_ids']) == 5000
    for name, count in [('TIMING_PERSON_SET.json',100),('TIMING_FRAME_SET.json',50)]:
        timing = load(STUDY / 'manifests' / name)
        assert len(timing['samples']) == count and timing['benchmark_authorized'] is False
        assert timing['dataset_manifest_sha256'] == manifest_hash
        assert all(sample['image_id'] in splits['train'] for sample in timing['samples'])
        if name.startswith('TIMING_PERSON'):
            assert all(sample['person_id'] in persons for sample in timing['samples'])
    assert development['dataset_manifest_sha256'] == final['dataset_manifest_sha256'] == manifest_hash
    checks['train_only_draft_workloads_and_original_validation_reservation'] = 'PASS'

    with (STUDY / 'metrics/DATASET_PERSON_STATISTICS.csv').open() as stream:
        stats = list(csv.DictReader(stream))
    assert len(stats) == len(persons) and {row['person_id'] for row in stats} == set(persons)
    assert Counter(row['split'] for row in stats) == {'train':41056,'val':13260}
    with (STUDY / 'metrics/DATASET_NATIVE_CLASS_SUPPORT.csv').open() as stream:
        support = list(csv.DictReader(stream))
    assert {int(row['native_id']) for row in support} == set(range(59))
    checks['dataset_statistics_population'] = 'PASS'

    allowed = {'EXACT','SAFE_MERGE','COARSE_ONLY','AMBIGUOUS','UNSUPPORTED','UNKNOWN'}
    with (STUDY / 'taxonomy/TAXONOMY_REPRESENTABILITY_MATRIX.csv').open() as stream:
        matrix = list(csv.DictReader(stream))
    assert len(matrix) == len({(row['mhpv2_id'],row['model']) for row in matrix}) == 472
    assert len({row['model'] for row in matrix}) == 8
    assert all(row['representability'] in allowed and row['mapping_frozen'] == 'False' for row in matrix)
    for name in ['COMMON_HP_CORE_DRAFT.yaml','COMMON_HP_EXTENDED_DRAFT.yaml']:
        draft = yaml.safe_load((STUDY / 'taxonomy' / name).read_text())
        assert draft['mapping_frozen'] is False and draft['evaluation_authorized'] is False
    for name in ['FASHN','SCHP_LIP','D2FP_LIP','D2FP_CIHP','M2FP_MHPV2','CPI_MHPV2']:
        native = yaml.safe_load((STUDY / 'taxonomy/native' / f'{name}.yaml').read_text())
        assert digest(WORKSPACE / native['source_workspace_relative']) == native['source_sha256']
    checks['source_native_taxonomy_and_draft_matrix'] = 'PASS_DRAFT_NOT_FROZEN'

    checkpoints = load(STUDY / 'provenance/CHECKPOINT_MANIFEST.json')
    assert all(row['loaded'] is False and row['sha256'] is None for row in checkpoints.values())
    with (STUDY / 'provenance/MODEL_REGISTRY.csv').open() as stream:
        registry = list(csv.DictReader(stream))
    assert len(registry) == len({row['model_id'] for row in registry}) == 11
    assert all(row['gpu_model_inference'] == 'False' and row['checkpoint_downloaded'] == 'False' for row in registry)
    for row in load(STUDY / 'provenance/SOURCE_REVISIONS.json').values():
        if 'local_path' in row:
            source = WORKSPACE / row['local_path']
            assert command(['git','rev-parse','HEAD'],source) == row['commit']
            assert command(['git','status','--porcelain'],source) == row['status']
            for name, value in row['relevant_hashes'].items():
                assert digest(source / name) == value
    env = load(run / 'FASHN_ENVIRONMENT_CHECK.json')
    assert env['model_smoke_pass'] is False and env['checkpoint_loaded'] is False
    assert env['synthetic_fp32_matrix_operation'] == 'PASS'
    with (STUDY / 'provenance/ENVIRONMENT_MATRIX.csv').open() as stream:
        for row in csv.DictReader(stream):
            if row['status'] == 'TESTED':
                assert digest(STUDY / 'env_specs' / f'{row["environment_id"]}.txt') == row['package_freeze_sha256']
    checks['source_checkpoint_environment_status_not_overstated'] = 'PASS_NO_MODEL_SMOKES'

    test_environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    test = subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_mhpv2_stage0.py','-v'],
                          cwd=STUDY,env=test_environment,text=True,capture_output=True)
    (run / 'synthetic_tests_final.log').write_text(test.stdout + test.stderr)
    assert test.returncode == 0 and 'Ran 25 tests' in test.stderr
    checks['study_specific_synthetic_evaluator_and_contract_tests'] = 'PASS_25_TESTS'
    official = load(STUDY / 'provenance/OFFICIAL_METRIC_FIXTURES.json')
    assert len(official['fixtures']) == 5 and all(row['status'] == 'PASS' for row in official['fixtures'])
    assert digest(WORKSPACE / official['source_file']) == official['source_sha256']
    edge = load(run / 'OFFICIAL_METRIC_EDGE_CASES.json')
    assert edge['empty_prediction_case'] == 'FAIL_UPSTREAM_EDGE_CASE'
    checks['official_function_limited_fixtures'] = 'PASS_5_FIXTURES'
    checks['full_native_official_metric_parity'] = 'BLOCKED_UPSTREAM_EMPTY_PREDICTION_EDGE_AND_UNTESTED_VOL'

    visuals = load(STUDY / 'provenance/MHPV2_GT_VISUAL_VALIDATION.json')
    assert len(visuals['cases']) == 8
    for case in visuals['cases']:
        assert case['split'] == 'train' and case['image_id'] in splits['train']
        assert digest(STUDY / case['image']) == case['sha256']
        assert case['native_vs_canonical_pixels_identical'] is True
    checks['eight_train_gt_visuals_hashes_and_review_records'] = 'PASS_WITH_OWNERSHIP_WARNING'

    before = load(run / 'PRESERVATION_BEFORE.json')
    after = {'repos':{},'yolo26x_sha256':digest(WORKSPACE / 'models/yolo26x-seg.pt'),
             'yolo_environment_files':{},'ppss_read_or_modified':False}
    for name, source in before['repos'].items():
        repo = WORKSPACE / name
        current = {'head':command(['git','rev-parse','HEAD'],repo), 'branch':command(['git','branch','--show-current'],repo),
                   'status':command(['git','status','--porcelain'],repo),'remotes':command(['git','remote','-v'],repo),
                   'files':{name:digest(repo/name) for name in source['files']}}
        assert current == source, f'Protected YOLO repository changed: {name}'
        after['repos'][name] = current
    after['yolo_environment_files'] = {name:digest(WORKSPACE/name) for name in before['yolo_environment_files']}
    assert after == before, 'Protected checkpoint/environment metadata changed'
    atomic_json(run / 'PRESERVATION_AFTER.json', after)
    checks['protected_yolo_files_checkpoint_environment_metadata_and_git_status'] = 'PASS'

    state = load(STUDY / 'STUDY_STATE.json')
    for key, value in load(run / 'SHARED_STATE_PAUSED_NODES_BEFORE.json').items():
        assert state[key] == value
    assert state['benchmark_status'] == 'NOT_STARTED' and state['stage0_overall_status'] == 'BLOCKED'
    checks['previous_shared_state_nodes_preserved'] = 'PASS'
    python_paths = [Path(__file__),STUDY/'tests/test_mhpv2_stage0.py']
    for directory in ['src/data','src/contracts','src/evaluation','src/adapters']:
        python_paths.extend((STUDY/directory).glob('*.py'))
    python_paths.extend(STUDY/'scripts'/name for name in ['audit_mhpv2.py','complete_mhpv2_audit.py','visualize_mhpv2_gt.py',
                         'audit_model_sources.py','build_taxonomy_drafts.py','smoke_fashn.py','test_official_metric_fixtures.py'])
    for path in python_paths:
        ast.parse(path.read_text(),filename=str(path))

    docs = [STUDY/name for name in ['README.md','STUDY_STANDARD.md','EXPERIMENT_PROTOCOL_DRAFT.md','DATA_SCHEMA.md','REFERENCES.md','REPRODUCIBILITY.md',
            'reports/MHPV2_DATASET_AUDIT.md','reports/MODEL_COMPATIBILITY_REPORT.md','reports/TAXONOMY_AUDIT.md',
            'reports/PROTOCOL_REVIEW.md','reports/STAGE0_FEASIBILITY_REPORT.md']]
    for path in docs:
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
            if target.startswith(('http:','https:','#')) or 'PPSS' in target.upper():
                continue
            resolved = path.parent / target.split('#')[0]
            if resolved.resolve() == output.resolve():
                continue
            assert resolved.exists(), f'Broken active MHP link {path.name}: {target}'
    checks['new_mhp_document_links_and_python_syntax'] = 'PASS'
    for row in load(run / 'FINAL_DOCUMENT_REVISION.json')['records']:
        assert digest(WORKSPACE/row['original_workspace_relative']) == row['sha256_after']
        assert digest(STUDY/row['archived_study_relative']) == row['sha256_before']
    checks['shared_document_archives_before_after_hashes'] = 'PASS'

    scope = {'ppss_dataset_reports_manifests_results_read_or_modified':False,'original_mhp_dataset_modified':False,
             'previous_yolo_artifacts_modified':False,'yolo_environment_modified':False,'frozen_yolo_weights_modified':False,
             'full_benchmark_started':False,'training_started':False,'hybrid_fusion_started':False,'color_study_started':False,
             'parser_model_inference_started':False,'stage1_started':False,'remote_repository_created_or_pushed':False}
    result = {'schema_version':'1.0','run_id':active['run_id'],'overall_status':'BLOCKED',
              'audit_execution_completed':True,'stage1_ready':False,'next_action':'WAIT_FOR_USER_APPROVAL',
              'gates':{'A':'PASS','B':'BLOCKED','C':'BLOCKED_DEFERRED','D':'PASS_SYNTHETIC_ONLY_DRAFT',
                       'E':'DRAFT','F':'PARTIAL_NATIVE_PARITY_BLOCKED','G':'DRAFT_FOR_REVIEW','H':'PASS'},
              'checks':checks,'scope':scope,'actual_parser_smoke_models':[],
              'dataset_manifest_sha256':manifest_hash,'inventory_sha256':manifest['inventory_sha256'],
              'protected_yolo_files_verified':sum(len(row['files']) for row in before['repos'].values()),
              'git':{'workspace':'NOT_A_GIT_REPOSITORY','study':'NOT_A_GIT_REPOSITORY','six_yolo_statuses_unchanged':True,
                     'commit_created':False,'push_performed':False},'validated_utc':datetime.now(timezone.utc).isoformat()}
    atomic_json(output,result)
    evidence = docs + python_paths + [STUDY/'configs/study.yaml',STUDY/'configs/dataset.yaml',STUDY/'STUDY_STATE.json',output]
    evidence.extend(STUDY/name for name in ['provenance/MODEL_REGISTRY.csv','provenance/CHECKPOINT_MANIFEST.json',
                    'provenance/ENVIRONMENT_MATRIX.csv','provenance/DATASET_INTEGRITY.json','taxonomy/TAXONOMY_REPRESENTABILITY_MATRIX.csv',
                    'taxonomy/COMMON_HP_CORE_DRAFT.yaml','taxonomy/COMMON_HP_EXTENDED_DRAFT.yaml'])
    atomic_json(run / 'FINAL_RUN_MANIFEST.json',{'run_id':active['run_id'],'start_utc':active['started_utc'],
        'end_utc':result['validated_utc'],'study_git_commit':None,'study_git_status':'NOT_INITIALIZED',
        'status':'BLOCKED','config_sha256':digest(STUDY/'configs/study.yaml'),'dataset_manifest_sha256':manifest_hash,
        'input_scope':'Exhaustive immutable MHP-v2 audit; 8 fixed train GT visual cases; synthetic tests only',
        'model_inputs':[],'checkpoint_inference_runs':[],'precision':'FP32_SYNTHETIC_GPU_ONLY',
        'hardware_reference':'HARDWARE.json','environment_reference':'../../ENVIRONMENT_MATRIX.csv',
        'artifacts':{str(path.relative_to(STUDY)):digest(path) for path in evidence},
        'safety':scope,'failure_diagnostics':{'rgb_failures':bad_rgb,'native_metric_empty_prediction':edge['error']}})
    print('[STAGE0] contracts/evaluator synthetic tests: PASS (25)',flush=True)
    print('[STAGE0] protected YOLO artifacts: UNCHANGED',flush=True)
    print('[STAGE0] final status: BLOCKED — WAIT FOR USER APPROVAL',flush=True)


if __name__ == '__main__':
    main()
