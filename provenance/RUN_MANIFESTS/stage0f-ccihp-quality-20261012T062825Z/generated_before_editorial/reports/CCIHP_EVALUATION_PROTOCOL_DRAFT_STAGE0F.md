# CCIHP person-level evaluation — DRAFT, Stage 0F

Status: DRAFT_REQUIRES_EVIDENCE_REVIEW. No inference/evaluation thresholds frozen; not official CIHPbenchmark results

## Targets and cohorts

1. **Native CCIHP known-category track:** preserve0BG,1..21 categories and unknown22. Only compatible prediction semantics can be interpreted under this native target; pretrained CIHP/ MHP outputs do not becomeCCIHPnative by renamingnumericIDs. Full21classcomparativeleaderboard is not valid whencheckpoints cannotexpressFaceMask/Bag/Others anddresssplits
2. **Common body/clothing cohort:** checkpoint-specific representabilityaudit, sameGTprojection/classes/domain for allcohortmembers. Draftconcepts: exposedface/skin/bodyparts, hair, coarsegarmentregions, footwear; eligibleleft/rightdetailsonlywhereexpressible. Face≠head; glove≠hand; shoe≠barefoot; wholeDresscannot becomeupper/lowerusingGTcoordinates. Entiregarmentmerge may be possible butreducesapplicationdetail
3. **Extended subset:** detailedbody/clothing/accessories onlywithin comparable expressibility. Bag/FaceMask/Othersoftenunsupported orheterogeneous, reportnativeGTsupport/semanticcoverage independently. No arbitraryuniversalweightedscore

Mappings remainproposals in existingmatrix; complete numericalGTpixel/personretention must be computed after mappingapproval, beforeVALevaluation. UnsupportedGT mustnot becomeBG or a favorablemodel-specificdenominator. If excludedfromcohortdomain, identicalsharedvoidprojectionandretainedsupport mustbedisclosed for allmodels. Native outputs remainlossless and separate

## Unknown/background policy proposals

Preserveraw Category22 and requestauthorclarification. Proposedknown-domain metricusesexplicitunknownvoidmask sharedacrossmodels, plusunknownregioncounts/unassignedpredictionbehavior diagnostic; this iscustom known-subsetscore, notunqualifiednativeresult. Untilmeaningagreed no complete-nativecategoryscoreclaimed. Neverreuse upstream gt>=num_classes→0 assemanticpolicy

BG0outsideHuman is documentedbackground. Human>0/Category0 meaningunresolved: propose two separatelynamed sensitivitydomains (rawCategorybackground versusunclassifiedinsideHumanvoid), with fixedwhole-cohortdenominators andsupportcounts. No silentGT repair. Changes mustbe decidedonTRAINreview anddocumented beforefinalVALinference

## Person association and ownership

Source identity=(split,imageID,positiveHumanID), sourcegridRGBdimensions. RawHuman support is provisional GTpersongeometry includingassignedaccessorypixels, notpureanatomicalsilhouette. Deterministic one-to-one maxweight mask-IoU assignment, explicitthreshold and tiepolicy selectedfromTRAINprotocoldevelopmentthenfrozen. Matchingbboxonly or anatomy-only wouldbe separate justifiedablation, notsilentMOTS20copypolicy

KeepunmatchedGT/missedpersons, unmatchedpredictions/duplicates andmatchedpersons separately. CCIHPrastercanonlyrepresentoneownerperpixel; do notflattenoverlapsfromnativeparserpredictions irreversibly. Document ambiguoussourceownership as reviewflags withoutautoexclusion. Cropmargins/TRAINthresholds remainpending

Semanticcropmaycontainneighbors: store rawsemanticcrop andownermappedpredictionseparately. Candidateownershippolicy usesonlyfrozenYOLOmask/geometricassociation andexplicitambiguityflag, neverGTlabels atdeployment. A hardpostparsingmask canloseclothing/accessories outsideYOLOsilhouette, so no defaultclaimedcorrect; comparepolicyonTRAIN afterapproval. GToraclegeometryprovidescrop only, not GT-guidedpixelownership

