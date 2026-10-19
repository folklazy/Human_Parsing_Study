"""Bounded real saved TRAIN-output integration, never model inference or ranking."""
from pathlib import Path
import sys
import json
import csv
from datetime import datetime, timezone
import numpy as np

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))
from src.application_v2.policy import load_config, digest, fingerprints
from src.application_v2.contracts import validate_frame
from src.application_v2.artifacts import commit_packet, resume_packet, file_hash
from src.application_v2.evaluation import associate_native


def ident(origin, final_id, native_id=None, opportunity=None):
    return {'origin': origin, 'native_identity_supported': native_id is not None,
            'native_instance_id': native_id, 'conditioning_source': 'YOLO' if origin == 'NATIVE_AND_YOLO' else
            'ORACLE' if origin == 'ORACLE_INPUT' else None,
            'source_opportunity_id': opportunity, 'final_person_id': final_id}


def main():
    config = load_config(STUDY / 'configs/application_v2.yaml')
    active = json.loads((STUDY / 'provenance/APPLICATION_V2_IMPLEMENTATION_ACTIVE.json').read_text())
    output = STUDY / active['run_path'] / ('saved_train_replay_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(exist_ok=False)
    pilot = STUDY.parent / 'Human_Parsing_CCIHP_10_Image_Pilot'
    manifest = json.loads((pilot / 'configs/TEN_IMAGE_MANIFEST.json').read_text())
    inputs = manifest['images'][:3]
    if manifest.get('split', '').lower() not in {'train', 'training', 'train_only'} or any(i['split'] != 'Training' for i in inputs):
        raise ValueError('Only TRAIN replay authorized')
    rows = {r['model_id']: r for r in csv.DictReader((pilot / 'metrics/MODEL_PILOT_STATUS.csv').open())}
    results = []
    for model in ['FASHN_B4', 'SCHP_R101_LIP', 'CPI_R50_CIHP']:
        run = json.loads((pilot / rows[model]['run_manifest']).read_text())
        for source in inputs:
            image_id = source['image_id']; case = next(c for c in run['cases'] if c['image_id'] == image_id)
            artifact = pilot / case['artifact']
            if file_hash(artifact) != case['artifact_sha256']:
                raise ValueError('Saved native output integrity failed')
            wh = case['wh']; persons = []; supported = model == 'CPI_R50_CIHP'; native_ids = [] if supported else None
            native_arrays = {}
            with np.load(artifact, allow_pickle=False) as arrays:
                if model == 'FASHN_B4':
                    masks = np.empty((0, wh[1], wh[0]), np.uint8)
                    native_arrays['scene_semantic_mask'] = arrays['semantic_mask'].copy(); track = 'T1'
                elif model == 'SCHP_R101_LIP':
                    crop = case['geometry']['crop_xyxy']; native = arrays['semantic_mask'].copy()
                    native_arrays['native_crop_mask'] = native
                    masks = np.zeros((1, wh[1], wh[0]), np.uint8)
                    x0, y0, x1, y1 = crop
                    if native.shape != (y1-y0, x1-x0): raise ValueError('Native crop coordinate mismatch')
                    masks[0, y0:y1, x0:x1] = native
                    persons = [{'identity': ident('ORACLE_INPUT', 'final:0', opportunity='oracle:' + str(case['geometry']['target_human_id'])),
                                'score': None, 'crop_xyxy': crop}]; track = 'T2'
                else:
                    masks = arrays['person_semantic_masks'].copy(); boxes = arrays['bboxes_xyxy_scores'].copy()
                    native_ids = [f'native_index:{i}' for i in range(len(masks))]
                    native_arrays['native_boxes_scores'] = boxes
                    persons = [{'identity': ident('NATIVE_MODEL', f'final:{i}', native_id=native_ids[i]),
                                'score': float(boxes[i, 4]), 'native_array_index': i} for i in range(len(masks))]; track = 'T1'
            count = int(rows[model]['native_classes_including_background'])
            record = {'schema_version': '2.0', 'study_id': 'human_parsing_mhpv2', 'run_id': output.parent.name,
                      'system_id': model + '_SAVED_REPLAY', 'model_id': model, 'image_id': image_id,
                      'adapter_revision': file_hash(Path(__file__)), 'execution_profile': 'SAVED_TRAIN_REPLAY_NO_INFERENCE',
                      'source_track': track, 'mask_grid_space': 'ORIGINAL', 'original_wh': wh,
                      'source_commit': run['source_commit'], 'label_space': 'NATIVE',
                      'geometry_metadata': case.get('geometry') or {'export_grid': 'ORIGINAL', 'source_run_manifest': rows[model]['run_manifest'],
                                                                 'native_input_geometry': 'RESOLVE_FROM_PINNED_RUN_CONFIG'},
                      'precision_profile': {'parameters': run['precision'], 'source': 'RECORDED_NATIVE_RUN_NOT_NEW_EXECUTION'},
                      'label_catalog': list(range(count)), 'persons': persons,
                      'native_identity_supported': supported, 'native_instance_ids': native_ids,
                      'checkpoint_sha256': run['checkpoint_sha256'], 'config_sha256': digest(config),
                      'input_sha256': file_hash(pilot / 'outputs/inputs' / (image_id + '.npz')),
                      'source_native_artifact_sha256': case['artifact_sha256'], 'source_run_manifest': rows[model]['run_manifest'],
                      'dataset_split': 'TRAIN', 'new_inference': False, 'metric_scores_generated': False}
            validate_frame(record, masks)
            fp = fingerprints(config, {'native_artifact': case['artifact_sha256'], 'source_run': file_hash(pilot / rows[model]['run_manifest']),
                                       'oracle_crop': case.get('geometry', {}).get('crop_xyxy')})
            directory = output / (model + '_' + image_id)
            commit_packet(directory, record, masks, fp, native_arrays=native_arrays)
            resume_packet(directory, fp['inference'])
            results.append({'model': model, 'image_id': image_id, 'source_track': track, 'status': 'CONTRACT_ARTIFACT_ROUNDTRIP_PASS'})
            if supported:
                # Predictions-only association integration with synthetic conditioning.
                # Explicitly NOT frozen-YOLO inference or live T3b validation.
                opportunities = [{'id': f'SYNTHETIC_OP:{i}', 'bbox': box[:4].tolist()} for i, box in enumerate(boxes)]
                native = [{'id': native_ids[i], 'bbox': box[:4].tolist()} for i, box in enumerate(boxes)]
                association = associate_native(opportunities, native, config['evaluation']['threshold'])
                for a in association['associations']:
                    i = native_ids.index(a['native_instance_id'])
                    persons[i]['identity'] = ident('NATIVE_AND_YOLO', f'gated:{i}', a['native_instance_id'], a['source_opportunity_id'])
                record = {**record, 'source_track': 'T3B', 'system_id': model + '_SYNTHETIC_ASSOCIATION_REPLAY',
                          'persons': persons, 'conditioning_inputs_kind': 'SYNTHETIC_NOT_YOLO',
                          'association': association}
                if len(association['associations']) != len(native): raise ValueError('Self-box association fixture failed')
                validate_frame(record, masks)
                association_fp = fingerprints(config, {'native_artifact': case['artifact_sha256'],
                                                        'conditioning_opportunities': opportunities,
                                                        'source_track': 'T3B_SYNTHETIC_ASSOCIATION'})
                commit_packet(output / (model + '_' + image_id + '_synthetic_association'), record, masks, association_fp)
    evidence = {'status': 'PASS_SAVED_TRAIN_CONTRACT_INTEGRATION', 'input_ids': [i['image_id'] for i in inputs],
                'saved_cases': results, 'native_and_oracle_and_semantic_interfaces_checked': True,
                'source_arrays_unchanged': True, 'new_inference': False, 'model_scores_generated': False,
                'live_T3a_validated': False, 'live_T3b_validated': False,
                'limitation': 'T3b association uses explicit synthetic opportunities; no claim of YOLO-conditioned execution.'}
    (output / 'VALIDATION.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({'saved_train_cases_pass': len(results), 'synthetic_association_cases': 3,
                      'new_inference': False, 'live_T3_validation': 'NOT_EXECUTED'}))


if __name__ == '__main__': main()
