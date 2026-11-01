# CCTV Human Parsing Benchmark

> **อัปเดต 2026-11-01T10:16:54.165252+07:00: GT_OWNER_REVIEW_REQUIRED.** พบsourceownerlabelsรวมส่วนจากคนละคนอย่างน้อย2ภาพ พักการใช้ตาราง90ภาพเพื่อตัดสินเลือกโมเดล;ค่าผลเดิมเก็บเป็นhistoricalagreementกับGTที่ให้มา. [ผลตรวจและfreshSapiensทั้ง3ขนาด](reports/SAPIENS2_MEASUREMENT_REVIEW_TH.md).

**ผลล่าสุด: [รายงาน selected annotated-part IoU/Dice ครบ 9 ระบบ](reports/CCTV_SELECTED_PART_RESULTS_TH.md)** — QANet สูงสุดตามเกณฑ์นี้: IoU4 61.773%, Dice4 69.203%. ใช้ saved masks เดิม ไม่มี inference ใหม่. Primary 315 ส่วน; รายงาน sensitivity ครบ 324 ส่วนด้วย. เป็นผลบนคน/ส่วนที่ annotate หลัง agent-assisted visual screen ไม่ใช่ full-scene IoU หรือ independent expert certification.

อ่าน [STATUS](STATUS.md) → [selected-part protocol](SELECTED_PART_PROTOCOL.md) → [ตารางเต็ม](metrics/SELECTED_PART_PER_TARGET.csv). เนื้อหา positive-domain benchmark ด้านล่างเก็บเป็นบริบทของรอบเดิม; ผลและ GT เดิมไม่เปลี่ยน.

ทดสอบ pretrained parsing 9 checkpoints เดิมกับ CCTV partial annotations โดยเก็บภาพและ artifacts ภายใน workspace เท่านั้น เริ่มอ่าน [PROTOCOL.md](PROTOCOL.md) → [STATUS.md](STATUS.md) → [ผลจริง](reports/RESULTS_TH.md)

นี่เป็น experiment แยกที่ workspace root ตาม AGENTS.md ใช้ shared code จาก `../Human_Parsing_Benchmark/src/`, weights `../models/`, environments `../.venvs/` และ dataset `../datasets/CCTV_100_Evaluation/` ไม่มีการย้ายหรือลบงานเดิม ไม่มี nested Git ข้อมูล CIHP/native/common results เดิมคงเดิม

ชุดนี้มี90ภาพจริง (48day/42night),127คนที่มีannotatedparts. รู้labelsเฉพาะบางคน/บางส่วน จึงไม่รายงานfull-image mIoU/FP/personF1หรือoveralldeploymentwinner. ใช้macrorecall4และcross-classconfusionบนknownannotationpixels. ชื่อโฟลเดอร์100ไม่ใช่จำนวนประชากรที่ยืนยัน

## คำสั่ง

ใช้ path ของ environment โดยตรง ห้าม resolve symlink ของ Python จนหลุด environment:

```bash
.venvs/sapiens2-pilot/bin/python CCTV_Human_Parsing_Benchmark/scripts/benchmark.py --config CCTV_Human_Parsing_Benchmark/outputs/cctv-partial-20261031T1800Z/CONFIG.json
```

คำสั่งข้างบนอัปเดตรายงานจากstateที่บันทึกไว้เท่านั้น ไม่เปิดinference. Live progressอ่าน `outputs/<run>/BATCH_STATUS.json`, `CURRENT_WORKER.json`, `<model>/STATE.json` และ log ชื่อmodel. Ctrl+Cของviewerไม่หยุดdetachedcontroller

การรันใช้ `--run` เฉพาะfreshfrozenrunที่อนุญาตแล้ว ไม่มีautomaticretry/resume; ถ้ามีpartial/failedattemptต้องreconcileก่อน ห้ามลบหรือทับไฟล์เดิม

## Git และ privacy

PUBLIC repoเดิม `folklazy/Human_Parsing_Study` เก็บเฉพาะcode/tests/protocol/aggregateaudit/status/reportที่ตรวจแล้ว. ห้ามsyncCCTVimages/filenames/annotations/metadata/personroles/masks/logsขึ้นpublicGit. Local `outputs/` เก็บprivateinputmanifest,fullnative integer masks,YOLOcache,geometry/ownership/confidences,hashes,scoreconfusion,ledger,environment/attemptfailures. ไม่มีinferenceเพื่อการสี/training/CCTVtrackingในรอบนี้

เกณฑ์ยกระดับสู่ full benchmark ที่เลือก configuration ได้: [FULL_BENCHMARK_ACCEPTANCE_TH.md](reports/FULL_BENCHMARK_ACCEPTANCE_TH.md). รอบปัจจุบันไม่สร้าง labels ที่ยังขาดขึ้นมาเอง

ดู progress จริงแบบ read-only:

```bash
python3 CCTV_Human_Parsing_Benchmark/scripts/progress.py --watch
```

กด Ctrl+C ปิดเฉพาะviewer ไม่หยุดcontroller. PID/สถานะล่าสุดอ่านจากprivateJSONจริง; publicGitเป็นsnapshotตอนsync ไม่ใช่liveสถานะ

## Metric audit — 1 November2026

[เหตุผลที่ไม่มี full-image IoU และผล IoU บน known annotation domain](reports/CCTV_METRIC_AUDIT_TH.md) ตรวจจาก canonical source/GT/ledgers/scoring artifacts เดิม ไม่มี inference ใหม่. ตัวเลขที่เพิ่มเป็น post-hoc diagnostics ไม่แทน primary recall4 หรือยืนยัน full-scene/deployment winner.

## Sapiens2 input audit

[ตรวจ preprocessing](reports/SAPIENS2_PREPROCESSING_AUDIT_TH.md): CPU12casesตรงofficialinputทุกค่า; ยังไม่พบchannel/normalizationbug. Full-frame stretchเปลี่ยนสัดส่วนคนอย่างมากและต่างจากROIroute จึงยังไม่อ้างสาเหตุarchitectureหรือความด้อยของSapiensทุกรูปแบบ. ไม่มีlearnedforwardใหม่หรือคะแนนเปลี่ยน.

## Latest Sapiens input experiment

[Input diagnostic report](reports/SAPIENS2_INPUT_DIAGNOSTIC_TH.md):0.4B/6images/31parts, mean selected-partIoU4: full-frame37.447%,full-frameletterbox29.913%,YOLOROIletterbox59.575%. Input-routeeffectobserved; notfull90reranking/architectureclaim.25callscompleted; numericalcontrolgatehistoryretained. Noadditionalexperimentstartedautomatically.

## Latest Sapiens measurement review

[Independent scoring review and fresh three-size ROI results](reports/SAPIENS2_MEASUREMENT_REVIEW_TH.md):90-image saved score audit plus6-image fresh0.4/0.8/1Bdiagnostic. Bothaggregation/YOLO/nativeerrorsandinputeffectsreported; nofull90ROIbenchmarkstarted.
