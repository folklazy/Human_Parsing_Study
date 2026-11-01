# ตรวจวัด Sapiens2 ใหม่: scorer, ownership และ fresh inference ทั้งสามขนาด

ตรวจปิด 2026-11-01T10:14:29.486816+07:00 (Asia/Bangkok). **CPU reconciliation90ภาพ×3ขนาดครบ และfreshROI diagnostic6ภาพ×3ขนาดครบ**. รันใหม่รวม51calls=TRAIN3+full-framecontrols3+ROI45;ทั้ง3worker/controllerหยุดแล้ว. ไม่มีfull90/CIHP5000หรือโมเดลอื่นต่อ.

**ข้อสรุปที่ต้องแก้จากรอบก่อน:** พบsourceGTownershipผิดอย่างน้อย2ภาพ โดยlabelownerเดียวรวมส่วนของคนละคน;เป็นข้อผิดพลาดที่การตรวจภาพรอบก่อนของผมพลาดไป จึงพักข้อสรุปการเลือกจากตาราง90ภาพของทุกโมเดลไว้ก่อน. ไม่พบการนับIoU/Diceผิดหรือการอ่านperson/channelผิดในหลักฐานที่ตรวจ แต่คะแนนที่รายงานเดิมเป็นค่าเฉลี่ยรายส่วนที่ให้น้ำหนักส่วนเล็ก/คนที่พลาด ไม่ใช่pooledpixelIoU. Full-frameinputจำกัดผลของSapiensมากในชุดdiagnostic;ตารางfreshROIด้านล่างเป็นหลักฐานของแต่ละขนาดโดยตรง ไม่ยกผล0.4Bไปแทนขนาดอื่น. ไม่ปรับGT/mapping/thresholdให้คะแนนดีขึ้น.

## 0. ปัญหาGTที่พบจริง — ต้องปิดก่อนใช้คะแนนเลือกโมเดล

ตรวจภาพRGBและcanonicalpolygonJSONยืนยัน2กรณี:หนึ่งภาพมีfaceของสองคนใช้ownerlabelเดียวกัน;อีกภาพมีlowerของคนใกล้/ไกลใช้ownerlabelเดียวกัน. Human_idsจึงรวมtargetจากคนละคนก่อนmatching ทำให้เกิดทั้งผิดคนและmissปลอมได้. ปัญหานี้อยู่ในreferenceต้นฉบับ ไม่ใช่Sapiensเท่านั้น และไม่ได้เกิดจากการอ่านnativeclassIDผิด.

GT-onlyspatialtriageจากsame-labelpolygonsที่อยู่ห่างกันมากพบ3candidate;เปิดภาพตรวจครบ พบ2ownerconflictsและ1กรณีที่เป็นเสื้อคนเดียวถูกอุปกรณ์บังจริง ไม่ตัดกรณีหลังอัตโนมัติ. การtriageนี้ไม่รับรองว่าownerที่เหลือทั้งหมดถูกต้อง. ทำprivatecorrectionproposalรายpolygonไว้ แต่ยังไม่แก้sourceGTหรือคะแนนเก่า. [PublicGTreview](GT_OWNER_BINDING_REVIEW.json).

ทั้ง2confirmedcasesอยู่นอก6ภาพdiagnosticนี้ แต่ไม่ทำให้6ภาพกลายเป็นexpert-certifiedGT. ผลfreshด้านล่างยังเป็นdiagnostics. หลักฐาน2ภาพมีอยู่privateoutputsในรูปGT_targets/matching_review และGT_OWNER_ISSUES_PRIVATE.json. ตัวเลข90ภาพยังเป็นagreementกับownerlabelsที่ให้มา ไม่ควรใช้รับรองfair/finalselectionจนปิดGTownerQAและcontourrequirements.

ขั้นต่อไปที่จำเป็นคือทบทวนproposalและสร้างderivedGT/bindingversionที่แก้ownerอย่างเปิดเผย จากนั้นCPUscoreใหม่จากsavedpackets;ไม่ต้องinferenceโมเดลซ้ำเพื่อแก้ownerlabels. ห้ามใช้parser/YOLOpredictionสร้างGTownerหรือแต่งcontour และต้องเก็บsourceGTเดิมไว้.

## 1. ตรวจว่าคำนวณผิดหรือไม่

อ่านsavednative29/full-frame/personplanesของSapiensทั้ง3ตัวรวม270packetsและGTbindingsเดิม. ใช้binary2×2contingency `[TN,FP,FN,TP]` แยกจากintersectionhelperเดิมตรวจทุก315GTpartsต่อระบบ รวม945items. TP/FP/FNตรงcanonicalselected-partrecordsทุกค่า. Native labelsอยู่0–28;exportedpersonplanesเท่ากับnativefullframe×frozenYOLOmaskจริง และextents/scores/orderตรงcache.

