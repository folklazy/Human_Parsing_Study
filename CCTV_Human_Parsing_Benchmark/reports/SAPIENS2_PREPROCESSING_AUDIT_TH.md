# ตรวจ Sapiens2 preprocessing: input parity และข้อจำกัดของ full-frame route

ตรวจ 2026-11-01T09:12:57.965549+07:00 (Asia/Bangkok). Scope: bounded source/input-tensor audit หลังผู้ใช้สงสัย preprocessing. **Model forward0ครั้ง, ไม่โหลด checkpoint/โมเดล, ไม่แก้ frozen source/config/GT/scores และไม่เปิด GPU worker**.

**ข้อสรุป:** ยังไม่พบ RGB/BGR, normalization, tensor layout หรือ resize implementation bug ในกรณีที่ตรวจ. Tensor ก่อนเข้า network ตรงกับ official demo path ทุกค่าใน12 CPU cases. แต่ full-frame stretch จากภาพแนวนอนเป็น portrait input ทำให้รูปทรงและรายละเอียดคนเปลี่ยนมากจริง จึงต้องแยก “โค้ดทำตรง official” ออกจาก “configuration นี้เหมาะกับ CCTV หรือไม่”. ยังไม่พิสูจน์ว่า stretch เป็นสาเหตุทั้งหมดของผลต่ำ/fragmented output.

## 1. หลักฐานที่ตรวจจริง

|ส่วน|หลักฐาน/ผล|
|---|---|
|Source identity|Official local revision `7e5bae88456ac418ff0e58e74106c9fe192055d4`; imported sapiens มาจาก checkout นี้; Git working treeสะอาด|
|Frozen implementation|benchmark.py และ common_view/sapiens_route.py hashesตรง parent run; ไม่แก้ไฟล์ทั้งสอง|
|Configs|segmentation0.4B/0.8B/1B แต่ละตัวตรง native_config hashของตัวเอง;29classes/test1024H×768W|
|กรณีต่อ config|RGB quadrant fixture, asymmetric gradient fixture, ภาพdayและnightจาก fixed galleryเดิม|
|CPU runtime|torch 2.14.0+cu130, OpenCV 5.0.0; CUDAไม่ได้initialize|
|RGB→native pipeline|PIL RGB→BGR copy→official SegResize/SegPackInputs→ImagePreprocessor bgr_to_rgb|
|Independent arithmetic|resize RGB โดยตรง แล้วคำนวณ (x−mean)/std และHWC→NCHW โดยไม่เรียกwrapper|
|Official reference|cv2.imread(BGR)→config.pipeline→config.data_preprocessor ตาม official vis_seg.py|
|Output-grid check|synthetic29-channel logits asymmetric quadrants→bilinear original-grid→argmax ตรง literal expected mask; ไม่มีneuralforward|

|Model config|Cases|Max difference vs direct RGB math|Max difference vs official demo input|
|---|---:|---:|---:|
|Sapiens2_0.4b|4|0.0|0.0|
|Sapiens2_0.8b|4|0.0|0.0|
|Sapiens2_1b|4|0.0|0.0|

ทุกtensorเป็นFP32 `[1,3,1024,768]`. Mean `[123.675,116.28,103.53]`, std `[58.395,57.12,57.375]` ใช้กับค่าRGB0–255; ไม่มีหาร255เพิ่ม. Rangeของquadrantfixtureประมาณ−2.118ถึง2.640. เปิดดูinverse-normalized previewsของCCTVทั้ง2ภาพแล้ว สีและcontentตรงภาพต้นทางหลังresize; inverse imageตรงcv2-resizedRGBทุกpixel. PIL/OpenCV decodeของ2ภาพนี้ตรงกันทุกpixelด้วย.

**ขอบเขตของคำว่า parity:** เป็น CPU reconstruction จากภาพ/source/config/environmentที่ผูกไว้ ไม่ใช่ tensor ที่บันทึกระหว่าง historical GPU forward เพราะรอบเดิมไม่ได้เก็บtensorนั้น. ไม่ใช่ learned-forward/output equivalence, ไม่ตรวจครบ90/5,000ภาพ และไม่รับรองว่า pipelineไม่มีbugทุกประเภท. [Evidence](SAPIENS2_PREPROCESSING_AUDIT_EVIDENCE.json).

