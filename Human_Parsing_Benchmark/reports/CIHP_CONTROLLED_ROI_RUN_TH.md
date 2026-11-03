# CIHP controlled person-ROI — readiness และการเดินคิว

อัปเดต 2026-11-02T19:05:31.621985+07:00 (Asia/Bangkok) · **CONTINUATION_PREPARED / THREE_SYSTEMS_COMPLETE / RPR_GATE_PENDING**

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
