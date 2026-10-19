# Stage 0E — CCIHP / CIHP GT Compatibility Audit

**Current bounded execution: PASS_WITH_WARNINGS. Decision B — PARTIALLY_COMPATIBLE. Native CIHP equivalence: BLOCKED. Full Quality Audit: NOT_STARTED.**

CCIHP ZIP เพิ่มมาแล้วหลังการตรวจรอบก่อน รายงานก่อนที่ระบุ source missing/Decision C ถูกเก็บพร้อม hashes ใน archive ไม่เปลี่ยนข้อเท็จจริงของรอบก่อน และไม่เริ่ม Stage 0 ใหม่

## 1. Actual archives / provenance

| รายการ | CCIHP | CIHP DatasetNinja |
|---|---|---|
| Workspace-relative source | `datasets/CCIHP_icip.zip` | `datasets/cihp-DatasetNinja.tar` |
| Size | 842,868,844 bytes | 2,015,375,360 bytes |
| Actual role | Annotation-only CCIHP_icip release | CIHP RGB + converted semantic part bitmaps |
| Human GT | Human_ids present | Original human ownership omitted |
| Integrity | All-member ZIP CRC + SHA inventory PASS | Reuse complete preflight; no whole TAR rehash |

CCIHP SHA256: `373f3183bf58c3e5637ba3564c9b8abef923dc434b78f469b3722282d1514829`. ZIP มี **209,707 members / 209,688 regular files**, safe paths/no duplicates/no symlinks, 877,848,629 uncompressed bytes ทุก payload อ่าน/CRC/SHA256ครบ ไม่มี full extraction

Included README/LICENSE/evaluation-source headers ตรงกับ CCIHP ICIP 2021 documentation แต่ไม่มี publisher checksum/download receipt อิสระยืนยัน binary identity Local SHA พิสูจน์ไฟล์ที่ตรวจ ไม่รับรองต้นทางเกินหลักฐาน

## 2. Completeness / splits / geometry

Train **28,280 annotation sets**, Validation **5,000**, รวม **33,280** ทั้ง Category_ids/Human_ids/Instance_ids/Color_ids/Pattern_ids/Size_ids จับคู่ IDs/split lists ครบไม่มี missing/orphan Train/Val IDsไม่ซ้ำกัน และตรงกับ DatasetNinja **ทั้งสอง split ทุก ID** ไม่ใช้ filenames เป็น RGB-identity proof

Validation มี Charac_instance_ids อีก 5,000 ไฟล์และ evaluation lookup tables; inspect เฉพาะ structure/CRC ไม่รัน color/pattern/size evaluation ZIP ไม่มี RGB และไม่มี test annotations; ไม่ถือ hidden test GT เป็น corruption

Strict PNG CRC/full-load/grid checks **30 images × 3 maps = 90 PNGs**: 25 TRAIN (20 SHA-ranked + 5 previous native demos) และ 5 VAL เพื่อ integrity/compatibility เท่านั้น ไม่ใช้ปรับ model/taxonomy thresholds หรือเลือกจาก runtime ผลนี้ไม่ใช่ full semantic audit ทั้ง 33,280 ชุด

RGB ใช้จาก CIHP TAR ตาม CCIHP documentation ที่ประกาศ shared images; 30 grids ตรงและดู alignment 3 ภาพ มี official native CIHP RGB/semantic references 5 TRAIN demos ที่ยืนยัน DatasetNinja byte/pixel parity แต่ CCIHP ไม่มี RGB copy ให้เทียบ independent bytes จึงไม่อ้าง CCIHP-RGB byte equality ที่ไม่ได้ตรวจ

## 3. Human_ids / Instance_ids

Human_ids samples เป็น uint8 image-local IDs, background0; Category_ids uint8 และ Instance_ids uint16 ไม่สับสน part-instance IDs กับ person IDs ไม่ downcast หรือทำ connected-component person reconstruction

