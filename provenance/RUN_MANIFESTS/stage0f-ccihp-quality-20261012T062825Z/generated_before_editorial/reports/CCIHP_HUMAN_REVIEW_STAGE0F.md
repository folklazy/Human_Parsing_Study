# CCIHP — Independent TRAIN annotation review

**PENDING_INDEPENDENT_HUMAN_REVIEW**, not dataset-clean certification. Error prevalence **NOT ESTIMATED**

## Sampling design

Frame: 28,280 TRAIN images with verified GT/RGB grids. Seed20261012, stratified simple random sampling without replacement. Strata: nativepersoncount(0/1/2–3/4–7/8+), sourcepixels≤250000/>250000, minpersonmaskarea<1%/≥1%, humanoccupancy<25%/≥25%, bboxintersectionproxy/nointersection. All 38 populated strata have positive inclusion probability; allocateatleastoneeach then proportional remainder to200. Proximity/occupancy are measured proxies, notverifiedocclusion/camera-causes

Withinstratum inclusionπ_i=n_h/N_h; designweight=N_h/n_h. Selection fromall reviewableTRAIN was made without preferring knownanomalies and without excluding previoussampleIDs. [Frozen sample/strata/π](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/TRAIN_REVIEW_SAMPLE.json), [structured checklist](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/HUMAN_REVIEW_CHECKLIST.csv)

## Full-resolution diagnostic package

[Gallery](../outputs/visualizations/stage0f-ccihp-quality-20261012T062825Z/index.html), [output/sourcehashes and exact fidelity](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/REVIEW_PACKAGE.json). **200random images +1purposive0033810**, noGT/RGB resampling. EachRGB/Human/Category/Instance/per-personpanelhasoriginalW×H; nativepersonIDs and semanticvalues preserved. Yellowlinesmark boundaries, noterrors; magenta marks unknown/coverageflags. Everypersongets individualfull-frameGTpanel, neighboringGT overlayshidden butRGBunchanged

Image grids/bytefingerprintschecked; allthreeGTplanes roundtrip 201/201 exact on package. This proves fidelity, not annotationtruth

## Review checklist and adjudication

For eachimage, reviewerrecords: missingphysicalpersons; duplicatepersonIDs; multiplephysicalpersonssharingID; wrongsemanticcategory; person/partownership; boundaryerror; ambiguous/occludedregion. Use PASS(noissueobserved)/CONFIRMED/SUSPECTED/UNASSESSABLE, severityminor/major/critical/uncertain, personID/class/ROIandreason. Do not convert an automatedflag toCONFIRMED without reviewingRGBandGT. Tinybackgroundpeople may be outside annotationpolicy; markuncertainuntilpolicyknown

Two independenthumanreviewsrecommended; secondreview/adjudicationrequiredforcritical/suspectedownershipandboundaryambiguity. Reviewers should not know future modelrankings. Recordreviewer/date/adjudication; keepimmutableautomatedoutputs and use newreviewversion. Assistant spotchecks ofrendering do not substitute forhuman qualityreviews

**No prevalence estimate yet.** Future estimates must use stratificationweights and image-clustered uncertainty; imageinclusionprobability doesnot mean personsareindependently sampled. Reportimage/persondenominatorsseparately; purposiveunknowncase mustnot be included inrandomsampleestimates
