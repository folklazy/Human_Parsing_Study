# ตรวจรอบด้าน: Human Parsing Benchmark Protocol — 20 variants, V2

วันที่ตรวจ: 14 ตุลาคม 2026 UTC · **REVIEW ONLY / NOT FROZEN / NO BENCHMARK STARTED**

แผนที่อ่านทั้งฉบับ: [Protocol V2](../../HUMAN_PARSING_BENCHMARK_PROTOCOL_20_VARIANTS_V2_TH_20261014.md) · [Review รอบก่อน](BENCHMARK_PROTOCOL_20_VARIANTS_REVIEW_TH_20261014.md)

**ความเห็นหลัก:** V2 แก้ข้อเสนอรอบก่อนอย่างมีสาระแล้ว ทั้งสถานะหลักฐาน, GT ที่ไม่มี semantic truth, T3a/T3b, runtime profiles และ selection/confirmation เหมาะใช้เป็นกรอบหลักต่อ ไม่ต้องออกแบบงานใหม่ทั้งหมด แต่ยังไม่ใช่ executable frozen protocol ต้องทำให้ข้อความ สูตร โค้ด และ prediction schema ตรงกันก่อนรันผลหลัก

จุดที่พบเพิ่มรอบนี้มีทั้งความไม่ตรงกันจริงระหว่างแผนกับโค้ด และรายละเอียดที่แผนประกาศ PENDING อย่างถูกต้องแล้ว สองประเภทนี้ไม่ควรถูกเรียกรวมว่าแผนผิด หรือใช้เป็นเหตุให้ทุก cohort ต้องหยุด

## 1. สิ่งที่ V2 แก้แล้วและควรรักษา

| เรื่อง | ความเห็น |
|---|---|
| ยกระดับ evidence จาก USER_REPORTED | ตรงกับหลักฐานจริง และแยกผู้ตรวจ/ขอบเขต verification ได้ดี |
| ไม่เริ่ม full audit/pilot ใหม่ | เหมาะสม งานเหลือเป็น specification และ application adapter gaps |
| G_native / G_loc / G_sem | ช่วยไม่ให้คนที่ไม่มี semantic GT ถูกลงคะแนน0 หรือหายจาก localization โดยไร้เหตุผล |
| Category22 และ Human>0/Category0 | แยก unresolved semantic domain จาก background พร้อมคง raw GT |
| T3b YOLO-gated association | ระบุ unmatched native/YOLO cases และไม่ใช้ GT ขณะ inference ชัดกว่ารอบแรก |
| Variant กับ complete system configuration | ถูกต้อง 20 checkpoints อาจมีมากกว่า20ระบบเมื่อ route/profile ต่างกัน |
| Sapiens2/CPI execution profiles | เปิดเผย native BF16 RoPE, offload control และ memory adapter โดยไม่เปลี่ยนประวัติ |
| Body/clothing เป็นผลหลัก | ไม่บังคับ universal foreground score ให้ครอบทุกตัวจนเสียคำถามวิจัย |
| VAL shortlist / independent confirmation | บทบาทชัดขึ้น และยังไม่แปลว่า benchmark ได้รับอนุมัติ |
| Optional datasets/metrics | ไม่ทำทุกอย่างให้เป็น prerequisite ช่วยให้ทดลองที่พร้อมเดินต่อได้ |

Counts ของ roster และ source populations ใน V2 สอดคล้องกับหลักฐานที่ตรวจรอบก่อน ไม่ได้พบเหตุให้เริ่มดาวน์โหลดหรือ re-audit ทั้งชุดในรอบนี้

## 2. สรุปประเด็นที่ต้องจัดลำดับ

