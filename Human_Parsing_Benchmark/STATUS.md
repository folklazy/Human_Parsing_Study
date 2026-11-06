# คิว Sapiens1B → CPI ConvNeXt พร้อมเปิด — 2026-11-06T17:56:51.856783+07:00

**SAPIENS_VAL_RUNNING / FIRST_NEW_PACKET_PASS / CPI_QUEUED** — ผู้ใช้ให้พักSapiensชั่วคราวเพื่อเตรียมCPIก่อน แล้วค่อยรันต่อเป็นลำดับ. พักworker3616747เมื่อ17:41:41น.ไทยด้วยSIGINTหนึ่งครั้งระหว่างMODEL_CALL_START;processออกแล้วและไม่มีการเขียนpacketค้าง. เก็บKeyboardInterruptและผลทุกsegmentไว้ ไม่ใช่modelOOM

| ระบบ | ผลเดิมที่ตรวจผ่าน | ที่เหลือตอนfreeze:ภาพ / ROIใหม่ | สถานะ |
|---|---:|---:|---|
| Sapiens2 1B | 4,268ภาพ /20,356ROIs รวม4partialROIs |732 /3,706|กำลังรันต่อ|
| CPI ConvNeXt-B |4,335ภาพ /20,702ROIs รวม2partialROIs|665 /3,360|รอ1Bครบและprocessออก|
| CPI R50 |5,000ภาพ|0|ครบแล้ว ไม่รันซ้ำ|

CPI shared-head CPU3casesและคิว/merge CPU5casesผ่าน. GPUdiagnostic3callsขณะSapiensพัก:TRAINrevision1↔revision3 hardmask/candidate/associationตรงกัน;probeภาพ0037051 ROI2ผ่าน peakallocated7.429GiB/reserved7.764GiB. Diagnosticแยกจากcanonical ไม่ใช้ปรับคะแนน/settings. ใช้CPI_FEATURE_BRANCH_SCHEDULE_3แบบmodel-localเพื่อแก้จุดcnt_part_parser/ReLU OOM ไม่เปลี่ยนFP32/resolution/threshold/TTA/GT/YOLO/scorer;เป็นboundedparity ไม่ใช่populationbitwiseproof

Queue`cihp-sequential-finish-20261106T105503Z`จะรัน1BครบSTRICT_COMPLETEและรอcontroller/workerออกก่อนเปิดCPI;ถ้า1Bไม่ครบคิวหยุด ไม่เปิดCPIแทรก. ตัวคิวรอchildprocessแบบblockingwait ไม่มีmodel/GPUcontext;viewerอ่านSTATEไฟล์เล็กทุก30วินาที. ยกเลิกwalltimecapในการทำให้ครบ คงVRAM/disk/callbudget/noautomaticretry. ไม่เปิดSAM3/โมเดลอื่น

[First packet verification](runs/cihp-sequential-finish-20261106T105503Z/LAUNCH_VERIFICATION.json) / [รายงาน](reports/CIHP_CONTROLLED_ROI_RUN_TH.md) / [Queue config](runs/cihp-sequential-finish-20261106T105503Z/QUEUE_CONFIG.json) / [CPI diagnostic](runs/cihp-sequential-finish-20261106T105503Z/CPI_DIAGNOSTIC_SUMMARY.json). เปิดคิว17:58:41น.ไทยแล้ว:queuePID3677294,1Bcontroller3677320/worker3677383อยู่ในtmux`cihp_seq_20261106T105503Z`;1BกลับมาทำVALจริงแล้ว;ตรวจ18:03:31น.ไทยสำเร็จสะสม4,269/5,000ภาพ,newVALcalls2,failed0invalid0. CPIยังไม่เปิด. ดู `tmux attach -t cihp_seq`

## ก่อนการพักเพื่อเตรียม CPI (historical snapshot)

# Sapiens1B รันต่อแล้วใน tmux — 2026-11-06T17:24:11.176769+07:00

