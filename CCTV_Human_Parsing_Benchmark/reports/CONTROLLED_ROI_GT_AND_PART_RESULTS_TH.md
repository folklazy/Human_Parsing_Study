# CCTV controlled ROI — ผลส่วนที่ตรวจได้และงาน GT Face/Neck ที่ยังเหลือ

ตรวจปิด work unit 2026-11-01T21:34:07.412255+07:00 (Asia/Bangkok). **NON_FACE_DIAGNOSTICS_COMPLETE_9_OF_9_FACE_GT_PENDING**.

รอบ person ROI มี predictions ครบ **9 checkpoints × 90 ภาพ / 130 frozen YOLO opportunities ต่อระบบ** แล้ว. รอบนี้ตรวจ RGB/source GT, ตรึง GT-only subset และคำนวณจาก saved masks ด้วย CPU เท่านั้น **model calls ใหม่ 0**. ได้ IoU/Dice ของ Hair/Upper/Lower ครบเก้าระบบ; **Face-domain และคะแนนรวมสี่ targets ยัง null** เพราะยังไม่มี annotation Face/Neck แยกที่ผ่านการตรวจ ไม่ประกาศผู้ชนะรวมจากสามส่วนแทนสี่ส่วน.

## ทำอะไรเสร็จแล้ว

- ตรวจ RGB กับ source GT ของ **127 person records / 32 หน้าภาพรวม** และ Face close-ups **35 รายการ** โดยไม่เปิด parser predictions มาช่วยตัด GT. ไม่มี owner conflict เพิ่มที่สังเกตพบหลังสอง correction เดิม; เป็น visual screen โดย Codex ไม่ใช่ independent expert certification.
- ใช้ owner corrections สองจุดใน derived copies เดิมเท่านั้น. Source annotations/masks ไม่เปลี่ยน. จำนวน grouped parts หลังแก้ owner เป็น **326**: Hair69 / Face35 / Upper120 / Lower102; ไม่ใช่ source324 หรือ old-primary315 โดยอัตโนมัติ.
- กำหนด **269 eligible non-Face parts** จาก source contours ที่ผ่าน GT-only screen: Hair61 / Upper112 / Lower96. อีก22 non-Face records มีเหตุเฉพาะด้าน semantics/contour และเก็บไว้ใน all-source sensitivity. ภาพยาก/เล็กไม่ได้ถูกตัดเพียงเพราะยาก.
- ตรึง GT binding และ protocol **ก่อนอ่านคะแนน ROI รอบใหม่นี้**. รู้ผล historical runs มาก่อนแล้ว จึงเป็น post-hoc review ไม่ใช่ blinded/preregistered confirmation.
- CPU acceptance **9 literal cases PASS** และ actual saved packet → projection → scorer → JSON/CSV ครบ810 frames. ตรวจ exact90 IDs/ระบบ, original-grid geometry, native IDs, frozen YOLO identity/extents/scores, atomic packet/GT bindings, per-frame record hashes และ aggregate arithmetic. ไม่เปิด GPU, ไม่ inference YOLO/parser และไม่แก้ frozen inference source/config/results.

หลักฐาน: [GT review](CONTROLLED_GT_SCREEN_SUMMARY.json), [CPU acceptance](CONTROLLED_ROI_SCORER_ACCEPTANCE.json), [derived result index](CONTROLLED_ROI_DIAGNOSTIC_INDEX.json), [ตารางเต็ม](../metrics/CONTROLLED_ROI_PART_DIAGNOSTICS.csv).

## ผลที่รายงานได้ขณะนี้

หน่วยในตารางเป็น **percent ของ mean per-GT-part IoU ภายใน target** เรียง frozen roster order. ไม่ใช่ global semantic mIoU20 หรือ pooled IoU. แต่ละระบบใช้ GT parts/domain/weights เดียวกัน. N/A หมายถึงยังไม่ได้ประเมิน Face-domain ที่ถูกต้อง ไม่ใช่ Face score0.

| Checkpoint | Frame packets | Hair (n61) | Upper (n112) | Lower (n96) | Face-domain | Macro4 |
|---|---:|---:|---:|---:|---:|---:|
| QANet_CIHP_HRNetW48_512x384 | 90/90 | 60.817 | 68.746 | 57.134 | N/A | null |
| M2FP_R101_CIHP | 90/90 | 48.990 | 56.264 | 46.032 | N/A | null |
| D2FP_R101_CIHP | 90/90 | 47.454 | 51.497 | 41.062 | N/A | null |
| RPR_CIHP | 90/90 | 43.918 | 51.482 | 41.940 | N/A | null |
| CPI_R50_CIHP | 90/90 | 41.730 | 39.992 | 35.993 | N/A | null |
| CPI_ConvNeXtB_CIHP | 90/90 | 59.795 | 53.832 | 44.967 | N/A | null |
| Sapiens2_0.4b | 90/90 | 65.746 | 62.330 | 53.818 | N/A | null |
| Sapiens2_0.8b | 90/90 | 60.770 | 60.281 | 55.198 | N/A | null |
| Sapiens2_1b | 90/90 | 67.152 | 66.044 | 58.919 | N/A | null |