จึงยังไม่พบว่าคะแนนเกิดจากscorer arithmetic, classindexหรือลำดับpersonplaneผิด. ข้อสรุปนี้ไม่รับรองว่าannotation/taxonomyหรือinputconfigurationเหมาะสมทั้งหมด. Independenthand-counted3casesและcoordinate-setreadbackบนfreshpacket3modelผ่านด้วย. [Evidence](SAPIENS2_MEASUREMENT_REVIEW_EVIDENCE.json).

## 2. ทำไมค่า40%กับภาพบางส่วนจึงดูไม่สอดคล้องกัน

ตัวหารทั้งตารางนี้เหมือนกัน:315selectedGTpartsบน90inputs. **Primary** เฉลี่ยIoUรายpartภายในtargetก่อนเฉลี่ย4targets. **Pooled-partIoU** สะสมTP/FP/FNภายในtargetก่อนหารแล้วเฉลี่ย4targets;ส่วนที่ใหญ่มีน้ำหนักpixelมากกว่า. เป็นคนละaggregationจึงให้ค่าต่างกันได้โดยไม่ใช่bug. ทั้งคู่ยังเป็นselectedpartmetrics ไม่ใช่full-scene mIoU.

|Sapiens size|Primary mean-part IoU4%|Mean pooled-part IoU4%|Detector-present mean IoU4% (diagnostic)|Zero-TP parts /315|
|---|---:|---:|---:|---:|
|Sapiens2_0.4b|42.023|65.467|49.315|71|
|Sapiens2_0.8b|39.724|65.754|46.679|108|
|Sapiens2_1b|41.441|66.022|48.693|111|

ทุกระบบมี46GTpartsที่detectorจับคู่ไม่ได้และได้0เหมือนกัน;ยังคงอยู่ในprimary ไม่ลบทิ้ง. Detector-presentcolumnแสดงเพื่อวิเคราะห์เท่านั้น ไม่ใช้แทนคะแนนหลัก. ZeroTPรวมทั้งdetectorพลาดและsemanticไม่มีcorrectpixels ไม่ใช่executionfailure. Targetเล็กมีน้ำหนักเท่ากับtargetใหญ่ในmean-part;ข้อมูลarea-binอยู่CSVและเลือกbinsจากGTpixelarea ไม่ใช่modelscore.

การเฉลี่ยแบบpooledทำให้ภาพรวมอยู่ประมาณ65–66%ในtaskนี้ แต่ **ไม่เปลี่ยนprimaryเพื่อให้Sapiensดูดีขึ้น** และไม่เรียกตัวเลขนี้ว่าofficial/globalmIoU. [Summary90](../metrics/SAPIENS_SAVED_REVIEW_SUMMARY.csv) / [sizebins](../metrics/SAPIENS_SAVED_REVIEW_GT_SIZE_BINS.csv).

## 3. แยกnativeผิดจากYOLOตัดส่วนที่ทายถูก

บนGTpositivepixelsเท่านั้น: `FN = native-wrong-on-GT + native-correct-lost-to-detector-miss + native-correct-lost-to-matched-mask-clipping`. เป็นการแจกแจงsavedpredictionอย่างตรวจสอบได้ ไม่ใช่การพิสูจน์causalerrorของarchitectureหรือGT.

|Model|GT target|Native-positive recallก่อนownership%|Recallหลังownership%|Nativeผิด pixels|Correctแต่detectorพลาด|Correctแต่ถูกmatchedmaskตัด|
|---|---|---:|---:|---:|---:|---:|
|Sapiens2_0.4b|Face|86.681|85.673|7198|305|240|
|Sapiens2_0.4b|Hair|91.574|88.184|20809|4973|3400|
|Sapiens2_0.4b|Upper|88.670|84.405|98515|16440|20646|
|Sapiens2_0.4b|Lower|69.652|64.620|107292|10552|7238|
|Sapiens2_0.8b|Face|83.669|82.721|8826|482|30|
|Sapiens2_0.8b|Hair|88.721|85.600|27857|4897|2811|
|Sapiens2_0.8b|Upper|80.234|77.456|171870|7142|17021|
|Sapiens2_0.8b|Lower|70.369|65.759|104759|8460|7837|
|Sapiens2_1b|Face|80.225|78.480|10687|656|287|
|Sapiens2_1b|Hair|84.260|82.471|38873|1961|2457|
|Sapiens2_1b|Upper|77.438|74.554|196185|8421|16655|
|Sapiens2_1b|Lower|73.108|66.056|95075|16238|8693|

