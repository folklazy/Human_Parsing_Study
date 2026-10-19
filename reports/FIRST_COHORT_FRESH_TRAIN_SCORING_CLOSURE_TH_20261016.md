# ปิด integration ของ CPI สองระบบ — fresh TRAIN และ configured scoring

ตรวจจริงวันที่ 16 ตุลาคม 2026 — **PASS ในขอบเขต bounded integration; พร้อมเข้าสู่การพิจารณาอนุมัติ benchmark แยก**

รอบนี้ปิดสามงานที่ผู้ใช้ระบุ: ผูก validation packages เดิมกับ executable config/decision, รันโมเดลใหม่บน TRAIN สามภาพเดิม และนำ final packets เข้า configured scorer/report ทั้งสอง matching views สำเร็จ ไม่เปลี่ยน mapping, thresholds, ประชากร หรือห้านโยบายเดิม ไม่ค้น annotation header เพิ่ม และไม่เปิด taxonomy review ใหม่

## 1. Configuration และ validation packages

- [Executable config V9](../configs/application_v2_first_cohort_v9.yaml) / [Decision V8](../provenance/APPLICATION_V2_DECISIONS_V8.json)
- [Config lineage](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/CONFIG_LINEAGE.json) ยืนยัน mapping/domain/population/matching/runtime ทั้งห้าส่วนเหมือน V8 ทุกค่า
- [Dry-run ปัจจุบัน](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/DRY_RUN_PLAN.json) เลือก CPI_R50_CIHP และ CPI_ConvNeXtB_CIHP พร้อม YOLO26X_FROZEN dependency เท่านั้น ไม่ใช้ legacy FASHN/20-variant fields เป็น roster
- `validation_context_packages` ผูก manifest และ artifact SHA256 เดิม ตรวจ model templates, native model bindings, common projection, domain policy, population membership และตัวหารกับ config ไม่สร้าง GT packages ใหม่

| Population | Images | System-image contexts | G_loc ต่อระบบ | G_sem ต่อระบบ | การอนุญาตรัน |
|---|---:|---:|---:|---:|---|
| Main overlap-controlled | 4,961 | 9,922 | 17,434 | 17,390 | ไม่อนุญาตในรอบนี้ |
| Source reference | 5,000 | 10,000 | 17,548 | 17,504 | ไม่อนุญาตในรอบนี้ |

Main เป็น subset ของ reference; สองแถวไม่ใช่ประชากรอิสระ และไม่ควรรวมตัวหารเข้าด้วยกัน Controlled set ไม่ได้รับรองว่าปลอด checkpoint training exposure ทุกชนิด [ผล binding](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/fresh_train_v1/VALIDATION_PACKAGE_BINDINGS.json) เป็น metadata/hash validation ไม่ใช่ validation inference

## 2. Fresh route ที่รันจริง

ใช้ entry point เดียวกัน `scripts/first_cohort_entrypoint.py` กับ V9 และ `--fresh-train` การตรวจ dry-run ไม่โหลดโมเดล ส่วน fresh mode เปิดโหลดได้เฉพาะ TRAIN integration ที่รับรองไว้

**TRAIN IDs:** `0021834`, `0000930`, `0001368` ใช้ cached RGB และ GT ที่ผูก hash ไว้ ตรวจ original JPEG SHA256 และ strict decoded RGB เท่ากับ fixture ก่อน inference ไม่อ่าน validation RGB เพื่อรันโมเดล

| Component | Environment เดิม | Fresh inference | Precision | หน้าที่ |
|---|---|---|---|---|
| Frozen YOLO26x-Seg | `.venv` | 3/3 ภาพ | FP32 | สร้าง predicted person opportunities |
| CPI_R50_CIHP | `.venvs/parser-legacy-cu113` | 3/3 ภาพ | FP32 | Native full-frame parsing แล้ว associate กับ YOLO |
| CPI_ConvNeXtB_CIHP | `.venvs/parser-legacy-cu113` | 3/3 ภาพ | FP32 | Native full-frame parsing แล้ว associate กับ YOLO |

ตรวจ checkpoint hash ใหม่ทั้งสามตัว; CPI ตรวจ source commit/config hash และ strict checkpoint load Native score thresholds คง R50=0.01 / ConvNeXt-B=0.05; YOLO ใช้ imgsz640, conf0.25, IoU0.7, max_det200, retina masks ตาม config เดิม ปิด autocast/TF32 ไม่ติดตั้ง dependencies หรือดาวน์โหลดเพิ่ม

