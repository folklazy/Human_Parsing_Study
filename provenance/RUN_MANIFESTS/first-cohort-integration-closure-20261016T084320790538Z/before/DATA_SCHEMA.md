# Human Parsing — Application Output Schema V2

## Current scoring and acquisition contracts — 16 October 2026

- Current evidence navigation: [CURRENT_STUDY_ARTIFACTS](provenance/CURRENT_STUDY_ARTIFACTS.json). This index does not authorize execution; runner values remain in accepted-bound executable config.
- `ConfiguredRunner.score_frame` and `score_person_result` share `scoring.score_frame`; absent/unaccepted context blocks scoring. Mapping fingerprint, checkpoint/config/head/native class order, support policy, accepted GT domain and evaluation-bbox provenance are checked before matching.
- `evaluate_persons(..., original_wh=[W,H])` validates every emitted integer semantic grid, unique identity and finite score even for unmatched/empty-GT cases. G_sem must be a subset of G_loc. Original W/H must come from trusted input evidence, not inferred from predictions.
- `conditioning_bbox` is separate from `evaluation_bbox={xyxy, source, coordinate_convention, derivation_revision}`. Only the configured evaluation source is used for scoring.
- Numeric mapping V2 requires `native_taxonomy` for prediction projection. CIHP10 Torso-skin and LIP10 Jumpsuits are distinct. The CPI-only V3 bundle is accepted under the explicit indirect-evidence policy; the historical V2 and retained LIP projection remain draft outside that accepted cohort. LIP does not support the exposed-torso target.
- Execution/acquisition dimensions are independent: downloaded, SHA256 verified, tensor-inspected, architecture-loaded, inference-passed, canonical-export-passed and intended-use eligibility must not collapse into one READY flag. CDGNet currently has acquisition/tensor inspection evidence only. Historical Sapiens technical runs remain separate from current intended-use eligibility; 5B remains excluded from execution for resources.
- Cached scoring and workflow resume are NOT_IMPLEMENTED/DISABLED. Packet hash/finalization/fingerprint validation is an artifact helper, not full workflow certification. Hard labels do not support probability aggregation.
- STRICT_COMPLETE is accepted as the primary run-level policy with retained INCOMPLETE rows and operational diagnostics. Operational-empty fallback is not the primary score. The first CPI cohort's five policies and converging-evidence mapping policy are accepted. Six TRAIN contexts are materialized; full validation packages are materialized/validated but execution activation and fresh execute readiness remain pending. Failure events never independently add localization FN penalties.

## Accepted CPI evidence policy and saved TRAIN route — 16 October 2026

[Config V8](configs/application_v2_first_cohort_v8.yaml) binds the five policies and the explicit evidence-policy revision in [decision V7](provenance/APPLICATION_V2_DECISIONS_V7.json). Neither grants scientific freeze or full-benchmark authorization.

`first_cohort.channel_order_evidence.accepted_statuses` distinguishes `DIRECT_VERIFIED` (official header/creator order) from `ACCEPTED_WITH_INDIRECT_EVIDENCE` (project-accepted paper/release/config/numeric-source/TRAIN-review chain). Indirect records require the declared policy ID, checkpoint/source/class-order binding and five hash-bound components. A status string alone is insufficient. Historical V7 remains direct-only; user acceptance does not fabricate a training header.

Contexts set `require_channel_order_evidence=true`, the exact accepted confidence-policy list and checkpoint-specific support. `support_binding.status=VERIFIED` refers to structural/hash bindings; `semantic_review=ACCEPTED_WITH_INDIRECT_EVIDENCE` preserves semantic provenance limitations. Unobserved/incorrect predictions do not create an all-class accuracy requirement.

The entry point requires explicit `--config` and either `--dry-run` or `--saved-train-replay`. V8 selects only `first_cohort.models` / `execution_spec`, runs no model and supports saved TRAIN lifecycle→association→native packet export. Cached model score thresholds must match the declared runtime settings; no threshold is applied again to retained predictions. `semantic_scoring_enabled=false` rejects scoring even though six TRAIN contexts are bound. Cached semantic scoring/workflow resume remain disabled; this route is artifact/lifecycle replay only.

Owner-unknown known-target pixels remain valid globally and VOID per person. Numeric target1 retains its source identifier and displays as **Face region**. See [current acceptance report](reports/CPI_STANDARD_MAPPING_ACCEPTANCE_AND_TRAIN_REPLAY_TH_20261016.md).

## Earlier first-cohort proposal and context scope — 16 October 2026

