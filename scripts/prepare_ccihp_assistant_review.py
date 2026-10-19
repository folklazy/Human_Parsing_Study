"""Read existing diagnostics to prepare an assistant visual review; preserve human review."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.audit_ccihp_full_quality import sha,write_json

def main():
    active=json.loads((ROOT/'provenance/CCIHP_STAGE0F_ACTIVE_RUN.json').read_text());parent=ROOT/active['run_path']
    now=datetime.now(timezone.utc);rid='ccihp-assistant-review-'+now.strftime('%Y%m%dT%H%M%SZ')
    run=ROOT/'provenance/RUN_MANIFESTS'/rid;run.mkdir();out=ROOT/'outputs/visualizations'/rid;out.mkdir(parents=True)
    sample=json.loads((parent/'TRAIN_REVIEW_SAMPLE.json').read_text())
    package=json.loads((parent/'REVIEW_PACKAGE.json').read_text());byid={x['image_id']:x for x in package['outputs']}
    preserve=['STUDY_STATE.json',str((parent/'TRAIN_REVIEW_SAMPLE.json').relative_to(ROOT)),str((parent/'HUMAN_REVIEW_CHECKLIST.csv').relative_to(ROOT)),str((parent/'VALIDATION.json').relative_to(ROOT))]
    write_json(run/'BEFORE.json',{'parent_run':active['run_id'],'timestamp':now.isoformat(),'protected_hashes':{p:sha(ROOT/p) for p in preserve},
               'original_dataset_reads':False,'previous_human_review_status':'PENDING','independent_human_review':False})
    pages=[]
    for start in range(0,200,4):
        selected=sample['samples'][start:start+4];sheet=Image.new('RGB',(1440,4*440),'#161616');draw=ImageDraw.Draw(sheet)
        ids=[]
        for row,s in enumerate(selected):
            iid=s['image_id'];rec=byid[iid];p=ROOT/rec['output'];assert sha(p)==rec['output_sha256']
            W,H=rec['image_wh'];y=row*440
            draw.text((8,y+6),f"{start+row+1:03d}/200 TRAIN/{iid} | nativeHuman IDs={rec['native_person_count']} | RGB / Human / Category",fill='white')
            with Image.open(p) as im:
                for col in range(3):
                    panel=im.crop((col*W,28,(col+1)*W,28+H))
                    # Contact views only; original full-resolution diagnostic remains the reference.
                    panel=ImageOps.contain(panel,(478,410),Image.Resampling.LANCZOS)
                    sheet.paste(panel,(col*480+(480-panel.width)//2,y+26+(410-panel.height)//2))
            ids.append(iid)
        dest=out/f'contact_{start//4+1:02d}.png';sheet.save(dest,compress_level=3)
        pages.append({'page':start//4+1,'image_ids':ids,'output':str(dest.relative_to(ROOT)),'sha256':sha(dest),'view_size':[1440,1760],
                      'scope':'full-frame contact screening; detailed flags require original-resolution inspection'})
    write_json(run/'CONTACT_MANIFEST.json',{'parent':active,'sample':str((parent/'TRAIN_REVIEW_SAMPLE.json').relative_to(ROOT)),
             'sample_ids':[s['image_id'] for s in sample['samples']],'pages':pages,'human_review_completed':False})
    write_json(ROOT/'provenance/CCIHP_ASSISTANT_REVIEW_ACTIVE.json',{'run_id':rid,'run_path':str(run.relative_to(ROOT)),'output_path':str(out.relative_to(ROOT))})
    print(rid,flush=True)

if __name__=='__main__':main()
