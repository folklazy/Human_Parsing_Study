"""Fixed-16 private common-view original-grid panels, saved outputs only."""
from pathlib import Path
import html,json,sys
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'))
from common_view.core import load_spec,project,compose_native,sha_file
from common_view.packets import read_packet,atomic_json
from cihp_benchmark.data import read_image
from render_common_pilot import overlay,colors

def render(c):
    root=W/c['artifact_root'];out=root/'gallery';out.mkdir(exist_ok=False);spec=load_spec(W/c['protocol'])
    sample=json.loads((P/'manifests/CIHP_NATIVE_DIAGNOSTIC_SAMPLE.json').read_text());reused={r['image_id']:W/r['packet'] for r in c['reused']}
    sources={mid:{r['image_id']:r for r in map(json.loads,(W/s['input_manifest']).open())} for mid,s in c['legacy'].items()}
    records=[]
    for iid in sample['ids']:
        rgb,_=read_image(W/'datasets/CIHP/Validation/Images'/(iid+'.jpg'));category,_=read_image(W/'datasets/CIHP/Validation/Category_ids'/(iid+'.png'),True)
        gt=np.full(category.shape,255,np.uint8);valid=category<20;gt[valid]=project(category[valid],'CIHP_GT_AND_NATIVE_PRED',spec)
        panels=[('RGB',Image.fromarray(rgb)),('GT common4 + OTHER',overlay(rgb,gt))];refs=[]
        for mid in c['models']:
            packet=reused.get(iid,root/'models/Sapiens2_0.4b/packets'/iid) if mid=='Sapiens2_0.4b' else W/sources[mid][iid]['packet']
            if not packet.exists():panels.append((mid+' NOT_AVAILABLE',Image.fromarray(rgb)));continue
            meta,a=read_packet(packet,legacy=mid!='Sapiens2_0.4b')
            space='SAPIENS2_DOME29_PRED' if mid=='Sapiens2_0.4b' else 'CIHP_GT_AND_NATIVE_PRED'
            mask=project(compose_native(a['person_semantic_masks'],a['person_scores'],category.shape),space,spec)
            panels.append((mid,overlay(rgb,mask)));refs.append(dict(model_id=mid,source_packet=str(packet.relative_to(W)),packet_sha256=meta['packet_sha256']))
        h,w=category.shape;canvas=Image.new('RGB',(4*w,2*(h+30)),'#171b22');draw=ImageDraw.Draw(canvas)
        for j,(name,panel) in enumerate(panels):
            x=(j%4)*w;y=(j//4)*(h+30);draw.text((x+5,y+5),name,fill='white');canvas.paste(panel,(x,y+30))
        path=out/(iid+'.png');canvas.save(path);preview=canvas.copy();preview.thumbnail((1800,1200));preview.save(out/(iid+'.jpg'),quality=88)
        records.append(dict(image_id=iid,PNG=path.name,sha256=sha_file(path),source_packets=refs,original_wh=[w,h]))
    page='<html><meta charset="utf-8"><h1>Fixed16 C4-P application comparison</h1><p>Face proxy / Hair / Upper non-Dress / Lower non-Dress / OTHER; same palette. Missing predictions marked, not fabricated. Private dataset imagery.</p>'
    palette=colors()
    for index,name in enumerate(['Background','Face proxy','Hair','Upper non-Dress','Lower non-Dress','OTHER']):
        color='#'+''.join(f'{int(v):02x}' for v in palette[index])
        page+=f'<span style="display:inline-block;border-left:20px solid {color};padding:5px">{index}: {name}</span>'
    page+=''.join(f'<h2>{r["image_id"]}</h2><a href="{r["PNG"]}"><img src="{r["image_id"]}.jpg"></a>' for r in records)
    (out/'index.html').write_text(page+'</html>');atomic_json(out/'MANIFEST.json',records)
    atomic_json(W/c['record_root']/'GALLERY_INDEX.json',dict(fixed_sample=str((P/'manifests/CIHP_NATIVE_DIAGNOSTIC_SAMPLE.json').relative_to(W)),
        gallery=str((out/'index.html').relative_to(W)),manifest_sha256=sha_file(out/'MANIFEST.json'),IDs=sample['ids'],images_public=False))
    return records
