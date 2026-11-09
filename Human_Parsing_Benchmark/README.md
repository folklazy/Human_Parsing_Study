# ผลล่าสุด: สามคลาสหลัก + Face-local (CIHP และ CCTV)

อัปเดต 2026-11-09T17:40:23.483262+07:00 รายงานปัจจุบันมีหัวข้อเหมือนกันทั้ง CIHP/CCTV ครบคะแนน 4 targets, mIoU3/Macro4-local, binary confusion, Precision/Recall/F1, ส่วนที่พลาด, person matching, timing และ source bindings ดู[รายงานพร้อมภาพ matrix](reports/CIHP_COMMON_NINE_RESULTS_TH.md#confusion-matrix-และความครบของแต่ละส่วน)

**ครบทั้งเก้า checkpoints ในสอง dataset** — CIHP 5,000 และ CCTV 90 ภาพต่อโมเดล ใช้ saved predictions ไม่มี inference ใหม่ ทั้งสองชุดใช้กติกาจับคู่คน สูตร วิธีเฉลี่ย และการให้คะแนนในกรอบ Face GT เดียวกัน แต่ GT ยังเป็นคนละ reference รายงานสามคลาสและ Face แยกกัน พร้อม Macro4-local ที่เฉลี่ยสี่ target เท่ากัน

| Dataset | สามคลาสหลัก | Face-local | ค่าเฉลี่ยสี่คลาส Macro4-local |
|---|---|---|---|
| CIHP | Sapiens2 0.4B 73.163% | M2FP 81.423% | **M2FP 75.018%** |
| CCTV | Sapiens2 1B 61.806% | Sapiens2 1B 69.497% | **Sapiens2 1B 63.729%** |

[รายงานหลักพร้อมนิยาม สูตร ข้อจำกัด และแหล่งที่มา](reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md) · [สถานะ](STATUS.md)

อัปเดต 2026-11-09T17:19:52.672427+07:00 เพิ่มค่าเฉลี่ยสี่คลาสและตารางเวลาต่อภาพ/เวลารวมจาก logs ใน[รายงานเดิม](reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md#ค่าเฉลี่ยสี่คลาสและเวลาจากการรันที่บันทึกไว้) CIHP มี timing ครบ 5,000 ภาพต่อโมเดล ส่วน CCTV Sapiens มี 84/90 ภาพ จึงคงค่าเวลาทั้งชุดเป็น null ตามข้อมูลที่มี

<!-- SPEED_OVERVIEW_START -->

## เวลาประมวลผล parsing ต่อภาพ

หน่วยวินาทีต่อภาพ คำนวณจากผลรวมเวลา adapter ของทุก person ROI ในภาพ แล้วเฉลี่ยตามจำนวนภาพที่มีเวลาครบ ตารางแสดงเวลาที่บันทึกระหว่างการใช้ GPU ร่วม

| โมเดล | CIHP วินาที/ภาพ | ภาพที่มีเวลา | CCTV วินาที/ภาพ | ภาพที่มีเวลา |
|---|---:|---:|---:|---:|
| QANet | 0.352 | 5,000/5,000 | 0.110 | 90/90 |
| M2FP | 1.038 | 5,000/5,000 | 0.318 | 90/90 |
| D2FP | 3.067 | 5,000/5,000 | 1.004 | 90/90 |
| RP-R-CNN | 1.095 | 5,000/5,000 | 0.328 | 90/90 |
| CPI R50 | 10.178 | 5,000/5,000 | 4.325 | 90/90 |
| CPI ConvNeXt-B | 2.974 | 5,000/5,000 | 0.709 | 90/90 |
| Sapiens2 0.4B | 6.742 | 5,000/5,000 | 1.931 | 84/90 |
| Sapiens2 0.8B | 13.927 | 5,000/5,000 | 4.001 | 84/90 |
| Sapiens2 1B | 19.976 | 5,000/5,000 | 5.672 | 84/90 |

ตัวอย่าง QANet บน CIHP ใช้เวลา parsing รวมทุกคนในภาพเฉลี่ย 0.352 วินาที ส่วน Sapiens2 1B เฉลี่ย 19.976 วินาทีต่อภาพ จำนวน ROI ต่อภาพมีผลต่อเวลานี้

CCTV ของ Sapiens แต่ละรุ่นใช้ค่าเฉลี่ยจาก 84 ภาพที่มี timing ครบ อีก 6 ภาพใช้ predictions เดิมซึ่งขาด adapter timer ของรอบนี้ ค่าเฉลี่ยดังกล่าวจึงใช้ตัวหาร 84 ภาพ

ขอบเขต adapter ครอบ preprocessing, model call และ map-back ตาม implementation รวม native file I/O ของ CPI ส่วน YOLO, การส่งออก packet และการให้คะแนนอยู่ภายนอกช่วงนี้ ขอบเขต timer ของ CCTV continuation รวมงานรอ GPU และบันทึกทรัพยากรด้วย รายละเอียดและเวลารวมอยู่ในตารางเวลาของรายงานหลัก

[เปิดตารางเวลารวมและรายละเอียดการจับเวลา](reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md#เวลาต่อภาพและเวลารวม)

<!-- SPEED_OVERVIEW_END -->

## ประวัติรายงานและสถานะก่อนหน้า (historical views)

> **Current controlled CIHP: QUALITY_COMPLETE 9/9** (verified 2026-11-08T01:22:12.700583+07:00). Each checkpoint has exact 5,000 accepted IDs and non-null canonical primary metrics. Latest sequential queue has stopped; no inference worker remains. Controlled-results consolidation and live/clean speed measurement remain separate next steps. [Current report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md) / [STATUS](STATUS.md).

The older notices below are historical snapshots; use the current report above for this controlled run.

> **Current controlled CIHP (2026-11-06T17:56:51.856783+07:00):** Sapiens was operator-paused to finish CPI readiness. Sequential1B→CPIConvNeXt queue launched17:58:41Thai in tmux `cihp_seq_20261106T105503Z`;1BVALIDATION_RUNNING(firstnewpacketPASS,snapshot4269/5000at18:03:31Thai),CPIqueued; accepted1B4268/CPI4335frames, pending732/665. CPI diagnostic passed; R50complete5000 not rerun. No parallelGPUjobs. [STATUS](STATUS.md) / [Report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md).

> **Current CIHP controlled queue (2026-11-06T17:24:11.176769+07:00):** Sapiens1B resumed and new packet verified. Snapshot4,223/5,000;reused4,222frames/20,101ROIs,failed0invalid0. User removed only1B's wall-time cap; other guards stay. `tmux attach -t cihp_1b_finish` shows the live viewer. [STATUS](STATUS.md) / [Report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md).

> **Current CIHP controlled queue (2026-11-06T17:05:51.585401+07:00):** Queue stopped. Sapiens2 1B hit the24h wall-time guard at4,222/5,000;778frames remain and primary=null. Seven systems are complete;ConvNeXt remains held at4,335. No GPU worker is running. Continuation needs packet reconciliation and an explicit time-budget amendment; the remaining tmux viewer is not a worker. [Report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md) / [STATUS](STATUS.md).

> **Historical snapshot (2026-11-05T15:33:58+07:00):** Seven systems complete, including recovered Sapiens2 0.8B; Sapiens2 1B running in tmux `cihp_resume_20261105T044738Z`. ConvNeXt remains held incomplete. [Report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md) / [STATUS and progress command](STATUS.md).

> **Current controlled CIHP queue (2026-11-04T09:38:00+07:00):** Five systems complete; CPI ConvNeXt-B stopped on CUDA OOM at 4,335/5,000 and remains incomplete; Sapiens2 0.4B is running in the existing tmux queue. [Report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md) / [STATUS](STATUS.md). Use `.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/continue_controlled_cihp_resources.py progress` from the workspace root for live counts.

> **Current controlled CIHP continuation:** QANet/M2FP/D2FP complete; RP-R-CNN empty-native decoder repaired and fresh segment running. [Current report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md) / [STATUS](STATUS.md). Use `.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/continue_controlled_cihp.py progress` from workspace root for the combined parent/continuation state.

> **Controlled CIHP implementation — 2026-11-02T19:05:31.621985+07:00** CPU acceptance13casesผ่านสองenvironments; frozenqualitymanifest5000frames/24,062ROIs×9พร้อม. GPU TRAINgateยังpendingก่อนVAL. [รายงานรอบใหม่](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). Live/clean speedphaseยังpendingแยกจากqualityqueue

> **Comparability review — 2026-11-02T18:03:20.041685+07:00:** ตรวจ CIHP กับ CCTV90 และคำนวณ aggregation sensitivity แล้ว: input route, ownership, Face domain และหน่วยเฉลี่ยต่างกัน จึงไม่ใช่การวัดเงื่อนไขเดียวกันข้าม dataset. [รายงานตรวจละเอียด](reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md) · audit 9 systems / 36 targets PASS; ผลเดิมคงเดิม. Controlled CIHP ROI ยังไม่รันและยังไม่ผ่าน readiness.

> **Current CCTV design:** [controlled person-ROI and Face/Neck proposal](../CCTV_Human_Parsing_Benchmark/CONTROLLED_ROI_PROTOCOL_TH.md), PROPOSED_NOT_FROZEN. Derived GT/scorer/route readiness precede any new batch; CIHP frozen results are unchanged.

> **CCTV status: GT_OWNER_REVIEW_REQUIRED.** [Sapiens measurement review](../CCTV_Human_Parsing_Benchmark/reports/SAPIENS2_MEASUREMENT_REVIEW_TH.md) confirms source-owner conflicts and reports bounded fresh0.4/0.8/1B ROI diagnostics. Nine-system CCTV selection is on hold; CIHP results below remain frozen.

> **Current: common C4-P revision2 COMPLETE 9/9 checkpoints, 5,000 CIHP VAL IDs each.** [รายงานผลและ shortlist](reports/CIHP_COMMON_NINE_RESULTS_TH.md) → [STATUS](STATUS.md) → [normalized canonical result index](manifests/CIHP_COMMON_RESULT_INDEX.json). Native20 results preserved; CPI added by saved-only CPU scoring, no model inference.

The notices below are historical snapshots; STATUS is current.

> **Current approved work: full CIHP–Sapiens C4-P evaluation.** [Report/status](reports/CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md) → [STATUS](STATUS.md). Saved-only four systems + Sapiens2 0.4B; reuse6/pending4,994; no CPI/other sizes/newYOLO.

> **CPI operator commands prepared; no new inference.** [คำสั่ง R50 / ConvNeXt-B และ progress](docs/CPI_CONTINUATION_COMMANDS_TH.md). ใช้ผลเดิม 3/113 ภาพตามลำดับ; manual continuation ยังเสี่ยง OOM

> **Current outcome: C4-P Sapiens2 0.4B pilot PASS (6/6 +1warmup,7-callbudgetconsumed).** [Closure report](reports/CIHP_SAPIENS_04B_PILOT_TH.md) → [STATUS](STATUS.md). CPU23cases/GTbindings/QANetextentparityverified; fullcommonscoresnotrun. Nativefour/CPIhistorypreserved;noautomaticnextmodel.

> CPI ConvNeXt manual continuation หยุดจาก OOM หลังรวม145/5000; [รายงานไทย](reports/convnext-20261029T070405365918Z.md). แยกจาก common-view batch ที่ยังทำงาน

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
