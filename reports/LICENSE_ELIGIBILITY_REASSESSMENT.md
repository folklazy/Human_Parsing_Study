# ตรวจสิทธิ์ใช้งานภายใต้ขอบเขตวิจัย — Decision 5A

สถานะการตรวจเอกสาร: **PASS_WITH_WARNINGS**; Stage 0 โดยรวมยัง **BLOCKED / WAITING_FOR_USER_APPROVAL** ไม่ใช่ model readiness หรือสิทธิ์ deployment ตรวจ source/license snapshots ที่เก็บ 2026-10-08 และทบทวนแหล่งหลักอีกครั้ง 2026-10-12 ไม่มี weights ดาวน์โหลด/โหลด/รัน

## ขอบเขตที่ยืนยันแล้ว

ผู้ใช้ยืนยัน **NONCOMMERCIAL ACADEMIC RESEARCH / EVALUATION** สำหรับงานอิสระของนักศึกษา ภาพ CCTV จากบริษัทเป็นข้อมูลประเมินในอนาคต ไม่ใช่หลักฐาน sponsorship/product development; commercial use อยู่นอกขอบเขต ต้องตรวจใหม่หากเปลี่ยนวัตถุประสงค์ [Research scope](../RESEARCH_SCOPE.md)

## โมเดล: code และ checkpoint แยกกัน

| Candidate | Code ที่ตรวจ | Checkpoint / เงื่อนไข | ข้อสรุปสำหรับ Decision 5A |
|---|---|---|---|
| FASHN | Wrapper กำหนดให้ปฏิบัติตาม SegFormer terms | Official pinned model card ยืนยัน weights สืบทอด NVIDIA SegFormer license | เข้าเงื่อนไข research/evaluation; **รออนุมัติ download/smoke** |
| M2FP | Predominantly CC-BY-NC-4.0 | Official checkpoints ถูกอ้างใน README; ขอบเขต grant ของ asset ที่เลือกยังไม่ยืนยันแยก | Research candidate แบบมีเงื่อนไข; ตรวจ applicability/attribution ก่อน execution |
| CPI R50 / ConvNeXt-B | Apache-2.0 | Official dataset-specific weights มีจริง; ไม่ได้ตรวจพบ weight-specific grant ที่ยืนยันได้แยก | Code เข้ากับ academic scope; checkpoint applicability ยัง pending |
| D2FP CIHP / LIP | MIT ที่ root; README รับรองการใช้ M2FP และ source มี inherited notices | Official full-parser release มี CIHP/LIP; weight terms และ inherited-file scope ต้องบันทึกต่อ | Research candidate แบบมีเงื่อนไข; ไม่เหมารวมว่า MIT เคลียร์ทุกไฟล์ |
| SCHP LIP / ATR / Pascal | MIT code | Official weights linked; applicability ของ code grant ต่อ weights ยังไม่ยืนยัน | Research candidate แบบมีเงื่อนไข; legacy environment ไม่พร้อม |
| Sapiens2-0.4B | Custom Sapiens2 license | ข้อห้าม surveillance ครอบคลุม related research/development | **LICENSE_BLOCKED_PENDING_APPLICABLE_PERMISSION** |

