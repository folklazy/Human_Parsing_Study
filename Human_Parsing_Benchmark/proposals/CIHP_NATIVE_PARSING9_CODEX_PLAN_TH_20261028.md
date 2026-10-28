# แผนดำเนินงานสำหรับ Codex — Parsing 9 ตัวบน CIHP native
วันที่: 28 ตุลาคม 2026 (Asia/Bangkok)
ฉบับรวมใหม่: 3
สถานะ: ข้อกำหนดงานและแผนดำเนินการ; ไม่ใช่รายงานผล benchmark

## 1. ใช้ไฟล์นี้อย่างไร

ส่งไฟล์นี้ให้ Codex ที่ทำงานใน repository Human-Body-Extraction ได้เพียงไฟล์เดียว ใช้แทนเอกสาร PARSING_CIHP6_THEN_SAPIENS3_DECISION_TH_20261027.md Revision 2 สำหรับงานรอบนี้ ไม่ต้องรวมคำสั่งจากหลายฉบับ
รายงาน CIHP_NATIVE_ARCHIVE_INTAKE.md เป็นหลักฐานการนำเข้าที่อยู่ใน repo แล้ว ให้ใช้อ้างอิงต่อและรักษาต้นฉบับ ไม่เขียนทับประวัติ

เริ่มจากอ่าน current instructions, PLAN, configs, status และ git state ใน repo แล้วปรับแผนและ implementation ที่เกี่ยวข้องตามเอกสารนี้ รักษางานของผู้ใช้ที่ยังไม่ได้ commit
เป้าหมายใกล้ที่สุดคือปิดผล parsing หกตัวแรกบน CIHP ให้มีหลักฐานและรายงานสำหรับพี่เลี้ยง ไม่ให้ Ninja, matrix ของ Sapiens2 หรืองานสีเป็น dependency ของ milestone นี้
ใช้การอนุญาตและขอบเขตงานที่ผู้ใช้ให้ไว้ใน session Codex โดยไม่ขอซ้ำสำหรับงานที่อนุญาตแล้ว การจัดทำเอกสารนี้ไม่ใช่หลักฐานว่าได้รัน GPU/แก้ repo/commit หรือ push แล้ว

## 2. ข้อตกลงและขอบเขต

- Parsing ทั้ง 9 checkpoint variants ประเมินบน CIHP dataset และ evaluation image population เดียวกัน
- จบหกตัวที่มี CIHP checkpoints ก่อน → ทำ semantic matrix → ทดสอบ Sapiens2 สามขนาดบน CIHP → งานสีภายหลัง
- Minimum targets เดิมคือ face, hair, uppercloth, lowercloth; เก็บ native predictions ครบทุกคลาสเพื่อไม่ให้ข้อมูลสูญหาย
- ใช้ pretrained checkpoints ที่เลือกไว้ ไม่เริ่ม fine-tuning เพื่อทำให้เข้ากับ GT รอบนี้
- YOLO26x-Seg เป็นองค์ประกอบ frozen ที่เลือกไว้แล้วตาม route เดิม ไม่เปิดคัดเลือก YOLO ใหม่และไม่นับเป็น parser
- ผล CPI และการทดลองเก่าเป็น historical evidence ไม่ลบ ไม่เขียนทับ และไม่ใช้ผล incomplete สรุปว่าคุณภาพโมเดลแพ้

| กลุ่ม | Model/checkpoint variant | Dataset ประเมิน |
|---|---|---|
| หกตัวแรก | QANet HRNet-W48 CIHP, H512×W384 ตามแผนเดิม; bind config จริง | CIHP native |
| หกตัวแรก | M2FP R101 CIHP | CIHP native |
| หกตัวแรก | D2FP R101 CIHP | CIHP native |
| หกตัวแรก | RP-R-CNN R50 CIHP ตาม specification เดิม; ยืนยัน exact config | CIHP native |
| หกตัวแรก | CPI-Parser R50 CIHP | CIHP native |
| หกตัวแรก | CPI-Parser ConvNeXt-B CIHP | CIHP native |
| หลัง matrix | Sapiens2 0.4B segmentation | CIHP native |
| หลัง matrix | Sapiens2 0.8B segmentation | CIHP native |
| หลัง matrix | Sapiens2 1B segmentation | CIHP native |

