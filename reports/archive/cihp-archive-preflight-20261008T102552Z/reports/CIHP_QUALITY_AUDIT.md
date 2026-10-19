# CIHP — availability และแผนตรวจคุณภาพ GT

**สถานะ: NOT AVAILABLE LOCALLY / QUALITY UNVERIFIED / ACQUISITION AWAITING APPROVAL** ไม่ได้ตรวจหรือสร้างผล integrity/GT-quality ของภาพ CIHP ที่ยังไม่มีในเครื่อง

## สิ่งที่ยืนยันจากแหล่งทางการ

[PGN implementation](https://github.com/Engineering-Course/CIHP_PGN) ที่ commit `0cf1cbe54a44fc86abe2023b0e762df3f9605242` เป็นแหล่งเชื่อมไปยัง dataset distribution โฟลเดอร์แรกมี resource key และชี้ต่อไปยัง `Human_Parsing_Dataset/CIHP` พบ metadata archive `instance-level_human_parsing.tar.gz`, file ID `1HdqA8yWVxZ8od0hngKzZTziHx_ONzCWj`, ขนาด **2,033,753,964 bytes ≈ 2.034 GB / 1.894 GiB** หน้า sign-in ที่พบครั้งแรกหายไปเมื่อใช้ resource-key link ที่โฟลเดอร์ทางการแสดง ไม่ได้หลบสิทธิ์หรือใช้ mirror

[Paper ECCV 2018](https://arxiv.org/html/1808.00157) ระบุ reference population 38,280 ภาพ: train 28,280, validation 5,000, test 5,000; 20 labels รวม background พร้อม person identities และ hidden test annotations มีการกล่าวถึง professional labeling และ second review แต่ไม่ใช่ผล independent quality audit ของ release ที่เราจะใช้

**License:** MIT ใน PGN repository เป็น software license ยังไม่พบ grant ที่ยืนยันสิทธิ์ของ dataset images/GT จากหลักฐานที่ตรวจรอบนี้ หน้า project รุ่นเดิมไม่สามารถเปิดใช้งานได้ตามปกติ การเผยแพร่ผ่าน Drive ไม่พอรับรองการใช้เชิงพาณิชย์หรือเผยแพร่ตัวอย่างภาพ ต้องอ่าน release terms และขอ clarification ถ้ายังไม่ชัดก่อน evaluation/publication/deployment

[Acquisition evidence](../provenance/CIHP_ACQUISITION_REVIEW_V1.json) และ [archive metadata snapshot](../provenance/RUN_MANIFESTS/dataset-reassessment-20261008T095241Z/sources/CIHP_DATASET_FOLDER_METADATA.json) แยก provider size ออกจาก local measured checksum ซึ่งยังเป็น null

## Native annotations: source evidence และสิ่งที่ต้องตรวจจริง

Parser source อ้าง layout `Training/Validation/{Images,Category_ids,Human_ids,Instance_ids}` Category IDs คือ semantic labels; Human IDs คือ person identities; part-instance IDs ต้องตรวจสัมพันธ์กับทั้งสอง map ก่อนสร้าง per-person parsing planes ห้ามสรุปเองว่า `Instance_ids` คือ human IDs

[Native source inventory](../taxonomy/CIHP_NATIVE_SOURCE_INVENTORY_DRAFT.yaml) ระบุ IDs 0–19: background, hat, hair, gloves, sunglasses, upper-clothes, dress, coat, socks, pants, torso-skin, scarf, skirt, face, left/right arm, left/right leg, left/right shoe ตาม registration code และ paper **Human=20 เป็น auxiliary model class ไม่ใช่ native GT label** Framework ระบุ ignore 255 แต่การพบค่า 255 จริงใน release ยังไม่ตรวจ

CIHP label 10 = torso-skin; LIP label 10 = jumpsuit จำนวน 20 classes เท่ากันไม่ได้ทำให้ weights/mapping interchangeable การเก็บ one-human-ID-per-pixel อาจไม่เก็บ overlapping amodal planes แบบ MHP-v2 ต้องตรวจ release semantics และการมองเห็นจริง ไม่อนุมาน amodal/visible ownership จากชื่อ directory

## Audit ที่ยังไม่ดำเนินการเพราะไม่มี dataset

| รายการ | สถานะ |
|---|---|
| ภาพจริง, GT count, split membership, person counts | NOT TESTED |
| Strict decode, pairing, dimensions, class/ID validity, orphans | NOT TESTED |
| Exact decoded train/val duplicates และ within-val duplicates | NOT TESTED |
| Near duplicates / external pretraining overlap | UNKNOWN |
| Spatial GT alignment / physical-person ownership | NOT REVIEWED |
| Class distribution, rare-label support และ invalid annotations | NOT COMPUTED |
| Local file inventory/SHA256 และ annotation fidelity | NOT GENERATED |
| Dataset research/deployment permission | UNKNOWN |

ดังนั้นยังไม่มีหลักฐานเพียงพอให้ **promote CIHP เป็น primary อย่างเด็ดขาด** และห้ามเรียก CIHP ว่าสะอาดกว่า MHP-v2

## การสุ่มตรวจ 200 ภาพที่เตรียมไว้

[Versioned sampling plan](../manifests/CIHP_QUALITY_REVIEW_PLAN_V1.json) ยังไม่มี image IDs เพราะไม่มีข้อมูลจริง เป้าหมาย 200 ภาพจาก **train** แบ่ง strata ตาม person count, minimum person occupancy และ image size แล้ว allocate ตามขนาด strata พร้อม inclusion probabilities, seed และ recorded frame ก่อนเปิดดูภาพ ไม่ใช้ validation GT เพื่อเลือก thresholds/crops/taxonomy

ตรวจทุก person ในภาพด้วย Original RGB + semantic/person/part IDs + per-human planes; ใช้ checklist ownership, missing visible person, boundary alignment, class semantics, ambiguity และ severity ผู้ตรวจสองคนอิสระถ้าทำได้ เก็บ suspected ต่างจาก confirmed ห้ามถือ overlap หรือ automated flags เป็น physical-person error ด้วยตัวเอง

Rare-label examples เพิ่มได้ในชุด diagnostic แยก ห้ามนำมารวม unweighted prevalence estimate หาก review ไม่ครบหรือ ambiguity ยังไม่ resolve ต้องรายงาน PENDING/uncertainty ไม่สรุป error prevalence

## Acquisition หลังได้รับอนุมัติ

เสนอ download cap **2.1 GB** จาก official chain นี้เท่านั้น ไม่มี packages เพิ่ม ใช้ disk quota ชั่วคราว **15 GB** สำหรับ archive + extraction (เป็น budget ไม่ใช่ขนาดแตกไฟล์ที่ยืนยันแล้ว) ปัจจุบันพื้นที่ว่างประมาณ 620 GiB ตรวจ SHA256, safe tar inventory, paths/symlinks และ release terms ก่อน extraction ที่ canonical `datasets/CIHP/` หากขนาด/แหล่งผิดจาก metadata ให้หยุด ไม่มี download หรือ directory migration ในรอบนี้