| ประเด็น | ประเภท | ความสำคัญ | สิ่งที่แนะนำ |
|---|---|---|---|
| Maximum-weight vs cardinality-first matching | ข้อความไม่ตรงกับ evaluator เดิม | ต้องแก้ก่อน freeze matching | เลือก objective อย่างชัดเจน แยก application matching จาก native AP matching |
| Class set สำหรับ mIoU | แผนกับ generic aggregator ไม่ตรงกันทุกกรณี | ต้องแก้ก่อนใช้ primary scores | Pass fixed K explicitly และทดสอบ GT-absent/pred-present classes |
| APr ถูกวางร่วมกับ wrapper ที่ตรวจแล้ว | ขอบเขตความพร้อมเกิน implementation ที่พบ | ต้องแก้สถานะ metric | ปัจจุบัน wrapper มี APp/PCP/APp_vol; APr ต้องมี reference/implementation/parity แยก |
| Per-person valid domain / semantic aggregation | รายละเอียดที่ยังต้องกำหนด | ต้องแก้ก่อน person-level results | แยก image semantic, instance-accumulated semantic และ target-person scoring |
| Q_person_fg กับ person semantic quality | สูตร diagnostic ถูกหลัก แต่ยังตอบ semantic person quality ไม่ครบ | เพิ่มเมื่อใช้เลือก person-level parsing systems | รายงาน miss-inclusive person semantic mIoU ร่วม โดยกำหนด absent-class rules |
| T3b gates และ output accounting | แผนถูกทิศทางแต่ยังต้องมี outcome definitions | ต้องแก้ก่อนเปรียบเทียบ routes | แยก YOLO input opportunities, final emitted persons และ no-output events |
| Ownership ambiguity/void | ความเสี่ยงตอนต่อ adapter กับ evaluator | ต้องมี integration fixture | Prediction-derived ambiguity ห้ามลด GT evaluation domain |
| Multi-environment end-to-end execution | โครงระบบยังต้องระบุ | ต้องแก้ก่อนอ้าง live pipeline latency/VRAM | ระบุ processes, IPC, residency และ measurement boundary |
| Prediction schema / artifact storage | Schema เดิมยังไม่ครอบรายละเอียด V2 | ต้องแก้ก่อนสร้าง canonical benchmark artifacts | Versioned extension + storage budget + resume/checkpoint integrity |
| Statistics/confirmation/visual reporting | Governance ส่วนใหญ่เหมาะสมแล้ว | ล็อกให้พอสำหรับคำถามหลัก | อย่าเพิ่มทุก metric/dataset/pairwise test เป็นงานบังคับ |

## 3. Matching: ชื่อ objective เปลี่ยน Recall ได้

V2 §8.1 เสนอ maximum-weight matching บน edges ที่ผ่าน threshold ส่วน [match_persons เดิม](../src/evaluation/common_metrics.py) ใช้ **maximize eligible cardinality ก่อน แล้ว maximize sum IoU** สองแบบไม่เหมือนกัน

ตรวจด้วย synthetic edge-weight fixture ไม่ใช่ค่าจากภาพจริง:

```text
Threshold = 0.45
              Prediction A   Prediction B
GT 1              0.95           0.46
GT 2              0.46           0.00  (ineligible)
```

- จับ GT1–A คู่เดียว ได้ sum0.95
- จับ GT1–B และ GT2–A ได้สองคู่ แต่ sum0.92
- ถ้า objective คือ sum weight อย่างเดียวและอนุญาต unmatched คู่เดียวชนะ
- โค้ดเดิมเลือกสองคู่ เพราะ coverage/cardinality เป็น objective แรก

นี่เป็นตัวอย่างทางคณิตศาสตร์ของ assignment ไม่ได้อ้างว่า matrix นี้ถูกสร้างจาก GT masks จริง การทดสอบแยก objective ด้วย controlled weights และเรียกฟังก์ชันเดิมจริง

**ข้อเสนอ:** สำหรับ application localization/coverage ใช้ eligible-cardinality-first หากต้องการนับจำนวนคนที่จับคู่ได้มากที่สุด แล้วใช้ IoU/IDs เป็นลำดับถัดไป ถ้าตั้งใจใช้ weight-only ก็ทำได้แต่ต้องใช้ชื่อและ interpretation ให้ตรง ไม่เปลี่ยนโดย runner เดาเอง Threshold, box-vs-mask geometry, `>=`/`>` และ deterministic ties ต้องล็อก