30 ภาพมี **96 source person IDs**, **840 attribute instances** ทุก sampled attribute instance มีหนึ่ง positive human ID และหนึ่ง positive semantic ID แยก native CCIHP per-person planes และ recompose source maps ได้ตรงทุก pixel **30/30 PASS** เก็บ human support ต่างหากจาก semantic foreground จึงไม่ทิ้ง human pixels ที่ไม่มี category

Cross-map coverage: category foreground without human=0; instance without human=0; human without category=**12 pixels** ต้องตรวจ semantics/annotation intent ไม่เรียก overlap/holes ว่า error โดยอัตโนมัติ Original Human_ids เป็น single-valued visible-grid representation; ไม่มีหลักฐานเพียงพอเรื่อง amodal/occluded completion หรือ full visible-person completeness

[Person verification with full-frame images](CCIHP_PERSON_INSTANCE_VERIFICATION.md), [lossless fidelity](../provenance/RUN_MANIFESTS/stage0e-ccihp-native-20261012T045912Z/CCIHP_GT_FIDELITY.json) ไม่ประมาณ physical-ownership error prevalence จาก 3 inspected examples

## 4. Native semantic equivalence ไม่ผ่าน

Included README กำหนด 1–21 foreground concepts (รวม Face Mask6, Bag20, Others21), background0 ส่วน original CIHP มี Dress6 และไม่มี standalone Bag/Others/FaceMask Same numeric ID ไม่ใช่ same semantic target Dressถูกแยก UpperClothes/Skirt, glasses/scarf/hair เปลี่ยน scope; paper ยืนยัน human masks ถูกปรับด้วย [Original publication §2](https://arxiv.org/html/2201.09594v1#S2)

Same-frame raw ID differences ที่ native demos (เป็น **diagnostic counts**, ไม่ใช่ harmonized metric/quality score):

| TRAIN demo | CCIHP person IDs | Semantic raw-ID differing pixels | FG/BG differing pixels |
|---|---|---|---|
| 0002190 | 2 | 361 | 7 |
| 0005008 | 7 | 4,836 | 3,228 |
| 0012008 | 3 | 46,665 | 4,905 |
| 0026375 | 3 | 19,811 | 327 |
| 0032190 | 2 | 59,326 | 806 |

รวม 30 samples raw semantic difference **304,537 pixels**, FG/BG difference **35,492 pixels** การเปลี่ยน semantic definition และ mask boundariesปนกัน จึงไม่ตีความเป็น corruption/accuracy drop หรือ causal effect รายการที่ไม่เปลี่ยนชื่อยังไม่พิสูจน์ exact benchmark-equivalent target

[Class-by-class matrix](../taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv) มี observed support/diagnostic differences และ incompatible/ambiguous/NOT_VERIFIED distinctions Common mapping ยัง DRAFT ไม่มี universal coarse remapping ที่ silently hide difficult GT

## 5. Can DatasetNinja parts inherit CCIHP person IDs?

ตรวจ **741 CIHP part objects** ใน 30 frames กับ CCIHP Human_ids:

| Association outcome | Objects |
|---|---|
| One human ID covers full object support | 694 |
| Object covers multiple human IDs | 21 |
| One human ID plus unassigned/background pixels | 26 |

จึงไม่สามารถ claim every native CIHP object มี unambiguous CCIHP owner Splitting objects by CCIHP masks หรือเลือก majority owner จะเป็น **derived mixed-source GT policy** ไม่ใช่ original native CIHP ที่พิสูจน์แล้ว No heuristics applied Native human reference unavailable จึงยังไม่ทราบว่า label conflicts เกิดจาก annotation correction/boundary changes/ownership mistakes อย่างใด

## 6. Annotation warnings / source code caveats

พบ TRAIN `0033810` มี Category_ids **22 จำนวน 2 pixels** ที่ original xy `(301,162),(302,162)` นอก README0–21 definition Source ZIP/PNG CRC valid ค่าเดิมคงไว้; classification=`UNRESOLVED_UNDOCUMENTED_LABEL` ไม่ assign เป็น background/void ไม่สรุปว่าทั้ง dataset corrupt [Exact evidence](../provenance/RUN_MANIFESTS/stage0e-ccihp-native-20261012T045912Z/UNEXPECTED_CATEGORY_SCREEN.json)

README/paper/release versionแตกต่าง: paperเดิม19 foreground; local README21 foreground และพบ22ที่ยังไม่อธิบาย Evaluation generator default `class_num=21` อาจไม่รวม Others21; metric script maps labels>=num_classes เป็น background จึง **ห้ามนำ defaults มา freeze study scoring** โดยไม่ตรวจ ไม่ execute/patch upstream codeหรือ attribute metrics

Known CIHP split leakage reused: **39 train–val JPEG-byte groups / 39 validation IDs**, 83 all-cross-split groups Membership ของ CCIHPตรงสอง split จึงต้อง disclose risk เดิม ไม่ claim split independence Near-duplicate/decoded full checks และ CCIHP duplicate-annotation fidelityยัง NOT_TESTED ไม่เปลี่ยน lists/exclude samples

## 7. License / research scope

Reuse user-confirmed **Decision 5A — independent noncommercial academic research/evaluation** Local CCIHP annotation LICENSEเป็น **CC-BY-NC-4.0**, READMEและevaluation .py headersแยก code **MIT** เข้ากับ research scope ภายใต้ attribution/notices แต่ไม่ได้โอนสิทธิ์ original CIHP RGB/GT ซึ่งยัง unresolved ตาม reviewเดิม DatasetNinja provider MIT ก็ไม่ใช่ RGB-owner grant ไม่ audit parser licensesใหม่ ไม่ใช้ CCTV

## 8. Decision / next gate

**B — PARTIALLY_COMPATIBLE:** CCIHP own human+semantic+attribute-instance GT กู้เป็น lossless per-person recordsได้ใน samplesและมี source filesครบ แต่ modified targets/ambiguous cross-source linksทำให้ **A — native CIHP compatible ยังไม่ผ่าน**

Native CIHP benchmark routeยังต้อง original verified GT supplement/distribution; **ไม่จำเป็นต้อง downloadเพิ่มเพื่อไปต่อ bounded/full quality audit ของ custom CCIHP-person track หากผู้ใช้เลือกและอนุมัติ trackนี้** ทั้งสอง routeต้องแยกชื่อ dataset/targets/denominatorsและไม่เรียก custom score official CIHP

ก่อน freeze: ทำ Full Quality Audit ตาม trackที่เลือก, resolve unknown22/coverage/visible ownership/ignore conventions และ review ~200 deterministic stratified TRAIN images [Draft review plan](../manifests/CCIHP_QUALITY_REVIEW_PLAN_V1.json), [decision](CIHP_GROUND_TRUTH_RECOVERY_DECISION.md)

## 9. Executed tests / limitations

New GT reader **8/8 synthetic tests PASS**, actual 30-frame source roundtrip PASS; lossless diagnostic NPZ export3cases passes reload (`allow_pickle=False`) Preserves instance dtype/unknown IDs/unassigned regionsและrejects silent overlap flattening Tests ไม่เป็น scientific quality/benchmark scores

First auditหยุดเมื่อพบ undocumented22 หลัง CRCครบ และ JSON exportเคยติด NumPy bool; เก็บ failure recordsและแก้ checker/exportใน studycodeเท่านั้น Resume verified CRC ledger ไม่รัน full CRCซ้ำ ไม่แก้ sourcePNG/third-party evaluator

**Overall Stage 0 still BLOCKED / WAITING_FOR_USER_APPROVAL.** ไม่มี full benchmark, parser/checkpoint download/inference, training, hybrid, attributes, PPSS หรือ CCTV activity
