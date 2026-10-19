# CPI กลุ่มแรก — ปิดงานค้น เตรียมคำขอหลักฐานและงานอิสระ

**SOURCE SEARCH: CLOSED WITH DOCUMENTED BLOCKER · SEMANTIC ACCEPTANCE: PAUSED · FULL BENCHMARK: NOT AUTHORIZED**

รอบนี้รับแนวทางให้หยุดค้น README/annotation sources ตามขอบเขตที่ตรวจครบแล้ว ไม่เพิ่ม tests เพื่อชดเชยหลักฐานที่ไม่มี และไม่เปิดการรับรองห้านโยบายใหม่ งานที่ทำคือเตรียมข้อความขอคำยืนยัน ตรวจ queue ดาวน์โหลดจากแผนเดิม และระบุจุดเชื่อม runner จาก source ปัจจุบัน

## 1. ขอหลักฐานเฉพาะชิ้น: ร่างพร้อม แต่ยังไม่ส่ง

[ร่างข้อความภาษาอังกฤษ](CPI_CHANNEL_CONFIRMATION_REQUEST_DRAFT_20261016.md) ระบุสอง released checkpoint links ของ R50/ConvNeXt-B และขอ ordered output labels IDs 0–19 รวม background หากทั้งคู่ใช้ standard CIHP order โดยไม่มี remapping ให้ยืนยันสั้น ๆ ว่าครอบคลุมสองลิงก์ก็เพียงพอ ไม่ขอ dataset ทั้งชุดหรือประวัติการฝึกทั้งหมด

