"""Compact operational progress only; no accuracy/speed ranking."""
from pathlib import Path
from datetime import datetime,timezone
import collections,json

S=Path(__file__).resolve().parents[1]


def main():
    root=S/json.loads((S/'provenance/FIRST_COHORT_BENCHMARK_ACTIVE.json').read_text())['run']
    result={'utc':datetime.now(timezone.utc).isoformat(),'components':[]}
    for execution in ['execution','continuation_20261019','execution_restored_detector_v1']:
        for model in ['YOLO26X_FROZEN','CPI_R50_CIHP','CPI_ConvNeXtB_CIHP']:
            directory=root/execution/model;manifest=directory/'RUN.json';ledger=directory/'FRAMES.jsonl'
            if not manifest.exists() and not ledger.exists():continue
            state=json.loads(manifest.read_text()) if manifest.exists() else {}
            counts=collections.Counter();errors=collections.Counter()
            if ledger.exists():
                for line in ledger.read_text().splitlines():
                    try:row=json.loads(line)
                    except json.JSONDecodeError:continue
                    counts[row['status']]+=1
                    if row['status']!='COMPLETE':errors[row.get('failure_type','UNKNOWN')]+=1
            result['components'].append(dict(execution=execution,model=model,status=state.get('status','NOT_STARTED'),counts=dict(counts),error_types=dict(errors)))
    for execution in ['execution','execution_restored_detector_v1']:
        completion=root/execution/'BENCHMARK_EXECUTION.json'
        if completion.exists():result[execution]=json.loads(completion.read_text())['status']
    print(json.dumps(result))
    with (root/'OPERATIONAL_PROGRESS.jsonl').open('a') as stream:stream.write(json.dumps(result)+'\n')


if __name__=='__main__':main()
