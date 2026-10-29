# ผล implementation และ pilot CIHP–Sapiens2 0.4B common view

**PILOT_PASS — ตรวจปิดแล้ว 6/6 diagnostic IDs, warmup1, รวม7 model-frame calls** · Updated **2026-10-29T08:45:10.351455+07:00 (เวลาไทย UTC+07)**

ผลนี้เป็น **engineering/quality diagnostics ของหกภาพที่เลือกตามcoverage ไม่ใช่คะแนนbenchmark5,000ภาพ ไม่ใช่modelrankingหรือabsolutequalitypass** Full-population primaryยัง **null / NOT_A_5000_ID_COMMON_VIEW_RUN** คิวหยุดแล้ว ไม่มี0.8B/1B/CPI/YOLOinferenceใหม่/training/color/CCTV

## 1. ขอบเขตและตัวตนการทดลอง

- Protocol `CIHP_SAPIENS_C4P / revision-2-pilot`, [ข้อกำหนด](CIHP_SAPIENS_COMMON_VIEW_PROTOCOL_TH.md), [specification](../protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json), [pilot config](../configs/cihp_sapiens_04b_pilot.json)
- Model **Sapiens2_0.4b segmentation**, source`7e5bae88456ac418ff0e58e74106c9fe192055d4`,406,601,693parameters; native29labels/semantichead29. Source/configและcheckpointแยกจากtask/ขนาดอื่น; strictstate-dictloadPASS
- Checkpoint `models/human_parsing/sapiens2/0.4b/sapiens2_0.4b_seg.safetensors`, SHA256 **b85fdb50b7d6123a967d5ee4a505e222baff8d2f7ad6bbf353578c1a61dfbac9** ตรงlocalregistryและตรวจไฟล์จริง ไม่อ้างว่าlocaldigestรับรองcreatorauthenticityโดยไม่มีต้นทางdigest
- Actual environmentเดิม `.venvs/sapiens2-pilot`: Python3.12.3,PyTorch2.14.0+cu130,CUDA runtime13.0,NumPy2.5.4,SciPy1.18.1,Pillow12.3.0/OpenCV5.0.0.93. ไม่install/เปลี่ยนenvironment/allocator/ระบบGPU
- Current segment **`common-c4p-pilot-20261029T010410394659Z-binary-cache-fix`**; launch commit **`a7683da4b4ad5bfe4a248aba168d74a1cdc24391`** บันทึกก่อนmodelcalls ผลส่งมอบหลังrunเป็นอีกdocumentationcommit ไม่อ้างแทนlaunchrevision
- Parent **`common-c4p-pilot-20261029T010410394659Z`** เป็นpre-forwardsetupattemptที่เก็บไว้ครบ ไม่ปะปนกับnativeCIHPsix/CPIhistoricalexperiments

Native QANet/M2FP/D2FP/RP-R-CNN ยังคง COMPLETE5,000each/[ผลเดิม](CIHP_FOUR_MODEL_RESULTS_TH.md);สองCPIยังพักพร้อม3/113successfulIDs/OOMhistory/mainnull ไม่ inferenceหรือแก้ผลเดิม Native masks/configs/worker/scorerและcompactmetrics18protectedfilehashesคงเดิม

## 2. สองประเด็นที่แก้ก่อนเห็น pilot scores

### Matching ties / ID renaming

SyntheticcounterexampleจริงมีGT2คนที่คนละpixel,predictionextents2ชุดครอบทั้ง2pixels ทุกmaskIoU=.5 มีสองassignment cardinality2/sumIoU1เท่ากัน แต่semanticQของassignmentเป็น1หรือ0

|กติกาที่ตรวจจริงบนCPU|ก่อนเปลี่ยนชื่อGTIDs|หลังสลับชื่อGTIDs|ข้อสรุป|
|---|---|---|---|
|Nativelegacy/SciPyinputorderตามnumericGTIDs|1|0|ใช้IDorderตัดtieแล้วQไม่invariant;ผลnativeเดิมไม่ถูกแก้หรือrescore|
|Commonrevision2 geometrycanonical|1|1|GTgeometryต่างกันทำให้orderingไม่ขึ้นกับเลขID;ไม่ใช้semanticqualityเลือกคู่|

