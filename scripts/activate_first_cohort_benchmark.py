"""Record the explicit user approval and freeze the two-system quality-only run."""
from pathlib import Path
import copy
import json
import sys
import yaml

S=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(S))
from src.application_v2.artifacts import file_hash
from src.application_v2.policy import digest,field,load_config


def main():
    run=S/json.loads((S/'provenance/FIRST_COHORT_BENCHMARK_ACTIVE.json').read_text())['run']
    approval=json.loads((run/'USER_APPROVAL.json').read_text())
    if not approval['approved'] or approval['approval']!='อนุมัติ':raise ValueError('Explicit approval missing')
    candidate=json.loads((S/approval['candidate']).read_text())
    assert file_hash(S/candidate['config_path'])==candidate['config_file_sha256']
    assert file_hash(S/candidate['decision_record'])==candidate['decision_file_sha256']
    before={row['path']:row for row in json.loads((run/'BEFORE.json').read_text())}
    allowed={'src/application_v2/runner.py','scripts/first_cohort_entrypoint.py'};changes=[]
    for path,expected in candidate['code_hashes'].items():
        actual=file_hash(S/path)
        if actual!=expected:
            if path not in allowed or before[path]['sha256']!=expected:raise ValueError('Unexpected candidate source change: '+path)
            changes.append(dict(path=path,before_sha256=expected,after_sha256=actual))
    patch=dict(reason='Measured registry digest0.766s per call across20,000 scoring calls; seal benchmark metadata once. Enable metadata-only validation-plan for an approved frozen config.',
        scientific_values_changed=False,changes=changes,new_module='src/application_v2/immutable_config.py',
        new_module_sha256=file_hash(S/'src/application_v2/immutable_config.py'))
    (run/'PRELAUNCH_ENGINEERING_PATCH.json').write_text(json.dumps(patch,indent=2)+'\n')
    cfg=load_config(S/candidate['config_path']);previous=copy.deepcopy(cfg)
    decisions=json.loads((S/cfg['decision_record']).read_text())
    cfg['status']='FROZEN';cfg['authorization']['full_benchmark']=True
    cfg['authorization']['allowed_modes'].append('VALIDATION_BENCHMARK')
    cfg['pending_score_decisions']=[]
    cfg['required_freeze_decisions'].append('FIRST_COHORT_VALIDATION_LAUNCH')
    cfg['readiness_artifact']='provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/VALIDATION.json'
    cfg['readiness_artifact_sha256']=file_hash(S/cfg['readiness_artifact'])
    launch=cfg['validation_launch'];launch.update(status='ACCEPTED',execution_authorized=True,
        approval='EXPLICIT_USER_APPROVAL_อนุมัติ',current_scope='APPROVED_REFERENCE_ONCE_TWO_SCORING_POPULATIONS_QUALITY_ONLY')
    launch['code_hashes']={path:file_hash(S/path) for path in launch['code_hashes']}
    launch['code_hashes']['src/application_v2/immutable_config.py']=file_hash(S/'src/application_v2/immutable_config.py')
    decisions['record_id']='APPLICATION_V2_DECISIONS_V10'
    superseded=[]
    for decision in decisions['decisions']:
        if decision['status']=='ACCEPTED_BY_USER':
            for path,old in list(decision['bindings'].items()):
                value=copy.deepcopy(field(cfg,path))
                if value!=old:
                    if path not in {'authorization.full_benchmark','authorization.allowed_modes'}:raise ValueError('Unexpected accepted policy change: '+path)
                    superseded.append(dict(decision=decision['id'],path=path,before=old,after=value))
                    decision['bindings'][path]=value
        if decision['id']=='FULL_BENCHMARK_EXECUTION':
            decision.update(status='ACCEPTED_BY_USER',evidence=str((run/'USER_APPROVAL.json').relative_to(S)),
                bindings={'authorization.full_benchmark':True,'status':'FROZEN'})
        if decision['id']=='FIRST_COHORT_VALIDATION_LAUNCH':
            decision.update(status='ACCEPTED_BY_USER',evidence=str((run/'USER_APPROVAL.json').relative_to(S)),bindings={'validation_launch':copy.deepcopy(launch)})
    cfg['decision_record']='provenance/APPLICATION_V2_DECISIONS_V10.json';cfg['decision_record_id']=decisions['record_id'];cfg['decision_record_sha256']=digest(decisions)
    for path,text in [('provenance/APPLICATION_V2_DECISIONS_V10.json',json.dumps(decisions,indent=2,ensure_ascii=False)+'\n'),
                      ('configs/application_v2_first_cohort_v11.yaml',yaml.safe_dump(cfg,sort_keys=False,allow_unicode=True))]:
        with (S/path).open('x') as stream:stream.write(text)
    assert cfg['first_cohort']['protocol']==previous['first_cohort']['protocol']
    load_config(S/'configs/application_v2_first_cohort_v11.yaml',benchmark=True)
    (run/'DECISION_ACTIVATION.json').write_text(json.dumps(dict(superseded_authorization_bindings=superseded,
        five_scientific_policies_unchanged=True,candidate_verified=True,approval_record=str((run/'USER_APPROVAL.json').relative_to(S))),indent=2)+'\n')
    print('Explicit approval recorded; V11 frozen configuration validated')


if __name__=='__main__':main()