GPU ที่ตรวจจริงคือ Tesla T4 15,360 MiB, driver 580.178.04; ก่อนเริ่มไม่มี compute job อื่น ใช้ subprocess แยกและโหลดทีละโมเดล ไม่ใช่หลักฐาน joint-resident deployment memory หรือ clean timing comparison

| TRAIN image | YOLO opportunities | Native R50 | Native ConvNeXt-B | Final R50 / ConvNeXt-B |
|---|---:|---:|---:|---:|
| 0021834 | 6 | 2 | 2 | 2 / 2 |
| 0000930 | 2 | 2 | 2 | 2 / 2 |
| 0001368 | 2 | 8 | 3 | 2 / 2 |

จำนวน final เท่ากันไม่ได้แปลว่า mask quality หรือ GT coverage เท่ากัน ตารางนี้แสดง execution/identity accounting เท่านั้น Native instances ที่ไม่ associate ยังคงอยู่ใน retained native inventory ไม่ลบเพื่อทำให้จำนวนดูเท่ากัน

[Process attempts](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/fresh_train_v1/PROCESS_ATTEMPTS.json) / [Worker plan](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/fresh_train_v1/WORKER_PLAN.json) / [Entry-point log](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/FRESH_ENTRYPOINT.log) / [Integration result](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/fresh_train_v1/INTEGRATION.json)

## 3. เส้นทางถึงคะแนนและ report ที่พิสูจน์แล้ว

1. Native API คืน masks บน original grid ตรวจขนาด/label IDs/counts/finite boxes โดยไม่ resize GT
2. Prediction-only association ใช้ YOLO bbox ↔ native parser bbox ที่ IoU0.50 โดยไม่รับ GT
3. Final records รักษา native ID และ YOLO opportunity ID พร้อมกัน เก็บ conditioning bbox แยกจาก evaluation bbox (`NATIVE_PARSER_BOX`)
4. Commit lossless packets จาก fresh outputs และอ่านกลับผ่าน packet integrity validation ก่อน scoring เก็บ native masks/boxes ทั้งชุดไว้ด้วย
5. Project native CIHP labels ด้วย accepted explicit mapping แล้วเรียก `ConfiguredRunner.score_frame` กับ registered TRAIN context และ GT cache เดิม
6. `ConfiguredRunner.comparison_report` รับผลครบ 2 ระบบ × 3 ภาพ ใช้ STRICT_COMPLETE และรายงาน stage rates/denominators ทั้งสองระบบครบ 3/3, G_loc=7 และ G_sem=7 ต่อระบบ

Primary matching0.50 และ secondary0.75 ใช้ config เดียวกัน แต่คนละ effective context fingerprint และ comparison revision ทดสอบว่า secondary scores ไม่สามารถสวมเป็น primary report ได้ Thresholds ไม่ถูกเลือกจากคะแนน

- [Primary frame scores](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/fresh_train_v1/PRIMARY_FRAME_SCORES.json) / [Primary reporter output](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/fresh_train_v1/PRIMARY_REPORT.json)
- [Secondary frame scores](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/fresh_train_v1/SECONDARY_FRAME_SCORES.json) / [Secondary reporter output](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/fresh_train_v1/SECONDARY_REPORT.json)

ตัวเลขในไฟล์เหล่านี้มีไว้ตรวจ integration บน TRAIN เท่านั้น ไม่ใช้จัดอันดับ เลือกโมเดล ปรับ mapping หรือ threshold ยังไม่มีคะแนน validation และไม่มีผล benchmark ทั้งประชากร การอ่าน packets ที่เพิ่งสร้างไม่ใช่การรับรอง standalone cached re-scoring หรือ full workflow resume

## 4. ชี้แจง 190/131 tests และ 126/37 protected files

