# MHP-v2 — ตรวจ ZIP ใหม่และ RGB Integrity Blocker

**ตรวจสอบเสร็จ: PASS สำหรับการตรวจหลักฐาน / RGB dataset gate ยัง BLOCKED**

## ZIP ใหม่

- ไฟล์: `/home/skyaidev/folk/Human-Body-Extraction/datasets/LV-MHP-v2.zip`
- ขนาด: **5,429,618,040 bytes**
- SHA256: `89f010742d4797d3efd7a7eab83a405d9828749381da20638a03df947238059e`
- เทียบกับ previous import record: **BYTE-IDENTICAL — ZIP ใหม่ตรงกับ archive ที่บันทึกไว้เดิม**
- Central directory อ่านได้ครบ **179,896 entries**; ชื่อไม่ซ้ำ และ local headers/name/compression/bounds ผ่าน
- พบ wrapped local offsets **122,426 entries**; resolve เฉพาะ ZipInfo ใน memory ตามชื่อ local header ไม่แก้ ZIP และไม่ extract
- Root `LV-MHP-v2`, README ระบุ MHP-v2.0 และ bytes ตรง dataset เดิม; official split lists ตรงทุก byte

| Split | Images | Person GT PNG | Pose MAT |
|---|---:|---:|---:|
| train | 15,403 | 41,056 | 15,403 |
| val | 5,000 | 13,260 | 5,000 |
| test | 5,000 | 0 | 0 |

จำนวนไฟล์จาก central directory คือ existence/inventory verification ไม่ใช่การ decode รูปทั้งชุดซ้ำ Test GT ไม่ supplied ตามโครงสร้างเดิม

CRC ถูกตรวจใหม่จาก full member reads **24 สมาชิก**: RGB 4, GT ที่เกี่ยวข้อง 16, README 1 และ split lists 3 ไม่ได้อ้างว่า retest CRC ทั้ง 179,896 สมาชิก การมี CRC ผ่านไม่ได้แปลว่า JPEG ใช้งานได้

## ผลตรวจภาพทั้งสี่

| Split | ID | Old SHA256 | New SHA256 | Same bytes | ZIP CRC | Pillow | OpenCV | Result |
|---|---|---|---|---|---|---|---|---|
| train | 1396 | `41d6fa43f171276aabb7fe5755f4c889ec47aeb9f5f50667bc74c43f011d4bfd` | `41d6fa43f171276aabb7fe5755f4c889ec47aeb9f5f50667bc74c43f011d4bfd` | YES | PASS | FAIL | NO IMAGE | SAME_DEFECTIVE_BYTES |
| train | 18613 | `972661e3d580252c443c7dad706bb81449cbfd70222192c2debd2517a33506b5` | `972661e3d580252c443c7dad706bb81449cbfd70222192c2debd2517a33506b5` | YES | PASS | FAIL | NO IMAGE | SAME_DEFECTIVE_BYTES |
| train | 24328 | `9fa5cfb69834a81dfa18b2f22719fce431db9b35cee276a74a0b60b882bf31c1` | `9fa5cfb69834a81dfa18b2f22719fce431db9b35cee276a74a0b60b882bf31c1` | YES | PASS | FAIL | NO IMAGE | SAME_DEFECTIVE_BYTES |
| val | 17844 | `01e647b1f38f6aeddfe8959c5af23b9aeda4565bd3770b06fa0454f2154feb87` | `01e647b1f38f6aeddfe8959c5af23b9aeda4565bd3770b06fa0454f2154feb87` | YES | PASS | FAIL | NO IMAGE | SAME_DEFECTIVE_BYTES |

| Split / ID | Member bytes | JPEG header W×H | GT persons | Strict Pillow diagnostic |
|---|---:|---|---:|---|
| train/1396 | 379497 | [1024, 640] | 6 | OSError: image file is truncated (21 bytes not processed) |
| train/18613 | 577978 | [1920, 1200] | 5 | OSError: image file is truncated (0 bytes not processed) |
| train/24328 | 320069 | [1080, 1620] | 2 | OSError: image file is truncated (19 bytes not processed) |
| val/17844 | 440931 | [1024, 731] | 3 | OSError: image file is truncated (26 bytes not processed) |

