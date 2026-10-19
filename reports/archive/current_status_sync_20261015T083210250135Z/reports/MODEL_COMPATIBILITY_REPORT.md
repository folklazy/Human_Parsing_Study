# Model Compatibility — Stage 0B/0C

**No intended-checkpoint parser smoke test was run. No candidate is SMOKE_PASS.** The user explicitly deferred large downloads; the MHP RGB/GT review gate is also blocked. This report distinguishes real source/metadata/import tests from unexecuted inference.

## Verified local hardware

NVIDIA Tesla T4, 15,360 MiB total VRAM; 15,360 MiB free and no GPU worker at initial audit. Driver 580.178.04. `nvidia-smi` reports driver CUDA compatibility 13.0; this is not a toolkit check. No `nvcc`/system CUDA compiler was found. GCC 13 is available, RAM 31 GiB with approximately 27 GiB available, and disk approximately 628 GiB free at inspection. [Hardware run record](../provenance/RUN_MANIFESTS/stage0-20261008T063349Z/HARDWARE.json).

Two new isolated environments were actually installed outside the repository: `.venvs/mhpv2-stage0` (Python 3.10.21, NumPy 2.2.6, Pillow 11.3.0, SciPy 1.15.3, PyYAML 6.0.3) and `.venvs/fashn-stage0` (Python 3.12.3, torch 2.14.0+cu130, torchvision 0.29.0+cu130, transformers 4.57.1, OpenCV 4.11.0, safetensors 0.6.2). Torch/CUDA packages were reused from the local uv cache under pinned constraints; the existing YOLO environment was never installed into or changed. FASHN dependency imports, CUDA visibility, T4 compute capability 7.5 and a synthetic FP32 matrix operation passed. That is **not model-load/inference or model peak-VRAM evidence**.

## Primary candidates

| Candidate | Source/checkpoint metadata | Native behavior | Real local status / blockers |
|---|---|---|---|
| M2FP R101 MHP-v2 | Pinned source; public official folder exposes `model_final.pth`, 757,779,078 bytes | Full-image query-based instance parsing; 59 semantic classes plus auxiliary Human | No weights downloaded; Detectron2/MSDeformAttn native stack uninstalled; nvcc absent; no FP32 model test |
| CPI R50 MHP-v2 | Pinned HAG fork; Google Drive `epoch_75.pth` view HTTP 200 | Causal parser with internal Deformable-DETR detection; 59 parsing labels | No weights; legacy native stack not installed; no inference or T4 resource claim |
| CPI ConvNeXt-B MHP-v2 | Separate official model link view HTTP 200 | Same full-frame detection/parsing system | No automatic preference over R50; no actual FP32 memory test |
| Sapiens2-0.4B | License/source metadata pinned; no checkpoint requested | Excluded from execution/cohort pending permission | **LICENSE_BLOCKED_PENDING_CLARIFICATION**; surveillance and related R&D prohibited under current terms |
| FASHN | Pinned source and Hugging Face revision; safetensors HEAD HTTP 200, 256,146,352 bytes; official LFS hash recorded | Semantic image/crop parser, SegFormer-B4, 18 classes, RGB INTER_AREA resize 384×576 W×H, ImageNet normalization, bilinear logits map-back | Environment/import/synthetic GPU PASS; checkpoint absent; adapter implemented but intended-checkpoint smoke NOT_RUN |
| D2FP CIHP / LIP | Official GitHub Releases inspected; full `cihp.pth` / `lip.pth` assets HEAD HTTP 200, ~958 MB each | CIHP instance parsing vs LIP semantic parsing are distinct variants | No weights; native Detectron2/MSDeformAttn/compiler prerequisites unmet; upstream/weight license scope unresolved |
| SCHP-LIP | Canonical source pinned; official LIP Drive page HTTP 200 | Crop semantic baseline; 20 LIP labels; native 473×473 extractor input and BGR normalization | No weights; source imports JIT-build InPlaceABNSync CUDA; nvcc absent; no silent BatchNorm replacement |

Source files are under workspace `third_party/human_parsing/`, not the study. [Exact revisions](../provenance/SOURCE_REVISIONS.json), [registry](../provenance/MODEL_REGISTRY.csv), [checkpoint manifest](../provenance/CHECKPOINT_MANIFEST.json), [environment matrix](../provenance/ENVIRONMENT_MATRIX.csv).

