"""Copy canonical metrics and render 16 frozen examples. No model inference/rescore."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,csv,hashlib,html,json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'))
from cihp_benchmark.data import LABELS,read_sample
from cihp_benchmark.evaluation import compose
from render_cihp_comparisons import overlay,palette

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def csvwrite(p,rows):
    with Path(p).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)

def build():
    unit='presentation-four-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    index=json.loads((P/'manifests/CIHP_NATIVE_COHORT_INDEX.json').read_text());parent=W/'Human_Parsing_MHPv2_Study/outputs/cihp_native'/index['parent_run_id']
    raw=parent/'presentations'/unit;raw.mkdir(parents=True,exist_ok=False);metrics=P/'metrics'/unit;metrics.mkdir(parents=True,exist_ok=False);record=P/'runs'/index['parent_run_id']/unit;record.mkdir(parents=True,exist_ok=False)
    pop_path=parent/'FROZEN_POPULATION.json';population=json.loads(pop_path.read_text());pop={r['id']:r for r in population['members']};assert len(pop)==5000
    sample_path=parent/'FROZEN_DIAGNOSTIC_SAMPLE.json';assert sha(sample_path)==sha(P/'manifests/CIHP_NATIVE_DIAGNOSTIC_SAMPLE.json');sample=json.loads(sample_path.read_text());assert len(sample['ids'])==16
    # Choose presentation examples before opening predictions: first frozen ID per GT-only stratum.
    showcase={}
    for iid in sample['ids']:
        x=pop[iid];key=f"people_ge5={int(x['G_loc']>=5)};area_gt187500={int(x['wh'][0]*x['wh'][1]>187500)}";showcase.setdefault(key,iid)
    assert len(showcase)==4
    rows=[];classrows=[];personrows=[];systems={};sources=[];complete_ids=[]
    for row in index['models']:
        mid=row['model_id'];source=P/row['canonical_source'];assert sha(source)==row['canonical_source_sha256'];closure=json.loads(source.read_text());sources.append({'path':row['canonical_source'],'sha256':sha(source)})
        if 'summary' in closure:
            canonical=next(r for r in closure['summary'] if r['model_id']==mid);folder=W/closure['artifact_root']/'validation'/mid
        else:canonical=closure;folder=W/closure['raw_root']/'assembled/validation'/mid
        assert canonical['status']==row['status'] and canonical['complete']==row['complete']
        r=dict(model_id=mid,execution_status=canonical['status'],work_status='COMPLETE' if canonical['status']=='COMPLETE' else 'PAUSED_NOT_CANCELLED',expected=5000,complete=canonical['complete'],failed=canonical['failed'],invalid=canonical['invalid'],not_attempted=canonical['not_attempted'],mIoU_20_including_BG=None,mIoU_19_foreground=None,native_reference_mIoU20=None,resource_policy=row['resource_policy'],execution_segment=row['execution_segment_or_record'],canonical_source=row['canonical_source'],missing_main_score_reason=None if canonical['status']=='COMPLETE' else 'STRICT_COMPLETE_NOT_SATISFIED; paused after recorded failure; successful subset not a full-population score')
        if canonical['status']=='COMPLETE':
            assert canonical['complete']==5000 and canonical['failed']==canonical['invalid']==canonical['not_attempted']==0
            ledger=folder/'FRAMES.jsonl';frames=[json.loads(l) for l in ledger.read_text().splitlines()];assert len(frames)==5000 and len({x['image_id'] for x in frames})==5000 and set(x['image_id'] for x in frames)==set(pop) and all(x['status']=='COMPLETE' for x in frames)
            metric_path=folder/'METRICS.json';m=json.loads(metric_path.read_text());primary=m['primary'];assert primary is not None and primary['mIoU_20_including_BG']==row['mIoU_20_including_BG'] and primary['mIoU_19_foreground']==row['mIoU_19_foreground']
            assert primary['labels']==LABELS and len(primary['IoU'])==20
            if 'metrics' in closure:assert m==closure['metrics']
            r.update(mIoU_20_including_BG=primary['mIoU_20_including_BG'],mIoU_19_foreground=primary['mIoU_19_foreground'],native_reference_mIoU20=m['native_reference_primary']['mIoU_20_including_BG'] if m.get('native_reference_primary') else None)
            for k in range(20):classrows.append(dict(model_id=mid,class_id=k,class_name=LABELS[k],IoU=primary['IoU'][k],GT_pixel_support=primary['GT_pixel_support'][k],predicted_pixel_support=primary['predicted_pixel_support'][k],union_pixels=primary['union'][k]))
            for threshold,v in m['person_metrics'].items():
                assert v['G_loc']==v['G_sem']==17520 and v['TP']+v['FN']==v['G_loc'];personrows.append(dict(model_id=mid,mask_IoU_threshold=float(threshold),**v))
            write(metrics/(mid+'.json'),{'model_id':mid,'primary':primary,'person_metrics':m['person_metrics'],'native_reference_primary':m.get('native_reference_primary'),'source_metrics':str(metric_path.relative_to(W)),'source_metrics_sha256':sha(metric_path)})
            systems[mid]={'folder':folder,'committed':{x['image_id']:x for x in frames},'metrics':m,'metadata_source':str(metric_path.relative_to(W))};complete_ids.append(mid)
            sources.extend([{'path':str(metric_path.relative_to(W)),'sha256':sha(metric_path)},{'path':str(ledger.relative_to(W)),'sha256':sha(ledger),'unique_complete_IDs':5000}])
        rows.append(r)
    assert len(complete_ids)==4
    # CPI: inspect all cohort execution ledgers; exclude diagnostic and older protocols.
    cpi=[]
    for mid in [r['model_id'] for r in rows if r['execution_status']!='COMPLETE']:
        locations=[parent/'validation'/mid,*parent.glob('continuations/*/segments/'+mid),*parent.glob('rounds/*/segments/'+mid)];success={};failures=[];attempts=[]
        for folder in locations:
            ledger=folder/'FRAMES.jsonl'
            if not ledger.exists():continue
            entries=[json.loads(l) for l in ledger.read_text().splitlines()];assert len({r['image_id'] for r in entries})==len(entries)
            for e in entries:
                assert e['image_id'] in pop;attempts.append(e)
                if e['status']=='COMPLETE':
                    assert e['image_id'] not in success;success[e['image_id']]=e
                else:failures.append(e)
            audit=folder.parent.parent/'final_audit'/mid/'RECONCILED.json'
            if audit.exists():a=json.loads(audit.read_text());assert a['source_ledger_sha256']==sha(ledger) if a['verified_count'] else True
            sources.append({'path':str(ledger.relative_to(W)),'sha256':sha(ledger)})
        row=next(r for r in rows if r['model_id']==mid);assert len(success)==row['complete']
        cpi.append({'model_id':mid,'successful_unique_ids':sorted(success),'successful_unique_count':len(success),'failed_unique_ids':sorted({e['image_id'] for e in failures}),'failed_attempt_count':sum(e['status']=='FAILED' for e in failures),'total_VAL_attempts':len(attempts),'diagnostic_attempts_excluded':True,'work_status':'PAUSED_NOT_CANCELLED'})
    csvwrite(metrics/'COHORT_STATUS.csv',rows);csvwrite(metrics/'PER_CLASS.csv',classrows);csvwrite(metrics/'PERSON_METRICS.csv',personrows);write(metrics/'CPI_ATTEMPT_COUNTS.json',cpi)
    # Deterministic original-grid figures, private artifacts only.
    (raw/'panels').mkdir();(raw/'previews').mkdir();figures=[];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
    for iid in sample['ids']:
        truth,gtmeta=read_sample(W/'datasets/CIHP','Validation',iid);rgb=truth['rgb'];h,w=rgb.shape[:2];assert [w,h]==pop[iid]['wh'] and gtmeta['RGB']['file_sha256']==pop[iid]['RGB_sha256']
        for kind in ['Category_ids','Human_ids','Instance_ids']:assert gtmeta[kind]['file_sha256']==pop[iid]['GT_sha256'][kind]
        canvas=Image.new('RGB',(6*w,2*(h+42)),'#202027');draw=ImageDraw.Draw(canvas)
        def panel(col,row,img,label):
            x=col*w;y=row*(h+42);draw.text((x+3,y+10),label,font=font,fill='white');canvas.paste(img,(x,y+42))
        panel(0,0,Image.fromarray(rgb),'Original RGB');panel(0,1,Image.fromarray(rgb),'Same RGB / original pixel grid');panel(1,0,overlay(rgb,truth['Category_ids']),'GT / CIHP20 semantic');panel(1,1,overlay(rgb,truth['Human_ids'],True),'GT / Human_ids')
        records=[]
        for col,mid in enumerate(complete_ids,2):
            folder=systems[mid]['folder'];frame=systems[mid]['committed'][iid];packet=W/frame['packet'];meta=json.loads((packet/'packet.json').read_text());assert meta['model_id']==mid and meta['image_id']==iid and meta['original_wh']==[w,h] and meta['input_sha256']==pop[iid]['RGB_sha256'];digest=sha(packet/'prediction.npz');assert digest==meta['packet_sha256']==frame['packet_sha256']
            with np.load(packet/'prediction.npz',allow_pickle=False) as arrays:
                planes=arrays['person_semantic_masks'];extents=arrays['person_extents'];scores=arrays['person_scores'];assert planes.shape==extents.shape and list(planes.shape[1:])==[h,w] and planes.dtype.kind in 'ui' and np.all(planes<20);semantic=compose(planes,scores,(h,w));owners=np.zeros((h,w),np.int32)
                for j in sorted(range(len(scores)),key=lambda j:(float(scores[j]),-j)):owners[extents[j]]=j+1
            short={'QANet_CIHP_HRNetW48_512x384':'QANet HRNet-W48','M2FP_R101_CIHP':'M2FP R101','D2FP_R101_CIHP':'D2FP R101','RPR_CIHP':'RP-R-CNN R50'}[mid]
            panel(col,0,overlay(rgb,semantic),short+' / application labels');panel(col,1,overlay(rgb,owners,True),short+f' / final extents ({len(scores)})')
            records.append({'model_id':mid,'packet':str(packet.relative_to(W)),'packet_sha256':digest,'metadata_sha256':sha(packet/'packet.json'),'source_segment':meta.get('continuation_id',meta.get('parent_run_id')),'final_person_count':len(scores),'source_route':meta['source_track'],'original_wh':[w,h]})
        full=raw/'panels'/(iid+'.png');canvas.save(full);preview=canvas.copy();preview.thumbnail((1800,1800));preview.save(raw/'previews'/(iid+'.jpg'),quality=93)
        figures.append({'image_id':iid,'GT_people':pop[iid]['G_loc'],'original_wh':[w,h],'GT_sha256':pop[iid]['GT_sha256'],'RGB_sha256':pop[iid]['RGB_sha256'],'figure':'panels/'+iid+'.png','preview':'previews/'+iid+'.jpg','figure_sha256':sha(full),'figure_size':list(canvas.size),'is_showcase':iid in showcase.values(),'packets':records})
    colors=palette();legend=''.join(f'<span class="label"><i style="background:rgb{tuple(map(int,colors[k]))}"></i>{k}: {html.escape(name)}</span>' for k,name in enumerate(LABELS))
    cards=''.join(f'<article id="{r["image_id"]}"><h2>{r["image_id"]} | GT people={r["GT_people"]} | {r["original_wh"]}</h2><p>{"Presentation example: first frozen ID in GT-only stratum" if r["is_showcase"] else "Frozen 16-image sample"}</p><a href="{r["figure"]}"><img loading="lazy" src="{r["preview"]}" alt="{r["image_id"]}: RGB, GT and four systems"></a><p>Top: semantic labels. Bottom: person extents. Columns: RGB / GT / QANet / M2FP / D2FP / RP-R-CNN. Click for full original-grid PNG. Local person numbers/colors are NOT matched identities across panels.</p></article>' for r in figures)
    page='<!doctype html><html lang="en"><meta charset="utf-8"><title>CIHP four-model presentation</title><style>body{font:16px system-ui;background:#13151b;color:#eee;margin:24px;max-width:1850px}a{color:#8dc7ff}article{border-top:1px solid #697080;padding:14px 0}img{width:100%;height:auto}.label{display:inline-flex;align-items:center;margin:7px}.label i{width:20px;height:20px;display:inline-block;margin-right:6px;border:1px solid #888}</style><h1>CIHP — four completed application pipelines</h1><p>Private local research figures; do not redistribute dataset images automatically. All16 pre-score IDs retained. No inference, rescore, or score-based image selection. Overlay alpha:65% label/35% RGB. Unpainted background reveals RGB; it does NOT imply predicted foreground.</p><p>Fixed presentation IDs: '+html.escape(', '.join(showcase.values()))+'</p><nav>'+''.join(f'<a href="#{i}">{i}</a> ' for i in sample['ids'])+'</nav><div>'+legend+'</div>'+cards+'</html>'
    (raw/'index.html').write_text(page)
    manifest={'work_unit':unit,'parent_run_id':parent.name,'frozen_sample':sample,'sample_sha256':sha(sample_path),'population_sha256':sha(pop_path),'showcase_rule':'First frozen ID per annotated people>=5 x area>187500 stratum; set before opening predictions in this report, after aggregate results already existed','showcase_by_stratum':showcase,'new_model_inference':False,'new_full_rescore':False,'source_GT_modified':False,'mask_geometry':'All full panels original grid, no categorical mask resize. JPEG previews for display only.','semantic_composition':'Exact frozen compose of saved hard-label planes/scores; owners display highest confidence over extents, local IDs not GT matching','source_renderer_sha256':sha(__file__),'records':figures}
    write(raw/'MANIFEST.json',manifest);write(record/'VISUALIZATION_MANIFEST.json',manifest)
    provenance={'work_unit':unit,'created_utc':datetime.now(timezone.utc).isoformat(),'status':'REPORTING_FOUR_COMPLETE_CPI_PAUSED','models_complete':complete_ids,'sources':sources,'frozen_config_sha256':sha(P/'configs/cihp_native_six.json'),'population_sha256':sha(pop_path),'metrics_directory':str(metrics.relative_to(P)),'raw_gallery':str(raw.relative_to(W)),'gallery_manifest_sha256':sha(raw/'MANIFEST.json'),'metric_operations':'Copy exact canonical scalars/support; count ledgers and check algebra; no model inference or pixelwise rescore','source_script_sha256':sha(__file__),'CPI_attempt_counts':cpi}
    write(record/'PROVENANCE.json',provenance);write(record/'REPORT_DATA.json',{'status':rows,'per_class':classrows,'person_metrics':personrows,'showcase_by_stratum':showcase});write(raw/'PROVENANCE.json',provenance)
    print(json.dumps({'work_unit':unit,'metrics':str(metrics.relative_to(P)),'run_record':str(record.relative_to(P)),'gallery':str(raw.relative_to(W)),'figures':len(figures),'validated_selected_packets':sum(len(r['packets']) for r in figures),'showcase':showcase}))
    return unit

if __name__=='__main__':build()
