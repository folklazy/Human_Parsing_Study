# CCTV controlled ROI — ผลประเมินสี่เป้าหมายครบเก้าระบบบน GT domain ที่ตรวจได้

ตรวจปิด 2026-11-01T23:26:54.611649+07:00 (Asia/Bangkok). สถานะ **FOUR_TARGET_EVALUATION_COMPLETE_ON_REVIEWED_GT — 9/9**. รอบนี้ model inference ใหม่ **0**; ใช้ predictions ที่ครบ90ภาพ/130frozen YOLO opportunities ต่อ checkpoint และเก็บผล/attempts เดิมครบ.

**Sapiens2 1B ได้ค่าเฉลี่ยหลักสี่ targets สูงสุดที่65.430%** ตาม reference/domain นี้; QANet64.533% ตามมา ห่าง0.898percentage points. QANetได้ Face-domainและUpperสูงสุด; Sapiens2 1Bได้HairและLowerสูงสุด. เป็น observed point estimates ไม่ใช่ statistical significance หรือการรับรองพร้อม deployment.

Face-domain ใช้ได้ **21จาก35 source Face records** หลัง GT-only review; อีก14รายการมีปัญหา reference/contour หรือ RGBยืนยันไม่ได้และกันออกเท่ากันทุกโมเดล. ใน21รายการนั้น18มี Neckที่ไม่ทราบขอบแน่ชัดและมี explicit uncertainty; Face+Neck delivery ใช้ได้เพียง3รายการ. **การคำนวณรอบนี้จบแล้วบน domain ที่ประกาศ ไม่ได้หมายความว่า GTทั้ง35รายการเป็น anatomical gold หรือให้คะแนน Face/Neckครบทุกกรณีแล้ว.**

## ตารางหลัก

หน่วยเป็นpercentของ **mean per-GT-part IoUภายในแต่ละtarget** แล้วเฉลี่ยtargetละ25%. ไม่ใช่ global full-image mIoU, official native parser benchmark หรือคะแนนCIHPเดิม. Frozen roster order:

| Checkpoint | Prediction frames | Hair n61 | Face-domain n21 | Upper n112 | Lower n96 | Macro4 |
|---|---:|---:|---:|---:|---:|---:|
| QANet_CIHP_HRNetW48_512x384 | 90/90 | 60.817 | 71.434 | 68.746 | 57.134 | 64.533 |
| M2FP_R101_CIHP | 90/90 | 48.990 | 54.790 | 56.264 | 46.032 | 51.519 |
| D2FP_R101_CIHP | 90/90 | 47.454 | 57.279 | 51.497 | 41.062 | 49.323 |
| RPR_CIHP | 90/90 | 43.918 | 52.964 | 51.482 | 41.940 | 47.576 |
| CPI_R50_CIHP | 90/90 | 41.730 | 56.192 | 39.992 | 35.993 | 43.477 |
| CPI_ConvNeXtB_CIHP | 90/90 | 59.795 | 63.172 | 53.832 | 44.967 | 55.441 |
| Sapiens2_0.4b | 90/90 | 65.746 | 64.157 | 62.330 | 53.818 | 61.513 |
| Sapiens2_0.8b | 90/90 | 60.770 | 65.665 | 60.281 | 55.198 | 60.479 |
| Sapiens2_1b | 90/90 | 67.152 | 69.607 | 66.044 | 58.919 | 65.430 |

ใช้ **290 eligible parts**: Hair61 + Face21 + Upper112 + Lower96. Sourceหลังแก้ownerมี326groupedparts; non-Face exclusions22และFace exclusions14เก็บเหตุผล/private recordsไว้ครบ. ไม่เติมคะแนนของGTที่ไม่รองรับเป็น0 และไม่ตีความGT exclusionเป็นmodel failure.

[CSVหลักพร้อมfull precision](../metrics/CONTROLLED_ROI_FOUR_TARGET_RESULTS.csv) / [per-target overall/day/night](../metrics/CONTROLLED_ROI_PER_TARGET.csv) / [Face views](../metrics/CONTROLLED_ROI_FACE_VIEWS.csv) / [canonical derived index](CONTROLLED_ROI_FOUR_TARGET_INDEX.json).

## สูงสุดรายเป้าหมายและข้อเสนอเลือกใช้ต่อ

