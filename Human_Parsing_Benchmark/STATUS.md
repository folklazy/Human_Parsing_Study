# Human Parsing Benchmark — current status

Updated 2026-10-29T00:07:17.768881+07:00 Bangkok

**CPI_R50_ROUND_BLOCKED — EXTERNAL_GPU_BUSY**. Current authorization CPI_R50_CIHP only, original GPU admission policy; no RPR shared override. Snapshot00:03:52+07:00 on29Oct: external PID126277 uses1736MiB onT4; utilization0%/free13173MiB does not pass the no-external-compute gate. No parsing worker/controller active or launched, no wait/poll, no retry or other-process intervention. Reuse0/remain5000, failed_VAL0/invalid_VAL0/not_attempted5000, main score null.

[Main .md report: CPI R50 section and current overview](reports/CIHP_CONTROLLED_CONTINUATION.md) / [preflight](runs/cihp-native-six-20261028T034103254470Z/cpi-r50-preflight-20261028T170717768881Z/PREFLIGHT.json) / [current canonical-source index](manifests/CIHP_NATIVE_COHORT_INDEX.json) / [current CSV](metrics/CIHP_NATIVE_COHORT_OVERVIEW.csv). Parent `cihp-native-six-20261028T034103254470Z`, record `cpi-r50-preflight-20261028T170717768881Z`; execution segment/PID/launch N/A.

Current cohort **4/6 COMPLETE** from canonical results, in frozen roster order:

| Model | Complete/5000 | Context |
|---|---:|---|
| QANet |5000|original parent|
| M2FP |5000|original parent|
| D2FP |5000|parent1810 + continuation3190|
| RP-R-CNN |5000|separate SHARED_GPU_QUALITY_ONLY round|
| CPI R50 |0|current resource-blocked preflight|
| CPI ConvNeXt-B |0|historical blocked setup; not in current scope|

No inference/rescoring for this summary. Original REPORT_TH.md now visibly labeled historical with a link to current overview; old contents/results remain byte-identical below the label. Not a single segment/resource regime or an exclusive timing claim; no model ranking.

Next: end blocked round; on later continuation recheck resources once and proceed only within CPI_R50 scope when original gate passes. Checkpoint/nativeconfig/source/environment identities use recorded readiness; startup payload hash/model load/first packet remain pending. No ConvNeXt/matrix/Sapiens/color/training/additional experiment. All prior results and scientific config/source unchanged.
