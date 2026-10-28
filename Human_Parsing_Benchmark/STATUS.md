# Human Parsing Benchmark — current status

Updated 2026-10-28T23:01:47.384252+07:00 Bangkok

**RPR_SHARED_GPU_QUALITY_RUNNING**. RP-R-CNN-only nativeCIHP5000 round `rpr-cihp-shared-20261028T155439603873Z`, parent `cihp-native-six-20261028T034103254470Z`. New admission policy SHARED_GPU_QUALITY_ONLY is explicit, not an exclusive/clean timing claim. Scientific frozen configSHA`3b6c98ef8056bc24c0a503559972619b7cb82bcf40cdfa2983579a84567c5a24`, model/preprocessing/ownership/scorer/FP32 settings unchanged. Existing VAL reuse0, complete170/5000 at this observation; failed0/invalid0. No partial score analysis/ranking.

ControllerPID145516, workerPID145530; independent session/DEVNULL and PPID/SID verified in launch evidence. First image0000001 passed NPZ hash, native-label/original-grid geometry, metadata/resource-policy and both scoring-artifact checks. [Report](reports/CIHP_CONTROLLED_CONTINUATION.md) / [launch](runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-shared-20261028T155439603873Z/LAUNCH_VERIFICATION.json) / [resource override](runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-shared-20261028T155439603873Z/RESOURCE_POLICY.json).

External root `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/rounds/rpr-cihp-shared-20261028T155439603873Z`: ROUND_STATUS.json for controller/terminal status, segments/RPR_CIHP/RUN.json and FRAMES.jsonl for live counts, WORKER.log/CONTROLLER.log, GPU_HEALTH.jsonl and PROCESS.json for command/session. No need for Codex polling. Atomic committed artifacts retained on interruption; no automatic restart/retry/fallback.

Controller contains exactly one RPR worker and stops before CPI. After exit it validates NPZ/metadata/GT/scoring/unique IDs, assembles canonical metrics, keeps main scores null if incomplete and appends the RPR terminal report/COMPLETION evidence. Original24h/80GiB/50GiB caps retained; shared-GPU timings/VRAM not ranked. No CPI/matrix/Sapiens/color/training/other model.

## Live progress (read-only)

From the workspace root run `python3 Human_Parsing_Benchmark/scripts/rpr_progress.py --watch`. It refreshes every5seconds, shows separate inference and artifact-validation progress, failed/invalid counts, latest image and actual PID liveness, and exits at terminal/interruption. Ctrl+C stops only the viewer. `--json` prints machine-readable status; omit `--watch` for one snapshot. Existing numeric counts above are dated observations, not live counters. No GPU query/model import/new inference or persistent monitor daemon is added.
