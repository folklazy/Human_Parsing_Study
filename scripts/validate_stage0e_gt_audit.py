"""Validate Stage 0E evidence and preservation; do not evaluate datasets/models."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import csv
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
active = json.loads((ROOT / 'provenance/CCIHP_STAGE0E_ACTIVE_RUN.json').read_text())
RUN = ROOT / active['run_path']


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


before = json.loads((RUN / 'BEFORE.json').read_text())
revisions = json.loads((ROOT / 'provenance/CCIHP_STAGE0E_DOCUMENT_REVISIONS.json').read_text())
facts = json.loads((ROOT / 'provenance/CCIHP_ARCHIVE_AUDIT.json').read_text())
bounded = json.loads((RUN / 'CIHP_BOUNDED_REFERENCE_RECHECK.json').read_text())
identity = json.loads((RUN / 'ARCHIVE_IDENTITY.json').read_text())
state = json.loads((ROOT / 'STUDY_STATE.json').read_text())
checks = {}
checks['actual_target_identity_cihp_not_ccihp'] = identity['publisher_metadata_identity'] == 'CIHP_CROWD_INSTANCE_LEVEL_HUMAN_PARSING' and not identity['is_verified_ccihp_release']
checks['absent_ccihp_not_faked_as_zip_integrity_pass'] = (facts['requested_ccihp_archive_sha256'] is None
    and facts['requested_ccihp_archive_bytes'] is None and facts['ccihp_crc_validation'].startswith('NOT_TESTED'))
checks['human_counts_not_invented'] = facts['ccihp_person_count'] is None and all(x['person_count'] is None for x in bounded['actual_cases'])
checks['no_person_source_present_in_member_inventory'] = all(not value for value in identity['ccihp_expected_component_members'].values())
checks['native_person_readiness_blocked'] = facts['actual_target_human_gt'] == 'MISSING' and not facts['native_cihp_benchmark_gt_ready']
checks['selected_decision_scope_is_current_assets'] = facts['decision'] == 'C' and facts['decision_scope'] == 'CURRENTLY_AVAILABLE_ASSETS_ONLY'
checks['native_and_custom_tracks_separated'] = facts['custom_semantic_track'].startswith('CONDITIONAL') and facts['custom_person_instance_track'].startswith('BLOCKED')
checks['five_native_semantic_demos_only'] = len(bounded['actual_cases']) == 5 and all(x['semantic_pixel_differences'] == 0 and x['foreground_boundary_pixel_differences'] == 0 and x['native_demo_RGB_bytes_match'] for x in bounded['actual_cases'])
checks['actual_payload_hashes_and_bounded_budget'] = len(bounded['member_reads']) == 13 and all(x['matches_prior_member_hash'] for x in bounded['member_reads']) and bounded['member_bytes_read'] == 322301
checks['three_semantic_not_human_visuals'] = sum('diagnostic_image' in x for x in bounded['actual_cases']) == 3 and all(x['human_GT'] == 'NOT_AVAILABLE' for x in bounded['actual_cases'])
checks['diagnostic_hashes_unchanged'] = all(sha(ROOT / x['diagnostic_image']) == x['diagnostic_sha256'] for x in bounded['actual_cases'] if 'diagnostic_image' in x)
visual = json.loads((RUN / 'VISUAL_INSPECTION.json').read_text())
checks['visual_evidence_limits_explicit'] = len(visual['images']) == 3 and not visual['physical_person_GT_verified'] and not visual['ccihp_visuals_generated']
tests = json.loads((RUN / 'CIHP_DECODER_TESTS_V2.json').read_text())
log = (ROOT / tests['log']).read_text()
checks['nine_decoder_tests_executed'] = tests['exit_code'] == 0 and 'Ran 9 tests' in log and '\nOK\n' in log and sha(ROOT / tests['log']) == tests['log_sha256']
checks['failed_test_launch_preserved'] = (RUN / 'CIHP_DECODER_TESTS.json').exists() and json.loads((RUN / 'CIHP_DECODER_TESTS.json').read_text())['status'] == 'FAIL'
matrix = list(csv.DictReader((ROOT / 'taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv').open()))
allowed = {'EXACT','VERIFIED_EQUIVALENT','SAFE_MERGE','AMBIGUOUS','INCOMPATIBLE','MISSING','NOT_VERIFIED'}
checks['native_20_class_inventory_covered'] = {r['cihp_native_id'] for r in matrix if r['cihp_native_id'].isdigit()} == {str(i) for i in range(20)}
checks['matrix_no_fabricated_equivalence_or_frozen_mapping'] = all(r['compatibility_status'] in allowed and r['compatibility_status'] not in {'EXACT','VERIFIED_EQUIVALENT'} and r['local_ccihp_pixel_verification'] == 'NOT_TESTED' and r['mapping_frozen'] == 'False' for r in matrix)
checks['class6_dress_mask_conflict_retained'] = next(r for r in matrix if r['cihp_native_id'] == '6')['compatibility_status'] == 'INCOMPATIBLE'
checks['release_count_uncertainty_recorded'] = '21' in facts['documented_taxonomy_version_warning'] and '19' in facts['documented_taxonomy_version_warning']
sources = json.loads((RUN / 'sources/SOURCE_MANIFEST.json').read_text())
checks['source_snapshots_sha_verified'] = all(sha(ROOT / x['snapshot']) == x['sha256'] for x in sources.values() if x.get('snapshot'))
checks['failed_official_metadata_fetches_honestly_recorded'] = sources['cea_readme']['status'] == 'FETCH_FAILED'
checks['scope_license_findings_reused_not_overwritten'] = all(sha(ROOT / p) == before['hashes_before'][p] for p in ['provenance/LICENSE_REASSESSMENT_DECISION5A_V1.json','provenance/LICENSE_MATRIX_DECISION5A_V1.csv'])

protected = {p:h for p,h in before['hashes_before'].items() if p not in {r['original_relative'] for r in revisions['revisions']}}
checks['prior_dataset_checkpoint_scientific_records_unchanged'] = all(sha(ROOT / p) == h for p,h in protected.items())
checks['archives_and_before_after_hashes'] = all(sha(ROOT / r['archived_relative']) == r['sha256_before'] and sha(ROOT / r['original_relative']) == r['sha256_after'] for r in revisions['revisions'])
checks['previous_state_nodes_preserved'] = all(state[k] == value for k,value in before['prior_state'].items() if k != 'last_updated_utc')
checks['benchmark_and_roles_not_promoted'] = state['benchmark_status'] == 'NOT_STARTED' and state['stage0_overall_status'] == 'BLOCKED' and not state['stage0e_ccihp_cihp']['primary_promoted']
checks['scope_invariants_no_execution'] = all(facts[k] is False for k in ['model_inference','checkpoint_download','dataset_download','original_dataset_modified','full_benchmark','ppss_activity','cctv_activity'])
exec_evidence = json.loads((RUN / 'EXECUTION.json').read_text())
checks['target_not_extracted_modified_or_rehashed'] = exec_evidence['size_mtime_inode_unchanged'] and facts['actual_target_whole_archive_rehashed'] is False

git_results = {}
for name, old in before['git_repos'].items():
    cwd = WORKSPACE / name
    git_results[name] = {k:subprocess.check_output(['git'] + command, cwd=cwd, text=True).strip() for k,command in
                         [('head',['rev-parse','HEAD']),('status',['status','--short']),('branch',['branch','--show-current']),('remotes',['remote','-v'])]}
checks['six_yolo_git_states_and_user_changes_preserved'] = git_results == before['git_repos']
missing = []
docs = [ROOT / p for p in revisions['new_artifacts'] if p.endswith('.md')] + [ROOT / r['original_relative'] for r in revisions['revisions'] if r['original_relative'].endswith('.md')]
for doc in docs:
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', doc.read_text()):
        if not re.match(r'^(https?://|mailto:|#)', target) and not (doc.parent / target.split('#')[0].strip('<>')).exists():
            missing.append({'document': str(doc.relative_to(ROOT)), 'target': target})
checks['active_report_links_and_images_resolve'] = not missing
result = {'run_id': active['run_id'], 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
          'evidence_record_validation': 'PASS' if all(checks.values()) else 'FAIL',
          'dataset_person_GT_status': 'BLOCKED', 'stage0e_overall_status': 'BLOCKED',
          'checks': checks, 'checks_passed': sum(checks.values()), 'checks_total': len(checks),
          'missing_links': missing, 'git_after': git_results, 'protected_hashes': protected,
          'scope_limits': ['Not a new full TAR hash/integrity audit', 'No CCIHP source/CRC/pixel test',
                           'No native human-reference parity', 'No quality-prevalence estimate',
                           'YOLO git/provenance unchanged; no repeat full model/dataset hashing'],
          'review_gate': 'WAIT_FOR_USER_APPROVAL'}
for path in [RUN / 'VALIDATION.json', ROOT / 'provenance/CCIHP_STAGE0E_VALIDATION.json']:
    if path.exists():
        raise RuntimeError(f'Refusing to overwrite validation: {path}')
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'record_validation': result['evidence_record_validation'], 'checks_passed': result['checks_passed'],
                  'checks_total': result['checks_total'], 'failed_checks': [k for k,v in checks.items() if not v],
                  'person_GT': 'BLOCKED', 'decision': 'C', 'model_inference': 0}))
if not all(checks.values()):
    raise SystemExit(1)
