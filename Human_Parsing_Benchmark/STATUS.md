# Human Parsing Benchmark — current status

Updated: 2026-10-28T22:04:49.552812+07:00 (Asia/Bangkok)

**D2FP_ROUND_COMPLETE_STOPPED** — current authorization is D2FP CIHP only. Verified union: original1810 + continuation3190 =5000 unique official validation IDs; duplicate/missing/failed/invalid IDs all0. No inference was launched in this closure round. Main metrics satisfy STRICT_COMPLETE; no quality ranking/selection was performed.

D2 worker completed 2026-10-28T16:27:59.022013+07:00; segment reconciliation completed2026-10-28T09:33:37UTC. Historical controller70184/worker70200/monitor71022 have exited. No Human Parsing controller/worker remains; do not touch the unrelated GPU workload. Original stale parent LAUNCH/RUN and historical results remain unchanged.

[Machine-readable D2 closure](runs/cihp-native-six-20261028T034103254470Z/D2FP_ROUND_CLOSURE.json) / [continuation report](reports/CIHP_CONTROLLED_CONTINUATION.md) / [PLAN](PLAN.md). Segment `continuation-20261028T073741308461Z`. Parent `cihp-native-six-20261028T034103254470Z`. Exact status/log/ledger paths and audit hashes are in closure JSON.

The previous controller had already attempted RPR/CPI setup before this instruction; all3 blocked with EXTERNAL_GPU_BUSY,0 VAL inference. These are historical attempts, not current authorization. No retries or automatic continuation. The historical six-system cohort remains FINISHED_WITH_INCOMPLETE_SYSTEMS and is preserved.

Next: wait for a separate scoped instruction. No RPR/CPI, matrix, Sapiens2, color, new inference, training or CCTV processing. Frozen config/scorer/adapter/checkpoint/population/ownership/precision/resource policies unchanged. Timing remains unequal adapter diagnostics, no clean parser-only or end-to-end speed ranking.
