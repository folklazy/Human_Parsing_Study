"""Finalize scoped evidence; does not repeat full dataset audit or touch PPSS."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import csv
import json
import re
import subprocess
import sys

S=Path(__file__).resolve().parents[1]
W=S.parent
sys.path.insert(0,str(S))
from src.evaluation.official_mhp_compat import PINNED_SOURCE_SHA256,PINNED_VOC_SHA256,source_directory


def digest(path):
    h=sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()


def main():
    run=S/'provenance/RUN_MANIFESTS/dataset-reassessment-20261008T095241Z'
    before=json.loads((run/'BEFORE.json').read_text())
    revisions=json.loads((S/'provenance/DATASET_REASSESSMENT_DOCUMENT_REVISIONS.json').read_text())
    changed={e['original_path'] for e in revisions['entries']}
    failures=[];checks={}
    def check(name,condition):
        checks[name]='PASS' if condition else 'FAIL'
        if not condition:failures.append(name)
    protected={p:h for p,h in before['study_files'].items() if p not in changed}
    check('historical_study_evidence_unchanged',all(digest(S/p)==h for p,h in protected.items()))
    check('archives_and_after_hashes',all(digest(S/e['archive'])==e['sha256_before'] and
          digest(S/e['original_path'])==e['sha256_after'] for e in revisions['entries']))
    original_state=next(e for e in revisions['entries'] if e['original_path']=='STUDY_STATE.json')
    previous=json.loads((S/original_state['archive']).read_text());state=json.loads((S/'STUDY_STATE.json').read_text())
    check('paused_state_nodes_preserved', {k:v for k,v in previous.items() if k.startswith('ppss')}==
          {k:v for k,v in state.items() if k.startswith('ppss')})
    check('no_primary_freeze_or_benchmark',state['primary_benchmark']=='UNDECIDED' and
          not state['dataset_reassessment']['primary_roles_frozen'] and state['benchmark_status']=='NOT_STARTED')
    source=source_directory()
    check('official_evaluator_source_unchanged',digest(source/'eval_mhp.py')==PINNED_SOURCE_SHA256 and
          digest(source/'voc_eval.py')==PINNED_VOC_SHA256)
    tests=json.loads((run/'BOUNDED_TESTS_V2.json').read_text())
    check('executed_tests',tests['status']=='PASS' and tests['tests_run']==51 and digest(S/tests['log'])==tests['log_sha256'])
    policy=json.loads((S/'provenance/MHPV2_READABLE_POLICY_V1.json').read_text())
    check('population_manifest_hashes',all(digest(S/p['manifest'])==p['sha256'] for p in policy['populations']))
    check('population_sources_unchanged',all(digest(S/p)==h for p,h in policy['sources'].items()))
    root=W/'datasets/LV-MHP-v2'
    sample=policy['random_sample']
    check('random_sample_source_and_visual_hashes',len(sample)==30 and all(
        digest(root/r['image_path'])==r['image_sha256'] and
        all(digest(root/p['annotation_path'])==p['sha256'] for p in r['source_annotations']) and
        digest(S/r['diagnostic'])==r['diagnostic_sha256'] for r in sample))
    check('contact_sheet_hashes',all(digest(S/r['path'])==r['sha256'] for r in policy['contact_sheets']))
    checklist=list(csv.DictReader((S/'reports/MHPV2_RANDOM_QUALITY_REVIEW_V1.csv').open()))
    check('human_review_not_fabricated',len(checklist)==30 and all(r['status']=='PENDING' for r in checklist))
    registry=list(csv.DictReader((S/'provenance/MODEL_VARIANT_REGISTRY_V2.csv').open()))
    check('registry_no_false_inference_claim',len(registry)==17 and len({r['model_id'] for r in registry})==17 and
          all(r['checkpoint_inference_passed']=='False' and r['checkpoint_downloaded']=='False' and
              r['model_loaded']=='False' for r in registry))
    check('registry_config_hashes',all(not r['source_config'] or digest(W/r['source_config'])==r['source_config_sha256'] for r in registry))
    old_sources=json.loads((S/'provenance/SOURCE_REVISIONS.json').read_text());source_fail=[]
    for name,entry in old_sources.items():
        if 'local_path' not in entry:continue
        repo=W/entry['local_path']
        if subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()!=entry['commit']:source_fail.append(name)
        if subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip()!=entry['status']:source_fail.append(name+':status')
    check('parser_sources_unchanged',not source_fail)
    # Compare full frozen YOLO tracked-file/metrics baseline, not only headline CSVs.
    preservation=json.loads((S/'provenance/RUN_MANIFESTS/stage0-20261008T063349Z/PRESERVATION_AFTER.json').read_text())
    repo_states={};yolo_changed=[];protected_count=0
    for name,entry in preservation['repos'].items():
        repo=W/name
        current={key:subprocess.check_output(['git',*args],cwd=repo,text=True).strip() for key,args in
                 [('head',['rev-parse','HEAD']),('branch',['branch','--show-current']),
                  ('status',['status','--porcelain']),('remotes',['remote','-v'])]}
        repo_states[name]=current
        for key in ['head','branch','status','remotes']:
            if current[key]!=entry[key]:yolo_changed.append(name+':'+key)
        for p,h in entry['files'].items():
            protected_count+=1
            if not (repo/p).is_file() or digest(repo/p)!=h:yolo_changed.append(name+'/'+p)
    check('previous_YOLO_repositories_and_user_changes_preserved',not yolo_changed)
    check('frozen_YOLO26x_checkpoint_unchanged',digest(W/'models/yolo26x-seg.pt')==preservation['yolo26x_sha256'])
    check('YOLO_environment_metadata_unchanged',all(digest(W/p)==h for p,h in preservation['yolo_environment_files'].items()))
    sources=json.loads((run/'sources/SOURCE_METADATA.json').read_text())
    check('source_snapshots_hashes',all('sha256' not in r or digest(S/r['snapshot'])==r['sha256'] for r in sources.values()))
    cihp=json.loads((S/'provenance/CIHP_ACQUISITION_REVIEW_V1.json').read_text())
    check('CIHP_unverified_local_quality_not_fabricated',not cihp['local_CIHP_dataset_found'] and not cihp['archive_downloaded']
          and cihp['archive_sha256_local'] is None and cihp['archive_bytes_provider_metadata']==2033753964)
    docs=[S/'README.md',S/'STUDY_STANDARD.md',S/'DATA_SCHEMA.md',S/'EXPERIMENT_PROTOCOL_DRAFT.md',
          *[S/'reports'/n for n in ['DATASET_REASSESSMENT.md','CIHP_QUALITY_AUDIT.md','MHPV2_QUALITY_RISK_REVIEW.md',
                                    'PRIMARY_DATASET_DECISION.md','STAGE0_NEXT_ACTIONS.md']]]
    missing=[]
    for p in docs:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
            if target.startswith(('http:','https:','#')):continue
            resolved=(p.parent/target.split('#')[0]).resolve()
            if target=='provenance/DATASET_REASSESSMENT_VALIDATION.json':continue
            if not resolved.exists():missing.append((str(p.relative_to(S)),target))
    check('active_documentation_links_resolve',not missing)
    result={'schema_version':'1.0','run_id':run.name,'end_utc':datetime.now(timezone.utc).isoformat(),
        'preparation_status':'FAIL' if failures else 'PASS_WITH_WARNINGS','overall_stage0_status':'BLOCKED',
        'review_gate':'WAITING_FOR_USER_APPROVAL','checks':checks,'failures':failures,
        'missing_links':missing,'YOLO_changed':yolo_changed,'YOLO_protected_files_compared':protected_count,
        'git_status':repo_states,'study_git_initialized':(S/'.git').exists(),
        'scientific_invariants':{'original_MHP_dataset_modified':False,'original_GT_modified':False,
          'official_split_files_modified':False,'previous_YOLO_modified':False,'PPSS_file_contents_accessed_or_modified':False,
          'parser_inference':False,'validation_inference':False,'full_benchmark':False,'training':False,
          'hybrid':False,'color_attributes':False,'company_CCTV_inference':False,'checkpoint_download':False,
          'CIHP_archive_download':False,'heavyweight_installation':False,'remote_created_or_pushed':False},
        'scope_of_dataset_preservation_check':'Reused prior exhaustive inventory; compared its/index hashes and directly hashed 30 diagnostic image/GT source sets. No new exhaustive 100134-file rehash.',
        'warning_gates':['CIHP absent: GT integrity/ownership/license unverified','MHP human random quality review pending',
          'Exact overlap control not full independence','No intended-checkpoint parser smoke pass',
          'Synthetic evaluator parity is not published-score or CIHP evaluator parity','Taxonomy/protocol/dataset roles remain draft'],
        'executed_tests':tests,'archive_record':'provenance/DATASET_REASSESSMENT_DOCUMENT_REVISIONS.json'}
    out=S/'provenance/DATASET_REASSESSMENT_VALIDATION.json'
    if out.exists():raise FileExistsError(out)
    tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');tmp.replace(out)
    # Seal new run code/docs/evidence; no placeholder references to unexecuted tests.
    assets=docs+[S/'STUDY_STATE.json',S/'configs/study.yaml',S/'configs/dataset.yaml',out,
         S/'src/evaluation/official_mhp_compat.py',S/'tests/test_official_mhp_compat.py',S/'tests/test_dataset_reassessment.py',
         S/'provenance/MODEL_VARIANT_REGISTRY_V2.csv',S/'provenance/MHPV2_READABLE_POLICY_V1.json',
         S/'provenance/CIHP_ACQUISITION_REVIEW_V1.json',S/'provenance/MHPV2_RANDOM_REVIEW_DISPLAY_SPOTCHECK_V1.json',
         S/'provenance/DATASET_REASSESSMENT_DOCUMENT_REVISIONS.json',S/'manifests/MHPV2_RANDOM_QUALITY_REVIEW_V1.json',
         S/'manifests/CIHP_QUALITY_REVIEW_PLAN_V1.json',S/'taxonomy/CIHP_NATIVE_SOURCE_INVENTORY_DRAFT.yaml',
         S/'taxonomy/CIHP_COMMON_HP_PROPOSAL_V1.yaml',S/'reports/MHPV2_RANDOM_QUALITY_REVIEW_V1.csv',
         *list((S/'manifests/mhpv2_readable_v1').glob('*.json')),
         *[S/'scripts'/n for n in ['prepare_dataset_reassessment.py','build_model_variant_registry.py',
                                  'update_reassessment_documents.py','validate_dataset_reassessment.py']]]
    final={'run_id':run.name,'start_utc':json.loads((S/'provenance/DATASET_REASSESSMENT_ACTIVE_RUN.json').read_text())['start_utc'],
           'end_utc':result['end_utc'],'git_commit':'NOT_GIT_INITIALIZED','asset_hashes':{str(p.relative_to(S)):digest(p) for p in assets},
           'checkpoint_runs':[],'actual_operations':['Population manifest derivation from pinned prior inventory',
              '30 TRAIN RGB/native-GT decoding and diagnostic generation','Bounded source/Drive HTML metadata inspection',
              '51 synthetic/contract/population tests','Archives and current draft documentation update','Scoped preservation/links validation'],
           'existing_environment':'.venvs/mhpv2-stage0','no_new_model_run_hardware_claim':True,
           'source_snapshots':str((run/'sources').relative_to(S)),'status':result['preparation_status']}
    (run/'FINAL_RUN_MANIFEST.json').write_text(json.dumps(final,indent=2)+'\n')
    print(json.dumps({'preparation_status':result['preparation_status'],'tests_passed':tests['tests_run'],
        'YOLO_protected_files':protected_count,'checks_passed':sum(v=='PASS' for v in checks.values()),
        'failures':failures,'Stage0':'BLOCKED_WAITING_FOR_APPROVAL','remote_push':False}))
    if failures:sys.exit(1)


if __name__=='__main__':main()
