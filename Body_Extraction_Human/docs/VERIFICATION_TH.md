# ผลตรวจ Body Extraction Human รุ่นแรก

สถานะ **V1_END_TO_END_VERIFIED_ON_T4**. เป็นการตรวจการทำงานครบเส้นทางของ
โปรแกรมบน server นี้ ไม่ใช่ผลวัดความแม่นยำใหม่หรือการรับรองพร้อม production
สำหรับทุกสภาพภาพ/codec/จำนวนผู้ใช้.

รายละเอียดที่เครื่องอ่านได้: [VERIFICATION.json](VERIFICATION.json).
การตรวจหลักเริ่ม 2026-11-02 02:00 เวลาไทย; final execution-source check ผ่าน
02:21 และตรวจ geometry/bindings อีกครั้งเวลา02:23. Browser checks/เอกสาร
ส่งมอบดำเนินต่อหลังจากนั้นตาม timestamps ในหลักฐาน private.

## สิ่งที่รันจริง

ใช้ **Tesla T4 ที่ตรวจพบจริง**. Pipeline คือ YOLO26x-Seg → Sapiens2 segmentation1B
บน controlled person ROI → native29 map-back/YOLO ownership → T4 MLP ที่เลือกไว้
และ observed palette จาก RGB เดิม → PostgreSQL/ไฟล์ถาวร. ไม่มีการอ่าน saved
benchmark predictions มาตอบแทน inference ของไฟล์ที่อัปโหลด.

สร้างไฟล์ทดสอบใหม่จากภาพ Training สาธารณะหนึ่งภาพที่มีสองคน: mirror/เพิ่มขอบ,
บังส่วนล่าง, วิดีโอ H.264 ที่เข้ารหัสใหม่ และภาพว่าง. นี่คือ functional fixtures
ที่ประมวลผลจริง ไม่ใช่หลายฉากอิสระหรือชุดวัด generalization.

| กรณี | ผลจริง |
|---|---|
| ภาพหลายคนที่แปลงใหม่ | สำเร็จ1เฟรม/2คน; มี bbox, instance/native parsing, crop และสีใน DB |
| ภาพไม่มีคน | สำเร็จ1เฟรม/0คน ไม่มีข้อผิดพลาดและไม่มีบุคคลปลอม |
| ภาพบังส่วนล่าง | สำเร็จ1เฟรม/2คน; ใช้ masks จริง และคืน unknown เมื่อพื้นที่ไม่พอ |
| MP4 H.264 ใหม่ | สำเร็จ3เฟรม/6observations ที่ PTS-relative 0,1,2วินาที |
| final execution-source uploads อีก2งาน | สำเร็จ2เฟรม/4ROIs; ใช้ detector/parser PID เดิมข้ามงานจริง |
| อัปโหลดใหม่จาก UI ของ browser | งานภาพว่างสำเร็จจริงอีก1เฟรม/0คน ผ่าน API→worker→DB |

สี่ไฟล์รอบแรกมี6เฟรม/10ROIs; final-source มี2เฟรม/4ROIsเพิ่มเพื่อพิสูจน์ execution
bindings และ model reuse. ยังมี blank frame ของ operations retry อีก1เฟรม.
ไม่รวม failure ที่ไม่ถึง inference เป็นภาพสำเร็จ และไม่อ้างว่า warm-resident
process หมายถึงใช้ cached predictions.

ตรวจ original-grid masks/crops ของทั้ง14 person observations: ขนาดตรง frame,
native IDs0–28, foregroundไม่หลุด instance extent, lossless crop เท่ากับ pixels
ต้นฉบับตาม crop_xyxy ทุกจุด. เปิดดู screenshot ผลจริงแล้ว; ไม่พบปัญหาสลับช่อง
พิกัดในตัวอย่างที่ตรวจ แต่ไม่ใช้ตัวอย่างนี้รับรอง pixel accuracy ทุกภาพ.

## การเชื่อมข้อมูลและการกู้สถานะ