[Config V6](configs/application_v2_first_cohort_v6.yaml) preserves the pre-acceptance `first_cohort.protocol_proposal` submission and [decision V5](provenance/APPLICATION_V2_DECISIONS_V5.json). Current policy acceptance is in V8/V7 above; the historical submission did not authorize scoring or a benchmark.

A shared `mapping_sha256` fingerprints the complete versioned mapping bundle; native projections within it may differ. The first CPI pair both use the CIHP projection, with separate checkpoint/config bindings. Arbitrary per-checkpoint mapping files remain outside this implementation's scope.

`domain` contains common policy metadata plus optional `image_binding`. Registry validation compares the policy separately from the image binding. When `first_cohort.require_per_image_GT_domain_binding=true` (V6), each context requires image ID, G_loc/G_sem and `GT_domain_recipe_sha256` equal to the other systems' binding for that image. Different images may have different dimensions, domains and GT counts. The recipe fingerprints source maps, GT projection and domain policy; it is not a decoded-mask hash. GT reconstruction must separately verify those source hashes and transformation fidelity before accepted-context use. See [first-cohort approval package](reports/FIRST_COHORT_T3B_APPROVAL_PACKAGE_TH_20261016.md).

## Per-system/image scoring context registry — 16 October 2026

Optional `scoring_contexts[system_id][image_id]` replaces the single context for multi-system/multi-image reporting. It requires an accepted `SCORING_CONTEXTS` decision binding both the full registry and `scoring_population` (ordered image IDs and G_loc/G_sem). Single and registry contexts cannot coexist. V8 binds six actual TRAIN contexts only; semantic scoring is explicitly disabled. Main/reference validation packages are materialized and registry-validated, but not activated by the current executable config.

Every system must cover the exact predeclared population. Model bindings stay fixed per system; verified input bindings agree per image across systems. Mapping, GT domain, target-support policy, threshold, evaluation geometry source and failure policy are common to the comparison. Checkpoint-specific support remains mandatory. Native taxonomy may differ only within the explicitly supported mapping/cohort contract.

Configured scoring requires explicit system/image IDs and exports both identities with the context digest. Reporting checks this binding and the accepted population; it rejects score reuse across rows and post-hoc population reduction. Registry fields affect scoring fingerprints only; absent fields preserve existing packet fingerprints. Synthetic temp-file acceptance tests do not accept real-data contexts. See [current context closure evidence](reports/FIRST_COHORT_CONTEXT_CLOSURE_TH_20261016.md).

## Conditional policy update — 15 October 2026

`comparison.summarize_comparison` reports every predeclared system and final-frame denominator. Incomplete populations have `main_metrics=null` and status `INCOMPLETE`; successful frames are separately labeled diagnostics. Complete execution without an accepted scoring context is `BLOCKED_SCORING_POLICY`. Valid empty output remains successful execution with GT-dependent misses.

`ConfiguredRunner.comparison_report` requires eligible metrics to carry the accepted context digest. Comparison IDs bind population, view/track/mapping and reporting policy. The configured runner rejects post-load config mutation. Checkpoint-specific `support_binding` requires checkpoint/config/source/class-order/target/mapping fingerprints and reviewed semantic evidence; a dataset name is insufficient.

Prediction-only association is in `first_cohort.draft_association`; final GT matching is in `evaluation`. Their fingerprints are distinct. The latest V5 packets are derived from retained actual V4 detector/parser outputs, not new GPU inference or production cached scoring. Original packets and configs remain immutable.

## Active executable schema / accepted decisions

The application V2 validator is [contracts.py](src/application_v2/contracts.py); current config authority is [application_v2_first_cohort_v8.yaml](configs/application_v2_first_cohort_v8.yaml), linked by canonical-content digest to [decision V7](provenance/APPLICATION_V2_DECISIONS_V7.json). Accepted bindings cannot be overridden by prose. Mapping and GT-sidecar byte hashes are checked independently. Six TRAIN contexts exist; scoring/fresh model execution/full benchmark remain disabled in this preparation entry point.

Native first-cohort checkpoints/config/settings and resolved native score thresholds now enter inference fingerprints; evidence confidence and context changes remain scoring dependencies. Existing historical packet records are immutable, not rewritten to a new fingerprint revision.

Each final person retains an `identity` record:

| Origin | native_identity_supported | native_instance_id | conditioning_source / source_opportunity_id |
|---|---|---|---|
| NATIVE_MODEL | true | native ID | null / null |
| YOLO_CONDITIONED | false | null | YOLO / opportunity ID |
| ORACLE_INPUT | false | null | ORACLE / input ID |
| NATIVE_AND_YOLO | true | native ID | YOLO / opportunity ID |
| NATIVE_AND_ORACLE | true | native ID | ORACLE / input ID |

