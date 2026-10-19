# Stage 0 — งานที่เสร็จและ review gate ถัดไป

**WAITING_FOR_USER_APPROVAL — Stage 1 / benchmark ยังไม่อนุมัติ** งานเตรียมรอบนี้ไม่เปลี่ยนผล scientific benchmark และไม่ประกาศ Stage 0 complete

## สิ่งที่เสร็จจริง

Approved readable manifests 5 ชุด, sample GT 30 train images/ทุก native plane + human checklist, CIHP official availability/size audit, taxonomy source proposal, model-variant registry 17 metadata rows, compatibility wrapper และ **51 tests PASS** ส่วน original dataset, upstream evaluator และ YOLO artifacts คงเดิม ไม่มี PPSS activity

## Evaluator correction: ผลและขอบเขต

[Wrapper](../src/evaluation/official_mhp_compat.py) โหลดเฉพาะ function AST จาก pinned `eval_mhp.py` และ `voc_eval.py` ใน source ทางการ Port Python2 syntax/removed NumPy aliases ใน memory โดยไม่แก้ upstream หรือเปิด pickle caches

Nonempty inputs delegate reference matching/confidence ordering/strict `>` parsing-IoU/background treatment ตามเดิม Empty predictions เมื่อมี GT support ให้ AP^p=0 และ PCP=0 ตาม empty precision–recall integral และ missed-person definition; no GT support ให้ null/undefined ไม่แทนด้วยศูนย์

AP^p_vol คำนวณ arithmetic mean ของ 9 fresh reference calls ที่ literal thresholds 0.1…0.9; state reset ทุกครั้ง ตาม threshold convention ที่ตรวจใน M2FP source Original official v2 file มี single-threshold function ไม่ได้มี AP-volume function จึงแยกชื่อ **reference-derived nine-threshold summary** และยังไม่ claim reproduction of published results/CIHP official parity

Test cases ครอบ perfect, no predictions, zero GT, all-background GT, absent classes, missing person, duplicate, scores/ties, reordered identities, overlapping GT, ignore pixels, RGBA first-channel, strict threshold boundary, known volume 4/9, invalid dimensions/IDs/labels/NaN และ exact nonempty parity ที่เก้า thresholds [51-test evidence/log](../provenance/RUN_MANIFESTS/dataset-reassessment-20261008T095241Z/BOUNDED_TESTS_V2.json) แบ่ง 25 original tests + 19 official wrapper tests + 7 population tests ไม่มี validation inference

## Model preparation

| Method | Metadata variants ที่ตรวจ | Local readiness |
|---|---|---|
| M2FP | R101 MHP-v2 / CIHP / LIP; training schedules ไม่ใช่ model-size variants | Source/config/links pinned; no weights; Detectron2/MSDeform stack pending |
| CPI | R50 และ ConvNeXt-B × MHP-v2/CIHP | Backbone variants จริง; same-backbone dataset weights/epoch75 ไม่ใช่คนละขนาด; legacy MMCV/MMDet pending |
| FASHN | Verified official SegFormer-B4, 18 classes | Environment imports + synthetic T4 FP32 passed earlier; model/checkpoint inference 0 |
| D2FP | R101 CIHP / LIP official parser release | ไม่ใช่ R-103 backbone weights; inherited code/weight license review + extensions pending |
| SCHP | R101 LIP / ATR / Pascal-Person-Part | Dataset taxonomies ต่างกัน; no official CIHP weight verified; legacy ABN pending |
| Optional / excluded | QANet/CDGNet/RP-R-CNN source metadata; Sapiens2 excluded | ไม่ติดตั้งเพิ่ม; Sapiens2 surveillance-related execution license-blocked |

All weights downloaded/loaded/checkpoint inference = **NO** ไม่มี model-size หรือ FP32 T4 memory feasibility ที่พิสูจน์แล้ว missing nvcc ไม่ขวาง FASHN path โดยตรง แต่ M2FP/D2FP custom extension และ SCHP legacy path ต้อง controlled build/user-space isolated toolkit proposal ไม่แก้ system CUDA และไม่ถือ prebuilt dependency เป็นหลักฐาน model works

