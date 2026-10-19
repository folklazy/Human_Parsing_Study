# CIHP — Current Quality Audit Status

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

## Stage 0E — Actual archive identity and person-GT recovery

ผู้ใช้ระบุ TAR นี้ว่า CCIHP แต่ actual README/LICENSE/meta/annotations ยืนยัน **CIHP DatasetNinja conversion, not CCIHP** ไม่มี CCIHP_icip.zip/native Human_ids source บน workspace ไม่ใช้ชื่อที่เรียกเป็นหลักฐาน release identity

Fresh bounded recheck 5 official TRAIN demos: RGB/semantic pixels ตรงทั้งหมด, 0 differing pixels; GT diagnostics 3 images inspect แล้ว ไม่มี person GT reconstructed Publication CCIHP ระบุ modified semantic/human targets จึงไม่ silently substitute CCIHP Human_ids เป็น native CIHP

**Decision C — native GT supplement/distribution required for current assets**; full download อาจเลี่ยงได้ถ้ามี verified original GT-only supplement ไม่เริ่ม acquisition/Full Quality Audit/benchmark Native ~200-image human reviewยังรอ input

[Stage 0E audit](CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [person verification](CCIHP_PERSON_INSTANCE_VERIFICATION.md), [GT decision](CIHP_GROUND_TRUTH_RECOVERY_DECISION.md), [evidence](../provenance/CCIHP_ARCHIVE_AUDIT.json)
