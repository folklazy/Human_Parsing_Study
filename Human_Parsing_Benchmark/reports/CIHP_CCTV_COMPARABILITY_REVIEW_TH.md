# ตรวจความเทียบกันได้ของ CIHP และ CCTV 90 ภาพ

ตรวจ 2 พฤศจิกายน 2026 (Asia/Bangkok) · **AUDIT_COMPLETE / CROSS_DATASET_DIRECT_COMPARISON_NOT_VALID / CONTROLLED_CIHP_NOT_RUN**

## คำตอบและข้อแก้ไข

ข้อสงสัยของผู้ใช้มีเหตุผล: การนำอันดับ CIHP เดิมไปเทียบกับ CCTV รอบ controlled ROI แล้วอธิบายว่าเป็นความสามารถของโมเดลล้วน ๆ ไม่ถูกต้อง เพราะเปลี่ยน input route, ownership, GT/domain และการเฉลี่ยคะแนนพร้อมกัน **ยังไม่พบ arithmetic error ในสถิติที่ตรวจ แต่พบความไม่ตรงกันของคำถามที่แต่ละตารางตอบ**. การใช้ official CIHP validation ไม่ทำให้ C4-P หรือ Q_GT ที่โครงการกำหนดเป็น official benchmark โดยอัตโนมัติ

CIHP เดิมยังเป็นผลที่ใช้ได้ของ checkpoint พร้อม application configuration ที่ระบุ ส่วน CCTV เป็นผลเฉพาะ selected annotated parts ภายใต้ controlled ROI และ GT ที่ตรวจแก้แล้ว ไม่ใช่ gold standard ที่รับรอง CIHP ว่าผิด และยังไม่ใช่ independent expert-reviewed test set. ไม่ควรลบผลเดิมหรือเปลี่ยน weight/mapping จน Sapiens ชนะ

รอบนี้ทำ CPU audit และ aggregation sensitivity จากสถิติจริงเสร็จแล้ว ไม่มี inference/mask rescore ใหม่ ไม่มีการเขียนทับ GT, predictions, scientific configs หรือ scorer เดิม. ผลและขอบเขตตรวจอยู่ใน [evidence](CIHP_CCTV_COMPARABILITY_EVIDENCE.json), [ตารางก่อนปัดเศษ](../metrics/CIHP_CCTV_AGGREGATION_SENSITIVITY.csv), [สคริปต์ทำซ้ำ](../scripts/audit_cihp_cctv_comparability.py)

## 1. เงื่อนไขที่ต่างกันจริง

