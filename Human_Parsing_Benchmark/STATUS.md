# Human Parsing Benchmark — current status

Updated: 2026-10-30T10:44:14.373500+07:00 (Asia/Bangkok)

**EXECUTION_COMPLETE / HANDOFF_READY_WITH_LIMITATIONS** — [รายงานรวมสำหรับส่งตรวจ](reports/CIHP_EVALUATION_HANDOFF_TH.md).

- 9 unique checkpoints มี canonical observations ครบตัวละ5,000 official CIHP Validation IDs.
- Native20: QANet/M2FP/D2FP/RP-R-CNN/CPI R50/CPI ConvNeXt-B **6/6 COMPLETE**.
- Common C4-P revision2: QANet/M2FP/D2FP/RP-R-CNN + Sapiens2 0.4B/0.8B/1B **7/7 COMPLETE**.
- CPIสองตัวยังไม่ได้ทำcommon C4-P; ห้ามเทียบnative20คะแนนกับcommon4โดยตรงหรืออ้าง9ระบบมีcommonleaderboardแล้ว.
- R50ล่าสุด [completion](runs/r50-20261029T183615747685Z/COMPLETION.json): reuse912 +new4088=5000; missing/duplicate/failed/invalid0; ended2026-10-30T02:56:12+07:00. รอบ912/5000ก่อนหน้ายังคงhistoricalINCOMPLETE พร้อมOOMhistory.
- ไม่มีprojectinference/controllerPythonทำงานเมื่อเช็ค GPU `0, Tesla T4, 0 MiB, 14912 MiB, 0 %`. tmux sessionsที่เหลือไม่ใช่liveworker; ไม่มีkill/restart/newmodel.

Current native index: [CIHP_NATIVE_COHORT_INDEX](manifests/CIHP_NATIVE_COHORT_INDEX.json). [Verification scope](runs/closure-review-20261030/VERIFICATION.json) ระบุสิ่งที่ตรวจและหลักฐานเดิมที่reuse ไม่มีfullNPZrehash/fullrescore/testsใหม่.

Next action: ส่งรายงานรวม/CSVให้ผู้review แล้วตัดสินงานanalysisหรือCPIcommonevaluationแยก ไม่มีautomaticbenchmark/retry/newexperiment. ยังไม่ประกาศoverallwinner/CCTVready/clean speed ranking. Historical attempts/configs/sourceGT/results preserved.
