# CIHP controlled person-ROI — readiness และการเดินคิว

## เตรียมคิว Sapiens1B → CPI ConvNeXt ตามคำสั่งผู้ใช้ — 2026-11-06T17:56:51.856783+07:00

ผู้ใช้ชี้แจงให้พักSapiensก่อนเตรียมคิวและตรวจภาพOOMของCPI แล้วให้Sapiensทำต่อจนจบและต่อCPI. ส่งSIGINTหนึ่งครั้งไปworker3616747ที่ตรวจcmdlineแล้วเมื่อ6พฤศจิกายน17:41:41น.ไทยระหว่างMODEL_CALL_START เพื่อหลีกเลี่ยงpacketwrite;รอprocessออกและGPUว่างก่อนCPUfixtures/GPUdiagnostic. คงทุกpacket/partial/KeyboardInterruptและtimeguardhistory. ไม่ถือว่าoperatorpauseเป็นmodelOOM และไม่ใช้failedcounterใหม่ลบประวัติเก่า

**ReconciliationPASS:** 1Bรวม4222older+46new=4268frames,20101older+255new=20356acceptedROIs. Segmentที่พักมี256attemptedVALcallsแต่committed255ROIs;ไม่นำcallที่ถูกinterruptมาอ้างว่าเป็นpredictionสำเร็จ. ภาพ0036922มี4partialROIsที่ตรวจผ่าน. Pending732frames/3706VALROIs. CPIConvNeXtมี4335frames/20702acceptedROIs,partial0037051สองROIs;pending665frames/3360VALROIs. exact5000/24062ROI membershipsและaccepted/pendingdisjointตรวจจากmanifest/packet/scoreledger/NPZ/hash/input/crop/ownership ไม่ใช้counterอย่างเดียว. ไม่มีinferenceภาพที่ผ่านแล้วซ้ำ

**CPI readiness:** sharednativehead numericCPUfixtures3casesผ่าน;model-boundGPUdiagnosticใช้ConvNeXtcheckpoint/configจริง3callsเท่านั้น:fixedTRAIN ROIด้วยrevision1,TRAINROIเดิมด้วยrevision3 และVAL0037051 ROIindex2ที่เคยOOMหนึ่งครั้ง. TRAINnative selectedmask/allcandidates/boxes/scores/associationตรงกัน;knownOOMprobeผ่านและอ่านnative20packetกลับได้. peakallocated7.429GiB/reserved7.764GiBของprobeเป็นdiagnosticobservation ไม่รับประกันทุกภาพและไม่ใช้จัดspeed/VRAMefficiency ranking. setupแรกจบก่อนmodelconstructionเพราะrelativepathhelper (0modelcalls) แก้pathnormalizationและรักษาหลักฐานแยกไว้ ไม่ใช่OOMretry

ใช้model-localCPI_FEATURE_BRANCH_SCHEDULE_3พร้อมdependenciesCPI_FEATURE_BUFFER_REUSE_2และCPI_PERSON_CHUNK_RESTORATION_1โดยไม่แก้nativefilesบนdisk. Source/weights/nativeconfig/FP32/resolution/batch/TTA/threshold/crop/mapback/YOLO/scorerเดิม. ขอบเขตหลักฐานคือshared-headnumericcontrolsและoneTRAINoutputparity/oneknownOOMprobe;ไม่อ้างbitwiseequivalenceทั้งประชากร. ผลต่อไปเป็นconfigurationที่ประกาศimplementationhistoryชัดเจน:20702parentROIsด้วยrevision1และ3360pendingด้วยrevision3. Diagnosticoutputsไม่รวมcanonical และไม่ใช้คะแนนเลือกsettings

**Queue:** `cihp-sequential-finish-20261106T105503Z` ใช้stdlib-only `scripts/sequential_cihp_queue.py`,รอchildcontrollerจบโดยไม่pollGPU/โหลดโมเดล. ต้องได้ROUND_CLOSUREstrict5000,missing/duplicate/failed/invalid0และBATCH_TERMINALของ1B แล้วcontroller/workerออก ก่อนเปิดCPI. ไม่มีparallelGPUworkers. Viewerอ่านเฉพาะSTATE/CONTROLLERไฟล์เล็กทุก30วินาที. CPUคิว/merge5casesผ่าน รวมduplicate rejectionและpartial/null/running dependencyที่ห้ามเลื่อนคิว. คิวหยุดเมื่อjobใดไม่ครบหรือerror ไม่auto-retry/fallback

Resource amendmentคงแนวทางทำให้ครบโดยไม่หยุดตามwalltime;เก็บเวลาสะสม1B87757.283วินาทีและCPI15590.660วินาที (รวมdiagnostic28.339วินาที) ในfreshconfig ไม่resetcounter. 80GiBstream/50GiBfree/VRAMheadroom/finiteVAL+TRAINbudgetsเดิม. CPUsetup0callที่ไม่มีtimerระบุelapsedunknown ไม่สมมติ0. Canonicalwarmup/parity2TRAINcallsต่อfreshprocessแยกจาก3diagnosticcalls. R50และ7ระบบที่ครบไม่รันใหม่;ไม่มีSAM3/0.8/โมเดลอื่น

หลักฐาน: [Queue](../runs/cihp-sequential-finish-20261106T105503Z/QUEUE_CONFIG.json), [CPI diagnostic](../runs/cihp-sequential-finish-20261106T105503Z/CPI_DIAGNOSTIC_SUMMARY.json), [1B reuse](../runs/cihp-pending-sapiens2_1b-20261106T105013Z/RECONCILIATION.json), [CPI reuse](../runs/cihp-pending-cpi_convnextb_cihp-20261106T105013Z/RECONCILIATION.json). ชุดconfigเต็ม/reusefingerprints/rawlogs/predictionsอยู่privateoutputs. Controllerจะสร้างROUND_CLOSURE.json/SUMMARY_TH.mdและcanonicalMETRICSแต่ละระบบเมื่อจบ;ไม่วิเคราะห์จัดอันดับระหว่างรัน


