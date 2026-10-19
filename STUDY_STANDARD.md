# Human Parsing Study — Current Scientific Standard

This document governs the current first-cohort record. Earlier Stage 0 standards are preserved [byte-identically](reports/archive/pre_public_snapshot/STUDY_STANDARD.md). They must not override later accepted, hash-bound decisions.

1. Original datasets, the completed YOLO study, weights and working environments are immutable.
2. Runner/evaluator values come from [configs/application_v2_first_cohort_v12.yaml](configs/application_v2_first_cohort_v12.yaml), bound to [provenance/APPLICATION_V2_DECISIONS_V11.json](provenance/APPLICATION_V2_DECISIONS_V11.json). File version numbers alone are not evidence of acceptance. Original V11 launch and V12 detector-infrastructure restoration freezes are separate from any Git snapshot/tag.
3. Scope is exactly CPI_R50_CIHP and CPI_ConvNeXtB_CIHP plus frozen YOLO26x, T3b FP32. Reference 5,000 inference jobs per component support separate main 4,961 and reference 5,000 reports. No post-hoc membership changes.
4. STRICT_COMPLETE requires full eligible-population completion for main metrics. INCOMPLETE rows and operational diagnostics stay visible. Valid empty output is successful execution and incurs the applicable GT misses. No failed-image retries were authorized.
5. Native identity and YOLO opportunity identity remain separate, and T3b records retain both. A semantic adapter's final person output does not establish native instance capability. Unsupported native count is null; a supported empty count is zero.
6. Prediction-only association IoU 0.50 is distinct from final prediction-to-GT bbox matching 0.50/0.75. GT never conditions parser inference or deployment ownership.
7. Mapping confidence remains ACCEPTED_WITH_INDIRECT_EVIDENCE, not DIRECT_VERIFIED. Unsupported GT is not silently background; known-target/owner-unknown pixels can contribute globally but are void per person.
8. Source track, model/checkpoint/config, input geometry, taxonomy, GT domain and population bindings must be explicit. Retain native hard labels losslessly; logits are unavailable unless actually exported.
9. No tuning on validation. Quality-only findings cannot support FPS/VRAM rankings, architecture causality, statistical significance, CCTV robustness, tracking performance or deployment readiness.
10. Preserve failed/interrupted records and historical reports. Scoped continuation/restoration is not a general certified workflow-resume or cached-rescoring feature.
11. A public Git snapshot created after execution is not a launch commit. Human review of independent annotation quality is distinct from automated integrity checks and assistant visual inspection.
12. A new configuration, precision, population, inference pass, model download, training, hybrid or CCTV experiment requires separate explicit authorization. This repository grants none.

Dataset, person sources, adapters, canonical prediction records, taxonomy, evaluator, resource measurement and interpretation remain separate layers. [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) is the procedure; [DATA_SCHEMA.md](DATA_SCHEMA.md) is the interface.
