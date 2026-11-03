# คำอธิบายคะแนนและเวลา CCTV ฉบับอ่านง่าย — 2026-11-03T16:03:18+07:00 (Asia/Bangkok)

**REPORT_EXPLANATION_REVIEW_COMPLETE / DOCUMENTATION_ONLY** — ปรับ [รายงานผลเดิม](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#วิธีอ่านคะแนนชุด-cctv-นี้) และข้อความในตัวสร้างรายงานทั้งสองไฟล์ เพิ่มคำศัพท์ mapping สี่คลาส สูตร/ตัวอย่าง IoU/P/R/F1, Mean-part/Macro4 เทียบ pooled, partial-GT/Face-domain และวิธีอ่านเวลา A/B/C/D/E เปลี่ยนตัวแปรโค้ดที่อ่านยากเป็นคำอธิบายภาษาไทย มีจุดเริ่ม/จบ หน่วย s/ms ต่อ ROI/ภาพ ตัวอย่าง Mean/Median/P95 และบัญชีเวลา ไม่เพิ่ม Q_C4_GT/C3 ให้ CCTV หรือเปลี่ยนเกณฑ์เลือก

ตรวจ113แถวผลตัวเลขและ9ไฟล์ผล/protocol/ภาพmatrixคงเดิม; AST ส่วนคำนวณและควบคุมของสองตัวสร้างรายงานเหมือนเดิมทุกส่วนเมื่อไม่นับข้อความ; สร้างส่วนรายงานจาก aggregate เดิมได้ตรงกัน ตรวจ Markdown22ตารางและ Chromium พร้อมฟอนต์ไทย: ตารางนิยามเวลา4คอลัมน์/8แถว ตารางต่อภาพ6คอลัมน์/9โมเดล และลิงก์ D เดิมใช้ได้ ไม่มี inference/rescore หรืออ่าน raw images/masks/logs ใหม่

ผลคุณภาพ CCTV ยังเป็น9/9บน90ภาพ/130ROIsต่อระบบและ290ส่วนที่เลือกประเมิน; Sapiens แต่ละขนาดมีเวลาครบ84/90ภาพตามเดิม ค่า null และข้อจำกัดไม่เปลี่ยน รอบ CIHP controlled ROI เป็นงานแยก [ติดตาม CIHP](../Human_Parsing_Benchmark/STATUS.md). Hashes เก่าเป็น snapshotsตามเวลา เก็บไว้ครบและบันทึก hashรายงานปัจจุบันใน STUDY_STATE.report_explanation_review ขั้นถัดไป: ใช้รายงานนี้อธิบายผลพร้อมขอบเขต; ไม่มีงานทดลองเพิ่มจากการแก้เอกสารนี้

## บันทึกก่อนการปรับคำอธิบายครั้งนี้

# ตรวจความเทียบกันได้กับ CIHP — 2026-11-02T18:03:20.041685+07:00

**COMPARABILITY_AUDIT_COMPLETE** — [รายงาน](../Human_Parsing_Benchmark/reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md). ตรวจ aggregate bindings/arithmetic และคำนวณ pooled sensitivity ของ 36 target records แล้ว คงผลหลัก/GT/predictionsเดิม. CIHP กับ CCTV ล่าสุดต่าง input route, Face domain, matching และ aggregation; ไม่ใช่ direct cross-dataset model ranking. ไม่มี inference ใหม่. งานต่อคือ controlled CIHP ROI bindings/readiness และ independent GT review ตามข้อจำกัดที่ระบุ

# ปรับภาษารายงาน — 2026-11-02T16:54:52.799096+07:00 (Asia/Bangkok)

**THAI_WORDING_REVIEWED** — เกลาภาษาใน [รายงานผลเดิม](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md) และตัวสร้างรายงานทั้งสองไฟล์ ให้ใช้คำไทยและหน่วยสม่ำเสมอ เปลี่ยน “ภาพที่เวลาครบ” เป็น “ภาพที่มีข้อมูลเวลาครบ” และ “ประชากร90” เป็น “ทั้งชุด 90 ภาพ” อธิบาย GT/ROI/คลาสเดิมของโมเดล การจับคู่ และความต่างระหว่างเวลาที่บันทึกได้กับเวลารวมของชุดภาพ พร้อมคงความหมาย null และข้อจำกัดเดิม

ตรวจแถวข้อมูลผลประเมิน 113 แถวตรงเดิมทุกช่อง และไฟล์ข้อมูล/สถิติ/ภาพรวม/protocol/recommendation 9 ไฟล์มี hash เดิม ฟังก์ชันคำนวณไม่เปลี่ยน การสร้างข้อความจากผลรวมเดิมตรงกับรายงาน ตรวจ GitHub Markdown ครบ 21 ตารางและเปิดดูตาราง E ใน Chromium แล้ว ลิงก์ส่วน D เดิมยังใช้ได้

ไม่รัน tests หรือ inference ใหม่สำหรับงานแก้ถ้อยคำนี้ ไม่มีการอ่าน masks หรือคำนวณคะแนน/เวลาใหม่ ขั้นถัดไป: อ่านรายงานฉบับล่าสุดจาก working branch ส่วนสถานะและ hashes เก่าเป็น snapshot ตาม commit ที่ระบุ

## ประวัติสถานะก่อนหน้า

# Current report formatting update — 2026-11-02T16:35:57.399792+07:00 (Asia/Bangkok)

**TABLE_E_RENDERING_FIXED**. แก้เฉพาะ Markdown ของตารางE:หัวตาราง6คอลัมน์แต่separator7 ทำให้แสดงเป็นplain text แก้เป็น6ทั้งรายงานเดิมและreport_runtime.pyแล้ว GitHubGFMrenderมี9model rows×6columns,ChromiumDOM54cellsและpreviewภาษาไทยตรวจผ่าน

ตัวเลข/ตัวหาร/CSVรายภาพ/PRF/timingเดิมไม่เปลี่ยน ไม่อ่านlogsซ้ำหรือทำinference/rescore และไม่เพิ่มtest suiteสำหรับformattingfixนี้ Reporthashปัจจุบันอยู่ในSTUDY_STATE.json→report_formatting;เดิมเป็นhashsnapshotตามcommitที่ระบุ Next:เปิดรายงานrevisionล่าสุด ไม่ใช้snapshotcommitเก่าที่immutable

## Earlier current-state snapshots — historical records below

# Current per-image timing update — 2026-11-02T15:57:24.562485+07:00 (Asia/Bangkok)

**PER_IMAGE_PARSING_WORK_REPORT_COMPLETE_WITH_TIMING_GAPS — 9 models×90 images.** เพิ่ม [ตารางE:ต่อภาพและรวม90ภาพ](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#e-เวลาต่อหนึ่งภาพ-และรวมทั้ง-90-ภาพ) จากการบวกROIlogsของแต่ละภาพจริง ไม่ใช้meanROI×จำนวนคน Private `outputs/per-image-timing-report-20261102-final/PER_IMAGE_TIMING.csv` มี810model-image rows พร้อมชื่อภาพ/status/ROIcounts/เวลารวม ข้อมูลรายภาพไม่ขึ้นpublicGit

หกโมเดลCIHPมีเวลาครบ90/90 แต่ละSapiensครบ84/90 เพราะ6ภาพ/15ROIsreuseไม่มีadaptertimerของรอบนี้ ค่าmean/totalประชากร90ของSapiensเป็นnull; meanของ84ภาพแสดงแยกชัด มี8ภาพไม่มีYOLO ROIต่อโมเดลจึงไม่มีparsercallและparsing-work=0จริง ไม่ได้แปลว่าYOLO/end-to-endtime=0 Predictions/F1/qualityยังครบและไม่เปลี่ยน

รวม timingครบ792/810model-image records จาก90ภาพเดียวกัน คงoldROI/log/worker totals,16targetedCPUcasesPASS ไม่มีinference/rescore/GTหรือnativeconfigเปลี่ยน Next:เปิดCSVprivateเพื่อดูรายภาพ และอ่านสรุปpublicที่ระบุขอบเขต ไม่มีคิวGPUเพิ่มเติม

## Earlier current-state snapshots — historical records below

# Current per-class metrics update — 2026-11-02T15:28:03.173159+07:00 (Asia/Bangkok)

**PER_CLASS_PIXEL_PRF_COMPLETE — 9 models ×4 targets =36 F1 scores.** เพิ่ม [ตาราง F1 รายโมเดล/สี่คลาส](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#f1-score-แยก-4-คลาสต่อโมเดล) ในรายงานเดิม และ F1 ในตาราง Precision/Recall ของทุกคลาส [CSV เดิม](metrics/CONTROLLED_ROI_TARGET_CONFUSION.csv) เพิ่ม pooled_F1 เพียงคอลัมน์เดียว; original columns/values เดิมครบ

เป็น pooled binary pixel F1 =2TP/(2TP+FP+FN), เท่ากับ pooled Dice บน counts/domain เดียวกัน ไม่ใช่ person-detection F1 หรือ mean-part Dice ใช้ Hair61/Face-domain21/Upper112/Lower96 ตามเดิม ไม่มี mapping/GT/ตัวหารใหม่ และไม่เปลี่ยน mean-part IoU/Macro4 หรือตารางเวลา

ตรวจ 36 pairs กับ canonical target counts/Dice และ CPU reporting10/10PASS ไม่มี inference, mask/GT reads, rescore หรือ figure regeneration Next: ใช้ตารางรายคลาสพร้อมสูตร/aggregation; ไม่มี benchmark เพิ่มหรือคิว GPU

## Earlier current-state snapshots — historical records below

# Current timing accounting update — 2026-11-02T15:14:46.443883+07:00 (Asia/Bangkok)

**TIMING_ACCOUNTING_SUMMARY_COMPLETE — 9 models.** เพิ่ม [ตาราง D และ metric definitions ในรายงานเดิม](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#d-ตารางสรุปรวม--บวกค่าที่มี-log-แล้ว): บวก A+B เป็นบัญชีช่วงเวลาที่มี log และแยก C เป็นผลรวม worker เพื่อไม่ให้นับซ้ำ ROI timing coverage 1125/1170; อีก45 reuse ไม่มี timer รอบนี้ ไม่เติมเวลาศูนย์

เวลารายคลาสไม่มี เพราะ forward คืน native classes ร่วมกัน; quality IoU/Recall/Precision/Dice ราย Hair/Face/Upper/Lower มีอยู่เดิม ยอดรวม log1586.100s และ worker2365.697s เป็นบัญชีเก้าระบบ ไม่ใช่ latency ต่อภาพหรือ pipeline YOLO→parsing→สี→DB และยังไม่ใช้จัดอันดับความเร็ว

Original A/B/C statistics และ quality/canonical results คงเดิม CPU reporting checks 11/11 ผ่าน; ไม่มี inference/rescore/แก้ frozen configs Next: อ่านตารางรวมพร้อมขอบเขตและตัวหาร ไม่มีคิวทดลองเพิ่ม

## Earlier current-state snapshots — historical records below

# Current timing update — 2026-11-02T14:57:13.879230+07:00 (Asia/Bangkok)

**HISTORICAL_TIMING_DIAGNOSTICS_COMPLETE — 9 models.** เพิ่ม [สถิติเวลาจาก log เดิม](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#ความเร็วและเวลาประมวลผลจาก-log-เดิม) ในรายงานผลเดิม: monotonic adapter timers 791 ROI และ continuation UTC event intervals 334 ROI แยกตาราง พร้อม Mean/Median/P95 และ worker elapsed; อีก 45 ROI reuse ไม่มี timer ของรอบนี้ แยก TRAIN warmup 12 calls และ failed forward ที่ไม่มี end 1 call ออก ไม่เติมเวลาเป็นศูนย์

Historical Tesla T4 / SHARED_GPU_QUALITY_ONLY; ไม่ใช่ clean parser-only/end-to-end speed ranking เวลาราย ROI ยังไม่รวม YOLO, final ownership/packet I/O หรือ GT scoring; CPI มี native file I/O และ internal detector อยู่ใน adapter ตาม source ขอบเขตต่างกันราย configuration ไม่แปลงเป็น FPS ทั้งระบบ

ตรวจ log/accepted membership/source timer bindings และ CPU reporting checks 8/8 ผ่าน โดยไม่มี inference หรือเปลี่ยน quality/GT/mapping/native results [ค่าก่อนปัดเศษและ provenance](STUDY_STATE.json) → runtime_reporting Next: ใช้รายงานคุณภาพและ timing diagnostics ตามขอบเขตที่ระบุ ไม่มีคิวรันทดลองใหม่

## Earlier current-state snapshots — historical records below

# Current reporting update — 2026-11-02T13:50:26.324719+07:00 (Asia/Bangkok)

**TARGET_CONFUSION_REPORTING_COMPLETE — 9/9 models, 4 targets.** เพิ่ม diagnostics ใน [รายงานสี่เป้าหมายเดิม](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#confusion-matrix-และการเก็บส่วนที่ต้องการครบแค่ไหน): [ภาพเดียวรวม 36 binary matrices](reports/figures/CONTROLLED_ROI_TARGET_CONFUSION.png) และ [CSV 36 แถว](metrics/CONTROLLED_ROI_TARGET_CONFUSION.csv) มี Recall/พลาด/Precision และส่วนที่ไม่ทับ GT พร้อมสูตร ตัวหาร และที่มา

ตรวจ accepted score JSON 981 records / 2,610 person-part tasks จาก 9 ระบบ; TP/FP/FN/support/IoU ตรง canonical results, GT domains เท่ากันข้ามโมเดล และ protected artifacts 28 ไฟล์คงเดิม CPU reporting checks 8/8 ผ่าน ไม่มี inference, mask rescore, GT/mapping หรือ native benchmark เปลี่ยนแปลง

ยังเป็น selected-part reference evaluation: Hair61 / Face21 / Upper112 / Lower96 ต่อโมเดล TN เป็น task-domain complement ไม่ใช่หลักฐาน full-scene accuracy คะแนนหลักและคำแนะนำ Sapiens2 1B / ทางเลือก QANet คงเดิม Next action: อ่านตาราง Recall คู่ Precision/IoU และเปิดภาพ matrix จากรายงาน ไม่มี experiment หรือ worker เปิดต่ออัตโนมัติ

## Earlier current-state snapshots — historical records below

# CCTV parsing — current status

Updated 2026-11-01T23:26:54.611649+07:00 (Asia/Bangkok). **FOUR_TARGET_EVALUATION_COMPLETE_ON_REVIEWED_GT — 9/9**.

- [รายงานจบรอบสี่targets](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md) / [CSVหลัก](metrics/CONTROLLED_ROI_FOUR_TARGET_RESULTS.csv) / [canonicalindex](reports/CONTROLLED_ROI_FOUR_TARGET_INDEX.json).
- Savedpredictions90images/130ROIsต่อcheckpointครบอยู่เดิม; CPUFace21itemsครบทุกระบบแล้ว รวมHair61/Upper112/Lower96จากacceptedstatisticsเดิม. Macro4พร้อมทั้ง9 ไม่มีinferenceใหม่.
- ObservedMacro4leader:Sapiens2 1B65.430%;QANet64.533%. Face-domainและUpperสูงสุดQANet;Hair/LowerสูงสุดSapiens2 1B. ไม่ใช่statisticalsignificance/deploymentacceptance.
- FaceGTreview35recordsปิดด้วย21eligible/14ineligibleที่ใช้ร่วมทุกโมเดล. UnknownNeck18มีGT-onlyuncertainty ไม่สมมติabsent; delivery/knownNeckviewมี3items. GTไม่ใช่independentexpertgold. [Coverage](reports/FACE_NECK_GT_SUMMARY.json).
- [CPUและactual-packetacceptance](reports/FACE_NECK_ACCEPTANCE.json). Privatefixed6/ninemodelgallery:`outputs/face-neck-comparison-gallery-20261101/index.html`. ไม่มีCCTVassetsขึ้นpublicGit.
- Next:พิจารณารายงาน/ข้อเสนอใช้Sapiens2 1BหรือQANetตามrequirements. ไม่มีFace-scorejobหรือGPUqueueค้าง; independentGT/deploymentvalidationเป็นงานเพิ่มหากต้องการคำอ้างที่เข้มกว่า ไม่เริ่มอัตโนมัติ.

## Recommendation update — 2026-11-02T00:48:08.405168+07:00

[MODEL_RECOMMENDATION](reports/MODEL_RECOMMENDATION.json): แนะนำ **Sapiens2_1b + CONTROLLED_YOLO_PERSON_ROI** เป็นตัวหลักด้านคุณภาพรวม Macro4 65.430%; QANet64.533%เป็นทางเลือกด้านFace/Upper. เหตุผล รุ่น/parameter/checkpoint/preprocessing และข้อจำกัดอยู่ใน [รายงานหลัก](reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md). สถานะคำแนะนำ `RECOMMENDED_FROM_COMPLETED_CCTV_REFERENCE_BENCHMARK`; deployment/inferenceใหม่ยังไม่ได้อนุมัติจากงานสรุปนี้. Numeric results/protocol/GTเดิมไม่เปลี่ยน.

## Image detail delivery — 2026-11-02T01:21:23.575402+07:00

Privateviewerพร้อม: `outputs/model-detail-gallery-20261102/index.html`, ZIPชื่อเดียวกัน,9โมเดล×15frozenROIsจาก6ภาพเดิม. [Artifactsummary](reports/MODEL_IMAGE_GALLERY.json). Owned/rawและcommon/nativepaletteแยกชัด; source masks/metrics/GT/protocolไม่เปลี่ยน. Modelcalls0; browserinteractionยังไม่ได้ทดสอบบนเครื่องนี้, ตรวจJSsyntax/assets/PNGroundtrip/geometry/ZIPและภาพcontactจริงแล้ว.

## Earlier status — historical snapshots below

# CCTV parsing — current status

Updated 2026-11-01T21:34:07.412255+07:00 (Asia/Bangkok). **NON_FACE_DIAGNOSTICS_COMPLETE_9_OF_9_FACE_GT_PENDING**.

- Predictions ครบ9/9 checkpoints ×90images/130ROIs; controllers/workersหยุดแล้ว. [Prediction collection](reports/CONTROLLED_ROI_RUN_TH.md).
- [รายงานปัจจุบัน: GT review และผลที่วัดได้](reports/CONTROLLED_ROI_GT_AND_PART_RESULTS_TH.md): CPU Hair/Upper/Lower ครบ9/9 จาก saved masks; GT-only subset269parts, matchingร่วมทุกระบบ. **Face-domain/macro4ยังnull**.
- Face35recordsยังไม่มี reviewed Neck annotation; source maskไม่ถูกแก้. RGB/GT-only screen127persons/32pagesและ35closeupsเสร็จแล้ว; ownercorrections2จุดอยู่ในderivedcopy. Reviewนี้ไม่ใช่independentexpertcertification.
- [Derived result index](reports/CONTROLLED_ROI_DIAGNOSTIC_INDEX.json) / [GT screen](reports/CONTROLLED_GT_SCREEN_SUMMARY.json) / [CPU acceptance](reports/CONTROLLED_ROI_SCORER_ACCEPTANCE.json). Non-Face outputsไม่ใช่final four-target selection.
- Next: Face/Neck annotation/adjudicationจากprivate`outputs/gt-neck-review-20261101-inspection/index.html` →newGTbinding→targetedFaceintegration→CPUscoreจากpredictionsเดิม. ไม่มีinferenceใหม่ในworkunitนี้ และไม่ต้องGPUrerunเพื่อแก้GT.

## Earlier status — historical snapshots below

# CCTV parsing — current status

Updated 2026-11-01T20:38:12.849866+07:00 (Asia/Bangkok). **PREDICTIONS_COMPLETE_9_OF_9_SCORING_PENDING_GT**.

- ทั้ง9checkpointsมีacceptedassembledpredictionsครบตัวละ90images/130ROIs; finalmissing/duplicate/failed/invalid0 ตามcanonicalcompletion.
- จบ 2026-11-01T19:37:40.125828+07:00; controllers/workersหยุดแล้ว,GPUว่างตอนตรวจ. Parentpartialfailuresเก็บครบและไม่ใช้เป็นfinalview.
- [รายงานปิดpredictioncollection](reports/CONTROLLED_ROI_RUN_TH.md) / [completionevidence](reports/CONTROLLED_ROI_COMPLETION.json). Parent`cctv-controlled-roi-20261101T115653Z`;continuation`cctv-roi-continuation-20261101T121138Z`.
- **คะแนนใหม่ยังnull**:GTNeck/remainingowner/contourQAและfinalscorerbindingยังไม่ครบ. Inferencecompleteไม่เท่ากับevaluationcompleteหรือผ่านdeployment.
- Next:ปิดGT/scorerแล้วCPUscoreจากsavedmasks ไม่ต้องinferenceใหม่เพียงเพื่อแก้GT. ไม่มีคิวGPUรอทำต่ออัตโนมัติ.

Read-onlyviewerยังใช้ตรวจterminalstateได้:

```bash
python3 CCTV_Human_Parsing_Benchmark/scripts/controlled_roi_progress.py
```

## Earlier launch/design history — snapshots below

Updated 2026-11-01T19:01:06.078883+07:00 (Asia/Bangkok). **RUNNING_PREDICTION_COLLECTION / SCORING_PENDING_GT**.

Userสั่งรันpersonROIใหม่เก้าระบบ. [รายงานรอบใหม่](reports/CONTROLLED_ROI_RUN_TH.md) → [ขอบเขตที่ตรึง](configs/CONTROLLED_ROI_SCOPE.json). Run `cctv-controlled-roi-20261101T115653Z`,90images/130ROIsต่อmodel,45Sapiensreused/1125pendingROIAPIcalls+9TRAINwarmups. CPU12casesPASS; QANetGPUgate+90frames/130ROIsครบแล้ว. ระบบอื่นใช้per-modelGPUgatesก่อนดำเนินต่อ.

Predictioncollectionแยกจากscoring:GTowner2กรณีแก้ในderivedcopyแล้ว,sourcecontoursไม่เปลี่ยน;Neck/remainingQAยังไม่ครบ. **Headlineใหม่nullจนGT/scorerพร้อม**. ไม่ใช้GTสร้างpredictionและไม่ใช้predictionวาดGT.

Live:

```bash
python3 CCTV_Human_Parsing_Benchmark/scripts/controlled_roi_progress.py --watch
```

Private`outputs/cctv-controlled-roi-20261101T115653Z/`เก็บcontroller/workerSTATE/logs/atomicpackets. คิวหยุดหลัง9checkpoints;ไม่มีmodelretry/fallback/YOLOreinference/CIHP5000/training/colorเพิ่ม.

Launch PID1353092/SID1353092,PPID1;sourcecommit`12ef1185e7def76d2a1091bf2dcc5d1e972fb5af`. [Launch snapshot](reports/CONTROLLED_ROI_LAUNCH.json). ข้อมูลนี้เป็นsnapshot;viewerอ่านliveprivateJSONและ`BATCH_COMPLETION.json`บอกคิวจบ.

## Controlled continuation

Segment`cctv-roi-continuation-20261101T121138Z` (QUEUED_UNTIL_PARENT_TERMINAL, PID1357726) เตรียมแก้เฉพาะRPRempty-outputhandlingและCPIdevicefree-versus-ownpoolaccounting. ReuseRP1/R5028/Conv27;pending129/102/103ROIs. [รายละเอียด/ขอบเขต](reports/CONTROLLED_ROI_CONTINUATION.json). ไม่แก้parentfrozen source/config ไม่รันcheckpointที่ครบซ้ำ. Extraengineeringbudgetสูงสุด4APIcallsประกาศในรายงาน;genuineOOM/modelretries0;scoregateเดิม. Viewerแสดงcontinuationและassembledindexด้วย.

## Earlier design and completed evidence — historical snapshots

Updated 2026-11-01T18:27:25.122054+07:00 (Asia/Bangkok).

**GT_OWNER_REVIEW_REQUIRED / GT_REVISION_AND_ROI_READINESS_PENDING**. วิธีประเมินรอบใหม่จัดทำครบเป็น **PROPOSED_NOT_FROZEN**: [controlled ROI / Face-Neck protocol](CONTROLLED_ROI_PROTOCOL_TH.md). ยังไม่ใช่ launch approval หรือ execution acceptance.

- รอบ CCTV90 เก่า: QANet รับ YOLO ROI; Sapiens รับ full frame ก่อน YOLO ownership; อีกห้าระบบรับ full frame แล้ว associate. ผลเก็บครบ9/9 แต่พัก final selection เพราะ source owner conflicts และข้อจำกัด taxonomy/input.
- ข้อเสนอใหม่: same predicted crop/context/ownership สำหรับ9checkpoints; GT แยก Face/Neck; headline Hair/Face-on-neck-excluded-domain/Upper/Lower เท่ากัน25%; Face+Neck delivery แยกพร้อมข้อจำกัด strict Face-only.
- Cache metadata:90images/130opportunities/8zero-detection images. Proposed1,170ROIjobs; potential Sapiens reuse45 → new1,125เมื่อ bindings ผ่าน. ยังไม่มี inference/scoring jobs ของรอบใหม่นี้เปิดทำงาน.
- Next: derived GT owner/contour/Neck revision และ CPU acceptance; จากนั้นเสนอ adapter/resource-readiness scope และ batch approval. ไม่มี model calls, full rescore หรือ active code/config/GT changes ใน work unit ออกแบบนี้.

[หลักฐานการตรวจเฉพาะจุด](reports/CONTROLLED_ROI_DESIGN_REVIEW.json) / [ผล fresh6ภาพเดิม](reports/SAPIENS2_MEASUREMENT_REVIEW_TH.md) / [WORK_LOG](WORK_LOG.md). Authoritative working copy: `CCTV_Human_Parsing_Benchmark/`; public copy แยกที่ `Human_Parsing_Study_Public/`.

## Historical milestones — snapshots below, not current launch authorization

> **อัปเดต 2026-11-01T10:16:54.165252+07:00: GT_OWNER_REVIEW_REQUIRED.** พบsourceownerlabelsรวมส่วนจากคนละคนอย่างน้อย2ภาพ พักการใช้ตาราง90ภาพเพื่อตัดสินเลือกโมเดล;ค่าผลเดิมเก็บเป็นhistoricalagreementกับGTที่ให้มา. [ผลตรวจและfreshSapiensทั้ง3ขนาด](reports/SAPIENS2_MEASUREMENT_REVIEW_TH.md).

Updated 2026-11-01T10:16:54.165252+07:00 (Asia/Bangkok). **SELECTED_PART_EVALUATION_COMPLETE —9/9×90IDs**, no active model worker or CPU scorer.

[Final Thai report](reports/CCTV_SELECTED_PART_RESULTS_TH.md) → [Protocol](SELECTED_PART_PROTOCOL.md) → [Evidence](reports/SELECTED_PART_EVALUATION_EVIDENCE.json). Observed selected-task leader: **QANet**, macro mean selected-part IoU4 61.773%, Dice4 69.203%. Primary315parts; all324 sensitivity reported. GT-only agent screening is not independent expert certification; no full-scene/deployment claim.

Original partial/native packets/GT/config/recall results unchanged; old known-domain IoU report remains historical diagnostic. New evaluation uses whole selected-person masks with spill FP and retained misses. Model inference calls0; no retries/training/environment changes.

Next: review this final report and QANet configuration proposal. Full-scene metrics/production acceptance require separate annotation scope/QA and independent confirmation; no new experiment scheduled automatically. Private review/gallery/records stay in outputs; public Git has aggregates only.

## Sapiens input audit

[Preprocessing audit](reports/SAPIENS2_PREPROCESSING_AUDIT_TH.md):12CPUinputtensorcases across3segconfigs exactlymatchofficialdemo/directnormalization. NoRGB/BGR/doublenormalizationbugfoundonthesecases. Full-frame1920×1080→768×1024stretchstronglychangespersonaspect/scale;qualityeffectunproven. No learnedforward/checkpointload/GPUworker or scorechanges. Nextboundedreferenceforwardwouldrequireanewinferencescope; existing9/9resultsremainconfiguration-specific.

## Current user-authorized input experiment

INPUT_DIAGNOSTIC_PREPARED: Sapiens0.4B only,6fixed images/3input routes/29model calls maximum including1TRAINwarmup and1official-forwardreference. [Frozen diagnostic specification](configs/SAPIENS_INPUT_DIAGNOSTIC.json). User has now authorized this test; prior no-forward sentence above describes the previous audit. Next detachedworker; no full benchmark, other sizes or changes to old scores.

Input diagnostic revision2: parent raw-logit allclose gate stopped after3calls; exact inputs/original-grid masks matched official and saved native output. Failure retained. Independent variant phase uses6accepted baselines,6letterbox+15ROI+1processwarmup; combined25calls within original29bound. Raw-logit equivalence remains unverified; next single child worker, no full benchmark.

## Latest outcome — input diagnostic closed 2026-11-01T09:34:27.498729+07:00

**INPUT_DIAGNOSTIC_COMPLETE_WITH_RAW_LOGIT_CONTROL_LIMITATION**. [Main Thai diagnostic report](reports/SAPIENS2_INPUT_DIAGNOSTIC_TH.md). Sapiens0.4B,6images/31parts: FFstretch37.447%,FFletterbox29.913%,ROIletterbox59.575%meanpartIoU4. Combined25modelcalls,allworkers exited; nofull90/othermodelstart. ParentrawlogitallcloseFAILretained;originalgridmaskcontrolmatchedofficial/savedoutput. Old9-systemresultsunchanged. NextreviewandseparateROI90imageevaluationdecision.

## Current scope — Sapiens measurement review

SAVED_SCORE_RECONCILIATION_PASS / FRESH_ROI_REVIEW_PREPARED. [Specification](configs/SAPIENS_MEASUREMENT_REVIEW.json). User authorizes fresh inference to investigate;3sizes/6fixedimages,17calls permodel/51totalcap, sequentialFP32 and same ROIroute/scorer. No full90/5000benchmark or othermodels. Private progress under CURRENT_SAPIENS_REVIEW pointer and permodelSTATE. Oldscores unchanged.

## Latest outcome — measurement review closed

**MEASUREMENT_RECONCILED_FRESH_ROI_COMPLETE_GT_OWNER_REVIEW_REQUIRED**. [Thai report](reports/SAPIENS2_MEASUREMENT_REVIEW_TH.md). Saved90×3independentcountsauditPASS;freshROI6×3complete,51calls,controllerstopped. Originalscoresunchanged;newresultsdiagnostic-only,not90imagebenchmark. NextreviewGT/aggregation/inputfindingsanddecidefull90ROIseparately.
