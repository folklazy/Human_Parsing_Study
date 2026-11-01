# ทดสอบ input Sapiens2 0.4B บน CCTV — diagnostic 6 ภาพ

ตรวจปิด 2026-11-01T09:34:27.498729+07:00 (Asia/Bangkok). **ครบ6ภาพ ×3input configurations**, source baseline6packets reuse; learnedforwardรวม25callsจาก2attempts/processes ภายในเพดาน29ที่ประกาศ. จบแล้ว ไม่มีworker/การรันต่อไปยังโมเดลอื่น.

**ผลที่พบ:** person cropจาก frozen YOLO +letterbox ให้ mean selected-part IoU4 **59.575%** เทียบ full-frame stretchเดิม **37.447%**, เพิ่ม **22.128 percentage points** ในตัวอย่างชุดเดียวกัน. ส่วน full-frameletterboxได้ **29.913%**, ลด **7.534 points**. จึงมีหลักฐานว่าinputconfigurationมีผลจริง แต่การรักษาสัดส่วนทั้งภาพเพียงอย่างเดียวไม่ได้แก้ปัญหา; personscale/crop/contextมีบทบาทร่วม. ยังแยกสาเหตุแต่ละองค์ประกอบหรือรับรองผลทั้ง90ภาพไม่ได้.

## 1. สิ่งที่ควบคุมและสิ่งที่เปลี่ยน

|คงเดิมทุกconfiguration|รายละเอียด|
|---|---|
|Model|Sapiens2 segmentation0.4B/checkpoint/config/source revisionเดียวกัน;406,601,693parameters;ไม่โหลดtask/ขนาดอื่น|
|Inference|FP32/batch1/eval/inference mode/noAMP/TF32/extraTTA;ไม่มีfallback/retry|
|Detector/ownership|frozenYOLOcacheเดิม ไม่ inferenceYOLO; person extents/scores/orderเหมือนเดิมทุกpixel/ค่า|
|GT/score|selected-part protocolเดิม, projectionFaceproxy/Hair/Upper/Lowerเดิม, matching/eligibilityเดิม|
|Domain|31primaryGTpartsใน6ภาพเดียวกัน; Face3/Hair8/Upper10/Lower10|
|Missing|detector-miss2partsยังอยู่ในตัวหารและได้0เหมือนกันทั้ง3วิธี|

|Configuration|Inputก่อนnetwork|การคืนพิกัด/ownership|
|---|---|---|
|FULL_FRAME_STRETCH|ภาพทั้งframeยืดเป็น768W×1024Hตามconfigเดิม|ใช้accepted native/personpacketsเดิมทั้งหมด มีfreshcontrol1ภาพที่ตรงsavedmaskทุกpixel|
|FULL_FRAME_LETTERBOX|ภาพทั้งframeรักษาสัดส่วน, centeredpaddingสีRGBmean→normalizedzero|crop paddingออกจากlogitsก่อนbilinearกลับoriginalgrid/argmax แล้วYOLOmaskownershipเดิม|
|YOLO_ROI_LETTERBOX|แต่ละpredictedYOLObox+context10%แต่ละด้าน;ขยายให้ครอบYOLOextentเดิม;letterboxcropเป็น768×1024|คืนlogitsกลับcropgrid→วางoriginalgrid→clipด้วยYOLOmaskเดิม;ไม่ใช้GTcrop|

ไม่เปลี่ยนmapping/threshold/ROIcontextจากคะแนน. ROIcontext10%และวิธีเลือกภาพตรึงก่อนเริ่มalternativeforwards. แต่เป็น post-hoc/exploratory diagnosticหลังเห็นผลเดิม ไม่ใช่confirmatorybenchmarkหรือpreregistration.

ตัวอย่างเลือกด้วยกติกาคงที่:2ภาพday/nightจากgalleryเดิม,ภาพday/nightที่medianpredictedpersonbboxrelativeareaเล็กที่สุด,ภาพที่มีYOLOopportunitiesมากที่สุด และภาพขนาดไม่ใช่1920×1080แรกที่เข้าเกณฑ์. Tieใช้sourceorder. รวม3day/3night,หนึ่ง1280×720และอีกห้า1920×1080. ไม่เลือกจากparserคะแนน. Selection/member/sourcehashesอยู่privateCONFIG; publicspecบันทึกหลักเกณฑ์/ขอบเขต.

## 2. ผลตัวเลข — mean selected annotated-part IoU (%)

ทุกcolumnวัด31partsชุดเดียวกัน; macroเฉลี่ยper-partภายในtargetแล้วเฉลี่ย4targetsเท่ากัน. นี่ไม่ใช่globalmIoU/officialparserAP. ไม่เอาIoUคลาสย่อยมาถัวแทนunion.

