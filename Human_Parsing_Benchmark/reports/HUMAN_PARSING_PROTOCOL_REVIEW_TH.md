# Human Parsing — Prompt A: evidence and protocol review

**REVIEWED_PROPOSAL · 21 ตุลาคม 2026 UTC** ไม่ใช่ DESIGN_READY/LAUNCH_READY และไม่ implement execution pipeline แผน authoritative คือ [PLAN.md](../PLAN.md) ใช้ชื่อเดิมจาก SETUP ต่อ ไม่สร้าง design report ซ้ำอีกชื่อ

## A. สถานะจริงที่ตรวจแล้ว

Root workspace, current Human_Parsing_Benchmark และ legacy Human_Parsing_MHPv2_Study ไม่มี Git repository ของตน Public checkout แยกอยู่ที่ Human_Parsing_Study_Public, branch main, remote folklazy/Human_Parsing_Study, base commit `8b1b813baf2a010f3140cd7ed12ea3554f04e33d` working tree สะอาดก่อนงานนี้ ใช้ explicit path/hash publication workflow เดิม ไม่สร้าง nested Git หรือเปลี่ยน remotes

อ่าน README/STATUS/PLAN/decisions, registry V7/roster V4, actual checkpoint RUN manifests, upstream decoder/config snippets, old scoring/route assembly, dataset audits/population bindings, CPI CSV และ QANet candidate/worker จาก filesystem จริง ไม่มี inference, model load, tests ชุดเดิม, full dataset audit, checkpoint/dataset download หรือ bulk payload hash scan ในรอบนี้

ใช้รูปแบบ navigation/evidence/report separation ของ YOLO Master และ Largest tier ที่อ่านได้จริงจาก SETUP และอ่าน README อีกครั้งใน A ผล YOLO/CPI ยังคงเดิม ไม่เอาเวลา/metrics ของ MOTS20 มาเป็น parsing defaults

## B. ข้อค้นพบที่มีผลต่อแผน

| ข้อค้นพบ | Evidence ที่อ่าน | ผลตัดสิน |
|---|---|---|
| เจ็ดรายการ user review input อยู่จริง แต่ current Prompt A ยังไม่รับรอง exact roster | registry/CANDIDATES.csv จาก SETUP และคำสั่งปัจจุบัน | เสนอ 7 ไม่อ้าง accepted19 หรือ launchready; รอ scope acceptance ไม่ขอให้ผู้ใช้ส่ง inventory ทั้งหมดใหม่ |
| Registry V7 บาง fields Sapiens ว่างและ route state ยัง RESTRICTED | V7 CSV เทียบ actual pilot RUNs และ user direction ปัจจุบัน | ห้ามตีความว่าไม่เคยโหลด/ไม่มี evidence; เติม review matrix จาก actual RUN โดยไม่แก้ historical CSV และไม่ใช้ stale restriction บล็อก candidates |
| Sapiens0.4B/0.8B native public TRAIN10 ภาพผ่าน; 1B native GPU-resident10 ภาพผ่านพร้อม offload-control warning | Three actual pilot RUN.json, weights/source hashes, geometry/precision fields | รันได้ใน native pilot ไม่ใช่ crop/conditioned pipeline ready; ไม่เอา 5B กลับมา |
| CIHP four checkpoints มี native TRAIN1 ภาพ evidence ตรง revision และ preparation route packets | Native smoke RUNs + preparation eligibility/RUN/packet records | Reuse feasibility ไม่ rerun inventory; new view/mask scorer และ full runtime profile ยังต้อง B |
| QANet reference smoke ใช้ GT person ROI ไม่ใช่ native detector; actual YOLO ROI TRAIN ก็มีภายหลัง | run_qanet_additional.py เทียบ bounded_train/.../RUN.json | เก็บ checkpoint; application YOLO route มี evidence แต่ไม่ตั้ง native full-frame detector configuration เทียม |
| M2FP/D2FP source returns semantic/part/human queries; upstream assembles owned semantic planes | m2fp/d2fp_model.py และ parsing_evaluation.py; normalization helper | เสนอ native-reference reuse ได้หลัง parity fixture; human confidence ไม่ใช่ official parsing AP confidence |
| Old helper drops all-zero semantic persons | experiment_preparation_v1.py: final_crop keep-if-any / final_native skip-empty | ใหม่ต้องเก็บ location extent แยก semantic outcome เพื่อให้ empty prediction ถูกให้คะแนนตาม policy แทนการเปลี่ยนตัวหาร; แก้เฉพาะ B ไม่แตะ old packets |
| Old score_frame calls bbox-based evaluate_persons | src/application_v2/scoring.py / evaluation.py | ใช้เป็น reusable contract/lifecycle logic แต่ไม่อ้างว่า mask-IoU evaluator ใหม่พร้อมแล้ว ต้อง version scoring recipe/actual code |
| M2FP/D2FP มี retry_if_cuda_oom รอบ postprocess/instance inference | Pinned model source | MUST_FIX สำหรับ GPU-only runtime: instrument/explicitly control hidden retry/CPU fallback ใน future isolated compatibility layer ไม่ทำ patch เงียบใน A |
| Native TTA/thresholds/ROI behavior ไม่เท่ากัน | Configs + QANet InstanceBox + RPR defaults | เปรียบเทียบ released configurations โดยประกาศ settings/cost ไม่อ้าง backbone causality และไม่ tune ให้คะแนนดีจาก VAL |
| Body mapping ของ Sapiens ไม่ตรง CCIHP exact partitions | SEG.md: Face_Neck/Torso/Apparel/hands/feet/facial subparts | C3 clothing primary ยังร่วมได้; C7 body diagnostic แยกจาก exact cohort ไม่ตัด Sapiens ออกจาก active set |

