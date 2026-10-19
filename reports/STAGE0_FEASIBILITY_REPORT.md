# Human Parsing MHP-v2 — Stage 0A–0D Evidence Summary

> Current update — 15 October 2026: the body below is the historical initial audit. Current acquisition/inference status is in [Model Compatibility](MODEL_COMPATIBILITY_REPORT.md), [current artifact index](../provenance/CURRENT_STUDY_ARTIFACTS.json), and [handoff validation](APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md). Old zero-checkpoint/zero-smoke statements are historical; scientific taxonomy acceptance remains pending.

## Historical initial-audit evidence

**Overall: BLOCKED — Stage 0 audit executed; Stage 1 is NOT authorized.** This is an actual dataset/source/contracts audit, not a completed parser benchmark. The user chose source/dataset/tests first and deferred large downloads. No parser checkpoint was downloaded, loaded or inferred. No candidate earns `SMOKE_PASS`.

## Acceptance gates

| Gate | Result | Evidence / practical limit |
|---|---|---|
| A — Workspace preservation | See [final validation](../provenance/STAGE0_VALIDATION.json) | Compare six YOLO repositories, frozen YOLO26x SHA256 and recorded environment metadata before/after; PPSS paused without accessing its files |
| B — Dataset | BLOCKED | 25,403 images inventoried; four required RGB inputs fail both Pillow and OpenCV; all 54,316 native person planes decoded and round-tripped losslessly |
| C — Models | BLOCKED / DEFERRED | Official sources/checkpoint links and licensing audited; zero downloaded checkpoints and zero actual parser smoke tests |
| D — Architecture | DRAFT; synthetic contract tests pass | Base adapter, native lossless prediction export and FASHN adapter implemented; FASHN dependency imports and synthetic FP32 GPU operation pass, but intended checkpoint execution is untested |
| E — Taxonomy | DRAFT | 472 representability entries (59 concepts × eight candidate variants); no universal comparable body/clothing score frozen |
| F — Evaluation | Partial verification; native parity BLOCKED | 25 study-specific unit tests pass; five official-function fixtures pass; source function fails on zero predictions; AP^p_vol and full native parity not established |
| G — Protocol | DRAFT awaiting decisions | Oracle, YOLO-conditioned, native-reference and full-frame association alternative designed with explicit ownership, coverage, timing and leakage policies |
| H — Scope | See final preservation/scope checks | No full benchmark, training, fusion, colors, PPSS activity or YOLO inference/results changes |

## Dataset: observed facts

Canonical physical root is `datasets/LV-MHP-v2` relative to the workspace. Train/validation/test contain **15,403 / 5,000 / 5,000** images. Train/validation contain **41,056 / 13,260** per-person parsing files; test GT is not supplied and is not counted as corruption. Native labels are background 0 plus 58 foreground categories. RGBA PNG labels reside in the first channel; alpha 255 is not an ignore map. Palette PNG indices are preserved. Person identities remain separate; numeric pose IDs are not assumed to identify the corresponding parsing person.

**Required RGB failures:** train `1396`, `18613`, `24328`; validation `17844`. Their exact bytes/hashes remain unchanged. The audit attempts all inputs but cannot claim all RGB inputs are readable. **100,134 source files** have SHA256 records; the inventory file digest is `2864eea092e7424d80aa6241100243b31dd6f7f3214eba7f040b8094df6f5822`. The historical import reports successful archive CRC, but CRC success does not establish image decoding. Original download URL and current official ZIP byte equivalence remain unverified.

**Leakage:** 628 exact decoded-content groups span train and validation, affecting 652 validation IDs. Original split lists remain unchanged. There is no claim of content-independent validation or zero checkpoint exposure. A separately approved sensitivity cohort would supplement, not replace, official reporting.

**GT warning:** in training image `9968`, the selected native person-1 plane visibly includes regions at both adults. Pixel conversion fidelity passes, while physical-person ownership needs review. This is one observed anomaly, not a measured dataset-wide error rate, and legitimate overlap is not automatically corruption.

