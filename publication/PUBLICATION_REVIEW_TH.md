# ชุดตรวจรับก่อนเผยแพร่ Public

## เป้าหมายที่เสนอ

Owner/repo: **folklazy/Human_Parsing_Study**; visibility ที่เสนอ: **PUBLIC**. ยังไม่สร้าง remote และไม่มี public URL/remote commit/tag ที่อ้างว่าสร้างสำเร็จ การอนุมัติ public จะขอครั้งเดียวหลังเตรียมชุดนี้ครบ

Working copy หลักยังเป็น `Human_Parsing_MHPv2_Study`; staging copy คือ `Human_Parsing_Study_Public` ไม่มีการย้ายหรือลบโครงการเดิม Source/config ที่คัดลอกบันทึก hashes และการ sync ต้องเลือก diff/path อย่างชัดเจน ไม่ทำอัตโนมัติ

## สิ่งที่จะเผยแพร่

- เอกสารหลัก 16 เรื่อง/ไฟล์ที่มีหน้าที่แยกกัน รวม README, standard/protocol, dataset details, REPORT, RESULTS, PRESENTATION, schema, state, agents/handoff, setup/reproducibility และ artifact/license notices
- First-party source/tests/scripts, frozen configs/decisions/mappings, source hashes และ metadata ที่แจกจ่ายได้
- Canonical summary CSV 8 แถว, failure inventory 566 รายการ และ success-only diagnostics ที่ติดป้ายว่าไม่ใช่คะแนนหลัก
- Compact report views ที่ประกาศว่า DERIVED จาก canonical JSON เดิม โดยไม่คำนวณคะแนนใหม่
- Historical reports ที่เลือกไว้แบบ byte-identical พร้อม index; เอกสารรุ่นเก่าไม่ใช่ execution authorization ปัจจุบัน
- Model inventory 29 variant/component records ไม่ใช่ roster benchmark 29 ระบบ
- กราฟ execution counts ที่สร้างจากผลเดิม ไม่ใช้ภาพคนหรืออ้างเป็น semantic mask quality
- ผลทดสอบและ validation ของ publication snapshot

รายการจริงอยู่ใน [PUBLISH_FILES.txt](PUBLISH_FILES.txt) และ hashes ใน [PUBLIC_FILE_MANIFEST.json](PUBLIC_FILE_MANIFEST.json)

## สิ่งที่ไม่เผยแพร่

Datasets/GT pixels, weights, environment directories, bulk predictions/masks/logits, detailed GT person bindings, full operational ledgers/large logs, company CCTV, dataset RGB/GT overlays ที่ยังไม่ยืนยันสิทธิ์, secrets/credentials/signed URLs และ raw HTTP capture ที่มี cookies ไม่มีการนำ Git history หรือ repositories ของ YOLO เข้ามา

## ผลและขอบเขตการตรวจ

รอบจริงเป็น FINISHED_WITH_INCOMPLETE_SYSTEMS: main 4,961 / reference 5,000, CPI สองระบบ + frozen YOLO26x, T3b FP32, matching 0.50/0.75 และ STRICT_COMPLETE คุณภาพหลัก null ทั้งคู่ ไม่มี accuracy/timing/FPS/VRAM winner ไม่ tune VAL และไม่ retry ภาพที่ล้มเหลว

Clean checkout ผ่าน 133 portable CPU tests โดยไม่โหลดโมเดล/สร้าง GT หรือ weights ปลอม สอง launch-plan tests และ 16 validation/fresh-package tests ยังต้อง external assets ไม่ถือว่าผ่านใน clone Source/tests/configs/taxonomy ที่ทดสอบถูก hash ไว้แยกจาก 151 server tests เดิม

Clone สามารถตรวจ summary และ synthetic contracts ได้ แต่ reproduce full benchmark ไม่ได้จนกว่าจะมี artifacts/environments ภายนอกที่ได้รับอนุญาต และการเริ่มรันใหม่ยังต้องอนุมัติแยก

First-party license ใหม่ยังไม่ได้เลือก; public readability ไม่ใช่ blanket commercial license. CPI configuration excerpts คง Apache-2.0 attribution/license ส่วน checkpoint/dataset/third-party rights ไม่ได้โอนมาเพราะ repo นี้ public

## Git และ publication

Commit แรกจะเป็น post-run snapshot ตามวันที่จริง ไม่อ้างว่าใช้ commit นี้ตอน launch Benchmark freezes V11/V12 แยกจาก Git commit/tag ไม่มี force push หรือ tag overwrite ไม่เปลี่ยน visibility ของ repository เดิม

ยังไม่ทดสอบสิทธิ์ push หรืออ่าน GitHub แบบ anonymous เพราะยังไม่เผยแพร่ ไม่พบ credential ที่เรียกใช้ได้แบบ noninteractive ใน session เตรียมงานนี้ ไม่ขอหรือเก็บ token ในเอกสาร/แชท และไม่อ้างว่าทดสอบ agent ปลายทางแล้ว

เมื่อได้รับอนุมัติ public และมีสิทธิ์ GitHub ที่ใช้งานได้ จึงสร้าง repo ตามเป้าหมายที่ยังไม่ชน repo เดิม, push commit ที่ตรวจแล้ว และตรวจ README/ไฟล์ตัวอย่างแบบไม่ล็อกอินจาก commit SHA จริง หาก authentication ไม่ผ่าน ให้รายงานแยกจากสถานะทางวิทยาศาสตร์

**ขอบเขตนี้ไม่อนุมัติ benchmark/inference/training/tuning/hybrid/CCTV เพิ่ม**