## 2. จุดที่น่ากังวล: รูปแบบ input

Official config ตั้ง `SegResize(height=1024,width=768,keep_ratio=False)` และ official demo ส่งภาพทั้งภาพเข้า pipeline. เส้นทางของเราจึงยืดทั้ง CCTV frameตามค่านั้น ไม่ได้ cropคนก่อน:

|ปริมาณ|ค่า สำหรับภาพ1920W×1080H|
|---|---:|
|Input width/height|768W×1024H|
|Scaleแนวนอน|768/1920=0.4000|
|Scaleแนวตั้ง|1024/1080≈0.9481|
|อัตราส่วนwidth/heightของวัตถุหลังresize เทียบต้นฉบับ|0.4000/0.9481=0.421875|

คนจึงมีwidth/heightเหลือประมาณ42.2%ของสัดส่วนเดิม: แคบลงและดูยืดในแนวตั้ง. คนสมมติกว้าง100pixelsในต้นภาพจะเหลือ40pixelsแนวนอน; รายละเอียดเสื้อผ้า/หน้าเล็กลงตามนั้น แม้ tensorมี1024rows. นี่เป็นผลเชิงgeometryที่คำนวณได้และเห็นในprivatepreview ไม่ใช่ผลaccuracyที่พิสูจน์แล้ว.

การ map-back logits กลับoriginalgridคืนขนาดoutputได้ แต่ไม่กู้รายละเอียดที่หายตอนresize และไม่ทำให้networkเห็นคนสัดส่วนเดิมย้อนหลัง. FrozenYOLO maskownershipเกิดหลังnetwork จึงไม่ได้ช่วยขยายคนก่อนinference.

QANetได้รับpredicted personROIก่อนparser จึงมี input conditioning ต่างจาก Sapiens full-frame. ผลรอบเดิมเปรียบ checkpoint+applicationconfiguration ได้ แต่ไม่แยกผลarchitecture/route/scale. ไม่ควรใช้ผลนี้ตัดสินว่าSapiens2โดยตัวมันเองด้อยกว่าโดยยังไม่จำกัดคำอ้าง.

## 3. ตรวจจุดที่อาจทำผิด

|สมมติฐาน|สิ่งที่พบ|ข้อสรุปจำกัดขอบเขต|
|---|---|---|
|RGB/BGRสลับผิด|readerสร้างRGB; wrapperสร้างBGR; officialpreprocessorแปลงกลับRGB; asymmetricfixtures/directmathตรง|ไม่พบใน12cases|
|Normalizeซ้ำ/scaleผิด|workerเรียกpreprocessorครั้งเดียว; SegEstimator.forwardเข้าbackbone/decode_headตรง ไม่เรียกimagepreprocessorซ้ำ; directmathตรง|ไม่พบจากsource/CPUparity ไม่ใช่historicalGPUtensorcapture|
|W/Hกลับด้าน|configระบุheight1024,width768จริง; outputshapeตรง|ไม่ได้สลับค่า แต่ intentionalstretchอาจไม่เหมาะกับCCTV|
|Class/channelmap-backผิด|sourcechannel29/BCHW, bilinearก่อนargmax; asymmetriclogitscaseผ่าน|เป็นcontract/geometrytest ไม่ใช่learnedlogitsemanticparity|
|Saved mask/galleryเพี้ยน|รอบก่อนตรวจnative reference→ownedplanesบน3Sapienspacketsผ่าน; ภาพfragmentedมาจากstorednativeoutput|packetintegrityไม่ยืนยันว่าforward/preprocessingเหมาะสม|
|Weight-loadingผิด|workerใช้segconfig/checkpointbindingsของแต่ละขนาด, strictstate_dictload; officialinit_modelถูกเรียกก่อนloadและeval/cuda|รอบนี้ตรวจsource/bindings ไม่โหลดweightsหรือพิสูจน์forward|

