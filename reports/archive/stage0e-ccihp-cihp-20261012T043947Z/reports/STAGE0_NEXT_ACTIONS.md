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

ทะเบียนใหม่ [MODEL_VARIANT_REGISTRY_V3.csv](../provenance/MODEL_VARIANT_REGISTRY_V3.csv) (V2 historical unchanged) เก็บ sizes/commits/config hashes/mode/licenses/states แยก; ทะเบียนก่อนหน้าคงไว้เป็น historical evidence

## Updated next gate — Native CIHP GT ก่อน Full Quality Audit

Local DatasetNinja TAR มีแล้วและ preflight เสร็จ จึงไม่ต้องอนุมัติ download DatasetNinja ซ้ำ [Focused report](CIHP_ARCHIVE_PREFLIGHT_AUDIT.md) ยืนยันครบ 38,280 images/33,280 labeled images/768,446 part objects, แต่ Human_ids และ person ownership ไม่ preserved ภาพซ้ำ train–val แบบ JPEG bytes 39 groups ต้องตรวจ decoded/near duplicates ต่อ

**แนะนำ:** ขอ native official CIHP copy/GT supplement พร้อม Human_ids, Category_ids, Instance_ids/full splits จาก local assets หรือผู้ใช้ หากจำเป็นต้อง download official native release ให้ขออนุมัติแยก: metadata ประมาณ 2,033,753,964 bytes (cap 2.1 GB; ไม่มี checkpoint/packages) ไม่ใช่ renewed permission จาก budget เดิม

หลัง native GT พร้อมและได้รับอนุมัติ Full Quality Audit: strict-decode ทุก RGB, paired native-map validation, full conversion fidelity, ignore/overlap semantics, decoded/near-duplicate leakage, class/person counts และ deterministic 200-image stratified TRAIN review ตาม [V2 plan](../manifests/CIHP_QUALITY_REVIEW_PLAN_V2.json) ห้าม auto exclude/relabel source GT หรือตั้ง CIHP primary จาก integrity เพียงอย่างเดียว

ทางเลือก: semantic-only Full Quality Audit ของ conversion เป็น separate cohort หลังอนุมัติ แต่จะยังไม่มี oracle-person geometry, person-macro, matched coverage หรือ native APp/PCP GT ห้ามเดา Human_ids จาก YOLO/connected components/part grouping แล้วถือเป็น native truth

Provider/license file declares MIT แต่ original dataset rights ยังไม่ verified จึงต้องอ่าน native release terms/clarify scopeก่อน evaluation/publication/deployment ไม่มี full extraction/download/checkpoint execution ใน preflight นี้

## Approval 2 — FASHN checkpoint smoke แยกจาก dataset audit

ผู้ใช้ยืนยัน **Decision 5A: noncommercial academic research/evaluation** แล้ว; scope ambiguity ปิดแล้ว แต่ยังไม่อนุมัติ download/inference เสนอเป็นงานอิสระ: official pinned safetensors **256,146,352 bytes ≈ 256 MB**; checkpoint-only cap **300 MB** ใช้ existing isolated FASHN environment ก่อน ไม่มี dependency installation ที่ได้รับอนุมัติใน cap นี้

รัน initial 1 และสูงสุด 3 verified-readable train images, FP32/T4, native decoding/coordinate/schema checks เก็บ hashes/VRAM/errors ไม่ ranking และไม่ final timing หาก compatibility ต้อง dependency เพิ่มให้หยุดเสนอ budget ใหม่ ไม่โหลดอื่นอัตโนมัติ M2FP/CPI-R50 native priority ตามมาหลังเลือก dataset cohort/weight terms ไม่ใช้ CIHP absence ขวาง FASHN feasibility โดยไม่จำเป็น

**Current license assessment:** FASHN เข้า research/evaluation terms สำหรับ independent student research นี้ Company CCTV เป็น future evaluation input ไม่ใช่หลักฐาน company R&D; commercial deployment อยู่นอกขอบเขต ไม่ต้องถาม scope ซ้ำ Sapiens2 ยังคง excluded เพราะข้อห้าม surveillance-related research ใช้บังคับ [Component review](LICENSE_ELIGIBILITY_REASSESSMENT.md), [scope](../RESEARCH_SCOPE.md), [fixed-input proposal](../manifests/FASHN_SMOKE_PROPOSAL_V2.json) cap 300 MB รวม metadata, TRAIN IDs 967/14282/4480, สูงสุด 4 forward รวม native parity ไม่มี dependencies ใหม่; ขอ execution/download approval แยก

## GT review และ scientific decisions ที่ยังเปิด

Human reviewers ต้องตรวจ 30-image MHP checklist แล้วค่อยขยาย/ประมาณ prevalence; ไม่ต้องอนุมัติ readable policy ซ้ำ ไม่มี authorization ให้ relabel/exclude uncertain ownership cases Common taxonomy, target-person ownership, crop/matching/coverage definitions และ sensitivity reporting ยัง draft ต้อง freeze ก่อน Stage 1

Public-checkpoint training exposure ต้องรายงานพร้อมผลภายหลัง ทำ separate native/crop cohorts และ separate dataset scores ไม่มี hybrid/fusion implementation หรือ CCTV inference ในงานถัดไปที่เสนอ

## Safety และ Git

ไม่สร้าง remote/commit/push ในรอบนี้ Workspace และ study ไม่ใช่ Git repositories; existing YOLO repositories แยกกันและ user changes คงไว้ Current documents ที่แก้เก็บ archive/diff/hash ก่อน–หลัง ส่วน original measured/source records เก็บ immutable Review-validation record แยกจาก historical `STAGE0_VALIDATION.json` ที่รายงาน BLOCKED ในอดีต

**Next action: WAIT FOR USER APPROVAL.**

## Preflight execution evidence — 2026-10-08

All TAR regular payloads read and SHA256-inventoried; all converted bitmaps decoded/CRC/coordinate checks passed; strict RGB sample 20/20 passed; official semantic demo fidelity 5/5 passed; actual human metadata missing confirmed by all-JSON and converter AST audit New decoder tests 9 + existing 51 = **60 PASS** No full RGB/semantic-quality/ownership audit claim

[Preflight manifest](../manifests/CIHP_DATASETNINJA_ARCHIVE_MANIFEST_V1.json), [validation](../provenance/CIHP_ARCHIVE_PREFLIGHT_VALIDATION_V1.json), [byte-duplicate evidence](../provenance/CIHP_DATASETNINJA_BYTE_DUPLICATES_V1.json). Previous run/validation preserved as historical evidence; current docs archived before edits
