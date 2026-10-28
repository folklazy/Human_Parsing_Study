# Human Parsing Study

**Current Phase 2–3 planning workspace:** [Human_Parsing_Benchmark](Human_Parsing_Benchmark/README.md) → [STATUS](Human_Parsing_Benchmark/STATUS.md) → [PLAN](Human_Parsing_Benchmark/PLAN.md). **A_REVIEW_COMPLETE / REVIEWED_PROPOSAL**; proposed scope/tasks/selection await user decisions, no implementation or new execution authorized. CCIHP VAL checkpoint selection is permitted by current Prompt A, with no VAL tuning or independent-confirmation claim.

Current proposal: **revision3**, with [specification closure and bounded Stage B handoff](Human_Parsing_Benchmark/reports/HUMAN_PARSING_PROTOCOL_REVIEW_TH.md#i-specification-closure-และ-stage-b-handoff--revision-3). View-specific mappings and evidence, empty-person semantics and application comparison groups are explicit. The [single decision table](Human_Parsing_Benchmark/PLAN.md#11-คำตัดสินคงเหลือ--ชุดเดียวก่อน-bfreeze) remains pending; documentation completeness is not design acceptance or execution readiness. Selected7checkpoints/10configurations are preserved. No Stage B, inference or benchmark started.

The closed first-cohort results and earlier preparation notes below remain historical evidence. The workspace-root Human_Parsing_Benchmark is the canonical editable planning directory; this subdirectory is its reviewed public copy.

## Closed first CPI cohort — historical results

Independent noncommercial student academic research on pretrained body/clothing parsing and supported accessories. Frozen YOLO26x-Seg supplies person opportunities for the first **T3b** cohort; native parsers also infer their own instances. This is a post-run publication snapshot, not the Git revision used at launch.

**Latest run: `first-cohort-benchmark-20261016T094257313856Z` — FINISHED_WITH_INCOMPLETE_SYSTEMS.** No main accuracy winner is available under STRICT_COMPLETE. The two systems remain in every result table; missing main scores are null, never zero.

| Component | Frames | COMPLETE | FAILED | INVALID |
|---|---:|---:|---:|---:|
| YOLO26X_FROZEN | 5,000 | 5,000 | 0 | 0 |
| CPI_R50_CIHP | 5,000 | 4,475 | 525 | 0 |
| CPI_ConvNeXtB_CIHP | 5,000 | 4,959 | 40 | 1 |

The 565 native failures are CUDA OOM; one ConvNeXt-B image is an unresolved interrupted output. Inference was shared across reference **5,000** and main **4,961** memberships; it was not run twice for two tables. Both systems are INCOMPLETE in both populations and at matching IoU 0.50/0.75. This is quality-only: no timing, FPS or VRAM ranking.

## Start here

| Document | Canonical responsibility |
|---|---|
| [REPORT.md](REPORT.md) | Technical account of the completed attempt and retained limitations |
| [RESULTS_SUMMARY_TH.md](RESULTS_SUMMARY_TH.md) | Compact numerical quick summary in Thai |
| [PRESENTATION_SUMMARY_TH.md](PRESENTATION_SUMMARY_TH.md) | Presentation narrative, operational visual evidence and interpretation limits |
| [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | Exact first-cohort procedure and executable authority |
| [DATASET_DETAILS.md](DATASET_DETAILS.md) | Dataset roles, populations, GT domains and taxonomy distinctions |
| [DATA_SCHEMA.md](DATA_SCHEMA.md) | Columns, metric formulas, denominators and missing values |
| [STUDY_STANDARD.md](STUDY_STANDARD.md) | Scientific and operational invariants |
| [HANDOFF.md](HANDOFF.md) / [AGENTS.md](AGENTS.md) | Continuation instructions and prohibited actions |
| [SETUP.md](SETUP.md) / [REPRODUCIBILITY.md](REPRODUCIBILITY.md) | Portable checks versus asset-dependent reproduction |
| [ARTIFACTS.md](ARTIFACTS.md) | Public metadata versus local/restricted assets |
| [History index](reports/HISTORY_INDEX.md) | Current and superseded evidence, without rewriting past knowledge |

## Machine-readable results

- [Quality results](metrics/first-cohort-benchmark-20261016T094257313856Z/QUALITY_RESULTS.csv): 8 rows, all INCOMPLETE with blank main metrics.
- [Failure inventory](metrics/first-cohort-benchmark-20261016T094257313856Z/FAILURES.csv): 566 component-image failure/invalid rows, zero retries.
- [Operational success-only diagnostics](metrics/first-cohort-benchmark-20261016T094257313856Z/OPERATIONAL_SUCCESS_ONLY_DIAGNOSTICS.csv): not main scores and not a ranking on unequal successful populations.
- [Current study state](STUDY_STATE.json), [run manifest](cohorts/first_cpi_t3b/RUN_MANIFEST.json), [model inventory](inventory/MODEL_INVENTORY.csv).
- [Source/config copy manifest](publication/SOURCE_COPY_MANIFEST.json), [benchmark validation](provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/FINAL_BENCHMARK_VALIDATION.json), [server post-export checks](provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z/POST_EXPORT_VERIFICATION.json).

## Reproduction boundary

Clone alone permits the documented portable CPU/synthetic checks and verification of released result summaries. It does **not** provide datasets, checkpoints, native CUDA environments, pixel GT, saved masks/logits or all GT context bindings. See [external artifacts](ARTIFACTS.md). Frozen config flags document the historical approval for this one run; they do not authorize a new run.

No company CCTV, source dataset photos, native model source trees, weights or bulk predictions are included. The small archived CCIHP evaluation-code snapshots retain their MIT notices; see [third-party notices](THIRD_PARTY_NOTICES.md). No new benchmark, download or GPU smoke is performed to prepare this repository.

## Publication

Published **PUBLIC** repository: [folklazy/Human_Parsing_Study](https://github.com/folklazy/Human_Parsing_Study). The approved base `2d78f85b8785e87a568fd6ac8f9e1006a40972b0` and subsequent publication commits are **post-run snapshots**, not launch revisions.

Anonymous README/result/config reads and remote HEAD were verified at the [initial public commit](publication/INITIAL_PUBLICATION_VERIFICATION.json). [Current publication state](publication/PUBLICATION_STATE.json) is separate from the unchanged scientific run status. The canonical research working copy remains `Human_Parsing_MHPv2_Study`; this repository is its reviewed public snapshot, with explicit synchronization instructions in [HANDOFF.md](HANDOFF.md).

## Planning transition — 21 October 2026

The [previous roadmap](reports/PROJECT_ROADMAP_TH_20261020.md) is preserved as **WIP**, not an accepted new experiment. [STATUS](STATUS.json) and [WORK_LOG](WORK_LOG.md) separate historical decisions from the next Prompt A review. The user will supply Prompt A and the current parser list after this preservation step; neither the old 19-candidate roster nor the QANet proposal is automatically the new launch scope. No experiment was resumed. This selected documentation sync does not publish the newer local implementation/config tree.

Native CIHP asset intake (2026-10-28): shared archive extracted on server; [receipt](Human_Parsing_Benchmark/reports/CIHP_NATIVE_ARCHIVE_INTAKE.md). Dataset payloads remain external; no benchmark/protocol changes.
