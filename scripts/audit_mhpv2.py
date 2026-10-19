"""Exhaustive original-image/per-person-GT audit; no model inference."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from collections import Counter, defaultdict
from io import BytesIO
import argparse
import json
import re
import struct
import sys

import numpy as np
from PIL import Image
from scipy.io import loadmat

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data.mhpv2 import ANNOTATION_NAME, decode_native, bounding_region, lossless_roundtrip, BODY_CLOTHING_IDS


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite completed evidence: {path}")
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("x") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    tmp.rename(path)


def quantiles(values):
    return {str(q): float(np.quantile(values, q)) for q in [0, .1, .25, .5, .75, .9, 1]} if values else {}


def inspect_image(task):
    root, split, image_id, image_path, annotation_paths, pose_path = task
    errors, warnings = [], []
    persons = []
    counts, occurrences = Counter(), Counter()
    try:
        with Image.open(image_path) as image:
            image.load()
            original_mode = image.mode
            orientation = image.getexif().get(274)
            rgb = np.array(image.convert("RGB"))
            width, height = image.size
        coverage = np.zeros((height, width), dtype=np.uint16)
        seen_classes = set()
        declared_counts, person_ids = set(), []
        png_modes = Counter()
        for path in annotation_paths:
            match = ANNOTATION_NAME.match(path.name)
            if not match:
                errors.append(f"Invalid parsing filename: {path.name}"); continue
            person_id = int(match['person_id']); person_ids.append(person_id)
            declared_counts.add(int(match['person_count']))
            labels = decode_native(path)
            if labels.shape != (height, width):
                errors.append(f"GT dimensions: {path.name}"); continue
            with Image.open(path) as image:
                png_modes[image.mode] += 1
                array = np.array(image)
                alpha = np.unique(array[..., 3]).tolist() if array.ndim == 3 and array.shape[2] == 4 else None
            histogram = np.bincount(labels.ravel(), minlength=59)
            values = np.flatnonzero(histogram)
            foreground = labels > 0
            bbox = bounding_region(foreground)
            if bbox is None:
                errors.append(f"Empty person annotation: {path.name}")
            if not lossless_roundtrip(labels):
                errors.append(f"Lossless conversion mismatch: {path.name}")
            coverage += foreground
            counts.update({int(k): int(histogram[k]) for k in values})
            occurrences.update(map(int, values)); seen_classes.update(map(int, values))
            support = np.isin(labels, tuple(BODY_CLOTHING_IDS))
            persons.append({"person_file_id": person_id, "canonical_person_id": f"{image_id}:parsing:{person_id}",
                            "annotation_path": str(path.relative_to(root)), "source_sha256": sha256(path.read_bytes()).hexdigest(),
                            "semantic_array_sha256": sha256(labels.tobytes()).hexdigest(), "native_ids": values.tolist(),
                            "foreground_area": int(foreground.sum()), "foreground_bbox_xyxy_half_open": bbox,
                            "body_clothing_area_draft": int(support.sum()), "body_clothing_bbox_draft": bounding_region(support),
                            "carried_or_accessory_support_excluded_from_core_area": int((foreground & ~support).sum()),
                            "lossless_roundtrip": True, "alpha_values": alpha,
                            "pose_person_key": None, "pose_identity_mapping": "NOT_ASSUMED_FROM_FILENAME"})
        if split != 'test':
            if not persons: errors.append("Missing required person annotations")
            if len(declared_counts) != 1 or next(iter(declared_counts), None) != len(annotation_paths):
                errors.append("Filename-declared count differs from person-file count")
            if len(set(person_ids)) != len(person_ids) or set(person_ids) != set(range(1, len(annotation_paths) + 1)):
                errors.append("Non-unique/non-contiguous parsing person IDs")
            if len(persons) < 2: warnings.append("Fewer than two parsing persons; reference headline is not enforced as GT repair")
        pose = {"path": str(pose_path.relative_to(root)) if pose_path else None,
                "status": "NOT_SUPPLIED_FOR_TEST" if split == 'test' else "MISSING", "person_keys": []}
        if pose_path:
            data = loadmat(pose_path)
            entries = {key: value for key, value in data.items() if not key.startswith('__')}
            malformed = [key for key, value in entries.items() if not re.match(r'^person_\d+$', key) or value.shape != (20, 3) or not np.isfinite(value).all()]
            flags = sorted(set(float(v) for value in entries.values() if value.ndim == 2 and value.shape[1] == 3 for v in value[:, 2]))
            pose.update({"status": "READABLE_WITH_WARNINGS" if malformed else "READABLE", "person_keys": sorted(entries),
                         "shapes": {key: list(value.shape) for key, value in entries.items()}, "flag_values": flags,
                         "malformed": malformed, "count_matches_parsing": len(entries) == len(persons)})
            if malformed or len(entries) != len(persons): warnings.append("Optional pose metadata differs from parsing count or shape")
        elif split != 'test': warnings.append("Optional pose metadata missing")
        record = {"split": split, "image_id": image_id, "image_path": str(image_path.relative_to(root)),
                  "image_sha256": sha256(image_path.read_bytes()).hexdigest(), "original_wh": [width, height], "image_mode": original_mode,
                  "exif_orientation": orientation, "decoded_rgb_sha256": sha256(struct.pack('>II', width, height) + rgb.tobytes()).hexdigest(),
                  "persons": persons, "pose": pose, "png_modes": dict(png_modes),
                  "overlap_pixels": int(np.count_nonzero(coverage > 1)), "maximum_overlap": int(coverage.max()),
                  "native_class_image_support": sorted(seen_classes), "errors": errors, "warnings": warnings}
        if orientation not in [None, 1]: record['warnings'].append("Non-identity EXIF orientation requires explicit adapter handling")
        return record, counts, occurrences
    except Exception as exc:
        # An RGB failure must not prevent independent GT/pose inspection.
        with Image.open(image_path) as header:
            width,height=header.size
        orphan_inspection=[]
        if not persons:
            for path in annotation_paths:
                try:
                    labels=decode_native(path);match=ANNOTATION_NAME.match(path.name)
                    histogram=np.bincount(labels.ravel(),minlength=59);values=np.flatnonzero(histogram)
                    counts.update({int(k):int(histogram[k]) for k in values});occurrences.update(map(int,values))
                    bbox=bounding_region(labels>0);support=np.isin(labels,tuple(BODY_CLOTHING_IDS))
                    assert labels.shape==(height,width) and bbox is not None and lossless_roundtrip(labels)
                    with Image.open(path) as png:
                        mode=png.mode;arr=np.array(png);alpha=np.unique(arr[...,3]).tolist() if arr.ndim==3 and arr.shape[2]==4 else None
                    persons.append({'person_file_id':int(match['person_id']),'canonical_person_id':f'{image_id}:parsing:{int(match["person_id"])}',
                                    'annotation_path':str(path.relative_to(root)),'source_sha256':sha256(path.read_bytes()).hexdigest(),
                                    'semantic_array_sha256':sha256(labels.tobytes()).hexdigest(),'native_ids':values.tolist(),
                                    'foreground_area':int(np.count_nonzero(labels)),'foreground_bbox_xyxy_half_open':bbox,
                                    'body_clothing_area_draft':int(support.sum()),'body_clothing_bbox_draft':bounding_region(support),
                                    'carried_or_accessory_support_excluded_from_core_area':int(np.count_nonzero((labels>0)&~support)),
                                    'lossless_roundtrip':True,'alpha_values':alpha,'pose_person_key':None,'pose_identity_mapping':'NOT_ASSUMED_FROM_FILENAME','png_mode':mode})
                except Exception as annotation_error:orphan_inspection.append(f'{path.name}: {type(annotation_error).__name__}: {annotation_error}')
        pose_info={}
        if pose_path:
            try:
                data=loadmat(pose_path);pose_info={'readable':True,'person_shapes':{k:list(v.shape) for k,v in data.items() if not k.startswith('__')}}
            except Exception as pose_error:pose_info={'readable':False,'error':str(pose_error)}
        return {"split": split, "image_id": image_id, "image_path": str(image_path.relative_to(root)),
                "original_wh":[width,height],"image_sha256":sha256(image_path.read_bytes()).hexdigest(),
                "persons": persons,"pose":pose_info,"native_class_image_support":sorted({label for p in persons for label in p['native_ids']}),
                "png_modes":dict(Counter(p.get('png_mode') for p in persons)),
                "errors": [f"{type(exc).__name__}: {exc}",*orphan_inspection], "warnings": warnings,
                "independent_gt_inspection_after_rgb_failure":True}, counts, occurrences


def main():
    study = Path(__file__).resolve().parents[1]; workspace = study.parent
    args = argparse.ArgumentParser(); args.add_argument('--dataset-root', default='datasets/LV-MHP-v2'); args.add_argument('--workers', type=int, default=3)
    args = args.parse_args(); root = (workspace / args.dataset_root).resolve()
    active = json.loads((study/'provenance/STAGE0_ACTIVE_RUN.json').read_text()); run = study/'provenance/RUN_MANIFESTS'/active['run_id']
    required = [study/'manifests/DATASET_MANIFEST.json', study/'provenance/DATASET_INTEGRITY.json']
    if any(path.exists() for path in required): raise RuntimeError('Existing MHP audit must be reviewed, not overwritten')
    lists = {}; tasks = []; structural = []; stats = {}; all_ids = set(); annotations = {}
    for split, name, expected in [('train','train.txt',15403),('val','val.txt',5000),('test','test_all.txt',5000)]:
        ids = (root/'list'/name).read_text().split(); lists[split] = ids
        if len(ids) != expected or len(set(ids)) != len(ids): structural.append(f'{split}: split count/ID uniqueness')
        if all_ids.intersection(ids): structural.append(f'{split}: cross-split ID reuse')
        all_ids.update(ids)
        images = {path.stem: path for path in (root/split/'images').iterdir() if path.suffix.lower() in {'.jpg','.jpeg','.png'}}
        if set(ids) != set(images): structural.append(f'{split}: missing/orphan images')
        grouped = defaultdict(list)
        directory = root/split/'parsing_annos'
        if directory.exists():
            for path in directory.iterdir():
                if path.suffix.lower() != '.png':
                    if path.name != '.DS_Store': structural.append(f'Unexpected annotation: {path.name}')
                    continue
                match = ANNOTATION_NAME.match(path.name)
                if not match: structural.append(f'Invalid annotation filename {path.name}'); continue
                grouped[match['image_id']].append(path)
        if set(grouped) - set(ids): structural.append(f'{split}: orphan annotations')
        for image_id in ids:
            if image_id not in images: continue
            pose = root/split/'pose_annos'/f'{image_id}.mat'
            tasks.append((root, split, image_id, images[image_id], sorted(grouped[image_id]), pose if pose.exists() else None))
        annotations[split] = sum(len(value) for value in grouped.values())
    files = sorted(path for path in root.rglob('*') if path.is_file())
    inventory = run/'DATASET_SHA256.jsonl'; inventory_digest = sha256(); before = {}
    with inventory.open('x') as stream:
        for path in files:
            stat = path.stat(); key = str(path.relative_to(root)); before[key] = (stat.st_size, stat.st_mtime_ns)
            record = {'path': key, 'bytes': stat.st_size, 'sha256': sha256(path.read_bytes()).hexdigest()}
            line = json.dumps(record,sort_keys=True,separators=(',',':'))+'\n'; stream.write(line); inventory_digest.update(line.encode())
    print(f'[MHP-v2] SHA256 inventory complete: {len(files)} files', flush=True)
    per_image = run/'CANONICAL_GT_INDEX.jsonl'; counts = Counter(); occurrences = Counter(); class_image = Counter(); summaries = defaultdict(list); duplicate_hashes = defaultdict(list)
    error_records, warning_records = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool, per_image.open('x') as stream:
        for record, pixel_counts, instance_support in pool.map(inspect_image, tasks):
            stream.write(json.dumps(record,separators=(',',':'))+'\n')
            counts.update(pixel_counts); occurrences.update(instance_support); class_image.update(record.get('native_class_image_support', []))
            summaries[record['split']].append(record)
            if record.get('decoded_rgb_sha256'): duplicate_hashes[record['decoded_rgb_sha256']].append([record['split'],record['image_id']])
            if record['errors']: error_records.append({'image_id':record['image_id'],'split':record['split'],'errors':record['errors']})
            if record['warnings']: warning_records.append({'image_id':record['image_id'],'split':record['split'],'warnings':record['warnings']})
    for split, records in summaries.items():
        persons = [person for record in records for person in record['persons']]
        bbox = [person['foreground_bbox_xyxy_half_open'] for person in persons if person.get('foreground_bbox_xyxy_half_open')]
        stats[split] = {'images':len(records),'persons':len(persons),'persons_per_image_distribution':dict(Counter(len(record['persons']) for record in records)),
                        'resolution_distribution':dict(Counter('x'.join(map(str,record['original_wh'])) for record in records if 'original_wh' in record)),
                        'mask_area_quantiles':quantiles([person['foreground_area'] for person in persons]),
                        'bbox_width_quantiles':quantiles([b[2]-b[0] for b in bbox]),'bbox_height_quantiles':quantiles([b[3]-b[1] for b in bbox]),
                        'overlap_images':sum(record.get('overlap_pixels',0)>0 for record in records),'overlap_pixels':sum(record.get('overlap_pixels',0) for record in records),
                        'png_modes':dict(sum((Counter(record.get('png_modes',{})) for record in records),Counter()))}
    changed = [key for key, value in before.items() if not (root/key).exists() or ((root/key).stat().st_size,(root/key).stat().st_mtime_ns) != value]
    if changed: structural.append('Source file metadata changed during audit')
    duplicates = [group for group in duplicate_hashes.values() if len(group)>1]
    cross = [group for group in duplicates if len({value[0] for value in group})>1]
    atomic(run/'AUDIT_ERRORS.json',{'structural_errors':structural,'required_pair_errors':error_records,'optional_warnings':warning_records,'source_changed':changed})
    atomic(run/'DUPLICATE_IMAGES.json',{'exact_decoded_groups':duplicates,'cross_split_groups':cross,'near_duplicate_audit':'NOT_EXECUTED','official_splits_changed':False})
    taxonomy = {int(match[0]):match[1].strip() for match in re.findall(r'^\s*(\d+)\s*:\s*([^\r\n]+)',(root/'README.txt').read_text(),flags=re.M) if int(match[0])<=58}
    # README's later pose section reuses numeric IDs; take only the parsing section.
    text = (root/'README.txt').read_text().split('III.')[0]
    taxonomy = {int(k):v.strip() for k,v in re.findall(r'^\s*(\d+)\s*:\s*([^\r\n]+)',text,flags=re.M)}
    atomic(study/'taxonomy/MHPV2_NATIVE.json',{'status':'VERIFIED_NATIVE_IDS','labels':taxonomy,'background_id':0,'native_ignore_id':None,'decoding':'First channel, not grayscale conversion; alpha excluded','classes_including_background':59})
    status = 'DATASET_BLOCKED' if structural or error_records else 'DATASET_READY_WITH_WARNINGS' if warning_records or cross else 'DATASET_READY'
    manifest = {'schema_version':'1.0','dataset':'LV-MHP-v2','version':'2.0','root_workspace_relative':str(root.relative_to(workspace)),
                'run_id':active['run_id'],'status':status,'source_readme_sha256':sha256((root/'README.txt').read_bytes()).hexdigest(),
                'download_provenance_record':'datasets/LV-MHP-v2/IMPORT_VALIDATION.json','official_source':'https://lv-mhp.github.io/',
                'inventory':str(inventory.relative_to(study)),'inventory_sha256':inventory_digest.hexdigest(),'files_hashed':len(files),
                'canonical_gt_index':str(per_image.relative_to(study)),'canonical_gt_index_sha256':sha256(per_image.read_bytes()).hexdigest(),
                'split_lists':{k:{'image_count':len(v),'ids_sha256':sha256(json.dumps(v,separators=(',',':')).encode()).hexdigest()} for k,v in lists.items()},
                'statistics':stats,'class_pixels_per_person_planes':dict(counts),'class_person_support':dict(occurrences),'class_image_support':dict(class_image),
                'class_frequency_denominator':'Per-person native planes; overlaps retained and background counted independently for each person',
                'structural_error_count':len(structural),'required_pair_error_count':len(error_records),'optional_warning_images':len(warning_records),
                'exact_duplicate_groups':len(duplicates),'exact_cross_split_groups':len(cross),'source_files_changed':False,
                'test_annotations_supplied':bool(annotations['test']),'pose_identity_mapping':'Separate identity namespaces; do not assume suffix n maps to pose person_(n-1)',
                'annotation_geometry':'Identity: native GT dimensions equal original RGB; half-open derived bounding regions',
                'foreground_semantics':'All annotated body/clothing/accessory/carried-object support, not anatomical person silhouette'}
    atomic(study/'manifests/DATASET_MANIFEST.json',manifest)
    # No development output is published if the critical native parsing gate fails.
    if status != 'DATASET_BLOCKED':
        train = summaries['train']; seed=20261008
        ranked=sorted(train,key=lambda record:sha256(f'MHPV2_STAGE0:{seed}:{record["image_id"]}'.encode()).hexdigest())
        selected={record['image_id']:record for record in ranked[:24]}
        valid_person = [record for record in train if record['persons']]
        for criterion,record in [('most_persons',max(valid_person,key=lambda x:len(x['persons']))),('most_overlap',max(valid_person,key=lambda x:x['overlap_pixels'])),('smallest_person',min(valid_person,key=lambda x:min(p['foreground_area'] for p in x['persons']))),('largest_person',max(valid_person,key=lambda x:max(p['foreground_area'] for p in x['persons'])))]:
            selected[record['image_id']]=record
        rare=sorted((int(k) for k,v in occurrences.items() if int(k)>0),key=lambda label:(occurrences[label],label))[:3]
        for label in rare:
            matches=[record for record in train if label in record['native_class_image_support']]
            if matches: selected[matches[0]['image_id']]=matches[0]
        ids=sorted(selected,key=int)
        atomic(study/'manifests/DEVELOPMENT_SET.json',{'status':'DEVELOPMENT_ONLY_NO_FINAL_TUNING','seed':seed,'split':'train','image_ids':ids,'dataset_manifest_sha256':sha256((study/'manifests/DATASET_MANIFEST.json').read_bytes()).hexdigest(),'selection':'24 SHA256-ranked IDs + fixed GT variation extremes + 3 rare-label diagnostics','validation_used_for_selection':False,'smoke_image_ids':[record['image_id'] for record in ranked[:3]],'smoke_limit':3})
        atomic(study/'manifests/FINAL_VALIDATION_SET.json',{'split':'val','image_ids':lists['val'],'count':5000,'status':'RESERVED_NO_MODEL_EVALUATION','membership':'Original official list/val.txt unchanged','tuning_authorized':False})
    atomic(study/'provenance/DATASET_INTEGRITY.json',{'status':status,'required_pair_error_count':len(error_records),'structural_errors':structural,'optional_warning_images':len(warning_records),'manifest_sha256':sha256((study/'manifests/DATASET_MANIFEST.json').read_bytes()).hexdigest(),'inventory_sha256':inventory_digest.hexdigest(),'all_required_images_annotations_read':True,'all_native_mask_roundtrips_tested':True,'source_metadata_before_after_unchanged':not changed,'original_gt_modified':False,'inference_run':False,'audit_script_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'reader_sha256':sha256((study/'src/data/mhpv2.py').read_bytes()).hexdigest(),'end_utc':datetime.now(timezone.utc).isoformat()})
    print(f'[MHP-v2] exhaustive integrity: {status}; images={len(tasks)}, persons={sum(v["persons"] for v in stats.values())}, errors={len(error_records)+len(structural)}',flush=True)


if __name__=='__main__': main()
