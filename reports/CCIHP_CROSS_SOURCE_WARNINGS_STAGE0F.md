# CCIHP / DatasetNinja CIHP — Cross-source ownership review

Reuse Stage0E30pairedimages, 741 DatasetNinja-converted CIHP semantic part objects: 694singlehumanfullsupport,21multi-human,26partlyunassigned. Reexamined actualobjectbitmaps and CCIHPHuman/Categorygrids for **47 flaggedobjects**; [per-object evidence](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/CROSS_SOURCE_CONFLICT_REVIEW.json)

Verified: CIHPDress6 and CCIHPFaceMask6 are differentconcepts; dress is annotated asupper5/skirt12 inCCIHP. CCIHP addsBag20/Others21 and broadenseyewear/hat/scarfdefinitions. Authorpaper§2 explicitlychangeshumanmasks. All affectedobjects listCC-categorypixel support andhumanowner support, includingzeroownerpixels

These facts support multiple possible causes: definitionchanges, changedboundaries or ownershippolicy, conversionpartgrouping, and possibleannotationerrors. **Cannot attribute everymixed object toonecause without nativeCIHPhumanreference and physicalreview.** A nativepartobject crossing twoCCIHPHumanIDs is a cross-source discrepancy, not proven erroneousCCIHPownership; zero-ownerpixels need RGBboundaryreview, not automaticdiscard

เก็บ DatasetNinja object ID (ไม่ใช่ original CIHP person/part-instance ID) กับ CCIHP Human ID แยกกัน. No majorityassignment, speculative grouping, nativeCIHP reconstructionclaim, or GTrepair. Currentpairedimages do not establish dataset-widefrequency. Some flags are inVAL: usedonlyannotationintegrity/compatibility, nevermodel/taxonomytuning


## ขอบเขตของ native reference

หลักฐาน native CIHP ที่ตรวจอิสระใน Stage0E ครอบคลุม semantic maps ของ5TRAIN demoเท่านั้น ไม่ได้ครอบคลุม originalHuman/part-instance maps ตัวobjectsในDatasetNinjaจึงเป็น converted semantic objects ไม่ควรเรียกnativeCIHP part-instance GT Cross-sourceflagsอาจเกิดจากconversion groupingร่วมกับannotation changes และยังไม่ทราบสาเหตุครบ
