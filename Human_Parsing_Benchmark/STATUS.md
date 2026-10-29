# Human Parsing Benchmark — current status

Updated: 2026-10-29T22:10:38.229214+07:00 (Asia/Bangkok)

**CPI_CONVNEXT_PREPARING_MANUAL_CONTINUATION** — latest user requests CPI after GPU became free. [Current attempt](reports/cpi-convnext-idle-gpu-20261029T151038229214Z.md) / [authorization](runs/cpi-convnext-idle-gpu-20261029T151038229214Z/AUTHORIZATION.json).

Sapiens2 0.4B and 0.8B are each COMPLETE 5,000/5,000: [0.4B/cohort report](reports/CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md), [0.8B report](reports/CIHP_SAPIENS_08B_C4P_RESULTS_TH.md). Their predictions/results are preserved. Four original native CIHP and saved-only common evaluations are complete and will not be rerun.

CPI ConvNeXt-B previous canonical segment had 145 verified successes; new controller must reconcile artifacts before reuse/pending counts are authoritative. CPI R50 remains paused. This attempt uses the frozen native CIHP20 scientific protocol, not C4-P. STRICT_COMPLETE main scores remain null until exact 5,000 IDs pass. One manual attempt only, no automatic model/OOM retries/fallback/next model; timing/resource observations are diagnostics only. Existing shared-quality authorization applies, other resource guards unchanged.

Read-only progress after launch:
```bash
.venvs/parser-legacy-cu113/bin/python Human_Parsing_Benchmark/scripts/run_cpi_continuation.py --model convnext --status --watch
```

Next: reconcile, start only ConvNeXt-B in a detached process if bindings/guards pass, confirm first packet, then allow controller to finish or stop on error. No R50/1B/training/color/CCTV.
