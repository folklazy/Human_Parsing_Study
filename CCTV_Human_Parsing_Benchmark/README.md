# ผลล่าสุด: สามคลาสหลัก + Face-local (CIHP และ CCTV)

อัปเดตบัญชีเวลา 2026-11-09T17:51:26.842995+07:00 ตรวจคืน original forward timers ของ CCTV Sapiens แล้วครบ 90 ภาพ/130 ROI ต่อขนาด ตารางแสดงกลุ่ม A/B/C และรายละเอียดช่วงที่วัดได้

อัปเดต 2026-11-09T17:40:23.483262+07:00 รายงานปัจจุบันมีหัวข้อเหมือนกันทั้ง CIHP/CCTV ครบคะแนน 4 targets, mIoU3/Macro4-local, binary confusion, Precision/Recall/F1, ส่วนที่พลาด, person matching, timing และ source bindings ดู[รายงานพร้อมภาพ matrix](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#confusion-matrix-และความครบของแต่ละส่วน)

**ครบทั้งเก้า checkpoints ในสอง dataset** — CIHP 5,000 และ CCTV 90 ภาพต่อโมเดล ใช้ saved predictions ไม่มี inference ใหม่ ทั้งสองชุดใช้กติกาจับคู่คน สูตร วิธีเฉลี่ย และการให้คะแนนในกรอบ Face GT เดียวกัน แต่ GT ยังเป็นคนละ reference รายงานสามคลาสและ Face แยกกัน พร้อม Macro4-local ที่เฉลี่ยสี่ target เท่ากัน

| Dataset | สามคลาสหลัก | Face-local | ค่าเฉลี่ยสี่คลาส Macro4-local |
|---|---|---|---|
| CIHP | Sapiens2 0.4B 73.163% | M2FP 81.423% | **M2FP 75.018%** |
| CCTV | Sapiens2 1B 61.806% | Sapiens2 1B 69.497% | **Sapiens2 1B 63.729%** |

[รายงานหลักพร้อมนิยาม สูตร ข้อจำกัด และแหล่งที่มา](../Human_Parsing_Benchmark/reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md) · [สถานะ](STATUS.md)

อัปเดต 2026-11-09T17:19:52.672427+07:00 เพิ่มค่าเฉลี่ยสี่คลาสและตารางเวลาต่อภาพ/เวลารวมจาก logs ใน[รายงานเดิม](../Human_Parsing_Benchmark/reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md#ค่าเฉลี่ยสี่คลาสและเวลาจากการรันที่บันทึกไว้) CIHP มี timing ครบ 5,000 ภาพต่อโมเดล ส่วน CCTV Sapiens มี adapter timers 84/90 ภาพ และเพิ่มบัญชีเวลา A+C ที่ตรวจผูกกับ logs เดิมครบ 90/90 ภาพแล้ว

<!-- SPEED_OVERVIEW_START -->

## เวลาประมวลผล parsing ต่อภาพ

หน่วยวินาทีต่อภาพ คำนวณจากผลรวมเวลา adapter ของทุก person ROI ในภาพ แล้วเฉลี่ยตามจำนวนภาพที่มีเวลาครบ ตารางแสดงเวลาที่บันทึกระหว่างการใช้ GPU ร่วม

| โมเดล | CIHP วินาที/ภาพ | ภาพที่มีเวลา | CCTV ช่วงที่มีบันทึก s/ภาพ | ภาพที่มีเวลา |
|---|---:|---:|---:|---:|
| QANet | 0.352 | 5,000/5,000 | 0.110 | 90/90 |
| M2FP | 1.038 | 5,000/5,000 | 0.318 | 90/90 |
| D2FP | 3.067 | 5,000/5,000 | 1.004 | 90/90 |
| RP-R-CNN | 1.095 | 5,000/5,000 | 0.328 | 90/90 |
| CPI R50 | 10.178 | 5,000/5,000 | 4.325 | 90/90 |
| CPI ConvNeXt-B | 2.974 | 5,000/5,000 | 0.709 | 90/90 |
| Sapiens2 0.4B | 6.742 | 5,000/5,000 | 2.000 | 90/90 |
| Sapiens2 0.8B | 13.927 | 5,000/5,000 | 4.162 | 90/90 |
| Sapiens2 1B | 19.976 | 5,000/5,000 | 5.917 | 90/90 |

ตัวอย่าง QANet บน CIHP ใช้เวลา parsing รวมทุกคนในภาพเฉลี่ย 0.352 วินาที ส่วน Sapiens2 1B เฉลี่ย 19.976 วินาทีต่อภาพ จำนวน ROI ต่อภาพมีผลต่อเวลานี้

CCTV ของ Sapiens รวม 115 adapter timers กับ 15 original forward intervals ครบ 90 ภาพแล้ว โดย preprocessing/map-back ของ 15 ROI เดิมอยู่นอกช่วงนั้น ตารางนี้เป็นบัญชีเวลาตามขอบเขต A+C

ขอบเขต adapter ครอบ preprocessing, model call และ map-back ตาม implementation รวม native file I/O ของ CPI ส่วน YOLO, การส่งออก packet และการให้คะแนนอยู่ภายนอกช่วงนี้ ขอบเขต timer ของ CCTV continuation รวมงานรอ GPU และบันทึกทรัพยากรด้วย รายละเอียดและเวลารวมอยู่ในตารางเวลาของรายงานหลัก

[เปิดตารางเวลารวมและรายละเอียดการจับเวลา](../Human_Parsing_Benchmark/reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md#เวลาต่อภาพและเวลารวม)

<!-- SPEED_OVERVIEW_END -->

## ประวัติรายงานและสถานะก่อนหน้า (historical views)

> **เปิด GT viewer ฉบับใหม่:** ดาวน์โหลด `outputs/master-gt-repair-20261107T191020Z/review_offline.html` แล้วเปิดในChrome/Edge/Firefoxได้จากไฟล์เดียว มี90ภาพฝังไว้ ไม่ต้องใช้JavaScriptหรือพาธserver. ดูตัวอย่างตรงจาก `owner_repairs_before_after.jpg` ในโฟลเดอร์เดียวกัน. [ตำแหน่งและการตรวจ](STATUS.md). GT/masks/ผลคะแนนเดิมไม่เปลี่ยน.

> **GT ฉบับแก้จาก Master พร้อมเปิดตรวจแล้ว:** แก้ownerสองจุดและส่งออก90ภาพในโฟลเดอร์ส่วนตัว `outputs/master-gt-repair-20261107T191020Z/` เปิด `index.html` ดูก่อน–หลังได้. ยังรอตรวจcoverage/ขอบเขต ไม่ใช่GTที่พร้อมให้คะแนนใหม่ และผลที่รายงานด้านล่างยังเป็นผลGTrevisionเดิม. [สถานะและตำแหน่งไฟล์](STATUS.md) / [รายงานการแก้](../Human_Parsing_Benchmark/reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md).

# CCTV Human Parsing Benchmark

**ตัวหลักที่แนะนำ: Sapiens2 segmentation 1B** สำหรับคุณภาพรวมสี่เป้าหมายบน CCTV reference-domain ที่ประเมินแล้ว. คะแนน Macro4 **65.430%** สูงสุดจาก9ระบบ; QANet **64.533%** ตามหลัง0.898pp และเป็นทางเลือกเมื่อเน้น Face-domain/Upper.

| ตัวเลือก | Macro4 | ส่วนที่ได้คะแนนสูงสุด |
|---|---:|---|
| **Sapiens2 1B — ตัวหลักตามเกณฑ์รวม** | **65.430%** | Hair / Lower |
| QANet — ทางเลือกด้าน Face/Upper | 64.533% | Face-domain / Upper |

[รายละเอียดการเลือก รุ่น และ configuration ที่รันจริง](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md) · [ตารางเก้าระบบ](metrics/CONTROLLED_ROI_FOUR_TARGET_RESULTS.csv) · [Recommendation JSON](reports/MODEL_RECOMMENDATION.json) · [STATUS](STATUS.md)

การคำนวณจบ9/9 จาก90ภาพ/130ROIsต่อระบบ. ใช้ Hair61 / Face21 / Upper112 / Lower96 parts โดย Face14/35รายการกันออกเหมือนกันทุกโมเดล; Neck deliveryมี3รายการ. GTเป็นagent-assisted reference ไม่ใช่expertgold และส่วนต่างยังไม่ผ่านstatistical-significance study. คำแนะนำนี้สำหรับ checkpoint+controlled YOLO person-ROI configuration ไม่ใช่ production acceptance. ไม่มีการรันใหม่หรือเปลี่ยน config จากงานสรุปนี้.


[วิธีอ่านคะแนน CCTV แบบเข้าใจง่าย](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#วิธีอ่านคะแนนชุด-cctv-นี้) อธิบายคลาส สูตร ตัวหาร ตัวอย่าง Mean-part เทียบ pooled และวิธีอ่านเวลาต่อ ROI/ต่อภาพ พร้อมขอบเขตของแต่ละตาราง

## Confusion matrix และส่วนที่พลาด

[รายงานเดิม: ตารางรายคลาส พร้อมสูตรและแหล่งอ้างอิงของ metrics](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#confusion-matrix-และการเก็บส่วนที่ต้องการครบแค่ไหน) · [ภาพ matrix ทั้งเก้าระบบ](reports/figures/CONTROLLED_ROI_TARGET_CONFUSION.png) · [CSV counts/ตัวหาร](metrics/CONTROLLED_ROI_TARGET_CONFUSION.csv)

[F1 / Precision / Recall แยก Hair / Face-domain / Upper / Lower](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#f1-score-แยก-4-คลาสต่อโมเดล): โมเดลละ 4 F1 scores รวม 36 ค่า จาก pooled pixel counts เดิม พร้อมสูตรและความต่างจาก mean-part scores; F1 เท่ากับ pooled Dice ใน domain เดียวกัน

Hair / Face-domain / Upper / Lower ใช้ binary 2×2 ต่อคลาส รวม 36 matrices ในภาพเดียว แสดง TP/FP/FN/TN, Recall, พิกเซลที่พลาด และ Precision พร้อมจำนวนส่วนที่ไม่ทับ GT เลย ไม่เปลี่ยนคะแนนหลัก Mean-part IoU / Macro4 เดิม ตัวเลขเป็น selected-person part tasks บน 90 ภาพ ไม่ใช่ full-scene accuracy; Face มี 21 eligible parts และ TN เป็นส่วนเติมเต็มของ task domain

[สถิติความเร็วจาก log เดิม](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#ความเร็วและเวลาประมวลผลจาก-log-เดิม): Mean/Median/P95 ต่อ ROI และ worker elapsed ทั้ง 9 โมเดล แยก monotonic adapter timer กับ continuation UTC intervals พร้อมจำนวนตัวอย่างและขอบเขต; เป็น shared-GPU diagnostics ยังไม่ใช่ end-to-end FPS ranking

[สรุปเวลาที่บันทึกได้และเวลารวมของ worker](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#d-ตารางสรุปรวม--บวกค่าที่มี-log-แล้ว): แยก A+B จาก C เพื่อไม่ให้นับเวลาซ้ำ พร้อมสูตร ตัวหาร และสัดส่วน ROI ที่มีข้อมูลเวลา

[เวลาต่อภาพและเวลารวมทั้งชุด 90 ภาพ](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#e-เวลาต่อหนึ่งภาพ-และรวมทั้ง-90-ภาพ): รวมเวลา ROI ของภาพนั้นจาก log จริง ไฟล์ส่วนตัว `outputs/per-image-timing-report-20261102-final/PER_IMAGE_TIMING.csv` มี 9×90 รายการพร้อมชื่อภาพ หกโมเดลมีข้อมูลเวลาครบ 90 ภาพ ส่วน Sapiens แต่ละขนาดครบ 84/90 ภาพ จึงคงเวลารวมทั้งชุดเป็น null ไม่ใช้คำนวณ FPS ของ pipeline ทั้งหมด

## ภาพรายละเอียดรายโมเดล (private)

เปิด `outputs/model-detail-gallery-20261102/index.html` เพื่อเลือกดูทั้ง9โมเดลจาก6ภาพเดิม/15ROIs: RGBเทียบGTและprediction, ซูม,ปรับopacity และสลับnativeclasses/สี่เป้าหมายร่วม. ดาวน์โหลด `outputs/model-detail-gallery-20261102.zip` แล้วแตกเปิดindex.htmlได้โดยไม่ตั้งserver. Images/GT/masks/ZIPไม่ขึ้นpublicGit; [สรุปartifactsและการตรวจ](reports/MODEL_IMAGE_GALLERY.json) มีcounts/hashesและข้อจำกัด. ใช้ผลเดิม ไม่มีinference/rescore.

## Previous proposal and historical results

**สถานะในข้อเสนอเดิม: GT_OWNER_REVIEW_REQUIRED / PROPOSED_NOT_FROZEN.** อ่าน [ข้อเสนอ controlled person-ROI และ Face/Neck](CONTROLLED_ROI_PROTOCOL_TH.md) → [STATUS](STATUS.md) → [หลักฐาน design review](reports/CONTROLLED_ROI_DESIGN_REVIEW.json). ผู้ใช้มอบหมายให้กำหนดวิธีประเมินที่เหมาะสม; ยังไม่มี inference รอบใหม่หรือการอนุมัติ batch เพิ่มจากการออกแบบนี้.

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