| ประเด็น | CIHP common C4-P revision2 | CCTV controlled ROI ล่าสุด | ผลต่อข้อสรุป |
|---|---|---|---|
| ประชากร | official validation 5,000 ภาพ/ระบบ; 17,520 GT persons, 17,454 eligible C4 persons | 90 ภาพ/130 YOLO ROIs; GT ใช้ได้ Hair61/Face21/Upper112/Lower96 รวม290parts | จำนวนภาพและหน่วยประเมินไม่ใช่สิ่งเดียวกัน |
| QANet input | native YOLO box/aspect conversion + native ROI expansion | shared person crop/context10% แต่ละข้าง + letterbox; ไม่ขยาย ROI ซ้ำ | แม้ QANet ก็เปลี่ยน configuration |
| M2FP/D2FP/RPR/CPI input | native full frame/internal instances → YOLO association | shared person crops → native parser → designated-instance selection | ความยากและบริบทของ internal detection เปลี่ยน |
| Sapiens input | ทั้งภาพ stretch เป็น1024H×768W | crop ต่อคน + aspect-preserving letterbox1024H×768W | ขนาดคนใน tensor/context/distortion ต่างกัน |
| Ownership | QANet/Sapiens ใช้ YOLO extents; อีกห้าระบบคง native extents หลัง association | final extents/identity และ clip ตาม YOLO เดียวกันทุกระบบ | fairness ของ opportunity/extent ใน CCTV ควบคุมมากกว่า |
| Augmentation | ตาม frozen checkpoint config; บางระบบมี flip/multiscale | ปิด external TTA; คง internal architecture เช่น CPI branches | compute/behavior ไม่เหมือนกัน; อย่าเหมารวมทุก native route ว่า no TTA |
| Face | CIHP Face เป็น reference; Sapiens Face_Neck+facial subparts เป็น proxy; ไม่มี neck GT แยก | Face domain ตัด known neck และ GT-only uncertainty รายบุคคลออก; 21/35 eligible | Sapiens neck prediction อาจเป็น FP ใน CIHP แต่ถูกกันออกใน CCTV บางพื้นที่ |
| เสื้อผ้า | CIHP UpperClothes+Coat / Pants+Skirt; Dress/Apparel เป็น OTHER | projection เดียวกัน แต่ reference เป็น selected CCTV annotations ที่ผ่าน screen | ชื่อ mapping เหมือนกันไม่ได้ยืนยัน annotation equivalence |
| ตัวชี้วัดหลัก | รวม global pixel confusion ทั้งชุด → IoU รายคลาส → mean4 | IoU ของแต่ละ GT part → meanภายในคลาส → mean4 | CIHP ให้ส่วนที่มี union ใหญ่มีน้ำหนักมากกว่าในแต่ละคลาส; CCTV ให้แต่ละ part เท่ากัน |
| Person matching | mask-IoU one-to-one ที่0.50/0.75, geometry-canonical rev2 | partial GT union-box coverage0.50 กับ frozen detector opportunities | threshold0.50 ไม่ได้หมายถึง matching metric เดียวกัน |
| Negatives/การตรวจเกิน | global valid BG/OTHER คิด FP; Q_GT ไม่หัก unmatched prediction โดยตรง | ประเมิน candidate ของคน/ส่วนที่มี GT; unannotated people ไม่ใช่ global negatives | pooled CCTV ก็ไม่เท่ากับ full-image confusion; ไม่อ้าง scene precision จาก partial GT |
| GT quality | release annotations เดิม; native label identities มี bindings | derived owner fixes/contour screen/Face uncertainty; ผู้ช่วยเป็นผู้ตรวจ | ต้องมี independent annotation review ก่อนคำอ้างที่เข้มขึ้น |

หลักฐาน source: [CIHP input](../src/common_view/sapiens_route.py), [CIHP scorer](../src/common_view/core.py), [CCTV adapter](../../CCTV_Human_Parsing_Benchmark/scripts/controlled_roi_models.py), [ROI geometry](../../CCTV_Human_Parsing_Benchmark/scripts/sapiens_input_variants.py), [CCTV scorer](../../CCTV_Human_Parsing_Benchmark/scripts/controlled_roi_evaluation.py), [Face scorer](../../CCTV_Human_Parsing_Benchmark/scripts/face_neck_evaluation.py), [CCTV mapping/matching](../../CCTV_Human_Parsing_Benchmark/configs/CONTROLLED_ROI_SCORING_PROTOCOL.json)

## 2. ผลจริงและ sensitivity ของ aggregation

ตารางต่อไปนี้วางเทียบเพื่ออธิบายความต่างของนิยาม **ห้ามลบคะแนน CIHP−CCTV เพื่อวัด domain degradation**. คอลัมน์ pooled CCTV คำนวณจาก counts ของ selected person-part tasks ไม่ใช่ global pixels ที่ไม่ซ้ำทั้งภาพ และไม่ใช่คะแนนหลักใหม่. ไม่มีการเลือก aggregation ตามโมเดลที่ชนะ

