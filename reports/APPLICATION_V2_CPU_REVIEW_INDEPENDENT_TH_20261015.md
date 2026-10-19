# ตรวจอิสระ: Application V2 CPU Review Fixes

วันที่ตรวจ: 15 ตุลาคม 2026 UTC

**ข้อประเมิน: เห็นด้วยกับข้อค้นพบหลักและแนวแก้ไข แต่ยังรับรอง patched implementation หรือ freeze ไม่ได้** ใน active study ยังเป็นโค้ดเดิม ไม่มี mapping V2 หรือ `test_application_v2_cpu_review.py` ที่รายงานกล่าวถึง รอบนี้ยืนยันข้อผิดพลาดด้วยการรันโค้ดเดิม ตรวจ native source และนับ GT metadata ซ้ำ โดยไม่ apply patch

เอกสารที่ตรวจ: [APPLICATION_V2_CPU_REVIEW_FIXES_TH_20261014.md](../../APPLICATION_V2_CPU_REVIEW_FIXES_TH_20261014.md)

## 1. สิ่งที่ยืนยันได้จริง

| ประเด็นในรายงาน | ผลตรวจอิสระ | ความสำคัญ |
|---|---|---|
| CIHP/LIP class 10 หมายถึงคนละอย่าง | ยืนยันจาก native inventories และ M2FP source ในเครื่อง | ต้องแก้ก่อน semantic scoring |
| V1 ใช้ prediction mapping เดียวจึงแปลง LIP ผิด | รัน `project_prediction([[10]], V1)` ได้ target 2 แทน garment target 5 ของข้อเสนอ | เป็น bug ของ harmonization ไม่ใช่ parser prediction error |
| Invalid class หลุดเมื่อไม่เข้าสู่ semantic matching | ทำซ้ำได้ทั้ง unmatched, unscored GT และ empty GT | ต้อง validate ทุก emitted output ก่อน matching |
| G_sem นอก G_loc ถูกกรองหายโดยไม่ปฏิเสธ | ทำซ้ำได้ใน synthetic input | ต้องตรวจ denominator contract ก่อน filter |
| Human ID ติดลบผ่าน `project_gt` | ทำซ้ำได้ | เป็น defensive validation gap ไม่ใช่หลักฐานว่า source GT มีค่าติดลบ |
| Unowned known semantic pixels ยังอยู่ใน global domain | ยืนยัน: `project_gt` valid แต่ `person_truth` void | รายงานแยก global/person domains ได้ถูกต้อง |
| GT support counts และกลุ่ม Hair/Hat/Others | นับทุกแถวซ้ำแล้วตรง รวม sidecar SHA256 | เป็น metadata consistency ไม่รับรอง physical ownership |

ข้อผิดพลาด mapping ร่วม V1 เป็นข้อผิดพลาดจริงของ implementation เดิมที่ทำไว้ ไม่ควรรอให้เริ่ม benchmark แล้วค่อยแก้

## 2. ทำไมการแก้ class 10 จึงจำเป็น แต่ยังไม่จบ taxonomy

[CIHP native source](../../third_party/human_parsing/M2FP/m2fp/data/datasets/register_cihp_parsing.py) กำหนด ID 10 เป็น `Torso-skin`; [LIP native source](../../third_party/human_parsing/M2FP/m2fp/data/datasets/register_lip_semseg.py) กำหนดเป็น `Jumpsuits` ขณะที่ [candidate V1](../taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V1.json) map ID 10 เป็น `Exposed_torso` สำหรับทั้งสอง taxonomy

การแยก prediction tables และบังคับ `native_taxonomy` จึงเหมาะสม แต่การ map LIP Jumpsuits → Garments ไม่ได้ทำให้ LIP รองรับ Exposed_torso ต้องแยกประเด็น **เลขแปลงถูกต้อง** กับ **checkpoint แสดง semantic distinctions ของ cohort ได้ครบ**

ก่อนรับ V2 ควรตรวจให้ครบ:

- Native taxonomy/catalog ต้องผูกกับ checkpoint variant และ checkpoint hash; ห้ามเลือกจาก architecture name, จำนวนคลาส หรือ labels ที่บังเอิญปรากฏในภาพ
- `validate_prediction_target_support` ต้องดู declared native catalog/mapping ทั้งหมด ไม่ใช่ labels ที่พบใน smoke sample และต้องถูกเรียกจริงก่อน scoring
- Unsupported target ต้องทำให้ cohort scoring ถูกปฏิเสธ ไม่ใช่แค่ warning ที่ caller ไม่อ่าน
- ถ้าเปลี่ยนรายการ target ต้องกำหนด shared GT projection, valid pixels, known negatives และ person support ใหม่ให้เหมือนกันทุกโมเดลใน cohort ไม่ใช่ลบ Torso ออกจาก mean อย่างเดียว
- ตารางนี้ยังเป็น candidate สำหรับ CIHP/LIP ไม่ใช่ universal mapping ของ 20 variants และไม่ได้ตัด FASHN ออกจาก YOLO-conditioned pipeline; mapping/cohort eligibility เป็นคนละเรื่องกับ native instance capability

