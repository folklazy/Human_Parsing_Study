"""Create explicitly derived compact views of existing report JSON, never re-score data."""
from pathlib import Path
import argparse
import copy
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
REL='provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/execution_restored_detector_v1'

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-study',type=Path,required=True)
    args=parser.parse_args();out=ROOT/'cohorts/first_cpi_t3b/reports';out.mkdir(exist_ok=False)
    manifest=[]
    for role in ['MAIN','REFERENCE']:
        for view in ['PRIMARY','SECONDARY']:
            name=role+'_'+view+'_REPORT.json';source=args.source_study/REL/name
            original=json.loads(source.read_text());compact=copy.deepcopy(original)
            for row,before in zip(compact['systems'],original['systems']):
                diagnostics=row.pop('operational_diagnostics')
                row['operational_diagnostics_summary']=dict(failure_event_count=diagnostics['failure_event_count'],
                    native_stage_ledger_rows=len(diagnostics['native_stage_ledgers']),
                    full_events_and_ledgers='EXTERNAL_SOURCE_REPORT; failures retained separately in FAILURES.csv')
                for key in ['system_id','status','main_score_eligible','main_metrics','execution','population','success_only_diagnostic']:
                    assert row[key]==before[key],key
            compact['publication_derivation']=dict(status='DERIVED_FROM_EXISTING_CANONICAL_RESULTS_NO_RESCORING',
                source_path=REL+'/'+name,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                source_bytes=source.stat().st_size,source_raw_report_in_git=False,
                change='Only bulk operational diagnostics replaced by counts; score/denominator/completeness fields unchanged')
            target=out/name
            with target.open('x') as f:json.dump(compact,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
            manifest.append(dict(source_path=REL+'/'+name,source_sha256=compact['publication_derivation']['source_sha256'],
                public_path=str(target.relative_to(ROOT)),public_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                retained_score_fields_equal=True))
    (ROOT/'publication/PUBLIC_REPORT_VIEWS.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_report_schema='Unmodified external canonical report',public_schema='COMPACT_DERIVED_VIEW_1.0',reports=manifest),indent=2)+'\n')
