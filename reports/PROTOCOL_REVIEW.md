# Protocol Review — Decisions Required Before Stage 1

**Stage 1 freeze: BLOCKED pending scientific decisions, not blanket absence of downloaded weights.** STRICT_COMPLETE primary reporting and checkpoint-specific cohort membership are accepted with conditions; this does not accept real-data mapping/domain/population/matching/runtime. See [current first-cohort evidence](FIRST_COHORT_CONDITIONAL_POLICY_REVIEW_TH_20261015.md). Current model status: [compatibility report](MODEL_COMPATIBILITY_REPORT.md), [registry V6](../provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv). PPSS is paused; its license or reports are not prerequisites. This document records decisions for review, not permission to execute them.

| Issue | Actual evidence | Recommended next decision | Current gate |
|---|---|---|---|
| Four RGB failures | Strict Pillow and OpenCV fail; original SHA256/headers retained | Prefer independently verified source replacements kept as a separate version; otherwise approve/disclose an explicit non-destructive failure/exclusion policy | Approved versioned readable views prepared; original files/splits unchanged; no automatic repair |
| Native ownership | `train/9968_02_01.png` labels both adults in a selected example | Verify source/author annotation intent; retain anomaly and quantify only a separately justified screen | Ownership not guaranteed by filename |
| Train/val exact reuse | 652 val IDs share exact decoded content with train | Preserve official result population; consider separately approved overlap-controlled sensitivity and disclosure of native-checkpoint exposure | No content-independent validation claim |
| Checkpoints | Current registry V6: native smokes exist for 21 checkpoints/components; CDGNet now downloaded and tensor-inspected | Review actual route/capability before cohort readiness; no duplicate acquisition | Native passes do not authorize full benchmark |
| Native CUDA stacks | Existing isolated legacy stack executed the recorded native smokes; user-space toolchain and restored PATH used | Retain tested environment/profile; no system driver/toolkit changes | Per-model evidence in current compatibility report |
| License scope | User confirmed Decision 5A noncommercial academic research; FASHN matches research terms | Record code/weights/dependency/dataset terms separately; selected legacy-weight applicability pending | Scope ambiguity RESOLVED; execution permissions still candidate-specific |
| Sapiens2 | Current license prohibits surveillance-related R&D | Exclude unless verifiable applicable permission is obtained | LICENSE_BLOCKED_PENDING_CLARIFICATION |
| Taxonomy | Fine/native labels and coarse/ambiguous parser capacity differ | Approve explicit cohorts and common denominators, not one misleading global score | DRAFT |
| GT geometry | Full parsing foreground includes carried items; pose IDs/order differ | Review shared body/clothing-support geometry and an all-support sensitivity | DRAFT |
| Crop ownership | Semantic crop can include neighbors | Approve a deployment-available post-parsing ownership/ambiguity policy; keep raw outputs | DRAFT |
| Native evaluator edge | Upstream empty prediction bug preserved; separate wrapper passes 19 synthetic tests | Retain wrapper/reference separation; verify broader published/native parity before freeze | Wrapper preparation PASS; official benchmark parity not claimed |
| Timing | Native/crop/integrated workloads differ | Approve stage boundaries, N-person workloads, FP32 and resident memory reporting | DRAFT; no latency result |

The plan's strongest features are layer separation, train-only development, native-mode reference cohorts, honest failed-candidate states and refusal to assume hybrid superiority. The audit demonstrates why these gates matter: extraction success is not RGB readability, numeric mask fidelity is not physical-person ownership, and split-ID disjointness is not image-content independence.

Study-specific evaluator tests cover perfect/wrong labels, missing/duplicate/swapped persons, overlapping masks, ignore/absent classes, unsupported labels, dimensions and coordinate/ownership failures. Native-function fixtures cover only a limited synthetic subset; they do not prove complete official AP^p/PCP parity. Boundary metrics and deployable ownership effectiveness remain protocol proposals, not tested model claims.

Later Stage 1 should be an off-the-shelf **system/candidate** comparison, not a controlled architecture experiment. MHP-trained and cross-dataset parsers have different exposure. Native/full-frame and YOLO/crop cohorts must remain separate until a complete-system common-task evaluation is explicitly authorized. Hybrid routing, oracle ceilings and deployable fusion must also be distinguished and separately authorized.

**Next action: review the blockers and approve only the next bounded corrective/feasibility step. Do not start Stage 1 or a full benchmark.** No owner-contact message, remote repository, model ranking or color/attribute work was created.

## Scope decision recorded — 2026-10-12

See [Decision 5A](../RESEARCH_SCOPE.md) and [license reassessment](LICENSE_ELIGIBILITY_REASSESSMENT.md). Commercial deployment is out of scope; company CCTV data supply does not establish product R&D. No repeat approval is needed for the scope or previously approved readable-view policy. FASHN checkpoint download/smoke remains unapproved; its bounded proposal can proceed independently of CIHP native GT once specifically authorized. Other scientific decisions, human GT review and dataset rights remain open. PPSS remains paused.