ควรพิจารณา cohort ที่นิยามร่วมกันได้จริง โดยรักษา body/clothing objective เดิม ไม่เพิ่ม metric หรือ dataset เพื่อกลบความไม่เข้ากัน และไม่เลือก taxonomy จาก validation prediction performance

## 3. Evaluator: ช่องโหว่จริงและขอบเขตที่ต้องตรวจใน patch

ใน [evaluate_persons](../src/application_v2/evaluation.py) ปัจจุบัน การตรวจผ่าน `confusion` เกิดเมื่อพบ GT ที่ semantic-eligible และ prediction จับคู่กับคนนั้นเท่านั้น Synthetic probes ได้ผลดังนี้:

| Input ที่จงใจผิด | พฤติกรรมโค้ดเดิม |
|---|---|
| class 99, ภาพไม่มี GT | ยอมรับและนับ FP 1 |
| class 99, unmatched prediction | ยอมรับและนับ FP 1 |
| class 99, matched GT ที่ G_sem=false | ยอมรับและนับ localization TP |
| class 99, matched scored GT — control | ปฏิเสธ ValueError |
| float labels, ภาพไม่มี GT | ยอมรับ |
| predictions สองคนมีคนละ grid, ภาพไม่มี GT | ยอมรับ |

แนวแก้ในรายงานตรงจุด: ตรวจ schema/labels/dtype/grid ของทุก output ก่อนจับคู่ ข้อมูล decoder ผิดต้องเป็น contract/system failure ไม่ใช่ FP ปกติ ส่วน valid extra prediction ต้องยังเป็น FP

ยังต้องเห็น patch จริงเพื่อยืนยันว่า original frame W/H มาจาก canonical frame contract หรือ frame context ที่เชื่อถือได้ เมื่อ G_loc/G_sem ว่าง การตรวจแค่ predictions มีขนาดเท่ากันพิสูจน์ไม่ได้ว่าเท่ากับภาพจริง และห้าม resize prediction ผิดขนาดเงียบ ๆ เพื่อให้ผ่าน

All-background **common/ownership-derived** mask อาจเป็น final view ที่ชอบด้วย contract เพราะมี native foreground นอก target หรือถูก ownership gate ตัดออก แต่ต้องเก็บ native provenance ไม่เปิดให้ all-background native output สร้าง final person โดยไม่มีหลักฐาน ข้อเสนอของรายงานที่แยก evaluator ออกจาก emission contract จึงถูกต้อง

ช่องโหว่ที่ทำซ้ำนี้เป็น evaluator API gap การมี canonical frame validation ก่อนหน้าอาจกัน input ผิดได้บางกรณี ไม่ใช่หลักฐานว่า class 99 เคยหลุดจากการรันโมเดลจริง หรือผล benchmark ใดผิดแล้ว

## 4. GT sidecars ตรงจริง แต่ต้องแก้ถ้อยคำเรื่อง detection miss

อ่านเฉพาะ metadata ไม่เปิด RGB/GT pixels ไม่แก้ sidecars ได้ผล:

| Population | G_native | Native-known semantic support | Candidate target support |
|---|---:|---:|---:|
| Source 5,000 images | 17,548 | 17,539 | 17,504 |
| Controlled 4,961 images | 17,434 | 17,425 | 17,390 |

ทั้งสองชุดมี 9 native identities ที่ไม่มี known semantic foreground: **8 มี raw label 0 เท่านั้น และ 1 มี raw labels 0 กับ undocumented 22** จึงไม่ควรเรียกทั้งเก้าคนว่า background-only เหมือนกัน

อีก 35 identities มี known foreground แต่นอก candidate targets: Hair 31, Hat 2, Hat+Hair 1, Others 1 ตรงตามรายงาน การไม่อยู่ใน semantic denominator ของ candidate ไม่ได้แปลว่า GT ถูกยืนยันว่าดีหรือโมเดลทำผิด

อย่างไรก็ตาม ประโยค “คนเหล่านี้ไม่ได้ถูกนับว่าโมเดลตรวจพลาด” ควรเปลี่ยนเป็น:

