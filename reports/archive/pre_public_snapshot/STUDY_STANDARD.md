# Human Parsing MHP-v2 — Scientific Standard

Version: `0.2-DRAFT`, Stage 0 only. **Stage 1 is not authorized.** The completed YOLO study, its measurements, environment and frozen `models/yolo26x-seg.pt` are immutable. PPSS is paused and is neither an input nor a prerequisite for this work.

## Layer separation

| Layer | Responsibility | Invariant |
|---|---|---|
| L0 | Original MHP-v2 and official lists | No edits, inferred repairs, moves or global-mask replacement |
| L1 | Per-person GT/source geometry | Preserve parsing-file identity, overlap, source dimensions and hashes; keep pose identity separate |
| L2 | Native model adapters | Native preprocessing/architecture; no evaluator, fusion or GT class injection |
| L3 | Prediction contract | Lossless native planes and declared transforms; confidence/logits only when supported |
| L4 | Taxonomy | Draft, checkpoint-specific representability and shared cohort domains |
| L5 | Evaluation | Model-independent primitives; native and custom metrics named separately |
| L6 | Timing/resources | Separate manifests/workloads/precision; no accuracy-smoke ranking |
| L7 | Interpretation | Evidence and limitations; no architecture-causality or CCTV-superiority claim |

GT foreground includes associated accessories/carried objects; it is not an anatomical silhouette. The current draft body/clothing localization support uses native IDs 1–38, 57–58 and excludes other accessory/carried support. It is not frozen. Original labels are always retained for parsing evaluation.

## Governance and stop gates

Required decoding failures block use of the affected samples. The user-approved versioned readable views preserve originals and explicitly record exclusions/denominators. Bounded feasibility on verified readable TRAIN samples is scientifically independent of final benchmark readiness, but model licenses and execution approval are still required. Known content overlap and ownership anomalies must be reviewed before a final independent-validation claim. File decoding fidelity does not prove semantic ownership correctness. Missing public test GT is expected, not corruption.

Source/link/import/checkpoint-load/GPU-inference/contract-export states are separate. Only intended-checkpoint inference permits `SMOKE_PASS`. Unverified weight permissions block the affected execution; deployment permission is distinct from research permission. Sapiens2 is excluded while surveillance-related permission is not applicable/verified.

All checkpoint/environment assets live outside the study, under workspace `models/`, `third_party/` and `.venvs/`. Existing environments remain unchanged. No large download occurs after the user's explicit decision to defer it.

Use fresh run directories, atomic output publication and content fingerprints. Archive replaced active evidence; never rewrite historical attempts. Record failures, input IDs, source/config/environment versions and output hashes. Do not create a remote repository or push without explicit authorization.

## Scope

No full benchmark, validation-set model testing/tuning, training, fine-tuning, hybrid fusion, color study or tracking. Stage 0 concludes with independently assessed gates and `WAITING_FOR_USER_APPROVAL`; a blocked gate is not renamed PASS to meet a schedule.

## Dataset reassessment amendment — 2026-10-08

Do not assume MHP-v2 must remain primary. CIHP is candidate primary; MHP-v2 provisional secondary; roles are not frozen. PPSS remains paused, CCIHP is future color/characteristics work, and unlabeled company CCTV is reserved for later authorized finalist field testing.

Keep full official and exact-overlap-controlled targets separate from their readable views. No source image/GT/list repair or deletion. A 4,999-image score must identify the readable subset; overlap-controlled sensitivity is a separate benchmark condition and does not guarantee content/pretraining independence.

File decode and lossless-coordinate fidelity do not prove GT physical ownership. Independent randomized/stratified quality samples retain uncertain outcomes; purposive anomaly examples do not estimate prevalence. No annotation relabel/exclusion beyond approved unreadable views without a documented decision.

Native and common-class metrics remain separate; dataset-specific raw mIoU scores are not pooled. The official evaluator compatibility wrapper is separate, pinned and synthetic-tested. Empty predictions with positive GT support give zero AP/PCP; zero GT support is undefined. Nine-threshold AP-volume is explicitly reference-derived; synthetic parity does not establish published-benchmark or CIHP evaluator parity.

## Research scope amendment — Decision 5A, 2026-10-12

Current intended use is **NONCOMMERCIAL ACADEMIC RESEARCH / EVALUATION**, explicitly confirmed by the user. Company CCTV provision is later student evaluation data, not evidence of commercial R&D or product deployment. Commercial use requires a separate future license review. [Scope](RESEARCH_SCOPE.md), [component license assessment](reports/LICENSE_ELIGIBILITY_REASSESSMENT.md).

Academic scope does not override license restrictions. FASHN matches inspected research/evaluation terms, but checkpoint download/inference still requires explicit authorization; Sapiens2 remains blocked for surveillance-related research absent applicable permission. Preserve code/weight/dependency/dataset eligibility separately. Dataset roles, taxonomy and protocol remain draft; no benchmark/CCTV/Stage 1 authorization is implied. Existing approved readable TRAIN views permit independent feasibility preparation, not automatic model execution.
