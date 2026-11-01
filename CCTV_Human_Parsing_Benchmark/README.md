# CCTV Human Parsing Benchmark

**Current status: four-target evaluation complete9/9 on reviewed GT domain.** [รายงานจบรอบ](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md) / [CSVหลัก](metrics/CONTROLLED_ROI_FOUR_TARGET_RESULTS.csv) / [STATUS](STATUS.md). Sapiens2 1Bได้Macro4สูงสุด65.430%;QANet64.533%และสูงสุดFace-domain/Upper. ใช้Face21จาก35items,Hair61/Upper112/Lower96;14Faceambiguitiesกันออกร่วมทุกโมเดล,Neckdeliveryn3. GTเป็นagent-assistedreference ไม่ใช่expertgoldหรือdeploymentacceptance. CPUscoringจบ ไม่มีinferenceใหม่หรือคิวรันต่อ.


## Previous proposal and historical results

**สถานะปัจจุบัน: GT_OWNER_REVIEW_REQUIRED / PROPOSED_NOT_FROZEN.** อ่าน [ข้อเสนอ controlled person-ROI และ Face/Neck](CONTROLLED_ROI_PROTOCOL_TH.md) → [STATUS](STATUS.md) → [หลักฐาน design review](reports/CONTROLLED_ROI_DESIGN_REVIEW.json). ผู้ใช้มอบหมายให้กำหนดวิธีประเมินที่เหมาะสม; ยังไม่มี inference รอบใหม่หรือการอนุมัติ batch เพิ่มจากการออกแบบนี้.

ข้อเสนอใช้ crop/context/YOLO ownership เดียวกันทั้ง9 checkpoints และ GT revision ที่แยก Face/Neck: headline Hair/Face-on-neck-excluded-domain/Upper/Lower เท่ากัน25%, พร้อม Face+Neck delivery แยก. ต้องปิด GT owner/contour QA และ adapter/scorer readiness ก่อน; Face view ไม่รับรอง strict face-only capability.

**ผลเก่าที่เก็บไว้:** [selected annotated-part IoU/Dice](reports/CCTV_SELECTED_PART_RESULTS_TH.md),9/9×90ภาพ และ [fresh Sapiens6ภาพ×3ขนาด](reports/SAPIENS2_MEASUREMENT_REVIEW_TH.md). ค่าจาก GT เดิมเป็น historical agreement; ไม่ใช้รับรองผู้ชนะจน owner correction/GT requirements พร้อม. input ต่างกันตาม route จริง: QANet ROI, Sapiens full frame, native instance parsers full frame+association.

## Historical protocols and completed evidence

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