| การตรวจ | ผล |
|---|---|
| ค้นสีส่วนบน+ล่าง AND | ตรวจ3positive searches จากผลจริง; ทุกแถวต้องมีทั้งสองสีใน person เดียว |
| เปิดกลับ job/frame/person | API identifiers และ Chromium deep-link/highlight ตรงจริง |
| คลิกคนบนภาพ/แถบรายชื่อ | เปลี่ยน crop/รายละเอียด/highlight; refreshแล้วยังเลือกคนเดิม |
| เลือกเฟรมวิดีโอ/seek | Chromium เปลี่ยนรายละเอียดและเลื่อนไป1s/2sจาก timestamps ที่บันทึก |
| วิดีโอ range request | authenticated HTTP206,256bytesตามช่วงที่ขอ |
| รีสตาร์ต API+worker+PostgreSQL จริง | person IDs/frame bindings10รายการเดิมคงอยู่ทั้งหมด |
| Worker heartbeat หาย | CPU fixture ทำให้ FAILED/WORKER_LOST; ไม่สรุปว่า OOM และไม่ retryอัตโนมัติ |
| ไฟล์ต้นทางของแอปหายจริง | worker FAILED; restoreไฟล์+manual retryเป็นattempt2สำเร็จหนึ่งเฟรม ไม่ซ้ำ |
| ประวัติ failed attempt | ยังอยู่หลังretry; fixtureทั้งหมดถูกลบทีหลังด้วย endpoint delete ตามการทดสอบ |
| ยกเลิกงานQUEUED | CANCELLED/attempt0 ไม่มี model call |
| ลบไฟล์และผล | DBjobไม่พบ404 และไฟล์ผลเดิม404 หลัง DELETE |

## CPU, UI และไฟล์ไม่ถูกต้อง

- **8 targeted CPU tests PASS**: auth/CSRF/path traversal, corrupt/unsupported
  uploads, upload limitรวมchunked request, EXIF geometry, actual PTS sampling,
  canonical color naming, terminal queue/cancel contract และ stale worker lease.
- React/TypeScript production build PASS; มี package-lock และ API environment
  lockfile. ไม่ rerun benchmark test suites เดิม.
- Chromium จริงตรวจ login, source preview, rejected corrupt preview/disabled
  submission, ผล/crop overlays, search, refresh, exact deep link และvideo seek.
  Browserตรวจรอบสุดท้ายไม่มี JavaScript page errors.
- PNGเสีย→422, extensionไม่รองรับ→415, oversized body→413,
  anonymous file access→401. มีการตรวจ byte content/decoder ไม่เชื่อ extension
  เพียงอย่างเดียว. ขีดจำกัดอยู่ใน config และ docs/IMPLEMENTATION.md.
- พบ Thai font ไม่ครบใน browser บน server ระหว่างพัฒนา จึง bundle Noto Sans Thai
  พร้อม OFL notice; ภาพตรวจล่าสุดอ่านภาษาไทยได้และไม่ใช้ font CDN.
- Pytest มี deprecation warning จาก Starlette TestClient ที่ยังใช้ httpx;
  การทดสอบผ่าน ไม่ใช่ inference warning หรือหลักฐานความแม่นยำ.

## ความหมายและข้อจำกัด

1. ไม่ได้ประเมิน accuracy ของแอปกับ GT ใหม่. แม้พิกัดถูก โมเดลยังแบ่งชุดชิ้นเดียว
   หรือส่วนที่บังผิดได้. Native labels/masks เก็บไว้ให้ตรวจตามจริง.
2. Sapiens Upper/Lower ไม่ยืนยัน Coat/Pants/Skirt. Apparelไม่ถูกแบ่งครึ่งและ
   Face_Neckไม่ได้กลายเป็น Face-only. ไม่อ้าง tracking/identity ข้ามเฟรม.
3. โมเดลสีที่เลือกยังคืน CCIHP12; generic categories ของ Sapiens ใช้ hypothesis
   agreement ตามที่ประกาศ. Familiar-name palette ที่ใช้ค้นหาเป็น LAB/HSV observed
   descriptor อีกส่วนหนึ่ง ไม่ใช่คะแนน accuracy ของ selected MLP. ทั้งสองวิธีอาจ
   ให้ชื่อสีต่างกันจากแสง/เงา/ขอบเขตประเภทคลาส ซึ่ง UIแสดงแยกกัน.
