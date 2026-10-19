"""Versioned compatibility boundary around pinned original MHP-v2 functions.

No model-specific branches, pickle loading, GT mutation or upstream edits.
Valid nonempty inputs delegate to reference functions unchanged mathematically.
Only syntax/removed NumPy aliases are ported; empty-domain behavior is explicit.
"""
from pathlib import Path
from functools import lru_cache
from contextlib import redirect_stdout
from io import StringIO
from hashlib import sha256
import ast
import re
import numpy as np
from PIL import Image

VERSION = '1.0'
THRESHOLDS = (0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9)
PINNED_SOURCE_SHA256 = '1f0bee0315f7d23e8020bed6d842c4be2d0334be6b20bd11a0bd08de77d889e2'
PINNED_VOC_SHA256 = '44f34bdd8e3c733b0bb5d61209ee4efd19d361ddaa1d9ab484b5c3c592bb8487'


def source_directory():
    workspace = Path(__file__).resolve().parents[3]
    return workspace/'third_party/human_parsing/Multi-Human-Parsing/Evaluation/Multi-Human-Parsing/v2'


@lru_cache(maxsize=1)
def reference_functions():
    source = source_directory()
    raw = (source/'eval_mhp.py').read_text()
    if sha256(raw.encode()).hexdigest() != PINNED_SOURCE_SHA256:
        raise ValueError('Upstream evaluator differs from audited pin; review required')
    modern = re.sub(r'\bnp\.float\b','np.float64',raw)
    modern = re.sub(r'\bnp\.int\b','np.int64',modern)
    modern = re.sub(r'\bxrange\b','range',modern)
    modern = re.sub(r'(?m)^(\s*)print (.+)$',r'\1print(\2)',modern)
    tree = ast.parse(modern)
    wanted = {'fast_hist','cal_one_mean_iou','get_gt','eval_seg_ap'}
    body = [node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in wanted]
    helper_raw = (source/'voc_eval.py').read_text()
    if sha256(helper_raw.encode()).hexdigest() != PINNED_VOC_SHA256:
        raise ValueError('Upstream VOC helper differs from audited pin; review required')
    helper = ast.parse(helper_raw)
    body += [node for node in helper.body if isinstance(node,ast.FunctionDef) and node.name=='voc_ap']
    assert {node.name for node in body} == wanted|{'voc_ap'}
    namespace = {'np':np,'Image':Image,'tqdm':lambda values,**kwargs:values,'trange':lambda n,**kwargs:range(n)}
    exec(compile(ast.Module(body=body,type_ignores=[]),'pinned_official_mhp_reference','exec'),namespace)
    return namespace


def validate_native_inputs(results, data, classes):
    if not isinstance(classes,int) or not 2<=classes<=256:
        raise ValueError('Explicit native class count including background required')
    ids=[];grids={}
    for item in data:
        image_id=item['filepath'].split('/')[-1].replace('.jpg','')
        ids.append(image_id)
        shape=None
        for box in item['bboxes']:
            with Image.open(box['ann_path']) as im:
                im.load();labels=np.asarray(im)
                labels=labels[...,0] if labels.ndim==3 else labels
            if labels.ndim!=2 or labels.dtype.kind not in 'ui':
                raise ValueError('Native GT must decode to an integer 2D label grid')
            # Native ignore outside classes is retained for the reference reader.
            if shape is not None and shape!=labels.shape:
                raise ValueError('Per-person GT grids differ')
            shape=labels.shape
        grids[image_id]=shape
    if len(ids)!=len(set(ids)):
        raise ValueError('Duplicate image identifiers in evaluation population')
    for image_id,item in results.items():
        if image_id not in grids:
            raise ValueError('Prediction image absent from evaluation population')
        if len(item['MASKS'])!=len(item['DETS']):
            raise ValueError('Parsing planes/detection scores differ')
        for mask,det in zip(item['MASKS'],item['DETS']):
            arr=np.asarray(mask)
            if arr.ndim!=2 or arr.dtype.kind not in 'ui' or np.any((arr<0)|(arr>=classes)):
                raise ValueError('Invalid native prediction labels/grid')
            if grids[image_id] is not None and arr.shape!=grids[image_id]:
                raise ValueError('Prediction does not use original GT coordinates')
            if len(det)!=5 or not np.isfinite(det).all():
                raise ValueError('Native finite bbox/confidence tuple required')
    return sum(len(item['DETS']) for item in results.values())


def evaluate_native(results,data,classes=59,threshold=0.5):
    if not np.isfinite(threshold) or not 0<=threshold<=1:
        raise ValueError('Invalid parsing-IoU threshold')
    count=validate_native_inputs(results,data,classes)
    functions=reference_functions()
    with redirect_stdout(StringIO()):
        _,positives=functions['get_gt'](data,task_id=None)
    if positives==0:
        ap=pcp=None;status='UNDEFINED_NO_GT_SUPPORT'
    elif count==0:
        # VOC empty precision/recall helper integrates to zero. The published
        # PCP definition assigns zero to every missed GT person.
        ap=pcp=0.0;status='DEFINED_ALL_GT_MISSED'
    else:
        with redirect_stdout(StringIO()),np.errstate(divide='ignore',invalid='ignore'):
            ap,pcp=functions['eval_seg_ap'](results,data,nb_class=classes,
                    ovthresh_seg=threshold,Sparse=False,From_pkl=False,task_id=None)
        ap=float(ap);pcp=float(pcp);status='DEFINED_REFERENCE_DELEGATION'
    return {'APp':ap,'PCP':pcp,'threshold':float(threshold),'GT_person_support':int(positives),
            'prediction_person_count':count,'status':status,'score_unit':'fraction_0_to_1',
            'wrapper_version':VERSION,'reference_source_sha256':PINNED_SOURCE_SHA256}


def evaluate_volume(results,data,classes=59):
    # Each reference call rebuilds GT matching state; no reused detected flags.
    rows=[evaluate_native(results,data,classes,t) for t in THRESHOLDS]
    defined=all(row['APp'] is not None for row in rows)
    return {'APp_vol':float(np.mean([row['APp'] for row in rows])) if defined else None,
            'APp50':rows[4]['APp'],'PCP50':rows[4]['PCP'],'per_threshold':rows,
            'thresholds':list(THRESHOLDS),'status':'DEFINED' if defined else 'UNDEFINED_NO_GT_SUPPORT',
            'official_dataset_benchmark_run':False,'wrapper_version':VERSION}
