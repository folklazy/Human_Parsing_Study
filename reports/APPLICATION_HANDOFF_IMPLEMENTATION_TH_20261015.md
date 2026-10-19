# ผลดำเนินการ Implementation Handoff — 15 ตุลาคม 2026

> อัปเดตภายหลัง: CDGNet ดาวน์โหลดจาก Google Drive ทางการและตรวจ tensor แล้ว ดู [ผลล่าสุด](CDGNET_ACQUISITION_TH_20261015.md), [registry V6](../provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv) และ [current artifact index](../provenance/CURRENT_STUDY_ARTIFACTS.json) จำนวนและสถานะ DOWNLOAD_NOT_OBTAINED ในเนื้อหารอบ handoff ด้านล่างเป็นหลักฐานก่อนการแก้ acquisition นี้

**สถานะงานที่ดำเนินได้: PASS WITH WARNINGS — พร้อมตรวจรับงานวิศวกรรม; scientific freeze / full benchmark ยัง BLOCKED**

ทำต่อจาก server implementation เดิมตาม handoff1.1 ไม่เริ่ม study ใหม่ ไม่มี VAL inference, training, CCTV, fusion หรือ full benchmark ผล CPU ล่าสุด **138 tests ผ่าน** และ protected hashes **126 รายการตรงเดิม** จำนวน tests เป็นรายละเอียดหลักฐาน ไม่ใช่เกณฑ์รับรองทุก production route

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
| CPU tests รอบนี้ | VERIFIED | 138 tests จาก 6 suite patterns; log/commands/source hash อยู่ใน validation |
| A01–A20 | VERIFIED_WITH_DISABLED_CAPABILITIES | แยกขอบเขตแต่ละแถวด้านล่าง |
| Checkpoint inference ใหม่ | VERIFIED | TRAIN `0000930` 1 ภาพต่อ checkpoint/component ที่ผ่าน 21 รายการ |
| CPI canonical contract | VERIFIED | 8 immutable packets: 4 variants × T1/T3B |
| T3B conditioning รอบนี้ | VERIFIED_SAVED_YOLO | fresh native CPI + saved verified YOLO ภาพเดียวกัน; ไม่ใช่ jointly timed live system |
| Native FP32 profile | VERIFIED_LIMITED | parameters checked by worker, floating module outputs FP32, autocast/TF32/seeds/env recorded; internal ops ไม่ได้ตรวจทุก kernel |
| Remote CPU patch 103 tests | REPORTED_NOT_REVERIFIED | ไม่มี ZIP ให้ตรวจ parity |
| Accepted common taxonomy/domain/population | PROPOSED / BLOCKED | ยังไม่มีการรับรอง semantic mapping และ annotation completeness |
| Cached scorer / workflow resume | NOT_IMPLEMENTED_DISABLED | packet-integrity helper ไม่แทน production scheduling/rescore |
| Benchmark/model winner | NOT_TESTED | ไม่จัดอันดับจาก smoke |

[Validation และ commands](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/LATEST_VALIDATION.json) · [source/patch ก่อนแก้](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/BEFORE.json) · [input evidence status](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/INPUT_EVIDENCE_STATUS.json) · [data-use ledger](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/DATA_USE_LEDGER.json)

## 3. Acceptance A01–A20

PASS ในตารางหมายถึง behavior ตาม scope ที่เขียน ไม่ขยายเป็นทุก runtime/route หรือ final benchmark

| ID | ผล | หลักฐาน / ขอบเขต |
|---|---|---|
| A01 | PASS | ConfiguredRunner.score_frame: checkpoint/config/head/class order mismatch rejected using accepted synthetic context |
| A02 | PASS | score_frame rejects LIP unsupported Exposed_torso in common-capability fixture |
| A03 | NOT_IMPLEMENTED | Live ConfiguredRunner rejects DRAFT/UNKNOWN/hash changes; cached scoring is absent and disabled |
| A04 | PASS | Trusted original W/H checked on scored arrays, including no GT |
| A05 | PASS | Unmatched/no-GT invalid IDs/dtype/score/duplicate identities rejected |
| A06 | PASS | G_loc=1 G_sem=0 no prediction => FN1 recall0 semantic null |
| A07 | PASS | 10 GT semantic persons with 8 perfect outputs => Q=.8, G_sem=10 |
| A08 | PASS | Actual person runner failure ledger through final matching; other valid output => no duplicate FN |
| A09 | PASS | Actual PERSON failure retains other valid final outputs under explicit fixture policy |
| A10 | PASS | Strict/operational eligibility and invalid/incomplete states tested; finalizer contract failure distinguished |
| A11 | PASS | Empty GT/output and GT-supported/prediction-only/undefined cases tested across actual numerical API |
| A12 | PASS | 100 correct A + 900 B leakage => semantic IoU1 / foreground IoU.1 |
| A13 | PASS | Known-negative FP versus void, owner-unknown global/person handling tested |
| A14 | PASS | Permuted GT/prediction rows with immutable IDs produce identical matched IDs and metrics |
| A15 | PASS | Actual scoring uses declared evaluation bbox provenance, independently of conditioning bbox |
| A16 | NOT_IMPLEMENTED | Existing packet resume hash/finalization/fingerprint rejection tests pass; workflow resume/cached scorer absent |
| A17 | NOT_IMPLEMENTED | Retention capability API rejects probabilities from hard labels; production re-scoring API remains disabled |
| A18 | NOT_IMPLEMENTED | Inference/scoring fingerprint separation tested, including scoring context; actual cached re-score route absent |
| A19 | NOT_IMPLEMENTED | Declared artifact-set checks reject missing/partial shards and distinguish duplicate content; acquired set hash-verified. Immutable-version resume policy not implemented for mutable Drive shares; not certified. |
| A20 | PASS | 21 actual checkpoint/component FP32 TRAIN smokes; CPI canonical T1/T3B exports pass. Limited to these routes; all-variant YOLO integration and joint runtime NOT_TESTED |

