# Decisions — current scope and historical boundaries

วันที่บันทึก 21 ตุลาคม 2026 ที่มาเป็น user messages ใน session นี้ ไม่ใช่การรับรองข้อเสนอทุกข้อในเอกสารเก่า

| ID | Decision | Status | ที่มา / ผลต่อการทำงาน |
|---|---|---|---|
| SCOPE | Independent noncommercial student academic research | ACCEPTED_USER_SCOPE | คำชี้แจง Decision 5A ก่อนหน้า; ไม่ใช่ company product R&D และไม่โอนสิทธิ code/weights/dataset โดยอัตโนมัติ |
| BASELINE | Phase 1 จบแล้ว, YOLO26x-Seg frozen baseline | ACCEPTED_USER_DIRECTION | Workflow และคำสั่ง SETUP ปัจจุบัน; คง weights/YOLO results |
| OBJECTIVE | Phase 2–3 เปรียบเทียบ/คัด body/clothing/supported accessories, ownership และ speed/VRAM | ACCEPTED_USER_DIRECTION | Workflow + SETUP; metric definitions/runtime ยังต้อง A review |
| DATASET | CCIHP เป็น public selection benchmark หลัก | ACCEPTED_USER_DIRECTION_NOT_GT_OR_PROTOCOL_CERTIFICATION | คำสั่ง SETUP §2; ไม่แปลว่า native CIHP equivalent หรืออนุมัติใช้ VAL เลือกโมเดล |
| CANDIDATES | ชุดเจ็ด configurations ที่ผู้ใช้ส่งล่าสุด | USER_SPECIFIED_FOR_REVIEW | ตารางผู้ใช้ก่อนคำสั่ง SETUP ดู registry; ไม่ใช่ accepted executable roster, readiness หรือ inference permission |
| ROUTES | พิจารณา native full-frame และ YOLO-conditioned ตามความสามารถจริง | ACCEPTED_USER_DIRECTION | ไม่ force crop หรือ bypass internal detector เพื่อให้ตัวเลขเทียบง่าย |
| FUTURE | สี/attributes/CCTV เป็นบริบทอนาคตในรอบนี้ | ACCEPTED_SCOPE_BOUNDARY | ไม่เริ่ม attribute study หรือ CCTV inference จาก workflow diagram |
| WORKSPACE | Human_Parsing_Benchmark ที่ workspace root; public copy ใน repo เดิม | IMPLEMENTED_WITHIN_USER_SETUP_AUTHORIZATION | ชื่อ/ตำแหน่งเลือกตามสิทธิที่ผู้ใช้ให้; ไม่สร้าง Git หรือย้ายข้อมูลเดิม |
| EXECUTION | SETUP อนุญาตเอกสาร/metadata/Git sync เท่านั้น | ACCEPTED_SCOPE_BOUNDARY | ห้าม inference/smoke/benchmark/training/download/pipeline refactor |
| LEGACY | Roster 19 / two-QANet proposal / roadmap WIP ไม่เป็น launch scope ใหม่อัตโนมัติ | HISTORICAL_NOT_CURRENT_LAUNCH_AUTHORITY | คำสั่งเก็บ WIP และ candidate list ปัจจุบัน |
| CPI | CPI closed run คง INCOMPLETE/null/STRICT_COMPLETE และ ACCEPTED_WITH_INDIRECT_EVIDENCE | PRESERVED_HISTORICAL_ACCEPTANCE | ไม่ retry/ซ่อมผลเดิมหรือ promote evidence confidence |
| SELECTION | SETUP-era question about VAL selection | SUPERSEDED_FOR_CURRENT_PLAN_BY_PROMPT_A | User Prompt A now explicitly permits CCIHP VAL checkpoint selection; historical CPI policy remains historical. Mapping/threshold/preprocess/retry tuning remains prohibited. |
| DESIGN | Exact roster/targets/mappings/metrics/config/jobs ของรอบใหม่ | NOT_DECIDED | รอ Prompt A; ไม่เติมจาก filename ล่าสุดหรือ old accepted context |

