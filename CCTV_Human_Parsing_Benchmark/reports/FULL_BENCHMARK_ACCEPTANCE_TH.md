# เงื่อนไขยกระดับ CCTV เป็น full benchmark สำหรับเลือก configuration

เอกสารนี้เป็นข้อกำหนด QA/annotation ที่ต้องปิดก่อนอ้าง full-image performance ไม่ได้เปลี่ยน source labels หรืออนุญาตให้นำ predictions ไปสร้าง GT อัตโนมัติ รอบ partial ที่เปิดแล้วคง PROTOCOL.md เดิม

## สิ่งที่ตัดสินแล้วจากข้อเท็จจริงของข้อมูล

- แยก immutable source release ปัจจุบัน90ภาพออกจาก derived evaluation version ทุกครั้ง ห้ามเรียก100ภาพตามชื่อfolder
- Partial labels ไม่ยืนยันว่า pixelsที่เหลือเป็นbackground. GTต้องระบุknown/unknown/ignoreโดยannotation ไม่ใช่จากpredictionของmodelใด
- ห้ามใช้ Human_ids ที่เป็นunionของpartsอ้างว่ามีfullpersonGTแล้ว. Instance/ownership claimsต้องใช้GTที่รองรับจริง
- ทดสอบcheckpointพร้อมapplicationroute ไม่แยกarchitecture/training/adaptercausality. ยึดเก้าcheckpoint/YOLOเดิม ไม่มีtuneบนCCTV/ensemble/เพิ่มโมเดลเพื่อไล่คะแนน

## กติกา annotation ที่แนะนำสำหรับ release ถัดไป

|เรื่อง|กติกาที่แนะนำ|หลักฐานรับงานที่ต้องมี|
|---|---|---|
|Scope ของภาพ|เลือกว่าจะannotateครบทั้งภาพ หรือกำหนดmanually-reviewed evaluation regionsที่ทุกperson/targetภายในครบ;นอกregionเป็นVOIDเหมือนกันทุกระบบ|per-image region/mask,reviewer,date,version;ไม่เลือกregionจากmodelscore|
|บุคคลที่ไม่ประเมิน|ระบุignoreperson/regionพร้อมเหตุผล;unselectedคนที่ไม่ทราบlabelsห้ามกลายเป็นnegative|รายการบุคคล/regionและpolicyoverlap;ไม่ใช้modeldetectorเลือกGT|
|Target visibility|เก็บlabelstateรายperson/target:VISIBLE_AND_ANNOTATED,ABSENT_OR_NOT_VISIBLE,UNRESOLVABLE,NOT_ANNOTATED;สองสถานะท้ายไม่ใช่negative|coveragecheckเทียบannotationและimage;ไม่เติมส่วนที่ถูกบังตามanatomicalguess|
|Face|visibleface regionตามนิยามเดียว;แยกจากhair/neckอย่างชัดในguideline|ตัวอย่างboundaryและreviewความสม่ำเสมอ;SapiensFace_Neckยังเป็นproxy/representationlimitationไม่ใช้ชื่อเหมือนกันยืนยันequivalence|
|Hair|visiblehairรวมhairlineตามguideline;หมวก/ส่วนที่ไม่เห็นไม่ใช่hairปลอม|กรณีไกล/IR/หมวก/หัวหันหลังที่ระบุobservability|
|Upper/Lower|Upper=visibleuppergarmentsรวมcoat;Lower=visiblepants/skirt;กำหนดlayer/occlusionboundaryตามสิ่งที่เห็น|manualexamplesเสื้อยาว/coatทับpants/skirt/เสื้อชั้นใน ไม่ใช้เส้นตัดกลางคนแบ่งmask|
|Dress/ชุดชิ้นเดียว|แนะนำเก็บDress/one-pieceแยกเป็นOTHERสำหรับงานUpper/Lower non-Dress;ไม่splitด้วยgeometry;เมื่อดูไม่ออกให้UNRESOLVABLE|manualreviewกรณีที่เดิมlabelupper/lowerอาจรวมDress;เก็บrevisionต่าง ไม่แก้GTเดิมให้ดูเหมือนกำหนดแล้ว|
|Background/OTHER|ภายในknown domain:BG=ไม่ใช่คน/targetตามนิยาม,OTHER=recognized non-targetที่กำหนด;มีGTตรวจรองรับ ไม่collapseuncertainpartsเป็นBG|schemaครบ,target/OTHER/BG/VOIDไม่ขัดกัน;source255/derivedVOIDแยกprovenance|
|Person extent|ถ้าต้องการinstanceF1 ให้annotatevisiblepersonsilhouetteพร้อมpersonID;ถ้ามีแค่partsให้จำกัดmetric/ชื่อclaimตามparts|extent/parts/ownerbindingsตรงกัน ไม่filledbboxหรือfullsilhouetteที่เดาจากparts|
|Overlap/edges|annotationต้องกำหนดvisiblefrontsurface/occlusion;ambiguouspixelsเป็นsharedVOIDที่เขียนไว้ก่อนคะแนน|ไม่มีper-modelignoreหรือerosionหลังเห็นคะแนน|
|QA|ผู้ตรวจอิสระดูscope/exhaustiveness/semanticboundaryและแก้conflictsโดยมีchange log|reviewrecordsและGT-only counts/hashes;automatedchecksไม่แทนsemanticQA|

