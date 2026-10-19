"""Read-only ZIP/member verification; no extraction, repair, inference or view activation."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
import struct
import stat
import subprocess
import zlib
from zipfile import ZipFile

import cv2
import numpy as np
from PIL import Image, ImageFile


STUDY = Path(__file__).resolve().parents[1]
WORKSPACE = STUDY.parent
EXPECTED_PREVIOUS_HASH = '89f010742d4797d3efd7a7eab83a405d9828749381da20638a03df947238059e'


def hash_file(path):
    h = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def decode(data):
    result = {'pillow_header_wh':None,'pillow_format':None,'pillow_full_pixel_load':False,
              'pillow_verify_pass':False,'pillow_error':None,'opencv_nonempty':False,
              'opencv_wh':None,'opencv_error':None,'complete_pixels_verified':False}
    try:
        with Image.open(BytesIO(data)) as im:
            result['pillow_header_wh'] = list(im.size)
            result['pillow_format'] = im.format
            im.load()  # Strict entropy/pixel loading, not just Image.open.
            rgb = np.asarray(im.convert('RGB'))
            result['pillow_full_pixel_load'] = rgb.shape == (im.height,im.width,3)
        with Image.open(BytesIO(data)) as im:
            im.verify()
        result['pillow_verify_pass'] = True
    except Exception as error:
        result['pillow_error'] = f'{type(error).__name__}: {error}'
    try:
        image = cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
        result['opencv_nonempty'] = image is not None and image.size > 0
        if result['opencv_nonempty']:
            result['opencv_wh'] = [int(image.shape[1]),int(image.shape[0])]
    except Exception as error:
        result['opencv_error'] = f'{type(error).__name__}: {error}'
    result['complete_pixels_verified'] = (result['pillow_format']=='JPEG' and
        result['pillow_full_pixel_load'] and result['pillow_verify_pass'] and
        result['opencv_nonempty'] and result['pillow_header_wh']==result['opencv_wh'])
    # A nonempty permissive OpenCV result alone never establishes completeness.
    return result


def main():
    report_path = STUDY/'reports/MHPV2_NEW_ZIP_RGB_VERIFICATION.md'
    evidence_path = STUDY/'provenance/MHPV2_NEW_ZIP_RGB_VERIFICATION.json'
    if report_path.exists() or evidence_path.exists():
        raise RuntimeError('Verification already exists; explicit archived revision required before overwrite')
    archive = WORKSPACE/'datasets/LV-MHP-v2.zip'
    dataset = WORKSPACE/'datasets/LV-MHP-v2'
    assert archive.is_file() and dataset.is_dir()
    started = datetime.now(timezone.utc).isoformat()
    before_stat = archive.stat()
    import_record_path = dataset/'IMPORT_VALIDATION.json'
    import_record_bytes = import_record_path.read_bytes()
    import_record = json.loads(import_record_bytes)
    dataset_manifest_path = STUDY/'manifests/DATASET_MANIFEST.json'
    manifest_bytes = dataset_manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    state_path = STUDY/'STUDY_STATE.json'
    state_hash_before = hash_file(state_path)
    index = {}
    affected = {('train','1396'),('train','18613'),('train','24328'),('val','17844')}
    with (STUDY/manifest['canonical_gt_index']).open() as stream:
        for line in stream:
            row = json.loads(line)
            if (row['split'],row['image_id']) in affected:
                index[row['split'],row['image_id']] = row
    assert len(index)==4
    archive_hash = hash_file(archive)
    identical_to_previous = archive_hash == import_record['source_sha256'] == EXPECTED_PREVIOUS_HASH
    print('[ZIP] whole-archive SHA256: '+('IDENTICAL TO PREVIOUS' if identical_to_previous else 'DIFFERENT'),flush=True)
    ImageFile.LOAD_TRUNCATED_IMAGES = False
    with ZipFile(archive) as zipped, archive.open('rb') as raw:
        infos = zipped.infolist()
        names = [info.filename for info in infos]
        assert len(names)==len(set(names)), 'Duplicate central-directory names'
        corrected = 0
        for info in infos:
            path = PurePosixPath(info.filename)
            assert not path.is_absolute() and '..' not in path.parts and '\\' not in info.filename
            assert not stat.S_ISLNK(info.external_attr>>16) and not info.flag_bits&1
            candidates = [info.header_offset]
            if info.header_offset>=2**32:
                candidates.append(info.header_offset-2**32)
            valid_offsets = []
            for offset in candidates:
                raw.seek(offset)
                header = raw.read(30)
                if len(header)!=30 or header[:4]!=b'PK\x03\x04':
                    continue
                fields = struct.unpack('<4s5H3L2H',header)
                name = raw.read(fields[-2]).decode('utf-8' if fields[2]&0x800 else 'cp437')
                if name==info.orig_filename:
                    assert fields[3]==info.compress_type
                    local_data_start = offset+30+fields[-2]+fields[-1]
                    assert local_data_start+info.compress_size<=zipped.start_dir
                    valid_offsets.append(offset)
            assert len(valid_offsets)==1, f'Unresolvable central/local header: {info.filename}'
            corrected += valid_offsets[0]!=info.header_offset
            info.header_offset=valid_offsets[0]  # In-memory ZipInfo only; original ZIP unchanged.
        end = zipped.start_dir
        for info in sorted(infos,key=lambda value:value.header_offset,reverse=True):
            info._end_offset=end
            end=info.header_offset
        name_index={info.filename:info for info in infos}
        read_members=[]

        def read_member(name):
            info=name_index[name]
            data=zipped.read(info)  # Reads full member; ZipFile checks CRC at EOF.
            assert len(data)==info.file_size
            crc=zlib.crc32(data)&0xffffffff
            assert crc==info.CRC
            read_members.append({'path':name,'bytes':len(data),'sha256':sha256(data).hexdigest(),
                                 'crc32_expected':f'{info.CRC:08x}','crc32_actual':f'{crc:08x}','crc_status':'PASS'})
            return data

        readme_names=[name for name in names if PurePosixPath(name).name=='README.txt' and '__MACOSX' not in name]
        assert len(readme_names)==1
        root=PurePosixPath(readme_names[0]).parent.as_posix()
        readme=read_member(readme_names[0])
        assert b'LV MHP v2.0' in readme
        assert readme==(dataset/'README.txt').read_bytes()
        counts={}
        expected_counts={'train':(15403,41056,15403),'val':(5000,13260,5000),'test':(5000,0,0)}
        split_names={'train':'train.txt','val':'val.txt','test':'test_all.txt'}
        for split,expected in expected_counts.items():
            images=[name for name in names if name.startswith(f'{root}/{split}/images/') and name.endswith('.jpg')]
            parsing=[name for name in names if name.startswith(f'{root}/{split}/parsing_annos/') and name.endswith('.png')]
            pose=[name for name in names if name.startswith(f'{root}/{split}/pose_annos/') and name.endswith('.mat')]
            assert (len(images),len(parsing),len(pose))==expected
            list_path=f'{root}/list/{split_names[split]}'
            split_bytes=read_member(list_path)
            assert split_bytes==(dataset/'list'/split_names[split]).read_bytes()
            ids=split_bytes.decode().split()
            assert len(ids)==len(set(ids))==len(images)
            assert set(ids)=={PurePosixPath(name).stem for name in images}
            counts[split]={'images':len(images),'person_parsing_PNGs':len(parsing),'pose_MATs':len(pose),
                           'official_split_bytes_equal_existing':True}
        print('[ZIP] central directory/local headers and expected inventories: PASS',flush=True)
        cases=[]
        for split,image_id in [('train','1396'),('train','18613'),('train','24328'),('val','17844')]:
            row=index[split,image_id]
            matches=[name for name in names if name==f'{root}/{split}/images/{image_id}.jpg']
            old_path=dataset/row['image_path']
            old_bytes=old_path.read_bytes()
            old_hash=sha256(old_bytes).hexdigest()
            assert old_hash==row['image_sha256'], 'Existing RGB changed since prior audit'
            case={'split':split,'image_id':image_id,'old_relative_path':row['image_path'],'old_sha256':old_hash,
                  'old_bytes':len(old_bytes),'new_archive_member':matches[0] if matches else None,
                  'new_sha256':None,'new_uncompressed_bytes':None,'same_bytes':False,'zip_crc':'NOT_TESTED',
                  'old_decode':decode(old_bytes),'new_decode':None,'GT':[],'visual_pixel_alignment_verified':False,
                  'replacement_activated':False}
            if not matches:
                case['result']='MISSING'
                cases.append(case)
                continue
            new_bytes=read_member(matches[0])
            case.update({'new_sha256':sha256(new_bytes).hexdigest(),'new_uncompressed_bytes':len(new_bytes),
                         'same_bytes':new_bytes==old_bytes,'zip_crc':'PASS','new_decode':decode(new_bytes)})
            for person in row['persons']:
                path=person['annotation_path']
                existing=(dataset/path).read_bytes()
                archived=read_member(f'{root}/{path}')
                assert archived==existing and sha256(existing).hexdigest()==person['source_sha256']
                with Image.open(BytesIO(archived)) as im:
                    im.load()
                    labels=np.asarray(im)
                    labels=labels[...,0] if labels.ndim==3 else labels
                    assert set(map(int,np.unique(labels)))<=set(range(59))
                    assert list(im.size)==row['original_wh']
                    assert sha256(labels.tobytes()).hexdigest()==person['semantic_array_sha256']
                case['GT'].append({'person_id':person['canonical_person_id'],'annotation_path':path,
                    'original_wh':row['original_wh'],'source_sha256':person['source_sha256'],
                    'archive_vs_existing_bytes_equal':True,'native_label_pixels_fidelity':'PASS','zip_crc':'PASS'})
            case['image_identity_evidence']='Exact image member bytes match existing file' if case['same_bytes'] else 'Archive path and unchanged matching GT; visual identity not verified'
            case['header_wh_equals_existing_GT']=case['new_decode']['pillow_header_wh']==row['original_wh']
            case['complete_RGB_to_GT_alignment_verified']=False
            if case['same_bytes'] and not case['new_decode']['complete_pixels_verified']:
                case['result']='SAME_DEFECTIVE_BYTES'
            elif not case['new_decode']['complete_pixels_verified']:
                case['result']='DIFFERENT_BUT_INVALID'
            else:
                # Valid JPEG pixels alone cannot prove photo identity/alignment.
                # Manual visual verification must occur before RECOVERED_VALID.
                case['result']='SOURCE_UNVERIFIED'
                case['requires_manual_identity_alignment_review']=True
            assert old_path.read_bytes()==old_bytes
            cases.append(case)
    after_stat=archive.stat()
    assert (before_stat.st_size,before_stat.st_mtime_ns,before_stat.st_ino)==(after_stat.st_size,after_stat.st_mtime_ns,after_stat.st_ino)
    assert import_record_path.read_bytes()==import_record_bytes and dataset_manifest_path.read_bytes()==manifest_bytes
    assert hash_file(state_path)==state_hash_before
    preservation_dir=STUDY/'provenance/RUN_MANIFESTS'/json.loads((STUDY/'provenance/STAGE0_ACTIVE_RUN.json').read_text())['run_id']
    protected=json.loads((preservation_dir/'PRESERVATION_AFTER.json').read_text())
    git_checks={}
    for name,previous in protected['repos'].items():
        repo=WORKSPACE/name
        current={key:subprocess.check_output(args,cwd=repo,text=True).strip() for key,args in [
            ('head',['git','rev-parse','HEAD']),('branch',['git','branch','--show-current']),
            ('status',['git','status','--porcelain']),('remotes',['git','remote','-v'])]}
        assert all(current[key]==previous[key] for key in current)
        git_checks[name]={'head_branch_status_remotes_unchanged':True}
    outcomes=Counter(case['result'] for case in cases)
    recovered=outcomes.get('RECOVERED_VALID',0)
    unreadable=sum(not case['new_decode']['complete_pixels_verified'] for case in cases if case['new_decode'])
    result={'schema_version':'1.0','start_utc':started,'end_utc':datetime.now(timezone.utc).isoformat(),
        'verification_status':'PASS_VERIFICATION_RGB_BLOCKER_REMAINS' if recovered==0 else 'REVIEW_REQUIRED',
        'source_provenance':{'user_declared_source':'Newly downloaded official dataset ZIP transferred to server',
            'independent_download_URL_log_or_publisher_SHA256_available':False,
            'identity_claim_scope':'Cryptographic equality to historical archive hash; does not establish all publisher releases identical'},
        'archive':{'workspace_relative_path':str(archive.relative_to(WORKSPACE)),'bytes':before_stat.st_size,
            'sha256':archive_hash,'previous_import_sha256':import_record['source_sha256'],
            'previous_hash_comparison':'BYTE_IDENTICAL_TO_PREVIOUS_RECORDED_ARCHIVE' if identical_to_previous else 'DIFFERENT',
            'central_directory_parse':'PASS','central_directory_entries':len(infos),'central_directory_start':zipped.start_dir,
            'duplicate_names':0,'local_header_filename_method_bounds_validation':'PASS',
            'wrapped_offsets_resolved_in_memory':corrected,'original_archive_offsets_or_bytes_modified':False,
            'dataset_member_root':root,'dataset_version':'2.0','README_bytes_equal_existing':True,
            'expected_split_inventories':counts,'all_archive_members_CRC_retested':False,
            'CRC_scope':'Selected 4 JPEG + 16 associated GT + README + 3 official lists, complete member reads',
            'members_CRC_verified_count':len(read_members),'file_size_mtime_inode_unchanged_during_read':True},
        'decoders':{'pillow':Image.__version__,'opencv':cv2.__version__,'Pillow_LOAD_TRUNCATED_IMAGES':False,
            'header_only_success_is_sufficient':False,'permissive_OpenCV_success_alone_is_sufficient':False},
        'cases':cases,'members_verified':read_members,'outcome_counts':dict(outcomes),
        'actually_recovered_images':recovered,'still_unreadable_images':unreadable,
        'verified_replacement_overlay_available':False,'overlay_activated':False,'dataset_status':'DATASET_BLOCKED',
        'remaining_integrity_blockers':['Four required RGB members are not verified complete JPEG inputs'],
        'other_stage0_gates_not_resolved':['Train/validation content reuse and reporting population decisions',
            'Uncertain native GT physical-person ownership','Official evaluator compatibility/parity','Checkpoint/model feasibility and licensing'],
        'scientific_conclusion':'Identical recorded ZIP and identical member bytes cannot repair the four images through another extraction/download of the same bytes',
        'recommended_next_action':'Seek independently verified different source copies with provenance; otherwise ask approval for explicitly named readable-subset policy and shared denominators; bounded train-only feasibility is a separate approval',
        'safety':{'full_archive_extracted':False,'original_RGB_or_GT_modified':False,'official_splits_modified':False,
            'canonical_state_or_dataset_manifest_modified':False,'PPSS_accessed_or_modified':False,'YOLO_artifacts_modified':False,
            'parser_models_run':False,'validation_inference_run':False,'stage1_or_full_benchmark_started':False},
        'existing_YOLO_git_validation':git_checks,'verification_script_sha256':hash_file(Path(__file__))}
    atomic_json(evidence_path,result)
    lines=['# MHP-v2 — ตรวจ ZIP ใหม่และ RGB Integrity Blocker','',
        '**ตรวจสอบเสร็จ: PASS สำหรับการตรวจหลักฐาน / RGB dataset gate ยัง BLOCKED**','',
        '## ZIP ใหม่','',f'- ไฟล์: `{archive}`',f'- ขนาด: **{before_stat.st_size:,} bytes**',
        f'- SHA256: `{archive_hash}`',
        f'- เทียบกับ previous import record: **{"BYTE-IDENTICAL — ZIP ใหม่ตรงกับ archive ที่บันทึกไว้เดิม" if identical_to_previous else "DIFFERENT — hash ต่างจาก archive เดิม"}**',
        f'- Central directory อ่านได้ครบ **{len(infos):,} entries**; ชื่อไม่ซ้ำ และ local headers/name/compression/bounds ผ่าน',
        f'- พบ wrapped local offsets **{corrected:,} entries**; resolve เฉพาะ ZipInfo ใน memory ตามชื่อ local header ไม่แก้ ZIP และไม่ extract',
        f'- Root `{root}`, README ระบุ MHP-v2.0 และ bytes ตรง dataset เดิม; official split lists ตรงทุก byte','',
        '| Split | Images | Person GT PNG | Pose MAT |','|---|---:|---:|---:|']
    for split,c in counts.items():
        lines.append(f'| {split} | {c["images"]:,} | {c["person_parsing_PNGs"]:,} | {c["pose_MATs"]:,} |')
    lines.extend(['','จำนวนไฟล์จาก central directory คือ existence/inventory verification ไม่ใช่การ decode รูปทั้งชุดซ้ำ Test GT ไม่ supplied ตามโครงสร้างเดิม','',
        f'CRC ถูกตรวจใหม่จาก full member reads **{len(read_members)} สมาชิก**: RGB 4, GT ที่เกี่ยวข้อง 16, README 1 และ split lists 3 ไม่ได้อ้างว่า retest CRC ทั้ง 179,896 สมาชิก การมี CRC ผ่านไม่ได้แปลว่า JPEG ใช้งานได้','',
        '## ผลตรวจภาพทั้งสี่','',
        '| Split | ID | Old SHA256 | New SHA256 | Same bytes | ZIP CRC | Pillow | OpenCV | Result |',
        '|---|---|---|---|---|---|---|---|---|'])
    for case in cases:
        d=case['new_decode']
        lines.append(f'| {case["split"]} | {case["image_id"]} | `{case["old_sha256"]}` | `{case["new_sha256"]}` | {"YES" if case["same_bytes"] else "NO"} | {case["zip_crc"]} | {"PASS" if d and d["pillow_full_pixel_load"] else "FAIL"} | {"NONEMPTY" if d and d["opencv_nonempty"] else "NO IMAGE"} | {case["result"]} |')
    lines.extend(['','| Split / ID | Member bytes | JPEG header W×H | GT persons | Strict Pillow diagnostic |',
                  '|---|---:|---|---:|---|'])
    for case in cases:
        d=case['new_decode'] or {}
        lines.append(f'| {case["split"]}/{case["image_id"]} | {case["new_uncompressed_bytes"]} | {d.get("pillow_header_wh")} | {len(case["GT"])} | {d.get("pillow_error")} |')
    lines.extend(['','**Header dimensions ไม่ใช่ successful decode dimensions:** Pillow `.load()` ล้มทั้งสี่ และ OpenCV ไม่คืนรูป จึงไม่มี fully decoded RGB dimensions ให้รับรอง ใช้ `LOAD_TRUNCATED_IMAGES=False` ไม่มี marker insertion หรือ partial-pixel repair','',
        '## Identity, GT และ alignment','',
        'RGB members ตรงกับ extracted files เดิมทั้ง bytes และ SHA256 โดย existing hashes ตรง prior canonical index จึงยืนยัน byte identity ของสี่ภาพ Associated GT ทั้ง 16 ไฟล์มี CRC ผ่าน, bytes ตรง existing GT, native label IDs อยู่ใน 0–58 และ semantic array hashes ตรง index เดิม','',
        'JPEG header grid ตรง dimensions ของ GT แต่ **ยังรับรอง RGB-to-GT spatial alignment จาก complete pixels ไม่ได้** เพราะไม่มี RGB ใด decode ครบ ไม่มีการอ้าง header agreement ว่าภาพได้รับการกู้แล้ว','',
        '## ข้อสรุป','',f'- Actually recovered: **{recovered}/4**',f'- Still unreadable: **{unreadable}/4**',
        '- Replacement overlay ที่ยืนยันใช้ได้: **NO**; ยังไม่ activate overlay',
        '- Existing dataset: **DATASET_BLOCKED** สำหรับ required-input readiness ของ full evaluation',
        '- การแตกใหม่หรือโหลด archive ที่ hash เดิมซ้ำไม่ซ่อมสี่ภาพ เพราะ archive บรรจุ defective bytes เหมือน existing files',
        '- สำหรับสี่สมาชิกนี้ การ extraction ไม่ได้สร้าง byte difference จาก ZIP ที่เคยบันทึกไว้ และ hash ทั้ง archive ตรง historical import record',
        '', 'ผู้ใช้ระบุว่าเป็น official download แต่รอบนี้ไม่มี download URL log หรือ publisher hash มายืนยันแหล่งปลายทางอย่างอิสระ ข้อสรุปที่พิสูจน์คือ archive/member identity กับสำเนาที่บันทึกไว้ ไม่ใช่การกล่าวว่าทุก release หรือทุก mirror ของ MHP-v2 เสียเหมือนกัน','',
        '## ทางเลือกถัดไปที่ต้องอนุมัติ','',
        '1. หา **different, independently verified source copies** ของสี่ JPEG ที่ decode ได้จริง พร้อม provenance และตรวจ identity/GT alignment เก็บ originals ไว้; ห้ามใช้ generated pixels หรือ re-encoding partial decode เป็น replacement',
        '2. หากไม่มี verified replacements ให้พิจารณา readable-subset policy แบบ non-destructive: original validation target ยัง 5,000 ภาพ / 13,260 persons; scored readable view จะเป็น 4,999 ภาพ / 13,257 persons ทุกโมเดลต้องใช้ denominator เดียวและเปิดเผยว่าไม่ใช่ full official-5,000 score',
        '3. หากยังไม่อนุมัติ policy ให้หยุด full evaluation ต่อไป งาน source/synthetic tests และ train-only checkpoint smoke เป็น gate แยกที่ต้องอนุมัติเอง','',
        'ยังไม่สร้างหรือ activate replacement/evaluation views ไม่แก้ official splits หรือ protocol และไม่เริ่ม benchmark','',
        '## แยกจาก blockers อื่น','',
        'ZIP verification นี้ไม่แก้ train/val leakage, GT person ownership, official evaluator parity หรือ actual parser checkpoint feasibility แม้ภายหลัง RGB กู้ได้ ก็ต้องตรวจ gates เหล่านั้นแยกต่างหาก','',
        '## หลักฐานและการรักษาข้อมูล','',
        '[Machine-readable evidence](../provenance/MHPV2_NEW_ZIP_RGB_VERIFICATION.json) มี member paths, CRC32, sizes, hashes, decoding errors, GT links และ scope checks [Independent blocker review](STAGE0_BLOCKER_REVIEW_TH_20261008T082918Z.md) อธิบายทางเลือกและ denominators ของ sensitivity population','',
        'Archive size/mtime/inode, four originals, associated GT, import record, official list bytes, study state และ dataset manifest คงเดิม Git HEAD/branch/status/remotes ของ YOLO หก repositories ตรง preserved evidence ไม่มี full extraction, deletion, dataset/GT/split modification, PPSS activity, model loading, parser/validation inference หรือ Stage 1','',
        '**STOP — รออนุมัติก่อนเปลี่ยน active dataset view หรือ evaluation protocol**',''])
    tmp=report_path.with_suffix('.md.tmp')
    tmp.write_text('\n'.join(lines))
    tmp.replace(report_path)
    print(f'[RGB] recovered: {recovered}/4; unreadable: {unreadable}/4; '+str(dict(outcomes)),flush=True)
    print('[SAFETY] no extraction/replacements/protocol changes/model inference',flush=True)


if __name__=='__main__':
    main()
