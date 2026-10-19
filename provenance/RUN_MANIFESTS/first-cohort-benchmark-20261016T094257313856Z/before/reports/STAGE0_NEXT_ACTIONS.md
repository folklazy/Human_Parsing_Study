# ขั้นตอนถัดไป — รออนุมัติ benchmark กลุ่มแรก

ดู [launch readiness](FIRST_COHORT_VALIDATION_LAUNCH_READY_TH_20261016.md) และ [launch plan](../provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/LAUNCH_PLAN.json)

1. Bounded integration ปิดแล้ว ไม่เปิด mapping/five-policy review ใหม่
2. Validation route/main-reference population binding เตรียมแล้ว; CPU 147tests ผ่าน; execution ยังปิด
3. **รอคำอนุมัติแยก:** CPI_R50_CIHP/CPI_ConvNeXtB_CIHP+frozen YOLO26x T3b, reference 5,000 รันครั้งเดียวแล้วรายงาน main 4,961 แยก, matching0.50/0.75, STRICT_COMPLETE, quality-only ไม่ tuneVAL หรือจัดอันดับเวลา/VRAM
4. หลังอนุมัติจึง version accepted execution config/decision ตรวจ candidate hashes และ launch plan และ freeze ก่อน inference ไม่แก้ flag อย่างเดียวหรือถือข้อความความคืบหน้าเป็นคำอนุมัติ

ยังไม่รัน validation, full benchmark, CCTV, PPSS, training, hybrid หรือ color ไม่มี downloads/remote push