Native AP ใช้ score-ranked matching ของ reference evaluator ตามนิยามเดิม ไม่แทนด้วย Hungarian/cardinality-first แล้วเรียกว่า official parity ส่วน inference association T3b อาจมี objective ต่างจาก evaluation matching ได้ แต่ต้องระบุทั้งสองแยก

## 4. mIoU: ฟังก์ชันเดิมยังไม่ใช่ aggregator ตาม V2 ทุกกรณี

V2 §8.2 เลือก K จาก foreground classes ที่มี GT support ใน population ที่ล็อก ส่วน `scores()` เดิมเฉลี่ย foreground classes ที่ union>0 ซึ่งรวมคลาสที่มีเฉพาะ prediction ด้วย

ตัวอย่างที่ตรวจจริง:

```text
GT:         [class1, background]
Prediction: [class1, class2]
K ของ population = {class1}; class2 ไม่มี GT support
```

- V2 fixed-K mIoU =1.00 พร้อม hallucinated class2 FP report
- `scores()` เดิม =0.50 เพราะเฉลี่ย class1 IoU1 และ class2 IoU0

สองนิยามมีเหตุผลของตัวเอง แต่เป็นคนละ metric การผ่าน tests เก่าไม่รับรองว่าค่าเท่ากับ V2 ควรให้ aggregator รับ explicit class indices/support policy และตั้งชื่อ metric ชัด

หากใช้ fixed GT-supported K ตาม V2 ต้องรายงาน hallucinated/UNMAPPED pixels และ foreground precision ร่วมจริง ๆ ไม่ซ่อนความผิดพลาดด้วยการตัด absent classes ออกจากคะแนน จากตัวอย่าง primary mIoU1.00 ไม่ได้หมายถึง prediction ถูกทุกพิกเซล

K ควรมาจาก required taxonomy ที่กำหนดด้วย TRAIN แล้วตรวจ support metadata ก่อน inference ไม่เปลี่ยน class definitions หรือใช้ VAL model scores เพื่อเลือก K ที่ทำให้โมเดลหนึ่งดูดี ใน bootstrap ต้องคง policy เดียวกัน รวมกรณี GT class หายจาก replicate และ union undefined

## 5. Foreground, global semantics และ person semantics ตอบคนละคำถาม

V2 บอกถูกแล้วว่า Q_person_fg ไม่แทน body/clothing mIoU จึงควรรักษาสูตร diagnostic นี้ ไม่เรียกเป็น semantic parsing quality

Synthetic fixture ที่ foreground ตรงแต่สลับ class1/class2 ให้ foreground IoU1.00 แต่ semantic mIoU0.00 จึงพิสูจน์เพียงความต่างของนิยาม ไม่ใช่ผลของโมเดลใน dataset

อีก fixture มีคนซ้าย/ขวา แต่ prediction แยกเป็น “ท่อนบนของทั้งสองคน” และ “ท่อนล่างของทั้งสองคน” เมื่อรวมภาพ global semantic mIoU1.00 ทั้งที่แต่ละ predicted instance มีชิ้นส่วนจากคนสองคน Per-person foreground IoU เป็น1/3 และ person semantic mIoU ภายใต้ declared pairing เป็น0.25

V2 ที่รายงาน global mIoU ร่วมกับ Q_person_fg สามารถเปิดเผยข้อผิดพลาดเช่นนี้ได้อยู่แล้ว สิ่งที่ผมเสนอเพิ่มคือ **person semantic score** เพื่อบอกโดยตรงว่าคนเล็ก คนที่ถูกบัง หรือคนที่พลาด มี body/clothing labels ถูกเพียงใด ไม่ให้ global pixel weighting ของคนใหญ่กลบคำถามนี้

