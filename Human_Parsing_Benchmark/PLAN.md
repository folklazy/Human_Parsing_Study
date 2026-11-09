> Reporting audit 2026-11-09T17:40:23.483262+07:00. Completed shared-view confusion and aligned CIHP/CCTV report sections from saved counts. Exact 18 jobs and 72 target rows verified. Current report includes diagnostics navigation, raw counts and source hashes.

> Reporting supplement 2026-11-09T17:19:52.672427+07:00. User requested equal four-target Macro4-local and saved-log timing tables. Accepted masks/scores are the inputs. Completed 18 derived summaries and CIHP/CCTV timing coverage checks. Current report contains definitions, timer scopes and source hashes.

> **Shared scoring COMPLETE (2026-11-08T16:01:46.245563+07:00):** CIHP9x5000 and CCTV9x90 exact; protocol SHARED_C3_PART_FACE_LOCAL_V1,13CPUcases plus actualpacket/resume acceptance and independent526,086-part arithmetic/membership verification. Main report: reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md; no automatic new inference or extra metric experiments. Existing native/globalC3/C4 and CCTVFace-domain remain historical separate views.

> **User-approved shared scoring — 8 November 2026:** CPU-only rescoring of saved controlled-ROI predictions for all nine checkpoints on CIHP5000 and user-accepted CCTV90. New frozen protocol `protocol/SHARED_C3_FACE_LOCAL_V1.json`: equal target mean of per-GT-person-part Hair/Upper/Lower IoU; separate tight-GT-box Face-local IoU; common geometry-only mask-IoU0.50 matcher,0.75 diagnostics. No inference, mapping/settings tuning or changes to old C4/native results. Source data domains/ontology limitations remain disclosed. CPU acceptance13cases PASS before new scores; exact populations and GT supports are materialized from actual bindings.

> **Quality execution closure (2026-11-08T01:22:12.700583+07:00):** Controlled CIHP ROI predictions/scoring are STRICT_COMPLETE for all nine checkpoints, exact 5,000 IDs each. The sequential finish queue is terminal; do not relaunch workers. Next: consolidate the existing canonical controlled-run metrics, retaining implementation/route provenance. Live/clean speed remains pending and is not covered by quality completion. [Evidence](runs/cihp-sequential-finish-20261106T105503Z/TERMINAL_VERIFICATION.json) / [Report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md).

> **Latest operator order (2026-11-06T17:56:51.856783+07:00):** Pause1B only during CPI preparation/diagnostic, then resume remaining1B before CPIConvNeXt. CPI_R50 is already complete. Sequential queue `cihp-sequential-finish-20261106T105503Z` requires strict5000 first-job closure and exited processes before the next controller; never concurrentGPUworkers. Keep source/checkpoint/FP32/crops/ownership/GT/scorer frozen; model-local CPI_FEATURE_BRANCH_SCHEDULE_3 is bound to the new ConvNeXt diagnostic/config and mixed-revision provenance. No wall-time stop, no model/OOM retry/fallback. [Report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md).

> **User operational amendment (2026-11-06T17:16:27.279851+07:00):** User explicitly directs Sapiens1B to finish exact5000 without the24h wall-time stop. A fresh linked continuation may disable only this model's time guard; preserve elapsed history, source/config/checkpoint/GT/YOLO/scorer behavior, finite pending-call budget and VRAM/80GiB/50GiB guards. No automatic model/OOM retries, no other checkpoint or SAM service. [Report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md).

> **Operational update (2026-11-06T17:05:51.585401+07:00):** 1B stopped at the existing24h guard with4,222complete frame packets and778missing frames; no OOM in this stop. Seven systems remain complete;ConvNeXt remains held incomplete. Before continuation, reconcile complete/partial packets and obtain an explicit per-model time-budget amendment; preserve cumulative time and frozen scientific settings. No new inference is authorized by this status update. [Current report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md) / [STATUS](STATUS.md).

> **Historical operational update (2026-11-05T15:33:58+07:00):** The interruption continuation recovered Sapiens0.8 to exact5,000 without repeating parent inference; the existing queue is now on1B, then stops. ConvNeXt is held incomplete. Scientific protocol and limits are unchanged. [Current report](reports/CIHP_CONTROLLED_ROI_RUN_TH.md) / [STATUS](STATUS.md).

> **Controlled CIHP implementation — 2026-11-02T19:05:31.621985+07:00** CPU acceptance13casesผ่านสองenvironments; frozenqualitymanifest5000frames/24,062ROIs×9พร้อม. GPU TRAINgateยังpendingก่อนVAL. [รายงานรอบใหม่](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). Live/clean speedphaseยังpendingแยกจากqualityqueue

> **Comparability review — 2026-11-02T18:03:20.041685+07:00:** ตรวจ CIHP กับ CCTV90 และคำนวณ aggregation sensitivity แล้ว: input route, ownership, Face domain และหน่วยเฉลี่ยต่างกัน จึงไม่ใช่การวัดเงื่อนไขเดียวกันข้าม dataset. [รายงานตรวจละเอียด](reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md) · audit 9 systems / 36 targets PASS; ผลเดิมคงเดิม. Controlled CIHP ROI ยังไม่รันและยังไม่ผ่าน readiness.

> **Latest completed work (2026-10-30T11:11:02.869193+07:00):** Common C4-P revision2 **9/9 COMPLETE**. CPI saved-only scoring plus seven accepted results reused. [Authoritative result/analysis](reports/CIHP_COMMON_NINE_RESULTS_TH.md); [STATUS](STATUS.md). Earlier closures/scopes below are historical. No new inference or protocol change is authorized by completion.