ยังไม่มีหลักฐานให้ระบุสาเหตุแน่นอนว่าเป็น domain, full-frame stretch/scale, learnedforward หรือ modelquality. ไม่ปรับsettings/แก้คะแนนเพื่อทำให้Sapiensดีขึ้นจากข้อสงสัยอย่างเดียว.

## 4. ผลต่อรายงานและการตรวจต่อ

ผล [selected-part CCTV90](CCTV_SELECTED_PART_RESULTS_TH.md) ยังคงเดิมและครบ9/9ตามconfigurationที่รัน. QANetเป็นobservedleaderของconfigurationเหล่านั้น; ไม่เปลี่ยนเป็นคำตัดสินarchitectureหรือปฏิเสธSapiensทุกรูปแบบ. Inputparityที่ผ่านไม่ทำให้ข้อจำกัดGT/Faceproxy/partialannotationsหายไป.

การตรวจถัดไปที่ตอบคำถามได้ตรงจุด เมื่อมีขอบเขตinferenceใหม่:

1. **Learned-forward parity แบบจำกัด:** Sapiens0.4B, checkpointเดิม, ภาพdayจากfixedgalleryเดิม1ภาพ; officialreference pathกับwrapperภายใต้FP32/eval/inference/device/seedเดียวกัน รวมไม่เกิน2VALforwards ไม่มีretry/fallback. จับactualinputtensorและrawlogitsก่อนmap-backเพื่อระบุความต่าง ไม่ใช้GTหรือคะแนนเลือกsettings. หากต้องwarmupให้แยกTRAINไม่เกิน1callและบันทึกbudgetรวม.
2. ถ้าforwardpathตรงกัน จึงเสนอ **Sapiens YOLO-ROI configuration แยกใหม่** เพื่อทดสอบผลของpersonscale/context โดยใช้YOLOcacheเดิม, padding/map-back/clip/overlappolicyที่ตรึงก่อนรัน; ไม่ใช้GTcrops ไม่ลองหลายsettingsแล้วเลือกคะแนนสูงสุด. Letterboxเป็นอีกconfiguration ไม่ใช่bugfixที่แทนfrozenresultอัตโนมัติ.
3. การเทียบrouteใหม่ต้องรายงานเป็นexploratoryconfigurationcomparisonพร้อมinputcost/coverageและGTชุดเดียวกัน. ไม่rerunอีก8โมเดลโดยอัตโนมัติ ไม่เขียนทับfull-framepackets และไม่รวมrouteใหม่เข้าคะแนนเก่า.

**รอบนี้ยังไม่ทำทั้ง3ขั้นดังกล่าว**: คงข้อห้ามmodelinferenceใหม่ของงานสรุปผล ไม่มีGPUmodelโหลด/forward, training, checkpointdownload หรือenvironmentchange. ไม่เปิดbenchmarkเพื่อไล่หาคะแนนที่ดีกว่า.

## 5. ไฟล์และ reproduction

- [CPU audit script](../scripts/audit_sapiens_preprocessing.py):สร้างfreshdirectory ไม่เขียนnativeoutputs. ต้องใช้environment `.venvs/sapiens2-pilot`เดิม พร้อมofficialsourceและprivateCCTVinputs.
- Private artifacts: `CCTV_Human_Parsing_Benchmark/outputs/sapiens-preprocessing-audit-20261101/` มีEVIDENCE, PRIVATE_INPUTS และinverse-normalizedday/nightPNG; เก็บภายในเครื่อง ไม่ขึ้นGit.
- PublicJSONเก็บsanitizedresults/config/sourcehashes ไม่มีCCTVfilenames/personrecords/ภาพ. Publiccloneอย่างเดียวไม่มีprivateinputs จึงทำซ้ำreal-imagecasesไม่ได้.

Primary sourcesที่อ่านจริง: [official segmentation demo](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/sapiens/dense/tools/vis/vis_seg.py), [0.4B config](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/sapiens/dense/configs/seg/shutterstock_goliath/sapiens2_0.4b_seg_shutterstock_goliath-1024x768.py), [image preprocessor](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/sapiens/engine/datasets/data_preprocessors/image_preprocessor.py). ใช้revisionเดียวกับlocalrun; officialdemoไม่ได้รับรองว่าfull-frameinputเหมาะกับCCTVทุกภาพ.
