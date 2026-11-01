# CCTV90 controlled person-ROI — การเตรียมและสถานะรอบใหม่

อัปเดต 2026-11-01T19:01:06.078883+07:00 (Asia/Bangkok). **RUNNING_PREDICTION_COLLECTION / SCORING_PENDING_GT**; ยังไม่อ้างว่า GPU readiness ผ่านทั้งเก้าระบบ. ผู้ใช้สั่ง “ได้รันใหม่เลย” ต่อจาก [ข้อเสนอหลัก](../CONTROLLED_ROI_PROTOCOL_TH.md). Run `cctv-controlled-roi-20261101T115653Z` ใช้ภาพCCTVเดิม90ภาพ/130frozenYOLOopportunitiesต่อcheckpoint ไม่ใช่ CIHPvalidation5,000.

## ขอบเขตที่ตรึงและเหตุผล

ทั้งเก้า checkpoints เดิมใช้ crop pixels เดียวกัน (box+10%แต่ละข้าง,ขยายครอบmask),losslessPNG,FP32/batch1/noAMP/TF32/externalTTA;native normalization/resolutionของแต่ละfamily. QANetใช้nativebackbone/headบนwhole-crop letterbox ไม่มีnativeROI1.25ซ้ำ;nativeinstanceparsersคงinternaldetectorแล้วเลือกdesignatedinstanceด้วยbboxIoU≥0.50/score/geometry/index ไม่ใช้GT. Finalownership/extents/scoresจากYOLOcacheเดียวกัน;เก็บnativecandidates/rawROI/ownedoriginal-gridplanesแยกกัน. [Frozen public scope](../configs/CONTROLLED_ROI_SCOPE.json).

ScientificbehaviorของoldnativeCIHP/CCTVsource/config/resultsไม่ถูกแก้. ใหม่เป็นcheckpoint+applicationconfigurationcomparison ไม่ใช่architecture-onlyหรือofficialnativebenchmark. ภาพ/GT/per-personmetadata/privatepacketsไม่ขึ้นpublicGit.

**Operational separation:** อนุมัติรันแล้วจึงเก็บGT-independentpredictionsได้ระหว่างที่ทำGTrevision. ห้ามนำpredictionsหรือคะแนนไปสร้างGT. Scoring gateยังคงอยู่: headlineใหม่เป็น`null`จนFace/Neckbindingsและowner/contourQAผ่าน. ไม่ผ่อนGTpolicyเพื่อให้ได้ผู้ชนะเร็วขึ้นและไม่ถือว่าการรันครบเท่ากับGTพร้อม.

## หลักฐานก่อน launch

- ไม่พบactiveCCTV/parserworker; GPUตอนตรวจT4free14,912MiB; diskfreeประมาณ444GiB. Existingtmuxshells/oldGitpushloopคงเดิม ไม่ปิดprocessอื่น.
- CPUacceptance12casesPASSในlegacyparserenvironment รวม literal100Face/25Neck,sharedignore/outsideFP,wrongperson,garmentunion/OTHER,empty/zero-support/null,asymmetricRGB/geometry,QANetnormalization/map-back,losslessPNG,actualpacket→scorer→JSONและmembership. เป็นCPUcontractacceptance ไม่ใช่GPUmodelacceptanceหรือGTexpertcertification.
- อ่านinput/YOLOcacheจริงทั้ง90:exact130opportunities,8zero-detectionframes;checksums/originalgrid/box-scoreorder/losslessdecodedpixelsผ่าน.
- Sapiensทั้งสาม reuse parentROI6ภาพ×15ROIs/ขนาด =45observationsที่ตรวจcheckpoint/nativeconfig/source/input/cropgeometry/extent/score/packetbindingsแล้ว. ไม่เลือกattemptจากscore;population/scoringmetadataต่างกันประกาศexplicitcompatibility.
- Pending1,125ROIAPIcalls +TRAINwarmup9 =maximum1,134compositeROIAPIcalls. Two largest/smallest pendingROIgeometrygatesต่อmodelนับในpendingและreuseต่อเข้าfullpopulation ไม่มีGPUreadinesspassซ้ำทั้งชุด. Internalmodule/featurecallsไม่ใช่APIcounterนี้.
- Resourceplan:sharedcropPNGs7409029bytes;finalrawtwo-labelplanes+extentประมาณ6.901GiBสำหรับเก้าระบบก่อนcompression. ไม่ใช่totaldiskrequirement;nativecandidates/metadata/tempยังต้องวัด. หลัง2geometrygatesมีobservedpacketestimateก่อนดำเนินต่อและguardsระหว่างรัน. ไม่มีETAที่รับรอง.

## GT และคะแนน

แก้sourceownerconflictsสองกรณีในderivedcopyแล้ว โดยrasterizationcv2/int-truncationให้sourceCategory/Humanตรงทุกpixelก่อนแก้;semanticcategorycontourไม่เปลี่ยน. [AggregateGTrevision](CONTROLLED_GT_REVISION.json). Sourceimages/annotations/masksเดิมไม่เปลี่ยน. Groupedpartsหลังแยกowner=Face35/Hair69/Upper120/Lower102 รวม326;ตัวเลขนี้ยังไม่ใช่eligibleprimarydenominator. Remainingowners/contoursยังไม่expert-certified;Neckยังไม่มีannotationแยก.

ดังนั้นใหม่ยังไม่มีคะแนนรวมให้เลือกโมเดล. Targetweights25%เท่ากันและFace-domain/Face+Neckviewsตามข้อเสนอคงเดิม. ต้องสร้างreviewedGTbinding/scoringrevisionแยกก่อนคำนวณผลใหม่ ไม่ใช้ตารางเก่าหรือเติม0แทนnull.

