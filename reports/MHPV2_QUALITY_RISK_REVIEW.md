# MHP-v2 — readable views และ annotation-quality risk

**Native files unchanged; readable policy approved; semantic quality ยังไม่ได้รับรอง** ใช้ exhaustive inventory/GT index และ leakage audit ที่มีอยู่ ไม่ hash หรือ decodeทั้งชุดใหม่

## Readable policy ที่ดำเนินการแล้ว

เก็บ original official train/validation/test lists และไฟล์ทุกชิ้นไว้ Train ที่อ่านได้ 15,400 / 41,043 native persons; readable official-split validation 4,999 / 13,257; exact train-overlap-controlled readable validation 4,347 / 11,408

Excluded JPEGs ใน views: train `1396` (6 persons), `18613` (5), `24328` (2); val `17844` (3) ไม่ซ่อม pixels, ไม่ใช้ permissive decode, ไม่ลบ GT และไม่ย้าย splits [ZIP verification](MHPV2_NEW_ZIP_RGB_VERIFICATION.md) ยืนยัน archive ใหม่และสมาชิกทั้งสี่ byte-identical จึงกู้กลับ **0 ภาพ**

Full official target 5,000 / 13,260 และ controlled target 4,348 / 11,411 อยู่คนละ manifest กับ readable subsets การรายงาน future score ต้องระบุ condition และ denominator ชัด ไม่ใช่ official-population score ที่มีเพียง failure policy ซ่อนอยู่

## Image reuse และความเป็นอิสระ

652 validation IDs ใน 628 train–validation exact decoded-RGB groups; รอบนี้ตรวจ set อีกครั้งจาก canonical index และได้ IDs ตรง leakage manifest เดิม ในหลักฐาน review ก่อนหน้า 651 IDs มี JPEG bytes เหมือน train; อีก 1 มี pixels เหมือนแต่ bytes ต่าง ส่วน GT bundles 42 เหมือนตามลำดับ, 1 เหมือนแต่สลับ IDs, 609 ต่าง และ 6 val IDs มี person counts ต่างจาก train copies ทุกชุด

Within-validation เดิม 106 groups / 214 IDs / 108 extra repetitions; controlled target ยังมี within-val repetition จึงไม่ใช่ fully deduplicated population การตัด exact train overlap ไม่ลบ external pretraining/near duplicates และไม่พิสูจน์ public checkpoints memorized ภาพเหล่านี้

**Recommendation:** แสดง readable official-split และ exact-overlap-controlled sensitivity แยกตารางพร้อม checkpoint exposure declarations ไม่ใช้ความต่างสองคะแนนเป็น causal memorization effect และไม่ปรับนโยบายตาม future test score

## GT ownership: confirmed pixels กับ unresolved cause

Selected evidence เดิม `train/9968` มี plane ที่ครอบคลุม regions ของ visible adults มากกว่าหนึ่งคน; `11766` และ `25373` มี semantic planes เหมือนกันทุก pixel; `16898` มี planes ใกล้กันมาก ข้อเท็จจริงระดับ pixels เหล่านี้ตรวจซ้ำได้ แต่สาเหตุใน official annotation/release และการจัด ownership ที่ถูกต้องยังไม่ยืนยันครบ

Overlap เองไม่เท่ากับ annotation error มือ/เสื้อผ้า/ของที่ถืออาจเป็นของคนอื่นและตกอยู่ในคนละบริเวณที่เห็นได้ Pose IDs ไม่ควรใช้สั่ง reorder parsing IDs โดยไม่ตรวจ native convention

**ผลต่อ protocol:** GT crop อาจรวมเพื่อนบ้าน; oracle เป็น oracle ของ supplied annotation geometry ไม่ใช่ perfect physical-person oracle; matching และ person-macro/coverage metrics อาจได้รับผลจากผิด ownership; native evaluator ยังให้คะแนนต่อ native GT ที่ supplied

**นโยบายเสนอ ยังไม่ freeze:** เก็บ native GT ทุก plane; อ้าง flag และ uncertainty แยกจาก scores; ให้ independent reviewers resolve ประเภท/ระดับความเสียหายก่อนอนุมัติ sensitivity exclusions หรือ optional clean-view diagnostic ห้าม relabel native GT และไม่แอบตัด anomaly-selected cases เพื่อให้คะแนนดีขึ้น

## Independent random sample ที่สร้างจริง

[Sample manifest](../manifests/MHPV2_RANDOM_QUALITY_REVIEW_V1.json): 30 train-readable image IDs, simple random without replacement, seed `20261008`, sampling frame 15,400, image inclusion probability `30/15400` ไม่เลือกด้วย anomaly score และไม่เอา known anomalies ออกจาก frame สุ่มก่อนอ่าน GT pixels และไม่ใช้ validation

สร้าง **30 full diagnostic images + 5 contact sheets** เก็บ RGB, แยกทุก native parsing plane และ overlays ไม่ flatten เป็น metric truth ตรวจ source hashes, full decoding, dimensions, valid labels และ semantic-array fidelity จริงครบ sample

![Six randomly sampled TRAIN diagnostics](../outputs/visualizations/dataset-reassessment-20261008T095241Z/mhpv2_random_quality/contact_01.png)

[Checklist CSV](MHPV2_RANDOM_QUALITY_REVIEW_V1.csv) ยัง PENDING ทั้ง 30 ภาพ Assistant ดู contact sheet แรก 6 ภาพและ full panel `7922` เพื่อ spotcheck การแสดงผล ไม่ได้ตัดสินทุก semantic/ownership condition [Display evidence](../provenance/MHPV2_RANDOM_REVIEW_DISPLAY_SPOTCHECK_V1.json) แยกข้อสังเกตและข้อจำกัดไว้

Observation ของ `7922`: planes หลักติดตาม visible adults คนละคน รูปแบบตัวอย่างนี้ไม่รองรับข้อสรุปว่าทั้ง dataset ถูกต้อง/ผิดทั้งหมด การตรวจ grids และ round-trip fidelity ไม่ใช่ semantic correctness

## Checklist และการประมาณ prevalence

ผู้ตรวจควรบันทึก physical person ↔ native plane, missing visible person, multi-person contamination, same-person duplicate, semantic mismatch และ boundary offset พร้อม ID/class/region อ้างอิง ตีความ small overlap อย่างระมัดระวัง แยก severity critical/major/minor/uncertain/no issue observed และให้ second review สำหรับ uncertain/critical

**ยังไม่ประมาณ prevalence**: human review ไม่ครบและ sample 30 มี uncertainty สูง ต้องระบุ image-level และ person-level denominator ต่างกัน ภาพถูกสุ่ม uniform ไม่ได้หมายความว่า persons ถูกสุ่ม uniform หากต้องการ weighted person prevalence ต้องใช้วิธีที่รองรับ clustering ผู้ตรวจ AI รอบแรกไม่แทน final human adjudication

การตัดสิน dataset primary ควรใช้ independent review ที่กำหนดไว้ล่วงหน้า ไม่ใช้ handful of anomaly-selected examples เป็นอัตราความเสียหายระดับ dataset
