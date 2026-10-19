# ทบทวน dataset และการเตรียม Stage 0

วันที่ 2026-10-08; run `dataset-reassessment-20261008T095241Z` — **งานเตรียมที่ได้รับอนุมัติผ่านพร้อมข้อจำกัด; Stage 0 โดยรวมยัง BLOCKED / รอการตัดสินใจ** ไม่มี parser inference หรือผล benchmark ใหม่

## สิ่งที่ดำเนินการจริง

1. Initial discovery เคยไม่พบ CIHP; รอบต่อเนื่องตรวจ archive ที่ผู้ใช้โอนมา `datasets/cihp-DatasetNinja.tar` จริงครบทุก payload/JSON/bitmap พบ 38,280 images แต่ native Human_ids/part→person mapping ไม่ retained ไม่มีการดาวน์โหลด dataset เพิ่มหรือ full extraction
2. สร้าง MHP-v2 population manifests 5 ชุด ตรวจ membership จาก official lists และตรวจ train overlap ซ้ำจาก decoded-RGB hashes ใน GT index เดิม ไม่อ่าน/แฮชทั้ง dataset ซ้ำ
3. สุ่ม train ที่อ่านได้ 30 ภาพอย่างอิสระ สร้าง overlays ของทุก native person plane ตรวจ SHA256, dimensions, native IDs และ array fidelity จริง พร้อม checklist สำหรับผู้ตรวจ
4. สร้าง compatibility wrapper แยกจาก evaluator ทางการ และรัน synthetic/contract/population tests **51 ข้อผ่านทั้งหมด**
5. ขยายทะเบียนเป็น **17 รายการ metadata variants** ซึ่งรวม dataset-specific weights และ optional/excluded candidates; ไม่ใช่ roster benchmark 17 โมเดล และยังมี **0 checkpoint inference**

## ประชากร MHP-v2 ที่ต้องรายงานแยก

| Population | ภาพ | Native GT persons | สถานะ |
|---|---:|---:|---|
| Train readable | 15,400 | 41,043 | ใช้เตรียมข้อมูล/พัฒนาได้ตามขอบเขตที่อนุมัติ |
| Official validation target | 5,000 | 13,260 | เก็บครบทุก ID รวม JPEG เสีย 1 ภาพ |
| Official-split readable validation | 4,999 | 13,257 | future score ต้องระบุ readable subset |
| Exact train-overlap-controlled target | 4,348 | 11,411 | เก็บ target ก่อนตัด JPEG เสีย |
| Exact train-overlap-controlled readable validation | 4,347 | 11,408 | sensitivity population แยกจาก official-split readable |

ไฟล์ต้นฉบับและ split lists ไม่เปลี่ยน การตัดเกิดใน manifests เท่านั้น ชุด 4,999 ภาพห้ามเรียกว่า official 5,000-image result โดยไม่มี qualification และคะแนน 4,347 กับ 4,999 ต้องแสดงคนละ condition ไม่รวมเป็นคะแนนเดียว ไม่มีคะแนนใดถูกคำนวณในรอบนี้

[Policy และ hashes](../provenance/MHPV2_READABLE_POLICY_V1.json) อ้างถึง inventory และ GT index ที่ตรวจครบในรอบก่อน; [population manifests](../manifests/mhpv2_readable_v1/VALIDATION_READABLE.json) มี IDs, exclusions, RGB hashes, GT-person denominators และ source-artifact hashes ที่ตรวจย้อนกลับได้

## ข้อค้นพบที่เปลี่ยนความเข้าใจเดิม

**Observation:** ZIP ใหม่ให้ JPEG เสียเดิมทั้งสี่ภาพ จึงไม่ได้ซ่อมข้อมูล แต่ผู้ใช้อนุมัติ readable-view policy แล้ว ปัญหาไฟล์เหล่านี้ไม่จำเป็นต้องขวาง bounded feasibility test บน train ที่ตรวจอ่านได้ทุกภาพอีกต่อไป

**Interpretation:** แยก readiness ของ input สำหรับ smoke ออกจาก readiness ของ final benchmark; weights/license/execution approval ยังคงเป็น gate ของ model smoke

**Observation:** มี 652 validation IDs / 628 exact train–validation groups; within-validation มี 106 groups / 214 IDs ในหลักฐานเดิม ต่าง GT ได้แม้ RGB เหมือนกัน

