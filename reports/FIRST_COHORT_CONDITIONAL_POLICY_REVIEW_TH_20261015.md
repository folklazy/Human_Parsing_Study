# รับรองนโยบายแบบมีเงื่อนไข และตรวจความพร้อมกลุ่มแรก

**สองนโยบาย: ACCEPTED WITH CONDITIONS · implementation รอบนี้: LOCAL TESTS PASS · กลุ่มจริง: NOT FROZEN / SCORING BLOCKED**

การตอบรับของผู้ใช้เป็นการรับรองนโยบายหลังอ่านเอกสาร ไม่ใช่ independent source/log/test certification รายงานนี้แยกผลตรวจที่รันบน server รอบนี้ออกจากการตัดสินใจดังกล่าว ไม่เริ่ม audit ทั้งโครงการใหม่ และไม่เปิด full benchmark

## 1. Accepted decisions ที่บันทึกแล้ว

[Decision record V4](../provenance/APPLICATION_V2_DECISIONS_V4.json) ผูก [executable config V5](../configs/application_v2_first_cohort_v5.yaml) ด้วย content digest; V3/V4 configs เดิมยังคงอยู่

| นโยบาย | เงื่อนไขที่บังคับ |
|---|---|
| STRICT_COMPLETE เป็นคะแนนหลัก | ถ้าผลไม่ครบประชากร comparison run ไม่มีคะแนนหลัก; ไม่เฉลี่ยเฉพาะภาพสำเร็จแล้วใช้ชื่อคะแนนหลัก |
| ระบบไม่ครบยังอยู่ในตาราง | แสดง INCOMPLETE, งานสำเร็จ/ล้มเหลว/invalid/not attempted และ numerator/denominator ของ final-frame stage |
| Operational diagnostics แสดงร่วม | failure ledger, completion rate, stage ledgers และ success-only diagnostic ที่ระบุชื่อ/ตัวหารต่างหาก |
| Valid empty output | เป็น execution success; เมื่อบริบทคะแนนได้รับรองแล้วต้องรับ FP/FN/semantic misses ตาม GT ไม่แปลงเป็น failure |
| ไม่มี post-hoc rescue | model retries เป็น0; duplicate frame attempts ไม่ overwrite failure; ไม่ตัดภาพเฉพาะโมเดลหลังเห็นผล |
| Cohort ตาม capability จริง | ต้อง bind checkpoint/config/source/native class order/mapping/target catalog และ reviewed support evidence; ชื่อ CIHP/LIP ไม่ให้สิทธิ์อัตโนมัติ |
| ไม่ลบ Exposed_torso เฉพาะ LIP | LIP ที่ไม่รองรับยังไม่เข้ากลุ่มที่บังคับ target นี้ |
| ไม่จัดอันดับข้ามข้อสอบ | comparison revision ผูก population, mapping, view/track และ policy; shared view ใหม่ต้องออก revision ใหม่ |

คะแนน strict ไม่ตอบ deployment reliability ครบทั้งหมด Operational diagnostics จึงอยู่ในรายงานหลักด้วย การประเมิน operational quality เต็มรูปแบบยังเป็นโจทย์ที่ต้องนิยามแยก ไม่แอบเปลี่ยน strict main เป็น empty fallback

## 2. สิ่งที่แก้ในโค้ดจริง

- `comparison.summarize_comparison` และ `ConfiguredRunner.comparison_report`: ใช้ population/system roster ที่ประกาศก่อนงาน รักษาระบบที่ขาดผลและให้ main_metrics=null ทั้ง run พร้อม diagnostic แยกตัวหาร
- Run-level semantic quality ใช้ตัวหาร G_sem ทั้งประชากร ไม่เฉลี่ย frame means แบบน้ำหนักเท่ากัน และไม่ใช้เฉพาะภาพที่สำเร็จเป็นคะแนนหลัก
- Reporter ผ่าน runner ปฏิเสธ eligible metric payload ที่ไม่ผูก accepted scoring context ข้อมูลจริงยังไม่มี context ดังกล่าว จึงได้สถานะ BLOCKED_SCORING_POLICY แม้รันทุก engineering frame สำเร็จ
- `cohorts.validate_support_binding` ทำ checkpoint-specific gate ผ่าน shared scorer; semantic support ที่ยัง DRAFT ไม่ผ่าน ชื่อ dataset เหมือนกันแต่ checkpoint hash ต่างกันก็ไม่ผ่าน
- Scoring context ต้องตรง accepted mapping file ที่ executable config อ้าง ไม่ใช่ accepted object ที่แยกจากไฟล์จริง
- Runner ตรวจ config mutation หลังโหลด ป้องกันการเปลี่ยนนโยบายใน memory โดยไม่สร้าง validated runner ใหม่
- Fingerprints รวม strict reporting/cohort policy และ association dependencies แยกจาก GT scoring threshold การเปลี่ยน association ต้องสร้าง derived packet ใหม่ถ้าผล final-person เปลี่ยน; retained native outputs อาจเพียงพอโดยไม่ต้องรันโมเดลใหม่

