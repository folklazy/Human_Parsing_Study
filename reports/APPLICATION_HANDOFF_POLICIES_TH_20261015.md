# ขอบเขต implementation และนโยบายที่ยังรอรับรอง — 15 ตุลาคม 2026

> อัปเดตหลังผู้ใช้รับรอง: STRICT_COMPLETE เป็นคะแนนหลักพร้อมเงื่อนไข INCOMPLETE/operational diagnostics และ cohort ตาม checkpoint-specific support ได้รับการยอมรับแล้ว ดู [decision V4](../provenance/APPLICATION_V2_DECISIONS_V4.json) และ [first-cohort review](FIRST_COHORT_CONDITIONAL_POLICY_REVIEW_TH_20261015.md) ข้อความ pending ทางเลือกสองนโยบายในเนื้อหาเดิมด้านล่างเป็นประวัติก่อนการรับรอง; mapping/domain/population/matching/runtimeยังไม่ freeze

เอกสารนี้บันทึกงานวิศวกรรม ไม่ freeze protocol และไม่อนุญาต benchmark ใหม่ ค่ารันอยู่ใน [config V3](../configs/application_v2_handoff_v3.yaml) ซึ่งผูก [decision V3](../provenance/APPLICATION_V2_DECISIONS_V3.json) โดย hash; config เก่ายังเก็บไว้เพื่อ replay ประวัติ

## Taxonomy และ GT domain

[Numeric mapping V2](../taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V2.json) แยก CIHP ID10 Torso-skin กับ LIP ID10 Jumpsuits; V1 ยังอ่าน GT ได้ แต่ใช้ project prediction ไม่ได้อีกเพื่อป้องกันการเลือก taxonomy โดยเดา ค่า LIP ID10 ไป Garments_coarse เป็นข้อเสนอ projection ไม่ใช่หลักฐานว่า LIP มี Exposed_torso หรือมี semantic coverage เท่า CIHP

LIP จึงยังเข้ากลุ่ม common-capability ที่บังคับ Exposed_torso ไม่ได้ ข้อเสนอคือแยก cohort ที่อธิบายได้ก่อน ไม่ตัดคลาสที่ยากเฉพาะโมเดลเพื่อให้ผ่าน ตัวเลือก fixed-task ต้องรับรองนโยบาย unsupported อย่างชัดเจนและใช้ตัวหารเดียวกัน

[View cards](../taxonomy/APPLICATION_HANDOFF_VIEW_CARDS_DRAFT_V1.json) ยังคง DRAFT: V0 ยังเรียก full-person silhouette ไม่ได้ถ้า mapping void hair/hat; V2 ยังต้องตรวจ annotation completeness ก่อนกำหนด known negatives ห้ามใช้ prediction สร้าง void และห้ามถือ category background เป็นคำตอบลบที่ยืนยันแล้วทุกพิกเซลโดยอัตโนมัติ

การไม่มี semantic GT ทำให้ semantic quality ของคนนั้นเป็น undefined แต่ถ้าคนนั้นอยู่ใน G_loc และไม่มี prediction จับคู่ ยังนับ localization FN หากอยู่ใน G_sem และไม่มีผลจับคู่ คุณภาพรายคนเป็น 0 และยังอยู่ในตัวหาร G_sem

Known semantics แต่ owner unknown เก็บใน global domain แต่ void ใน person domain ไม่สร้างคนจากการเดา ownership ข้อมูล sidecars เดิมยังไม่ถูกเปลี่ยน: CCIHP source 5,000 ภาพ/17,548 native persons และ controlled 4,961 ภาพ/17,434 native persons; candidate G_sem เดิม 17,504 / 17,390 เป็นคนละตัวหารกับ native persons และยังไม่ใช่ประชากรที่ freeze

## Scoring boundary และ failure lifecycle

`ConfiguredRunner.score_frame`/`score_person_result` เรียก `scoring.score_frame` และปฏิเสธ config ที่ไม่มี accepted scoring context การเพิ่ม context โดยแก้ YAML อย่างเดียวไม่ผ่าน decision binding ส่วน scorer ตรวจ mapping hash, checkpoint/config/head/native class order binding, target support, GT domain, original W/H, emitted predictions ทุกตัว และ evaluation bbox provenance ก่อน matching

Public numerical `evaluate_persons` ตรวจทุก mask แม้ไม่มี GT หรือไม่มี semantic GT และต้องระบุ trusted original W/H แต่ไม่ใช่ benchmark authorization API ผู้ใช้ต้องเรียก runner ที่ผูก config เมื่อทำงานจริง ฟังก์ชันคณิตศาสตร์อย่าง `confusion` ใช้สำหรับ fixtures และการสะสม counts; ไม่ใช่ทางลัดเพื่ออ้าง accepted benchmark

| เหตุการณ์ | STRICT_COMPLETE | OPERATIONAL_EMPTY_FALLBACK ที่ต้องเลือก explicit | การนับ |
|---|---|---|---|
| Complete / valid empty | ให้คะแนนตาม GT | เช่นเดียวกัน | empty ไม่ได้ perfect; zero denominator เป็น null |
| Person model failure | ไม่มีคะแนนหลักครบประชากร | รับ final outputs ที่ valid หากอนุญาต PERSON_PARTIAL | จับคู่ G_loc ครั้งเดียว |
| Frame/load failure | ไม่มีคะแนนหลัก | empty fallback เฉพาะ state ที่อนุญาต; ระบุว่า evaluator สร้าง | ไม่เรียกว่า native prediction |
| Contract failure | ไม่ให้คะแนน | ไม่แปลง invalid output เป็น valid output | ledger แยกจาก model failure |
| Shared data / external invalid / unscheduled / unresolved | ไม่ให้คะแนน | ไม่ให้คะแนน | ต้องแก้สาเหตุ ไม่ตัดตัวหารเฉพาะโมเดล |

