# ข้อเสนอพร้อมรับรอง — กลุ่มแรก CPI × T3b

**READY FOR POLICY REVIEW · ไม่ freeze · ไม่อนุญาต full benchmark**

เอกสารนี้เสนอค่าจริงของกลุ่มแรก **CPI_R50_CIHP และ CPI_ConvNeXtB_CIHP เท่านั้น** ใน T3b: full-frame native parsing + frozen YOLO26x association ไม่ขยาย roster ไม่รันโมเดลเพิ่ม ไม่ใช้คะแนน validation เลือกนโยบาย และไม่เปิด audit ทั้งโครงการใหม่

ค่าที่เสนออยู่ใน [executable config V6](../configs/application_v2_first_cohort_v6.yaml) และมี bindings ใน [decision record V5](../provenance/APPLICATION_V2_DECISIONS_V5.json) **ห้าข้อใหม่ยังเป็น PROPOSED** สองนโยบายเดิม STRICT_COMPLETE/checkpoint-specific cohorts ยัง ACCEPTED ตามเงื่อนไขเดิม การรับรองชุดนี้ในภายหลังไม่ใช่การอนุมัติ full benchmark

## 1. ห้าข้อที่เสนอให้รับรอง

| ข้อ | ค่าที่เสนอ | หลักฐาน | ข้อจำกัด | สิ่งที่ยังขาดเฉพาะจุด |
|---|---|---|---|---|
| Mapping | 6 foreground targets + BG; coarse selected-garment union; projections ของ CIHP20 ผูกสอง checkpoint แยกกัน | ตารางครบ 63rows, creator README, CIHP catalog, configs/head/unchanged-ID loader และ actual checkpoint load | เป็น common-task projection; ไม่ใช่ native CIHP equivalence หรือ fine clothing/accessory benchmark | รับรอง coarse unions/exclusions; direct CPI training-JSON class-name header ยังไม่มีใน local assets ตามข้อ 3 |
| GT domain | Released-annotation-relative; BG เฉพาะ Category0/Human0; unknown22, Human>0/Category0 และ outside-task labels เป็น shared VOID | Full structural audit เดิม, source hashes และ GT projection ที่ตรวจแล้ว | ไม่รับรองว่าคนจริงทุกคนถูก annotate; FP เป็น annotation-relative | รับรอง domain/wording นี้; ไม่ต้องทราบความหมาย 22 เพื่อเก็บเป็น unknown แต่ห้ามอ้าง native full-label score |
| Population | Main=controlled4,961; reference=source5,000; รายงานแยก | Manifests/sidecars เดิมที่ hash ตรง ไม่ recount | ควบคุมเฉพาะ exact TRAIN RGB reuse; ยังมี within-VAL repeats/near-duplicate risk/unknown exposure | รับรอง main/reference roles; ไม่มี exclusions ใหม่ให้เลือกย้อนหลัง |
| Matching | Association bbox IoU≥0.50; final↔GT bbox IoU≥0.50 primary/0.75 secondary; native parser evaluation box | Existing matching tests + actual T3b TRAIN route | เป็น study-specific geometry rule ไม่ใช่ official MHP/CIHP protocol; coarse/native boxes อาจมีข้อผิดพลาด | รับรอง thresholds/box source และ native default score filters ก่อนดูคะแนน |
| Runtime | **Quality-only first comparison**, FP32; ไม่จัดอันดับ latency/FPS/VRAM หรือ cost Pareto | Actual engineering smoke/profile ยืนยัน feasibility เฉพาะที่รัน | ไม่ตอบว่าใครเร็ว/ประหยัดกว่า; joint-resident throughput ยังไม่ได้วัด | รับรองขอบเขตคำอ้างคุณภาพ; ถ้าจะอ้างต้นทุนต้องอนุมัติ profile และ clean repeats แยก |

คำว่า evidence assembled หมายถึงหลักฐานพร้อมให้ประเมิน ไม่ใช่ semantic acceptance โดยอัตโนมัติ ไม่ใช้ test count, protected hashes หรือจำนวนลิงก์แทนการตัดสินใจห้าข้อนี้

## 2. ตรวจความหมายของ common context จากโค้ดแล้ว