**VALIDATION_RUNNING / FIRST_NEW_PACKET_PASS / USER_TIME_CAP_REMOVED** — run `cihp-sapiens1b-finish-20261106T101324Z`;controller3616671,worker3616747,tmux `cihp_1b_finish_20261106T101324Z`. [รายงาน](reports/CIHP_CONTROLLED_ROI_RUN_TH.md) / [หลักฐานเปิดงาน](runs/cihp-sapiens1b-finish-20261106T101324Z/LAUNCH_VERIFICATION.json)

ตรวจใช้ผลเดิมผ่าน4,222ภาพ/20,101ROIs รวม2partialROIs;pendingตอนfreeze778ภาพ/3,961VALROIs. TRAINparityสองcallsผ่าน. ภาพแรกที่ทำต่อ0036823ปิดpacketและscoreสำเร็จ:7ROIs=2parent+5new,originalgrid375×500,native29/NPZ atomic hashes/config/input/checkpoint/YOLOextent-scores/ownership/scoring linksผ่าน. Snapshot17:24:11น.ไทย: **4,223/5,000ภาพ**,newVALcalls7,failed0invalid0;ตัวเลขปัจจุบันดูprogress ไม่ใช้snapshotนี้แทนlivecount

ผู้ใช้ยกเลิกเพดานเวลาเฉพาะ1Bแล้ว จึงไม่หยุดซ้ำเพราะ24ชั่วโมง. เก็บเวลาparent86,402.741วินาทีรวมกับsegmentใหม่;VRAM/พื้นที่ว่าง50GiB/stream80GiB/finitecallbudget/noOOMretryยังเหมือนเดิม. Native/scorer/checkpoint/FP32/YOLO/GTไม่เปลี่ยน;7ระบบครบแล้วไม่รันซ้ำ,CPIConvNeXtยังพัก4,335/null,SAM3ไม่เปิด

ดูสถานะ: `tmux attach -t cihp_1b_finish` (Ctrl+Bแล้วDเพื่อออกโดยไม่หยุดงาน). Viewerในsessionเก่า`cihp_resume_20261105T044738Z`ชี้runใหม่นี้แล้วด้วย. Logs/statusอยู่`outputs/cihp-sapiens1b-finish-20261106T101324Z/`. Workerอยู่ในdetachedtmuxและไม่ต้องให้Codexเฝ้า เมื่อจบสร้าง`ROUND_CLOSURE.json`/`SUMMARY_TH.md`อัตโนมัติ พร้อมcanonical`Sapiens2_1b/METRICS.json`เมื่อSTRICT_COMPLETEผ่าน. Next:ปล่อยworkerเดิมทำจนterminal;ไม่เปิดงานซ้ำหรือโมเดลอื่น

## สถานะก่อนผู้ใช้อนุมัติให้ทำจนครบ

# Sapiens1B หยุดที่เพดาน24ชั่วโมง — 2026-11-06T17:05:51.585401+07:00

**STOPPED_RESOURCE_TIME_GUARD / SEVEN_COMPLETE / TWO_INCOMPLETE** — [รายงานปัจจุบัน](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). Sapiens1B ของ segment `cihp-sapiens-resume-20261105T044738Z` หยุด6พฤศจิกายน15:22:25น.ไทยด้วย `RESOURCE_TIME_GUARD` หลัง86,402.741วินาที; เป็นเพดานเวลา24ชั่วโมง ไม่ใช่OOM และไม่ใช่การจบ5,000ภาพ

ตรวจ17:03น.ไทย: controller2096828/worker2375725ออกแล้ว ไม่มีcompute PIDบนT4; tmuxยังเหลือหน้าดูสถานะ ไม่ได้แปลว่าworkerทำงาน. ตรวจmanifest hashและmembershipของframe packets/score filesตรงกัน4,222unique IDs,เหลือ778ภาพ;20101ROI packet directoriesคงเดิม รวมpartialที่ต้องreconcile. terminalfailed=1เป็นresource-stop record,invalid=0,primary=null. การนับไฟล์ครั้งนี้ไม่ใช่NPZ acceptanceหรือfull rescoreใหม่ [หลักฐาน](runs/cihp-sapiens-resume-20261105T044738Z/SAPIENS1B_TIME_GUARD_REVIEW.json)

