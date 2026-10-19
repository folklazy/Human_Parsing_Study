# Review — Decisions Appendix ของ Human Parsing Protocol V2

วันที่: 14 ตุลาคม 2026 UTC · **REVIEW ONLY / NOT FROZEN / NO INFERENCE**

เอกสารที่ตรวจทั้ง396บรรทัด: [Decisions Appendix](../../BENCHMARK_PROTOCOL_20_VARIANTS_V2_DECISIONS_APPENDIX_TH_20261014.md) · [V2 review เดิม](BENCHMARK_PROTOCOL_20_VARIANTS_V2_REVIEW_TH_20261014.md)

**ความเห็นหลัก:** Appendix ปิดข้อค้นพบสำคัญจากรอบก่อนแล้วและเหมาะใช้ส่งต่อไปทำ config/evaluator ไม่ต้องออกแบบการศึกษาใหม่ จุดที่ยังต้องเติมเป็น operational definitions และ tests ของระบบจริง ไม่ใช่เหตุให้ขยายแผนเป็น dataset/metric เพิ่มอีก การยอมรับหลักการในเอกสารยังแยกจากการ freeze ค่าจริงและการอนุมัติ benchmark

## 1. สิ่งที่เห็นด้วยและตรวจรองรับแล้ว

| ข้อเสนอ | ความเห็นและหลักฐาน |
|---|---|
| Eligible cardinality ก่อน sum IoU | ตรงกับ objective ของโค้ด matching เดิม และตัวอย่าง binary masks ใน appendix ให้ผลตามที่ระบุ |
| GT-supported mIoU พร้อมรายงาน FP/foreground precision | เป็นนิยามที่ใช้ได้ ต้องเปิดเผยข้อจำกัดและแยกจาก union-active mean ไม่จำเป็นต้องเปลี่ยนกลับเพียงเพราะ generic aggregator เดิมต่างกัน |
| เพิ่ม miss-inclusive person semantic score | ตอบโจทย์ body/clothing รายคนได้ตรงกว่า foreground diagnostic อย่างเดียว |
| G_loc รวม GT ที่ semantic undefined | ไม่ลงโทษ prediction ที่พบคนนี้ว่าเป็น extra person เพียงเพราะไม่มี semantic truth และไม่เติม semantic score0 ให้ GT ที่ไม่มีเฉลย |
| D/O/P ledger และ no-output conventions | แยก upstream detection, processing opportunity และ final emitted output ได้ดี |
| APp/PCP/APp_vol พร้อม APr pending | ตรงกับขอบเขต wrapper ที่มีจริง |
| Native/adapted profiles และจริงทั้ง pipeline | เปิดเผย CPI memory adapter, Sapiens native intermediate dtype และ process/resource costs |
| Native hard-label projection / lossless masks / scoring fingerprint | ลด storage ที่ไม่จำเป็น พร้อมระบุว่าสิ่งใด re-score ได้หรือไม่ได้ |
| Optional metrics/datasets ไม่เป็น prerequisites | เหมาะสมกับงานนี้ ไม่ควรเพิ่ม APr/PartPQ/PWQ หรือ dataset ใหม่เพื่อให้เอกสารดูครบ |