| Target | Observed leader | IoU % | อันดับถัดไป | ส่วนต่าง pp |
|---|---|---:|---|---:|
| Hair | Sapiens2_1b | 67.152 | Sapiens2_0.4b | 1.406 |
| Face-domain | QANet_CIHP_HRNetW48_512x384 | 71.434 | Sapiens2_1b | 1.827 |
| Upper | QANet_CIHP_HRNetW48_512x384 | 68.746 | Sapiens2_1b | 2.702 |
| Lower | Sapiens2_1b | 58.919 | QANet_CIHP_HRNetW48_512x384 | 1.785 |
| Macro4 | Sapiens2_1b | 65.430 | QANet_CIHP_HRNetW48_512x384 | 0.898 |

เมื่อให้น้ำหนักสี่targetsเท่ากันตามที่กำหนด **เสนอ Sapiens2 1B เป็นตัวเลือกหลักสำหรับขั้นต่อไป** จากผลรอบนี้ และเก็บ **QANetเป็นทางเลือกเมื่อเน้น Face-reference/Upper**. ยังไม่อ้างว่า1Bดีกว่าทุกtarget, เป็นoverall winnerของทุกสภาพCCTV หรือแม่นพอในงานจริง. ส่วนต่างMacro4เล็กและยังไม่ได้ประเมินuncertainty; ไม่ตั้งpractical-tie thresholdหรือคะแนนผสมใหม่หลังเห็นผล. ไม่มีการทดสอบensemble/fusionและไม่เสนอผลรวมหลายโมเดลว่าเกิดขึ้นแล้ว.

## GT Face/Neck และความหมายของคะแนน

1. ตรวจRGB/source GT35รายการใหม่ในcoordinate references และGT-only overlaysหกcontact pages. Sourceannotations/masksไม่เปลี่ยน; owner correctionsสองจุดเดิมคงอยู่ในderivedcopy. ผู้ตรวจคือCodex visual assistant ไม่ใช่independent expert.
2. Face referenceคือ **source Face contour ลบ known Neck, uncertainty และ known opaque occluder**. Contourส่วนอื่นยังสืบทอดsource annotation จึงไม่รับรองpixel-perfect anatomical Faceหรือแก้ข้อผิดพลาดGTทุกชนิดหมดแล้ว.
3. Known Neckวาดเป็นvisible polygons3กรณี. อีก18กรณีใช้ `REGION_UNCERTAIN`: manually boundบริเวณown-neck/jaw/collarที่ระบุไม่ได้จากRGB. Unknown Neckยังเป็นunknown ไม่ใช่zero-Neck truth. Face-domainใช้พื้นที่ที่เหลือร่วมทุกโมเดล; Face+Neck/NeckCoverageเป็นnullสำหรับกรณีเหล่านี้.
4. Face valid domain `V_i = original grid − known Neck_i − GT-only uncertainty_i`. ใช้Neck/UของGTคนที่ประเมินเท่านั้น ไม่ignoreคอคนอื่นทั้งภาพ. Known opaque occluder coresเป็นvalidnegative; ไม่เติมamodalNeckหลังวัตถุ. พบplantเข้าdraftNeckแล้วแก้จากRGBก่อนเปิดคะแนนFace; draftเก็บไว้.
5. Mappingเดิมไม่เปลี่ยน: CIHPFace13; SapiensFace_Neck3+mouth subparts24–28. ไม่ใช้Torso-skinแทนNeck ไม่แบ่งpredictionด้วยGTหรือgeometry. Sapiensoutputยังเป็นFace+Neckcandidate ไม่กลายเป็นstrictFace-only output.
6. ตรึงmanualannotations/GT masks/eligibility/domain hashesและprotocol **ก่อนคำนวณคะแนนFaceใหม่นี้**. รู้historical/non-Face resultsมาก่อน จึงเป็นpost-hoc exploratory revision ไม่ใช่preregistered/blinded confirmation. ไม่มีการปรับGT/mappingจากFace scoresรอบนี้.

GTcoverage: Face21/35 (day9/night12), validFacepositive36,743pixels จากsourceFaceของ21items45,453pixels เหลือ80.837%. ส่วนที่ถูกกัน/เปลี่ยนบทบาทรายitemอยู่ในprivatebinding. สัดส่วนนี้ไม่ใช่annotationaccuracyหรือความสมบูรณ์ทั้งdataset.

[Protocol revisionR2](../configs/CONTROLLED_ROI_FACE_NECK_PROTOCOL.json) / [GTcoverageและstates](FACE_NECK_GT_SUMMARY.json) / [CPU+actual-packet acceptance](FACE_NECK_ACCEPTANCE.json). Historical [non-Face report](CONTROLLED_ROI_GT_AND_PART_RESULTS_TH.md) และR1indexยังคงnullFaceตามสถานะตอนนั้น ไม่ได้แก้ย้อนหลัง.

## Face+Neck delivery และ known-Neck coverage — supplementary n3

