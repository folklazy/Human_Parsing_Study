# Human Parsing Study — Stage 0

**Dataset reassessment preparation: PASS_WITH_WARNINGS. Overall Stage 0: BLOCKED / WAITING_FOR_USER_APPROVAL. Stage 1 and benchmarks: NOT STARTED.**

CIHP is a **candidate primary** public body/clothing benchmark; MHP-v2 is a **provisional secondary** fine-grained benchmark. Roles and COMMON_HP are not frozen. PPSS remains paused; CCIHP/color/attributes are out of scope. Company CCTV images remain reserved for a later finalist field test. The existing directory/study ID is retained to preserve provenance.

## Research scope and current license decision — 2026-10-12

**Decision 5A: NONCOMMERCIAL ACADEMIC RESEARCH / EVALUATION.** Independent student study; company CCTV is future research evaluation data, not proof of commercial sponsorship. [Scope](RESEARCH_SCOPE.md), [Decision 5A license review](reports/LICENSE_ELIGIBILITY_REASSESSMENT.md), [license matrix](provenance/LICENSE_MATRIX_DECISION5A_V1.csv).

FASHN research terms are compatible, but checkpoint download/inference is **not authorized yet**. Other released candidates retain separate code/weight applicability records; Sapiens2 remains surveillance-research license-blocked. [Bounded FASHN proposal](manifests/FASHN_SMOKE_PROPOSAL_V2.json): 256 MB checkpoint, combined cap 300 MB, 1–3 readable train images, no new dependency installation. No checkpoint inference, validation benchmark or CCTV execution has occurred.

## Current evidence and decisions

- [Dataset reassessment](reports/DATASET_REASSESSMENT.md): completed bounded preparation, exact populations and limitations.
- [CIHP availability / quality audit](reports/CIHP_QUALITY_AUDIT.md): DatasetNinja archive present and audited; native Human GT missing, full quality and dataset permission pending.
- [MHP-v2 quality risks](reports/MHPV2_QUALITY_RISK_REVIEW.md): reuse, ownership uncertainty and independent train review.
- [Primary dataset decision](reports/PRIMARY_DATASET_DECISION.md): evidence matrix and provisional A direction, without claiming CIHP is cleaner.
- [Next bounded actions / approvals](reports/STAGE0_NEXT_ACTIONS.md): CIHP acquisition, research-only FASHN smoke proposal and open scientific decisions.
- [Current preflight validation](provenance/CIHP_ARCHIVE_PREFLIGHT_VALIDATION_V1.json), [prior reassessment validation](provenance/DATASET_REASSESSMENT_VALIDATION.json), [51 executed tests](provenance/RUN_MANIFESTS/dataset-reassessment-20261008T095241Z/BOUNDED_TESTS_V2.json), [study state](STUDY_STATE.json).

## MHP-v2 readable views

Original data/splits remain unchanged. Train readable: **15,400 / 41,043 native GT persons**. Official-split readable validation: **4,999 / 13,257**. Exact train-overlap-controlled readable validation: **4,347 / 11,408**. Full official and controlled targets are retained separately. Readable-subset scores must disclose excluded files and denominators; no validation inference has run.

[Readable policy / fingerprints](provenance/MHPV2_READABLE_POLICY_V1.json), [official target](manifests/mhpv2_readable_v1/VALIDATION_OFFICIAL_TARGET.json), [readable validation](manifests/mhpv2_readable_v1/VALIDATION_READABLE.json), [controlled target](manifests/mhpv2_readable_v1/VALIDATION_OVERLAP_CONTROLLED_TARGET.json), [controlled readable view](manifests/mhpv2_readable_v1/VALIDATION_OVERLAP_CONTROLLED_READABLE.json).

Thirty independently sampled readable train images have native GT diagnostics and a [human checklist](reports/MHPV2_RANDOM_QUALITY_REVIEW_V1.csv), still pending. Pixel fidelity is verified; semantic ownership/error prevalence is not established. [CIHP's 200-image review V2](manifests/CIHP_QUALITY_REVIEW_PLAN_V2.json) waits for native human GT, with no fabricated person strata.

## Contracts, environments and candidate metadata

[Scientific standard](STUDY_STANDARD.md), [draft tracks](EXPERIMENT_PROTOCOL_DRAFT.md), [schema](DATA_SCHEMA.md), [taxonomy audit](reports/TAXONOMY_AUDIT.md), [core](taxonomy/COMMON_HP_CORE_DRAFT.yaml) and [extended](taxonomy/COMMON_HP_EXTENDED_DRAFT.yaml) retain layer/cohort separation. [CIHP concept proposal](taxonomy/CIHP_COMMON_HP_PROPOSAL_V1.yaml) is not an executable mapping.

[Current variant registry V3](provenance/MODEL_VARIANT_REGISTRY_V3.csv) (V2 retained as historical evidence) distinguishes backbones, dataset weights and training schedules. There are **zero downloaded/loaded/smoke-passed parser checkpoints**. FASHN environment imports and a historical synthetic T4 FP32 check are not checkpoint inference. Sapiens2 remains excluded from surveillance-related execution pending applicable permission.

Shared assets stay outside the study: workspace `datasets/`, `models/human_parsing/`, `third_party/human_parsing/`, `.venvs/`. The YOLO environment, benchmark repositories and frozen YOLO26x checkpoint are preserved. No heavyweight packages/weights/datasets downloaded in this continuation; only bounded source/HTML metadata was fetched. No Git remote created or push performed.

## Historical evidence

[Original Stage 0 gates](provenance/STAGE0_VALIDATION.json), [feasibility report](reports/STAGE0_FEASIBILITY_REPORT.md), [original dataset audit](reports/MHPV2_DATASET_AUDIT.md), [raw dataset manifest](manifests/DATASET_MANIFEST.json), [model registry V1](provenance/MODEL_REGISTRY.csv), [original leakage audit](manifests/LEAKAGE_AUDIT.json) and [ZIP verification](reports/MHPV2_NEW_ZIP_RGB_VERIFICATION.md) are preserved. Their historical raw-data blockers are not rewritten as repaired inputs; current approved views and wrapper evidence supersede specific policies, without altering historical results.

[Archive/hash record](provenance/DATASET_REASSESSMENT_DOCUMENT_REVISIONS.json), [reproducibility](REPRODUCIBILITY.md) and [references](REFERENCES.md) support traceability. **STOP: wait for approval before acquisition, checkpoint execution, Stage 1 or any field test.**

## CIHP archive preflight — current evidence

[Focused report](reports/CIHP_ARCHIVE_PREFLIGHT_AUDIT.md): local converted TAR SHA256 and all member inventory; 38,280 RGB/JSON pairs, 768,446 part bitmaps validated; 20 strict JPEG sample decodes; five official semantic demo matches. Original human-instance ownership data is absent, so native person GT readiness is **BLOCKED** despite file/bitmap integrity PASS. 39 exact train–val JPEG-byte duplicate groups; full leakage/quality review pending. **60 bounded tests passed; zero model inference.**

[Archive manifest](manifests/CIHP_DATASETNINJA_ARCHIVE_MANIFEST_V1.json), [preflight JSON](provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json), [duplicate evidence](provenance/CIHP_DATASETNINJA_BYTE_DUPLICATES_V1.json), [revision/archives](provenance/CIHP_PREFLIGHT_DOCUMENT_REVISIONS_V1.json). No full extraction, native dataset download, primary promotion or Stage 1 authorization. Native GT supplement and Full Quality Audit require the next review decision.