YOLOclippingมีผลจริง แต่ไม่อธิบายnativewrongทั้งหมด. ก่อนownershipยังทายHairถูกบนGTpixelsประมาณ84–92%และUpperประมาณ77–89%ในpixelweightedview;การประกาศว่าโมเดลทำนายผิดทุกบริเวณจึงไม่ตรงข้อมูล. Lowerยังมีsemanticconfusion/Backgroundมาก. Nativeclasscountsต่อGTtargetอยู่[CSV](../metrics/SAPIENS_SAVED_REVIEW_NATIVE_GT_DISAGREEMENT.csv);ไม่ใช้ตารางนี้เลือกremappingให้ตรงGT.

ไม่คำนวณfull-frameprecision/IoUก่อนownership เพราะnativeframeมีคนอื่นที่ไม่ได้annotate;จะนับFPของคนเหล่านั้นอย่างไม่ถูกต้อง. ตารางก่อนownershipจึงเป็นGT-positivecoverageเท่านั้น.

GT-onlytheoreticalceilingภายใต้YOLOextentที่ตรึงไว้ (สมมติรู้GTแล้วทายเฉพาะG∩extent จึงไม่ใช่deployableprediction) มีmean4ประมาณ82.517%. ใช้แสดงขอบเขตของextentconstraint ไม่สร้างprediction/แก้คะแนนหรือใช้เป็นnormalizationใหม่.

## 4. Fresh inference — same6images/31parts, sharedROIconfiguration

Freshทุกขนาดใช้checkpoint/configของตนเอง strictload,FP32/batch1/eval/noAMP/TF32/extraTTA. FrozenYOLOpredictedbox+10%contextและextentเดิม→letterbox1024H×768W→officialnormalizerครั้งเดียว→logitsstrip-padding/map-backก่อนargmax→original-gridYOLOownership. ไม่มีGTช่วยcrop/inference.

|Size|Acceptedfull-frame IoU4% บน6ภาพเดียวกัน|FreshROI IoU4%|ส่วนต่าง pp|FreshROI Dice4%|
|---|---:|---:|---:|---:|
|Sapiens2_0.4b|37.447|59.575|+22.128|67.660|
|Sapiens2_0.8b|32.492|56.057|+23.565|62.896|
|Sapiens2_1b|21.906|67.372|+45.466|76.387|

|Size|Face IoU%|Hair IoU%|Upper IoU%|Lower IoU%|
|---|---:|---:|---:|---:|
|Sapiens2_0.4b|45.177|60.521|68.637|63.964|
|Sapiens2_0.8b|44.926|57.655|66.534|55.114|
|Sapiens2_1b|63.738|70.467|69.975|65.307|

ตัวอย่างมีFaceเพียง3parts/Hair8/Upper10/Lower10,3day/3night. ใช้6ภาพเดิมจากfrozeninputdiagnostic ไม่เลือกใหม่จากคะแนน;phaseนี้เกิดหลังเห็นdiagnostic0.4Bแล้ว จึงเป็นexploratoryretest ไม่ใช่independentconfirmation/preregistration.

Freshfull-framecontrolของแต่ละขนาดเทียบกับsavednative29maskบนภาพcontrolเดิมก่อนROI. Guardpixel-disagreement≤0.0001ตั้งก่อนรันเพื่อจับreproductiondrift ไม่ใช่qualitythreshold. ผลจริง:

|Model|Control native-grid disagreement fraction|Modelcalls|
|---|---:|---:|
|Sapiens2_0.4b|0|17|
|Sapiens2_0.8b|0|17|
|Sapiens2_1b|0|17|

0.4BfreshROIเทียบ6packetsจากdiagnosticก่อนหน้า: changedownedpixelsรวม 0 / 173424. ไม่เลือกpredictionจากรอบที่คะแนนดีกว่า;รายงานรอบfreshที่freezeไว้นี้. Nativehardmaskcontrolไม่ใช่raw-logitbitwiseequivalence;ข้อจำกัดrawlogitgateของattemptก่อนหน้ายังเก็บครบ.

## 5. การclipและtaxonomyยังมีผลอย่างไร

เก็บnativeROIunownedmaskและownedmaskแยกกัน. ตารางนี้แสดงclippingcost/benefitของfreshoutputsโดยไม่ต้องinferenceเพิ่ม:

|Model|Correctpixelsที่clipออก|Falsepositivepixelsที่clipออก|MeanROI IoU4ก่อนclip% (diagnostic)|Primaryหลังclip%|
|---|---:|---:|---:|---:|
|Sapiens2_0.4b|1953|9755|57.007|59.575|
|Sapiens2_0.8b|2788|10522|55.515|56.057|
|Sapiens2_1b|2495|4255|66.443|67.372|

