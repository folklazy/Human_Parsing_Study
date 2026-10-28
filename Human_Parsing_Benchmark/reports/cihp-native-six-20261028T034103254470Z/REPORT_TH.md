# ผลทดสอบ CIHP native — หก checkpoints แรก

Status: **FINISHED_WITH_INCOMPLETE_SYSTEMS** · 2026-10-28T09:33:43.118939+00:00
Run `cihp-native-six-20261028T034103254470Z`. Actual launch codecommit `5e8f36ae2a249295c6a1b424b066b010449da048`. Frozen configSHA256 `3b6c98ef8056bc24c0a503559972619b7cb82bcf40cdfa2983579a84567c5a24`. Source [PLAN](../../PLAN.md), compact [completion](../../runs/cihp-native-six-20261028T034103254470Z/COMPLETION.json). Dataset officialCIHPnativeVAL5000, nativeGT17520persons. This is a configured-system/YOLO-conditioned comparison using native labelspace, not architecture-only causality or an official parsingAP reproduction.

| System | Status | Complete/5000 | Failed | Invalid | Pending | mIoU20 inclBG | FG19mIoU |
|---|---|---:|---:|---:|---:|---:|---:|
|QANet_CIHP_HRNetW48_512x384|COMPLETE|5000|0|0|0|64.866%|63.449%|
|M2FP_R101_CIHP|COMPLETE|5000|0|0|0|68.155%|66.796%|
|D2FP_R101_CIHP|COMPLETE|5000|0|0|0|64.352%|62.827%|
|RPR_CIHP|INCOMPLETE|0|0|0|5000|N/A|N/A|
|CPI_R50_CIHP|INCOMPLETE|0|0|0|5000|N/A|N/A|
|CPI_ConvNeXtB_CIHP|INCOMPLETE|0|0|0|5000|N/A|N/A|

## วิธีอ่านผลและข้อจำกัด

- ใช้ STRICT_COMPLETE: ระบบที่ไม่ครบประชากรมีคะแนนหลัก null ไม่จัดอันดับจากชุดภาพสำเร็จที่ต่างกัน จะเรียกหกตัวครบได้เมื่อทุกแถว COMPLETE เท่านั้น ยังไม่ใช่ผลครบเก้าตัว และยังไม่รัน Sapiens หรือปรับ mapping/threshold/precision จาก VAL
- รายงาน IoU/support รายคลาส และ person-mask FP/FN/F1 ที่ threshold 0.50/0.75 แยกจาก semantic mIoU เพราะ semantic Q ไม่ลงโทษ unmatched FP โดยตรง Native references ห้าระบบใช้ผล inference เดียวกัน ไม่เพิ่มผู้สมัคร application หรือรันซ้ำ
- คะแนนหลัก native20 รวม background; FG19 เป็นคะแนนรอง ใช้ zero-union=0 ตาม reference ที่ประกาศไว้ Native Dress6 ไม่ใช่ CCIHP FaceMask6 เก็บ Face/Hair/เสื้อผ้าครบ native classes และไม่แบ่ง Dress เป็น upper/lower ด้วย heuristic
- คง 39 กลุ่มภาพ train–VAL ที่ bytes ซ้ำและหนึ่งกลุ่มซ้ำภายใน VAL ตาม official population ประวัติ training/selection exposure บางส่วนยัง UNKNOWN ไม่ใช่ NO GT native CIHP ต่างจาก CCIHP จึงไม่เทียบ raw scores กับผล taxonomy เดิมโดยตรง ทุกคะแนนอ้างอิง released annotations รวมข้อจำกัดคนพื้นหลังที่ไม่ได้ annotate
- Latency เป็น inline parser pipeline บนประชากรที่รันครบ หลัง TRAIN warmup และ CUDA synchronization ไม่ใช่ fresh YOLO end-to-end FPS คอลัมน์ peak memory เป็น parser allocated/reserved ของ frames ที่สำเร็จ ไม่ใช่หน่วยความจำระบบทั้งหมดหรือ peak ของ frame ที่ OOM ส่วน GPU monitor ใช้บันทึก contention ไม่ใช่หลักฐาน clean repeated timing
- เก็บ integer masks/extents/person scores/unowned outputs/geometry และ hashes ของ input/checkpoint/source/environment พร้อม attempt ledger ภายนอก Git ไม่เก็บ full logits จึงไม่อ้าง probability re-scoring Native confidence export รอบนี้จำกัดที่ canonical person-score outputs; quality-head scores เพิ่มเติมไม่ได้อ้างว่าเก็บครบ และ AP/PCP parity เป็น N/A

## หลักฐานและงานที่เหลือ

Canonical CSV/JSON tables under metrics/runID andruns/runID;externalbulkrootshownincompletionmanifest.Failed/incompletecandidatesremainvisible;errortracesandpendingIDsareintact.NoautoOOMretry/CPU/FP16fallbackoroldCPIresultrepair.Ninja/Sapiens/color/CCTV/traininguntouched.

งานที่เหลือ: ตรวจสาเหตุ failure/contract/resource ที่บันทึกไว้ และกำหนดการแก้แบบมี version แยก ไม่ retry failed images อัตโนมัติหรือเรียกว่าหกตัวครบ ผลของระบบอิสระที่รันครบยังคงเก็บไว้ตาม protocol เดิม

## ภาพเทียบผลที่กำหนดไว้ล่วงหน้า

สร้างภาพเทียบ 16 ภาพจาก sample ที่ล็อกก่อนดูคะแนน ใช้ RGB/GT และผลทั้งหกระบบบนพิกัดต้นฉบับ ไม่มี inference เพิ่ม และไม่เลือกรูปใหม่เพื่อสนับสนุนระบบใด เปิด `QUALITATIVE/index.html` ภายใต้ artifact root ของ run นี้ ภาพและ masks ไม่รวมใน public Git รายการไฟล์และ hashes อยู่ที่ `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/continuations/continuation-20261028T073741308461Z/assembled/QUALITATIVE/MANIFEST.json`

แถวบน: ภาพจริง / semantic GT / semantic predictions ของทั้งหกระบบ แถวล่าง: ภาพจริง / Human_ids GT / final person extents เลขคนเป็น local ID ในแต่ละ panel ไม่ใช่ผลจับคู่ GT หากระบบไม่มี committed output สำหรับภาพนั้น ให้แสดง N/A โดยไม่ใช้ partial packet แทนผลสำเร็จ ภาพใช้ประกอบการตีความ ไม่เปลี่ยน mapping, settings หรือกติกาการคัดเลือก

## Correction / controlled continuation

Original run interrupted; its LAUNCH/RUN and packets remain unchanged. This report uses verified original and disjoint continuation packets, with reconstructed statistics and exact population reconciliation. Continuation code commit: `e51464da35327811ee49453649394edbdd508872`. Original launch commit above is not a claim that the continuation controller existed at original launch.

- Primary results are YOLO ROI/association pipelines on native CIHP labels, not an official native-parser benchmark for all models.
- Timing is adapter diagnostics with unequal I/O boundaries; not clean parser-only or end-to-end speed ranking. CPI native file reads/writes are timed; global semantic composition/scoring is outside the timer.
- Historical RPR/CPI TRAIN inference fingerprints repeat across models; never use them alone as cache identity. Reuse here is exclusively hash-validated VAL packets with current model/checkpoint/input/source/config bindings.
- Artifacts support hard-label remapping under stored ownership, not every probability/native-confidence evaluation. M2FP/D2FP overlap arbitration precedes export.

No matrix/Sapiens/color execution is authorized by completion of this continuation.
