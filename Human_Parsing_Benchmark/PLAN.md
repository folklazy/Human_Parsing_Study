# Human Parsing Benchmark — แผนงานปัจจุบัน

สถานะ: **FRAMEWORK_ONLY · NOT_AN_ACCEPTED_EXECUTABLE_PROTOCOL**  
ที่มา: คำสั่งจัดตั้ง workspace ของผู้ใช้ วันที่ 21 ตุลาคม 2026 ดู [decisions](docs/DECISIONS.md) และ [status](STATUS.md)

เอกสารนี้เป็นจุดอ้างอิงเดียวของแผนรอบใหม่ รายงาน/roadmap เก่าใช้เป็นหลักฐานตั้งต้น ไม่เป็นคู่มือสั่งรันปัจจุบัน การแก้แผนใช้ path คงที่และ Git history; protocol/config versions และ run IDs เก็บใน metadata

## ลำดับงานและเงื่อนไขจบ

| ขั้น | งานและผลส่งมอบ | เงื่อนไขจบ / ขอบเขตอำนาจ |
|---|---|---|
| SETUP | Navigation, user candidate input, decisions, references, artifact locations, preservation and Git sync | เอกสารอ่านได้เอง, links/ignore ถูก, งานเดิมไม่ถูกย้าย/เขียนทับ; ไม่เท่ากับ design/launch readiness |
| A — review/design | ตรวจ Prompt A กับ workspace จริงและหลักฐานเดิม; เสนอ comparable routes/cohorts, target semantics, GT/domain, population/split, metrics, selection rule และ runtime workload | PLAN/protocol review มีข้อเสนอพร้อมที่มาและ unresolved decisions เฉพาะจุด; exact roster/config/jobs ต้องมาจากการตรวจ ไม่เติมใน SETUP; ไม่ implement execution หรือ inference จากขั้นนี้ |
| B — implementation/readiness | หลังอนุมัติขอบเขต: reuse code, ผูก config/decision/asset identities, ปิดช่องว่าง scorer/runner และ verification ที่จำเป็น | Readiness report และ exact launch package ผ่าน gates ที่กำหนด; bounded GPU work ต้องมี authorization ที่ใช้ได้; การผ่าน B ยังไม่อนุมัติ full benchmark |
| C — batch execution | หลังมี explicit batch approval: freeze manifests/settings แล้วทำเฉพาะ approved jobs และเก็บ completion/failure/provenance | ประชากรและตัวหารตรวจได้; failures/incomplete คงแสดงตาม accepted policy ไม่ซ่อมด้วย successful-subset score; ไม่ tune จากผล held-out โดยเงียบ |
| D — analysis/selection | วิเคราะห์ผลตาม selection/evaluation rules ที่กำหนดก่อนใช้คะแนน รวมรายละเอียด body/clothing, ownership และต้นทุนที่วัดจริง | ผลคัดเลือก/ยังสรุปไม่ได้พร้อมเหตุผล ข้อจำกัด และข้อเสนอ field test; ไม่เริ่ม color/attributes/CCTV/hybrid อัตโนมัติ |

## กรอบการออกแบบที่ต้องรักษา

CCIHP เป็น public selection benchmark หลักตามทิศทางผู้ใช้ แต่ target/mapping/population และความหมายของ selection versus held-out reporting ยังต้องตรวจใน A ใช้ CCIHP-specific GT อย่างเปิดเผย ไม่เรียกคะแนนว่า official native CIHP ผลที่ coarse หรือ unsupported ต้องอธิบายว่าตอบโจทย์รายละเอียดใดได้จริง

Native full-frame กับ YOLO-conditioned เป็นคนละระบบ/เส้นทางตามความสามารถ checkpoint ต้องแยก native instance identity จาก conditioning/final pipeline identity และไม่ซ่อน missed persons ในตัวหาร ระบบที่เสร็จ native smoke ไม่ได้พร้อม benchmark โดยอัตโนมัติ

Speed/VRAM เป็นวัตถุประสงค์ของการศึกษารอบใหม่ แต่ต้องกำหนด workload, synchronization, precision, stage boundaries และ resource profile ก่อนอ้างต้นทุน ไม่จัดอันดับจาก smoke diagnostics หรือ CPI quality-only เดิม

Historical ban on VAL-based tuning/selection ไม่ถูกยกเลิกเพียงเพราะใช้คำว่า selection benchmark ให้ A แยก development selection กับ frozen reporting หรือเสนอการเปลี่ยน policy อย่างเปิดเผยเพื่ออนุมัติก่อนใช้คะแนน ไม่แปลง accepted historical settings เป็น config ของทุกโมเดล

## Deliverables จาก Prompt A–D → path หลัก

| ชื่อผลงาน/หน้าที่ | Path ที่จะใช้ |
|---|---|
| Experiment design / work plan | `PLAN.md` |
| Protocol review และเหตุผล | `docs/PROTOCOL_REVIEW.md` — ยังไม่สร้างเพราะ Prompt A ยังไม่รับ |
| Decisions และสถานะ accepted/proposed/superseded | `docs/DECISIONS.md` |
| Candidate/route/asset/risk tables | `registry/` — ขณะนี้มีเพียง user candidate input |
| Targets/mappings/metrics/runtime specification | `protocol/` — สร้างเมื่อมีรายละเอียดจริง |
| Executable configurations | `configs/` — เกิดใน B หลังหลักฐาน/การอนุมัติที่จำเป็น |
| Population/workload/job manifests | `manifests/` — แยก exact jobs จาก references เดิม |
| Readiness report | `reports/READINESS.md` พร้อม revision/run references |
| Batch completion | `reports/BATCH_COMPLETION.md` เป็น index ของ immutable per-run summaries |
| Final parsing analysis/selection | `reports/PARSING_ANALYSIS.md` ตามกติกาที่รับรอง |
| Run-specific immutable evidence | `runs/<run_id>/` และ artifact references |
| Current status / append-only history | `STATUS.md` / `WORK_LOG.md` |

ยังไม่กำหนด exact executable roster, targets, mappings, metric thresholds, image count หรือ job counts ใน SETUP รายชื่อที่ผู้ใช้ส่งคือ input สำหรับ review เท่านั้น

## งานถัดไป

**Prompt A ยังไม่ได้รับ** ให้ตรวจแผนตามข้อความนั้นต่อในพื้นที่นี้ ไม่ย้อนปิด roadmap WIP ทั้งหมด ไม่รัน smoke ทั้ง inventory ซ้ำ และไม่ resume entry points เก่า
