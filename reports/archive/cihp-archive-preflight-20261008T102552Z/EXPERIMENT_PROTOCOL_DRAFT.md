# Human Parsing MHP-v2 — Experimental Protocol Draft

Version `0.2-DRAFT`. **Not frozen, not executable as a benchmark.** Readable-view preparation is approved and completed; dataset-role selection, GT-quality review, exposure disclosure, candidate permissions and unexecuted checkpoint smoke tests still block Stage 1. PPSS is paused and excluded.

## Inputs and leakage controls

Use the original 15,403 train / 5,000 val / 5,000 test image IDs. Parsing GT exists for train/val; no public test GT is supplied. Development and timing workloads remain train-only and draft; use approved readable input IDs where applicable, without authorizing inference. Validation decoding/hashing was an integrity audit, not model evaluation or tuning.

Maintain the original validation manifest. Exact train-content reuse is recorded for **652 validation IDs in 628 duplicate groups**. Report official-split results, if eventually authorized, without implying content independence. The user-approved exact train-overlap-controlled readable population is prepared for a future separately reported sensitivity result; do not silently replace the official split. Removing shared images only from our development sample cannot remove prior checkpoint exposure to duplicated training content. Near-duplicate and external-pretraining reuse remain unverified.

## Native GT and coordinates

Read native PNG indices with the official first-channel rule. Preserve each `imageID_totalPersons_personFileID.png` independently; no global semantic flattening. Background is 0; native semantic IDs are 0–58; alpha 255 is not void. Adapter-created padding void is a separate provenance field.

Canonical derived bboxes are half-open `[x1,y1,x2,y2)` in original RGB coordinates. Categorical GT uses nearest resampling only if a separately declared transformation requires it. Native GT is otherwise unresized. Pose `person_0…` is a separate namespace; do not assume a numeric parsing/pose join. A supplied parsing filename is not proof of correct ownership in every annotation.

## Track A — ORACLE_PERSON

GT source geometry → one globally declared expanded crop → compatible semantic parser. Proposed margin is 10% of bbox dimensions, clipped to the image, **pending train-only review**. Original RGB values inside the crop are preserved; no irreversible hard mask. GT defines geometry only, not class labels/foreground supplied to the parser. Log every crop, expansion, resize and padding transform.

Use a body/clothing-support crop proposal rather than blindly including an umbrella or carried object in an anatomical bbox. Compare alternative geometry only as predeclared development ablations; parsing metrics still include the stated full native/common semantic support.

## Track B — YOLO26X_CONDITIONED

Full RGB → frozen YOLO26x → predicted person geometry → eligible crop parser. Frozen weight SHA256 is recorded in [YOLO26X_SOURCE.json](manifests/YOLO26X_SOURCE.json). YOLO input size, threshold/NMS/maxDet and crop expansion require a versioned application protocol; do not claim the MOTS20 settings automatically define MHP-specific choices.

Report detection coverage, conditional parsing on matched persons, missed-person parsing, unmatched-prediction burden and target ownership separately. Missed GT persons contribute explicit all-background prediction planes to coverage-aware scores. Unmatched predictions remain false-person/error outputs; do not omit them from every system metric. No weighted combined score is proposed.

## Track C — NATIVE_REFERENCE

M2FP/CPI and compatible D2FP variants operate in documented full-image mode. Preserve internal query/detection inference and native instance scores. This reference cohort is separate from YOLO-conditioned crop systems. Official-style AP^p/PCP requires original-coordinate per-person semantic maps and native confidences. Semantic crop outputs with no native person confidence cannot be silently promoted into official native-instance results.

## Track D — FULL_FRAME_INTEGRATION_ALTERNATIVE

Design only: full image feeds frozen YOLO and a native multi-human parser independently, followed by deterministic person association. Preserve unmatched outputs and account for both systems' detection/query cost. Compare complete configurations on a common output task, not as interchangeable parser-only architectures. No fusion/integration implementation or benchmark is authorized here.

## Matching and ownership proposal

For study-specific detector association, use original-grid body/clothing-support mask IoU on an explicitly valid domain. Draft threshold is 0.5; freeze it from train development, not validation. Compute one-to-one matching by maximum eligible cardinality, then total IoU, with dummy unmatched assignments. Sort IDs and pin SciPy for reproducible ties; record tie ambiguities. Report an all-native-foreground association sensitivity only if approved, because accessories can change IoU.

Keep overlap planes intact. Neither overlap alone nor GT-file identity guarantees a corrupt/correct annotation. The `train/9968` anomaly requires ownership review.

