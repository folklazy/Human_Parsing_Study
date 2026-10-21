# Human Parsing — Prompt A: evidence and protocol review

**REVIEWED_PROPOSAL · Revision 3 · 21 ตุลาคม 2026 UTC** ไม่ใช่ DESIGN_READY/LAUNCH_READY และไม่ implement execution pipeline แผน authoritative คือ [PLAN.md](../PLAN.md) ใช้ชื่อเดิมจาก SETUP ต่อ ไม่สร้าง design report ซ้ำอีกชื่อ

## A. สถานะจริงที่ตรวจแล้ว

ในการตรวจ Prompt A ครั้งแรก Root workspace, current Human_Parsing_Benchmark และ legacy Human_Parsing_MHPv2_Study ไม่มี Git repository ของตน Public checkout แยกอยู่ที่ Human_Parsing_Study_Public, branch main, remote folklazy/Human_Parsing_Study, initial-review base commit `8b1b813baf2a010f3140cd7ed12ea3554f04e33d` working tree สะอาดก่อนงานนี้ ใช้ explicit path/hash publication workflow เดิม ไม่สร้าง nested Git หรือเปลี่ยน remotes

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

Timingdraft เลือก 64mainimages แบบ 8strata×8 ด้วย SHA256seed20261021 ไม่มี parserperformance เกี่ยวข้อง มี 350opportunities Proposed3rounds: application1,344framejobs พร้อม freshYOLO1,344; native-reference 576framejobs; ROI 4,200tasks; warmup 150framejobs/YOLO105/ROI120 แยกออก Summaryrows68 (application44/native-reference24) เฉพาะ C3 และ compatibleC7 ไม่ใช่จำนวนโมเดล ดู [workload](../manifests/WORKLOAD_PROPOSAL.json)

ROIunowned+owneduint8fullgrid4models payload33,740,001,016bytes ยังไม่รวม nativeoutputcounts/metadata/logs/compression Nativepredictedpersoncounts และ actualforward/runtime/peakmemory ยังไม่มี evidence สำหรับ workload นี้ ไม่ออก ETA Reserve200GiB เป็น planning capacity envelope ไม่ใช่ totalestimate/globalcap; free50GiB/per-stream80GiB/24hcheckpoint เป็น proposedguards/caps ขณะ initialreview free~564.2GBdecimalเป็น historicalsnapshot ดู §H.6 สำหรับการนับและ readiness gap

## F. Fairness review และ readiness ที่จำเป็นเฉพาะจุด

[Risk table 17 issues](../registry/FAIRNESS_RISKS.csv) แยก MUST_FIX / CONTROL_AND_REPORT / RESIDUAL_LIMITATION พร้อม evidence→bias→mitigation→verification→claimeffect ไม่มี zero-biasclaim

**MUST_FIX:** new accepted roster/view/split/selection binding; deterministic hardmapping+rejectionconfusion; view GT contexts; actual maskmatching; retain valid-empty locations; native assemblytie/scoreparity; target ownership/map-back; Sapienscropintegration; hiddenfallback/devicepolicy; joint residency/runtimeboundaries; strictledger/resumevalidation สิ่งเหล่านี้มี implementationgap จริง ไม่แก้ด้วยจำนวน tests หรือการรับนโยบายอย่างเดียว

**Reuse โดยไม่ต้องรันใหม่ทั้งชุด:** source commits ของ 5families ตรง pinnedheads และ workingtrees สะอาดที่ตรวจ; checkpoint fingerprint records; actual native GPUevidence; QANet YOLOTRAINpacket; frozenYOLOqualityledger; immutableCPIresults; datasetstructuralaudit/nativecategorysupports and memberships

**Targeted B checks เท่านั้น:** replayexistingTRAINpackets กับ new actualscorer/contexts; source confidence/decoderparity; validempty/overlap/GTvoid/unsupportednative/crop-boundaryfixtures; Sapiens ใหม่≤3TRAINframes ต่อ checkpoint หลังอนุมัติ; jointresidentTRAINload/device/fallback faultinjection; storage/caps estimate จาก actualartifactbytes ไม่มี VALscoretuning การได้ evidence เหล่านี้พร้อม acceptedconfig คือ readiness ไม่ใช่อนุมัติ batch