> **Current closure review (2026-10-30T10:44:14.373500+07:00):** Native20 6/6 COMPLETE and C4-P revision2 7/7 COMPLETE, 9 unique checkpoints. [Current handoff](reports/CIHP_EVALUATION_HANDOFF_TH.md) / [STATUS](STATUS.md). Earlier scope/outcome sections below are dated history; no new execution is authorized by this closure. CPI common-view scoring and final selection remain separate work.

> **Current scope supersedes prior full-evaluation-pending statements:** approved full C4-P revision2 on official CIHP5000; saved-only four systems + Sapiens2 0.4B. [Full config](configs/cihp_sapiens_c4p_full.json) / [report](reports/CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md). Stop after this batch.

## คิวอัตโนมัติและการเก็บเวลาแยกขั้นสำหรับ controlled CIHP

อัปเดต 2026-11-02T18:51:46.168259+07:00 (Asia/Bangkok). ผู้ใช้ยืนยันให้เก็บเวลาแต่ละขั้นและ pipeline สำหรับวิเคราะห์ภายหลัง พร้อมกำหนดให้วิเคราะห์อันดับหลัง batch ปิด. สถานะ **QUEUE_AND_TIMING_REQUIREMENTS_DEFINED / IMPLEMENTATION_AND_READINESS_PENDING**. หัวข้อนี้เป็นข้อกำหนดของรอบใหม่ การตรวจ source พบ runner CCTV ปัจจุบันมีเพียง synchronized `adapter_elapsed_seconds` ซึ่งครอบ CPI native file I/O จึงต้องเพิ่ม instrumentation ใน execution revision ใหม่ก่อน launch

### การเดินคิวและจุดหยุด

รันหนึ่ง GPU worker และหนึ่ง checkpoint ในแต่ละครั้งตาม frozen roster QANet → M2FP → D2FP → RP-R-CNN → CPI R50 → CPI ConvNeXt-B → Sapiens0.4B → 0.8B → 1B. เมื่อ checkpoint จบ ให้ reconcile expected/accepted/missing/duplicate/failed/invalid และ atomic outputs จากนั้นปิด process/release model memory ตรวจ resource gate ใหม่แล้วเปิด checkpoint ถัดไปอัตโนมัติ. ขั้นตอนปกติเดินต่อได้ด้วย detached controller โดยผู้ใช้ดู progress ได้ตลอด

| เหตุการณ์ | การดำเนินการของ controller |
|---|---|
| ครบ5,000 unique IDs และ artifact checksผ่าน | ปิดผล checkpoint แล้วตรวจทรัพยากรเพื่อเริ่มตัวถัดไป |
| Model-local OOM/CUDA failure | บันทึก failed attempt/partial outputs ปิด process ของ checkpointนั้น และคง primary null. checkpointอิสระถัดไปเริ่มได้เมื่อ GPU health และ bindingsผ่าน หากสาเหตุยังจัดประเภทไม่ได้ให้หยุดคิว |
| Shared source/GT/cache drift, scorerผิด, atomic corruptionที่กระทบส่วนกลาง | หยุดคิวพร้อมหลักฐานและรอการแก้ที่มี revision ชัดเจน |
| Resource guard เช่น disk/freeVRAM/timecap ไม่ผ่าน | บันทึก QUEUED_RESOURCE หรือ STOPPED_RESOURCE ตามขอบเขต wait/timecapที่ freeze. เวลาเข้าคิวแยกจากexecution การเปิดต่อใช้ resource gateที่ผ่านแล้ว |
| External interruption | เก็บ immutable attempt history และเข้าสู่ reconciliation ก่อน continuation |
| โมเดลสุดท้ายเข้าสู่ terminal state | ปิดbatch สร้างcompletion report แล้ววิเคราะห์คุณภาพรวม |

Automatic model/OOM retries=0. การเริ่ม checkpointถัดไปอาศัยcompleteness/integrity/resources ไม่อาศัยคะแนนสูงต่ำ. ระหว่างrunตรวจhealth, progress, geometry/nativeIDs, ledgerและdisk/VRAM; เก็บscore statisticsที่protocolกำหนดได้ การอ่านrank/วิเคราะห์เปรียบเทียบทำหลังbatchterminal. ผู้ใช้สามารถขอสถานะได้โดยไม่มีผลต่อ scientific settings

Sequential executionลดการแข่งขันระหว่างcheckpointของเรา. งานอื่นบนGPU, CPU/I/O contention, cache, thermal stateและลำดับrunยังส่งผลต่อlatency. Shared GPU quality observationsต้องผูกtelemetryและfailure history. ไม่มีข้อสรุปzero biasจากการเรียงคิวเพียงอย่างเดียว. CPU scoringที่กินmemory/I/Oมากต้องอยู่นอกclean timing windows

### ขอบเขตเวลาที่ต้องเก็บ

