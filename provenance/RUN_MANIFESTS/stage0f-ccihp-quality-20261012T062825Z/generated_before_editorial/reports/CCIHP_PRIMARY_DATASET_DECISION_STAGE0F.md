# CCIHP vs MHP-v2 — Primary dataset decision Stage 0F

**Selected D — Insufficient evidence; human review still required.** This isprimary-readinessdecision, not a reversal ofacceptedStage0E **B PARTIALLY_COMPATIBLE**. CCIHPusablecustompersonGT isreal; itsidentitytooriginalCIHP remainsunverified

| Criterion | CCIHP current evidence | MHP-v2 existing evidence | Implication |
|---|---|---|---|
| Input integrity | 33,280 RGB/GTsets, 0 decode/dimensionerrors; fullstreamingGTaudit | 4sourceJPEGsunreadable; approvedreadableviews | Integrityalonecannotchooseprimary |
| Person ownership | TRAIN93,292/VAL17,548 nativeIDs; 200randomTRAIN reviewpending | perpersonplanes54316; knownownershipflags;30randomTRAIN reviewpending | Neitherhasindependentlyverifiedphysical-qualityprevalence |
| Taxonomy | README21foreground + unknown22(8,268 pixels); alteredDress/FaceMask/Bag/Others | 58foregroundfinegrainedbody/clothing/accessorylabels | CCIHPcoarsebody/clothingpotential; classsupportandexpressibilitymustbechecked |
| Leakage | 39 VALIDsexactTRAINreuse; nearflags114; withinVALrepeatseparate | 652VALIDsexactTRAINreuse;106withinVALgroups | Differentrisks/denominators, notproofmemorization; sensitivityseparate |
| Native checkpoints | CIHP-nativeweightsdo notpredictmodifiedCCIHPsemanticsunmodified; customcohortsneeded | M2FP/CPI MHPnativeweights metadata verified, actualsmokes0 | Roster/exposureandtaxonomyfairnessareseparategates |
| Reproducibility | RawZIP/TAR preserved; fullpixel/sourceledger, sampleπ, statisticsandproposedpopulations | Originalhashes/readablepopulations/leakageledger available | Bothcanbereproducible despite qualitylimitations |
| Rights | CCIHPannotationCCBYNCcompatiblewithacademic scope; originalCIHPRGBpermission unresolved | Priorprojectresearchtermsassessment reused | Imagepermissionstillneedsclarification beforepublication/useclaims |
| CCTV application | Potentialexternalpublichumanparsingtarget; noCCTVtested | MOTS/MHPpublicdata do notverifycompanyCCTVrobustness | Fieldtestseparate, notprimaryselectionargument |

## Recommendation

ContinueCCIHPbody/clothingcandidateprimary preparation with **explicit limitations**, but do notpromote/freeze untilreviewandpolicygatespass. Complete200TRAINhumanreviews includingadjudication andwarninginterpretation; MHPsecondaryfine-grainedrole remainsprovisional. Do notcompare rawdatasetmIoUs acrossdifferentclasses orforceone overlycoarse universalranking

Recordunknown22support andhuman/categorygaps insteadofautomaticrepair. Approve anysharedvoid/sensitivitypolicyonlyafterreview. ExactreusecontrolledVALmanifestisproposed, sourcepopulationunchanged. No newdatasetdownload needed to finishthisreview; originalnativeCIHPwould be needed onlyifnativeCIHPpersonGT/equivalence becomesa requiredobjective

[Full audit](CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md), [human review](CCIHP_HUMAN_REVIEW_STAGE0F.md), [leakage](CCIHP_SPLIT_LEAKAGE_STAGE0F.md), [draft evaluation](CCIHP_EVALUATION_PROTOCOL_DRAFT_STAGE0F.md), [MHP risks](MHPV2_QUALITY_RISK_REVIEW.md)
