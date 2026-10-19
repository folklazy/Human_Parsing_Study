"""Isolated config-plan worker: one frozen detector or one native CPI, TRAIN only."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess
import sys
import traceback

S = Path(__file__).resolve().parents[1]
W = S.parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--kind', choices=['yolo', 'cpi'], required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    if plan['split'] != 'Training' or len(plan['images']) > 3 or plan['full_benchmark']:
        raise ValueError('Worker accepts only bounded TRAIN inputs')
    spec = plan['systems'][args.model]
    if spec['kind'] != args.kind:
        raise ValueError('Worker kind differs from selected system')
    out = args.output.resolve()
    if not out.is_relative_to(S) or out.exists():
        raise ValueError('Use a fresh study-owned worker output')
    out.mkdir(parents=True)
    result = dict(model_id=args.model, status='INITIALIZING', start_utc=datetime.now(timezone.utc).isoformat(),
                  plan_sha256=sha(args.plan), worker_sha256=sha(Path(__file__)), precision='FP32',
                  full_benchmark=False, images=[], checkpoint_loaded=False)
    try:
        import numpy as np
        from PIL import Image
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA unavailable')
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        checkpoint = W / spec['checkpoint_workspace_relative']
        if sha(checkpoint) != spec['checkpoint_sha256']:
            raise ValueError('Checkpoint bytes changed')
        result.update(checkpoint_sha256=sha(checkpoint), python=sys.version, torch=torch.__version__,
                      cuda_runtime=torch.version.cuda, GPU=torch.cuda.get_device_name(0),
                      autocast=False, TF32=False, device_visibility=os.environ.get('CUDA_VISIBLE_DEVICES'))
        if args.kind == 'yolo':
            os.environ['YOLO_CONFIG_DIR'] = str(out / 'settings')
            from ultralytics import YOLO
            import ultralytics
            model = YOLO(str(checkpoint))
            if model.task != 'segment' or model.names[0].lower() != 'person':
                raise ValueError('Frozen detector task/Person mapping invalid')
            model.model.float().eval()
            parameters = model.model.parameters()
            result['ultralytics'] = ultralytics.__version__
            result['settings'] = spec['settings']
        else:
            source = W / spec['source_workspace_relative']
            revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=source, capture_output=True, text=True, check=True).stdout.strip()
            if revision != spec['source_commit']:
                raise ValueError('Native source commit changed')
            sys.path.insert(0, str(source))
            from mmcv import Config
            from mmdet.apis import init_detector, inference_detector
            import mmcv
            native_config = W / spec['native_config_workspace_relative']
            if sha(native_config) != spec['native_config_sha256']:
                raise ValueError('Native config changed')
            cfg = Config.fromfile(str(native_config))
            cfg.model.test_cfg.save_root = str(out / 'native')
            cfg.work_dir = str(out)
            # Only output destinations are changed; all native processing retained.
            model = init_detector(cfg, str(checkpoint), device='cuda:0').float().eval()
            state = torch.load(checkpoint, map_location='cpu')['state_dict']
            model.load_state_dict(state, strict=True)
            del state
            if model.bbox_head.test_cfg.get('score_thr') != spec['native_score_threshold']:
                raise ValueError('Runtime native threshold differs from executable config')
            result.update(source_commit=revision, native_config_sha256=sha(native_config),
                          native_score_threshold=spec['native_score_threshold'], resolved_config=cfg.pretty_text,
                          mmcv=mmcv.__version__)
            parameters = model.parameters()
        if not all(p.dtype == torch.float32 for p in parameters):
            raise ValueError('Model parameters are not FP32')
        result['checkpoint_loaded'] = True
        for sample in plan['images']:
            iid = sample['image_id']
            if sample['split'] != 'Training':
                raise ValueError('Non-TRAIN sample rejected')
            jpeg, fixture = W / sample['jpeg_workspace_relative'], W / sample['input_workspace_relative']
            if sha(jpeg) != sample['rgb_source_sha256'] or sha(fixture) != sample['input_sha256']:
                raise ValueError('Source RGB bytes changed')
            with Image.open(jpeg) as image:
                image.load()
                rgb_decoded = np.asarray(image.convert('RGB')).copy()
            with np.load(fixture, allow_pickle=False) as arrays:
                rgb = arrays['rgb'].copy()
            if not np.array_equal(rgb, rgb_decoded):
                raise ValueError('Source JPEG pixels differ from bound RGB fixture')
            width, height = sample['wh']
            if rgb.shape != (height, width, 3):
                raise ValueError('Source geometry mismatch')
            if args.kind == 'yolo':
                options = spec['settings']
                with torch.inference_mode():
                    prediction = model.predict(rgb[..., ::-1].copy(), device=0, classes=[0], half=False,
                        verbose=False, imgsz=options['imgsz'], conf=options['conf'], iou=options['iou'],
                        max_det=options['max_det'], retina_masks=options['retina_masks'], save=False,
                        project=str(out / 'native'))[0]
                boxes = prediction.boxes.xyxy.cpu().numpy().astype('float32')
                scores = prediction.boxes.conf.cpu().numpy().astype('float32')
                masks = ((prediction.masks.data.cpu().numpy() > .5).astype('uint8')
                         if prediction.masks is not None else np.empty((0,height,width), 'uint8'))
                if masks.shape != (len(boxes), height, width):
                    raise ValueError('Detector original mask geometry invalid')
                payload = dict(masks=masks, boxes=boxes, scores=scores)
                extra = dict(opportunities=[dict(id=f'{iid}:YOLO:{i}', bbox=box.tolist(), score=float(scores[i]))
                                            for i, box in enumerate(boxes)])
            else:
                previous = Path.cwd()
                try:
                    os.chdir(jpeg.parent)
                    with torch.inference_mode():
                        raw = inference_detector(model, jpeg.name)
                finally:
                    os.chdir(previous)
                boxes = np.vstack(raw).astype('float32')
                paths = sorted((out/'native/val_parsing').glob(iid+'-*.png'), key=lambda p:int(p.stem.split('-')[-1]))
                if boxes.shape != (len(paths),5) or not np.isfinite(boxes).all():
                    raise ValueError('Native detection/mask count mismatch')
                planes = []
                for path in paths:
                    with Image.open(path) as image:
                        image.load(); mask = np.asarray(image).copy()
                    if mask.shape != (height,width) or mask.dtype.kind not in 'iu' or int(mask.max()) >= 20:
                        raise ValueError('Native output grid/class invalid')
                    planes.append(mask)
                masks = np.stack(planes) if planes else np.empty((0,height,width), 'uint8')
                payload = dict(person_semantic_masks=masks, bboxes_xyxy_scores=boxes)
                extra = dict(native_instances=len(masks))
            for array in payload.values():
                if not np.isfinite(array).all():
                    raise ValueError('Nonfinite native output')
            dest = out / (iid+'.npz')
            np.savez_compressed(dest, **payload)
            result['images'].append(dict(image_id=iid, wh=sample['wh'], input_sha256=sample['input_sha256'],
                rgb_source_sha256=sample['rgb_source_sha256'], artifact=str(dest.relative_to(S)),
                artifact_sha256=sha(dest), native_to_original='NATIVE_API_ORIGINAL_GRID_NO_ADDITIONAL_RESIZE', **extra))
            write(out/'RUN.json',result)
        torch.cuda.synchronize()
        result['status'] = 'PASS'
    except Exception:
        result['status'] = 'FAIL'
        result['error'] = traceback.format_exc()
    result['end_utc'] = datetime.now(timezone.utc).isoformat()
    write(out/'RUN.json',result)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
