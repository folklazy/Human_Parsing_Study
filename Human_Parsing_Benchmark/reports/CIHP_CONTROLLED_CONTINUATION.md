# CIHP — controlled continuation / correction record

Updated 2026-10-28T07:47:16.592548+00:00 UTC. Status: **RECONCILIATION_RUNNING**, not a completed benchmark report. Parent `cihp-native-six-20261028T034103254470Z`; continuation `continuation-20261028T073741308461Z`. User explicitly authorizes reconciliation and disjoint continuation; no new scientific task/precision/threshold/ownership change.

## Interruption evidence

No original controller34503, worker49052 or monitor53568 at inspection; GPU idle. Monitor detected `INTERRUPTED_CONTROLLER_REQUIRES_RECONCILIATION` at2026-10-28T07:09:10 UTC. Last D2 committed image0016668 ended07:08:49 UTC. Original LAUNCH/RUN labels are stale and preserved, not evidence of a live process. No CUDA/OOM traceback, exit signal or original controller exit code captured. Kernel journal interval07:07–07:10 returned no entries. **Cause UNKNOWN**; this does not prove absence of GPU/host OOM.

## Reconciliation and planned work

| Model | Original ledger COMPLETE | New VAL jobs if all original artifacts validate |
|---|---:|---:|
| QANet CIHP HRNet-W48 |5000|0|
| M2FP R101 CIHP |5000|0|
| D2FP R101 CIHP |1810|3190|
| RPR CIHP |0|5000|
| CPI R50 CIHP |0|5000|
| CPI ConvNeXt-B CIHP |0|5000|

Total reuse candidates11810; remaining18190; total30000 frame/system observations after verified union. Original source population is5000 IDs per model, with no exclusions or membership change. D2 first pending ID0016688. Its prior in-flight status is unknown: it may have entered forward before process loss, but has no committed packet/ledger row. Recovery does not repeat any verified completed image and is not an automatic retry of a recorded model/OOM failure.

Original packet-directory counts equal ledger counts, no orphan directories found. Every accepted source NPZ is SHA256 checked against metadata+ledger and every array read (ZIP member CRC checked). Checkpoint/source/input/config/original geometry, detector binding, inference fingerprint and evaluation fingerprint are verified. Re-score both0.50/0.75 and native reference from saved masks+unchanged GT, require exact agreement with scoring artifacts, then rebuild sufficient statistics. All historical source files remain unchanged. Scores are not used to choose which output to keep.

Fresh segment manifests contain source-order pending/reused IDs and their disjoint exhaustive partition, parent link, config/source/checkpoint binding, prior resource accounting and exact control-only worker diff. Frozen worker and config remain byte-identical. A bounded source expansion adds only segment selection, output provenance and cumulative resource accounting; native forward/scoring blocks are unchanged and CPU checks enforce this. Four additional TRAIN0000930 process warmups are needed; none are VAL observations.

Fresh assembled view contains links to verified packets, rebuilt terminal ledgers and recomputed metrics. It does not duplicate or rewrite raw predictions. Complete only with5000 unique eligible IDs/scoring records; incomplete main scores null, failures retained. Original model failure/OOM retry0, FP32, no CPU fallback or changed native resolution/TTA/settings. Prior execution duration and retained bytes count against24h/80GiB stream limits; free-space guard50GiB remains.200GiB remains planning, not a guaranteed storage bound. Reconciliation CPU cost and additional warmups are separate operational evidence, not parser timing.

## Corrections to interpretation (no scoring-policy change)

