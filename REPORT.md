# First CPI T3b Cohort — Technical Report

## Status and scope

`first-cohort-benchmark-20261016T094257313856Z` is **FINISHED_WITH_INCOMPLETE_SYSTEMS**. This describes terminal execution and reporting, not successful accuracy completion. Both CPI systems are INCOMPLETE in main/reference at IoU0.50/0.75. No main quality winner exists.

The objective is pretrained body/clothing parsing conditioned by frozen YOLO opportunities, without training or validation tuning. [Protocol](EXPERIMENT_PROTOCOL.md), [dataset/domain](DATASET_DETAILS.md) and [schema](DATA_SCHEMA.md) are canonical for those topics.

## Observed execution

| Component | Frames | COMPLETE | FAILED | INVALID |
|---|---:|---:|---:|---:|
| YOLO26X_FROZEN | 5,000 | 5,000 | 0 | 0 |
| CPI_R50_CIHP | 5,000 | 4,475 | 525 | 0 |
| CPI_ConvNeXtB_CIHP | 5,000 | 4,959 | 40 | 1 |

565 CUDA OOM failures and one unresolved interrupted native output remain in the [failure CSV](metrics/first-cohort-benchmark-20261016T094257313856Z/FAILURES.csv). Main complete frames are R50 **4,436/4,961** and ConvNeXt-B **4,920/4,961**; all 566 noncomplete component-images belong to main as well as reference. No population was altered based on these outcomes.

## Canonical score tables

[QUALITY_RESULTS.csv](metrics/first-cohort-benchmark-20261016T094257313856Z/QUALITY_RESULTS.csv) contains exactly 8 rows: two systems × two populations × two matching views. Main metrics are blank CSV fields / JSON null, with `main_score_eligible=false` and `status=INCOMPLETE`. Null does not mean zero accuracy. The four explicitly derived compact views retain all denominators and failure diagnostics:

- [Main primary](cohorts/first_cpi_t3b/reports/MAIN_PRIMARY_REPORT.json), [main secondary](cohorts/first_cpi_t3b/reports/MAIN_SECONDARY_REPORT.json).
- [Reference primary](cohorts/first_cpi_t3b/reports/REFERENCE_PRIMARY_REPORT.json), [reference secondary](cohorts/first_cpi_t3b/reports/REFERENCE_SECONDARY_REPORT.json).

[Success-only diagnostics](metrics/first-cohort-benchmark-20261016T094257313856Z/OPERATIONAL_SUCCESS_ONLY_DIAGNOSTICS.csv) are conditional on different successful subsets, and cannot replace primary scores or rank the two systems. No new per-target score table is invented: the released aggregate reporter did not publish a completed-population target leaderboard; hard-label predictions and detailed scoring evidence stay external.

The original report JSONs contain bulk operational stage ledgers and remain external. [PUBLIC_REPORT_VIEWS.json](publication/PUBLIC_REPORT_VIEWS.json) records original and public hashes and verifies that score, population and execution fields are unchanged. Compact views replace only the bulk diagnostic block; they are not original canonical files.

## Interpretation and limitations

**Observation:** Native FP32 paths encountered different numbers of OOM failures under their declared, different native score thresholds. YOLO completed every input. **Interpretation:** These are configuration/resource feasibility findings, not evidence of semantic accuracy or backbone causality. A successful three-image TRAIN smoke did not certify completion on every validation input.

This is custom CCIHP coarse body/clothing evaluation, not official CIHP AP or mIoU. Mapping remains ACCEPTED_WITH_INDIRECT_EVIDENCE. Training exposure differs across inventory checkpoints. Controlled membership is not universal leakage clearance; released GT is not complete physical-person truth. No significance, CCTV robustness, tracking, latency/FPS/VRAM winner or commercial deployment conclusion is made.

## Integrity and provenance

[Server final validation](provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/FINAL_BENCHMARK_VALIDATION.json) and [independent export checks](provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/POST_EXPORT_VERIFICATION.json) verify rows/bindings, retained 566 failure records, null main metrics, 126 protected-file hashes and unchanged YOLO repository statuses. Archived CPU application tests passed **151**; that is not a claim that 151 portable tests run from a public clone or that inference completed successfully.

The [dated executed report](reports/FIRST_COHORT_T3B_BENCHMARK_REPORT_TH_20261019.md) is retained unchanged. [Run manifest](cohorts/first_cpi_t3b/RUN_MANIFEST.json) distinguishes original V11 freeze, V12 infrastructure restoration, source/checkpoint/environment hashes and the later public Git snapshot. [Reproducibility](REPRODUCIBILITY.md) lists missing external assets and tested clean-checkout boundaries.

## Visual and presentation evidence

[PRESENTATION_SUMMARY_TH.md](PRESENTATION_SUMMARY_TH.md) explains operational visual evidence without duplicating this numerical table. Actual dataset photos and saved-mask overlays are not redistributed without verified image/annotation rights; no synthetic image is substituted for benchmark visual evidence.

## Stop condition

This run is closed. A resource correction, new precision, inference retry or broader roster is a new configuration/authorization decision. No further experiment starts automatically.