ห้ามใช้จำนวนโมเดล/รายชื่อ cohort เก่าแทน roster นี้ ทุกตัวต้องมี exact checkpoint/config/hash และ native class order ที่ตรวจได้ก่อนนำผลมาอ้างอิง

## 3. Dataset ที่เลือกใช้ในแผนฉบับนี้

ข้อเสนอที่นำมาใช้ในแผน: ใช้ CIHP native จากแหล่ง CIHP_PGN ที่แตกแล้วเป็นแหล่งหลัก เมื่อผ่านการตรวจหลังนำเข้าตามข้อ 5
Dataset Ninja ดาวน์โหลดแล้วแต่ยังไม่ได้แตก ให้พัก archive ไว้ ไม่ต้องแตก/แปลง/เปรียบเทียบทั้งชุด และไม่ต้องรอ Ninja เพื่อเริ่ม benchmark native ที่พร้อม
ไม่ต้องดาวน์โหลด CIHP native ซ้ำหรือแตกทับของเดิม ไม่มีเหตุให้รัน parser ซ้ำสอง distribution เพียงเพราะมาจากคนละเว็บ

ข้อมูลที่ผู้ใช้แจ้ง:
- แหล่งชุด native: https://github.com/Engineering-Course/CIHP_PGN โดยดาวน์โหลด dataset ผ่าน Google Drive ที่ README ลิงก์ไว้
- แหล่งชุดเดิม: https://datasetninja.com/cihp
- Root ที่แตกแล้ว: /home/skyaidev/folk/Human-Body-Extraction/datasets/CIHP/
- Repository ที่ใช้: /home/skyaidev/folk/Human-Body-Extraction/
- Ninja archive: ผู้ใช้แจ้งว่ามีแล้ว; exact filename/path ยังไม่ให้มาและไม่จำเป็นต่อ native milestone ปัจจุบัน

ข้อมูล source จากผู้ใช้ช่วยเติม provenance ที่ receipt เดิมยังไม่ทราบ แต่ไม่ใช่ publisher checksum หรือการตรวจยืนยันตัวตนไฟล์จากผู้เผยแพร่
ไม่ถือว่าสอง distribution เป็นข้อมูลอิสระสำหรับ cross-dataset generalization และไม่ผสมภาพ/GT จากทั้งสองชุดโดยไม่ตรวจความเทียบเท่า

## 4. งานนำเข้าที่เสร็จแล้ว — ใช้หลักฐานเดิม

ตรวจจากไฟล์แนบ CIHP_NATIVE_ARCHIVE_INTAKE(3).md ซึ่งเป็นสำเนาของรายงาน:
Human_Parsing_Benchmark/reports/CIHP_NATIVE_ARCHIVE_INTAKE.md

| รายการ | ข้อมูลตาม receipt |
|---|---|
| Work unit | cihp-native-intake-20261028T030159730335Z |
| Archive | datasets/instance-level_human_parsing.tar.gz — เก็บไว้ |
| Archive size | 2,033,753,964 bytes |
| SHA256 | 6dea91e6c7ffa48c023eb0bdaa3ee259fe0d4e9d89e108bd26b312fdf646d2bb |
| Archive integrity | Full gzip trailer CRC/ISIZE และ TAR header stream ผ่าน; TAR ไม่มี per-file CRC |
| Unsafe/special members | 0 |
| Duplicate normalized paths | 0 |
| Extracted files | 237,965 |
| Payload bytes | 2,078,741,021 |
| การแตก | เอาออกเฉพาะ wrapper instance-level_human_parsing/; รักษา child paths/bytes; staging แล้ว atomic rename; ไม่ทับชุดเดิม |

| Split | RGB | Category_ids | Human_ids | Instance_ids |
|---|---:|---:|---:|---:|
| Training | 28,280 | 28,280 | 28,280 | 28,280 |
| Validation | 5,000 | 5,000 | 5,000 | 5,000 |
| Testing | 5,000 | ไม่มีใน archive | ไม่มีใน archive | ไม่มีใน archive |

