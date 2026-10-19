# Model Compatibility — current evidence, 15 October 2026

**Native technical evidence exists; no final benchmark or universal READY roster is declared.** Current [registry V6](../provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv) records checkpoint acquisition, actual native execution, canonical export, historical pilot evidence and use eligibility separately.

CPU regression: 138 tests passed in the [dated validation](../provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/validation_20261015T071746Z/VALIDATION.json). The last handoff executed FP32 on one fixed CCIHP TRAIN image per eligible checkpoint/component: 21 native passes. This status synchronization executes no models.

| Family | Actual technical evidence | Important operating-mode / readiness limit |
|---|---|---|
| FASHN B4 | Actual FP32 native smoke PASS; prior YOLO-conditioned bounded integration retained | Semantic parser; external YOLO/oracle identity is not native identity |
| M2FP R101 LIP / CIHP / MHP-v2 | 3 native checkpoint smokes PASS | LIP semantic mode versus CIHP/MHP multi-human mode must remain separate |
| CPI R50 / ConvNeXt-B, CIHP / MHP-v2 | 4 native smokes PASS; 8 T1/T3B canonical packets verified | T3B uses fresh parser plus saved verified YOLO; joint live runtime not certified; earlier R50-CIHP crowded-frame OOM warning retained |
| D2FP R101 CIHP / LIP | 2 native smokes PASS | Native instance versus semantic modes differ |
| SCHP LIP / ATR / Pascal | 3 native smokes PASS | Oracle-crop semantic tests, not native instance identity |
| SCHP CIHP global/local | 2 component smokes PASS; auxiliary detector downloaded | Full detector/global-local multi-person pipeline NOT_TESTED |
| QANet CIHP R50 / HRNet-W48 and LIP HRNet-W48 two resolutions | 4 native smokes PASS | Oracle proposal geometry; not detector-conditioned deployment proof |
| RP-R-CNN CIHP / MHP-v2 | 2 native smokes PASS | Internal detection cost remains part of native behavior |
| CDGNet R101 LIP | Downloaded; 603 finite FP32 tensor entries; 20-class head structurally verified | Architecture load / GPU inference / canonical adapter NOT_TESTED; prior code-license grant unresolved |
| Sapiens2 0.4B / 0.8B / 1B | Historical 10-image technical pilots recorded; 1B includes offload-control warning | Not re-executed in latest handoff; intended-use eligibility is separate from technical feasibility |
| Sapiens2 5B | Existing checkpoint retained | Excluded from execution by user due to resources; no new test |

27 unique checkpoint artifacts are catalogued, including one auxiliary detector and parser components; this is not the number of comparable standalone systems. [Current inventory](../provenance/CHECKPOINT_INVENTORY_CURRENT_V1.json). CDGNet trained weights came from the Google Drive folder linked by its official README, which also contains a separate ImageNet initializer. [Acquisition and inspection](CDGNET_ACQUISITION_TH_20261015.md).

No dependency reinstall was required to restore the tested legacy stack: source/toolchain/environment evidence is in the [handoff report](APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md). Sapiens permission questions and model-resource feasibility remain separate; downloading a checkpoint does not itself resolve use restrictions.

All model weights and environments remain outside the study. Scientific mappings/populations/matching/failure policy are still pending acceptance; full benchmark remains false. [Current protocol decisions](PROTOCOL_REVIEW.md) and [policy detail](APPLICATION_HANDOFF_POLICIES_TH_20261015.md).

The previous report describing zero downloaded weights was a dated Stage0B/0C snapshot; its byte-identical version is [archived](../reports/archive/current_status_sync_20261015T083210250135Z/reports/MODEL_COMPATIBILITY_REPORT.md), not treated as current execution status. Prior license/source evidence remains under its original manifests.
