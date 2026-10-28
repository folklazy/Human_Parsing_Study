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

## D2FP-only closure — 2026-10-28T22:04:49.552812+07:00

Latest user requests one round restricted to D2FP and a short health check instead of persistent polling. Actual inspection found D2 already finished at2026-10-28T16:27:59.022013+07:00; controller/worker/monitor exited. Verified parent1810 + continuation3190 =5000 distinct official IDs; duplicate/missing/failed/invalid0. Strict-complete main score available, no quality ranking in this closure. [Machine-readable closure](../runs/cihp-native-six-20261028T034103254470Z/D2FP_ROUND_CLOSURE.json). Reused existing full NPZ/CRC/metadata/GT/rescore audit evidence and revalidated ledger digests, membership, required artifacts and denominators; no new inference or redundant full audit.

Before this instruction the old controller had already attempted RP-R-CNN/CPI setup, all blockedEXTERNAL_GPU_BUSY with0 VAL inference. Preserve those historical attempts; they are not an authorization to retry now. No active queue remains, so no controller edit/new process is needed. Current round is closed, remaining D2 IDs0. All further model rounds/matrix/Sapiens/color wait for a separate explicit instruction. Original frozen config and run records remain unchanged.

## RP-R-CNN CIHP only — readiness BLOCKED (2026-10-28T22:32:24.395816+07:00)

This section is the self-contained handoff for the newly authorized **RP-R-CNN only** round. **Status BLOCKED / EXTERNAL_GPU_BUSY**, VAL inference NOT_ATTEMPTED. No worker/controller/session or background launch was created; no waiting/poll loop and no process of another project was stopped.

- Model/checkpoint: RPR_CIHP, RP-R-CNN R50 trained on CIHP; `models/human_parsing/rp_r_cnn/RPR_CIHP/model.pth`,234931960bytes. Expected frozen SHA256 `6b596210f3ea67c79aae94c4769716b3cd41d781e2dbf36e0900c1b020721d98`. Existence/size checked; the payload was not rehashed because GPU gate already blocked. Retain prior readiness; verify SHA at eventual worker startup.
- Native config: `Human_Parsing_CCIHP_10_Image_Pilot/configs/RPR_CIHP.yaml`, SHA256 `44f4c4d08b917c9e141104cc225863231ceb0fac5c84566a22e04d3c793b6bd2` verified. Source `third_party/human_parsing/RP-R-CNN` commit `dfcc227723d4bf6566356cda4513a84ed9a8ba30` verified. Environment `.venvs/parser-legacy-cu113` retained from readiness; no model/environment smoke or package change this round.
- Parent `cihp-native-six-20261028T034103254470Z`, historical segment `continuation-20261028T073741308461Z`. New preflight record `rpr-cihp-preflight-20261028T153224395816Z`; **new execution segment NOT_LAUNCHED**. [Machine evidence](../runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-preflight-20261028T153224395816Z/PREFLIGHT.json).
- Source/scientific config unchanged, frozen SHA256 `3b6c98ef8056bc24c0a503559972619b7cb82bcf40cdfa2983579a84567c5a24`. Same official CIHP VAL5000 IDs, native20labels, frozen YOLO cache, association/ownership, FP32, native preprocessing/TTA/settings and scorer. Caps unchanged:24h/checkpoint,80GiB stream,free50GiB; no automatic model/OOM retry or CPU/FP16 fallback.
- Readiness resource observation **2026-10-28 22:30:14+07:00**: TeslaT4 15360MiB,13173MiB free, utilization0%, but unrelated GPU compute PID126277 held1736MiB. Policy forbids GPU contention and the unchanged worker rejects any existing compute PID. Free VRAM/utilization alone do not satisfy this gate. Disk approximately509GiB free is sufficient for the minimum guard, not proof of a whole-run storage bound.
- Current inventory: original parent RPR VAL folder absent; historical blocked segment has0 packets/no frame ledger, COMPLETE0. No reusable VAL results; **remaining5000 IDs**. Setup blocked history is preserved separately from VAL failures: failed_VAL0, invalid_VAL0, not_attempted5000. STRICT_COMPLETE main score null. No score/ranking analysis.
- Time: resource check22:30:14+07:00, preflight closed2026-10-28T22:32:24.395816+07:00; model start/end N/A because no model process launched. New PID/session/log for inference N/A. Local preflight log `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/rounds/rpr-cihp-preflight-20261028T153224395816Z/PREFLIGHT.log`.