## G. Decisions / next action

Currentrevision3: selectedscope7/10ได้รับคำสั่งให้คงไว้แล้ว ไม่ถามrosterซ้ำ;ยังไม่DESIGN_READYเพราะmandatorycapability/selection/recovery/resource decisionsค้าง ใช้คำตัดสินชุดเดียวในPLAN§11/spec.pending_user_decisions ไม่ขอห้านโยบายCPIหรือheaderที่ปิดไปแล้วอีก

เมื่อรับ design แล้วจึงจัด StageB implementation/readiness เฉพาะ gaps ตาม scope ที่อนุมัติ และเสนอ exactlaunchpackage ให้อนุมัติ benchmark แยก ไม่มี newinference/smoke/download/activeexecutioncodeorconfigchange ใน A

[Primary research sources and limitations](../docs/RESEARCH_REFERENCES.md) สนับสนุนแนวทาง explicitmapping/instanceownership/boundarydiagnostics ไม่รับรอง targets หรือ projectsemantics แทน evidence

## H. การปิดหกประเด็นเฉพาะจุด — Revision 2

**ขอบเขต:** อ่านเฉพาะ PLAN/draftspec/tablesและ pinned native catalog/CCIHPREADME ที่เกี่ยวข้อง ใช้ audit/manifestsเดิม ไม่ทดสอบซ้ำหรือเพิ่ม tests, inference, productioncode/config หกข้อด้านล่างเป็นการปิดความกำกวมในข้อเสนอ ไม่ใช่ acceptance/implementationproof ยังคง REVIEWED_PROPOSAL

Work unit: `proposal-clarification-20261021T063557842659Z`; publication base `d85c69d4469df525370a120e6718e24217b57ced`. Initial-review baseline in §A remains historical; this revision changes documentation/draft specifications only.

### H.1 Dress/Apparel และความหมายของ rejection

| Native label / applicable checkpoints | นิยามที่มีหลักฐาน | Target projection / ข้อจำกัด |
|---|---|---|
| CIHP5 UpperClothes — CIHP4 | Pinned CIHP catalogระบุชื่อ UpperClothes; CCIHPREADME5ระบุรวม top of dress | →UPPERตาม proposedmerge; nativecategoryและ CCIHP annotationpolicyไม่เหมือนกันทุกขอบเขตโดยอัตโนมัติ |
| CIHP6 Dress — QANet/M2FP/D2FP/RPR CIHP | Catalogแยก Dressจาก5/7/9/12; one native labelไม่มี upper/lower boundary | RECOGNIZED_UNSUPPORTED; ไม่ใช่ sourceunknownหรือ executionunresolved |
| CIHP7 Coat — CIHP4 | Named Coat; CCIHP7รวม outermostcoat/jacket/vest/sweaterตามคำอธิบายผู้สร้าง | →UPPERเป็น garmentcategory ไม่ใช่ anatomicalwaistcrop; sourcepolicyต่างได้ |
| CIHP9 Pants — CIHP4 | Native Pants; CCIHP9เสื้อผ้าสองขารวมshorts/tights/etc. | →LOWER; ไม่สร้าง dress-bottomจาก nativePants |
| CIHP12 Skirt — CIHP4 | Native Skirt; CCIHP12รวมbottom of dress | →LOWERสำหรับ nativeSkirt; ไม่ได้ทำให้ nativeDressแบ่งได้ |
| Sapiens1 Apparel — 0.4/0.8/1B | OfficialSEG.mdยืนยัน name/ID; **ไม่ได้อธิบาย exhaustive annotation scope** | RECOGNIZED_UNSUPPORTEDเพราะยังไม่มี supported upper/lower projection; ไม่อ้างว่า Apparelเท่ากับ Dressหรือ allclothes |
| Sapiens13 Lower_Clothing — 3sizes | Official named label13 | →LOWERใน proposal; detailed boundary conventionยังไม่ independentverified |
| Sapiens23 Upper_Clothing — 3sizes | Official named label23 | →UPPERใน proposal; detailed boundary conventionยังไม่ independentverified |

