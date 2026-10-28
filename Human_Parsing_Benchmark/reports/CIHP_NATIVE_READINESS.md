# CIHP native — first-six readiness

Status: READY_FROZEN_FOR_USER_AUTHORIZED_FIRST_SIX · 2026-10-28T04:08:54.410169+00:00
Run `cihp-native-six-20261028T034103254470Z`. Authority [user-adopted plan](../proposals/CIHP_NATIVE_PARSING9_CODEX_PLAN_TH_20261028.md), [operative PLAN](../PLAN.md), [resolved config](../configs/cihp_native_six.json). This readiness is not the six-model benchmark result. Ninja archive remains unopened;Sapiens deferreduntilmatrix.

## Verified data

CIHPnativealreadyextracted, no re-extraction/hashscanofarchive repeated. RequiredVAL5000 RGB+Category_ids+Human_ids+Instance_ids allfullystrictdecoded;TRAIN3fullydecoded. No unreadablefiles,unknownsemanticIDs,dimensionmismatches,unresolvedEXIForientations. ObservedsemanticIDs0..19;PNGmodesL/uint8 preservedbyloader, no palette-to-RGBconversion. NativeREADMElabelorderandmodelreferenceevaluator confirm native20includingBG, Dress6. PGN image_reader documentsignore255 but noneobservedinVAL. OriginalGTunchanged.

VALGTpersons **17520**, partinstances121374; everyobservedpartinstancehas singlecategory/person association. SourceHumanpositive/Category0pixels1573remainnativeBGforsemanticmetricsandpersonextentforlocalization. Structuralassociationisnotphysicalownershipcertification.

OfficialsplitIDsunique andpairwiseID-disjoint;images/requiredGTbasenamescomplete. **39train–VAL exactJPEGduplicategroups**, one withinVALgroupIDs0021594/0023177. Keepofficial5000forprimary,discloseexposure;no inheritedCCIHP4961exclusion. All5000nativeJPEGbytesandgeometryequalexistingfrozenYOLOsourceidentities;12decodedhashrecipechecksalsomatch. NoNinjaarchiveprocessing. Initial0matchflagwas a hash-recipe comparison bug (oldincludesdimensions,newrawRGBonly);initialrecordpreserved, correctedusingexactJPEGidentitiesratherthanguessexclusion.

CPUauditfirstattemptslowtuple-groupingwasstoppedbyagent;362completedstrictdecoderecordswerepreserved/reusedwithsourcehashverification. Optimizedintegercodingsameobservedtuplegroups;noinferenceretryorGTchange. Attemptsource/snapshotrecordsexternal.

## Actual evaluation/route evidence

6hand-countedCPUtests exercise actualpacketread→scorer→serializedreport:perfect/wrongclass/nativeDress/invalidIDs,missing/duplicate,missedperson/wrongowner/IDrename,VOID,referenceabsentclasspolicy,dimensioncontract. New nativeDress remains nativecorrectclass, not oldcommon-taxonomyrejection. All18savedTRAINpackets replayunchangedthroughcurrentnative-scoringrecipe atmaskIoU0.50/0.75. These are targetedrequirements, nottest-count-onlycertification.

Generated16deterministicoriginal-gridGTpanels;AIoverviewinspection16,full-resolutiondetail2(0021448/0034387). Noglobalshiftidentified. Example0000822hasvisiblebackgroundcrowdunannotatedasforeground:allclaimsreleased-annotationrelative,notcompletephysicalpersontruth. No dataset-wideerrorprevalenceestimateorindependenthumanQAclaim. Diagnosticsimagesremainexternal.

| Model | Route | Actual TRAIN frames | FP32/T4 | Readiness note |
|---|---|---:|---|---|
| QANet_CIHP_HRNetW48_512x384 | YOLO_ROI |3|PASS|Peak parser allocated 394.3MiB;native API retained|
| M2FP_R101_CIHP | YOLO_ASSOCIATED_NATIVE_FRAME |3|PASS|Peak parser allocated 977.8MiB;native API retained|
| D2FP_R101_CIHP | YOLO_ASSOCIATED_NATIVE_FRAME |3|PASS|Peak parser allocated 1413.0MiB;native API retained|
| RPR_CIHP | YOLO_ASSOCIATED_NATIVE_FRAME |3|PASS|Peak parser allocated 665.1MiB;native API retained|
| CPI_R50_CIHP | YOLO_ASSOCIATED_NATIVE_FRAME |3|PASS|Peak parser allocated 1564.0MiB;native API retained|
| CPI_ConvNeXtB_CIHP | YOLO_ASSOCIATED_NATIVE_FRAME |3|PASS|Peak parser allocated 928.7MiB;native API retained|