The eventual result remains a **YOLO-associated application pipeline on native CIHP labels**, not an official native parser result by default. Timing is adapter diagnostics, not clean parser-only/end-to-end speed ranking. Other interpretation limitations from the correction section remain unchanged.

**Queue boundary:** RPR_CIHP only; stop after it. Do not invoke the historical six-system controller without a scoped controller. CPI2/matrix/Sapiens/color/training and all other model rounds are outside this authorization. This blocked round ends now; no automatic retry or deferred auto-launch. When a later continuation is requested and GPU policy passes, finish the remaining readiness/bindings, use a fresh linked RPR-only segment, check the first committed packet briefly, then leave automatic strict-completeness/closure reporting to the controller. No full audit or inference repetition just for reporting.

## RP-R-CNN only — shared-GPU quality override / ready (2026-10-28T22:57:26.070519+07:00)

Latest user asks to proceed despite the other GPU application after the no-contention gate was explained. Adopt explicit **SHARED_GPU_QUALITY_ONLY** resource-policy amendment for this RPR-only round; do not describe shared GPU as having no effect. Timing/free VRAM and OOM risk can change, and identical numerical outcomes are not guaranteed. No latency/FPS/VRAM ranking. Prior EXTERNAL_GPU_BUSY records remain immutable.

Parent `cihp-native-six-20261028T034103254470Z`, new segment `rpr-cihp-shared-20261028T155439603873Z`, queue only `RPR_CIHP`; no CPI or other checkpoint can be launched by this controller. New worker uses a hash-bound expansion of the original scientific worker, changing GPU admission and operational/timing provenance only; original frozen config/adapter/scorer/worker remain byte-identical. [Effective resource policy](../runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-shared-20261028T155439603873Z/RESOURCE_POLICY.json) / [exact5000-ID segment plan](../runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-shared-20261028T155439603873Z/SEGMENT_PLAN.json). Checkpoint/model/native-config/source hashes verified, installed-package freeze matches prior RPR readiness. Existing VAL packets0, remaining5000. No previous successful inference is repeated.

Preserve FP32, native preprocessing/TTA/thresholds, frozenYOLO cache/ownership/association, GT/scorer/native20,24h/80GiB stream/50GiB free-space limits, model/OOM retry0 and no CPU/FP16 fallback. A controller24h wallclock watchdog includes setup, never extends the original24h worker loop cap; it can stop only its own worker. One declaredTRAIN0000930 warmup is required; excluded fromVAL/timing scores.

Two targeted CPU control tests pass: only RPR shared-quality scope is accepted, and the frozen forward/scoring blocks remain byte-identical. No extra GPU smoke or cross-model analysis. Controller opens exactly one worker, logs health without Codex polling, validates artifacts/ID union at terminal, preserves STRICT_COMPLETE/null incomplete scores, appends the standalone RPR terminal section and publishes compact canonical summaries. Atomic NPZ/metadata/ledger output remains unchanged; interruption requires explicit reconciliation, not automatic restart. State READY_NOT_LAUNCHED until actual launch evidence appears.

## RP-R-CNN shared-quality — actual launch (2026-10-28T23:01:47.384252+07:00)

**RUNNING**, segment `rpr-cihp-shared-20261028T155439603873Z`, launch commit `ec3731211baf6520ac4c8fc567ef7eed8825ed19`. Controller PID145516, worker PID145530, detached session confirmed; both live at inspection. First VAL image0000001 committed with matching NPZ hashes, original-grid native20 masks, resource-policy metadata and both threshold/native-reference scoring files. Complete170/5000 at this observation, failed0, invalid0; reuse0. No quality scores inspected/ranked. [Launch evidence](../runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-shared-20261028T155439603873Z/LAUNCH_VERIFICATION.json).

Frozen scientific config/source/weights retained; GPU admission override is explicit. Raw root `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/rounds/rpr-cihp-shared-20261028T155439603873Z`. Use ROUND_STATUS.json for terminal state and segments/RPR_CIHP/RUN.json for live progress; WORKER.log and CONTROLLER.log retain diagnostics. Exactly one RPR worker, no CPI queue. Automatic artifact reconciliation/strict-complete report follows terminal; no auto restart/OOM retry/precision fallback. This verifies detached execution under this server's process model, not immunity to server shutdown or external termination.