> **Launch verified 2026-11-06T17:24:11.176769+07:00:** 1Bทำต่อจริงแล้ว ภาพ0036823ประกอบจาก2parentROIs+5newROIsปิดpacket/scoreสำเร็จ;native29,original375H×500W,NPZ/atomicmemberhashes,config/input/checkpointbindings,YOLOextent/scoreparityและownershipclip/scoringlinkผ่าน. Snapshot4223/5000,newVALcalls7,failed0invalid0. [Verification](../runs/cihp-sapiens1b-finish-20261106T101324Z/LAUNCH_VERIFICATION.json). ไม่มีการวิเคราะห์คะแนนระหว่างรัน

## ผู้ใช้สั่งให้ Sapiens1B ทำจนครบ: ยกเลิกเพดานเวลาเฉพาะรุ่น — 2026-11-06T17:16:27.279851+07:00

เปิดdetachedcontrollerเวลา17:19:03น.ไทย ด้วยlaunchcommit `50fd9b9284652ce4763614c26cdccf1c2462363f`;tmux `cihp_1b_finish_20261106T101324Z`, controller3616671/worker3616747. Process SIDอยู่ในtmuxและอยู่ต่อเมื่อSSH/Codexจบturnได้;ไม่มีworkerซ้ำ. เปลี่ยนเฉพาะviewerเก่าที่เป็นwatchให้ชี้runใหม่ ไม่ส่งสัญญาณไปยังbenchmarkworker. ใช้ `tmux attach -t cihp_1b_finish` เพื่อดูprogress window;detachด้วยCtrl+Bแล้วD. TRAINparityผ่านสองcalls และตรวจfirstnewframe0036823ผ่านเมื่อ17:24:11น.ไทย

สถานะ **VALIDATION_RUNNING / FIRST_NEW_PACKET_PASS**, run `cihp-sapiens1b-finish-20261106T101324Z`. คำสั่งปัจจุบันของผู้ใช้ให้เอาข้อจำกัดเวลาออกและทำให้ครบ เป็นresource-policy amendmentที่ชัดเจน ไม่ใช่การปรับโมเดลเพื่อเพิ่มคะแนน. ใช้ตัวควบคุมใหม่ `scripts/finish_controlled_cihp_sapiens1b.py` แยกจากparent/frozenconfigs;ยกเลิกเฉพาะwall-time guardด้วย `execution_time_limit_enabled=false`, `max_hours=null`. เวลาสะสมparent86402.74051067303วินาทีคงอยู่และจะรวมกับเวลาของsegmentใหม่ในROUND_CLOSURE.json

TargetedCPU6casesผ่านก่อนGPU: อนุญาตเวลาสะสมเกิน24hเมื่อamendmentปิดtimeguard;เปิดguardเดิมแล้วยังหยุดที่24h;free disk49GiB/stream81GiB/VRAMต่ำ1GiBยังหยุด;ตรวจsourceเทียบworkerเดิมแล้วเปลี่ยนเพียงเงื่อนไขtimeguard ไม่มีinference/ownership/scoringchanges. ไม่รันfullsuiteหรือGPUdiagnosticเพิ่มเพื่อแก้เรื่องเวลา

Reuseตามกลไกcontinuationเดิม:ตรวจframepacket/score/ledger bindings,NPZ atomic hashes,original-gridownershipและnative29/crop/inputของROIpackets แล้วfreezeaccepted/pendingก่อนlaunch. ตรวจผ่านจริง:4222completeframes/20101parentROIobservations รวม2partialROIsของ0036823;accepted/pendingdisjointและครบ5000frames/24062ROIs;pending778frames/3961VALROIs. Model-callbudgetใหม่3963=3961VAL+2TRAIN. Warmup/parityTRAINสองcallsตามfrozenworkerสำหรับprocessใหม่ แยกจากVALและไม่ใช้คะแนนเลือกsettings. คิวหยุดหลัง1B;CPIConvNeXtและSAM3.1ไม่เปิด

เมื่อlaunchผ่านจะบันทึกconfig/worker/sourcehashes,launchcommit,tmux/PIDsและfirstpacketverificationใน `runs/cihp-sapiens1b-finish-20261106T101324Z/`. Canonicalpredictions/ledgerอยู่privateoutputs. หลังworkerจบตัวครอบจะสร้าง `ROUND_CLOSURE.json` และ `SUMMARY_TH.md` อัตโนมัติ โดยตรวจ5000unique/missing/duplicate/metrics hashและคงSTRICT_COMPLETE;ไม่มีautoretry/fallbackหรือการลบประวัติtimeguardเดิม


## สถานะปัจจุบัน: Sapiens1B หยุดที่เพดานเวลา24ชั่วโมง — 2026-11-06T17:05:51.585401+07:00

**STOPPED_RESOURCE_TIME_GUARD / SEVEN_COMPLETE / TWO_INCOMPLETE.** `Sapiens2_1b` เริ่ม5พฤศจิกายน15:22:22น.ไทย และหยุด6พฤศจิกายน15:22:25น.ไทย หลัง86,402.741วินาที (24ชั่วโมง2.741วินาที). Tracebackใน `outputs/cihp-sapiens-resume-20261105T044738Z/Sapiens2_1b.log` และFAILURE.jsonตรงกันว่า `guard()` ยก `RESOURCE_TIME_GUARD` ก่อนเรียกROIถัดไป;configเดิมกำหนดmax_hours=24และรวมprior_execution_seconds. ไม่ใช่OOMและไม่ใช่การจบครบชุด Controllerบันทึกreturncode1และqueue_stopped=trueเวลา15:22:32น.ไทย

ตรวจprocess/GPU/tmuxเวลา17:03น.ไทย: controller2096828กับworker2375725ไม่อยู่แล้ว,GPUไม่มีcomputePID,tmuxsessionเดิมเหลือหน้าดูสถานะเท่านั้น. ไม่มีworkerทำงานเงียบอยู่และไม่ได้เปิดworkerใหม่

