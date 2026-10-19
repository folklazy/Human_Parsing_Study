"""Validate Decision 5A records without dataset evaluation, GPU or model imports."""
from pathlib import Path
import csv
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


active = json.loads((ROOT / 'provenance/LICENSE_REASSESSMENT_ACTIVE_RUN.json').read_text())
run = ROOT / active['run_path']
prior = ROOT / active['prior_review_run']
before = json.loads((prior / 'BEFORE.json').read_text())
revisions = json.loads((ROOT / 'provenance/LICENSE_REASSESSMENT_DOCUMENT_REVISIONS_V1.json').read_text())
scope = yaml.safe_load((ROOT / 'configs/research_scope.yaml').read_text())
state = json.loads((ROOT / 'STUDY_STATE.json').read_text())
checks = {}
checks['scope_decision'] = scope['decision_id'] == '5A' and state['research_scope']['decision'] == '5A'
checks['no_automatic_authorization'] = all(scope[k] is False for k in [
    'academic_status_overrides_explicit_restrictions', 'fashn_checkpoint_download_authorized',
    'fashn_checkpoint_inference_authorized', 'heavyweight_dependency_install_authorized',
    'full_benchmark_authorized', 'stage1_authorized', 'training_authorized', 'hybrid_authorized'])
checks['commercial_scope_excluded'] = (scope['company_rd'] is False and scope['commercial_product_development'] is False
                                      and scope['commercial_deployment'] == 'OUT_OF_SCOPE_SEPARATE_FUTURE_LICENSE_REVIEW')
checks['no_cctv_execution'] = scope['company_cctv']['inference_authorized_now'] is False
checks['benchmark_not_started'] = state['benchmark_status'] == 'NOT_STARTED' and state['stage0_overall_status'] == 'BLOCKED'

archive_records = revisions['documents']
archives_ok = True
modified_relative = set()
for item in archive_records:
    original = WORKSPACE / item['original_workspace_relative'] if 'original_workspace_relative' in item else ROOT / item['original_relative']
    if 'original_relative' in item:
        modified_relative.add(item['original_relative'])
    archives_ok &= sha(ROOT / item['archived_relative']) == item['sha256_before'] and sha(original) == item['sha256_after']
checks['archives_and_before_after_hashes'] = bool(archives_ok)
protected = {p: h for p, h in before['hashes_before'].items() if p not in modified_relative}
checks['original_registries_checkpoint_dataset_evidence_unchanged'] = all(sha(ROOT / p) == h for p, h in protected.items())

state_archive = next(item for item in archive_records if item.get('original_relative') == 'STUDY_STATE.json')
old_state = json.loads((ROOT / state_archive['archived_relative']).read_text())
checks['paused_state_nodes_preserved_without_dataset_access'] = all(
    value == state[key] for key, value in old_state.items() if key.startswith('ppss'))
checks['scientific_state_preserved'] = all(old_state[k] == state[k] for k in old_state
                                         if k not in ['last_updated_utc', 'research_scope', 'license_reassessment'])

registry = list(csv.DictReader((ROOT / 'provenance/MODEL_VARIANT_REGISTRY_V3.csv').open()))
prior_registry = list(csv.DictReader((ROOT / 'provenance/MODEL_VARIANT_REGISTRY_V2.csv').open()))
checks['registry_17_variants_preserved'] = {r['model_id'] for r in registry} == {r['model_id'] for r in prior_registry} and len(registry) == 17
checks['zero_checkpoint_inference_and_downloads'] = all(
    row[k] == 'False' for row in registry for k in ['checkpoint_downloaded', 'model_loaded', 'checkpoint_inference_passed', 'execution_authorized'])
checks['sapiens_license_blocked'] = next(r for r in registry if r['model_id'] == 'SAPIENS2_0_4B')['weight_eligibility'] == 'LICENSE_BLOCKED_PENDING_APPLICABLE_PERMISSION'
checks['model_weights_directory_still_absent'] = not (WORKSPACE / 'models/human_parsing').exists()
matrix = list(csv.DictReader((ROOT / 'provenance/LICENSE_MATRIX_DECISION5A_V1.csv').open()))
checks['separate_model_code_weight_rows'] = all(
    {row['component'] for row in matrix if row['candidate'] == name} >= {'CODE', 'CHECKPOINT'}
    for name in ['FASHN', 'M2FP', 'CPI-Parser', 'D2FP', 'SCHP', 'Sapiens2-0.4B'])