## RP-R-CNN CIHP shared-GPU round — terminal 2026-10-28T23:52:39.754400+07:00

**COMPLETE**, model `RPR_CIHP` (RP-R-CNN R50 CIHP). Parent `cihp-native-six-20261028T034103254470Z` / segment `rpr-cihp-shared-20261028T155439603873Z`. Launch commit `ec3731211baf6520ac4c8fc567ef7eed8825ed19`. Checkpoint `models/human_parsing/rp_r_cnn/RPR_CIHP/model.pth`, SHA256 `6b596210f3ea67c79aae94c4769716b3cd41d781e2dbf36e0900c1b020721d98`; native config `Human_Parsing_CCIHP_10_Image_Pilot/configs/RPR_CIHP.yaml` / SHA256 `44f4c4d08b917c9e141104cc225863231ceb0fac5c84566a22e04d3c793b6bd2`; source commit `dfcc227723d4bf6566356cda4513a84ed9a8ba30`; environment `.venvs/parser-legacy-cu113`. Frozen scientific config unchanged; effective resource policy is explicit **SHARED_GPU_QUALITY_ONLY** override.

StartedUTC `2026-10-28T16:00:03.273514+00:00`, endedUTC `2026-10-28T16:43:39.973125+00:00`, checkedUTC `2026-10-28T16:52:39.754020+00:00` / Bangkok `2026-10-28T23:52:39.754400+07:00`. Completed/expected 5000/5000; failed 0, invalid 0, not-attempted 0, missing IDs 0, duplicate IDs 0. Main native20mIoU inclBG **59.1241%**, FG19 **57.4079%**. No cross-model ranking.

[Canonical completion](../runs/cihp-native-six-20261028T034103254470Z/rpr-cihp-shared-20261028T155439603873Z/COMPLETION.json), [summary](../metrics/rpr-cihp-shared-20261028T155439603873Z/SUMMARY.csv), [per-class](../metrics/rpr-cihp-shared-20261028T155439603873Z/PER_CLASS.csv). Person metrics at0.50/0.75 and native-reference metrics are in canonical completion when complete. Historical EXTERNAL_GPU_BUSY setup attempts are preserved separately; this segment setup status `PASS` is distinct from VAL failures. Error `None`.

Scientific policy: CIHP official5000IDs/native20, frozen YOLO cache, native preprocessing/TTA, FP32, association/ownership/scoring unchanged. Only GPU admission policy differs: coexistence allowed by current user direction; original frozen config is retained, not silently edited. This is a YOLO-associated application pipeline, not an official native-parser benchmark reproduction. Timing is shared-GPU adapter diagnostics, not clean parser-only/end-to-end speed ranking; no contention-free claim or quality transfer guarantee. Hard labels/stored ownership retained; full probabilities/native confidence outputs are not all recoverable.

Checks: {'hashes_metadata_NPZ_CRC_GT_and_saved_mask_rescore': 'PASS', 'exact_expected_ID_union': True, 'no_duplicate_IDs': True, 'source_artifacts_preserved': True}. Original model/OOM retry0, no CPU/FP16 fallback. Raw logs/packets/ledgers/audit under `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/rounds/rpr-cihp-shared-20261028T155439603873Z`; use ROUND_STATUS.json for terminal state. Queue contains only RP-R-CNN and has stopped; no CPI/matrix/Sapiens/color/training. Next inspect failures if incomplete or review this model's canonical report if complete; no automatic retry or next-model launch.

## CPI R50 CIHP only — preflight BLOCKED (2026-10-29T00:07:17.768881+07:00)

**BLOCKED / EXTERNAL_GPU_BUSY**, no execution segment/worker/controller launched. Current authorization permits only CPI_R50_CIHP on native CIHP5000 with the original GPU admission policy; RP-R-CNN SHARED_GPU_QUALITY_ONLY is explicitly **not** inherited. Stop before ConvNeXt-B. [Preflight evidence](../runs/cihp-native-six-20261028T034103254470Z/cpi-r50-preflight-20261028T170717768881Z/PREFLIGHT.json).

