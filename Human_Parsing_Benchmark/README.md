> **Current outcome: C4-P Sapiens2 0.4B pilot PASS (6/6 +1warmup,7-callbudgetconsumed).** [Closure report](reports/CIHP_SAPIENS_04B_PILOT_TH.md) → [STATUS](STATUS.md). CPU23cases/GTbindings/QANetextentparityverified; fullcommonscoresnotrun. Nativefour/CPIhistorypreserved;noautomaticnextmodel.

# Human Parsing Benchmark

เปรียบเทียบ pretrained human parsing checkpoints/configurations เพื่อแยกส่วนร่างกาย เสื้อผ้า และ accessories ที่รองรับ ในงานวิจัยนักศึกษาอิสระ ผลเป็นการเปรียบเทียบ configuration ไม่ใช่การแยกผลของ architecture หรือข้อมูลฝึกโดยลำพัง

## เริ่มอ่าน

**README → [STATUS](STATUS.md) → [PLAN](PLAN.md) → [decisions](docs/DECISIONS.md)**

แผนปัจจุบันคือ [CIHP native Parsing9](proposals/CIHP_NATIVE_PARSING9_CODEX_PLAN_TH_20261028.md) ที่ผู้ใช้สั่งให้ใช้แทนข้อเสนอ CCIHP เดิม ขั้นตอนคือ **native CIHP หกตัวแรก → semantic compatibility matrix → Sapiens2 สามตัวบน CIHP → งานสีภายหลัง** การเก็บ inventory ไม่เท่ากับรัน benchmark ครบทุกรุ่น

| เรื่อง | แหล่งหลัก |
|---|---|
| สถานะและงานถัดไป | [STATUS.md](STATUS.md) |
| กติกาที่ใช้งานปัจจุบัน | [PLAN.md](PLAN.md) |
| Exact roster/checkpoint/source bindings | [CIHP_NATIVE_ROSTER.csv](registry/CIHP_NATIVE_ROSTER.csv), [frozen config](configs/cihp_native_six.json) |
| Population official CIHP native VAL 5,000 | [CIHP_NATIVE_VALIDATION.json](manifests/CIHP_NATIVE_VALIDATION.json) |
| ข้อมูลนำเข้าและ strict decoding/readiness | [intake](reports/CIHP_NATIVE_ARCHIVE_INTAKE.md), [readiness](reports/CIHP_NATIVE_READINESS.md) |
| Launch identity และหลักฐานของ batch ปัจจุบัน | [run manifest](runs/cihp-native-six-20261028T034103254470Z/READINESS_MANIFEST.json), [launch](runs/cihp-native-six-20261028T034103254470Z/LAUNCH_MANIFEST.json) |
| ภาพ diagnostics ที่ล็อกก่อนคะแนน | [16-image sample](manifests/CIHP_NATIVE_DIAGNOSTIC_SAMPLE.json) |
| ประวัติการทำงาน | [WORK_LOG.md](WORK_LOG.md) |
| งาน/โค้ด/ผลเดิมและตำแหน่ง assets | [legacy references](docs/LEGACY_REFERENCES.md), [workspace layout](docs/WORKSPACE_LAYOUT.md) |

## การทดลองปัจจุบัน

- First six: **QANet CIHP HRNet-W48 512×384, M2FP R101 CIHP, D2FP R101 CIHP, RP-R-CNN CIHP R50, CPI R50 CIHP, CPI ConvNeXt-B CIHP**
- CIHP native labels 20 รวม background / 19 foreground; Dress ID6 คงเป็น Dress ไม่ใช้ CCIHP FaceMask ID6 และไม่ใช้ denominator 4,961 จากแผนเดิม
- QANet ใช้ frozen YOLO ROI และ mask ownership อีกห้าตัวใช้ native full-frame API แล้ว association กับ frozen YOLO แบบ prediction-only; native references แยกจากผล application โดย reuse inference เดียวกัน
- Native20 mIoU เป็นคะแนนหลัก, foreground19/per-class และ person-mask FP/FN/F1/coverage semantic quality แยกกัน ไม่เรียก custom metrics ว่า official AP/PCP
- **STRICT_COMPLETE**: ระบบไม่ครบมีคะแนนหลัก null และยังอยู่ในตารางพร้อม failure/pending counts ไม่จัดอันดับจากภาพสำเร็จที่ต่างกัน
- FP32/T4, native preprocessing/TTA/thresholds ที่ bind ไว้; ไม่มี automatic OOM retry, CPU/FP16 fallback หรือการ tune จาก VAL
- เวลาเป็น synchronized parser-pipeline diagnostics ไม่รวม source I/O/export/scoring และไม่ใช่ fresh YOLO end-to-end FPS; ข้อจำกัด memory/timing อยู่ใน PLAN/config