| Field/กลุ่ม | จุดเริ่มและจบที่ต้องระบุ | หน่วย |
|---|---|---|
| `queue_wait`, `model_load`, `warmup`, `closure` | แยกแต่ละช่วงจากเวลาที่ประมวลผลภาพ | s ต่อattempt |
| `decode_read` | ก่อนอ่านไฟล์จนได้decodedRGB | ms/ภาพ |
| `yolo_preprocess`, `yolo_transfer`, `yolo_forward`, `yolo_postprocess` | YOLOจริงด้วย frozenweights/settings และmaskคืนพิกัด | ms/ภาพในlive timing pass |
| `detector_cache_read` | อ่าน/ตรวจcacheที่ใช้ในqualityroute | ms/ภาพในcached pass |
| `crop_prepare` | สร้างcrop/context/ข้อมูลgeometryของopportunities | ms/ภาพและROI |
| `parser_preprocess`, `parser_transfer` | resize/padding/normalize แล้วส่งinputเข้าGPU | ms/ROI |
| `parser_forward` | model executionตามnativecontract รวมinternaldetector/branchesที่โมเดลใช้ | ms/ROI |
| `parser_decode_mapback` | decoder/postprocess, unpadding/resizeและargmaxที่อยู่นอกforward, ส่งผลกลับCPU | ms/ROI |
| `association_ownership` | เลือกdesignatedinstance/clipYOLOmask/compose | ms/ROIและภาพ |
| `export_commit` | serialize/hash/write/atomiccommitตามdurabilitycontract | ms/ภาพ |
| `evaluation` | อ่านGTและคำนวณmetric | ms/ภาพแยกจากproductionpipeline |
| `cached_route_wall` | อ่านภาพ/cache → crop/parser → atomicoutputcommit | ms/ภาพจากwalltimerจริง |
| `live_route_wall` | อ่านภาพ → YOLOจริง → crop/parser → atomicoutputcommit | ms/ภาพจากwalltimerจริง |
| `batch_wall`, `active_work`, `downtime` | run/attempttimeline ครอบsuccess/failure/recoveryและwaitingแยก | s ทั้งชุด |

ทุกช่วงใช้monotonic high-resolution wall clockและกำหนดCUDA synchronizationที่boundaryเพื่อครอบงานasync. OptionalCUDAeventsเป็นdevice diagnosticแยกจากwall latency. ระบุexclusiveหรือinclusiveและparent stageต่อtimer. Composite APIที่แบ่งไม่ได้ให้เก็บinclusiveชื่อชัด พร้อมsubstage=nullและเหตุผล. CPIมีnativefileI/Oภายใน API ต้อง instrumentขอบเขตจริงก่อนอ้างforward-only. Closureตรวจผลรวมexclusive stagesกับmeasuredtotalพร้อมunattributedoverheadและnested spans จึงป้องกันdouble count. การsynchronizeหลายจุดมีoverhead ต้องเก็บinstrumentationmodeเดียวกันในcomparisonและรายงานขอบเขตนี้

Parserคำนวณnativeclassesทั้งหมดในforwardครั้งนั้นแล้วprojectเป็น4targets. เก็บprojectionเวลาแยกได้ ส่วนforward timeรายclassไม่สามารถแยกจากsharednetworkด้วยการหาร4. Per-imageใช้เวลาwallที่จับจริงและจำนวนROIของภาพนั้น พร้อมผลรวมROIworkเป็นอีกคอลัมน์. กรณีzeroROIมีparserwork=0แต่decode/detector/exportยังมีเวลา กรณีreuseที่ไม่มีtimerให้missing/nullตามหลักฐาน

### Quality pass และ clean timing pass

Quality5000ใช้YOLOcacheเดิมและบันทึกstage timingsพร้อมresourceobservations. ผลที่ใช้งานGPUร่วมอยู่ในกลุ่มdiagnostic. การทำlatencyrankingต้องมีclean timing passที่ workload, precision/settings, instrumentation, residencyและI/Oscopeตรงกันทุกระบบ

reuseรูปแบบที่ตรวจจากงาน YOLO จริงใน workspace. ตัวอย่างอ้างอิง `YOLO_Large_Seg_MOTS20_Benchmark/src/benchmark.py` ฟังก์ชัน `timing` และ `src/report.py` มี100ภาพ×3รอบ,10warmups,stage timings,Mean/P50/P95และcontamination flags. `src/repeat_clean_timing.py` เก็บ original pass พร้อมprovenance. อ่านเพื่อยืมหลักการเท่านั้น การออกแบบคิวใหม่ต้องมีbounded waiting ตามpolicyปัจจุบัน

ข้อเสนอ bounded timing workloadของรอบใหม่ใช้100CIHPframesที่เลือกด้วยhash-orderจากexact5000ก่อนดูquality/runtimeผลใหม่ seedและIDsต้องfreezeในmanifest. รวมโอกาสzero/multipleROIผ่านการรายงานcoverageจากYOLOcache. หากเปลี่ยนเป็นstratifiedsampleต้องประกาศsamplingweightsและclaimของsampleก่อนrun. วัด3รอบโดยใช้cyclic model-order offsets0/3/6เพื่อให้แต่ละmodelกระจายตำแหน่งในสามช่วงของคิว และใช้frameorderเดียวกันทุกmodelในแต่ละรอบ. Qualitypassยังคงrosterorderเดิม

สำหรับprocessใหม่กำหนดwarmupไม่เกิน10framesจากprefixของfixedtimingsampleและเก็บactualROI/modelcallcount. จำนวน100×3และwarmupเป็นข้อเสนอtimingแยกจากqualitybudget. ต้องคำนวณจำนวนROIcalls/disk/timecapและfreezeconfigก่อนlaunch. ไม่ใช้งานtimingเติมcanonicalqualitypredictionsหรือเลือกattemptที่คะแนนดีที่สุด