- Basenames ภาพกับ annotations/visualizations ตรงกันตาม receipt; นี่เป็น filename-level check
- Category_ids/Human_ids/Instance_ids เป็น label data ส่วน Categories/Human/Instances เป็น rendered visualizations ตาม README ที่ receipt อ่านพบ
- Receipt พบ semantic foreground 19 คลาสและ Dress ID6; อย่าใช้ CCIHP FaceMask ID6 มาถอดรหัสแทน
- Compact manifest: Human_Parsing_Benchmark/manifests/CIHP_NATIVE_IMPORT.json
- Inventories รายไฟล์อยู่ภายนอก Git ใต้ Human_Parsing_MHPv2_Study/outputs/dataset_intake/ พร้อม work-unit ID ข้างต้น; resolve exact path จาก manifest
- Digests รายไฟล์ถูกคำนวณจาก bytes ขณะแตก ไม่ได้อ้าง independent second full disk read
- ผู้ใช้แจ้งว่า push เอกสารแล้วที่ commit b2a3849; ผู้จัดทำแผนนี้ยังไม่ได้ตรวจ remote commit โดยตรง Codex ตรวจใน checkout ได้เมื่อเริ่มงาน
- ไม่มี inference/benchmark และยังไม่มี full strict decoding หรือ annotation-quality audit จากงาน intake นี้

ไม่รัน intake เดิมซ้ำเพียงเพื่อสร้างรายงานชื่อใหม่ ตรวจไฟล์/manifest ปัจจุบันให้ผูกกับ receipt และตรวจต่อเฉพาะช่องว่าง หากพบ identity drift จึงตรวจเพิ่มเฉพาะส่วนที่ได้รับผลกระทบ
ถ้อยคำใน receipt ว่า protocol ยัง pending เป็นสถานะ ณ เวลานำเข้า ไม่ใช่ข้อห้ามถาวรในการทำแผน parsing ล่าสุดของผู้ใช้

## 5. งานตรวจ native ที่ยังเหลือ — CPU ก่อน GPU

ข้อเสนอ population หลัก: Validation 5,000 ภาพที่มี GT ครบตาม receipt ใช้ Training สำหรับ readiness/dev ที่จำเป็น
Testing ไม่มี GT ใน archive นี้ จึงไม่ใช้คำนวณ supervised metrics และไม่ถือว่าเสียหายจากการไม่มี GT เพียงอย่างเดียว
ใช้ manifest/split lists ที่ตรวจแล้วเป็น authority ของรอบรัน ไม่คัดลอก 4,961 ภาพหรือ exclusions/จำนวนคนจาก protocol CCIHP เดิม

### 5.1 ตรวจ metadata และ split โดย reuse intake manifest

- ตรวจ root และรายการที่ใช้งานจริงตรง receipt; บันทึก source URL ที่ผู้ใช้ให้, archive identity, decoder version และผลตรวจ
- อ่าน README/schema/split lists จริง ระบุ class order, background, void/ignore (ถ้ามี) และ dtype ที่ต้องใช้
- ตรวจ split IDs ซ้ำ/ทับซ้อน ชื่อภาพและ GT ของ evaluation population รวมไฟล์ขาด/เกิน
- ใช้ inventories/hash evidence เดิมตรวจ exact duplicate images ข้าม Training/Validation ที่ทำได้ ไม่เปิด perceptual-duplicate research ทั้ง dataset โดยอัตโนมัติ
- หากมี duplicate หรือ split exposure ให้บันทึกและกำหนด policy ก่อนดูคะแนน; ไม่คัดลอกเลข 39 exclusions จากงานเดิม และไม่ตัดภาพเงียบ ๆ
- เก็บ canonical validation population และเหตุผลของ derived filtered view แยกกันหากจำเป็น ไม่เปลี่ยน headline population โดยไม่เปิดเผย

### 5.2 Strict decoding ของข้อมูลที่นำไปวัดผล

