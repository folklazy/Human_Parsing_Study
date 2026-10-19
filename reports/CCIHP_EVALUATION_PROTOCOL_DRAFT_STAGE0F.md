# CCIHP person-level evaluation — DRAFT

ยังไม่ freeze taxonomy, thresholds, crop/ownership policy หรือ population exclusions ไม่มี benchmarkในStage0F และคะแนนในอนาคตจะเรียก CCIHP/custom cohort ไม่ใช่ official CIHP result

## 1. Taxonomy และ comparison cohorts

Native targetเก็บ BG0, categories1..21 และ unknown22ครบ Native CCIHP category scoreใช้ได้เฉพาะเมื่อ semantics ของ outputรองรับจริง CIHPDress6 ไม่ใช่ CCIHPFaceMask6; ห้าม rename IDsเพื่อให้ดู native-compatible

Common body/clothing cohortต้องมี checkpoint-specific representability matrix และใช้ GT projection/classes/domainเดียวกันทุกโมเดล Draft conceptsครอบคลุม exposed face/skin/body parts, hair, clothing และ footwearตามที่เปรียบเทียบได้จริง แยก extended accessories/detail cohortสำหรับ subsetที่ expressได้เหมือนกัน

Face≠head, glove≠hand, shoe≠barefoot และ whole dressไม่สามารถแบ่งupper/lowerโดยใช้GT geometryช่วยprediction ถ้ารวมเสื้อผ้าทั้งหมดเป็นcoarse classต้องเปิดเผยความละเอียดที่เสียไป ไม่บังคับ universal taxonomyที่ไม่ตอบโจทย์body/clothing

UnsupportedGTห้ามกลายเป็นBGหรือถูกตัดคนละชุดตามโมเดล ถ้าจำเป็นต้องใช้shared void domainต้องรายงาน retained pixels/persons/class supportของทั้งcohortก่อนประเมิน VAL Native predictionsยังคงแยกจากmapped predictions ยังไม่มี executable mappingที่อนุมัติ

## 2. Unknown/background และ valid denominators

Category22มี8,268พิกเซล/322ภาพ ความหมายไม่อยู่ในREADME จึงเก็บraw22และขอrelease clarification ข้อเสนอknown-label sensitivityใช้ explicit UNKNOWN/VOID maskที่เหมือนกันทุกโมเดล พร้อมจำนวนpixelsที่ไม่นำมาคิด ไม่เรียกว่าคะแนนnativeครบชุด ห้ามใช้ upstream gt>=num_classes→0

Human>0แต่Category0มี94,856พิกเซล/762ภาพ เสนอเปรียบเทียบสองdomainที่ตั้งชื่อแยก: raw Category background กับ unclassified-inside-Human void ต้องreviewTRAINแล้วตัดสินpolicyก่อนVALinference

พบ35 Human IDsที่Category0ทั้งหมด และรวม42IDsไม่มีknown foreground1..21 ต้องกำหนด undefined-person/support policyอย่างเปิดเผย ห้ามนับเป็นperfectหรือzeroโดยอัตโนมัติ และห้ามใช้minimum-area thresholdเพื่อลบIDsให้ตรงจำนวนในpaper

Source targets: TRAIN28,280/93,292 IDs; VAL5,000/17,548 IDs ส่วน exactTRAIN-overlap-controlled proposalคือ VAL4,961/17,434 IDs ตัวเลขคนเป็นraw Human IDs ยังไม่ใช่scorable-person denominatorหลัง common projection ตัวsource splitไม่เปลี่ยน

## 3. Person matching และ ownership

Identityคือ(split,imageID,positiveHumanID) ในoriginal RGB coordinates Human maskเป็นsupplied supportรวมส่วนที่ถูกassign accessories ไม่ใช่ anatomical silhouetteที่รับรองแล้ว

เสนอ deterministic one-to-one maximum-weight mask-IoU assignment พร้อม threshold/tie rulesที่จะทดสอบTRAINแล้วfreeze การใช้bboxแทนmaskหรือ anatomy-only geometryต้องเป็น ablationที่มีเหตุผล ไม่copyMOTS20 policyโดยอัตโนมัติ

เก็บmatchedGT, missedGT, unmatched predictions และduplicate predictionsแยก Human rasterมีownerเดียวต่อpixelแต่native predictionอาจทับกันได้ ห้ามflattenprediction overlapก่อนเก็บnative output