FirstRPRattemptBLOCKEDbeforeinferencebecauseisolatedshimimportpathmissing;failedattemptpreserved. RevisedadapterreusesexistingFP32Apex-decoratorcompatibilitymoduleonly,noAMP/weights/architecturechanges;3TRAINframespass. M2FP/D2FPhiddenretry_if_cuda_oomreplacedbyprocess-localidentitywrapper:OOMfailswithoutautomaticGPUretry/CPUfallback. NativeTTA/resolution/confidencefiltersunchanged.

Qualityglobalcompositeusessamehighestfinal-person-scoreforegroundpriorityacrosssystems;minimumviewsnotheursticallysplitDress.Allnativeintegerlabelsandunowned/person/extentconfidenceartifactsretained.Native5ungatedreferencecomputedfromsameinference,notadditionalfullpassesorapplicationwinners. Publicselectioncomparesconfigurations,noseparatearchitecture/trainingcausalclaim.

## Resource and launch scope

ThreeTRAINexamplespercheckpointobservedcompressedpacketcomponentlinear5000scalingaggregate1.06–1.40GBdecimal;notworst-casebound/notincludingallCPInativePNGs/logs/temp. Actualperstream80GiB,free50GiB,24hcapsandstoragecounterremainoperative.200GiBplanningnotglobalhardcap. RuntimeestimatefromthreeTRAINscenesismarginalsampleonly,notafinalETAorfairnessrank.

OneTRAIN0000930warmupbeforeVALexcludedfromVALstatistics. InlineCUDA-synchronizedparserpipeline latency/allocated/reservedmemorycaptured;JPEGdecode/write/scoringexcludedfromtimer.Nativeinternaldetectorretainedwhereapplicable. FrozenYOLOcachemeans freshend-to-endlatency/FPS N/A,nocached-read=detectorinferenceclaim. Noquality/speedrankingfromTRAINsmokes.

ConfigfingerprintsourceboundbeforeVAL;sourceGitcommitwillbeenteredfromactualpublicationcommit,notfalselycalledlaunchrevisionofpriorruns. Userexplicitlyauthorizedsixwhenready;noadditionalmodelapprovalneeded. Fullofficial5000×6 parserframe-systemjobs;native referencesreuseoutputs.YOLOnewqualityjobs0. Anygenuinefailurestopsaffectedsystemkeepsnullmainmetrics/NOT_ATTEMPTEDcounts;independentmodelscontinue. NoCPU/FP16/resolutionfallbackorfailedinputretry. Sharedcontractbugstopsaffecteddependenciesandrequiresconsistentversionedfix beforefurtherclaims.

## References and external evidence

- User-suppliedacquisitionchain: [CIHP_PGN README](https://github.com/Engineering-Course/CIHP_PGN), linksGoogleDrive;notpublisherdigestauthentication.
- Background/ignoredecoderreference: [PGN image_reader](https://github.com/Engineering-Course/CIHP_PGN/blob/master/utils/image_reader.py).
- Semanticaggregationreference:pinnedM2FP m2fp/evaluation/parsing_eval/semseg_eval.py;all20epsilonzero-unionconvention, missing-inputskippingNOTcopied (STRICT_COMPLETEinstead).

ExactsourceaudadapterRUN/config/environment/inputidentitylinksandhashesincompactrunmanifest;fullDECODED_INPUTS.jsonl,DATA_READINESS.json,READINESS_REPLAY.json,RESOURCE_READINESS.json,GT_VISUAL_REVIEW.jsonandlogsunderexternalrunroot.NoofficialAP/PCPparityclaimed:no fabricatedconfidence/instance-APscores.