ตรวจsource manifest hashตรงconfigและexpected5,000unique IDs;frame directoriesที่มีCOMMIT.json/packet.json/prediction.npzและscore-file IDsตรงกัน4,222ภาพ ไม่มีIDsนอกmanifest เหลือ778ภาพ. มีROI packet directories20,101รายการ เก็บpartialของภาพ0036823ไว้ด้วย แต่ยังไม่ประกาศว่าpartialทั้งหมดผ่านreuse acceptance. `STATE/COMPLETION`ระบุfailed1,invalid0,primary=null;failed1ในครั้งนี้คือresource-stop ไม่ใช่หลักฐานmodel forwardล้มเหลว ต้องreconcileledger/partialก่อนเปิดcontinuation

การตรวจครั้งนี้เป็นterminal-record/hashและfilename/membership inspection ไม่ได้full rehashNPZ,full rescoreหรือinferenceใหม่. หลักฐานพร้อมhashของterminalrecords: [SAPIENS1B_TIME_GUARD_REVIEW.json](../runs/cihp-sapiens-resume-20261105T044738Z/SAPIENS1B_TIME_GUARD_REVIEW.json). CPIConvNeXtยังคง4,335/nullจากOOMเดิม;อีก7ระบบใช้completionที่ตรวจแล้ว ไม่รันซ้ำ

**การใช้GPUร่วมที่ต้องเปิดเผย:** การเตรียมและทดสอบSAM3.1สำหรับX-AnyLabelingใช้งานT4ร่วมช่วงประมาณ14:09–14:15น.ไทย และปิดเฉพาะSAM3.1เมื่อ14:15:48น.ไทย โดยเก็บlogsใน `SAM3_1_XAnyLabeling/logs/` ของworkspace. ไม่ควรกล่าวว่าไม่กระทบเวลาของbenchmark;ผลกระทบเชิงเหตุและผลยังไม่ได้วัด. เหตุหยุดโดยตรงที่ยืนยันได้คือwall-time guard ไม่ใช่หลักฐานว่าSAM3ทำให้OOMหรือทำให้หยุดทั้งหมด. Timingคงเป็นshared-resource diagnosticsและไม่ใช้จัดspeed ranking

**ขั้นถัดไป:** ต้องรับรองtime-budget amendmentเฉพาะ1Bและทำcontrolled reconciliationก่อนfresh linked continuation;ห้ามresetเวลาเดิมเพื่อหลบcap ห้ามแก้frozen scientific config/precision/resolutionหรือเลือกoutputจากคะแนน. รักษา4,222complete framesกับpartialROIsไว้ ตรวจและreuseเฉพาะส่วนที่ผ่านcontract แล้วทำpendingเท่านั้น. การตรวจสาเหตุครั้งนี้ไม่ได้ขยายresource limitsหรือเปิดCPI/SAM3/modelอื่น

## บันทึกก่อนการหยุดด้วยเพดานเวลา (historical snapshot)

## รันต่อสำเร็จ: Sapiens0.8ครบ และ1Bกำลังทำงาน — 2026-11-05T15:33:58+07:00

**SEVEN_COMPLETE / SAPIENS1B_RUNNING / CONVNEXT_HELD_INCOMPLETE**. ต่อจากreconciliation4182ภาพ/19907ROIs เปิดtmuxเมื่อ5พ.ย.11:51:36ไทยด้วยlaunchcommit`4cf655f111bbea0ecf0a8d97a86c26a2a5e6c2ba` Controller2096828อยู่จริงในsession`cihp_resume_20261105T044738Z`. Sapiens0.8ทำเพิ่ม818ภาพ/4155ROIs จบ15:22:18ไทย ครบexact5000unique/24062ROIs missing0duplicate0 Strictcomplete/METRICShash/assemblyผ่าน;เก็บKeyboardInterrupthistoryเดิม ไม่inference4182ภาพซ้ำ เวลาทำงานรวมparent+segment=19.912ชั่วโมงยังอยู่ในcap24hเดิม

คิวเดิมเริ่มSapiens1B15:22:22ไทย worker2375725;TRAIN2calls/parityPASSและpacketแรก0000001ผ่านNPZ/memberhash/label29/original-grid/ownership/config+checkpoint+protocol/scoring reference. Snapshot17/5000ภาพ ณเวลาตรวจด้านบน failed0invalid0 ไม่ใช่จำนวนล่าสุดตลอดเวลา ผล0.8recovered packet0036736อ่านกลับผ่านด้วย ไม่ตรวจbulk5000ซ้ำและไม่วิเคราะห์คะแนนจัดอันดับระหว่างคิว

[Launch](../runs/cihp-sapiens-resume-20261105T044738Z/LAUNCH.json) · [verification](../runs/cihp-sapiens-resume-20261105T044738Z/LAUNCH_VERIFICATION.json) · [0.8 closure](../runs/cihp-sapiens-resume-20261105T044738Z/SAPIENS08_COMPLETION.json). Fullassembly/reusefingerprintsอยู่privateoutputs คงCPIConvNeXt4335/5000primarynullและOOMhistoryโดยไม่retry ไม่ถือcohort9ตัวcomplete

ดูprogressจากworkspace: `.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/resume_controlled_cihp_sapiens.py progress --config Human_Parsing_Benchmark/outputs/cihp-sapiens-resume-20261105T044738Z/CONFIG.json` หรือ `tmux attach -t cihp_resume_20261105T044738Z` ซึ่งเลือกwindowprogressไว้ `Ctrl+B`แล้ว`D`เพื่อdetach งานเดินต่อ. Logs: `outputs/cihp-sapiens-resume-20261105T044738Z/controller.log` และ `Sapiens2_1b.log`;terminalstatusอยู่CONTROLLER.json/MODEL COMPLETION. คิวหยุดหลัง1Bตามgatesเดิม ไม่มีautomaticCPIretry/ขยาย24h/precisionfallback. Next:ปล่อยworker1Bเดิมทำงานจนterminalแล้วตรวจclosureโดยreuseaudits ไม่เปิดซ้ำ

## บันทึกก่อนการตรวจlaunch/closureครั้งนี้

## Sapiens interruption continuation เตรียมพร้อม — 2026-11-05T11:51:00+07:00