**Primary evidence ที่อ่านจริง:** CCIHP release README §Datasetdescription; pinned M2FP register_cihp_parsing.py@17a89de… catalog; Sapiens docs/SEG.md@7e5bae8… catalog ตัวเลข/pathเต็มอยู่ mappingtableและ editorialrecord ไม่คัด third-party sourceเพิ่มเข้าGit นี่เป็น semantictraceจาก existingevidence ไม่ใช่ nativeaccuracymeasurementใหม่

Native segmentation errorคือทำนายไม่ตรงกับ nativeclass/regionที่ถูกต้อง ต้องมี compatible nativeGTหรือการreviewที่ยืนยันได้ Target-taxonomy incompatibilityคือ regionอาจถูกแต่ไม่มี labelpartitionที่ targetต้องการ การต่ำของ projectedIoUแยกสองสาเหตุนี้เองไม่ได้

**ตัวอย่างเชิงนิยาม ไม่ใช่ผลทดลอง:** มีคนเดียว visible dressเต็มชุด Nativeprediction6ตรง dressregionสมบูรณ์ CCIHPแบ่งregionเป็นGTupper5และlower12 แต่ไม่มีshoesในกรณีสมมติ Predictionทั้งหมดเป็น rejection จึงIoUupper=0, IoUlower=0 และpersonQ_C3=0 ทั้งที่nativeDressอาจถูกทั้งหมด ถ้า footwearที่มีGTทำนายถูก จะเพิ่มclassตามนิยามK_i ไม่เปลี่ยนdresspixelsเป็นvoid กรณี Apparelให้ตีความแบบ conditionalเท่านั้นเพราะnativeannotationdefinitionยังไม่ครบ คะแนนรองรับ “ใช้ส่งupper/lowerpartitionที่ต้องการได้เพียงใด” ไม่รองรับ “โมเดลsegment Dressผิด/แพ้nativeaccuracy”

**Diagnostics ที่เสนอให้ B implement:** nativeclasspixel/image/personhistogramก่อน/หลังclip; rejectedvalidpixels/validdomainpixels; rejectedpixelsแยกแต่ละGTtarget/targetGTsupport; rejectedcontextและGTvoidcountsแยก; affectedperson/imagecountsพร้อมfixeddenominators เก็บ nativeIDs/masks ไม่ heuristic split ไม่ per-modelignore ไม่claimว่าdiagnosticsเหล่านี้คำนวณแล้วหรือเป็นอันดับใหม่

### H.2 Extent source และ expected scoring

| Route | Evaluation extent | Dependency/semantic-empty consequence |
|---|---|---|
| QANet/Sapiens YOLO_ROI | Frozen original-gridYOLOinstance mask | Detector-derived; semanticemptyยังคงextent/ID แม้Q=0 |
| M2FP/D2FP native + associated | Native humanownershipmaskก่อน labelcomposition | Nativehumanqueries; associatedrouteยังมีYOLOgating Nonemptyhumanextentไม่หายเมื่อsemanticsว่าง |
| RPR native + associated | Unionnative nonBGpersonparsinglabels | Extentพึ่งparserforegroundและinternaldetector; semanticemptyไม่มีindependentsilhouetteให้คง ห้ามfilledbboxreplacement |

QANet/Sapiensที่ retainedYOLOopportunitiesเหมือนกันมี extentP/R/F1เหมือนกันได้ทั้งหมด จึงเรียก **person-extent detection/separation F1 ของระบบ** ไม่ใช่ standaloneparserownershipaccuracy ต้องแสดง matchedpersonsemanticQ, FP, cross-ownercontaminationและcollisionด้วย GTใช้เฉพาะscorerไม่ช่วยแก้ownership

ตารางนี้เป็นผลที่อนุมานจากนิยามสำหรับ simplifiedcases **ไม่ใช่ executedtests**; หนึ่งGTมีvalidtargetsupportและไม่มีvoid เว้นแต่ระบุ:

