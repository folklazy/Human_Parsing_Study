# Decisions — current scope and historical boundaries

วันที่บันทึก 21 ตุลาคม 2026 ที่มาเป็น user messages ใน session นี้ ไม่ใช่การรับรองข้อเสนอทุกข้อในเอกสารเก่า

| ID | Decision | Status | ที่มา / ผลต่อการทำงาน |
|---|---|---|---|
| SCOPE | Independent noncommercial student academic research | ACCEPTED_USER_SCOPE | คำชี้แจง Decision 5A ก่อนหน้า; ไม่ใช่ company product R&D และไม่โอนสิทธิ code/weights/dataset โดยอัตโนมัติ |
| BASELINE | Phase 1 จบแล้ว, YOLO26x-Seg frozen baseline | ACCEPTED_USER_DIRECTION | Workflow และคำสั่ง SETUP ปัจจุบัน; คง weights/YOLO results |
| OBJECTIVE | Phase 2–3 เปรียบเทียบ/คัด body/clothing/supported accessories, ownership และ speed/VRAM | ACCEPTED_USER_DIRECTION | Workflow + SETUP; metric definitions/runtime ยังต้อง A review |
| DATASET | CCIHP เป็น public selection benchmark หลัก | ACCEPTED_USER_DIRECTION_NOT_GT_OR_PROTOCOL_CERTIFICATION | คำสั่ง SETUP §2; ไม่แปลว่า native CIHP equivalent หรืออนุมัติใช้ VAL เลือกโมเดล |
| CANDIDATES | ชุดเจ็ด configurations ที่ผู้ใช้ส่งล่าสุด | USER_SPECIFIED_FOR_REVIEW | ตารางผู้ใช้ก่อนคำสั่ง SETUP ดู registry; ไม่ใช่ accepted executable roster, readiness หรือ inference permission |
| ROUTES | พิจารณา native full-frame และ YOLO-conditioned ตามความสามารถจริง | ACCEPTED_USER_DIRECTION | ไม่ force crop หรือ bypass internal detector เพื่อให้ตัวเลขเทียบง่าย |
| FUTURE | สี/attributes/CCTV เป็นบริบทอนาคตในรอบนี้ | ACCEPTED_SCOPE_BOUNDARY | ไม่เริ่ม attribute study หรือ CCTV inference จาก workflow diagram |
| WORKSPACE | Human_Parsing_Benchmark ที่ workspace root; public copy ใน repo เดิม | IMPLEMENTED_WITHIN_USER_SETUP_AUTHORIZATION | ชื่อ/ตำแหน่งเลือกตามสิทธิที่ผู้ใช้ให้; ไม่สร้าง Git หรือย้ายข้อมูลเดิม |
| EXECUTION | SETUP อนุญาตเอกสาร/metadata/Git sync เท่านั้น | ACCEPTED_SCOPE_BOUNDARY | ห้าม inference/smoke/benchmark/training/download/pipeline refactor |
| LEGACY | Roster 19 / two-QANet proposal / roadmap WIP ไม่เป็น launch scope ใหม่อัตโนมัติ | HISTORICAL_NOT_CURRENT_LAUNCH_AUTHORITY | คำสั่งเก็บ WIP และ candidate list ปัจจุบัน |
| CPI | CPI closed run คง INCOMPLETE/null/STRICT_COMPLETE และ ACCEPTED_WITH_INDIRECT_EVIDENCE | PRESERVED_HISTORICAL_ACCEPTANCE | ไม่ retry/ซ่อมผลเดิมหรือ promote evidence confidence |
| SELECTION | Exact split policy/selection rules และความสัมพันธ์กับ historical no-VAL-selection | A_REVIEW_REQUIRED | ยังไม่เปลี่ยน prohibition เดิม ต้องกำหนดก่อนดูผล; คำว่า selection benchmark ไม่ยกเลิกเอง |
| DESIGN | Exact roster/targets/mappings/metrics/config/jobs ของรอบใหม่ | NOT_DECIDED | รอ Prompt A; ไม่เติมจาก filename ล่าสุดหรือ old accepted context |

ไม่มี decision ใดในชุดนี้ให้ Sapiens2 หรือ candidate อื่นมี new inference authorization หรือเป็น license clearance ใหม่ ใช้บันทึกสิทธิ/technical feasibility เดิมตามบริบท ไม่เปิด license audit ทั้งชุดเพื่อจัดโฟลเดอร์

ข้อเสนอใหม่บันทึก PROPOSED พร้อมหลักฐาน/ข้อจำกัดก่อนเปลี่ยน ACCEPTED ตามอำนาจที่ใช้ได้ หาก supersede ให้เก็บแถว/เอกสารเดิมและชี้ตัวแทน ไม่เขียนประวัติให้ดูเหมือนรู้ก่อนทดลอง