**RECONCILIATION_PASS / PREPARED_FOR_TMUX**. ผู้ใช้สั่งรันต่อหลัง KeyboardInterrupt. Segment `cihp-sapiens-resume-20261105T044738Z` ต่อจาก `cihp-controlled-resources-20261103T062248Z`; parent controller/workerไม่มีprocessแล้วและtmuxเดิมไม่อยู่ ไม่วินิจฉัยว่าเป็นOOM. Reuse6ระบบที่strictcompleteรวมSapiens0.4และCPI_R50 โดยไม่inferenceซ้ำ;CPIConvNeXtยังพัก4,335/5,000/primarynull ไม่เพิ่มเข้าqueue

Sapiens0.8ตรวจผ่าน4,182completeframes/19,907ROIpacketsพร้อมNPZ/COMMIT/memberhashes,geometry/cropRGB/input/checkpoint/config/YOLOownershipและscoreledger เหลือ818frames/4,155ROIs รวมกันexact5,000/24,062โดยไม่ซ้ำ ไม่มีacceptedROIของภาพที่interrupt0036736. Reuseคะแนนรายภาพเดิมผ่านaccumulatorเดิม จึงไม่ต้องrescore4,182ภาพและไม่inferenceใหม่ [compactconfig](../runs/cihp-sapiens-resume-20261105T044738Z/CONTINUATION_SUMMARY.json) / [reconciliation](../runs/cihp-sapiens-resume-20261105T044738Z/RECONCILIATION.json)

Scientific generatedworkerมีhashตรงparentทุกbyte;wrapperใหม่เปลี่ยนเฉพาะinterruptionreconciliation/queueโดยพักConvNeXtและตรวจเฉพาะnative29สำหรับreuseSapiens ตัวตรวจprepจำกัดdecodedcacheหนึ่งภาพ ไม่มีแก้scorer/checkpoint/FP32/resolution/ownership/GT เริ่มprocessใหม่ทำTRAINbaseline/timedparity2callsตามเดิม ไม่มีautoOOMretry/fallback คงเวลา24hและ80GiBต่อstreamรวมparent:0.8ใช้parent16.401hและพื้นที่เดิมแล้ว ไม่resetbudgets

คิวใหม่0.8ส่วนที่ขาด→1Bแล้วหยุด ไม่มีCPIretry. tmuxใช้หน้าต่างcontrollerแยกจากprogressที่เลือกไว้เพื่อดูความคืบหน้า ปิดSSH/detachไม่หยุดworker การกลับมาทำต่อครั้งหน้าอ่านconfig/source/attemptและparentmanifestก่อนเสมอ ไม่เรียกprepareหรือcontrollerซ้ำ. Fullconfig/reusefingerprintsอยู่privateoutputsเพื่อเลี่ยงcommitbulkmetadata;Gitเก็บcompactbindings/คำสั่งและรายงาน

## บันทึกก่อน interruption continuation

## สถานะล่าสุด: ConvNeXt-B OOM และคิวไป Sapiens2 0.4B — 2026-11-04T09:38:00+07:00

**FIVE_COMPLETE / CONVNEXT_STOPPED_INCOMPLETE / SAPIENS04_RUNNING**. ตรวจ controller/PIDs/tmux, terminal records และ log ท้ายไฟล์จริง ไม่เปิด worker หรือ retry เพิ่ม [หลักฐานสรุป](../runs/cihp-controlled-resources-20261103T062248Z/CPI_CONVNEXT_OOM_REVIEW.json)

| ระบบ | สิ่งที่ยืนยันได้ | เวลาไทย |
|---|---|---|
| CPI R50 | STRICT_COMPLETE 5,000/5,000; missing0/duplicate0; metrics hash ตรง completion | จบ 4 พ.ย. 2026 05:06:43 น. |
| CPI ConvNeXt-B | CUDA OOM ภาพ0037051; ครบ4,335/5,000; ยังขาด665ภาพที่ complete; primary=null | หยุด 4 พ.ย. 2026 09:26:09 น. |
| Sapiens2 0.4B | Worker151980ทำงานในtmuxเดิม; snapshot80/5,000, failed0/invalid0 | เริ่ม 4 พ.ย. 2026 09:26:15 น.; จำนวนเป็น snapshot ณเวลาตรวจด้านบน |

OOM ยืนยันจาก `FAILURE.json` และ traceback ใน `cnt_part_parser`/ReLU ของ CPI parsing head: ขอ allocationเพิ่ม2.19GiB ขณะข้อความ error รายงานdevice free2.08GiB, PyTorch allocated9.77GiB/reserved11.12GiB ข้อความนี้ยืนยันว่า allocation ครั้งนั้นล้มเหลว แต่ไม่พิสูจน์ว่าเกิดจาก external process หรือ fragmentation อย่างเดียว ค่า own-reusable-pool ที่ guard ตรวจล่วงหน้าเป็น estimate และไม่ได้รับประกัน allocation ก้อนใหญ่ระหว่าง model peak; ห้ามอ้างว่าผ่านguardแล้วจะไม่OOM

เหตุที่คิวเดินต่อเป็น **policy เดิม** ใน `continue_controlled_cihp.py::controller`: รอ worker เดิมออก ถ้า error_kind เป็น MODEL_OOM ให้เก็บ partial โดยไม่retry แล้วตรวจresourceก่อนcheckpointถัดไป หากเป็น unknown/contract failure จึงหยุดทั้งคิว การเริ่มSapiensไม่ได้แปลว่าConvNeXtเสร็จครบหรือยกเว้นภาพที่ล้มเหลว

นับจากdirectoryที่เขียนเสร็จ: ConvNeXtมี4,335frame packets,4,335score records และ20,702ROI packets เทียบ20,703attemptedVALcalls ส่วนภาพที่ไม่ครบ/partial และfailure historyเก็บไว้เดิม ตัวเลขนี้เป็นการนับdirectoryและอ่านterminalrecords ไม่ใช่fullNPZ/hash/semantic auditใหม่ ไม่มีMETRICSครบชุดของConvNeXtในsegmentนี้และคะแนนหลักยังnullตามSTRICT_COMPLETE

