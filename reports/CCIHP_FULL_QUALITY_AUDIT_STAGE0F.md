# CCIHP — Full Quality Audit Stage 0F

**Structural audit: PASS_WITH_WARNINGS; physical-person annotation quality: HUMAN REVIEW PENDING.** Run `stage0f-ccihp-quality-20261012T062825Z`. งานที่อนุมัติคือการตรวจ dataset และเตรียม review ไม่ใช่ parser benchmark

## ขอบเขตและ provenance

ใช้ `datasets/CCIHP_icip.zip` สำหรับ GT และ `datasets/cihp-DatasetNinja.tar` สำหรับ RGB ที่ผู้เขียนระบุว่าใช้ร่วมกับ CIHP อ่านจาก archive โดยตรง ไม่แตก/เปลี่ยน source ไม่ตรวจ Color/Pattern/Size pixels

SHA256 archive เดิม: CCIHP `373f3183bf58c3e5637ba3564c9b8abef923dc434b78f469b3722282d1514829`; DatasetNinja `085d2b694a8c4e0081292a905972e1f31af9d454c12698427b187c7af67a2793` ใช้ CRC/SHA ledger ที่ตรวจครบใน Stage 0E/preflight และตรวจ ledger hash + archive stat ก่อน/หลัง ไม่ทำ complete ZIP CRC/TAR integrity ซ้ำ Required PNG และ RGB ที่อ่านรอบนี้เทียบ member SHA กับ ledger จริง

## Image-level และ person-level denominators

| Split | Images | Native Human IDs (image-local) | Attribute instances | Source pixels |
|---|---:|---:|---:|---:|
| Training | 28,280 | 93,292 | 730,213 | 4,956,221,356 |
| Validation | 5,000 | 17,548 | 136,412 | 876,659,024 |

ตรวจ required PNG **99,840 ไฟล์**: verify PNG stream แล้ว load pixels, dtype, label inventory, dims และ association อ่านครั้งละภาพ ไม่โหลด masks ทั้งชุดพร้อมกัน RGB strict full load 33,280/33,280; dimensions match 33,280/33,280. Decode/dimension errors **0**

**จำนวน native Human IDs ไม่ใช่จำนวน physical persons ที่มนุษย์รับรองแล้ว** คนเดียวอาจถูกแบ่ง ID หรือคนหลายคนอาจแชร์ ID ต้องใช้ review แยก Instance_ids เป็น attribute instances ไม่ใช่ person IDs

[Full per-image ledger](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/IMAGE_AUDIT.jsonl), [person areas/boxes](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/PERSON_AUDIT.jsonl), [statistics/quantiles](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/DESCRIPTIVE_STATISTICS.json), [aggregate evidence](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/FULL_STRUCTURAL_AUDIT.json)

## Cross-map support

| Pixel condition | TRAIN | VALIDATION |
|---|---:|---:|
| category_without_human | 0 | 0 |
| human_category_without_instance | 7,958 | 310 |
| human_without_category | 94,218 | 638 |
| instance_without_category | 0 | 0 |
| instance_without_human | 0 | 0 |
| unknown_category_pixels | 7,958 | 310 |

Association conflicts: TRAIN 0 instances/0 images; VAL 0/0. ตรวจแต่ละ positive Instance ID ว่ามี Human ID และ Category ID เดียวหรือไม่ ไม่ majority-assign หรือ relabel

## Undocumented labels และ background gaps

พบ labels นอก README **[22]**, 322 images/8,268 pixels. TRAIN0033810 ยังคง Category22 ที่ 2 pixels ตามต้นฉบับ แต่ไม่ได้เป็นกรณีเดียว ห้ามอ้างว่าทั้ง dataset มี unknown เพียง 2 pixels

Human>0 แต่ Category0 **762 images/94,856 pixels** ขยายผลจาก 12 pixels ใน 30-image sample เดิม ไม่เปลี่ยน observation เดิมให้เป็น dataset-wide count เก็บทุกพิกเซลไว้ รวมบริเวณที่ Instance0

ความต่าง support เป็น **automated structural flags** ไม่ยืนยัน missing person/wrong body class ไม่ตีความ Category0 ใน Human mask เป็น corrupted RGB, occlusion หรือ void ที่ทราบนิยามแล้ว [Warning ledger](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/ANNOTATION_WARNINGS.json), [all affected images/coordinates](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/ANOMALIES.jsonl)

