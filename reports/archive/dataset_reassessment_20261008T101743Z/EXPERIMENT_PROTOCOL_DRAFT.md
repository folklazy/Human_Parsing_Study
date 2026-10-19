# Human Parsing MHP-v2 — Experimental Protocol Draft

Version `0.1-DRAFT`. **Not frozen, not executable as a benchmark.** Dataset RGB corruption, GT ownership diagnostics, exact split overlap and unexecuted checkpoint smoke tests currently block Stage 1. PPSS is paused and excluded.

## Inputs and leakage controls

Use the original 15,403 train / 5,000 val / 5,000 test image IDs. Parsing GT exists for train/val; no public test GT is supplied. Development and timing manifests are train-only and currently draft/blocked. Validation decoding/hashing was an integrity audit, not model evaluation or tuning.

Maintain the original validation manifest. Exact train-content reuse is recorded for **652 validation IDs in 628 duplicate groups**. Report official-split results, if eventually authorized, without implying content independence. A separately approved train-overlap-excluded sensitivity result could supplement them; do not silently replace the official split. Removing shared images only from our development sample cannot remove prior checkpoint exposure to duplicated training content. Near-duplicate and external-pretraining reuse remain unverified.

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

Five synthetic fixtures passed through minimally ported official functions. The upstream empty-prediction path raises an IndexError; a reviewed zero-input compatibility fix and broader official/native parity tests are required before a native benchmark. No approximate custom metric is relabeled official.

## Future FP32 timing and memory design

Use the pinned T4 and fixed train timing manifests. Measure independently: parser forward ms/person; parser pipeline ms/person; native full-frame ms/image; integrated end-to-end ms/frame at observed N persons. Do not extrapolate full-frame FPS from single-person latency or mix workloads in one Pareto plot.

Suggested future schedule: 10 warmups and 3 clean measured rounds, synchronized CUDA boundaries, batch 1 unless a separate declared batching track is approved. Monitor contention and defer/mark contaminated rounds without killing other jobs. Record mean, median, SD, P50/P95, allocated/reserved peak VRAM, parameters, checkpoint bytes, resident pipeline memory, actual input resolution and N persons.

Parser pipeline stages: crop construction, native preprocessing, forward, native postprocessing, map-back, ownership/association and composition. Integrated measurements additionally include YOLO, crop preparation and total frame work. Exclude model loading/downloads, visualization and disk serialization unless separately measuring initialization or I/O. Keep native outputs/resolutions; do not surgically remove an internal detector. FP16 is a separately authorized future track, not a fallback for FP32 failure.

## Freeze review requirements

Resolve or explicitly approve a non-destructive handling policy for four unreadable RGB files; confirm selected GT ownership anomaly; disclose/review exact cross-split content reuse; obtain complete candidate weight/use permissions; finish intended-checkpoint FP32 smoke tests; approve cohort taxonomy, crop/matching/ownership rules, score denominators, zero-input native evaluator handling and timing boundaries. Hybrid/complementary-error analysis requires later authorization and real single-parser predictions.