Draft formula เมื่อจะใช้:

```text
Q_person_sem = sum(q_g for g in G_sem) / |G_sem|
q_g = declared per-person semantic mIoU, or 0 for an unmatched/no-output eligible GT
```

ต้องกำหนด q_g เรื่อง absent classes, prediction-only classes, background และ partial void ให้ชัด สูตรนี้เป็น study-specific ไม่ใช่ official metric และไม่แก้ extra-person errors ด้วยตัวเอง จึงยังต้องมี final-output precision/FP reporting

**ไม่จำเป็นต้องเพิ่มทุก metric ที่เป็นไปได้:** ถ้า research question คือ person-aware body/clothing ควรเลือก global common mIoU + person semantic/coverage + precision และ runtime เป็นผลหลักที่อ่านร่วมกัน ไม่รวมเป็น weighted overall score

## 6. GT domain: source counts ถูกแล้ว แต่ pixel semantics ต้องละเอียดอีกขั้น

การแยก G_native/G_loc/G_sem และห้ามลบ42จาก VAL17,548ตรง ๆ ใน V2 ถูกต้อง ขณะนี้มี per-split evidence สำหรับบางส่วนแล้ว: Category22 TRAIN261images/7,958pixels, VAL61images/310pixels; Human>0/Category0 TRAIN94,218pixels, VAL638pixels จึงใช้ ledger เติม sidecars ได้โดยไม่อ่าน masks ทั้งชุดใหม่

สิ่งที่ต้องล็อกเพิ่ม:

1. **Global image domain:** CCIHP มี single-valued category/human raster ใช้ known-label V ได้ แต่ C0/H0 คือ background ตาม annotation ไม่ใช่หลักฐานว่าทุกจุดไม่มี physical person หาก GT ไม่ annotate คนจริง prediction อาจถูกนับ unmatched/FP ภายใต้ benchmark policy ต้องใช้ถ้อยคำนี้แทนคำว่า “คนไม่มีอยู่จริง”
2. **Per-person domain:** นอก target person เป็นอะไร โดยเฉพาะบริเวณคนข้างเคียง? ถ้าวัด target ownership ต้องลงโทษ semantic pixels ที่ถูกมอบให้คนผิด แม้ class ของ pixels นั้นจะถูกสำหรับคนข้างเคียง ห้ามจำกัด domain เหลือเพียง target positives จน neighbor leakage ไม่ถูกคิด
3. **MHP overlap:** คง GT planes ไม่ flatten เป็น global map แบบ arbitrary หาก accumulate confusion ต่อ matched GT plane ต้องตั้งชื่อเป็น instance-accumulated semantic mIoU และรายงานว่าพิกเซลเดียวอาจมีหลาย person targets ไม่เรียกเหมือน image-level semantic aggregation โดยไม่อธิบาย
4. **Prediction-derived void:** `target_ownership()` เดิมมี ambiguity จาก predicted target/neighbor masks ซึ่งมีประโยชน์เป็น output status แต่ห้ามนำ ambiguity นั้นไปลบ GT domain รายโมเดล Native outputs คงไว้ ส่วน ambiguous predicted labels บน valid GT ต้องได้รับ disposition/error ตามกติกา ไม่เป็นช่องหลบ denominator
5. **GT ที่ไม่มี semantic truth:** หากอยู่ใน G_loc ให้ร่วม localization matching และรายงาน semantic undefined ไม่สร้าง free ignore region ที่ดูด unmatched predictions ได้ไม่จำกัด Duplicates และ invalid-geometry cases ต้องมี separate rules
6. **Foreground extent:** Human mask รวม accessories/carried objects ตาม release บางรุ่นไม่แสดงข้อมูลนี้ ต้องกำหนด geometry ที่ใช้ matching และ common foreground support ไม่ถือว่า native non-background ของทุก checkpoint มีขอบเขตเดียวกัน