ไม่มี decision ใดในชุดนี้ให้ Sapiens2 หรือ candidate อื่นมี new inference authorization หรือเป็น license clearance ใหม่ ใช้บันทึกสิทธิ/technical feasibility เดิมตามบริบท ไม่เปิด license audit ทั้งชุดเพื่อจัดโฟลเดอร์

ข้อเสนอใหม่บันทึก PROPOSED พร้อมหลักฐาน/ข้อจำกัดก่อนเปลี่ยน ACCEPTED ตามอำนาจที่ใช้ได้ หาก supersede ให้เก็บแถว/เอกสารเดิมและชี้ตัวแทน ไม่เขียนประวัติให้ดูเหมือนรู้ก่อนทดลอง

## Prompt A — 21 October 2026

| ID | Decision | Status | Source / consequence |
|---|---|---|---|
| A-VAL | CCIHP Validation may select pretrained checkpoints/configurations | ACCEPTED_EXPLICIT_USER_POLICY | Current Prompt A §4.3 supersedes previous no-VAL-selection for this new study only; no independent final confirmation claim and no VAL-based config/mapping/threshold/retry tuning |
| A-SAPIENS | 0.4B/0.8B/1B remain active candidates, 5B excluded | ACCEPTED_EXPLICIT_USER_ROSTER_DIRECTION | Current Prompt A §2; stale RESTRICTED metadata does not block candidate review; not new inference approval or model-license assurance |
| A-ROSTER | Proposed seven checkpoints / ten configurations | REVIEWED_PROPOSAL_USER_ACCEPTANCE_PENDING | Earlier seven-input table reused as proposal; no current accepted launch roster |
| A-VIEWS | C3 shared garment + C7 compatible CIHP cohort + separate Sapiens body diagnostics | REVIEWED_PROPOSAL_USER_ACCEPTANCE_PENDING | Semantic support matrix, no upper/lower collapse or invented class split |
| A-SELECT | Relative quality/coverage and Pareto, no arbitrary application-quality floor | REVIEWED_PROPOSAL_USER_ACCEPTANCE_PENDING | Near-tie0.005 and cluster bootstrap proposed before scores; multiple suitable configurations permitted |
| A-SCOPE | Review/design/metadata/Git only | ACCEPTED_EXPLICIT_USER_BOUNDARY | No active execution code/config change, GPU smoke, inference, downloads or benchmark in this work unit |

The authoritative current design remains PLAN.md; draft protocol values in protocol/REVIEWED_SPECIFICATION.json are not executable acceptance. No historical frozen run/config/result is modified by these decisions.

## Prompt A targeted clarification — Revision 2

| ID | Proposed clarification | Status / consequence |
|---|---|---|
| A-UNSUPPORTED | Known Dress/Apparel → RECOGNIZED_UNSUPPORTED; no execution failure/GTvoid/heuristic split | REVIEWED_PROPOSAL; not implemented; projected target delivery score is not native segmentation accuracy |
| A-EXTENT | Per-route mask sources; YOLO-derived extent F1 is not parser semantic ownership accuracy | REVIEWED_PROPOSAL; extent+semantic/contamination+FP evidence required for claim |
| A-TIE | Point gap≤.005 independent of interval crossing0; remove undefined important-per-class-regression auto veto | REVIEWED_PROPOSAL; user accepted class floors only if defined before scores |
| A-CAPABILITY | C3 garment / C7 compatible joint task shortlists; named mandatory body/accessory profile pending | USER_DECISION_PENDING; no universal winner from C3 alone |
| A-RECOVERY | Verified external interruption may be recoverable with frozen identities, atomic packets, immutable attempt history | PROPOSED_NOT_ACCEPTED; extra in-flight attempts require explicit recovery authorization; genuine model retry remains0 |
| A-DISK | 200GiB planning envelope, not global cap/total estimate;80GiB per checkpoint stream;50GiB free guard | REVIEWED_PROPOSAL; B aggregate peak measurement/capacity allocation required before launch |

