# CPI — Paper, official repository, taxonomy และความหมายของการรันดูคลาส

**ผลตรวจ: paper ระบุ repository ที่ใช้อยู่โดยตรง; standard CIHP taxonomy มีหลักฐานประกอบชัดเจน แต่ยังไม่ได้อ่าน original annotation header**

ข้อแนะนำที่ปรับจากเดิม: ไม่ควรให้การรอผู้สร้างเป็นเส้นทางบังคับเพียงทางเดียว และไม่ควรตัด CPI เพราะการขาด header นี้เพียงอย่างเดียว การยืนยันโดยตรงทุก channel เป็นระดับความมั่นใจที่โครงการกำหนดไว้ ไม่ใช่ข้อกำหนดสากลในการใช้ official pretrained models เอกสารนี้ยังไม่เปลี่ยน gate/config หรืออนุญาต benchmark

## 1. Paper ชี้ repository นี้จริงหรือไม่

**จริง:** abstract ของบทความตีพิมพ์ *CPI-Parser: Integrating Causal Properties Into Multiple Human Parsing*, IEEE TIP 2024, DOI `10.1109/TIP.2024.3469579` ระบุ code/model URL `https://github.com/HAG-uestc/CPI-Parser` โดยตรง ตรวจจาก author abstract ที่ NCBI จัดเก็บ ไม่ได้อาศัยเพียงคำว่า Official ใน GitHub README