หน่วยpercent. Face+Neckใช้mean per-part IoUบนvaliddomainที่ตัดGTuncertainty; Neckcoverageคือmean recallของcandidateบนknownNeck. **ไม่ใช่Neck-only IoU/precision** และไม่รวมซ้ำในprimaryMacro4.

| Checkpoint | Face+Neck IoU n3 | Known-Neck coverage n3 |
|---|---:|---:|
| QANet_CIHP_HRNetW48_512x384 | 62.288 | 5.949 |
| M2FP_R101_CIHP | 39.632 | 3.668 |
| D2FP_R101_CIHP | 70.151 | 30.438 |
| RPR_CIHP | 61.729 | 4.512 |
| CPI_R50_CIHP | 63.509 | 5.386 |
| CPI_ConvNeXtB_CIHP | 55.091 | 0.000 |
| Sapiens2_0.4b | 85.751 | 68.605 |
| Sapiens2_0.8b | 84.240 | 57.126 |
| Sapiens2_1b | 86.614 | 66.336 |

KnownNecksupportรวม10,190pixels; n3น้อยและขนาดไม่สมดุล จึงใช้เป็นdiagnostic ไม่สรุปNeckcapabilityทั่วไป. ไม่รายงาน18unknownNeckเป็นbackground/score0หรือส่งผ่านว่าverifiedabsent. สถานะverified-not-visibleรองรับในscorerแต่ชุดGTนี้ไม่มีกรณีนั้น.

## Matching, metrics และ completeness

คงmatchingจากowner-correctedsourceparts union→frozenYOLO bbox coverage≥0.50, maximumcardinalityก่อนsumcoverage และtie policyเดิม. NewNeck/Uไม่เปลี่ยนmatching, detectorcache, parserinstance selection หรือownership. เป็นpartial-person association ไม่ใช่maskAPหรือfull-personF1.

ต่อeligible partใช้whole original-grid person plane, ไม่clipด้วยGTbbox/polygon. `TP=|G∩P∩V|`, `FP=|P∩V−G|`, `FN=|G∩V−P|`; IoU=TP/(TP+FP+FN), Dice=2TP/(2TP+FP+FN). Meanของแต่ละpartภายในtargetก่อนmacro4; pooledIoU/Diceเป็นตารางประกอบ ไม่เฉลี่ยnative-classIoUแทนunion. Zero-supportgroupsเป็นnull.

GTpersonที่ไม่จับคู่ใช้emptycandidateและpositivepartsเป็นFN/IoU0. Faceมี **2unmatched partsคงอยู่ในn21**; Hair5/Upper15/Lower14ตามเดิม. `detector_unmatched`รวมกรณีไม่มีeligiblebboxหรือone-to-onecompetition ไม่พิสูจน์ว่าdetectorไม่เห็นคนในทุกกรณี. Validextentแต่semanticemptyคงเป็นemptytargetprediction ไม่ใช่executionfailure.

STRICT_COMPLETEต่อระบบ: accepted90unique source framepackets + non-Face statisticsเดิมที่ครบ + Face21eligible tasks + delivery3tasksครบ. ผลจริงครบ9/9, missing/duplicate/scoringfailed0ในacceptedview. Historicalmodel/setup/controller/CPUerrorsยังเก็บครบ; finalfailed0ไม่ได้แปลว่าไม่เคยล้ม. SourceCCTVเป็นpartialselectedpeople/parts ไม่สร้างunlabeledpeopleเป็นfull-scenenegatives และไม่อ้างfull-sceneFP/AP.

## ตรวจอะไรจริงและreuseอะไร

- CPU9independent literal casesPASS: known/unknown/absentNeckต่างกัน, OTHER/invalidID, union, positiveFN/missedperson/wrongperson, knownoccluderFP, asymmetricgeometry, mean-part vs pooled, null/STRICT_COMPLETE, actualatomicpacket→scorer→JSON และsourceimmutability. ไม่รับรองGTจากtestcount.
- ActualFacepacket→scorer→reportครบ **171 source framepackets /189Face tasks /27delivery tasks**. ReadbackNPZ/COMMIT/sourcepacket identity เทียบacceptednon-Faceframe, checkpoint/input/config/native-label/original-grid/YOLObindingsและmaskhashes. Per-frameledger/recordhashes,GTsupport/counts/means/Macro4reconciliationผ่าน.
- ReuseHair/Upper/Lowerและexact90membership auditเดิม; ตรวจตัวเลขเหมือนเดิมแบบfullprecision ไม่rerun non-Facescoringหรือmodelinference. Sourceweights/environment identitiesใช้หลักฐานรับรองเดิม ไม่bulkrehashweights/datasetsใหม่เพื่อเขียนรายงาน.
- Usage-limit interruptionเกิดระหว่างGTmaterialization; กลับมาตรวจprocessและfinalbindingพบเขียนเสร็จแล้ว จึงใช้ต่อ ไม่เปิดซ้ำ. CPUscoringรอบนี้เปิดครั้งเดียวและปิดครบ.

