# Human Parsing Study — Stage 0

ขอบเขตคือ independent noncommercial student academic research เป้าหมายbody/clothingและaccessoriesที่โมเดลรองรับ ยังไม่เริ่มparserbenchmarkหรือcompanyCCTVtest

## สถานะปัจจุบัน

Stage0F automated CCIHPaudit: **PASS_WITH_WARNINGS**; primary-readiness decision **D — human review required** Stage0EcompatibilityBที่ยอมรับยังคงเดิม และdataset/taxonomy/protocolยังไม่freeze

ตรวจTRAIN28,280/VAL5,000ครบ; RGB33,280และPNG99,840อ่านได้ NativeHumanIDs93,292/17,548; unknown22และsemantic-supportwarningsถูกเก็บไว้ ชุดสุ่ม200TRAINพร้อมfull-resolutiondiagnostics/checklistยังPENDINGhumanreview ไม่มีannotation-errorprevalenceestimate

## อ่านผลและตรวจหลักฐาน

- [CCIHP full quality audit](reports/CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md)
- [200-image human review + checklist](reports/CCIHP_HUMAN_REVIEW_STAGE0F.md)
- [Full-resolution gallery](outputs/visualizations/stage0f-ccihp-quality-20261012T062825Z/index.html)
- [Split leakage / proposed sensitivity population](reports/CCIHP_SPLIT_LEAKAGE_STAGE0F.md)
- [Cross-source ownership discrepancies](reports/CCIHP_CROSS_SOURCE_WARNINGS_STAGE0F.md)
- [CCIHP draft evaluation protocol](reports/CCIHP_EVALUATION_PROTOCOL_DRAFT_STAGE0F.md)
- [Primary dataset decision](reports/CCIHP_PRIMARY_DATASET_DECISION_STAGE0F.md)
- [Machine-readable audit](provenance/CCIHP_FULL_QUALITY_AUDIT_V1.json)
- [Validation](provenance/CCIHP_STAGE0F_VALIDATION_V1.json)

## Existing scientific foundation

[Study standard](STUDY_STANDARD.md), [draft tracks](EXPERIMENT_PROTOCOL_DRAFT.md), [schema](DATA_SCHEMA.md), [study state](STUDY_STATE.json), [references](REFERENCES.md), [researchscope](RESEARCH_SCOPE.md), [licenseassessment](reports/LICENSE_ELIGIBILITY_REASSESSMENT.md)

[MHPreadableviews](provenance/MHPV2_READABLE_POLICY_V1.json) คงต้นฉบับและofficial/controlledpopulationsแยกกัน; [qualityrisks](reports/MHPV2_QUALITY_RISK_REVIEW.md) และsample30TRAINhumanreviewยังpending ไม่re-auditMHPในStage0F

[Currentmodelregistry](provenance/MODEL_VARIANT_REGISTRY_V3.csv): zero downloaded/loaded/smoke-passedparsercheckpoints FASHNexecutionยังรอapproval Sapiens2surveillance-relatedexecutionยังlicense-blocked PPSSpaused

Sharedassetsอยู่workspace datasets/models/third_party/.venvsภายนอกstudy ไม่มีsourceGT/YOLO/environmentchanges ไม่มีcheckpointdownloadหรือremoteGitactions Historicalreports/manifestsและ[documentrevisionarchives](provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/DOCUMENT_REVISIONS.json) คงไว้

**Next:** humanreview/adjudication +label/denominator/rightsclarification แล้วขอprotocolapproval งานauditนี้ไม่อนุมัติStage1หรือbenchmark
