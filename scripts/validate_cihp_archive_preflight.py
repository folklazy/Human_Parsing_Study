"""Validate actual preflight evidence and preserve original study/assets.

No archive extraction or benchmark. Does not access paused PPSS file contents.
"""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
from collections import Counter
import json
import re
import subprocess
import sys

S=Path(__file__).resolve().parents[1];W=S.parent


def digest(path):
    h=sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()


def main():
    result=json.loads((S/'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json').read_text())
    run=S/'provenance/RUN_MANIFESTS'/result['run_id'];before=json.loads((run/'BEFORE.json').read_text())
    revisions=json.loads((S/'provenance/CIHP_PREFLIGHT_DOCUMENT_REVISIONS_V1.json').read_text())['revisions']
    edited={r['original_path'] for r in revisions};checks={};failures=[]
    def check(name,condition):
        checks[name]='PASS' if condition else 'FAIL'
        if not condition:failures.append(name)
    protected={p:h for p,h in before['hashes_before'].items() if p not in edited}
    check('existing_protected_stage0_artifacts',all(digest(S/p)==h for p,h in protected.items()))
    check('active_archive_and_revision_hashes',all(digest(S/r['archive'])==r['before_sha256'] and
        digest(S/r['original_path'])==r['after_sha256'] for r in revisions))
    source_state=json.loads((S/next(r['archive'] for r in revisions if r['original_path']=='STUDY_STATE.json')).read_text())
    state=json.loads((S/'STUDY_STATE.json').read_text())
    check('paused_state_nodes_preserved',{k:v for k,v in state.items() if k.startswith('ppss')}==
        {k:v for k,v in source_state.items() if k.startswith('ppss')})
    archive=W/result['archive_workspace_relative'];stat=archive.stat()
    check('original_archive_unchanged',stat.st_size==before['archive_stat_before']['size']==result['archive_bytes'] and
        stat.st_mtime_ns==before['archive_stat_before']['mtime_ns'] and digest(archive)==result['archive_sha256']==result['archive_sha256_after'])
    check('complete_TAR_and_bitmap_checks',result['container_integrity']=='PASS' and not result['errors'] and
        result['counts']['bitmap_decoded']==768446 and result['all_annotation_bitmaps_full_decode_and_PNG_CRC']=='PASS')
    check('inventory_fingerprints',digest(S/result['member_inventory'])==result['member_inventory_sha256'] and
        digest(S/result['annotation_summary'])==result['annotation_summary_sha256'])
    inventory_counts=Counter();regular=0
    for line in (S/result['member_inventory']).open():
        row=json.loads(line);regular+=1
        if '/img/' in row['path']:inventory_counts[row['path'].split('/')[0]+'_images']+=1
        if '/ann/' in row['path']:inventory_counts[row['path'].split('/')[0]+'_annotations']+=1
    check('all_regular_payloads_in_inventory',regular==76563 and all(result['counts'][k]==v for k,v in inventory_counts.items()))
    check('image_annotation_pairing_and_header_grids',not result['missing_image_annotation_pairs'] and
        not result['header_annotation_dimension_mismatches'])
    check('official_validation_IDs',result['official_validation_ID_set_exact_match'])
    check('bounded_RGB_tests_only',len(result['sample_strict_RGB_decode'])==20 and
        all(r['strict_full_RGB_decode']=='PASS' for r in result['sample_strict_RGB_decode']))
    check('five_official_demo_fidelity_tests',len(result['native_reference_semantic_comparisons'])==5 and
        all(r['same_JPEG_bytes'] and r['RGB_pixels_identical'] and r['GT_semantic_pixels_identical'] and r['mismatched_pixels']==0
            for r in result['native_reference_semantic_comparisons']))
    check('diagnostic_images_unchanged',all(not r.get('diagnostic') or digest(S/r['diagnostic'])==r['diagnostic_sha256']
        for r in result['sample_strict_RGB_decode']))
    supplemental=json.loads((run/'CONVERSION_SUPPLEMENT.json').read_text())
    check('class_ID_title_consistency',supplemental['class_mapping_consistency_counts'].get('class_ID_title_mismatch',0)==0 and
        supplemental['class_mapping_consistency_counts']['objects']==768446)
    ast=json.loads((run/'CONVERTER_STATIC_AUDIT.json').read_text())
    check('missing_native_human_metadata_honestly_reported',not result['ownership_field_counts'] and
        result['annotation_image_tag_count']==result['annotation_object_tag_count']==0 and not ast['humans_path_reads'] and
        not state['cihp_archive_preflight']['native_human_GT_ready'])
    check('no_false_primary_or_full_quality_claim',state['primary_benchmark']=='UNDECIDED' and
        not state['cihp_archive_preflight']['primary_promoted'] and not state['cihp_archive_preflight']['full_quality_audit_started'])
    tests=json.loads((run/'BOUNDED_TESTS.json').read_text())
    check('actual_test_evidence',tests['status']=='PASS' and tests['tests_run']==60 and
        digest(S/tests['log'])==tests['log_sha256'])
    source_manifests=[run/'sources/DATASETNINJA_SOURCE_MANIFEST.json',run/'sources/PGN_SPLIT_SOURCE_MANIFEST.json',
                     run/'sources/reference_fixtures/SOURCE_MANIFEST.json']
    check('reference_snapshots_unchanged',all('sha256' not in entry or digest(S/entry['snapshot'])==entry['sha256']
        for p in source_manifests for entry in json.loads(p.read_text()).values()))
    repo_status={};repo_fail=[]
    for name,entry in before['git_repos'].items():
        path=W/name
        status={k:subprocess.check_output(['git',*args],cwd=path,text=True).strip() for k,args in
            [('head',['rev-parse','HEAD']),('branch',['branch','--show-current']),('status',['status','--porcelain']),('remotes',['remote','-v'])]}
        repo_status[name]=status
        if status!=entry:repo_fail.append(name)
    check('existing_YOLO_Git_branches_remotes_user_work',not repo_fail)
    preservation=json.loads((S/'provenance/RUN_MANIFESTS/stage0-20261008T063349Z/PRESERVATION_AFTER.json').read_text())
    changed=[];protected_count=0
    for name,entry in preservation['repos'].items():
        for p,h in entry['files'].items():
            protected_count+=1
            if digest(W/name/p)!=h:changed.append(name+'/'+p)
    check('previous_YOLO_frozen_files',not changed)
    check('frozen_YOLO26x_and_environment',digest(W/'models/yolo26x-seg.pt')==preservation['yolo26x_sha256'] and
        all(digest(W/p)==h for p,h in preservation['yolo_environment_files'].items()))
    docs=[S/'README.md',S/'DATA_SCHEMA.md',S/'EXPERIMENT_PROTOCOL_DRAFT.md',
        *[S/'reports'/p for p in ['DATASET_REASSESSMENT.md','CIHP_QUALITY_AUDIT.md','CIHP_ARCHIVE_PREFLIGHT_AUDIT.md',
                                'STAGE0_NEXT_ACTIONS.md','PRIMARY_DATASET_DECISION.md']]]
    missing=[]
    for p in docs:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
            if target.startswith(('http:','https:','#')):continue
            if target.endswith('CIHP_ARCHIVE_PREFLIGHT_VALIDATION_V1.json'):continue
            if not (p.parent/target.split('#')[0]).exists():missing.append([str(p.relative_to(S)),target])
    check('active_documentation_links',not missing)
    validation={'schema_version':'1.0','run_id':result['run_id'],'end_utc':datetime.now(timezone.utc).isoformat(),
        'execution_status':'FAIL' if failures else 'PASS_WITH_WARNINGS','archive_integrity':'PASS',
        'human_instance_contract':'BLOCKED_MISSING_NATIVE_HUMAN_GT','overall_stage0_status':'BLOCKED',
        'primary_promoted':False,'checks':checks,'failures':failures,'missing_links':missing,
        'tests':tests,'git_status':repo_status,'YOLO_protected_files_compared':protected_count,'YOLO_changed':changed,
        'original_archive_modified':False,'original_MHP_or_YOLO_modified':False,'PPSS_file_contents_accessed_or_modified':False,
        'full_extraction':False,'full_quality_audit':False,'model_inference':False,'validation_inference':False,
        'full_benchmark':False,'checkpoint_download':False,'training':False,'fusion':False,'color_analysis':False,'remote_push':False,
        'network_scope':'Bounded source code/documentation/API metadata and 10 official repo demo reference fixtures (235490 bytes); no dataset archive/checkpoint download',
        'limitations':['No verified native human ownership or full original-release fidelity',
            'RGB full-pixel decoding bounded to 20; headers/payload hashes exhaustive',
            'Full native train/test ID parity unverified; official-val GT metadata IDs verified',
            'Byte duplicate groups are not full decoded/near-duplicate audit',
            'Provider MIT claim is not independent original dataset rights verification'],
        'review_gate':'WAITING_FOR_USER_APPROVAL'}
    path=S/'provenance/CIHP_ARCHIVE_PREFLIGHT_VALIDATION_V1.json'
    if path.exists():raise FileExistsError(path)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
    assets=docs+[S/'STUDY_STATE.json',path,S/'src/data/cihp_datasetninja.py',S/'tests/test_cihp_archive_preflight.py',
        S/'scripts/audit_cihp_archive_preflight.py',S/'scripts/update_cihp_preflight_documents.py',Path(__file__),
        S/'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json',S/'provenance/CIHP_DATASETNINJA_BYTE_DUPLICATES_V1.json',
        S/'provenance/CIHP_PREFLIGHT_DOCUMENT_REVISIONS_V1.json',S/'manifests/CIHP_DATASETNINJA_ARCHIVE_MANIFEST_V1.json',
        S/'manifests/CIHP_QUALITY_REVIEW_PLAN_V2.json']
    final={'run_id':result['run_id'],'start_utc':before['start_utc'],'end_utc':validation['end_utc'],
        'study_git_commit':'NOT_GIT_INITIALIZED','environment_workspace_relative':'.venvs/mhpv2-stage0',
        'dataset_archive_sha256':result['archive_sha256'],'checkpoint_runs':[],
        'assets':{str(p.relative_to(S)):digest(p) for p in assets},
        'preserved_older_evidence':protected,'current_document_revision_record':'provenance/CIHP_PREFLIGHT_DOCUMENT_REVISIONS_V1.json',
        'actual_operations':['TAR all-member payload/hash/integrity scan','All-JSON/all-bitmap readability/coordinate validation',
            '20-image bounded strict RGB decoding','Five official repo demo semantic fidelity comparisons',
            'Reference converter static audit and exact-byte duplicate inventory','60 synthetic/contract tests',
            'Archived documentation/state continuation and scoped preservation validation'],
        'status':validation['execution_status'],'scientific_readiness':'BLOCKED','benchmark_authorized':False}
    (run/'FINAL_RUN_MANIFEST.json').write_text(json.dumps(final,indent=2)+'\n')
    print(json.dumps({'preflight':validation['execution_status'],'checks_passed':sum(v=='PASS' for v in checks.values()),
                     'failures':failures,'tests_passed':tests['tests_run'],'YOLO_files_preserved':protected_count,
                     'native_human_GT':'BLOCKED','primary_promoted':False}))
    if failures:sys.exit(1)


if __name__=='__main__':main()
