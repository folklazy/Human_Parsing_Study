"""Execute isolated synthetic fixtures through official v2 metric functions.

Only Python-2 syntax and removed NumPy aliases are ported. No original third-
party file is modified. This is not validation of full-dataset official parity.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
from contextlib import redirect_stdout
from io import StringIO
import ast
import json
import re
import numpy as np
from PIL import Image


def main():
    study=Path(__file__).resolve().parents[1];workspace=study.parent
    source=workspace/'third_party/human_parsing/Multi-Human-Parsing/Evaluation/Multi-Human-Parsing/v2'
    raw=(source/'eval_mhp.py').read_text()
    modern=raw.replace('np.float','np.float64').replace('np.int','np.int64').replace('xrange','range')
    # Avoid replacing modern np.int64 inside names introduced in the first pass.
    modern=modern.replace('np.int6464','np.int64')
    modern=re.sub(r'(?m)^(\s*)print (.+)$',r'\1print(\2)',modern)
    tree=ast.parse(modern)
    names={'fast_hist','cal_one_mean_iou','get_gt','eval_seg_ap'}
    selected=ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names],type_ignores=[])
    helper=ast.parse((source/'voc_eval.py').read_text())
    selected.body.extend(node for node in helper.body if isinstance(node,ast.FunctionDef) and node.name=='voc_ap')
    namespace={'np':np,'Image':Image,'tqdm':lambda values,**kwargs:values,'trange':lambda n,**kwargs:range(n)}
    exec(compile(selected,'official_v2_compatibility_fixture','exec'),namespace)
    fixtures=[]
    with TemporaryDirectory() as directory:
        path=Path(directory)/'gt.png'; gt=np.array([[0,1,1],[0,2,2]],np.uint8);Image.fromarray(gt).save(path)
        data=[{'filepath':'fixture.jpg','bboxes':[{'ann_path':str(path),'x1':1,'y1':0,'x2':2,'y2':1}]}]
        cases={'perfect':[gt],'wrong_class':[np.where(gt>0,3,0).astype(np.uint8)],'no_foreground':[np.zeros_like(gt)],'duplicate':[gt,gt]}
        for name,masks in cases.items():
            results={'fixture':{'MASKS':masks,'DETS':[(1,0,2,1,1.-i*.1) for i in range(len(masks))]}}
            buffer=StringIO()
            with redirect_stdout(buffer),np.errstate(divide='ignore',invalid='ignore'):
                ap,pcp=namespace['eval_seg_ap'](results,data,nb_class=59,ovthresh_seg=.5)
            if name in {'perfect','duplicate'}: assert ap==1. and pcp==1.
            else: assert ap==0. and pcp==0.
            fixtures.append({'fixture':name,'ap_p50':float(ap),'pcp50':float(pcp),'status':'PASS'})
        rgba=np.zeros((*gt.shape,4),np.uint8);rgba[...,0]=gt;rgba[...,3]=255;Image.fromarray(rgba).save(path)
        with redirect_stdout(StringIO()),np.errstate(divide='ignore',invalid='ignore'):
            ap,pcp=namespace['eval_seg_ap']({'fixture':{'MASKS':[gt],'DETS':[(1,0,2,1,.9)]}},data,nb_class=59,ovthresh_seg=.5)
        assert ap==1. and pcp==1.;fixtures.append({'fixture':'native_RGBA_first_channel','status':'PASS'})
    active=json.loads((study/'provenance/STAGE0_ACTIVE_RUN.json').read_text());run=study/'provenance/RUN_MANIFESTS'/active['run_id']
    (run/'OFFICIAL_METRIC_EXTRACTED_COMPAT.py').write_text(ast.unparse(selected)+'\n')
    result={'status':'PASS','scope':'Five synthetic fixtures through source functions; no full evaluation and no claim of full official parity',
            'source_file':str((source/'eval_mhp.py').relative_to(workspace)),'source_sha256':sha256(raw.encode()).hexdigest(),
            'compatibility_changes':['Python2 print/xrange to Python3','np.float/np.int aliases to np.float64/np.int64','Select metric functions only; disable caching, sparse/pickle loading, progress UI'],
            'fixtures':fixtures,'ap_p_vol_not_run':True,'official_native_metric_not_mixed_with_common_miou':True}
    p=study/'provenance/OFFICIAL_METRIC_FIXTURES.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n')
    print('[METRICS] five official-function synthetic fixtures: PASS')


if __name__=='__main__':main()