| Checkpoint | CIHP global C4-P % | CCTV mean-part Macro4 % (เดิม) | CCTV pooled person-part mean4 % (diagnostic) |
|---|---:|---:|---:|
|QANet_CIHP_HRNetW48_512x384|80.984|64.533|75.881|
|M2FP_R101_CIHP|83.623|51.519|71.016|
|D2FP_R101_CIHP|82.610|49.323|69.846|
|RPR_CIHP|78.747|47.576|63.975|
|CPI_R50_CIHP|78.595|43.477|64.471|
|CPI_ConvNeXtB_CIHP|81.961|55.441|72.585|
|Sapiens2_0.4b|75.827|61.513|77.653|
|Sapiens2_0.8b|74.618|60.479|77.668|
|Sapiens2_1b|72.759|65.430|80.735|

ตัวอย่าง QANet: เปลี่ยนเฉพาะ aggregation บน CCTV จาก64.533เป็น75.881 ไม่ได้ inference ดีขึ้นหรือแก้ mask. Sapiens0.8B ต่ำกว่า0.4B ใน mean-part แต่สูงกว่าเล็กน้อยใน pooled; แสดงว่าลำดับอาจเปลี่ยนได้แม้ภาพ/GT/prediction คงเดิม. ขณะเดียวกัน M2FP ยังไม่เป็นอันดับหนึ่งใน CCTV เมื่อใช้ pooled จึงอธิบายทั้งหมดด้วย aggregation อย่างเดียวไม่ได้

IoU_c=TP/(TP+FP+FN), Precision_c=TP/(TP+FP), Recall_c=TP/(TP+FN), F1_c=2TP/(2TP+FP+FN). สำหรับ binary pixel masks F1 เท่ากับ Dice. Mean-part IoU_c=(sum IoU_i)/N_c; pooled IoU_c=sumTP_i/sumUnion_i เท่ากับค่าเฉลี่ย IoU_i ถ่วงด้วย union_i จึงมีน้ำหนักต่างกัน. C4-P global mean เป็นค่าเฉลี่ยสี่ IoU จาก global confusion ไม่ใช่เฉลี่ย IoU ของ native classes ที่รวมกลุ่ม

Q_C4_GT เป็น supplementary project metric: match person extents ก่อน → mean IoU ของ target classes ที่มีใน GT หรือ prediction ของคู่นั้น → รวม eligible GT persons โดย missed=0. ไม่ใช่ AP/PCP/F1 และไม่ลงโทษ unmatched predicted persons โดยตรง. G_sem=17,454 ของ common CIHP ห้ามยกมาใช้ CCTV290parts. Native20 Q ใช้17,520และอีก taxonomy แยกกัน

## 3. Sapiens: หลักฐานสาเหตุและสิ่งที่ยังสรุปไม่ได้

- **ยืนยันจาก source:** CIHP full-frame stretch กับ CCTV controlled ROI คนละ input configuration; ไม่ใช่แค่เปลี่ยน dataset path. การ harmonize คะแนนย้อนหลังไม่สามารถทำให้ network เคยเห็น crop ได้
- **หลักฐาน diagnostic เดิมบน CCTV0.4B:** same6images/31parts/GT/mapping/YOLOownership ได้ mean-part Macro4=37.447% full-frame stretch,29.913% full-frame letterbox,59.575% person ROI letterbox. การเพิ่ม22.128pp รองรับผลของ input configuration ในชุดนั้น; ไม่พิสูจน์ว่า stretch อย่างเดียวผิด, ไม่ใช่ estimate CIHP5000, และไม่แทนผลทั้งสามขนาด. [รายงานและ attempts](../../CCTV_Human_Parsing_Benchmark/reports/SAPIENS2_INPUT_DIAGNOSTIC_TH.md)
- **ไม่พบหลักฐาน RGB/BGR หรือ normalization ซ้ำใน audit เดิม:** official-normalizer CPU parity/asymmetric geometry ผ่าน; controlหนึ่งภาพมี original-grid hard maskตรง แต่ raw logitsต่างเล็กน้อยและมี failed numeric gate เก็บไว้. ห้ามเรียก bitwise forward parity ทั้งประชากร. [หลักฐาน preprocessing](../../CCTV_Human_Parsing_Benchmark/reports/SAPIENS2_PREPROCESSING_AUDIT_TH.md)
- **Face mismatch มีจริงตาม taxonomy:** native29ใช้ Face_Neck ไม่ใช่ Face-only. จำนวน FP ของ neck ที่แท้จริงใน CIHPยังไม่ทราบ เพราะไม่มี neck GTแยก. ห้ามกล่าวว่าคะแนนต่ำทั้งหมดเกิดจากคอ/GTผิด หรือ ignore neck จาก prediction เพื่อช่วยคะแนน
- **Domain/training exposure เป็น residual confounder:** CIHP-labelled checkpoints กับ Sapiens taxonomy/trainingต่างกัน. UNKNOWN overlap ไม่ใช่ NO overlap; การตรวจครั้งนี้ไม่ได้พิสูจน์การปนเปื้อนหรือแยกผล architecture. กล้อง/ขนาดคน/แสง/occlusionอาจมีผล แต่ยังไม่มี controlled CIHP ROIผลใหม่เพื่อแยกแต่ละสาเหตุ

