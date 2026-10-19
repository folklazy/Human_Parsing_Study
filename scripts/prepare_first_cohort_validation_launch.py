"""Metadata-only launch candidate. Does not grant approval or read dataset pixels."""
from pathlib import Path
import copy
import json
import sys
import yaml

S=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(S))
from src.application_v2.policy import load_config,digest
from src.application_v2.artifacts import file_hash


def main():
    run=S/json.loads((S/'provenance/FIRST_COHORT_VALIDATION_LAUNCH_ACTIVE.json').read_text())['run']
    cfg=load_config(S/'configs/application_v2_first_cohort_v9.yaml')
    package=(S/cfg['validation_context_packages']['manifest']).parent
    images=[json.loads(line) for line in (package/'IMAGE_BINDINGS.jsonl').read_text().splitlines()]
    archive_manifest=S/'manifests/CIHP_DATASETNINJA_ARCHIVE_MANIFEST_V1.json'
    archive=json.loads(archive_manifest.read_text())
    inventory=S/archive['member_inventory']
    if file_hash(inventory)!=archive['member_inventory_sha256']:raise ValueError('Prior TAR inventory changed')
    members={r['path']:r for r in (json.loads(line) for line in inventory.read_text().splitlines()) if r['path'].startswith('validation/img/')}
    inputs=[]
    for row in images:
        iid=row['image_id'];source=members['validation/img/'+iid+'.jpg'];binding=row['input_binding']
        if source['sha256']!=binding['input_sha256']:raise ValueError('Image ID alone is insufficient: RGB hash mismatch')
        inputs.append(dict(image_id=iid,split='Validation',wh=binding['original_wh'],RGB_sha256=source['sha256'],
            decoded_RGB_sha256=binding['decoded_RGB_sha256'],RGB_member=source['path'],RGB_tar_data_offset=source['data_offset'],
            RGB_bytes=source['bytes'],GT_allowed_as_model_input=False))
    target=run/'VALIDATION_INPUTS.jsonl'
    with target.open('x') as stream:
        for row in inputs:stream.write(json.dumps(row,separators=(',',':'))+'\n')
    code=[*S.glob('src/application_v2/*.py'),*[S/p for p in ['scripts/first_cohort_entrypoint.py','scripts/first_cohort_validation_worker.py',
        'scripts/first_cohort_gpu_worker.py','scripts/prepare_first_cohort_validation_launch.py']]]
    cfg['validation_launch']=dict(status='PROPOSED',execution_authorized=False,scope='TWO_CPI_T3B_QUALITY_ONLY',
        inference_population='reference',scoring_populations=['main','reference'],one_inference_per_system_image=True,
        model_retries=0,precision='FP32',inputs=dict(path=str(target.relative_to(S)),sha256=file_hash(target)),
        RGB_archive_workspace_relative=archive['archive_workspace_relative'],GT_archive_workspace_relative='datasets/CCIHP_icip.zip',
        RGB_inventory=dict(path=str(inventory.relative_to(S)),sha256=file_hash(inventory)),
        worker='scripts/first_cohort_validation_worker.py',code_hashes={str(p.relative_to(S)):file_hash(p) for p in code},
        approval='PENDING_EXPLICIT_USER_APPROVAL_NOT_GRANTED_BY_PROGRESS_REVIEW',
        current_scope='LAUNCH_PREPARATION_ONLY_NO_VALIDATION_INFERENCE')
    # Keep all previously accepted bindings intact; the new launch decision is PROPOSED.
    decisions=copy.deepcopy(json.loads((S/cfg['decision_record']).read_text()))
    decisions['record_id']='APPLICATION_V2_DECISIONS_V9'
    decisions['decisions'].append(dict(id='FIRST_COHORT_VALIDATION_LAUNCH',status='PROPOSED',
        rationale='User accepts bounded integration closure; explicitly states benchmark execution not yet approved',
        bindings={'validation_launch':cfg['validation_launch']}))
    cfg['status']='VALIDATION_LAUNCH_CANDIDATE_NOT_FROZEN'
    cfg['decision_record']='provenance/APPLICATION_V2_DECISIONS_V9.json'
    cfg['decision_record_id']=decisions['record_id'];cfg['decision_record_sha256']=digest(decisions)
    assert not cfg['authorization']['full_benchmark']
    for path,text in [('provenance/APPLICATION_V2_DECISIONS_V9.json',json.dumps(decisions,indent=2,ensure_ascii=False)+'\n'),
                      ('configs/application_v2_first_cohort_v10.yaml',yaml.safe_dump(cfg,sort_keys=False,allow_unicode=True))]:
        with (S/path).open('x') as stream:stream.write(text)
    load_config(S/'configs/application_v2_first_cohort_v10.yaml')
    print(json.dumps(dict(status='PREPARED_NOT_APPROVED',unique_RGB_inputs=len(inputs),config='configs/application_v2_first_cohort_v10.yaml',model_loading=False)))


if __name__=='__main__':main()
