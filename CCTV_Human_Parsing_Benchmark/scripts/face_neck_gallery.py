"""Private fixed-sample comparison gallery from saved controlled-ROI packets.

Uses the six prior pilot frames, never score-selected images. Display-only native
composition precedes projection; quantitative metrics use per-person full grids.
No new inference; CCTV images/filenames/manifests remain outside public Git.
"""
from pathlib import Path
import argparse
import html
import json
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from controlled_roi_core import read, atomic, sha
from controlled_roi_evaluation import project_native

P=Path(__file__).resolve().parents[1];W=P.parent
COLORS={'Hair':(40,200,255),'FaceCandidate':(255,225,20),'Upper':(40,240,80),'Lower':(240,70,220)}


def create(base_path, gt_path, out):
    sys.path.insert(0,str(W/'Human_Parsing_Benchmark/src'))
    from common_view.packets import read_packet
    from common_view.core import compose_native
    base,facegt=read(base_path),read(gt_path)
    binding=read(W/facegt['base_GT_binding']);source=read(W/binding['source_config'])
    prediction=read(P/'outputs/cctv-controlled-roi-20261101T115653Z/CONFIG.json')
    sample=sorted({r['packet'].split('/')[-1] for r in prediction['reuse']['Sapiens2_0.4b'].values()})
    if len(sample)!=6:raise ValueError('Prior fixed sample changed')
    members={m['id']:m for m in source['members']};frames={r['image_id']:r for r in binding['frames']}
    projection=read(P/'configs/CONTROLLED_ROI_SCORING_PROTOCOL.json')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    try:f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
    except OSError:f=ImageFont.load_default()
    manifests=[]
    def panel(rgb,labels,title):
        data=rgb.copy()
        if labels:
            for mask,color in labels:
                data[mask]=(data[mask].astype(float)*.45+np.asarray(color)*.55).astype(np.uint8)
        im=Image.fromarray(data);ratio=min(640/im.width,365/im.height);im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.NEAREST)
        card=Image.new('RGB',(640,400),'#151515');card.paste(im,((640-im.width)//2,32+(365-im.height)//2));ImageDraw.Draw(card).text((8,6),title,font=f,fill='white');return card
    for iid in sample:
        member=members[iid];frame=frames[iid];rgb_path=W/source['dataset_root']/'Images'/(member['stem']+'.jpg')
        if sha(rgb_path)!=member['RGB_sha256']:raise ValueError('Gallery RGB input changed')
        rgb=np.asarray(Image.open(rgb_path).convert('RGB'));category=np.asarray(Image.open(W/frame['Category_ids']));human=np.asarray(Image.open(W/frame['Human_ids']))
        gtlabels=[]
        for target,native in [('Hair',2),('Upper',5),('Lower',9)]:
            mask=np.zeros(category.shape,bool)
            for part in binding['part_records']:
                if part['image_id']==iid and part['target']==target and part['eligible']:mask|=(human==part['person_id'])&(category==native)
            gtlabels.append((mask,COLORS[target]))
        for record in facegt['records']:
            if record['image_id']!=iid or record['disposition']!='ELIGIBLE':continue
            with np.load(W/record['masks'],allow_pickle=False) as z:
                gtlabels.extend([(z['Face'],COLORS['FaceCandidate']),(z['Neck'],(30,130,255)),(z['uncertainty'],(255,140,0))])
        cards=[panel(rgb,None,'RGB — fixed prior sample'),panel(rgb,gtlabels,'GT evaluated positives / Neck blue / uncertain orange')];panels=[]
        for mid,info in base['models'].items():
            packet=W/info['source_packet_root']/iid;meta,a=read_packet(packet)
            prior=read((W/info['accepted_metrics_path']).parent/(iid+'.json'))
            if meta['packet_sha256']!=prior['source_packet_sha256']:raise ValueError('Gallery prediction differs from scored source')
            native=compose_native(a['person_semantic_masks'],a['person_scores'],category.shape)
            projected=project_native(native,info['family'],projection)
            cards.append(panel(rgb,[(projected[k],color) for k,color in COLORS.items()],mid))
            panels.append(dict(model_id=mid,source_packet_sha256=meta['packet_sha256'],source_metadata_sha256=sha(packet/'packet.json')))
        canvas=Image.new('RGB',(1920,1665),'#101010')
        draw=ImageDraw.Draw(canvas);draw.text((8,5),'Hair cyan | Face CANDIDATE yellow (Sapiens includes Neck) | Upper green | Lower pink; GT is PARTIAL, uncolored is not scene background',font=f,fill='white')
        for j,card in enumerate(cards):canvas.paste(card,((j%3)*640,35+(j//3)*400))
        name=iid+'.png';canvas.save(out/name)
        manifests.append(dict(image_id=iid,file=name,figure_sha256=sha(out/name),input_sha256=member['RGB_sha256'],panels=panels))
    atomic(out/'MANIFEST.json',dict(selection='six fixed prior pilot images, not score selected',
        base_result_index_sha256=sha(base_path),Face_GT_binding_sha256=sha(gt_path),
        display_composition='highest frozen detector score among non-background native labels; native composition before target projection',
        quantitative_scoring='per-person original full grid; gallery downsampling/composition is display only',
        predictions_clipped_by_GT=False,Face_candidate_is_not_strict_face_only=True,model_calls=0,figures=manifests))
    page=['<!doctype html><meta charset="utf-8"><title>CCTV controlled ROI comparison</title><style>body{font:16px sans-serif;max-width:1500px;margin:auto}img{width:100%}</style><h1>Fixed six-frame / nine-model gallery</h1><p>Private CCTV assets. Predictions are unchanged. GT is partial; orange marks Face uncertainty. Uncolored GT is not scene background. Face candidate includes Neck in Sapiens.</p>']
    for row in manifests:page.append(f'<h2>{html.escape(row["image_id"])}</h2><a href="{row["file"]}"><img loading="lazy" src="{row["file"]}"></a>')
    (out/'index.html').write_text('\n'.join(page))
    print(json.dumps(dict(figures=len(manifests),models_per_figure=9,model_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-results',type=Path,required=True);parser.add_argument('--GT',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args();create(a.base_results,a.GT,a.out)
