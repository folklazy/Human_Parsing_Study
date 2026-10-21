# Artifact storage and Git tracking

ตำแหน่งเชิงตรรกะเป็น workspace-relative ดู [location specification](../manifests/ARTIFACT_LOCATIONS.json) ไม่มี resolver/runner ใหม่ใน SETUP

## Bindings

`HPB_WORKSPACE_ROOT` หมายถึง Human-Body-Extraction root ให้ tooling ภายหลังรับ CLI/env หรือ resolve จาก workspace layout ไม่ hard-code username เมื่อตั้งใน public clone ต้องชี้ asset workspace ที่จัดเตรียมแยก; parent ของ Git clone ไม่ถือว่ามี datasets เอง

`HPB_ARTIFACT_ROOT` default ที่เสนอสำหรับ outputs ใหม่คือ `<workspace>/Human_Parsing_MHPv2_Study/outputs/human_parsing_benchmark/` ซึ่งอยู่นอก publication Git และไม่ย้าย outputs เก่า **ยังไม่สร้างโฟลเดอร์ output เปล่านี้และยังไม่มี execution config ใช้ binding ดังกล่าว** ขั้น B ต้องนำ specification ไปผูกและตรวจจริง

| Artifact | ตำแหน่งตามหน้าที่ | Git policy |
|---|---|---|
| Dataset originals / checkpoint weights / environments / third-party trees | shared workspace locations เดิม | ไม่ commit หรือคัดเข้า public workspace |
| Raw predictions, masks, logits | `$HPB_ARTIFACT_ROOT/<run_id>/predictions/` | external only |
| Detailed worker/execution logs | `$HPB_ARTIFACT_ROOT/<run_id>/logs/` | external; Git เก็บ failure/completion summaries ที่ redact แล้ว |
| Runtime traces | `$HPB_ARTIFACT_ROOT/<run_id>/traces/` | external only |
| Run-specific caches | `$HPB_ARTIFACT_ROOT/<run_id>/cache/` | external only; shared framework caches เดิมคงไว้ไม่เปลี่ยน |
| Temporary files | `$HPB_ARTIFACT_ROOT/<run_id>/tmp/` | external only; ไม่ลบของเก่าอัตโนมัติ |
| Run identities/config/input/job/artifact manifests, environment references, compact completion/failure summaries | `runs/<run_id>/` | track เมื่อแจกจ่ายได้; ไม่ ignore ทั้ง runs |
| Protocol/config/code/tests, small metrics tables, reports | workspace subdirectories ตามหน้าที่ | track หลัง review; missing/null ต้องมีเหตุผล |

Output ใหม่ต้องใช้ fresh run_id ไม่ overwrite run เดิม; artifact manifest บันทึก logical root, relative path, bytes, SHA256 และ access/redistribution status เมื่อไฟล์เกิดจริง ไม่สร้าง hash เทียมให้ assets ที่ยังไม่อ่าน

Local bindings ที่มี paths เฉพาะเครื่องเก็บใน `local/` หรือ `.env` ที่ ignore แล้ว ไม่มี credentials, signed URLs, company images/camera metadata ใน Git ตัวอย่าง schema ที่ไม่เป็นความลับเก็บ version ได้ แต่ยังไม่สร้าง config เปล่า

`.gitignore` ที่เพิ่มจำกัดเฉพาะ local overrides, cache/tmp และ bulk fallback directories/extensions ไม่ ignore CSV/JSON หรือทุกภาพ/runs แบบเหมารวม GT diagnostic images หรือ outputs ที่อนุญาตเผยแพร่ต้องตรวจสิทธิและข้อมูลส่วนบุคคลก่อน ไม่คัดมาเพียงเพราะไฟล์เล็ก

Historical outputs ยังคง paths เดิมใน evidence records ห้าม rewrite ให้ชี้ artifact root ใหม่ที่ยังไม่ได้ใช้จริง
