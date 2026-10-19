# ต้นแบบ YOLO ที่ตรวจจริง

ตรวจจาก working copies ของ Master และ Small ที่เสร็จแล้วโดย read-only รายการไฟล์ SHA256 และ commit อยู่ใน [inspection manifest](../publication/YOLO_REFERENCE_REVIEW.json)

| แนวทาง | การใช้ใน Human Parsing |
|---|---|
| README เป็น landing page, technical report แยกจากสรุป | นำมาใช้ พร้อม navigation หลักต่อหนึ่งเรื่อง |
| RESULTS เป็นสรุปตัวเลข, PRESENTATION เป็นหลักฐานและการตีความ | นำมาใช้ โดยไม่แต่ง semantic visual case หรือคะแนนให้ระบบ INCOMPLETE |
| Canonical CSV + schema + provenance/source hashes | นำมาใช้ พร้อม population/cohort/run IDs, null reasons และ failure rows |
| Protocol/freeze แยกจาก source Git revision | ปรับให้บันทึก V11 launch/V12 restoration และ Git snapshot หลังรัน |
| Qualitative same-frame comparisons | เก็บแนวทางไว้ แต่ไม่แจกภาพ dataset/GT ก่อนยืนยันสิทธิ์ และไม่ใช้ plot operational แทนหลักฐานความแม่น mask |
| Tier split / 17-model winners / per-sequence / timing Pareto | ไม่ย้ายมาทั้งชุด เพราะงานนี้มี cohort สองระบบ, still-INCOMPLETE และ quality-only |

อ่าน README/REPORT/RESULTS/PRESENTATION/protocol และ manifest ของ Small; README/MASTER_RESULTS/standard/schema/methodology/state/source/validation ของ Master จริง ไม่พบ DATA_SCHEMA.md หรือ DATASET_DETAILS.md เฉพาะ Small จึงใช้ canonical schema กับ dataset evidence ของ Master และ manifests ที่มีจริง ไม่พบ handoff เฉพาะในสอง repositories ที่ตรวจ จึงสร้าง handoff ตามขอบเขต Human Parsing เอง

ไม่ได้แก้ไฟล์ ผล หรือ Git history ของ YOLO ไม่มีการรัน validator/model/benchmark ของ YOLO เพื่อจัด repository นี้
