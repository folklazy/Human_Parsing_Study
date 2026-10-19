"""Export assistant observations separately from independent human review."""
from pathlib import Path
import json,sys,csv,re
from datetime import datetime,timezone
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.audit_ccihp_full_quality import sha,write_json,stat

ROIS={'0014422':[0,0,274,367],'0010505':[326,170,400,336],
      '0000287':[54,241,87,274],'0034455':[155,130,249,227],'0008613':[283,235,349,488]}
FINDINGS={
 '0014422':('CONFIRMED_SEMANTIC_SUPPORT_GAP','H1 exists (91332 pixels), all Category0 and Instance0; cause unknown.'),
 '0010505':('CONFIRMED_UNDOCUMENTED_LABEL','2938 Category22 pixels; all H1, Instance0; native class meaning unresolved.'),
 '0000287':('CONFIRMED_DEGENERATE_HUMAN_ID','H3 consists of one pixel (70,257), Category0/Instance0; no useful person extent.'),
 '0034455':('VISIBLE_PERSON_UNASSIGNED_POLICY_UNCERTAIN','Patient face/arm visible; no person identity there. Exhaustiveness policy unknown.'),
 '0008613':('VISIBLE_PERSON_UNASSIGNED_POLICY_UNCERTAIN','Marching group has four annotated IDs; visible rightmost marcher unassigned.'),
 '0004381':('EXPLAINED_ACCESSORY_SUPPORT','H3 contains28494 Bag20 pixels; broad silhouette is supported accessory semantics.'),
 '0019700':('EXPLAINED_NATIVE_CONVENTION','Scalp regions are Hair2; included README explicitly permits sparse/bald hair characterization.'),
 '0002891':('AMBIGUOUS_NOT_CONFIRMED_ERROR','Pants9 triangular region may be seated bent knee; image alone insufficient to call carried-object leakage.'),
 '0026977':('UNCERTAIN_PARTIAL_PERSON_OWNERSHIP','H4 has1716 pixels with categories5/9/14; possible partially hidden person. Do not delete by visible head count.'),
 '0019562':('CONTROL_PATIENT_ANNOTATED','Patient H6 has2683 pixels with six supported categories; no general all-patients omission claim.'),
 '0003009':('CONTACT_NOTE_CORRECTED','Native view is military group with three IDs; earlier instrument hypothesis was mistaken and withdrawn.'),
 '0031399':('OCCLUDING_BLANKET_POLICY_UNCERTAIN','Baby H3 has7847 pixels, categories1/2/5/13; blanket excluded, no evidence of required amodal completion.'),
 '0028338':('LOWER_REGION_COVERAGE_POLICY_UNCERTAIN','Visible lower torso beneath burned-in subtitle bands largely unassigned; do not infer amodal policy.'),
}