**Header dimensions ไม่ใช่ successful decode dimensions:** Pillow `.load()` ล้มทั้งสี่ และ OpenCV ไม่คืนรูป จึงไม่มี fully decoded RGB dimensions ให้รับรอง ใช้ `LOAD_TRUNCATED_IMAGES=False` ไม่มี marker insertion หรือ partial-pixel repair

## Identity, GT และ alignment

RGB members ตรงกับ extracted files เดิมทั้ง bytes และ SHA256 โดย existing hashes ตรง prior canonical index จึงยืนยัน byte identity ของสี่ภาพ Associated GT ทั้ง 16 ไฟล์มี CRC ผ่าน, bytes ตรง existing GT, native label IDs อยู่ใน 0–58 และ semantic array hashes ตรง index เดิม

JPEG header grid ตรง dimensions ของ GT แต่ **ยังรับรอง RGB-to-GT spatial alignment จาก complete pixels ไม่ได้** เพราะไม่มี RGB ใด decode ครบ ไม่มีการอ้าง header agreement ว่าภาพได้รับการกู้แล้ว

## ข้อสรุป

- Actually recovered: **0/4**
- Still unreadable: **4/4**
- Replacement overlay ที่ยืนยันใช้ได้: **NO**; ยังไม่ activate overlay
- Existing dataset: **DATASET_BLOCKED** สำหรับ required-input readiness ของ full evaluation
- การแตกใหม่หรือโหลด archive ที่ hash เดิมซ้ำไม่ซ่อมสี่ภาพ เพราะ archive บรรจุ defective bytes เหมือน existing files
- สำหรับสี่สมาชิกนี้ การ extraction ไม่ได้สร้าง byte difference จาก ZIP ที่เคยบันทึกไว้ และ hash ทั้ง archive ตรง historical import record

ผู้ใช้ระบุว่าเป็น official download แต่รอบนี้ไม่มี download URL log หรือ publisher hash มายืนยันแหล่งปลายทางอย่างอิสระ ข้อสรุปที่พิสูจน์คือ archive/member identity กับสำเนาที่บันทึกไว้ ไม่ใช่การกล่าวว่าทุก release หรือทุก mirror ของ MHP-v2 เสียเหมือนกัน

## ทางเลือกถัดไปที่ต้องอนุมัติ

1. หา **different, independently verified source copies** ของสี่ JPEG ที่ decode ได้จริง พร้อม provenance และตรวจ identity/GT alignment เก็บ originals ไว้; ห้ามใช้ generated pixels หรือ re-encoding partial decode เป็น replacement
2. หากไม่มี verified replacements ให้พิจารณา readable-subset policy แบบ non-destructive: original validation target ยัง 5,000 ภาพ / 13,260 persons; scored readable view จะเป็น 4,999 ภาพ / 13,257 persons ทุกโมเดลต้องใช้ denominator เดียวและเปิดเผยว่าไม่ใช่ full official-5,000 score
3. หากยังไม่อนุมัติ policy ให้หยุด full evaluation ต่อไป งาน source/synthetic tests และ train-only checkpoint smoke เป็น gate แยกที่ต้องอนุมัติเอง

ยังไม่สร้างหรือ activate replacement/evaluation views ไม่แก้ official splits หรือ protocol และไม่เริ่ม benchmark

## แยกจาก blockers อื่น

ZIP verification นี้ไม่แก้ train/val leakage, GT person ownership, official evaluator parity หรือ actual parser checkpoint feasibility แม้ภายหลัง RGB กู้ได้ ก็ต้องตรวจ gates เหล่านั้นแยกต่างหาก

## หลักฐานและการรักษาข้อมูล

[Machine-readable evidence](../provenance/MHPV2_NEW_ZIP_RGB_VERIFICATION.json) มี member paths, CRC32, sizes, hashes, decoding errors, GT links และ scope checks [Independent blocker review](STAGE0_BLOCKER_REVIEW_TH_20261008T082918Z.md) อธิบายทางเลือกและ denominators ของ sensitivity population

Archive size/mtime/inode, four originals, associated GT, import record, official list bytes, study state และ dataset manifest คงเดิม Git HEAD/branch/status/remotes ของ YOLO หก repositories ตรง preserved evidence ไม่มี full extraction, deletion, dataset/GT/split modification, PPSS activity, model loading, parser/validation inference หรือ Stage 1

**STOP — รออนุมัติก่อนเปลี่ยน active dataset view หรือ evaluation protocol**
