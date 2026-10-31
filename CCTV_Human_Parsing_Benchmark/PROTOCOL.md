# CCTV partial-annotation benchmark — protocol v1

สถานะ: FROZEN_FOR_SCOPED_PARTIAL_BENCHMARK ก่อนmodelscoring ตามผู้ใช้ยืนยันselectedpeople/parts,Dressไม่มีกติกา และมอบหมายให้จัดกติกา. ยังไม่ใช่full-annotationbenchmark/CIHP C4-P reproduction

## เป้าหมายและผลที่ตอบได้

วัดว่าสี่semanticoutputsตรงกับpixelsที่มนุษย์annotateไว้เพียงใดบน90ภาพเดิม. Primary = macro recall4 ของ Face/Hair/Upper/Lower; secondary = recallรายtarget,correct/supportpixels,confusion,annotatedpixelaccuracy,day/nightแยก. ห้ามเรียกค่านี้ว่าfull-imageIoU/precision/FP หรือoverallmodelwinner. Partialannotationอาจbiasedไปคน/ส่วนที่เลือกและmissedคนอื่นไม่อยู่ตัวหาร

## ประชากรและ domain

`val_id.txt` มี90uniqueIDs ทุกระบบใช้รายการเดียวกัน ไม่มีเลือกภาพจากคะแนน. 48day/42night; 87ภาพ1920×1080,2ภาพ2688×1520,1ภาพ1280×720 ใช้originalgridจริงไม่บังคับทุกภาพ1920. รักษาsourceGTเดิม hashRGB/GT/canonicalannotationและgeometryต่อภาพไว้private

D = pixelsที่GT Category_ids∈{13 Face,2 Hair,5 Upper,9 Lower}. GT0 = UNKNOWNทั้งหมด ไม่มีหลักฐานให้ถือเป็นbackgroundnegative. Domainต้องคำนวณจากGTเท่านั้นและเหมือนทุกmodel ห้ามเพิ่มignoreตามprediction. ไม่ใช้GTpolygons/crops/ownerเพื่อช่วยinference. Human_idsเป็นunionของannotatedparts ไม่ใช่personsilhouette; G_loc/G_semจากCIHP17,520/17,454ใช้ที่นี่ไม่ได้. ไม่รายงานextentmatching/personF1จากmaskนี้

## Mapping และ composition

ใช้totalpredictionmappingจาก CIHP_SAPIENS_COMMON_VIEW_REVISION2.json เดิม CIHP0–19/Sapiens0–28ครบ; nativeprediction255/unknown/nonfinite/invalidshapeเป็นcontractfailure. Compose nativeoriginal-gridplanesตามconfidence/tiepacketindexเดิมก่อนprojection ไม่ลบOTHER/Dress/Apparelก่อนresolveoverlap. เก็บnativeBG/OTHERไว้ ไม่collapseเป็นBG

Face: CIHP13 เทียบSapiensFace_Neck3+facialsubparts24–28 เป็นproxy ไม่อ้างstrictface/neckboundaryequivalence. Upper: CIHP5+7 กับSapiens23; Lower: CIHP9+12 กับSapiens13. Dress6/Apparel1→OTHER ไม่มีheuristicsplit. GTชุดนี้upper/lowerยังไม่มีDressrule จึงเรียกannotationagreement ไม่ยืนยันnon-Dressontology; ต้องรายงานtaxonomy-support limitationร่วมกับrecall

## Metric และ missing

h[g,p] = countบนD, rowsGT4targets, colsBG/4targets/OTHER. Recall_c=h[c,c]/sum_p h[c,p]. Macrorecall4=meanของ4recallsเมื่อทั้ง4มีsupport; targetไม่มีsupport→nullและmacro4→null(ไม่เปลี่ยนเป็น3-classmacroเงียบๆ). เก็บsupport/absentflag/ทั้งpopulationและday/night. ตัวเลขfraction0–1 displaypercent. Globalaggregateconfusionก่อนหาร ไม่เฉลี่ยper-imagepercent

ทำนายtargetผิดชนิดบนknownpixelsเป็นcross-classerror; ทำนายBG/OTHERบนknownpositiveเป็นFNของtargetนั้น. PredictionนอกDไม่ถูกให้เครดิตหรือpenaltyเพราะGTไม่ทราบ; จึงมีoversegmentationblindspot ไม่ใช้เป็นหลักฐานprecisionดีหรือgeneraldeployment. ไม่คำนวณconfidenceAPจากhardlabelsหรือเอาIoUเดิมเฉลี่ยแทนunion

