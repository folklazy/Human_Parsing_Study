# Protocol Review — Decisions Required Before Stage 1

**Stage 1 freeze: BLOCKED.** PPSS is paused; its license or reports are not prerequisites. This document records decisions for review, not permission to execute them.

| Issue | Actual evidence | Recommended next decision | Current gate |
|---|---|---|---|
| Four RGB failures | Strict Pillow and OpenCV fail; original SHA256/headers retained | Prefer independently verified source replacements kept as a separate version; otherwise approve/disclose an explicit non-destructive failure/exclusion policy | BLOCKED; no automatic repair or split change |
| Native ownership | `train/9968_02_01.png` labels both adults in a selected example | Verify source/author annotation intent; retain anomaly and quantify only a separately justified screen | Ownership not guaranteed by filename |
| Train/val exact reuse | 652 val IDs share exact decoded content with train | Preserve official result population; consider separately approved overlap-controlled sensitivity and disclosure of native-checkpoint exposure | No content-independent validation claim |
| Checkpoints | Official links inspected, zero weights downloaded; user deferred large files | Revisit explicit bounded download approval after source/dataset review | No model SMOKE_PASS |
| Native CUDA stacks | nvcc absent; M2FP/D2FP/SCHP require CUDA compilation, CPI may support a compatible binary MMCV stack | Review one pinned isolated stack per candidate; no system driver/toolkit edits or arbitrary retries | Native environments not ready |
| License scope | MHP/FASHN noncommercial restrictions; uncertain legacy weight grants; D2FP upstream code | Record applicable weight and intended-use terms before affected execution/deployment | Candidate-specific |
| Sapiens2 | Current license prohibits surveillance-related R&D | Exclude unless verifiable applicable permission is obtained | LICENSE_BLOCKED_PENDING_CLARIFICATION |
| Taxonomy | Fine/native labels and coarse/ambiguous parser capacity differ | Approve explicit cohorts and common denominators, not one misleading global score | DRAFT |
| GT geometry | Full parsing foreground includes carried items; pose IDs/order differ | Review shared body/clothing-support geometry and an all-support sensitivity | DRAFT |
| Crop ownership | Semantic crop can include neighbors | Approve a deployment-available post-parsing ownership/ambiguity policy; keep raw outputs | DRAFT |
| Native evaluator edge | Source function raises IndexError with zero predictions | Add/test a reviewed compatibility guard; broader source/native parity required | Native official-style freeze blocked |
| Timing | Native/crop/integrated workloads differ | Approve stage boundaries, N-person workloads, FP32 and resident memory reporting | DRAFT; no latency result |

The plan's strongest features are layer separation, train-only development, native-mode reference cohorts, honest failed-candidate states and refusal to assume hybrid superiority. The audit demonstrates why these gates matter: extraction success is not RGB readability, numeric mask fidelity is not physical-person ownership, and split-ID disjointness is not image-content independence.

Study-specific evaluator tests cover perfect/wrong labels, missing/duplicate/swapped persons, overlapping masks, ignore/absent classes, unsupported labels, dimensions and coordinate/ownership failures. Native-function fixtures cover only a limited synthetic subset; they do not prove complete official AP^p/PCP parity. Boundary metrics and deployable ownership effectiveness remain protocol proposals, not tested model claims.

Later Stage 1 should be an off-the-shelf **system/candidate** comparison, not a controlled architecture experiment. MHP-trained and cross-dataset parsers have different exposure. Native/full-frame and YOLO/crop cohorts must remain separate until a complete-system common-task evaluation is explicitly authorized. Hybrid routing, oracle ceilings and deployable fusion must also be distinguished and separately authorized.

**Next action: review the blockers and approve only the next bounded corrective/feasibility step. Do not start Stage 1 or a full benchmark.** No owner-contact message, remote repository, model ranking or color/attribute work was created.