Next:ปล่อยSapiensคิวเดิมทำงาน ไม่ย้อนCPIหรือปรับconfigระหว่างรัน การทำConvNeXtต่อภายหลังต้องreconcile4335complete/partialROI/failed0037051แล้วกำหนดtargetedrepairหรือcontinuationแยก ไม่เริ่ม5000ใหม่และไม่ลดprecision/resolutionเพื่อให้ผ่าน ไม่มีการวิเคราะห์คะแนนจัดอันดับในงานตรวจนี้

## บันทึกก่อนการตรวจครั้งนี้

อัปเดต 2026-11-02T19:05:31.621985+07:00 (Asia/Bangkok) · **FOUR_SYSTEMS_COMPLETE / CPI_RESOURCE_CONTINUATION_RUNNING**

ผู้ใช้อนุมัติให้เริ่มรอบเปรียบเทียบที่ควบคุมinput/ownership และตกลงให้รันcheckpointเดิมเก้าตัวตามคิว เก็บเวลาแยกขั้น และวิเคราะห์คุณภาพรวมเมื่อbatchเข้าสู่terminalstate. รอบนี้ใช้ officialCIHPvalidation5000 IDs กับ frozenYOLOcacheเดิม รวม **24,062 ROIs ต่อcheckpoint**. Run `cihp-controlled-roi-20261102T120403Z` แยกจากnative/commonเดิมและCCTV90

## สิ่งที่เตรียมแล้ว

- [Frozen quality config](../configs/controlled_cihp_quality.json), [run manifest](../runs/cihp-controlled-roi-20261102T120403Z/RUN_MANIFEST.json), [CPU acceptance](CONTROLLED_CIHP_CPU_ACCEPTANCE.json), [entry point](../scripts/controlled_cihp.py)
- คงC4-P revision2 projection/Face proxy/UpperและLower non-Dress,composeก่อนproject,OTHERและsharedVOID,geometry-canonicalmatching0.50/0.75. GTbindingsที่ผูกsourceแล้วให้G_loc17,520/G_sem_C417,454 และGTpartcounts Face16,494/Hair15,803/Upper15,674/Lower10,157. ตัวหารได้จากbindingsและตรวจตอนclosure
- ReuseCCTV `CropModel` และcrop/context10%/losslessRGB/letterbox/nativeconfigsingle-view/prediction-onlyselection/finalYOLOextent. Native20/29integer outputsและrawcandidate planesเก็บทั้งระดับROIและoriginal-grid. FP32/batch1/eval ไม่มีextraTTAตามconfigurationที่ผ่านCCTV. รายละเอียดCPI restoration/feature scheduleคงimplementationที่ผูกไว้
- CPU13literal/integrationcasesผ่านทั้งPython3.9parserlegacyและPython3.12sapiens environments. ActualsavedQANetpacket→scorer→report,perpersoncounts/Qตรงcommon scorerเดิม พร้อมinputhashคงเดิม. ใช้scorerrevision2เดิมที่ผ่านacceptanceสำหรับmatching/ties โดยincrementalcodeใหม่ผ่านกรณีIDrenaming/semanticempty/duplicate/VOID/OTHER/geometry

## คิวและGPU readiness

QANet → M2FP → D2FP → RP-R-CNN → CPI R50 → CPI ConvNeXt-B → Sapiens0.4B → 0.8B → 1B. แต่ละcheckpointใช้freshprocessและmodel-localoutput. ก่อนVALของแต่ละตัวตรวจweights hash/nativeconfig/sourcecommit,environmentและresourceguards แล้วทำTRAIN0000930 personROIสองcallsหนึ่งครั้ง ได้แก่baselineadapterและtimedadapter. Nativehardmasksและcandidateplanesต้องตรงกันจึงผ่าน พร้อมatomicpacketreadback/storageestimate. TRAINcallsแยกจากVALและงบรวม **216,576 model-ROI API calls สูงสุด** สำหรับqualityรวมwarmup โดยภายในAPIอาจมีหลายnetworkoperations

Model/OOMretries0. confirmedmodelOOMเก็บpartial/nullแล้วคิวอิสระถัดไปตรวจresourceใหม่ ส่วนunknown/contract/sharedbindingfailureหยุดเพื่อreconciliation. resourcewaitมีเพดาน600วินาทีแยกจากexecution หากไม่ผ่านจะหยุดQUEUE_RESOURCEเพื่อกลับมาตรวจต่อ. ต่อcheckpointคง80GiB/24hและfree-spaceguard50GiB. 200GiBเป็นplanningenvelope. ขนาดfinalarraysก่อนcompressionประมาณ106.05GiBรวมเก้าระบบยังไม่รวมnativecandidates/crops/logs/temp จึงใช้TRAINestimateพร้อมguardsต่อไป ไม่รับรองtotalstorageจากrawarraysเพียงค่าเดียว

## Metrics และเวลา

GlobalC4-P mIoU4/per-targetIoU/Precision/Recall/F1-Dice/confusion/support, C3global และpersonTP/FP/FN/F1/Q_C4_GTที่0.50/0.75. เพิ่มmeanGT-person-partIoUและpooledperson-partIoUโดยใช้GTclasseligibility/validdomainร่วม,missedpersonpart=0. MatchingของCIHPใช้fullGTpersonmask ส่วนCCTVpartialGTใช้unionboxcoverage จึงยังต้องอธิบายความต่างของGT/denominatorข้ามdataset

เก็บsynchronizedadapterspans/ROIpreparation/ownership/export+readback/scoringและmeasuredcached-routewallต่อภาพ. QANet/Sapiensมีpreprocess/model/mapbackspans; nativeinstanceAPIที่รวมdetector/decoder/fileI/Oใช้inclusiveชื่อชัด transferหรือinternalI/Oที่แยกไม่ได้มีmissingreason. Nestedspansไม่บวกซ้ำเป็นpipeline. Forwardคำนวณnativeclassesทั้งหมดแล้วproject4targets ไม่มีforwardtimeรายclass

