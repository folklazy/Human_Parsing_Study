# เตรียม launch benchmark กลุ่มแรก — รออนุมัติแยก

16 ตุลาคม 2026 — **PASS_PREPARATION_ONLY**

ปิด bounded integration แล้ว ไม่เปิดประเด็น mapping หรือห้านโยบายเดิมใหม่ รอบนี้เตรียม execution scope ของ validation, ตรวจ launch plan และผูก reproducibility candidate ให้ review ได้ ข้อความความคืบหน้าของผู้ใช้ **ไม่ถือเป็นคำอนุมัติ benchmark** จึงคง `full_benchmark=false`, `execution_authorized=false` และยังไม่ตั้ง config เป็น FROZEN

## ขอบเขตคำอนุมัติที่ขอ

| รายการ | ค่าเดิมที่คงไว้ |
|---|---|
| ระบบ | CPI_R50_CIHP และ CPI_ConvNeXtB_CIHP ใน T3b พร้อม frozen YOLO26x |
| Precision | FP32; native model processing เดิม ไม่ bypass internal detection |
| Main | 4,961 ภาพ; G_loc 17,434 / G_sem 17,390 ต่อระบบ |
| Reference | 5,000 ภาพ; G_loc 17,548 / G_sem 17,504 ต่อระบบ |
| Mapping / domain | Accepted V3, ACCEPTED_WITH_INDIRECT_EVIDENCE, released-annotation-relative |
| Association | Prediction-only bbox IoU 0.50; YOLO box ↔ native parser box ไม่ใช้ GT |
| Final GT matching | Native parser bbox เป็น evaluation box; IoU 0.50 หลัก /0.75 เสริม |
| Native confidence | R50=0.01 / ConvNeXt-B=0.05 ไม่ปรับให้เท่ากันหรือ tune จาก VAL |
| Failure | STRICT_COMPLETE; INCOMPLETE rows และ diagnostics ต้องอยู่ใน report; valid empty เป็น execution success |
| การตีความ | Quality-only; ไม่จัดอันดับเวลา/FPS/VRAM ไม่อ้าง backbone causality หรือ CCTV superiority |

## 1. Inference ครั้งเดียว แล้วรายงานสองประชากร

ใช้ ordered reference manifest 5,000 เป็น inference population เดียว Main 4,961 เป็น subset เดิม ไม่สั่งรันซ้ำอีกชุด

- YOLO: **5,000 frame jobs** ใช้ detector artifacts ร่วมกับทั้งสอง CPI
- CPI: **10,000 frame jobs** =2 checkpoints ×5,000 ภาพ ไม่ใช่ 19,922 งานจากการบวกสอง scoring populations
- Scoring contexts: main 9,922 / reference 10,000 ผูก membership, original RGB hash, GT/domain และ checkpoint ตาม population
- Shared image/context และ threshold ต้องตรงกันก่อนใช้ per-frame score ร่วมกัน Reporter สร้างคนละ population fingerprint และ comparison revision

หากภาพที่อยู่นอก main แต่ยังอยู่ reference ล้มเหลว main อาจยังครบได้ ส่วน reference ต้องคง INCOMPLETE และไม่มี main score ภายใต้ STRICT_COMPLETE ห้ามเปลี่ยน membership หลังเห็นผล Main ไม่ใช่การรับรองว่าปลอด training exposure ทั้งหมด และสอง population ไม่ใช่ independent samples

## 2. สิ่งที่เชื่อมเพิ่ม

- [Config V10](../configs/application_v2_first_cohort_v10.yaml) / [Decision V9](../provenance/APPLICATION_V2_DECISIONS_V9.json): เพิ่ม `validation_launch` เป็น **PROPOSED**; accepted bindings เดิมไม่เปลี่ยน
- [Launch plan](../provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/LAUNCH_PLAN.json) ตรวจ exact ordered IDs/roster/settings/counts และใช้ inventory ที่มี hash แล้วจับ RGB จาก DatasetNinja TAR กับ GT ของ CCIHP ด้วย byte SHA ไม่อาศัยชื่อไฟล์อย่างเดียว ไม่มีการอ่าน dataset pixels ในรอบนี้
- เพิ่ม `--validation-plan` และ approval-gated `--validation-run` ใน entry point เดิม พร้อม isolated worker สำหรับ validation; ไม่มีการดาวน์โหลดหรือติดตั้ง environment ใหม่
- Lazy reader เตรียมตรวจ JPEG bytes/strict decoded RGB/dimensions และคืน GT ทีละภาพโดยเทียบ decoded contract/person hashes เดิม ไม่มีการสร้าง GTpackages ทั้งชุดใหม่
- รักษา native ID/YOLO opportunity แยกกัน, lossless native/final masks, original-coordinate geometry และ configured scorer/report เดิม
- Failure ledger เก็บแต่ละภาพ รวม load failures/worker aborts/unattempted work; ไม่ retry ภาพหรือปรับ threshold เพื่อให้ครบ การปล่อย GPU cache หลัง failure ไม่ใช่การรันภาพนั้นซ้ำ