`final_person_id` is required separately. Complete native inventory is retained even when T3b gates instances out. Unsupported native count serializes as `{value: null, status: N/A_UNSUPPORTED}`; supported empty inventory has `{value: 0, status: DEFINED}`. Assigning a YOLO/oracle ID never gives a semantic parser native instance capability.

Canonical V2 packet uses ORIGINAL-grid N×H×W integer `canonical_semantic_masks`, explicit native/common label catalog and separate lossless native arrays. JSON retains exact model commit/checkpoint, system/model/run IDs, geometry, precision, input/config hashes and inference/scoring fingerprints. `NATIVE_OWNERSHIP_DERIVED` distinguishes post-parser ownership view from raw native masks. Common/native-owned target-empty final views retain a truthful native-foreground provenance flag; all-background native output cannot fabricate a final person.

Native scores may be null; conditioning score is separately named. No unsupported probability is invented. Native arrays and crop outputs remain available for remapping; metric truth is not a rendered image. The validator rejects wrong grids, invalid IDs, identity disagreement and inconsistent native capability.

## Execution, failure and artifact schemas

Every stage rate contains `stage`, `unit`, `numerator`, `denominator`, `value`, `status`, `skipped_by_routing`. Zero eligible units → null/undefined. Eligibility comes from the declared policy, never successful execution. Failure events retain affected units and distinguish MODEL_SYSTEM_FAILURE, INVALID_ENV and UNRESOLVED_EVENT; external/unresolved events invalidate the operational trial. Parser completion, native foreground, final emission and target availability are independent quantities.

Packets have `arrays.npz`, `record.json`, `COMMITTED.json`. Atomic single-writer publication refuses overwrite. Resume checks byte hashes, schema and inference fingerprint. Changed scoring config permits only explicit re-scoring from sufficient native outputs; it does not rewrite historical run results. Config and implementation snapshots are preserved separately from completed outputs.

## GT sidecars and scoring

GT `person_key` contains dataset/split/image/native identity; source annotation references/hashes and native masks are preserved. `G_loc_structural_draft` is geometry eligibility, not certification of physical identity. `G_sem_native_known_draft` and `G_sem_common_candidate_draft` are explicitly separate, mapping-dependent support flags. Source and overlap-controlled populations remain separate.

Application evaluator matches all eligible G_loc once, then scores G_sem. UNMAPPED predictions are an error column, unsupported GT follows a shared draft void policy, and known neighboring persons remain negative pixels in per-person views. GT-supported semantic IoU, full-catalog foreground quality and global accumulated-confusion metrics have distinct names and denominators. Fixed scored class sets are independent of model success. These functions do not redefine official MHP AP/PCP.

[Current implementation report](reports/APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md) records tests and readiness limits. Full benchmark, new datasets/metrics and production readiness are not authorized by this schema.

---

## Retained Stage 0 schema history

The sections below describe existing V1 artifacts and historical audit schemas. Historical model download statuses are interpreted at the time of those records, not as current pilot status.

# Human Parsing MHP-v2 — Data Schema Draft 1.0

## Dataset manifests and GT index

[DATASET_MANIFEST.json](manifests/DATASET_MANIFEST.json) identifies the dataset root relative to the workspace, version, official source, actual splits, content inventory, per-person GT index and descriptive support. SHA256 inventory records `{path, bytes, sha256}` as deterministic JSONL; the inventory digest hashes those exact lines. No hash is written to original data.

GT-index rows retain `split`, original `image_id`, RGB path/hash/dimensions and independent `persons` arrays. Each person has filename-native ID, canonical ID `image:parsing:person`, annotation path/hash, native array hash, class support, full parsing foreground and draft body/clothing support. Bboxes are half-open original-coordinate rectangles. Native per-person masks are read by source reference and checked SHA256; overlap is never flattened. Pose metadata has separate keys and no assumed ID correspondence.

`class_pixels_per_person_planes` counts pixels over individual GT planes; overlaps and each person's background are independently counted. These are not global scene frequencies. Test person counts are unknown/unannotated, not zero actual people. Diagnostics/statistics are **derived from existing GT**, not model results.

## Canonical prediction contract

Implementation: [prediction.py](src/contracts/prediction.py). Required fields include schema/study/run/model IDs, source commit, checkpoint SHA256, track, image ID, original and native input W×H, crop coordinates, native label IDs, native predicted person IDs when available, source-person ID, ownership status, transforms, precision/environment, dataset manifest hash, native scores and logit availability.