**สถานะความเร็ว** qualitypassให้cached-route/resource diagnostics. LiveYOLOend-to-end,isolatedtransfer/internalstageinstrumentationและclean100frame×3roundtimingยังpendingimplementation/readinessตาม[PLAN](../PLAN.md). คุณภาพเริ่มได้เมื่อTRAINgateผ่าน โดยreportไม่ใช้diagnosticนี้จัดspeedranking. เก็บartifactsให้ตรวจย้อนหลังได้

## การเปิดงานและตรวจสถานะ

ใช้tmuxdetachedsessionเฉพาะrunนี้ ให้controllerเปิดworkerตามคิว. Launchcommit/session/PIDsอยู่ `runs/cihp-controlled-roi-20261102T120403Z/LAUNCH.json` และprivate `outputs/cihp-controlled-roi-20261102T120403Z/CONTROLLER.json`. เปิด controller เมื่อ 2 พฤศจิกายน 2026 เวลา 19:06:08 น. (Asia/Bangkok) ด้วย launch commit `371910efd8903426f05e19a376644fb4d6909a38` แล้ว QANet ผ่าน TRAIN parity สอง calls และเริ่ม VAL จริง. ตรวจปิดขั้นเปิดงานเวลา 19:13:14 น. พบผล 521/5,000 ภาพ ณ snapshot โดย failed/invalid เป็นศูนย์. โมเดลถัดไปยังอยู่ในคิว

จากworkspace root ใช้คำสั่งดูสถานะ

```bash
.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/controlled_cihp.py progress
```

Private logsและpacketsอยู่ `Human_Parsing_Benchmark/outputs/cihp-controlled-roi-20261102T120403Z/`. แต่ละmodelมี `STATE.json`, `READINESS.json`, `ATTEMPTS.jsonl`, `packets/`, `roi_packets/`, `scores/` และ `COMPLETION.json`. canonical `METRICS.json`เกิดหลังexactmembership/ROIcounts/GTdenominatorsและsourcebindingsผ่านเท่านั้น primarynullเมื่อไม่ครบ. `CONTROLLER.json`บอกstatus/workerPID/currentmodel/terminalqueue. ปิดSSHหรือviewerคงcontrollerในtmux

การวิเคราะห์winnerทำเมื่อbatchterminal. ผลรอบนี้เป็นcheckpoint+controlledapplicationconfigurationบนCIHP reference Faceproxy. รายงานตรวจความเทียบกันได้เดิมยังใช้ประกอบ[CIHP/CCTV review](CIHP_CCTV_COMPARABILITY_REVIEW_TH.md)

## ตรวจการทำงานต่อหลังบทสนทนาหยุด

ตรวจ process และ tmux แล้ว controller PID **2144827** กับ QANet worker PID **2144852** ยังทำงานภายใต้ session `cihp_controlled_20261102T120403Z`. ตรวจ packet แรกของ VAL `0000001` สำเร็จ ทั้ง atomic member hashes, NPZ readback, original grid375H×500W,4person planes, nativeCIHP labelIDs และ identity/config/input/checkpoint/protocol/detector bindings. Owned masks ตรงกับ raw native masks ที่ clip ด้วย frozen YOLO extents. ตรวจ source bindings19รายการตรง frozenconfig

ผลตรวจ TRAIN เทียบ adapter เดิมกับ adapter ที่เพิ่ม timing ให้ native hard masks/candidate planes เหมือนกันใน TRAIN ROI ที่ตรวจ. หลักฐานนี้ครอบคลุม readiness ตัวอย่างดังกล่าว ส่วนโมเดลอื่นต้องผ่าน gate ของตนก่อนเข้า VAL. [Launch verification](../runs/cihp-controlled-roi-20261102T120403Z/LAUNCH_VERIFICATION.json) และ [launch provenance](../runs/cihp-controlled-roi-20261102T120403Z/LAUNCH.json) เก็บเวลา/PID/config hash/ผลตรวจตามจริง

รอบคุณภาพกำลังบันทึก cached-route wall และ adapter spans. ขั้น liveYOLO joint-residency / clean timing100frames×3rounds และบางช่วง transfer/internal API ยังต้องพัฒนาและตรวจรับแยก. ข้อมูลเวลาใน quality pass มีขอบเขตตามที่ระบุใน metadata

ขั้นถัดไปของ batch คือให้ QANet รันจนตรวจปิดผล แล้ว controller ตรวจทรัพยากรและเปิด M2FP ต่ออัตโนมัติ หากมี error ให้ใช้ terminal status และ FAILURE.json ประกอบการ reconciliation ตาม policy. รายงานคุณภาพ/อันดับรวมจัดทำหลัง batch terminal

## Controlled continuation หลัง RP-R-CNN คืน native instances ว่าง

อัปเดต 2026-11-03T09:11:08.068227+07:00. ผู้ใช้อนุมัติให้แก้และรันต่อ โดยยังประเมินประชากรเดิม **5,000 IDs ต่อโมเดล**. การสนทนาเรื่อง subset2,500 ยังเป็นทางเลือกและไม่ได้เปลี่ยน population

Parent `cihp-controlled-roi-20261102T120403Z` หยุดตามpolicyที่ RP-R-CNN ภาพ0000312 หลังครบ22ภาพ/149ROIpacketsและattempted150VALcalls. Tracebackเป็นKeyError('parsing'). ตรวจupstream `rcnn/core/test.py` พบว่าทางเดินzero-native-detectionsคืนemptyBoxListได้โดยไม่มีfieldparsing. Frozenadapterพยายามอ่านfieldนั้น. เคยปิดปัญหาประเภทเดียวกันในCCTVแล้ว จึงreuse `continuation_model`/`empty_rpr_prediction` จาก `CCTV_Human_Parsing_Benchmark/scripts/controlled_roi_continuation.py` revision `RPR_ROI_EMPTY_OUTPUT_1`

การแก้เปลี่ยนเฉพาะdecoderของemptyresult. หากnativecount0ส่งcandidatearrayว่างและnativecropmaskเป็นbackground โดยเก็บYOLOextent/identityเดิม. ValidGTtargetsที่ไม่มีpredictionยังเป็นFNและQcontribution0ตามscorer. Nativecountมากกว่า0แต่ขาดfieldparsingยังเป็นcontractfailure. Threshold/checkpoint/FP32/crop/context/TTA/ownership/GT/projection/matching/scorerคงเดิม

