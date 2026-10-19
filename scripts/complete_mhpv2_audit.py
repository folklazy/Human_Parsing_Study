"""Inspect GT behind four failed RGB decodes; preserve initial audit evidence."""
from pathlib import Path
from hashlib import sha256
from collections import Counter,defaultdict
from datetime import datetime,timezone
import json
import numpy as np
from audit_mhpv2 import inspect_image,quantiles,atomic


def main():
    study=Path(__file__).resolve().parents[1];workspace=study.parent
    path=study/'manifests/DATASET_MANIFEST.json';manifest=json.loads(path.read_text());root=workspace/manifest['root_workspace_relative']
    run=study/'provenance/RUN_MANIFESTS'/manifest['run_id'];initial=json.loads((study/'provenance/DATASET_INTEGRITY.json').read_text())
    archive=study/'reports/archive'/('stage0_dataset_initial_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));archive.mkdir(parents=True,exist_ok=False)
    originals=['manifests/DATASET_MANIFEST.json','provenance/DATASET_INTEGRITY.json','taxonomy/native/D2FP_LIP.yaml']
    records=[]
    for name in originals:
        original=study/name;target=archive/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(original.read_bytes())
        records.append({'original':name,'archived':str(target.relative_to(study)),'sha256_before':sha256(original.read_bytes()).hexdigest()})
    source_path=study/'scripts/audit_mhpv2.py';code=source_path.read_text();start=code.index('        # An RGB failure must not prevent independent GT/pose inspection.')
    end=code.index('\n\n\ndef main():',start)
    old=code[:start]+'        return {"split": split, "image_id": image_id, "image_path": str(image_path.relative_to(root)),\n                "persons": persons, "errors": [f"{type(exc).__name__}: {exc}"], "warnings": warnings}, counts, occurrences'+code[end:]
    assert sha256(old.encode()).hexdigest()==initial['audit_script_sha256']
    (run/'audit_mhpv2_INITIAL.py').write_text(old)
    errors=json.loads((run/'AUDIT_ERRORS.json').read_text())['required_pair_errors']; replacements={};supplement=[]
    pixel_add=Counter();occurrence_add=Counter();image_add=Counter()
    for item in errors:
        split,image_id=item['split'],item['image_id'];image=root/split/'images'/(image_id+'.jpg');annotations=sorted((root/split/'parsing_annos').glob(image_id+'_*.png'));pose=root/split/'pose_annos'/(image_id+'.mat')
        record,counts,occurrences=inspect_image((root,split,image_id,image,annotations,pose))
        assert record['independent_gt_inspection_after_rgb_failure'] and len(record['persons'])==len(annotations)
        assert len(record['errors'])==1 and all(p['lossless_roundtrip'] for p in record['persons'])
        replacements[(split,image_id)]=record;pixel_add.update(counts);occurrence_add.update(occurrences);image_add.update(record['native_class_image_support'])
        supplement.append({'split':split,'image_id':image_id,'annotations_independently_decoded':len(annotations),'all_gt_dimensions_native_ids_and_roundtrips_pass':True,'rgb_error_preserved':record['errors']})
    output=run/'CANONICAL_GT_INDEX_V2.jsonl';all_records=[]
    with (study/manifest['canonical_gt_index']).open() as input_stream,output.open('x') as output_stream:
        for line in input_stream:
            value=json.loads(line);value=replacements.get((value['split'],value['image_id']),value);all_records.append(value);output_stream.write(json.dumps(value,separators=(',',':'))+'\n')
    manifest['canonical_gt_index']=str(output.relative_to(study));manifest['canonical_gt_index_sha256']=sha256(output.read_bytes()).hexdigest()
    for name,added in [('class_pixels_per_person_planes',pixel_add),('class_person_support',occurrence_add),('class_image_support',image_add)]:
        for key,value in added.items():manifest[name][str(key)]=manifest[name].get(str(key),0)+value
    grouped=defaultdict(list)
    for value in all_records:grouped[value['split']].append(value)
    for split,items in grouped.items():
        persons=[person for item in items for person in item['persons']];bbox=[person['foreground_bbox_xyxy_half_open'] for person in persons]
        manifest['statistics'][split].update({'persons':len(persons),'persons_per_image_distribution':dict(Counter(len(item['persons']) for item in items)),
            'resolution_distribution':dict(Counter('x'.join(map(str,item['original_wh'])) for item in items)),
            'mask_area_quantiles':quantiles([person['foreground_area'] for person in persons]),
            'bbox_width_quantiles':quantiles([b[2]-b[0] for b in bbox]),'bbox_height_quantiles':quantiles([b[3]-b[1] for b in bbox]),
            'png_modes':dict(sum((Counter(item.get('png_modes',{})) for item in items),Counter()))})
    assert sum(item['persons'] for item in manifest['statistics'].values())==54316
    manifest.update({'native_person_planes_fully_decoded':54316,'rgb_fully_decoded':25399,'required_rgb_decode_failures':4,
                     'native_gt_critical_errors':0,'overlap_statistics_scope':'All successfully decoded RGB records; four RGB-failure records have independent GT decoding but overlap computed separately',
                     'supplement_evidence':str((run/'GT_BEHIND_RGB_FAILURES.json').relative_to(study))})
    overlap=[]
    for (split,image_id),item in replacements.items():
        coverage=np.zeros((item['original_wh'][1],item['original_wh'][0]),np.uint16)
        from src.data.mhpv2 import decode_native
        for person in item['persons']:coverage+=decode_native(root/person['annotation_path'])>0
        count=int(np.count_nonzero(coverage>1));overlap.append({'split':split,'image_id':image_id,'overlap_pixels':count})
        manifest['statistics'][split]['overlap_pixels']+=count;manifest['statistics'][split]['overlap_images']+=count>0
    manifest['overlap_statistics_scope']='All 54316 native person planes, including independent GT inspection behind four RGB failures'
    # Original memberships are always reserved, even while the dataset gate is blocked.
    train=[value for value in all_records if value['split']=='train' and not value['errors']];seed=20261008
    ranked=sorted(train,key=lambda r:sha256(f'MHPV2_STAGE0:{seed}:{r["image_id"]}'.encode()).hexdigest());selected={r['image_id']:r for r in ranked[:24]}
    extremes={'most_persons':max(train,key=lambda r:len(r['persons'])),'most_overlap':max(train,key=lambda r:r['overlap_pixels']),
              'smallest_person':min(train,key=lambda r:min(p['foreground_area'] for p in r['persons'])),
              'largest_person':max(train,key=lambda r:max(p['foreground_area'] for p in r['persons']))}
    for record in extremes.values():selected[record['image_id']]=record
    rare=sorted((int(key) for key in manifest['class_person_support'] if int(key)>0),key=lambda k:(manifest['class_person_support'][str(k)],k))[:3]
    rare_cases={}
    for label in rare:
        matches=[record for record in ranked if label in record['native_class_image_support']]
        if matches:record=matches[0];selected[record['image_id']]=record;rare_cases[str(label)]=record['image_id']
    manifest['diagnostic_selection']={'extremes':{key:value['image_id'] for key,value in extremes.items()},'rare_class_examples':rare_cases}
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    atomic(study/'manifests/DEVELOPMENT_SET.json',{'status':'DRAFT_DATASET_BLOCKED_NO_MODEL_EXECUTION','seed':seed,'split':'train','image_ids':sorted(selected,key=int),
        'selection':'24 SHA256-ranked readable train IDs + GT variation extremes + rare-label examples','integrity_diagnostic_selection_not_protocol_tuning':True,
        'excluded_unreadable_train_ids':['1396','18613','24328'],'original_train_split_modified':False,'validation_used_for_selection':False,
        'smoke_image_ids':[r['image_id'] for r in ranked[:3]],'smoke_limit':3,'execution_authorized_now':False})
    atomic(study/'manifests/FINAL_VALIDATION_SET.json',{'status':'RESERVED_ORIGINAL_SPLIT_DATASET_BLOCKED','split':'val','image_ids':(root/'list/val.txt').read_text().split(),
        'count':5000,'tuning_authorized':False,'original_membership_unchanged':True,'unreadable_rgb_ids':['17844'],'cross_train_content_overlap_requires_review':True})
    atomic(run/'GT_BEHIND_RGB_FAILURES.json',{'status':'ANNOTATION_FIDELITY_PASS_RGB_GATE_STILL_BLOCKED','additional_person_planes':16,'cases':supplement,'overlap':overlap})
    initial.update({'manifest_sha256':sha256(path.read_bytes()).hexdigest(),'reader_source_revision_note':'Original audit source preserved in run; patched source separately verifies GT after RGB failure',
                    'audit_script_sha256':sha256(source_path.read_bytes()).hexdigest(),'all_native_person_planes_decoded':54316,
                    'rgb_fully_decoded':25399,'rgb_decode_failures':4,'native_gt_critical_errors':0,'end_utc':datetime.now(timezone.utc).isoformat()})
    (study/'provenance/DATASET_INTEGRITY.json').write_text(json.dumps(initial,indent=2)+'\n')
    # Source-native D2FP label names, not borrowed labels from another repository.
    from build_taxonomy_drafts import literal_assignment
    labels=literal_assignment(workspace/'third_party/human_parsing/D2FP/d2fp/data/datasets/register_lip_semseg.py','LIP_SEMSEG_CATEGORIES')
    import yaml
    p=study/'taxonomy/native/D2FP_LIP.yaml';value=yaml.safe_load(p.read_text());value['labels']=dict(enumerate(labels));value['source_workspace_relative']='third_party/human_parsing/D2FP/d2fp/data/datasets/register_lip_semseg.py';value['source_sha256']=sha256((workspace/value['source_workspace_relative']).read_bytes()).hexdigest();p.write_text(yaml.safe_dump(value,sort_keys=False))
    for record in records:record['sha256_after']=sha256((study/record['original']).read_bytes()).hexdigest()
    atomic(run/'DATASET_AUDIT_REVISION_ARCHIVE.json',{'reason':'Inspect all GT despite failed RGB decoding; preserve blocker and official memberships; correct D2FP native source attribution','records':records})
    print('[MHP-v2] all 54316 person annotations verified; four original RGB failures remain BLOCKED')


if __name__=='__main__':main()