นี่เป็นการเพิ่ม code/config/tests ภายใน implementation เดิม ไม่มี metric/dataset ใหม่ ไม่มี weighted score

## 3. กลุ่มแรกและหลักฐาน checkpoint

กลุ่มเตรียมตรวจ: **CPI_R50_CIHP / CPI_ConvNeXtB_CIHP, Track T3b** ใช้ full-image native CPI ซึ่งมี internal detector แล้ว association กับ frozen YOLO26x ทั้งระบบ ไม่เรียกว่า crop parser-only comparison และไม่จัดอันดับร่วม T1/T3a

เลือกคู่นี้จากความพร้อมของ lossless per-person output/canonical adapter ไม่ใช้ smoke accuracy เพื่อคัดผู้ชนะ

ตรวจแต่ละ checkpoint แยก: exact SHA256, official source commit, native config source hash, resolved config, strict load evidence, head20classes, native output inventories และ original-grid masks จาก actual TRAIN run ไม่อนุญาต CIHP checkpoint อื่นเข้ากลุ่มโดยชื่อเพียงอย่างเดียว

[Checkpoint support bindings](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/CHECKPOINT_SUPPORT_BINDINGS_DRAFT.json) มี structural_binding=VERIFIED แต่ semantic_mapping_review=DRAFT_NOT_ACCEPTED ยังไม่ใช้ label VERIFIED แทนการรับรอง target semantics

## 4. Mapping / domain: ปิดส่วนไหนแล้ว และยังขาดอะไร

ตรวจ README ผู้สร้าง CCIHP และ source CIHP class inventory/annotation loader อีกครั้ง: CCIHP ID6 คือ Face Mask แต่ native CIHP prediction ID6 คือ Dress; GT6 จึง VOID ใน candidate นี้ ขณะที่ prediction6 map ไป selected coarse garments การเปลี่ยน CIHP upper/coat/dress เป็น coarse union เป็น projection ของ study ไม่ใช่การกู้ native CIHP GT

Target6กลุ่มเดิม: face, torso-skin, naked arms, naked legs, selected garments และ footwear ชื่อ Garments_coarse ไม่ครอบคลุม headwear/gloves/accessories ทุกชนิด รายการ native IDs ที่รวม/ไม่รวมอยู่ใน [mapping evidence CSV](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/CLASS_MAPPING_EVIDENCE_DRAFT.csv) และ [mapping V2](../taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V2.json)

**ตรวจพิสูจน์แล้ว:** GT mapping และ target catalog ของ V1/V2 เหมือนกัน จึง reuse sidecars เดิมได้โดย hash และ GT-projection digest ไม่ต้อง decode validation GT ซ้ำ เปลี่ยนเฉพาะ prediction taxonomy ของ LIP ไม่สร้าง exclusions ใหม่

**ยังไม่รับรอง:** ทุกพิกเซล Category0/Human0 เป็น physical known-negative หรือไม่ และรายละเอียด annotation completeness ไม่ได้ถูกพิสูจน์จากชื่อ background หรือ grid integrity ทั้งยังมี human-without-category/unknown22 ตาม auditเดิม จึงยังไม่สร้าง accepted real-data scoring context

เตรียมสอง domain proposals บน TRAIN `0000930` โดยไม่ใช้ผล prediction เลือก policy:

| Draft domain | Valid pixels ใน TRAIN ภาพนี้ | ข้อจำกัด |
|---|---:|---|
| Released-background candidate | 166,453 | รวม Category0/Human0 เป็น negative โดยสมมติ annotation completeness; ยังไม่รับรองสมมติฐาน |
| Human-envelope-only candidate | 42,969 | ไม่มี whole-background FP coverage จึงเป็นคนละข้อสอบ ไม่ใช้แทน domain แรกอย่างเงียบ ๆ |