| หลักฐาน | ขอบเขตจริง | การใช้ในรอบนี้ |
|---|---|---|
| เดิม 190 tests | Application123 + foundation67 จากอีกห้า suites | ใช้ประวัติเดิมตาม scope |
| ล่าสุดก่อนรอบนี้ 131 | Application เท่านั้น: 123เดิม +8 ข้อสำหรับ evidence/replay | ไม่ใช่ full-suite regression เหลือเพียง131 |
| รอบนี้ 138 tests | Application131 +7 checks สำหรับ package binding, dry-run/fresh separation และ secondary scoring binding | รันใหม่ผ่าน พร้อม [log](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/CPU_APPLICATION_TESTS.log) |
| Foundation67 | MHP-v2 reader/contracts/common metrics25; official compatibility19; reassessment7; CCIHP GT8; quality8 | ไม่รันซ้ำ: test files5 และ production modules9 ไม่เปลี่ยนจากหลักฐานเดิม |
| Protected126 เดิม | YOLO six repositories59 + study67 ซึ่งรวม foundation production modules9 | ตรวจ hash ซ้ำครบ126 ตรงทั้งหมด |
| Protected37 ล่าสุด | Historical configs/taxonomy/records อีกชุด; intersection กับ126เท่ากับ0 | ไม่ใช่ subset และแทน126ไม่ได้ ตรวจซ้ำ35ที่ไม่เกี่ยวPPSS |

สองไฟล์ PPSS ในชุด37ไม่เปิดอ่านหรือ hash ใหม่เพราะพัก PPSS ไว้ อ้างผลเดิมเท่านั้น ไม่อ้างว่าตรวจ37ใหม่ครบในรอบนี้ ชุด126ไม่รวม PPSS [Scope reconciliation พร้อมรายชื่อ/hash](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/EVIDENCE_SCOPE_RECONCILIATION.json)

Foundation tests อ้างผลผ่าน67จาก revision ก่อน ไม่รวมเป็นจำนวน tests ที่รันใหม่ครั้งนี้ Snapshot test files สำหรับเทียบมาจาก context-closure validation ก่อนหน้า; production modules อยู่ใน original126 baseline ไม่ใช่การอนุมานจากจำนวน tests อย่างเดียว

ตรวจขนาด/mtime ของ CCIHP ZIP และ DatasetNinja TAR ตรง baseline ไม่อ่าน hash archive ใหญ่ซ้ำ และไม่อ้างว่า stat check เท่ากับ cryptographic audit ใหม่ Original measured YOLO CSVs ใน protected list ไม่เปลี่ยน Hash assurance มีขอบเขตเฉพาะไฟล์ที่บันทึก ไม่ใช่การรับรองทุกไฟล์ใน workspace

## 5. ข้อจำกัดและ readiness

**ปิดแล้ว:** validation preparation binding, fresh two-CPI/YOLO TRAIN path, original-coordinate packets, primary/secondary configured scoring และ strict reporting ทั้งหกงาน

**สถานะพร้อม:** เข้าสู่ separate full-benchmark approval review ของกลุ่มแรก quality-only ได้ โดยไม่ต้องวนห้า policies, channel header หรือความถูกต้องครบทุกคลาสใหม่

**ยังไม่อ้าง:** full-validation inference/capacity, production resume/cached scoring, semantic accuracy certification, statistical comparison, cost ranking หรือความเหนือกว่าสำหรับ CCTV Mapping ยังเป็น ACCEPTED_WITH_INDIRECT_EVIDENCE; ข้อจำกัดหลักฐานภาพขา/รองเท้าเดิมยังเปิดเผย แต่ไม่สร้าง gate ใหม่

`full_benchmark=false` และ scientific freeze=false; current executable entry point รับเฉพาะ TRAIN bounded route Validation packages ผูกใน config แล้วแต่ยังไม่ได้เปิด launch บน validation การขยาย execution scope สำหรับประชากรจริงต้องอยู่ในงานที่ได้รับอนุมัติแยก ไม่ถือว่าผ่าน TRAIN สามภาพเท่ากับรันประชากรเต็มสำเร็จ

## 6. ไฟล์และการรักษางานเดิม

เพิ่ม `validation_packages.py`, `first_cohort_fresh.py`, isolated GPU worker และ preparation/validation scripts; แก้ entry point และ runner/context เฉพาะการเชื่อม fresh TRAIN/secondary configured view คง evaluator math และ numeric projections เดิม

[Validation](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/VALIDATION.json) / [Source changes](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/SOURCE_REVISIONS.json) / [Source diff](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/SOURCE.diff) / [Before archive](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/BEFORE.json) / [Git status](../provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/GIT_STATUS_AFTER.json)

Workspace root และ study ยังไม่มี Git repository; จึงเก็บ before/after hashes, source snapshots และ diff แทน ไม่มี commit/push ไม่เปลี่ยน remote ของ YOLO repositories ไม่มี training, downloads, PPSS, CCTV, hybrid หรือ full benchmark

**หยุดที่ WAITING_FOR_USER_APPROVAL — ยังไม่เริ่ม benchmark**