**Policy proposal — ยังไม่ freeze:** ขอคำอธิบาย Category22 จาก release author; เก็บ raw22 แยกจาก background. ถ้าจะประเมิน known-label subset ใช้ explicit UNKNOWN/VOID domain เดียวกันทุก model ใน cohort และรายงาน retained pixels/persons ไม่ทำ unknown→BG. Human-with-category0 ต้องเสนอ human-mask denominator sensitivity เทียบ semantic-FG denominator โดยตั้งชื่อคนละ metric ไม่ซ่อนให้เป็น policy เดียว

## Native taxonomy และ distribution

README archive ระบุ BG0 + 21foreground (1..21), ไม่ได้กำหนด22 บทความรุ่น publication ใช้19semantic labels และ20 **characteristic** classes; 20ดังกล่าวไม่ใช่หลักฐานว่า Category_ids มี20foregroundเสมอ Author datacard header/countและรายการปัจจุบันไม่สอดคล้องครบ Generator default class_num21/loop1..20 และ evaluator remap gt>=num_classes→0 ต้องไม่คัดลอกเป็น unknown policy ของ study

| ID/name | TRAIN pixels | VAL pixels | TRAIN images with label | VAL images with label |
|---|---:|---:|---:|---:|
| 0: Background | 2,935,886,596 | 525,667,203 | 28,280 | 5,000 |
| 1: Hat | 38,225,039 | 6,664,890 | 7,810 | 1,391 |
| 2: Hair | 237,368,190 | 41,646,197 | 27,761 | 4,913 |
| 3: Glove | 3,099,043 | 530,649 | 1,832 | 321 |
| 4: Sunglasses/Glasses | 5,813,006 | 1,014,020 | 8,879 | 1,584 |
| 5: UpperClothes | 420,023,795 | 73,318,502 | 26,448 | 4,684 |
| 6: FaceMask | 964,473 | 221,824 | 436 | 88 |
| 7: Coat | 456,710,790 | 80,047,537 | 17,827 | 3,200 |
| 8: Socks | 3,756,067 | 705,831 | 3,210 | 571 |
| 9: Pants | 205,818,591 | 36,386,960 | 19,968 | 3,580 |
| 10: Torso-skin | 73,147,775 | 12,203,295 | 27,443 | 4,839 |
| 11: Scarf | 15,239,197 | 2,540,029 | 6,114 | 1,040 |
| 12: Skirt | 83,720,630 | 14,339,785 | 6,819 | 1,226 |
| 13: Face | 215,019,814 | 36,960,110 | 28,110 | 4,966 |
| 14: Left-arm | 78,592,666 | 13,299,315 | 24,873 | 4,454 |
| 15: Right-arm | 84,253,036 | 14,692,011 | 25,221 | 4,546 |
| 16: Left-leg | 19,622,566 | 3,254,914 | 8,064 | 1,466 |
| 17: Right-leg | 19,422,756 | 3,219,889 | 8,071 | 1,464 |
| 18: Left-shoe | 11,116,891 | 1,975,101 | 9,421 | 1,725 |
| 19: Right-shoe | 11,256,737 | 1,995,647 | 9,405 | 1,725 |
| 20: Bag | 7,816,841 | 1,245,507 | 2,279 | 428 |
| 21: Others | 29,338,899 | 4,729,498 | 19,402 | 3,367 |
| 22: UNKNOWN_UNDOCUMENTED_22 | 7,958 | 310 | 261 | 61 |

[CSV with fixed all-pixel denominators](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/CLASS_DISTRIBUTIONS.csv). Pixel support/image occurrenceไม่ใช่ class accuracy หรือ physical ownership reliability Rare classes ต้องรายงาน support พร้อมคะแนนในอนาคต

## Visible/occluded และ overlap semantics

**Verified:** Human_ids เป็น single-valued raster per image; Category/Human/Instance มี gridเดียวกับRGB; paper §2 ระบุ human masks/category definitions ถูกเปลี่ยนจาก CIHP; native person identity อยู่ใน Human IDs ไม่ใช่ part objectsในDatasetNinja

**Unresolved:** ไม่มี authoritative per-class amodal completion/hidden-pixel rules หรือวิธี annotate visible background personsทุกคนครบ Human IDsสองค่าทับพิกเซลเดียวกันไม่ได้ใน rasterนี้ จึงไม่ใช้ bbox intersection เป็น occlusion count หรือพิสูจน์ไม่มีคนซ้อน physical alignment/completeness ต้องตรวจภาพและ adjudicate ห้ามอ้าง CCTV/occlusion robustnessจาก dataset statistics

## ผลตรวจคนที่ไม่มี known semantic foreground

ตรวจทุกภาพที่มี Category0/Human gap หรือ unknown label เพิ่มแบบเจาะจง **1,027 ภาพ** พบ **35 Human IDs** ที่ Category เป็น0ทั้ง mask: TRAIN27 / VAL8 ในจำนวนนี้34 IDsมีเพียง1–8พิกเซล อีก1IDคือ TRAIN0014422/Human1 ขนาด91,332พิกเซล จึงห้ามสมมติว่า positive Human ID ทุกค่ามี semantic GT ที่ใช้ทำ person-macro mIoU ได้