| สิ่งที่ตรวจ | ผลจาก source ปัจจุบัน |
|---|---|
| `mapping_sha256` ตรงกัน | เป็น hash ของ bundle ซึ่งมีหลาย native projections; CIHP10→Exposed_torso แต่ LIP10→Garments_coarse ได้ ไม่ได้บังคับ native class10 มีความหมายเดียวกัน |
| Native mapping แต่ละ checkpoint | กลุ่มนี้ทั้งสองเป็น CIHP20 และใช้ rules ชุดเดียวกันโดยมี binding แยก checkpoint; การใช้ไฟล์ mapping อิสระราย checkpoint ยังไม่รองรับและไม่จำเป็นสำหรับคู่นี้ หากจะเพิ่มภายหลังต้อง version contract |
| `domain` เท่ากัน | เทียบ common policy metadata ไม่เคยเปรียบเทียบ pixel masks ของคนละภาพให้เท่ากัน |
| Same-image GT/domain binding | เพิ่ม `domain.image_binding`: image ID, G_loc/G_sem และ source/projection/domain recipe hash ต้องตรงกันข้ามระบบ |
| คนละภาพ | image binding, resolution, domain mask และจำนวน GT แตกต่างได้ตาม source ของภาพนั้น |
| Checkpoint/config | คงเดิมภายในระบบเดียวข้ามภาพ แต่สองระบบมี checkpoint/config ของตนเอง |

V6 กำหนด `require_per_image_GT_domain_binding=true` เมื่อจะ materialize accepted registry ต้อง derive binding จาก source-map hashes ของแต่ละ image ไม่คัดลอก mask เดียวไปทุกภาพ ตัวอย่างและสูตรอยู่ใน [per-image recipe](../provenance/RUN_MANIFESTS/first-cohort-t3b-submission-20261016T032428703965Z/PER_IMAGE_BINDING_RECIPE.json) recipe hash **ไม่ใช่** hash ของ decoded valid-mask bytes; ขั้น reconstruct GT ต้องตรวจ source fidelity ด้วย

แก้เฉพาะ [contexts.py](../src/application_v2/contexts.py) และเพิ่มสอง regression cases ที่ตรงปัญหา: คนละภาพมี domain/counts ต่างกันได้ และภาพเดียวกันต่างระบบห้าม binding ต่าง/ขาด ไม่เพิ่มความสามารถเพื่อให้ทุก roster พร้อม

## 3. Mapping semantics: source → target → evidence → limitation

Target0=reference BG; 1=declared Face region; 2=Torso-skin; 3=left/right naked-arm union; 4=naked-leg union; 5=selected garments; 6=left/right shoe union ไม่มี independent hand/bare-foot/headwear/accessory score ในกลุ่มนี้

**Selected garments:** GT5,7,8,9,11,12 เทียบกับ CIHP prediction5,6,7,8,9,11,12 รวม socks/scarf โดยตั้งใจเพราะเป็น clothing regions และรวม Dress prediction กับ upper/skirt GT เพื่อไม่สมมติ category6 เท่ากัน ไม่ใช่การอ้างว่า jacket/dress/skirt boundaries เดิมเหมือนกันทุกพิกเซล

ตารางนี้ใช้กับทั้งสอง checkpoint แยกตาม [checkpoint bindings](../provenance/RUN_MANIFESTS/first-cohort-t3b-submission-20261016T032428703965Z/CHECKPOINT_BINDINGS.json) ส่วน [CSV ครบ 63 แถว](../taxonomy/FIRST_COHORT_CPI_SOURCE_TO_TARGET_V1.csv) มี 40 prediction rows และ 23sharedGT rows พร้อม source evidence/limitations รายแถว

