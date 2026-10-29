# CIHP–Sapiens C4-P full evaluation — สถานะและผลจริง

อัปเดต 2026-10-29T13:57:33.203732+07:00 Bangkok UTC+07 · run `common-c4p-full-20261029T063458522990Z` · **2/5 ระบบ COMPLETE**

## ขอบเขตและวิธีทดลอง

ผู้ใช้อนุมัติ QANet/M2FP/D2FP/RP-R-CNN จาก saved artifacts เท่านั้น และ Sapiens2 segmentation 0.4B บน official CIHP validation 5,000 IDs. ใช้ [full config](../configs/cihp_sapiens_c4p_full.json), [revision-2](../protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json), [freeze](../runs/common-c4p-full-20261029T063458522990Z/FREEZE.json). ไม่ inference สี่โมเดลหรือ YOLO ใหม่ ไม่เริ่ม CPI/0.8B/1B/training/color/CCTV

Native20 results คงเดิมที่ [รายงานสี่โมเดล](CIHP_FOUR_MODEL_RESULTS_TH.md) ตารางนี้เป็น common view ใหม่ ห้ามเทียบตัวเลขข้ามนิยามโดยตรง. C4-P เฉลี่ย Face proxy/Hair/Upper non-Dress/Lower non-Dress เท่ากัน C3 เป็น global mean Hair/Upper/Lower เท่านั้น ไม่มี Q_C3. Compose native planes ก่อน projection; BG/OTHER valid, GT255 shared VOID, prediction255/unknown เป็น contract failure. Dress/Apparel เป็น OTHER ไม่แบ่งด้วย geometry หรือ void ตามโมเดล.

Global CIHP confusion20×20 projected หลังตรวจ pixel equivalence บน fixed ambiguity examples; person metrics คำนวณใหม่จาก saved planes/extents/scores ด้วย geometry-canonical revision2 matcher ทั้ง 0.50/0.75 ไม่คัดลอก scalar native scores. G_loc=17,520, G_sem_C4=17,454 ตรวจจาก bound GT-only manifest; ใช้ fixed GT domain ข้ามระบบ

## สถานะและคะแนนที่มีสิทธิ์

เรียง roster order, IoU ในตารางเป็นเปอร์เซ็นต์; CSV/JSON เก็บ fraction0–1 และ null/ช่องว่างเมื่อยังไม่ครบตาม STRICT_COMPLETE

|ระบบ|สถานะ|Complete/expected|C4-P mIoU4 (%)|C3 global (%)|
|---|---|---:|---:|---:|
|QANet_CIHP_HRNetW48_512x384|COMPLETE|5000/5000|80.984|78.747|
|M2FP_R101_CIHP|COMPLETE|5000/5000|83.623|82.127|
|D2FP_R101_CIHP|PENDING|0/5000|null|null|
|RPR_CIHP|PENDING|0/5000|null|null|
|Sapiens2_0.4b|INFERENCE|605/5000|null|null|

[Overview CSV](../metrics/common-c4p-full-20261029T063458522990Z/OVERVIEW.csv) · [current canonical overview](../runs/common-c4p-full-20261029T063458522990Z/OVERVIEW.json). Per-target IoU/support/union และ person metrics/denominators เพิ่มเมื่อระบบนั้น COMPLETE; ไม่สร้างคะแนน subset เป็นผลชุดเต็ม. Completion counts ต้องผ่าน source/GT/packet/score bindings และ exact5,000 unique IDs. ระบบที่ครบรายงานได้โดยไม่อ้างว่าทั้ง cohort เสร็จ

## Reuse, provenance และทรัพยากร

Sapiens reuse หก pilot observations ที่ตรวจ scientific compatibility ก่อน launch เหลือ4,994 pending VAL IDs; process ใหม่ warmup TRAIN0000930 ไม่เกิน1ครั้ง แยกจาก scoring ไม่แก้ fingerprint ของ pilot ย้อนหลัง. [Compatibility](../runs/common-c4p-full-20261029T063458522990Z/REUSE_COMPATIBILITY.json) / [resource budget](../runs/common-c4p-full-20261029T063458522990Z/RESOURCE_BUDGET.json). Source datasets/checkpoints/native masks/metrics ไม่เขียนทับ. Full config/protocol/source hashes และ launch commit อยู่ใน [launch](../runs/common-c4p-full-20261029T063458522990Z/LAUNCH.json) เมื่อเปิดงาน

ผลใหม่/attempt ledgers/raw logs/native29 original-grid masks/atomic packet commits/scoring evidence อยู่ `Human_Parsing_Benchmark/outputs/common_view/common-c4p-full-20261029T063458522990Z` ภายนอก Git. CPU สี่โมเดลอ่าน source runs/segments/audit references ตาม full config. แต่ละระบบอาจมาจาก native inference resource regimes ต่างกัน. Shared GPU ของ Sapiens อนุมัติโดยตรง ไม่หยุดเพียง external PID; คง 80GiB ต่อ stream,50GiB free guard,24h ต่อ checkpoint,one attempt,no fallback/retry. 200GiB เป็น planning envelope ไม่ใช่หลักฐานว่าข้อมูลทั้งหมดใช้เท่านั้น

## ภาพและข้อจำกัด

[Gallery reconciliation](../runs/common-c4p-full-20261029T063458522990Z/GALLERY_RECONCILIATION.json) ตรวจ PNG ต้นฉบับทั้งหกกับ manifest เดิม ไม่เขียนทับ manifest; ผู้ตรวจรายงานสำเนาที่ส่งมาสี่ไฟล์ไม่ byte-identical แต่ไม่ได้รับ bytes ของสำเนาให้ตรวจอิสระ จึงไม่เดาสาเหตุของช่องทาง. Prediction packets ตรวจแยก ไม่ใช้ภาพ overlay เป็น scientific input. ภาพเปรียบเทียบใช้ 16 IDs เดิมใน CIHP_NATIVE_DIAGNOSTIC_SAMPLE และเก็บ private gallery ใต้ run นี้เมื่อ predictions ที่จำเป็นพร้อม

Face proxy รวม Face_Neck/facial parts จึงไม่รับรอง strict face-only pixel equivalence. Upper/Lower เป็น non-Dress family, Dress/Apparel OTHER ยังคงสร้าง FP/FN ตาม fixed task; native GT×prediction discordance matrix ในผล canonical รองรับการวิเคราะห์ภายหลัง ไม่เปลี่ยน mapping ตามผล. ไม่อ้างว่าทุก taxonomy equivalent. Q_C4_GT ไม่ลงโทษ unmatched predicted persons โดยตรง ต้องอ่าน FP/F1 และ contamination/background leakage พร้อมกัน. Sapiens extents/identity มาจาก YOLO ไม่ใช่ native instance capability.

ไม่มี clean parser-only/end-to-end latency/FPS/VRAM-efficiency ranking; forward/map-back/resource observations เป็น shared adapter diagnostics และ native routes เดิมมี conditioning ต่างกัน. ไม่อ้าง architecture causality,ความพร้อม CCTV/สี หรือ statistical significance/uncertainty ที่ไม่ได้คำนวณ. จบรอบแล้วหยุด ไม่เปิดรุ่นอื่นหรือ retry อัตโนมัติ
