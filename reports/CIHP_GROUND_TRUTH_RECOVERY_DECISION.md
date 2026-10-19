# CIHP Ground Truth Recovery Decision — Actual CCIHP Available

**Decision B — PARTIALLY_COMPATIBLE.** Previous Decision C was for the earlier available TAR only; historical reports and fingerprints preserved

| Target | Result with current ZIP + TAR | Scientific limit |
|---|---|---|
| Original native CIHP per-person GT | BLOCKED | Modified CCIHP masks/taxonomy;21mixed-owner and26partly unassigned cross-source objects in30samples; no original Human_ids reference |
| CCIHP-native per-person parsing | CONDITIONAL | Human/category/instance filescomplete;30sample roundtrip verified; global quality/unknown22/rights/cohort definitionspending |
| Body/clothing common-class benchmark | CONDITIONAL | Possible underexplicit shared GT projection; no automatic Dress recovery or unsupported->background |
| Supported accessory diagnostics | CONDITIONAL | Bag/Others/FaceMask differ from native CIHP and parser capacities; needs representability/cohort denominators |
| Native CIHP APp/PCP-equivalent benchmark | NOT_VERIFIED | Same images/classes-by-name are insufficient; do not relabel custom scores official |

## Recommended route and approval

Recommend **first review a separate custom CCIHP-person body/clothing GT track using existing CIHP RGB**, then Full Quality Audit if approved. This can resolve useful per-person preparation without another dataset download, while keeping native CIHP reference separate. It does not freeze primary dataset, shared taxonomy or evaluator thresholds

If the study requires original CIHP official/native target comparability, obtain verified native GT-only supplement/local native copy; otherwise official original distributionrequires separate acquisition approval. CCIHP cannot automatically replace that source. Do not download DatasetNinja again

Additional CCIHP GT passes file-integrity/paired-ID gates, but does not resolve all dataset quality issues. Next bounded work should investigate unknown22 at two pixels,12human-without-category pixels, publication/release class definitions, visible-person/ignore policy and RGB/native-reference limits; no automatic repairs or exclusions. Then independently review ~200 stratified TRAIN images with complete source audit under agreed cohort

Keep imageset denominators separate: CCIHP train28,280 / val5,000 annotated IDs pairexactly with CIHP TAR; person counts96only for audited30images, full person total NOT_COMPUTED. Existing39train–valexact-byte duplicategroupsremain disclosed; no silent split changes/sensitivity activation

CCIHP native-class mapping remains DRAFT; source semantic details and rights remain separate from original CIHP RGB/GT and model terms. CC-BY-NC annotationtermscompatible with Decision5A subject to terms; original RGB permissionstillunverified. CompanyCCTV, colors/patterns/size evaluation and parser benchmarksremainoutside this audit

[Compatibility audit](CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [person evidence](CCIHP_PERSON_INSTANCE_VERIFICATION.md), [matrix](../taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv), [quality-review proposal](../manifests/CCIHP_QUALITY_REVIEW_PLAN_V1.json)

**STOP — WAIT FOR USER APPROVAL.** No additional dataset acquisition, Stage1, full benchmark or inference
