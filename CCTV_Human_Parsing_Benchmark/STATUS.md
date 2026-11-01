# CCTV parsing — current status

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

Segment`cctv-roi-continuation-20261101T121138Z`เตรียมแก้เฉพาะRPRempty-outputhandlingและCPIdevicefree-versus-ownpoolaccounting. ReuseRP1/R5028/Conv27;pending129/102/103ROIs. [รายละเอียด/ขอบเขต](reports/CONTROLLED_ROI_CONTINUATION.json). ไม่แก้parentfrozen source/config ไม่รันcheckpointที่ครบซ้ำ. Extraengineeringbudgetสูงสุด4APIcallsประกาศในรายงาน;genuineOOM/modelretries0;scoregateเดิม. Viewerแสดงcontinuationและassembledindexด้วย.

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