def main():
    active=json.loads((ROOT/'provenance/CCIHP_ASSISTANT_REVIEW_ACTIVE.json').read_text());run=ROOT/active['run_path'];out=ROOT/active['output_path']/'details'
    notes=json.loads((run/'CONTACT_SCREEN_NOTES.json').read_text());contacts=json.loads((run/'CONTACT_MANIFEST.json').read_text())
    assert sorted(n for b in notes for n in b['pages'])==list(range(1,51))
    assert sum(b['screened_ids'] for b in notes)==200
    assert len(set(contacts['sample_ids']))==200
    details=json.loads((run/'DETAIL_SOURCE_MANIFEST.json').read_text());byid={x['image_id']:x for x in details['cases']}
    candidates={x['id']:x for b in notes for x in b['candidates']}
    with (run/'ASSISTANT_SCREEN_CHECKLIST.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['image_id','split','contact_page','reviewer','screen_status','contact_flag','detail_status','scope','independent_human_review'])
        writer.writeheader()
        for p in contacts['pages']:
            assert sha(ROOT/p['output'])==p['sha256']
            for iid in p['image_ids']:
                writer.writerow({'image_id':iid,'split':'Training','contact_page':p['page'],'reviewer':'ASSISTANT',
                    'screen_status':'CANDIDATE_REQUIRING_DETAIL' if iid in candidates else 'NO_MAJOR_ISSUE_VISIBLE_AT_CONTACT_RESOLUTION',
                    'contact_flag':candidates.get(iid,{}).get('type',''),'detail_status':FINDINGS.get(iid,('NOT_DETAIL_REVIEWED',))[0],
                    'scope':'full-frame contact screen; fine boundaries not certified','independent_human_review':'PENDING'})
    fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font=ImageFont.truetype(fontpath,16) if Path(fontpath).exists() else ImageFont.load_default()
    crops=[];adjudications=[]
    for iid,rec in byid.items():
        assert sha(ROOT/rec['native_cache'])==rec['cache_sha256']
        with np.load(ROOT/rec['native_cache'],allow_pickle=False) as a:
            c,h,i,rgb=[a[k] for k in ['category','human','instance','rgb']]
            assert list(rgb.shape[1::-1])==rec['wh']
            assert sum(p['area'] for p in rec['persons'])==int((h>0).sum())
            extra={}
            if iid=='0014422':
                sel=h==1;assert int(sel.sum())==91332 and np.all(c[sel]==0) and np.all(i[sel]==0)
                extra={'human_id':1,'pixels':91332,'category_support':0,'instance_support':0}
            elif iid=='0010505':
                sel=c==22;assert int(sel.sum())==2938 and np.all(h[sel]==1) and np.all(i[sel]==0)
                extra={'unknown_category':22,'pixels':2938,'human_ids':[1],'instance_values':[0]}
            elif iid=='0000287':
                assert int((h==3).sum())==1 and (int(h[257,70]),int(c[257,70]),int(i[257,70]))==(3,0,0)
                extra={'human_id':3,'pixels':1,'xy':[70,257],'category':0,'instance':0}
            elif iid in ['0034455','0008613']:
                point=(211,159) if iid=='0034455' else (300,274)
                x,y=point;assert (int(h[y,x]),int(c[y,x]),int(i[y,x]))==(0,0,0)
                extra={'illustrative_visible_face_xy':list(point),'point_human_category_instance':[0,0,0],
                       'point_is_illustrative_not_pixelwise_manual_GT':'true','exhaustiveness_policy':'UNRESOLVED'}
            if iid in ROIS:
                x0,y0,x1,y1=ROIS[iid];W,H=rec['wh'];assert 0<=x0<x1<=W and 0<=y0<y1<=H
                scale=4 if max(x1-x0,y1-y0)<300 else 2
                # Display only: exact integer crop, nearest-neighbor enlargement for RGB and masks alike.
                native=Image.open(ROOT/rec['output']);cw,ch=(x1-x0)*scale,(y1-y0)*scale
                roi=Image.new('RGB',(3*cw,ch+70),'#111111');d=ImageDraw.Draw(roi)
                for col,name in enumerate(['RGB','Human IDs','Category IDs']):
                    im=native.crop((col*W+x0,28+y0,col*W+x1,28+y1)).resize((cw,ch),Image.Resampling.NEAREST)
                    roi.paste(im,(col*cw,32));d.text((col*cw+3,7),name,fill='white',font=font)
                # Tiny ID highlight is a display outline, not a changed mask.
                if iid=='0000287':
                    px,py=(70-x0)*scale,(257-y0)*scale
                    for col in range(3):d.rectangle([col*cw+px-2,32+py-2,col*cw+px+scale+1,32+py+scale+1],outline='yellow',width=2)
                d.text((3,ch+38),f'TRAIN/{iid}; source ROI {ROIS[iid]}; display x{scale}; native GT unchanged',fill='white',font=font)
                dest=out/f'{iid}_ROI.png';assert not dest.exists();roi.save(dest)
                vals,counts=np.unique(c[y0:y1,x0:x1],return_counts=True)
                crops.append({'image_id':iid,'roi_xyxy_half_open':ROIS[iid],'scale_display_only':scale,'interpolation':'NEAREST',
                    'output':str(dest.relative_to(ROOT)),'sha256':sha(dest),'roi_category_pixels':dict(zip(map(str,vals.tolist()),counts.tolist()))})
            adjudications.append({'image_id':iid,'reviewer':'ASSISTANT','status':FINDINGS[iid][0],'observation':FINDINGS[iid][1],
                                 'verified_numeric_evidence':extra,'source_manifest_reference':'DETAIL_SOURCE_MANIFEST.json',
                                 'independent_human_review':'PENDING','dataset_wide_error_prevalence_estimated':False})
    write_json(run/'DETAIL_ADJUDICATION.json',{'cases':adjudications,'roi_artifacts':crops,'human_review_completed':False,
        'source_readme':'CCIHP_icip.zip::CCIHP_icip/README.md','source_readme_claim':'Sparse/bald for Hair attribute only; Bag20 carried on oneself'})
    before=json.loads((run/'BEFORE.json').read_text());unchanged={p:sha(ROOT/p)==v for p,v in before['protected_hashes'].items()};assert all(unchanged.values())
    parent=ROOT/json.loads((ROOT/'provenance/CCIHP_STAGE0F_ACTIVE_RUN.json').read_text())['run_path']
    previous=json.loads((parent/'BEFORE.json').read_text())
    assets_unchanged={p:stat(ROOT.parent/p)==v for p,v in previous['asset_stats'].items()};assert all(assets_unchanged.values())
    protected={p:sha(ROOT.parent/p)==v for p,v in previous['protected_sha256'].items()};assert all(protected.values())
    write_json(run/'VALIDATION.json',{'status':'PASS','timestamp':datetime.now(timezone.utc).isoformat(),
        'contact_images_visually_screened':200,'contact_pages_recorded':50,'source_verified_native_detail_cases':13,'ROI_cases':5,
        'protected_hashes_unchanged':unchanged,'prior_protected_assets_unchanged':protected,'source_archive_stats_unchanged':assets_unchanged,
        'source_RGB_and_GT_hash_validation':'PASS','coordinate_bounds_and_selected_pixel_checks':'PASS',
        'human_review_completed':False,'dataset_error_prevalence_estimated':False,'primary_dataset_role_changed':False,
        'parser_inference':False,'dataset_bytes_modified':False,'evaluation_policy_frozen':False,
        'scripts':{str(Path(__file__).relative_to(ROOT)):sha(__file__)},'git_repository':'STUDY_HAS_NO_LOCAL_GIT_METADATA'})
    print('200 screens /13 detailed cases /5 ROI exports: validation PASS; human review preserved PENDING')

if __name__=='__main__':main()