ก่อนclipคำนวณเฉพาะROIของคนที่จับคู่แล้ว ไม่ใช่full-frameunownedsemantics. เป็นpostprocessingdiagnostic ไม่ได้สลับมาใช้แทนprimaryหรือเลือกownershipตามGTscore. ClassmappingเดิมยังคงFace_Neck+facialsubpartsเป็นFaceproxy,Hair4,Upper23,Lower13;Apparel/ส่วนอื่นOTHER. Nativeถูกตามtaxonomyของตัวเองอาจยังไม่ตรงreference. ไม่splitDress/neck/แต่งGTด้วยheuristic.

GTชุดนี้เลือกบางคน/บางส่วนและผ่านagentassistedscreen ไม่ใช่expertgoldcertification. เป้าหมายที่ทำนายถูกนอกcontourที่ยังไม่สมบูรณ์อาจถูกนับFP;ภาพ/GTboundaryจึงต้องอ่านควบคู่ ไม่ใช้คะแนนนี้รับรองfullsceneหรือdeployment.

## 6. ภาพและสิ่งที่ตรวจจริง

Private comparison gallery: `CCTV_Human_Parsing_Benchmark/outputs/sapiens-roi-remeasurement-20261101T025855Z/gallery/` มีsample_01.png…sample_06.png. แต่ละภาพมี3rowsของ0.4/0.8/1B;columns=RGB/GT/fullframeเดิม/freshROIหลังclip/freshROIก่อนclip. เลือกpersonที่มีprimarytargetsมากสุดและstableIDtieตามกติกาเดิม ไม่เลือกpersonจากคะแนน. DisplayGTcropใช้แสดงภาพเท่านั้น ไม่ใช่input.

ตรวจall18freshatomicpackets/NPZhash/readback/originalgeometry/native29IDs/extent+scoreidentity;independentcoordinate-setTP/FP/FNบน3realpacketsตรง,per-targetaggregation/31partmembership/51callledgerตรง. OriginalGT/sourceconfig/frozeninference/scorerและคะแนนเก่าไม่ถูกแก้. Scientificsourcecodeที่reuseยังตรงhash;ฉบับpublicเก็บเฉพาะcode/config/aggregateCSV/report ไม่มีCCTVimages/filenames/annotations/personrecords.

[FreshcomparisonCSV](../metrics/SAPIENS_FRESH_ROI_COMPARISON.csv) / [freshtargets](../metrics/SAPIENS_FRESH_ROI_PER_TARGET.csv) / [savedtargetdecomposition](../metrics/SAPIENS_SAVED_REVIEW_PER_TARGET.csv) / [protocol](../configs/SAPIENS_MEASUREMENT_REVIEW.json) / [evidence](SAPIENS2_MEASUREMENT_REVIEW_EVIDENCE.json). ค่าnumericCSVเป็นfraction0–1หรือpixelcountsตามชื่อ;nullไม่ใช่0. RawGT/packets/logs/ledgers/environmentอยู่privateoutputs;publiccloneอย่างเดียวทำซ้ำGPUงานนี้ไม่ได้.

## 7. สรุปการใช้งานผล

สถานะการเลือกจาก90ภาพ: **GT_OWNER_REVIEW_REQUIRED**. การคำนวณตรงกันไม่เท่ากับGTถูกต้อง;คำแนะนำQANetจากตารางก่อนหน้ายังเป็นhistoricalresultภายใต้labelsเดิม และพักการใช้เป็นfinalselection.

คะแนนเดิมมีความหมายตามaggregationและpipelineที่รัน แต่ไม่ใช่ข้อพิสูจน์ศักยภาพสูงสุดของSapiens. การวัดใหม่ต้องรายงานผลfreshROIตามตารางจริง พร้อมข้อจำกัดinput/GT/ownershipและชุดตัวอย่างเล็ก ไม่คาดหวังให้โมเดลใหญ่ชนะเสมอหรือเลือกremappingเพื่อช่วยคะแนน.

ต้องปิดGTowner/contourQAและderivedbindingsก่อน. หากจะเปรียบเทียบเพื่อเลือกconfigurationบนCCTV90ต่อ ให้freezeROIconfigurationและทำรอบ90ภาพแยกตามขอบเขตที่ผู้ใช้อนุมัติ;ไม่เอา6ภาพมาแทน90หรือปนกับnativeCIHP5,000. ไม่มีfullbenchmark/โมเดลอื่น/training/colorเริ่มต่ออัตโนมัติ.
