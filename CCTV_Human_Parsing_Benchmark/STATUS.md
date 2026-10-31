# Current CCTV partial benchmark

Updated 2026-10-31T18:28:18.826756+00:00 UTC. **9/9 COMPLETE**; active worker none.

Blocked resource: none. No automatic model/OOM retries.

[Results](reports/RESULTS_TH.md) / [Protocol](PROTOCOL.md). Partial annotations: full-imageIoU/personF1/overallwinner not identifiable. Private run `cctv-partial-20261031T1800Z`; `outputs/<run>/CURRENT_WORKER.json` and `<model>/STATE.json` show live progress; filesystem report is current, GitHub updates only after explicit sync.

## Metric review

Audit complete: accepted90IDs×9models/810atomic score records reconcile; three bounded saved-mask replays pass, no new model calls. [Metric audit report](reports/CCTV_METRIC_AUDIT_TH.md) adds explicitly restricted-domain IoU/Dice diagnostics. Full-image IoU/personF1 remain unestablished; known-negative/annotation-scope QA is still required. Original run and canonical metrics unchanged.