The preferred CPI repository is a GitHub fork of `JosonChan1998/CPI-Parser`; its README and the published paper identify HAG-uestc as the release link. Both lineage and preferred source are recorded, not silently replaced by an arbitrary mirror. [Preferred source](https://github.com/HAG-uestc/CPI-Parser), [paper DOI](https://doi.org/10.1109/TIP.2024.3469579).

D2FP's README references `R-103.pkl` backbone initialization and an outdated `m2fp/` extension path. Actual current source is under `d2fp/`; release parser weights are separate from backbone initialization. Do not report those official parser checkpoints as unavailable or confuse a downloaded backbone with a trained parser. [Official releases](https://github.com/cvlab-yongin/D2FP/releases).

## License eligibility

MHP-v2 project terms permit noncommercial research, subject to stated terms. Frozen YOLO26x uses the existing Ultralytics licensing path (AGPL/enterprise); no closed commercial deployment assurance is inferred. M2FP code is predominantly CC-BY-NC-4.0. CPI code carries Apache-2.0 and the paper describes research release; separate weight-grant scope still needs recording. SCHP code is MIT; no separate weight license was verified. D2FP carries MIT locally but incorporates M2FP code, so inherited restrictions and weight scope must be reviewed rather than assuming MIT clears every component. Public checkpoint links are not a blanket permission grant.

FASHN explicitly inherits NVIDIA SegFormer's noncommercial research/evaluation restriction. It is a research candidate, not an authorized commercial deployment selection. Sapiens2 explicitly excludes surveillance-related research and development, so no downloading/executing its checkpoint occurred. [M2FP license](https://github.com/soeaver/M2FP/blob/main/LICENSE), [FASHN license](https://github.com/fashn-AI/fashn-human-parser/blob/main/LICENSE), [SegFormer terms](https://github.com/NVlabs/SegFormer/blob/master/LICENSE), [Sapiens2 terms](https://github.com/facebookresearch/sapiens2/blob/main/LICENSE.md).

## Training exposure and fairness

M2FP/CPI variants declare MHP-v2 training; exact checkpoint validation/model-selection exposure is not established by source configs. D2FP/SCHP declare CIHP/LIP training and are cross-dataset candidates, not controlled zero-content-exposure models. FASHN's official card declares proprietary FASHN curated fine-tuning data; exact composition and MHP/CIHP content exposure remain UNKNOWN (current V3 correction). No architecture-superiority conclusion is possible from differently trained checkpoints, and exact train/val image reuse in local MHP reinforces the limitation.

## Optional models

QANet, CDGNet and **Renovating** Parsing R-CNN (RP R-CNN) were metadata/README audited with official revisions and checkpoint links recorded. RP R-CNN is not the earlier Parsing R-CNN implementation. None was cloned/installed for inference or added automatically to the roster. Optional metadata does not delay primary resolution. [QANet](https://github.com/soeaver/QANet), [CDGNet](https://github.com/tjpulkl/CDGNet), [RP R-CNN](https://github.com/soeaver/RP-R-CNN).

## Operating-mode eligibility

| Cohort | Candidate role after permissions/smoke | Fairness limitation |
|---|---|---|
| Oracle / YOLO crop semantic | FASHN, SCHP; D2FP-LIP only after crop compatibility | Crop ownership and native single-person distribution must be reviewed |
| Native full-image reference | M2FP, CPI, D2FP-CIHP | Internal query/detection overhead remains in total cost; separate ranking |
| Full-frame YOLO association alternative | Future complete-system proposal | Adds dual processing cost; not implemented or benchmarked |

Adapter schema/export correctness passed synthetic tests. The FASHN adapter retains official preprocessing/native forward/logits interpolation and has a hard 1–3-train-image smoke runner prepared with one optional native-API parity forward; it has not been executed. Other native adapters cannot be honestly marked executable until their stack, permissions and intended weights pass actual tests. No random model or import-only test is labeled SMOKE_PASS.

## Current intended-use reassessment — 2026-10-12

Decision 5A resolves research-scope ambiguity: independent **noncommercial academic research/evaluation**. Use the [component license report](LICENSE_ELIGIBILITY_REASSESSMENT.md), [matrix](../provenance/LICENSE_MATRIX_DECISION5A_V1.csv) and [V3 registry](../provenance/MODEL_VARIANT_REGISTRY_V3.csv) as current eligibility evidence. Earlier paragraphs describe the pre-clarification audit; they do not override the user's clarified scope.

FASHN is research-license compatible, execution approval pending. M2FP/CPI/D2FP/SCHP code is compatible with this scope subject to notices, while applicability to selected weights remains separately documented/pending; absence of a separate weight license is uncertainty, not a universal prohibition. Sapiens2 remains explicitly license-blocked for surveillance-related research. No checkpoint downloaded, loaded or inference passed; FP32 T4 feasibility remains NOT_TESTED for every checkpoint. D2FP LIP release-config metadata corrected in V3 only. Native/crop cohorts and ownership policies remain draft.
