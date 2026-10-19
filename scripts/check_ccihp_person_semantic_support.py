"""Examine all flagged maps for zero/unknown semantic support per native Human ID."""
from pathlib import Path
import io,json,sys,zipfile
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from audit_ccihp_full_quality import write_json

def main():
    active=json.loads((ROOT/'provenance/CCIHP_STAGE0F_ACTIVE_RUN.json').read_text());run=ROOT/active['run_path']
    rows=[json.loads(l) for l in (run/'IMAGE_AUDIT.jsonl').open()];checked=[];all_bg=[];no_known=[]
    with zipfile.ZipFile(ROOT.parent/'datasets/CCIHP_icip.zip') as z:
        for r in rows:
            if not (r['counts']['human_without_category'] or r['unknown_ids']):continue
            maps=[]
            for component in ['Category_ids','Human_ids']:
                with Image.open(io.BytesIO(z.read(f"CCIHP_icip/dataset/{r['split']}/{component}/{r['image_id']}.png"))) as im:im.load();maps.append(np.asarray(im))
            c,h=maps;persons=[]
            for pid in np.unique(h):
                if not pid:continue
                support=h==pid;values,counts=np.unique(c[support],return_counts=True)
                item={'split':r['split'],'image_id':r['image_id'],'person_id':int(pid),'area':int(support.sum()),
                      'category_support':{str(k):int(v) for k,v in zip(values,counts)},
                      'background_pixels':int(np.count_nonzero(support&(c==0))),
                      'known_foreground_pixels':int(np.count_nonzero(support&(c>0)&(c<=21))),
                      'unknown_pixels':int(np.count_nonzero(support&(c>21)))}
                persons.append(item)
                if not item['known_foreground_pixels']:no_known.append(item)
                if item['background_pixels']==item['area']:all_bg.append(item)
            checked.append({'split':r['split'],'image_id':r['image_id'],'persons':persons})
    write_json(run/'PERSON_SEMANTIC_SUPPORT_WARNINGS.json',{'checked_images':len(checked),'selection':'all images with Human/Category0 gap or undocumented category',
               'all_other_images_have_positive_known_foreground_for_each_human_by_zero_gap_zero_unknown_invariants':True,
               'completely_background_person_planes':all_bg,'without_known_foreground_person_planes':no_known,
               'checks':checked,'source_GT_modified':False,'physical_cause':'UNRESOLVED_PENDING_HUMAN_ADJUDICATION'})
    print(f'[STAGE0F] flagged person support: {len(checked)} images, {len(all_bg)} wholly-background person planes',flush=True)

if __name__=='__main__':main()