Model/checkpoint: CPI-Parser R50 CIHP, `models/human_parsing/cpi_parser/CPI_R50_CIHP/model.pth`,571901148bytes, expected SHA256 `e58f8cb4b4fb3b7513e4dd2efb2c8aece07fd237404789204b8b9863f2b7cf35`. File exists/size matches; no redundant payload hash after failed resource gate, verify at actual worker startup. Native config `third_party/human_parsing/CPI-Parser/configs/COSParser/causal_parser_r50_inter_8_135k_cihp.py` SHA256 `62b39d8753d5ce8afc137fab5857757024e999ac49a3023645c239a8c4511575` verified; source commit `d62cae523ba913fec4a7fda5816bc1d96bbf644d` verified. Environment `.venvs/parser-legacy-cu113` package-freeze matches prior3TRAIN FP32/Torch1.10.2+cu113/CUDA11.3 readiness. No new dependency/checkpoint/environment/model import or smoke. Historical TRAIN fingerprints are not cache identities.

Parent `cihp-native-six-20261028T034103254470Z`, preflight `cpi-r50-preflight-20261028T170717768881Z`; historical native setup at `continuation-20261028T073741308461Z/segments/CPI_R50_CIHP` remains BLOCKED with0VAL/no ledger/no packets. Current native parent/continuation/round inventories have0 reusable CPI_R50 packets,5000 pending. Unrelated older CPI experiments under a different protocol are excluded. Failed_VAL0/invalid_VAL0/not_attempted5000; setup-preflight blocked is not a VAL inference failure. Main score null under STRICT_COMPLETE. No model start/end or launch PID exists; resource observation2026-10-29T00:03:52+07:00, blocked round closed2026-10-29T00:07:17.768881+07:00.

GPU: TeslaT4 Default15360MiB total,13173MiB free, utilization0%, external compute PID126277 holding1736MiB. Original worker admission rejects any compute PID; sufficient free memory/utilization0 does not waive policy. Disk~508GiB above50GiB guard. Did not wait/poll, modify other processes, weaken policy or launch a broad queue. Frozen scientific source/config/weights unchanged; preserve FP32/native20/population/YOLOcache/ownership/association/preprocessing/TTA/thresholds/scoring/24h/80GiB/50GiB/retry0/no fallback.

Results, when obtained, are YOLO-associated application native-label metrics, not an official native-parser reproduction. CPI adapter timing includes native JPEG/PNG I/O; not clean parser-only or end-to-end speed ranking. Raw preflight log/evidence stay at `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/rounds/cpi-r50-preflight-20261028T170717768881Z`. Next later continuation rechecks resources once; only after original gate passes, finish startup hashes/scoped CPI_R50 controller/first-packet verification and autonomous closure. No ConvNeXt/matrix/Sapiens/color/training or automatic retry in this round.

## Current cohort overview

Updated 2026-10-29T00:32:12.175639+07:00. **4/6 complete**, fields copied from canonical records in frozen roster order; no inference/rescoring/ranking. Distinct segments/resource policies remain explicit. [Current CSV](../metrics/CIHP_NATIVE_COHORT_OVERVIEW.csv) / [source index](../manifests/CIHP_NATIVE_COHORT_INDEX.json).

| Model | Status | Complete/5000 | mIoU20 inclBG | FG19 | Segment/resource |
|---|---|---:|---:|---:|---|
|QANet_CIHP_HRNetW48_512x384|COMPLETE|5000|64.866%|63.449%|cihp-native-six-20261028T034103254470Z; ORIGINAL_NO_CONTENTION_ADMISSION; exclusive runtime not certified|
|M2FP_R101_CIHP|COMPLETE|5000|68.155%|66.796%|cihp-native-six-20261028T034103254470Z; ORIGINAL_NO_CONTENTION_ADMISSION; exclusive runtime not certified|
|D2FP_R101_CIHP|COMPLETE|5000|64.352%|62.827%|cihp-native-six-20261028T034103254470Z + continuation-20261028T073741308461Z; ORIGINAL_NO_CONTENTION_ADMISSION; exclusive runtime not certified; D2 concurrent external GPU PIDs observed in health log|
|RPR_CIHP|COMPLETE|5000|59.124%|57.408%|rpr-cihp-shared-20261028T155439603873Z; SHARED_GPU_QUALITY_ONLY|
|CPI_R50_CIHP|READY_NOT_LAUNCHED|0|null / unavailable|null / unavailable|cpi-r50-shared-20261028T172951337299Z; SHARED_GPU_QUALITY_ONLY|
|CPI_ConvNeXtB_CIHP|HISTORICAL_SETUP_BLOCKED_OUTSIDE_CURRENT_SCOPE|0|null / unavailable|null / unavailable|continuation-20261028T073741308461Z (historical setup only); ORIGINAL_NO_CONTENTION_ADMISSION; exclusive runtime not certified|