Live timingpassต้องรัน frozenYOLOกับ parserในrouteเดียวกันบนsampleจริง เก็บYOLO/parserjoint-residencyVRAM. กำหนดresidentสองmodelเป็นcontractเริ่มต้นและตรวจreadinessแต่ละคู่. คู่ที่resourceไม่ผ่านมีสถานะblockedตามจริง การเสนอload/unloadrouteเป็นconfigurationอีกแบบต้องระบุlifecyclecostครบก่อนใช้เทียบ. ห้ามนำcachedYOLOreadtimeหรือYOLObenchmarkคนละdatasetมาทดแทนliveYOLOtime. Timingpacketsอยู่freshprivateoutputแยกจากcanonicalqualityและbudgetคิดค่าliveYOLOcallsด้วย

หากมีexternalGPUactivityหรือcontaminationตามgateที่freeze ให้รอบนั้นเก็บเป็นdiagnostic. ถ้ายังไม่มีcleanroundsที่ครบเงื่อนไขให้cleanranking=unavailable. ไม่เลือกช่วงที่เร็วที่สุดมาแทนทั้งรอบ และไม่ปล่อยautomaticrerunไม่จำกัด. Freezeเวลารอคิวและจำนวนattemptก่อนexecute resourcepolicyใช้sharedqualityได้ขณะclean timingรอresourceที่เหมาะสม

### ข้อมูลสำหรับวิเคราะห์ภายหลังและการตรวจรับ

เก็บหนึ่งledgerที่มีrun/segment/attempt/model/checkpoint/source/config/protocol/environmenthashes, imageID/ROIopportunityID, reused/new, purpose, image/crop/tensorgeometry, nativeclasscount, status, UTCtimestampและmonotonicdurations. เก็บtimerboundary/inclusive-parent, decoder/device/precision/TTA, ROIcountและartifactbytes. Telemetryเก็บGPUUUID/PID, externalprocessmemoryตามสิทธิ์ที่อ่านได้,utilization/temperature/clocks, freeVRAM, allocated/reserved/deviceusage, CPU/RAM/disk/I/O observationsและsamplinginterval. ข้อมูลallocatorกับwholedeviceusageมีคอลัมน์แยก

สรุปรายstage/ROI/ภาพ/ทั้งชุดด้วยcount, coverage, sum, mean, median/P50, P95,stdและmin/max พร้อมsampledefinition. FPSของscopeหนึ่งใช้จำนวนframeที่ประมวลผลหารเวลารวมของscopeเดียวกัน. รายงานfailedattemptcostและqueue/model-load/warmupแยก คงrawrecordsทุกattempt. Stage timingไม่ใช่latencyรายtargetclass. PeakVRAMของlive routeรวมYOLO+parserresidencyและoverlappingbuffersที่วัดได้จริง

Acceptanceก่อนlaunchต้องผ่าน timerboundaries, exclusive/inclusiveaccounting, asynccompletion, zeroROI, multiROI, emptysemantic, reusedmissingtime, exceptionflushing, atomicledger/continuation และguardที่sourcebindingตรง. ตรวจoutputequivalenceของinstrumentedadapterกับacceptedadapterบนboundedreadinesscasesโดยไม่แก้expectedvaluesตามผล. Reportต้องย้อนกลับถึงactualrecordและคำนวณtotal/coverageได้ พร้อมnormalentrypointprogressและautomaticqueueclosure. สถานะปัจจุบันเป็นข้อกำหนดที่บันทึกแล้ว ส่วนinstrumentation/controller/liveYOLOjointreadinessและnewrunยังpending

# Human Parsing Benchmark — current plan

**CIHP_NATIVE_SIX_READINESS** · 28 October2026 UTC. User explicitly adopts [CIHP native Parsing9 plan](proposals/CIHP_NATIVE_PARSING9_CODEX_PLAN_TH_20261028.md); it supersedes conflicting CCIHP-selection/7-checkpoint design provisions. Historical configs/results remain immutable and available in Git history and legacy study. This change authorizes preparation, implementation and first-six execution when readiness passes; it does not authorize Sapiens before matrix, color work or model training.

## Scope and sequence

CIHP native only →6CIHP checkpoints →native results/report →semantic matrix →Sapiens0.4/0.8/1B on sameCIHP IDs →color later. Ninja deferred; no extraction/read/whole-distribution comparison dependency. YOLO26x frozen.

Firstsix: QANet_CIHP_HRNetW48_512x384, M2FP_R101_CIHP, D2FP_R101_CIHP, RPR_CIHP(R50), CPI_R50_CIHP, CPI_ConvNeXtB_CIHP. [Exact roster](registry/CIHP_NATIVE_ROSTER.csv). Checkpoints/config/source are bound in [executionconfig](configs/cihp_native_six.json). Prior closed CPI incomplete scores are historical, not repaired/reused as this run's accuracy.

## Data and population

Shared datasets/CIHP already extracted. Do not re-extract. User provides original download provenance through Engineering-Course/CIHP_PGN README GoogleDrive; no publisher digest assertion. Use native labels20includingbackground, Dress6, not CCIHPFaceMask6. Category_ids/Human_ids/Instance_ids remain separate. TRAIN28280/VAL5000/TEST5000;testGT unavailable, not a corruption claim. Official VAL5000 is primary, new [populationmanifest](manifests/CIHP_NATIVE_VALIDATION.json), not oldCCIHP4961. Exact overlaps retained and disclosed, no score-based exclusions. Actual decoder/split/label/association evidence required; no source repair. Dataset-wide physical ownership accuracy not certified from automated checks.