| ID | CCIHP GT → disposition/target | CPI CIHP prediction → disposition/target | หลักฐานและข้อจำกัดเฉพาะ |
|---:|---|---|---|
| 0 | Reserved zero; background/unknown policy under review → 0 | Background → 0 | E1+E3; source zero ต้องแยกตาม Human ID |
| 1 | Hat → VOID | Hat → OUTSIDE_TARGET | E1/E2; excluded fixed task |
| 2 | Hair → VOID | Hair → OUTSIDE_TARGET | E1/E2; excluded fixed task |
| 3 | Glove → VOID | Gloves → OUTSIDE_TARGET | E1/E2; gloves excluded, no hand-only score |
| 4 | Sunglasses/Glasses → VOID | Sunglasses → OUTSIDE_TARGET | E1/E2; eyewear excluded |
| 5 | UpperClothes → 5 | UpperClothes → 5 | E1: top of dress อยู่ upper; E2 CIHP upper |
| 6 | Face Mask → VOID | Dress → 5 | E1 Face Mask ≠ E2 Dress; ห้าม identity mapping |
| 7 | Coat → 5 | Coat → 5 | E1 coat มี outermost sweater/vest ด้วย; coarse merge ไม่อ้าง fine equivalence |
| 8 | Socks → 5 | Socks → 5 | รวม socks เป็น garments โดย study design |
| 9 | Pants → 5 | Pants → 5 | E1 รวม shorts/tights/leggings; coarse target |
| 10 | Torso-skin → 2 | Torso-skin → 2 | E1/E2 Torso-skin; ไม่ใช่ LIP Jumpsuits |
| 11 | Scarf → 5 | Scarf → 5 | E1 รวม ties/bow ties; coarse merge |
| 12 | Skirt → 5 | Skirt → 5 | E1 รวม bottom of dress; coarse merge |
| 13 | Face → 1 | Face → 1 | source Face region; ไม่รับรอง pixel-identical exposed-skin convention |
| 14 | Left-arm (naked part) → 3 | Left-arm → 3 | E1 naked part; merge left/right; no independent hand class |
| 15 | Right-arm (naked part) → 3 | Right-arm → 3 | เช่นเดียวกับ 14 |
| 16 | Left-leg (naked part) → 4 | Left-leg → 4 | E1 naked part; socks ไม่ใช่ exposed leg |
| 17 | Right-leg (naked part) → 4 | Right-leg → 4 | เช่นเดียวกับ 16 |
| 18 | Left-shoe → 6 | Left-shoe → 6 | E1/E2 shoe; left/right รวม; no bare-foot score |
| 19 | Right-shoe → 6 | Right-shoe → 6 | เช่นเดียวกับ 18 |
| 20 | Bag → VOID | ไม่มี source label | E1 Bag; CPI20-label ไม่มี corresponding class |
| 21 | Others → VOID | ไม่มี source label | E1 Others เป็น heterogeneous accessories; ไม่เดาความหมาย |
| 22 | UNDEFINED_RELEASE_ID_22 → VOID | ไม่มี source label | E3 พบจริงแต่ E1 ไม่กำหนด; unknown/sharedVOID |

**E1:** [creator CCIHP README](../provenance/RUN_MANIFESTS/stage0e-ccihp-native-20261012T045912Z/archive_documents/README.md) อธิบาย category/person/attribute semantics; **E2:** [pinned CIHP catalog](../../third_party/human_parsing/M2FP/m2fp/data/datasets/register_cihp_parsing.py) และ CPI config20 / [unchanged-ID parsing loader](../../third_party/human_parsing/CPI-Parser/mmdet/datasets/pipelines/loading.py); **E3:** [full structural audit](CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md) บันทึก labels/support จริง