## Model และ input fairness

ใช้QANet/M2FP/D2FP/RP-R-CNN/CPI R50/CPI ConvNeXt-B/Sapiens0.4/0.8/1B checkpoint/config/precision/settingsจากCIHPที่ตรวจรับแล้ว. FrozenYOLO26x weights/settings(imgsz640/conf.25/iou.7/maxdet200/retinamasks) สร้างCCTVcacheเพียงครั้งเดียวด้วยBGRinputตามUltralytics แล้วใช้cacheเดียวกันทุกmodel

QANetใช้YOLOROIและmaskownership; Sapiensfull-frame1024×768 native29/mapbackก่อนargmaxแล้วYOLOownership; nativeinstanceparsersใช้nativefullframeแล้วprediction-onlyYOLOassociation. คงTTA/preprocess/threshold/architectureที่ประกาศ ไม่บังคับinputresizeเท่ากันจนเปลี่ยนconfiguration. นี้เป็นapplicationconfigurationcomparison ไม่แยกarchitecture/training/adaptereffects. รุ่นCPIใช้memoryimplementationที่ผ่านboundedparityเดิม (R50feature-schedule3,Convperson-chunk1) ไม่อ้างbitwiseparityทุกCCTVinput

FP32/eval/noAMP/TF32,seedเดิม,หนึ่งTRAIN0000930warmupต่อparserprocessไม่นับในCCTVscore, oneattempt/ID ไม่มีfallback/retry. เก็บfullnativehardmasks/per-personplanes/extents/confidences/geometry,input/model/config/source/environment/detectorhashesและatomiccommit. GTเข้าหลังpredictionexportเฉพาะscorer

## Resources และการจบ

แชร์GPUเพื่อqualityโดยไม่ปิดหรือแก้processอื่น; sequentialoneGPUworker. ตรวจfreeVRAMต่อmodelจากempiricalCIHPpeak+margin ไม่ใช้externalPIDเพียงอย่างเดียวตัดสิน. CPIต้องมีbudgetสูงกว่า~10GiBที่ว่างอยู่ขณะเตรียม; ถ้าไม่ผ่านให้BLOCKED_RESOURCEและทำระบบอิสระต่อ ไม่ลดresolution/precision/thresholdเพื่อให้ผ่าน. 50GiBfree-disk,80GiB/model,24h/modelเดิม. เวลา/VRAMdiagnosticsไม่ใช้ranking

STRICT_COMPLETEต่อระบบ: exact90uniqueIDsพร้อมpacket/readback/scoringครบจึงมีprimary; incomplete/blockedprimarynull ห้ามsubsetแทน90. เก็บallfailures/attempts ไม่retryวน. Controllerจบหลัง9รายการ ไม่มีcolor/training/โมเดลเพิ่มเติม. ถ้าต้องทำcontinuationให้ยืนยันprocess/ledger/hashก่อนและเขียนsegmentใหม่ ไม่ทับfailedattempt

## แผน full benchmark ที่น่าเชื่อถือสำหรับตัดสินใช้งาน

ต้องจัดทำscope/negative/ignoremanifestที่มนุษย์ตรวจครบ,policyDress/Upper/Lower/Face/hairvisibilityและocclusion,ตรวจmissinglabels/QA,freezeversionใหม่โดยไม่แก้sourceย้อนหลัง. ถ้าจะวัดinstanceต้องมีpersonGTextentที่รองรับ ไม่ใช้partunionแทนsilhouette. นอกscopeที่annotateไม่ครบต้องVOIDตามGT-onlypolicyเหมือนทุกmodel. ไม่มีconfigurationใดสร้างข้อมูลannotationที่ขาดได้ ผลpartialรอบนี้ใช้diagnostics/preparation ไม่ยกเป็นfinaldeploymentselection

ร่างนี้เกิดหลังมีexploratoryCCTVscoresบางไฟล์อยู่แล้ว ไม่อ้างpreregistered/confirmatory; mapping/settingsยึดนิยามเดิมและcurrentuserannotationfacts ไม่เลือกให้modelที่คะแนนต่ำได้ประโยชน์
