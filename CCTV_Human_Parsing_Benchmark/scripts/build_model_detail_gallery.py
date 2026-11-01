"""CPU visualization of the same fixed six frames and all 15 detected ROIs.

No model loading or rescoring. Private RGB, integer masks, GT and manifests stay
outside Git. Source arrays, GT, scientific protocols and scores are never written.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import argparse
import ast
import colorsys
import csv
import html
import json
import shutil
import sys
import zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from controlled_roi_core import read, atomic, sha, pixel_sha
from controlled_roi_evaluation import project_native
from selected_part_evaluation import final_plane_lookup

P=Path(__file__).resolve().parents[1];W=P.parent
COMMON={'Hair':(40,200,255),'FaceCandidate':(255,225,20),'Upper':(40,240,80),'Lower':(240,70,220)}


def native_catalogs():
    catalog_path=W/'Human_Parsing_Benchmark/protocol/NATIVE_LABEL_MAPPING_DRAFT.csv'
    with catalog_path.open() as stream:
        rows=[r for r in csv.DictReader(stream) if r['source_taxonomy']=='CIHP_PRED']
    cihp=[]
    for row in sorted(rows,key=lambda r:int(r['source_id'])):
        i=int(row['source_id']);color=[round(255*x) for x in colorsys.hsv_to_rgb((i*.61803398875)%1,.7,.95)] if i else [0,0,0]
        cihp.append(dict(id=i,name=row['source_label'],color=color))
    source=W/'third_party/human_parsing/sapiens2/sapiens/dense/src/datasets/seg/seg_utils.py'
    node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.Assign)
              and any(isinstance(t,ast.Name) and t.id=='DOME_CLASSES_29' for t in n.targets))
    dome=ast.literal_eval(node.value.args[0])  # Data literal only: do not import model libraries.
    sapiens=[dict(id=i,name=v['name'],color=v['color']) for i,v in dome]
    if [r['id'] for r in cihp]!=list(range(20)) or [r['id'] for r in sapiens]!=list(range(29)):
        raise ValueError('Native label catalog incomplete/duplicate')
    if sapiens[3]['name']!='Face_Neck' or sapiens[23]['name']!='Upper_Clothing':
        raise ValueError('Wrong native29 catalog')
    return dict(CIHP20=cihp,SAPIENS29=sapiens),dict(CIHP20=dict(path=str(catalog_path.relative_to(W)),sha256=sha(catalog_path)),
        SAPIENS29=dict(path=str(source.relative_to(W)),sha256=sha(source)))


def rgba_common(mask,family,projection):
    mapped=project_native(mask,family,projection)
    rgba=np.zeros((*mask.shape,4),np.uint8);rgba[mask>0]=[155,155,155,190]
    for name,color in COMMON.items():rgba[mapped[name]]=[*color,255]
    return rgba


def rgba_native(mask,catalog):
    lut=np.asarray([r['color']+[0 if r['id']==0 else 255] for r in catalog],np.uint8)
    return lut[mask]


def save_integer(path,mask,catalog):
    # Reconstruct explicitly from native bytes: RGB quantization must not rename IDs.
    im=Image.frombytes('P',(mask.shape[1],mask.shape[0]),mask.astype(np.uint8).tobytes())
    palette=[v for row in catalog for v in row['color']]+[0]*(768-3*len(catalog))
    im.putpalette(palette);im.save(path,transparency=0)
    if not np.array_equal(np.asarray(Image.open(path)),mask):raise ValueError('Native PNG changed integer IDs')


def build(fixed_gallery_path,base_path,gt_path,out):
    sys.path.insert(0,str(W/'Human_Parsing_Benchmark/src'))
    from common_view.packets import read_packet
    fixed,base,facegt=read(fixed_gallery_path),read(base_path),read(gt_path)
    if fixed['base_result_index_sha256']!=sha(base_path) or fixed['Face_GT_binding_sha256']!=sha(gt_path):
        raise ValueError('Gallery and evaluated source bindings differ')
    if sha(W/facegt['base_GT_binding'])!=facegt['base_GT_binding_sha256']:
        raise ValueError('GT parent binding changed')
    binding=read(W/facegt['base_GT_binding']);source=read(W/binding['source_config'])
    frames={r['image_id']:r for r in binding['frames']};sample=[r['image_id'] for r in fixed['figures']]
    if len(sample)!=6 or len(set(sample))!=6:raise ValueError('Expected fixed six-frame sample')
    parent=P/'outputs/cctv-controlled-roi-20261101T115653Z'
    inputs=read(parent/'INPUT_MANIFEST.json');jobs=[r for r in inputs['jobs'] if r['image_id'] in sample]
    if len(jobs)!=15:raise ValueError('Fixed sample ROI workload changed')
    jobs_by_image=defaultdict(list)
    for job in jobs:jobs_by_image[job['image_id']].append(job)
    assignments={(r['image_id'],r['opportunity_id']):r['person_id'] for r in binding['matches'] if r['opportunity_id'] is not None}
    parts=defaultdict(list)
    for part in binding['part_records']:parts[(part['image_id'],part['person_id'])].append(part)
    face_records={(r['image_id'],r['person_id']):r for r in facegt['records']}
    catalogs,label_sources=native_catalogs();projection_path=P/'configs/CONTROLLED_ROI_SCORING_PROTOCOL.json'
    if sha(projection_path)!=read(P/'configs/CONTROLLED_ROI_FACE_NECK_PROTOCOL.json')['projection_protocol_sha256']:
        raise ValueError('Native projection changed')
    projection=read(projection_path)
    out=Path(out);out.mkdir(parents=True,exist_ok=False);(out/'cases').mkdir();(out/'context').mkdir();(out/'by_model').mkdir()
    cases=[];by_id={};panel_manifest=[]
    try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    except OSError:font=ImageFont.load_default()
    for figure in fixed['figures']:
        path=fixed_gallery_path.parent/figure['file']
        if sha(path)!=figure['figure_sha256']:raise ValueError('Existing overview figure changed')
        shutil.copyfile(path,out/'context'/figure['file'])
        frame=frames[figure['image_id']]
        for key,digest in [('Category_ids','Category_sha256'),('Human_ids','Human_sha256')]:
            if sha(W/frame[key])!=frame[digest]:raise ValueError('GT image changed')
        category=np.asarray(Image.open(W/frame['Category_ids']));human=np.asarray(Image.open(W/frame['Human_ids']))
        for job in jobs_by_image[figure['image_id']]:
            iid=job['image_id'];jid=job['job_id'];root=out/'cases'/jid;root.mkdir();x0,y0,x1,y1=job['crop_xyxy']
            rgb_path=W/job['crop_png']
            if sha(rgb_path)!=job['crop_png_sha256']:raise ValueError('Frozen shared ROI PNG changed')
            rgb=np.asarray(Image.open(rgb_path).convert('RGB'))
            if pixel_sha(rgb)!=job['crop_pixel_sha256'] or list(rgb.shape[:2])!=job['crop_hw']:
                raise ValueError('Shared crop identity/geometry changed')
            shutil.copyfile(rgb_path,root/'rgb.png')
            pid=assignments.get((iid,job['opportunity_id']));labels=np.zeros((*category.shape,4),np.uint8);eligible=[]
            if pid is not None:
                for part in parts[iid,pid]:
                    if part['target']=='FaceDomain':continue
                    m=(human==pid)&(category=={'Hair':2,'Upper':5,'Lower':9}[part['target']])
                    labels[m]=[*COMMON[part['target']],255] if part['eligible'] else [160,160,160,255]
                    if part['eligible']:eligible.append(part['target'])
                record=face_records.get((iid,pid))
                if record and record['disposition']=='ELIGIBLE':
                    if sha(W/record['masks'])!=record['masks_sha256']:raise ValueError('Frozen Face GT changed')
                    with np.load(W/record['masks'],allow_pickle=False) as z:
                        for key,color in [('Face',COMMON['FaceCandidate']),('Neck',(30,130,255)),('uncertainty',(255,140,0)),('known_occluder',(255,0,160))]:labels[z[key]]=[*color,255]
                    eligible.append('FaceDomain')
                elif record:labels[(human==pid)&(category==13)]=[160,160,160,255]
            Image.fromarray(labels[y0:y1,x0:x1]).save(root/'gt.png')
            case=dict(id=jid,image_id=iid,opportunity_index=job['opportunity_index'],crop_xyxy=job['crop_xyxy'],
                width=rgb.shape[1],height=rgb.shape[0],YOLO_score=job['YOLO_score'],GT_person_id=pid,
                eligible_targets=eligible,rgb=f'cases/{jid}/rgb.png',gt=f'cases/{jid}/gt.png',
                contact=f'cases/{jid}/all_models.png',sceneOverview='context/'+figure['file'],models={})
            cases.append(case);by_id[jid]=case
    for mid,model in base['models'].items():
        family=model['family'];catalog=catalogs[family]
        for iid,image_jobs in jobs_by_image.items():
            packet=W/model['source_packet_root']/iid;meta,a=read_packet(packet)
            prior=read((W/model['accepted_metrics_path']).parent/(iid+'.json'))
            if (meta['packet_sha256']!=prior['source_packet_sha256'] or meta['model_id']!=mid
                    or sha(packet/'COMMIT.json')!=prior['source_commit_sha256']):
                raise ValueError('Different prediction than evaluated source')
            dm=read((W/frames[iid]['detector_npz']).parent/'COMMIT.json')
            with np.load(W/frames[iid]['detector_npz'],allow_pickle=False) as z:da={k:z[k] for k in ['masks','scores']}
            lookup=final_plane_lookup(meta,a,da,dm['opportunities'])
            for job in image_jobs:
                case=by_id[job['job_id']];j=lookup[job['opportunity_id']];x0,y0,x1,y1=job['crop_xyxy'];root=out/'cases'/job['job_id']/mid;root.mkdir()
                entry={}
                for name,key in [('owned','person_semantic_masks'),('raw','native_roi_unowned_semantic_masks')]:
                    mask=a[key][j,y0:y1,x0:x1]
                    if mask.shape!=(case['height'],case['width']):raise ValueError('ROI/original-grid crop mismatch')
                    # Projection validates every native ID even for native-palette viewing.
                    Image.fromarray(rgba_common(mask,family,projection)).save(root/(name+'_common.png'))
                    Image.fromarray(rgba_native(mask,catalog)).save(root/(name+'_native.png'))
                    save_integer(root/(name+'_integer.png'),mask,catalog)
                    for kind in ['common','native','integer']:entry[name+'_'+kind]=str((root/(name+'_'+kind+'.png')).relative_to(out))
                case['models'][mid]=entry
                panel_manifest.append(dict(job_id=job['job_id'],model_id=mid,source_packet_sha256=meta['packet_sha256'],source_metadata_sha256=sha(packet/'packet.json')))
    def card(rgb,overlay,title):
        if overlay is not None:
            alpha=np.asarray(overlay.getchannel('A'),float)/255*.65
            rgb=Image.fromarray((np.asarray(rgb)*(1-alpha[:,:,None])+np.asarray(overlay)[:,:,:3]*alpha[:,:,None]).astype(np.uint8))
        ratio=min(340/rgb.width,470/rgb.height);im=rgb.resize((round(rgb.width*ratio),round(rgb.height*ratio)),Image.Resampling.NEAREST)
        tile=Image.new('RGB',(360,510),'#151515');tile.paste(im,((360-im.width)//2,32+(470-im.height)//2));ImageDraw.Draw(tile).text((6,7),title,font=font,fill='white');return tile
    for case in cases:
        rgb=Image.open(out/case['rgb']).convert('RGB');cards=[card(rgb,None,'RGB — same saved input'),card(rgb,Image.open(out/case['gt']).convert('RGBA'),'Evaluated GT (partial)')]
        for mid,entry in case['models'].items():cards.append(card(rgb,Image.open(out/entry['owned_common']).convert('RGBA'),mid))
        contact=Image.new('RGB',(1440,1560),'#101010');d=ImageDraw.Draw(contact);d.text((8,5),'Hair cyan | Face candidate yellow | Upper green | Lower pink; owned masks; GT uncolored is not scene background',font=font,fill='white')
        for i,tile in enumerate(cards):contact.paste(tile,((i%4)*360,30+(i//4)*510))
        contact.save(out/case['contact'])
    data=dict(models=[dict(id=mid,family=m['family']) for mid,m in base['models'].items()],cases=cases,native_catalogs=catalogs,
        common_legend=[dict(id=i+1,name=k,color=list(v)) for i,(k,v) in enumerate(COMMON.items())]+[dict(id='OTHER',name='native classes outside four-target view',color=[155,155,155])])
    template=P/'scripts/visualization/model_details.html'
    (out/'index.html').write_text(template.read_text().replace('__DATA_JSON__',json.dumps(data,ensure_ascii=False).replace('</','<\\/')))
    shutil.copyfile(P/'scripts/visualization/model_details.css',out/'viewer.css');shutil.copyfile(P/'scripts/visualization/model_details.js',out/'viewer.js')
    for model in data['models']:
        target='../index.html?model='+model['id'];(out/'by_model'/(model['id']+'.html')).write_text(f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={html.escape(target)}"><a href="{html.escape(target)}">{html.escape(model["id"])}</a>')
    manifest=dict(status='PRIVATE_MODEL_DETAIL_GALLERY_COMPLETE',created_utc=datetime.now(timezone.utc).isoformat(),
        fixed_frames=len(sample),ROIs=len(cases),models=len(data['models']),model_ROI_panels=len(panel_manifest),
        source_fixed_gallery_sha256=sha(fixed_gallery_path),source_non_Face_index_sha256=sha(base_path),Face_GT_binding_sha256=sha(gt_path),
        label_sources=label_sources,source_files={n:sha(P/'scripts'/n) for n in ['build_model_detail_gallery.py','visualization/model_details.html','visualization/model_details.js','visualization/model_details.css']},
        native_integer_PNG_roundtrip='PASS for owned/raw each model and ROI',overlay_geometry='All overlay/crop dimensions identical, no new model resizing',
        selection='All15detectedROIs in prior fixed6images; not selected by scores; missed GT people have no detected ROI and remain visible in scene overview',
        model_calls=0,rescoring=False,source_panels=panel_manifest,private_only=True)
    atomic(out/'MANIFEST.json',manifest)
    archive=out.with_suffix('.zip')
    if archive.exists():raise FileExistsError('Never overwrite an existing private bundle')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=2) as z:
        for path in sorted(out.rglob('*')):
            if path.is_file():z.write(path,str(Path(out.name)/path.relative_to(out)))
    print(json.dumps(dict(status=manifest['status'],frames=6,ROIs=15,models=9,model_ROI_panels=135,bundle_bytes=archive.stat().st_size,model_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixed-gallery',type=Path,required=True);parser.add_argument('--base-results',type=Path,required=True)
    parser.add_argument('--GT',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();build(args.fixed_gallery,args.base_results,args.GT,args.out)