**จุดที่ยังขาดมีสองอย่างที่ต้องแยกกัน:** (ก) ID22 ไม่มีนิยามจากผู้สร้าง จึงไม่มี target ที่พิสูจน์ได้ แต่เสนอ shared VOID อย่างเปิดเผยได้ใน known-label task นี้; (ข) CPI อ่านชื่อ parsing classes จาก `categories[].parsing` ใน training annotation JSON ซึ่งไม่มีใน checkout ปัจจุบัน ชื่อ channel ใน smoke manifest มาจาก standard CIHP inventory ไม่ใช่หลักฐานอิสระจาก weights เอง หลักฐาน order ตอนนี้เป็น published CIHP checkpoint + 20-class config + loader ที่ไม่ remap IDs + standard CIHP catalog ถือเป็น indirect evidence ที่ต้องเปิดเผย ไม่อ้างว่าอ่าน training header แล้ว ดู [dataset loader ทางการที่ pinned commit](https://github.com/HAG-uestc/CPI-Parser/blob/d62cae523ba913fec4a7fda5816bc1d96bbf644d/mmdet/datasets/cihp.py) และ [evaluator ที่อ่านชื่อจาก JSON](https://github.com/HAG-uestc/CPI-Parser/blob/d62cae523ba913fec4a7fda5816bc1d96bbf644d/utils/eval.py)

ไม่มีแถวที่ต้องเดา target ของ 22 หรือบังคับ FaceMask→Dress หากต้องการ direct checkpoint-channel certification ให้ตรวจเฉพาะ original CPI annotation JSON **header** หรือคำยืนยันผู้สร้างในงานต่อ ไม่จำเป็นต้องดาวน์โหลด dataset ใหม่หรือ audit ทุกโมเดล และห้ามถือ user acceptance เป็นหลักฐานว่า header ตรงแล้ว

## 4. Released-annotation-relative GT domain ที่เสนอ

| Pixel condition | Policy เดียวกันทุกระบบ | เหตุผล/ข้อจำกัด |
|---|---|---|
| Category0/Human0 | BG0 valid เทียบ released reference | ไม่ใช่คำรับรองว่าไม่มีคนจริงใน RGB |
| Human>0/Category0 | VOID_UNKNOWN | ไม่มี known semantic class; ยังเก็บ Human ID ใน G_loc |
| Category22 | sharedVOID/raw22 retained | ความหมายไม่ทราบ; ห้าม 22→BG |
| Documented labels นอก target:1,2,3,4,6,20,21 | sharedVOID | เป็น fixed task exclusion; ต้องรายงาน retained coverage/label list ไม่เรียก fullCCIHP/nativeCIHP score |
| Target1..6 owned by this Human ID | GT target class valid | ใช้ original-grid masks |
| Known target ของคนอื่น | negative สำหรับ target-person บน shared valid domain | ตรวจ neighbor contamination เทียบ released ownership |
| Positive category/Human0 | VOID_OWNER_UNKNOWN | audit เดิมพบ 0; rule ไม่สร้าง identity ด้วย heuristic |
| Invalid decoder ID | CONTRACT_FAILURE | ไม่แปลงเป็น ignore เพื่อหลีกเลี่ยงคะแนนต่ำ |

E3 เดิมพบ VAL unknown22 **310 pixels**, Human>0/Category0 **638 pixels** ไม่มีการอ่าน GT ใหม่เพื่อหาตัวเลขนี้ และไม่มี source repair การตั้ง benchmark annotation-relative แก้ความเกินขอบเขตของคำอ้าง known-negative ไม่ได้พิสูจน์ annotation completeness หรือ physical ownership ทุกตัวอย่าง

**G_loc:** ทุก positive native Human ID ที่มี nonempty mask ใช้ bbox จาก Human-ID foreground ทั้งหมด รวม labels นอก target ไม่คำนวณ bbox จากเฉพาะ target ที่โมเดลทายได้ **G_sem:** subset ที่มี target1..6 อย่างน้อย 1validpixel 44native IDs ไม่มี candidate support ยังอยู่ G_loc (9 ไม่มี native known support +35knownlabels นอก candidate)

ใช้ metric เดิม `Q_person_sem_GT`: ค่า IoU เฉลี่ยของ GT-supported target classes รายคน แล้วเฉลี่ยทุก eligible GT person; missed G_semperson ได้ 0; คนที่ไม่มี semantic support เป็น undefined และยังรับ localizationFN ตามจริง ไม่เรียกค่านี้ global pooled mIoU หรือ official AP/PCP Metric อื่นและ diagnostics เดิมไม่ถูกเพิ่ม/เปลี่ยนเพื่อเลือกผู้ชนะ

`STRICT_COMPLETE` ยังคงใช้ทั้ง comparison population หากรันไม่ครบไม่มีคะแนนหลัก ระบบยังอยู่ในตารางพร้อม diagnostics; valid empty เป็น execution success และรับ misses ตาม GT **FP หมายถึง unmatched prediction เทียบ released annotations ภายใต้ matching/domain policy นี้** ไม่แปลว่าทำนายคนที่ไม่มีอยู่จริง

## 5. Population: เสนอ controlled เป็น main และ source เป็น reference

| Role ที่เสนอ | Existing population | Images | G_loc | G_sem |
|---|---|---:|---:|---:|
| Main | overlap_controlled_source_target | 4,961 | 17,434 | 17,390 |
| Reference | original_source_target | 5,000 | 17,548 | 17,504 |

เหตุผล: สอง checkpoint ประกาศ CIHP training exposure และ CCIHP ใช้ CIHP RGB การแยก 39validation IDs ที่มี decodedRGB ตรง TRAIN ออกใน main ลดความเสี่ยงที่ตรวจพบได้โดยไม่ใช้ model scores Full5,000 ยังเก็บเป็น source-reference แยกตาราง ไม่แก้ officialsplit และไม่รวมคะแนนสอง populations เป็นเงื่อนไขเดียว

[Population bindings](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/POPULATION_BINDINGS_DRAFT.json) อ้าง ordered frame manifests และ person sidecars ด้วย SHA256 เดิม รอบนี้ตรวจ identity เท่านั้น **ไม่ recount** และไม่เพิ่ม exclusions

ยังคง within-VAL duplicate1group/2IDs ตาม source; 114non-exact near-duplicate candidate pairs เป็น risk screen ไม่ใช่รายการคัดออก ทั้ง controlled population ไม่รับรองว่าไม่มี exposure จาก pretraining, checkpoint selection, near-duplicates หรือการรั่วรูปแบบอื่น และไม่ทำให้ 33ksource IDs เป็น independent statistical samples

## 6. Matching และ native settings ที่เสนอให้ใช้จริง

| ขั้น/setting | ค่าเสนอ | เหตุผลก่อนดูคะแนน | ข้อจำกัด |
|---|---|---|---|
| Prediction-only T3b association | bboxIoU≥0.50; eligible-cardinality ก่อน sumIoU | ต้องมี spatialagreement ระดับหนึ่งและ reuse กลไกที่ทดสอบ/actualTRAIN แล้ว; GT ไม่เป็น input | เป็น studychoice ไม่ใช่ threshold ที่พิสูจน์ว่า optimal |
| Final prediction↔GT | bbox IoU≥0.50 primary; 0.75 secondary | แยก coverage จาก class-mask quality; 0.75 ใช้แสดง sensitivity | ไม่เลือก threshold ที่ให้คะแนนดีกว่าหลังเห็นผล |
| Evaluation bbox | original-grid native CPI predicted box | แยก parser localization จาก YOLO conditioning box; ไม่ recompute จาก mapped classes | อาจมี localization error ของ native detector |
| GTbbox | tight half-openbbox จาก originalHumanID ทั้งหมด | เก็บ source person geometry ไม่เลือกจาก modelcapability | ไม่ใช่ human-certifiedanatomicalbox |
| Tie/assignment | cardinalityfirst→sumIoU; immutableIDsort; pinnedSciPy1.15.3 | permutationfixtures เดิมรองรับ | ไม่อ้าง universallexicographictie ทุก solverversion |
| YOLO | frozen checkpoint; imgsz640, conf0.25, NMS IoU0.70, maxDet200, retina_masks, FP32 | reuse actual route configuration ก่อน quality scores | ยังไม่พิสูจน์ความเหมาะสมกับ CCTV หรือทุกขนาดคน |
| NativeCPI | officialcheckpoint-specificconfig: R50score_thr0.01;ConvNeXtB0.05;max_per_img100;native1333×800keep-ratio;FP32 | รักษา nativebehavior ไม่ tune จาก CCIHPVAL | เป็น configurationcomparison ไม่ใช่ controlledarchitecturecomparison |
| Visualization | displaycompositionthreshold0.2 ไม่เป็น metricfilter | losslessnativeinstances เก็บแยกจาก overlay | ภาพ overlay ไม่ใช่ metrictruth |

Association0.50 และ GTmatching0.50 เป็นคนละ parameter แม้ค่าเท่ากัน; GTmatching0.75 ไม่เปลี่ยน association. Retain ทั้ง native instance ID และ YOLO opportunity ID Final persons เฉพาะ matchedassociation; unmatchednative และ unmatchedYOLO รายงานเป็น associationdiagnostics ไม่แอบนับ native ที่ถูก YOLOgate ออกเป็น finalFP

Unmatched final prediction เป็น annotation-relativeFP; unmatched GT เป็น FN และ semantic0 ถ้าอยู่ G_sem คน G_semundefined ยังอยู่ G_loc Nativeoutput ที่ empty อย่างถูกต้องไม่ใช่ failure ไม่ retry หลังเห็นผล กรณี YOLOopportunities0 ใช้ routing ปัจจุบันที่ยังรัน native ได้ แต่ final YOLO-gated persons0, opportunity rateundefined และ GT misses ตามประชากร

## 7. Runtime: เลือก quality-only ในกลุ่มแรก

เสนอให้วัด/เปรียบเทียบคุณภาพก่อนโดย **ไม่เพิ่มการอ้าง latency/FPS/VRAM ranking หรือ costPareto** ใน comparisonrevision นี้ Profiles เดิมใช้ยืนยันว่า actualroute รันผ่านบน T4FP32 ใน TRAIN หนึ่งภาพ ไม่ใช้ cold process wall time หรือ peak คนละ process อ้าง jointmemory

ถ้าจะเปรียบเทียบต้นทุนภายหลัง ต้องออก cost-profiledecision ที่ระบุ sameworkload/personcount, sequential หรือ jointresidency, stageboundaries, warmups, synchronization, repeatedcleanrounds และ contentionpolicy แล้วรัน cleanmeasurements ที่อนุมัติแยก ไม่ต้องรัน 21checkpoints ซ้ำเพื่อปิดกลุ่มนี้

## 8. ขั้นรับรองและงานถัดไปที่มีขอบเขต

1. Review/รับรองค่าห้าข้อใน configV6 พร้อมรับทราบ source-channel-order evidence gap และ sharedVOID ข้อจำกัด ไม่ถือว่าการรับรองได้สร้างหลักฐานที่ยังไม่มี
2. **แนะนำให้ปิด direct CPI channel-header verification ก่อนให้ checkpoint semantic binding เป็น VERIFIED:** ตรวจเฉพาะ header ของ annotation JSON ทางการ หรือคำยืนยัน class order จากผู้สร้าง ไม่ต้องดาวน์โหลดภาพ/GT ทั้งชุด หากหาไม่ได้ให้รักษาสถานะ indirect evidence และนำกลับมา review เฉพาะจุดนี้ ไม่ถือว่าการรับรอง policy ได้พิสูจน์ header แล้ว
3. หลังรับรอง policy สร้าง versionedacceptedmapping/domain/populationcontexts ของสอง checkpoint จาก sources ที่ผูก hash ตรวจ actualGTreconstruction และ per-imagebindings โดยยังไม่รัน VALmodelinference
4. ขออนุมัติ fullbenchmark แยกเมื่อ readiness ของกลุ่มนี้ผ่าน ไม่ใช้การผ่าน review/fixtures เป็นสิทธิ์เริ่มอัตโนมัติ

Cached scorer / workflow resume และความพร้อมโมเดลนอกกลุ่มไม่เป็นเงื่อนไขให้ขยายงานรอบนี้ Full benchmark, training, hybrid, color, PPSS และ CCTV ไม่เริ่ม

## 9. Evidence ของรอบนี้

[Submissionmachine-record](../provenance/RUN_MANIFESTS/first-cohort-t3b-submission-20261016T032428703965Z/SUBMISSION.json), [targetedcontextaudit](../provenance/RUN_MANIFESTS/first-cohort-t3b-submission-20261016T032428703965Z/CONTEXT_SCOPE_AUDIT.json), [validation/logs/source diff](../provenance/RUN_MANIFESTS/first-cohort-t3b-submission-20261016T032428703965Z/validation/VALIDATION.json), [source diff](../provenance/RUN_MANIFESTS/first-cohort-t3b-submission-20261016T032428703965Z/validation/CHANGES.diff)

Validation แยกหน้าที่: regressiontests ตรวจ behavior ที่ทดสอบ; source/protectedhashes ตรวจ preservation เฉพาะไฟล์ที่ระบุ; links ตรวจการเข้าถึงเอกสาร **ไม่มีอย่างใดแทน semantic/domainacceptance** รอบนี้ไม่มี modelinference/download/installation หรือ datasetmodification
