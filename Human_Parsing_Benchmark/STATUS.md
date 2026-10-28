# Human Parsing Benchmark — current status

Updated 2026-10-29T00:32:12.166849+07:00 Bangkok

**CPI_R50_SHARED_QUALITY_READY_NOT_LAUNCHED**. User explicitly amends CPI R50 admission to SHARED_GPU_QUALITY_ONLY for quality/completeness; no external-PID blockage. No global/system changes or solo/shared experiment. Prior QANet/M2FP/D2FP/RPR completions preserved. CPI_R50 existing/reuse0, pending5000; only CPI_R50 may launch, stop before ConvNeXt-B.

Checkpoint/config/source hashes and environment freeze match original readiness. VRAM13173MiB free vs prior TRAIN reserved peak3760MiB, not an OOM guarantee. Standard TRAIN0000930 warmup/first VAL packet must pass. Frozen scientific configSHA`3b6c98ef8056bc24c0a503559972619b7cb82bcf40cdfa2983579a84567c5a24`, FP32/preprocessing/thresholds/ownership/GT/scoring/limits unchanged. Shared timings/native CPI file I/O are diagnostics only, no speed or memory ranking.

[Main R50 report](reports/CIHP_CONTROLLED_CONTINUATION.md) / [resource amendment](runs/cihp-native-six-20261028T034103254470Z/cpi-r50-shared-20261028T172951337299Z/RESOURCE_POLICY.json) / [exact plan](runs/cihp-native-six-20261028T034103254470Z/cpi-r50-shared-20261028T172951337299Z/SEGMENT_PLAN.json) / [overview](manifests/CIHP_NATIVE_COHORT_INDEX.json). Round `cpi-r50-shared-20261028T172951337299Z`, parent `cihp-native-six-20261028T034103254470Z`. Read-only progress: `python3 Human_Parsing_Benchmark/scripts/cpi_r50_progress.py --watch`. Current cohort4/6 closed; CPI pending, ConvNeXt outside current scope.

Next commit/push reviewed control snapshot, launch one detached controller, check first packet briefly, end turn. Auto health/strict-complete validation/report at terminal. No fallback/unbounded restart/retry or other-process change. No ConvNeXt/matrix/Sapiens/color/training/other model inference.