Commonmatcherเรียงgeometryด้วยbbox(y0,x0,y1,x1),area,sumY,sumXและpackedbooleanmaskbytes แล้วmaximizeeligiblecardinalityก่อนsumIoU และเลือกlexicographicallyfirstcanonicaloptimumภายใน1e-12 (thresholdinclusive≥.50/.75) หากgeometryGTเหมือนกันจริงใช้stableIDfallback;predgeometryเหมือนกันใช้packetindex รายงานalternativeoptimum/identicalgeometrygroupsและจำกัดinvarianceตามจริง **ไม่อ้างว่าgeometryแก้physicalambiguityทุกกรณี** และไม่รับรองpredictionpermutationinvarianceเมื่อgeometryเหมือนกัน Pilotนี้ambiguousmatchingframes0ทั้งสองthreshold แต่counterexamplefixtureพิสูจน์pathที่มีambiguity

### C3 sensitivity

C3เป็น **global mean Hair/Upper/LowerจากconfusionเดียวกับC4** เท่านั้น Faceยังvalidnon-targetสำหรับC3 ดังนั้นHair/Upper/LowerpredictionบนGTFaceยังเป็นFP ไม่มีQ_C3หรือpersondenominatorชุดC3 Personmetricsใช้C4ตามเดิม

Mapping/Faceproxy/garmentunions/OTHERpolicyไม่เปลี่ยนหลังpilot: CIHP13↔Sapiens3+24–28เป็นFaceproxy,Hair2↔4,UpperCIHP5+7↔S23,Lower9+12↔S13;Dress6/Apparel1→OTHERvalid ไม่ignore ไม่ตัดคอ/แบ่งDressด้วยheuristic ไม่มีGTช่วยprediction

งานนี้เป็นpost-resultsdevelopment/evaluation: เห็นnativefourresultsก่อนทำproposal และแก้ข้อกำหนดตามผู้ใช้ก่อนpilot ไม่เรียกpreregistered/confirmatoryprotocol และไม่เลือกmapping/thresholdจากคะแนนpilot

## 3. Implementation และ CPU acceptance ที่ทำจริง

แยก `src/common_view/` (projection,geometrymatcher,person/globalscorer,atomicpackets/reporter,detectorcacheadapter,Sapiensroute) และ scripts/config/outputจาก frozen native implementation ไม่แก้nativeexecution/scientificsource

**23independentexpected-valuecases PASS** ผ่านactualtiny packet→scorer→reporter ไม่ได้generateexpectedvaluesจากfunctionunder-test ครอบคลุม:

- mappingครบCIHP0–19/Sapiens0–28ตามliteralexpected49IDs,GT255sharedvoid/pred255/unknown/negativeIDscontractfailure
- unionจากconfusion/pixels (native5↔7ผิดทั้งหมดแต่mergedUpperIoU1),OTHERFP/FN,high-scoreOTHERชนะoverlapโดยไม่ลบทิ้งก่อนproject
- perfect/wrongclass,semantic-emptyextentยังTPแต่Q0,no-personเป็นmiss,duplicateTP1FP1/F1=2/3,mergedpeople/globalIoU1แต่Q1/4/contamination1/2ตามfixture
- sharedVOID/ownerunknown/global-persondomainแตกต่าง,denominator0→JSONnull,missing/duplicatepopulationmainnull
- tiecounterexample/IDrename/identicalgeometryfallback,cache/protocol/modelbindingmismatch,orphan/tamperedNPZ/immutability
- actualpinnedCPUpreprocessorผ่านasymmetricRGBcorners/normalization/1024×768stretch/logitsbilinear-mapback-beforeargmax→originalgrid→serializedpacket/scorer/reporter
- losslessbinarycachefixtureและ **actualfrozenYOLO7caches** (warmup+sixVAL) ตรวจhash/shape/binary0–1/footprintก่อนforward

Read-onlysavedpacketintegrationสี่ระบบ×1ภาพ0021448ผ่าน model/checkpoint/source/input/config/NPZbindingsและcommonreporter ไม่มีinferenceใหม่หรือfullaudit [CPUacceptance](../runs/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/CPU_ACCEPTANCE.json),source/testsในGit ใช้existingexternalassetsจึงไม่อ้างว่าcleanpubliccloneอย่างเดียวรันGPU/ทุกintegrationได้

## 4. GT-only domains และ denominators

สร้างderivedGTsidecarsแบบstreamingต่อภาพจากnativeCIHPsource ไม่มีแก้sourcebytes ไม่มีmodelpredictionsเข้าeligibility ตรึงCategory0–19validรวมBG/OTHER,GT255VOIDเท่ากันทุกโมเดล;persondomainตัดCategorypositive/Human0เฉพาะownershipsemantics ไม่สร้างmodel-specificignore

