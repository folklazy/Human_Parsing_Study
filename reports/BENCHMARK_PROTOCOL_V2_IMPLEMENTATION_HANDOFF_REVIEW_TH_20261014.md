# Review — Protocol V2 Implementation Handoff

วันที่ตรวจ: 14 ตุลาคม 2026 UTC · **REVIEW ONLY — ไม่ freeze หรือเริ่ม benchmark**

เอกสารที่อ่านครบ 819 บรรทัด: [Implementation Handoff](../../BENCHMARK_PROTOCOL_V2_IMPLEMENTATION_HANDOFF_TH_20261014.md)

**คำตอบหลัก: ลงตัวพอสำหรับเริ่ม implementation แล้ว** กติกาที่เพิ่มตอบช่องว่างจาก review ก่อนอย่างตรงประเด็น ไม่พบความขัดแย้งระดับหลักการที่ต้องย้อนออกแบบการศึกษาใหม่ แต่ยังไม่พร้อม full benchmark เพราะ numeric mappings, scoring sidecars, production evaluator, routing และ runner ยังต้องทำและตรวจจริง

สิ่งที่เหลือส่วนใหญ่เป็นงาน implementation ตาม acceptance criteria ที่เอกสารกำหนดแล้ว ไม่ควรนำไปวนเพิ่ม dataset, metrics หรือแผนฉบับใหม่ทั้งหมดอีก การอ่านหรือ review เอกสารนี้ยังไม่ใช่ user acceptance ของ population roles หรือคำอนุญาตรัน benchmark

## 1. ความพร้อมแต่ละระดับ

| ระดับ | ความเห็น |
|---|---|
| Research design / implementation handoff | **พร้อมใช้ส่งต่องาน** หลังเติมคำชี้แจงเล็กน้อยตามข้อ3 |
| Embedded reference evidence | **ตรวจได้และรันซ้ำผ่าน** ตามขอบเขต standalone CPU fixtures |
| Actual cohort taxonomy / G_loc / G_sem | ต้องมี numeric tables/sidecars/hash จริงก่อน score |
| Production evaluator / bbox / routing / failure lifecycle | ต้อง implement และผ่าน actual-code tests |
| Frozen run configuration | ยังไม่ freeze และยังไม่ควรมี score-affecting placeholders |
| Full benchmark execution | ยังไม่เริ่มและไม่อนุมัติจาก review นี้ |

## 2. ส่วนที่ปิดประเด็นเดิมแล้ว

### Per-person FP และการแยก catalog

ใช้ทั้ง cohort target catalog สร้าง predicted foreground แยกจาก K_g ที่ใช้เฉลี่ย semantic IoU เป็นข้อแก้ที่สำคัญ และ fixture แสดงว่า neighbor class ที่เคยซ่อนด้วย global composition ถูกนับ FPจริง คงสูตร GT-supported person quality ได้เมื่อรายงาน foreground/error accounting ร่วมอย่างที่กำหนด

Domain ครอบคลุม known negatives ของเพื่อนบ้าน/ฉากหลัง ไม่จำกัดเฉพาะ GT positives และไม่ใช้ prediction-derived void ช่วยคะแนน กติกานี้ตอบ target-person ownership ได้ตรงกับโจทย์

### Availability และ denominator

เอกสารแยก execution completed, native/final output, target semantic available และ GT-person availability แล้ว รวมคนที่ YOLO พลาดใน G_sem denominator ทำให้ processing success ไม่ถูกตีความเป็น end-to-end coverage

Precision ของ no-positive-output เป็น undefined แต่ miss-inclusive quality/recall เป็น 0 ตามเงื่อนไข GT ต่างกันถูกต้อง ไม่ควรเปลี่ยน undefined เป็น perfect 1 หรือใช้ conditional mean ซ่อน misses

### Failure lifecycle

การแยก person job, native frame job, association stage และ run-load failure รวมถึง root failure_event_id ช่วยไม่ให้นับ frame OOM หนึ่งครั้งเป็นหลาย independent events

**Atomic artifact write กับ frame all-or-nothing เป็นคนละเรื่อง** ข้อแก้นี้ถูกต้อง packet ที่เขียนครบสามารถมี finalized outputs สองคนและ failure ของอีกคนได้ ถ้า system profile/global finalizer รองรับ ไม่จำเป็นต้องทิ้งผลที่ valid เพื่อให้ไฟล์ atomic

