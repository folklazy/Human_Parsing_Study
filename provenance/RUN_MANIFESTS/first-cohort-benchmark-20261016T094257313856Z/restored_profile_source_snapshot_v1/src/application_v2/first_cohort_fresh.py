"""Bounded TRAIN route: isolated native inference, packets, configured scoring/reporting."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import json
import subprocess
import sys
import numpy as np
from .artifacts import file_hash, commit_packet, resume_packet
from .contracts import stage_rate
from .evaluation import associate_native
from .first_cohort_replay import _arrays, _json, _inside
from .plan import first_cohort_plan
from .policy import digest, fingerprints, field
from .runner import ConfiguredRunner, ContractFailure
from .taxonomy import project_prediction
from .validation_packages import validate_packages


def _write(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def _idle():
    output = subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'],
                            check=True, text=True, capture_output=True).stdout
    if output.strip():
        raise RuntimeError('GPU occupied: defer without interrupting other jobs')


def score_committed_packet(runner, packet, fp, gt, model, iid, *, matching_view='primary'):
    """Read committed lossless output, then enter the configured scoring boundary."""
    record = resume_packet(packet, fp['inference'])
    cfg = runner.config
    context = cfg['scoring_contexts'][model][iid]
    if (record['system_id'], record['image_id'], record['checkpoint_sha256'], record['input_sha256']) != (
            model, iid, context['model_binding']['checkpoint_sha256'], context['input_binding']['input_sha256']):
        raise ValueError('Committed packet differs from registered scoring identity')
    mapping = json.loads((runner.study_root / cfg['cohort']['mapping']).read_text())
    with np.load(packet/'arrays.npz', allow_pickle=False) as data:
        native = data['canonical_semantic_masks'].copy()
    predictions = []
    for person, labels in zip(record['persons'], native):
        predictions.append(dict(id=person['identity']['final_person_id'], score=person['score'],
            evaluation_bbox=person['evaluation_bbox'],
            semantic=project_prediction(labels, mapping, native_taxonomy=context['model_binding']['native_taxonomy'])))
    return runner.score_frame(mapping, context['model_binding'], context['input_binding'], gt, predictions,
        lifecycle=dict(status='COMPLETE', events=[]), system_id=model, image_id=iid, matching_view=matching_view)


def execute_fresh_train(config_path, output):
    runner = ConfiguredRunner(config_path, mode='FRESH_TRAIN_INTEGRATION')
    cfg = runner.config
    cohort = cfg['first_cohort']
    first_cohort_plan(cfg, runner.study_root)
    if (cohort['entrypoint']['mode'] != 'DRY_RUN_AND_FRESH_TRAIN_INTEGRATION'
            or not cohort['execution_spec']['semantic_scoring_enabled']
            or cfg['authorization']['full_benchmark'] or cohort['engineering']['split'] != 'Training'):
        raise ValueError('Fresh TRAIN engineering execution is not authorized')
    study, workspace = runner.study_root, runner.study_root.parent
    output = Path(output).resolve()
    if not output.is_relative_to(study) or output.exists():
        raise ValueError('Use a fresh study-owned execution directory')
    output.mkdir(parents=True)
    spec = cohort['entrypoint']['fresh_inputs']
    inputs = _json(_inside(study, spec['path']), spec['sha256'])
    ids = cohort['engineering']['input_ids']
    if inputs['split'] != 'Training' or [v['image_id'] for v in inputs['images']] != ids:
        raise ValueError('Fresh inputs must exactly match accepted TRAIN image order')
    gt_manifest_spec = cohort['entrypoint']['GT_cache']
    gt_manifest = _json(_inside(study, gt_manifest_spec['path']), gt_manifest_spec['sha256'])
    if [row['image_id'] for row in gt_manifest['images']] != ids:
        raise ValueError('GT cache differs from accepted TRAIN population')
    package_result = validate_packages(cfg, study)
    _write(output/'VALIDATION_PACKAGE_BINDINGS.json', package_result)
    systems = {}
    for model, parser in cohort['execution_spec']['parser_systems'].items():
        systems[model] = dict(parser, kind='cpi', source_workspace_relative='third_party/human_parsing/CPI-Parser',
                             native_score_threshold=field(cfg, parser['score_threshold_source']))
    for model, detector in cohort['execution_spec']['dependencies'].items():
        systems[model] = dict(detector, kind='yolo', settings=field(cfg, detector['settings_source']))
    if len(systems) != len(cohort['models']) + 1:
        raise ValueError('Expected exact parser roster and one detector dependency')
    plan = dict(split='Training', full_benchmark=False, images=inputs['images'], systems=systems,
                config_path=str(Path(config_path).resolve().relative_to(study)), config_sha256=digest(cfg))
    plan_path = output/'WORKER_PLAN.json'
    _write(plan_path, plan)
    worker = study / cohort['entrypoint']['worker']['path']
    if file_hash(worker) != cohort['entrypoint']['worker']['sha256']:
        raise ValueError('Selected worker revision changed')
    results = {}
    order = list(cohort['execution_spec']['dependencies']) + cohort['models']
    attempts = []
    for model in order:
        _idle()
        system = systems[model]
        python = workspace / system['environment_workspace_relative'] / 'bin/python'
        command = [str(python), str(worker), '--plan', str(plan_path), '--kind', system['kind'],
                   '--model', model, '--output', str(output/model)]
        started = datetime.now(timezone.utc).isoformat()
        with (output/(model+'.log')).open('x') as log:
            try:
                done = subprocess.run(command, cwd=study, stdout=log, stderr=subprocess.STDOUT,
                    timeout=cohort['engineering']['worker_timeout_seconds'])
                exit_code = done.returncode
            except subprocess.TimeoutExpired:
                exit_code = 'TIMEOUT_NO_RETRY'
        record_path = output/model/'RUN.json'
        record = json.loads(record_path.read_text()) if record_path.exists() else dict(status='MISSING_WORKER_RECORD')
        attempts.append(dict(model_id=model, command=command, start_utc=started, end_utc=datetime.now(timezone.utc).isoformat(),
            exit_code=exit_code, status=record['status'], run_manifest=str(record_path.relative_to(study))))
        _write(output/'PROCESS_ATTEMPTS.json', attempts)
        if exit_code != 0 or record['status'] != 'PASS' or [v['image_id'] for v in record['images']] != ids:
            raise RuntimeError('Fresh model execution incomplete; see PROCESS_ATTEMPTS.json and worker log')
        results[model] = record
        print('['+model+'] fresh TRAIN: PASS', flush=True)
    detector_id = next(iter(cohort['execution_spec']['dependencies']))
    detector_frames = {r['image_id']:r for r in results[detector_id]['images']}
    primary, secondary, frames = [], [], []
    for row in gt_manifest['images']:
        iid, wh = row['image_id'], row['original_wh']
        gt_arrays = _arrays(_inside(study,row['artifact']), row['artifact_sha256'])
        gt = [dict(id=str(person['person_id']), bbox=person['bbox'], loc_eligible=person['G_loc'],
              sem_eligible=person['G_sem'], semantic=gt_arrays['person_semantic'][i], valid=gt_arrays['person_valid'][i])
              for i, person in enumerate(row['persons'])]
        detector = detector_frames[iid]
        _arrays(study/detector['artifact'],detector['artifact_sha256'])
        opportunities = detector['opportunities']
        for model in cohort['models']:
            context = cfg['scoring_contexts'][model][iid]
            if context['domain']['image_binding'] != row['image_binding']:
                raise ValueError('GT cache/context domain recipe mismatch')
            saved = next(r for r in results[model]['images'] if r['image_id']==iid)
            if saved['input_sha256'] != context['input_binding']['input_sha256'] or saved['wh'] != wh:
                raise ValueError('Fresh RGB input/context mismatch')
            def validate(arrays):
                masks, boxes = arrays['person_semantic_masks'], arrays['bboxes_xyxy_scores']
                if masks.shape != (len(boxes),wh[1],wh[0]) or boxes.shape != (len(masks),5):
                    raise ContractFailure('Native original-grid output mismatch')
                if masks.dtype.kind not in 'iu' or not set(np.unique(masks)) <= set(range(20)) or not np.isfinite(boxes).all():
                    raise ContractFailure('Native labels/coordinates invalid')
                return True
            lifecycle = runner.native_frame(iid, opportunities,
                lambda _: _arrays(study/saved['artifact'], saved['artifact_sha256']), validate)
            arrays = lifecycle.pop('native_output')
            if arrays is None or lifecycle['failure_events']:
                raise RuntimeError('Fresh native artifact failed lifecycle contract')
            masks, boxes = arrays['person_semantic_masks'], arrays['bboxes_xyxy_scores']
            instances = [dict(id=f'native:{i}',bbox=box[:4].tolist()) for i,box in enumerate(boxes)]
            association = associate_native(opportunities, instances, cohort['protocol']['matching']['association']['threshold'])
            persons, chosen = [], []
            for link in association['associations']:
                i = int(link['native_instance_id'].split(':')[-1])
                if not np.any(masks[i]):
                    continue
                opportunity = next(o for o in opportunities if o['id']==link['source_opportunity_id'])
                chosen.append(masks[i])
                persons.append(dict(identity=dict(origin='NATIVE_AND_YOLO', native_identity_supported=True,
                    native_instance_id=link['native_instance_id'], conditioning_source='YOLO',
                    source_opportunity_id=opportunity['id'], final_person_id=f'{model}:{iid}:{link["native_instance_id"]}'),
                    score=float(boxes[i,4]), conditioning_bbox=opportunity['bbox'],
                    evaluation_bbox=dict(xyxy=boxes[i,:4].tolist(), source='NATIVE_PARSER_BOX',
                        coordinate_convention='XYXY_HALF_OPEN',derivation_revision=file_hash(Path(__file__)))))
            final = np.stack(chosen) if chosen else np.empty((0,wh[1],wh[0]),'uint8')
            record = dict(schema_version='2.0', study_id='human_parsing_mhpv2', run_id=output.name,
                system_id=model, model_id=model, image_id=iid, source_track='T3B', mask_grid_space='ORIGINAL',
                original_wh=wh,label_catalog=list(range(20)),label_space='NATIVE',dataset_split='Training',
                adapter_revision=file_hash(Path(__file__)),execution_profile='FRESH_TRAIN_ENGINEERING_NO_RANKING',
                source_commit=systems[model]['source_commit'],checkpoint_sha256=systems[model]['checkpoint_sha256'],
                config_sha256=digest(cfg),input_sha256=context['input_binding']['input_sha256'],
                precision_profile=dict(source_native='FP32',autocast=False,TF32=False,latency_claim='NONE'),
                geometry_metadata=dict(native_artifact=saved['artifact'],native_artifact_sha256=saved['artifact_sha256'],
                    association=association,native_to_original=saved['native_to_original'],
                    RGB_source_sha256=saved['rgb_source_sha256']),
                native_identity_supported=True,native_instance_ids=[v['id'] for v in instances],persons=persons)
            fp = fingerprints(cfg,dict(native=saved['artifact_sha256'], yolo=detector['artifact_sha256'],
                                       source_input=record['input_sha256'],adapter=record['adapter_revision']))
            packet = output/'packets'/model/iid
            commit_packet(packet, record, final, fp, native_arrays=dict(native_boxes_scores=boxes, native_person_semantic_masks=masks))
            scores = {view: score_committed_packet(runner,packet,fp,gt,model,iid,matching_view=view)
                      for view in ['primary','secondary']}
            rates = dict(native=lifecycle['native_frame_completion_rate'],
                association=stage_rate('T3B_association','YOLO_opportunity',
                    [dict(unit_id=o['id'],eligible=True,status='COMPLETED') for o in opportunities]))
            base = dict(system_id=model,image_id=iid,execution_status='COMPLETE',failure_events=[],stage_rates=rates)
            primary.append(dict(base,score_result=scores['primary']))
            secondary.append(dict(base,score_result=scores['secondary']))
            frames.append(dict(base,status='PASS',native_instances=len(masks),YOLO_opportunities=len(opportunities),
                final_persons=len(persons),packet=str(packet.relative_to(study)),packet_scored_after_integrity_check=True))
    for view, rows in [('primary',primary),('secondary',secondary)]:
        report = runner.comparison_report(cfg['scoring_population'],rows,matching_view=view)
        report.update(purpose='TRAIN_ENGINEERING_SCORER_REPORTER_INTEGRATION_NOT_MODEL_RANKING',
                      matching_view=view, GT_matching_threshold=cfg['evaluation']['threshold' if view=='primary' else 'secondary_threshold'])
        if not all(r['main_score_eligible'] and r['execution']['completed']==len(ids) for r in report['systems']):
            raise RuntimeError('Configured reporting path incomplete')
        _write(output/(view.upper()+'_FRAME_SCORES.json'),rows)
        _write(output/(view.upper()+'_REPORT.json'),report)
    result = dict(status='PASS',scope='TWO_CPI_SYSTEMS_THREE_FIXED_TRAIN_IMAGES_ONLY',frames=frames,
        config_sha256=digest(cfg),model_loading=True,new_inference=True,semantic_scores_computed=True,
        thresholds=[cfg['evaluation']['threshold'],cfg['evaluation']['secondary_threshold']],
        validation_package_binding=package_result,validation_inference=False,GT_regenerated=False,
        ranking_generated=False,timing_ranking=False,full_benchmark=False,scientific_freeze=False)
    _write(output/'INTEGRATION.json',result)
    return result