- [Published article record / author abstract](https://pubmed.ncbi.nlm.nih.gov/39361466/)
- [Publisher article](https://ieeexplore.ieee.org/document/10704987/)
- [NCBI XML ที่อ่านจริง](../provenance/RUN_MANIFESTS/cpi-paper-taxonomy-reassessment-20261016T065136837053Z/pubmed.xml)

HAG เป็น fork ตาม GitHub metadata แต่สถานะ fork ไม่ได้ทำให้เป็น unofficial source ในกรณีที่ผู้เขียนบทความเลือกเผยแพร่ผ่าน URL นี้ การตาม upstream ก่อนหน้ามีประโยชน์ต่อการหาลิงก์ แต่ไม่ควรนำคำว่า fork มาลดน้ำหนัก paper-declared repository

ขอบเขตการอ่าน: ยืนยัน abstract ของฉบับตีพิมพ์แล้ว แต่ไม่ได้อ่าน full journal PDF ฉบับ 2024 ตารางฉบับเต็มที่ตรวจได้คือ related 2023 preprint *CIParsing: Unifying Causality Properties into Multiple Human Parsing* ซึ่งใช้ชื่อ/รายชื่อผู้เขียนต่างบางส่วน ไม่เรียกสองฉบับว่าไฟล์เดียวกัน

## 2. Paper กับ released model table ตรงกันหรือไม่

[Preprint Table 1](https://arxiv.org/html/2308.12218v1#S4.T1) และ [pinned official README](https://github.com/HAG-uestc/CPI-Parser/blob/d62cae523ba913fec4a7fda5816bc1d96bbf644d/README.md) ระบุผลตรงกันครบสี่ metrics ต่อ variant:

| Backbone | mIoU | APvol | APp50 | PCP50 |
|---|---:|---:|---:|---:|
| R50 / D-DETR | 59.0 | 58.4 | 72.2 | 67.8 |
| ConvNeXt-B / D-DETR | 66.5 | 63.1 | 80.9 | 74.6 |

ตัวเลขนี้เป็น **ผลเผยแพร่ของผู้สร้าง** ไม่ใช่ผลที่เรารันซ้ำ ความตรงกันสนับสนุนสาย paper→official repository→released variant ส่วน README แถวเดียวกันเชื่อมไปยังสอง Drive weights ที่ดาวน์โหลดไว้แล้ว

Preprint §4.1 ระบุ CIHP 19 foreground categories และใช้ benchmark metrics ตาม official settings จึงสนับสนุนว่าเป็น CIHP task เดิม ไม่พบคำประกาศให้ตีความเป็น taxonomy ใหม่จากส่วนที่ตรวจ แต่ paper ไม่ได้แจกแจง ordered output IDs ครบทุกช่อง

## 3. หลักฐานจากตัว weights และ source

ตรวจ `archive/data.pkl` ของ weights ที่มีอยู่ด้วย `pickletools.genops` ไม่ deserialize pickle ไม่ import torch และไม่โหลดโมเดล Embedded config ของทั้งคู่ระบุ:

- `data/CIHP/annotations/CIHP_train.json` และ `CIHP_val.json`;
- per-person `train_parsing` / `val_parsing`;
- `num_parse_classes=20`;
- flip pairs `(14,15)`, `(16,17)`, `(18,19)`.

รวมกับ source ที่ตรวจแล้ว: PNG loader รักษา numeric IDs, training target สร้างด้วย `parsing == class_id`, native decoder ส่งออกด้วย channel argmax จึงมีสายเหตุผลที่มากกว่าแค่ชื่อไฟล์ `CIHP`:

**หาก training PNG ใช้ native CIHP IDs ตามที่ release ประกาศ การ supervise ตาม ID และ export โดยไม่ remap ทำให้ output IDs สอดคล้องกับ IDs นั้น**

นี่เป็นข้ออนุมานจาก release/source/config evidence ไม่ใช่การอ่าน header ที่ยังไม่มี แต่เป็นฐานที่สมเหตุผลสำหรับ proposed standard-CIHP mapping ในการใช้ released model โดยเปิดเผยข้อจำกัด ไม่จำเป็นต้องปฏิบัติเสมือนยังไม่มีข้อมูล taxonomy เลย

[Embedded config evidence](../provenance/RUN_MANIFESTS/cpi-paper-taxonomy-reassessment-20261016T065136837053Z/EMBEDDED_CONFIG_EVIDENCE.json)

รายละเอียดอื่นไม่ได้ต้องเท่ากันทุกค่า: R50 embedded config มี `score_thr=0.1` แต่ published runtime config ที่โครงการเลือกใช้มี `0.01`; ConvNeXt-B เป็น `0.05` ทั้งสองแหล่ง ค่านี้เป็นคนละเรื่องกับ class order ต้องรักษาและเปิดเผย runtime configuration ที่รับรองไว้ ไม่เปลี่ยน threshold อัตโนมัติจาก metadata และไม่อ้างว่าเรารันด้วยทุกค่าตรงกับ training snapshot

## 4. รันเพื่อดู class และชื่อได้หรือไม่

**ดู class IDs ที่ทำนายได้แน่นอน และแสดงชื่อประกอบได้** แต่ต้องแยกแหล่งของข้อมูล:

| ข้อมูล | มาจากไหน |
|---|---|
| Pixel label เช่น 13 | Native model decoder |
| ชื่อ `Face` ของ ID13 | Dataset label catalog / adapter metadata |
| ข้อความ `13: Face` ในหน้าเว็บ | โปรแกรมนำ ID ไป lookup ชื่อ |
| `model.CLASSES=('person',)` | Detection metadata; ไม่ใช่ parsing taxonomy |

Model weights ไม่จำเป็นต้องเก็บคำภาษาอังกฤษทุกชื่อไว้ การสั่ง print รายชื่อที่ wrapper เติมให้จึงไม่ใช่หลักฐานอิสระว่าค้นพบชื่อจาก weights ส่วนการดูว่าพิกเซล channel13 อยู่ตรงใบหน้าในหลายตัวอย่างเป็น functional consistency evidence ที่มีประโยชน์ แต่ยังเป็น model behavior และอาจมี prediction errors

โค้ด `run_cpi.py` ใน smoke รอบก่อนอ่าน `taxonomy/NATIVE_CLASS_INVENTORY.json` มาเป็น `native_labels` และใช้ `classes[str(k)]` ใส่ชื่อในรายงาน ส่วน raw native PNG/NPZ เก็บ integer IDs ไม่ได้มีชื่อคลาสฝังในแต่ละพิกเซล

รอบนี้อ่าน **saved TRAIN prediction** ของ `0000930` จากทั้งสองรุ่นโดยไม่รัน inference ใหม่ แต่ละรุ่นมี 2 instance masks บนกริด `346×500` และพบ IDs `0,1,3,6,11,13` หากใช้ standard CIHP lookup จะแสดง Background, Hat, Gloves, Dress, Scarf, Face ตามลำดับ การพบ ID ชุดเดียวกันไม่แปลว่าทั้งสองรุ่นมี masks เหมือนกันหรือยืนยันทุกคลาสแล้ว

[Saved artifact hashes และ class-ID demonstration](../provenance/RUN_MANIFESTS/cpi-paper-taxonomy-reassessment-20261016T065136837053Z/SAVED_PREDICTION_DEMONSTRATION.json)

## 5. Standard CIHP catalog ที่กำลังเสนอใช้

| ID | Class | ID | Class |
|---:|---|---:|---|
| 0 | Background | 10 | Torso-skin |
| 1 | Hat | 11 | Scarf |
| 2 | Hair | 12 | Skirt |
| 3 | Gloves | 13 | Face |
| 4 | Sunglasses | 14 | Left-arm |
| 5 | UpperClothes | 15 | Right-arm |
| 6 | Dress | 16 | Left-leg |
| 7 | Coat | 17 | Right-leg |
| 8 | Socks | 18 | Left-shoe |
| 9 | Pants | 19 | Right-shoe |

[Catalog ใน official M2FP implementation](https://github.com/soeaver/M2FP/blob/main/m2fp/data/datasets/register_cihp_parsing.py) เป็นแหล่ง explicit numeric/name declaration ของ standard CIHP ที่เราใช้ประกอบ ไม่เปลี่ยนให้เป็น CPI training header โดยเรียกชื่อใหม่ รายการ Human ID20 ใน M2FP metadata เป็น internal additional human category ไม่ใช่ foreground parsing class ที่เพิ่มให้ CPI

## 6. CIHP กับ CCIHP ต้องแยกกัน

การประกาศว่า weights ฝึกบน CIHP สนับสนุน **CIHP native output taxonomy** แต่ GT ที่โครงการกำลังประเมินเป็น **CCIHP-specific** ซึ่งไม่เหมือนกันทุก ID เช่น CIHP ID6 คือ Dress แต่ CCIHP ID6 คือ Face Mask จึงยังต้องมี explicit projection เหมือนที่นโยบายกลุ่มแรกกำหนดไว้ ไม่ใช้ identity mapping เพียงเพราะชื่อ dataset คล้ายกัน

## 7. ข้อแนะนำที่ปรับแล้ว

คง CPI เป็น candidate ไม่ตัดออกจากเหตุผลนี้ และไม่ให้การรอผู้สร้างเป็นเส้นทางเดียว เสนอให้พิจารณายอมรับ standard-CIHP mapping จาก **published-paper repository link + matched release table + embedded CIHP20 config + numeric source trace + bounded TRAIN consistency review** ภายใต้สถานะที่เปิดเผยว่าไม่มี direct annotation header

การตรวจ TRAIN ควรใช้ saved predictions ก่อน ไม่ต้องรันซ้ำเพื่อ print ชื่อ ตรวจขอบเขตของ target classes ที่ให้คะแนนจริง ถ้า rare target ยังไม่ปรากฏ ให้รายงาน coverage ที่ขาด ไม่เลือก remapping จาก validation scores หากมีข้อขัดแย้งจากภาพ ให้ตรวจเฉพาะจุดก่อนยอมรับ mapping

ข้อเสนอนี้ยังไม่ใช่ accepted decision: direct-evidence gate เดิมยังอยู่ ไม่เปลี่ยนเป็น DIRECT_VERIFIED และยังไม่ materialize accepted parser contexts หรือเริ่ม benchmark การรับนโยบายหลักฐานใหม่ต้อง version ให้ชัดก่อนใช้งาน

ไม่มี model inference, downloads ของ dataset/weights, tests เพิ่ม, GT modification, creator contact หรือการเปลี่ยน config/evaluator ในรอบนี้ มีเพียง metadata/source inspection, อ่าน saved TRAIN artifacts และเอกสารข้อเสนอ
