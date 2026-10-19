# Public Data Schema — First CPI T3b Cohort

UTF-8 CSV with one header; JSON null and empty CSV metric cells mean unavailable, never fabricated zero. This publication schema documents existing fields and adds navigation; it does not change source result files. [Historical schema](reports/archive/pre_public_snapshot/DATA_SCHEMA.md) is preserved.

## QUALITY_RESULTS.csv

Key: `(system_id,population,matching_view)`; 8 unique rows. `system_id` names a configured parser system, `population=main|reference`, `matching_view=primary|secondary`, `IoU_threshold=0.50|0.75` (bbox, fraction). `status=INCOMPLETE`, `main_score_eligible=False` in every current row.

`frames`: fixed image denominator. `G_loc`: eligible GT localization persons; `G_sem`: eligible semantic persons, subset of G_loc. `frames_complete`, `frames_failed`, `frames_invalid`, `frames_not_attempted` sum to `frames`. Completion is assessed separately per system and population; two matching views do not duplicate inference.

Main metric columns are `Q_person_sem_GT,TP,FP,FN,localization_recall,localization_precision`; all blank for current INCOMPLETE rows. For an eligible complete population, TP/FP/FN are one-to-one final bbox matches/unmatched persons; recall=TP/G_loc and precision=TP/(TP+FP), undefined when the denominator is zero. Counts are integers; ratios are fractions 0–1. FP is unmatched relative to released annotations, not proof that a physical person does not exist.

## Person semantic metric

For each semantically eligible matched GT person, the accepted GT-derived domain supplies a confusion matrix with an extra UNMAPPED-prediction error column. For each foreground class with GT support, IoU=TP/(GT support+prediction support−TP). The person's IoU is the mean over its fixed GT-supported foreground classes. `Q_person_sem_GT = sum(matched eligible GT person IoUs) / G_sem`; unmatched G_sem persons contribute zero. Undefined absent-GT support remains null. It is not pooled global mIoU or official AP. See [actual evaluator](src/application_v2/evaluation.py), [score boundary](src/application_v2/scoring.py) and [aggregation](src/application_v2/comparison.py).

## OPERATIONAL_SUCCESS_ONLY_DIAGNOSTICS.csv

Same system/population/view keys. `label=SUCCESS_ONLY_DIAGNOSTIC_NOT_MAIN_SCORE`, `scored_frames`, observed `G_loc/G_sem`, conditional Q and TP/FP/FN describe only successfully scored frames. Different successful populations prohibit treating these as main scores or ranking systems. Undefined values stay blank/null.

## FAILURES.csv

One unique `(component,image_id)` per native failure/invalid event; 566 rows. Fields: `component,image_id,status,failure_stage,failure_kind,error_last_line,retries,source_ledger`. `failure_kind=CUDA_OOM|UNRESOLVED_INTERRUPTION`, `retries=0`; source ledger paths identify external immutable originals. A failure event does not independently add FN again; no operational-empty fallback is the primary policy.

## Native prediction and context interfaces

Native per-person integer grids, boxes/scores, original W/H, source/crop transforms, checkpoint/source/adapter/config/input hashes and separate native/YOLO identities are specified by [contracts.py](src/application_v2/contracts.py) and frozen [V12](configs/application_v2_first_cohort_v12.yaml). Categorical resizing is nearest-neighbor; metric truth is lossless, never a colored/JPEG overlay. Native identity unsupported→null; supported but no instance→0. Stage rates carry stage/unit/numerator/denominator and return null on zero denominator; routing skips differ from failures.

Mapping [V3](taxonomy/APPLICATION_BODY_CLOTHING_CPI_ACCEPTED_V3.json) keeps GT VOID outside the shared denominator, while unmapped predictions cannot create favorable GT void. Global known-target/owner-unknown pixels and per-person void are distinct. Background0, ignore/void and unsupported concepts must not collapse. Numeric source IDs are taxonomy-specific.

## Inventory and provenance

[MODEL_INVENTORY.csv](inventory/MODEL_INVENTORY.csv) is not a leaderboard. Download status, local file integrity, architecture load, bounded native inference, historical pilot, canonical export, use restriction and full-cohort completion are independent fields. Local SHA256 identifies local bytes; publisher authenticity is NOT independently verified without an upstream digest. Source hashes and config freezes predate public Git; Git commit/tag is publication provenance only.

Detailed GT/person bindings, 10,000 primary and secondary frame score journals, arrays and ledgers are external. Their absence in a clone must not be replaced with invented values. [ARTIFACTS.md](ARTIFACTS.md) describes access.

## Compact public report views

`cohorts/first_cpi_t3b/reports/*.json` use `COMPACT_DERIVED_VIEW_1.0`: the exact original score/status/execution/population/success-only fields are preserved, while `operational_diagnostics` is replaced by `operational_diagnostics_summary`. `publication_derivation` identifies the external original SHA256 and bytes. This is not a re-scored or overwritten canonical report. [View provenance](publication/PUBLIC_REPORT_VIEWS.json) records both byte hashes.

The preserved V3 mapping also contains the older generic `benchmark_eligible:false` field. Current first-cohort acceptance/scoring is bound by the accepted config/decision, cohort support and context checks; this generic field is not the runtime authorization gate. Publication preserves its original bytes and does not use it to authorize any new run.