These entries revise only current proposal semantics, not historical CPI policies/results. This user instruction authorizes documentation/Git synchronization only, with no new tests, Prompt B, inference or active execution code/config changes.

## Current specification closure — Revision 3

Earlier SETUP/Prompt A rows above retain historical state; the current table here supersedes their stale roster-question/wait-for-Prompt-A interpretation only.

| ID | Current status | Source / effect |
|---|---|---|
| A-SELECTED-SCOPE | USER_CONFIRMED_SELECTED_PROPOSAL_SCOPE | Current user §1 explicitly preserves exact7checkpoints/7application/3references. AllIDs match registry; no renewed scope question, no launch/execution acceptance |
| A-SELECTION-GOAL | ACCEPTED_EXPLICIT_USER_DIRECTION | Current clarification: CCIHP must drive real checkpoint/config selection; no wait for CCTV GT or speculative exception preserving dominated candidates |
| A-GROUP-CONTRACT | SPECIFIED_FOR_DESIGN_REVIEW | ApplicationC3 all7 and C7 supportedCIHP4 compare full configurations across routefamilies under same task/domain/metrics; native3 references separate |
| A-PROJECTION-EVIDENCE | SPECIFIED_FOR_DESIGN_REVIEW | View-specific disposition; mapping_typeEXACT means one-to-oneconceptoperation, separate evidencelevel for everytaxonomy; no global disposition or header gate |
| CAP-GARMENT / CAP-BODY / CAP-ACCESSORY | USER_DECISION_PENDING | Recommendations and alternatives in PLAN§11/spec.pending_user_decisions; none is automatically mandatory from this doc |
| SELECT-PREFERENCE | USER_DECISION_PENDING | Semanticqualityleader distinct from Pareto and selectednextphase; proposed capability-eligible Pareto multi-selection, no arbitrary absolute floors |
| RECOVERY | PROPOSED_NOT_ACCEPTED |1extraexternalattempt/item,1epoch/batch; model/OOMretry0; no currentexecutionpermission |
| RESOURCES-B | USER_DECISION_PENDING |200planning/80stream/free50/24h;separateBbudget≤16conditionalTRAINcalls;aggregateestimate required |
| A-CURRENT-BOUNDARY | ACCEPTED_EXPLICIT_USER_BOUNDARY | Documentation/schema consistency only; no StageB implementation, inference, scorer/execution code/config change or benchmark |

Decisionacceptance is not source evidence or executionreadiness. Pendingdecision authority is one consolidated table in PLAN§11 and its machine-readable spec counterpart, not multiple new questionnaires.

Proposed B resource ceiling clarification:≤16parser TRAIN frame-system calls,≤32external ROI tasks and≤7freshfrozenYOLO TRAIN calls (one initial0000930 per co-resident application profile, only if exact proof missing). ExistingfrozenTRAINopportunity metadata gives2/6/2 for0000930/0021834/0001368;read-only counts, no new model execution. No nominalquality/timingjob increase.

## 2026-10-28 — user-adopted CIHP native Parsing9 revision3

The current user explicitly replaces conflicting previous plan with proposals/CIHP_NATIVE_PARSING9_CODEX_PLAN_TH_20261028.md. CIHPnative active, Ninja deferred. Firstsix includesCPI_R50_CIHP/CPI_ConvNeXtB_CIHP again for a NEW native-GT run, not repair of historical results. SourceCIHP_PGN GoogleDrive provenance user-supplied. VAL5000, notCCIHP4961;native20-classsemantics. Preparation/implementation/CPUchecks and six-model testing authorized whenready, no per-model reapproval needed. Sapiens3followmatrix, no color/training/CCTV work now. Old7/10view/mappingdecisions retained as superseded history for prior CCIHP design.
