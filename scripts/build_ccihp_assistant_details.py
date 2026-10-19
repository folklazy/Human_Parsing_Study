"""Read-only, source-hashed diagnostics for assistant-selected TRAIN cases.

No inference, annotation edits, exclusions or independent human adjudication.
"""
from pathlib import Path
import sys, json, io, hashlib, zipfile
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.audit_ccihp_full_quality import sha, write_json

IDS=['0014422','0010505','0000287','0034455','0008613','0004381',
     '0019700','0002891','0026977','0019562','0003009','0031399','0028338']

def main():
    active=json.loads((ROOT/'provenance/CCIHP_ASSISTANT_REVIEW_ACTIVE.json').read_text())
    run=ROOT/active['run_path'];out=ROOT/active['output_path']/'details';out.mkdir(exist_ok=True)
    parent=ROOT/json.loads((ROOT/'provenance/CCIHP_STAGE0F_ACTIVE_RUN.json').read_text())['run_path']
    rows={}
    for line in (parent/'IMAGE_AUDIT.jsonl').open():
        r=json.loads(line)
        if r['split']=='Training' and r['image_id'] in IDS:rows[r['image_id']]=r
    pre=json.loads((ROOT/'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json').read_text())
    index={}
    for line in (ROOT/pre['member_inventory']).open():
        r=json.loads(line)
        if r['path'] in {f'training/img/{iid}.jpg' for iid in IDS}:index[r['path']]=r
    palette=np.array([[0,0,0]]+[[k*83%200+35,k*139%200+35,k*191%200+35] for k in range(1,22)]+[[255,0,255]],dtype=np.uint8)
    result=[]
    with zipfile.ZipFile(ROOT.parent/'datasets/CCIHP_icip.zip') as z, (ROOT.parent/'datasets/cihp-DatasetNinja.tar').open('rb') as tar:
        for iid in IDS:
            r=rows[iid];ref=index[f'training/img/{iid}.jpg'];tar.seek(ref['data_offset']);b=tar.read(ref['bytes'])
            assert hashlib.sha256(b).hexdigest()==ref['sha256']==r['RGB_sha256']
            with Image.open(io.BytesIO(b)) as im:im.load();rgb=np.asarray(im.convert('RGB')).copy()
            maps={}
            for m in r['source_maps']:
                b=z.read(m['member']);assert hashlib.sha256(b).hexdigest()==m['sha256']
                with Image.open(io.BytesIO(b)) as im:im.load();maps[m['component']]=np.asarray(im).copy()
            c,h,i=[maps[k] for k in ['Category_ids','Human_ids','Instance_ids']]
            H,W=c.shape;assert rgb.shape==(H,W,3)
            ids=np.unique(h[h>0]);hcolor=np.zeros_like(rgb)
            for pid in ids:hcolor[h==pid]=[(int(pid)*83)%200+35,(int(pid)*139)%200+35,(int(pid)*191)%200+35]
            panels=[Image.fromarray(rgb),Image.fromarray(np.where((h>0)[...,None],(.40*rgb+.60*hcolor).astype('uint8'),(rgb*.35).astype('uint8'))),
                    Image.fromarray(np.where((c>0)[...,None],(.30*rgb+.70*palette[c]).astype('uint8'),(rgb*.35).astype('uint8')))]
            draw=ImageDraw.Draw(panels[1]);persons=[]
            for pid in ids:
                yy,xx=np.where(h==pid);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
                values,counts=np.unique(c[h==pid],return_counts=True)
                persons.append({'human_id':int(pid),'area':int(len(xx)),'bbox_xyxy_half_open':box,'category_pixels':dict(zip(map(str,values.tolist()),counts.tolist()))})
                draw.rectangle([box[0],box[1],box[2]-1,box[3]-1],outline='white',width=1);draw.text((box[0],box[1]),f'H{pid}',fill='white',stroke_width=1,stroke_fill='black')
            canvas=Image.new('RGB',(3*W,H+60),'#111111');d=ImageDraw.Draw(canvas)
            for col,(name,p) in enumerate(zip(['RGB original','Human IDs','Category IDs (0 dim; 22 magenta)'],panels)):
                canvas.paste(p,(col*W,28));d.text((col*W+4,5),f'TRAIN/{iid} | {name}',fill='white')
            d.text((4,H+34),'Same source coordinates. Display overlays only; native masks unchanged.',fill='white')
            dest=out/f'{iid}_full.png';assert not dest.exists();canvas.save(dest)
            cache=run/f'{iid}_native_planes.npz';assert not cache.exists();np.savez_compressed(cache,category=c,human=h,instance=i,rgb=rgb)
            result.append({'image_id':iid,'split':'Training','wh':[W,H],'output':str(dest.relative_to(ROOT)),'output_sha256':sha(dest),
                           'native_cache':str(cache.relative_to(ROOT)),'cache_sha256':sha(cache),'RGB_sha256':r['RGB_sha256'],'source_maps':r['source_maps'],
                           'persons':persons,'category_pixels':r['category_pixels'],'counts':r['counts'],'role':'purposive verification; not prevalence estimate'})
    write_json(run/'DETAIL_SOURCE_MANIFEST.json',{'cases':result,'script_sha256':sha(__file__),'source_masks_modified':False,'parser_inference':False})
    print(f'{len(result)} TRAIN source-verified diagnostics generated')

if __name__=='__main__':main()