Crop parsing can include neighbors. Preserve raw semantic predictions and separately derive a proposed YOLO-mask ownership view after parsing; pixels claimed by target and neighbors remain ambiguous. Report native foreground outside target support, ambiguous overlap and missing ownership support. Deployment ownership uses only YOLO geometry/native predictions, never GT-guided person selection. GT-guided ownership belongs only to an explicitly named oracle diagnostic. A policy that restricts ownership can discard valid clothes/accessories, so it must not be presented as an unconditional quality improvement.

## Common and native metrics

Common global mIoU uses one accumulated confusion matrix over stated class/domain projections; foreground primary score excludes background. Per-person macro mIoU first computes each GT person's supported-class IoU, then averages defined person values. They are distinct metrics. Zero unions are undefined, not perfect scores; include GT and prediction support. Ignore only an approved common valid domain. Unsupported GT is never background. Explicit UNMAPPED predictions remain counted in GT support and are reported as a separate burden; the final background-hallucination penalty policy is still open.

Body/clothing/footwear/accessory scores average supported per-class IoUs within predeclared groups and disclose support/coverage. They are semantic analysis groups, not preassigned parser-expert roles. Dice, pixel accuracy, boundary and person-size metrics are secondary definitions needing approval; no unsupported boundary-score implementation is claimed.

The inspected official v2 AP^p implementation confidence-ranks person parsing predictions, selects GT using mean class IoU including background with undefined classes omitted, uses **strict `>`** thresholds, and marks duplicate GT matches as FP. PCP divides successfully parsed foreground parts by GT-present parts and adds zeros for missed people. AP-volume averages thresholds 0.1…0.9 in later native implementations; version-specific parity must be verified before labeling a result official. This differs from study-specific mask-IoU detector matching.

The original upstream empty-prediction path remains unchanged. A separate pinned compatibility wrapper now passes 19 synthetic evaluator tests, including nine-threshold AP-volume, native confidence/matching, duplicates, overlap and zero support. All 51 contract/evaluator/population tests pass. Nonempty cases delegate the original evaluator functions; no-GT is undefined and all-missed supported GT gives zero. Published-result and CIHP-specific official parity remain unclaimed.

## Future FP32 timing and memory design

Use the pinned T4 and fixed train timing manifests. Measure independently: parser forward ms/person; parser pipeline ms/person; native full-frame ms/image; integrated end-to-end ms/frame at observed N persons. Do not extrapolate full-frame FPS from single-person latency or mix workloads in one Pareto plot.

Suggested future schedule: 10 warmups and 3 clean measured rounds, synchronized CUDA boundaries, batch 1 unless a separate declared batching track is approved. Monitor contention and defer/mark contaminated rounds without killing other jobs. Record mean, median, SD, P50/P95, allocated/reserved peak VRAM, parameters, checkpoint bytes, resident pipeline memory, actual input resolution and N persons.

Parser pipeline stages: crop construction, native preprocessing, forward, native postprocessing, map-back, ownership/association and composition. Integrated measurements additionally include YOLO, crop preparation and total frame work. Exclude model loading/downloads, visualization and disk serialization unless separately measuring initialization or I/O. Keep native outputs/resolutions; do not surgically remove an internal detector. FP16 is a separately authorized future track, not a fallback for FP32 failure.

## Freeze review requirements

Use the approved readable views with named denominators; confirm selected GT ownership anomaly; disclose/review exact cross-split content reuse; obtain complete candidate weight/use permissions; finish intended-checkpoint FP32 smoke tests; approve cohort taxonomy, crop/matching/ownership rules, score denominators, zero-input native evaluator handling and timing boundaries. Hybrid/complementary-error analysis requires later authorization and real single-parser predictions.

## Dataset populations and role selection amendment

CIHP is a candidate primary and MHP-v2 provisional secondary; no final role freeze or shared universal score is authorized. CIHP is absent locally: source taxonomy/archive metadata are not a GT-quality audit. Inspect native Human_ids versus part Instance_ids and preserve original pixel semantics before adopting any reader.

MHP full official validation target: 5,000 images / 13,260 native persons; official-split readable: 4,999 / 13,257. Exact train-overlap-controlled target: 4,348 / 11,411; controlled readable: 4,347 / 11,408. Train readable: 15,400 / 41,043. Keep each manifest and exposure/duplicate warning explicit. Do not present unreadable subsets as unqualified full official scores or merge scores across populations/datasets.

Random/stratified GT review belongs to TRAIN; final validation integrity/leakage audits are read-only and do not authorize threshold/taxonomy/crop tuning. Quality failures remain reported, with no silent source repairs or favorable class denominators. Company CCTV remains unlabeled and untested; quantitative field testing needs a separately approved annotation/evaluation design.

See reports/STAGE0_NEXT_ACTIONS.md for bounded acquisition/checkpoint proposals. Neither the readable policy nor evaluator tests authorize Stage 1, parser inference, downloads or field testing.
