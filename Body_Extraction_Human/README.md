# Body Extraction Human

เว็บแอปภาษาไทยสำหรับอัปโหลดภาพ/วิดีโอ → แยกคน → Human Parsing → อ่านสีเสื้อผ้า
→ บันทึก PostgreSQL → ค้นหา AND ตามลักษณะเสื้อผ้าระดับบุคคล

แอปอยู่แยกจาก benchmark ไม่ย้ายหรือเขียนทับ datasets/weights/ผลทดลองเดิม
ไม่มี face recognition, ReID หรือการระบุว่า observations ข้ามเฟรมเป็นคนเดียวกัน

## เปิดระบบบน server ที่จัดเตรียมแล้ว

จาก workspace root:

```bash
python3 Body_Extraction_Human/scripts/bootstrap.py
python3 Body_Extraction_Human/scripts/services.py start
python3 Body_Extraction_Human/scripts/services.py status
```

เปิด **http://127.0.0.1:8038** บนเครื่อง server หรือ forward port จาก laptop:

```bash
ssh -N -L 8038:127.0.0.1:8038 YOUR_USER@YOUR_SERVER
```

แล้วเปิด http://localhost:8038 บน laptop. ระบบ bind loopback เท่านั้น ไม่ใช่
public hosted site. บัญชี local `admin`; รหัสผ่านที่สุ่มครั้งแรกอยู่ในไฟล์ private
`Body_Extraction_Human/.runtime/app.env` (permission600) — เปิดอ่านบน server:

```bash
sed -n '/^BODY_USERNAME=/p; /^BODY_PASSWORD=/p' Body_Extraction_Human/.runtime/app.env
```

อย่า commit/ส่ง credentials ขึ้นแชทหรือ Git. API docs: http://127.0.0.1:8038/docs

## ติดตั้งครั้งแรก / เปิดจาก checkout อื่น

```bash
python3 -m venv .venvs/body-extraction-api
.venvs/body-extraction-api/bin/pip install -r Body_Extraction_Human/requirements.lock.txt
cd Body_Extraction_Human/frontend
npm ci
npm run build
cd ../..
python3 Body_Extraction_Human/scripts/bootstrap.py
python3 Body_Extraction_Human/scripts/services.py start
```

ต้องมี Docker/Compose, PostgreSQL15 image, shared model environments/checkpoints
และ source ตาม [setup รายละเอียด](docs/SETUP.md). ไม่มีการดาวน์โหลด weights
อัตโนมัติหรือยัด torch ทั้งหลายเวอร์ชันลง environment เดียว. `compose.yaml`
เปิดเฉพาะ PostgreSQL; API/worker ใช้ host environments ที่ตรวจแล้ว ไม่ได้อ้างว่า
GPU pipeline ทั้งชุดถูก containerize หรือ clone แล้วรันได้โดยไม่เตรียม assets.

## ทดลองตั้งแต่อัปโหลดจนค้นหา

1. เข้าสู่ระบบ → เลือก JPG/PNG/MP4 และตั้งชื่อแหล่งข้อมูล
2. วิดีโอเลือก sampling interval; เวลาเริ่มเหตุการณ์ไม่บังคับและต้องอ้างอิงได้จริง
3. กดส่งวิเคราะห์ → ได้ job ID; ดู QUEUED/RUNNING/สำเร็จ/ล้มเหลว/ยกเลิก
4. เปิดงาน เลือกเฟรมและบุคคล สลับ bbox/instance mask/parsing/หมายเลข
5. อ่านสีหลัก/รองและข้อจำกัด; เปิดวิดีโอที่เวลาที่พบ หรือดาวน์โหลดต้นฉบับ
6. หน้า “ประวัติและค้นหาบุคคล” เลือกสีส่วนบน+ล่างร่วมกัน เช่น แดง+ดำ
7. เปิดผลค้นหา → กลับไป job/frame/person ตรงรายการ พร้อม highlight
8. Refresh/ปิดเปิด API/worker หรือ restart PostgreSQL แล้วข้อมูลยังอยู่

### ค้นบุคคลตามเสื้อผ้าในวิดีโอและดูเวลาที่พบ