Eight deterministic train-only GT diagnostic cases were generated and visually inspected. All native/canonical selected planes match exactly; seven cases have limited visual alignment checks, and `9968` retains the ownership warning. [Dataset audit](MHPV2_DATASET_AUDIT.md) contains statistics, source paths, hashes and images.

## Model feasibility: actual status

| Candidate | Verified evidence | Remaining blocker |
|---|---|---|
| M2FP R101 MHP-v2 | Pinned official source and MHP checkpoint link; native multi-human query parser | Weights deferred; Detectron2/MSDeformAttn stack absent; no nvcc; weight-use terms require review |
| CPI R50 / ConvNeXt-B MHP-v2 | HAG fork lineage, two checkpoint pages and native detection/parsing source verified | Weights deferred; legacy MMDetection/MMCV stack untested; native checkpoint FP32 memory unknown |
| Sapiens2-0.4B | Official source revision and license inspected | `LICENSE_BLOCKED_PENDING_CLARIFICATION`: surveillance-related R&D restriction; not downloaded/executed |
| FASHN | Official 18-class source, pinned HF revision/LFS hash and 256,146,352-byte expected checkpoint verified; isolated imports and synthetic T4 FP32 check pass | Actual checkpoint absent; model load, dimensions/class IDs/map-back and model VRAM untested; research terms do not establish commercial permission |
| D2FP CIHP / LIP | Official parser release assets verified; these are not backbone weights | Weights deferred; native CUDA stack absent; upstream/license scope review; cross-dataset taxonomy |
| SCHP LIP | Official source, LIP checkpoint page, 20 labels and 473×473 native mode verified | Weights deferred; legacy InPlaceABNSync CUDA compilation; do not substitute standard BN silently |

QANet, CDGNet and RP-R-CNN received metadata/source/checkpoint-link review only; no optional installation or inference occurred. See the [candidate registry](../provenance/MODEL_REGISTRY.csv) and [compatibility report](MODEL_COMPATIBILITY_REPORT.md) for variants, source commits, training exposure and separate verification states.

## Executed tests and reproducibility

- Exhaustive image/annotation attempts, source SHA256 inventory and all 54,316 native annotation round-trips.
- **25 passing synthetic unit tests**: decoding, identities/overlap, confusion/aggregation, missing/duplicate persons, valid/ignore domains, ownership, crop coordinates and lossless prediction contract.
- **Five passing limited official-function fixtures**; **one separately documented upstream empty-prediction failure**. These are synthetic inputs, not validation-set evaluation.
- Isolated environment imports and **synthetic** FP32 matrix operation on Tesla T4 pass. This is not parser inference or a performance benchmark.
- Source/weights/environment manifests distinguish verified source metadata from local downloaded bytes and actual inference. FASHN's expected LFS SHA256 is not represented as a measured local checkpoint SHA256.

The GPU observed was Tesla T4, 15,360 MiB, driver 580.178.04. Tested isolated Torch is 2.14.0+cu130; compiler `nvcc` is absent. Driver-advertised CUDA compatibility is distinct from installed runtime and compiler availability. The previous YOLO environment was not modified. See [reproducibility](../REPRODUCIBILITY.md), [final validation](../provenance/STAGE0_VALIDATION.json) and [run evidence](../provenance/STAGE0_ACTIVE_RUN.json).

## Decision and next action

The plan's layer separation and native/crop cohorts are appropriate. The audit adds three essential review gates: **RGB readability despite successful extraction; physical ownership despite file-level identity; content leakage despite disjoint official IDs.** A narrow universal face/hair intersection would not answer the body/clothing objective; richer, explicitly comparable cohorts are needed.

**No model is presently verified ready for Stage 1.** Potential next feasibility candidates are FASHN (lowest environment barrier), CPI-R50/M2FP (native MHP reference) and SCHP-LIP (cross-dataset crop baseline), conditional on dataset/license/environment/weight gates. ConvNeXt-B and D2FP remain candidates to verify, not exclusions based on performance. Sapiens2 remains license blocked.

Review the [protocol decisions](PROTOCOL_REVIEW.md) before approving a bounded corrective/feasibility continuation. Dataset originals, official splits and checkpoints remain unchanged. Do not start Stage 1. **WAIT FOR USER APPROVAL.**