ข้อมูลใน CSV เป็น fractions 0–1 ก่อนปัดเศษ; มี overall/day/night, mean-part Dice, TP/FP/FN/support/union และ pooled IoU/Dice ซึ่งเป็น metrics คนละ aggregation. มีทั้ง `GT_REVIEWED_DIAGNOSTIC` และ `ALL_SOURCE_NON_FACE_SENSITIVITY`; ห้ามนำแถวสอง subsets มาปนกัน. ยังไม่มี four-target overall winner หรือ final deployment acceptance.

ข้อสังเกตจำกัดในสาม targets ที่วัดได้: Sapiens2 1B มี mean-part IoU สูงสุดของ Hair และ Lower; QANet สูงสุดของ Upper. ไม่มี uncertainty study จึงไม่อ้าง statistical significance. ไม่ใช้ผลนี้เปลี่ยน GT/mapping/settings หรือแทนผล Face ที่ยังขาด.

## การจับคู่ ตัวหาร และ FP/FN

GT เป็นบางคน/บางส่วน ไม่ใช่ annotation ครบทั้งฉาก. ใช้ union ของ source parts หลัง owner correction เพื่อจับคู่กับ frozen YOLO bbox: coverage≥0.50, maximum cardinality แล้ว sum coverage; tie ตาม geometry/detector confidence กติกาเดิม. Matching ถูกตรึงครั้งเดียวร่วมทุกโมเดลและไม่ใช้ parser semantics. มี **20 GT-person records ที่ไม่จับคู่** และ1equal-objective ambiguity; ไม่ใช่ detector AP/full-person silhouette F1.

ต่อ annotated target ของคนที่จับคู่แล้ว ประเมิน **whole original-grid person plane**; ไม่ crop หรือ intersect prediction กับ GT bbox/polygon เพื่อซ่อน spill FP. GT person ที่ไม่จับคู่ตาม policy ใช้ empty prediction และ IoU0. ใน269eligible tasks มี detector-unmatched parts Hair5/Upper15/Lower14 ซึ่งยังอยู่ในตัวหาร. ฟิลด์ `detector_missed_parts` หมายถึง unmatched ตาม coverage/one-to-one policy รวมกรณีไม่มี eligible bbox หรือ competition; ไม่ใช่ข้อพิสูจน์ว่า detector ไม่เห็นคนนั้นทุกกรณี. GT support รวมตามลำดับ **232,447 / 861,845 / 327,214 pixels**. Person/target ที่ไม่ annotate ไม่ถูกสมมติเป็น full-scene negative task.

Native unions: CIHP Hair2, Upper5+7, Lower9+12; Sapiens Hair4, Upper23, Lower13. CIHP Dress6/Sapiens Apparel1 เป็น OTHER ไม่แบ่งด้วย heuristic. ทาย OTHER บน target เป็น FN; ทาย target นอก contour ของ annotated target เป็น FP บน fixed domain. Prediction255/unknown IDs เป็น contract failure; recognized OTHER ไม่ใช่ execution failure.

## ทำไม Face ยังไม่ปิด

Source label Face มีทั้งหน้า/คอ/ด้านข้างศีรษะตามภาพ และหลายภาพเบลอหรือถูกบังจนขอบ jaw/neck ไม่ชัด. การมี source polygon ไม่ได้พิสูจน์ anatomical Face/Neck partition. Screening แยก **11รายการที่ยังต้องวาด contour** และ **24รายการที่ต้องตัดสิน boundary ambiguity**; นี่เป็นคิวงาน ไม่ใช่การยืนยันว่า11รายการนั้น annotated เสร็จหรือ24รายการประเมินไม่ได้ตลอดไป.

ยังไม่ได้สร้าง positive Neck masks และ **ไม่ใช้ Neck=null เป็น zero-mask**. ไม่ใช้เส้นตัด/geometry heuristic, skin model หรือ predictions มาสร้าง GT. ด้วยเหตุนี้ไม่ใช้ source-Face agreement เดิมแทน neck-excluded Face, ไม่ประกาศว่าคะแนนรวมครบ และไม่ลบ Face requirement เพื่อให้ได้ผู้ชนะ.

กติกาที่คงอยู่จาก [controlled ROI protocol](../CONTROLLED_ROI_PROTOCOL_TH.md):

1. Annotate visible Face, Neck และ uncertainty แยกราย GT person จาก RGB/source annotation แล้ว review. หาก boundary ยังยืนยันไม่ได้ ให้คง pending หรือกำหนด GT-only uncertainty/eligibility พร้อมเหตุผลร่วมทุกโมเดลก่อน score.
2. Face-domain ใช้ prediction CIHP13 หรือ Sapiens3+24–28; valid grid ตัดเฉพาะ Neck/uncertainty ของ GT person นั้น. ไม่ ignore คอคนอื่น ไม่รับรอง deployable strict Face-only output.
3. Face+Neck delivery และ NeckCoverage เป็น supplementary; ต้องมี reviewed GT เช่นกัน. ไม่ split Face_Neck hard labels หรือรวม Torso-skin เพื่อสร้างคอ.
4. เมื่อ GT พร้อม สร้าง **new binding/version** พร้อม eligibility/support/domain hashes, ตรวจ actual Face packet → scorer → reporter แล้ว CPU score จาก masks ชุดเดิม. Scorer diagnostic version นี้ตั้งใจ refuse `Face_Neck_GT_complete=true`; ไม่มีการอ้างว่าผ่าน final Face integration แล้ว.