Next:เก็บparentและpartialทั้งหมด ตรวจreconciliationก่อนfresh continuation และต้องมีการรับรองการขยายtime budgetเฉพาะ1Bก่อนlaunch ห้ามresetเวลาสะสมหรือแก้frozenconfigย้อนหลัง. ConvNeXtยังพัก4,335/nullจากOOMเดิม ไม่เปิดงานใดใหม่ในการตรวจครั้งนี้. SAM3.1ที่ใช้GPUร่วมช่วง14:09–14:15น.ไทยหยุดแล้ว;ไม่ถือว่าไม่มีผลต่อเวลา และยังไม่ได้วัดผลกระทบเชิงเหตุและผล

## สถานะก่อนการตรวจเพดานเวลา (historical snapshot)

# Sapiens0.8ครบ5,000; Sapiens1Bรันในtmux — 2026-11-05T15:33:58+07:00

**SEVEN_COMPLETE / SAPIENS1B_RUNNING / CONVNEXT_HELD_INCOMPLETE** — [รายงาน](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). Segment`cihp-sapiens-resume-20261105T044738Z` ต่อ0.8สำเร็จ:4182parent+818new=5000unique,19907parent+4155new=24062ROIs strictcomplete missing0duplicate0/METRICShashตรง จบ15:22:18ไทย ประวัติKeyboardInterruptคงเดิม

Controller2096828/1Bworker2375725aliveในtmux`cihp_resume_20261105T044738Z`;1Bเริ่ม15:22:22ไทย TRAINparity2callsและpacketแรกPASS snapshot17/5000 ณเวลาตรวจ failed0invalid0 CPIConvNeXtพัก4335/null ไม่retry. ดูสถานะปัจจุบันจาก `.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/resume_controlled_cihp_sapiens.py progress --config Human_Parsing_Benchmark/outputs/cihp-sapiens-resume-20261105T044738Z/CONFIG.json` หรือattachsessionนี้ ไม่ใช้viewerparentที่RUNNINGค้าง

Next:ปล่อย1Bworkerเดิมทำงาน;จบแล้วหยุดตามqueue/capเดิม ตรวจclosureภายหลังโดยไม่inferenceซ้ำ ไม่มีการวิเคราะห์qualityrankingหรือเปิดงานอื่นในรอบนี้ [Verification](runs/cihp-sapiens-resume-20261105T044738Z/LAUNCH_VERIFICATION.json)

## บันทึกก่อนการยืนยันรันต่อ

# Sapiens0.8 interruption continuation — 2026-11-05T11:51:00+07:00

**RECONCILIATION_PASS / PREPARED_FOR_TMUX**. [รายงาน](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). Newsegment`cihp-sapiens-resume-20261105T044738Z` reuse4,182frames/19,907ROIs;pending818frames/4,155ROIs. Reuse6completeระบบไม่inferenceซ้ำ;ConvNeXtพักincomplete. คิว0.8→1Bตามกติกาเดิม ใช้scientificworkerhashเดิมและคง24h/80GiBรวมparent ไม่มีauto-retry/fallback รอTRAINparity/packetใหม่เพื่อยืนยันlaunch

Next:เปิดdetachedtmux controllerพร้อมprogresswindow แล้วตรวจpacketใหม่สั้น ๆ ผลเก่า/KeyboardInterrupthistoryคงเดิม รายละเอียดconfig/identityในruns/cihp-sapiens-resume-20261105T044738Z/CONTINUATION_SUMMARY.json

## บันทึกก่อนการรันต่อครั้งนี้

# CPI ConvNeXt-B หยุดด้วย OOM; คิวเดิมรัน Sapiens2 0.4B — 2026-11-04T09:38:00+07:00