สำหรับ Validation ที่จะใช้จริง ให้ decode RGB และ Category_ids/Human_ids/Instance_ids ทุกไฟล์ที่จำเป็นด้วย loader ที่ใช้งานจริง:
- โหลด pixel arrays เต็ม ไม่ใช้เพียงเปิด header หรือ file exists
- ตรวจ dimensions, mode/dtype, truncated/corrupt files และ orientation ให้ภาพกับ GT ตรงกัน
- รักษา integer label IDs และ bit depth; อย่าบังคับทุก mask เป็น uint8 และอย่าแปลง palette PNG เป็น RGB แล้วถือค่า RGB เป็น class IDs
- ตรวจ observed semantic values กับ schema จริง; แยก background/ignore ตามหลักฐาน ห้ามสมมติว่า 255 เป็น ignore โดยไม่มีข้อกำหนด
- สรุป label histograms และจำนวน invalid/unknown IDs; ห้าม remap unknown เป็น background แบบเงียบ ๆ
- ตรวจ person IDs และ part-instance relationships จาก README/loader/evaluator จริง ไม่เดาว่า Instance_ids เป็น person IDs
- ตรวจความสัมพันธ์ของ categorical/person/instance masks ตาม schema ที่ยืนยันได้; ความต่างเล็กน้อยให้รายงานเพื่อวินิจฉัยก่อน ไม่แก้ GT อัตโนมัติ

Training: decode เฉพาะตัวอย่างที่ใช้ smoke/dev อย่างครบถ้วนก่อนใช้ ไม่ต้อง decode ภาพและ visualization ทั้ง 237,965 ไฟล์เพื่อให้ validation benchmark เดินได้
Testing/visualization folders: ไม่ต้อง full-decode เพื่อปิด readiness ของ evaluation ที่ไม่ได้ใช้มัน

### 5.3 ตรวจการวาง mask และเส้นทางเข้า scorer

- เลือกตัวอย่างขนาดเล็กแบบทำซ้ำได้จาก ID seed/list ที่บันทึก เช่น 12–20 ภาพ ให้มีคนซ้อน คนเล็ก ภาพหลายขนาด และ garment classes สำคัญ
- ตรวจ overlays บน original grid รวม Dress/Coat/Pants/Skirt และเจ้าของ mask; แยก sampling สำหรับดู GT correctness ออกจากการใช้คะแนน VAL ปรับโมเดล
- ตัวอย่างไม่ใช่การรับรองคุณภาพ annotation ทุกภาพ ระบุจำนวนและขอบเขตที่ตรวจจริง
- ให้ actual loader → dataset packet → scorer → reporter รับข้อมูลถูก schema; แยกการตรวจ GT กับ model inference
- ภาพที่ decode ไม่ได้/พิกัดผิดเป็น blocker ของข้อมูลส่วนที่ใช้; เก็บ failure list ไม่แทนด้วยภาพดำหรือ drop เงียบ ๆ
- ไม่ repair source GT หรือใช้ GT ช่วย crop/ตัด prediction เพื่อให้ผลดีขึ้น

### 5.4 จบงาน readiness เมื่อใด

มี validation manifest ที่แน่นอน, decode/schema report ของข้อมูลที่ใช้จริง, loader/scorer checks ผ่าน, issues ที่กระทบคะแนนถูก resolve หรือระบุ protocol ที่เปิดเผยแล้ว
หาก native ผ่าน งาน Ninja ที่ยังไม่ทำไม่ใช่ blocker
การตรวจส่วนอื่นของ Training/Testing หรือ full annotation quality review เป็นงานแยก ไม่ขยายงานก่อนพรีเซนต์โดยไม่มีเหตุจาก failure ที่พบ

## 6. เตรียมและรันหกตัวแรก

