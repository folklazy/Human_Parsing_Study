# ขอบเขตงานวิจัย — Decision 5A

**NONCOMMERCIAL ACADEMIC RESEARCH / EVALUATION** — งานวิจัยอิสระของนักศึกษาเพื่อเปรียบเทียบ pretrained human parsing สำหรับ body/clothing/accessories ที่โมเดลรองรับ ผู้ใช้ยืนยันขอบเขตนี้โดยตรง งานพัฒนาผลิตภัณฑ์เชิงพาณิชย์และ company R&D อยู่นอกขอบเขตปัจจุบัน

ภาพ CCTV จากบริษัทเป็นข้อมูลสำหรับประเมิน finalist ในงานวิจัยภายหลัง การให้ข้อมูลเพียงอย่างเดียวไม่ได้ยืนยันการสนับสนุนเชิงพาณิชย์หรือการพัฒนาผลิตภัณฑ์ ต้องมีสิทธิ์จากเจ้าของข้อมูลและมาตรการความเป็นส่วนตัวที่เหมาะสมก่อน field test; รอบนี้ยังไม่ตรวจภาพหรือรัน CCTV inference

สถานะ academic ไม่ยกเว้นข้อห้ามเฉพาะของ license ตรวจ code, checkpoint, dependency และ dataset แยกกัน Sapiens2 ยัง blocked เพราะข้อห้ามครอบคลุม surveillance-related research ด้วย การเปลี่ยนภาพ smoke เป็น public dataset ไม่ได้ลบ intended-use restriction ของการศึกษานี้

FASHN เข้าเงื่อนไข research/evaluation ใน terms ที่ตรวจ แต่ **ยังไม่อนุมัติ checkpoint download หรือ inference** การอนุมัติ readable MHP-v2 views และคำสั่งให้ทำงานต่อไม่ใช่การอนุมัติ weights หรือ GPU execution ไม่มีการนำ budget 8 GB ที่เคยเสนอมาใช้เป็น permission

การใช้เชิงพาณิชย์ในอนาคตต้องตรวจสิทธิ์ใหม่ ไม่รับรอง commercial deployment จากผลการประเมินรอบนี้ CIHP/MHP-v2 roles และ common taxonomy ยัง draft; PPSS paused; full benchmark, Stage 1, training, fusion และ color study ยังไม่อนุมัติ

[ขอบเขต machine-readable](configs/research_scope.yaml), [รายงานตรวจสิทธิ์](reports/LICENSE_ELIGIBILITY_REASSESSMENT.md), [license matrix](provenance/LICENSE_MATRIX_DECISION5A_V1.csv), [ข้อเสนอ FASHN smoke](manifests/FASHN_SMOKE_PROPOSAL_V2.json)
