# Human Parsing Benchmark — current status

Updated: 2026-10-29T22:14:04.456886+07:00 (Asia/Bangkok)

**CPI_CONVNEXT_RUNNING** — [current attempt/report](reports/cpi-convnext-idle-gpu-20261029T151038229214Z.md), [process](runs/cpi-convnext-idle-gpu-20261029T151038229214Z/PROCESS.json), [frozen segment plan](runs/convnext-20261029T151056554085Z/SEGMENT_PLAN.json). Segment `convnext-20261029T151056554085Z`; controller PID `607715`, worker PID `607888`; detached session `607715` verified with controller parent PID1. Reused145; remaining at launch4855; observed new160, total305/5000, failed0 at this timestamp. Counts are a snapshot; use viewer for live progress.

TRAIN warmup passed; first new ID0001641 (previous OOM image) now passed with native20 integer/original geometry, metadata/NPZ/GT bindings and saved-mask scores checked at0.50/0.75. Its peak allocated10489.09MiB/reserved10718MiB is an observation, not a bound for remaining images. No guarantee of full completion; no automatic retry/fallback/next model.

Sapiens2 0.4B and 0.8B each COMPLETE5000: [0.4B/common cohort](reports/CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md), [0.8B](reports/CIHP_SAPIENS_08B_C4P_RESULTS_TH.md). Four native/common systems preserved. CPI R50 paused. Native20 and C4-P results remain separate; STRICT_COMPLETE primary null until5,000 verified. Timing/resource diagnostics only.

```bash
.venvs/parser-legacy-cu113/bin/python Human_Parsing_Benchmark/scripts/run_cpi_continuation.py --model convnext --status --watch
```

Controller stops after this model/error and writes canonical COMPLETION. Read-only detached finalizer will update this report/status if its guard still matches and publish summaries; it never launches inference. Interrupted controller/missing completion requires reconciliation. No1B/R50/training/color/CCTV.