1. Primary results are **YOLO ROI/association application pipelines on native CIHP labels**. Ungated references from the same raw outputs are separate; this is not an official native-parser benchmark for every model or an architecture-only causal comparison.
2. **Adapter timing diagnostics have unequal boundaries**. Frozen YOLO forward is absent. Native preprocessing/forward/postprocessing/map-back/association are timed; RPR/CPI internal detection is retained. CPI native JPEG loading, PNG writing and re-reading happen inside adapter timing; common/global semantic composition and metric scoring occur outside. Do not call these clean parser-only or end-to-end speed/FPS rankings. Per-ROI time distributions and joint YOLO/parser residency were not measured.
3. Historical TRAIN RPR/CPI packets have repeated inference fingerprints across models. They are not standalone cache identities. This continuation reuses only VAL packets verified with checkpoint/model/input/NPZ/config/source/detector bindings and expected fingerprints, never those TRAIN fingerprints.
4. Outputs support hard-label remapping **under stored ownership**. Full probabilities/logits and some native quality-head confidence/part-query outputs were not retained. M2FP/D2FP overlap ownership is already resolved before export. No claim of arbitrary probability aggregation, native-confidence metric parity or recovering excluded predictions.

## Verification and artifacts

New code: scripts/reconcile_cihp_continuation.py, run_cihp_segment.py, continue_cihp_batch.py. CPU checks: tests/test_cihp_continuation.py (partition no-repeat/no-missing/order; corrupted NPZ rejection without source modification; unchanged frozen forward/scoring source blocks). Original scorer tests/evidence reused, no full-suite/model smoke rerun.

External evidence root: `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/continuations/continuation-20261028T073741308461Z/`. RECONCILIATION.log, reconciliation/<model>/VERIFIED_FRAMES.jsonl + RECONCILED.json, INTERRUPTION_INVESTIGATION.json, CPU_ACCEPTANCE.log; segment plans/controller state/segments/assembled appear only when preparation/execution occurs. New reporting uses continuation binding in completion report. No false COMPLETE/launch claim while these steps are pending.

Next: finish reconciliation → exact segment manifest/dry plan → source/config freeze check and Git snapshot → continue only disjoint jobs → validate new artifacts and aggregate → terminal report. No matrix/Sapiens/color/Ninja/training/CCTV starts from this action.

## Reconciliation closure — 2026-10-28T08:00:34.137922+00:00

**VERIFIED** all11810 original VAL packets: QANet5000, M2FP5000, D2FP1810. No orphan/non-complete ledger rows. Full NPZ decode/hash, metadata/inference/evaluation bindings, GT hashes and independent stored-mask re-score match both thresholds/native-reference artifacts. Six disjoint/exhaustive partition plans prepared:0/0/3190/5000/5000/5000 new jobs in original roster order. [Exact continuation plan](../runs/cihp-native-six-20261028T034103254470Z/continuation-20261028T073741308461Z/CONTINUATION_PLAN.json).

Three CPU control cases pass in both stage0 and actual legacy environments. Real QANet2500+2500 aggregation equals original global scores; person roundoff1.887e-15 (<1e-12), missing-fragment main score null, duplicate fragment rejected. [Acceptance](../runs/cihp-native-six-20261028T034103254470Z/continuation-20261028T073741308461Z/CONTROL_ACCEPTANCE.json). No new inference performed during reconciliation.

Status at this closure: **CONTINUATION_READY_PRELAUNCH**, not a completed batch. Original model/input/preprocessing/ownership/scorer/config bytes preserved. New control-code snapshot is committed before continuation launch.

## Actual launch — 2026-10-28T08:05:28.487293+00:00

**CONTROLLED_CONTINUATION_RUNNING**. Actual continuation commit `e51464da35327811ee49453649394edbdd508872`, controller PID70184, D2 worker PID70200. First new VAL image0016688 committed with verified NPZ/metadata/fingerprint and no overlap with original1810 D2 IDs. No QANet/M2FP worker was launched. [Launch evidence](../runs/cihp-native-six-20261028T034103254470Z/continuation-20261028T073741308461Z/LAUNCH_VERIFICATION.json). The benchmark is still incomplete; no headline score/ranking from partial frames. Original frozen config and source identities verified unchanged again after first new output.
