"""Stage0F streaming full GT/RGB integrity audit. No models, GT edits or attribute scoring.

Run: ../.venvs/mhpv2-stage0/bin/python scripts/audit_ccihp_full_quality.py
Immutable fresh evidence directories; inventories from Stage0E/preflight are reused.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import csv, hashlib, io, json, os, struct, subprocess, sys, zipfile
import numpy as np
from PIL import Image, ImageFile
from scipy.fft import dctn

ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parent
sys.path.insert(0,str(ROOT))
from src.data.ccihp_quality import audit_planes
ImageFile.LOAD_TRUNCATED_IMAGES=False

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def write_json(p,v):
    p=Path(p);temp=p.with_suffix(p.suffix+'.tmp')
    temp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');os.replace(temp,p)

def stat(p):
    s=Path(p).stat();return {'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'inode':s.st_ino}

def main():
    now=datetime.now(timezone.utc);run_id='stage0f-ccihp-quality-'+now.strftime('%Y%m%dT%H%M%SZ')
    run=ROOT/'provenance/RUN_MANIFESTS'/run_id;run.mkdir()
    active=json.loads((ROOT/'provenance/CCIHP_STAGE0E_CURRENT_RUN_V2.json').read_text());old=ROOT/active['run_path']
    pre=json.loads((ROOT/'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json').read_text())
    zi=json.loads((old/'ZIP_INTEGRITY.json').read_text())
    assert sha(ROOT/zi['member_inventory'])==zi['member_inventory_sha256']
    assert sha(ROOT/pre['member_inventory'])==pre['member_inventory_sha256']
    assets=[WORKSPACE/'datasets/CCIHP_icip.zip',WORKSPACE/'datasets/cihp-DatasetNinja.tar']
    assert stat(assets[0])==json.loads((old/'BEFORE.json').read_text())['zip_stat']
    protected=[p for p in ROOT.glob('provenance/*') if p.is_file() and ('PPSS' in p.name or p.name in ['DATASET_INTEGRITY.json','CHECKPOINT_MANIFEST.json','LICENSE_MATRIX_DECISION5A_V1.csv'])]
    git_before={}
    for repo in WORKSPACE.iterdir():
        if (repo/'.git').exists():
            git_before[repo.name]=subprocess.run(['git','status','--porcelain=v1'],cwd=repo,text=True,capture_output=True).stdout
            if repo.name.startswith('YOLO_'):protected.extend(repo.glob('metrics/*.csv'))
    write_json(run/'BEFORE.json',{'start_utc':now.isoformat(),'asset_stats':{str(p.relative_to(WORKSPACE)):stat(p) for p in assets},
                                'protected_sha256':{str(p.relative_to(WORKSPACE)):sha(p) for p in protected},'git_status':git_before,
                                'prior_state':json.loads((ROOT/'STUDY_STATE.json').read_text())})
    write_json(ROOT/'provenance/CCIHP_STAGE0F_ACTIVE_RUN.json',{'run_id':run_id,'run_path':str(run.relative_to(ROOT))})
    config={'schema_version':'1.0','scope':'CCIHP_BODY_CLOTHING_DATASET_AUDIT_ONLY','train':28280,'validation':5000,
            'components':['Category_ids','Human_ids','Instance_ids'],'full_quality_audit_authorized':True,
            'parser_inference':False,'attribute_evaluation':False,'pixel_hash':'SHA256(big-endian uint32 width,height + RGB bytes)',
            'RGB_policy':'strict Pillow complete load, convert RGB, no EXIF orientation transform',
            'near_duplicate_screen':{'method':'64bit DCT pHash; 32x32 grayscale LANCZOS; top8x8 median incl DC; Hamming<=4; aspect relative difference<=5%',
                                     'purpose':'candidate risk flags, not exclusion or proof of same scene'},
            'review_seed':20261012,'review_target':200,'review_status':'PENDING_INDEPENDENT_HUMAN_REVIEW'}
    write_json(run/'CONFIG.json',config)
    tar_index={}
    with (ROOT/pre['member_inventory']).open() as f:
        for line in f:
            x=json.loads(line);tar_index[x['path']]=x
    zip_index={}
    with (ROOT/zi['member_inventory']).open() as f:
        for line in f:
            x=json.loads(line);zip_index[x['member']]=x
    splits=json.loads((old/'CCIHP_SPLITS.json').read_text())
    agg={s:{'images':0,'persons':0,'instances':0,'pixels':0,'counts':Counter(),'classes':Counter(),'class_images':Counter(),
            'modes':Counter(),'dtypes':Counter(),'person_count_distribution':Counter(),'association_conflict_images':0,
            'association_conflict_instances':0,'empty_human_images':0} for s in splits}
    errors=[];byte_groups=defaultdict(list);rgb_groups=defaultdict(list)
    with zipfile.ZipFile(assets[0]) as z,assets[1].open('rb') as tar, (run/'IMAGE_AUDIT.jsonl').open('x') as out, (run/'PERSON_AUDIT.jsonl').open('x') as pout, (run/'ANOMALIES.jsonl').open('x') as aout:
        for split in ['Training','Validation']:
            for idx,iid in enumerate(sorted(splits[split])):
                row={'split':split,'image_id':iid};maps=[];meta=[]
                try:
                    for component in config['components']:
                        name=f'CCIHP_icip/dataset/{split}/{component}/{iid}.png';data=z.read(name)
                        assert hashlib.sha256(data).hexdigest()==zip_index[name]['sha256']
                        with Image.open(io.BytesIO(data)) as im:im.verify()
                        with Image.open(io.BytesIO(data)) as im:
                            im.load();a=np.asarray(im).copy();mode=im.mode
                        maps.append(a);meta.append({'component':component,'member':name,'sha256':zip_index[name]['sha256'],
                                                    'mode':mode,'dtype':str(a.dtype),'wh':[a.shape[1],a.shape[0]],
                                                    'labels':np.unique(a).tolist()})
                    diag=audit_planes(*maps);h,w=maps[0].shape
                    row.update(diag);row['wh']=[w,h];row['source_maps']=meta;row['GT_decode']='PASS'
                    for p in row.pop('persons'):pout.write(json.dumps({'split':split,'image_id':iid,**p},separators=(',',':'))+'\n')
                    a=agg[split];a['images']+=1;a['persons']+=diag['person_count'];a['instances']+=diag['instance_count'];a['pixels']+=w*h
                    a['counts'].update(diag['counts']);a['classes'].update(diag['category_pixels']);a['class_images'].update(diag['category_pixels'].keys())
                    a['person_count_distribution'][diag['person_count']]+=1
                    a['association_conflict_images']+=bool(diag['association_conflicts']);a['association_conflict_instances']+=len(diag['association_conflicts'])
                    a['empty_human_images']+=diag['person_count']==0
                    for m in meta:a['modes'][m['component']+':'+m['mode']]+=1;a['dtypes'][m['component']+':'+m['dtype']]+=1
                    if diag['unknown_ids']:
                        yy,xx=np.where(maps[0]>21);row['unknown_coordinates_xy']=[[int(x),int(y)] for x,y in zip(xx,yy)]
                    if any(diag['counts'].values()) or diag['association_conflicts'] or diag['person_count']==0:
                        aout.write(json.dumps(row,separators=(',',':'))+'\n')
                except Exception as e:
                    row['GT_decode']='FAIL';row['GT_error']=repr(e);errors.append({'split':split,'id':iid,'stage':'GT','error':repr(e)})
                name=f'{split.lower()}/img/{iid}.jpg';ref=tar_index[name];tar.seek(ref['data_offset']);data=tar.read(ref['bytes'])
                try:
                    assert hashlib.sha256(data).hexdigest()==ref['sha256']
                    row['RGB_sha256']=ref['sha256'];byte_groups[ref['sha256']].append([split,iid])
                    with Image.open(io.BytesIO(data)) as im:im.verify()
                    with Image.open(io.BytesIO(data)) as im:
                        im.load();im=im.convert('RGB');rgb=np.asarray(im);rw,rh=im.size
                        ph=dctn(np.asarray(im.convert('L').resize((32,32),Image.Resampling.LANCZOS),dtype=float),type=2,norm='ortho')[:8,:8]
                    digest=hashlib.sha256(struct.pack('>II',rw,rh)+rgb.tobytes()).hexdigest()
                    row['RGB_decoded_sha256']=digest;rgb_groups[digest].append([split,iid]);row['RGB_wh']=[rw,rh]
                    row['RGB_decode']='PASS';row['RGB_GT_dimensions_match']=row.get('wh')==[rw,rh]
                    bits=(ph>np.median(ph)).ravel();row['phash64']=f'{sum(int(v)<<(63-k) for k,v in enumerate(bits)):016x}'
                    if not row['RGB_GT_dimensions_match']:errors.append({'split':split,'id':iid,'stage':'dimensions'})
                except Exception as e:
                    row['RGB_decode']='FAIL';row['RGB_error']=repr(e);errors.append({'split':split,'id':iid,'stage':'RGB','error':repr(e)})
                out.write(json.dumps(row,separators=(',',':'))+'\n')
                if (idx+1)%250==0:
                    out.flush();pout.flush();aout.flush();write_json(run/'PROGRESS.json',{'split':split,'completed':idx+1,'total':len(splits[split]),'errors':len(errors)})
            print(f'[STAGE0F] {split}: complete {len(splits[split])}',flush=True)
    def dup_summary(groups):
        dup=[{'sha256':h,'members':m} for h,m in groups.items() if len(m)>1]
        overlap=sorted({iid for g in dup if {s for s,_ in g['members']}=={'Training','Validation'} for s,iid in g['members'] if s=='Validation'})
        within=[g for g in dup if sum(s=='Validation' for s,_ in g['members'])>1]
        return {'duplicate_groups':dup,'train_validation_overlap_validation_ids':overlap,'within_validation_groups':within}
    write_json(run/'EXACT_DUPLICATES.json',{'byte':dup_summary(byte_groups),'decoded_RGB':dup_summary(rgb_groups),'original_splits_modified':False})
    # Counter keys are normalized by JSON. Ledger retains exact per-image label inventories.
    after={str(p.relative_to(WORKSPACE)):stat(p) for p in assets}
    before=json.loads((run/'BEFORE.json').read_text())
    assert after==before['asset_stats']
    write_json(run/'FULL_STRUCTURAL_AUDIT.json',{'run_id':run_id,'status':'PASS_WITH_WARNINGS' if not errors else 'FAIL',
               'aggregate':agg,'errors':errors,'required_PNGs':sum(a['images'] for a in agg.values())*3,
               'all_required_maps_source_sha256_checked':True,'source_stats_unchanged':True,'archive_CRC_repeated':False,
               'prior_archive_sha256':{'CCIHP':zi['archive_sha256'],'CIHP_DatasetNinja':pre['archive_sha256']},
               'physical_person_quality':'NOT_VERIFIED_BY_AUTOMATED_STRUCTURE','end_utc':datetime.now(timezone.utc).isoformat()})
    print('[STAGE0F] streaming audit finished',flush=True)

if __name__=='__main__':main()