กติกานี้ไม่ได้ทำให้ทุกtaxonomyเท่ากัน: ถ้าmodelส่งFace_NeckหรือDressที่แบ่งไม่ได้ จะรายงานความสามารถต่อtargetที่ต้องการตามmappingที่ประกาศโดยไม่ช่วยแยกด้วยGT และแยกtaxonomy incompatibilityออกจากsegmentationerrorในการอภิปราย

## Gate ก่อน freeze full evaluation

1. มีmanualevidenceของknownnegative/ignore/completeannotationsบนpopulationที่จะอ้าง ไม่จำเป็นต้องอ้างครบทุกpixelsถ้าเลือกregionbenchmarkที่ระบุชื่อ/ข้อจำกัดตรงไปตรงมา
2. ข้อกำหนดFace/Hair/garment/Dress/visibility/ownershipผ่านQAและmaterializederivedGTโดยไม่เปลี่ยนsource; GT-onlysupport/personeligibility/hashตรวจแล้ว
3. Totalmapping,GTdomain,metricdenominators,absentclass/emptyoutput/missed/duplicate policiesเหมือนกันทุกmodel;unsupportedpredictionไม่กลายเป็นignoreตามmodel
4. CPU hand-counted acceptance + actualpacket→scorer→reporterผ่าน; read-onlysavedpredictionsที่bindingsตรงสามารถreuseได้ ไม่inferenceใหม่เพียงเพราะปรับGT/evaluator version
5. Exactpopulation,attempt/recovery/resourcepolicyและquality-onlyclaimsfreezeก่อนaggregateคะแนนfullใหม่;scoreที่เคยเห็นต้องเปิดเผยว่าไม่ใช่preregisteredblindtest

เมื่อผ่านจึงคำนวณglobalIoU/FPและinstance metricsเฉพาะที่GTรองรับได้ พร้อมday/nightแยกและจำนวน support. หากGTยังไม่ผ่านให้รายงานpartialrecallภายใต้ขอบเขตเดิม ไม่เติมคะแนนหรือเลือกoveralldeploymentwinner

## ผลสรุปที่อนุญาตแต่ละระดับ

|ระดับ|กล่าวได้|ยังกล่าวไม่ได้|
|---|---|---|
|Partial benchmark ปัจจุบัน|annotation-conditioned targetrecall/cross-classagreement,missedknownpositivepixels,executioncompleteness|full-imageprecision/IoU,falsepersoncount,ความแม่นทุกคนหรือoverallwinner|
|Full semantic known-domain benchmark|targetIoU/support/precision/recallภายในdomainที่ตรึง;configurationleaderบนpopulationนี้|native-taxonomyequivalence,architecture-onlycausality,ทุกกล้อง/ทุกsite|
|Instance benchmark ที่มีfull GT|personmaskmatching/FP/FN/ownershipตามนิยามพร้อมsemanticQและcoverage|tracking/ReID/real-timeperformanceหรือสีที่ยังไม่ได้ทดสอบ|

ผลpartialยังมีประโยชน์ตรวจdomainshiftและimplementation แต่ต้องใช้ร่วมกับข้อจำกัดselection biasและannotated-class imbalance ไม่ถือว่าทดสอบครบ90ภาพแล้วแปลว่าGTครบทั้งภาพ