| Case | Expected extent scores | Expected semantic/ownership observation |
|---|---|---|
| Semanticempty + exactindependentextent | ROI/M2FP/D2FP:TP1,FP0,FN0,F1=1 | Q=0; contaminationN/Aเมื่อไม่มีmappedtargetpixels ไม่ใส่0เพื่ออ้างcleanownership |
| SemanticemptyของRPR | No nonemptyextent:TP0,FP0,FN1; recall/F1=0,precisionN/A | Q=0; preserveemptyentrydiagnostic ไม่สร้างmaskใหม่ |
| Wrong-personsemanticsแต่extentถูก | F1อาจยัง1 | Qลดถึง0ได้; cross-ownerpixelsเพิ่มcontaminationถ้ายังsurviveclip PureIDstringpermutationไม่ผิดและ identicalextentsอาจแยกphysicalownerไม่ได้ |
| Duplicatecorrectprediction2ชุดต่อGT1 | TP1 FP1 FN0;precision=.5,recall1,F1=2/3 | Qอาจยัง1เพราะ matchedpredictionถูก ต้องอ่านFP/F1ร่วม; duplicateไม่ใช่executionfailure |
| ExtentIoU=.60, soleGT/predtargetclassตรงกัน | Threshold.50:TP1/F1=1; threshold.75:TP0/FP1/FN1/F1=0 | Q=.60ที่.50และ0ที่.75ในกรณีนี้ ไม่ใช่generalformulaเมื่อextent≠targetsupport |

Contaminationนิยามให้ชัดเป็น mappedtarget-labeledpixelsของpredictedpersonบนfixedvaliddomainที่ตกใน **otherGTHuman_ids** / mappedtarget-labeledvalidpixels denominator0ให้null/NO_MAPPED_TARGET_PIXELS พร้อมdefinedpersoncountและemptycount รายงาน pooledpixelratioแยกจาก per-personratio ไม่เอาundefinedมาเฉลี่ยเป็น0 Extentmatchingหรือcontaminationอย่างเดียวไม่วัดclasscorrectnessทั้งหมด แยกpre-clipunownedและpost-clipfinalcontaminationพร้อมstage/domaindenominators เพราะYOLOclipอาจกดcontaminationลงแต่ตัดtruepartsจนsemanticFNสูงได้ post-clipratioต่ำไม่พิสูจน์learnedownership

### H.3 Selection closure

Practicalnear-tie: **abs(pointΔQ)≤.005** แยกจากintervaldirectionflag; CIincludes0ไม่ได้เป็นtieอัตโนมัติ

| abs(point gap) | CI contains0 | Practical near-tie | Interpretation |
|---:|---|---|---|
| .004 | NO | YES | ผลต่างเล็กตามmarginแต่intervalไม่คร่อม0 |
| .004 | YES | YES | ผลต่างเล็กและdirectionuncertain |
| .020 | YES | NO | ผลต่างobservedใหญ่แต่directionยังไม่ชัด ไม่ให้costชนะอัตโนมัติในชื่อtie |
| .020 | NO | NO | ผลต่างobservedใหญ่และintervalไม่คร่อม0 |

ยกเลิก **automatic “no important per-class regression” criterion** ที่ยังไม่กำหนดimportance/threshold รายงานperclassdelta/supportครบ ไม่มีpost-hocveto ถ้าต้องมีmandatoryclassfloor/toleranceต้องรับก่อนดูVALและversionselectionrule Near-tieระบุคู่หรือเทียบbestobservedQภายในcomparison_group/population/matching_thresholdเดียวกัน ไม่ถือเป็นtransitiveequivalencegroup Near-tieไม่บังคับเลือกตัวถูกสุด; qualityleaderและnon-dominatedalternativesยังรายงาน ไม่weightedscore

C3ให้garmentshortlistทุกproposedcheckpointแต่ไม่รับรองbody/accessory C7ให้jointbody/clothingselectionเฉพาะcompatiblecohort ไม่poolคะแนนสองview Sapiensbodyproxyเป็นdiagnostic ถ้า **ทุกexposedbodytargetเป็นmandatory** Sapiensยังไม่eligibleสำหรับexactjointtaskจากbodyproxyเพียงอย่างเดียว ไม่เท่ากับnativebodymodelไม่ดี