4. รอบแรกมี unknown garment observations7รายการ; ไม่แทนด้วย black. Pixel
   fractions/softmax ไม่ใช่ calibrated confidence. ไม่ได้ตรวจสีภายใต้แสง/กล้อง
   ทุกชนิด หรือรับรองการรู้สีจริงของเสื้อในภาพIR.
5. ทดสอบ server/T4 และ H.264 ตามขอบเขตนี้. ไม่ทดสอบ Sapiens CPUครบเส้นทาง,
   reverse-proxy/TLS production, high concurrency,ทุก MP4codec/โทรศัพท์ หรือ
   disaster recoveryจากdiskเสีย. ไม่มี latency/FPS/VRAM efficiency ranking.
6. ข้อกำหนดของ Sapiens2/YOLO/source/weightsยังมีผล; integrationหรือคำสั่งผู้ใช้
   ไม่ได้ให้สิทธิ์ใหม่สำหรับ surveillance deployment. อ่านแหล่งต้นทางใน
   [implementation](IMPLEMENTATION.md).

## เปิดใช้และตรวจต่อ

[README](../README.md) มีคำสั่งเปิด/SSH forwarding/อ่านบัญชี local. ใช้ไฟล์ใหม่
ที่มีสิทธิ์ประมวลผล แล้วเปิดผลบุคคลและค้นหาได้ทันที. API/workerรัน detached;
ดู PID/สถานะด้วย scripts/services.py status, logsที่ .runtime/ และ attempts
ที่ storage/jobs/. ภาพ/วิดีโอ/ไฟล์ผล/ภาพbrowserทั้งหมดเป็น private ไม่อยู่บนGit.

public Git เก็บ source/config/schema/docs/aggregate evidence เท่านั้น. Commit
ส่งมอบเป็น snapshot หลังพัฒนาและตรวจ ไม่ใช่ commitที่มีอยู่ตอนเริ่มทดสอบ;
execution source hashes ในแต่ละ attempt เป็นหลักฐานโค้ดที่ผูกกับงานนั้น.
ผล benchmark เดิม/weights/GT/datasetsไม่เปลี่ยน และไม่มี benchmark/trainingใหม่.

## Video appearance search

เพิ่มการค้นหาเฉพาะ completed video job, ตัวกรองช่วงวินาทีแบบ inclusive และ
ตารางเวลาที่พบรายเฟรม พร้อมจำนวน observations/ปุ่มเปิดบุคคลโดยตรง. ใช้เงื่อนไข
AND ชุดเดียวกับ person cards และเฉพาะ current successful attempt. จำนวน
เวลาที่พบคือจำนวนเฟรมที่มีผลตรง ไม่ใช่จำนวนคนไม่ซ้ำหรือช่วงติดตามต่อเนื่อง.

ตรวจเฉพาะส่วนเพิ่มด้วย saved QA video outputs เดิม:3 integration tests PASS
ครอบคลุม exact clip scope, moment pagination, matching-person AND filters,
inclusive zero-time/range validation และ authentication. Chromium จริงผ่าน
result→ค้นหาในคลิป→เลือกสี→เวลาที่พบ→exact person/frame→video seek, ไม่มีJSerror.
เปิดดู screenshot timeline จริงแล้ว. พบรอบแรกว่า accessible label ของ select
รวมข้อความ options จึงเพิ่ม aria-label ให้ชัด แล้วตรวจ browser ผ่าน.

รอบนี้ไม่มี upload/model inference ใหม่, ไม่มีการเปลี่ยน worker/weights/
preprocessing/color/scientific configs และไม่รีสตาร์ต worker. รีสตาร์ตเฉพาะAPI
เพื่อโหลด endpoints ใหม่; native benchmark/results และงานที่บันทึกแล้วคงเดิม.
ภาพ/ผลรายคน/รายละเอียดคลิปจากการตรวจอยู่ใน private .runtime/ เท่านั้น.