## การรันและตรวจจบ

Controller/workerแยกprocess,oneGPUworker,locksป้องกันซ้ำ,model-specificenvironment/checkpoint/sourcechecksและTRAINwarmup1. ไม่มีretry/CPUfallbackหรือเปลี่ยนprecision/resolution. SharedGPUquality-only;minfree-disk50GiB,stream80GiB/checkpoint,time24h/checkpointและadmissionguardsเดิม. Timing/VRAM observationsเป็นdiagnostics ไม่จัดอันดับspeed/efficiency.

Nativecandidate/ROI/framepacketsเขียนatomicallyพร้อมhash/metadata/readbackและimmutableattemptledger. Model failureหยุดcheckpointนั้น/primarynull;independentcheckpointsดำเนินต่อได้ในfreshprocess;ไม่retryfailedIDs. Externalinterruptionต้องreconcileแยก ไม่restartcontrollerเดิม. ทุกmodelตรวจexact90uniqueframes/130ROIjobsรวมemptyframesและreuse/newcounts;batchหยุดหลังเก้าระบบ ไม่มีtraining/color/CIHP5,000/YOLOinferenceต่อ.

ดูสถานะ:

```bash
python3 CCTV_Human_Parsing_Benchmark/scripts/controlled_roi_progress.py --watch
```

Privateartifacts:`CCTV_Human_Parsing_Benchmark/outputs/cctv-controlled-roi-20261101T115653Z/` มี`CONTROLLER.json`,`CURRENT_WORKER.json`,`<model>/STATE.json`,`<model>.log`,`<model>/ATTEMPTS.jsonl`,`roi_packets/`,`packets/`,`READINESS.json`,`COMPLETION.json`. `BATCH_COMPLETION.json`บอกว่าคิวpredictionจบแล้ว ไม่ได้บอกว่าGT/scoringรับรองแล้ว. Ctrl+Cปิดviewerอย่างเดียว. Launchcommand/commit/sessionบันทึกใน`LAUNCH.json`หลังprelaunchcommit. PublicGitเป็นsnapshot ไม่ใช่liveprogress.

## งานที่เหลือ

1. GPUgateและpredictioncollectionตามscopedcontroller;รายงานfailed/incompleteตามจริง.
2. CompleteGT-onlyowner/contour/Face-Neckreviewโดยไม่ใช้predictionเป็นคำตอบ และmaterializeeligibleitems/domains/denominators.
3. CPUscoreจากnewROIpacketsเมื่อGTbindingรับรองแล้ว;preserveoldresultsและแสดงใหม่เป็นคนละprotocol.

[STATUS](../STATUS.md) / [WORK_LOG](../WORK_LOG.md). Publiccloneไม่มีprivateCCTV/assets/environment จึงreproduceGPUทั้งงานจากcloneอย่างเดียวไม่ได้.

Prelaunch correction: พบ native CPI exporter ใช้ชื่อ`input.png-index.png`เมื่อรับPNG. Adapterใหม่อ่านชื่อตามactualsourceโดยตรง คงPNGdecodedpixelsเดิม;เพิ่มCPUfilename/config-preservationcases รวม12PASS. Preparedparentเก็บครบและมีGPUcalls0;childrunเชื่อมmanifest/cropsเดิมและตรึงsourcehashesใหม่ก่อนlaunch ไม่แก้configเดิมย้อนหลัง.

## Launch acceptance — 2026-11-01T19:01:06.078883+07:00

ControllerPID1353092,SID1353092,PPID1ตรวจแล้ว;workerทำงานแยกและไม่ต้องค้างCodexturn. Launchcommit`12ef1185e7def76d2a1091bf2dcc5d1e972fb5af`เป็นsourcecommitที่รันจริง;commitรายงานภายหลังเป็นdocumentationupdate ไม่ใช่launchrevision. ตรวจatomicoriginal-gridpacketของQANetผ่านnativeIDs/shape/readback/YOLOownership/environmenthash/GT-not-used. QANetครบ90frames/130ROIs,failed0/invalid0ตามcanonicalcompletion. Queueกำลังทำระบบถัดไป ไม่ใช้ผลpartialมาจัดอันดับ. [Sanitized launch snapshot](CONTROLLED_ROI_LAUNCH.json).

Snapshotตารางขณะบันทึก (ไม่ใช่live):

|Checkpoint|Frame packets /90|ROI packets /130|Status|
|---|---:|---:|---|
|QANet_CIHP_HRNetW48_512x384|90|130|PREDICTIONS_COMPLETE_SCORING_PENDING_GT|
|M2FP_R101_CIHP|90|130|PREDICTIONS_COMPLETE_SCORING_PENDING_GT|
|D2FP_R101_CIHP|43|74|ROI_INFERENCE|
|RPR_CIHP|0|0|NOT_STARTED|
|CPI_R50_CIHP|0|0|NOT_STARTED|
|CPI_ConvNeXtB_CIHP|0|0|NOT_STARTED|
|Sapiens2_0.4b|0|0|NOT_STARTED|
|Sapiens2_0.8b|0|0|NOT_STARTED|
|Sapiens2_1b|0|0|NOT_STARTED|

ดูviewer/privateJSONสำหรับสถานะหลังtimestampนี้;publicGitและMarkdownเป็นdatedsnapshots. HeadlineยังnullเพราะGTgate ไม่ใช่ศูนย์หรือผลคุณภาพของโมเดล.
