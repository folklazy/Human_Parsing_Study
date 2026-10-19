"""Publish conditional decisions, local implementation evidence and remaining gates."""
from pathlib import Path
from datetime import datetime,timezone
import json,shutil,hashlib
S=Path(__file__).resolve().parents[1]
R=S/json.loads((S/'provenance/FIRST_COHORT_READINESS_ACTIVE.json').read_text())['run']
validation_path=S/json.loads((R/'LATEST_VALIDATION.json').read_text())['path'];validation=json.loads(validation_path.read_text());assert validation['status']=='PASS'
pops=json.loads((R/'POPULATION_BINDINGS_DRAFT.json').read_text())['populations'];train=json.loads((R/'TRAIN_DOMAIN_REVIEW.json').read_text());route=json.loads((R/'live_route/ROUTE_EVIDENCE.json').read_text());lineage=json.loads((R/'V4_TO_V5_LINEAGE.json').read_text())
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');archive=S/'reports/archive'/('conditional_policies_first_cohort_'+stamp);archive.mkdir(parents=True)
paths=['README.md','STUDY_STATE.json','DATA_SCHEMA.md','provenance/CURRENT_STUDY_ARTIFACTS.json','reports/STAGE0_NEXT_ACTIONS.md','reports/PROTOCOL_REVIEW.md','reports/APPLICATION_HANDOFF_POLICIES_TH_20261015.md']
archives=[]
for name in paths:
 p=S/name;q=archive/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);archives.append({'path':name,'before_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'archive':str(q.relative_to(S))})
view=json.loads((S/'taxonomy/APPLICATION_HANDOFF_VIEW_CARDS_DRAFT_V1.json').read_text());view['source']='Explicit user conditional policy acceptance, 15 October 2026';view['policy_acceptance_is_semantic_acceptance']=False
for card in view['views']:
 if card['id']=='V2_body_clothing_candidate':
  card['failure_policy']='STRICT_COMPLETE_ACCEPTED_WITH_INCOMPLETE_ROWS_AND_OPERATIONAL_DIAGNOSTICS'
  card['cohort_membership']='CHECKPOINT_SPECIFIC_VERIFIED_SUPPORT_AND_MAPPING_EVIDENCE; no dataset-name auto-eligibility'
  card['population']='See first-cohort POPULATION_BINDINGS_DRAFT.json; both populations retained, roles not accepted'
  card['first_cohort_configuration']='configs/application_v2_first_cohort_v5.yaml'
  card['matching']='GT evaluation reads evaluation config; prediction-only YOLO/native association has separate draft_association config'
  card['real_scoring_context']='NOT_ACCEPTED'
(S/'taxonomy/APPLICATION_HANDOFF_VIEW_CARDS_DRAFT_V2.json').write_text(json.dumps(view,ensure_ascii=False,indent=2)+'\n')

def link(name):return '../'+str((R/name).relative_to(S))
report=S/'reports/FIRST_COHORT_CONDITIONAL_POLICY_REVIEW_TH_20261015.md'
text=f'''# รับรองนโยบายแบบมีเงื่อนไข และตรวจความพร้อมกลุ่มแรก

**สองนโยบาย: ACCEPTED WITH CONDITIONS · implementation รอบนี้: LOCAL TESTS PASS · กลุ่มจริง: NOT FROZEN / SCORING BLOCKED**

การตอบรับของผู้ใช้เป็นการรับรองนโยบายหลังอ่านเอกสาร ไม่ใช่ independent source/log/test certification รายงานนี้แยกผลตรวจที่รันบน server รอบนี้ออกจากการตัดสินใจดังกล่าว ไม่เริ่ม audit ทั้งโครงการใหม่ และไม่เปิด full benchmark

## 1. Accepted decisions ที่บันทึกแล้ว

[Decision record V4](../provenance/APPLICATION_V2_DECISIONS_V4.json) ผูก [executable config V5](../configs/application_v2_first_cohort_v5.yaml) ด้วย content digest; V3/V4 configs เดิมยังคงอยู่

| นโยบาย | เงื่อนไขที่บังคับ |
|---|---|
| STRICT_COMPLETE เป็นคะแนนหลัก | ถ้าผลไม่ครบประชากร comparison run ไม่มีคะแนนหลัก; ไม่เฉลี่ยเฉพาะภาพสำเร็จแล้วใช้ชื่อคะแนนหลัก |
| ระบบไม่ครบยังอยู่ในตาราง | แสดง INCOMPLETE, งานสำเร็จ/ล้มเหลว/invalid/not attempted และ numerator/denominator ของ final-frame stage |
| Operational diagnostics แสดงร่วม | failure ledger, completion rate, stage ledgers และ success-only diagnostic ที่ระบุชื่อ/ตัวหารต่างหาก |
| Valid empty output | เป็น execution success; เมื่อบริบทคะแนนได้รับรองแล้วต้องรับ FP/FN/semantic misses ตาม GT ไม่แปลงเป็น failure |
| ไม่มี post-hoc rescue | model retries เป็น0; duplicate frame attempts ไม่ overwrite failure; ไม่ตัดภาพเฉพาะโมเดลหลังเห็นผล |
| Cohort ตาม capability จริง | ต้อง bind checkpoint/config/source/native class order/mapping/target catalog และ reviewed support evidence; ชื่อ CIHP/LIP ไม่ให้สิทธิ์อัตโนมัติ |
| ไม่ลบ Exposed_torso เฉพาะ LIP | LIP ที่ไม่รองรับยังไม่เข้ากลุ่มที่บังคับ target นี้ |
| ไม่จัดอันดับข้ามข้อสอบ | comparison revision ผูก population, mapping, view/track และ policy; shared view ใหม่ต้องออก revision ใหม่ |

คะแนน strict ไม่ตอบ deployment reliability ครบทั้งหมด Operational diagnostics จึงอยู่ในรายงานหลักด้วย การประเมิน operational quality เต็มรูปแบบยังเป็นโจทย์ที่ต้องนิยามแยก ไม่แอบเปลี่ยน strict main เป็น empty fallback

## 2. สิ่งที่แก้ในโค้ดจริง

- `comparison.summarize_comparison` และ `ConfiguredRunner.comparison_report`: ใช้ population/system roster ที่ประกาศก่อนงาน รักษาระบบที่ขาดผลและให้ main_metrics=null ทั้ง run พร้อม diagnostic แยกตัวหาร
- Run-level semantic quality ใช้ตัวหาร G_sem ทั้งประชากร ไม่เฉลี่ย frame means แบบน้ำหนักเท่ากัน และไม่ใช้เฉพาะภาพที่สำเร็จเป็นคะแนนหลัก
- Reporter ผ่าน runner ปฏิเสธ eligible metric payload ที่ไม่ผูก accepted scoring context ข้อมูลจริงยังไม่มี context ดังกล่าว จึงได้สถานะ BLOCKED_SCORING_POLICY แม้รันทุก engineering frame สำเร็จ
- `cohorts.validate_support_binding` ทำ checkpoint-specific gate ผ่าน shared scorer; semantic support ที่ยัง DRAFT ไม่ผ่าน ชื่อ dataset เหมือนกันแต่ checkpoint hash ต่างกันก็ไม่ผ่าน
- Scoring context ต้องตรง accepted mapping file ที่ executable config อ้าง ไม่ใช่ accepted object ที่แยกจากไฟล์จริง
- Runner ตรวจ config mutation หลังโหลด ป้องกันการเปลี่ยนนโยบายใน memory โดยไม่สร้าง validated runner ใหม่
- Fingerprints รวม strict reporting/cohort policy และ association dependencies แยกจาก GT scoring threshold การเปลี่ยน association ต้องสร้าง derived packet ใหม่ถ้าผล final-person เปลี่ยน; retained native outputs อาจเพียงพอโดยไม่ต้องรันโมเดลใหม่

นี่เป็นการเพิ่ม code/config/tests ภายใน implementation เดิม ไม่มี metric/dataset ใหม่ ไม่มี weighted score

## 3. กลุ่มแรกและหลักฐาน checkpoint

กลุ่มเตรียมตรวจ: **CPI_R50_CIHP / CPI_ConvNeXtB_CIHP, Track T3b** ใช้ full-image native CPI ซึ่งมี internal detector แล้ว association กับ frozen YOLO26x ทั้งระบบ ไม่เรียกว่า crop parser-only comparison และไม่จัดอันดับร่วม T1/T3a

เลือกคู่นี้จากความพร้อมของ lossless per-person output/canonical adapter ไม่ใช้ smoke accuracy เพื่อคัดผู้ชนะ

ตรวจแต่ละ checkpoint แยก: exact SHA256, official source commit, native config source hash, resolved config, strict load evidence, head20classes, native output inventories และ original-grid masks จาก actual TRAIN run ไม่อนุญาต CIHP checkpoint อื่นเข้ากลุ่มโดยชื่อเพียงอย่างเดียว

[Checkpoint support bindings]({link('CHECKPOINT_SUPPORT_BINDINGS_DRAFT.json')}) มี structural_binding=VERIFIED แต่ semantic_mapping_review=DRAFT_NOT_ACCEPTED ยังไม่ใช้ label VERIFIED แทนการรับรอง target semantics

## 4. Mapping / domain: ปิดส่วนไหนแล้ว และยังขาดอะไร

ตรวจ README ผู้สร้าง CCIHP และ source CIHP class inventory/annotation loader อีกครั้ง: CCIHP ID6 คือ Face Mask แต่ native CIHP prediction ID6 คือ Dress; GT6 จึง VOID ใน candidate นี้ ขณะที่ prediction6 map ไป selected coarse garments การเปลี่ยน CIHP upper/coat/dress เป็น coarse union เป็น projection ของ study ไม่ใช่การกู้ native CIHP GT

Target6กลุ่มเดิม: face, torso-skin, naked arms, naked legs, selected garments และ footwear ชื่อ Garments_coarse ไม่ครอบคลุม headwear/gloves/accessories ทุกชนิด รายการ native IDs ที่รวม/ไม่รวมอยู่ใน [mapping evidence CSV]({link('CLASS_MAPPING_EVIDENCE_DRAFT.csv')}) และ [mapping V2](../taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V2.json)

**ตรวจพิสูจน์แล้ว:** GT mapping และ target catalog ของ V1/V2 เหมือนกัน จึง reuse sidecars เดิมได้โดย hash และ GT-projection digest ไม่ต้อง decode validation GT ซ้ำ เปลี่ยนเฉพาะ prediction taxonomy ของ LIP ไม่สร้าง exclusions ใหม่

**ยังไม่รับรอง:** ทุกพิกเซล Category0/Human0 เป็น physical known-negative หรือไม่ และรายละเอียด annotation completeness ไม่ได้ถูกพิสูจน์จากชื่อ background หรือ grid integrity ทั้งยังมี human-without-category/unknown22 ตาม auditเดิม จึงยังไม่สร้าง accepted real-data scoring context

เตรียมสอง domain proposals บน TRAIN `0000930` โดยไม่ใช้ผล prediction เลือก policy:

| Draft domain | Valid pixels ใน TRAIN ภาพนี้ | ข้อจำกัด |
|---|---:|---|
| Released-background candidate | {train['domain_candidates']['released_background_negative']['valid_pixels']:,} | รวม Category0/Human0 เป็น negative โดยสมมติ annotation completeness; ยังไม่รับรองสมมติฐาน |
| Human-envelope-only candidate | {train['domain_candidates']['human_envelope_only']['valid_pixels']:,} | ไม่มี whole-background FP coverage จึงเป็นคนละข้อสอบ ไม่ใช้แทน domain แรกอย่างเงียบ ๆ |

ทั้งสอง void unresolved/unsupported GT ตาม shared policy เดียวกัน ไม่ให้ prediction สร้าง void ต่างกันรายโมเดล เก็บ masks แบบ lossless เพื่อ review [TRAIN domain evidence]({link('TRAIN_DOMAIN_REVIEW.json')}) · [domain proposal arrays]({link('TRAIN_DOMAIN_PROPOSALS.npz')})

## 5. Population และ denominators ที่ตรวจแล้ว

| ประชากรเดิม | Images | G_loc structural draft | G_sem candidate draft | ไม่มี candidate semantic support |
|---|---:|---:|---:|---:|
'''
for name,p in pops.items():text+=f"| {name} | {p['frames']:,} | {p['G_loc_structural_draft']:,} | {p['G_sem_candidate_draft']:,} | {p['G_loc_structural_draft']-p['G_sem_candidate_draft']:,} |\n"
text+=f'''
คน44IDsที่ไม่มี candidate semantic support ประกอบด้วย9IDsไม่มี native known support และ35IDsมีแต่ known labels นอก candidate ไม่ลบออกจาก G_loc และไม่ให้ semantic undefined กลบ localization FN ถ้าอยู่ G_sem แล้ว unmatched ให้คุณภาพ0ในตัวหารเดิม

ตรวจ per-image manifest membership/unique IDs, sums และ sidecar SHA256 แล้ว [population bindings]({link('POPULATION_BINDINGS_DRAFT.json')}) อ้าง exact source files โดยไม่ flatten คนหรือเปลี่ยน source splits

ตัวเลขนี้หมายถึง native Human IDs ไม่ใช่การรับรอง physical person counts ทุกคน การกำหนดประชากรหลัก/reference กับ domain ที่ใช้ยังไม่ accepted รักษาทั้งสอง populationแยกกัน

## 6. Matching กับ prediction-only association แยกกัน

| ขั้น | Draft config / แหล่ง geometry | สถานะ |
|---|---|---|
| T3b association | `first_cohort.draft_association`: YOLO box ↔ native CPI box, IoU0.50, no GT | ผ่าน bounded TRAIN route; ไม่ accepted สำหรับ benchmark |
| Final prediction ↔ GT | `evaluation`: bbox half-open, primary0.50 / secondary0.75; maximize eligible cardinality then summed IoU | กลไกผ่าน fixtures; threshold ยังไม่ accepted |
| Evaluation bbox | native CPI box; GT boxจาก original Human-ID foreground | source/provenanceระบุชัด; policyยังรอรับรอง |
| Conditioning bbox | frozen YOLO26x box | เก็บแยกจาก evaluation bbox |

Immutable IDs + pinned SciPy1.15.3 และ permutation fixtures เป็นหลักฐาน matching logic ไม่ใช่การรับรองว่า threshold0.50เหมาะกับทุกข้อมูล V5แยก threshold dependencies จากกัน; การใช้ค่าเดียวกันใน engineering V4ไม่ใช่การรับรองว่าจะต้องผูกสองขั้นนี้เสมอ

## 7. Actual route รอบนี้

ใช้ **TRAIN `0000930` เพียงภาพเดียว**, 500×346 pixels, ไม่ใช่ validation:

- Frozen YOLO26x รันจริง FP32 ใน environmentเดิม โดยไม่แก้ weights/environment
- CPIทั้งสอง checkpoint รันจริง FP32 ใน isolated legacy environment พร้อม strict pretrained state load
- Association ใช้ predicted boxesเท่านั้น และ export canonical person masks ที่ original resolution พร้อม native+YOLO identities

| Candidate | YOLO opportunities | Native instances | Final persons | Actual components |
|---|---:|---:|---:|---|
'''
for e in route:text+=f"| {e['model']} | {e['YOLO_opportunities']} | {e['native_instances']} | {e['final_instances']} | actual YOLO + actual CPI + association |\n"
text+=f'''
จำนวนเท่ากันไม่พิสูจน์ว่าคุณภาพ mask หรือ GT coverage เท่ากัน ไม่คำนวณ quality score ของภาพนี้ Actual component runใช้ configV4; configV5แยก association/GT matching จากนั้น replay association จาก retained native data ได้ผลตรงกันและสร้าง2canonical V5packetsใหม่พร้อม explicit checkpoint/config/source dependencies ไม่มี GPU inference ซ้ำเพื่อทำ derived evidence

[Actual route outputs]({link('live_route/ROUTE_EVIDENCE.json')}) · [process commands/logs]({link('live_route/PROCESS_LOG.json')}) · [V4→V5 lineage]({link('V4_TO_V5_LINEAGE.json')}) · [V5 reporting output]({link('COMPARISON_ENGINEERING_STATUS_V5.json')})

Reporterแสดงทั้งสองระบบเป็น **BLOCKED_SCORING_POLICY**, execution1/1 และ main_metrics=null ไม่ปั้นคะแนนหลักจาก accepted synthetic context หรือจากการเห็น outputสำเร็จ

## 8. Runtime profile และขอบเขตคำอ้าง

เป็น sequential detector/parser processes, batch1, FP32, TF32off, warmups0, one engineering frame ไม่ใช่ steady-state timing; detectorและparserไม่ได้ residentบนGPUพร้อมกัน ไม่บวก peaksคนละprocessเพื่ออ้าง joint memory

Native profileมี framework/CUDA/driver/seed/environment lock และ observed dtype/cases ส่วน complete pipelineสำหรับเปรียบเทียบ latency/VRAM ยังต้องกำหนด N-person workload/residency/warmups/clean rounds/boundariesให้ตรงงานจริง ไม่ใช้ cold process wall timeหรือภาพเดียวตัดสินความเร็ว

[Native worker profile]({link('live_route/logs/run_cpi_PROFILE.json')}) · [YOLO engineering profile]({link('live_route/YOLO.json')}) การรันผ่านแสดง executable route ภายใต้ profileนี้ ไม่พิสูจน์ว่าทุกภาพหรือ joint-resident workloadพอดี T4

## 9. Tests, source diff และ preservation

ผลจริงล่าสุด **{validation['tests']} tests PASS**; ไม่ใช้จำนวนเป็นใบรับรองทุกเส้นทาง ตรวจ strict run-completeness, valid empty/FN, retained INCOMPLETE rows, person-weighted denominator, no posthoc retry, checkpoint-specific support, actual configured runner gates, accepted mapping-file binding, config mutation และ comparison revisions

[Commands/logs/source snapshot]({str(validation_path.relative_to(S)).replace('provenance/','../provenance/',1)}) · [source diff](../{(validation_path.parent/'CHANGES.diff').relative_to(S)})

Protected hashes126รายการและ frozen YOLO checkpoint ตรงเดิม; original archives stat checksตรงเดิม ไม่มี VAL inference, final benchmark, training, hybrid fusion, color study, CCTV หรือ PPSS activity ไม่มี package install/download ใหม่ในรอบนี้

Remote CPU patch ZIPไม่เป็น gateต่อไปตามที่ผู้ใช้ยืนยัน รักษา provenanceว่าไม่ได้ applyremoteZIP แต่ตรวจ source behaviorปัจจุบันแทน ไม่อ้าง independent reviewer certificationจาก local testsเหล่านี้

## 10. Readiness และขั้นต่อไป

| เรื่อง | ผลตอนนี้ | ก่อน freeze ยังต้องปิด |
|---|---|---|
| Strict primary / incomplete reporting | ACCEPTED + IMPLEMENTED + TESTED | ใช้ผ่าน actual accepted data context ของกลุ่ม |
| Checkpoint-specific cohorts | ACCEPTED + GATE TESTED | Semantic support/mapping evidence ของสมาชิกจริงต้อง reviewed |
| Mapping | Source definitions/projection lineage documented | รับรอง target semantics/coarse unions; ไม่ใช่ native CIHP equivalence |
| GT domain | Two explicit TRAIN proposals; unknown22/human0 policyไม่ซ่อน | หลักฐานหรือข้อจำกัด annotation completeness/known negativesที่ยอมรับอย่างชัดเจน |
| Population | Exact manifests/G_loc/G_sem/support/reasons ตรวจแล้ว | เลือก main/reference roles และ eligibilityของกลุ่มจริง |
| Matching | Independent association/evaluation config + tested logic | รับรอง threshold/geometry source |
| Actual route | PASS bounded TRAIN, two candidates | ไม่ขยายเป็นความพร้อมทุกframe/ทุกsystem |
| Runtime | Actual engineering profile retained | Frozen workload/profileสำหรับคำอ้าง latency/VRAM |
| Full benchmark | NOT AUTHORIZED / NOT STARTED | ขออนุมัติแยกหลัง review gatesครบ |

ไม่ต้องรับรองสองนโยบายเดิมซ้ำ และไม่ต้องรอ universal shared view งานถัดไปควร reviewสิ่งที่เป็นข้อสอบจริงของกลุ่มนี้จาก manifests/evidenceข้างต้น ไม่ย้อน auditทั้งโครงการ ไม่ freezeเพราะมี tests/smokeผ่านเพียงอย่างเดียว
'''
report.write_text(text)

# Add an explicit conditional-decision notice to the older policy record.
p=S/'reports/APPLICATION_HANDOFF_POLICIES_TH_20261015.md';title,body=p.read_text().split('\n',1)
p.write_text(title+'\n\n> อัปเดตหลังผู้ใช้รับรอง: STRICT_COMPLETE เป็นคะแนนหลักพร้อมเงื่อนไข INCOMPLETE/operational diagnostics และ cohort ตาม checkpoint-specific support ได้รับการยอมรับแล้ว ดู [decision V4](../provenance/APPLICATION_V2_DECISIONS_V4.json) และ [first-cohort review](FIRST_COHORT_CONDITIONAL_POLICY_REVIEW_TH_20261015.md) ข้อความ pending ทางเลือกสองนโยบายในเนื้อหาเดิมด้านล่างเป็นประวัติก่อนการรับรอง; mapping/domain/population/matching/runtimeยังไม่ freeze\n'+body)

p=S/'README.md';t=p.read_text();t=t.replace('**ล่าสุด 15 ตุลาคม 2026: engineering handoff พร้อมตรวจรับ โดย scientific freeze / full benchmark ยัง BLOCKED**', '**ล่าสุด 15 ตุลาคม 2026: รับรอง STRICT_COMPLETE และ checkpoint-specific cohorts แบบมีเงื่อนไขแล้ว; กลุ่มแรกยังไม่ freeze และ full benchmark ยัง BLOCKED**')
t=t.replace('- [Executable config V3 — DRAFT](configs/application_v2_handoff_v3.yaml)', '- [First-cohort review และ source/test evidence](reports/FIRST_COHORT_CONDITIONAL_POLICY_REVIEW_TH_20261015.md)\n- [Executable config V5 — DRAFT](configs/application_v2_first_cohort_v5.yaml)\n- [Accepted conditional decisions V4](provenance/APPLICATION_V2_DECISIONS_V4.json)')
t=t.replace('CPU regression 138 tests ผ่าน; protected hashes 126 รายการตรงเดิม Actual FP32 TRAIN smoke ผ่าน 21 checkpoints/components บนภาพเดียว; CPI canonical exports 8 packets ผ่าน ยังไม่ใช่ทุกระบบ YOLO-conditioned และไม่ใช้ smoke เลือกผู้ชนะ', f'CPU regression ล่าสุด {validation["tests"]} tests ผ่าน; protected hashes126รายการตรงเดิม กลุ่มแรกมี actual YOLO26x + CPIสองvariants + association บน TRAIN1ภาพ และ2derived canonical V5packets ที่ตรวจ dependenciesแล้ว ไม่มีคะแนนคุณภาพจริงระหว่าง mapping/domainยังไม่ accepted หลักฐาน 21checkpoint/component smokes และ CPI8packetsรอบก่อนเก็บเป็นประวัติ ไม่ใช่21ระบบพร้อม benchmark')
p.write_text(t)
p=S/'DATA_SCHEMA.md';t=p.read_text().replace('[application_v2_handoff_v3.yaml](configs/application_v2_handoff_v3.yaml)', '[application_v2_first_cohort_v5.yaml](configs/application_v2_first_cohort_v5.yaml)',1).replace('[decisions V3](provenance/APPLICATION_V2_DECISIONS_V3.json)','[decisions V4](provenance/APPLICATION_V2_DECISIONS_V4.json)',1)
t=t.replace('STRICT_COMPLETE versus OPERATIONAL_EMPTY_FALLBACK is implemented/tested as an explicit choice and remains pending acceptance.', 'STRICT_COMPLETE is accepted as the primary run-level policy with retained INCOMPLETE rows and operational diagnostics. Operational-empty fallback is not the primary score. Actual mapping/domain/population/matching acceptance remains pending.')
t=t.replace('## Active executable schema / accepted decisions','''## Conditional policy update — 15 October 2026

`comparison.summarize_comparison` reports every predeclared system and final-frame denominator. Incomplete populations have `main_metrics=null` and status `INCOMPLETE`; successful frames are separately labeled diagnostics. Complete execution without an accepted scoring context is `BLOCKED_SCORING_POLICY`. Valid empty output remains successful execution with GT-dependent misses.

`ConfiguredRunner.comparison_report` requires eligible metrics to carry the accepted context digest. Comparison IDs bind population, view/track/mapping and reporting policy. The configured runner rejects post-load config mutation. Checkpoint-specific `support_binding` requires checkpoint/config/source/class-order/target/mapping fingerprints and reviewed semantic evidence; a dataset name is insufficient.

Prediction-only association is in `first_cohort.draft_association`; final GT matching is in `evaluation`. Their fingerprints are distinct. The latest V5 packets are derived from retained actual V4 detector/parser outputs, not new GPU inference or production cached scoring. Original packets and configs remain immutable.

## Active executable schema / accepted decisions''',1)
p.write_text(t)
p=S/'reports/STAGE0_NEXT_ACTIONS.md';t=p.read_text().replace('**Engineering evidence ready for review; scientific freeze and full benchmark remain blocked.**','**Conditional policies accepted; first-cohort evidence updated, scientific freeze and full benchmark remain blocked.**\n\n[Current first-cohort review](FIRST_COHORT_CONDITIONAL_POLICY_REVIEW_TH_20261015.md) records actual route, population/mapping evidence and local test logs.')
t=t.replace('| Failure scoring | Choose strict-complete versus explicit operational fallback before benchmark; both mechanisms tested |','| Failure scoring | STRICT_COMPLETE accepted with retained INCOMPLETE rows, diagnostics and valid-empty treatment; run-level reporter implemented/tested |')
t=t.replace('| Common body/clothing view | Mapping V2 remains DRAFT; keep CIHP/LIP support differences explicit; do not fabricate exposed-torso support for LIP |','| Common body/clothing view | Mapping V2 remains DRAFT; accepted membership rule is checkpoint-specific support/mapping evidence, not CIHP/LIP names |')
t=t.replace('| First comparison route | Verify only the actual route/profile needed for the first accepted cohort; native smoke alone is insufficient |','| First comparison route | Actual YOLO26x + CPI-R50/ConvNeXtB-CIHP association passed on one TRAIN frame; real scoring context and resource benchmark profile still pending |')
t=t.replace(f'- 138 CPU tests passed;', f'- {validation["tests"]} CPU tests passed;')
p.write_text(t)
p=S/'reports/PROTOCOL_REVIEW.md';t=p.read_text();t=t.replace('**Stage 1 freeze:', '**Stage 1 freeze:',1)
t=t.replace('Current model status:', 'STRICT_COMPLETE primary reporting and checkpoint-specific cohort membership are accepted with conditions; this does not accept real-data mapping/domain/population/matching/runtime. See [current first-cohort evidence](FIRST_COHORT_CONDITIONAL_POLICY_REVIEW_TH_20261015.md). Current model status:',1)
p.write_text(t)

p=S/'provenance/CURRENT_STUDY_ARTIFACTS.json';index=json.loads(p.read_text());index.update(updated_utc=datetime.now(timezone.utc).isoformat(),executable_config='configs/application_v2_first_cohort_v5.yaml',decision_record='provenance/APPLICATION_V2_DECISIONS_V4.json',CPU_validation=str(validation_path.relative_to(S)),first_cohort_report=str(report.relative_to(S)),first_cohort_evidence=str(R.relative_to(S)),view_cards='taxonomy/APPLICATION_HANDOFF_VIEW_CARDS_DRAFT_V2.json',policy_acceptance='STRICT_COMPLETE_AND_CHECKPOINT_SPECIFIC_COHORTS_WITH_CONDITIONS',scientific_freeze='BLOCKED_REAL_DATA_CONTEXT_NOT_ACCEPTED');p.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
p=S/'STUDY_STATE.json';state=json.loads(p.read_text());state['last_updated_utc']=index['updated_utc'];state['conditional_policies_first_cohort_20261015']={'policies_accepted':['PRIMARY_SCORE_COMPLETENESS','CHECKPOINT_SPECIFIC_COHORTS'],'user_review_scope':'DOCUMENT_REVIEW_ONLY_NOT_INDEPENDENT_IMPLEMENTATION_CERTIFICATION','decision_record':'provenance/APPLICATION_V2_DECISIONS_V4.json','config':'configs/application_v2_first_cohort_v5.yaml','tests':validation['tests'],'actual_route':'ACTUAL_YOLO26X_PLUS_TWO_CPI_VARIANTS_ASSOCIATION_TRAIN_ONE_FRAME','population_metadata':'VERIFIED_ROLES_DRAFT','mapping':'DRAFT','GT_domain':'DRAFT_COMPLETENESS_UNRESOLVED','matching':'DRAFT_THRESHOLDS_UNACCEPTED','resource_profile':'ENGINEERING_ONLY_NOT_BENCHMARK','real_scoring_context':False,'full_benchmark':False,'freeze':False,'evidence':str(R.relative_to(S)),'report':str(report.relative_to(S))};state['current_artifacts']['CPU_tests_last_executed']=validation['tests'];state['current_artifacts']['first_cohort_report']=str(report.relative_to(S));p.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
for row in archives:row['after_sha256']=hashlib.sha256((S/row['path']).read_bytes()).hexdigest()
(R/'EDITORIAL_UPDATES.json').write_text(json.dumps(archives,indent=2)+'\n')
readiness={'status':'POLICIES_ACCEPTED_IMPLEMENTATION_TESTED_FIRST_COHORT_NOT_FROZEN','policies_accepted':True,'local_tests':validation['tests'],'independent_reviewer_source_certification':False,'actual_route_candidates':2,'actual_route_TRAIN_frames':1,'mapping_review':'DRAFT','domain_review':'UNRESOLVED_COMPLETENESS_ASSUMPTION','population_metadata':'VERIFIED','population_roles':'DRAFT','GT_matching_thresholds':'DRAFT','runtime':'BOUNDED_ENGINEERING_NO_COST_RANKING','benchmark_authorized':False,'benchmark_started':False,'report':str(report.relative_to(S)),'validation':str(validation_path.relative_to(S))}
(R/'READINESS.json').write_text(json.dumps(readiness,indent=2)+'\n');print(json.dumps(readiness,indent=2))
