"""Deterministic native GT diagnostic panels, external artifacts only."""
from pathlib import Path
import sys,json
P=Path(__file__).resolve().parents[1];W=P.parent;sys.path.insert(0,str(P/'src'))
from cihp_benchmark.data import read_sample
import numpy as np
from PIL import Image,ImageDraw
root=W/'Human_Parsing_MHPv2_Study/outputs/cihp_native';unit=(root/'CURRENT_RUN.txt').read_text().strip();out=root/unit/'GT_DIAGNOSTICS';out.mkdir(exist_ok=False);sample=json.loads((P/'manifests/CIHP_NATIVE_DIAGNOSTIC_SAMPLE.json').read_text());evidence=[]
for iid in sample['ids']:
 a,meta=read_sample(W/'datasets/CIHP','Validation',iid);rgb=a['rgb'];h,w=rgb.shape[:2];panels=[]
 for label,key in [('RGB','rgb'),('Native Category_ids overlay','Category_ids'),('GT Human_ids + GT boxes (NOT YOLO)','Human_ids'),('Native part Instance_ids','Instance_ids')]:
  if key=='rgb':canvas=Image.fromarray(rgb)
  else:
   ids=a[key].astype('int64');col=np.stack([(ids*67+23)%255,(ids*113+47)%255,(ids*41+79)%255],-1).astype('uint8');col[ids==0]=0;overlay=(.5*rgb+.5*col).astype('uint8');canvas=Image.fromarray(overlay)
  d=ImageDraw.Draw(canvas);d.rectangle((0,0,w,18),fill='black');d.text((3,3),label,fill='white')
  if key=='Human_ids':
   for pid in np.unique(a[key]):
    if not pid:continue
    y,x=np.where(a[key]==pid);d.rectangle((int(x.min()),int(y.min()),int(x.max()),int(y.max())),outline='white');d.text((int(x.min()),int(y.min())),str(pid),fill='yellow')
  panels.append(canvas)
 sheet=Image.new('RGB',(w*2,h*2+20));sheet.paste(panels[0],(0,20));sheet.paste(panels[1],(w,20));sheet.paste(panels[2],(0,h+20));sheet.paste(panels[3],(w,h+20));ImageDraw.Draw(sheet).text((3,3),iid+' | native GT source, no prediction',fill='white');path=out/(iid+'.png');sheet.save(path);evidence.append({'id':iid,'path':str(path.relative_to(W)),'wh':meta['wh'],'visual_review_status':'GENERATED_NOT_ALL_VISUALLY_REVIEWED'})
(root/unit/'GT_DIAGNOSTIC_MANIFEST.json').write_text(json.dumps(evidence,indent=2)+'\n');print('GT panels',len(evidence),str(out))
