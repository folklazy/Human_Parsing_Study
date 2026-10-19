"""Finalize reviewable handoff evidence. No model, dataset, or benchmark execution."""
from pathlib import Path
import csv,json,datetime,hashlib,shutil,subprocess,re
S=Path(__file__).resolve().parents[1];W=S.parent
R=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run'];stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
validation_path=S/json.loads((R/'LATEST_VALIDATION.json').read_text())['path'];validation=json.loads(validation_path.read_text());assert validation['status']=='PASS'
smokes=json.loads((R/'SMOKE_SUMMARY.json').read_text());assets=json.loads((R/'CHECKPOINT_MANIFEST.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Enrich the new revision only; historical registries stay untouched.
registry_path=S/'provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V4.csv';registry=list(csv.DictReader(registry_path.open()))
plans=[row for p in (W/'Human_Parsing_CCIHP_10_Image_Pilot/configs').glob('CHECKPOINT_DOWNLOAD_PLAN*.json') for row in json.loads(p.read_text()).get('checkpoints',[])]
official_names={f['id']:f['path'] for folder in json.loads((R/'OFFICIAL_FOLDER_DISCOVERY.json').read_text()) for f in folder.get('files',[])}
plan_by_id={p['model_id']:p for p in plans};discovery=json.loads((R/'OFFICIAL_ROSTER_DISCOVERY.json').read_text());remote_by_family={x['family']:x['remote'] for x in discovery}
for row in registry:
 mid=row['model_id'];family='CPI-Parser' if mid.startswith('CPI_') else 'RP-R-CNN' if mid.startswith('RPR_') else 'fashn-human-parser' if mid.startswith('FASHN') else 'sapiens2' if mid.startswith('Sapiens2') else mid.split('_')[0]
 row['family']=family;row['official_repository']=remote_by_family.get(family,'')
 artifact=next((a for a in assets['files'] if a['sha256']==row.get('checkpoint_sha256')),None)
 plan=plan_by_id.get(mid)
 if artifact:
  row['official_checkpoint_url']=(plan or {}).get('url',artifact.get('source_url',''))
  if not row['official_checkpoint_url'] and mid.startswith('Sapiens2'):
   alias='Sapiens2_'+mid.split('_')[-1].upper();plan=next((p for p in plans if p.get('destination','').endswith('/'+mid.split('_')[-1]+'/sapiens2_'+mid.split('_')[-1]+'_seg.safetensors')),None)
   if plan:row['official_checkpoint_url']=plan['url']
  row['original_filename'] = artifact.get('original_filename',row['official_checkpoint_url'].split('/')[-1] if row['official_checkpoint_url'] else Path(artifact['path']).name)
 if row.get('official_checkpoint_url') and 'drive.google.com' in row['official_checkpoint_url']:
  match=re.search(r'/d/([A-Za-z0-9_-]+)',row['official_checkpoint_url'])
  row['original_filename']=official_names.get(match[1],'NOT_VERIFIED_LEGACY_RENAMED_FILE') if match else 'NOT_VERIFIED_LEGACY_RENAMED_FILE'
 row['training_dataset']='MHPV2' if 'MHPV2' in mid else 'CIHP' if 'CIHP' in mid else 'LIP' if 'LIP' in mid else 'ATR' if 'ATR' in mid else 'Pascal-Person-Part' if 'PASCAL' in mid else 'SEE_OFFICIAL_MODEL_CARD'
 row['backbone']='ResNet101' if family in ['M2FP','D2FP','SCHP','CDGNet'] else 'ConvNeXt-B' if 'ConvNeXtB' in mid else 'ResNet50' if family in ['CPI-Parser','RP-R-CNN'] or mid=='QANet_CIHP' else 'HRNet-W48' if family=='QANet' else 'MiT-B4' if family=='fashn-human-parser' else 'SEE_VARIANT'
 row['framework']='PyTorch1.10.2+cu113' if family not in ['fashn-human-parser','sapiens2'] else 'SEE_ENVIRONMENT_PROFILE'
 row['license_evidence']='provenance/LICENSE_MATRIX_DECISION5A_V1.csv; '+str(R.relative_to(S))+'/OFFICIAL_ROSTER_DISCOVERY.json'
 row['code_weight_dependency_licenses']='Separate; see prior license matrix and official source notices. No commercial clearance.'
 if mid=='CDGNet_LIP':row['reason']='Author Baidu share and published code verified (errno=0), filename verified; automated public download path unresolved, NOT a missing-checkpoint claim.'
fields=sorted(set().union(*(r.keys() for r in registry)))
with registry_path.open('w') as f:
 writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(registry)
# Record actual requirement coverage, including intentionally disabled APIs.
test_file='tests/test_application_v2_handoff.py'
rows=[
 ('A01','PASS','ConfiguredRunner.score_frame: checkpoint/config/head/class order mismatch rejected using accepted synthetic context'),
 ('A02','PASS','score_frame rejects LIP unsupported Exposed_torso in common-capability fixture'),
 ('A03','NOT_IMPLEMENTED','Live ConfiguredRunner rejects DRAFT/UNKNOWN/hash changes; cached scoring is absent and disabled'),
 ('A04','PASS','Trusted original W/H checked on scored arrays, including no GT'),
 ('A05','PASS','Unmatched/no-GT invalid IDs/dtype/score/duplicate identities rejected'),
 ('A06','PASS','G_loc=1 G_sem=0 no prediction => FN1 recall0 semantic null'),
 ('A07','PASS','10 GT semantic persons with 8 perfect outputs => Q=.8, G_sem=10'),
 ('A08','PASS','Actual person runner failure ledger through final matching; other valid output => no duplicate FN'),
 ('A09','PASS','Actual PERSON failure retains other valid final outputs under explicit fixture policy'),
 ('A10','PASS','Strict/operational eligibility and invalid/incomplete states tested; finalizer contract failure distinguished'),
 ('A11','PASS','Empty GT/output and GT-supported/prediction-only/undefined cases tested across actual numerical API'),
 ('A12','PASS','100 correct A + 900 B leakage => semantic IoU1 / foreground IoU.1'),
 ('A13','PASS','Known-negative FP versus void, owner-unknown global/person handling tested'),
 ('A14','PASS','Permuted GT/prediction rows with immutable IDs produce identical matched IDs and metrics'),
 ('A15','PASS','Actual scoring uses declared evaluation bbox provenance, independently of conditioning bbox'),
 ('A16','NOT_IMPLEMENTED','Existing packet resume hash/finalization/fingerprint rejection tests pass; workflow resume/cached scorer absent'),
 ('A17','NOT_IMPLEMENTED','Retention capability API rejects probabilities from hard labels; production re-scoring API remains disabled'),
 ('A18','NOT_IMPLEMENTED','Inference/scoring fingerprint separation tested, including scoring context; actual cached re-score route absent'),
 ('A19','NOT_IMPLEMENTED','Declared artifact-set checks reject missing/partial shards and distinguish duplicate content; acquired set hash-verified. Immutable-version resume policy not implemented for mutable Drive shares; not certified.'),
 ('A20','PASS','21 actual checkpoint/component FP32 TRAIN smokes; CPI canonical T1/T3B exports pass. Limited to these routes; all-variant YOLO integration and joint runtime NOT_TESTED')]
acceptance=[dict(id=i,status=status,evidence_scope=reason,validation=str(validation_path.relative_to(S)),source_revision_sha256=validation['source_revision_sha256']) for i,status,reason in rows]
(R/'ACCEPTANCE_A01_A20.json').write_text(json.dumps(acceptance,indent=2)+'\n')
archive=S/'reports/archive'/('implementation_handoff_'+stamp);archive.mkdir(parents=True)
archived=[]
for name in ['README.md','STUDY_STATE.json','reports/APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md']:
 p=S/name;q=archive/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);archived.append({'original':name,'archive':str(q.relative_to(S)),'before_sha256':sha(p)})
report=S/'reports/APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md'
def link_run(name):return '../'+str((R/name).relative_to(S))
text=f'''# ผลดำเนินการ Implementation Handoff — 15 ตุลาคม 2026

**สถานะงานที่ดำเนินได้: PASS WITH WARNINGS — พร้อมตรวจรับงานวิศวกรรม; scientific freeze / full benchmark ยัง BLOCKED**

ทำต่อจาก server implementation เดิมตาม handoff1.1 ไม่เริ่ม study ใหม่ ไม่มี VAL inference, training, CCTV, fusion หรือ full benchmark ผล CPU ล่าสุด **{validation['tests']} tests ผ่าน** และ protected hashes **{validation['protected_hashes_checked']} รายการตรงเดิม** จำนวน tests เป็นรายละเอียดหลักฐาน ไม่ใช่เกณฑ์รับรองทุก production route

## 1. สิ่งที่แก้จริง

- แยก CIHP/LIP numeric mapping: class10 Torso-skin กับ Jumpsuits คนละความหมาย ปฏิเสธ ambiguous V1 สำหรับ prediction; เก็บ V1 ไว้อ่าน GT/ประวัติ
- ตรวจ emitted masks ทั้งหมดก่อน matching แม้ไม่มี GT, ไม่มี semantic GT หรือ unmatched ตรวจ original W/H จาก trusted input, integer labels, finite scores, unique IDs และ G_sem ⊆ G_loc
- เพิ่ม shared scoring boundary และเชื่อม `ConfiguredRunner.score_frame`/`score_person_result`; context ต้องมี accepted decision binding การแก้ config อย่างเดียวเปิดคะแนนไม่ได้
- บังคับ target-support / mapping hash / model binding / GT-domain acceptance / evaluation bbox provenance; config จริงยังไม่มี accepted context จึงให้คะแนน benchmark ไม่ได้
- แยก contract failure จาก model failure; failure event ไม่เพิ่ม FN ซ้ำจากการจับคู่ final outputs กลไก strict/operational ผ่าน fixtures แต่ยังไม่ได้เลือกนโยบายหลัก
- ทำผลรายคนเรียง immutable ID ให้ reproducible เมื่อสลับ row order และเพิ่ม scoring-context dependency ใน scoring fingerprint
- เพิ่มการตรวจ artifact-set completeness และเอกสาร capability/retention โดยไม่อ้างว่ามี production cached scorer หรือ workflow resume

ใช้ [config V3](../configs/application_v2_handoff_v3.yaml), [decision V3](../provenance/APPLICATION_V2_DECISIONS_V3.json), [mapping V2](../taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V2.json), [view cards DRAFT](../taxonomy/APPLICATION_HANDOFF_VIEW_CARDS_DRAFT_V1.json) และ [รายละเอียดนโยบาย](APPLICATION_HANDOFF_POLICIES_TH_20261015.md)

ไม่พบ `APPLICATION_V2_CPU_FIXES_20261014.zip` และคู่มือ `(2).md` ที่ handoff อ้างถึง จึง **ไม่ได้ apply หรือรับรอง remote patch** งานนี้แก้จาก source server และ failure ที่ทำซ้ำได้ ไม่อ้างว่าเป็น patched103-tests เดิม

## 2. Evidence และข้อจำกัด

| ประเภท | สถานะ | ขอบเขต |
|---|---|---|
| CPU tests รอบนี้ | VERIFIED | {validation['tests']} tests จาก 6 suite patterns; log/commands/source hash อยู่ใน validation |
| A01–A20 | VERIFIED_WITH_DISABLED_CAPABILITIES | แยกขอบเขตแต่ละแถวด้านล่าง |
| Checkpoint inference ใหม่ | VERIFIED | TRAIN `0000930` 1 ภาพต่อ checkpoint/component ที่ผ่าน 21 รายการ |
| CPI canonical contract | VERIFIED | 8 immutable packets: 4 variants × T1/T3B |
| T3B conditioning รอบนี้ | VERIFIED_SAVED_YOLO | fresh native CPI + saved verified YOLO ภาพเดียวกัน; ไม่ใช่ jointly timed live system |
| Native FP32 profile | VERIFIED_LIMITED | parameters checked by worker, floating module outputs FP32, autocast/TF32/seeds/env recorded; internal ops ไม่ได้ตรวจทุก kernel |
| Remote CPU patch 103 tests | REPORTED_NOT_REVERIFIED | ไม่มี ZIP ให้ตรวจ parity |
| Accepted common taxonomy/domain/population | PROPOSED / BLOCKED | ยังไม่มีการรับรอง semantic mapping และ annotation completeness |
| Cached scorer / workflow resume | NOT_IMPLEMENTED_DISABLED | packet-integrity helper ไม่แทน production scheduling/rescore |
| Benchmark/model winner | NOT_TESTED | ไม่จัดอันดับจาก smoke |

[Validation และ commands]({link_run('LATEST_VALIDATION.json')}) · [source/patch ก่อนแก้]({link_run('BEFORE.json')}) · [input evidence status]({link_run('INPUT_EVIDENCE_STATUS.json')}) · [data-use ledger]({link_run('DATA_USE_LEDGER.json')})

## 3. Acceptance A01–A20

PASS ในตารางหมายถึง behavior ตาม scope ที่เขียน ไม่ขยายเป็นทุก runtime/route หรือ final benchmark

| ID | ผล | หลักฐาน / ขอบเขต |
|---|---|---|
'''
for row in acceptance:text+=f"| {row['id']} | {row['status']} | {row['evidence_scope']} |\n"
text+=f'''
ดู [machine-readable acceptance matrix]({link_run('ACCEPTANCE_A01_A20.json')}) และ tests ผ่าน entry point จริงใน `test_application_v2_handoff.py` พร้อม `test_application_v2.py`/`test_application_v2_acquisition.py`

## 4. ดาวน์โหลด official roster

ตรวจ author repositories/folders ของ 9 families ณรอบนี้ เก็บ exact local source commits และ official README responses ไม่อ้างว่าค้นพบทุกโมเดลที่มีในโลก

- Checkpoint content ที่มีอยู่ทั้งหมด **{assets['unique_content_artifacts']} unique artifacts** / **{assets['unique_inode_files']} physical inode files**, มี {assets['checkpoint_path_entries_including_aliases']} paths รวม aliases เดิม
- ใน unique artifacts มี 25 parser weights/components และ 1 auxiliary detector; SCHP global/local เป็น components ไม่ใช่สองระบบ multi-person ที่รันครบแล้ว
- เพิ่มใหม่ **{assets['new_checkpoint_artifacts']} artifacts**: parser weights/components {assets['new_parser_checkpoints']} + auxiliary detector {assets['new_auxiliary_checkpoints']}
- New checkpoint bytes **{assets['new_checkpoint_bytes']:,} bytes = {assets['new_checkpoint_bytes']/1e9:.3f} GB**; configs เพิ่มแยกใน acquisition results
- Unique checkpoint content รวม **{assets['unique_checkpoint_content_bytes']/1e9:.3f} GB**; directory ใช้ disk allocation **{assets['all_human_parsing_storage_allocated_bytes_including_old_partials']/1e9:.3f} GB** รวม old partial/cache fragments ซึ่งยังไม่ลบ
- SHA256 เป็น local content fingerprint; ถ้า author ไม่มี checksum ไม่อ้าง cryptographic authenticity จาก hash ที่คำนวณเอง
- เก็บ original filenames ของ assets ใหม่; ของเดิมที่เคยใช้ชื่อ `model.pth` ไม่ย้ายและไม่ทำสำเนาซ้ำ

Assets ใหม่: SCHP CIHP global/local, CIHP auxiliary Mask R-CNN, QANet CIHP HRNet-W48 512×384 และ QANet LIP HRNet-W48 544×416 พร้อม author configs

| ยังไม่ได้ / จำกัด | ผลตรวจ |
|---|---|
| M2FP Pascal-Person-Part | official result table ไม่มี checkpoint download link; ไม่ใช้ backbone แทน parser |
| QANet MHP-v2 / CIHP R101 | ไม่พบ parser release link ใน official table ที่ตรวจ |
| CDGNet LIP | official Baidu share และ public extraction code ใช้ได้; พบชื่อ `LIP_epoch_149.pth`; automated client download path ยังไม่สำเร็จ จึงเป็น DOWNLOAD_NOT_OBTAINED ไม่ใช่ CHECKPOINT_UNAVAILABLE |
| Sapiens2 0.4/0.8/1/5B | weights เดิมครบและ hash ตรวจแล้ว; **USE_RESTRICTED / NOT_EXECUTED_THIS_REVISION** ตาม handoff |
| Auxiliary SCHP detector | ดาวน์โหลดและ hash แล้ว; **NOT_TESTED** inference ในรอบนี้ |

[Official discovery]({link_run('OFFICIAL_ROSTER_DISCOVERY.json')}) · [checkpoint SHA256 manifest]({link_run('CHECKPOINT_MANIFEST.json')}) · [new asset-set verification]({link_run('ADDITIONAL_ASSET_SET_VALIDATION.json')}) · [registry V4](../provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V4.csv)

ยังไม่รับรอง resumable download ของ mutable Drive shares ข้าม source versions; gdown ใช้ partial files แต่การมี `.part` ไม่ใช่ VERIFIED และไม่มีการอ้างว่าได้ทดสอบ immutable-version resume ครบใน A19

## 5. Actual FP32 TRAIN feasibility

GPU Tesla T4 / driver580.178.04; no warmups, one TRAIN image per checkpoint, parser sequential, native preprocessing/TTA ตาม worker ไม่ใช้ smoke time จัดอันดับ เนื่องจาก boundaries ต่างกันและมี asset/hash/download activity บางช่วง

| Checkpoint / component | Native mode | Native inference | Allocated MiB | Reserved MiB | Canonical export รอบนี้ |
|---|---|---|---:|---:|---|
'''
for x in smokes:text+=f"| {x['model_id']} | {x['mode']} | {x['status']} | {x['peak_allocated_mib']:.1f} | {x['peak_reserved_mib']:.1f} | {x['canonical_contract']} |\n"
text+=f'''
ทั้ง 21 checkpoint/component ผ่าน input นี้บน T4 FP32 ไม่ได้แปลว่าทุกภาพหรือทุก joint pipeline จะพอดี VRAM โดยเฉพาะ CPI-R50 CIHP เคยมี OOM ใน pilot10ภาพเดิม; ครั้งนี้ผ่าน1ภาพไม่ลบข้อจำกัดนั้น SCHP global/local ผ่านเฉพาะ component, ไม่ได้รัน native detector/global-local composition/fusion

Attempt แรกของ launcher ล้มก่อน model loading เพราะ environment ไม่มี pip; แก้ metadata capture ให้ใช้ `importlib.metadata` โดยไม่ติดตั้ง pip ต่อมา SCHP ขาด ninja ใน PATH; คืน path ของ tools เดิมและ copy compiled cache ไป run directory จึงผ่าน ไม่แก้ YOLO environment, system CUDA หรือ driver เก็บ failed-attempt logs ไว้

Native identities มีเฉพาะ interface ที่รองรับ Semantic parser + crop ยังไม่มี native identity การใส่ oracle/YOLO ID ภายหลังไม่เปลี่ยนความสามารถนั้น

[Smoke summary / output hashes]({link_run('SMOKE_SUMMARY.json')}) · [native logs/profiles]({link_run('native_smoke/logs')}) · [canonical CPI evidence]({link_run('CANONICAL_SMOKE.json')}) · [artifact capabilities]({link_run('ARTIFACT_CAPABILITIES.json')})

## 6. Readiness ต่อกลุ่ม

| กลุ่ม | สถานะ | ยังขาด |
|---|---|---|
| Native technical feasibility ของ weights ที่ทดสอบ | VERIFIED_LIMITED | actual benchmark config/profile แยกจาก smoke |
| CPI T1/T3B schema + saved-YOLO association | VERIFIED_LIMITED | live joint workload/memory/timing และ accepted evaluation context |
| CIHP-body/clothing common-capability cohort | BLOCKED_FOR_FREEZE | mapping/domain/population/matching/failure acceptance |
| LIP ร่วม cohort ที่ต้องมี Exposed_torso | INELIGIBLE_UNDER_CURRENT_SUPPORT | แยก cohort หรือเสนอ common view ใหม่พร้อม semantic coverage |
| V0 full-person silhouette | BLOCKED_DEFINITION | hair/hat exclusion และ annotation completeness |
| Cached scoring / workflow resume | DISABLED | ยังไม่มี actual production API |
| Sapiens2 execution | USE_RESTRICTED | applicable permission สำหรับ surveillance-related research |

ไม่มี comparison group ถูก freeze หรืออนุญาต full benchmark ในรอบนี้ การเลือกผู้ชนะต้องมี approved selection data และกติกาที่กำหนดก่อนดูผล

## 7. สิ่งที่ต้องตัดสินใจต่อ

1. **Failure scoring:** แนะนำ STRICT_COMPLETE เป็นคะแนนหลัก เก็บ operational behavior diagnostic แยก อีกทางคือ OPERATIONAL_EMPTY_FALLBACK เป็นโจทย์หลัก ซึ่งต้องกำหนด eligible states/denominators ก่อนผลจริง กลไกสองแบบ implement/test แล้ว
2. **Taxonomy cohorts:** แนะนำแยก CIHP-capability กับ LIP จนมี shared body/clothing view ที่อธิบายได้ ไม่ void exposed-torso เฉพาะ LIP เพื่อทำตารางรวม
3. **GT domain/population/matching:** ต้องรับรองจาก annotation evidence และประชากรที่ระบุชัด ยังไม่เสนอให้ยอมรับ background ทุก pixel เป็น known negative การยืนยัน policy โดยผู้ใช้ไม่แทนหลักฐาน annotation completeness

ดูคำอธิบายและผลกระทบใน [policy review](APPLICATION_HANDOFF_POLICIES_TH_20261015.md) ขั้นถัดไปคือรับรองเฉพาะ decision/config ที่ยังค้างและตรวจ actual route ของ comparison group แรก **ยังไม่ใช่เริ่ม full benchmark**

## 8. Preservation และ version control

Protected measured/source artifacts {validation['protected_hashes_checked']} รายการ hash ตรงเดิม; original archive stat checks ตรงเดิม ไม่แก้ raw MHP-v2/CIHP/CCIHP/PPSS, frozen YOLO checkpoint หรือผล YOLO ไม่มี training/fusion/color/CCTV/VAL inference ไม่ติดตั้ง package เพิ่ม

Workspace root และ study นี้ไม่มี `.git` จึงไม่มี commit/branch/diff ของ Git และไม่ได้สร้าง remote/push เก็บ before snapshots, unified source diff และ content-addressed source revision แทน; ไม่อ้างว่า Git validation PASS

Source revision: `{validation['source_revision_sha256']}`
'''
report.write_text(text)
readme=S/'README.md';current=readme.read_text();prefix=f'''# Human Parsing Study — Implementation V2

**ล่าสุด 15 ตุลาคม 2026: engineering handoff พร้อมตรวจรับ โดย scientific freeze / full benchmark ยัง BLOCKED**

- [ผลดำเนินการและ A01–A20](reports/APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md)
- [กติกาที่ยังรอรับรองและข้อจำกัด](reports/APPLICATION_HANDOFF_POLICIES_TH_20261015.md)
- [Executable config V3 — DRAFT](configs/application_v2_handoff_v3.yaml)
- [Model/checkpoint registry V4](provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V4.csv)
- [Evidence pointer](provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json)

CPU regression {validation['tests']} tests ผ่าน; protected hashes {validation['protected_hashes_checked']} รายการตรงเดิม Actual FP32 TRAIN smoke ผ่าน 21 checkpoints/components บนภาพเดียว; CPI canonical exports 8 packets ผ่าน ยังไม่ใช่ทุกระบบ YOLO-conditioned และไม่ใช้ smoke เลือกผู้ชนะ

## หลักฐาน implementation ก่อนรอบล่าสุด

'''
baseline=current.split('## หลักฐาน implementation ก่อนรอบล่าสุด\n\n',1)[-1] if '## หลักฐาน implementation ก่อนรอบล่าสุด' in current else current.split('\n',1)[1]
baseline=baseline.replace('## สถานะปัจจุบัน','## สถานะที่บันทึกไว้ ณ 14 ตุลาคม 2026')
readme.write_text(prefix+baseline)
statepath=S/'STUDY_STATE.json';state=json.loads(statepath.read_text());state['last_updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();state['implementation_handoff_20261015']={'status':'ENGINEERING_REVIEW_READY_WITH_WARNINGS','scientific_freeze':'BLOCKED_PENDING_DECISIONS_AND_EVIDENCE','validation':str(validation_path.relative_to(S)),'tests':validation['tests'],'native_checkpoint_smokes_passed':len(smokes),'canonical_packets':8,'new_checkpoints':5,'registry':'provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V4.csv','report':str(report.relative_to(S)),'full_benchmark_authorized':False,'full_benchmark_started':False,'remote_patch_applied':False,'cached_scorer':'NOT_IMPLEMENTED_DISABLED','workflow_resume':'NOT_IMPLEMENTED_DISABLED'};statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
for a in archived:a['after_sha256']=sha(S/a['original']);a['reason']='Add latest evidence navigation and additive state; preserve historical records'
(R/'EDITORIAL_ARCHIVES.json').write_text(json.dumps(archived,indent=2)+'\n')
# Snapshot all current implementation + tests/config/source provenance without environments or raw data.
snapshot=R/('final_source_snapshot_'+stamp);snapshot.mkdir()
paths=[p for base in [S/'src/application_v2',S/'tests'] for p in base.glob('*.py')]
paths += [S/'scripts'/n for n in ['audit_handoff_assets.py','acquire_handoff_additions.py','prepare_handoff_smoke.py','run_handoff_smoke_worker.py','run_handoff_smokes.py','export_handoff_cpi_contract.py','validate_implementation_handoff.py','summarize_handoff_evidence.py','finalize_implementation_handoff.py','check_cdgnet_public_access.py']]
paths += [S/n for n in ['configs/application_v2_handoff_v3.yaml','provenance/APPLICATION_V2_DECISIONS_V3.json','taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V2.json','taxonomy/APPLICATION_HANDOFF_VIEW_CARDS_DRAFT_V1.json']]
files=[]
for p in paths:
 q=snapshot/p.relative_to(S);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);files.append({'path':str(p.relative_to(S)),'sha256':sha(p)})
(snapshot/'MANIFEST.json').write_text(json.dumps(files,indent=2)+'\n')
final={'status':'ENGINEERING_REVIEW_READY_WITH_WARNINGS','scientific_readiness':'BLOCKED_PENDING_ACCEPTANCE','validation':str(validation_path.relative_to(S)),'acceptance':str((R/'ACCEPTANCE_A01_A20.json').relative_to(S)),'report':str(report.relative_to(S)),'source_snapshot':str(snapshot.relative_to(S)),'full_benchmark':False,'inference_scope':'TRAIN_ONE_IMAGE_PER_ELIGIBLE_CHECKPOINT_COMPONENT','datasets_modified':False,'YOLO_results_modified':False,'PPSS_modified':False,'Sapiens2_executed':False,'git_status':'NO_GIT_REPOSITORY_NO_COMMIT_NO_PUSH'}
(R/'FINAL.json').write_text(json.dumps(final,indent=2)+'\n');print(json.dumps(final,indent=2))