ดู [machine-readable acceptance matrix](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/ACCEPTANCE_A01_A20.json) และ tests ผ่าน entry point จริงใน `test_application_v2_handoff.py` พร้อม `test_application_v2.py`/`test_application_v2_acquisition.py`

## 4. ดาวน์โหลด official roster

ตรวจ author repositories/folders ของ 9 families ณรอบนี้ เก็บ exact local source commits และ official README responses ไม่อ้างว่าค้นพบทุกโมเดลที่มีในโลก

- Checkpoint content ที่มีอยู่ทั้งหมด **26 unique artifacts** / **26 physical inode files**, มี 30 paths รวม aliases เดิม
- ใน unique artifacts มี 25 parser weights/components และ 1 auxiliary detector; SCHP global/local เป็น components ไม่ใช่สองระบบ multi-person ที่รันครบแล้ว
- เพิ่มใหม่ **5 artifacts**: parser weights/components 4 + auxiliary detector 1
- New checkpoint bytes **2,562,348,114 bytes = 2.562 GB**; configs เพิ่มแยกใน acquisition results
- Unique checkpoint content รวม **43.604 GB**; directory ใช้ disk allocation **64.065 GB** รวม old partial/cache fragments ซึ่งยังไม่ลบ
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

[Official discovery](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/OFFICIAL_ROSTER_DISCOVERY.json) · [checkpoint SHA256 manifest](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/CHECKPOINT_MANIFEST.json) · [new asset-set verification](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/ADDITIONAL_ASSET_SET_VALIDATION.json) · [registry V4](../provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V4.csv)

ยังไม่รับรอง resumable download ของ mutable Drive shares ข้าม source versions; gdown ใช้ partial files แต่การมี `.part` ไม่ใช่ VERIFIED และไม่มีการอ้างว่าได้ทดสอบ immutable-version resume ครบใน A19

## 5. Actual FP32 TRAIN feasibility

GPU Tesla T4 / driver580.178.04; no warmups, one TRAIN image per checkpoint, parser sequential, native preprocessing/TTA ตาม worker ไม่ใช้ smoke time จัดอันดับ เนื่องจาก boundaries ต่างกันและมี asset/hash/download activity บางช่วง

