# Human Parsing Benchmark

พื้นที่ทำงานหลักของ **แผนปัจจุบัน** สำหรับเปรียบเทียบและคัดเลือก pretrained human parsing checkpoints/configurations เพื่อแยกส่วนร่างกาย เสื้อผ้า และ accessories ที่รองรับ ในงานวิจัยนักศึกษาอิสระแบบ noncommercial academic research

**A_REVIEW_COMPLETE · REVIEWED_PROPOSAL** — มีข้อเสนอจาก code/metadata/หลักฐานจริงแล้ว รอ user decisions สำคัญก่อน DESIGN_READY; ยังไม่ LAUNCH_READY และไม่อนุมัติ implementation/inference/benchmark

## เริ่มอ่านตรงนี้

ลำดับสำหรับคนและ agent ทุกช่วง: **README → [STATUS](STATUS.md) → [PLAN](PLAN.md) → [relevant decisions](docs/DECISIONS.md)**

| เรื่อง | จุดอ้างอิงหลัก |
|---|---|
| สถานะ งานเสร็จ งานค้าง และ next action | [STATUS.md](STATUS.md) |
| Authoritative experiment design และ A–D lifecycle | [PLAN.md](PLAN.md) |
| Protocol review: findings, fairness, gaps และเหตุผล | [reports/HUMAN_PARSING_PROTOCOL_REVIEW_TH.md](reports/HUMAN_PARSING_PROTOCOL_REVIEW_TH.md) |
| Exact checkpoints/routes/roster diff | [checkpoint matrix](registry/CHECKPOINT_ROUTE_REVIEW.csv), [routes](registry/ROUTES_PROPOSED.csv), [diff](registry/ROSTER_DIFF.csv) |
| Mapping/requirements/risk review | [mapping](protocol/NATIVE_LABEL_MAPPING_DRAFT.csv), [requirements](registry/REQUIREMENTS_TARGETS.csv), [risks](registry/FAIRNESS_RISKS.csv) |
| Draft specification และ exact workload proposal | [specification](protocol/REVIEWED_SPECIFICATION.json), [workload](manifests/WORKLOAD_PROPOSAL.json), [new denominators](manifests/POPULATION_DOMAIN_PROPOSAL.json) |
| User decisions / proposals / historical boundaries | [docs/DECISIONS.md](docs/DECISIONS.md) |
| รายชื่อที่ผู้ใช้ส่งให้ตรวจ ไม่ใช่ executable roster | [registry/CANDIDATES.csv](registry/CANDIDATES.csv) |
| โค้ด dataset/checkpoint manifests และผลเดิม | [docs/LEGACY_REFERENCES.md](docs/LEGACY_REFERENCES.md) |
| ที่เก็บ artifacts และ Git/local bindings | [docs/ARTIFACT_STORAGE.md](docs/ARTIFACT_STORAGE.md), [location specification](manifests/ARTIFACT_LOCATIONS.json) |
| หลักฐาน file identities ที่ reuse | [manifests/LEGACY_EVIDENCE.json](manifests/LEGACY_EVIDENCE.json) |
| ประวัติ work units / วิธี sync | [WORK_LOG.md](WORK_LOG.md), [docs/WORKSPACE_LAYOUT.md](docs/WORKSPACE_LAYOUT.md) |

## โจทย์และขอบเขต

Phase 1 YOLO benchmark จบแล้ว ใช้ YOLO26x-Seg เป็น frozen baseline งานปัจจุบันคือ Phase 2–3: เตรียม ตรวจความพร้อม ประเมิน และคัดเลือก parsing configurations โดยใช้ **CCIHP เป็น public selection benchmark หลักตามทิศทางผู้ใช้** การกำหนดนี้ไม่ใช่การรับรองว่า annotations ถูกทุกคนหรือว่าคลาส CIHP/CCIHP ใช้เลขตรงกัน

ต้องพิจารณา native full-frame และ YOLO-conditioned routes ตามความสามารถจริง รวม semantic quality, person ownership/instance quality, speed และ VRAM โดย Prompt A จะกำหนดการทดลองที่เปรียบเทียบกันได้ ขอบเขต timing และการใช้คะแนนคัดเลือก ไม่ยกค่าจาก CPI/MOTS20 หรือแผนเก่ามาเป็น defaults อัตโนมัติ

Phase 4 สี/attributes และ Phase 5 CCTV เป็นบริบทของ requirements สำหรับอนาคต ไม่อยู่ใน execution scope นี้ Person ID ในภาพนิ่งยังไม่หมายถึง Tracking/ReID

## สิ่งที่มีอยู่แล้ว