**Interpretation:** readable policy ไม่แก้ split independence และ overlap-controlled view ไม่รับรองว่าไม่มี near duplicates หรือ pretraining exposure

**Observation:** CIHP archive ทางการชื่อ `instance-level_human_parsing.tar.gz` มี provider metadata **2,033,753,964 bytes** ยังไม่ได้ตรวจ bytes, SHA256, contents หรือ annotations ในเครื่อง

**Interpretation:** ขนาดข้างต้นเป็น metadata ของ native official distribution คนละไฟล์กับ local DatasetNinja TAR 2,015,375,360 bytes ที่ตรวจในรอบใหม่ ห้ามเทียบ SHA ของสอง formats เป็น proof of fidelity; CIHP ยังไม่มีหลักฐานว่าสะอาดกว่า MHP-v2

## สถานะการตัดสินใจ

CIHP = candidate primary; MHP-v2 = provisional secondary; dataset roles และ COMMON_HP ยังไม่ freeze เป้าหมาย body/clothing/accessories และ frozen YOLO26x คงเดิม Company CCTV ที่ยังไม่มี labels สงวนไว้สำหรับ finalist field test ภายหลัง จึงยังใช้คำนวณ mIoU/coverage accuracy ไม่ได้

อ่านต่อ: [CIHP audit](CIHP_QUALITY_AUDIT.md), [MHP quality risks](MHPV2_QUALITY_RISK_REVIEW.md), [decision matrix](PRIMARY_DATASET_DECISION.md), [next bounded actions](STAGE0_NEXT_ACTIONS.md), [test log](../provenance/RUN_MANIFESTS/dataset-reassessment-20261008T095241Z/BOUNDED_TESTS_V2.log)

## CIHP Archive Preflight — ข้อมูลใหม่ 2026-10-08

[Focused preflight report](CIHP_ARCHIVE_PREFLIGHT_AUDIT.md) supersedes availability finding เดิม: local archive พบแล้ว Container PASS; all 768,446 part bitmaps decode/CRC/grid checks PASS; train/validation/test 28,280/5,000/5,000; validation IDs match official GT metadata 5,000/5,000; strict RGB decode 20 sampled images PASS ไม่ใช่ full 38,280-image decode audit

Five official repository RGB/semantic fixtures byte/pixel-identical แต่ไม่มี native Human_ids/person-group fields/tags และ converter ไม่อ่าน Human_ids จึง **BLOCKED สำหรับ person-instance evaluation** Semantic-only audit เป็น conditional track ไม่แทน person-macro/oracle/coverage GT

พบ 39 train–validation exact JPEG-byte groups (39 validation IDs) และ cross-split ทั้งหมด 83 groups; decoded/near-duplicate audit ยังไม่ทำ ชุดนี้ไม่ถูกประกาศ clean จาก integrity PASS และยังไม่ promote CIHP primary DatasetNinja declares MIT แต่ authoritative original dataset-use grant ยังไม่ verified

Next gate เปลี่ยนจาก “หา CIHP archive” เป็น “หา native person GT/full split provenance และตรวจ conversion fidelity” ก่อน Full Quality Audit อ่าน [updated next actions](STAGE0_NEXT_ACTIONS.md) และ [preflight validation](../provenance/CIHP_ARCHIVE_PREFLIGHT_VALIDATION_V1.json) ประวัติ reassessment/tests 51 ข้อเดิมคงไว้; รอบ preflight เพิ่ม 9 tests รวม 60 PASS ไม่มี model/checkpoint inference

## Research-scope clarification — Decision 5A, 2026-10-12

User-confirmed independent **noncommercial academic research/evaluation** supersedes any earlier uncertainty about company R&D. [Scope](../RESEARCH_SCOPE.md), [separate dataset/model/dependency license review](LICENSE_ELIGIBILITY_REASSESSMENT.md). MHP project terms fit this scope; CIHP original RGB/GT permission remains unverified even though DatasetNinja/PGN software declares MIT. Scope clarification does not restore missing native Human GT, remove duplication or prove annotation ownership. Dataset roles remain provisional and no Full Quality Audit/benchmark/model inference has started. Bounded FASHN feasibility on verified readable TRAIN inputs is an independent proposed action, still awaiting download/execution approval.