การใช้ void policy เดียวกันทั้ง cohort ช่วย fairness แต่ยังต้องรายงานว่าทิ้ง classes/pixels/persons เท่าใด และสิ่งที่ทิ้งเกี่ยวกับโจทย์ clothing/accessories มากหรือไม่ Unknown/unsupported native predictions ที่ map ไม่ได้ต่างจาก invalid out-of-range decoder output ซึ่งควรเป็น contract failure

## 7. T3a/T3b: แยก person opportunity จาก person output

T3b YOLO-gated design ใน V2 มีเหตุผล และไม่ใช่ hybrid fusion ต้องเปิดเผยว่าระบบนี้สามารถทิ้ง native detections ที่ YOLO ไม่ gate ไว้ ผลนั้นเป็นข้อจำกัดที่ตั้งใจของระบบ ไม่ใช่ native parser Recall เต็ม

ควรมี counts แยก:

| รายการ | Denominator/ความหมาย |
|---|---|
| Upstream detector precision/recall | Shared YOLO predictions เทียบ G_loc |
| Parser/association execution | opportunities, attempted, valid outputs, no-associated/empty/failure |
| Final system precision/recall | Final emitted person instances หลัง routing/composition เทียบ G_loc |
| Semantic availability/quality | Eligible G_sem พร้อม miss-inclusive scores และ undefined ledger |

NO_OUTPUT ไม่ใช่ final emitted false-positive instance โดยอัตโนมัติ หาก YOLO box ผิดแต่ parser ไม่ส่ง person ออกมา ให้สะท้อน upstream FP และ routing status; final precision ใช้จำนวน final outputs จริง หาก boxนั้นตรง GT แต่ไม่มี parsing จะเป็น system miss และ semantic availability loss

เช่นเดียวกัน input YOLO duplicates ที่ระบบ suppress สำเร็จควรอยู่ใน upstream ledger แต่ไม่ลงโทษเป็น duplicate final output ที่ไม่ได้ส่งออกมา ต้องลงโทษ duplicate final instances ที่ยังคงอยู่จริง

T3a ต้องล็อกว่าจะคง YOLO person identity ทุก opportunity หรือ emit เฉพาะ nonempty semantic result T3b ต้องล็อก empty/suppression policy เดียวกับ final-output contract ไม่ให้แต่ละโมเดลเลือกตามคะแนน

Association, crop target selection และ overlap composition ใช้ predicted geometry/scores เท่านั้น ไม่ใช้ GT เลือกตัวที่ถูกที่สุด Mask/bbox differences, partial visibility และ neighbor contamination ต้องมี bounded TRAIN integration tests ก่อน full population

Native instance parsers, semantic-only full-frame parsers และ crop parsers ไม่ต้องมี routing เดียวกันทุกตัว เปรียบเทียบ complete configurations ที่ output task ตรงกันได้ แต่ไม่อ้าง input/architecture controls เหมือนกัน

## 8. Native metric readiness: แก้ APr ให้ตรง implementation

V2 §8.4 เขียน native MHP เป็น APp/PCP/APr ตาม wrapper ที่ตรวจแล้ว แต่ [wrapper ปัจจุบัน](../src/evaluation/official_mhp_compat.py) export APp, PCP และ APp_vol ที่ thresholds0.1..0.9 ไม่มี APr implementation หรือ APr parity evidence ใน wrapper นี้