## Metrics and aggregation

For eachfixedcohortdomain andclassk, IoU_k=TP_k/(TP_k+FP_k+FN_k), accumulateconfusionmatrices on the sameGTprojection. GlobalmIoU=mean validunionclasses withsupportcounts; absentclasswithzeroGTandzeropredunion isundefined/omitted, not1. Predicted-onlyclasswithpositiveunion hasIoU0. ReportBGinclusionexplicitly; foregroundmIoUdoesnot silentlyincludeBG

Person-macro mIoU: computeclassIoUs on a fixedoriginal-coordinate per-personcomparison domain (includingpredictions outsideassignedGT wherepolicyallows), averageclasseswithpositiveunion, thenaveragepersons. ThisdiffersfromglobalconfusionmIoU andmustbenamedseparately. Classabsence/noGTsupport cases undefinedandreported. Dice_k=2TP/(2TP+FP+FN), sameaggregation/supportpolicy. Body/clothing/accessorygroupmeanonlyoverpredeclaredexpressibleclasses, notarbitrarymodel-specificmeans

Matched-person quality Q_matched isconditional, accompaniedbyGTcoverage=matchedGT/allGT andpredictionprecision=matchedpred/allpred. Coverage-awarepersonmacro Q_allGT=mean over allGTpersonslots ofmatchedquality orzeroformissedGT; labelthiscustommetric. Unmatchedpredictions stillneedseparate FP/personprecision andfalsepositivesemanticareareport, becauseQ_allGTalone doesnotpenalizeallspuriousinstances. Do nothide detector missesor claimconditionalquality is end-to-endquality

Person-sizeanalysis uses fixedTRAIN-derived bins ofGTmaskarea/bboxheight andrecordsGTcounts/matchedcounts, nobinselectionbyVALscores. Boundarymetric requires agreed categoricalmapback/native-resolutionpolicy andTRAIN-fixedtolerance; no bilinearGT interpolation

CCIHPnativecharacterized-region AP evaluator isnot automaticallythe personparsing AP^p/PCP evaluator andattributecharacterizationisoutofscope. MHPcompatibilitywrapper tests remainMHP-reference tests, not proof ofCCIHP/CIHPofficialparity. No officialscoreclaimswithoutmatchingnativeprotocol

## Operational tracks and resources

OracleTRAIN/VALGTgeometry → compatiblecropsemanticparser separatesupstreamlocalization. FrozenYOLO26x → crop → parser → source-coordinate ownership isapplicationtrack. Nativefull-frameM2FP/CPI/D2FP retainsinternaldetection andinstancebehavior asreference. Optionalfull-frameparser+YOLOassociation is a separatecompleteconfiguration, not crop-parser-equivalence or hybridfusion

Futuretimingseparate ms/person, native ms/image, end-to-end ms/framewithpersoncount. FixedsourceRGB/nativepreprocess, FP32, warmups/CUDAsync/cleanrounds, crop/preprocess/forward/postprocess/association/mapback separately; residentpipeline allocated/reservedVRAM andNpersons recorded. Do notinferFPSfromparserforward oromit internaldetection. No timingdoneinStage0F

## Leakage and governance

OfficialCCIHPVAL5000 retained; proposedexactTRAIN-overlap-controlledview is sensitivityonly andhasindependentdenominators. Do not merge populationscores. VALintegrityscreen is allowed; no modelthreshold/taxonomy/hyperparameter tuning onVAL. NativeCIHP/MHPcheckpoints mayhave training/selectionexposuretocorrespondingimages; declareYES/NO/UNKNOWN withoutassumingmemorization. This isoff-the-shelfconfigurationcomparison, not controlledarchitecturecausality

Prebenchmarkgate: independenthumanreviews/adjudication, unknownlabelandHumanBGpolicy, originalimagepermissions, checkpointlicenses/readiness, representability/retainedsupport, evaluatorfixturevalidation forapprovedCCIHPdomains andownership, frozenTRAINprotocol. No fullbenchmark untiluserapproval