ผู้รับที่เสนอคือผู้ดูแล [linked upstream](https://github.com/JosonChan1998/CPI-Parser) ซึ่งพบความสัมพันธ์ไว้ในงานค้นที่ปิดแล้ว **ยังไม่มีอนุญาตส่งข้อความ และยังไม่เปิด issue** ผู้ใช้สามารถนำร่างไปส่งเองหรืออนุญาตการติดต่อแยกต่างหาก

การใช้ direct evidence เป็นระดับความมั่นใจที่โครงการเลือกรับรอง ไม่ได้แปลว่าพบว่า CPI ใช้ class order ผิด และไม่ใช่ข้อบังคับสากล semantic acceptance คง INDIRECT_ONLY จนกว่าจะได้หลักฐานที่ตรวจความสัมพันธ์กับสอง release ได้ การติดต่อแล้วไม่ได้คำตอบไม่ทำให้ gate ผ่านอัตโนมัติ

[Contact draft record](../provenance/RUN_MANIFESTS/cpi-independent-preparation-20261016T060059630511Z/CONTACT_DRAFT.json) · [ผลค้นที่ปิดแล้ว](CPI_CHANNEL_ORDER_SOURCE_BLOCKER_TH_20261016.md)

## 2. ดาวน์โหลดที่อนุญาตไว้: ไม่มีไฟล์ที่ขาดในแผนเดิม

ตรวจไฟล์จาก [inventory ปัจจุบัน](../provenance/CHECKPOINT_INVENTORY_CURRENT_V1.json) ครบ **31 path entries**: พบทุกไฟล์และ byte size ตรงรายการเดิมทั้งหมด จำนวน **27 unique checkpoint artifacts** และ SHA256 เป็นหลักฐานจาก inventory ที่ตรวจไว้ก่อนหน้า รอบนี้ไม่ rehash weights ทั้งหมด จึงไม่อ้างว่าเป็นการตรวจ content integrity ใหม่

ตรวจ destinations ของ existing non-Sapiens checkpoint download plans ด้วย พบไฟล์ครบ ไม่มี actionable missing download ในแผนเหล่านั้น จึงไม่ดาวน์โหลดซ้ำหรือเพิ่ม roster เพื่อให้มีงาน acquisition

| รายการยังไม่ได้มาใน registry | หลักฐานเดิม | การดำเนินการรอบนี้ |
|---|---|---|
| M2FP_PASCAL | Official model table ไม่มี checkpoint link ตาม audit ที่เก็บไว้ | คง BLOCKED; ไม่เปิดค้นใหม่ |
| QANet_MHPV2 | ไม่พบ official trained parser release ในตารางที่ตรวจไว้ | คง BLOCKED; ไม่เดาลิงก์ |
| QANet_CIHP_ResNet101 | Official table row ไม่มี download link ตาม audit เดิม | คง BLOCKED; ไม่ใช้ HRNet weights แทน |
| CDGNet_LIP | Trained weights ดาวน์โหลดและ CPU structural inspection ผ่านแล้ว | ไม่โหลดซ้ำ; inference ยัง NOT_TESTED และ license review ยังแยกต่างหาก |

Sapiens2 และ 5B ไม่มีการดำเนินการใหม่หรือเปลี่ยนสถานะสิทธิ์ รอบนี้ไม่ตรวจเว็บโมเดลเพิ่มเติม

[Queue evidence: paths, sizes, prior source hashes และ plan destinations](../provenance/RUN_MANIFESTS/cpi-independent-preparation-20261016T060059630511Z/CHECKPOINT_QUEUE.json)

## 3. เตรียมจุดเชื่อมกับ runner เดิม

รัน entry point เดิมหนึ่งครั้งใน `--dry-run` ด้วย [V7](../configs/application_v2_first_cohort_v7.yaml) ได้ plan ตรงกับหลักฐานรอบก่อน: CPI_R50_CIHP, CPI_ConvNeXtB_CIHP และ frozen YOLO dependency; native thresholds 0.01/0.05, association 0.50, FP32 ไม่โหลด torch/ultralytics/mmcv/mmdet และไม่รัน worker/scoring

| ขั้นที่ต้องเชื่อม | Source ที่มีจริง | สถานะที่ยืนยันได้รอบนี้ |
|---|---|---|
| อ่าน roster/settings | `plan.first_cohort_plan` | Existing dry-run เลือก `first_cohort.models` / `first_cohort.execution_spec` ถูกต้อง |
| Native frame execution lifecycle | `ConfiguredRunner.native_frame` | ระบุตำแหน่งใน source; ยังไม่ได้ต่อ native worker ของกลุ่มแรก |
| YOLO↔native association | `evaluation.associate_native` | รับ prediction records และ threshold; ไม่รับ GT หรือชื่อคลาส |
| Native numeric contract / identity | `contracts.validate_frame` | มี schema ที่รักษา native ID และ YOLO opportunity ID; การตรวจ numeric masks ไม่ใช่ semantic acceptance |
| Lossless artifact export | `artifacts.commit_packet` | มีฟังก์ชันเดิมให้เชื่อม; รอบนี้ไม่สร้าง prediction packets |
| Semantic scoring | `ConfiguredRunner.score_frame` | Channel gate และ accepted-context gate เดิมยังอยู่; ไม่เรียก scorer |
| Comparison report | `ConfiguredRunner.comparison_report` | ใช้ภายหลังเมื่อ population/context bindings ผ่าน; รอบนี้ไม่สร้างผลเปรียบเทียบ |

ข้อจำกัดที่ต้องรักษา: `run_handoff_smokes.py` dispatch หลาย family, `bounded_train_application_v2.py` ใช้ YOLO/FASHN engineering configuration เดิม และ `export_handoff_cpi_contract.py` อ้าง historical handoff V3/active pointers/ตัวอย่างคงที่ จึงนำ entry points เหล่านี้มาเรียกเป็น V7 executor โดยตรงไม่ได้ สามารถนำฟังก์ชัน/adapters ที่เกี่ยวข้องมาเชื่อมผ่าน V7 อย่างชัดเจนภายหลัง โดยไม่สร้าง runner ใหม่ทั้งชุด

เก็บ source symbols/line numbers/hashes และจุดที่ต้องต่อไว้ใน [wiring preparation](../provenance/RUN_MANIFESTS/cpi-independent-preparation-20261016T060059630511Z/RUNNER_WIRING_PREPARATION.json) **นี่คือ source wiring preparation ไม่ใช่ execute path ที่เชื่อมแล้วหรือผ่าน integration** entry point ยังคง DRY_RUN_ONLY ไม่มีการเปิด execution mode

[Dry-run plan](../provenance/RUN_MANIFESTS/cpi-independent-preparation-20261016T060059630511Z/DRY_RUN_PLAN.json) · [คำสั่งและผลรัน](../provenance/RUN_MANIFESTS/cpi-independent-preparation-20261016T060059630511Z/DRY_RUN_EXECUTION.json)

## 4. ทางไปต่อและขอบเขต

1. ผู้ใช้ส่งร่างเองหรืออนุญาตการติดต่อ upstream; เก็บคำตอบต้นฉบับและ source URL โดยไม่ตั้งชื่อ channel แทนผู้สร้าง
2. งานเชื่อม worker/lifecycle/association/native export เตรียมได้แยกจากชื่อ channel แต่ต้องไม่ข้าม semantic scoring gate และไม่เรียก benchmark จาก config นี้
3. หลังหลักฐานผ่าน จึง materialize accepted parser contexts ของประชากรตาม manifests/policies และตรวจ actual execute route ก่อน readiness review; ไม่ reconstruct GT สามภาพเดิมซ้ำเมื่อ dependencies ไม่เปลี่ยน
4. Full benchmark ยังต้องได้รับอนุมัติแยก ไม่ใช้การรับรองนโยบายหรือการตอบ class order เป็นสิทธิ์เริ่มรัน

ไม่มี tests เพิ่ม/รันซ้ำ, inference, accepted contexts ใหม่, model loading, downloads/installs, GT reconstruction, dataset/YOLO/PPSS changes หรือ remote Git actions การแก้รอบนี้อยู่ในเอกสารและ provenance/navigation/state เท่านั้น
