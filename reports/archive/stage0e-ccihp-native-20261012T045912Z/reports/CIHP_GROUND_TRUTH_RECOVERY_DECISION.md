# CIHP Ground Truth Recovery Decision — Stage 0E

**Decision C — NATIVE_CIHP_REQUIRED (current assets). Native benchmark readiness: BLOCKED.**

ผู้ใช้ยืนยันไฟล์ `datasets/cihp-DatasetNinja.tar` เป็นเป้าหมาย การอ่าน README/LICENSE/meta/JSON และ native demo parity พบว่าเป็น CIHP semantic-part conversion **ไม่ใช่ CCIHP release** ไม่มี Human_ids/grouping จึงไม่กู้ native per-human parsing/GT matching/person denominator จากไฟล์นี้อย่าง defensible ได้

| Output task | Current feasibility | ขอบเขต |
|---|---|---|
| Global semantic/body/clothing regions | CONDITIONAL | Converted parts verified structurally; native demo parity 5 only; full quality/license/common projection pending |
| Native GT person IDs | BLOCKED | Original Human_ids missing; object IDs ไม่ใช่ person IDs |
| Per-person native parsing | BLOCKED | No lossless person ownership; original mapping source necessary |
| Oracle geometry / GT person matching | BLOCKED | Heuristic bbox/connected components ไม่แทน physical ownership |
| Person-macro/coverage-aware parsing | BLOCKED | Native person populations/support undefined |
| Native CIHP APp/PCP targets | BLOCKED | Semantic demo referencesไม่เพียงพอ; original instance/part metadata required |
| Custom CCIHP common track | NOT_TESTED | Actual CCIHP absent; future independent custom source audit required |

## เหตุผลที่ไม่เลือก A/B/D

A ไม่มี original person-equivalence evidence และ paper ยืนยัน CCIHP annotations เปลี่ยนจาก CIHP B อาจเหมาะเมื่อมี actual CCIHP ให้ตรวจ custom-person information แต่ตอนนี้ไม่มี source Human_ids เลย D จะเหมาะกับการตัดสิน unseen CCIHP archive; อย่างไรก็ดีสำหรับ **actual available TAR** มีหลักฐานพอว่าข้อมูล ownership หาย จึงเลือก C ไม่อ้างว่า CCIHP ทุก release ไม่มีประโยชน์

## Next bounded execution หลังอนุมัติ

1. Obtain original native CIHP GT supplement หรือ distribution ที่ verified source มี Human_ids/Category_ids/Instance_ids และ full original lists ก่อน ไม่ต้องโหลด DatasetNinja conversion ซ้ำ หากมี copy บน server ให้ตรวจ copy นั้นก่อน download
2. Small same-frame source fidelity gate: image IDs/RGB identity/grids, native class IDs/void, every part's human association, semantic/person count consistency เทียบ original reference หลาย-person cases ไม่ flatten overlaps/guess ownership
3. เมื่อ small gate ผ่านจึงเสนอ Full Quality Audit: strict decode ทั้งชุด, exact/near reuse, native distributions และ ~200 deterministic stratified TRAIN human-review sample ตาม existing V2 plan ไม่เลือก from validation หรือตั้ง primary จาก file-integrity PASS อย่างเดียว

**อีก CIHP download จำเป็นหรือไม่:** native-person GT เพิ่มจำเป็น แต่ full RGB distribution download อาจไม่จำเป็นถ้าได้ verified GT-only supplement/local native copy หากไม่มี supplement ให้ขออนุมัติ official native distribution แยกก่อน; **ยังไม่อนุมัติหรือเริ่ม download**

ถ้าได้ CCIHP จริง สามารถ audit custom cohort ต่างหากได้ แต่การประกอบ native CIHP semantic × modified CCIHP Human_ids ต้องผ่าน fidelity/denominator tests และห้ามเรียก official CIHP หาก person/region target เปลี่ยน การไม่มี file ในรอบนี้ไม่ให้ข้อสรุปเชิง pixel ของ CCIHP

Reuse Decision 5A license findings แยก original CIHP image rights, CCIHP annotation CC-BY-NC declaration, DatasetNinja provider terms และ model weights ไม่ใช้ license ของ source หนึ่งแทนอีก source

[Compatibility audit](CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [Human evidence](CCIHP_PERSON_INSTANCE_VERIFICATION.md), [draft matrix](../taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv), [~200 review plan](../manifests/CIHP_QUALITY_REVIEW_PLAN_V2.json)

**STOP — WAIT FOR USER APPROVAL.** No source edits/download/model inference, no PPSS/CCTV/attributes, no Stage 1 or benchmark