## เปิดหลักฐานภาพและส่งต่อ annotation

Private review package ที่มีจริง:

- `CCTV_Human_Parsing_Benchmark/outputs/gt-neck-review-20261101-inspection/index.html` — เปิด RGB close-ups35รายการและสถานะคิว ไม่มี parser predictions.
- ใน directory เดียวกัน: `persons_01.png` ถึง `persons_32.png`, `faces/`, `faces_close/`, `REVIEW_MANIFEST.json`, `FACE_CLOSE_MANIFEST.json`, `MANUAL_REVIEW_DRAFT.json`, `NECK_ANNOTATION_QUEUE.json`.
- GT binding ที่ตรึง: `outputs/controlled-gt-screen-20261101-bound/GT_BINDING.json`. มี per-part reasons, matches และ original/derived GT locations/hashes. Source masks คงเดิม.

ภาพ CCTV, filenames/roles/person records, annotations และ private galleries ไม่ขึ้น PUBLIC Git. ผู้ทำ annotation ต้องใช้ local/restricted package นี้; public clone ไม่มีข้อมูลพอทำงานภาพหรือ reproduce metrics ทั้งชุดจาก clone อย่างเดียว.

## บั๊ก scorer และการรักษาหลักฐาน

ครั้งแรก system Python ไม่มี NumPy จึงใช้ existing `.venvs/sapiens2-pilot/bin/python` โดยไม่ติดตั้งอะไร. จากนั้น CLI relative-path handling ผิดก่อนเขียน GT binding; แก้เฉพาะ scorer ใหม่และเก็บ attempt directory เดิมไว้.

CPU scoring attempt แรกได้หกระบบครบ แต่ RP-R-CNN/CPIสองตัวหยุดก่อน accept frame เพราะ scorer เข้าใจ continuation `models` list เป็น checkpoint dictionary. แก้ให้อ่าน exact checkpoint จาก hash-bound parent; ไม่แก้ model/config/predictions. ใช้ completed six results เดิมต่อและคำนวณเฉพาะสามระบบที่ยังไม่ผ่าน. Derived index ระบุ scorer revisions/accepted metric paths/hashes และเก็บ failed-to-score records ทุกครั้ง. ไม่เลือก result จากคะแนนดีที่สุด.

Assembly ตรวจ stored per-frame record hashes/exact membership และคำนวณ aggregate arithmetic จาก numeric rows อีกครั้ง โดยไม่เปิด NPZ scoring ทั้งชุดซ้ำ. Public derived index/CSV แสดง **null/empty สำหรับ Face-domain counts ที่ยังไม่วัด** แทน raw zero-item accumulator fields; อธิบาย normalization ไว้ชัดและไม่แก้ source METRICS/attempts ย้อนหลัง. ไม่มีการเติม score.

## ขอบเขตคำอ้างและขั้นต่อไป

ผลนี้คือ checkpoint + controlled application configuration comparison: crop/context/ownership จาก frozen YOLO เดียวกัน แต่ native resolution, normalization และ internal parsers ต่างกัน. YOLO clipping อาจจำกัดขอบเขตที่ทำนายได้. GT-only agent screening ยังไม่ใช่ independent expert gold; source garment boundaries/one-piece semantics มีข้อจำกัด. ไม่อ้าง full-scene accuracy, architecture-only effect, color quality, หรือ production CCTV acceptance. ไม่จัดอันดับ timing/FPS/VRAM เพราะต้นทุนและสภาพ shared GPU ต่างกัน.

**ขั้นถัดไปที่เหลือจริง:** annotate/adjudicate Face/Neck35รายการจาก private review package → freeze GT revision/domain/eligibility ใหม่ → targeted Face integration acceptance → CPU Face scoring + macro4 จาก saved predictions → final four-target report. ไม่ต้อง inference เก้าระบบใหม่เพียงเพื่อแก้ GT. ตอนนี้ไม่มีคิว GPU รอหรือ permission ให้เปิดงานอื่นอัตโนมัติ.

Source working copy คือ `CCTV_Human_Parsing_Benchmark/`; public publication checkout คือ `Human_Parsing_Study_Public/`. Sync เฉพาะ approved source/protocol/aggregate docs/tables ตาม path/hash manifest; datasets/weights/environments/predictions/annotation queue อยู่ภายนอก Git. CPU dependencies ที่สังเกตจริงอยู่ [requirements-cpu.txt](../requirements-cpu.txt); synthetic commandอยู่ใน acceptance JSON. วันที่/commit รอบนี้เป็น post-scoring documentation snapshot ไม่ใช่ launch commit ของ model inference.