Canonical `native.npz` contains integer `native_semantic_maps` of shape N×H×W on the declared original/crop output grid and optional finite `native_logits` of shape N×C×H×W on that same export grid. Logit availability must agree with the actual artifact. Native model-input geometry is retained separately; exact source Git SHA, positive integer dimensions and unique native labels/identities are validated. Load with `allow_pickle=False`. The JSON export hashes its array artifact. An unsupported confidence is `null`; no pseudo-score is fabricated. Semantic crop source identity is not a native predicted instance or ownership guarantee. Native results remain separate from draft common projections.

## Metric primitives

For fixed K classes and approved domain V, `C[i,j]` accumulates GT i and prediction j over V. A K+1-th prediction column records UNMAPPED; it is not an ignored GT denominator. Class IoU is TP/(GT support + predicted support − TP). Dice is 2TP/(GT support + predicted support). Zero denominator is undefined; internal per-class NaN must be serialized as null/blank in future metric writers, never a perfect value. Foreground mIoU excludes class 0; global and person-macro aggregations use separate names.

Matching results contain `(gt_index, prediction_index, mask_iou)`, unmatched GT and unmatched prediction lists. Stable source identities are sorted before assignment. Missing GT persons remain in coverage-aware parsing denominators. Raw unsupported GT must be projected under an approved shared policy or rejected, never silently mapped to background.

Native AP^p/PCP and common IoU have different matching/scoring semantics. Refer to the [protocol](EXPERIMENT_PROTOCOL_DRAFT.md) and [official fixture evidence](provenance/OFFICIAL_METRIC_FIXTURES.json); full native parity is not established by Stage 0 fixtures.

## Model/environment/run provenance

[MODEL_REGISTRY.csv](provenance/MODEL_REGISTRY.csv) separates source, link, download, load, GPU inference, canonical export and precision status. [CHECKPOINT_MANIFEST.json](provenance/CHECKPOINT_MANIFEST.json) distinguishes expected official LFS hashes from measured local hashes; absent local weights have null SHA256. Environment import/synthetic CUDA success is not model inference success.

Every actual run records source/config/input/hardware/environment fingerprints, start/end, outputs and failure diagnostics under `provenance/RUN_MANIFESTS/`. Draft configs/manifests authorize no full evaluation.

## Readable-population and reassessment schemas — v1

`manifests/mhpv2_readable_v1/` separates full targets and readable views. Each contains population/policy version, official split, ordered IDs and ID digest, RGB source hashes, native GT counts, explicit exclusion reasons, upstream manifest/index/evidence hashes, scope flags and score limitations. Per-person source annotation/array hashes resolve through the immutable canonical GT index. These are views, not modified original splits.

`MHPV2_RANDOM_QUALITY_REVIEW_V1.json` records seed, sampling frame/probability and draw order before viewing GT. Each diagnostic records source and output hashes. Human-review CSV status remains pending until actual reviewer decisions; numerical grid fidelity is distinct from physical-person correctness. CIHP review plan has no fabricated image IDs or measured quality fields while acquisition is pending.

`official_mhp_compat.py` pins both official evaluator and VOC helper hashes. Its fractional outputs record GT/prediction support, threshold, wrapper/source version and defined/undefined status. Zero GT support serializes as null; AP-volume averages nine fresh reference calls. No learned confidence or GT-guided prediction is manufactured. These tests are synthetic, not final dataset results.

`MODEL_VARIANT_REGISTRY_V2.csv` separates backbone capacity, dataset-specific weights and training schedules. Provider checkpoint bytes are metadata, local weight SHA256 is NOT_DOWNLOADED, and no import success is a checkpoint smoke pass. Current validation is separate from immutable historical Stage 0 validation.

## CIHP DatasetNinja archive preflight — v1

`CIHP_DATASETNINJA_ARCHIVE_MANIFEST_V1.json` records archive size/SHA256, member inventory/digest and split image IDs, annotation counts and part-object counts. Part-object IDs and Supervisely numeric class IDs are not person/native semantic IDs. `CIHP_ARCHIVE_PREFLIGHT_V1.json` separates all-member payload/bitmap integrity, header-grid checks, bounded strict JPEG loading, 5 source-fixture semantic parity, full split verification scope and missing native human GT.

`cihp_datasetninja.py` decodes alpha support from base64(zlib(PNG)) and explicit origin. Native concepts use reviewed converter title mapping; no Human=20 GT class. Semantic reconstruction is a derived diagnostic with explicit overlap/overwrite counts and unknown original void fidelity, not lossless per-human GT. It never manufactures person IDs. `CIHP_DATASETNINJA_BYTE_DUPLICATES_V1.json` records exact file-byte groups/IDs only; no automatic exclusions or decoded/near-duplicate equivalence claim.