Continuation `cihp-controlled-continuation-20261103T021021Z` ใช้freshconfig/outputและworker snapshotจาก11exactsource substitutionsบนfrozenrunner. [Config](../configs/controlled_cihp_continuation.json), [CPU acceptance](CONTROLLED_CIHP_CONTINUATION_ACCEPTANCE.json), [reconciliation](../runs/cihp-controlled-continuation-20261103T021021Z/RECONCILIATION.json), [reviewable worker](../runs/cihp-controlled-continuation-20261103T021021Z/WORKER_REVISION2.py)

| รายการ | การนำกลับมาใช้ |
|---|---|
| QANet / M2FP / D2FP | canonicalcompletionครบ5,000ภาพต่อระบบ ตรวจstrictcompleteและmetricshashแล้ว ใช้ผลเดิม |
| RP-R-CNN completeframes | 22ภาพ ตรวจatomicmembers/NPZ/input/config/checkpoint/YOLOextent/scores/scoreledgerhashesแล้ว |
| RP-R-CNN acceptedROIpackets | 149รายการตรวจnativeIDs/geometry/decodedcroppixelhashและmetadata รวม2ROIsในpartialframe0000312 |
| RP-R-CNN pending | 23,913ROIs;มีหนึ่งfailedattemptเดิมเก็บไว้ การแก้ครั้งนี้อนุญาตattemptใหม่หนึ่งครั้งต่อpendingROI |
| CPIสองตัว/Sapiensสามตัว | ยังไม่เคยเริ่มcontrolledCIHPparent จึงเข้าคิวต่อหลังRP-R-CNNตามreadinessเดิม |

CPU5regressioncasesผ่านในสองenvironments ครอบemptydecoder/nonemptymalformed/boundedpendingbudget/atomicimmutability/literal scoreaccumulation. GPUreadinessจะใช้TRAINสองcallsเพื่อเทียบnonemptybaselineกับfixedinstrumentedpathก่อนcanonicalpending. ภาพ0000312คงอยู่ตามpopulationและประเมินตามจริงเมื่อรันต่อผ่าน ยังไม่อ้างpopulation-widebitwiseforwardequivalenceจากTRAINตัวอย่างเดียว

RP-R-CNN model-callaccountingรวมfailedattemptเดิม150VAL+2TRAIN, continuationสูงสุด23,913VAL+2TRAIN รวม24,067calls. เก็บimmutableattempthistoryทั้งparent/continuation. Guard24h/80GiBคิดรวมprioractiveexecution/streambytes ไม่รวมช่วงข้ามคืนที่controllerหยุด. Resourcequeue600s/50GiBfreeheadroomคงเดิม. Automaticretry0 ไม่มีการลดprecision/resolutionหรือเลือกattemptตามคะแนน

Scorerรับacceptedparentframesและnewframesรวมexact5,000uniqueIDsผ่านaccumulatorเดิม พร้อมตรวจROIcount149+new23,913และGTdenominatorsจากbindings. `ASSEMBLED_INDEX.json`เชื่อมparent22framesกับnewpacketroot และระบุacceptedROIcountsต่อimplementationrevision. Mainmetricsยังnullหากไม่ครบหรือcontractไม่ผ่าน การใช้parent/currentimplementationผสมเปิดเผยในmanifest

Timingของ22parentframesยังอ้างparentledger. ภาพpartialที่reuse2ROIsมีadapterspansจากparentกำกับorigin และcurrentframewallไม่รวมforwardเก่า ต้องแยกattemptwall/activeworkจากfulluninterruptedframelatencyในการรายงานภายหลัง. Live/clean timingphaseยังpendingตามแผนเดิม

คำสั่งดูสถานะcontinuationจากworkspace root

```bash
.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/continue_controlled_cihp.py progress
```

งานถัดไปคือเปิดdetachedcontinuationหลังcommit ตรวจTRAIN/firstnewpacket แล้วให้controllerเดินคิวเดิม. ประเมินอันดับเมื่อbatchterminalตามที่ตกลง

### ตรวจเปิด continuation แล้ว

เปิด 3 พฤศจิกายน 2026 เวลา **09:11:17 น.** (Asia/Bangkok), launchcommit `66c6a5b05b3c926deb3cb276cb75e9eb8cf91ca1`, tmuxsession `cihp_cont_20261103T021021Z`. Controller PID **2760271**, RP-R-CNN worker PID **2760310**. ตรวจเวลา09:12:04น.พบรวม **42/5,000ภาพ** โดย22ภาพเป็นparentreused, newVALROIcalls113,failed/invalid0สำหรับattemptนี้. ประวัติparentfailedattemptยังอยู่

TRAINสองcallsผ่านoriginal-vs-instrumented hard-mask/candidateparity. อ่านpacketใหม่ภาพ0000312และROI0000312_002กลับพร้อมhash/atomicmembers/ownershipผ่าน. ROIที่เคยล้มให้nativepersoncount0จริง, candidatecount0 และsemanticmaskว่าง โดยคงYOLOextentไว้และไม่ได้ใช้GTช่วยสร้างprediction. กรณีนี้จะถูกscorerคิดFN/Qตามนิยามเดิม ไม่เพิ่มignoreหรือแทนsilhouette

[Launch](../runs/cihp-controlled-continuation-20261103T021021Z/LAUNCH.json) / [verification](../runs/cihp-controlled-continuation-20261103T021021Z/LAUNCH_VERIFICATION.json) เก็บbindingsและsnapshotที่ตรวจ. Nextให้controllerเดินRP-R-CNNและโมเดลที่ยังไม่เริ่มต่อ เฝ้าตรวจhealth/contract/completenessตามpolicyโดยไม่วิเคราะห์อันดับระหว่างรัน. Live/clean timingยังเป็นขั้นถัดไปตามแผน

## Resource continuation หลัง CPI R50 headroom guard