ตรวจ [Detectron2 SemSegEvaluator source ที่ appendix อ้าง](https://detectron2.readthedocs.io/en/latest/_modules/detectron2/evaluation/sem_seg_evaluation.html) พบ `acc_valid = pos_gt > 0` และ `iou_valid` ใช้เงื่อนไขนี้ จึงรองรับคำอ้างเรื่อง GT-positive class averaging ใน source ฉบับที่อ่าน อย่างไรก็ตาม study ยังต้อง pin revision และระบุว่า foreground-only K ของเราไม่ใช่การคัดลอกทุก convention ของ evaluator นั้นโดยอัตโนมัติ

## 2. ตรวจ matching ของ project จริงเพิ่มเติม

สร้าง GT สอง masks ไม่ทับกัน คนละ10พิกเซล ตามคำอธิบายใน appendix และเรียก [match_persons เดิม](../src/evaluation/common_metrics.py) โดยไม่แก้ source:

```text
IoU matrix = [[0.75, 0.20],
              [2/19, 0.00]]
threshold = 0.10
```

โค้ดเดิมเลือกสองคู่ รวม IoU0.3052631579 ตรงกับ cardinality-first ส่วน weight-only เลือกคู่เดียว0.75ได้ ผลนี้เป็น synthetic mask check ไม่ใช่ model accuracy

ตรวจ solver เดิมกับ independent exhaustive partial-assignment oracle บน300กราฟเพิ่มเติม ขนาด1..4×1..4, seed20261014, weights0..1ขั้นละ0.1 และ thresholds0.1/0.3/0.5/0.75: **จำนวนคู่และผลรวม IoUตรงทุกกราฟ**

รอบนี้เป็นการตรวจของเราเอง ไม่อ้างว่า reproduce execution300กราฟของผู้เขียน appendix เพราะเอกสารไม่ได้แนบชุด inputs/script เดิม ผลนี้ยังไม่รับรอง stable-ID tie selection หรือ bbox implementation

ประเด็นที่ต้องทำใน implementation คือ `match_persons` เดิมใช้ **mask IoU** แต่ appendix เลือก **bbox IoU** เป็น primary geometry จึงต้องมี bbox primitive หรือ generic assignment ที่รับ geometry-specific weights ไม่ส่งพิกัดbboxเข้า mask function โดยตรง ต้องทดสอบ xyxy/xywh, half-open/inclusive coordinates, clipping, empty boxes, threshold equality และ ties

## 3. GT-supported person score: ต้องบังคับ FP accounting รายคนให้ชัด

Appendix ระบุข้อจำกัดนี้แล้วใน§6.2 แต่ควรเขียนให้ชัดว่า FP/foreground precision เป็น **per-target-person ก่อน composition** ด้วย เพราะ global metrics และ final person FP ไม่ตรวจ neighbor contamination ครบทุกกรณี

ตัวอย่างสังเคราะห์ที่ตรวจจริง โดยใช้ declared pairing A→A,B→B:

```text
GT person A: [1,1,0,0]
GT person B: [0,0,2,2]
Prediction A: [1,1,2,2]   ← เอาคลาสของ B ติดเข้ามาด้วย
Prediction B: [0,0,2,2]
```

- A มี K_A={1} จึงได้ GT-supported person semantic score1.00 แม้ติดคลาส2ของคนข้างเคียง
- B ได้1.00 และ composed global semantic mIoUก็1.00
- แต่ person A มี foreground IoU/precision0.50 และ predicted-only class2 FPสองพิกเซลใน target-person negative domain

ถ้าใช้ emitted detector identity boxes ที่จับตำแหน่งได้ถูกต้อง final bbox person precision/recall ก็อาจไม่เปิดเผยปัญหา masks นี้ กรณีใช้ mask-derived boxes จะให้ geometry ต่างกัน ตัวอย่างนี้เป็นข้อจำกัดทางนิยาม ไม่ได้อ้างว่าเป็น output ของโมเดลจริงหรือผ่านทุก routing rule ที่ยังไม่ freeze

**ข้อเสนอ:** คง Q_person_sem_GT ตาม appendix แต่ให้ per-person foreground IoU/precision และ predicted-only/UNMAPPED FP บน V_g เป็นผลที่ต้องอ่านร่วมก่อน shortlist อย่ารายงาน FP เฉพาะ composed global map หรือ extra person count ซึ่งอาจซ่อนการให้ pixels ของคนหนึ่งไปอยู่ในอีก instance

ไม่ต้องเพิ่ม weighted overall score หรือเปลี่ยน primaryสูตรย้อนหลัง หากจะเพิ่ม person union-active semantic mean เป็น sensitivity ให้ประกาศก่อนผลตามแนวทางที่ appendix อนุญาต

## 4. Bbox matching เหมาะเป็น localization criterion แต่ไม่ใช่ parsing success

การเลือก bbox IoU0.50 และ sensitivity0.75 เป็น proposed operating points ที่สมเหตุสมผลสำหรับ localization ไม่ใช่หลักฐานว่าค่าที่เลือกดีที่สุดสำหรับ dataset นี้ ให้ตรวจ TRAIN conventions แล้ว freeze ไม่เลือกจาก VAL scores

สิ่งที่ควรเติมเป็น config คือ **GT bbox source เดียวกันทุกระบบ** และ **prediction bbox source ของแต่ละ system ที่ล็อกล่วงหน้า** โดยเฉพาะ Human mask ที่รวมกระเป๋า/objects เทียบกับ YOLOหรือnative boxesที่อาจครอบคนต่างขอบเขต

ตัวอย่าง GT mask100พิกเซล และ parsing maskมีเพียงหนึ่งพิกเซล แม้ emitted identity bboxจะตรงGTจน bboxIoU1.00 ก็มี maskIoU0.01ได้ ภายใต้กฎnonempty-native-foreground ระบบยัง emit person ได้ กฎนี้ไม่ผิด แต่คะแนนต้องเรียก **bbox localization success** ไม่ใช่ segmentation/body-clothing success

จึงควรแยก availability อย่างน้อย:

| สถานะ | ความหมาย |
|---|---|
| Execution completed | Parser/adapter จบและcontractผ่าน |
| Native person emitted | มีnative foregroundและvalid identity recordตามกฎ |
| Target semantic available | มีcanonical target foregroundตามmappingที่ล็อก โดยไม่ใช้GTตัดสินขณะinference |
| Quality | Class/extent/ownership ถูกเพียงใดเมื่อevaluateกับGT |

Native foregroundที่เป็นแต่OUTSIDE_TARGETยังอาจมีperson emittedแต่target semanticว่างได้ ตามappendix§7.1อย่ารวมสองavailabilityนี้เป็นเปอร์เซ็นต์เดียว

## 5. Population primary เปลี่ยนเป็นข้อเสนอใหม่ ต้องบันทึกเป็น decision

Appendix §3 เสนอ CCIHP exact TRAIN-overlap-controlled 4,961 ภาพเป็น primary candidate และ source 5,000 ภาพเป็น reference/sensitivity ผมเห็นด้วยว่าเป็นทางเลือกที่มีเหตุผลสำหรับ research comparison ที่ต้องการลด known exact reuse

แต่เรื่องนี้เป็น **การเลือกบทบาท population** ที่ต้องยอมรับก่อน freeze ไม่ใช่แค่แก้ชื่อ column จาก V2 และไม่ควร activate จาก review นี้อัตโนมัติ

แนะนำเมื่อยอมรับแนวทางนี้: controlled 4,961 เป็นผลหลักสำหรับ cohort ที่กำหนด พร้อมรายงาน source 5,000 แยก และเก็บ manifest/version/จำนวน G_loc/G_sem ของทั้งสอง ไม่มีการเปลี่ยน original split การควบคุม 39 IDs นี้ไม่พิสูจน์ว่าไม่เคยเห็นภาพจาก training/pretraining ทั้งหมด และ within-VAL duplicate ไม่หายเอง

MHP controlled-readable 4,347 และ readable 4,999 ให้คงแยกเป็น complementary/source-reference อย่างที่เสนอ ไม่เฉลี่ย raw คะแนนกับ CCIHP ที่ GT ต่าง taxonomy/aggregation

## 6. Operational failures: ระบุหน่วยความล้มเหลวก่อนเริ่ม

ข้อเสนอ full-population operational result ถูกทิศทาง เพราะไม่ให้ OOM/crash แล้วตัดภาพยากของรุ่นนั้นออก แต่ยังต้องกำหนดว่า failed unit คือ person opportunity, frame หรือ run

ตัวอย่าง frame มีสาม opportunities สองคนมี validated outputs แล้ว คนที่สาม OOM:

- หากระบบรองรับ incremental per-person emission อาจคงสอง outputs และบันทึกคนที่สาม no-output
- หาก frame ต้องสำเร็จแบบ atomic ก่อน emit การ fail อาจทำให้ final outputs ของ frame ว่างทั้งหมด

สองนโยบายใช้ได้สำหรับ system behavior ต่างกัน แต่คะแนน/latency ต่างกัน จึงห้าม runner เลือกเมื่อเห็นผล ต้องล็อก per-route lifecycle, partial-output retention, cleanup/restart, retry limit, failed-attempt cost และ timeout unit

**แยก external infrastructure failure:** GPU contention, disk full, server interruption หรือ bad input ไม่ใช่หลักฐาน model quality ต่ำ หากทรัพยากรไม่ตรง frozen profile ให้ pause/retry ตามกฎที่บันทึก ส่วน OOM ของ system บน clean intended hardware เป็น resource/operational failure ตามที่เสนอ ไม่แปลง environment contamination เป็น model miss

Conditional quality บน success และ operational full-population quality มีประโยชน์ทั้งคู่ ต้องตั้งชื่อแยก และไม่ใช้ conditional score ของ population คนละชุดแข่งกันโดยปิดบัง failures

## 7. สิ่งที่ยังต้องมีจริงก่อน freeze

Appendix เป็น decision proposal ที่ชัดขึ้นมาก แต่ค่าที่เหลือควรลง config และ tested artifacts ให้จบ:

- Target taxonomy/numeric mapping/cohort eligibility และ G_loc/G_sem sidecars พร้อม retained support
- Canonical GT bbox/pred bbox source, matching geometry/threshold/ties, person negative pixels และ FP definitions
- YOLO confidence/NMS/maxDet/input geometry, crop/ROI policy, target ownership, T3b association และ D/O/P emission rules
- Actual execution profile/processes/IPC/residency/TTA/dtypes, timing manifest/warmups/repeats และ failure/retry lifecycle
- Schema/grid/transforms, inference/scoring fingerprints, storage budget และ atomic resume tests
- Primary contrasts/shortlist criteria และ resource comparison conditions รวม hardware/workload ไม่ใช้ tuple accuracy เพียงอย่างเดียวสร้าง latency Pareto ข้ามเงื่อนไข

ตัวเลขที่ appendix เลือกเป็น proposals มีแล้วหลายส่วน ไม่ต้องปล่อยทั้งหมด PENDING ต่อ เพียงตรวจและแปลงเป็น config พร้อม tests เฉพาะส่วนที่ใช้จริง ไม่ต้องเพิ่ม metric หรือ dataset ใหม่เพื่อปิด gate

Standalone 15 scenarios/300 graphs ที่เอกสารรายงานเป็น specification evidence ตามขอบเขตผู้เขียน หากมี script/results ให้แนบและ pin hash ไว้ แต่ไม่เรียกเป็น project integration tests การตรวจ 300 graphs ของรอบนี้ก็ยังไม่ใช่ 300 model tests หรือ complete evaluator certification

## 8. ขอบเขตการตรวจรอบนี้

- อ่าน appendix ครบ 396 บรรทัด เทียบ V2 review และ common metrics implementation
- ตรวจ primary source ของ Detectron2 และ SciPy ไม่ติดตั้งหรือ import Detectron2 เพื่อรัน model
- รัน real binary-mask matching check, 300 synthetic assignment graphs กับ oracle, per-person neighbor-class fixture และ bbox-vs-sparse-mask check เป็น CPU-only ไม่มี dataset inputs
- ไม่รัน tests 20/26 เดิมซ้ำ และไม่เพิ่ม claim ความพร้อมของ APr หรือ CCIHP official metrics
- เขียน review และ evidence record แยก ไม่แก้ appendix, V2, evaluator, GT, model adapters, study state หรือ YOLO artifacts ไม่รัน parser/download/benchmark

**คำแนะนำของผม:** รับแนวทางหลักของ appendix นี้ แล้วทำ config/evaluator/schema ที่ใช้จริงพร้อม bounded tests ในขั้นที่ได้รับอนุมัติ เติมความชัดเจนเรื่อง per-person FP, bbox semantics, availability และ failure unit ก่อน freeze งานต่อควรเป็น implementation ที่ตรวจได้มากกว่าการวนเขียนแผนฉบับใหม่ทั้งหมด
