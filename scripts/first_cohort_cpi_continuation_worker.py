"""Approved validation only. One model per isolated process, no retries or tuning."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import os
import sys
import traceback

S=Path(__file__).resolve().parents[1]
W=S.parent
sys.path.insert(0,str(S))


def write(path,data):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--model',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--continuation',type=Path,required=True)
    parser.add_argument('--continuation-sha256',required=True)
    args=parser.parse_args()
    from src.application_v2.policy import load_config,digest,field
    from src.application_v2.validation_launch import require_validation_authorization,_read
    from src.application_v2.artifacts import file_hash
    cfg=load_config(args.config,benchmark=True)
    require_validation_authorization(cfg,S)  # Before model imports, dataset reads or output creation.
    launch=cfg['validation_launch'];spec=cfg['first_cohort']['execution_spec']
    detector=args.model in spec['dependencies']
    if args.model not in (spec['dependencies'] if detector else spec['parser_systems']):
        raise ValueError('Model outside approved roster')
    system=(spec['dependencies'] if detector else spec['parser_systems'])[args.model]
    out=args.output.resolve()
    if not out.is_relative_to(S) or out.exists():raise ValueError('Fresh study output required')
    out.mkdir(parents=True)
    result=dict(status='INITIALIZING',model_id=args.model,start_utc=datetime.now(timezone.utc).isoformat(),
        config_sha256=digest(cfg),worker_sha256=file_hash(Path(__file__)),precision='FP32',model_retries=0)
    rows=[json.loads(line) for line in _read(S,launch['inputs']).read_text().splitlines()]
    if file_hash(args.continuation)!=args.continuation_sha256:raise ValueError('Continuation manifest changed')
    continuation=json.loads(args.continuation.read_text())
    if continuation['worker_sha256']!=file_hash(Path(__file__)) or continuation['source_config_sha256']!=digest(cfg) or args.model!=continuation['model_id']:raise ValueError('Continuation binding mismatch')
    if file_hash(S/continuation['original_ledger'])!=continuation['original_ledger_sha256']:raise ValueError('Original native evidence changed')
    prefix=[json.loads(line) for line in (S/continuation['original_ledger']).read_text().splitlines()]
    attempted={r['image_id'] for r in prefix}|set(continuation['unresolved_interrupted_ids'])
    selected=[row for row in rows if row['image_id'] not in attempted]
    if [row['image_id'] for row in selected]!=continuation['pending_image_ids'] or len(selected)!=continuation['pending_frames']:raise ValueError('Only predeclared unattempted continuation is permitted')
    rows=selected
    result.update(continuation_manifest_sha256=file_hash(args.continuation),image_retry_count=0)

    import numpy as np
    from PIL import Image
    import torch
    from src.application_v2.validation_data import read_rgb
    from src.application_v2.runner import ContractFailure
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    try:
        checkpoint=W/system['checkpoint_workspace_relative']
        if file_hash(checkpoint)!=system['checkpoint_sha256']:raise ValueError('Checkpoint bytes changed')
        result.update(checkpoint_sha256=file_hash(checkpoint),python=sys.version,torch=torch.__version__,
            cuda_runtime=torch.version.cuda,GPU=torch.cuda.get_device_name(0),autocast=False,TF32=False)
        if detector:
            os.environ['YOLO_CONFIG_DIR']=str(out/'settings')
            from ultralytics import YOLO
            model=YOLO(str(checkpoint))
            if model.task!='segment' or model.names[0].lower()!='person':raise ValueError('Frozen detector task mismatch')
            model.model.float().eval();parameters=model.model.parameters()
            options=field(cfg,system['settings_source'])
        else:
            import subprocess
            source=W/'third_party/human_parsing/CPI-Parser'
            revision=subprocess.run(['git','rev-parse','HEAD'],cwd=source,capture_output=True,text=True,check=True).stdout.strip()
            if revision!=system['source_commit']:raise ValueError('Native source revision changed')
            sys.path.insert(0,str(source))
            from mmcv import Config
            from mmdet.apis import init_detector,inference_detector
            native_config=W/system['native_config_workspace_relative']
            if file_hash(native_config)!=system['native_config_sha256']:raise ValueError('Native config bytes changed')
            native=Config.fromfile(str(native_config));native.model.test_cfg.save_root=str(out/'native');native.work_dir=str(out)
            model=init_detector(native,str(checkpoint),device='cuda:0').float().eval()
            state=torch.load(checkpoint,map_location='cpu')['state_dict'];model.load_state_dict(state,strict=True);del state
            if model.bbox_head.test_cfg.get('score_thr')!=field(cfg,system['score_threshold_source']):raise ValueError('Native threshold changed')
            parameters=model.parameters();result.update(source_commit=revision,resolved_config=native.pretty_text,
                native_config_sha256=file_hash(native_config),native_score_threshold=field(cfg,system['score_threshold_source']))
        if not all(p.dtype==torch.float32 for p in parameters):raise ValueError('FP32 required')
        result['checkpoint_loaded']=True;result['status']='RUNNING';write(out/'RUN.json',result)
    except Exception:
        result.update(status='LOAD_FAILURE',error=traceback.format_exc(),end_utc=datetime.now(timezone.utc).isoformat())
        write(out/'RUN.json',result)
        return 1
    rgb_root=out.parent/'source_rgb';rgb_root.mkdir(exist_ok=True)
    failures=0
    with (out/'FRAMES.jsonl').open('x') as ledger:
        for sample in rows:
            iid=sample['image_id'];w,h=sample['wh'];row=dict(image_id=iid,status='INITIALIZING')
            phase='SOURCE_READ'
            try:
                if sample['split']!='Validation':raise ValueError('Only approved validation population allowed')
                raw,rgb=read_rgb(W/launch['RGB_archive_workspace_relative'],sample)
                jpeg=rgb_root/(iid+'.jpg')
                if jpeg.exists():
                    if file_hash(jpeg)!=sample['RGB_sha256']:raise ValueError('Derived RGB view changed')
                else:
                    with jpeg.open('xb') as stream:stream.write(raw)
                phase='MODEL_INFERENCE'
                if detector:
                    with torch.inference_mode():
                        pred=model.predict(rgb[...,::-1].copy(),device=0,classes=[0],half=False,verbose=False,
                            imgsz=options['imgsz'],conf=options['conf'],iou=options['iou'],max_det=options['max_det'],
                            retina_masks=options['retina_masks'],save=False,project=str(out/'native'))[0]
                    phase='OUTPUT_CONTRACT'
                    boxes=pred.boxes.xyxy.cpu().numpy().astype('float32');scores=pred.boxes.conf.cpu().numpy().astype('float32')
                    masks=(pred.masks.data.cpu().numpy()>.5).astype('uint8') if pred.masks is not None else np.empty((0,h,w),'uint8')
                    if masks.shape!=(len(boxes),h,w):raise ContractFailure('Detector original grid invalid')
                    arrays=dict(boxes=boxes,scores=scores,masks=masks)
                    row['opportunities']=[dict(id=f'{iid}:YOLO:{i}',bbox=box.tolist(),score=float(scores[i])) for i,box in enumerate(boxes)]
                else:
                    previous=Path.cwd()
                    try:
                        os.chdir(jpeg.parent)
                        with torch.inference_mode():pred=inference_detector(model,jpeg.name)
                    finally:os.chdir(previous)
                    phase='OUTPUT_CONTRACT';boxes=np.vstack(pred).astype('float32')
                    paths=sorted((out/'native/val_parsing').glob(iid+'-*.png'),key=lambda p:int(p.stem.split('-')[-1]))
                    if boxes.shape!=(len(paths),5):raise ContractFailure('Native output count invalid')
                    planes=[]
                    for path in paths:
                        with Image.open(path) as image:image.load();mask=np.asarray(image).copy()
                        if mask.shape!=(h,w) or mask.dtype.kind not in 'iu' or int(mask.max())>=20:raise ContractFailure('Native mask contract invalid')
                        planes.append(mask)
                    masks=np.stack(planes) if planes else np.empty((0,h,w),'uint8')
                    arrays=dict(person_semantic_masks=masks,bboxes_xyxy_scores=boxes)
                if not all(np.isfinite(a).all() for a in arrays.values()):raise ContractFailure('Nonfinite output')
                path=out/(iid+'.npz');np.savez_compressed(path,**arrays)
                row.update(status='COMPLETE',artifact=str(path.relative_to(S)),artifact_sha256=file_hash(path),
                           input_sha256=sample['RGB_sha256'],original_wh=sample['wh'])
            except Exception:
                failures+=1
                row.update(status='FAILED' if phase=='MODEL_INFERENCE' else 'INVALID',failure_stage=phase,
                    failure_type='MODEL_SYSTEM_FAILURE' if phase=='MODEL_INFERENCE' else 'SHARED_DATA_ERROR' if phase=='SOURCE_READ' else 'CONTRACT_FAILURE',
                    error=traceback.format_exc(),retries=0)
                torch.cuda.empty_cache()  # Release failed-frame state; never re-run that image.
            ledger.write(json.dumps(row,allow_nan=False)+'\n');ledger.flush()
    result.update(status='COMPLETE' if not failures else 'INCOMPLETE',frames=len(rows),failed_frames=failures,
        end_utc=datetime.now(timezone.utc).isoformat())
    write(out/'RUN.json',result)
    return 0


if __name__=='__main__':raise SystemExit(main())