## Routes and contracts

QANet: native externalROIAlign on frozen predictedYOLO boxes, postparseYOLOmaskownership, unowned integerplanes retained. Otherfive: native fullframe/internaldetector orqueries, preserve allnativeintegerplanes/extents/confidences, prediction-onlyone-to-oneYOLO bboxassociation0.50;noGT prediction input or extraYOLO pixelclip. Native referencesungated derivedfromsameoutputs, separatelyreported. Identity provenance bothnative/conditioning;nativeidentitycountN/AforQANet vs0nativecapabledetection. Semantic-empty withvalidextent retained;RPR/CPIallBGnativeplanehas no nonemptyderivedextent, preserve rawentrydiagnostic;notmalformed. UnknownIDs/malformedoutputs failcontract.

## Metrics fixed before VAL scores

Primary globallyaccumulated native20mIoU includingBG, foreground19secondary/perclassIoU/support;zero-union0 follows inspectedM2FP CIHP SemSegEvaluator epsilonbehavior, not an absentclass=1 reward. No CCIHPprojection/rejection of nativeDress. Hair2/Face13/UpperClothes5/Pants9/Skirt12/Dress6/Coat7 remain separate in native reports; no heuristic Dressupper/lowersplit. Commonminimumview deferredtomatrix. NativepersonmaskIoU matching0.50/0.75;maxcardinalitythensumIoU, stableIDs. Coverageaware perpersonforegroundmacroIoU sumsGT-personcontributions/G_sem, missed0;FP/F1alongside, not officialAP/PCP. GlobalBG0valid;documented255semanticignore;unknownnot0. Hpositive/C0 retainsGTlocation and nativebackgroundlabel;noautoVOID. Semanticglobal/instanceevaluationare distinct.

## Readiness and execution

CPU: fullRGB+3GT decodeVAL,3fixedTRAIN;integerdtype/labels/shapes/EXIF,splitandhashidentity,instanceassociations,GTdiagnostics16fixedIDs;targetedactualpacket→scorer→serializedreport hand-countedcases. Reuseexistingcheckpoint/source/smoke evidence; newisolatedadapterswithnativepreprocessing, no hiddenOOMretry/CPUfallback. SixTRAIN readinesschecks initial0000930; additional0021834/0001368onlyifclosingconcretegeometry/resourcegap. Use thoseoutputsfor resourceestimates; no unboundedGPUtests.

Afterready freeze exact config/input/source/environment identities and commit snapshot before VAL. FullVAL5000perfirstsix; preserveSTRICT_COMPLETE null main score for anyincompletepopulation, retain allcandidate rows/failures/pending. Modelretry0, noCPU/FP16/resolution/TTAfallback. Firstmodelerror stopsaffectedstream ratherthan repeatfailures throughoutVAL;otherindependents continue. Shareddata/contractfailure stopsdependentwork. Resumeonlymatchingfingerprints,committedartifactsorreconciledcompleteorphan;unattemptedcontinuationallowedundercurrentbatchscope,failedinputsneverretriedautomatically. Preserveattemptlogs/partials. Uncertainexternalinterruption stopsaffectedrun; no arbitrary retryuntilspecificrecoverybindingexists.

Resourcecaps:free50GiB,80GiBpercheckpointstream,24hpercheckpoint;200GiBplanningnotproventotal. Sampleactualoutputbytes/nativecountsandtemporarygrowthbeforelaunch. Declaredmaxpersonquery/outputcountpernativeconfig,noGTdroppingtofit. If budgetcannot support5000, predeclarecommonstratifiedpresentationsubsetbeforeanyVALscores;callsubsetresults, no5000claim. Do notchoosepopulationfromscores.

Timing: inline synchronizedFP32 parserpipelineafterdeclaredTRAINwarmup,preprocess/forward/nativepostprocess/association/mapbackincluded;JPEGread/export/scoring/modelinitexcluded. QualityusescachedYOLOthereforeend-to-endYOLOlatency/FPS N/A,neverusecachedreadasdetectorinference. NoGPUcontention;recordpeakallocated/reservedandstage/personunits. Noarchitecture-onlycausality orCCTVreadyclaim.

## Reporting and governance

FreezeandrunbatchwithoutpartialVALranking/tuning. Correctnessbug:stopaffecteddependencies,preserveevidence,consistentversionedcorrectionforallaffectedsystems. Allsixcompleteonlywhenallinputs/scoringcomplete;otherwiseprogressreportwithnullheadlineandremainingjobs,not six-complete/winner9. Store nativehardmasks,preclipmaps,scores/extents/RGBidentity/transforms, atomicpackets,attemptledger,sufficientstatistics,environment/hardware/config/sourcehashes. Inferencefingerprintseparateevaluationfingerprint. FixedqualitativeIDsselectedbeforemodelscore. No fullprobabilityrecoverabilityclaimfromhardlabels. Gitcompactcode/config/manifests/results;bulkoutsideGit. Log/commit/pushworkunitsusingexistingpublicationcheckout,notYOLOrepositories.

## Controlled continuation and reporting correction — 28 October2026

User explicitly authorizes reconciliation after original controller interruption, then disjoint D2FP remaining work and RPR/CPI2. [Correction/continuation report](reports/CIHP_CONTROLLED_CONTINUATION.md) is the operational record, not a new master plan. Frozen config/source/data/model policy remains unchanged; fresh segment manifests bind parent, reused/pending IDs and cumulative resources. Recompute accepted statistics from validated saved masks/scoring artifacts, never re-infer completed images or select outputs by score. Original LAUNCH/RUN stay unchanged even if stale; current STATUS/continuation state describe actual liveness.

