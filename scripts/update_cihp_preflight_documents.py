"""Archive active docs and supersede availability claims with actual preflight."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
from copy import deepcopy
import difflib
import json

S=Path(__file__).resolve().parents[1]


def main():
    evidence=json.loads((S/'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json').read_text())
    run=S/'provenance/RUN_MANIFESTS'/evidence['run_id']
    archive=S/'reports/archive'/evidence['run_id'];archive.mkdir(parents=True,exist_ok=False)
    revisions=[]
    def update(path,text,reason):
        old=path.read_bytes();rel=path.relative_to(S) if path.is_relative_to(S) else Path('WORKSPACE_README.md')
        backup=archive/rel;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(old)
        temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(text);temp.replace(path)
        (backup.parent/(backup.name+'.diff')).write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),text.splitlines(True),fromfile=str(rel),tofile=str(rel))))
        revisions.append({'original_path':str(path.relative_to(S)) if path.is_relative_to(S) else '../README.md',
            'archive':str(backup.relative_to(S)),'before_sha256':sha256(old).hexdigest(),
            'after_sha256':sha256(path.read_bytes()).hexdigest(),'reason':reason,'utc':datetime.now(timezone.utc).isoformat()})
    report=S/'reports/DATASET_REASSESSMENT.md';text=report.read_text()
    text=text.replace('1. ตรวจ CIHP ใน workspace: ไม่พบชุดภาพ/GT; พบเพียง source/config/taxonomy ของ parser ที่รองรับ CIHP ตรวจ metadata ของแหล่งทางการต่อ โดยไม่ดาวน์โหลด dataset',
        '1. Initial discovery เคยไม่พบ CIHP; รอบต่อเนื่องตรวจ archive ที่ผู้ใช้โอนมา `datasets/cihp-DatasetNinja.tar` จริงครบทุก payload/JSON/bitmap พบ 38,280 images แต่ native Human_ids/part→person mapping ไม่ retained ไม่มีการดาวน์โหลด dataset เพิ่มหรือ full extraction')
    text=text.replace('**Interpretation:** CIHP มีเหตุผลให้ตรวจต่อ แต่ยังไม่มีหลักฐานว่าดีกว่าหรือสะอาดกว่า MHP-v2 จำนวนคลาสและคำอธิบาย quality control ใน paper ไม่แทน independent audit',
        '**Interpretation:** ขนาดข้างต้นเป็น metadata ของ native official distribution คนละไฟล์กับ local DatasetNinja TAR 2,015,375,360 bytes ที่ตรวจในรอบใหม่ ห้ามเทียบ SHA ของสอง formats เป็น proof of fidelity; CIHP ยังไม่มีหลักฐานว่าสะอาดกว่า MHP-v2')
    text+='''
## CIHP Archive Preflight — ข้อมูลใหม่ 2026-10-08

[Focused preflight report](CIHP_ARCHIVE_PREFLIGHT_AUDIT.md) supersedes availability finding เดิม: local archive พบแล้ว Container PASS; all 768,446 part bitmaps decode/CRC/grid checks PASS; train/validation/test 28,280/5,000/5,000; validation IDs match official GT metadata 5,000/5,000; strict RGB decode 20 sampled images PASS ไม่ใช่ full 38,280-image decode audit

Five official repository RGB/semantic fixtures byte/pixel-identical แต่ไม่มี native Human_ids/person-group fields/tags และ converter ไม่อ่าน Human_ids จึง **BLOCKED สำหรับ person-instance evaluation** Semantic-only audit เป็น conditional track ไม่แทน person-macro/oracle/coverage GT

พบ 39 train–validation exact JPEG-byte groups (39 validation IDs) และ cross-split ทั้งหมด 83 groups; decoded/near-duplicate audit ยังไม่ทำ ชุดนี้ไม่ถูกประกาศ clean จาก integrity PASS และยังไม่ promote CIHP primary DatasetNinja declares MIT แต่ authoritative original dataset-use grant ยังไม่ verified

Next gate เปลี่ยนจาก “หา CIHP archive” เป็น “หา native person GT/full split provenance และตรวจ conversion fidelity” ก่อน Full Quality Audit อ่าน [updated next actions](STAGE0_NEXT_ACTIONS.md) และ [preflight validation](../provenance/CIHP_ARCHIVE_PREFLIGHT_VALIDATION_V1.json) ประวัติ reassessment/tests 51 ข้อเดิมคงไว้; รอบ preflight เพิ่ม 9 tests รวม 60 PASS ไม่มี model/checkpoint inference
'''
    update(report,text,'Local archive availability supersedes earlier discovery; native Human GT and byte-leakage findings')
    update(S/'reports/CIHP_QUALITY_AUDIT.md','''# CIHP — Current Quality Audit Status

**ARCHIVE PRESENT / CONVERTED INTEGRITY PASS / HUMAN-INSTANCE GT BLOCKED / FULL QUALITY AUDIT NOT RUN.** เอกสาร availability ก่อนหน้านี้เก็บใน archive; ไม่มีการเริ่ม Stage 0 ใหม่

อ่าน [CIHP Archive Preflight Audit](CIHP_ARCHIVE_PREFLIGHT_AUDIT.md) เป็นรายงานหลักของ evidence รอบนี้ ครอบ SHA256, TAR/member integrity, splits, bitmap completeness, native taxonomy, instance-information loss, source fidelity และ license provenance

## สถานะที่ตรวจจริง

| รายการ | ผล |
|---|---|
| Local archive | `datasets/cihp-DatasetNinja.tar`, 2,015,375,360 bytes |
| TAR headers/bounds/payload reads/paths/trailer + member hashes | PASS, 76,573 members |
| Image / JSON pairing | 38,280 pairs; no missing/orphan; image-header/GT grids match |
| Labeled images | 28,280 train + 5,000 val = 33,280 |
| Test GT | 5,000 empty JSON placeholders; expected hidden annotations |
| Converted bitmap integrity | All 768,446 decoded, PNG CRC/grid/fidelity PASS |
| Semantic concepts | 19 foreground + implicit background; Human=20 not GT |
| Official validation membership | Exact 5,000-ID match to pinned official GT metadata |
| Full native train/test membership | Not independently verified; counts match |
| RGB full-pixel decoding | 20/20 fixed preflight sample PASS; remaining not strict-decoded |
| Native source semantic fidelity | 5 official repo demo images byte/pixel match; full release not compared |
| Native human ownership | Human_ids/maps/group metadata absent; cannot validate per-human reconstruction |
| Reuse | 39 train–val / 83 all cross-split JPEG-byte groups; no new exclusions |
| Decoded-RGB / near duplicates | Full audit pending |
| Physical-person GT quality | Not reviewed comprehensively; missing human association must be supplemented |
| Licensing | Provider declares MIT; original dataset rights grant still unverified |

Integrity ผ่านไม่ทำให้ semantic/ownership truth ผ่าน ไม่มี error-prevalence estimate และไม่มี primary promotion

## Full Quality Audit ที่เสนอ

แนะนำ supplement native official `Human_ids`, `Category_ids`, `Instance_ids` และ full official split lists ก่อน แล้วตรวจ original-versus-converted semantic/part/human fidelity โดยไม่ overwriting sources Full Quality Audit ต้อง strict-decode RGB ทุกภาพ, ตรวจ cross-map identities/ignore/coordinates, exact decoded and near-duplicate leakage, distributions และ human review 200 stratified TRAIN images

[Review plan V2](../manifests/CIHP_QUALITY_REVIEW_PLAN_V2.json) รอ native Human GT เพื่อใช้ person-count/occupancy strata ที่ถูกต้อง Part-object count ห้ามใช้แทนจำนวนคนโดยไม่เปลี่ยน protocol และห้ามสร้าง person GT จาก YOLO/heuristics

Alternative หลังอนุมัติ: semantic-only quality audit ของ DatasetNinja conversion เป็น cohort แยก โดยยังไม่เรียก native-human benchmark และไม่แก้ person-instance gate ผู้ใช้ต้องอนุมัติ native asset download ถ้าจำเป็น; ไม่จำเป็นต้องโหลด DatasetNinja archive เดิมซ้ำ

**Stage 0 remains BLOCKED / WAITING_FOR_USER_APPROVAL.** ไม่มี full benchmark, checkpoints, training, field test หรือ color study
''','Replace absent-dataset claim with scoped measured archive findings; defer full quality')
    actions=S/'reports/STAGE0_NEXT_ACTIONS.md';text=actions.read_text()
    start=text.index('## Approval 1 —');end=text.index('## Approval 2 —')
    text=text[:start]+'''## Updated next gate — Native CIHP GT ก่อน Full Quality Audit

Local DatasetNinja TAR มีแล้วและ preflight เสร็จ จึงไม่ต้องอนุมัติ download DatasetNinja ซ้ำ [Focused report](CIHP_ARCHIVE_PREFLIGHT_AUDIT.md) ยืนยันครบ 38,280 images/33,280 labeled images/768,446 part objects, แต่ Human_ids และ person ownership ไม่ preserved ภาพซ้ำ train–val แบบ JPEG bytes 39 groups ต้องตรวจ decoded/near duplicates ต่อ

**แนะนำ:** ขอ native official CIHP copy/GT supplement พร้อม Human_ids, Category_ids, Instance_ids/full splits จาก local assets หรือผู้ใช้ หากจำเป็นต้อง download official native release ให้ขออนุมัติแยก: metadata ประมาณ 2,033,753,964 bytes (cap 2.1 GB; ไม่มี checkpoint/packages) ไม่ใช่ renewed permission จาก budget เดิม

หลัง native GT พร้อมและได้รับอนุมัติ Full Quality Audit: strict-decode ทุก RGB, paired native-map validation, full conversion fidelity, ignore/overlap semantics, decoded/near-duplicate leakage, class/person counts และ deterministic 200-image stratified TRAIN review ตาม [V2 plan](../manifests/CIHP_QUALITY_REVIEW_PLAN_V2.json) ห้าม auto exclude/relabel source GT หรือตั้ง CIHP primary จาก integrity เพียงอย่างเดียว

ทางเลือก: semantic-only Full Quality Audit ของ conversion เป็น separate cohort หลังอนุมัติ แต่จะยังไม่มี oracle-person geometry, person-macro, matched coverage หรือ native APp/PCP GT ห้ามเดา Human_ids จาก YOLO/connected components/part grouping แล้วถือเป็น native truth

Provider/license file declares MIT แต่ original dataset rights ยังไม่ verified จึงต้องอ่าน native release terms/clarify scopeก่อน evaluation/publication/deployment ไม่มี full extraction/download/checkpoint execution ใน preflight นี้

'''+text[end:]
    text+='''
## Preflight execution evidence — 2026-10-08

All TAR regular payloads read and SHA256-inventoried; all converted bitmaps decoded/CRC/coordinate checks passed; strict RGB sample 20/20 passed; official semantic demo fidelity 5/5 passed; actual human metadata missing confirmed by all-JSON and converter AST audit New decoder tests 9 + existing 51 = **60 PASS** No full RGB/semantic-quality/ownership audit claim

[Preflight manifest](../manifests/CIHP_DATASETNINJA_ARCHIVE_MANIFEST_V1.json), [validation](../provenance/CIHP_ARCHIVE_PREFLIGHT_VALIDATION_V1.json), [byte-duplicate evidence](../provenance/CIHP_DATASETNINJA_BYTE_DUPLICATES_V1.json). Previous run/validation preserved as historical evidence; current docs archived before edits
'''
    update(actions,text,'Replace acquisition-of-absent-CIHP gate with missing-native-person-GT gate; no new execution permission')
    decision=S/'reports/PRIMARY_DATASET_DECISION.md';text=decision.read_text()
    text=text.replace('Paper/source มี human/part maps; local semantics ยังไม่ตรวจ','Native source มี human/part maps; local DatasetNinja lacks human ownership metadata')
    text=text.replace('ไม่มี local data; NOT TESTED','Local TAR/bitmap integrity PASS; RGB strict decoding sampled 20 only')
    text=text.replace('Exact/near duplicate audits ยังไม่ทำ','39 exact JPEG-byte train–val groups confirmed; full decoded/near audit pending')
    text=text.replace('Official archive metadata/commit verified; local checksum/reader/evaluator fidelity ยังไม่มี','Local converted SHA256/reader tested; official demo semantic parity 5/5; human GT missing/full native parity pending')
    text+='''
## Preflight amendment

CIHP archive exists; availability is no longer a blocker. Native-human ownership loss is a genuine input-contract blocker for this study's person-instance tracks, not proof that native CIHP is poor quality. Provisional A remains a direction conditional on obtaining native GT and completing an independent quality audit. DatasetNinja semantic-only track cannot substitute silently for native human parsing; no primary promotion or final role freeze.
'''
    update(decision,text,'Decision matrix reflects observed conversion/duplicate risks without promoting CIHP')
    readme=S/'README.md';text=readme.read_text()
    text=text.replace('absent locally; official archive metadata 2,033,753,964 bytes; acquisition and dataset permission pending.',
        'DatasetNinja archive present and audited; native Human GT missing, full quality and dataset permission pending.')
    text=text.replace('[Current validation](provenance/DATASET_REASSESSMENT_VALIDATION.json)',
        '[Current preflight validation](provenance/CIHP_ARCHIVE_PREFLIGHT_VALIDATION_V1.json), [prior reassessment validation](provenance/DATASET_REASSESSMENT_VALIDATION.json)')
    text=text.replace('[CIHP\'s proposed 200-image stratified review](manifests/CIHP_QUALITY_REVIEW_PLAN_V1.json) has no IDs until the dataset exists.',
        '[CIHP\'s 200-image review V2](manifests/CIHP_QUALITY_REVIEW_PLAN_V2.json) waits for native human GT, with no fabricated person strata.')
    text+='''
## CIHP archive preflight — current evidence

[Focused report](reports/CIHP_ARCHIVE_PREFLIGHT_AUDIT.md): local converted TAR SHA256 and all member inventory; 38,280 RGB/JSON pairs, 768,446 part bitmaps validated; 20 strict JPEG sample decodes; five official semantic demo matches. Original human-instance ownership data is absent, so native person GT readiness is **BLOCKED** despite file/bitmap integrity PASS. 39 exact train–val JPEG-byte duplicate groups; full leakage/quality review pending. **60 bounded tests passed; zero model inference.**

[Archive manifest](manifests/CIHP_DATASETNINJA_ARCHIVE_MANIFEST_V1.json), [preflight JSON](provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json), [duplicate evidence](provenance/CIHP_DATASETNINJA_BYTE_DUPLICATES_V1.json), [revision/archives](provenance/CIHP_PREFLIGHT_DOCUMENT_REVISIONS_V1.json). No full extraction, native dataset download, primary promotion or Stage 1 authorization. Native GT supplement and Full Quality Audit require the next review decision.
'''
    update(readme,text,'Landing page reflects present converted archive and missing native-human GT')
    protocol=S/'EXPERIMENT_PROTOCOL_DRAFT.md';text=protocol.read_text().replace('Version `0.2-DRAFT`','Version `0.3-DRAFT`')
    text=text.replace('CIHP is absent locally: source taxonomy/archive metadata are not a GT-quality audit.',
        'A local DatasetNinja CIHP TAR passed container/bitmap preflight; native Human_ids/person association is missing. This is not a full GT-quality or human-instance-fidelity audit.')
    text+='''
## Converted CIHP input-contract gate

The DatasetNinja export retains semantic part objects with project object/class IDs, not validated GT human identities. No oracle-person crops, person-macro, detector coverage or human APp/PCP may be computed from inferred grouping. Obtain and fidelity-check native human/semantic/part maps before native-human tracks. A separately approved semantic-only cohort would use different GT assumptions and must not replace person-instance evaluation silently. Archive validation-ID compatibility and 5 demo semantic matches are not whole-release provenance/quality proof. Full RGB decoding, decoded/near-duplicate audit and stratified human GT review remain pending; CIHP primary role and COMMON_HP remain unfrozen.
'''
    update(protocol,text,'Input-contract blocker for DatasetNinja human GT; no protocol freeze')
    schema=S/'DATA_SCHEMA.md';text=schema.read_text()+'''
## CIHP DatasetNinja archive preflight — v1

`CIHP_DATASETNINJA_ARCHIVE_MANIFEST_V1.json` records archive size/SHA256, member inventory/digest and split image IDs, annotation counts and part-object counts. Part-object IDs and Supervisely numeric class IDs are not person/native semantic IDs. `CIHP_ARCHIVE_PREFLIGHT_V1.json` separates all-member payload/bitmap integrity, header-grid checks, bounded strict JPEG loading, 5 source-fixture semantic parity, full split verification scope and missing native human GT.

`cihp_datasetninja.py` decodes alpha support from base64(zlib(PNG)) and explicit origin. Native concepts use reviewed converter title mapping; no Human=20 GT class. Semantic reconstruction is a derived diagnostic with explicit overlap/overwrite counts and unknown original void fidelity, not lossless per-human GT. It never manufactures person IDs. `CIHP_DATASETNINJA_BYTE_DUPLICATES_V1.json` records exact file-byte groups/IDs only; no automatic exclusions or decoded/near-duplicate equivalence claim.
'''
    update(schema,text,'Document actual converted-archive representation and missing ownership')
    state_path=S/'STUDY_STATE.json';state=json.loads(state_path.read_text());paused=deepcopy({k:v for k,v in state.items() if k.startswith('ppss')})
    state['dataset_reassessment']['CIHP_local_status']='DATASETNINJA_ARCHIVE_PRESENT_NATIVE_HUMAN_GT_BLOCKED'
    state['cihp_archive_preflight']={'run_id':evidence['run_id'],'container_integrity':'PASS','converted_bitmap_integrity':'PASS',
        'archive_workspace_relative':evidence['archive_workspace_relative'],'archive_sha256':evidence['archive_sha256'],
        'images':38280,'labeled_images':33280,'part_objects':768446,'native_human_GT_ready':False,
        'validation_ID_compatibility':'EXACT_OFFICIAL_GT_METADATA_MATCH','full_native_train_test_ID_parity':'UNVERIFIED',
        'strict_RGB_sample_passed':20,'full_quality_audit_started':False,'primary_promoted':False,
        'tests_passed':60,'model_inference':False,'validation':'provenance/CIHP_ARCHIVE_PREFLIGHT_VALIDATION_V1.json',
        'next_gate':'NATIVE_HUMAN_GT_SUPPLEMENT_AND_FULL_QUALITY_REVIEW_APPROVAL'}
    state['last_updated_utc']=datetime.now(timezone.utc).isoformat()
    assert paused=={k:v for k,v in state.items() if k.startswith('ppss')}
    update(state_path,json.dumps(state,ensure_ascii=False,indent=2)+'\n','Current archive state; historical/paused nodes preserved')
    root=S.parent/'README.md';text=root.read_text()
    text=text.replace('CIHP is absent locally: its official archive metadata is 2,033,753,964 bytes; acquisition/quality/license review awaits approval.',
        'CIHP DatasetNinja TAR is now present: [archive preflight](Human_Parsing_MHPv2_Study/reports/CIHP_ARCHIVE_PREFLIGHT_AUDIT.md) verifies 38,280 images and converted bitmaps, but native person ownership is absent. Full quality/native GT/license review awaits approval; no primary promotion.')
    update(root,text,'Workspace navigation reflects new archive evidence; prior historical sections retained')
    plan=json.loads((S/'manifests/CIHP_QUALITY_REVIEW_PLAN_V1.json').read_text());plan['schema_version']='1.1';plan['status']='DRAFT_WAITING_NATIVE_HUMAN_GT_FULL_AUDIT_APPROVAL'
    plan['supersedes']='manifests/CIHP_QUALITY_REVIEW_PLAN_V1.json';plan['archive_available']=True
    plan['native_person_GT_available']=False;plan['downloaded_by_this_execution']=False
    plan['critical_prerequisite']='Fidelity-verified native Human_ids + semantic/part maps; part-object count is not person count'
    plan['semantic_only_alternative']='Separate review design after explicit scope approval; cannot silently substitute person-count strata'
    (S/'manifests/CIHP_QUALITY_REVIEW_PLAN_V2.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    (S/'provenance/CIHP_PREFLIGHT_DOCUMENT_REVISIONS_V1.json').write_text(json.dumps({'run_id':evidence['run_id'],'revisions':revisions,'original_datasets_modified':False,'native_Human_GT_repair_performed':False},indent=2)+'\n')
    print(f'[DOCS] archived/updated {len(revisions)} current documents; native human-GT gate recorded; no primary promotion')


if __name__=='__main__':main()