อนุมัติรันหกตัวแรกเมื่อ readiness ผ่านแล้ว และ batch เริ่มแล้ว ดูสถานะจริงใน STATUS และ external `LAUNCH.json` ไม่ใช้ข้อความเก่าที่เคยห้าม Prompt A inference เป็นสถานะปัจจุบัน Sapiens2 0.4B/0.8B/1B ยังรอ matrix; Ninja พักไว้ งานสี/attributes/CCTV/training ยังไม่เริ่ม

## Working copy, Git และ artifacts

`Human_Parsing_Benchmark/` ระดับ workspace root เป็น working copy หลัก ส่วน `Human_Parsing_Study_Public/Human_Parsing_Benchmark/` เป็น publication copy ใน [folklazy/Human_Parsing_Study](https://github.com/folklazy/Human_Parsing_Study) ใช้ explicit path/hash sync ไม่สร้าง Git ซ้อนหรือย้ายโครงการเดิม

datasets อยู่ shared `datasets/`, checkpoints อยู่ `models/`, environments อยู่ `.venvs/` โค้ด/compiled shims และหลักฐานเดิมที่ reuse ยังอยู่ตำแหน่งเดิม ไม่คัดลอก source ทั้งชุดเพื่อจัด repository

Bulk artifacts ของ batch นี้อยู่ `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/` ชื่อนี้เป็น artifact location ที่กำหนดไว้ ไม่ได้หมายความว่าข้อมูลประเมินเป็น MHP-v2 ดู `LAUNCH.json`, `validation/<model>/RUN.json`, `FRAMES.jsonl`, `packets/` และ logs สำหรับสถานะจริง ตัวติดตามไม่เริ่ม inference/retry และจะสรุป comparative report หลัง batch สิ้นสุด ภาพเทียบใช้ sample เดิมทั้งหกระบบ ไม่มีเลือกภาพตามคะแนน

Git เก็บ source/tests/configs/manifests/provenance/reports และ CSV สรุปที่เผยแพร่ได้ ไม่รวม datasets/weights/bulk masks/logits/logs/CCTV หรือ environment binaries การ clone repository อย่างเดียวไม่สามารถ reproduce GPU run ได้ ต้องมี external assets และ environments ตาม bindings ก่อน

## ประวัติที่ยังคงไว้

YOLO26x-Seg เป็น frozen baseline ที่เลือกแล้ว ไม่เปิดเลือกใหม่ ผล CPI กลุ่มเดิมคง `FINISHED_WITH_INCOMPLETE_SYSTEMS`/null ตามจริง และไม่ใช้เป็นคะแนนของ batch CIHP native ใหม่นี้

ข้อเสนอ CCIHP เจ็ด checkpoints/สิบ configurations และเอกสาร Prompt A เดิมยังอ่านย้อนหลังได้ใน [protocol review](reports/HUMAN_PARSING_PROTOCOL_REVIEW_TH.md), [legacy references](docs/LEGACY_REFERENCES.md) และ Git history แต่ไม่ใช่ launch scope ปัจจุบัน การเปลี่ยนแผนไม่แก้ frozen results/GT และไม่อ้างว่ารู้ผลใหม่ก่อนเริ่มรัน

## Controlled continuation — current operational pointer

The original batch was interrupted; original LAUNCH/RUN RUNNING labels are preserved stale records, not liveness checks. Read [STATUS](STATUS.md) and [continuation/correction report](reports/CIHP_CONTROLLED_CONTINUATION.md). The continuation uses verified original packets plus disjoint fresh segments; no successful image is re-inferred. Its separate state lives under the parent artifact root's `continuations/` directory. No matrix/Sapiens/color run starts automatically.

## ดู progress สดโดยไม่ต้องถามแชท

จาก workspace root ใช้:

```bash
python3 Human_Parsing_Benchmark/scripts/rpr_progress.py --watch
```

แสดงจำนวน/เปอร์เซ็นต์ inference, ความคืบหน้าตรวจ artifacts, ภาพล่าสุด, failed/invalid และ worker/controller PID ทุก5วินาที กด Ctrl+C ปิดเฉพาะตัวดู งาน inference ไม่หยุด ใช้ `--json` สำหรับ agent หรือไม่ใส่ `--watch` เพื่อดูครั้งเดียว ตัวเลข100%ของ inference ยังไม่ใช่การตรวจปิดรอบสำเร็จ ต้องรอ phase COMPLETE หลังตรวจ artifacts คำสั่งอ่านข้อมูลเดิมเท่านั้น ไม่มี GPU/model imports หรือ inference เพิ่ม รูปแบบนี้ควรใช้เป็นมาตรฐานแสดง progress ของรอบถัดไปโดยผูกกับ model/round จริง

## CPI R50 live progress

```bash
python3 Human_Parsing_Benchmark/scripts/cpi_r50_progress.py --watch
```

Read-only 5-second view of inference, separate artifact verification, failures and PID liveness. Ctrl+C stops only this viewer. Use `--json` or omit `--watch` for one snapshot. The RP-R-CNN viewer still reads its own completed round; CPI has a separate round pointer and model bindings.
