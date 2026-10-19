"""Canonical metadata and lossless-array contract, version 1.0 draft."""
from pathlib import Path
import re
import json
from hashlib import sha256
import numpy as np

TRACKS={'ORACLE_PERSON','YOLO26X_CONDITIONED','NATIVE_REFERENCE','SMOKE_SYNTHETIC'}


def validate_prediction(record, semantic_maps=None):
    required={'schema_version','study_id','run_id','model_id','source_commit','checkpoint_sha256',
              'source_track','image_id','original_wh','native_input_wh','crop_xyxy','native_labels',
              'predicted_person_ids','source_person_id','ownership_status','transforms',
              'precision','environment','dataset_manifest_sha256','scores','logits_available'}
    missing=required-set(record)
    if missing: raise ValueError(f'Missing prediction metadata: {sorted(missing)}')
    if record['schema_version']!='1.0' or record['source_track'] not in TRACKS: raise ValueError('Unknown schema or track')
    for name in ['study_id','run_id','model_id','image_id','environment','ownership_status']:
        if not isinstance(record[name],str) or not record[name]: raise ValueError(f'Invalid identifier: {name}')
    if not isinstance(record['source_commit'],str) or not re.fullmatch(r'[a-f0-9]{40}',record['source_commit']):
        raise ValueError('Source revision must be an exact Git SHA')
    for name in ['checkpoint_sha256','dataset_manifest_sha256']:
        if not isinstance(record[name],str) or not re.fullmatch(r'[a-f0-9]{64}',record[name]): raise ValueError(f'Invalid fingerprint: {name}')
    for name in ['original_wh','native_input_wh']:
        geometry=record[name]
        if not isinstance(geometry,(list,tuple)) or len(geometry)!=2 or any(type(v) is not int or v<=0 for v in geometry):
            raise ValueError(f'Invalid integer geometry: {name}')
    labels=record['native_labels']
    if not isinstance(labels,list) or not labels or any(type(v) is not int or v<0 for v in labels) or len(labels)!=len(set(labels)):
        raise ValueError('Invalid native label inventory')
    if record['precision'] not in {'FP32','FP16','BF16'} or type(record['logits_available']) is not bool:
        raise ValueError('Invalid precision or logit availability')
    width,height=record['original_wh']
    if width<=0 or height<=0: raise ValueError('Invalid original dimensions')
    crop=record['crop_xyxy']
    if crop is not None:
        if not isinstance(crop,(list,tuple)) or len(crop)!=4 or any(type(v) is not int for v in crop):
            raise ValueError('Crop coordinates must be integers')
        x1,y1,x2,y2=crop
        if not (0<=x1<x2<=width and 0<=y1<y2<=height): raise ValueError('Crop outside original image')
        expected=(y2-y1,x2-x1)
        transform=record['transforms']['crop_to_original']
        if transform['offset_xy']!=[x1,y1] or transform['scale_xy']!=[1,1]: raise ValueError('Incorrect crop map-back')
    else: expected=(height,width)
    ids=record['predicted_person_ids']
    if ids is not None and (not isinstance(ids,list) or any(not isinstance(v,str) or not v for v in ids) or len(ids)!=len(set(ids))):
        raise ValueError('Invalid or duplicate native predicted identities')
    if record['scores'] is not None:
        if ids is None or len(record['scores'])!=len(ids) or not np.isfinite(record['scores']).all(): raise ValueError('Invalid native scores')
    if semantic_maps is not None:
        arrays=np.asarray(semantic_maps)
        if arrays.ndim!=3 or arrays.shape[1:]!=expected: raise ValueError('Canonical masks not on declared source/crop grid')
        if arrays.dtype.kind not in 'ui' or not set(map(int,np.unique(arrays)))<=set(record['native_labels']): raise ValueError('Invalid native semantic labels')
        if ids is not None and len(ids)!=len(arrays): raise ValueError('Instance identities/planes differ')
    return True


def export_prediction(directory,record,semantic_maps,logits=None):
    validate_prediction(record,semantic_maps)
    if record['logits_available'] != (logits is not None): raise ValueError('Declared and exported logits differ')
    if logits is not None:
        logits=np.asarray(logits);masks=np.asarray(semantic_maps)
        if not np.isfinite(logits).all(): raise ValueError('Non-finite native logits')
        if logits.ndim!=4 or logits.shape[0]!=len(masks) or logits.shape[1]!=len(record['native_labels']) or logits.shape[2:]!=masks.shape[1:]:
            raise ValueError('Logits must match exported instance/class/output-grid dimensions')
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=False)
    arrays={'native_semantic_maps':np.asarray(semantic_maps)}
    if logits is not None: arrays['native_logits']=np.asarray(logits)
    tmp=directory/'native.npz.tmp'
    with tmp.open('xb') as stream: np.savez_compressed(stream,**arrays)
    tmp.replace(directory/'native.npz')
    record={**record,'native_artifact':'native.npz','native_artifact_sha256':sha256((directory/'native.npz').read_bytes()).hexdigest(),
            'common_hp_outputs':'NOT_GENERATED_TAXONOMY_DRAFT'}
    (directory/'prediction.json.tmp').write_text(json.dumps(record,indent=2)+'\n')
    (directory/'prediction.json.tmp').replace(directory/'prediction.json')
    return record