- YOLO study และ baseline เดิม: คงที่เดิม อ่านอย่างเดียว
- Dataset audits, checkpoint inventory, isolated environments, implementation และ bounded tests: มีหลักฐานเดิมให้ตรวจใช้ซ้ำ ไม่ดาวน์โหลด/ทดสอบทั้งหมดใหม่
- CPI cohort เดิมปิด `FINISHED_WITH_INCOMPLETE_SYSTEMS` คะแนนหลัก null ตาม STRICT_COMPLETE ไม่ใช่ผลของแผนใหม่นี้และไม่มี quality winner
- Roadmap 20 ตุลาคมเป็น WIP ที่เก็บต้นฉบับและ hashes แล้ว รายชื่อ 19 รุ่น/QANet สองตัวเดิมไม่เป็น launch scope ของรอบนี้
- ผู้ใช้ส่งเจ็ด configurations จากห้า families ให้ตรวจใน Prompt A ดู registry; ยังไม่รับรอง readiness, checkpoint bindings หรือ execution

## พื้นที่ทำงานและ Git

Authoritative planning directory อยู่ที่ `Human_Parsing_Benchmark/` ระดับ workspace root ร่วมกับโครงการ YOLO ชื่อไม่ผูกกับ dataset เดียวหรือ version ของ implementation และไม่ต้องย้ายโค้ดเดิม

Reusable implementation/หลักฐานเดิมอยู่ `Human_Parsing_MHPv2_Study/` ตามเดิม ส่วน `Human_Parsing_Study_Public/Human_Parsing_Benchmark/` เป็น **publication copy** ใน Git repository เดิม [folklazy/Human_Parsing_Study](https://github.com/folklazy/Human_Parsing_Study) ไม่ใช่ working copy หลัก ไม่มี `.git` ใหม่และไม่มี automatic sync

Clone จาก GitHub อ่านแผนและตรวจ metadata ได้ แต่ไม่มี datasets/weights/bulk artifacts หรือ implementation ล่าสุดทั้งหมด จึงยัง reproduce benchmark ใหม่ไม่ได้

## Current proposal and authority

ใช้ PLAN.md ต่อเป็น authoritative design ไม่สร้างแผนชื่อ HUMAN_PARSING_EXPERIMENT_DESIGN_TH.md อีกชุด เปลี่ยนบทบาท CCIHP VAL เป็น checkpoint selection ตามคำสั่ง Prompt A อย่างเปิดเผย แต่ห้าม tune mappings/settings จากผล VAL และไม่อ้าง independent final confirmation

เสนอ7 checkpoints / 10 configurations (7 application +3 native reference reused); C3 upper/lower/shoes shared task, C7 body/clothing compatible cohort และ Sapiens body diagnostics แยกกัน ทุกอย่างยัง REVIEWED_PROPOSAL ไม่ใช่การรับรอง roster หรือ execution

Current reports/tables/specificationsมีเนื้อหาจริงแล้ว ไม่มี production configs/scripts/tests ใหม่ เก็บ input evidence และ review verification ใน runs/<review_id> ข้อมูลใหญ่ยังอยู่นอก Gitตามartifact specification

**Next action:** อ่าน review/PLAN และตอบสาม design decisions ที่รวบรวมไว้ จากนั้นจึงอนุมัติ Stage B เฉพาะช่องว่าง implementation/readiness; Stage C full benchmark ต้องอนุมัติแยก ไม่มี automatic resume

### Targeted Prompt A clarification (21 October 2026)

Current [PLAN revision2](PLAN.md) and [review §H](reports/HUMAN_PARSING_PROTOCOL_REVIEW_TH.md#h-การปิดหกประเด็นเฉพาะจุด--revision-2) resolve Dress/Apparel scoring versus execution, route-specific extent claims, selection margin versus uncertainty, interruption recovery proposal and storage accounting. Still REVIEWED_PROPOSAL; no new tests, B execution, inference or benchmark authorization. Draft JSON/CSV values are not active execution configurations.

### Current revision3 — specification closure / B handoff

[PLAN§11](PLAN.md#11-คำตัดสินคงเหลือ--ชุดเดียวก่อน-bfreeze) is the single remaining decision table; [PLAN§13](PLAN.md#13-stage-b-handoff--ระบุงานได้แล้ว-แต่ยังไม่เริ่ม) is the bounded implementation/acceptance handoff. Selectedseven/ten scope is confirmed as proposal, not launchauthorization. ApplicationC3 includes allseven across routefamilies, C7 includes supportedCIHPfour; native references separate. Mapping/evidence/view/eligibility and emptyoutcomes are explicit. Still REVIEWED_PROPOSAL, no Bimplementation/inference. [Revision3review](reports/HUMAN_PARSING_PROTOCOL_REVIEW_TH.md#i-specification-closure-และ-stage-b-handoff--revision-3) · [qualitative sample](manifests/QUALITATIVE_REPORT_SAMPLE_DRAFT.json).
