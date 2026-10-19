"""Frozen YOLO inference with a CPU-validated receipt; no evaluator dependencies."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json
import os
import struct
import sys
import traceback

S=Path(__file__).resolve().parents[1];W=S.parent


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()


def write(path,value):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temporary.replace(path)


def verified_receipt(path,expected):
    if sha(path)!=expected:raise ValueError('CPU validation receipt changed')
    receipt=json.loads(path.read_text())
    if receipt['status']!='APPROVED_FROZEN_CPU_VALIDATED' or receipt['model_id']!='YOLO26X_FROZEN':raise ValueError('Authorized detector receipt required')
    for source in receipt['frozen_files']:
        p=(S/source['path']).resolve()
        if not p.is_relative_to(S) or sha(p)!=source['sha256']:raise ValueError('Frozen authorization/input source changed')
    if receipt['worker_sha256']!=sha(Path(__file__)):raise ValueError('Detector worker source changed')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--receipt-sha256',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    receipt=verified_receipt(args.receipt,args.receipt_sha256)
    out=args.output.resolve()
    if not out.is_relative_to(S) or out.exists():raise ValueError('Fresh study-owned output required')
    out.mkdir(parents=True)
    record=dict(status='INITIALIZING',model_id='YOLO26X_FROZEN',precision='FP32',config_sha256=receipt['config_content_sha256'],
        receipt_sha256=sha(args.receipt),worker_sha256=sha(Path(__file__)),model_retries=0,start_utc=datetime.now(timezone.utc).isoformat())
    try:
        import numpy as np
        from PIL import Image
        from io import BytesIO
        import torch
        os.environ['YOLO_CONFIG_DIR']=str(out/'settings')
        from ultralytics import YOLO
        checkpoint=W/receipt['checkpoint_workspace_relative']
        if sha(checkpoint)!=receipt['checkpoint_sha256']:raise ValueError('Frozen YOLO checkpoint changed')
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        model=YOLO(str(checkpoint));model.model.float().eval()
        if model.task!='segment' or model.names[0].lower()!='person':raise ValueError('Frozen segmentation/Person mapping invalid')
        if not all(p.dtype==torch.float32 for p in model.model.parameters()):raise ValueError('FP32 parameters required')
        record.update(status='RUNNING',checkpoint_loaded=True,checkpoint_sha256=sha(checkpoint),torch=torch.__version__,
            python=sys.version,cuda_runtime=torch.version.cuda,GPU=torch.cuda.get_device_name(0),autocast=False,TF32=False)
        write(out/'RUN.json',record)
    except Exception:
        record.update(status='LOAD_FAILURE',error=traceback.format_exc());write(out/'RUN.json',record);return 1
    samples=[json.loads(line) for line in (S/receipt['inputs_path']).read_text().splitlines()]
    options=receipt['settings'];failed=0
    with (W/receipt['RGB_archive_workspace_relative']).open('rb') as archive,(out/'FRAMES.jsonl').open('x') as ledger:
        for sample in samples:
            iid=sample['image_id'];width,height=sample['wh'];row=dict(image_id=iid,status='INITIALIZING');phase='SOURCE_READ'
            try:
                if sample['split']!='Validation':raise ValueError('Non-validation source rejected')
                archive.seek(sample['RGB_tar_data_offset']);raw=archive.read(sample['RGB_bytes'])
                if hashlib.sha256(raw).hexdigest()!=sample['RGB_sha256']:raise ValueError('RGB member hash mismatch')
                with Image.open(BytesIO(raw)) as image:image.load();rgb=np.asarray(image.convert('RGB')).copy()
                if rgb.shape!=(height,width,3) or hashlib.sha256(struct.pack('>II',width,height)+rgb.tobytes()).hexdigest()!=sample['decoded_RGB_sha256']:
                    raise ValueError('Strict RGB geometry/decoded-content mismatch')
                phase='MODEL_INFERENCE'
                with torch.inference_mode():
                    result=model.predict(rgb[...,::-1].copy(),device=0,classes=[0],half=False,verbose=False,
                        imgsz=options['imgsz'],conf=options['conf'],iou=options['iou'],max_det=options['max_det'],
                        retina_masks=options['retina_masks'],save=False,project=str(out/'native'))[0]
                phase='OUTPUT_CONTRACT'
                boxes=result.boxes.xyxy.cpu().numpy().astype('float32');scores=result.boxes.conf.cpu().numpy().astype('float32')
                masks=(result.masks.data.cpu().numpy()>.5).astype('uint8') if result.masks is not None else np.empty((0,height,width),'uint8')
                if masks.shape!=(len(boxes),height,width) or not np.isfinite(boxes).all() or not np.isfinite(scores).all():raise ValueError('Detector output contract invalid')
                dest=out/(iid+'.npz');np.savez_compressed(dest,boxes=boxes,scores=scores,masks=masks)
                row.update(status='COMPLETE',artifact=str(dest.relative_to(S)),artifact_sha256=sha(dest),input_sha256=sample['RGB_sha256'],original_wh=sample['wh'],
                    opportunities=[dict(id=f'{iid}:YOLO:{i}',bbox=box.tolist(),score=float(scores[i])) for i,box in enumerate(boxes)])
                del result
            except Exception:
                failed+=1;row.update(status='FAILED' if phase=='MODEL_INFERENCE' else 'INVALID',failure_stage=phase,
                    failure_type='MODEL_SYSTEM_FAILURE' if phase=='MODEL_INFERENCE' else 'SHARED_DATA_ERROR' if phase=='SOURCE_READ' else 'CONTRACT_FAILURE',
                    error=traceback.format_exc(),retries=0);torch.cuda.empty_cache()
            ledger.write(json.dumps(row,allow_nan=False)+'\n');ledger.flush()
    record.update(status='COMPLETE' if not failed else 'INCOMPLETE',frames=len(samples),failed_frames=failed,end_utc=datetime.now(timezone.utc).isoformat())
    write(out/'RUN.json',record)
    return 0


if __name__=='__main__':raise SystemExit(main())
