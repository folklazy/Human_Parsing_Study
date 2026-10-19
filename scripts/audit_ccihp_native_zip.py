"""Read-only CCIHP ZIP integrity + bounded person/semantic compatibility audit.

No model imports, archive extraction, attribute evaluation or GT repairs.
CRC/SHA inventory covers archive payloads; semantic/physical review is sampled.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from collections import Counter, defaultdict
import hashlib
import io
import json
import re
import stat
import struct
import sys
import zipfile
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFile

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
sys.path.insert(0, str(ROOT))
from src.data.cihp_datasetninja import reconstruct_semantic, decode_bitmap

active = json.loads((ROOT / 'provenance/CCIHP_STAGE0E_CURRENT_RUN_V2.json').read_text())
RUN = ROOT / active['run_path']
ZIP = WORKSPACE / 'datasets/CCIHP_icip.zip'
PREFIX = 'CCIHP_icip/'
NOW = datetime.now(timezone.utc).isoformat()
ImageFile.LOAD_TRUNCATED_IMAGES = False


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def save(name, value):
    path = RUN / name
    if path.exists():
        if json.loads(path.read_text()) == value:
            return
        raise RuntimeError(f'Refusing to overwrite differing evidence: {path}')
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


print('[STAGE0E] archive SHA256', flush=True)
hash_record = RUN/'ARCHIVE_SHA256.json'
if hash_record.exists():
    current = ZIP.stat()
    expected = json.loads((RUN/'BEFORE.json').read_text())['zip_stat']
    assert (current.st_size,current.st_mtime_ns,current.st_ino)==(expected['bytes'],expected['mtime_ns'],expected['inode'])
    zip_hash = json.loads(hash_record.read_text())['sha256']
else:
    zip_hash = sha(ZIP)
save('ARCHIVE_SHA256.json', {'archive_workspace_relative':'datasets/CCIHP_icip.zip', 'bytes':ZIP.stat().st_size, 'sha256':zip_hash})
before = ZIP.stat()
with zipfile.ZipFile(ZIP) as z:
    infos = z.infolist()
    names = [i.filename for i in infos]
    counts = Counter(names)
    unsafe = [n for n in names if PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts or '\\' in n]
    links = [i.filename for i in infos if stat.S_ISLNK(i.external_attr >> 16)]
    assert not unsafe and not links and all(v == 1 for v in counts.values())
    archive_counts = Counter('/'.join(i.filename.split('/')[:4]) for i in infos if not i.is_dir())
    total_uncompressed = sum(i.file_size for i in infos)
    errors = []
    print('[STAGE0E] all-member CRC and SHA inventory', flush=True)
    ledger = RUN / 'ZIP_MEMBER_SHA256.jsonl'
    if ledger.exists():
        recorded = {}
        with ledger.open() as stream:
            for line in stream:
                row=json.loads(line);recorded[row['member']]=row
        assert len(recorded)==sum(not i.is_dir() for i in infos)
        assert all(recorded[i.filename]['bytes']==i.file_size and recorded[i.filename]['zip_crc32']==f'{i.CRC:08x}' and recorded[i.filename]['crc_validation']=='PASS' for i in infos if not i.is_dir())
        before_record=json.loads((RUN/'BEFORE.json').read_text())['zip_stat']
        assert before_record['bytes']==before.st_size and before_record['mtime_ns']==before.st_mtime_ns and before_record['inode']==before.st_ino
        print('[STAGE0E] reuse complete CRC ledger after documented label-range stop',flush=True)
    else:
      with ledger.open('x') as inventory:
        for index, member in enumerate(infos):
            if member.is_dir():
                continue
            h = hashlib.sha256()
            crc = 0
            size = 0
            try:
                with z.open(member) as stream:
                    for block in iter(lambda: stream.read(1024*1024), b''):
                        size += len(block)
                        h.update(block)
                        crc = zlib.crc32(block, crc)
                assert size == member.file_size and crc & 0xffffffff == member.CRC
                inventory.write(json.dumps({'member': member.filename, 'bytes': size, 'sha256': h.hexdigest(),
                                             'zip_crc32': f'{member.CRC:08x}', 'crc_validation': 'PASS'}, separators=(',', ':'))+'\n')
            except Exception as e:
                errors.append({'member': member.filename, 'error': str(e)})
            if index % 20000 == 0:
                (RUN / 'PROGRESS.json').write_text(json.dumps({'members_processed': index, 'total': len(infos), 'crc_errors': len(errors)})+'\n')
    assert not errors
    docs = RUN / 'archive_documents'
    docs.mkdir(exist_ok=True)
    document_evidence = []
    for name in names:
        if name in [PREFIX+'README.md', PREFIX+'README.html', PREFIX+'LICENSE'] or name.startswith(PREFIX+'evaluation/') and name.endswith('.py'):
            data = z.read(name)
            dest = docs / Path(name).name
            if dest.exists():assert dest.read_bytes()==data
            else:dest.write_bytes(data)
            document_evidence.append({'member': name, 'sha256': hashlib.sha256(data).hexdigest(), 'snapshot': str(dest.relative_to(ROOT))})
    split_ids = {}
    component_sets = {}
    for split, count in [('Training',28280), ('Validation',5000)]:
        raw = z.read(PREFIX+f'dataset/{split}/'+('train_id.txt' if split=='Training' else 'val_id.txt')).decode()
        ids = raw.split()
        assert len(ids) == count and len(set(ids)) == count
        split_ids[split] = ids
        component_sets[split] = {}
        for component in ['Category_ids','Human_ids','Instance_ids','Color_ids','Pattern_ids','Size_ids']:
            path = PREFIX+f'dataset/{split}/{component}/'
            members = [n for n in names if n.startswith(path) and not n.endswith('/')]
            assert all(n.endswith('.png') for n in members)
            actual = {Path(n).stem for n in members}
            assert actual == set(ids)
            component_sets[split][component] = {'files': len(members), 'missing_ids': [], 'orphan_ids': []}
    assert not set(split_ids['Training']) & set(split_ids['Validation'])
    dn = json.loads((ROOT / 'manifests/CIHP_DATASETNINJA_ARCHIVE_MANIFEST_V1.json').read_text())
    for split, lower in [('Training','training'),('Validation','validation')]:
        value = dn['splits'][lower]
        dn_ids = value if isinstance(value,list) else value['image_ids']
        assert set(dn_ids) == set(split_ids[split])
    save('SPLIT_COMPONENT_VALIDATION.json', {'split_counts': {k:len(v) for k,v in split_ids.items()},
                                            'components': component_sets, 'split_overlap_ids': [],
                                            'datasetninja_ID_parity': 'EXACT_TRAIN_AND_VALIDATION',
                                            'IDs_are_not_RGB_identity_proof': True})
    save('CCIHP_SPLITS.json', split_ids)
    print('[STAGE0E] bounded native-map comparison', flush=True)
    prior = json.loads((ROOT / 'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json').read_text())
    assert sha(ROOT / prior['member_inventory']) == prior['member_inventory_sha256']
    tar_index = {}
    with (ROOT / prior['member_inventory']).open() as stream:
        for line in stream:
            record = json.loads(line)
            tar_index[record['path']] = record

    def tar_read(name):
        row = tar_index[name]
        with (WORKSPACE/'datasets/cihp-DatasetNinja.tar').open('rb') as f:
            f.seek(row['data_offset'])
            data = f.read(row['bytes'])
        assert hashlib.sha256(data).hexdigest() == row['sha256']
        return data

    def mask_read(split, component, image_id):
        name = PREFIX+f'dataset/{split}/{component}/{image_id}.png'
        raw = z.read(name)
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            array = np.asarray(image).copy()
            assert array.ndim == 2
            mode = image.mode
        return array, {'member': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'mode':mode,
                       'dtype':str(array.dtype), 'wh':[array.shape[1],array.shape[0]], 'labels': [int(x) for x in np.unique(array)]}

    native_demo_ids = ['0002190','0005008','0012008','0026375','0032190']
    seed = 'stage0e-ccihp-20261012'
    sampled = [(split, image_id) for split,n in [('Training',20),('Validation',5)]
               for image_id in sorted(split_ids[split], key=lambda x: hashlib.sha256(f'{seed}:{split}:{x}'.encode()).hexdigest())[:n]]
    sampled += [('Training',x) for x in native_demo_ids if ('Training',x) not in sampled]
    save('BOUNDED_SAMPLE.json', {'selection':'20 SHA-ranked TRAIN + 5 SHA-ranked VALIDATION integrity-only + 5 existing native TRAIN demos',
                                'seed':seed, 'images':[{'split':s,'image_id':i} for s,i in sampled],
                                'validation_integrity_only_not_tuning':True, 'representative_quality_claim':False})
    results = []
    per_class = defaultdict(lambda: {'pixels_CCIHP':0,'pixels_CIHP':0,'same_ID_both':0,'differing_label_pixels':0})
    association_totals = Counter()
    label_values = set()
    out = ROOT/'outputs/visualizations'/active['run_id']
    out.mkdir(parents=True,exist_ok=True)
    palette = np.full((256,3),(255,0,255),dtype=np.uint8)
    palette[:22] = np.array([[0,0,0]]+[((k*83)%200+35,(k*139)%200+35,(k*191)%200+35) for k in range(1,22)],np.uint8)
    for split,image_id in sampled:
        semantic, sem_info = mask_read(split,'Category_ids',image_id)
        human, human_info = mask_read(split,'Human_ids',image_id)
        instance, instance_info = mask_read(split,'Instance_ids',image_id)
        label_values.update(sem_info['labels'])
        assert semantic.shape == human.shape == instance.shape
        lower = split.lower()
        rgb_bytes = tar_read(f'{lower}/img/{image_id}.jpg')
        with Image.open(io.BytesIO(rgb_bytes)) as image:
            image.load()
            rgb = np.asarray(image.convert('RGB'))
        assert rgb.shape[:2] == semantic.shape
        annotation = json.loads(tar_read(f'{lower}/ann/{image_id}.jpg.json'))
        dn_map,dn_diagnostics = reconstruct_semantic(annotation)
        assert dn_map.shape == semantic.shape
        # Preserve undocumented IDs as unresolved; do not turn them into background/ignore.
        undocumented_ids = sorted(set(sem_info['labels'])-set(range(22)))
        assert 255 not in human_info['labels']
        human_ids = [x for x in human_info['labels'] if x != 0]
        associations = []
        for obj in annotation['objects']:
            support,(x,y),label = decode_bitmap(obj,(rgb.shape[1],rgb.shape[0]))
            values,counts_ = np.unique(human[y:y+support.shape[0],x:x+support.shape[1]][support],return_counts=True)
            distribution = {str(int(v)):int(n) for v,n in zip(values,counts_)}
            positive = [int(v) for v in values if v>0]
            background_pixels = int(distribution.get('0',0))
            status = 'EXACT_ONE_HUMAN_FULL_SUPPORT' if len(positive)==1 and background_pixels==0 else 'MULTIPLE_HUMANS' if len(positive)>1 else 'ONE_HUMAN_WITH_UNASSIGNED_PIXELS' if len(positive)==1 else 'NO_HUMAN_SUPPORT'
            association_totals[status]+=1
            associations.append({'part_object_id':obj['id'],'native_cihp_class':label,'status':status,'human_distribution':distribution})
        part_relations = []
        for instance_id in np.unique(instance):
            if instance_id == 0:continue
            support=instance==instance_id
            humans=np.unique(human[support]); categories=np.unique(semantic[support])
            part_relations.append({'instance_id':int(instance_id),'human_ids':[int(v) for v in humans],
                                   'category_ids':[int(v) for v in categories],
                                   'single_human_and_class':bool(len(humans)==1 and humans[0]>0 and len(categories)==1 and categories[0]>0)})
        for class_id in range(20):
            per_class[str(class_id)]['pixels_CCIHP'] += int(np.count_nonzero(semantic==class_id))
            per_class[str(class_id)]['pixels_CIHP'] += int(np.count_nonzero(dn_map==class_id))
            per_class[str(class_id)]['same_ID_both'] += int(np.count_nonzero((semantic==class_id)&(dn_map==class_id)))
            per_class[str(class_id)]['differing_label_pixels'] += int(np.count_nonzero(((semantic==class_id)|(dn_map==class_id))&(semantic!=dn_map)))
        native_parity = None
        if image_id in native_demo_ids:
            ref = ROOT/'provenance/RUN_MANIFESTS/cihp-archive-preflight-20261008T102552Z/sources/reference_fixtures'
            with Image.open(ref/f'labels_{image_id}.png') as image:
                image.load(); orig=np.asarray(image)
            assert np.array_equal(orig,dn_map)
            native_parity={'native_demo_DatasetNinja_parity_pixels':0,
                           'CCIHP_vs_native_raw_ID_difference_pixels':int(np.count_nonzero(semantic!=orig)),
                           'native_human_reference':'UNAVAILABLE'}
        row={'split':split,'image_id':image_id,'image_sha256':hashlib.sha256(rgb_bytes).hexdigest(),
             'image_source':'DatasetNinja CIHP; CCIHP contains no RGB for independent same-image byte check',
             'wh':[rgb.shape[1],rgb.shape[0]],'CCIHP_pngs':[sem_info,human_info,instance_info],
             'undocumented_semantic_ids':undocumented_ids,
             'undocumented_semantic_pixels':int(np.count_nonzero(np.isin(semantic,undocumented_ids))),
             'undocumented_semantic_coordinates_xy':[[int(x),int(y)] for y,x in np.argwhere(np.isin(semantic,undocumented_ids))],
             'person_ids':human_ids,'native_file_person_count':len(human_ids),
             'semantic_without_human_pixels':int(np.count_nonzero((semantic>0)&(human==0))),
             'human_without_semantic_pixels':int(np.count_nonzero((human>0)&(semantic==0))),
             'instance_without_human_pixels':int(np.count_nonzero((instance>0)&(human==0))),
             'raw_same_ID_semantic_difference_pixels':int(np.count_nonzero(semantic!=dn_map)),
             'foreground_difference_pixels':int(np.count_nonzero((semantic>0)!=(dn_map>0))),
             'same_ID_differences_are_not_semantically_harmonized_error':True,
             'dn_part_associations':associations,'ccihp_part_relations':part_relations,
             'native_demo_reference':native_parity,'dn_overlap_diagnostics':dn_diagnostics}
        if image_id in ['0002190','0005008','0012008']:
            panels=[]
            human_colours=np.zeros_like(rgb)
            for hid in human_ids:human_colours[human==hid]=palette[(hid%21)+1]
            for title,colour,support in [('Original CIHP RGB',rgb,None),('CCIHP Human_ids',human_colours,human>0),
                                         ('CCIHP categories',palette[semantic],semantic>0),('CIHP categories',palette[dn_map],dn_map>0)]:
                array=rgb if support is None else np.where(support[...,None],(0.55*rgb+0.45*colour).astype(np.uint8),rgb)
                picture=Image.fromarray(array);width=400;picture=picture.resize((width,round(picture.height*width/picture.width)),Image.Resampling.LANCZOS)
                panel=Image.new('RGB',(width,picture.height+34),'white');panel.paste(picture,(0,34));draw=ImageDraw.Draw(panel);draw.text((8,8),title,fill='black')
                if title=='CCIHP Human_ids':
                    for hid in human_ids:
                        yy,xx=np.nonzero(human==hid);xx_=int(np.median(xx)*width/rgb.shape[1]);yy_=int(np.median(yy)*picture.height/rgb.shape[0])+34
                        draw.rectangle((xx_-2,yy_-2,xx_+28,yy_+14),fill='white');draw.text((xx_,yy_),str(hid),fill='black')
                panels.append(panel)
            height=max(p.height for p in panels);canvas=Image.new('RGB',(1600,height+38),'white')
            for k,p in enumerate(panels):canvas.paste(p,(k*400,0))
            ImageDraw.Draw(canvas).text((8,height+8),f'{image_id} | full frame, same display geometry | categories differ: no native equivalence assumed',fill='black')
            dest=out/f'case_{image_id}.png'
            encoded=io.BytesIO();canvas.save(encoded,format='PNG');data=encoded.getvalue()
            if dest.exists():assert dest.read_bytes()==data, 'Refusing to overwrite changed diagnostic image'
            else:dest.write_bytes(data)
            row['diagnostic_image']=str(dest.relative_to(ROOT));row['diagnostic_sha256']=sha(dest)
        results.append(row)
    save('BOUNDED_CROSS_DATASET_COMPARISON.json',{'cases':results,'sample_count':len(results),
                                               'observed_Category_ids':sorted(label_values),'association_counts':dict(association_totals),
                                               'per_class_same_numeric_ID_diagnostics':dict(per_class),
                                               'native_human_semantic_equivalence':'NOT_VERIFIED',
                                               'official_native_CIHP_reconstructed':False})
    after=ZIP.stat()
    save('ZIP_INTEGRITY.json',{'archive_workspace_relative':'datasets/CCIHP_icip.zip','archive_bytes':before.st_size,
                              'archive_sha256':zip_hash,'members':len(infos),'regular_files':sum(not x.is_dir() for x in infos),
                              'total_uncompressed_bytes':total_uncompressed,'all_member_crc':'PASS','member_errors':errors,
                              'safe_paths':'PASS','duplicate_members':[],'symlink_members':links,'component_counts':dict(archive_counts),
                              'documents':document_evidence,'member_inventory':str((RUN/'ZIP_MEMBER_SHA256.jsonl').relative_to(ROOT)),
                              'member_inventory_sha256':sha(RUN/'ZIP_MEMBER_SHA256.jsonl'),
                              'size_mtime_inode_unchanged':(before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino),
                              'complete_archive_extracted':False,'all_annotations_semantically_audited':False,
                              'model_inference':False,'attribute_evaluation':False,'end_utc':datetime.now(timezone.utc).isoformat()})
print('[STAGE0E] bounded audit complete; no native-equivalence claim',flush=True)