|ประชากร/binding|ผลจริง|
|---|---:|
|NativeCIHPVALGT-onlybindings|5,000uniqueIDs|
|G_locทั้ง5,000|17,520|
|**G_sem_C4ทั้ง5,000**|**17,454**|
|Ownerunknown / sourceVOIDpixels|0 / 0|
|GTpersonsในsixpilot / eligibleC4|23 / 23|
|C3persondenominator|N/A — ไม่มีนิยามเพิ่ม|

G_sem_C4ต่ำกว่าG_loc66คนตามGTtargetsupport จึงไม่hardcode17,520แทนsemanticdenominator การmaterializeGT5,000นี้ **ไม่ใช่การscorepredictions5,000หรือเผยแพร่fullbenchmark** [GTsummary](../runs/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/GT_BINDING_SUMMARY.json) ผูกmanifestSHA256 `1a6f635ffdd0da1b767a6d7279e0437130bdfdd47e510fbfdaeb9b047cc82cc0`. Newsegmentreusebindingsจากparentเพราะmapping/domainไม่เปลี่ยน ไม่decode/hashGTทั้งชุดซ้ำหลังแก้cache reader

## 5. Readiness, route และ shared GPU

Route **SAPIENS_FRAME_YOLO_MASK_OWNERSHIP**: exactCIHPJPEG/RGBfullframe→officialBGRinput/preprocessorbgr_to_rgb→ImageNetmean/std→nativeSegResizeH1024W768stretch/noextraPad→FP32modelbatch1eval/inference,noAMP/TF32/extraTTA→bilinearlogitsกลับoriginalH,W(align_corners=False)→native29argmax→clipด้วยfrozenYOLOmasks→nativeforegroundcomposeตามYOLOscores/packetindex→projectC4

YOLOใช้cacheเดิม imgsz640/conf.25/iou.7/max_det200/retina_masksTrue ไม่โหลดหรือรันYOLOใหม่ Identity/extentsมาจากYOLO ไม่ใช่nativeSapiensinstancecapability;confidenceที่เก็บคือYOLOdetectorconfidence ไม่ใช่semanticpixelprobability Nativefullframe29hardmaskเก็บครบเป็นreference;ไม่มีfull-logitrequirementหรือprobabilityevaluationclaim

ใช้ **SHARED_GPU_QUALITY_ONLY** ที่ผู้ใช้อนุมัติตรงสำหรับpilotนี้ ExternalPIDถูกบันทึกแต่ไม่เป็นblocker ไม่ปิดprocessอื่น และไม่เปลี่ยนGPU/system config ReadinessfreeVRAMประมาณ13070.8MiB;strictload/warmup/actualsixforwardsผ่าน

|ทรัพยากรที่สังเกตจริง|ค่า/ขอบเขต|
|---|---|
|GPU|Tesla T4/sharedGPU|
|PeakPyTorchallocatedระหว่าง7calls|2157.238MiB|
|PeakPyTorchreservedระหว่าง7calls|2606.000MiB|
|Guards|24hนับจากparentstart,80GiBรวมsegments/sharedGTretained,free50GiB;noOOM/modelretry/fallback|
|Retainedparent+currentตอนตรวจปิด|ประมาณ37.3MiB รวมderivedGTsidecars;ไม่ใช่full5,000predictionstorageestimate|

Allocated/reservedเป็นmeasurementของprocessนี้ ไม่ใช่peakdeviceusageรวมทุกprocess ไม่ใช้จัดอันดับVRAMefficiency. Timefieldในledgerคือ synchronizedmodel-forward+logitmapback/argmax/D2H ไม่รวมsourceI/O/decode/preprocessing/H2D/YOLOfreshinference/checkpointload/export/scorer จึง **ไม่ใช่cleanparser-onlyหรือend-to-endFPSranking** ไม่มีFPSrankingในรายงานนี้

## 6. ประวัติ setup failure และงบ model calls