อัปเดต 2026-11-03T13:24:44.856361+07:00. Parentcontinuation `cihp-controlled-continuation-20261103T021021Z` ปิดRP-R-CNNครบ5000เมื่อ3พ.ย.11:19น. ต่อมาCPI R50หยุด11:20น.หลัง4completeframes/34acceptedROIpackets ด้วย `RESOURCE_VRAM_HEADROOM_GUARD` ก่อนเริ่มforwardถัดไปที่ภาพ0000027. ไม่มีCUDA-OOMtracebackในattemptนี้. Lastsuccessfulcallบันทึกpeakallocated10729.631MiB/peakreserved12794MiB ตัวเลขpeakสองค่านี้อาจเกิดต่างขณะ จึงห้ามนำมาลบเพื่ออ้างowncachedpoolณจุดguardเดิม; guardเดิมไม่ได้เก็บcurrentallocated/reserved/freeที่จุดหยุด จึงยังไม่ยืนยันcacheamountย้อนหลัง

แก้เฉพาะresourceaccountingในfreshworker/config ใช้ฟังก์ชัน`reusable_memory`ที่ผ่านCCTVcontinuationเดิม: effectiveavailable=devicefree+ownreserved−ownallocated. ไม่รวมliveallocatedหรือcacheของprocessอื่น. เกณฑ์headroomยัง1024MiB,preloadguardsเดิม,FP32/batch1/resolution/TTA/threshold/crop/ownership/scorerเดิม. ไม่เรียกempty_cacheหรือเปลี่ยนallocator/systemsettings. บันทึกcurrentguardmemoryในSTATEเพื่อให้ตรวจoperationalamendmentรอบนี้ได้จริง ไม่รับประกันcontiguousallocationหรือว่าไม่OOMในภาพถัดไป

[Resource config](../configs/controlled_cihp_resources.json), [CPU acceptance](CONTROLLED_CIHP_RESOURCE_ACCEPTANCE.json), [reconciliation](../runs/cihp-controlled-resources-20261103T062248Z/RECONCILIATION.json), [worker snapshot](../runs/cihp-controlled-resources-20261103T062248Z/WORKER_REVISION2.py). ใช้sourcegeneration12exactsubstitutionsโดยreusefrozenrunner/continuationเดิมและเพิ่มresourceguardหนึ่งจุด. Originalsource/config/attemptsคงครบ

| รายการ | สถานะก่อนเปิด segment |
|---|---|
| QANet/M2FP/D2FP/RP-R-CNN | strictcomplete5000ต่อระบบ ใช้canonicalreferencesและcompletion/metricshashesเดิม |
| CPI R50 accepted | 4frames/34ROIsตรวจatomicmembers/NPZ/nativeIDs/geometry/decodedpixelhash/YOLOownership/scoreledgerhashesแล้ว |
| Partialframe0000027 | 3ROIsaccepted;restpending |
| CPI R50 newpending | 24,028ROIs +2TRAINreadinesscallsสูงสุด |
| อื่น | CPIConvNeXt-B/Sapiens0.4B/0.8B/1Bยังไม่เริ่ม เข้าqueueต่อเมื่อmodelgateผ่าน |

CPIcallaccountingคิดparent34VAL+2TRAIN และsegmentใหม่สูงสุด24028VAL+2TRAIN รวม24066calls. Parentstopเป็นresourceguardก่อนforward ไม่มีการนับstopนั้นเป็นCUDA-OOMหรือsuccessfulprediction. Stream80GiB/active24hคิดรวมparent+continuation;free-disk50GiB/queue600sคงเดิม. การเพิ่มownreusablepoolเป็นoperationalresourceamendmentพร้อมหลักฐานก่อนlaunch. ไม่มีautomaticmodel/OOMretry/fallback

CPU4cases×2envผ่าน ได้แก่owncacheincluded/liveallocatedexcluded/byte-unitthreshold/sourceguardcomposition. ModelscientificbehaviorคงเดิมและTRAINparityเป็นruntimegate. เป้าหมายยัง5000IDsต่อโมเดล,STRICT_COMPLETE/GTdenominatorchecksและการวิเคราะห์หลังbatchterminalคงเดิม. Live/cleantimingยังpendingแยก

ดูสถานะ segment ปัจจุบันจากworkspace root

```bash
.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/continue_controlled_cihp_resources.py progress
```

Nextcommitแล้วเปิดdetachedcontrollerและตรวจnewpacketของภาพ0000027 พร้อมcurrentmemoryguardobservations

### Resource continuation เปิดและตรวจ packet ใหม่แล้ว

Launch3พ.ย.2026 **13:24:57น.**(Asia/Bangkok), commit`1a67a3ac4d6280e05989f4c4e945834e017c947f`,tmux`cihp_resources_20261103T062248Z`,controllerPID**3034452**,CPI R50workerPID**3034473**. ตรวจเวลา2026-11-03T13:26:47.345448+07:00พบCPIรวม**14/5000ภาพ** (4parentreused),newVALROIcalls54,failed/invalid0ในattemptนี้. TRAIN2callsparityPASS. Packetใหม่0000027ที่parentเคยหยุดผ่านNPZ/memberhashes/config/ownershipreadback

Currentguardobservationsที่ตรวจมีdevicefree818.8MiB,ownallocated180.6MiB,ownreserved12698.0MiB และeffectiveavailable13336.1MiB. ตัวเลขเป็นcurrentoperationalguardหนึ่งขณะ ไม่ใช่peakVRAMหรือหลักฐานว่าparentstopมีcacheเท่ากัน ไม่รับรองทุกROIถัดไปผ่าน. [Launch](../runs/cihp-controlled-resources-20261103T062248Z/LAUNCH.json) / [verification](../runs/cihp-controlled-resources-20261103T062248Z/LAUNCH_VERIFICATION.json)

Controllerใช้ผล4โมเดลที่ครบแล้วตามreferencesและคิวเหลือCPI R50→ConvNeXt-B→Sapiens0.4/0.8/1Bตามresourceและreadinessgatesเดิม. ขั้นถัดไปปล่อยdetachedqueueทำงานและตรวจcompleteness/healthโดยวิเคราะห์rankเมื่อterminal. Live/clean timingpending