Interpretation correction: primary table is YOLO-conditioned application pipelines on native CIHP labels, not all official native parser results. Current timing is adapter diagnostics: CPI internal native file I/O is timed, global semantic composition/scoring is outside; no clean parser-only/end-to-end speed ranking. Historical TRAIN RPR/CPI fingerprints are not standalone cache identities. Retained hard labels support remapping under stored ownership, not all probability/native-confidence metrics. These clarify actual evidence without changing scoring settings mid-run. Matrix/Sapiens/color remain stopped for this continuation.

## Current execution scope — D2FP-only round, closed

Latest user instruction restricts execution to D2FP CIHP until5000 IDs only; it supersedes the earlier automatic remaining-model queue authorization. Inspection found D2 already complete and the old controller terminal. No new inference/controller or queue change is needed. Closure evidence is in runs/cihp-native-six-20261028T034103254470Z/D2FP_ROUND_CLOSURE.json. Preserve historical setup attempts/results; do not retroactively claim the old controller stopped before RPR/CPI setup. No future RPR/CPI/matrix/Sapiens/color execution without a separate scoped instruction. The six-model frozen config describes historical experiment semantics, not a renewed execution authorization.

## Current execution scope — RP-R-CNN CIHP only

Latest user authorizes RPR_CIHP readiness/execution on the unchanged nativeCIHP5000/frozen protocol, with a hard queue boundary before CPI. D2FP closure remains complete/historical. Preflight `rpr-cihp-preflight-20261028T153224395816Z` is BLOCKED by existing external GPU compute PID under the unchanged no-contention policy; no worker/controller or auto-wait/retry was launched. The current attempt ends blocked. On a later continuation recheck actual resources once, retain historical blocked attempts, and run only missing RPR IDs in a fresh scoped segment when readiness passes. Existing six-model config is scientific provenance, not authorization to execute its full queue. No CPI/matrix/Sapiens/color/new experiment scope. See current STATUS/report for evidence.

## Resource-policy amendment — RPR shared-GPU quality only

Latest user requests RPR continuation despite another GPU user. Effective operational policy now permits GPU coexistence for this RPR quality round, recorded separately as RESOURCE_POLICY.json. Original frozen scientific config is retained as provenance; its exclusive admission/profile is explicitly overridden in the new resource-aware wrapper, not silently edited. Inference/preprocessing/ownership/scoring/FP32 and original24h/80GiB/50GiB/model-retry0 limits are retained. Timing and memory diagnostics are not comparable clean rankings. One-model controller stops after RPR, no CPI/matrix/Sapiens/color. No arbitrary automatic restart or other-process changes.

## Current authorization — CPI R50 CIHP only, original GPU admission

Latest user authorizes CPI_R50_CIHP readiness/run under original frozen scientific and resource policies; stop before CPI ConvNeXt-B. RPR shared-GPU override is model/round-specific and does not transfer. Current preflight resource-blocked by external compute process, so end without launch/poll/retry or policy change. QANet/M2FP/D2FP/RPR results are closed and preserved. Canonical-source current overview is a derived navigation table, not a new run/ranking. On later continuation verify actual resources/artifacts, then create only a scoped CPI_R50 segment when readiness passes. No ConvNeXt/matrix/Sapiens/color/training.

## Explicit resource amendment — CPI R50 shared-GPU quality only

Latest user explicitly authorizes GPU sharing for CPI_R50_CIHP quality/completeness, superseding its prior no-external-PID gate only. Bind a separate effective RESOURCE_POLICY.json and CPI-specific single-model controller/wrapper. Preserve all scientific config, weights, preprocessing/FP32/determinism/ownership/GT/scoring/population and existing guards/failure policy; required warmup, no solo/shared comparison or other-model rerun. Shared CPI native file-I/O timing is diagnostics, not speed ranking. Exact-ID/packet reconciliation and STRICT_COMPLETE close only CPI_R50; never start ConvNeXt/matrix/Sapiens/color. Read-only CPI progress command is documented in STATUS.

### CPI R50 scoped round terminal — 2026-10-29T00:40:16.529470+07:00

[Current report](reports/CIHP_CONTROLLED_CONTINUATION.md) and [completion](runs/cihp-native-six-20261028T034103254470Z/cpi-r50-shared-20261028T172951337299Z/COMPLETION.json): explicit shared-GPU admission used, setup/warmup PASS, VAL CUDA OOM at0000018,3/5000 committed/verified and1failure; STRICT_COMPLETE main null, queue stopped. No scientific policy/config/source changes, no retries or next-model authorization. This is the outcome of the authorized attempt, not a change to metric/selection policy.

## Current scoped authorization — CPI ConvNeXt-B only (2026-10-29T01:17:06.416805+07:00)

UserpausesR50andexplicitlypermitsConvNeXtsharedqualityunderunchangedscientificsettings. RequiredTRAINwarmupthenoneVAL0000018diagnostic(separate,nevercanonicalreuse);onPASScanonicalofficial5000freshsegment,otherwiseSTOP/report. Includesdiagnosticcostin24h/80GiBbudget,freeguard50GiB,noautoretry/fallback/settingschanges/othermodel. [Currentreport](reports/CIHP_CONTROLLED_CONTINUATION.md), [policy](runs/cihp-native-six-20261028T034103254470Z/cpi-convnext-shared-20261028T181609262813Z/RESOURCE_POLICY.json), [exactplan](runs/cihp-native-six-20261028T034103254470Z/cpi-convnext-shared-20261028T181609262813Z/SEGMENT_PLAN.json). Timingonlydiagnostics,STRICT_COMPLETE;noautomaticmatrix/Sapiens/color.