1. Bind checkpoint/config/source commit/hash/class order ของทั้งหกตัว ตรวจ auxiliary human-query channel แยกจาก semantic classes
2. รักษา native preprocessing และ declared route ตาม config ที่ตรวจแล้ว อย่าบังคับทุกตัวเป็น YOLO crop โดยไม่ดู implementation เดิม
3. ระบุ route ที่ใช้ frozen YOLO proposals เทียบกับ route ที่มี native detector/ownership ให้ชัด ผลเป็น configuration comparison ไม่ใช่ architecture-only causal comparison
4. ตรวจ geometry restoration, clipping/overlap policy และ valid empty outputs; เก็บ output ก่อน destructive clipping เมื่อมี
5. Reuse evidence ที่ dependencies ตรง ทำ GPU smoke เฉพาะ config/route ที่ยังขาดหลักฐานบน Training ชุดเล็กที่ล็อกไว้
6. ใช้ smoke เดียวกันประเมิน memory/storage/เวลา ไม่เพิ่มรอบจำนวนมากเพื่อทดสอบซ้ำสิ่งเดียวกัน
7. Freeze evaluation population, resolution, precision, TTA, thresholds, runtime scope และ retry/resume policy ก่อนดูผลประเมิน
8. รันหกตัวตามขอบเขตที่ผู้ใช้สั่งไว้ใน session Codex; เมื่อพร้อมแล้วไม่รอ Sapiens/Ninja/color เพื่อเดินต่อ

หากเวลา/ทรัพยากรไม่พอ 5,000 ภาพ ให้รายงานข้อจำกัดและกำหนด common presentation subset ก่อนดูคะแนน รันทุกตัวบน subset เดียวกันและระบุว่าเป็น subset result ไม่เรียก full-validation result
ไม่ fallback เปลี่ยน precision/device/model อย่างเงียบ ๆ หากเกิด OOM หรือ error ให้เก็บ cause/attempt และแก้เป็น config revision ที่ตรวจสอบได้
อย่าเลือก retry output ที่คะแนนดีที่สุด; resume ได้เฉพาะ run fingerprint ตรงและ artifact ที่สมบูรณ์

### คะแนนและรายงานระยะ 1

- เสนอ native CIHP evaluation เป็น baseline: mIoU + IoU รายคลาส กำหนดการรวม background, absent-class policy และ aggregation ใน config ตาม reference evaluator ที่ตรวจแล้ว
- แสดง minimum target view เพิ่มได้เมื่อการรวมคลาสมีนิยาม แต่ไม่ทำให้ mapping ข้าม Sapiens เป็นเงื่อนไขของระยะนี้
- แสดงการแยกบุคคล/instance metrics ที่ representation และคะแนน confidence รองรับ พร้อม FP/FN; ถ้า metric ไม่รองรับให้ระบุ N/A พร้อมเหตุผล ไม่สร้าง dummy scores
- Semantic mIoU อย่างเดียวไม่ยืนยันว่า mask เป็นของคนถูกคน
- วัด latency/VRAM/failure rate โดยระบุ hardware, warm-up, synchronization และ timing scope; cached quality output ไม่ใช่ fresh end-to-end timing
- Completed/failed/invalid/not-attempted ต้องนับครบ; valid empty prediction ต่างจาก execution failure
- คะแนนหลักที่อ้าง population เต็มต้องมีผลครบ ห้ามเฉลี่ยเฉพาะภาพที่สำเร็จแล้วเรียกผลครบ
- จัด summary ทุก candidate, per-class results, fixed qualitative samples, failure cases และ limitations

จบครบหกตัว = ทุกตัวมี outputs/scoring ครบ population ที่ freeze
หากมีตัว incomplete ให้ออกรายงานความคืบหน้าพร้อมงานที่เหลือได้ แต่ไม่เรียกว่า benchmark หกตัวครบ และไม่เรียกผู้นำกลุ่มนี้ว่า winner ครบเก้าตัว

## 7. เก็บหลักฐานตั้งแต่ภาพแรก

| กลุ่ม | สิ่งที่ต้องเก็บ |
|---|---|
| Run identity | run ID, checkpoint/hash, code commit, resolved config/hash, environment/device |
| Dataset | source identity, split/IDs manifest/hash, decoder/schema version, GT identity |
| Predictions | native integer masks ทุกคลาส; per-person planes/extent/scores ตาม output จริง |
| Geometry | RGB reference/hash, original dimensions, crop/resize/padding, mapping กลับ original grid |
| Ownership | person association, source detector/query, overlap/clipping policy, pre-clipping outputs เมื่อมี |
| Execution | expected/attempted/completed/failed/invalid/not-attempted, attempt IDs, errors, atomic completion |
| Scoring | evaluator/mapping version, sufficient statistics, matches/FP/FN, full denominator |
| Resources | timings ที่ระบุ scope, precision จริง, VRAM และ retained/temporary storage |
| Report | summary/per-class/failure/qualitative IDs และตำแหน่ง artifacts |