|Input configuration|Face|Hair|Upper|Lower|Macro IoU4|Macro Dice4|
|---|---:|---:|---:|---:|---:|---:|
|FULL_FRAME_STRETCH|17.924|42.655|59.164|30.046|37.447|46.279|
|FULL_FRAME_LETTERBOX|14.198|37.504|48.108|19.842|29.913|38.045|
|YOLO_ROI_LETTERBOX|45.177|60.521|68.637|63.964|59.575|67.660|

ROIletterboxสูงกว่าbaselineในค่าเฉลี่ยทั้ง4targetsของชุดนี้ แต่ไม่ได้ดีขึ้นทุกperson/ทุกส่วน. Faceมีเพียง3annotatedpartsจึงยังเป็นหลักฐานขนาดเล็ก. ตารางpooledTP/FP/FN/precision/recall/IoU และday/nightอยู่ในCSV ไม่เปลี่ยนตัวหารเมื่อทำนายไม่ได้.

## 3. ภาพที่เปิดตรวจ

สร้างและเปิดดูครบ6panels แสดงRGB,GTและpredictions3วิธีในพิกัดเดียวกัน จากsavedpacketsของรอบนี้. ต่อภาพเลือกGTpersonที่มีannotatedtargetsมากที่สุดและsourceIDtie โดยไม่ใช้คะแนน;displaycropจากGTใช้แสดงภาพเท่านั้น ไม่ใช่modelinputหรือscoringdomain.

- ในตัวอย่างdayที่full-frameเคยมีlabelsกระจัดกระจาย ROIแยกHair/Face/Upper/Lowerเป็นพื้นที่ต่อเนื่องชัดขึ้น.
- Full-frameletterboxบางภาพยังมีfragmentedlabelsหรือสูญเสียรายละเอียด;เมื่อรักษาสัดส่วนทั้งframe คนมีresolutionแนวตั้งน้อยกว่าวิธียืดเดิม. นี่เป็นข้อสังเกต/คำอธิบายที่เป็นไปได้ ไม่ใช่การแยกcausalmechanismสำเร็จแล้ว.
- มีคนที่detectorจับคู่ไม่ได้:ทั้ง3วิธีว่างเหมือนกัน ไม่ถูกนำออกจากคะแนน.
- มีตัวอย่างROIเปลี่ยนupperส่วนหนึ่งเป็นOTHERและยังผิดเทียบGT; ไม่แก้mapping/ignoreเพื่อซ่อนข้อผิดพลาดนั้น.

Private gallery: `CCTV_Human_Parsing_Benchmark/outputs/sapiens-input-variants-20261101T022856Z/gallery/` — `sample_01.png`…`sample_06.png`, พร้อมMANIFEST/provenance. Inputpreviewletterbox/ROIของ2ภาพแรกอยู่runroot. ไม่เผยแพร่CCTVimages/filenames/annotations/personrecordsบนGitHub.

## 4. Official-forward control และเหตุที่มี2attempts

Parent diagnosticใช้1TRAINwarmup+1officialforward+1wrapperforward. ActualnormalizedinputบนGPUตรงกันทุกค่า; rawlogitsมีmaxabsdelta0.000244140625 (referenceabsmax981.067, relativeL2≈3.53×10⁻⁷). มีค่าบางจุดไม่ผ่านallclose(atol=rtol=1e-5), workerจึงหยุดตามgate. **เก็บสถานะFAIL/traceback/rawlogits/runner snapshotเดิมไว้ ไม่แก้ย้อนหลังให้ผ่าน**.

Argmaxบนnetworkgridบางจุดต่างกัน แต่หลังmap-backตามscoringcontractแล้ว native29maskบนoriginalgridตรงofficialและsavedbaselineทุกpixelในภาพcontrolนี้. จึงยังไม่พบหลักฐานว่าRGB/BGR/normalizationหรือwrapperสร้างอาการfragmentedแทนofficialในตัวอย่างนี้. ไม่อ้างraw-logitequivalenceหรือpopulationwidebitwiseparity.

