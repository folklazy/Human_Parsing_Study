"""Prepare isolated one-TRAIN-image copies of already verified native pilot workers.
No source/dataset mutation. Scientific preprocessing/model code is unchanged.
"""
from pathlib import Path
import sys,json,hashlib,shutil,difflib
S=Path(__file__).resolve().parents[1];W=S.parent;sys.path.insert(0,str(S))
from src.application_v2.policy import load_config
from src.application_v2.artifacts import file_hash
cfg=load_config(S/'configs/application_v2_handoff_v3.yaml');R=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run'];P=W/'Human_Parsing_CCIHP_10_Image_Pilot';B=R/'native_smoke';B.mkdir()
for d in ['scripts','configs','outputs','provenance','taxonomy','logs']:(B/d).mkdir()
manifest=json.loads((P/'configs/TEN_IMAGE_MANIFEST.json').read_text());rows=[r for r in manifest['images'] if r['image_id']=='0000930']
assert len(rows)==1 and rows[0]['split']=='Training' and rows[0]['image_id'] in cfg['bounded_train']['input_ids']
r=rows[0];assert file_hash(P/r['input'])==r['input_sha256']
manifest['images']=rows;manifest['scope']='Bounded TRAIN feasibility; no scoring, ranking, or benchmark';manifest['parent_manifest_sha256']=file_hash(P/'configs/TEN_IMAGE_MANIFEST.json');(B/'configs/TEN_IMAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
(B/'outputs/inputs').symlink_to((P/'outputs/inputs').resolve(),target_is_directory=True)
shutil.copy2(P/'taxonomy/NATIVE_CLASS_INVENTORY.json',B/'taxonomy/NATIVE_CLASS_INVENTORY.json')
for p in (P/'configs').glob('*.yaml'):shutil.copy2(p,B/'configs'/p.name)
patches=[]
for name in ['pilot_common.py','pilot_fp32_amp.py','run_fashn.py','run_cpi.py','run_mask_transformer.py','run_schp.py','run_qanet.py','run_rpr.py']:
 src=P/'scripts'/name;t=src.read_text();original=t
 if name=='pilot_common.py':
  t=t.replace('WORKSPACE = ROOT.parent',"WORKSPACE = Path(__import__('os').environ['HUMAN_PARSING_WORKSPACE'])")
  t=t.replace("len(result['cases']) == 10","len(result['cases']) == 1").replace("/10'","/1'")
 else:
  t=t.replace('WORKSPACE=ROOT.parent',"WORKSPACE=Path(os.environ['HUMAN_PARSING_WORKSPACE'])")
  t=t.replace('assert len(inputs)==10','assert len(inputs)==1').replace('/10 images','/1 image').replace('/10\'', '/1\'')
 t=t.replace("'PILOT_PASS'","'BOUNDED_NATIVE_PASS'").replace("'PILOT_FAIL'","'BOUNDED_NATIVE_FAIL'")
 (B/'scripts'/name).write_text(t)
 patches.append(''.join(difflib.unified_diff(original.splitlines(True),t.splitlines(True),fromfile=str(src.relative_to(W)),tofile=str((B/'scripts'/name).relative_to(W)))))
(B/'WORKER_CHANGES.diff').write_text('\n'.join(patches))
(B/'PREPARATION.json').write_text(json.dumps({'config_sha256':file_hash(S/'configs/application_v2_handoff_v3.yaml'),'input_ids':[r['image_id']],'split':'Training','native_workers_reused':True,'canonical_scoring':False,'full_benchmark':False,'source_worker_hashes':{p.name:file_hash(p) for p in (P/'scripts').glob('run_*.py')},'precision':'FP32','warmups':0,'measured_rounds':1,'timings':'smoke only; not benchmark distribution','resident_models':'one parser, sequential workers; no YOLO','seed':20261015,'Sapiens2':'NOT_EXECUTED_USE_RESTRICTED'},indent=2))
print(B)
