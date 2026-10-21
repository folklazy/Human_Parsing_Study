# Working directory, publication and naming

## Authoritative versus publication

| พื้นที่ | บทบาท |
|---|---|
| `<workspace>/Human_Parsing_Benchmark/` | Authoritative plans/decisions/status ของงานรอบปัจจุบัน ไม่มี `.git` ใหม่ |
| `<workspace>/Human_Parsing_MHPv2_Study/` | Reusable implementation, historical accepted configs/results, WIP และ assets metadata คงที่เดิม |
| `<workspace>/Human_Parsing_Study_Public/` | Existing publication Git checkout, branch main, remote `https://github.com/folklazy/Human_Parsing_Study.git` |
| `<public-checkout>/Human_Parsing_Benchmark/` | Reviewed publication copy ของ workspace ใหม่ ไม่แก้สองชุดพร้อมกันโดยไม่บันทึก sync |
| `<workspace>/datasets`, `models`, `third_party`, `.venvs` | Shared resources ภายนอก publication Git ไม่ย้าย/duplicate |

เลือกชื่อ Human_Parsing_Benchmark เพราะสื่อ Phase 2–3 และไม่ผูกกับ MHP-v2 หรือเลข implementation การวางที่ root ตามรูปแบบ sibling experiments ของ YOLO ช่วยหาเจอง่ายและไม่ทำให้โค้ดที่ใช้ `__file__.parents[...]` หรือ historical absolute paths เปลี่ยน ไม่ใช่สร้าง research project หรือ Git repo ใหม่

Root และ legacy working study ไม่ได้เป็น Git repositories จึงไม่มี Git working-tree status ให้เรียกว่า clean Git status/commit/push ในรายงานหมายถึง publication checkout เท่านั้น Source snapshots/hash-bound metadata ของ legacy ไม่ได้เท่ากับ commit ของ launch

## Synchronization procedure — workflow เดิม

1. ทำ current planning changes ใน authoritative directory อัปเดต STATUS/WORK_LOG และอ่าน decisions ที่เกี่ยวข้อง
2. เลือก explicit paths; copy เฉพาะ first-party docs/code/config ที่ตรวจแล้วไป publication checkout ไม่ย้ายต้นฉบับและไม่ bulk sync source/assets
3. ตรวจ before/after hashes, diff, links, file rights/secrets/size/symlinks และ update publication allowlist/file manifest + per-work-unit sync record
4. Commit/push ตาม working branch เดิม ตรวจ remote commit และ anonymous reads เมื่อไฟล์เผยแพร่เปลี่ยน ไม่มี force-push/rewrite tags
5. หาก push ติดขัดคง local commit พร้อม PENDING_SYNC reason ไม่ขอ token ในแชท ไม่แก้ scientific status เพื่อให้ดูเหมือน sync สำเร็จ

ไม่สร้าง synchronization daemon หรือระบบ deployment ใหม่ Root README และ legacy README เป็น navigation pointers เท่านั้น PLAN/STATUS ของงานปัจจุบันมีที่เดียวใน workspace นี้ Public mirror ใช้เพื่อเผยแพร่และตรวจอ่าน; local-only source/metadata ที่ไม่ได้ sync ยังไม่ถือว่ามีใน clone

## แบบแผน YOLO ที่อ่านจริง

อ่าน Master README/STUDY_STANDARD และ Largest README/EXPERIMENT_PROTOCOL จาก filesystem ก่อนจัดตั้ง โดยบันทึก file hashes กับ Git revisions ใน setup manifest

นำมาใช้: landing page แยกจาก protocol/results, evidence hierarchy, canonical machine tables, run-specific provenance, fixed history, shared assets ไม่ย้าย และ documentation roles ชัดเจน

ปรับสำหรับ parsing: checkpoint-specific taxonomy, target-person ownership, native versus conditioned routes, GT semantic/localization domains และ selection/timing methodology ต้องตรวจใหม่ใน A

ไม่ยกมา: MOTS20 sequence tables, fixed COCO AP thresholds, tier/model roster, inference defaults, Pareto/winner claims และผลเวลาเดิม ไม่มีตัวเลข benchmark ใหม่จาก SETUP