**FIVE_COMPLETE / CONVNEXT_INCOMPLETE / SAPIENS04_RUNNING** — [รายละเอียด](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). CPI R50จบstrict5,000/5,000เมื่อ05:06:43ไทย ConvNeXtOOMภาพ0037051เมื่อ09:26:09ไทย คง4,335complete/665missing-complete/20,702committedROI packets; attemptedVAL20,703รวมfailed1,primarynull ห้ามนับว่าปิดรอบแล้ว

Controller3034452รอConvNeXtออกแล้วไปSapiens0.4ตามMODEL_OOM→no-retry→next policyเดิม เริ่ม09:26:15ไทย Worker151980/tmuxcihp_resources_20261103T062248Z snapshot80/5,000ณเวลาตรวจ failed0/invalid0 ยอดปัจจุบันให้ใช้progress ไม่ใช้snapshotนี้ แก้เฉพาะรายงาน/สถานะและเพิ่มcompactevidence ไม่แตะexecution/config/resultsและไม่restart

Next:คิวSapiensเดิมทำงาน; ConvNeXtต้องcontrolledreconciliation/targetedmemoryrepairแยกเมื่อดำเนินต่อ ไม่ทิ้งpartial/ไม่rerunระบบที่ครบ/ไม่ลดquality settings ไม่วิเคราะห์rankระหว่างbatch

## บันทึกก่อนการตรวจOOMครั้งนี้

# ทำไม CIHP/CCTV ยังใช้วิธีให้คะแนนต่างกัน — 2026-11-04T01:25:24+07:00 (Asia/Bangkok)

**COMPARABILITY_REVIEW_COMPLETE / SHARED_PART_SCORING_PROPOSAL_NOT_FROZEN** — [ผลตรวจและข้อเสนอในรายงานเดิม](reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md). แยกความต่างที่เป็น design choice (global เทียบ mean-part) ออกจาก GT limitations (partial annotation/ไม่มี CIHP Neck-uncertainty binding) และ matching ที่ใช้คนละสูตร CIHP รอบ controlled มี mean-part/pooled part counts เป็น secondary อยู่แล้ว จึงใช้สูตรร่วมประกอบรายงานได้ แต่ไม่อ้าง GT/matching equivalent โดยอัตโนมัติ

ข้อเสนอคือคงผล/primary/คิวเดิม และเมื่อมี shared-part scoring revision ที่ชัดเจนใช้ saved masks บน CPU ด้วย mapping/domain/eligibility/association ที่ประกาศร่วมกัน ส่วน Face แบบเดียวกันจริงต้องมีคู่มือและ GT หน้า/คอ/uncertainty ในทั้งสองชุด ไม่เพิ่ม per-model ignore/weight/GT-assisted prediction การตรวจนี้ไม่อนุมัติ reannotation ทั้งชุดหรือเปิด scoring/inference เพิ่ม

ตรวจ17small source/config/protocol/result filesคงhashเดิม, ตัวอย่างสมมติ6ค่า, schema GT และลิงก์รายงานผ่าน โดยไม่ดูคะแนนpartial/อ่านGT arrays/รันmodel/scorer/ตรวจpopulationซ้ำ รายงาน2พฤศจิกายนที่เขียน controlled not run ติดป้าย historical ชัดแล้ว Next: ใช้ข้อสรุปนี้อธิบายเหตุผล; รักษา batch เดิมและวิเคราะห์ผลตาม frozen protocol เมื่อ terminal

## บันทึกก่อนการทบทวนวิธีให้คะแนนร่วม

# อธิบายตัวชี้วัด CIHP ในรายงานเดิม — 2026-11-03T15:20:20+07:00 (Asia/Bangkok)