**Verified fact:** SegFormer §3.3 กำหนด noncommercial เป็น research/evaluation และ FASHN card เชื่อม license นี้อย่างชัดเจน **Assessment:** ขอบเขต Decision 5A ตรงกับการใช้ที่อนุญาตในข้อความนี้ โดยยังต้องปฏิบัติตาม license/notices และข้อกำหนด derivative/redistribution ไม่มีข้อห้าม surveillance-specific ที่พบใน SegFormer/FASHN terms ที่ตรวจ การที่ model card แสดงคำว่า production ไม่ได้ลบข้อจำกัด license ส่วน MIT-B4 เป็นชื่อ architecture ไม่ใช่ MIT license [Official model card](https://huggingface.co/fashn-ai/fashn-human-parser/blob/1f80c34dbab321c5730dda5c3fea279fd3e97498/README.md), [SegFormer license](https://github.com/NVlabs/SegFormer/blob/master/LICENSE)

**Verified fact:** Sapiens2 §1(b)(vi)(i) ห้าม surveillance รวมถึง research/development ที่เกี่ยวข้อง **Assessment:** academic scope ไม่ปลดข้อห้ามนี้ และการเริ่ม smoke บน MHP-v2 ไม่ใช่ช่องทางเลี่ยง intended-use restriction [Pinned Sapiens2 license](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/LICENSE.md)

สำหรับ M2FP/CPI/D2FP/SCHP การไม่พบ separate weight license คือ **ความไม่แน่นอนเรื่อง applicability** ไม่ใช่ข้อพิสูจน์ว่า weights ทุกตัวถูกห้ามใช้หรือว่าต้องมี license อีกฉบับเสมอ ต้องเก็บหลักฐานว่าการเผยแพร่ asset ที่เลือกอยู่ภายใต้ grant ใดก่อน executing ไม่ตีความลิงก์สาธารณะเป็น blanket permission [M2FP](https://github.com/soeaver/M2FP/blob/17a89decacfca347ed18bed66baec7a5847ea43c/LICENSE), [CPI](https://github.com/HAG-uestc/CPI-Parser/blob/d62cae523ba913fec4a7fda5816bc1d96bbf644d/LICENSE), [D2FP release](https://github.com/cvlab-yongin/D2FP/releases/tag/weights), [SCHP](https://github.com/GoGoDuck912/Self-Correction-Human-Parsing/blob/eb84c432cc697f494d99662a05f2335eb2f26095/LICENSE)

Optional: QANet และ RP-R-CNN มี pinned MIT LICENSE; selected weights/dependencies ยังไม่ได้ตรวจครบ CDGNet pinned tree ไม่พบ LICENSE/COPYING/NOTICE และยังไม่ยืนยัน grant จากที่อื่น จัด CODE_LICENSE_UNSPECIFIED_REVIEW_REQUIRED ไม่ติดตั้งหรือเพิ่ม roster อัตโนมัติ

## Dependencies ตรวจแยกจากตัวโมเดล

ตรวจ metadata และไฟล์ license จริงใน existing FASHN environment โดยไม่ import/load โมเดล: torch 2.14.0 มีหลาย bundled licenses; torchvision 0.29.0 BSD, transformers 4.57.1 / huggingface-hub 0.36.2 / safetensors 0.6.2 / OpenCV 4.11.0.86 มี Apache terms, NumPy 2.5.3 มี bundled BSD/MIT/อื่น ๆ, Pillow 12.3.0 MIT-CMU/third-party notices, PyYAML 6.0.3 MIT และ NVIDIA CUDA runtime 13.0.96 มี **proprietary EULA** แยก ไม่เรียก CUDA ว่า BSD เพราะ PyTorch ใช้ OSS licenses

ขอบเขตหลักฐานคือ local research use และ inspected notices/metadata ไม่ใช่ complete transitive SBOM หรือ certification สำหรับ redistribution/deployment Reference Detectron2, MMCV 1.7.0, MMDetection 2.25.1 เป็น Apache-2.0 และ InPlaceABN เป็น BSD-3-Clause; native legacy stacks ยังไม่ installed จึงไม่อ้างว่า audit tested dependencies ครบหรือ model ใช้งานได้

## Dataset / upstream / data-owner rights

| Component | สิ่งที่ยืนยัน | สิ่งที่ยังเปิด |
|---|---|---|
| MHP-v2 | Official project อนุญาต noncommercial academic research ภายใต้ stated terms | Annotation quality/leakage เป็นคนละ gate; terms ไม่รับรองความสะอาดของข้อมูล |
| CIHP DatasetNinja / native CIHP | Provider ระบุ MIT; PGN repo software มี MIT | ยังไม่ยืนยัน grant ของ original RGB/GT; software/converter MIT ไม่ใช่หลักฐาน dataset-owner permission |
| Frozen YOLO26x | คง existing AGPL/enterprise licensing reference และ weights เดิม | Academic status ไม่ลบ AGPL obligations; review รอบนี้ไม่รับรอง future distribution/deployment |
| Company CCTV | ผู้ใช้กำหนดบทบาทเป็น later student research evaluation | Owner permission/privacy safeguards ยังไม่ตรวจในรอบนี้; ไม่มี access/inference |

[MHP project terms](https://lv-mhp.github.io/), [CIHP preflight](CIHP_ARCHIVE_PREFLIGHT_AUDIT.md), [frozen YOLO record](../manifests/YOLO26X_SOURCE.json) ไม่มี PPSS activity หรือ license recheck ของ PPSS

## Correction ที่ได้จากการตรวจ source

FASHN card ระบุ proprietary curated fine-tuning data แล้ว จึงแก้ current registry จาก training dataset UNKNOWN เป็น declared proprietary FASHN dataset แต่ **exact composition / MHP-v2 / CIHP content overlap ยัง UNKNOWN**; ไม่ตีความว่า zero exposure Native geometry คือ width 384 × height 576

D2FP official LIP release ชี้ `d2fp_R101_bs64_72k_prior100_dec9.yaml` ไม่ใช่ `wo_enhance` ablation จึงแก้เฉพาะ V3 metadata/config hash ไม่อ้าง load compatibility หรือผล accuracy ทะเบียน V1/V2 และ checkpoint manifests เดิมเก็บ unchanged

## ข้อเสนอ execution ที่ต้องอนุมัติ

FASHN official pinned safetensors **256,146,352 bytes (~256 MB)** และ same-revision small metadata; combined download cap **300 MB** ใช้ existing isolated environment ไม่ install dependencies เพิ่ม Initial 1 / สูงสุด 3 readable TRAIN IDs **967, 14282, 4480**; native FP32/T4, export/dimensions/class/coordinate/NaN checks, hashes/VRAM/errors; สูงสุด 4 forward calls รวม native API parity ครั้งแรก ไม่มี accuracy scoring, final timing, validation/CCTV inference หรือ model ranking

ภาพทั้งสามถูก strict-load และ source/decoded hashes เทียบ canonical evidence แล้ว การใช้ GT geometry เพื่อ feasibility ไม่ได้ freeze crop/ownership policy และไม่รับรอง GT physical ownership Existing runner ยังมี historical raw DATASET_BLOCKED gate: หลัง approval ต้องปรับ gate ให้ตรวจ approved readable view + run-specific execution permission ก่อนรัน ห้ามปลด gate เพื่อ Stage 1 หรือรันล่วงหน้า หากต้อง dependencies เพิ่ม/GPU contention/FP32 ไม่ผ่าน ให้หยุดพร้อม diagnostics ไม่เปลี่ยน precision อัตโนมัติ

[Reviewable smoke proposal](../manifests/FASHN_SMOKE_PROPOSAL_V2.json), [component matrix](../provenance/LICENSE_MATRIX_DECISION5A_V1.csv), [current registry V3](../provenance/MODEL_VARIANT_REGISTRY_V3.csv), [source evidence](../provenance/LICENSE_REASSESSMENT_DECISION5A_V1.json)

**WAIT FOR USER APPROVAL.** Scope clarification แก้ intended-use ambiguity เท่านั้น ไม่ได้อนุมัติ weights/GPU smoke, native CIHP acquisition/quality audit, Stage 1 หรือ CCTV field test