> การไม่มี semantic GT ไม่ใช่ข้อผิดพลาดของโมเดลโดยตัวมันเอง แต่ถ้า identity นั้นอยู่ใน frozen G_loc แล้วไม่มี prediction จับคู่ ยังต้องนับ localization FN ส่วน semantic quality เป็น undefined เมื่อไม่อยู่ใน G_sem

ตรวจด้วย fixture `G_loc=1, G_sem=0, predictions=[]` ได้ `final_fn=1`, localization recall 0 และ semantic score undefined จริง ห้ามยกเว้น localization/coverage denominator เพียงเพราะไม่มี target semantic support

หาก V2 มี GT mapping/catalog **และ GT projection behavior** เท่า V1 จริง สามารถทำ equivalence evidence อ้าง sidecars เก่าโดยไม่เขียนทับ แต่เมื่อเปลี่ยน cohort/GT domain ต้อง version sidecars/support counts ที่ขึ้นกับกติกานั้น ไม่อ้างว่าเลขเดิมคงใช้ได้จากชื่อ mapping อย่างเดียว

## 5. สิ่งที่ยังตรวจรับไม่ได้จาก Markdown

ยังไม่ได้รับ delta patch/code/tests ใหม่ใน active study จึงยืนยันไม่ได้ว่า V2 implementation, 20 regression tests, checker, patch applicability และ 7 new hashes ถูกต้องจริงตามรายงาน

ตรวจแล้ว current source snapshots ยังตรงเดิม และ 4 target files ที่รายงานว่าจะเปลี่ยนยังตรงกับ ZIP ต้นทางทุกไฟล์ Original ZIP SHA256 ตรง record; inventory counts 261 payload entries และ 257 copied source files ตรงรายงาน แต่สิ่งนี้ไม่ใช่การตรวจ patch ที่ยังไม่ได้รับ

คำแยก 83 portable + 20 new = 103 และอีก 26 historical tests ยังไม่ได้รันในเครื่องปลายทางถูกต้อง ไม่ควรนับการรัน 103 ซ้ำเป็น 206 หรืออ้างว่า patched server ผ่านแล้ว

รอบนี้รัน **โค้ดเดิม 109 tests / 6 suites** บน environment ต้นทางผ่านทั้งหมด: Python 3.10.21, NumPy 2.2.6, SciPy 1.15.3, Pillow 11.3.0, PyYAML 6.0.3 ผลนี้แสดงว่าชุด tests เดิมยังไม่ครอบคลุม bug ที่เพิ่งทำซ้ำ ไม่ใช่การหักล้าง review

เมื่อมี patch จริง หาก 20 tests ใหม่เพิ่มจากเดิมครบและ historical suites ยังอยู่ ควรตรวจครบ 129 tests บนต้นทาง รวม solver tie/permutation cases ไม่ต้อง upgrade environment เพื่อเลียนแบบเครื่อง review

## 6. ลำดับดำเนินการที่แนะนำ

1. รับ delta ZIP พร้อม base/new hashes และตรวจ diff ทั้ง 4 modified + 3 added files ตามที่รายงานระบุ เก็บ before snapshots ก่อน apply
2. ตรวจ V2/API/fixtures โดยเฉพาะ native-taxonomy selection, unsupported-target rejection, all-output validation และ G_sem⊆G_loc ไม่ถือว่า test count เป็นหลักฐานเพียงอย่างเดียว
3. Apply เฉพาะไฟล์ที่ตรวจแล้ว รัน source-environment suites และบันทึก changed-source provenance แยกจาก protected immutable assets
4. ผูก versioned config กับ mapping V2, checkpoint taxonomy/catalog, required targets และ GT-equivalence/support evidence โดยเก็บ V1/config/decisions เก่าไว้ ห้าม runtime fallback กลับ V1
5. จึงค่อยปิด semantic/cohort decisions แล้วไป live T3b และ resource-profile gaps ตามแผนเดิม ไม่เริ่ม full benchmark จาก review หรือ patch tests เพียงอย่างเดียว

## หลักฐานของการตรวจครั้งนี้

- [14 bounded probes และ support recount](../outputs/reviews/application_v2_cpu_review_20261015T025542893148Z/PROBES_AND_SUPPORT.json)
- [Base-code regression 109 tests + protected hashes](../outputs/reviews/application_v2_cpu_review_20261015T025542893148Z/BASE_TESTS.json)
- [Original ZIP/current patch-base checks](../outputs/reviews/application_v2_cpu_review_20261015T025542893148Z/PATCH_BASE_REVIEW.json)

Protected artifacts 126 รายการตรงเดิม ไม่มีการแก้ code/config/mappings/sidecars/study state หรือเอกสาร review ของผู้ใช้ ไม่มี inference, download/install, training, full benchmark หรือ PPSS activity ในการตรวจนี้