checks['dataset_dependency_rows_separate'] = {'DATASET', 'DEPENDENCY_INSTALLED', 'DEPENDENCY_REFERENCE_ONLY'} <= {r['component'] for r in matrix}
checks['license_clearance_not_execution_permission'] = all(r['download_execution_authorized'] == 'False' for r in matrix)
checks['all_matrix_evidence_links_exist'] = all((ROOT / path.strip()).is_file() for r in matrix for path in r['evidence'].split(';'))

source_manifest = json.loads((prior / 'sources/SOURCE_MANIFEST.json').read_text())
checks['fetched_source_hashes'] = all(sha(ROOT / row['snapshot']) == row['sha256'] for row in source_manifest.values() if row.get('snapshot'))
locals_ = json.loads((run / 'LOCAL_SOURCE_MANIFEST.json').read_text())
checks['pinned_local_source_snapshot_hashes'] = all(
    sha(ROOT / row['snapshot']) == sha(WORKSPACE / row['source_workspace_relative']) == row['sha256'] for row in locals_)
checks['registry_source_revisions_match'] = all(
    row['source_commit'] == next(x['source_commit'] for x in locals_ if x['method'] == row['method'])
    for row in registry if any(x['method'] == row['method'] for x in locals_))
deps = json.loads((prior / 'INSTALLED_DEPENDENCY_LICENSES.json').read_text())
checks['installed_dependency_license_files_unchanged'] = all(
    sha(WORKSPACE / file['path']) == file['sha256'] for row in deps for file in row.get('license_files', []))
checks['dependency_versions_unchanged'] = all(row['version_unchanged'] for row in json.loads((run / 'DEPENDENCY_METADATA_RECHECK.json').read_text()))

proposal = json.loads((ROOT / 'manifests/FASHN_SMOKE_PROPOSAL_V2.json').read_text())
checks['fixed_train_inputs_3_verified'] = (
    [i['image_id'] for i in proposal['inputs']] == ['967', '14282', '4480']
    and all(i['split'] == 'train' and i['strict_pixel_load'] == 'PASS'
            and i['gt_dimensions_and_class_range'] == 'PASS'
            and sha(WORKSPACE / i['image_workspace_relative']) == i['source_sha256']
            and sha(WORKSPACE / i['gt_annotation_workspace_relative']) == i['gt_source_sha256'] for i in proposal['inputs']))
checks['proposal_boundaries'] = (proposal['download_authorized'] is False and proposal['inference_authorized'] is False
                                 and proposal['maximum_images'] == 3 and proposal['maximum_model_forward_calls'] == 4
                                 and proposal['precision'] == 'FP32' and proposal['download_budget_bytes'] == 300_000_000
                                 and proposal['dependency_install_authorized'] is False and proposal['cctv_inference'] is False)
dataset = json.loads((ROOT / 'manifests/DATASET_MANIFEST.json').read_text())
checks['original_dataset_index_and_inventory_unchanged'] = (
    sha(ROOT / dataset['canonical_gt_index']) == dataset['canonical_gt_index_sha256']
    and sha(ROOT / dataset['inventory']) == dataset['inventory_sha256'])

preservation = json.loads((ROOT / 'provenance/RUN_MANIFESTS/stage0-20261008T063349Z/PRESERVATION_AFTER.json').read_text())
repo_results = {}
for name, expected in before['git_repos'].items():
    cwd = WORKSPACE / name
    current = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=cwd, text=True).strip(),
                   status=subprocess.check_output(['git', 'status', '--short'], cwd=cwd, text=True).strip(),
                   branch=subprocess.check_output(['git', 'branch', '--show-current'], cwd=cwd, text=True).strip(),
                   remotes=subprocess.check_output(['git', 'remote', '-v'], cwd=cwd, text=True).strip())
    files = preservation['repos'][name]['files']
    repo_results[name] = dict(git_unchanged=current == expected, hashed_files=len(files),
                              artifact_hashes_unchanged=all(sha(cwd / path) == h for path, h in files.items()))
