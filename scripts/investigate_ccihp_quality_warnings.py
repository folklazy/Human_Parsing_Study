"""Focused TRAIN warning diagnostics; unknown values retained, no GT correction."""
from pathlib import Path
from collections import Counter
import hashlib, io, json, sys, zipfile
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1];WS=ROOT.parent;sys.path.insert(0,str(ROOT))
from audit_ccihp_full_quality import sha,write_json

def main():
    active=json.loads((ROOT/'provenance/CCIHP_STAGE0F_ACTIVE_RUN.json').read_text());run=ROOT/active['run_path']
    rows=[json.loads(x) for x in (run/'IMAGE_AUDIT.jsonl').open()];bykey={(r['split'],r['image_id']):r for r in rows}
    pre=json.loads((ROOT/'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json').read_text());idx={x['path']:x for x in map(json.loads,(ROOT/pre['member_inventory']).open())}
    target=[('Training',x) for x in ['0033810','0014422','0010505','0010638','0013316','0006282']]+[('Validation','0037710'),('Validation','0012253')]
    output=ROOT/'outputs/visualizations'/active['run_id']/'focused_warnings_v2';output.mkdir(parents=True,exist_ok=True)
    records=[];unknown=[]
    with zipfile.ZipFile(WS/'datasets/CCIHP_icip.zip') as z,(WS/'datasets/cihp-DatasetNinja.tar').open('rb') as tar:
        def maps(split,iid):
            result=[]
            for comp in ['Category_ids','Human_ids','Instance_ids']:
                with Image.open(io.BytesIO(z.read(f'CCIHP_icip/dataset/{split}/{comp}/{iid}.png'))) as im:im.load();result.append(np.asarray(im).copy())
            return result
        for row in rows:
            if not row['unknown_ids']:continue
            c,h,i=maps(row['split'],row['image_id']);u=c>21
            unknown.append({'split':row['split'],'image_id':row['image_id'],'unknown_pixels':int(u.sum()),
                            'unknown_positive_human_pixels':int(np.count_nonzero(u&(h>0))),
                            'unknown_positive_instance_pixels':int(np.count_nonzero(u&(i>0))),
                            'unknown_human_ids':np.unique(h[u]).tolist(),
                            'unknown_labels':np.unique(c[u]).tolist()})
        for split,iid in target:
            row=bykey[(split,iid)];c,h,i=maps(split,iid);name=f'{split.lower()}/img/{iid}.jpg';ref=idx[name];tar.seek(ref['data_offset']);data=tar.read(ref['bytes'])
            assert hashlib.sha256(data).hexdigest()==ref['sha256']
            with Image.open(io.BytesIO(data)) as im:im.load();rgb=np.asarray(im.convert('RGB')).copy()
            masks={'unknown_Category22':c>21,'Human_positive_Category0':(h>0)&(c==0)}
            H,W=c.shape;canvas=Image.new('RGB',(W*3,H+24),'#171717');draw=ImageDraw.Draw(canvas)
            canvas.paste(Image.fromarray(rgb),(0,24));draw.text((2,4),'Original RGB; '+split+' '+iid,fill='white')
            info={'split':split,'image_id':iid,'purpose':'PURPOSIVE_WARNING_NOT_RANDOM_PREVALENCE_SAMPLE','masks':{},'physical_error_confirmation':'NOT_ADJUDICATED'}
            for k,(kind,m) in enumerate(masks.items(),1):
                rr=rgb.copy();rr[m]=[255,0,255];canvas.paste(Image.fromarray(rr),(k*W,24));draw.text((k*W+2,4),kind+f' pixels={int(m.sum())}',fill='white')
                ys,xs=np.where(m);values,counts=np.unique(h[m],return_counts=True)
                info['masks'][kind]={'pixels':int(m.sum()),'human_pixel_counts':{str(v):int(n) for v,n in zip(values,counts)},
                                     'bbox_xyxy_half_open':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if len(xs) else None}
                if len(xs):
                    x1=max(int(xs.min())-12,0);y1=max(int(ys.min())-12,0);x2=min(int(xs.max())+13,W);y2=min(int(ys.max())+13,H)
                    # Categorical ROI nearest-neighbor display, 4x; full source panel above remains unchanged.
                    crop_rgb=Image.fromarray(rgb).crop((x1,y1,x2,y2));colors=np.array([[0,0,0]]+[((a*83)%200+35,(a*139)%200+35,(a*191)%200+35) for a in range(1,256)],np.uint8);colors[22:]=[255,0,255]
                    native=Image.fromarray(colors[c[y1:y2,x1:x2]])
                    roi=Image.new('RGB',((x2-x1)*2*4,(y2-y1)*4+24),'#171717')
                    roi.paste(crop_rgb.resize(((x2-x1)*4,(y2-y1)*4),Image.Resampling.NEAREST),(0,24))
                    roi.paste(native.resize(((x2-x1)*4,(y2-y1)*4),Image.Resampling.NEAREST),((x2-x1)*4,24))
                    ImageDraw.Draw(roi).text((2,4),iid+' '+kind+' RGB / native Category (4x nearest)',fill='white')
                    rp=output/f'{iid}_{kind}_ROI.png';roi.save(rp,compress_level=3)
                    info['masks'][kind]['ROI']={'path':str(rp.relative_to(ROOT)),'sha256':sha(rp),'source_xyxy':[x1,y1,x2,y2],'display_scale':4,'resampling':'NEAREST_DISPLAY_ONLY'}
            path=output/f'{iid}_full.png';canvas.save(path,compress_level=3);info['full_image']=str(path.relative_to(ROOT));info['sha256']=sha(path);records.append(info)
    write_json(run/'FOCUSED_WARNING_INVESTIGATION.json',{'unknown_inventory':unknown,'unknown_pixels':sum(x['unknown_pixels'] for x in unknown),
                  'all_unknowns_have_human_support':all(x['unknown_positive_human_pixels']==x['unknown_pixels'] for x in unknown),
                  'all_unknowns_without_attribute_instance':all(x['unknown_positive_instance_pixels']==0 for x in unknown),
                  'diagnostic_cases':records,'no_unknown_background_relabeling':True,'physical_semantic_quality':'HUMAN_REVIEW_PENDING'})
    print(f'[STAGE0F] warning probes: {len(unknown)} unknown maps + {len(records)} focused integrity diagnostics',flush=True)

if __name__=='__main__':main()
