# สรุปผล Human Parsing — CPI T3b กลุ่มแรก

## สรุปใน 1 นาที

- เปรียบเทียบ CPI_R50_CIHP และ CPI_ConvNeXtB_CIHP กับ frozen YOLO26x ใน T3b / FP32 ไม่มี fine-tuning
- Reference 5,000 ภาพ ใช้ inference ครั้งเดียวต่อ component แล้วรายงาน main 4,961 ภาพแยกตาม membership
- Matching 0.50 หลัก / 0.75 เสริม และ STRICT_COMPLETE ตามกติกาที่รับรองไว้
- YOLO สำเร็จ 5,000 ภาพ; R50 สำเร็จ 4,475; ConvNeXt-B สำเร็จ 4,959
- R50 พบ CUDA OOM 525 ภาพ; ConvNeXt-B พบ OOM 40 และ interrupted/invalid 1 ภาพ
- **ทั้งสองระบบ INCOMPLETE จึงไม่มีคะแนนหลักและยังไม่มี accuracy winner**; ไม่ใช้ success-only จัดอันดับ
- เป็น quality-only ไม่มีผู้ชนะด้านเวลา FPS หรือ VRAM

## ผลลัพธ์หลัก

| Population | ระบบ | สำเร็จ | Failed / Invalid | G_loc / G_sem | คะแนนหลัก |
|---|---|---:|---:|---:|---|
| main | CPI R50 | 4,436 / 4,961 | 525 / 0 | 17,434 / 17,390 | N/A — INCOMPLETE |
| main | CPI ConvNeXt-B | 4,920 / 4,961 | 40 / 1 | 17,434 / 17,390 | N/A — INCOMPLETE |
| reference | CPI R50 | 4,475 / 5,000 | 525 / 0 | 17,548 / 17,504 | N/A — INCOMPLETE |
| reference | CPI ConvNeXt-B | 4,959 / 5,000 | 40 / 1 | 17,548 / 17,504 | N/A — INCOMPLETE |

จำนวน execution เหมือนกันที่ matching 0.50 และ 0.75; [CSV canonical](metrics/first-cohort-benchmark-20261016T094257313856Z/QUALITY_RESULTS.csv) เก็บครบ 8 แถว N/A ไม่ใช่คะแนนศูนย์

## สิ่งที่ตัวเลขบอกเรา

- Configuration ของ native CPI ทั้งสองยังรันไม่ครบประชากรบน T4 ในรอบนี้ แม้ bounded TRAIN integration เคยผ่าน
- R50 และ ConvNeXt-B สำเร็จต่างกัน 484 ภาพใน reference แต่ตัวเลขนี้ไม่ใช่ผลต่าง accuracy
- ทั้ง 566 failure/invalid component-image rows อยู่ใน main ด้วย การตัด 39 overlap members จึงไม่ได้ทำให้ระบบใด COMPLETE
- Main/reference เป็นชุดภาพซ้อนกัน ไม่ใช่การทดสอบอิสระสองรอบ และไม่มี inference ซ้ำเพื่อสร้างตารางแยก

## ข้อจำกัดและรายละเอียด

Mapping เป็น ACCEPTED_WITH_INDIRECT_EVIDENCE; GT เป็น released-annotation-relative; เป็น custom CCIHP coarse targets ไม่ใช่ official CIHP benchmark และยังไม่ยืนยัน CCTV robustness

[REPORT.md](REPORT.md) · [การนำเสนอและหลักฐานภาพ](PRESENTATION_SUMMARY_TH.md) · [Failures](metrics/first-cohort-benchmark-20261016T094257313856Z/FAILURES.csv) · [Data schema](DATA_SCHEMA.md)