## C. Dataset evidence และ policy change

CCIHP released GT มี Category/Human maps ใช้ person-level parsing ได้เชิงโครงสร้าง แต่ไม่อ้าง official CIHP GT equivalence หรือ annotation completeness ทุก physical person Unknown22/owner-category mismatch ต้องใช้ explicit fixed domains ไม่เอา predictions มาสร้าง void

Existing source audits: train28,280, validation5,000; PNG99,840 ทั้งหมดอ่าน; native persons93,292/17,548; raw category22 total8,268pixels/322images; validation310pixels/61images; validationH>0/C0=638pixels/144images Structural flags ไม่ใช่ confirmed physical-person errors ห้ามแก้/exclude GT เอง

Exact duplicates: byte และ decoded RGB evidence ตรงกัน 39train-overlap VAL IDs, main 4,961/reference 5,000, within-VALgroup1 Near-duplicate method pHash Hamming≤4 + aspect difference≤5% ให้ candidatepairs114 ยัง pendinghumanconfirmation ไม่ autoexclude และไม่รับรอง unseenexposure ใน main

Current Prompt A **explicitly supersedes no-VAL-selection สำหรับ checkpoint selection ของแผนนี้** ไม่ supersede prohibition ของ mapping/threshold/preprocess/retry tuning และไม่เขียน historical CPI decisions ใหม่ Selection-set optimism และ unknown checkpoint exposure ต้องรายงาน

อ่าน existing native per-person category-support sidecar เพื่อ derive G_sem ใหม่ ไม่ decode GTpixels: C3 main17,085/reference17,199; C7 main17,390/reference17,504 Main/reference G_loc17,434/17,548 C7 เท่า oldcount เพราะ union เหมือนเดิม แต่ recipe/matching/classes เปลี่ยนแล้วต้องสร้าง new context ใน B Legacydomainpixel proof ไม่ใช่ approval ของ newview ดู [domain proposal](../manifests/POPULATION_DOMAIN_PROPOSAL.json)

## D. ข้อเสนอที่ได้จาก evidence ไม่ใช่เพียงรายการควรตรวจ

1. เสนอ checkpoint 7 ตัวที่มี localofficialweights และ actual nativeevidence ครบ: QANetHRNetW48CIHP, M2FPR101CIHP, D2FPR101CIHP, RPRR50CIHP, Sapiens0.4/0.8/1B เก็บตัวนอกชุดเป็น HOLD ไม่กล่าวหาคุณภาพต่ำ; [29-entry diff](../registry/ROSTER_DIFF.csv) คงเหตุผล priorholds/exclusions
2. เสนอ 10configurations: application7, native-instance reference3 ที่ reuseparseroutputs ไม่มี newqualityinference สำหรับ reference ส่วน Sapiensnativefull-frame เป็น semanticpilot evidence ไม่เพิ่ม full VALroute ที่ตอบ ownership ไม่ได้
3. C3 upper/lower/shoes เป็น shared task จริง C7 เพิ่ม body เฉพาะ semanticallycompatibleCIHPcohort Sapiensapproximatebody คง diagnostics ไม่สร้าง universal6-targetscore ที่ลบ garmentdetail
4. Hardlabelprojection เป็น primary เพราะ interfacemixed; Dress6/Apparel1 เป็น explicitprediction rejection ไม่ VOID; upper/lower ไม่ split จาก coarselabels ถ้า maskclass อยู่ผิด GTtarget ก็เสียคะแนนตามจริง
5. FinalGTmatching ใช้ person-mask IoU0.50/0.75 และ maskprecision/recall/F1 แยกจาก prediction-onlybboxassociation0.50 ไม่ใช่ officialAP PrimaryQ_person_sem_GT รวม missedGT, side-by-sideFP/coverage ไม่ success-only mainmetrics
6. STRICT_COMPLETE คงไว้ พร้อม retainINCOMPLETErows; resourcefailure ไม่แปลงเป็น accuracyzero และไม่ erasequalitycompleteprofile Runtimecost ต้องผ่าน cleanprofile ของตน
7. Fullroutecost ต้อง freshfrozenYOLO ภายใต้ co-residentprofile รวม IPC/crops/parser/association; parsercomponent มี nestedtimers และ native-onlyreference แยก ไม่นับ cachedread เป็น YOLOms หรือ sumprocesspeaks เป็น routeVRAM
8. Relativequality+instancecoverage/Pareto เหมาะกว่าตั้ง arbitraryabsoluteIoUfloor ใน publicstudy นี้ เสนอ near-tie0.005 และ descriptiveclusterbootstrap แต่ไม่อ้าง deploymentpass หรือ winner ทุก task

