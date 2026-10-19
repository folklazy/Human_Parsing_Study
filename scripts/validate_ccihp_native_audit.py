"""Validate Stage 0E evidence records, calculations, links and preservation."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import csv
import hashlib
import json
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent
active=json.loads((ROOT/'provenance/CCIHP_STAGE0E_CURRENT_RUN_V2.json').read_text())
RUN=ROOT/active['run_path']


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


facts=json.loads((ROOT/'provenance/CCIHP_ARCHIVE_AUDIT_V2.json').read_text())
zip_e=json.loads((RUN/'ZIP_INTEGRITY.json').read_text())
cross=json.loads((RUN/'BOUNDED_CROSS_DATASET_COMPARISON.json').read_text())
fidelity=json.loads((RUN/'CCIHP_GT_FIDELITY.json').read_text())
before=json.loads((RUN/'BEFORE.json').read_text())
revisions=json.loads((ROOT/'provenance/CCIHP_STAGE0E_NATIVE_DOCUMENT_REVISIONS_V2.json').read_text())
state=json.loads((ROOT/'STUDY_STATE.json').read_text())
checks={}
checks['actual_CCIHP_present']=(WORKSPACE/'datasets/CCIHP_icip.zip').is_file() and facts['requested_ccihp_archive_present']
checks['archive_SHA_identity_recorded']=facts['archive_sha256']==zip_e['archive_sha256']==json.loads((RUN/'ARCHIVE_SHA256.json').read_text())['sha256']
checks['full_crc_and_member_inventory_recorded']=zip_e['all_member_crc']=='PASS' and sha(ROOT/zip_e['member_inventory'])==zip_e['member_inventory_sha256']
with (ROOT/zip_e['member_inventory']).open() as stream:
    crc_records=[json.loads(line) for line in stream]
checks['all_209688_regular_member_crc_pass']=len(crc_records)==209688 and all(x['crc_validation']=='PASS' for x in crc_records)
checks['archive_paths_safe_and_original_stat_unchanged']=zip_e['safe_paths']=='PASS' and not zip_e['duplicate_members'] and not zip_e['symlink_members'] and zip_e['size_mtime_inode_unchanged']
split=json.loads((RUN/'SPLIT_COMPONENT_VALIDATION.json').read_text())
checks['split_component_counts_pairing']=split['split_counts']=={'Training':28280,'Validation':5000} and all(x['files']==split['split_counts'][s] and not x['missing_ids'] and not x['orphan_ids'] for s,items in split['components'].items() for x in items.values())
checks['both_splits_match_datasetninja']=split['datasetninja_ID_parity']=='EXACT_TRAIN_AND_VALIDATION' and not split['split_overlap_ids']
cases=cross['cases']
checks['bounded_sample_30_not_full_quality']=len(cases)==30 and Counter(x['split'] for x in cases)=={'Training':25,'Validation':5} and not state['stage0e_ccihp_cihp']['full_quality_audit_started']
checks['ninety_source_pngs_strict_decoded']=sum(len(x['CCIHP_pngs']) for x in cases)==90 and all(len({tuple(p['wh']) for p in x['CCIHP_pngs']}|{tuple(x['wh'])})==1 for x in cases)
checks['source_person_total_96_sample_only']=sum(len(x['person_ids']) for x in cases)==96==facts['native_CCIHP_person_planes_in_sample'] and facts['CCIHP_full_person_count'].startswith('NOT_COMPUTED')
part_relations=[r for x in cases for r in x['ccihp_part_relations']]
checks['840_part_instances_one_owner_one_category']=len(part_relations)==840 and all(r['single_human_and_class'] and len(r['human_ids'])==len(r['category_ids'])==1 for r in part_relations)
counts=Counter(a['status'] for x in cases for a in x['dn_part_associations'])
checks['cross_source_object_counts_independently_summed']=dict(counts)==facts['CIHP_part_to_CCIHP_human_association']=={'EXACT_ONE_HUMAN_FULL_SUPPORT':694,'MULTIPLE_HUMANS':21,'ONE_HUMAN_WITH_UNASSIGNED_PIXELS':26} and sum(counts.values())==741
checks['semantic_numeric_deltas_verified']=sum(x['raw_same_ID_semantic_difference_pixels'] for x in cases)==304537==facts['raw_same_numeric_ID_semantic_difference_pixels'] and sum(x['foreground_difference_pixels'] for x in cases)==35492==facts['foreground_difference_pixels']
checks['unknown22_retained_not_repaired']=sum(x['undocumented_semantic_pixels'] for x in cases)==2 and facts['undocumented_category_values'][0]['image_id']=='0033810' and facts['undocumented_category_values'][0]['coordinates_xy']==[[301,162],[302,162]]
checks['human_category_gap_not_hidden']=sum(x['human_without_semantic_pixels'] for x in cases)==12 and sum(x['semantic_without_human_pixels'] for x in cases)==0
checks['native_demo_scope_five_semantic_only']=sum(x['native_demo_reference'] is not None for x in cases)==5 and all(x['native_demo_reference']['native_human_reference']=='UNAVAILABLE' for x in cases if x['native_demo_reference'])
checks['all_30_native_CCIHP_source_roundtrips']=fidelity['sample_images']==30 and fidelity['native_CCIHP_person_planes']==96 and all(x['all_three_grids_exact_roundtrip'] and x['unknown_values_retained'] for x in fidelity['cases'])
checks['lossless_three_GT_exports_hashes']=sum('lossless_sample_export' in x for x in fidelity['cases'])==3 and all(sha(ROOT/x['lossless_sample_export'])==x['export_sha256'] for x in fidelity['cases'] if x.get('lossless_sample_export'))
checks['eight_GT_unit_tests_executed']='Ran 8 tests' in (ROOT/fidelity['test_log']).read_text() and '\nOK\n' in (ROOT/fidelity['test_log']).read_text() and sha(ROOT/'src/data/ccihp_gt.py')==fidelity['source_code_sha256']
checks['three_GTs_visual_artifacts_present']=sum('diagnostic_image' in x for x in cases)==3 and all(sha(ROOT/x['diagnostic_image'])==x['diagnostic_sha256'] for x in cases if x.get('diagnostic_image'))
checks['native_vs_custom_evaluation_separated']=facts['decision']=='B' and not facts['native_CIHP_GT_ready'] and facts['custom_CCIHP_person_GT_feasibility'].startswith('CONDITIONAL')
checks['no_fake_independent_CCIHP_RGB_check']=facts['CCIHP_RGB_images_in_archive']==0 and facts['independent_CCIHP_RGB_identity'].startswith('NOT_TESTED')
matrix=list(csv.DictReader((ROOT/'taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv').open()))
checks['native_class_inventory_and_unknown22_covered']={x['cihp_native_id'] for x in matrix if x['cihp_native_id'].isdigit()}=={str(i) for i in range(20)} and any(x['ccihp_declared_id']=='22' and x['compatibility_status']=='NOT_VERIFIED' for x in matrix)
checks['taxonomy_not_frozen_or_falsely_equivalent']=all(x['mapping_frozen']=='False' and x['compatibility_status'] not in {'EXACT','VERIFIED_EQUIVALENT'} for x in matrix)
checks['source_LICENSE_inspected_scope_separate']=facts['annotation_license'].startswith('CC-BY-NC-4.0_VERIFIED') and facts['original_CIHP_RGB_rights'].startswith('UNRESOLVED') and facts['scope_decision']=='5A_REUSED'
changed={x['original_relative'] for x in revisions['revisions']}
protected={p:h for p,h in before['hashes_before'].items() if p not in changed}
checks['prior_scientific_records_unchanged']=all(sha(ROOT/p)==h for p,h in protected.items())
checks['old_reports_archived_with_before_after_hashes']=all(sha(ROOT/x['archived_relative'])==x['sha256_before'] and sha(ROOT/x['original_relative'])==x['sha256_after'] for x in revisions['revisions'])
checks['state_original_scientific_and_paused_nodes_preserved']=all(state[k]==v for k,v in before['prior_state'].items() if k not in {'last_updated_utc','stage0e_ccihp_cihp'})
checks['no_benchmark_primary_promotion_or_scope_overreach']=all(facts[k] is False for k in ['taxonomy_frozen','primary_dataset_promoted','new_inference','originals_modified','dataset_or_checkpoint_download','full_benchmark','ppss_activity','cctv_activity','attributes_evaluated']) and state['benchmark_status']=='NOT_STARTED' and state['stage0_overall_status']=='BLOCKED'
git_after={}
for name,previous in before['git_repos'].items():
    git_after[name]={k:subprocess.check_output(['git']+c,cwd=WORKSPACE/name,text=True).strip() for k,c in [('head',['rev-parse','HEAD']),('status',['status','--short']),('branch',['branch','--show-current']),('remotes',['remote','-v'])]}
checks['six_YOLO_repo_git_states_preserved']=git_after==before['git_repos']
missing=[]
docs=[ROOT/x['original_relative'] for x in revisions['revisions'] if x['original_relative'].endswith('.md')]
for doc in docs:
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',doc.read_text()):
        if not re.match(r'^(https?://|mailto:|#)',target) and not (doc.parent/target.split('#')[0].strip('<>')).exists():missing.append({'document':str(doc.relative_to(ROOT)),'target':target})
checks['active_document_visual_links_resolve']=not missing
checks['initial_failures_preserved']=(RUN/'FIRST_ATTEMPT_FAILURE.json').exists() and (RUN/'SECOND_ATTEMPT_FAILURE.json').exists()
result={'run_id':active['run_id'],'timestamp_utc':datetime.now(timezone.utc).isoformat(),'record_validation':'PASS' if all(checks.values()) else 'FAIL',
        'checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),'missing_links':missing,
        'native_CIHP_equivalence':'BLOCKED','custom_CCIHP_benchmark':'CONDITIONAL_NOT_STARTED','full_quality_audit':'NOT_STARTED',
        'git_after':git_after,'protected_hashes':protected,'physical_person_correctness_datasetwide':'NOT_VERIFIED',
        'limitations':['No original native CIHP Human_ids reference','Source annotation22 unresolved','Only30semantic/person frames audited',
                       'ZIPCRC is not semantic accuracy','No independent CCIHP RGB copy','No full decoded/near duplicate re-audit'],
        'next_action':'WAIT_FOR_USER_APPROVAL'}
for path in [RUN/'VALIDATION.json',ROOT/'provenance/CCIHP_STAGE0E_NATIVE_VALIDATION_V2.json']:
    if path.exists():
        previous=json.loads(path.read_text())
        if previous['record_validation']!='FAIL':raise RuntimeError('Refusing to overwrite passing validation evidence')
        backup=RUN/'failed_validation'/path.name;backup.parent.mkdir(exist_ok=True)
        if backup.exists():raise RuntimeError('Refusing to overwrite failed-validation archive')
        shutil.copyfile(path,backup)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'record_validation':result['record_validation'],'checks':f"{result['checks_passed']}/{result['checks_total']}",
                  'failed':[k for k,v in checks.items() if not v],'native_CIHP':'BLOCKED','decision':'B'}))
if not all(checks.values()):raise SystemExit(1)