**METRIC_EXPLANATION_VERIFIED / DOCUMENTATION_ONLY**. เพิ่มคำอธิบายภาษาง่ายใน [รายงาน CIHP เก้าระบบรอบก่อน](reports/CIHP_COMMON_NINE_RESULTS_TH.md#วิธีอ่านตัวชี้วัด-ความหมาย-ที่มา-และตัวอย่างคำนวณ): IoU, C4-P/C3, Q_C4_GT, person TP/FP/FN/F1 พร้อมที่มา สูตร ตัวหาร ตัวอย่างสมมติ และข้อจำกัด Q ที่ต้องอ่าน FP/F1 ร่วม ระบุว่า IoU เป็นสูตรมาตรฐาน ส่วนชื่อกลุ่ม C4-P/C3 และ Q เป็นนิยามโครงการ; Q เฉลี่ยคลาสที่มีใน GT หรือ prediction ของแต่ละคู่ ไม่หารสี่ทุกคน

ตรวจละเอียดเพิ่ม 2026-11-03T15:28:11+07:00: นิยาม global/person valid domains, confusion 6×6, compose-before-project, geometry ties/ID fallback, semantic-empty/unsupported/invalid และ contamination ตรงกับ core.py/full.py ตรวจ canonical METRICS9ไฟล์รวม90,954bytes, CSVรายtarget54รายการและperson18รายการ, ตัวเลขที่แสดงตรง full precision, ตารางเดิม117บรรทัดคงเดิม และ relative links39รายการใช้ได้ทั้ง source/publication ใช้ exact-membership audits เดิม ไม่อ่าน masks/ไม่ rescore หรือรัน test suite ใหม่

งานนี้เป็นคำอธิบายผลเก่าที่ครบ 9/9 ไม่ใช่สรุปคะแนนรอบ controlled ROI ที่กำลังรัน ไม่ได้คำนวณคะแนนใหม่หรือแก้ execution/scorer/config/GT/predictions. คิวปัจจุบันอยู่ใน tmux `cihp_resources_20261103T062248Z`; ใช้ progress command ในสถานะการรันด้านล่างตรวจจำนวนล่าสุด ไม่ใช้ snapshot เก่ามาอ้างเป็นจำนวนปัจจุบัน ขั้นถัดไป: อ่านรายงานพร้อมนิยาม และปล่อยคิวเดิมทำงานตาม gates เดิม; วิเคราะห์คุณภาพรอบใหม่เมื่อ batch terminal

## บันทึกสถานะการรันก่อนหน้างานเอกสาร

# Controlled CIHP resource continuation กำลังทำงาน — 2026-11-03T13:26:47.345448+07:00

**FOUR_COMPLETE / CPI_R50_RUNNING**. QANet/M2FP/D2FP/RPRครบ5000ต่อระบบและreuseเดิม. CPI R50parentหยุด4frames/34ROIsด้วยphysicalfreeguardก่อนforward ไม่มีOOMtraceback. Newsegment`cihp-controlled-resources-20261103T062248Z`ใช้ownreusablepoolaccountingพร้อมthreshold1GiBเดิม เปิด13:24:57Thai/controller3034452/worker3034473ในtmux. ตรวจsnapshot14/5000ภาพ,newROIcalls54,failed0/invalid0,TRAINparityและnewpacket0000027PASS. [รายงาน](reports/CIHP_CONTROLLED_ROI_RUN_TH.md)

ดูสถานะ `.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/continue_controlled_cihp_resources.py progress`. เหลือ5โมเดลรวมCPIปัจจุบัน;controllerเดินคิว5000ตามgatesเดิม. Livecleantimingpendingและวิเคราะห์rankหลังbatchterminal

# Controlled CIHP resource continuation เตรียมพร้อม — 2026-11-03T13:24:44.856361+07:00

**FOUR_COMPLETE / CPI_RESOURCE_CONTINUATION_PREPARED**. QANet/M2FP/D2FP/RPRครบ5000/ระบบ. คิวหยุดCPI R50ที่4frames/34ROIsก่อนforwardเพราะphysicalfreeheadroomguard ไม่พบCUDA-OOMtraceback. ReconciliationPASS,preparedownreusablecacheaccountingตามCCTVเดิมและCPU4cases×2envPASS. Freshsegment `cihp-controlled-resources-20261103T062248Z`. [รายงาน](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). NextlaunchTRAIN/newpacketแล้วคิวเดินต่อที่population5000เดิม. Livecleantimingpending

# Controlled CIHP continuation กำลังทำงาน — 2026-11-03T09:12:21.920742+07:00

**CONTINUATION_RUNNING / RPR_EMPTY_OUTPUT_VERIFIED**. QANet/M2FP/D2FPครบ5000และreuseเดิม. Freshsegment `cihp-controlled-continuation-20261103T021021Z` controller2760271/worker2760310ในtmux. ตรวจ09:12:04น.RPR42/5000ภาพ(22parentreused),newVALROIcalls113,failed0/invalid0ในattemptนี้. TRAINparityPASSและภาพ0000312/emptyROI0000312_002ผ่านatomicreadback/label/ownershipแล้ว. Parentfailureคงอยู่. [รายงาน](reports/CIHP_CONTROLLED_ROI_RUN_TH.md)

ดูสถานะด้วย `.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/continue_controlled_cihp.py progress`. Nextcontrollerเดินคิวเดิม5000ต่อโมเดลหลังclosure/resourcegate. วิเคราะห์คุณภาพเมื่อbatchterminal;clean/live timingpending

# Controlled CIHP continuation พร้อมเปิดงาน — 2026-11-03T09:11:08.068227+07:00

**THREE_COMPLETE / CONTINUATION_PREPARED_RPR_GATE_PENDING**. QANet/M2FP/D2FPครบ5000ต่อระบบ. ParentหยุดRPR22frames/149acceptedROIsที่KeyErrorparsing;zero-native-detectiondecoderfixเดิมจากCCTVนำมาใช้ต่อ. CPU5cases×2environmentsPASS,reconciliation149ROIs/22framesPASS,เหลือRPR23913ROIs. [รายงาน](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). Freshsegment `cihp-controlled-continuation-20261103T021021Z`. NextเปิดdetachedcontrollerตรวจTRAIN/packetแรก;ใช้ `continue_controlled_cihp.py progress` ดูสถานะใหม่. ประชากรยัง5000,historyคงครบ,livecleantimingpending

# Controlled CIHP quality batch กำลังทำงาน — 2026-11-02T19:13:53.625503+07:00

**QUALITY_BATCH_RUNNING / QANET_TRAIN_GATE_PASS** — [รายงานรอบปัจจุบัน](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). Run `cihp-controlled-roi-20261102T120403Z` เปิดใน tmux แล้ว controller2144827 / QANetworker2144852. ตรวจเวลา19:13:14น.พบ521/5000ภาพ, failed0/invalid0, packetแรกผ่าน atomic/readback/nativeIDs/ownership/bindings และ source19รายการตรง. คิวโมเดลถัดไปอัตโนมัติหลัง closure/resource gates

ใช้ `.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/controlled_cihp.py progress` จากworkspace rootเพื่อดูจำนวนล่าสุด. snapshotในเอกสารมีเวลาอ้างอิง. Live/clean timingphaseยังpendingแยกจากquality. Next action:ปล่อยcontrollerเดิมเดินคิว ติดตามhealth/completenessและวิเคราะห์รวมหลังbatchterminal

> **Controlled CIHP implementation — 2026-11-02T19:05:31.621985+07:00** CPU acceptance13casesผ่านสองenvironments; frozenqualitymanifest5000frames/24,062ROIs×9พร้อม. GPU TRAINgateยังpendingก่อนVAL. [รายงานรอบใหม่](reports/CIHP_CONTROLLED_ROI_RUN_TH.md). Live/clean speedphaseยังpendingแยกจากqualityqueue

> **Queue/timing requirements — 2026-11-02T18:51:46.168259+07:00** กำหนดsequentialautomaticqueue,model-boundaryreconciliation,health-onlymonitoringและวิเคราะห์หลังbatchterminalแล้ว. [PLAN](PLAN.md#คิวอัตโนมัติและการเก็บเวลาแยกขั้นสำหรับ-controlled-cihp) มีstage-leveltiming,cached/livepipelineboundaries,clean timing proposalและacceptance. Implementation/readinessของcontrolledCIHPยังpending

> **Comparability review — 2026-11-02T18:03:20.041685+07:00:** ตรวจ CIHP กับ CCTV90 และคำนวณ aggregation sensitivity แล้ว: input route, ownership, Face domain และหน่วยเฉลี่ยต่างกัน จึงไม่ใช่การวัดเงื่อนไขเดียวกันข้าม dataset. [รายงานตรวจละเอียด](reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md) · audit 9 systems / 36 targets PASS; ผลเดิมคงเดิม. Controlled CIHP ROI ยังไม่รันและยังไม่ผ่าน readiness.

> **New CCTV work is separate:** [CCTV_Human_Parsing_Benchmark](../CCTV_Human_Parsing_Benchmark/README.md) uses partial-annotation recall diagnostics on90images. CIHP results below remain frozen. No full-image CCTV IoU/instanceF1/overallwinner claim.

# Human Parsing Benchmark — current status

Updated: 2026-10-30T11:11:02.869193+07:00 (Asia/Bangkok)

**COMMON_C4P_COMPLETE_9_OF_9 / ANALYSIS_READY_FOR_REVIEW** — [รายงานผลหลักและ shortlist](reports/CIHP_COMMON_NINE_RESULTS_TH.md).

- Official CIHP Validation exact5,000 unique IDs ต่อระบบ common C4-P revision2 ครบ9/9 checkpoints.
- รอบนี้ CPI R50/ConvNeXt-B ใช้ saved artifacts เท่านั้น ครบตัวละ5,000; missing/duplicate/invalid/failed0. อีก7ระบบreuse accepted canonical common metrics ไม่มีrescoreทั้งชุด.
- Native20ยังครบ6/6และคงผลเดิม; common/global scoresไม่ปะปนกับnative20.
- M2FP_R101_CIHP สูงสุด global IoU ทั้งสี่ targets และ C4-P mean83.623%; QANetสูงสุด Q_C4_GT ทั้งmatching0.50/0.75แต่FPมากกว่า. ShortlistจากCIHP: M2FPหลัก, QANetสำหรับGT-personQ, CPIConvNeXt-Bเป็นtrade-offเพิ่มเติม ไม่ใช่deploymentacceptance.
- Faceใช้CIHP reference; SapiensFace_Neckเป็นproxy, Upper/Lower non-Dress, OTHER/VOIDคงrevision2 ไม่มีmapping/settingsเปลี่ยนจากคะแนน.

[Normalized result index](manifests/CIHP_COMMON_RESULT_INDEX.json) ประกาศcanonicalMETRICS.primaryและlegacycompletionnullเหตุผลโดยไม่แก้historicalcompletion. [Compatibility](runs/cpi-common-c4p-20261030/COMPATIBILITY.json), [parity review](runs/cpi-common-c4p-20261030/PARITY_REVIEW.json), [verification](runs/cpi-common-c4p-20261030/FINAL_VERIFICATION.json), [external artifact references](runs/cpi-common-c4p-20261030/ARTIFACT_MANIFEST.json).

CPIประวัติOOM/recovery/source-revisionmixคงครบ ไม่มีpopulationwidebitwiseequivalenceclaim. CPUscoringสองstreamจบแล้ว ไม่มีnewmodelinference/GPUdiagnostic/training/OOMrepair/color/CCTV ไม่มีcleanlatency/FPS/VRAMranking.

Next action: ส่งรายงานและCSVให้ผู้review แล้วผู้ใช้ตัดสินconfiguration/ขั้นตอนต่อไป ไม่มีautomaticexperimentเพิ่ม. [Previous closure handoff](reports/CIHP_EVALUATION_HANDOFF_TH.md) เป็นsnapshotก่อนCPIcommon.