## 4. คำว่าเป็นมาตรฐานและเป็นทางการ

IoU/mIoU, Precision/Recall, Dice/F1 เป็นสูตรมาตรฐาน แต่ protocol ต้องระบุหน่วย, classes, valid domain, negatives, matching และ aggregation. Custom task ที่นิยามโปร่งใสทำงานวิจัยได้ ไม่ควรเปลี่ยนชื่อให้ดูเป็น official reproduction

[CIHP/PGN ของผู้จัดทำ](https://github.com/Engineering-Course/CIHP_PGN) มี evaluation code สำหรับงาน instance-level parsing. [Parsing R-CNN official repository](https://github.com/soeaver/Parsing-R-CNN#results-and-models) รายงาน mIoU และ parsing APp50/APvol/PCP50 แยกกัน จึงห้ามเรียก Q_GT หรือ extent F1 ว่า parsing AP. [Sapiens2 native29 documentation ที่ revisionเดิม](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/docs/SEG.md) ระบุ Face_Neck/Upper_Clothing/Lower_Clothing/Apparel ต่างจากCIHP20. รอบนี้ตรวจแหล่งต้นทางเหล่านี้แล้ว แต่ไม่ได้รัน official evaluators หรือรับรอง reproduction

ให้รายงานสามคำถามแยกชัด: (1) native20 application reference ของหกระบบ (ยังมี YOLO association จึงไม่ใช่ official reproduction), (2) common C4-P CIHP application comparison ของเก้าระบบที่ routeต่างกัน, (3) controlled ROI selected-part CCTV comparison. คำว่า winner ต้องผูกกับตาราง/metric/GT/version ไม่ใช่โมเดลที่ดีที่สุดทั่วไป

## 5. ข้อเสนอรอบเปรียบเทียบที่ควบคุมได้จริง

เลือก **controlled YOLO person-ROI application comparison** เป็นการศึกษาถัดไปบน CIHP; reuse validated CCTV adaptersทั้งเก้าระบบแทนแก้เฉพาะ Sapiensให้ได้ inputที่ดีกว่า. นี่เป็นข้อเสนอวิธีทำที่แนะนำและได้รับอนุญาตในหลักการจากคำสั่งล่าสุด แต่ **ยังไม่เป็น execution manifest ที่ผ่าน readiness**. ผู้ใช้ไม่ต้องยืนยันอนุญาต inference ซ้ำเพื่อทำงานในขอบเขตนี้ ทว่าไม่ควรเปิด old controller5000โดยถือว่า contractตรงแล้ว

1. ใช้ CIHP5000 IDsเดิม/checkpointsเดิม/frozenYOLO cache; ทุกโมเดลได้ ROI/context10%/RGBbytesและ final extentเดียวกัน. คง native normalization/resolution, FP32/batch1/no externalTTA; internal CPI feature branchesคงเดิม. Model-specificinternal instance selectionตาม adapterเดียวกับCCTV. ควบคุม shared opportunity ไม่เท่ากับควบคุม training/computeทั้งหมด
2. แยก protocol ใหม่/run/output/hashจากnative/commonเดิม. Freeze geometry, projection, scorer, dispositionก่อนดูscoreใหม่; noVAL threshold tuning, score-drivencrop selectionหรือbest-attemptselection. คนYOLOmissต้องได้0ใน eligible-person/part metricsตามนิยามและนับแยกจากexecutionfailure
3. PrimaryบนCIHPคง conventional global C4-P mIoU4/per-target IoUจาก projected pixels; รายงาน mean-part, pooled person-part และQ/F1เป็นsecondaryโดยไม่รวมเป็นweightedscoreใหม่. CCTVคง primarymean-partเดิมและpooledประกอบ. **เลือกสูตรเดียวไม่ได้ทำให้GTdomainsเหมือนกัน**; รายงานผลข้ามdatasetเป็นexternal-validity evidenceมีข้อจำกัด ไม่ลบคะแนนหาความสามารถที่ตกลงโดยอัตโนมัติ
4. Faceใช้สองชื่อแยก: CIHP-reference proxy และ CCTV neck-excluded domain. หากต้องการ headlineFaceที่equivalentจริง ต้องมี independent Face/Neck/uncertainty GTบนชุดที่กำหนดล่วงหน้าและใช้domainเดียวกับทุกโมเดล; ไม่ใช้ GTแก้prediction ไม่ใช้geometrysplit. Hair/garment C3เป็นsensitivityประกอบ ไม่มีการอ้างว่าผ่านstrict4targetsเมื่อFaceยังเป็นproxy
5. Readinessเฉพาะช่องว่าง: CIHP cache→opportunity binding, RGBcrop hashes, losslessCPIbridge, channel/asymmetricmapback, intendedinstance selection, no-person/empty/duplicate, globalcompose-before-project และfixedGTvoid; literalCPUfixturesและpacket→scorer→report. Reuseเดิมเมื่อ source/configตรง; TRAIN bounded checksก่อนVALและเก็บ model-call budgetในmanifest
6. ก่อนเปิดGPU ต้องมี exactROIjobcount, pilot-byte estimate, peaksตามขนาดแต่ละmodel, sharedGPUheadroom, diskreserve/freeguard50GiB/permodel80GiB/24hและimmutable attempt history. ไม่ใช้จำนวนparamsตัดสินว่าVRAMพอ. Freeze reused/pendingตามscientificbindings; full-frame packetsเดิมไม่ผ่านROIreuseเพราะinputต่างกัน. ไม่rerunYOLO; QANetเดิมก็ reuseไม่ได้โดยอัตโนมัติถ้าcropcontractต่าง
7. หลัง readiness ใช้ one detached worker/locks, per-model stop-on-error/no hiddenfallback/retry และexact5000strictcompleteก่อนคะแนนหลัก. SharedGPUauthorizationไม่ใช่การยกเลิกguards. รายงานคะแนนหลังclosure ไม่ปรับprotocolระหว่างดูrank

การรันSapiens ROIบนCIHPอย่างเดียวตอบได้เพียง **input-route sensitivityของSapiens** หากต้องการ leaderboard controlledROIทั้งเก้าต้องทำconfigurationเดียวกันตามข้อ1กับทุกระบบที่ยังไม่มีpredictionsตรงbinding. ความต่างนี้เป็นเหตุผลต้องมีinferenceใหม่ในอนาคต ไม่ใช่เหตุผลrerunเพื่อให้คะแนนสวยขึ้น

## 6. Risk disposition และงานที่ยังเหลือ

| ประเด็น | ระดับ/ผลต่อคำอ้าง | สิ่งที่ปิดแล้ว/งานต่อ |
|---|---|---|
| เทียบต่างroute/metricว่าเป็นmodel-onlywinner | MUST_FIX สำหรับคำอ้างนั้น | แก้label/รายงานและเพิ่มsensitivityแล้ว; controlledCIHPใหม่ยังไม่รัน |
| Face_NeckกับFaceและGTdomainต่าง | MUST_FIX สำหรับstrictface-equivalence | proxyแยกชัด; independentFace/NeckGTยังไม่มี ไม่แก้ด้วยweight |
| CustomQดูเหมือนofficialmetric | MUST_FIX ด้านการนำเสนอ | กำหนดsupplementary projectmetric/formula/FP caveatและofficialreferenceแล้ว |
| arithmetic/canonicalnull/membership | CONTROL_AND_REPORT | เก้าCIHPcanonicalMETRICShashesตรง; reuseexactmembershipauditเดิม; 36targetcount/formula/domainchecksผ่าน |
| CCTVpartialannotation/unmatchedpred | CONTROL_AND_REPORT | ใช้selectedperson-partclaims; ไม่มีfullsceneAP/precisionclaim |
| GTreviewหลังเห็นผล/ผู้ตรวจคนเดียว | RESIDUAL_LIMITATION | exploratory; ยังต้องindependentreviewเพื่อstrongconfirmation |
| exposure/architecture/internaldecoder | RESIDUAL_LIMITATION | ไม่อ้างควบคุมข้อมูลฝึกหรือzero bias |
| sharedGPU/timingขอบเขตต่าง | CONTROL_AND_REPORT | ไม่จัดspeed/VRAMefficiencyranking |

ตรวจGPU ณ2026-11-02 17:56เวลาไทย: TeslaT4,ใช้อยู่10009/15360MiB,externalPID1846640;ไม่พบactivebenchmarkworkerจากprocessnamesที่ตรวจ พบtmuxsessionlauncherเก่าเพียงอย่างเดียวซึ่งไม่ใช่หลักฐานworkerทำงาน. ไม่แตะprocessอื่น. **ไม่ได้ใช้externalPIDอย่างเดียวเป็นblocker** และยังไม่ได้วัดresourceadmissionของcontrolledCIHPconfigurationใหม่. รอบนี้ไม่เปิดinferenceเพราะทำcomparabilityaudit/แก้reportingก่อน; ไม่อ้างว่ารันใหม่แล้วหรือfullfairnessปิดครบ

## 7. การตรวจที่ทำจริงและวิธีทำซ้ำ

`python3 Human_Parsing_Benchmark/scripts/audit_cihp_cctv_comparability.py`

ตรวจ9modelIDs/order, CIHPacceptedcompletion5000และexact-membership flagsจากindexเดิม, canonicalMETRICShashes9ไฟล์, protocolhashes3ไฟล์, CCTV90/130acceptedcompleteness, targetrowunique36, sharedGTsupport/domains, nonnegativeTP/FP/FN/TN, IoU/F1จากintegercounts, mean4ตรงsummaryทั้งสองชุด และimmutabilityของ16inputsที่อ่าน. ไม่อ้างว่าเป็นpacket/fullGTauditใหม่หรือmodel execution acceptance. CSVมี36targets+9macro rows; outputevidenceระบุhashesและขอบเขตชัดเจน

ผลauditนี้ไม่รับรองว่าGTถูกทุกpixel, checkpointทั้งหมดใช้bestsettings, หรือpaperreproductionผ่าน. ขั้นต่อไปที่ตรงเป้าหมายคือ bind/ตรวจcontrolledCIHPROIreadinessตามข้อ5 แล้วจึงรันconfigurationใหม่เมื่อผ่าน โดยยังเก็บตารางเดิมเป็นhistoricalreferenceครบ