Scientificbindingsตรึงด้วยfilehashesก่อนFaceCPUscoring; Gitcommitรอบส่งมอบเป็น **post-scoring publication snapshot** ไม่ใช่launchcommitของmodelinferenceหรือหลักฐานว่าsourceถูกcommitก่อนCPUlaunch. Sourcecurrent`CCTV_Human_Parsing_Benchmark/`; publicationcheckout`Human_Parsing_Study_Public/`แยกกัน.

## ภาพและartifacts

Privatepathsที่เปิดได้ในworkspace:

- `CCTV_Human_Parsing_Benchmark/outputs/face-neck-comparison-gallery-20261101/index.html` — fixed6framesเดิม,RGB/GT/เก้าระบบ, paletteเดียวกัน; ไม่เลือกภาพตามคะแนน. Gallerycomposition/downsamplingใช้แสดงผลเท่านั้น ขณะที่scorerใช้per-personfullgrid. SapiensFacecandidateในภาพรวมNeckด้วย.
- `outputs/face-neck-gt-reviewed-20261101/GT_ONLY_CONTACT/page_01.png` ถึง`page_06.png` — 21eligibleFaceGT overlaysที่ตรวจจริง (RGBเทียบFace/knownNeck/U/occluder). Directoryเก็บmaskdraft/GT-only reviewก่อนfinalfreeze; frozenbindingอยู่pathถัดไป.
- `outputs/face-neck-gt-frozen-20261101/index.html` — GT auditindexทั้ง35dispositionsและ21eligibleoverlays; `FACE_NECK_GT_BINDING.json`และ21original-gridGTNPZsอยู่directoryเดียวกัน. ตรวจarraysเท่ากับชุดที่เปิดดูจริงก่อนfreeze.
- `outputs/face-neck-manual-review-20261101/` — RGB/sourcecoordinates35items, frozenmanualvertices, ineligibleitemreasons, context/detailfigures.
- `outputs/face-neck-evaluation-20261101/` — Faceper-personrecords,immutableledgers,FROZEN_INPUTS,canonicalMETRICS/RESULTS.

ภาพCCTV,sourcefilenames,manualvertices/personrecords,GTmasks,predictions/logsอยู่privateoutputsเท่านั้น ไม่มีCCTVassetsขึ้นPUBLICGit. Publicrepoมีcode/tests/protocol/aggregateCSV/JSON/docs; cloneอย่างเดียวไม่พอทำซ้ำ ต้องมีrestrictedsourceassets,parentpredictionpacketsและGTbindingsตามhashes. [CPUrequirements](../requirements-cpu.txt)เป็นexistingenvironmentที่สังเกต ไม่ได้ติดตั้งหรือแก้modelenvironment.

## ข้อจำกัดและสถานะจบ

เปรียบเทียบ **checkpoint + controlledYOLO-ROI applicationconfiguration** บนCCTV90ชุดนี้: crop/context/ownershipร่วมกัน แต่native resolution,normalization,internaldetector/decoderต่างกัน. ไม่แยกarchitecture/training-data/adapter effects. NativeCIHP/commonCIHPresultsและfrozenYOLOคงเดิม.

GTยังเป็นagent-assistedreview ไม่ใช่independentexpertgold; Faceมีuncertaintydomainและ14excludeditems, Neckpositiveviewเพียง3items. คะแนนจึงรองรับการเลือกเบื้องต้นจากreference/domainนี้ ไม่รับรองstrictFace-only/Neck-only,ทุกคน/ทุกส่วนในฉาก,night/generalCCTVperformance,สี/attributes หรือproductionacceptance. Timing/VRAMของเดิมเป็นsharedGPUadapterdiagnostics ไม่ใช้จัดอันดับFPS/latency/VRAMefficiency.

**รอบประเมินสี่targetsปิดแล้วบนdeclaredeligibleGT ไม่เหลือFace-scorejobหรือGPUjobที่ต้องเปิดต่อเพื่อให้ได้ตารางนี้.** ขั้นถัดไปคือใช้รายงานนี้พิจารณาSapiens2 1B/QANetตามความต้องการ หรือจัดindependentGT/deploymentvalidationหากต้องการคำอ้างที่เข้มกว่า. ไม่เริ่มการฝึก สี CCTVinferenceเพิ่ม หรือexperimentอื่นอัตโนมัติ.
