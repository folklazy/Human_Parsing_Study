# Work log — เก็บ WIP และเปลี่ยนรอบตรวจแผน

## 21 ตุลาคม 2026 UTC — ก่อน Prompt A

คำสั่งปัจจุบันให้เก็บงานค้าง ไม่ทำแผนเก่าให้เสร็จทั้งหมด และไม่ resume งานทดลอง ตรวจสถานะ Git/process และใช้หลักฐานเดิมเฉพาะจุด ไม่รัน dataset audit หรือ tests ชุดเดิมซ้ำเพื่อปิดงานเก่า

### สิ่งที่เสร็จแล้วและนำไปใช้ต่อได้

- ผล CPI cohort เดิมปิด `FINISHED_WITH_INCOMPLETE_SYSTEMS` แล้ว คง STRICT_COMPLETE, INCOMPLETE rows และคะแนนหลัก null; ไม่ได้ retry หรือแก้ผล
- บันทึก preparation วันที่ 20 ตุลาคมระบุ A–D พร้อมเสนอ review, มี TRAIN packets 15 รายการ และสอง QANet candidate/config/jobs ที่ยังไม่อนุมัติรัน ข้อความนี้อ้างรายงานเดิม ไม่รับรองการรันทดสอบใหม่
- บันทึก roster V4 เดิมเป็นการรับรอง candidate pool เท่านั้น ยังใช้เป็นประวัติประกอบได้ ไม่บังคับ roster 19 หรือ QANet proposal เป็น scope ของ Prompt A

### สิ่งที่ยังเป็นร่าง/ไม่ได้ส่งขึ้น GitHub

Roadmap วันที่ 20 ตุลาคมเขียนเนื้อหาแล้วแต่ยังไม่ได้ finalize และอ้าง `PROJECT_ROADMAP_STATUS_V1.json` ที่เดิมยังไม่ถูกสร้าง รอบนี้เก็บสำเนาต้นฉบับพร้อม SHA256 และเพิ่มเฉพาะ WIP banner; เนื้อหาเดิมคงครบ สร้าง evidence record เพื่อระบุข้อจำกัด ไม่รับรอง selection rule หรือทั้งหก work packages เป็นคำสั่งทดลอง

Working copy หลักและ workspace root ไม่ใช่ Git repositories จึงเรียกทั้งคู่ว่า clean/committed ไม่ได้ Public staging เป็นอีก repository: main, HEAD ก่อนงาน `5f1db38c9f63be7256c2f40533ebf5e5fc375f31` ตรง remote และ working tree สะอาด ผลเปรียบเทียบ source-copy manifest เดิม: 752 ไฟล์ตรง fingerprints, README/STATE สองไฟล์ต่าง, ไม่มีไฟล์ต้นทางหาย นี่ไม่ใช่ full Git diff ของ working copy; public README/state มี publication derivation ต่างจาก working copyอยู่ก่อนแล้ว

ซอร์ส/config/หลักฐานใหม่ที่ยังไม่อยู่ใน public snapshot เก็บไว้ที่เดิม บันทึก inventory เฉพาะ authoring areas ในเครื่อง ไม่เหมารวม publish หรือ commit ทั้งต้นไม้ รอบนี้ commit เฉพาะเอกสาร WIP/สถานะ/manifest ที่คัดไว้

### Process ที่ยังทำงานจริง

พบเว็บดูผลเดิม `serve_review_web.py` port 8765, PID 1490036 จึงคงไว้ ไม่ใช่ parser inference ขณะตรวจ T4 ใช้ 0 MiB / utilization 0% และไม่พบ NVIDIA compute process หรือ workspace Python inference script นี่เป็น snapshot เฉพาะเครื่อง/กระบวนการที่ตรวจ ไม่รับรองว่า external process ทุกชนิดหยุดเพราะ usage limit ไม่มีการ kill/resume/change config

### การเปลี่ยนทิศทาง

ผู้ใช้จะส่ง Prompt A และ parser list หลังเก็บ WIP ชุดนี้เสร็จ ยังไม่มีเนื้อหาทั้งสองให้ตรวจ จึงยังไม่ประเมินแผนใหม่และไม่เลือกใช้ roster เก่าแทน เมื่อได้รับให้ตรวจ roadmap เป็นหลักฐานตั้งต้น: คงข้อเท็จจริงที่ยังตรง dependencies, พิจารณาข้อเสนอเดิมใหม่ตาม Prompt A, แยก historical decisions จากข้อเสนอรอบใหม่ ไม่ขออนุมัติเริ่มตรวจซ้ำ

ไม่มี pipeline implementation, inference, benchmark, download, training, VAL tuning, CCTV processing, PPSS activity หรือ YOLO change จากรอบนี้ Public commit เป็น post-work documentation snapshot ไม่ใช่ launch revision

[สถานะเครื่องอ่านได้](STATUS.json) · [หลักฐานเก็บงาน](provenance/WORK_PRESERVATION_20261021.json) · [Roadmap WIP](reports/PROJECT_ROADMAP_TH_20261020.md)