Cropอาจมีเพื่อนบ้าน จึงเก็บraw parser outputและtarget-owner outputแยก ข้อเสนอownershipใช้เฉพาะfrozenYOLO mask/geometric associationกับambiguity handling ไม่ใช้GTlabelsตอนdeployment Hard clippingหลังparseอาจตัดเสื้อผ้า/accessoriesที่YOLOmaskไม่ครอบ ต้องพิจารณาTRAINแยก ไม่ถือเป็นdefaultที่ถูกต้องแล้ว GToracleให้crop geometryเท่านั้น ไม่รั่วGTpixel ownershipไปช่วยprediction

## 4. Metrics

`IoU_k=TP_k/(TP_k+FP_k+FN_k)` บนfixed shared domain Global mIoUมาจากglobal accumulated confusion matrix แล้วเฉลี่ยclassesที่positive union; zero unionเป็นundefined/ไม่นำมาเฉลี่ย ไม่ใช่1 Predicted-only classที่มีunionได้0 เก็บGT/pred supportและระบุBG inclusion

Person-macro mIoUคิดclassIoUในcomparison domainที่อนุมัติของแต่ละpersonก่อนเฉลี่ยpersons จึงไม่ใช่global confusion mIoU การกำหนดdomainต้องครอบคลุมprediction outsideassignedGTตามpolicyเพื่อไม่ซ่อนleakage แยก no-known-GT/void-onlypersonsตามกติกาundefinedที่อนุมัติ

Dice_k=`2TP/(2TP+FP+FN)` ใช้support/aggregationpolicyเดียวกัน Body/clothing/accessory group scoresเฉลี่ยเฉพาะconceptsที่กำหนดก่อนและexpressได้เหมือนกัน ไม่มีmodel-specific favorable denominatorหรือweighted overall score

Matched-person qualityเป็นconditional ต้องรายงาน `GT coverage=matchedGT/allGT` และ `person precision=matchedpred/allpred` ควบคู่ Custom coverage-awareperson qualityเฉลี่ยqualityของmatchedpersonsและzeroของmissedGTในeligibleGTslotsที่กำหนดไว้ แต่ metricนี้ไม่penalizeทุกunmatchedprediction จึงต้องรายงานFP/personprecisionและfalse-positive semanticareaแยก ห้ามเรียกconditionalqualityว่าend-to-endquality

Person-size bins/Boundary metric toleranceต้องกำหนดจากTRAINก่อนVAL ไม่เลือกจากคะแนนVAL GT categorical mapกลับด้วยcategorical resamplingที่กำหนด ไม่ใช้bilinear

CCIHPcharacterized-region evaluatorไม่เท่ากับperson parsing AP^p/PCP และattributesอยู่นอกscope MHP official-wrapper testsไม่ใช่หลักฐานCCIHP/CIHPofficial parity ต้องมีfixturesของapprovedCCIHPdomains/ownershipก่อนrunจริง

## 5. Tracks และ timing

Oracle-personใช้GTgeometryให้compatiblecrop parser; YOLO26x-conditionedใช้frozenYOLOprediction→crop→parser→mapback/ownership Native full-frame referenceรักษาinternal detectionของM2FP/CPI/D2FP ส่วนfull-frameparser+YOLOassociationเป็นcompleteconfigurationแยก ไม่ใช่crop-parser-equivalentหรือhybridfusion

Timingอนาคตแยกms/person, native ms/image และactual complete ms/frameพร้อมNpersons ใช้FP32, fixed workloads/nativepreprocessing, warmups,CUDA synchronization, repeatedcleanrounds แยกcrop/preprocess/forward/postprocess/association/mapback และallocated/reserved/residentpipelineVRAM ไม่อนุมานFPSจากparserforwardหรือซ่อนinternaldetectorcost Stage0Fไม่มีtimingbenchmark

## 6. Leakage และ review gate

Official sourceVALและoverlap-controlled sensitivityรายงานคนละตาราง ไม่รวมคะแนนหรือแทนsource split การตรวจVALintegrity/duplicatesรอบนี้ไม่ใช่taxonomy/modelthresholdtuning Near-duplicateflagsไม่ถูกexcludeอัตโนมัติ และexactcontrolไม่ลบunknownpretraining exposure

ก่อนfreezeต้องผ่านhumanreview/adjudication, unknown/HumanBG policy, originalCIHPRGBpermission, checkpointlicense/readiness, comparabletaxonomy+retainedsupport, evaluatorfixtures และTRAIN protocol decisions นี่คือoff-the-shelfconfigurationstudy ไม่ใช่การพิสูจน์architecture causality **รอuserapprovalก่อนStage1**


ข้อเสนอแบบ machine-readable: [cohorts draft](../taxonomy/CCIHP_PERSON_EVALUATION_COHORTS_DRAFT_V1.yaml) ยังไม่ใช่ executable taxonomy mapping