|Attempt/segment|เวลาไทยเริ่ม→จบ|Modelcalls|ผล|
|---|---|---:|---|
|Parentinitialsetup|2026-10-29T08:23:17.916957+07:00 → 2026-10-29T08:24:12.970231+07:00|0|strictloadPASSแล้วSOURCE_BINDINGSINVALIDจากreaderassertbool แต่frozencacheเป็นuint8binary0/1;VAL0,noOOM|
|Freshbinary-cache-fixsegment|2026-10-29T08:32:43.228875+07:00 → 2026-10-29T08:33:54.164968+07:00|7|warmup1+VAL6 PASS;failed0/invalid0/notattempted0|
|รวมactualsegmentationforwards|—|**7/7**|แต่ละภาพมี1forwardattempt ไม่มีOOM/modelretry|

นี่เป็นimplementationbugที่ยอมรับและเก็บหลักฐานก่อนแก้: `normalize_detector_masks` ตรวจshape/ค่า0–1ก่อนlosslessastypebool และตรวจroundtripไม่เปลี่ยนbinaryfootprint ไม่มีthreshold/resizeหรือเปลี่ยนownership Sourcecacheไม่ถูกเขียนทับ เก็บparentRUN/EXECUTION/FAILURE/rawlog/commit`a514f3b`ไว้ และบันทึกcorrection+retestscopeก่อนlaunchใหม่ [Setupcorrection](../runs/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/SETUP_CORRECTION.json)

Parentก่อนforward0callsจึงไม่มีwarmup/VALpredictionให้retryหรือเลือกผลscoreดีกว่า Newsegmentมีinputsettings/mapping/scoringเดิม ยังคงbudgetรวม7calls/time/storageเดิม **ไม่ใช้คำว่าrecoveryเพื่อเพิ่มbudgetโดยเงียบ ๆ** DetachedworkerPID/session222281เริ่มจากcommit`a7683da`,stdin/dev/null/logfileแยก;exitแล้วหลังปิดรอบ ไม่ต้องเปิดcontrollerต่อ

## 7. Completion และคะแนน diagnostic ของหกภาพเท่านั้น

|IDตามลำดับที่กำหนด|GTpersons|GTeligibleC4|PredictedpersonsจากYOLO|Packet/readback/labels/geometry|QANetextentparity|
|---|---:|---:|---:|---|---|
|0021448|5|5|5|PASS|PASS|
|0006909|8|8|10|PASS|PASS|
|0001538|2|2|2|PASS|PASS|
|0001413|4|4|4|PASS|PASS|
|0027897|2|2|2|PASS|PASS|
|0031248|2|2|2|PASS|PASS|

Membership6uniqueIDsตรงmanifest,no missing/duplicate/VALfailed/invalid;warmup0000930ไม่อยู่ในscores. Full5,000commonprimaryยังnull **ไม่เทียบคะแนนชุดนี้กับnative20resultsของสี่โมเดลบน5,000**

Diagnosticglobalvalidpixels1,571,800;สะสมconfusionทั้ง6ภาพก่อนIoU ไม่เฉลี่ยIoUรายภาพ/nativeclass IoUs

|Target|GTpixels|Predpixels|Unionpixels|IoU(%)|
|---|---:|---:|---:|---:|
|1 Face ตาม CIHP reference / approximate Face_Neck proxy|52,314|70,419|74,510|64.720|
|2 Hair|75,513|69,055|78,990|83.021|
|3 Upper non-Dress family|162,564|174,296|201,080|67.525|
|4 Lower non-Dress family|59,674|47,706|62,521|71.750|

- **C4-P mIoU4 diagnostic = 71.754%** (ไม่รวมBG/OTHERในmeanแต่ยังเป็นvalidnegatives)
- **C3 global sensitivity = 74.099%**;ไม่มีpersonmetricC3และFaceยังไม่ถูกvoid

|GTmaskIoUthreshold|G_loc|G_sem_C4|TP / FP / FN|Precision(%)|Recall(%)|ExtentF1(%)|Q_C4_GT(%)|
|---|---:|---:|---|---:|---:|---:|---:|
|0.5|23|23|23 / 2 / 0|92.000|100.000|95.833|46.674|
|0.75|23|23|19 / 6 / 4|76.000|82.609|79.167|36.765|

Qคือsumper-GTpersonactive-targetIoU/G_sem_C4;missedeligibleGTให้0 Unmatchedpredไม่ถูกลงโทษโดยตรงในQ จึงต้องอ่านFP/F1ร่วมกัน ExtentmetricsของSapiens **เท่ากับQANetบนภาพเดียวกันทั้ง.50/.75** ตามcachedextentsเดียวกันอย่างที่คาด ไม่ใช้เป็นหลักฐานว่าSapiensมีnativeinstanceaccuracyสูงเท่ากัน