## E. Workload ที่คำนวณได้จริง / ข้อจำกัด estimate

Metadata reference 5,000frames มี 24,062YOLOopportunities; main 4,961 มี 23,877 รักษา sameinference reusemain/reference Qualityproposed35,000parserframe-systemjobs, native15,000, ROI96,248tasks โดย ROI 4checkpoint ไม่ใช่จำนวน forwardcalls เพราะ TTA/ROIenginesubcalls

Timingdraft เลือก 64mainimages แบบ 8strata×8 ด้วย SHA256seed20261021 ไม่มี parserperformance เกี่ยวข้อง มี 350opportunities Proposed3rounds: application1,344framejobs พร้อม freshYOLO1,344; native-reference 576framejobs; ROI 4,200tasks; warmup 150framejobs/YOLO105/ROI120 แยกออก Rankedsummaryrows68 เฉพาะ C3 และ compatibleC7 ไม่ใช่จำนวนโมเดล ดู [workload](../manifests/WORKLOAD_PROPOSAL.json)

ROIunowned+owneduint8fullgrid4models payload33,740,001,016bytes ยังไม่รวม nativeoutputcounts/metadata/logs/compression Nativepredictedpersoncounts และ actualforward/runtime/peakmemory ยังไม่มี evidence สำหรับ workload นี้ ไม่ออก ETA Reserve200GiB/free50GiB/per-system80GiB/24hcheckpoint เป็น proposedcaps ไม่ใช่คำพยากรณ์ ขณะตรวจ free~564.2GBdecimal

## F. Fairness review และ readiness ที่จำเป็นเฉพาะจุด

[Risk table 17 issues](../registry/FAIRNESS_RISKS.csv) แยก MUST_FIX / CONTROL_AND_REPORT / RESIDUAL_LIMITATION พร้อม evidence→bias→mitigation→verification→claimeffect ไม่มี zero-biasclaim

**MUST_FIX:** new accepted roster/view/split/selection binding; deterministic hardmapping+rejectionconfusion; view GT contexts; actual maskmatching; retain valid-empty locations; native assemblytie/scoreparity; target ownership/map-back; Sapienscropintegration; hiddenfallback/devicepolicy; joint residency/runtimeboundaries; strictledger/resumevalidation สิ่งเหล่านี้มี implementationgap จริง ไม่แก้ด้วยจำนวน tests หรือการรับนโยบายอย่างเดียว

**Reuse โดยไม่ต้องรันใหม่ทั้งชุด:** source commits ของ 5families ตรง pinnedheads และ workingtrees สะอาดที่ตรวจ; checkpoint fingerprint records; actual native GPUevidence; QANet YOLOTRAINpacket; frozenYOLOqualityledger; immutableCPIresults; datasetstructuralaudit/nativecategorysupports and memberships

**Targeted B checks เท่านั้น:** replayexistingTRAINpackets กับ new actualscorer/contexts; source confidence/decoderparity; validempty/overlap/GTvoid/unsupportednative/crop-boundaryfixtures; Sapiens ใหม่≤3TRAINframes ต่อ checkpoint หลังอนุมัติ; jointresidentTRAINload/device/fallback faultinjection; storage/caps estimate จาก actualartifactbytes ไม่มี VALscoretuning การได้ evidence เหล่านี้พร้อม acceptedconfig คือ readiness ไม่ใช่อนุมัติ batch

## G. Decisions / next action

ยังไม่ DESIGN_READY เพราะข้อเสนอ scope/view/selection ต้องให้ผู้ใช้รับรอง มีคำถาม 3 ชุดใน PLAN: (1) รับ 7checkpoints/10configs? (2) รับ C3shared+C7compatible/Sapiens bodydiagnostic และ accessoryscope? (3) รับ relativequality/coverage/Pareto+near-tie หรือมี absoluteconstraints? ไม่ขอห้านโยบาย CPI เดิมซ้ำและไม่ขอ header ที่ปิดไปแล้ว

เมื่อรับ design แล้วจึงจัด StageB implementation/readiness เฉพาะ gaps ตาม scope ที่อนุมัติ และเสนอ exactlaunchpackage ให้อนุมัติ benchmark แยก ไม่มี newinference/smoke/download/activeexecutioncodeorconfigchange ใน A

[Primary research sources and limitations](../docs/RESEARCH_REFERENCES.md) สนับสนุนแนวทาง explicitmapping/instanceownership/boundarydiagnostics ไม่รับรอง targets หรือ projectsemantics แทน evidence
