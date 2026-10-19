"""Population-specific contexts and launch preparation; no inference during planning."""
from pathlib import Path
import copy
import json
from .artifacts import file_hash
from .policy import digest
from .validation_packages import validate_packages


def _read(study, spec):
    path = (study / spec['path']).resolve()
    if not path.is_relative_to(study.resolve()) or file_hash(path) != spec['sha256']:
        raise ValueError('Launch input path/hash mismatch')
    return path


def package_data(config, study):
    validate_packages(config, study)
    manifest = study / config['validation_context_packages']['manifest']
    directory = manifest.parent
    images = [json.loads(line) for line in (directory/'IMAGE_BINDINGS.jsonl').read_text().splitlines()]
    templates = json.loads((directory/'MODEL_CONTEXT_TEMPLATES.json').read_text())
    return images, templates


def population_view(config, images, templates, role):
    """Pure metadata view; it does not grant execution or scoring authorization."""
    if role not in {'main','reference'}:
        raise ValueError('Unknown population role')
    rows = [r for r in images if role=='reference' or r['main']]
    cfg = copy.deepcopy(config)
    cfg['population_role'] = role
    cfg['scoring_context'] = None
    cfg['scoring_population'] = [{k:r[k] for k in ['image_id','G_loc','G_sem']} for r in rows]
    cfg['scoring_contexts'] = {model:{r['image_id']:{**template, 'input_binding':r['input_binding'],
        'domain':{**template['domain'],'image_binding':r['image_domain_binding']}} for r in rows}
        for model,template in templates.items()}
    from .contexts import validate_context_registry
    validate_context_registry(cfg)
    return cfg


def validation_plan(config, study):
    launch = config['validation_launch']
    if launch['scope'] != 'TWO_CPI_T3B_QUALITY_ONLY' or launch['inference_population'] != 'reference':
        raise ValueError('Launch scope or inference population changed')
    if launch['scoring_populations'] != ['main','reference'] or not launch['one_inference_per_system_image']:
        raise ValueError('One reference inference population with two scoring populations required')
    if launch['model_retries'] != 0 or launch['precision'] != 'FP32':
        raise ValueError('No retries or precision changes are authorized')
    decisions = json.loads((study/config['decision_record']).read_text())
    proposals = [r for r in decisions['decisions'] if r['id']=='FIRST_COHORT_VALIDATION_LAUNCH']
    if len(proposals)!=1 or proposals[0]['bindings'].get('validation_launch')!=launch:
        raise ValueError('Launch specification lacks its exact decision/proposal binding')
    for path,checksum in launch['code_hashes'].items():
        if file_hash(study/path)!=checksum:
            raise ValueError('Launch code changed after preparation: '+path)
    images,templates=package_data(config,study)
    inputs=[json.loads(line) for line in _read(study,launch['inputs']).read_text().splitlines()]
    if [r['image_id'] for r in inputs]!=[r['image_id'] for r in images]:
        raise ValueError('Inference inputs must equal the ordered reference population exactly')
    for sample,row in zip(inputs,images):
        if sample['split']!='Validation' or sample['RGB_sha256']!=row['input_binding']['input_sha256'] or sample['wh']!=row['input_binding']['original_wh']:
            raise ValueError('Input identity/geometry differs from scoring bindings')
        if sample['GT_allowed_as_model_input']:
            raise ValueError('GT cannot be an inference input')
    counts={}
    for role in launch['scoring_populations']:
        view=population_view(config,images,templates,role)
        rows=view['scoring_population']
        counts[role]=dict(images=len(rows),G_loc=sum(r['G_loc'] for r in rows),G_sem=sum(r['G_sem'] for r in rows),
            population_sha256=digest(rows),per_image_contexts=len(rows)*len(templates))
    roster=config['first_cohort']['models']
    return dict(status='PREPARED_NOT_AUTHORIZED' if not launch['execution_authorized'] else 'AUTHORIZED_CONFIG_REQUIRES_RUNTIME_GATE',
        parser_systems=roster,detector_dependencies=list(config['first_cohort']['execution_spec']['dependencies']),
        track=config['first_cohort']['track'],unique_RGB_inputs=len(inputs),
        detector_frame_jobs=len(inputs),parser_frame_jobs=len(inputs)*len(roster),
        populations=counts,shared_score_reuse='ONLY_IDENTICAL_IMAGE_CONTEXT_AND_MATCHING_VIEW',
        primary_matching=config['evaluation']['threshold'],secondary_matching=config['evaluation']['secondary_threshold'],
        native_score_thresholds=config['first_cohort']['protocol']['matching']['native_score_thresholds'],
        failure_policy=config['primary_reporting_policy']['main_score'],precision=launch['precision'],
        timing_or_VRAM_ranking=False,model_loading=False,validation_inference=False,
        full_benchmark=config['authorization']['full_benchmark'],launch_spec_sha256=digest(launch))


def require_validation_authorization(config, study):
    launch=config.get('validation_launch',{})
    if (config.get('status')!='FROZEN' or not config['authorization']['full_benchmark']
        or not launch.get('execution_authorized') or launch.get('status')!='ACCEPTED'
        or 'VALIDATION_BENCHMARK' not in config['authorization']['allowed_modes']):
        raise ValueError('Validation benchmark NOT AUTHORIZED: explicit separate user approval and frozen execution config required')
    decisions=json.loads((study/config['decision_record']).read_text())
    for name in ['FULL_BENCHMARK_EXECUTION','FIRST_COHORT_VALIDATION_LAUNCH']:
        rows=[r for r in decisions['decisions'] if r['id']==name and r['status']=='ACCEPTED_BY_USER']
        if len(rows)!=1:
            raise ValueError('Missing accepted execution decision: '+name)
    accepted=next(r for r in decisions['decisions'] if r['id']=='FIRST_COHORT_VALIDATION_LAUNCH')
    if accepted['bindings'].get('validation_launch')!=launch:
        raise ValueError('Accepted launch decision differs from executable config')
    validation_plan(config,study)


def population_reports(config, images, templates, frames, *, matching_view='primary'):
    """One score per system/image/view, separate strict reports per population."""
    from .contexts import check_report_binding
    from .comparison import summarize_comparison
    reports={}
    for role in ['main','reference']:
        view=population_view(config,images,templates,role)
        ids={r['image_id'] for r in view['scoring_population']}
        rows=[r for r in frames if r['image_id'] in ids]
        check_report_binding(view,view['scoring_population'],rows,matching_view=matching_view)
        definition=dict(cohort=config['first_cohort'],population_role=role,
            population_sha256=digest(view['scoring_population']),matching_view=matching_view,
            threshold=config['evaluation']['threshold' if matching_view=='primary' else 'secondary_threshold'])
        revision=digest(definition)
        reports[role]=summarize_comparison(dict(comparison_id=config['first_cohort']['comparison_id']+':'+role+':'+revision[:12],
            definition_sha256=revision),view['scoring_population'],config['first_cohort']['models'],rows,config['primary_reporting_policy'])
        reports[role].update(population_role=role,matching_view=matching_view,GT_matching_threshold=definition['threshold'])
    return reports