Not a single execution segment or uncontended timing cohort. Native-label YOLO application scores are not official native-parser reproduction; no clean speed/VRAM ranking. Historical source reports and closed-model outputs are preserved.

## CPI R50 shared-GPU quality amendment — ready (2026-10-29T00:32:12.166849+07:00)

User **explicitly authorizes** SHARED_GPU_QUALITY_ONLY for CPI_R50_CIHP in this round, prioritizing evaluation correctness/completeness/quality over speed. This supersedes the previous no-external-PID admission requirement for this checkpoint/round only; it is not an automatic transfer of the RPR override. No process/system/GPU configuration is changed, and no solo-versus-shared experiment is required. [Resource amendment](../runs/cihp-native-six-20261028T034103254470Z/cpi-r50-shared-20261028T172951337299Z/RESOURCE_POLICY.json).

Parent `cihp-native-six-20261028T034103254470Z`, segment `cpi-r50-shared-20261028T172951337299Z`. Dedicated controller uses only modelID CPI_R50_CIHP, stops before ConvNeXt-B, and validates its own model/scope/hash bindings. [Exact5000-ID plan](../runs/cihp-native-six-20261028T034103254470Z/cpi-r50-shared-20261028T172951337299Z/SEGMENT_PLAN.json), [readiness](../runs/cihp-native-six-20261028T034103254470Z/cpi-r50-shared-20261028T172951337299Z/READINESS.json), [checks](../runs/cihp-native-six-20261028T034103254470Z/cpi-r50-shared-20261028T172951337299Z/CONTROL_ACCEPTANCE.json). Prior native CPI setup blocks retained; current VAL packets0/reuse0/pending5000, unrelated older CPI protocols excluded. No completed model is re-inferred.

CPI checkpoint `models/human_parsing/cpi_parser/CPI_R50_CIHP/model.pth` SHA256 `e58f8cb4b4fb3b7513e4dd2efb2c8aece07fd237404789204b8b9863f2b7cf35` verified; native-config/source/old frozen scientific bindings verified, installed-package freeze equals original3TRAIN readiness. Free VRAM13173MiB vs observed prior TRAIN peak reserved3760MiB (not a worst-case guarantee). One standardTRAIN0000930 warmup checks load/forward beforeVAL. Four scoped CPU control cases and two backward-compatible progress cases pass; no new GPU smoke or isolated-GPU comparison.

Preserve native CIHP5000,20labels, FP32, resolution/TTA/thresholds, batch/deterministic seed/TF32 settings, YOLO cache, association/ownership, GT/scorer and24h/80GiB/50GiB/model-retry0/no fallback policies. Original config/worker/adapter/scorer bytes unchanged. Reuse reviewed resource/segment mechanics with a CPI-specific scope validator and timing metadata: native JPEG read, PNG writes/re-reads are inside CPI adapter timing, canonical export/GT scoring/global composition outside. Timing/resource traces are shared diagnostics, not latency/FPS/memory-efficiency ranking. Shared execution can change available memory/time; OOM/CUDA failures stop/preserve partial artifacts, never reduce quality/drop failed IDs/auto-retry.

On launch: detached one-model controller, required warmup and short first-packet check only, then Codex ends turn. Automatic packet/hash/NPZ/GT/saved-mask re-score and exact-ID union validation produce strict COMPLETE/null incomplete main scores and update this R50 report plus canonical-source overview, without inference/scoring of other models. Progress command: `python3 Human_Parsing_Benchmark/scripts/cpi_r50_progress.py --watch` (read-only; Ctrl+C stops only viewer). No ConvNeXt/matrix/Sapiens/color/training/other experiments. State currently READY_NOT_LAUNCHED.