สิ่งที่ผู้ใช้ต้องตัดสินก่อนfinalsuitability: (1) namedmandatorybodytargetsทั้งหมดFace/Exposedtorso/Arms/Legsหรือบางส่วน (2) namedaccessoriesเช่นBag/FaceMask/Headwear/etc. (3) absolutequality/resourcefloorsถ้ามี หากยังไม่มีprofile ให้conditionalC3/C7shortlistsหลายconfiguration ไม่ประกาศuniversalwinner/CCTVready ไม่เปลี่ยนrosterหรือขอรับรองห้านโยบายCPIซ้ำ

### H.4 Execution completeness × prediction disposition

| Execution stage state | Prediction disposition | Required pipeline work satisfied? | Scoring / STRICT_COMPLETE |
|---|---|---|---|
| COMPLETE_VALID | MAPPED_TARGET/CONTEXT | YES | Normalfixed-domainmetrics |
| COMPLETE_VALID | RECOGNIZED_UNSUPPORTED (Dress/Apparel) | YES | Rejectioncolumn/targetFN; **ไม่ทำrunINCOMPLETEเพียงเพราะmapไม่ได้** |
| COMPLETE_VALID | NO_PERSON_OUTPUT / SEMANTIC_EMPTY_PERSON (แยกกัน) | YES | Zero personsรับmissedGT;nonemptyextentคงmatchingแต่q=0เมื่อไม่มีtarget;ไม่เรียกfailureเพื่อหลบคะแนน |
| SKIPPED_BY_ROUTING | ValidfinalemptypacketตามfrozenzeroYOLOpolicy | PipelineYES;parserinvocationN/A | Logskipsแยก ไม่creditparsercompleted; GTยังอยู่coverage |
| INVALID_CONTRACT | Out-of-catalogID/invalidgeometry/missingrequiredfields | NO | Primarynull/INCOMPLETE; ไม่downgradeเป็นknownunsupported |
| FAILED_MODEL_OOM/EXCEPTION | Absent/uncommittedpartial | NO | Primarynull/INCOMPLETEและretainedfailure |
| INTERRUPTED_EXTERNAL/UNKNOWN_CAUSE | No committedvalidpacket | NO whilepending | ไม่scorepartial; recoveryรอexplicitdecision |
| NOT_ATTEMPTED/RUNNING | None | NO | ไม่มีmainคะแนนจากsuccesssubset |

Executionunresolvedหมายถึงงานยังไม่มีvalidterminaloutcome ไม่ใช่recognizedunsupportedclass แก้ชื่อ `UNRESOLVED_PRED` ในcurrentdraftเป็น `RECOGNIZED_UNSUPPORTED`/`REJECT_TARGET_UNREPRESENTABLE`; ไม่เปลี่ยนhistoricalrecords Framecompleteต้องมีทุกrequiredROIpacketหรือauthorizedroutingbypassและvalidfinalpacket Eligibilityมาจากfrozenpolicyไม่ใช่ภาพที่รันผ่าน

### H.5 Interruption — recovery proposal, no extra retry approved

| Cause/output evidence | Proposed action | Authority/state |
|---|---|---|
| ModelOOM/exception | Preservefailedattempt; retry0/noCPUorFP16fallback | Genuinefailureไม่เรียกexternal; requiredfailedworkทำINCOMPLETE |
| UI/SSHdisconnectแต่workerยังทำ | ตรวจledger/processแบบread-only; ไม่launchซ้ำ | Disconnectไม่พิสูจน์interruption |
| Verifiedexternalpreemption/reboot/signal + committedvalidoutput | Reusehash-boundpacket/receiptเมื่อfingerprintsตรง | Artifactreconciliationไม่ใช่inference/retry; ถ้าคนละrecipeหยุด |
| Completeimmutablepacketแต่ledgerยังไม่receipt | Validateidentity/hashและreattachreceiptโดยไม่compute | เสนอcrash-windowreconciliation; conflictingpacketsหยุดไม่เลือกตามscore |
| Externalinterruption + partial/uncommittedattempt | Preserveattempt-localpartial; proposeextraattempt withparent/proof | **ต้องexplicitrecoveryapprovalก่อน** ไม่เท่ากับnever-attemptedcontinuation |
| Unknowncause | KeepUNKNOWN_CAUSEandpending/incomplete | ห้ามเดาว่าexternalเพื่อretry;SIGKILLอย่างเดียวไม่พอและkernelOOM/resource-limitไม่ใช่verifiedexternal |

