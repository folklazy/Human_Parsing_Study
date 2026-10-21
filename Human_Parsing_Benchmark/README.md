# Human Parsing Benchmark

พื้นที่ทำงานหลักของ **แผนปัจจุบัน** สำหรับเปรียบเทียบและคัดเลือก pretrained human parsing checkpoints/configurations เพื่อแยกส่วนร่างกาย เสื้อผ้า และ accessories ที่รองรับ ในงานวิจัยนักศึกษาอิสระแบบ noncommercial academic research

**SETUP_COMPLETE · A_REVIEW_PENDING** — ตั้งพื้นที่และเชื่อมหลักฐานแล้ว ยังไม่ DESIGN_READY / LAUNCH_READY และไม่อนุมัติ inference หรือ benchmark ใหม่

## เริ่มอ่านตรงนี้

ลำดับสำหรับคนและ agent ทุกช่วง: **README → [STATUS](STATUS.md) → [PLAN](PLAN.md) → [relevant decisions](docs/DECISIONS.md)**

| เรื่อง | จุดอ้างอิงหลัก |
|---|---|
| สถานะ งานเสร็จ งานค้าง และ next action | [STATUS.md](STATUS.md) |
| กรอบงาน SETUP → A → B → C → D | [PLAN.md](PLAN.md) |
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

## โครงสร้างและสิ่งที่จะเพิ่มเมื่อจำเป็น

ตอนนี้มีเฉพาะเอกสาร, candidate input, artifact/evidence specifications และ setup provenance ที่ใช้จริง ยังไม่สร้าง protocol/config/script/test เปล่าหรือรายงานผลที่ยังไม่มี

ขั้น A จะเพิ่ม `docs/PROTOCOL_REVIEW.md`, target/mapping/metric proposals ใน `protocol/` และตาราง route/risk ใน `registry/` เมื่อได้ข้อสรุปจริง ขั้น B จึงเพิ่ม `configs/`, `scripts/`, `tests/` ที่ใช้ shared implementation ส่วน `reports/` เกิดเมื่อมี review/readiness/completion/analysis ให้รายงาน

`runs/<run_id>/` เก็บ provenance และ summaries ขนาดเหมาะสมกับ Git; raw predictions, detailed logs, traces, caches และ temporary files ต้องอยู่นอก Git ตาม artifact specification ไม่ ignore `runs/` ทั้งหมด

**Next action:** อ่าน README/STATUS/PLAN แล้วดำเนิน Prompt A เมื่อผู้ใช้ส่งข้อความนั้นมา ไม่มีการ resume benchmark เก่าจากการเปิดโฟลเดอร์นี้
