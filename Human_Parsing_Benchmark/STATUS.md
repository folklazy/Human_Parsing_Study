# Controlled CIHP quality batch กำลังทำงาน — 2026-11-02T19:13:53.625503+07:00

**QUALITY_BATCH_RUNNING / QANET_TRAIN_GATE_PASS** — [รายงานรอบปัจจุบัน](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). Run `cihp-controlled-roi-20261102T120403Z` เปิดใน tmux แล้ว controller2144827 / QANetworker2144852. ตรวจเวลา19:13:14น.พบ521/5000ภาพ, failed0/invalid0, packetแรกผ่าน atomic/readback/nativeIDs/ownership/bindings และ source19รายการตรง. คิวโมเดลถัดไปอัตโนมัติหลัง closure/resource gates

ใช้ `.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/controlled_cihp.py progress` จากworkspace rootเพื่อดูจำนวนล่าสุด. snapshotในเอกสารมีเวลาอ้างอิง. Live/clean timingphaseยังpendingแยกจากquality. Next action:ปล่อยcontrollerเดิมเดินคิว ติดตามhealth/completenessและวิเคราะห์รวมหลังbatchterminal

> **Controlled CIHP implementation — 2026-11-02T19:05:31.621985+07:00** CPU acceptance13casesผ่านสองenvironments; frozenqualitymanifest5000frames/24,062ROIs×9พร้อม. GPU TRAINgateยังpendingก่อนVAL. [รายงานรอบใหม่](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). Live/clean speedphaseยังpendingแยกจากqualityqueue

> **Queue/timing requirements — 2026-11-02T18:51:46.168259+07:00** กำหนดsequentialautomaticqueue,model-boundaryreconciliation,health-onlymonitoringและวิเคราะห์หลังbatchterminalแล้ว. [PLAN](PLAN.md#คิวอัตโนมัติและการเก็บเวลาแยกขั้นสำหรับ-controlled-cihp) มีstage-leveltiming,cached/livepipelineboundaries,clean timing proposalและacceptance. Implementation/readinessของcontrolledCIHPยังpending

> **Comparability review — 2026-11-02T18:03:20.041685+07:00:** ตรวจ CIHP กับ CCTV90 และคำนวณ aggregation sensitivity แล้ว: input route, ownership, Face domain และหน่วยเฉลี่ยต่างกัน จึงไม่ใช่การวัดเงื่อนไขเดียวกันข้าม dataset. [รายงานตรวจละเอียด](reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md) · audit 9 systems / 36 targets PASS; ผลเดิมคงเดิม. Controlled CIHP ROI ยังไม่รันและยังไม่ผ่าน readiness.

> **New CCTV work is separate:** [CCTV_Human_Parsing_Benchmark](../CCTV_Human_Parsing_Benchmark/README.md) uses partial-annotation recall diagnostics on90images. CIHP results below remain frozen. No full-image CCTV IoU/instanceF1/overallwinner claim.

# Human Parsing Benchmark — current status

Updated: 2026-10-30T11:11:02.869193+07:00 (Asia/Bangkok)

**COMMON_C4P_COMPLETE_9_OF_9 / ANALYSIS_READY_FOR_REVIEW** — [รายงานผลหลักและ shortlist](reports/CIHP_COMMON_NINE_RESULTS_TH.md).

- Official CIHP Validation exact5,000 unique IDs ต่อระบบ common C4-P revision2 ครบ9/9 checkpoints.
- รอบนี้ CPI R50/ConvNeXt-B ใช้ saved artifacts เท่านั้น ครบตัวละ5,000; missing/duplicate/invalid/failed0. อีก7ระบบreuse accepted canonical common metrics ไม่มีrescoreทั้งชุด.
- Native20ยังครบ6/6และคงผลเดิม; common/global scoresไม่ปะปนกับnative20.
- M2FP_R101_CIHP สูงสุด global IoU ทั้งสี่ targets และ C4-P mean83.623%; QANetสูงสุด Q_C4_GT ทั้งmatching0.50/0.75แต่FPมากกว่า. ShortlistจากCIHP: M2FPหลัก, QANetสำหรับGT-personQ, CPIConvNeXt-Bเป็นtrade-offเพิ่มเติม ไม่ใช่deploymentacceptance.
- Faceใช้CIHP reference; SapiensFace_Neckเป็นproxy, Upper/Lower non-Dress, OTHER/VOIDคงrevision2 ไม่มีmapping/settingsเปลี่ยนจากคะแนน.

[Normalized result index](manifests/CIHP_COMMON_RESULT_INDEX.json) ประกาศcanonicalMETRICS.primaryและlegacycompletionnullเหตุผลโดยไม่แก้historicalcompletion. [Compatibility](runs/cpi-common-c4p-20261030/COMPATIBILITY.json), [parity review](runs/cpi-common-c4p-20261030/PARITY_REVIEW.json), [verification](runs/cpi-common-c4p-20261030/FINAL_VERIFICATION.json), [external artifact references](runs/cpi-common-c4p-20261030/ARTIFACT_MANIFEST.json).

CPIประวัติOOM/recovery/source-revisionmixคงครบ ไม่มีpopulationwidebitwiseequivalenceclaim. CPUscoringสองstreamจบแล้ว ไม่มีnewmodelinference/GPUdiagnostic/training/OOMrepair/color/CCTV ไม่มีcleanlatency/FPS/VRAMranking.

Next action: ส่งรายงานและCSVให้ผู้review แล้วผู้ใช้ตัดสินconfiguration/ขั้นตอนต่อไป ไม่มีautomaticexperimentเพิ่ม. [Previous closure handoff](reports/CIHP_EVALUATION_HANDOFF_TH.md) เป็นsnapshotก่อนCPIcommon.
