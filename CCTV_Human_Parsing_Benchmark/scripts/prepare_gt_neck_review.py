"""Private RGB/source-GT review sheets; no parser/detector outputs are read."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from controlled_roi_core import read,atomic,sha
P=Path(__file__).resolve().parents[1];W=P.parent
COLORS={2:(0,200,255),13:(255,225,0),5:(60,245,80),9:(240,70,220)}
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
BIG=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)

def fit(a,size):
 im=Image.fromarray(a);ratio=min(size[0]/im.width,size[1]/im.height);im=im.resize((max(1,round(im.width*ratio)),max(1,round(im.height*ratio))),Image.Resampling.NEAREST);out=Image.new('RGB',size,(25,25,25));out.paste(im,((size[0]-im.width)//2,(size[1]-im.height)//2));return out

def render(run):
 out=P/'outputs'/run;out.mkdir(parents=True,exist_ok=False)
 parent=read(P/'outputs/cctv-partial-20261031T1800Z/CONFIG.json');gtpath=P/'outputs/controlled-gt-owner-20261101/GT_REVISION.json';gt=read(gtpath);lookup={x['image_id']:x for x in gt['bindings']};persons=[];faces=[];cards=[]
 for sample in parent['members']:
  rgb=np.asarray(Image.open(W/parent['dataset_root']/'Images'/(sample['stem']+'.jpg')).convert('RGB'));binding=lookup[sample['id']]
  cat=np.asarray(Image.open(W/binding['Category_ids']));human=np.asarray(Image.open(W/binding['Human_ids']));h,w=cat.shape
  for pid in sorted(int(x) for x in np.unique(human) if x>0):
   mask=human==pid;yy,xx=np.where(mask);bounds=[int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1];x0,y0,x1,y1=bounds
   dx=max(18,int((x1-x0)*.25));dy=max(18,int((y1-y0)*.2));b=[max(0,x0-dx),max(0,y0-dy),min(w,x1+dx),min(h,y1+dy)];a,b0,c,d=b
   overlay=rgb.copy()
   for code,color in COLORS.items():
    m=mask&(cat==code);overlay[m]=(rgb[m].astype(float)*.5+np.asarray(color)*.5).astype(np.uint8)
   idx=len(persons)+1;row=dict(review_index=idx,image_id=sample['id'],person_id=pid,condition=sample['condition'],source_bbox=bounds,crop_xyxy=b,source_part_ids=[int(v) for v in np.unique(cat[mask])],GT_binding=binding)
   persons.append(row)
   card=Image.new('RGB',(800,390),'#202020');draw=ImageDraw.Draw(card);draw.text((8,4),f"#{idx:03d} {sample['id']} p{pid} {sample['condition']} {row['source_part_ids']}",fill='white',font=BIG)
   card.paste(fit(rgb[b0:d,a:c],(390,345)),(5,35));card.paste(fit(overlay[b0:d,a:c],(390,345)),(405,35));cards.append(card)
   fmask=mask&(cat==13)
   if fmask.any():
    fy,fx=np.where(fmask);bb=[int(fx.min()),int(fy.min()),int(fx.max())+1,int(fy.max())+1];fw,fh=bb[2]-bb[0],bb[3]-bb[1]
    cb=[max(0,int(bb[0]-max(25,fw*1.8))),max(0,int(bb[1]-max(20,fh*1.5))),min(w,int(bb[2]+max(25,fw*1.8))),min(h,int(bb[3]+max(35,fh*2.2)))]
    fx0,fy0,fx1,fy1=cb;scale=min(7,600//max(fx1-fx0,fy1-fy0));scale=max(2,scale)
    region=Image.fromarray(rgb[fy0:fy1,fx0:fx1]).resize(((fx1-fx0)*scale,(fy1-fy0)*scale),Image.Resampling.NEAREST)
    over=Image.fromarray(overlay[fy0:fy1,fx0:fx1]).resize(region.size,Image.Resampling.NEAREST)
    im=Image.new('RGB',(region.width*2+70,region.height+75),'#191919');di=ImageDraw.Draw(im)
    faceidx=len(faces)+1;name=f'face_{faceidx:02d}.png';di.text((8,4),f'F{faceidx:02d} {sample["id"]} p{pid} sourceFaceBox={bb} crop={cb} scale={scale}',font=FONT,fill='white')
    im.paste(region,(35,45));im.paste(over,(region.width+55,45))
    for x in range(((fx0+4)//5)*5,fx1,5):
     px=35+(x-fx0)*scale;di.line([(px,35),(px,44)],fill='white');di.text((px-6,20),str(x),font=FONT,fill='white')
    for y in range(((fy0+4)//5)*5,fy1,5):
     py=45+(y-fy0)*scale;di.line([(28,py),(34,py)],fill='white');di.text((1,py-7),str(y),font=FONT,fill='white')
    (out/'faces').mkdir(exist_ok=True);im.save(out/'faces'/name)
    faces.append(dict(face_index=faceidx,review_index=idx,image_id=sample['id'],person_id=pid,source_face_bbox=bb,crop_xyxy=cb,scale=scale,figure='faces/'+name))
 for start in range(0,len(cards),4):
  page=Image.new('RGB',(1600,780),'#111111')
  for j,card in enumerate(cards[start:start+4]):page.paste(card,((j%2)*800,(j//2)*390))
  page.save(out/('persons_%02d.png'%(start//4+1)))
 atomic(out/'REVIEW_MANIFEST.json',dict(status='RGB_AND_GT_ONLY_REVIEW_PREPARED',created_utc=datetime.now(timezone.utc).isoformat(),source_config_sha256=sha(P/'outputs/cctv-partial-20261031T1800Z/CONFIG.json'),derived_owner_revision_sha256=sha(gtpath),persons=persons,faces=faces,person_pages=(len(cards)+3)//4,parser_outputs_read=False,detector_outputs_read=False))
 (P/'outputs/CURRENT_GT_NECK_REVIEW.txt').write_text(run+'\n')
 print(json.dumps(dict(run_id=run,persons=len(persons),faces=len(faces),pages=(len(cards)+3)//4)))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();render(a.run)