ทะเบียนใหม่ [MODEL_VARIANT_REGISTRY_V2.csv](../provenance/MODEL_VARIANT_REGISTRY_V2.csv) เก็บ sizes/commits/config hashes/mode/licenses/states แยก; ทะเบียนก่อนหน้าคงไว้เป็น historical evidence

## Approval 1 — CIHP acquisition และ read-only quality audit

แนะนำอนุมัติ dataset-only official archive **2,033,753,964 bytes** ด้วย download cap **2.1 GB** และ disk quota **15 GB** ก่อนใช้จริงตรวจ SHA256, safe tar inventory และ release terms; decompressed size ยังไม่รู้ พื้นที่ว่างประมาณ 620 GiB ไม่มี heavyweight dependencies เพิ่ม

หลัง acquisition ให้ตรวจไฟล์/semantics/leakage และ generate actual 200-image train review sample; ยังไม่ promote primary, ไม่ model inference และไม่ถือ user authorization เป็น third-party license grant ถ้า terms ไม่ชัด แยก integrity inspection จาก permission to evaluate/publish/deploy และรายงาน gate

ทางเลือก: รอผู้ใช้ส่ง archive/official terms หรือเลื่อน CIHP ไว้ ใช้ MHP readable samples ทำ protocol preparation ต่อ บทบาท primary ยัง pending ทุกทางเลือกไม่เปลี่ยน metric protocol โดยอัตโนมัติ

## Approval 2 — FASHN checkpoint smoke แยกจาก dataset audit

เสนอเป็นงานอิสระหลังยืนยัน **noncommercial research/evaluation scope**: official pinned safetensors **256,146,352 bytes ≈ 256 MB**; checkpoint-only cap **300 MB** ใช้ existing isolated FASHN environment ก่อน ไม่มี dependency installation ที่ได้รับอนุมัติใน cap นี้

รัน initial 1 และสูงสุด 3 verified-readable train images, FP32/T4, native decoding/coordinate/schema checks เก็บ hashes/VRAM/errors ไม่ ranking และไม่ final timing หาก compatibility ต้อง dependency เพิ่มให้หยุดเสนอ budget ใหม่ ไม่โหลดอื่นอัตโนมัติ M2FP/CPI-R50 native priority ตามมาหลังเลือก dataset cohort/weight terms ไม่ใช้ CIHP absence ขวาง FASHN feasibility โดยไม่จำเป็น

**License matters:** FASHN inherits SegFormer noncommercial research/evaluation terms; company development/deployment ต้องตรวจสิทธิ์แยก ห้ามรับรองว่า research label ครอบ company surveillance product R&D โดยอัตโนมัติ Sapiens2 ยังคง excluded ไม่ว่าจะเลือก research-only หรือ deployment direction

## GT review และ scientific decisions ที่ยังเปิด

Human reviewers ต้องตรวจ 30-image MHP checklist แล้วค่อยขยาย/ประมาณ prevalence; ไม่ต้องอนุมัติ readable policy ซ้ำ ไม่มี authorization ให้ relabel/exclude uncertain ownership cases Common taxonomy, target-person ownership, crop/matching/coverage definitions และ sensitivity reporting ยัง draft ต้อง freeze ก่อน Stage 1

Public-checkpoint training exposure ต้องรายงานพร้อมผลภายหลัง ทำ separate native/crop cohorts และ separate dataset scores ไม่มี hybrid/fusion implementation หรือ CCTV inference ในงานถัดไปที่เสนอ

## Safety และ Git

ไม่สร้าง remote/commit/push ในรอบนี้ Workspace และ study ไม่ใช่ Git repositories; existing YOLO repositories แยกกันและ user changes คงไว้ Current documents ที่แก้เก็บ archive/diff/hash ก่อน–หลัง ส่วน original measured/source records เก็บ immutable Review-validation record แยกจาก historical `STAGE0_VALIDATION.json` ที่รายงาน BLOCKED ในอดีต

**Next action: WAIT FOR USER APPROVAL.**