| Checkpoint / component | Native mode | Native inference | Allocated MiB | Reserved MiB | Canonical export รอบนี้ |
|---|---|---|---:|---:|---|
| CPI_ConvNeXtB_CIHP | NATIVE_FULL_FRAME_INTERNAL_DETECTOR | BOUNDED_NATIVE_PASS | 796.9 | 1178.0 | PASS_T1_AND_T3B_SAVED_YOLO |
| CPI_ConvNeXtB_MHPV2 | NATIVE_FULL_FRAME_INTERNAL_DETECTOR | BOUNDED_NATIVE_PASS | 1405.0 | 1888.0 | PASS_T1_AND_T3B_SAVED_YOLO |
| CPI_R50_CIHP | NATIVE_FULL_FRAME_INTERNAL_DETECTOR | BOUNDED_NATIVE_PASS | 584.2 | 1110.0 | PASS_T1_AND_T3B_SAVED_YOLO |
| CPI_R50_MHPV2 | NATIVE_FULL_FRAME_INTERNAL_DETECTOR | BOUNDED_NATIVE_PASS | 1200.9 | 1924.0 | PASS_T1_AND_T3B_SAVED_YOLO |
| D2FP_R101_CIHP | NATIVE_FULL_FRAME | BOUNDED_NATIVE_PASS | 1323.0 | 1938.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| D2FP_R101_LIP | ORACLE_CROP_LARGEST_PERSON | BOUNDED_NATIVE_PASS | 989.1 | 2286.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| FASHN_B4 | FULL_IMAGE_SEMANTIC_NO_PERSON_IDENTITIES | BOUNDED_NATIVE_PASS | 643.5 | 714.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| M2FP_R101_CIHP | NATIVE_FULL_FRAME | BOUNDED_NATIVE_PASS | 965.4 | 1286.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| M2FP_R101_LIP | ORACLE_CROP_LARGEST_PERSON | BOUNDED_NATIVE_PASS | 709.5 | 1812.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| M2FP_R101_MHPV2 | NATIVE_FULL_FRAME | BOUNDED_NATIVE_PASS | 1054.7 | 1316.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| QANet_CIHP | ORACLE_PERSON_NATIVE_ROI_ALIGN | BOUNDED_NATIVE_PASS | 250.8 | 342.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| QANet_CIHP_HRNetW48_512x384 | ORACLE_PERSON_NATIVE_ROI_ALIGN | BOUNDED_NATIVE_PASS | 390.7 | 498.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| QANet_LIP | ORACLE_PERSON_NATIVE_ROI_ALIGN | BOUNDED_NATIVE_PASS | 388.6 | 512.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| QANet_LIP_HRNetW48_544x416 | ORACLE_PERSON_NATIVE_ROI_ALIGN | BOUNDED_NATIVE_PASS | 979.3 | 1172.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| RPR_CIHP | NATIVE_FULL_FRAME_INTERNAL_DETECTOR | BOUNDED_NATIVE_PASS | 642.1 | 698.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| RPR_MHPV2 | NATIVE_FULL_FRAME_INTERNAL_DETECTOR | BOUNDED_NATIVE_PASS | 720.0 | 774.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| SCHP_CIHP_GLOBAL_COMPONENT | GLOBAL_SEMANTIC_COMPONENT | BOUNDED_NATIVE_PASS | 519.6 | 572.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| SCHP_CIHP_LOCAL_COMPONENT | LOCAL_COMPONENT_ORACLE_CROP | BOUNDED_NATIVE_PASS | 519.6 | 572.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| SCHP_R101_ATR | ORACLE_CROP_LARGEST_PERSON | BOUNDED_NATIVE_PASS | 530.2 | 586.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| SCHP_R101_LIP | ORACLE_CROP_LARGEST_PERSON | BOUNDED_NATIVE_PASS | 519.6 | 572.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |
| SCHP_R101_PASCAL_PERSON_PART | ORACLE_CROP_LARGEST_PERSON | BOUNDED_NATIVE_PASS | 530.2 | 586.0 | NOT_TESTED_IN_THIS_NATIVE_RUN |

ทั้ง 21 checkpoint/component ผ่าน input นี้บน T4 FP32 ไม่ได้แปลว่าทุกภาพหรือทุก joint pipeline จะพอดี VRAM โดยเฉพาะ CPI-R50 CIHP เคยมี OOM ใน pilot10ภาพเดิม; ครั้งนี้ผ่าน1ภาพไม่ลบข้อจำกัดนั้น SCHP global/local ผ่านเฉพาะ component, ไม่ได้รัน native detector/global-local composition/fusion

Attempt แรกของ launcher ล้มก่อน model loading เพราะ environment ไม่มี pip; แก้ metadata capture ให้ใช้ `importlib.metadata` โดยไม่ติดตั้ง pip ต่อมา SCHP ขาด ninja ใน PATH; คืน path ของ tools เดิมและ copy compiled cache ไป run directory จึงผ่าน ไม่แก้ YOLO environment, system CUDA หรือ driver เก็บ failed-attempt logs ไว้

Native identities มีเฉพาะ interface ที่รองรับ Semantic parser + crop ยังไม่มี native identity การใส่ oracle/YOLO ID ภายหลังไม่เปลี่ยนความสามารถนั้น

[Smoke summary / output hashes](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/SMOKE_SUMMARY.json) · [native logs/profiles](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/native_smoke/logs) · [canonical CPI evidence](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/CANONICAL_SMOKE.json) · [artifact capabilities](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/ARTIFACT_CAPABILITIES.json)

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

Protected measured/source artifacts 126 รายการ hash ตรงเดิม; original archive stat checks ตรงเดิม ไม่แก้ raw MHP-v2/CIHP/CCIHP/PPSS, frozen YOLO checkpoint หรือผล YOLO ไม่มี training/fusion/color/CCTV/VAL inference ไม่ติดตั้ง package เพิ่ม

Workspace root และ study นี้ไม่มี `.git` จึงไม่มี commit/branch/diff ของ Git และไม่ได้สร้าง remote/push เก็บ before snapshots, unified source diff และ content-addressed source revision แทน; ไม่อ้างว่า Git validation PASS

Source revision: `18173aa15adb899876499f30d3068f256be186fd8b546215f7705db9dbf43f95`
