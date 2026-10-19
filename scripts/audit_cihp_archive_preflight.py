"""Read-only TAR/container, converted annotation and bounded source-fidelity audit.

No extraction, parser, benchmark, large download or ownership reconstruction.
"""
from pathlib import Path, PurePosixPath
from collections import Counter, defaultdict
from hashlib import sha256
from datetime import datetime, timezone
from io import BytesIO
import json
import random
import sys
import tarfile
import numpy as np
from PIL import Image, ImageDraw

S=Path(__file__).resolve().parents[1];W=S.parent
sys.path.insert(0,str(S))
from src.data.cihp_datasetninja import NATIVE_IDS,decode_bitmap,reconstruct_semantic


def digest(path):
    h=sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()


def publish(path,obj):
    if path.exists():raise FileExistsError(path)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)


def main():
    active=json.loads((S/'provenance/CIHP_ARCHIVE_PREFLIGHT_ACTIVE_RUN.json').read_text())
    run=S/active['run_path'];archive=W/'datasets/cihp-DatasetNinja.tar'
    if (run/'ARCHIVE_PREFLIGHT.json').exists():raise FileExistsError('Run completed; create new run')
    stat=archive.stat();archive_hash=digest(archive)
    print('[CIHP] archive SHA256 recorded',flush=True)
    errors=Counter();examples=[];metadata={};counts=Counter();obj_counts=Counter();classes=Counter()
    object_keys=Counter();ann_keys=Counter();image_tags=object_tags=0;ownership_fields=Counter()
    ids=defaultdict(set);image_paths={};ann_paths={};image_grids={};ann_grids={};sample_ann={}
    names=set();part_ids=set();duplicates=[];byte_hashes=defaultdict(list)
    fields={'personId','person_id','humanId','human_id','groupId','group_id','parentId','parent_id','instanceId','instance_id'}
    def error(reason,name):
        errors[reason]+=1
        if len(examples)<100:examples.append({'member':name,'reason':reason})
    with tarfile.open(archive,'r:') as tar:
        members=tar.getmembers()
        images=[m for m in members if m.isfile() and '/img/' in m.name]
        sample_paths=[]
        for split,n in [('training',6),('validation',6),('testing',2)]:
            population=sorted([m.name for m in images if m.name.startswith(split+'/')])
            sample_paths+=random.Random(20261008).sample(population,n)
        reference_ids=['0002190','0005008','0012008','0026375','0032190']
        for m in images:
            if Path(m.name).stem in reference_ids+['0035374']:sample_paths.append(m.name)
        sample_paths=sorted(set(sample_paths));sample_anns={p.replace('/img/','/ann/')+'.json' for p in sample_paths}
        publish(run/'PREFLIGHT_SAMPLE.json',{'seed':20261008,'random_policy':'6 TRAIN + 6 VAL + 2 TEST; separate source-reference 5 and converter special-case 1',
                'images':sample_paths,'selection_before_pixel_inspection':True,'human_quality_sample':False,'benchmark':False})
        inventory_tmp=run/'TAR_MEMBER_SHA256.jsonl.tmp';ann_tmp=run/'ANNOTATION_SUMMARY.jsonl.tmp'
        with inventory_tmp.open('x') as inventory,ann_tmp.open('x') as annlog,(run/'PROGRESS.log').open('x') as progress:
            end_data=0
            for m in members:
                path=PurePosixPath(m.name);end_data=max(end_data,m.offset_data+((m.size+511)//512)*512)
                if m.name in names:duplicates.append(m.name)
                names.add(m.name)
                if path.is_absolute() or '..' in path.parts:error('UNSAFE_PATH',m.name)
                if not(m.isfile() or m.isdir()):error('NON_REGULAR_OR_DIRECTORY_ENTRY',m.name)
                if m.offset_data+m.size>stat.st_size:error('TRUNCATED_MEMBER_BOUND',m.name)
                counts['members']+=1
                if not m.isfile():counts['directories']+=1;continue
                b=tar.extractfile(m).read()
                if len(b)!=m.size:error('SHORT_MEMBER_PAYLOAD',m.name)
                h=sha256(b).hexdigest();counts['regular_files']+=1
                inventory.write(json.dumps({'path':m.name,'bytes':m.size,'sha256':h,
                    'header_offset':m.offset,'data_offset':m.offset_data},separators=(',',':'))+'\n')
                if m.name in ['meta.json','LICENSE.md','README.md']:
                    metadata[m.name]=json.loads(b) if m.name.endswith('.json') else b.decode()
                    continue
                parts=path.parts
                if len(parts)!=3 or parts[0] not in ['training','validation','testing']:
                    error('UNEXPECTED_LAYOUT',m.name);continue
                split,kind,name=parts
                if kind=='img':
                    i=Path(name).stem;counts[split+'_images']+=1;ids[split].add(i)
                    image_paths[(split,i)]=m.name;byte_hashes[h].append(m.name)
                    try:
                        with Image.open(BytesIO(b)) as image:
                            if image.format!='JPEG':error('UNEXPECTED_RGB_FORMAT',m.name)
                            image_grids[(split,i)]=image.size
                    except Exception as e:error('RGB_HEADER_UNREADABLE:'+type(e).__name__,m.name)
                elif kind=='ann':
                    i=name.removesuffix('.jpg.json');counts[split+'_annotations']+=1;ann_paths[(split,i)]=m.name
                    try:
                        ann=json.loads(b);ann_keys.update(ann.keys());w,h=ann['size']['width'],ann['size']['height']
                        if type(w)!=int or type(h)!=int or min(w,h)<=0:raise ValueError('Invalid dimensions')
                        ann_grids[(split,i)]=(w,h)
                        objects=ann['objects'];obj_counts[split]+=len(objects)
                        if not objects:counts[split+'_empty_annotations']+=1
                        image_tags+=len(ann.get('tags',[]))
                        for key in fields:
                            if key in ann:ownership_fields['annotation:'+key]+=1
                        for obj in objects:
                            object_keys.update(obj.keys());classes[obj.get('classTitle','MISSING')]+=1
                            object_tags+=len(obj.get('tags',[]))
                            for key in fields:
                                if key in obj:ownership_fields['object:'+key]+=1
                            obj_id=obj.get('id')
                            if obj_id in part_ids:error('DUPLICATE_OBJECT_ID',m.name)
                            part_ids.add(obj_id)
                            try:
                                tile,xy,label=decode_bitmap(obj,(w,h));counts['bitmap_decoded']+=1
                                if not np.array_equal(tile,np.unpackbits(np.packbits(tile),count=tile.size).reshape(tile.shape)):
                                    error('BITMAP_BINARY_ROUNDTRIP_FAILURE',m.name)
                            except Exception as e:error('BITMAP_INVALID:'+str(e),m.name)
                        annlog.write(json.dumps({'split':split,'image_id':i,'wh':[w,h],'objects':len(objects),
                            'class_counts':dict(Counter(o.get('classTitle') for o in objects)),
                            'image_tags':len(ann.get('tags',[])),'annotation_sha256':sha256(b).hexdigest()},separators=(',',':'))+'\n')
                        if m.name in sample_anns:sample_ann[m.name]=ann
                    except Exception as e:error('ANNOTATION_INVALID:'+str(e),m.name)
                else:error('UNEXPECTED_SUBFOLDER',m.name)
                if counts['regular_files']%5000==0:
                    progress.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'regular_files':counts['regular_files'],
                        'bitmaps_validated':counts['bitmap_decoded'],'errors':sum(errors.values())})+'\n');progress.flush()
        inventory_tmp.replace(run/'TAR_MEMBER_SHA256.jsonl');ann_tmp.replace(run/'ANNOTATION_SUMMARY.jsonl')
        print('[CIHP] complete payload/JSON/bitmap scan finished',flush=True)
        pair_missing=sorted(set(image_paths)^set(ann_paths))
        dim_mismatch=[list(k) for k in set(image_grids)&set(ann_grids) if image_grids[k]!=ann_grids[k]]
        with archive.open('rb') as f:
            f.seek(end_data);tail=f.read();trailer_ok=len(tail)>=1024 and not any(tail)
        source_tree=json.loads((run/'sources/PGN_OFFICIAL_TREE.json').read_text())
        official_val={Path(e['path']).stem for e in source_tree['tree'] if
            e['path'].startswith('evaluation/Instance_part_val/') and e['path'].endswith('.txt')}
        val_exact=ids['validation']==official_val and len(official_val)==5000 and not source_tree['truncated']
        allids=set().union(*ids.values());disjoint=sum(len(v) for v in ids.values())==len(allids)
        # Strict full JPEG loading is bounded, unlike exhaustive header/payload scan.
        samples=[];references=[]
        out=S/'outputs/visualizations'/active['run_id']/'cihp_preflight';out.mkdir(parents=True,exist_ok=False)
        palette=np.array([[0,0,0]]+[[int((j*67+80)%256),int((j*101+45)%256),int((j*149+130)%256)] for j in range(1,20)],np.uint8)
        for n,p in enumerate(sample_paths,1):
            split,_,name=p.split('/');i=Path(name).stem;blob=tar.extractfile(p).read()
            rec={'split':split,'image_id':i,'image_member':p,'image_sha256':sha256(blob).hexdigest()}
            try:
                with Image.open(BytesIO(blob)) as im:im.load();rgb=im.convert('RGB')
                rec['strict_full_RGB_decode']='PASS';rec['wh']=list(rgb.size)
            except Exception as e:
                rec['strict_full_RGB_decode']='FAIL';rec['error']=str(e);samples.append(rec);continue
            ann=sample_ann[p.replace('/img/','/ann/')+'.json']
            sem,diag=reconstruct_semantic(ann);rec.update(diag);rec['objects']=len(ann['objects'])
            rec['semantic_array_sha256']=sha256(sem.tobytes()).hexdigest()
            panels=[('Original RGB',rgb),('Converted semantic parts (NOT human IDs)',Image.fromarray(palette[sem]))]
            reference_dir=run/'sources/reference_fixtures'
            if i in reference_ids:
                reference_rgb=(reference_dir/f'images_{i}.jpg').read_bytes()
                with Image.open(BytesIO(reference_rgb)) as im:im.load();ref_rgb=np.array(im.convert('RGB'))
                with Image.open(reference_dir/f'labels_{i}.png') as im:im.load();ref=np.array(im)
                if ref.ndim==3:ref=ref[...,0]
                matching_grid=ref.shape==sem.shape
                comparison={'image_id':i,'archive_split':split,'same_JPEG_bytes':sha256(blob).hexdigest()==sha256(reference_rgb).hexdigest(),
                    'RGB_pixels_identical':np.array_equal(np.array(rgb),ref_rgb),'GT_dimensions_identical':matching_grid,
                    'GT_semantic_pixels_identical':np.array_equal(ref,sem),'native_reference_labels':np.unique(ref).tolist(),
                    'mismatched_pixels':int(np.count_nonzero(ref!=sem)) if matching_grid else None,
                    'native_GT_sha256':digest(reference_dir/f'labels_{i}.png'),
                    'reference_scope':'Five official repository demo semantic maps; not whole-release or human-ID fidelity'}
                references.append(comparison);panels.append(('Official repo demo semantic GT',Image.fromarray(palette[ref]) if ref.max()<20 else Image.fromarray(ref)))
            if split!='testing' and (i in reference_ids or n<=4):
                arr=np.array(rgb);fg=sem>0;arr[fg]=np.rint(.5*arr[fg]+.5*palette[sem][fg]).astype(np.uint8)
                panels.append(('Converted part overlay; no person grouping',Image.fromarray(arr)))
                canvas=Image.new('RGB',(420*len(panels),540),'white');draw=ImageDraw.Draw(canvas)
                draw.text((5,5),f'{split}/{i}; bitmap objects={len(ann["objects"])}; person IDs unavailable',fill='black')
                for j,(title,image) in enumerate(panels):
                    draw.text((j*420+5,28),title,fill='black');factor=min(410/image.width,470/image.height)
                    wh=(int(image.width*factor),int(image.height*factor));canvas.paste(image.resize(wh,Image.Resampling.NEAREST),(j*420+5,60))
                path=out/f'{split}_{i}_semantic_diagnostic.png';canvas.save(path);rec['diagnostic']=str(path.relative_to(S));rec['diagnostic_sha256']=digest(path)
            samples.append(rec)
    archive_hash_after=digest(archive)
    if archive_hash_after!=archive_hash:raise RuntimeError('Archive changed during audit')
    result={'schema_version':'1.0','run_id':active['run_id'],'end_utc':datetime.now(timezone.utc).isoformat(),
        'archive_workspace_relative':str(archive.relative_to(W)),'archive_bytes':stat.st_size,'archive_sha256':archive_hash,
        'archive_sha256_after':archive_hash_after,'archive_modified':False,'extraction_performed':False,
        'container_integrity':'PASS' if trailer_ok and not duplicates and not any(errors[k] for k in errors if k.startswith(('UNSAFE','TRUNCATED','SHORT','NON_REGULAR'))) else 'FAIL',
        'counts':dict(counts),'annotation_objects_by_split':dict(obj_counts),'class_object_counts':dict(classes),
        'object_field_counts':dict(object_keys),'annotation_field_counts':dict(ann_keys),
        'annotation_image_tag_count':image_tags,'annotation_object_tag_count':object_tags,'ownership_field_counts':dict(ownership_fields),
        'errors':dict(errors),'error_examples':examples,'duplicate_member_names':duplicates,'end_zero_blocks_validation':trailer_ok,
        'payload_integrity_limit':'Plain TAR headers have checksums, payloads do not. All payloads read and fingerprinted; no publisher checksum available.',
        'missing_image_annotation_pairs':pair_missing,'header_annotation_dimension_mismatches':dim_mismatch,
        'official_validation_reference':'Pinned PGN repository complete 5000 evaluation/Instance_part_val/*.txt IDs',
        'official_validation_ID_set_exact_match':val_exact,'official_train_test_ID_lists':'NOT_VERIFIED_FULL_LISTS_UNAVAILABLE_IN_REFERENCE_REPO',
        'split_IDs_disjoint':disjoint,'all_IDs_complete_1_to_38280':allids=={f'{i:07d}' for i in range(1,38281)},
        'native_PGN_train_val_demo_lists':'Both contain same 5 demo IDs; not official full split lists',
        'byte_duplicate_image_groups':sum(len(v)>1 for v in byte_hashes.values()),
        'byte_duplicate_cross_split_groups':sum(len({p.split('/')[0] for p in v})>1 for v in byte_hashes.values()),
        'exact_decoded_RGB_leakage_audit':'NOT_PERFORMED_IN_PREFLIGHT',
        'archive_meta':metadata,'taxonomy_native_mapping':NATIVE_IDS,
        'all_annotation_bitmaps_full_decode_and_PNG_CRC':'PASS' if counts['bitmap_decoded']==sum(obj_counts.values()) and not errors else 'FAIL',
        'sample_strict_RGB_decode':samples,'native_reference_semantic_comparisons':references,
        'human_instance_GT_status':'MISSING_NATIVE_HUMAN_OWNERSHIP_INFORMATION',
        'conversion_fidelity':'FAIL_FOR_PERSON_INSTANCE_CONTRACT; semantic/part full-native parity unverified',
        'local_full_quality_review':'NOT_RUN','primary_dataset_promoted':False,'model_inference':False,
        'tool_sha256':digest(Path(__file__)),'decoder_sha256':digest(S/'src/data/cihp_datasetninja.py'),
        'member_inventory':str((run/'TAR_MEMBER_SHA256.jsonl').relative_to(S)),
        'member_inventory_sha256':digest(run/'TAR_MEMBER_SHA256.jsonl'),
        'annotation_summary':str((run/'ANNOTATION_SUMMARY.jsonl').relative_to(S)),
        'annotation_summary_sha256':digest(run/'ANNOTATION_SUMMARY.jsonl')}
    publish(run/'ARCHIVE_PREFLIGHT.json',result)
    publish(S/'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json',result)
    publish(S/'manifests/CIHP_DATASETNINJA_ARCHIVE_MANIFEST_V1.json',{
        'schema_version':'1.0','run_id':active['run_id'],'archive_workspace_relative':result['archive_workspace_relative'],
        'archive_bytes':stat.st_size,'archive_sha256':archive_hash,'evidence':'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json',
        'member_inventory':result['member_inventory'],'member_inventory_sha256':result['member_inventory_sha256'],
        'splits':{s:{'image_ids':sorted(ids[s]),'images':counts[s+'_images'],'annotations':counts[s+'_annotations'],
                    'objects':obj_counts[s],'human_persons':'UNRECOVERABLE_FROM_RELEASE_METADATA'} for s in ids},
        'primary_dataset_frozen':False,'native_human_instance_evaluation_ready':False,'benchmark_authorized':False})
    print(json.dumps({'container':result['container_integrity'],'archive_sha256':archive_hash,'counts':dict(counts),
        'GT_objects':dict(obj_counts),'errors':dict(errors),'validation_ID_match':val_exact,'human_IDs':'MISSING',
        'native_semantic_reference_comparisons':references},indent=2),flush=True)


if __name__=='__main__':main()
