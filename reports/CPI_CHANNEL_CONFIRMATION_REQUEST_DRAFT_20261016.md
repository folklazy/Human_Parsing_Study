# ร่างขอคำยืนยัน CPI CIHP output class order

**สถานะ: DRAFT_NOT_SENT — ยังไม่ได้ส่งข้อความหรือเปิด issue**

เตรียมสำหรับผู้ดูแล upstream `JosonChan1998/CPI-Parser` ที่ preferred fork อ้างถึง การส่งต้องได้รับอนุญาตจากผู้ใช้ก่อน สามารถคัดลอกข้อความด้านล่างไปส่งเองได้ โดยไม่ต้องส่ง dataset, ภาพ CCTV หรือ weights แนบไปด้วย

## Subject

CIHP output label order for the released R50 and ConvNeXt-B checkpoints

## Message

Hello,

I am conducting independent, noncommercial student research comparing pretrained human parsing systems. Could you confirm the output label order for these two CIHP checkpoints linked in the CPI-Parser README?

- R50: https://drive.google.com/file/d/1uiqPVZNWIEIKquMNhZ7tv3OTZrc9WGt0/view
- ConvNeXt-B: https://drive.google.com/file/d/117grkZS6Q-v5tbeTLdyENSI0fSRD09lK/view

Specifically, what semantic class does each output ID 0–19 represent in the per-person parsing PNGs? Please include background ID 0 and confirm whether the same order applies to both checkpoints.

If both use the standard CIHP category order without remapping, a short explicit confirmation covering these two checkpoint links would be sufficient. Otherwise, an ordered list of the output labels would help us document the mapping correctly. A relevant `categories[].parsing` annotation header is also welcome, but we do not need the image dataset or the full training history.

Thank you for your help and for sharing your work.

## วิธีใช้คำตอบเป็นหลักฐาน

เก็บ URL/ข้อความต้นฉบับและวันที่ตอบ พร้อมผูกกับสอง release links และ local checkpoint hashes ที่ตรวจไว้แล้ว หากคำตอบครอบคลุมเพียง checkpoint เดียว ให้รับรองเฉพาะตัวนั้น ตรวจความหมายกับ native mapping ก่อนเปลี่ยน semantic binding เป็น VERIFIED ไม่แก้คำตอบให้สอดคล้องกับ catalog ที่เราคาดไว้

การกำหนดให้มี direct evidence เป็นระดับความมั่นใจที่โครงการนี้เลือกรับรอง ไม่ใช่หลักฐานว่า CPI ใช้ class order ผิด และไม่ใช่ข้อบังคับสากลของงานวิจัยทุกชิ้น หากยังไม่มีคำตอบ ให้คง gate ตามเดิม การพิจารณาทางเลือกจาก indirect evidence ต้องเป็นการตัดสินใจอย่างเปิดเผยในภายหลัง

[ขอบเขตการค้นที่ปิดแล้วและหลักฐานที่ขาด](CPI_CHANNEL_ORDER_SOURCE_BLOCKER_TH_20261016.md)