เก็บข้อมูล mask จริง ไม่ใช่เฉพาะ overlay/JPEG
แยก inference fingerprint จาก evaluation fingerprint เพื่อให้ rescore โดยไม่ inference ใหม่
Hard labels รองรับ deterministic remapping แต่กู้ logits/probabilities ไม่ได้ ไม่ต้องเก็บ full logits ทุกภาพอัตโนมัติ ให้ระบุข้อจำกัดและประเมินพื้นที่ก่อน
เก็บ source data/weights/bulk predictions นอก Git ตาม workflow เดิม Git เก็บ code/config/manifest/report ที่เหมาะสม

## 8. หลังจบหกตัว: Matrix → Sapiens2 สามตัวบน CIHP

Matrix หนึ่งแถวต่อ native class ต้องมี:
model/checkpoint, native ID/name, annotation meaning, pixel scope, granularity, target, relation, conversion, information loss, evidence, comparison eligibility

แยก one-to-one, many-to-one, one-to-many, partial/approximate, unsupported/unknown
ตรวจ Face_Neck/facial subparts, Hair, Upper/Lower clothing, Apparel และการจัดการ Dress/Coat ตาม source จริง ไม่เทียบจากชื่ออย่างเดียว
common view เป็น derived projection ที่ version ทั้ง CIHP GT และ predictions โดย source GT ไม่ถูกแก้

เมื่อ matrix พร้อม:
- รัน Sapiens2 0.4B/0.8B/1B บน CIHP split/IDs เดียวกับหกตัวแรก
- ใช้ hard-label remapping เป็นวิธีตั้งต้นที่เก็บข้อมูลรองรับ; probability aggregation/pose-assisted split/learned adapter เป็น config ใหม่ที่ต้องมีข้อมูลและ validation ของตน
- นำ native outputs หกตัวมา remap/rescore ตาม common protocol เดียวกัน ไม่ต้อง rerun parser เพียงเพราะเพิ่มคู่เทียบ
- ใช้ GT eligibility/ignore policy เดียวกัน ไม่สร้าง per-model void เพื่อซ่อนส่วนที่ส่งไม่ได้
- แยก unsupported prediction ที่ควรนับเป็น error ใน common task ออกจาก metric N/A เพราะความหมายไม่สามารถเทียบได้; ระบุนโยบายก่อนดูคะแนน
- เก็บ native CIHP6 table เดิมและ common-view table แยกกัน ไม่เทียบ native full-taxonomy mIoU กับ reduced-class mIoU โดยตรง
- รายงาน training provenance เท่าที่ทราบ ไม่อ้างว่า pretrained exposure เท่ากันทุกโมเดล
- ไม่เปลี่ยน evaluation dataset ของ Sapiens2 ไปเป็น CCIHP

## 9. สีเสื้อผ้าเป็นระยะต่อไป

เป้าหมายยังเป็น แยกบุคคล → garment masks ของคนนั้น → อ่านสีจาก original RGB → รายงานสี/หลายสี/unknown เมื่อหลักฐานไม่พอ
ตอนนี้เตรียม RGB identity, native masks, ownership และ transforms ให้ใช้ต่อได้ งานสีไม่เป็น gate ของหกตัวแรก

CCIHP เป็น candidate แรกของงานสี; CFPD เป็น candidate เสริม ยังไม่เริ่ม download/audit/benchmark สีจากเอกสารนี้โดยอัตโนมัติ
ต้องกำหนดหน่วยคำตอบก่อน: สีแยก garment กับสีสรุป upper/lower ไม่เหมือนกัน เช่นเสื้อยืดขาวใต้ coat ดำไม่ควรถูกรวม mean RGB แล้วเรียกว่าเสื้อเทา
เก็บ native garment classes ไว้ก่อน การรวมคลาสเพื่อพรีเซนต์ไม่ควรทำลายข้อมูล