หลังวิดีโอประมวลผลสำเร็จ กด **ค้นหาบุคคลในคลิปนี้** ที่หน้าผล หรือเลือกคลิป
จาก **ขอบเขตวิดีโอ** ในหน้าค้นหา. ระบุสีส่วนบน/ล่างและประเภทที่รองรับแล้วกด
ค้นหา. ส่วน **เวลาที่พบในวิดีโอ** แสดง timestamps ของเฟรมที่ตรงเงื่อนไขจริง
พร้อมจำนวน observations และปุ่มเปิดบุคคลแต่ละรายการ. เปิดผลแล้วกด
**เปิดคลิป ณ เวลาที่พบ** เพื่อเลื่อนไปตำแหน่งนั้น. จำกัดช่วงค้นเป็นวินาทีในคลิปได้.

ทุกเงื่อนไข AND บน person เดียวกัน; แต่หลายเฟรมยังไม่ยืนยันว่าเป็นคนเดียวกัน.
ระบบแสดงเวลาที่พบรายเฟรม ไม่สร้างช่วงปรากฏตัวต่อเนื่อง. Sampling interval
แสดงประกอบและอาจพลาดเหตุการณ์ระหว่างเฟรม. การค้นทำจาก DB/saved outputs
โดยไม่ inference ซ้ำ. ดู [รายละเอียดการตรวจ](docs/VERIFICATION_TH.md#video-appearance-search).

ผลบางส่วนแสดงในงานพร้อมป้าย partial แต่ไม่เข้า search ชุดสำเร็จ. ลองใหม่ได้เฉพาะ
FAILED/CANCELLED และสร้าง attempt ใหม่โดยรักษาประวัติเดิม. ไม่ retry OOM อัตโนมัติ.
ยกเลิกมีผลระหว่างเฟรม; ต้องรอ worker หยุดก่อนลบข้อมูลของงานที่กำลังทำ.

## โมเดลที่เลือกจริง

- YOLO26x-Seg person instance segmentation
- Sapiens2 segmentation1B (29native labels), controlled person ROI
- T4 MLP 62→64→32→12, 6,508 parameters จาก color study ที่เลือกไว้
- LAB cluster palette เพิ่มชื่อสีเข้าใจง่าย12กลุ่มและ swatches สำหรับค้นหา

Sapiens Upper/Lower ไม่แยก pants/skirt/coat; UI จึงใช้คำว่า “เสื้อผ้าส่วนล่าง”
และไม่บังคับ category ให้โมเดลสี. ผล MLP กับ observed palette แยกฟิลด์กันชัดเจน
และไม่อ้างว่า softmax/pixel support เป็น calibrated confidence.

**ข้อกำหนด Sapiens2:** license ต้นทางห้าม surveillance รวมถึงการวิจัยด้านนั้น;
การเชื่อมทางเทคนิค/คำสั่งผู้ใช้ไม่ได้เพิ่มสิทธิ์ตาม license. ไม่มีการเผยแพร่ weights
หรือรับรองสิทธิ์ deployment. อ่าน [implementation / terms](docs/IMPLEMENTATION.md).
มี QANet เป็นทางเลือก explicit; ไม่สลับ parser อัตโนมัติ.

## โครงสร้างและการดูแล

```text
backend/app/          FastAPI, database, media decoder, queue worker
backend/migrations/   PostgreSQL schema migration
frontend/src/         React + TypeScript UI
scripts/              real isolated inference hosts, startup, verification
tests/                CPU/security/lease contracts and Chromium checks
docs/                 setup, architecture, verification, API usage
storage/              private durable uploads + all attempts (ignored)
.runtime/             private credentials, process records, logs/QA (ignored)
```

```bash
# API restart ไม่หยุด worker
python3 Body_Extraction_Human/scripts/services.py restart-api
# หยุดเฉพาะ services ของแอป; งานที่ถูก interrupt ต้องตรวจและ manual retry
python3 Body_Extraction_Human/scripts/services.py stop
# ตรวจ CPU contracts (ใช้ DB ของแอปและ fixtures ของตนเอง)
.venvs/body-extraction-api/bin/python -m pytest Body_Extraction_Human/tests -q
```

ข้อมูลถาวร: Docker volume `body-extraction-human_body_database` + `storage/`.
Backup ต้องครอบคลุมทั้ง PostgreSQL dump และ storage, ไม่ใช่ฐานข้อมูลอย่างเดียว.
ห้ามใช้ `docker compose down -v` หากต้องการรักษาข้อมูล.

เอกสาร: [Setup](docs/SETUP.md) · [Implementation](docs/IMPLEMENTATION.md) ·
[API usage](docs/API.md) · [ผลตรวจจริง](docs/VERIFICATION_TH.md)
