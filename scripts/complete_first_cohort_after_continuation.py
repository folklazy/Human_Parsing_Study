"""Finish only the already approved run, from disjoint continuation evidence."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys,time

S=Path(__file__).resolve().parents[1]


def main():
    R=S/json.loads((S/'provenance/FIRST_COHORT_BENCHMARK_ACTIVE.json').read_text())['run']
    continuation=R/'continuation_20261019/CPI_ConvNeXtB_CIHP/RUN.json'
    while True:
        state=json.loads(continuation.read_text()) if continuation.exists() else {}
        if state.get('status') in {'COMPLETE','INCOMPLETE'}:break
        if state.get('status')=='LOAD_FAILURE':raise RuntimeError('Continuation load failure; preserve evidence and stop')
        time.sleep(10)
    commands=[
        [sys.executable,str(S/'scripts/merge_first_cohort_native_continuation.py')],
        [sys.executable,str(S/'scripts/activate_first_cohort_detector_restoration.py')],
        [sys.executable,str(S/'scripts/restore_first_cohort_detector.py'),'--config',str(S/'configs/application_v2_first_cohort_v12.yaml'),
         '--output',str(R/'execution_restored_detector_v1')],
        [sys.executable,str(S/'scripts/publish_first_cohort_benchmark_results.py')]]
    for index,command in enumerate(commands):
        record=dict(stage_index=index,command=command,status='RUNNING',utc=datetime.now(timezone.utc).isoformat())
        (R/'CONTINUATION_FINALIZATION_STATUS.json').write_text(json.dumps(record,indent=2)+'\n')
        with (R/('FINALIZATION_STAGE_'+str(index)+'.log')).open('x') as log:
            process=subprocess.run(command,cwd=S,stdout=log,stderr=subprocess.STDOUT)
        record.update(status='COMPLETE' if process.returncode==0 else 'FAILED',exit_code=process.returncode,utc=datetime.now(timezone.utc).isoformat())
        (R/'CONTINUATION_FINALIZATION_STATUS.json').write_text(json.dumps(record,indent=2)+'\n')
        if process.returncode:raise RuntimeError('Stage failed; inspect FINALIZATION_STAGE_'+str(index)+'.log')
    print('APPROVED_FIRST_COHORT_FINISHED_NO_FURTHER_EXPERIMENT')


if __name__=='__main__':main()
