# ผล benchmark กลุ่มแรก — CPI สองระบบ + Frozen YOLO26x บน CCIHP

**สถานะ: FINISHED_WITH_INCOMPLETE_SYSTEMS**

รันตามคำอนุมัติบน reference 5,000 ภาพหนึ่งครั้งต่อ component แล้วแยกรายงาน main 4,961 / reference 5,000 ตาม membership เดิม ใช้ T3b FP32, coarse body/clothing mapping ที่รับรองด้วยหลักฐานทางอ้อม, association0.50 และ final GT matching0.50/0.75 ไม่มีการ tune จาก VAL หรือเปลี่ยนตัวหารหลังเห็นผล

## 1. Execution และความล้มเหลว

| Component | ภาพทั้งหมด | สำเร็จ | Failed | Invalid | สาเหตุที่บันทึก |
|---|---:|---:|---:|---:|---|
| YOLO26X_FROZEN | 5,000 | 5,000 | 0 | 0 | {} |
| CPI_R50_CIHP | 5,000 | 4,475 | 525 | 0 | {'CUDA_OOM': 525} |
| CPI_ConvNeXtB_CIHP | 5,000 | 4,959 | 40 | 1 | {'CUDA_OOM': 40, 'UNRESOLVED_INTERRUPTION': 1} |

YOLO attempt แรกหยุดก่อนโหลดโมเดลเนื่องจาก config validator ดึง SciPy ที่ไม่มีใน YOLO environment จึงคง invalid trial เดิมไว้ และแยก CPU authorization receipt ออกจาก detector worker โดยไม่ติดตั้งหรือแก้ environment เดิม YOLO จึงทำ image inference เพียงครั้งเดียว ไม่ใช่การ retry ภาพที่เคยล้มเหลว ส่วน native CPI outputs และทุก failure ใช้จากการรันเดิมโดยไม่รันภาพซ้ำ

[Initial environment event](../provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/SHARED_ENVIRONMENT_EVENT.json) · [Original interruption evidence](../provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/INITIAL_TRIAL_TERMINATION.json) · [Restored profile freeze](../provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/RESTORED_PROFILE_FREEZE.json)

## 2. คะแนนหลักภายใต้ STRICT_COMPLETE

| Population | Model | GT IoU | Complete frames | Failed / Invalid | G_loc / G_sem | Status | Q_person_sem_GT หลัก |
|---|---|---:|---:|---:|---:|---|---:|
| main | CPI_R50_CIHP | 0.50 | 4,436/4,961 | 525 / 0 | 17,434 / 17,390 | INCOMPLETE | N/A — INCOMPLETE |
| main | CPI_ConvNeXtB_CIHP | 0.50 | 4,920/4,961 | 40 / 1 | 17,434 / 17,390 | INCOMPLETE | N/A — INCOMPLETE |
| main | CPI_R50_CIHP | 0.75 | 4,436/4,961 | 525 / 0 | 17,434 / 17,390 | INCOMPLETE | N/A — INCOMPLETE |
| main | CPI_ConvNeXtB_CIHP | 0.75 | 4,920/4,961 | 40 / 1 | 17,434 / 17,390 | INCOMPLETE | N/A — INCOMPLETE |
| reference | CPI_R50_CIHP | 0.50 | 4,475/5,000 | 525 / 0 | 17,548 / 17,504 | INCOMPLETE | N/A — INCOMPLETE |
| reference | CPI_ConvNeXtB_CIHP | 0.50 | 4,959/5,000 | 40 / 1 | 17,548 / 17,504 | INCOMPLETE | N/A — INCOMPLETE |
| reference | CPI_R50_CIHP | 0.75 | 4,475/5,000 | 525 / 0 | 17,548 / 17,504 | INCOMPLETE | N/A — INCOMPLETE |
| reference | CPI_ConvNeXtB_CIHP | 0.75 | 4,959/5,000 | 40 / 1 | 17,548 / 17,504 | INCOMPLETE | N/A — INCOMPLETE |

**N/A ไม่ใช่ศูนย์และไม่ใช่คะแนนคุณภาพต่ำ** หมายถึงระบบไม่มีคะแนนหลักที่ครบประชากรตาม STRICT_COMPLETE รายงานยังคงแถว INCOMPLETE และ diagnostics ตามข้อตกลง