checks['six_yolo_repositories_user_changes_remotes_and_hashes_preserved'] = all(
    x['git_unchanged'] and x['artifact_hashes_unchanged'] for x in repo_results.values())
yolo = json.loads((ROOT / 'manifests/YOLO26X_SOURCE.json').read_text())
checks['frozen_yolo_checkpoint_unchanged'] = sha(WORKSPACE / yolo['checkpoint_workspace_relative']) == yolo['sha256']
checks['yolo_environment_metadata_unchanged'] = all(sha(WORKSPACE / p) == h for p, h in preservation['yolo_environment_files'].items())

docs = {ROOT / p for p in modified_relative if p.endswith('.md')}
docs |= {ROOT / 'RESEARCH_SCOPE.md', ROOT / 'reports/LICENSE_ELIGIBILITY_REASSESSMENT.md', WORKSPACE / 'README.md'}
missing_links = []
preexisting_missing_links = []
for doc in docs:
    archive_record = next((x for x in archive_records
                           if (WORKSPACE / x['original_workspace_relative'] if 'original_workspace_relative' in x
                               else ROOT / x['original_relative']) == doc), None)
    old_targets = set(re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', (ROOT / archive_record['archived_relative']).read_text())) if archive_record else set()
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', doc.read_text()):
        if re.match(r'^(https?://|mailto:|#)', target):
            continue
        filename = target.split('#')[0].strip('<>')
        if filename and not (doc.parent / filename).exists():
            item = {'document': str(doc.relative_to(WORKSPACE)), 'target': target}
            # Do not silently fix unrelated historical workspace references.
            if doc == WORKSPACE / 'README.md' and target in old_targets:
                preexisting_missing_links.append(item)
            else:
                missing_links.append(item)
checks['active_review_document_links_resolve'] = not missing_links
result = dict(run_id=active['run_id'], validated_utc=datetime.now(timezone.utc).isoformat(),
              status='PASS' if all(checks.values()) else 'FAIL', checks=checks,
              checks_passed=sum(checks.values()), checks_total=len(checks), missing_document_links=missing_links,
              preexisting_workspace_link_warnings=preexisting_missing_links,
              protected_original_artifact_hashes=protected, yolo_repositories=repo_results,
              source_collection_date='2026-10-08', metadata_rechecked='2026-10-12',
              evidence_limits={'all_original_dataset_files_rehashed': False,
                               'dataset_recheck_scope': 'Existing full inventories/index unchanged; 3 RGB + 3 GT bytes/coordinates rechecked',
                               'dependency_scope': 'Installed metadata/notices and reference licenses; not complete transitive SBOM',
                               'model_t4_fp32_feasibility': 'NOT_TESTED_WITH_CHECKPOINT'},
              checkpoint_downloads_this_review=0, heavyweight_installs_this_review=0,
              parser_inference_this_review=0, validation_inference=False, cctv_inference=False,
              full_benchmark=False, ppss_activity=False, overall_stage0_status='BLOCKED',
              review_gate='WAITING_FOR_USER_APPROVAL')
for path in [run / 'VALIDATION.json', ROOT / 'provenance/LICENSE_REASSESSMENT_VALIDATION_V1.json']:
    if path.exists():
        previous = json.loads(path.read_text())
        if previous['status'] != 'FAIL':
            raise RuntimeError(f'Refusing to overwrite passing validation evidence: {path}')
        backup = run / 'failed_validation' / path.name
        backup.parent.mkdir(exist_ok=True)
        if backup.exists():
            raise RuntimeError(f'Refusing to overwrite failed validation archive: {backup}')
        shutil.copyfile(path, backup)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'checks_passed': result['checks_passed'], 'checks_total': len(checks),
                  'failed_checks': [k for k, v in checks.items() if not v],
                  'yolo_files_hash_checked': sum(x['hashed_files'] for x in repo_results.values()),
                  'model_inference': 0}, ensure_ascii=False))
if result['status'] != 'PASS':
    raise SystemExit(1)