Fingerprintsคง input/IDs, checkpoint/source/adapter/scorerrecipe, environment/precision/preprocess/thresholds, GTdomain/population/config/routing Atomicoutputเสนอ same-filesystemtemp→flush/fsync→renameimmutablepacket→ledgerreceipt เก็บattemptID/parent/timestamps/causeproof/hashes/status/decisionทุกattempt ไม่ลบfailure/partial ไม่overwritecompleted ไม่resetcaps Recoveryที่อนุมัติภายหลังอาจทำpopulationcompleteได้เฉพาะถ้าทุกrequiredworkreconcilevalidตามacceptedpolicy Genuinefailedattemptภายใต้zero-model-retryยังไม่recoverเอง ClosedCPIresultsคงเดิม

### H.6 Resource accounting และสิ่งที่ B ต้องวัด

| Quantity | Meaning / relation |
|---|---|
| 200GiB reserve | Proposedplanningcapacityenvelope; **ไม่ใช่ measuredtotal, filesystemguarantee หรือglobalhardcap** ยังไม่มีglobalcapnumeric |
| 80GiB/system | Proposedcapต่อcheckpointinferencestream; นับphysicalnative/finaloutputs/logs/cache/tmp/attemptsรวมจริง ไม่คูณnative-referenceviewที่reuse;sharedartifactsลงledgerครั้งเดียว |
| Free50GiB | Proposedfilesystemheadroomguard ตรวจnextwrite+atomictemporarypeak หยุดก่อนละเมิด ไม่ลบผลเพื่อผ่าน |
| Admissionproposal | ถ้าคงenvelope200ต้องfree≥250GiBและBaggregateestimateรองรับ;ไม่ได้กันdiskจากคนอื่น การถึง200อย่างเดียวไม่ใช่runtimehardstop |
| Aggregatefeasibility | 7×80=560GiB potentialceilings>reserve200 จึงยังรับรองว่าfitไม่ได้ ต้องallocatedesignจากBก่อนlaunch |
| Existingpayloadestimate | 33,740,001,016bytesเป็นROIuint8payloadcomponentเท่านั้น ไม่ใช่total;historicalfreeไม่ใช่liveguarantee |

Bต้องวัดnativepersoncounts/serializedbytesต่อframe/ROI/person, native/finalactualreuse, observedcompression, metadata/log/attempt/cachegrowth, temporary+atomicwritepeak/sharedallocation และjointmemory/cleanroutetime จึงคำนวณaggregateestimateพร้อมข้อจำกัดและcapacitydecision ไม่สร้างtotal/ETAตอนนี้ Timinglatencyไม่รวมdiskwriteไม่ได้แปลว่าdiskwriteไม่อยู่storagebudget Cases64/350opportunities/seed/weights/jobsยังเดิมทุกตัว ไม่มีnewtimingjobs/recoveryjobsอนุมัติในA

**สถานะหลังรอบนี้:** นิยามหกประเด็นถูกเขียนลงPLAN/spec/tablesแล้ว ยังมีuserdesignacceptance/mandatorycapabilities/externalrecoverypolicyและBimplementationevidenceที่รออยู่ สถานะ **REVIEWED_PROPOSAL** ไม่รับรองproductionevaluatorหรือrunreadinessจากเอกสาร

## I. Specification closure และ Stage B handoff — Revision 3

Baselineคือpubliccommit `df1c4a7a546cd5ad3122916228adaaa7fad3585b`, branchmain/clean;canonical/publicplanningcopiesตรงกันก่อนแก้เฉพาะไฟล์ที่เลือก ไม่resetหรือแก้activeexecutioncode/config ไม่อ่านผลaccuracyเก่าเพื่อเลือกmodel ไม่ค้นdataset/modelใหม่ รายการcheckpointตรงuserIDsทั้ง7 ไม่มีaliasหรือเปลี่ยนweights RegistryRPR_CIHPเป็นResNet50ตามเดิม

