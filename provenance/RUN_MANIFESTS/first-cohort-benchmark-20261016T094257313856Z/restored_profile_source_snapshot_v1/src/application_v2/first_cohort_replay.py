"""Config-selected CPI T3b saved-TRAIN replay. No model loading or scoring API."""
from pathlib import Path
import ast
import json
import sys
import numpy as np
from .artifacts import file_hash, commit_packet, resume_packet
from .contracts import stage_rate
from .evaluation import associate_native
from .policy import digest, fingerprints
from .runner import ConfiguredRunner, ContractFailure


def _inside(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Replay input must stay inside its declared root')
    return path


def _json(path, expected):
    if file_hash(path) != expected:
        raise ValueError('Saved replay manifest hash mismatch')
    return json.loads(path.read_text())


def _arrays(path, expected):
    if file_hash(path) != expected:
        raise ValueError('Saved replay array hash mismatch')
    with np.load(path, allow_pickle=False) as arrays:
        return {key: arrays[key].copy() for key in arrays.files}


def _native_threshold(run):
    if run.get('native_score_threshold') is not None:
        return run['native_score_threshold']
    values = [ast.literal_eval(node.value) for node in ast.walk(ast.parse(run['resolved_config']))
              if isinstance(node, ast.keyword) and node.arg == 'score_thr']
    # Resolved MMDetection configs repeat the same value at detector/head levels.
    if not values or len(set(values)) != 1:
        raise ValueError('Cannot identify one unambiguous saved native score threshold')
    return values[0]


def replay_saved_train(config_path, output):
    runner = ConfiguredRunner(config_path, mode='SAVED_TRAIN_REPLAY')
    cfg = runner.config
    cohort = cfg['first_cohort']
    entry = cohort['entrypoint']
    if entry['mode'] != 'DRY_RUN_AND_SAVED_TRAIN_REPLAY' or entry['model_loading'] or cohort['execution_spec']['actual_inference_enabled']:
        raise ValueError('Saved TRAIN replay is not enabled by this configuration')
    if cohort['execution_spec'].get('semantic_scoring_enabled') is not False or cfg['authorization']['full_benchmark']:
        raise ValueError('Replay profile must disable semantic scoring and full benchmark')
    study = runner.study_root
    workspace = study.parent
    spec = entry['replay_manifest']
    data = _json(_inside(study, spec['path']), spec['sha256'])
    if data['split'] != 'Training' or data['new_inference'] or data['scoring_enabled']:
        raise ValueError('Only unscored saved TRAIN inputs are permitted')
    ids = data['input_ids']
    if len(ids) > data['maximum_frames'] or ids != cohort['engineering']['input_ids'] or any(i not in cfg['bounded_train']['input_ids'] for i in ids):
        raise ValueError('Replay exceeds the accepted TRAIN population')
    if [row['image_id'] for row in data['images']] != ids:
        raise ValueError('Replay image rows must match the declared ordered population')
    for row in data['images']:
        if row['input']['split'] != 'Training' or set(row['parsers']) != set(cohort['models']):
            raise ValueError('Replay input split/roster mismatch')
    yolo_path = _inside(workspace, data['yolo']['path_workspace_relative'])
    yolo = _json(yolo_path, data['yolo']['sha256'])
    yolo_frames = {row['image_id']: row for row in yolo['frames']}
    output = Path(output).resolve()
    if not output.is_relative_to(study) or output.exists():
        raise ValueError('Use a fresh replay output directory inside the study')
    output.mkdir(parents=True)
    results = []
    for row in data['images']:
        iid, sample = row['image_id'], row['input']
        source = _arrays(_inside(workspace / 'Human_Parsing_CCIHP_10_Image_Pilot', sample['input']), sample['input_sha256'])
        wh = [source['rgb'].shape[1], source['rgb'].shape[0]]
        if wh != sample['wh']:
            raise ValueError('Source RGB original-grid dimensions changed')
        detector = yolo_frames[iid]
        if detector['input_sha256'] != sample['input_sha256']:
            raise ValueError('YOLO and parser input identities differ')
        if file_hash(yolo_path.parent / detector['artifact']) != detector['artifact_sha256']:
            raise ValueError('Saved detector artifact changed')
        opportunities = detector['opportunities']
        for model in cohort['models']:
            native_spec = cohort['execution_spec']['parser_systems'][model]
            saved = row['parsers'][model]
            source_run = _json(_inside(workspace, saved['manifest_workspace_relative']), saved['manifest_sha256'])
            if source_run['checkpoint_sha256'] != native_spec['checkpoint_sha256'] or source_run['source_commit'] != native_spec['source_commit'] or source_run['model_id'] != model or source_run['precision'] != 'FP32':
                raise ValueError('Saved native output differs from the selected model/checkpoint/precision')
            expected = cohort['protocol']['matching']['native_score_thresholds'][model]
            if _native_threshold(source_run) != expected:
                raise ValueError('Saved native score filter differs from executable configuration')
            artifact = _inside(workspace, saved['artifact_workspace_relative'])
            def worker(_):
                return _arrays(artifact, saved['artifact_sha256'])
            def validate(arrays):
                masks, boxes = arrays['person_semantic_masks'], arrays['bboxes_xyxy_scores']
                if masks.ndim != 3 or masks.shape[1:] != (wh[1], wh[0]) or boxes.shape != (len(masks), 5):
                    raise ContractFailure('Saved native original-grid/count contract mismatch')
                if masks.dtype.kind not in 'iu' or not set(np.unique(masks)) <= set(range(20)) or not np.isfinite(boxes).all():
                    raise ContractFailure('Saved native ID/score contract mismatch')
                return True
            native = runner.native_frame(iid, opportunities, worker, validate)
            if native['native_output'] is None:
                results.append(dict(system_id=model, image_id=iid, status='INCOMPLETE', lifecycle=native))
                continue
            arrays = native.pop('native_output')
            masks, boxes = arrays['person_semantic_masks'], arrays['bboxes_xyxy_scores']
            instances = [{'id': f'native:{i}', 'bbox': b[:4].tolist()} for i, b in enumerate(boxes)]
            association = associate_native(opportunities, instances, cohort['protocol']['matching']['association']['threshold'])
            persons, chosen = [], []
            for link in association['associations']:
                i = int(link['native_instance_id'].split(':')[-1])
                if not np.any(masks[i]):
                    continue  # Native-empty output does not fabricate a final person.
                opportunity = next(o for o in opportunities if o['id'] == link['source_opportunity_id'])
                chosen.append(masks[i])
                persons.append(dict(identity=dict(origin='NATIVE_AND_YOLO', native_identity_supported=True,
                    native_instance_id=link['native_instance_id'], conditioning_source='YOLO',
                    source_opportunity_id=opportunity['id'], final_person_id=f'{model}:{iid}:{link["native_instance_id"]}'),
                    score=float(boxes[i, 4]), conditioning_bbox=opportunity['bbox'],
                    evaluation_bbox=dict(xyxy=boxes[i, :4].tolist(), source='NATIVE_PARSER_BOX',
                        coordinate_convention='XYXY_HALF_OPEN', derivation_revision=file_hash(Path(__file__)))))
            final = np.stack(chosen) if chosen else np.empty((0, wh[1], wh[0]), np.uint8)
            record = dict(schema_version='2.0', mask_grid_space='ORIGINAL', original_wh=wh,
                label_catalog=list(range(20)), label_space='NATIVE', study_id='human_parsing_mhpv2',
                run_id=output.name, system_id=model, model_id=model, image_id=iid,
                adapter_revision=file_hash(Path(__file__)), execution_profile='SAVED_TRAIN_T3B_REPLAY_NO_INFERENCE_OR_SCORING',
                source_track='T3B', source_commit=native_spec['source_commit'],
                checkpoint_sha256=native_spec['checkpoint_sha256'], config_sha256=digest(cfg), input_sha256=sample['input_sha256'],
                geometry_metadata=dict(native_artifact_workspace_relative=saved['artifact_workspace_relative'],
                    native_artifact_sha256=saved['artifact_sha256'], association=association,
                    RGB_source_sha256=sample['rgb_source_sha256'],
                    saved_resolved_config_sha256=digest(source_run['resolved_config'])),
                precision_profile=dict(source_native='FP32', replay='CPU_SAVED_ARRAYS', latency_claim='NONE'),
                native_identity_supported=True, native_instance_ids=[v['id'] for v in instances], persons=persons, dataset_split='Training')
            fp = fingerprints(cfg, dict(native=saved['artifact_sha256'], yolo=detector['artifact_sha256'],
                                        source_input=sample['input_sha256'], adapter=record['adapter_revision']))
            dest = output / model / iid
            commit_packet(dest, record, final, fp, native_arrays={'native_boxes_scores': boxes})
            resume_packet(dest, fp['inference'])  # Packet integrity only; not workflow resume/scoring.
            events = [{'unit_id': o['id'], 'eligible': True, 'status': 'COMPLETED'} for o in opportunities]
            results.append(dict(system_id=model, image_id=iid, status='COMPLETE', lifecycle=native,
                native_instances=len(instances), YOLO_opportunities=len(opportunities), final_persons=len(persons),
                association=association, association_completion_rate=stage_rate('T3B_association', 'YOLO_opportunity', events),
                packet=str(dest.relative_to(study)), score_result=None))
    result = dict(status='PASS' if all(r['status'] == 'COMPLETE' for r in results) else 'INCOMPLETE',
        scope='SAVED_TRAIN_LIFECYCLE_ASSOCIATION_AND_PACKET_PATH_ONLY_NOT_FRESH_MODEL_EXECUTION',
        frames=results, config_path=str(Path(config_path).resolve().relative_to(study)), config_sha256=digest(cfg),
        new_inference=False, semantic_scores_computed=False, full_benchmark=False,
        full_validation_contexts_ready=False, fresh_joint_execute_path='NOT_TESTED')
    result['heavyweight_frameworks_imported'] = [name for name in ['torch', 'ultralytics', 'mmcv', 'mmdet'] if name in sys.modules]
    with (output / 'REPLAY.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    return result
