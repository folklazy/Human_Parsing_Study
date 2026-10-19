"""Three TRAIN-frame integration only; isolated existing GPU environments.

No model scores, timing benchmark, training, download, or validation images.
Raw native FASHN outputs are retained beside a DRAFT YOLO-mask ownership view.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import json
import os
import sys
import subprocess

STUDY = Path(__file__).resolve().parents[1]
WORKSPACE = STUDY.parent
sys.path.insert(0, str(STUDY))


def config():
    from src.application_v2.policy import load_config
    value = load_config(STUDY / 'configs/application_v2.yaml')
    if not value['authorization'].get('bounded_train_inference') or 'BOUNDED_TRAIN' not in value['authorization']['allowed_modes']:
        raise ValueError('Bounded TRAIN scope not authorized')
    return value


def idle_gpu():
    result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'],
                            capture_output=True, text=True, check=True)
    if result.stdout.strip(): raise RuntimeError('GPU busy: defer; do not interrupt other workers')


def inputs(value):
    pilot = WORKSPACE / 'Human_Parsing_CCIHP_10_Image_Pilot'
    manifest = json.loads((pilot / 'configs/TEN_IMAGE_MANIFEST.json').read_text())
    rows = [r for r in manifest['images'] if r['image_id'] in value['bounded_train']['input_ids']]
    if len(rows) != value['bounded_train']['maximum_frames'] or any(r['split'] != 'Training' for r in rows):
        raise ValueError('Bounded frozen TRAIN input mismatch')
    return pilot, rows


def yolo(out):
    value = config(); idle_gpu()
    if 'YOLO26X_FROZEN' not in value['bounded_train']['models']: raise ValueError('Model not allowed')
    os.environ['YOLO_CONFIG_DIR'] = str(out / 'ultralytics_settings')
    import numpy as np
    import torch
    from ultralytics import YOLO
    from src.application_v2.artifacts import file_hash
    pilot, rows = inputs(value)
    frozen = json.loads((STUDY / 'manifests/YOLO26X_SOURCE.json').read_text())
    checkpoint = WORKSPACE / frozen['checkpoint_workspace_relative']
    if file_hash(checkpoint) != frozen['sha256']: raise ValueError('Frozen YOLO weights changed')
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    model = YOLO(str(checkpoint)); assert model.task == 'segment' and model.names[0].lower() == 'person'
    model.model.float().eval()
    options = value['bounded_train']['yolo']; result_rows = []
    for rec in rows:
        source = pilot / rec['input']
        if file_hash(source) != rec['input_sha256']: raise ValueError('TRAIN RGB fixture changed')
        with np.load(source, allow_pickle=False) as data: rgb = data['rgb'].copy()
        prediction = model.predict(rgb[..., ::-1].copy(), device=0, classes=[0], half=False, verbose=False,
                                   imgsz=options['imgsz'], conf=options['conf'], iou=options['iou'],
                                   max_det=options['max_det'], retina_masks=options['retina_masks'],
                                   save=False, project=str(out / 'yolo_native'))[0]
        boxes = prediction.boxes.xyxy.cpu().numpy(); scores = prediction.boxes.conf.cpu().numpy()
        h, w = rgb.shape[:2]
        masks = (prediction.masks.data.cpu().numpy() > .5).astype(np.uint8) if prediction.masks is not None else np.empty((0, h, w), np.uint8)
        if masks.shape != (len(boxes), h, w): raise ValueError('YOLO original-mask grid differs')
        ops = []
        for index, box in enumerate(boxes):
            margin = value['bounded_train']['crop_margin_per_side']; bw, bh = box[2:] - box[:2]
            crop = [max(0, int(np.floor(box[0] - bw * margin))), max(0, int(np.floor(box[1] - bh * margin))),
                    min(w, int(np.ceil(box[2] + bw * margin))), min(h, int(np.ceil(box[3] + bh * margin)))]
            if crop[2] <= crop[0] or crop[3] <= crop[1]: raise ValueError('Invalid predicted crop')
            ops.append({'id': f'{rec["image_id"]}:YOLO:{index}', 'bbox': box.tolist(), 'score': float(scores[index]), 'crop': crop})
        path = out / (rec['image_id'] + '_yolo.npz')
        np.savez_compressed(path, masks=masks, boxes=boxes, scores=scores)
        result_rows.append({'image_id': rec['image_id'], 'wh': [w, h], 'input': rec['input'], 'input_sha256': rec['input_sha256'],
                            'opportunities': ops, 'artifact': path.name, 'artifact_sha256': file_hash(path)})
    if sum(len(r['opportunities']) for r in result_rows) > value['bounded_train']['maximum_person_jobs']:
        raise RuntimeError('Smoke scope exceeded: preserve YOLO outputs, do not start parser jobs')
    result = {'status': 'BOUNDED_TRAIN_YOLO_PASS', 'checkpoint_sha256': frozen['sha256'], 'precision': 'FP32',
              'torch': torch.__version__, 'new_inference': True, 'benchmark': False, 'config': options, 'frames': result_rows}
    (out / 'YOLO.json').write_text(json.dumps(result, indent=2) + '\n')


def fashn(out):
    value = config(); idle_gpu()
    if 'FASHN_B4' not in value['bounded_train']['models']: raise ValueError('Model not allowed')
    os.environ['HF_HUB_OFFLINE'] = '1'; os.environ['TRANSFORMERS_OFFLINE'] = '1'
    import numpy as np
    import torch
    from src.adapters.fashn import FashnAdapter
    from src.application_v2.artifacts import file_hash, commit_packet, resume_packet
    from src.application_v2.policy import digest, fingerprints
    from src.application_v2.contracts import stage_rate
    source = WORKSPACE / 'third_party/human_parsing/fashn-human-parser'
    checkpoint = WORKSPACE / 'models/human_parsing/fashn/FASHN_B4'
    expected = 'e43c8c8a9b04f28798f0a4630cf18caa2cdb27a0d454fae43a5716e6f7078244'
    if file_hash(checkpoint / 'model.safetensors') != expected: raise ValueError('Official FASHN weights changed')
    adapter = FashnAdapter(source, checkpoint)
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    adapter.load(); assert all(p.dtype == torch.float32 for p in adapter.parser.model.parameters())
    descriptor = adapter.describe_model(); assert not descriptor['native_instances']
    pilot, _ = inputs(value); yolo_record = json.loads((out / 'YOLO.json').read_text()); summaries = []
    for frame in yolo_record['frames']:
        with np.load(pilot / frame['input'], allow_pickle=False) as data: rgb = data['rgb'].copy()
        with np.load(out / frame['artifact'], allow_pickle=False) as data: yolo_masks = data['masks'].astype(bool)
        w, h = frame['wh']; winners = np.full((h, w), -1, np.int16)
        for i in sorted(range(len(frame['opportunities'])), key=lambda j: (-frame['opportunities'][j]['score'], frame['opportunities'][j]['id'])):
            winners[(winners < 0) & yolo_masks[i]] = i
        native_arrays = {'conditioning_yolo_masks': yolo_masks}; persons = []; canonical = []; events = []
        for i, op in enumerate(frame['opportunities']):
            x0, y0, x1, y1 = op['crop']; crop_rgb = rgb[y0:y1, x0:x1].copy()
            prepared = adapter.preprocess(crop_rgb); raw = adapter.infer(prepared)
            native, _ = adapter.postprocess(raw, output_hw=(y1-y0, x1-x0)); native = native[0]
            native_arrays[f'native_crop_{i}'] = native.copy()
            events.append({'unit_id': op['id'], 'eligible': True, 'status': 'COMPLETED'})
            if not np.any(native > 0): continue
            original = np.zeros((h, w), np.uint8); original[y0:y1, x0:x1] = native
            owned = np.where(winners == i, original, 0).astype(np.uint8)
            canonical.append(owned)
            persons.append({'identity': {'origin': 'YOLO_CONDITIONED', 'native_identity_supported': False,
                                        'native_instance_id': None, 'conditioning_source': 'YOLO',
                                        'source_opportunity_id': op['id'], 'final_person_id': 'FASHN:' + op['id']},
                            'score': None, 'conditioning_score': op['score'], 'bbox': op['bbox'],
                            'crop': op['crop'], 'native_foreground_nonempty': True,
                            'owned_native_foreground_nonempty': bool(np.any(owned > 0))})
        masks = np.stack(canonical) if canonical else np.empty((0, h, w), np.uint8)
        revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=source, text=True, capture_output=True, check=True).stdout.strip()
        record = {'schema_version': '2.0', 'study_id': 'human_parsing_mhpv2', 'run_id': out.name,
                  'system_id': 'FASHN_YOLO_TRAIN_DRAFT', 'model_id': 'FASHN_B4', 'image_id': frame['image_id'],
                  'source_track': 'T3A', 'source_commit': revision, 'adapter_revision': file_hash(Path(__file__)),
                  'execution_profile': 'BOUNDED_TRAIN_FP32_NOT_TIMING_BENCHMARK', 'precision_profile': {'parameters': 'FP32', 'autocast': False, 'TF32': False},
                  'geometry_metadata': {'native_input_wh': descriptor['native_input_wh'], 'opportunities': frame['opportunities'],
                                        'ownership_policy': value['bounded_train']['ownership'], 'RGB_hard_mask_before_parser': False},
                  'checkpoint_sha256': expected, 'config_sha256': digest(value), 'input_sha256': frame['input_sha256'],
                  'original_wh': frame['wh'], 'mask_grid_space': 'ORIGINAL', 'label_space': 'NATIVE_OWNERSHIP_DERIVED',
                  'label_catalog': list(range(18)), 'native_identity_supported': False, 'native_instance_ids': None,
                  'persons': persons, 'dataset_split': 'TRAIN', 'common_taxonomy_projected': False,
                  'opportunity_completion_rate': stage_rate('parser_opportunity', 'person', events)}
        fp = fingerprints(value, {'RGB': frame['input_sha256'], 'YOLO_artifact': frame['artifact_sha256'], 'parser_checkpoint': expected})
        commit_packet(out / ('T3A_' + frame['image_id']), record, masks, fp, native_arrays=native_arrays)
        resume_packet(out / ('T3A_' + frame['image_id']), fp['inference'])
        summaries.append({'image_id': frame['image_id'], 'opportunities': len(events), 'completed': len(events), 'final_persons': len(persons)})
    adapter.cleanup()
    (out / 'FASHN.json').write_text(json.dumps({'status': 'BOUNDED_TRAIN_T3A_PASS', 'frames': summaries,
                                             'new_parser_inference': True, 'model_scores_generated': False}, indent=2) + '\n')


def verify(out):
    import numpy as np
    from src.application_v2.evaluation import associate_native
    from src.application_v2.artifacts import file_hash, commit_packet
    from src.application_v2.policy import digest, fingerprints
    value = config(); pilot, rows = inputs(value)
    registry = next(r for r in csv.DictReader((pilot / 'metrics/MODEL_PILOT_STATUS.csv').open()) if r['model_id'] == 'CPI_R50_CIHP')
    native_run = json.loads((pilot / registry['run_manifest']).read_text()); yolo_record = json.loads((out / 'YOLO.json').read_text())
    cases = []
    for frame in yolo_record['frames']:
        case = next(c for c in native_run['cases'] if c['image_id'] == frame['image_id'])
        if file_hash(pilot / case['artifact']) != case['artifact_sha256']: raise ValueError('Native CPI source changed')
        with np.load(pilot / case['artifact'], allow_pickle=False) as data:
            boxes = data['bboxes_xyxy_scores'].copy(); native_masks = data['person_semantic_masks'].copy()
        instances = [{'id': f'native:{i}', 'bbox': box[:4].tolist()} for i, box in enumerate(boxes)]
        association = associate_native(frame['opportunities'], instances, value['bounded_train']['association_threshold'])
        persons, masks = [], []
        for match in association['associations']:
            index = int(match['native_instance_id'].split(':')[-1])
            if not np.any(native_masks[index] > 0): continue
            masks.append(native_masks[index])
            persons.append({'identity': {'origin': 'NATIVE_AND_YOLO', 'native_identity_supported': True,
                                        'native_instance_id': match['native_instance_id'], 'conditioning_source': 'YOLO',
                                        'source_opportunity_id': match['source_opportunity_id'],
                                        'final_person_id': 'CPI_GATED:' + match['source_opportunity_id']},
                            'score': float(boxes[index, 4]), 'bbox': boxes[index, :4].tolist()})
        w, h = frame['wh']; masks = np.stack(masks) if masks else np.empty((0, h, w), np.uint8)
        record = {'schema_version': '2.0', 'study_id': 'human_parsing_mhpv2', 'run_id': out.name,
                  'system_id': 'CPI_SAVED_NATIVE_PLUS_ACTUAL_YOLO', 'model_id': 'CPI_R50_CIHP', 'image_id': frame['image_id'],
                  'source_track': 'T3B', 'source_commit': native_run['source_commit'], 'adapter_revision': file_hash(Path(__file__)),
                  'execution_profile': 'SAVED_NATIVE_CPI_WITH_NEW_YOLO_TRAIN_ASSOCIATION',
                  'precision_profile': {'native_parser': 'RECORDED_FP32_NOT_RERUN'},
                  'geometry_metadata': {'native_source_artifact': case['artifact_sha256'], 'conditioning': frame['opportunities'],
                                        'association': association},
                  'checkpoint_sha256': native_run['checkpoint_sha256'], 'config_sha256': digest(value), 'input_sha256': frame['input_sha256'],
                  'original_wh': frame['wh'], 'mask_grid_space': 'ORIGINAL', 'label_space': 'NATIVE', 'label_catalog': list(range(20)),
                  'native_identity_supported': True, 'native_instance_ids': [i['id'] for i in instances], 'persons': persons,
                  'dataset_split': 'TRAIN', 'model_scores_generated': False}
        fp = fingerprints(value, {'native_parser_artifact': case['artifact_sha256'], 'YOLO_artifact': frame['artifact_sha256']})
        commit_packet(out / ('T3B_' + frame['image_id']), record, masks, fp,
                      native_arrays={'source_native_person_masks': native_masks, 'source_native_boxes_scores': boxes})
        cases.append({'image_id': frame['image_id'], 'native_source_sha256': case['artifact_sha256'],
                      'conditioning_source': 'ACTUAL_FROZEN_YOLO_TRAIN_INFERENCE', 'association': association,
                      'native_parser_execution': 'REUSED_IMMUTABLE_SAVED_NATIVE_OUTPUT_NOT_RERUN'})
    (out / 'T3B_ASSOCIATION.json').write_text(json.dumps({'status': 'REAL_TRAIN_PREDICTION_ASSOCIATION_PASS', 'cases': cases,
                                                     'GT_used_for_association': False, 'live_native_parser_timing_validated': False}, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--role', choices=['yolo', 'fashn', 'verify'])
    parser.add_argument('--out', type=Path); args = parser.parse_args()
    if args.role:
        out = args.out.resolve()
        if not out.is_relative_to(STUDY / 'provenance/RUN_MANIFESTS'): raise ValueError('Owning-study output path required')
        existing = {'yolo': 'YOLO.json', 'fashn': 'FASHN.json', 'verify': 'T3B_ASSOCIATION.json'}[args.role]
        if (out / existing).exists(): raise FileExistsError('Completed role evidence is immutable; use a fresh run directory')
        if args.role == 'yolo' and any(out.glob('*_yolo.npz')):
            raise FileExistsError('Partial YOLO run exists; use a fresh run directory')
        if args.role == 'fashn' and any(out.glob('T3A_*')):
            raise FileExistsError('Existing parser packets are immutable; use a fresh run directory')
        if args.role == 'verify' and any(out.glob('T3B_*')):
            raise FileExistsError('Existing native-association packets are immutable')
        {'yolo': yolo, 'fashn': fashn, 'verify': verify}[args.role](out); return
    config(); idle_gpu()
    active = json.loads((STUDY / 'provenance/APPLICATION_V2_IMPLEMENTATION_ACTIVE.json').read_text())
    out = STUDY / active['run_path'] / ('bounded_train_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(exist_ok=False)
    for role, python in [('yolo', WORKSPACE / '.venv/bin/python'), ('fashn', WORKSPACE / '.venvs/fashn-stage0/bin/python'),
                         ('verify', WORKSPACE / '.venvs/mhpv2-stage0/bin/python')]:
        with (out / (role + '.log')).open('x') as log:
            done = subprocess.run([str(python), str(Path(__file__).resolve()), '--role', role, '--out', str(out)],
                                  cwd=STUDY, stdout=log, stderr=subprocess.STDOUT, timeout=300)
        if done.returncode: raise RuntimeError(f'{role} integration failed; see {out / (role + ".log")}')
    result = {'status': 'PASS_BOUNDED_TRAIN_INTEGRATION', 'input_ids': config()['bounded_train']['input_ids'],
              'new_YOLO_and_FASHN_inference': True, 'full_benchmark': False, 'validation_inference': False,
              'common_accuracy_scores_or_ranking': False, 'timing_benchmark': False,
              'T3A_native_contract_ownership_integration': 'PASS', 'T3B_actual_YOLO_plus_saved_native_association': 'PASS',
              'live_T3B_parser_runtime_validation': 'NOT_EXECUTED', 'protocol_frozen': False}
    (out / 'VALIDATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'run': str(out.relative_to(STUDY)), 'full_benchmark': False}))


if __name__ == '__main__': main()