| ข้อสังเกต | HEADเดิม / สิ่งที่แก้ | หลักฐานปัจจุบัน / ยังไม่ใช่อะไร |
|---|---|---|
| View-specificdisposition | ยังมีglobalMAPPED_CONTEXTแม้C7roleTARGETจริง;ลบglobalfield แยกC3/C7disposition/cohort/evidence | Mapping72rows+spec.mapping_schema; CIHP10/13–17เป็นcontextC3/targetC7, SapiensTARGETในdiagnosticไม่ทำC7rank |
| Emptyoutput | spec.metrics.valid_empty_predictionยังเหมารวมว่าmissedpersonจริง;แทนด้วย4แยกกรณีและRPRraw-emptynormalization | spec.metrics.empty_output_cases/E04/E07/E08;มีextentไม่mappedtargetยังmatchได้ ไม่สร้างbboxsilhouette |
| Comparisongroups | same-task/route wordingยังอาจแบ่งapplicationอัตโนมัติ;แก้เป็นAPPLICATION_C3(7)/APPLICATION_C7(4),native3×2viewsแยก | spec.comparison_groups+routes columns;35,000quality/96,248ROIและtiming/warmupไม่เพิ่ม Nativeviewreuseเดิม |
| EXACT/evidence | operationกับevidenceยังไม่แยกจริง;EXACTนิยามone-to-oneconceptเท่านั้น เพิ่มsemantic_equivalence_statusทุกtaxonomy | Sourcecategorymetadata/registryRUNbindingsเดิม;ไม่claimpixelpartitionequivalenceของSapiensหรือCIHPจากชื่อ ไม่เพิ่มoriginalheadergate |

Selectedscopeผู้ใช้ยืนยันแล้วจึงไม่ถามrosterเดิมซ้ำ Usergoalclarificationรับรองให้CCIHPเป็นselectionจริง ไม่ต้องรอCCTVและไม่เก็บdominatedmodelsด้วยเหตุเดาว่าfieldดีกว่า แต่ไม่ยกเว้นtaxonomy/conditioning/executionerrorsออกจากคะแนน วิเคราะห์สาเหตุเฉพาะที่มีevidenceไม่เดาจากQอย่างเดียว

**Selectionterms:** semanticqualityleaderคือQสูงสุดในeligiblecompletegroup;Qไม่penalizeunmatchedFPโดยตรงจึงต้องแสดงFP/F1 ไม่เรียกoverallwinner Paretoและselectednextphaseใช้mandatorycapability/priorityที่รับก่อนผล Group/population/thresholdระบุชัด main4961/.50เป็นหลัก reference/.75sensitivityไม่เลือกเงื่อนไขตามคะแนน ไม่มีC3+C7poolingหรือnative-referenceapplicationwinner Margin.005เดิมและCIflagเป็นอิสระ

**Detail/qualitative:** pertargetIoU+support,coverage/FN/FP,pre/postclipcontamination,rejectionและmatched-onlyBoundaryIoUเดิมครอบคลุมมิติที่เสนอ;boundaryไม่เป็นnewhardcriterionและต้องแสดงmatched/G_sem/G_loccoverage Commonqualitative16IDsจาก8timingstrataเลือกก่อนผลใช้ภาพเดียวกันทุกระบบ [manifest](../manifests/QUALITATIVE_REPORT_SAMPLE_DRAFT.json) ไม่มีinferenceเพิ่มและไม่เปลี่ยนผู้ชนะตามภาพรู้สึกดี

**คำตัดสินคงเหลือชุดเดียว:** PLAN§11/spec.pending_user_decisions มีCAP-GARMENT,CAP-BODY,CAP-ACCESSORY,SELECT-PREFERENCE,RECOVERY,RESOURCES-B พร้อมrecommended/alternative/effect/unknown ไม่มีabsolutepassfloorใหม่ Bodymandatoryทั้ง4เป็นข้อเสนอ ไม่ใช่acceptanceแทนผู้ใช้;bodymappingยังไม่พอพิสูจน์ไม่เท่ากับโมเดลไม่มีbodycapability Accessoriesไม่เพิ่มhardrequirementเอง