แนะนำแก้แถวเป็น **APp / PCP / APp_vol ที่ wrapper รองรับ** ส่วน APr เป็น optional/native metric ที่ต้อง pin task-specific reference และทดสอบแยก [QANet paper](https://arxiv.org/abs/2103.05997) มี APr criterion แต่การปรากฏใน paper ไม่ได้ทำให้ wrapper ที่มีอยู่รองรับหรือรับรองอัตโนมัติ

26 tests จากรอบก่อนยังเป็นหลักฐานที่ใช้ได้ และรอบนี้ไม่รันซ้ำโดยไม่มีเหตุ เก็บไว้เป็น existing compatibility evidence ไม่ยกระดับเป็น complete CCIHP/common evaluation certification

## 9. Runtime architecture และ canonical schema ต้องตาม V2 ให้ทัน

### Process/environment boundaries

V2 นับ detector+parser+association ถูกแล้ว แต่ envs ที่ pilot ใช้ต่างกัน จึงต้องเลือก deployment execution ที่ทำได้จริง: compatible single process หรือ isolated worker processes ที่รับ RGB/crop metadata แล้วส่ง lossless outputs

ไม่จำเป็นต้องย้ายหรือแก้ working YOLO environment และไม่ควรสมมติว่าทุก parser import อยู่ใน Python processเดียวกับ YOLO ได้

Live timing ต้องรวม IPC/serialization/crop/map-back ตามระบบที่เลือก ใช้ wall-clock end-to-end พร้อม synchronization ของแต่ละ worker การวัด peak allocated ของ worker หนึ่งไม่ได้หมายถึง resident memory ของ YOLO+parser ทั้งระบบ และการบวก peak allocated จากคนละ RUN ไม่ได้ให้ simultaneous pipeline peak

ต้องกำหนด GPU-resident/offload/reload, warmup counts, repeated rounds, frame/person manifests, resolution/TTA, I/O boundaries และ external contention policy เป็นค่าจริงก่อน timing ไม่มีเหตุให้รันเมื่อเครื่องไม่ว่างหรือไปหยุด GPU jobs ของผู้อื่น

### Prediction schema

[Schema validator เดิม](../src/contracts/prediction.py) ใช้ tracks ORACLE_PERSON/YOLO26X_CONDITIONED/NATIVE_REFERENCE และ precision FP32/FP16/BF16 ไม่มี explicit T3a/T3b system profile จึงควรเพิ่ม versioned metadata โดยไม่ rewrite pilot records

แนะนำ fields: `system_id`, `routing_profile`, `execution_profile`, `adapter_revision`, `config_sha256`, `taxonomy_mapping_version`, `mask_grid_space`, component dtypes, source opportunity ID, native person ID และ final person ID

Validator เดิมคาด crop-sized maps เมื่อ crop_xyxy ไม่เป็น null แต่ application outputs อาจถูก mapกลับ full original image แล้ว ต้องประกาศ CROP/NATIVE/ORIGINAL grid space กับ transforms ให้ชัด ไม่ใส่ metadata ที่ดูครบแต่ array geometry ไม่ตรง contract

## 10. Storage/resume เป็นความเสี่ยงจริงเมื่อขยายจาก10เป็น5,000ภาพ

V2 ควรมี artifact retention/storage specification เพิ่มก่อน full run โดยคง lossless labels/instance IDs/scores/transforms ที่ต้องใช้ evaluator ไม่ใช้ overlays เป็น metric truth

จาก full audit CCIHP VALมี876,659,024sourcepixels หากเก็บ **full-original-grid FP32 logits**:

| Channels | Uncompressed bytes | GiB รวมทั้ง 5,000 ภาพต่อ variant |
|---|---:|---:|
|29|101,692,446,784|94.71|
|59|206,891,529,664|192.68|

สาม29-class variants รวมประมาณ284.13GiB ก่อน compression/metadata/native masks และไม่รวม outputs ของตัวอื่นหรือ per-person planes ตัวเลขนี้เป็นการคำนวณ storage scenario จาก source pixel counts ไม่ใช่ขนาดไฟล์จริงที่วัดจาก benchmark และไม่ได้สมมติว่าทุกรุ่นจำเป็นต้องเก็บ original-grid logits

`df -h` รอบนี้รายงาน available535G บน root filesystem เป็น snapshot ไม่ใช่การรับรองพื้นที่พอสำหรับทุก configuration การ compression/reduced native geometry อาจช่วยแต่ต้องวัด ไม่ assume compression ratio

ถ้า primary decoder คือ hard-label projection อาจเก็บ native lossless hard masks พร้อม identities/scores และ provenance ครบ ส่วน full logits เก็บ bounded diagnostic set หรือ native-grid outputs ตามสิ่งที่จำเป็นต่อการ reproduce decoder ต้องระบุข้อจำกัดว่าข้อมูลนั้นใช้ทดสอบ decoder ใหม่ใดไม่ได้ ไม่ลด precision ของ metric inputs โดยไม่เปลี่ยน profile

แนะนำ deterministic sequential runner, immutable run directories, atomic per-image writes และ resume ที่ตรวจ checkpoint/config/input/output hashes ก่อน reuse ไม่เก็บทุก logits/full-image GT ซ้ำแต่ละ run และไม่ overwrite pilot outputs

## 11. Taxonomy, selection และ uncertainty: เห็นด้วย แต่ไม่ขยาย scope โดยอัตโนมัติ

### Taxonomy

V2 ไม่แปลง Dress เป็น Upper/Lower ด้วย lookup และแยก anatomy-only ถูกแล้ว ก่อน freeze ควรมี numeric mappings สำหรับ eligible cohorts และ retained support ที่ตรวจจริง เพิ่มจากรายการแนวคิดที่มีอยู่

ตัวอย่างจาก native inventory: FASHN มี dress/hands/feet/belt/jewelry ส่วน Sapiens2 มี upper/lower clothing, apparel, face_neck และรายละเอียดปาก taxonomy ต่างกันจริง การมีชื่อ body/clothing คล้ายกันยังต้องตรวจ definitions [MSeg](https://arxiv.org/abs/2112.13762) ชี้ปัญหาจาก taxonomy และ annotation practices ที่ไม่สอดคล้องกัน งานนี้นำหลักการนั้นมาใช้ ไม่ได้แปลว่า MSeg รับรอง mapping ของ study โดยตรง

อย่าทำ universal taxonomy จนเหลือรายละเอียดต่ำกว่าความต้องการของผู้ใช้ หากมีหลาย cohorts ให้แจ้งสิ่งที่สรุปได้ภายในแต่ละ cohort และไม่เรียงคะแนนข้าม cohort เป็น overall winner

### Selection/confirmation

§11 เหมาะสม: TRAIN พัฒนากติกา, frozen VAL เปรียบเทียบ/shortlist เมื่ออนุมัติ, independent holdout ยืนยัน อย่ากลับไปตีความว่าห้ามเลือกโมเดลจากผล benchmark ตลอดไป

ถ้ายังไม่มี labeled independent holdout ก็รายงาน benchmark findings/shortlist ได้ โดยไม่อ้างยืนยัน performance ของ selected winner อย่างเป็นอิสระ [Cawley & Talbot](https://jmlr.org/papers/v11/cawley10a.html) สนับสนุนข้อควรระวังเรื่อง selection bias ไม่ได้บังคับให้งาน descriptive comparison ต้องหยุดจนได้ dataset ใหม่

Unlabeled CCTV ยังไม่มี quantitative accuracy โดยอัตโนมัติ และรอบนี้ไม่มีการอนุมัติ CCTV inference

### Statistics

20 variants ที่มีหลาย routes/profiles อาจมีมากกว่า 20 systems ต้องนับ selection candidates และ primary contrasts ตามระบบจริง ไม่ใช้จำนวน 20 เดิมบัง multiplicity ของ configurations

ทำ paired bootstrap ภายใน comparison key เดียวกัน ใช้ content clusters/sampling weights ตาม population กำหนด replicates, seed, undefined/support rules และ practical difference ก่อนผล ไม่ต้องเพิ่มทุก metric × ทุกคู่ ถ้ารายงาน descriptive CI โดยไม่อ้าง significance ให้ระบุเช่นนั้น

### Qualitative evidence

เมื่อรันผลหลักภายหลัง ควรมีภาพ same-frame พร้อม target IDs, full-frame + ROI และ GT/predicted boxes ที่บอกแหล่งชัด ใช้ preselected controls และ failure shortlisting ตามกฎ รวม common failures และ counterexamples ให้มีหลักฐานทั้งกรณีได้เปรียบและเสียเปรียบ การดู 10 TRAIN pilot มีประโยชน์ต่อ engineering แต่ไม่รองรับ population accuracy หรือ CCTV robustness

### Licensing/scope

V2 แยก technical pass กับ use eligibility แล้ว เหมาะสม รักษาหลักฐานและ scope assessment เดิม ไม่ทำ license audit ใหม่หรือให้ license blocker ของรุ่นเดียวหยุด eligible cohorts อื่น การ review นี้ไม่ให้สิทธิ์ execution เพิ่มเติม

## 12. ข้อเสนอสำหรับการปิดแผนก่อน freeze

ไม่ต้องเขียน scientific protocolใหม่ทั้งฉบับ แนะนำเพิ่ม **executable specification appendix** พร้อมconfig/referenceดังนี้:

1. Population/cohort/domain: exact manifest hash, K/numeric mapping, G_loc/G_sem, unknown/unsupported/invalid rules และ retained support
2. Matching/aggregation: objectives, thresholds, geometry, ties, absent classes, per-person negative pixels, overlap และ FP/no-output accounting
3. Application configurations: eligible T1/T2/T3a/T3b, GT-free routing/ownership, system_id และ actual checkpoint/profile
4. Runtime/artifacts: environment/process boundaries, residency, precision/TTA, timing manifests, storage budget, lossless output schema และ resume policy
5. Validation/authorization: required fixtures ผ่าน, scope และ selection population ชัด, ไม่มี score-affecting PENDING ใน track ที่จะรัน แล้วจึงขออนุมัติ benchmark

เริ่ม cohort ที่พร้อมได้เมื่อได้รับอนุมัติ ไม่ต้องให้ anatomy-only reference, optional native CIHP download, PartPQ หรือ external dataset ใหม่เป็น prerequisite ของทุกระบบ

## 13. หลักฐานและข้อจำกัดของ review รอบนี้

- อ่าน V2 ครบ 392 บรรทัดและเทียบ review เดิม, current active pilot validation, GT aggregate/semantic warning ledgers, common metrics, official MHP wrapper, prediction contract และ selected pilot scripts
- รัน existing MetricTests/MatchingOwnershipTests/PredictionContractTests: **20 tests PASS** เป็น synthetic/contract tests ไม่ใช่ parser inference หรือ dataset-wide benchmark
- รัน four bounded synthetic checks: assignment objective, foreground-vs-semantics, global-vs-instance quality และ fixed K-vs-generic aggregator ความต่างที่พบเป็น specification issues ไม่ใช่ข้อพิสูจน์ว่าผล benchmark เดิมผิด
- คำนวณ logit storage scenario จาก existing aggregate และตรวจ disk space ไม่อ่าน validation predictions หรือ GT masks ทั้งชุดใหม่
- อ้าง 26 tests จาก review ก่อนโดยไม่รันซ้ำ และไม่อ้าง APr/CCIHP certification ที่ไม่มีหลักฐาน
- เขียน review/evidence record แยกเท่านั้น คง V2 ต้นฉบับ ไม่แก้ evaluator/model adapters/datasets/YOLO artifacts/protocol state ไม่ดาวน์โหลดหรือติดตั้ง

**ข้อสรุป:** V2 เป็นแผนเตรียม benchmark ที่เหมาะสมขึ้นมาก เหลือการตัดสินและทำให้ implementations ตรง specification มากกว่าการหาข้อมูลใหม่ทั้งหมด ประเด็นที่ต้องปิดก่อนคือ matching objective, aggregation/GT domain, output accounting และ executable application profile ไม่จำเป็นต้องเพิ่มการทดลองจน scope กว้างกว่าคำถาม body/clothing/person-aware parsing ที่ตั้งไว้
