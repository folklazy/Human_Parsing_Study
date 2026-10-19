"""Restore only the shared detector's pre-inference environment failure, no parser retries."""
from pathlib import Path
from datetime import datetime,timezone
import copy,json,sys,yaml

S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S))
from src.application_v2.policy import load_config,digest
from src.application_v2.artifacts import file_hash
from src.application_v2.validation_launch import require_validation_authorization,validation_plan


def main():
    run=S/json.loads((S/'provenance/FIRST_COHORT_BENCHMARK_ACTIVE.json').read_text())['run'];initial=run/'execution'
    if not (initial/'BENCHMARK_EXECUTION.json').exists() and not (run/'INITIAL_TRIAL_TERMINATION.json').exists():raise ValueError('Initial trial must have terminal evidence before restoring the shared detector')
    cfg=load_config(S/'configs/application_v2_first_cohort_v11.yaml',benchmark=True);original=copy.deepcopy(cfg)
    decisions=json.loads((S/cfg['decision_record']).read_text());event=json.loads((run/'SHARED_ENVIRONMENT_EVENT.json').read_text())
    if event['image_inference_attempts']!=0 or (initial/'YOLO26X_FROZEN/FRAMES.jsonl').exists():raise ValueError('Restoration may not retry detector image inference')
    inputs=[json.loads(line) for line in (S/cfg['validation_launch']['inputs']['path']).read_text().splitlines()];expected=[r['image_id'] for r in inputs];components={}
    supplied=json.loads((run/'NATIVE_COMPONENTS_FOR_RESTORATION.json').read_text()) if (run/'NATIVE_COMPONENTS_FOR_RESTORATION.json').exists() else None
    for model in cfg['first_cohort']['models']:
        manifest=S/supplied[model]['manifest'] if supplied else initial/model/'RUN.json'
        ledger=S/supplied[model]['ledger'] if supplied else initial/model/'FRAMES.jsonl';state=json.loads(manifest.read_text())
        rows=[json.loads(line) for line in ledger.read_text().splitlines()]
        if state['status'] not in {'COMPLETE','INCOMPLETE'} or [r['image_id'] for r in rows]!=expected:raise ValueError('Native component incomplete population or unresolved worker: '+model)
        components[model]=dict(manifest=str(manifest.relative_to(S)),manifest_sha256=file_hash(manifest),ledger=str(ledger.relative_to(S)),ledger_sha256=file_hash(ledger))
    recovery=dict(initial_trial=str(initial.relative_to(S)),prior_YOLO_image_attempts=0,CPI_inference_retries=0,
        native_source_config_sha256=digest(original),native_components=components,detector_worker='scripts/first_cohort_yolo_bootstrap_worker.py',
        environment_packages_changed=False,scientific_values_changed=False,execution_driver='scripts/restore_first_cohort_detector.py',
        rationale='Initial detector aborted before model import because evaluator validation imported unavailable SciPy. CPU validates config; isolated detector verifies a frozen receipt.')
    cfg['validation_launch']['detector_infrastructure_restoration']=recovery
    cfg['validation_launch']['execution_driver']='scripts/restore_first_cohort_detector.py'
    for path in ['scripts/first_cohort_yolo_bootstrap_worker.py','scripts/restore_first_cohort_detector.py']:
        cfg['validation_launch']['code_hashes'][path]=file_hash(S/path)
    for decision in decisions['decisions']:
        if decision['id']=='FIRST_COHORT_VALIDATION_LAUNCH':decision['bindings']['validation_launch']=copy.deepcopy(cfg['validation_launch'])
    decisions['record_id']='APPLICATION_V2_DECISIONS_V11'
    decisions['decisions'].append(dict(id='FIRST_COHORT_SHARED_ENVIRONMENT_RESTORATION',status='ACCEPTED_BY_USER',
        basis='Implementation detail within the already approved run; no YOLO image previously attempted, no CPI retries, no new model/input/precision/threshold policy',
        evidence=str((run/'USER_APPROVAL.json').relative_to(S)),bindings={'validation_launch.detector_infrastructure_restoration':recovery}))
    cfg['required_freeze_decisions'].append('FIRST_COHORT_SHARED_ENVIRONMENT_RESTORATION')
    cfg['decision_record']='provenance/APPLICATION_V2_DECISIONS_V11.json';cfg['decision_record_id']=decisions['record_id'];cfg['decision_record_sha256']=digest(decisions)
    assert cfg['first_cohort']['protocol']==original['first_cohort']['protocol']
    for path,text in [('provenance/APPLICATION_V2_DECISIONS_V11.json',json.dumps(decisions,indent=2,ensure_ascii=False)+'\n'),
                      ('configs/application_v2_first_cohort_v12.yaml',yaml.safe_dump(cfg,sort_keys=False,allow_unicode=True))]:
        with (S/path).open('x') as stream:stream.write(text)
    cfg=load_config(S/'configs/application_v2_first_cohort_v12.yaml',benchmark=True);require_validation_authorization(cfg,S)
    plan=validation_plan(cfg,S);(run/'RESTORED_PROFILE_LAUNCH_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
    record=dict(status='RESTORED_SHARED_DETECTOR_PROFILE_FROZEN',timestamp_utc=datetime.now(timezone.utc).isoformat(),
        original_invalid_trial_retained=True,config='configs/application_v2_first_cohort_v12.yaml',config_sha256=file_hash(S/'configs/application_v2_first_cohort_v12.yaml'),
        decision=cfg['decision_record'],decision_sha256=file_hash(S/cfg['decision_record']),restoration=recovery,
        user_approval=str((run/'USER_APPROVAL.json').relative_to(S)),scientific_policies_unchanged=True,CPI_inference_rerun=False,model_frame_retry_count=0)
    (run/'RESTORED_PROFILE_FREEZE.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(status=record['status'],CPI_inference_rerun=False,YOLO_previous_image_attempts=0)))


if __name__=='__main__':main()