## Accepted task-order amendment — reporting four complete before CPI closure (2026-10-29T01:56:19.221143+07:00)

User explicitly pauses CPI R50/ConvNeXt-B, preservesallartifacts/OOMhistory/mainnull, and authorizesreportingfourCOMPLETE systems plus preliminaryclassmatrix now ratherthan waitingforCPI. This doesnotexclude/cancelCPI, alterfrozen native20protocol/config/scorer or authorize newmodelinference. Native4resultsand16frozenIDsuseexistingartifacts only; nativeCIHP↔Sapiensmappingispost-resultsdraft, notaccepted/executable/frozen. NoCPIretry/OOMwork/Sapiens/color/training/CCTV. Currentdeliverable [CIHP_FOUR_MODEL_RESULTS_TH.md](reports/CIHP_FOUR_MODEL_RESULTS_TH.md). Furthercommon-viewscoring needsreviewedclass/domain/eligibilitydecision; nottriggeredbythismatrix.

## 2026-10-29T07:51:06.417630+07:00 — common-view design continuation (proposal only)

[CIHP–Sapiens common-view protocol](reports/CIHP_SAPIENS_COMMON_VIEW_PROTOCOL_TH.md) เป็นข้อเสนอหลัก C4-P projectedapplicationagreement/4targets กับ CIHP reference โดยเปิดเผยFace_Neck approximation, non-Dress garmentfamilies และ validOTHER;C3sensitivityไม่แทนminimumfour. Draftspec/49-IDprojectionแยกจากnativeconfig;matrix/bindingsเดิมคงhistoricalproposal. Scorer/route/FPFN/domain/persondenominatorsและ≤7-call0.4Bpilotเป็นงานส่งต่อที่ยังไม่authorized/implemented ไม่มีinference/fullcommonscoring/activeexecutionchangeในรอบนี้ Native20results/configsและCPIpausednullคงเดิม ทำหลังเห็นผล4ระบบ ไม่preregisteredหรือVALtuning

## Scoped implementation/pilot authorization — 2026-10-29T08:20:28.215191+07:00

Latestuserexplicitlyauthorizescommonpipelineimplementation/CPUacceptanceandconditionalSapiens2_0.4b7-callpilotonlywithSHARED_GPU_QUALITY_ONLY. Geometrycanonicalmatching+identicalgeometryfallback/ambiguityreplacesnumericGT-IDordering;C3globalonly/nosecondpersondenominator. Mapping/Faceproxy/OTHERunchanged. Nativefrozenpipeline/results/CPIpausedimmutable. [Currentreport](reports/CIHP_SAPIENS_04B_PILOT_TH.md); runcommon-c4p-pilot-20261029T010410394659Z. Fullcommon5,000/othermodels/training/color/CCTVnotauthorized.

## 2026-10-29T08:31:06.729574+07:00 — binary-cache setup correction, same scientific protocol/budget

Parent common-c4p-pilot-20261029T010410394659Z strictloadPASS then SOURCE_BINDINGSINVALID:uint8binary0/1cacheexpectedbool, modelcalls0,VAL0,noOOM. Keepfailure/process/log/ledgerhistory. Losslessvalidatedbinaryastypeboolonly;23CPUoraclecases+actual7cacheprobes+4savednativepacketintegrationsPASS. Fresh common-c4p-pilot-20261029T010410394659Z-binary-cache-fix usesparentGTbindingsandmaxaggregate7calls (parent0),oneactualforwardattempt/image,noautomaticmodel/OOMretry.80GiBaggregatesbothsegments,time24hfromparentstart,free50GiBunchanged. Revision2mapping/Face/OTHER/C3/scoringunchanged;newimplementationhashesandsetupcorrectionrecordbeforelaunch. Nextcommitfix/readinessthenboundedpilotonly.

## 2026-10-29T08:45:10.351455+07:00 — scoped common pilot closed; budget consumed

Runcommon-c4p-pilot-20261029T010410394659Z-binary-cache-fix PILOT_PASS:1TRAINwarmup+6specifiedVAL=7calls,6complete0failed/invalid/noOOM/fallback/retry. Parentsetupinvalid0forwardcallsretained;losslessbinarycacheconversionfixedwithoutscientificchange. CPU23/saved4×1/cache7PASS,GT-onlyG_loc17520/G_sem_C417454,6savedmaskrescore/atomiccontract/QANetextentparityPASS. Nativefrozen18hashes/source/resultsunchanged;CPIpaused. [Closure](reports/CIHP_SAPIENS_04B_PILOT_TH.md). Noautomaticrestart/othermodel/full5,000;fullqualityproposalpossiblebutrequiresseparateacceptedlaunchconfig/approval. Oldpilotconfigflagsdescribetheconsumedauthorization,notnewpermission.

## 2026-10-29T13:04:01.363721+07:00 — CPI manual CLI preparation only