ระยะสีให้แยก:
1. RGB + GT mask เพื่อวินิจฉัยตัวอ่านสี
2. RGB + predicted mask ด้วย algorithm เดียวกันบน paired population
3. End-to-end รวม missed/extra persons/garments และ wrong-owner

ล็อก palette/multicolor/unknown และ threshold บน train/dev ก่อนประเมิน
รายงาน macro-F1/accuracy, per-color confusion, coverage, abstention และ correct person+garment+color rate บน denominator ที่ชัดเจน ไม่ตัด unknown ของโมเดลออกเพื่อให้ accuracy สูงขึ้น
ห้ามใช้ GT intersect prediction เพื่อทำความสะอาดก่อนอ่านสีแล้วเรียกว่า end-to-end
CCIHP อาศัยภาพ CIHP จึงไม่ใช่ independent image test อีกชุดโดยอัตโนมัติ และ GT semantics เปลี่ยนบางส่วน ต้องตรวจ mapping ใหม่เมื่อถึงระยะนี้
การใช้ภาพร่วมกันอาจให้ reuse inference ได้เมื่อ decoded RGB/geometry/config ตรง แต่คะแนนและ GT ไม่ใช้แทนกัน
การอ้างความพร้อม CCTV ต้องมี evidence บนโดเมนนั้นภายหลัง ไม่ให้การสร้าง CCTV dataset ขวางรอบนี้

## 10. จะกลับมาใช้ Ninja เมื่อใด

พัก Ninja archive เดิมไว้ ไม่ลบและไม่แตกอัตโนมัติ ใช้เมื่อมีเหตุเฉพาะ เช่นต้องเปิด annotation ในเครื่องมือที่รองรับ หรือจำเป็นต้องใช้ artifacts เก่าที่ผูกกับ Ninja

หากจำเป็น:
- ตรวจ inventory/metadata/schema จาก archive ก่อน และอ่าน/แตกเฉพาะส่วนที่ต้องใช้แบบปลอดภัยในพื้นที่แยก
- เทียบ image IDs/splits, dimensions และ decoded RGB; file hash ต่างไม่ได้พิสูจน์ว่า pixels ต่าง
- เทียบ semantic masks หลัง map encoding ที่มีหลักฐาน
- เทียบการแบ่งบุคคลและ part ownership โดยยอมให้ instance ID ถูก renumber ได้; raw ID arrays ต่างไม่เท่ากับ segmentation ต่างเสมอ
- ตรวจเต็ม population ที่จะ reuse หากจะอ้างว่าใช้แทนกันได้; sample check เพียงอย่างเดียวรับรองได้เฉพาะ sample
- เลือกแหล่งหลักและรายงาน mismatch ไม่รวม GT หรือเลือกแหล่งตามคะแนนที่สูงกว่า
- ถ้า native ผ่านและไม่ reuse Ninja artifacts ให้ข้ามงานนี้ได้เลย ไม่สร้าง source-comparison gate ใหม่

## 11. งานปรับ repo และผลส่งมอบ

ใช้โครงสร้าง repo ที่มีจริง ไม่สร้างโครงสร้างคู่ขนานโดยไม่จำเป็น

| ส่วน | การเปลี่ยน |
|---|---|
| PLAN / decision history | ใช้ CIHP native ที่นำเข้าแล้ว; CIHP6→matrix→Sapiens3 บน CIHP→color; Ninja deferred |
| README / status | intake complete ตาม receipt; decode/evaluation readiness pending จนมี evidence; แสดงสถานะจริงของแต่ละ checkpoint |
| Dataset registry/config | native root/archive/hash/manifest, Validation population, decoder/schema; แยกจาก CCIHP และ Ninja |
| Model registry/routes | เก้าตัวตาม roster, exact configs, phases และ route dependencies |
| Loader/evaluator | ใช้ native IDs ไม่ใช้ visualization/CCIHP schema; targeted checks ผ่าน actual pipeline |
| Run/artifact schema | รองรับ raw native masks, RGB/geometry/ownership, ledger และ safe resume |
| Reports | native readiness, phase-1 results, common-view results ภายหลัง; เก็บ historical CPI results |
| Repository hygiene | ไม่ commit datasets/archives/weights/bulk predictions; ใช้นโยบายเผยแพร่เดิม |

