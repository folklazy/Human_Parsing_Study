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
