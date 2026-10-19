"""Fixed TRAIN GT diagnostics. Composites are visualization-only, not truth."""
from pathlib import Path
from hashlib import sha256
from io import BytesIO
import json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.io import loadmat
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.data.mhpv2 import decode_native


def main():
    study=Path(__file__).resolve().parents[1];workspace=study.parent;manifest=json.loads((study/'manifests/DATASET_MANIFEST.json').read_text());root=workspace/manifest['root_workspace_relative']
    selected=manifest['diagnostic_selection'];development=json.loads((study/'manifests/DEVELOPMENT_SET.json').read_text())
    requested=[('ordinary',development['smoke_image_ids'][0]),*list(selected['extremes'].items()),*[(f'rare_class_{label}',image_id) for label,image_id in selected['rare_class_examples'].items()]]
    ids={value for _,value in requested};records={}
    with (study/manifest['canonical_gt_index']).open() as stream:
        for line in stream:
            record=json.loads(line)
            if record['split']=='train' and record['image_id'] in ids:records[record['image_id']]=record
    palette=np.rint(loadmat(root/'LV-MHP-v2_colormap.mat')['MHP_colormap']*255).astype(np.uint8)
    out=study/'outputs/visualizations'/manifest['run_id']/'mhpv2_gt';out.mkdir(parents=True,exist_ok=False)
    cases=[];thumbs=[]
    for case,(reason,image_id) in enumerate(requested,1):
        record=records[image_id];assert not record['errors']
        with Image.open(root/record['image_path']) as image:rgb=image.convert('RGB')
        labels=[decode_native(root/person['annotation_path']) for person in record['persons']]
        if reason=='smallest_person':focus=int(np.argmin([person['foreground_area'] for person in record['persons']]))
        elif reason.startswith('rare_class_'):focus=next(index for index,array in enumerate(labels) if np.any(array==int(reason.split('_')[-1])))
        else:focus=int(np.argmax([person['foreground_area'] for person in record['persons']]))
        native=labels[focus];buffer=BytesIO();Image.fromarray(native).save(buffer,format='PNG');buffer.seek(0)
        with Image.open(buffer) as image:canonical=np.array(image)
        assert np.array_equal(native,canonical)
        identities=np.array(rgb);coverage=np.zeros(native.shape,np.uint16)
        for index,array in enumerate(labels):
            fg=array>0;coverage+=fg;color=np.array([(61+index*71)%256,(103+index*97)%256,(181+index*43)%256])
            identities[fg]=np.rint(.45*identities[fg]+.55*color).astype(np.uint8)
        identities[coverage>1]=[255,0,255]
        native_vis=palette[native];canonical_vis=palette[canonical]
        panels=[rgb,Image.fromarray(identities),Image.fromarray(native_vis),Image.fromarray(canonical_vis)]
        title=['Original RGB','IDs; overlaps magenta','Native parsing: selected ID','Canonical lossless plane']
        canvas=Image.new('RGB',(1680,600),'white');draw=ImageDraw.Draw(canvas)
        draw.text((5,5),f'{reason}: train/{image_id}; N={len(labels)}; selected parsing ID={record["persons"][focus]["person_file_id"]}; native={rgb.width}x{rgb.height}',fill='black')
        for column,image in enumerate(panels):
            draw.text((column*420+5,30),title[column],fill='black');scale=min(410/image.width,520/image.height)
            wh=(max(1,int(image.width*scale)),max(1,int(image.height*scale)))
            resize=Image.Resampling.BILINEAR if column in [0,1] else Image.Resampling.NEAREST
            canvas.paste(image.resize(wh,resize),(column*420+(420-wh[0])//2,60))
        # Native instance labels are never merged into a metric artifact.
        path=out/f'case_{case:02d}_gt.png';canvas.save(path)
        cases.append({'reason':reason,'split':'train','image_id':image_id,'focus_person_file_id':record['persons'][focus]['person_file_id'],
                      'person_count':len(labels),'source_image_sha256':record['image_sha256'],'source_annotation_hashes':[person['source_sha256'] for person in record['persons']],
                      'image':str(path.relative_to(study)),'sha256':sha256(path.read_bytes()).hexdigest(),'native_vs_canonical_pixels_identical':True,
                      'manual_review':'PENDING','identity_display_precedence':'Last person only for display; shared support highlighted magenta; individual native planes retained'})
        thumbs.append(canvas.resize((840,300),Image.Resampling.BILINEAR))
    sheet=Image.new('RGB',(1680,((len(thumbs)+1)//2)*300),'white')
    for index,image in enumerate(thumbs):sheet.paste(image,((index%2)*840,(index//2)*300))
    sheet.save(out/'contact_sheet.png')
    result={'status':'NUMERICAL_FIDELITY_PASS_VISUAL_REVIEW_PENDING','cases':cases,'contact_sheet':str((out/'contact_sheet.png').relative_to(study)),
            'test_or_validation_used':False,'no_model_inference':True,'source_dataset_modified':False}
    p=study/'provenance/MHPV2_GT_VISUAL_VALIDATION.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(f'[GT] {len(cases)} fixed training diagnostics generated')


if __name__=='__main__':main()
