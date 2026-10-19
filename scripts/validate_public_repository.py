"""Validate published summaries and repository boundaries using only the standard library."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import re
import sys
import argparse

ROOT=Path(__file__).resolve().parents[1]
RUN='first-cohort-benchmark-20261016T094257313856Z'
R=ROOT/'provenance/RUN_MANIFESTS'/RUN


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before-clean-checkout',action='store_true',help='Permit only the not-yet-created clean-checkout evidence link during staging preflight')
    args=parser.parse_args()
    state=read(ROOT/'STUDY_STATE.json')
    assert state['benchmark_status']=='FINISHED_WITH_INCOMPLETE_SYSTEMS'
    assert not state['new_experiment_authorized']
    copied=read(ROOT/'publication/SOURCE_COPY_MANIFEST.json')['files']
    for row in copied:
        p=ROOT/row['public_path'];assert p.is_file() and sha(p)==row['sha256'],row['public_path']
    metrics=ROOT/'metrics'/RUN
    with (metrics/'QUALITY_RESULTS.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==8
    assert len({(x['system_id'],x['population'],x['matching_view']) for x in rows})==8
    for row in rows:
        assert row['status']=='INCOMPLETE' and row['main_score_eligible']=='False'
        assert all(row[k]=='' for k in ['Q_person_sem_GT','TP','FP','FN','localization_recall','localization_precision'])
        role=row['population'];view=row['matching_view'];model=row['system_id']
        report=read(ROOT/'cohorts/first_cpi_t3b/reports'/(role.upper()+'_'+view.upper()+'_REPORT.json'))
        provenance=report['publication_derivation']
        recorded={x['path']:x['sha256'] for x in read(R/'POST_EXPORT_VERIFICATION.json')['source_reports']}
        assert recorded[provenance['source_path']]==provenance['source_sha256']
        system=next(x for x in report['systems'] if x['system_id']==model)
        assert system['main_metrics'] is None and not system['main_score_eligible']
        for k in ['frames','G_loc','G_sem']:assert int(row[k])==system['population'][k]
        for key,name in [('frames_complete','completed'),('frames_failed','failed'),('frames_invalid','invalid'),('frames_not_attempted','not_attempted_or_unscheduled')]:
            assert int(row[key])==system['execution'][name]
        assert sum(int(row[k]) for k in ['frames_complete','frames_failed','frames_invalid','frames_not_attempted'])==int(row['frames'])
        assert float(row['IoU_threshold'])==report['GT_matching_threshold']==(.5 if view=='primary' else .75)
    with (metrics/'FAILURES.csv').open(newline='') as f:failures=list(csv.DictReader(f))
    assert len(failures)==len({(x['component'],x['image_id']) for x in failures})==566
    assert Counter(x['failure_kind'] for x in failures)=={'CUDA_OOM':565,'UNRESOLVED_INTERRUPTION':1}
    assert all(x['retries']=='0' for x in failures)
    final=read(R/'FINAL_BENCHMARK_VALIDATION.json')
    for name,expected in final['metrics'].items():assert sha(metrics/name)==expected
    assert state['semantic_mapping_evidence']=='ACCEPTED_WITH_INDIRECT_EVIDENCE'
    assert {(x['population'],int(x['frames']),int(x['G_loc']),int(x['G_sem'])) for x in rows}=={('main',4961,17434,17390),('reference',5000,17548,17504)}
    with (ROOT/'inventory/MODEL_INVENTORY.csv').open(newline='') as f:inventory=list(csv.DictReader(f))
    assert len(inventory)==29 and len({x['model_id'] for x in inventory})==29
    assert {x['model_id'] for x in inventory if x['first_cohort_status']=='INCOMPLETE'}=={'CPI_R50_CIHP','CPI_ConvNeXtB_CIHP'}
    required=['README.md','STUDY_STANDARD.md','EXPERIMENT_PROTOCOL.md','DATASET_DETAILS.md','REPORT.md','RESULTS_SUMMARY_TH.md','PRESENTATION_SUMMARY_TH.md','DATA_SCHEMA.md','AGENTS.md','HANDOFF.md','SETUP.md','REPRODUCIBILITY.md','ARTIFACTS.md','THIRD_PARTY_NOTICES.md','LICENSE.md','inventory/README.md','reports/HISTORY_INDEX.md']
    broken=[]
    for name in required:
        p=ROOT/name;assert p.is_file(),name
        for target in re.findall(r'\]\(([^\s)]+)\)',p.read_text()):
            if target.startswith(('http:','https:','mailto:','#')):continue
            if not (p.parent/target.split('#')[0]).exists():broken.append((name,target))
    deferred=[]
    if args.before_clean_checkout:
        deferred=[x for x in broken if x[1]=='publication/CLEAN_CHECKOUT_VALIDATION.json']
        broken=[x for x in broken if x not in deferred]
    assert not broken,broken
    candidates=[p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.relative_to(ROOT).parts]
    forbidden={'.pt','.pth','.safetensors','.npz','.npy','.zip','.tar','.jpg','.jpeg','.png'}
    secret_patterns=[re.compile(r'(?:ghp_|github_pat_|hf_)[A-Za-z0-9_]{20,}'),re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(r'X-Amz-Signature=[0-9a-fA-F]{20,}'),re.compile(r'https?://[^\s/]+:[^\s/]+@'),re.compile(r'''(?i)["']set-cookie["']\s*:'''),re.compile(r'(?i)[?&](?:x-amz-credential|x-amz-security-token|x-goog-signature|access_token|signature)=[A-Za-z0-9%+/_=-]{12,}'),re.compile(r'data:image/(?:jpeg|png);base64,[A-Za-z0-9+/]{50}')]
    for p in candidates:
        assert not p.is_symlink(),p
        assert p.stat().st_size<5_000_000,p
        assert not any(part in {'datasets','models','.venv','.venvs','parser_envs','third_party'} for part in p.relative_to(ROOT).parts),p
        # Only this first-party, count-derived chart may be a PNG.
        assert p.suffix.lower() not in forbidden or p.relative_to(ROOT)==Path('plots/first_cohort_completion.png'),p
        if p.suffix in {'.md','.txt','.json','.jsonl','.csv','.yaml','.yml','.py','.log'}:
            value=p.read_text(errors='replace')
            assert not any(pattern.search(value) for pattern in secret_patterns),('SECRET_OR_SIGNED_URL',str(p.relative_to(ROOT)))
    print(json.dumps(dict(status='PREPARED_PENDING_CLEAN_CHECKOUT' if args.before_clean_checkout else 'PASS',scope='PUBLIC_METADATA_AND_SYNTHETIC_BOUNDARIES_NOT_FULL_ARTIFACT_REPRODUCTION',
        original_copied_files=len(copied),quality_rows=8,failure_rows=566,inventory_records=29,strict_null_metrics=True,
        active_document_links='PASS',secrets_pattern_scan='PASS_NOT_A_GUARANTEE',no_datasets_weights_or_bulk_predictions=True,
        symlinks=0,benchmark_inference=False,deferred_links=deferred)))


if __name__=='__main__':main()
