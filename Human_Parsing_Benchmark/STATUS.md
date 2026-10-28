# Human Parsing Benchmark — current status

Updated 2026-10-28T22:57:26.070519+07:00 Bangkok

**RPR_SHARED_QUALITY_READY_NOT_LAUNCHED**. User requests proceeding despite GPU contention. Explicit shared-GPU quality resource override, not a claim of no effect. Existing VAL results0, pending5000IDs, parent `cihp-native-six-20261028T034103254470Z`, segment `rpr-cihp-shared-20261028T155439603873Z`. Checkpoint/config/source hashes and package-freeze match verified readiness; two targeted CPU control cases pass. Frozen scientific config/worker/adapter/scorer unchanged.

[RP-R-CNN report](reports/CIHP_CONTROLLED_CONTINUATION.md) / [resource override](runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-shared-20261028T155439603873Z/RESOURCE_POLICY.json) / [segment plan](runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-shared-20261028T155439603873Z/SEGMENT_PLAN.json). Only RPR may launch; stop before CPI. Timing shared adapter diagnostics only, no clean speed/VRAM ranking. OOM/model retries0, no CPU/FP16 fallback. Next commit/push source+plans then launch one detached controller, verify first packet briefly and end turn. No matrix/Sapiens/color/training/other-model work.
