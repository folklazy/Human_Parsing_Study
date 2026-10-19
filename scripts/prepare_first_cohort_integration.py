"""Versioned preparation binding; never activates validation or a full benchmark."""
from pathlib import Path
import copy
import json
import sys
import yaml

S = Path(__file__).resolve().parents[1]
W = S.parent
sys.path.insert(0,str(S))
from src.application_v2.artifacts import file_hash
from src.application_v2.policy import digest, load_config


def main():
    run = S / json.loads((S/'provenance/FIRST_COHORT_INTEGRATION_ACTIVE.json').read_text())['run']
    cfg = load_config(S/'configs/application_v2_first_cohort_v8.yaml')
    decisions = json.loads((S/cfg['decision_record']).read_text())
    previous = copy.deepcopy(cfg)
    package = S/'provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/validation_contexts_v1/MANIFEST.json'
    manifest = json.loads(package.read_text())
    cfg['validation_context_packages'] = dict(role='PREPARATION_ONLY',execution_authorized=False,
        manifest=str(package.relative_to(S)),manifest_sha256=file_hash(package),
        populations={role:{key:manifest['populations'][role][key if key in ['images','contexts'] else key+'_per_system'] for key in ['images','contexts','G_loc','G_sem']}
                     for role in ['main','reference']})
    pilot = W/'Human_Parsing_CCIHP_10_Image_Pilot'
    pilot_manifest = pilot/'configs/TEN_IMAGE_MANIFEST.json'
    records = {r['image_id']:r for r in json.loads(pilot_manifest.read_text())['images']}
    ids = cfg['first_cohort']['engineering']['input_ids']
    images = []
    for iid in ids:
        r = records[iid]
        images.append(dict(image_id=iid,split=r['split'],wh=r['wh'],input_sha256=r['input_sha256'],
            rgb_source_sha256=r['rgb_source_sha256'], input_workspace_relative=str((pilot/r['input']).relative_to(W)),
            jpeg_workspace_relative=str((pilot/'outputs/inputs'/f'{iid}.jpg').relative_to(W))))
    fresh = run/'FRESH_TRAIN_INPUTS.json'
    fresh.write_text(json.dumps(dict(split='Training',images=images,source_manifest_sha256=file_hash(pilot_manifest)),indent=2)+'\n')
    gt = S/'provenance/RUN_MANIFESTS/first-cohort-policy-acceptance-20261016T034543760531Z/GT_TRAIN_RECONSTRUCTION/MANIFEST.json'
    cohort = cfg['first_cohort']
    cohort['status'] = 'TRAIN_INTEGRATION_ENABLED_VALIDATION_BOUND_NOT_AUTHORIZED'
    cohort['entrypoint'].update(mode='DRY_RUN_AND_FRESH_TRAIN_INTEGRATION',model_loading=True,
        fresh_inputs=dict(path=str(fresh.relative_to(S)),sha256=file_hash(fresh)),
        GT_cache=dict(path=str(gt.relative_to(S)),sha256=file_hash(gt)),
        worker=dict(path='scripts/first_cohort_gpu_worker.py',sha256=file_hash(S/'scripts/first_cohort_gpu_worker.py')))
    cohort['execution_spec'].update(actual_inference_enabled=True,semantic_scoring_enabled=True)
    cohort['engineering']['semantic_scoring_integration'] = 'TRAIN_ONLY_NO_RANKING_OR_TUNING'
    cfg['authorization']['allowed_modes'].append('FRESH_TRAIN_INTEGRATION')
    cfg['status'] = 'BOUNDED_TRAIN_INTEGRATION_NOT_FROZEN'
    cfg['pending_score_decisions'] = ['FULL_BENCHMARK_EXECUTION_APPROVAL_AFTER_INTEGRATION_REVIEW']
    for contexts in cfg['scoring_contexts'].values():
        for context in contexts.values():
            context['scope'] = 'ACCEPTED_TRAIN_ENGINEERING_SCORING_ONLY_NOT_VALIDATION_EXECUTION'
    # Existing numeric policies are untouched. Update only user-authorized integration bindings.
    for decision in decisions['decisions']:
        if decision['status']=='ACCEPTED_BY_USER':
            from src.application_v2.policy import field
            decision['bindings'] = {key:copy.deepcopy(field(cfg,key)) for key in decision['bindings']}
    decisions['record_id'] = 'APPLICATION_V2_DECISIONS_V8'
    decisions['decisions'].extend([
        dict(id='VALIDATION_PACKAGE_PREPARATION_BINDING',status='ACCEPTED_BY_USER',
             evidence='User requested binding existing full validation packages while full_benchmark=false',
             bindings={'validation_context_packages':cfg['validation_context_packages']}),
        dict(id='FRESH_TRAIN_SCORING_INTEGRATION',status='ACCEPTED_BY_USER',
             evidence='User authorized two CPI plus frozen YOLO fresh TRAIN and configured scorer/reporter integration; no ranking/tuning',
             bindings={'first_cohort.engineering.semantic_scoring_integration':cohort['engineering']['semantic_scoring_integration']})])
    cfg['decision_record'] = 'provenance/APPLICATION_V2_DECISIONS_V8.json'
    cfg['decision_record_id'] = decisions['record_id']
    cfg['decision_record_sha256'] = digest(decisions)
    for rel,data in [('provenance/APPLICATION_V2_DECISIONS_V8.json',json.dumps(decisions,indent=2,ensure_ascii=False)+'\n'),
                     ('configs/application_v2_first_cohort_v9.yaml',yaml.safe_dump(cfg,sort_keys=False,allow_unicode=True))]:
        with (S/rel).open('x') as stream:stream.write(data)
    check = load_config(S/'configs/application_v2_first_cohort_v9.yaml')
    _ = check
    # Document exactly which policy paths remained identical; no semantic reapproval.
    unchanged = ['mapping','domain','population','matching','runtime']
    assert all(previous['first_cohort']['protocol'][key]==cohort['protocol'][key] for key in unchanged)
    (run/'CONFIG_LINEAGE.json').write_text(json.dumps(dict(old_config='configs/application_v2_first_cohort_v8.yaml',
        new_config='configs/application_v2_first_cohort_v9.yaml',unchanged_protocol_sections=unchanged,
        validation_GT_regenerated=False,full_benchmark=False),indent=2)+'\n')
    print('V9 config + V8 decision: bound; full_benchmark=false')


if __name__=='__main__':main()
