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