ใหม่ `first_cohort_validation_worker.py` ยัง **NOT_RUN บน GPU** เพราะยังไม่มีคำอนุมัติ validation inference ไม่ใช้ CPUfixtures อ้างว่า validation ประชากรเต็มรันผ่านแล้ว Model API/processing อิงเส้นทาง native เดิมที่มี fresh TRAIN evidence; worker และ assembly/scoring สำหรับ TRAIN เดิมยังมี hash ตรงหลักฐานรอบก่อน ส่วน runner เพิ่ม optional benchmark/population path และผ่าน CPUregression ปัจจุบัน

## 3. ผลตรวจจริงรอบนี้

| ตรวจ | ผลและขอบเขต |
|---|---|
| Application tests | **147 ผ่าน** =138 เดิม+9 สำหรับ validation launch; [log](../provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/CPU_APPLICATION_TESTS.log) |
| Population fixtures | Perfect output, distinct population revisions, excluded-reference failure, context mismatch, threshold-view mismatch ผ่านด้วย synthetic arrays ไม่ใช่ VAL predictions |
| Source readers | Synthetic JPEG/ZIP: strict decode, coordinate mismatch, decoded GT/person contract ผ่าน ไม่ใช้ภาพ VAL มาตั้งค่า |
| Approval gate | Public `--validation-run` ถูกปฏิเสธก่อนสร้าง run directory หรือเรียก GPU process; [log](../provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/UNAPPROVED_LAUNCH.log) |
| Syntax | ตรวจ new route/worker ใช้ syntax ที่ Python3.9 เดิมรองรับ |
| Protected artifacts |126 รายการเดิม hash ตรงทั้งหมด; archive stat ตรง baseline ไม่ hasharchive ใหญ่ซ้ำ |
| Foundation 67 | ใช้หลักฐานรอบก่อนต่อ; production modules ไม่เปลี่ยน ไม่อ้างว่าเพิ่งรันครบ 214tests |
| Mapping/five policies | เหมือน V9 ทั้งหมด ไม่ขอรับรองใหม่ |
| GPU/model inference | **ไม่รันในรอบนี้** |

รายละเอียด [validation](../provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/VALIDATION.json) / [fixtures](../provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/LAUNCH_FIXTURES.log) / [reproducibility candidate](../provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/LAUNCH_FREEZE_CANDIDATE.json)

## 4. การล็อก candidate และการอนุมัติ

`LAUNCH_FREEZE_CANDIDATE.json` บันทึก config,decision,code,input inventory,GTpackage และ launch-plan hashes ไว้แล้ว เป็น **candidate lock เพื่อ review ไม่ใช่ scientific freeze หรือ execution permission**

เมื่อได้รับคำอนุมัติขอบเขตในตารางข้างต้น จึงออก accepted execution decision/config revision, คงค่าทางวิทยาศาสตร์เดิม ตรวจ plan/hashes อีกครั้งและ freeze ก่อนเริ่ม validation inference ไม่ต้องย้อนหา header รับรองห้านโยบาย หรือขยาย roster ปัจจุบันการแก้ flag ใน YAML อย่างเดียวไม่ผ่าน gate

Stage0 integration success ไม่รับรองว่า full population จะไม่มี OOM/contract errors หากไม่ครบให้รายงานตาม STRICT_COMPLETE ไม่มี silent fallback หรือ success-only score แทนคะแนนหลัก และไม่เปลี่ยน metric/denominator หลังเห็น VAL

## 5. สถานะและคำขออนุมัติ

พร้อมให้พิจารณาอนุมัติ benchmark กลุ่มแรกตามตาราง โดยใช้ existing local assets เท่านั้น ไม่มี checkpoint download ใหม่ ไม่แตะ PPSS, datasets ต้นฉบับ, frozen YOLO weights/results, company CCTV, training, hybrid หรือ color study ไม่ commit/push

**WAITING_FOR_USER_APPROVAL — ยังไม่เริ่ม validation inference หรือ full benchmark**
