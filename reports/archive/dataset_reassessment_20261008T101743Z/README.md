# Human Parsing MHP-v2 Study

**Stage 0A–0D: BLOCKED — waiting for user review. Stage 1 and the full benchmark have NOT started.** MHP-v2 remains the primary dataset. PPSS is paused and its data/reports/manifests were not accessed or changed by this execution.

The current audit inventories 25,403 images and verifies 54,316 per-person parsing planes. Four RGB files cannot be decoded; a selected GT example raises a physical-person ownership warning; 652 validation images have exact decoded-content matches in train. Original files and official splits remain unchanged. Model checkpoint downloads were deferred by the user: **zero actual parser smoke tests**, with no model ranking.

## Stage 0 evidence

- [Feasibility and acceptance gates](reports/STAGE0_FEASIBILITY_REPORT.md): concise evidence and blockers.
- [Dataset audit](reports/MHPV2_DATASET_AUDIT.md): native masks, counts, distributions, overlap and eight real train GT diagnostics.
- [Model compatibility](reports/MODEL_COMPATIBILITY_REPORT.md) and [model registry](provenance/MODEL_REGISTRY.csv): official sources, weight links, licenses, environments and untested inference states.
- [Taxonomy audit](reports/TAXONOMY_AUDIT.md) and [representability matrix](taxonomy/TAXONOMY_REPRESENTABILITY_MATRIX.csv): concepts, ambiguities and unsupported classes.
- [Protocol review](reports/PROTOCOL_REVIEW.md): decisions required before freeze.
- [Final validation](provenance/STAGE0_VALIDATION.json) and [current run](provenance/STAGE0_ACTIVE_RUN.json): executed tests, protected-source comparison and scope.

## Scientific contracts and draft protocol

[STUDY_STANDARD.md](STUDY_STANDARD.md) defines immutable-source and layer boundaries. [EXPERIMENT_PROTOCOL_DRAFT.md](EXPERIMENT_PROTOCOL_DRAFT.md) separates oracle, YOLO-conditioned, native full-frame and future full-frame association systems. [DATA_SCHEMA.md](DATA_SCHEMA.md) defines native lossless outputs and metric aggregation. [Core](taxonomy/COMMON_HP_CORE_DRAFT.yaml) and [extended](taxonomy/COMMON_HP_EXTENDED_DRAFT.yaml) taxonomies remain draft, without a universal leaderboard or frozen mappings.

[Dataset manifest](manifests/DATASET_MANIFEST.json), [training development manifest](manifests/DEVELOPMENT_SET.json), [reserved original validation list](manifests/FINAL_VALIDATION_SET.json) and [exact-content leakage audit](manifests/LEAKAGE_AUDIT.json) preserve split provenance. Training development execution is currently blocked. The final validation split is not used for protocol tuning.

## Environments and external assets

Resolve the workspace from this study's parent. Dataset: `datasets/LV-MHP-v2`; parser source: `third_party/human_parsing`; checkpoints: `models/human_parsing`; isolated environments: `.venvs/mhpv2-stage0` and `.venvs/fashn-stage0`. None of these assets is duplicated inside the study. The existing YOLO environment and frozen YOLO26x checkpoint are preserved.

The FASHN environment passed imports and a synthetic FP32 GPU matrix test; this does **not** establish model/checkpoint inference feasibility. Legacy native parsers remain environment-blocked or deferred. Sapiens2 is license-blocked for the intended surveillance-related work.

[Reproducibility](REPRODUCIBILITY.md) records exact environments, bounded commands and evidence limitations. [References](REFERENCES.md) distinguish official evaluation, research design and source claims. [Study state](STUDY_STATE.json) preserves previous paused-dataset nodes and records the new MHP-v2 gate. Historical landing/state versions are archived before replacement; previous reports are retained.

**Next action: review blockers and approve a bounded continuation. No Stage 1 benchmark, training, fusion or color analysis is authorized.**
