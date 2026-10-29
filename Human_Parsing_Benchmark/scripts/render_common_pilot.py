"""Private original-grid pilot gallery, saved integer masks only; no model calls."""
from pathlib import Path
import html,json,sys
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'))
from common_view.core import compose_native,project,gt_domains,sha_file
from common_view.packets import atomic_json,read_packet
from cihp_benchmark.data import read_image


def colors():
    out=np.zeros((256,3),np.uint8)
    for c in range(256):
        v=c
        for bit in range(8):
            for ch in range(3):out[c,ch]|=((v>>ch)&1)<<(7-bit)
            v>>=3
    return out


def overlay(rgb,mask):
    out=rgb.copy();use=(mask>0)&(mask<255)
    out[use]=(out[use]*.35+colors()[mask[use]]*.65).astype(np.uint8)
    return Image.fromarray(out)


def render(raw,spec,ids):
    raw=Path(raw);out=raw/'gallery';out.mkdir(exist_ok=False);figures=[]
    for iid in ids:
        meta,a=read_packet(raw/'packets'/iid)
        rgb,_=read_image(W/'datasets/CIHP/Validation/Images'/(iid+'.jpg'))
        c,_=read_image(W/'datasets/CIHP/Validation/Category_ids'/(iid+'.png'),True)
        h,_=read_image(W/'datasets/CIHP/Validation/Human_ids'/(iid+'.png'),True)
        gt,_,_,_=gt_domains(c,h,spec)
        pred=project(compose_native(a['person_semantic_masks'],a['person_scores'],c.shape),'SAPIENS2_DOME29_PRED',spec)
        owners=np.zeros(c.shape,np.uint8)
        for j in sorted(range(len(a['person_scores'])),key=lambda j:(float(a['person_scores'][j]),-j)):owners[a['person_extents'][j]]=j+1
        height,width=c.shape;canvas=Image.new('RGB',(3*width,2*(height+30)),'#171b22');draw=ImageDraw.Draw(canvas)
        panels=[('Original RGB',Image.fromarray(rgb)),('GT common4 + OTHER',overlay(rgb,gt)),('Sapiens application common4',overlay(rgb,pred)),('Native Sapiens29 full-frame',overlay(rgb,a['native_full_frame_semantic_mask'])),('GT Human IDs (local)',overlay(rgb,h.astype(np.uint8))),('Frozen YOLO ownership (local)',overlay(rgb,owners))]
        for index,(name,img) in enumerate(panels):
            x=(index%3)*width;y=(index//3)*(height+30);draw.text((x+4,y+7),name,fill='white');canvas.paste(img,(x,y+30))
        canvas.save(out/(iid+'.png'));preview=canvas.copy();preview.thumbnail((1500,1500));preview.save(out/(iid+'.jpg'),quality=94)
        figures.append({'image_id':iid,'PNG':iid+'.png','preview':iid+'.jpg','original_wh':[width,height],'sha256':sha_file(out/(iid+'.png')),'packet_sha256':meta['packet_sha256']})
    native=['Background','Apparel','Eyeglass','Face_Neck','Hair','Left_Foot','Left_Hand','Left_Lower_Arm','Left_Lower_Leg','Left_Shoe','Left_Sock','Left_Upper_Arm','Left_Upper_Leg','Lower_Clothing','Right_Foot','Right_Hand','Right_Lower_Arm','Right_Lower_Leg','Right_Shoe','Right_Sock','Right_Upper_Arm','Right_Upper_Leg','Torso','Upper_Clothing','Lower_Lip','Upper_Lip','Lower_Teeth','Upper_Teeth','Tongue']
    def legend(names):
        return ' '.join(f'<span style="display:inline-block;margin:6px"><b style="background:rgb{tuple(map(int,colors()[i]))};padding:5px">{i}</b> {html.escape(n)}</span>' for i,n in enumerate(names))
    page='<html><meta charset="utf-8"><title>C4-P 0.4B pilot</title><style>body{font:16px system-ui;background:#151920;color:#eee;margin:20px}a{color:#8cf}img{max-width:100%}</style><h1>Private CIHP–Sapiens2 0.4B pilot</h1><p>6-image diagnostics, not a 5000-image benchmark. Common labels and native29 use different legends. Local owner colors are not matched person IDs across columns. BG reveals original RGB; overlays are not garment colors. No dataset redistribution.</p><h2>Common legend</h2>'+legend(list(spec['targets'].values()))+'<h2>Native29 legend (bottom-left panels)</h2>'+legend(native)
    page+=''.join(f'<h2>{r["image_id"]}</h2><a href="{r["PNG"]}"><img src="{r["preview"]}"></a>' for r in figures)
    (out/'index.html').write_text(page+'</html>');atomic_json(out/'MANIFEST.json',figures)
    return figures
