# CCIHP — การตัดสิน dataset หลักหลัง Stage 0F

**เลือก D — Insufficient evidence, human review still required.** ผลนี้เป็นprimary-readiness decision ส่วน Stage0E **B PARTIALLY_COMPATIBLE** ที่ผู้ใช้ยอมรับยังคงเดิม

| เกณฑ์ | CCIHP: หลักฐานปัจจุบัน | MHP-v2: หลักฐานเดิม | ผลต่อการเลือก |
|---|---|---|---|
| File integrity | 33,280 RGB/GT sets อ่านได้; 99,840 PNG; ไม่มีdecode/dimensionerrors | RGBเสีย4; approvedreadableviewsพร้อม | CCIHPดีกว่าด้านreadabilityในlocal copiesนี้ ไม่ได้พิสูจน์GTถูกกว่า |
| Physical ownership | Native IDs110,840; sample200TRAINพร้อมแต่ยังไม่มีindependent humanreviews | Knownownershipflagsและsample30TRAINยังpending | ยังเลือกprimaryจากownership reliabilityไม่ได้ |
| Semantic support | Unknown22ใน322ภาพ; 35IDsมีแต่BG,42IDsไม่มีknownFG | Fine-grained58foreground; knownownership/duplicatedplanesบางกรณี | ต้องresolvepolicyและhumanreviewทั้งคู่ ไม่เลือกจากจำนวนclasses |
| Body/clothing coverage | Exposedbodyparts+coarseclothes/footwear; modifieddress/FaceMask; accessorylabelsheterogeneous | Body/hands/feet/clothing/accessorydetailมากกว่า | CCIHPมีศักยภาพเป็นcustombody/clothingtrack; commoncohortsต้องรักษาmeaning |
| Split independence | 39VALIDs exactTRAINreuse;1withinVALgroup;114near-riskpairs | 652VALIDs exactTRAINreuse;106withinVALgroups | แยกpopulation sensitivity ไม่ตีความว่าcheckpointmemorization |
| Checkpoint compatibility | CIHPweightsไม่ได้nativeCCIHPทั้งหมด; taxonomy/GTmodified | M2FP/CPIมีMHPnativevariantsแต่actualsmokes0 | แยกnative-referenceจากYOLOcropcohort และdeclaretrainingexposure |
| Reproducibility | Rawarchives/ledgers/sampleπ/sourcehashesครบ | Approvedreadablepopulations/GTplanes/hashesครบ | ทั้งสองทำreproducibleได้แม้มีqualitylimitations |
| Rights | AnnotationCCBYNCใช้academic scopeได้ตามเงื่อนไข; originalCIHPRGBpermissionยังไม่ชัด | Reuseexistingprojectresearchtermsreview | ต้องclarifyoriginalimagerightsก่อนclaimpermission/publication |
| CCTV application | ไม่ได้ทดสอบcompanyCCTV | ไม่ได้ทดสอบcompanyCCTV | Primarydatasetไม่รับรองCCTVrobustness; fieldtestเป็นงานอนาคต |

แนะนำเดินหน้าCCIHPในฐานะ **candidate primary สำหรับbody/clothingโดยมีข้อจำกัด** แต่ยังไม่promote/freeze ต้องให้มนุษย์ตรวจ200ภาพและadjudicatewarnings, clarifylabel22/HumanBG/imagepermissions และอนุมัติsharedtaxonomy/scoringdomains

MHP-v2คงprovisionalsecondaryfine-grainedroleตามexistingdecision ไม่เปรียบเทียบrawdatasetmIoUข้ามtaxonomyหรือรวมเป็นleaderboardเดียว No nativeCIHPdownloadจำเป็นเพื่อทำreviewนี้ต่อ แต่ถ้าต้องการoriginalnativeCIHPpersonGT/equivalenceจริงจะต้องมีnativeGTreferenceเพิ่มโดยขอapprovalแยก

[Full audit](CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md), [humanreview](CCIHP_HUMAN_REVIEW_STAGE0F.md), [leakage](CCIHP_SPLIT_LEAKAGE_STAGE0F.md), [protocol](CCIHP_EVALUATION_PROTOCOL_DRAFT_STAGE0F.md), [MHP risks](MHPV2_QUALITY_RISK_REVIEW.md)