Matched-onlytargetcontaminationที่.50 =3,111/361,696pixels (0.860%) ไม่ครอบคลุมunmatchedpredictions;ไม่นำค่าต่ำไปอ้างownershipทั้งระบบ Backgroundleakageยังเก็บnumerator/denominatorแยกในcanonicaldiagnostics [Exactpilotmetrics](../runs/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/METRICS_DIAGNOSTICS.json),[extentparity](../runs/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/EXTENT_PARITY.json)

## 8. Artifact verification และ visual review

ตรวจ6NPZ/atomicCOMMIT/memberSHA/readbackทุกfield: native29integeroriginalgrid,perpersonnativeplanes,extents/YOLOscores/IDs/bboxes,input/model/config/source/env/protocol/detectorhashes;sourceGT/deriveddomainhashes/eligiblecounts;nativecliprelationเท่ากับwhere(cachedYOLOextent,native29,0)ทุกpixel Originalnativefiles/18protectedhashesและlaunchcommon-sourcehashesไม่เปลี่ยน

Workerrescoreจากsavedmasksเทียบexportedscoreทั้งสองthresholdPASS,aggregatehist/6-IDmembership/JSONnullPASS. [Artifactreceipt](../runs/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/ARTIFACT_VERIFICATION.json) แยกจากCPUexpectedvalueproof ไม่รับรองevaluatorจากจำนวนtestsอย่างเดียว

เปิดดู **ทั้ง6ภาพที่กำหนด** (AIinspection,ไม่ใช่independenthumanannotationQA) ไม่มีsystematicrotation/flip/shift/channel-swapที่สังเกตจากภาพ;CPUasymmetricfixtureและgeometryhashesสนับสนุนcontractแยกจากความเห็นภาพ ไม่อ้างboundaryทุกpixelถูกต้อง

|ภาพ|สิ่งที่เห็น/ข้อจำกัด|
|---|---|
|0021448|ตำแหน่งคน/ธงและขอบภาพตรงพิกัดเดิม มีความต่างที่คอ เหรียญและขอบเสื้อผ้า ไม่พบsystematicflip/shiftจากภาพนี้|
|0006909|ฉากคนซ้อน: GTDressส่วนใหญ่ถูกเรียกUpper_Clothingในnativeprediction จึงเป็นUpperFPบนOTHERตามpolicy ไม่ใช้การแบ่งเดรสแก้คะแนน|
|0001538|Face/Hairวางตำแหน่งตรงภาพ แต่Face_Neckproxyลงไปบางบริเวณใต้คางที่GTเป็นTorso-skin ต้องแยกdefinitiondiscordanceออกจากข้อสรุปว่าnativeทำนายผิดทุกpixel|
|0001413|GTไม่มีHair แต่มีบางHairpredictionบนGTHat;ยังนับFPตามdomain ไม่voidภาพ ขอบชุดดับเพลิงและอุปกรณ์มีdisagreement|
|0027897|ภาพแนวนอนกว้างrestoreกลับสัดส่วนเดิมถูกต้อง;ผม/เครื่องประดับศีรษะและDress/Upperlabelsต่างกัน ไม่ใช่หลักฐานmappingเท่ากันทุกบริเวณ|
|0031248|ภาพแนวตั้งแต่งงาน: DressGTส่วนใหญ่ทำนายApparel→OTHER;ขอบผ้าคลุม/ชุดและskinpartitionต่างกัน ตัวอย่างนี้ไม่พิสูจน์Apparel=Dressทั้งtaxonomy|

ตัวอย่างdiscordanceจากsavednative-ID application composition:0001538มีGTTorso-skin→SapiensFace_Neck17,486pixels;0006909มีGTDress→Upper_Clothing12,598จากDress12,870pixels;0031248มีGTDress→Apparel58,409จากDress59,397pixels เป็นlabeldisagreementที่ต้องตีความตามsource/reference ไม่ใช่proofว่าtaxonomyเป็นสาเหตุเพียงอย่างเดียวของทุกpixel และไม่เปลี่ยนmapping/ignore/thresholdเพื่อเพิ่มscore. [Qualitativereview/counts](../runs/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/QUALITATIVE_REVIEW.json)

## 9. เปิดดูภาพ/เข้าถึง artifacts

Privategalleryอยู่workspace-relative:

`Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/common_view/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/gallery/index.html`

จากworkspace rootเปิดstaticserverด้วยคำสั่งต่อไป แล้วforwardport8766และเปิด `http://127.0.0.1:8766/index.html` (คำสั่งนี้เป็นviewerเท่านั้น ไม่รันmodel;ในรอบนี้ไม่ได้เปิดpersistentwebserverไว้):

```bash
python3 -m http.server 8766 --bind 127.0.0.1 --directory Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/common_view/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/gallery
```

แต่ละภาพมีRGB/GTcommon/applicationcommon/native29fullframe/GTowners/YOLOownersบนoriginalgrid PNGเต็ม;JPEGpreviewย่อเพื่อแสดงผลเท่านั้น Common/native29คนละlegend และlocalpersoncolorsไม่ใช่IDที่matchกันข้ามpanel ภาพและnativeNPZ/rawlogs/derivedGT/envsnapshotเก็บprivate/externalGit ไม่publishdatasetimages/CCTV/weights

Rawstatus/log: `Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z/common_view/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/RUN.json`, `EXECUTION.jsonl`, `worker.log`;model/env/sourcehashesและdetachedsessionใน[processrecord](../runs/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/PROCESS.json)/[readiness](../runs/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/READINESS.json). Clonepublicrepoอย่างเดียวไม่มีdatasets/checkpoint/GTcache/native4packets/pinnedthirdpartyenvironment จึงreproduceGPUpilotไม่ได้ทันที

## 10. พร้อมเสนอ full evaluation หรือยัง

**พร้อมเสนอขอบเขต full-quality evaluation ของ Sapiens2_0.4b และ common rescoring ของsavedfour systems ได้แล้ว**: definitions/ties/C3ปิดตามrevision2,CPUoracle+savedpacketintegrationผ่าน,GT-only5,000bindingsพร้อม,realGPUrouteผ่าน6/6ภายใต้settings/sharedpolicyเดิม และsavedmask/ownershipparityตรวจผ่าน ไม่ต้องกลับไปรื้อtaxonomyทั้งโครงการหรือinferสี่ระบบใหม่

แต่ **ยังไม่อนุมัติ/ไม่เปิดfull5,000 และไม่ถือว่าfull-run launchconfig/controllerผ่านแล้ว** entrypointปัจจุบันhardlimitpilot6/7callsและreporterล็อกfullprimarynullโดยตั้งใจ ขั้นถัดไปคือจัดacceptedfull-runmanifest/config/streamingcontroller+failure/completenessreportingที่ผูกsource revisionจริง,ระบุpilotartifactreusepolicyจากfingerprintsอย่างชัดเจน (ไม่เลือกpacketตามscore),aggregateartifactbudget/headroomแล้วขอ/รับคำสั่งfullbatchแยก ไม่ใช้การผ่านpilotเป็นexecutionapproval

Existingmetadataสำหรับเสนอทรัพยากร:5,000frames/24,062cachedYOLOopportunities;predictionarraysแบบไม่บีบอัดประมาณ8.673GiBจาก(2N+1)×H×W+score/boxarrays—not totaldiskreserve. ขนาดpacketมากสุดตามmetadataประมาณ17.24MBที่0013072(890×668,N14);ยังไม่รวมmetadata/logs/sharedGT/temppeak/headroom/การบีบอัดและactivationpeak. Compressedtotalstorage/ETAยังไม่รับรอง และไม่ทำinferenceเพิ่มเพื่อตรวจภาพนี้ในรอบนี้ [Metadataestimate](../runs/common-c4p-pilot-20261029T010410394659Z-binary-cache-fix/FULL_WORKLOAD_METADATA_ESTIMATE.json)

ข้อจำกัดที่ยังคงอยู่:6purposiveVALimagesไม่แทนpopulationquality/generalranking;Faceproxyไม่ให้strictface-only/neckseparation;Dress/Apparelไม่ทำให้upper/lowerDresscovered;route/input/trainingexposureต่างจากnativefour;ไม่มีcleanlatency/VRAMefficiencyrankingหรือCCTV/colorconfirmation. 0.8B/1Bยังต้องมีscopedreadiness/approvalของตน ไม่extrapolateจาก0.4Bหรือweightsize

**หยุดหลังปิดpilotนี้** งบ7callsใช้ครบแล้ว ไม่restartจากconfig/permissionเก่า สองCPIพักและnativefourresultsคงเดิม