การแยก model-system failure จาก external contamination และ unresolved cause เหมาะสม คำกล่าวว่า GPU ทำงานแบบ asynchronous และ empty_cache ไม่ปล่อย live tensors สอดคล้องกับ [PyTorch CUDA semantics](https://docs.pytorch.org/docs/2.14/notes/cuda.html) การตรวจเอกสารนี้ไม่ได้รับรอง actual worker cleanup หรืออนุญาต upgrade environments

### Primary/source sensitivity

ใช้ mapping/domain/K เดียวกันเมื่อจะตีความผลต่างจาก population แก้ confounding ได้ถูกจุด ถ้า source มี supported classes เพิ่ม ให้รายงานแยกตามชื่อที่กำหนด ไม่เปลี่ยน K พร้อม population โดยไม่บอก

เมื่อ scope อนุญาตครบ 5,000 และระบบ stateless/fingerprints ตรง การ infer ครั้งเดียวแล้ว score ทั้ง source และ controlled subset เป็นแนวทางที่ประหยัดและถูกหลัก ไม่ต้อง inference ซ้ำเพื่อสร้างสองตาราง แต่ยังต้องได้รับอนุญาต population จริงก่อน

## 3. คำชี้แจงเล็กน้อยที่ควรเพิ่ม ไม่ต้องรื้อแผน

### 3.1 Native identity กับ conditioned identity

คำว่า **native person emitted** ใน §4 ควรสงวนสำหรับ parser ที่ให้ native instances จริง ส่วน semantic crop parser อาจให้ nonempty native foreground แต่ person identity มาจาก YOLO/ROI ไม่ได้มาจากโมเดลเอง

ตัวอย่าง FASHN pilot มี `FULL_FRAME_SEMANTIC_NO_INSTANCE_IDENTITY` ตาม [registry](../../Human_Parsing_CCIHP_10_Image_Pilot/metrics/MODEL_PILOT_STATUS.csv) ดังนั้นอย่าให้ boolean `identity=True` ใน reference helper ถูกนำไปตีความว่า semantic model มี native-instance capability เมื่อ external adapter แนบ person ID ให้

แนะนำ metadata ที่แยกได้โดยไม่ใช้ model-name branches:

- `identity_origin`: NATIVE_MODEL / YOLO_CONDITIONED / ORACLE_INPUT
- `native_instance_id`: null เมื่อโมเดลไม่มี native instances
- `source_opportunity_id` และ `final_person_id`: identity ของ pipeline ตาม route
- `native_foreground_nonempty`: สถานะmask แยกจาก native instance count

Native-instance count สำหรับ semantic-only model เป็น N/A ตาม capability แต่ final person output ใน T3a ยังมีได้ การยืนยันนี้เป็นเรื่องคำศัพท์/contract ไม่ได้ขัดกับกติกา nonempty output ที่เสนอ

### 3.2 O=0 ต้องระบุว่า rate ของ stage ไหน

ประโยค O=0 แล้ว execution rate undefined ใน §4 เหมาะกับ opportunity/person-job rate แต่ T1/T3b อาจยังมี native frame jobs ที่รันครบ แม้ YOLO opportunities เป็น 0

ให้รายงาน `parser_frame_completion_rate` กับ `opportunity_completion_rate` แยกตาม workload จริง ไม่ถือว่า frame rate ทุกประเภท undefined จาก O=0 ขณะเดียวกัน GT-person target availability ยังเป็น 0 เมื่อไม่มี final P และ G_sem>0 ตามกติกา

หาก profile ตั้งใจ skip native parsing เมื่อ YOLO ไม่มี detections ให้บันทึกเป็น SKIPPED_BY_ROUTING ไม่ใช่ parser failure หรือ completed inference ที่ไม่ได้ทำ

### 3.3 กติกา accepted/config ต้องเป็น authoritative source เดียว

V2, appendix และ handoff เป็นเอกสารร่วมกันหลายฉบับ ควรมี accepted decision record และ versioned executable config เป็นแหล่งค่าที่ runner อ่าน ไม่ให้ runner เลือกเองจาก prose สามฉบับ

เรื่อง controlled 4,961/source 5,000, matching geometry/threshold และ failure unit ยังเป็น **proposed decisions** จนยอมรับและ freeze ค่าจริง Config ต้องมี source/reference/version และ validation status ไม่เปลี่ยน study state ให้ accepted จาก review นี้

ทั้งสามข้อเป็นคำชี้แจงก่อน implement ไม่ใช่การเสนอ tracks,modelsหรือmetricsใหม่

## 4. สิ่งที่ตรวจด้วยการรันจริงในรอบนี้

ก่อน execute อ่าน embedded scripts ครบ ไม่มี model/dataset/project evaluator imports โปรแกรมเป็น bounded CPU fixtures และเขียน JSON เท่านั้น จากนั้นแยกสำเนา reference ออกจาก execution directory เพื่อไม่เขียนทับ saved results ที่แนบ

### Hash fidelity

ตรวจ SHA256 ตาม final-LF conventions ใน handoff ตรง **6/6 รายการ**:

- Embedded Python scripts สองไฟล์
- Embedded saved-results JSON สองไฟล์
- Decisions Appendix ปัจจุบัน
- Review Decisions Appendix ปัจจุบัน

จึงมี reproducibility evidence จริงในเอกสาร ไม่ได้มีเพียงคำกล่าวว่าทดสอบผ่าน

### Re-execution ใน environment ที่มีอยู่

ใช้ `.venvs/mhpv2-stage0/bin/python` โดยไม่ติดตั้งอะไรเพิ่ม:

| Script | ผลรอบนี้ | การเทียบreference |
|---|---|---|
| benchmark_spec_checks_20261014.py | **15 named checks PASS**, รวม 300 assignment graphs ในหนึ่ง scenario | Facts ตรงทั้งหมดหลังแยก version metadata |
| operational_cases_spec_20261014.py | **19 named cases PASS** | JSON ผลลัพธ์ byte-identical กับที่แนบ |

Original reference ใช้ NumPy2.3.5/SciPy1.17.0 ส่วน environment ปัจจุบันใช้ NumPy2.2.6/SciPy1.15.3 จึงไม่อ้างว่า environment หรือ JSON ไฟล์แรก byte-identical Facts/expected results ตรงกัน โดยไม่จำเป็นต้อง upgrade เพื่อให้ version string ตรง

เก็บ source สำเนา, original results, executed results, stdout/stderr และ [VALIDATION.json](../provenance/RUN_MANIFESTS/implementation-handoff-review-20261014T084737558371Z/VALIDATION.json) แยกตาม run timestamp

15 และ 19 เป็นจำนวน named reference cases ของสอง scripts ไม่ใช่ 34 unique production test coverage ไม่บวก 300 graphs เป็น 300 model tests และไม่ใช้ผลนี้อ้าง actual bbox/runner/CUDA/atomic filesystem/CCIHP pipeline ผ่านแล้ว

## 5. งาน implementation ที่เหลือเป็นรายการจำกัดแล้ว

ไม่พบเหตุให้เพิ่ม gates ใหม่กว้างกว่า §7 ของ handoff แนะนำทำตามลำดับนี้:

1. **Decision/config binding:** accepted roles, model/system IDs, schemas, GT-domain/cohort mapping และ actual manifest references
2. **Pure CPU evaluator:** bbox primitive, eligible assignment/fixed K, per-person catalog FP/metrics, availability และ D/O/P accounting พร้อม reference fixtures
3. **Runner/artifact semantics:** partial retention, root failure events, cause/retry, atomic commit, resume/fingerprints และ worker completion ที่ทดสอบ fault injection ได้
4. **Actual track integration:** bounded TRAIN inputs สำหรับ routing/ownership/profile ที่ได้รับอนุมัติ ทำเฉพาะช่องว่าง ไม่ rerun pilot 20 ทั้งชุด
5. **Freeze review:** actual configs/hashes/support counts/resources/scope ครบ ไม่มี score-affecting PENDING ของ track ที่จะรัน แล้วจึงพิจารณาอนุมัติ benchmark

ขั้น 1–3 ยังไม่ต้องมี full validation inference หรือ dataset ใหม่ Pure primitives และ synthetic fault tests ทำให้ตรวจ implementation ได้ก่อนใช้ GPU Native AP wrapper และ historical pilot records คงเดิม เว้นแต่มีการเปลี่ยนที่ได้รับอนุมัติและ versioned ชัด

ถ้า cohort หนึ่งยัง mapping ไม่ได้ ให้รายงานข้อจำกัดของ cohort นั้น ไม่หยุดทุก cohort หรือยุบ taxonomy จนไม่ตอบ body/clothing เพียงเพื่อให้ครบ 20 อันดับเดียว

## 6. ขอบเขตและความเห็นสุดท้าย

อ่าน handoff ครบ, ตรวจ source hashes, รัน standalone fixtures ในพื้นที่แยกและตรวจ current code interface/registry บางส่วน ไม่มี production implementation change, parser/YOLO inference, dataset/PPSS activity, training, downloads หรือ benchmark และไม่แก้เอกสาร handoff ต้นฉบับ

**ลงตัวระดับ design/handoff แล้ว; ยังต้องพิสูจน์ implementation ตามรายการที่เอกสารระบุ** ผมไม่แนะนำให้วนเขียน protocol ใหม่ทั้งหมดอีก งานถัดไปควรเป็น config + code + tests ที่ตรวจได้ โดยเพิ่มคำชี้แจง identity provenance และ stage-specific rates เล็กน้อยก่อนลงมือ
