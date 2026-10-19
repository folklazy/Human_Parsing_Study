# CCIHP — ชุดตรวจคุณภาพ GT โดยมนุษย์

สถานะ **PENDING_INDEPENDENT_HUMAN_REVIEW** ไม่ใช่การรับรองว่า dataset สะอาด และยังไม่ประมาณอัตราความผิดพลาด

## การสุ่ม

Sampling frame คือ TRAIN 28,280 ภาพที่ RGB/GT อ่านได้และ dimensions ตรงกัน ใช้ seed `20261012` สุ่มแบบ stratified simple random without replacement จำนวน200ภาพ มี38 strata ทุก stratumมีโอกาสถูกเลือกมากกว่าศูนย์

Strata ประกอบด้วยจำนวน Human IDs, ความละเอียดภาพ, mask ของคนที่เล็กที่สุดเทียบพื้นที่ภาพ, human occupancy และการตัดกันของ bbox สิ่งเหล่านี้เป็น proxy เชิงเรขาคณิต ไม่ใช่การรับรอง crowd severity หรือ occlusion

จัดอย่างน้อย1ภาพต่อ stratum แล้วแจกส่วนที่เหลือตามขนาด population; inclusion probability `π_i=n_h/N_h` และ design weight `N_h/n_h` บันทึกครบ การสุ่มใช้ TRAINทั้งหมดที่เข้าเงื่อนไข ไม่เลือกเฉพาะ known anomalies และไม่ใช้ VAL

[Sample/strata/inclusion probabilities](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/TRAIN_REVIEW_SAMPLE.json), [checklist200แถว](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/HUMAN_REVIEW_CHECKLIST.csv)

## ภาพตรวจ

[เปิด gallery](../outputs/visualizations/stage0f-ccihp-quality-20261012T062825Z/index.html), [source/output hashes และ round-trip tests](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/REVIEW_PACKAGE.json)

แต่ละภาพมี Original RGB, Human_ids พร้อม ID, Category_ids, Instance_ids, GTรายคน และ warning overlay ทุก panel ใช้ขนาดพิกเซลต้นฉบับ เพิ่มแต่พื้นที่ชื่อpanel ไม่มีการ resize GT ตัวอย่างสุ่ม200ภาพกับกรณี0033810ที่เลือกเจาะจงอีก1ภาพอยู่คนละ selection role

สีเหลืองแสดง boundary ซึ่งไม่ได้แปลว่า error; สี magenta ใน warning panelแสดง unknown/coverage flag ไม่ใช่ผลตัดสินของผู้ตรวจ ใช้ legend ในgalleryอ่าน semantic colors ส่วน Human/Instanceใช้สีตามIDเฉพาะภาพ

ตรวจ round-trip ของ Category/Human/Instance ได้ตรงทุกพิกเซล201/201ภาพ การตรวจนี้รับรอง conversion fidelity เท่านั้น Assistantดูภาพบางกรณีเพื่อเช็กการแสดงผล ไม่ถือเป็น independent human review

## Checklist

ผู้ตรวจบันทึก missing physical person, duplicate person IDs, หลายคนแชร์IDเดียว, wrong class, person/part ownership, boundary error และ ambiguous/occluded region พร้อมpersonID/class/ROI เหตุผลและseverity

ใช้สถานะ `NO_ISSUE_OBSERVED / CONFIRMED / SUSPECTED / UNASSESSABLE` แยกจาก automated flags และแยก minor/major/critical/uncertain ถ้าไม่ทราบ policyของคนเล็กด้านหลังหรือขอบเขตที่ถูกบัง ให้บันทึกuncertain ไม่เดาว่า annotationผิด

แนะนำผู้ตรวจสองคนโดยไม่เห็น model ranking; critical/uncertain casesต้อง second review และ adjudication เก็บ reviewer/date/เหตุผลไว้ใน versionใหม่ ไม่แก้ immutable automated evidence

## การประมาณ prevalence ภายหลัง

ตอนนี้ **NOT ESTIMATED** ต้องให้ reviewครบก่อน หากประมาณอัตราให้ใช้ stratum weights และ uncertainty ที่รองรับ image clustering รายงาน image-level และ person-level denominatorแยกกัน เพราะภาพถูกสุ่มไม่ได้ทำให้คนทุกคนมีโอกาสถูกเลือกเท่ากัน กรณี warning ที่เลือกเจาะจงห้ามปนใน prevalence sample
