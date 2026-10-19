"""Build Stage0F human-review package and duplicate-risk evidence from completed audit.

Selection uses TRAIN only. VAL hashes serve split integrity, never model/taxonomy tuning.
No score, no physical-person error prevalence, no reassignment of native CIHP parts.
"""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv, hashlib, io, json, random, sys, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1];WORKSPACE=ROOT.parent;sys.path.insert(0,str(ROOT))
from src.data.ccihp_quality import allocate_strata
from src.data.ccihp_gt import person_planes, reconstruct
from src.data.cihp_datasetninja import decode_bitmap
from audit_ccihp_full_quality import sha, write_json

def main():
    active=json.loads((ROOT/'provenance/CCIHP_STAGE0F_ACTIVE_RUN.json').read_text());run=ROOT/active['run_path']
    full=json.loads((run/'FULL_STRUCTURAL_AUDIT.json').read_text())
    # Metadata only; no corpus of decoded masks is kept in memory.
    rows=[json.loads(line) for line in (run/'IMAGE_AUDIT.jsonl').open()]
    bykey={(r['split'],r['image_id']):r for r in rows}
    eligible=[r for r in rows if r['split']=='Training' and r.get('GT_decode')=='PASS' and r.get('RGB_decode')=='PASS' and r.get('RGB_GT_dimensions_match')]
    strata=defaultdict(list)
    for r in eligible:
        n=r['person_count'];pb='0' if n==0 else '1' if n==1 else '2-3' if n<=3 else '4-7' if n<=7 else '8+'
        rb='pixels<=250000' if r['wh'][0]*r['wh'][1]<=250000 else 'pixels>250000'
        sb='min-area<1pct' if r['min_person_area_fraction']<.01 else 'min-area>=1pct'
        ob='occupancy<25pct' if r['human_occupancy']<.25 else 'occupancy>=25pct'
        bb='bbox-proximity' if r['bbox_intersection_pairs'] else 'no-bbox-proximity'
        strata['|'.join([pb,rb,sb,ob,bb])].append(r['image_id'])
    alloc=allocate_strata({k:len(v) for k,v in strata.items()},200);rng=random.Random(20261012);selected=[];stratum_records=[]
    for k in sorted(strata):
        pop=sorted(strata[k]);n=alloc[k];N=len(pop);sample=sorted(rng.sample(pop,n))
        stratum_records.append({'stratum':k,'population':N,'sample':n,'inclusion_probability':n/N,'weight':N/n})
        selected.extend({'split':'Training','image_id':iid,'stratum':k,'N_h':N,'n_h':n,'inclusion_probability':n/N,'design_weight':N/n} for iid in sample)
    eligible_ids={r['image_id'] for r in eligible}
    review={'run_id':active['run_id'],'seed':20261012,'selection':'stratified simple random without replacement; positive inclusion probability in every populated stratum',
            'sampling_frame_images':len(eligible),'sampling_frame_SHA256':hashlib.sha256('\n'.join(sorted(r['image_id'] for r in eligible)).encode()).hexdigest(),
            'sampling_frame_exclusions':[{'id':r['image_id'],'reason':'GT/RGB decoding or dimension failure'} for r in rows if r['split']=='Training' and r['image_id'] not in eligible_ids],
            'strata':stratum_records,'sample_count':len(selected),'samples':selected,
            'proximity_is_not_verified_occlusion':True,'selection_independent_of_prior_anomaly_sample':True,
            'review_status':'PENDING_INDEPENDENT_HUMAN_REVIEW','error_prevalence':'NOT_ESTIMATED','taxonomy_frozen':False}
    write_json(run/'TRAIN_REVIEW_SAMPLE.json',review)
    # Five exact-disjoint blocks guarantee any <=4-bit pHash neighbor shares a block.
    buckets=defaultdict(list);near=[];bit_lengths=[13,13,13,13,12];shift=[];p=64
    for length in bit_lengths:p-=length;shift.append(p)
    for idx,r in enumerate(rows):
        if r.get('RGB_decode')!='PASS':continue
        v=int(r['phash64'],16);keys=[(k,(v>>s)&((1<<length)-1)) for k,(s,length) in enumerate(zip(shift,bit_lengths))]
        candidates={j for key in keys for j in buckets[key]}
        for j in candidates:
            q=rows[j]
            if r['split']==q['split']=='Training' or r['RGB_decoded_sha256']==q['RGB_decoded_sha256']:continue
            d=(v^int(q['phash64'],16)).bit_count();ar=r['wh'][0]/r['wh'][1];aq=q['wh'][0]/q['wh'][1]
            if d<=4 and abs(ar-aq)/max(ar,aq)<=.05:
                near.append({'a':[q['split'],q['image_id']],'b':[r['split'],r['image_id']],'phash_hamming':d,
                             'aspect_relative_difference':abs(ar-aq)/max(ar,aq),'status':'AUTOMATED_CANDIDATE_NOT_CONFIRMED_DUPLICATE'})
        for key in keys:buckets[key].append(idx)
    write_json(run/'NEAR_DUPLICATE_SCREEN.json',{'method':json.loads((run/'CONFIG.json').read_text())['near_duplicate_screen'],
               'eligible_RGB_images':sum(r.get('RGB_decode')=='PASS' for r in rows),'pairs':near,'candidate_pairs':len(near),
               'auto_exclusion':False,'human_confirmation':'PENDING','missed_similarity_possible':True})
    exact=json.loads((run/'EXACT_DUPLICATES.json').read_text());excluded=set(exact['decoded_RGB']['train_validation_overlap_validation_ids'])
    populations=[]
    for name,filter_fn in [('original_source_target',lambda r:True),('overlap_controlled_source_target',lambda r:r['image_id'] not in excluded),
                           ('readable_source_view',lambda r:r.get('RGB_decode')=='PASS' and r.get('GT_decode')=='PASS' and r.get('RGB_GT_dimensions_match')),
                           ('overlap_controlled_readable_view',lambda r:r['image_id'] not in excluded and r.get('RGB_decode')=='PASS' and r.get('GT_decode')=='PASS' and r.get('RGB_GT_dimensions_match'))]:
        population=[r for r in rows if r['split']=='Validation' and filter_fn(r)]
        populations.append({'population':name,'image_count':len(population),'native_GT_persons':sum(r.get('person_count',0) for r in population),
                            'ids':[r['image_id'] for r in population],'source_split_changed':False,'proposed_only':name!='original_source_target'})
    write_json(run/'VALIDATION_POPULATIONS_DRAFT.json',{'populations':populations,'excluded_exact_overlap_validation_ids':sorted(excluded),'policy_frozen':False})
    pre=json.loads((ROOT/'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json').read_text());taridx={x['path']:x for x in map(json.loads,(ROOT/pre['member_inventory']).open())}
    eactive=json.loads((ROOT/'provenance/CCIHP_STAGE0E_CURRENT_RUN_V2.json').read_text());erun=ROOT/eactive['run_path']
    prior=json.loads((erun/'BOUNDED_CROSS_DATASET_COMPARISON.json').read_text())
    conflicts=[];outputs=ROOT/'outputs/visualizations'/active['run_id'];outputs.mkdir(parents=True,exist_ok=True)
    font=ImageFont.load_default()
    def palette(size):
        a=np.array([[0,0,0]]+[((k*83)%200+35,(k*139)%200+35,(k*191)%200+35) for k in range(1,size)],np.uint8)
        return a
    cp=palette(256);cp[22:]=[255,0,255];hp=palette(256)
    with zipfile.ZipFile(WORKSPACE/'datasets/CCIHP_icip.zip') as z,(WORKSPACE/'datasets/cihp-DatasetNinja.tar').open('rb') as tar:
        def read_tar(name):
            x=taridx[name];tar.seek(x['data_offset']);b=tar.read(x['bytes']);assert hashlib.sha256(b).hexdigest()==x['sha256'];return b
        def maps(split,iid):
            result=[]
            for component in ['Category_ids','Human_ids','Instance_ids']:
                with Image.open(io.BytesIO(z.read(f'CCIHP_icip/dataset/{split}/{component}/{iid}.png'))) as im:im.load();result.append(np.asarray(im).copy())
            return result
        # Recover diagnostics for all previous 47 conflicting objects, never majority-reassign.
        for case in prior['cases']:
            bad={o['part_object_id']:o for o in case['dn_part_associations'] if o['status']!='EXACT_ONE_HUMAN_FULL_SUPPORT'}
            if not bad:continue
            split,iid=case['split'],case['image_id'];c,h,ins=maps(split,iid)
            ann=json.loads(read_tar(f'{split.lower()}/ann/{iid}.jpg.json'))
            for obj in ann['objects']:
                if obj['id'] not in bad:continue
                mask,(x,y),label=decode_bitmap(obj,(c.shape[1],c.shape[0]));mh,mw=mask.shape
                cr=c[y:y+mh,x:x+mw][mask];hr=h[y:y+mh,x:x+mw][mask]
                uu,vv=np.unique(cr,return_counts=True);hu,hv=np.unique(hr,return_counts=True)
                mapping='CIHP dress6 is split across CCIHP upper5/skirt12; raw ID6 is FaceMask' if label==6 else 'Same numeric ID does not prove same category scope or boundaries'
                conflicts.append({'split':split,'image_id':iid,'part_object_id':obj['id'],'CIHP_category':label,'prior_status':bad[obj['id']]['status'],
                                  'CC_category_pixels':{str(k):int(v) for k,v in zip(uu,vv)},'CC_human_pixels':{str(k):int(v) for k,v in zip(hu,hv)},
                                  'unassigned_pixels':int(np.count_nonzero(hr==0)),
                                  'unassigned_CCIHP_background_pixels':int(np.count_nonzero((hr==0)&(cr==0))),
                                  'definition_note':mapping,'cause':'UNRESOLVED_PHYSICAL_OWNERSHIP; structural cross-source discrepancy verified',
                                  'no_majority_repair':True})
        write_json(run/'CROSS_SOURCE_CONFLICT_REVIEW.json',{'objects':conflicts,'status_counts':dict(Counter(x['prior_status'] for x in conflicts)),
                   'native_CIHP_human_reference_available':False,'physical_causes_confirmed':False,'same_numeric_class_is_not_semantic_equivalence':True})
        package=[];fidelity=[]
        extra=[{'split':'Training','image_id':'0033810','selection':'PURPOSIVE_UNKNOWN_LABEL_DIAGNOSTIC_NOT_IN_RANDOM_PREVALENCE_SAMPLE'}]
        for order,s in enumerate(selected+extra):
            split,iid=s['split'],s['image_id'];r=bykey[(split,iid)];c,h,ins=maps(split,iid)
            with Image.open(io.BytesIO(read_tar(f'{split.lower()}/img/{iid}.jpg'))) as im:im.load();rgb=np.asarray(im.convert('RGB')).copy()
            H,W=c.shape;ip=palette(int(ins.max())+1)
            def overlay(colors):return Image.fromarray((rgb.astype(np.float32)*.5+colors.astype(np.float32)*.5).astype(np.uint8))
            human_panel=overlay(hp[h]);draw=ImageDraw.Draw(human_panel)
            # Preserve every positive human ID as its own semantic plane, including class0 holes.
            canonical=person_planes(c,h,ins)
            boundary=np.zeros(c.shape,bool);boundary[:-1]|=h[:-1]!=h[1:];boundary[:,:-1]|=h[:,:-1]!=h[:,1:]
            person_rgb=np.where((h>0)[...,None],cp[c],rgb).copy();person_rgb[boundary]=[255,255,255]
            for p in canonical['persons']:
                x,y,x2,y2=p['bbox_xyxy_half_open'];draw.rectangle([x,y,x2-1,y2-1],outline='white');draw.text((x,y),f"H{p['person_id']}",fill='white',stroke_width=1,stroke_fill='black')
            warnings=((c>0)&(h==0))|((h>0)&(c==0))|((ins>0)&((h==0)|(c==0)))|(c>21)
            wr=rgb.copy();wr[warnings]=[255,0,255];wr[boundary&~warnings]=[255,255,0]
            panels=[Image.fromarray(rgb),human_panel,overlay(cp[c]),overlay(ip[ins]),Image.fromarray(person_rgb),Image.fromarray(wr)]
            titles=['Original RGB (no resize)','Human_ids + local IDs','Category_ids; unknown=magenta','Instance_ids (not person IDs)',
                    'Per-person semantic GT; outlines','Magenta=coverage/unknown; yellow=boundary (not error)']
            for person in canonical['persons']:
                one=rgb.copy();support=person['foreground_mask'];one[support]=cp[c[support]]
                panels.append(Image.fromarray(one));titles.append(f"GT human {person['person_id']} only; neighbor GT hidden")
            panel_rows=(len(panels)+2)//3
            canvas=Image.new('RGB',(W*3,(H+28)*panel_rows),'#171717');dd=ImageDraw.Draw(canvas)
            for k,(panel,title) in enumerate(zip(panels,titles)):
                x=(k%3)*W;y=(k//3)*(H+28);canvas.paste(panel,(x,y+28));dd.text((x+3,y+4),title,fill='white',font=font)
            dest=outputs/f'{split.lower()}_{iid}.png';canvas.save(dest,compress_level=3)
            rec={**s,'image_wh':[W,H],'output':str(dest.relative_to(ROOT)),'output_sha256':sha(dest),'source_maps':r['source_maps'],
                 'source_RGB_sha256':r['RGB_sha256'],'native_person_count':r['person_count'],
                 'all_panels_original_resolution':True,'source_values_changed':False,'automated_counts':r['counts']}
            package.append(rec)
            # Fidelity is executed, not inferred from visualization. All three original arrays round-trip.
            recon=reconstruct(canonical,c.dtype,h.dtype,ins.dtype)
            ok=all(np.array_equal(a,b) for a,b in zip((c,h,ins),recon))
            fidelity.append({'split':split,'image_id':iid,'pixel_exact_all_three_planes':ok})
            if (order+1)%25==0:print(f'[STAGE0F] review overlays: {order+1}/201',flush=True)
        write_json(run/'REVIEW_PACKAGE.json',{'random_sample_images':200,'purposive_extra_images':1,'outputs':package,'human_review':'PENDING',
                   'automated_flags_are_not_confirmed_errors':True,'fidelity':fidelity,'all_fidelity_passed':all(x['pixel_exact_all_three_planes'] for x in fidelity)})
    columns=['split','image_id','stratum','inclusion_probability','design_weight','reviewer','review_date','missing_physical_person',
             'duplicate_person_ID','multiple_people_one_ID','wrong_class','person_part_ownership','boundary_error',
             'ambiguous_occlusion','severity','confirmed_or_suspected','notes','adjudicator','review_status']
    with (run/'HUMAN_REVIEW_CHECKLIST.csv').open('x',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=columns);wr.writeheader()
        for s in selected:wr.writerow({**{k:s[k] for k in columns if k in s},'review_status':'PENDING','confirmed_or_suspected':'NOT_REVIEWED'})
    # Browser-local gallery is a navigation aid; images stay full resolution.
    gallery=['<!doctype html><meta charset="utf-8"><title>CCIHP TRAIN GT review — PENDING</title><h1>200 independent TRAIN images — human review pending</h1><p>Each original panel retains source resolution. Magenta flags are automated; yellow boundaries are not errors. Click the ID for the full PNG. Do not infer occlusion from proximity.</p>']
    for s in package:
        rel=Path(s['output']).name;gallery.append(f'<p><a href="{rel}">{s["split"]}/{s["image_id"]}</a> ({s["native_person_count"]} GT IDs)</p><img loading="lazy" src="{rel}" style="max-width:100%">')
    (outputs/'index.html').write_text('\n'.join(gallery))
    write_json(run/'PREPARATION_COMPLETE.json',{'run_id':active['run_id'],'time_utc':datetime.now(timezone.utc).isoformat(),
               'sample_images':200,'overlays':201,'human_review_pending':True,'fidelity_pass':all(x['pixel_exact_all_three_planes'] for x in fidelity),
               'near_duplicate_candidate_pairs':len(near),'full_benchmark':False})
    print('[STAGE0F] review preparation complete',flush=True)

if __name__=='__main__':main()