ภาพที่ไม่อยู่ main แต่ยังอยู่ reference ไม่ทำให้ main ล้มเหลวโดยอัตโนมัติ แต่ทุก failure ภายใน main ยังคงนับตาม population ของ main ไม่มี post-hoc exclusion

ConvNeXt-B มี ledger เดิม3,779ภาพ ก่อน process หยุดโดยไม่มี terminal manifest พบ output ของภาพ0034896เขียน NPZ ไม่สมบูรณ์ จึงเก็บเป็น INVALID/UNRESOLVED_INTERRUPTION ไม่ซ่อมหรือรันซ้ำ จากนั้นทำเฉพาะ1,220ภาพที่ยังไม่เคยเริ่มด้วย weights/settings เดิม และรวม ledger ตาม reference membership โดยไม่เปลี่ยน source files การโหลดโมเดลเพิ่มเพื่อทำภาพที่ยังไม่เริ่มไม่ใช่การ retryภาพที่ล้มเหลว

## 3. สิ่งที่ผลนี้บอกได้

- Observation: ตารางข้างต้นแสดงการรันจริงและ failures ภายใต้ native FP32 configuration บน Tesla T4 ไม่ใช่การรับรองทุกภาพจาก TRAIN smoke สามภาพ
- Interpretation: CUDA OOM เป็นข้อจำกัดของ configuration/resource path ที่รัน ไม่ใช่หลักฐานว่าโมเดลมี semantic accuracy ต่ำ หรือด้อยกว่าด้าน architecture/CCTV robustness
- คะแนน success-only เก็บไว้เพื่อวิเคราะห์การทำงานเท่านั้น หากชุดภาพสำเร็จต่างกัน ห้ามใช้จัดอันดับระบบหรือแทนคะแนนหลัก
- ไม่ปรับ confidence, resolution, precision, taxonomy หรือ chunk native processing หลังดู VAL เพื่อทำให้รอบนี้ผ่าน

## 4. วิธีการและข้อจำกัด

เป็น custom CCIHP coarse body/clothing evaluation ไม่ใช่ official native CIHP leaderboard; CIHP prediction taxonomy ถูก project อย่าง explicit ไปยัง CCIHP-derived common targets GT domain เป็น released-annotation-relative, unknown/unsupported GT void ตาม policy เดิม และ native identity แยกจาก YOLO opportunity identity

TP/FP/FN เป็นผลเทียบ released annotations ภายใต้ bbox matching ที่รับรอง FP ไม่ได้พิสูจน์ว่าไม่มีคนจริง ภาพ main/reference มี membership ซ้อนกันและไม่ใช่ประชากรอิสระ Controlled set ไม่ได้รับรองว่าปลอด checkpoint training exposure ทั้งหมด Mapping confidence ยังคง ACCEPTED_WITH_INDIRECT_EVIDENCE ไม่ใช่ DIRECT_VERIFIED

ไม่ได้วัด clean repeated timing/FPS/VRAM และไม่สร้าง cost ranking ไม่มีการประเมิน CCTV, training, fine-tuning, hybrid, สีหรือ attributes

## 5. หลักฐานและขั้นตอนถัดไป

- [Canonical quality results](../metrics/first-cohort-benchmark-20261016T094257313856Z/QUALITY_RESULTS.csv)
- [Operational success-only diagnostics](../metrics/first-cohort-benchmark-20261016T094257313856Z/OPERATIONAL_SUCCESS_ONLY_DIAGNOSTICS.csv) — ไม่ใช่คะแนนหลักและไม่ใช้จัดอันดับ
- [Failure inventory](../metrics/first-cohort-benchmark-20261016T094257313856Z/FAILURES.csv)
- [Final validation](../provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/FINAL_BENCHMARK_VALIDATION.json)
- [User approval](../provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/USER_APPROVAL.json) · [Original freeze](../provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/FREEZE.json)
- หากจะทดลอง precision/resolution/chunking/resource policy ใหม่ ต้องกำหนดเป็น configuration revision และขออนุมัติแยก ไม่เริ่มต่ออัตโนมัติ

**จบรอบที่อนุมัติ — ไม่เริ่ม experiment เพิ่ม**