เมื่อรวมกรณีที่มีแต่ unknown label พบ **42 Human IDs ไม่มี known foreground1..21** คงไว้ใน source population ทั้งหมด ไม่ตัดทิ้งหรือซ่อม ค่า native person denominator110,840หมายถึงจำนวน IDs ที่มีพิกเซล ไม่ใช่จำนวนคนที่ scoring policy รับรองแล้ว การกำหนด eligibility/undefined score ของกลุ่มนี้ต้องตรวจและอนุมัติก่อน benchmark

[Person semantic support evidence](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/PERSON_SEMANTIC_SUPPORT_WARNINGS.json). จำนวนnative IDsในreleaseนี้110,840 ต่างจากตัวเลข110,821ในpublication19 IDs ไม่ทราบสาเหตุversion/counting conventionครบ จึงรายงานค่าที่ตรวจจริง ไม่ลบ IDsเพื่อให้ตรงpaper

## ภาพตรวจ warning แบบเจาะจง

ตรวจ unknown label ทั้ง322ภาพ พบทุกพิกเซลมี Human support และไม่มี positive attribute Instance ID; ID22จึงไม่ควรถูกตีความเป็น background โดยอัตโนมัติ ดู [หลักฐาน](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/FOCUSED_WARNING_INVESTIGATION.json)

**Observation จาก assistant spotcheck:** ภาพ0014422มีบริเวณใบหน้า/ผมของคนด้านซ้ายอยู่ใน Human1 แต่ semanticทั้งหมดเป็น0 ส่วน0010505มี Category22ในบริเวณผ้าห้อย ไม่ได้เป็นแค่จุดสองพิกเซลทุกภาพ สองข้อเป็นการอ่านภาพกับค่าต้นฉบับ ไม่ใช่การรับรองสาเหตุหรือ human adjudication

**Interpretation:** ปัญหา semantic support อาจกระทบ oracle geometry และ person-macro denominator แม้ instance-to-class association ของ positive Instance IDs จะผ่าน ไม่ควรแก้ด้วย minimum-area threshold หรือ ignore policy ที่เลือกจากคะแนนVAL

![TRAIN0014422: source RGB and coverage flag](../outputs/visualizations/stage0f-ccihp-quality-20261012T062825Z/focused_warnings_v2/0014422_full.png)

## Quality gate

เตรียม independent stratified TRAIN sample **200ภาพ**, ทุกภาพมี full-resolution RGB/Human/Category/Instance/per-personGT/warningpanels; additional0033810เป็น purposive warning case ไม่รวม prevalence sample [Review package](CCIHP_HUMAN_REVIEW_STAGE0F.md)

ยังไม่มี independent human review/adjudication จึง **NOT ESTIMATED** annotation-error prevalence และไม่ promote primary หลังผ่าน structural testsเพียงอย่างเดียว Decision Stage0F **D — Insufficient evidence for primary readiness; human review required** ส่วน Stage0E DecisionB compatibilityที่ผู้ใช้ยอมรับคงเดิม

## Rights และ references

ใช้ Decision5A student academic scopeเดิม CCIHP annotations CC-BY-NC4 และ evaluation codeMITตาม includedLICENSE/README; originalCIHP image-rightsยังไม่ชัด DatasetNinja conversionlicenseไม่แทนสิทธิ์ต้นฉบับ ไม่แจกจ่ายรูปโดยอ้าง blanketpermission

[Author paper](https://arxiv.org/abs/2201.09594), [DOI](https://doi.org/10.1109/ICIP42928.2021.9506509), [included README](../provenance/RUN_MANIFESTS/stage0e-ccihp-native-20261012T045912Z/archive_documents/README.md). Source snapshots/prior license evidence retained. No source GT changes, model inference, checkpoint download, PPSS activity, attributes or CCTV execution


## Native known-class support เพิ่มเติม (ไม่ใช่ exclusion policy)

TRAIN มี native Human IDs 93,292; ไม่มีknown semanticforeground 33 IDs; มีknownsupport 93,259 IDs ส่วน VAL มี17,548 / ไม่มีknownsupport9 / มีknownsupport17,539 ทั้งหมดคงอยู่ในsourcepopulation ตัวเลขknownsupportไม่ใช่approvedCOMMON_HPหรือscorabledenominator เพราะยังไม่freezeprojection/domain [Support draft](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/PERSON_METRIC_SUPPORT_DRAFT.json)