ทั้งสอง void unresolved/unsupported GT ตาม shared policy เดียวกัน ไม่ให้ prediction สร้าง void ต่างกันรายโมเดล เก็บ masks แบบ lossless เพื่อ review [TRAIN domain evidence](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/TRAIN_DOMAIN_REVIEW.json) · [domain proposal arrays](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/TRAIN_DOMAIN_PROPOSALS.npz)

## 5. Population และ denominators ที่ตรวจแล้ว

| ประชากรเดิม | Images | G_loc structural draft | G_sem candidate draft | ไม่มี candidate semantic support |
|---|---:|---:|---:|---:|
| original_source_target | 5,000 | 17,548 | 17,504 | 44 |
| overlap_controlled_source_target | 4,961 | 17,434 | 17,390 | 44 |

คน44IDsที่ไม่มี candidate semantic support ประกอบด้วย9IDsไม่มี native known support และ35IDsมีแต่ known labels นอก candidate ไม่ลบออกจาก G_loc และไม่ให้ semantic undefined กลบ localization FN ถ้าอยู่ G_sem แล้ว unmatched ให้คุณภาพ0ในตัวหารเดิม

ตรวจ per-image manifest membership/unique IDs, sums และ sidecar SHA256 แล้ว [population bindings](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/POPULATION_BINDINGS_DRAFT.json) อ้าง exact source files โดยไม่ flatten คนหรือเปลี่ยน source splits

ตัวเลขนี้หมายถึง native Human IDs ไม่ใช่การรับรอง physical person counts ทุกคน การกำหนดประชากรหลัก/reference กับ domain ที่ใช้ยังไม่ accepted รักษาทั้งสอง populationแยกกัน

## 6. Matching กับ prediction-only association แยกกัน

| ขั้น | Draft config / แหล่ง geometry | สถานะ |
|---|---|---|
| T3b association | `first_cohort.draft_association`: YOLO box ↔ native CPI box, IoU0.50, no GT | ผ่าน bounded TRAIN route; ไม่ accepted สำหรับ benchmark |
| Final prediction ↔ GT | `evaluation`: bbox half-open, primary0.50 / secondary0.75; maximize eligible cardinality then summed IoU | กลไกผ่าน fixtures; threshold ยังไม่ accepted |
| Evaluation bbox | native CPI box; GT boxจาก original Human-ID foreground | source/provenanceระบุชัด; policyยังรอรับรอง |
| Conditioning bbox | frozen YOLO26x box | เก็บแยกจาก evaluation bbox |

Immutable IDs + pinned SciPy1.15.3 และ permutation fixtures เป็นหลักฐาน matching logic ไม่ใช่การรับรองว่า threshold0.50เหมาะกับทุกข้อมูล V5แยก threshold dependencies จากกัน; การใช้ค่าเดียวกันใน engineering V4ไม่ใช่การรับรองว่าจะต้องผูกสองขั้นนี้เสมอ

## 7. Actual route รอบนี้

ใช้ **TRAIN `0000930` เพียงภาพเดียว**, 500×346 pixels, ไม่ใช่ validation:

- Frozen YOLO26x รันจริง FP32 ใน environmentเดิม โดยไม่แก้ weights/environment
- CPIทั้งสอง checkpoint รันจริง FP32 ใน isolated legacy environment พร้อม strict pretrained state load
- Association ใช้ predicted boxesเท่านั้น และ export canonical person masks ที่ original resolution พร้อม native+YOLO identities

| Candidate | YOLO opportunities | Native instances | Final persons | Actual components |
|---|---:|---:|---:|---|
| CPI_R50_CIHP | 2 | 2 | 2 | actual YOLO + actual CPI + association |
| CPI_ConvNeXtB_CIHP | 2 | 2 | 2 | actual YOLO + actual CPI + association |

จำนวนเท่ากันไม่พิสูจน์ว่าคุณภาพ mask หรือ GT coverage เท่ากัน ไม่คำนวณ quality score ของภาพนี้ Actual component runใช้ configV4; configV5แยก association/GT matching จากนั้น replay association จาก retained native data ได้ผลตรงกันและสร้าง2canonical V5packetsใหม่พร้อม explicit checkpoint/config/source dependencies ไม่มี GPU inference ซ้ำเพื่อทำ derived evidence

[Actual route outputs](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/live_route/ROUTE_EVIDENCE.json) · [process commands/logs](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/live_route/PROCESS_LOG.json) · [V4→V5 lineage](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/V4_TO_V5_LINEAGE.json) · [V5 reporting output](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/COMPARISON_ENGINEERING_STATUS_V5.json)