Floatingpoint/การเลือกGPUkernelsอาจทำให้เกิดnumericalvariationได้ตาม [PyTorch numerical accuracy](https://docs.pytorch.org/docs/2.14/notes/numerical_accuracy.html) และ [reproducibility](https://docs.pytorch.org/docs/2.14/notes/randomness.html); รันนี้ไม่ได้พิสูจน์ว่าkernelใดเป็นสาเหตุ จึงไม่ใช้เอกสารแทนหลักฐานเฉพาะรัน.

หลังตรวจrawarraysบนCPU แยกchildphaseเพื่อทดสอบinputทางเลือกโดยใช้accepted hard-maskbaselineเดิม6ภาพ แทนการอ้างว่าrawcontrolผ่านหรือปรับtolerance. Amendmentนี้บันทึกก่อนalternativeinference ไม่เลือกจากalternativeคะแนน. Childใช้1TRAINwarmup+6letterbox+15ROIs=22calls; รวมparent3เป็น25≤29. ไม่retryofficial/wrappercontrolหรือรันวน.

|การบัญชีcallsรวม|จำนวน|
|---|---:|
|TRAINwarmup (2processes)|2|
|Officialreference|1|
|Freshwrapperbaselinecontrol|1|
|Full-frameletterbox|6|
|PersonROIletterbox|15|
|รวม|25|

SharedGPUquality-onlyได้รับอนุญาตตามบริบทงาน; ตรวจจริงGPUidleก่อนแต่ละlaunch,ไม่ปิดงานอื่น. Childไม่มีOOM/CUDA/invalidoutput. Peakforward allocated≈2157MiB/reserved2836MiBเป็นdiagnosticsเฉพาะขอบเขตที่วัด ไม่ใช่totaldeviceusageหรือspeed/VRAMefficiencyranking;ROIมีmodelcallsมากกว่าต่อframeชัดเจน.

## 5. การตรวจรับและprovenance

- CPUliteralcases5ผ่าน:ratio/paddingzero,trimlogitsก่อนargmax,ROIplacement/extent,detectorextentนอกbox,invalid/nonfinite. Actualofficialnormalizerpixel/zero-paddingprobeผ่านด้วย.
- Exact6IDs×3routes=18atomicpackets,ตรวจhash/readback/nativeID/geometryและextents/scoresตรงfrozenYOLO. ROIrawและownednative29masksเก็บแยก,ไม่ใช้overlayแทนnativeoutput.
- Baselineper-partTP/FP/FNตรงacceptedselected-partevaluationเดิมบน6ภาพนี้ทุกค่า. Macro/pooled/day+night arithmeticตรวจจากsavedpartrecordsและindependentFractioncalculation.
- Parentattemptsource snapshotตรงhashเดิม,childsource/GT/config/checkpointbindingsตรง; frozen native/common resultsและscientificsourceเดิมไม่เปลี่ยน.

Parent: `sapiens-input-diagnostic-20261101T022347Z` launchcommit `2bbec368b113af65f145b4b0ac96dafd2e4785fe`; child: `sapiens-input-variants-20261101T022856Z` launchcommit `59df24390bb3105916c3a870f147e550aee2d47e`. ParentstatusยังSTOPPED_DIAGNOSTIC_INCOMPLETEจากnumericgate; childDIAGNOSTIC_COMPLETE6/6และข้อจำกัดcontrolคงอยู่. Rawattempts/logits/logs/privateGTreviewเก็บในoutputsเดิม.

[Frozen/amendedspec](../configs/SAPIENS_INPUT_DIAGNOSTIC.json) / [aggregateevidence](SAPIENS2_INPUT_DIAGNOSTIC_EVIDENCE.json) / [summaryCSV](../metrics/SAPIENS_INPUT_DIAGNOSTIC_SUMMARY.csv) / [per-targetCSV](../metrics/SAPIENS_INPUT_DIAGNOSTIC_PER_TARGET.csv). ค่าCSVเป็นfraction0–1;blanknumericคือnull/N/Aไม่ใช่0. Publiccloneไม่มีprivateGT/predictions/weights/environment จึงทำซ้ำGPUexperimentจากcloneอย่างเดียวไม่ได้.

## 6. ตัดสินอย่างไรต่อ

**ข้อเสนอหลัก:** ควรประเมินSapiensแบบperson-ROIconfigurationเพิ่มเติมก่อนใช้ผลfull-frameเดิมตัดSapiensออก. การทดสอบนี้สนับสนุนว่าpersonscale/crop/contextของinputมีผลต่อคุณภาพอย่างมาก;ไม่พบว่าการเปลี่ยนfull-framestretchเป็นletterboxอย่างเดียวช่วย. ยังไม่พิสูจน์ว่าสัดส่วนเป็นสาเหตุเพียงอย่างเดียว และยังมีGT/Faceproxy/Dress/ownershipข้อจำกัดเดิม.

ผล6ภาพไม่ใช่คะแนนCCTV90ใหม่และไม่ใช้จัดอันดับใหม่กับอีก8ระบบ. ไม่ยกผล0.4Bไปแทน0.8B/1B. ขั้นถัดไปที่พร้อมมอบหมายคือfreezeROIconfigurationที่ทดสอบนี้และอนุมัติevaluation90ภาพของ0.4Bแยกรอบก่อน จากนั้นจึงพิจารณาขนาดอื่น ไม่ขยายอัตโนมัติหรือtuneหลายcrop/settingsจากCCTVคะแนน.

รอบนี้จบที่diagnosticและรายงาน ไม่เปิดfull90/CIHP5000,0.8B/1B,CPI,training,colorหรือCCTVงานอื่นต่อ. [ผล9ระบบเดิม](CCTV_SELECTED_PART_RESULTS_TH.md)ยังคงเดิมตามconfigurationที่ทดสอบ;การอ้างความเหมาะสมของSapiensสำหรับdeploymentต้องแยกจากผลconfigurationนั้น.