ยังไม่ได้เลือก policy หลักแทนผู้ใช้ กลไกทั้งสองมี synthetic tests; model retries เป็น 0 การคืน PATH เพื่อแก้ launcher ไม่ใช่การลองโมเดลซ้ำเพื่อเลือกคะแนน และบันทึก attempt เดิมไว้

Semantic quality รายคนไม่แทน foreground quality: fixture A ถูก 100 pixels แต่ B รั่วอีก 900 known-negative pixels ให้ A IoU=1 และ foreground IoU=0.1 ทั้งสองค่าตรวจแล้ว bbox conditioning กับ bbox evaluation มี provenance แยกกัน; actual scoring ใช้ source ที่ context กำหนด การเปลี่ยน source เป็นการเปลี่ยนข้อสอบ

## Retention และการประเมินซ้ำ

| Artifact | ทำได้ | ทำไม่ได้ |
|---|---|---|
| Native hard labels | hard remapping | probability aggregation / แยก probability ที่ทิ้งไป |
| Native per-person masks + scores | association และ person metrics ตาม retained candidates | กู้คนที่ถูก native decoder กรองก่อนบันทึก |
| Target hard masks | metric/domain ของ target เดิมเมื่อข้อมูลพอ | แยกกลับเป็น native classes |
| Native logits/probabilities + geometry | decoder ที่ข้อมูลรองรับ | เปลี่ยน input/crop/precision โดยไม่ inference ใหม่ |

`require_retention` ปฏิเสธ probability aggregation จาก hard labels; ยังไม่มี production cached-scoring API จึงระบุ **NOT_IMPLEMENTED / DISABLED** ไม่ใช่ PASS ทั้งระบบ `resume_packet` ตรวจ finalized packet, hashes, schema และ inference fingerprint เป็น artifact integrity API ไม่ได้รับรอง workflow scheduling/resume หรืออนุญาต re-score taxonomy โดยอัตโนมัติ

Native outputs ของ smoke ถูกเก็บ lossless พร้อม native IDs/boxes เมื่อ interface มีให้ Semantic-only parser ยังไม่มี native instance identity แม้ integration จะใส่ oracle/YOLO identity ภายหลัง CPI canonical exports 8 packets เก็บ T1 และ T3B origins แยกกัน: fresh CPI + saved verified YOLO ภาพเดียวกัน ไม่ใช่ jointly timed live pipeline

## บทบาทข้อมูลและ runtime

รอบนี้ใช้ CCIHP TRAIN `0000930` เท่านั้นต่อ checkpoint ไม่มี VAL inference, model selection, taxonomy tuning หรือ ranking จากผล smoke ภาพนี้เคยอยู่ใน exploratory pilot เดิม จึงไม่ใช่ holdout ใหม่ หลักฐาน GT/sidecar ของ validation ที่เคยดูเพื่อ audit ยังถือเป็น annotation audit ไม่เปลี่ยนชื่อเป็น development splitเพื่ออ้างความเป็นอิสระ ขอบเขตประวัติการเลือกค่าอื่นที่ไม่มีบันทึกยังเป็น UNKNOWN

FP32 smoke บน T4 เป็นการตรวจ feasibility: 0 warmups / 1 image, native TTA ตาม worker, batch1 และ parser ทีละตัว เก็บ allocated/reserved แยกกัน Process/device peak ไม่ได้ sample ให้ N/A; internal-op dtype ไม่ได้ตรวจทุก operation Hooks พบ floating outputs เป็น FP32 ไม่ใช่หลักฐานรับรองทุก kernel

เวลาของแต่ละ workerมี boundaries ต่างกันตาม native pipeline และรอบนี้มีงาน asset/hash/download บางช่วงร่วมด้วย จึงไม่ใช้ latency/VRAM จัดอันดับ ไม่บวก memory peaks จาก process ต่างกันเพื่ออ้าง resident pipeline memory

## สิ่งที่ต้องรับรองก่อนกลุ่มใดพร้อม

1. Target/view และ numeric mapping ที่มี semantic evidence รวม known-negative/unknown policy
2. ประชากรและ G_loc/G_sem ที่จะใช้เป็นหลัก พร้อม annotation ownership limitations
3. Strict-complete หรือ operational fallback, matching threshold และ evaluation bbox source
4. Actual route และ runtime profile ของกลุ่มนั้น; native smoke ผ่านไม่รับรองทุก YOLO-conditioned route

คำแนะนำเบื้องต้นคือ **STRICT_COMPLETE เป็นคะแนนหลัก** และเก็บ operational behavior แยกเป็น diagnostic, แยก CIHP/LIP capability cohorts จนมีข้อเสนอ shared taxonomy ที่ไม่เสียโจทย์ body/clothing การรับรองนโยบายเหล่านี้ยังไม่ใช่คำอนุญาต full benchmark