ผลส่งมอบขั้นต่ำก่อนรัน: native readiness report + machine-readable manifest + resolved run configs + targeted check evidence + resource estimate
ผลส่งมอบหลังรันหกตัว: summary table + per-class metrics + execution/failure ledger + artifact references + phase-1 completion report
ไฟล์รายงานใหม่ต้องบอก verified/proposed/not-checked และจำนวนที่ตรวจจริง ไม่ใช้คำว่า all-pass เมื่อยังมี required checks ไม่ได้ทำ

## 12. ลำดับที่ Codex ควรทำต่อทันทีเมื่อรับงาน

1. อ่านเอกสารนี้และ current instructions ใน repo; ตรวจ intake receipt/import manifest และ git state
2. บันทึกผู้ใช้ยืนยัน source CIHP_PGN; เลือก native root เป็น active candidate และ Ninja เป็น deferred ตามแผนนี้
3. ปรับ PLAN/status/config ที่เกี่ยวข้อง โดยระบุ intake เสร็จแล้วและไม่แตก native ซ้ำ
4. ทำ CPU checks ข้อ 5 และ targeted loader/scorer checks; reuse evidence เดิมที่ตรง
5. ปิด exact bindings/config/resource readiness ของหกตัว; GPU smoke เท่าที่ขาดตามขอบเขตงาน
6. ดำเนิน benchmark หกตัวตามคำสั่งผู้ใช้และขอบเขตที่ได้รับแล้ว เก็บหลักฐานให้ครบ ไม่รอ Ninja/Sapiens/color
7. ปิดรายงาน phase 1 ก่อนเริ่ม matrix และ phase 3 ตามลำดับ

อย่าถามข้อมูลที่อ่านได้จาก repo/manifest ให้ผู้ใช้ตอบซ้ำ หากหาไม่ได้หรือขัดกันจริง ให้ระบุ field และผลกระทบเฉพาะจุด
อย่าสร้างชื่อ CLI หรืออ้าง commit/push ที่ยังไม่ได้เกิดขึ้น รายงานคำสั่ง/config/hash/commit ตามหลักฐานจริง
ไม่มีการเปลี่ยน scope เป็น training, เพิ่มโมเดล หรือ full dataset audit ทั้งโครงการจากการรับไฟล์นี้

## 13. ที่มาของข้อมูลและขอบเขตการรับรองเอกสารนี้

- รายงานแนบ CIHP_NATIVE_ARCHIVE_INTAKE(3).md: อ่านเนื้อหาแล้ว; ยืนยันได้ว่ารายงานกล่าวอะไร ไม่ใช่การตรวจ server bytes ซ้ำ
- Root, download source, Ninja ยังไม่แตก และ commit b2a3849: ผู้ใช้ให้ข้อมูล; Codex ตรวจ binding ใน checkout ที่ใช้งานจริง
- รายชื่อโมเดลและลำดับ CIHP6→matrix→Sapiens3→color: ข้อตกลงจากบทสนทนา
- ใช้ native อย่างเดียวและพัก Ninja: แนวทางที่แนะนำในฉบับรวมใหม่นี้ เพื่อลดงานที่ไม่จำเป็นต่อ milestone
- ช่วงจัดทำไฟล์นี้ไม่มี dataset extraction, inference, benchmark หรือการแก้/push repository จริง

Source references สำหรับตรวจ provenance/รายละเอียดเมื่อจำเป็น:
- https://github.com/Engineering-Course/CIHP_PGN
- https://datasetninja.com/cihp
- https://github.com/facebookresearch/sapiens2/blob/main/docs/SEG.md
- https://arxiv.org/html/2201.09594v1

ชื่อ CIHP_PGN เป็นแหล่ง dataset/reference ไม่ใช่การเพิ่ม PGN เป็น parser ตัวที่สิบ