FixedTRAINreadinessIDsเสนอเริ่ม0000930แล้วSapiensเพิ่ม0021834/0001368เท่านั้นตามevidenceเดิม;Bต้องbindROIcountsก่อนdispatch ไม่ใช่unlimitedforwardbudget และไม่รันในรอบนี้

**Boundedrecoveryproposal:** model/OOMretry0;verifiedexternalเพิ่มได้สูงสุด1attempt/item(total2),batchrecoveryepoch1 ภายหลังรับpolicyและอนุมัติbatch;rawsignal/SSHdisconnectไม่พอ unknown/conflictหยุด Reuseatomiccommittedoutput/reconcilecompleteorphanโดยไม่compute เก็บpartial/attempts ไม่เลือกผลดีสุด รวมเวลา/พื้นที่ทุกattemptไม่resetbudget Timinginterruptedroundinvalidและreplacementจำกัดไม่ใช้แก้roundช้า ข้อเสนอนี้ยังไม่อนุมัติretryตอนนี้

**Bที่ส่งต่อได้:** PLAN§13มี8งานจริงพร้อมimplementation/acceptance/data/cap/stop/evidence/dependencies;specมี14expectedcasesแบบdeclarative (E01–E14) ต้องผ่านactualpacket→scorer→reporter ไม่ใช่แค่helpertests/testcount ยังไม่รันtestsในรอบนี้ ProposedTRAINceiling≤16calls (Sapiens9เดิม+CIHPapplication4/native-only3เฉพาะproofgap);แยกจากnominalbenchmarkjobsและต้องอนุมัติB/resourcebudgetแยก ใช้forwardเดียวปิดroute/map-back/residency/storage ไม่มี64frametiming/repeatedwarmupในB ใช้existingproofก่อนและไม่ต้องรันครบcap

**Resource:**200planning/80stream/free50/24hเดิม ไม่รับรองtotalfit ต้องledgerretained+shared+temporary+headroomจากBจริง เกินกรอบกลับไปresourceapproval ไม่เพิ่มprecisionfallback/resolutionchangesเพื่อให้ผ่าน ไม่มีtotalstorage/ETAแต่งขึ้น

**Riskeffects:** riskmatrixเดิม17issuesปรับeffectต่อeligibility/selectionให้ตรงMUST_FIXก่อนlaunch,CONTROL_AND_REPORTและRESIDUAL_LIMITATION ExposureUNKNOWNไม่ใช่NOและไม่claimarchitecturecausality ห้ามsemanticincompatibilityทำคนละtaskแล้วหลบด้วยfootnote Bต้องพิสูจน์commoncontract;otherwiseหยุดaffectedcomparison

**Governance:**ก่อนfreezeแก้ตามrequirement/evidence/TRAINพร้อมversion หลังfreezeห้ามpartialVALtuning ถ้าbugหยุดaffectedscopeพร้อมหลักฐานและconsistentcorrectionproposal ทุกbatchอนุมัติรันจนterminalแล้ววิเคราะห์qualityรวมครั้งเดียว ดูhealth/completenessระหว่างรันเท่านั้น

สถานะ: **DOCUMENTATION_CLARIFIED / REVIEWED_PROPOSAL / DECISIONS_PENDING**;ไม่DESIGN_READYเพราะmandatory/selection/recovery/resourceacceptanceและBverificationยังค้าง หลักฐานconsistencyเป็นdocumentationacceptanceเท่านั้น ไม่executionreadiness ผลตรวจอยู่ `runs/specification-handoff-20261021T092521331823Z/CONSISTENCY_REVIEW.json`

Proposed B resource ceiling clarification:≤16parser TRAIN frame-system calls,≤32external ROI tasks and≤7freshfrozenYOLO TRAIN calls (one initial0000930 per co-resident application profile, only if exact proof missing). ExistingfrozenTRAINopportunity metadata gives2/6/2 for0000930/0021834/0001368;read-only counts, no new model execution. No nominalquality/timingjob increase.
