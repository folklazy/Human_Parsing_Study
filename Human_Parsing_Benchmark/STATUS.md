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