Reporterแสดงทั้งสองระบบเป็น **BLOCKED_SCORING_POLICY**, execution1/1 และ main_metrics=null ไม่ปั้นคะแนนหลักจาก accepted synthetic context หรือจากการเห็น outputสำเร็จ

## 8. Runtime profile และขอบเขตคำอ้าง

เป็น sequential detector/parser processes, batch1, FP32, TF32off, warmups0, one engineering frame ไม่ใช่ steady-state timing; detectorและparserไม่ได้ residentบนGPUพร้อมกัน ไม่บวก peaksคนละprocessเพื่ออ้าง joint memory

Native profileมี framework/CUDA/driver/seed/environment lock และ observed dtype/cases ส่วน complete pipelineสำหรับเปรียบเทียบ latency/VRAM ยังต้องกำหนด N-person workload/residency/warmups/clean rounds/boundariesให้ตรงงานจริง ไม่ใช้ cold process wall timeหรือภาพเดียวตัดสินความเร็ว

[Native worker profile](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/live_route/logs/run_cpi_PROFILE.json) · [YOLO engineering profile](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/live_route/YOLO.json) การรันผ่านแสดง executable route ภายใต้ profileนี้ ไม่พิสูจน์ว่าทุกภาพหรือ joint-resident workloadพอดี T4

## 9. Tests, source diff และ preservation

ผลจริงล่าสุด **160 tests PASS**; ไม่ใช้จำนวนเป็นใบรับรองทุกเส้นทาง ตรวจ strict run-completeness, valid empty/FN, retained INCOMPLETE rows, person-weighted denominator, no posthoc retry, checkpoint-specific support, actual configured runner gates, accepted mapping-file binding, config mutation และ comparison revisions

[Commands/logs/source snapshot](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/validation_20261015T085912527266Z/VALIDATION.json) · [source diff](../provenance/RUN_MANIFESTS/first-cohort-readiness-20261015T083834196479Z/validation_20261015T085912527266Z/CHANGES.diff)

Protected hashes126รายการและ frozen YOLO checkpoint ตรงเดิม; original archives stat checksตรงเดิม ไม่มี VAL inference, final benchmark, training, hybrid fusion, color study, CCTV หรือ PPSS activity ไม่มี package install/download ใหม่ในรอบนี้

Remote CPU patch ZIPไม่เป็น gateต่อไปตามที่ผู้ใช้ยืนยัน รักษา provenanceว่าไม่ได้ applyremoteZIP แต่ตรวจ source behaviorปัจจุบันแทน ไม่อ้าง independent reviewer certificationจาก local testsเหล่านี้

## 10. Readiness และขั้นต่อไป

| เรื่อง | ผลตอนนี้ | ก่อน freeze ยังต้องปิด |
|---|---|---|
| Strict primary / incomplete reporting | ACCEPTED + IMPLEMENTED + TESTED | ใช้ผ่าน actual accepted data context ของกลุ่ม |
| Checkpoint-specific cohorts | ACCEPTED + GATE TESTED | Semantic support/mapping evidence ของสมาชิกจริงต้อง reviewed |
| Mapping | Source definitions/projection lineage documented | รับรอง target semantics/coarse unions; ไม่ใช่ native CIHP equivalence |
| GT domain | Two explicit TRAIN proposals; unknown22/human0 policyไม่ซ่อน | หลักฐานหรือข้อจำกัด annotation completeness/known negativesที่ยอมรับอย่างชัดเจน |
| Population | Exact manifests/G_loc/G_sem/support/reasons ตรวจแล้ว | เลือก main/reference roles และ eligibilityของกลุ่มจริง |
| Matching | Independent association/evaluation config + tested logic | รับรอง threshold/geometry source |
| Actual route | PASS bounded TRAIN, two candidates | ไม่ขยายเป็นความพร้อมทุกframe/ทุกsystem |
| Runtime | Actual engineering profile retained | Frozen workload/profileสำหรับคำอ้าง latency/VRAM |
| Full benchmark | NOT AUTHORIZED / NOT STARTED | ขออนุมัติแยกหลัง review gatesครบ |

ไม่ต้องรับรองสองนโยบายเดิมซ้ำ และไม่ต้องรอ universal shared view งานถัดไปควร reviewสิ่งที่เป็นข้อสอบจริงของกลุ่มนี้จาก manifests/evidenceข้างต้น ไม่ย้อน auditทั้งโครงการ ไม่ freezeเพราะมี tests/smokeผ่านเพียงอย่างเดียว
