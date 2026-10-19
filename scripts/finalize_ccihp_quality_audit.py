"""Final Thai editorial layer, focused warnings and explicit pending-review gates."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from audit_ccihp_full_quality import sha,write_json

def main():
    active=json.loads((ROOT/'provenance/CCIHP_STAGE0F_ACTIVE_RUN.json').read_text());run=ROOT/active['run_path'];rid=active['run_id']
    support=json.loads((run/'PERSON_SEMANTIC_SUPPORT_WARNINGS.json').read_text());warnings=json.loads((run/'FOCUSED_WARNING_INVESTIGATION.json').read_text())
    sample=json.loads((run/'TRAIN_REVIEW_SAMPLE.json').read_text());raw=run.relative_to(ROOT);link='../'+str(raw)
    revisions=json.loads((run/'DOCUMENT_REVISIONS.json').read_text())
    # Preserve generated intermediate reports too; original pre-revision archives remain unchanged.
    def edit(rel,text):
        path=ROOT/rel;archive=run/'generated_before_editorial'/rel;archive.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            with archive.open('xb') as f:f.write(path.read_bytes())
        path.write_text(text.rstrip()+'\n')
        for r in revisions:
            if r['original_relative_path']==rel:r['sha256_after']=sha(path);r['editorial_intermediate']=str(archive.relative_to(ROOT));break
    p=ROOT/'reports/CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md';text=p.read_text()
    text=text.replace('## Quality gate','''## ผลตรวจคนที่ไม่มี known semantic foreground

ตรวจทุกภาพที่มี Category0/Human gap หรือ unknown label เพิ่มแบบเจาะจง **1,027 ภาพ** พบ **35 Human IDs** ที่ Category เป็น0ทั้ง mask: TRAIN27 / VAL8 ในจำนวนนี้34 IDsมีเพียง1–8พิกเซล อีก1IDคือ TRAIN0014422/Human1 ขนาด91,332พิกเซล จึงห้ามสมมติว่า positive Human ID ทุกค่ามี semantic GT ที่ใช้ทำ person-macro mIoU ได้

เมื่อรวมกรณีที่มีแต่ unknown label พบ **42 Human IDs ไม่มี known foreground1..21** คงไว้ใน source population ทั้งหมด ไม่ตัดทิ้งหรือซ่อม ค่า native person denominator110,840หมายถึงจำนวน IDs ที่มีพิกเซล ไม่ใช่จำนวนคนที่ scoring policy รับรองแล้ว การกำหนด eligibility/undefined score ของกลุ่มนี้ต้องตรวจและอนุมัติก่อน benchmark

[Person semantic support evidence](PERSON_SUPPORT_LINK). จำนวนnative IDsในreleaseนี้110,840 ต่างจากตัวเลข110,821ในpublication19 IDs ไม่ทราบสาเหตุversion/counting conventionครบ จึงรายงานค่าที่ตรวจจริง ไม่ลบ IDsเพื่อให้ตรงpaper

## ภาพตรวจ warning แบบเจาะจง

ตรวจ unknown label ทั้ง322ภาพ พบทุกพิกเซลมี Human support และไม่มี positive attribute Instance ID; ID22จึงไม่ควรถูกตีความเป็น background โดยอัตโนมัติ ดู [หลักฐาน](FOCUSED_LINK)

**Observation จาก assistant spotcheck:** ภาพ0014422มีบริเวณใบหน้า/ผมของคนด้านซ้ายอยู่ใน Human1 แต่ semanticทั้งหมดเป็น0 ส่วน0010505มี Category22ในบริเวณผ้าห้อย ไม่ได้เป็นแค่จุดสองพิกเซลทุกภาพ สองข้อเป็นการอ่านภาพกับค่าต้นฉบับ ไม่ใช่การรับรองสาเหตุหรือ human adjudication

**Interpretation:** ปัญหา semantic support อาจกระทบ oracle geometry และ person-macro denominator แม้ instance-to-class association ของ positive Instance IDs จะผ่าน ไม่ควรแก้ด้วย minimum-area threshold หรือ ignore policy ที่เลือกจากคะแนนVAL

![TRAIN0014422: source RGB and coverage flag](WARNING_IMAGE)

## Quality gate'''.replace('PERSON_SUPPORT_LINK',link+'/PERSON_SEMANTIC_SUPPORT_WARNINGS.json').replace('FOCUSED_LINK',link+'/FOCUSED_WARNING_INVESTIGATION.json').replace('WARNING_IMAGE','../outputs/visualizations/'+rid+'/focused_warnings_v2/0014422_full.png'))
    edit('reports/CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md',text)
    review=f'''# CCIHP — ชุดตรวจคุณภาพ GT โดยมนุษย์

สถานะ **PENDING_INDEPENDENT_HUMAN_REVIEW** ไม่ใช่การรับรองว่า dataset สะอาด และยังไม่ประมาณอัตราความผิดพลาด

## การสุ่ม

Sampling frame คือ TRAIN 28,280 ภาพที่ RGB/GT อ่านได้และ dimensions ตรงกัน ใช้ seed `20261012` สุ่มแบบ stratified simple random without replacement จำนวน200ภาพ มี38 strata ทุก stratumมีโอกาสถูกเลือกมากกว่าศูนย์

Strata ประกอบด้วยจำนวน Human IDs, ความละเอียดภาพ, mask ของคนที่เล็กที่สุดเทียบพื้นที่ภาพ, human occupancy และการตัดกันของ bbox สิ่งเหล่านี้เป็น proxy เชิงเรขาคณิต ไม่ใช่การรับรอง crowd severity หรือ occlusion

จัดอย่างน้อย1ภาพต่อ stratum แล้วแจกส่วนที่เหลือตามขนาด population; inclusion probability `π_i=n_h/N_h` และ design weight `N_h/n_h` บันทึกครบ การสุ่มใช้ TRAINทั้งหมดที่เข้าเงื่อนไข ไม่เลือกเฉพาะ known anomalies และไม่ใช้ VAL

[Sample/strata/inclusion probabilities]({link}/TRAIN_REVIEW_SAMPLE.json), [checklist200แถว]({link}/HUMAN_REVIEW_CHECKLIST.csv)

## ภาพตรวจ

[เปิด gallery](../outputs/visualizations/{rid}/index.html), [source/output hashes และ round-trip tests]({link}/REVIEW_PACKAGE.json)

แต่ละภาพมี Original RGB, Human_ids พร้อม ID, Category_ids, Instance_ids, GTรายคน และ warning overlay ทุก panel ใช้ขนาดพิกเซลต้นฉบับ เพิ่มแต่พื้นที่ชื่อpanel ไม่มีการ resize GT ตัวอย่างสุ่ม200ภาพกับกรณี0033810ที่เลือกเจาะจงอีก1ภาพอยู่คนละ selection role

สีเหลืองแสดง boundary ซึ่งไม่ได้แปลว่า error; สี magenta ใน warning panelแสดง unknown/coverage flag ไม่ใช่ผลตัดสินของผู้ตรวจ ใช้ legend ในgalleryอ่าน semantic colors ส่วน Human/Instanceใช้สีตามIDเฉพาะภาพ

ตรวจ round-trip ของ Category/Human/Instance ได้ตรงทุกพิกเซล201/201ภาพ การตรวจนี้รับรอง conversion fidelity เท่านั้น Assistantดูภาพบางกรณีเพื่อเช็กการแสดงผล ไม่ถือเป็น independent human review

## Checklist

ผู้ตรวจบันทึก missing physical person, duplicate person IDs, หลายคนแชร์IDเดียว, wrong class, person/part ownership, boundary error และ ambiguous/occluded region พร้อมpersonID/class/ROI เหตุผลและseverity

ใช้สถานะ `NO_ISSUE_OBSERVED / CONFIRMED / SUSPECTED / UNASSESSABLE` แยกจาก automated flags และแยก minor/major/critical/uncertain ถ้าไม่ทราบ policyของคนเล็กด้านหลังหรือขอบเขตที่ถูกบัง ให้บันทึกuncertain ไม่เดาว่า annotationผิด

แนะนำผู้ตรวจสองคนโดยไม่เห็น model ranking; critical/uncertain casesต้อง second review และ adjudication เก็บ reviewer/date/เหตุผลไว้ใน versionใหม่ ไม่แก้ immutable automated evidence

## การประมาณ prevalence ภายหลัง

ตอนนี้ **NOT ESTIMATED** ต้องให้ reviewครบก่อน หากประมาณอัตราให้ใช้ stratum weights และ uncertainty ที่รองรับ image clustering รายงาน image-level และ person-level denominatorแยกกัน เพราะภาพถูกสุ่มไม่ได้ทำให้คนทุกคนมีโอกาสถูกเลือกเท่ากัน กรณี warning ที่เลือกเจาะจงห้ามปนใน prevalence sample
'''
    edit('reports/CCIHP_HUMAN_REVIEW_STAGE0F.md',review)
    protocol='''# CCIHP person-level evaluation — DRAFT

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
'''
    edit('reports/CCIHP_EVALUATION_PROTOCOL_DRAFT_STAGE0F.md',protocol)
    decision='''# CCIHP — การตัดสิน dataset หลักหลัง Stage 0F

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
'''
    edit('reports/CCIHP_PRIMARY_DATASET_DECISION_STAGE0F.md',decision)
    readme=f'''# Human Parsing Study — Stage 0

ขอบเขตคือ independent noncommercial student academic research เป้าหมายbody/clothingและaccessoriesที่โมเดลรองรับ ยังไม่เริ่มparserbenchmarkหรือcompanyCCTVtest

## สถานะปัจจุบัน

Stage0F automated CCIHPaudit: **PASS_WITH_WARNINGS**; primary-readiness decision **D — human review required** Stage0EcompatibilityBที่ยอมรับยังคงเดิม และdataset/taxonomy/protocolยังไม่freeze

ตรวจTRAIN28,280/VAL5,000ครบ; RGB33,280และPNG99,840อ่านได้ NativeHumanIDs93,292/17,548; unknown22และsemantic-supportwarningsถูกเก็บไว้ ชุดสุ่ม200TRAINพร้อมfull-resolutiondiagnostics/checklistยังPENDINGhumanreview ไม่มีannotation-errorprevalenceestimate

## อ่านผลและตรวจหลักฐาน

- [CCIHP full quality audit](reports/CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md)
- [200-image human review + checklist](reports/CCIHP_HUMAN_REVIEW_STAGE0F.md)
- [Full-resolution gallery](outputs/visualizations/{rid}/index.html)
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

Sharedassetsอยู่workspace datasets/models/third_party/.venvsภายนอกstudy ไม่มีsourceGT/YOLO/environmentchanges ไม่มีcheckpointdownloadหรือremoteGitactions Historicalreports/manifestsและ[documentrevisionarchives]({raw}/DOCUMENT_REVISIONS.json) คงไว้

**Next:** humanreview/adjudication +label/denominator/rightsclarification แล้วขอprotocolapproval งานauditนี้ไม่อนุมัติStage1หรือbenchmark
'''
    edit('README.md',readme)
    # Category legend is a visualization aid, not a new mapping or evaluation.
    from document_ccihp_full_quality import NAMES
    legend={k:([0,0,0] if k==0 else [255,0,255] if k==22 else [(k*83)%200+35,(k*139)%200+35,(k*191)%200+35]) for k in range(23)}
    gallery=ROOT/'outputs/visualizations'/rid/'index.html';html=gallery.read_text();parts=['<h2>Category legend (original IDs)</h2>']
    for k,colors in legend.items():parts.append(f'<span style="display:inline-block;margin:5px"><span style="background:rgb{tuple(colors)};display:inline-block;width:18px;height:18px"></span> {k}: {NAMES[k]}</span>')
    html=html.replace('<h1>', ''.join(parts)+'<h1>',1);gallery.write_text(html)
    write_json(run/'VISUALIZATION_LEGEND.json',{'categories':{str(k):{'name':NAMES[k],'RGB':v} for k,v in legend.items()},'unknown_semantics_defined':False})
    write_json(run/'DISPLAY_SPOTCHECK.json',{'reviewer':'ASSISTANT_RENDERING_SPOTCHECK_ONLY','human_review':False,
               'inspected_outputs':['training_0013186.png','focused_warnings_v2/0014422_full.png','focused_warnings_v2/0010505_full.png'],
               'observations':['0013186: panels share the source grid and retain three separate local Human IDs',
                              '0014422: Human1 support has Category0 throughout; warning covers left visible face/hair',
                              '0010505: unknown22 occupies a hanging fabric region, not only isolated pixels'],
               'physical_ownership_error_adjudication':'PENDING','whole_dataset_semantic_accuracy_claim':False})
    write_json(run/'FAILURE_DIAGNOSTICS.json',{'engineering_failures':[{'log':'WARNING_PROBES.log','cause':'Two prior sample IDs were Validation, not Training; split lookup failed before evidence summary',
                  'resolution':'Use actual split evidence, rerun focused probes into fresh focused_warnings_v2; earlier outputs/log preserved'}],
                  'source_data_changed':False,'failed_execution_not_reported_as_PASS':True})
    state=json.loads((ROOT/'STUDY_STATE.json').read_text());state['stage0f_ccihp_quality']['semantic_background_only_Human_IDs']=35
    state['stage0f_ccihp_quality']['no_known_foreground_Human_IDs']=42
    state['stage0f_ccihp_quality']['same_frame_diagnostics_ready']=True
    (ROOT/'STUDY_STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    for r in revisions:
        r['sha256_after']=sha(ROOT/r['original_relative_path'])
    write_json(run/'DOCUMENT_REVISIONS.json',revisions)
    write_json(run/'EDITORIAL_COMPLETE.json',{'completed':True,'human_reviews_completed':0,'primary_promoted':False})
    print('[STAGE0F] final editorial/evidence integration complete',flush=True)

if __name__=='__main__':main()
