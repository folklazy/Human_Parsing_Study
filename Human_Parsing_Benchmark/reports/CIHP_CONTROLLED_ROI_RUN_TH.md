# CIHP controlled person-ROI — readiness และการเดินคิว

อัปเดต 2026-11-02T19:05:31.621985+07:00 (Asia/Bangkok) · **CPU_ACCEPTED / GPU_TRAIN_GATE_PENDING**

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

ใช้tmuxdetachedsessionเฉพาะrunนี้ ให้controllerเปิดworkerตามคิว. Launchcommit/session/PIDsอยู่ `runs/cihp-controlled-roi-20261102T120403Z/LAUNCH.json` และprivate `outputs/cihp-controlled-roi-20261102T120403Z/CONTROLLER.json`. ขั้นถัดไปหลังcommitคือเปิดcontrollerและตรวจTRAINgate/packetVALแรก

จากworkspace root ใช้คำสั่งดูสถานะ

```bash
.venvs/sapiens2-pilot/bin/python Human_Parsing_Benchmark/scripts/controlled_cihp.py progress
```

Private logsและpacketsอยู่ `Human_Parsing_Benchmark/outputs/cihp-controlled-roi-20261102T120403Z/`. แต่ละmodelมี `STATE.json`, `READINESS.json`, `ATTEMPTS.jsonl`, `packets/`, `roi_packets/`, `scores/` และ `COMPLETION.json`. canonical `METRICS.json`เกิดหลังexactmembership/ROIcounts/GTdenominatorsและsourcebindingsผ่านเท่านั้น primarynullเมื่อไม่ครบ. `CONTROLLER.json`บอกstatus/workerPID/currentmodel/terminalqueue. ปิดSSHหรือviewerคงcontrollerในtmux

การวิเคราะห์winnerทำเมื่อbatchterminal. ผลรอบนี้เป็นcheckpoint+controlledapplicationconfigurationบนCIHP reference Faceproxy. รายงานตรวจความเทียบกันได้เดิมยังใช้ประกอบ[CIHP/CCTV review](CIHP_CCTV_COMPARABILITY_REVIEW_TH.md)