ผู้ใช้ขอคำสั่งรัน CPI ทั้งสองตัว จัดทำ [manual continuation CLI](docs/CPI_CONTINUATION_COMMANDS_TH.md) ที่ใช้ frozen worker/scientific settings เดิม แต่แยก operational manifest, output location และ cumulative reconciliation. CPU5casesและ existing3/113packet checksผ่าน ไม่มี inference/warmup/retryจริงใน work unit นี้ ไม่เปิด Sapiens/full common evaluation. Operatorต้องเรียก `--execute` เฉพาะรุ่นเพื่อเริ่ม manual attempt ใหม่; ไม่มี automatic next-model launch.

## 2026-10-29T13:37:34.226601+07:00 — approved full C4-P

Run `common-c4p-full-20261029T063458522990Z`. Same pilot scientific behavior/protocol; separate full population,6reuse+4994pending,≤1TRAINwarmup,oneGPUworker+oneCPUprocessforfour saved-onlysystems. Nativeglobalconfusionprojection checked againstpixels onfixedcrowd/Dress examples; per-personscoresrecomputedwithrevision2geometryties,notnative scalars. NoQ_C3/newmetric/bootstrap/nativeinference. Per-system5000STRICT_COMPLETE,primarynullifincomplete. Immutableattempts,80GiB/free50GiB/24h,sharedquality,noautomaticretry/fallback. Existingnative/pilot/GT unchanged; newoutputsownworkspace. Commitfreeze+launch,verifyfirstpacketthenreturn,automaticreports/Gitlogging,stopwithoutCPI/othersizes/YOLO/color/CCTV.

## 2026-10-29T15:14:48.282103+07:00 ? approved Sapiens2 0.8B C4-P concurrent/queued scope

Run `sapiens08-c4p-20261029T081254180014Z`. User authorizes `Sapiens2_0.8b` on official CIHP VAL 5,000 under unchanged C4-P revision-2 protocol (`SHARED_GPU_QUALITY_ONLY`) alongside running `0.4B` without interrupting `0.4B` or recomputing the 4 completed saved-only models. Separate checkpoint (`e7c1655b...`), config (`967f27e2...`), output tree, and lock (`SAPIENS08.lock`). Empirical admission (`10,236.83 MiB` combined budget vs `14,911.69 MiB` usable) admits concurrent execution with automatic fallback to resource queue (`QUEUE.jsonl`) if headroom drops; 6-ID pilot automatically freezes and promotes to full 5,000 when passed. Stop after `0.4B` and `0.8B`; no `1B`, `CPI`, training, or color benchmark.

## 2026-10-29T15:39:56.552075+00:00 — CPI memory repair, bounded implementation check

LatestuserrequestsfixOOMafteridleGPUattempt. Implementmodel-localperson-chunkrestorationrevision1, keepfrozenCPIconfig/source/results. CPU4oracles/anchorchecked;≤3diagnosticcallsTRAIN0000930→VAL0003218→VAL0001641, oneattempt/noautoretry. RequireGPUtoy/nativeprefixequivalence, packet/geometry/nativeIDs/scorercheck andexactoldpacketregression. [Currentrepairreport](reports/CPI_MEMORY_REPAIR_TH.md). No fullcohortrestart inthisunit; futurecontinuationmustbindnewimplementationandcountdiagnosticresources.

### 2026-10-29T22:50:05.630552+07:00 — bounded memory-repair verification complete

DIAGNOSTIC_PASS: CPU4/GPUfixture/nativeprefix checks plus3actualcalls(TRAIN0000930,VAL0003218,VAL0001641) passed; known0001641 packet/allarrays/scores exactly match original. RepairedConvNeXt continuation prepared with2CPUcontrolchecks, implementation fingerprint/dependency/diagnosticresource bindings. Nofullrunlaunched; firstcanonicalpatchedpacket/exact5000completion remain future checks. [Currentrepairreport](reports/CPI_MEMORY_REPAIR_TH.md).

### 2026-10-29T23:08:11.945471+07:00 — explicit repaired ConvNeXt continuation launched

Userเริ่มทำเลย authorizes fresh single-model attempt under unchangedscience/person-chunkrevision1. Segmentconvnext-20261029T160359716460Z;337reuse/4663pending,diagnosticexcluded,firstcanonical0003218packetPASS. Detachedbatch stopsaftermodel/error; noautomaticretry/nextmodel. [Currentreport](reports/cpi-convnext-chunked-20261029T160327964412Z.md); cumulativeguards/STRICT_COMPLETE retained.

### 2026-10-30T00:32:44.559860+07:00 — next-model R50 readiness stopped

UserauthorizedR50 nextafterConvNeXt complete. Source-isolatedsamepersonchunkrevision, R50ownGPUreadiness: warmupPASS, firstfailedhistoricalVAL0000018OOM upstreamcnt_part_parser.ReLU beforemaskrestoration;2calls/noautretry/fullvalidationNOT_STARTED. [Currentreport](reports/cpi-r50-chunked-20261029T172708697694Z.md). Canonical3/mainnull retained; futureworkmustaddressfeaturememoryandpassR50ownregression/diagnostic before full launch.

### 2026-10-30T01:14:54.758042+07:00 — R50 feature repair / revision3 launch

Revision2diagnosticpassedbutfullstoppedat0000266after17total; oldhistoryretained. Revision3same-kernel-shape independentbranchschedule passednativefloatreference/maximumheadcapacity100queries/3boundedimagecalls, byteexactknownpacket. Freshsegmentr50-20261029T181200001439Z,17reuse/4983pending; firstcanonical0000266PASS. [Currentreport](reports/cpi-r50-feature-20261029T175338825178Z.md). DetachedrunstopsafterR50/error,STRICT_COMPLETE/cumulativeguards unchanged; no othermodel.
