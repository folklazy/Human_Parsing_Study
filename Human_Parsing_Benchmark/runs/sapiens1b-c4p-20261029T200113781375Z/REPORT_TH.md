# Sapiens2 segmentation 1B — CIHP C4-P

อัปเดต 2026-10-30T10:03:08.892100+07:00 · run `sapiens1b-c4p-20261029T200113781375Z` · **COMPLETE**

## สถานะและขอบเขต

|ระบบ|สถานะ|Complete/5,000|
|---|---|---:|
|Sapiens2 0.4B (รอบเดิม)|COMPLETE|5000/5000|
|Sapiens2 1B|COMPLETE|5000/5000|

Pilot1B 6/6; model-frame callsรวม 5001; warmup 1; reused 6; queue 0.0s แยกจาก execution 24928.8s. ค่า complete ของ1Bนับ canonical หลัง pilot ผ่าน/manifestfreezeเท่านั้น. ทั้งสองค่าเวลานี้เป็น operational accounting ไม่ใช่ speed ranking

ผู้ใช้อนุมัติ pilotหนึ่งTRAINwarmup+6fixedVAL แล้ว full validation5,000 เมื่อผ่าน โดยไม่ถามซ้ำ; รันเดี่ยวบน GPU (tmux) หลัง CPI เสร็จ; admissionเดิมยังตรวจก่อนทุกภาพ. รอคิวสูงสุด24hแยกจากexecution24h,stream80GiB/free50GiBเดิม. ไม่มี5B/CPI/training/color/YOLO inference และไม่คำนวณ common view สี่โมเดลเดิมซ้ำ

## Identity และ protocol

Checkpoint `models/human_parsing/sapiens2/1b/sapiens2_1b_seg.safetensors` SHA256 `4b73c44963b377e93fcb4c4053f72a189836a22d05e12c30383046b9cd3c5bd4`; nativeconfig `third_party/human_parsing/sapiens2/sapiens/dense/configs/seg/shutterstock_goliath/sapiens2_1b_seg_shutterstock_goliath-1024x768.py` SHA256 `d33d8802741cb7b0cddc09ac3b2f780a801932bdeb88dc097c22a43996fef61d`; source `7e5bae88456ac418ff0e58e74106c9fe192055d4`. Strict model loadingและ1,470,819,805parameters/native29headตรวจในworkerก่อนforward ไม่ใช้ binding/weights0.4B. Environment `.venvs/sapiens2-pilot` versions/hashของรอบนี้บันทึกแยก

[Pilot config](../../configs/cihp_sapiens_1b_pilot.json), [readiness](READINESS.json), [resource readiness](RESOURCE_READINESS.json). Full config/compatibilityจะสร้างหลังpilotผ่านโดย scientific identityเดิม ไม่แก้ fingerprintย้อนหลังและไม่เลือก predictions จากคะแนน

ใช้ C4-P revision2 SHA256 `7fb101672407d465885efcc00202af927e93cd422daeae42bf215cbe504cd33d` เหมือน0.4B: full-frame semantic29/1024×768/FP32/batch1/eval/inference/noAMP/TF32/extraTTA; native logits map-backก่อนargmax แล้ว frozenYOLOmaskownership; compose nativeก่อนproject. BG/OTHER valid,GT255 sharedVOID,predictionunknown/255fail. Face proxyไม่ใช่strictface-only; Upper/Lower non-Dress; Dress/ApparelOTHER ไม่splitด้วยgeometry. G_loc=17,520/G_sem_C4=17,454 จากexact GTmanifest; geometry-canonical matching0.50/0.75,C3global-only,noQ_C3

## ผลคุณภาพ

**C4-P mIoU4 = 72.759%**; ไม่ใช้คะแนน subset แทนชุดเต็ม. ตาราง IoU เป็นเปอร์เซ็นต์ JSONเก็บfraction0–1

|Target|IoU (%)|GT support|Prediction support|Union|
|---|---:|---:|---:|---:|
|Face proxy|70.175|37932488|41173601|46485085|
|Hair|77.427|40760850|36278027|43419971|
|Upper non-Dress|71.778|148199276|138365260|166822127|
|Lower non-Dress|71.657|38702345|33442478|42028557|


Person Q_C4_GT/TP/FP/FN/precision/recall/extentF1/contamination/denominators และnativeGT×prediction discordanceอยู่ใน canonical METRICSเมื่อครบเท่านั้น. Qไม่ลงโทษunmatchedpredictionsโดยตรงจึงต้องอ่านFP/F1ร่วม ไม่อ้างoverallwinnerจากQตัวเดียว; extents/IDsมาจากYOLOไม่ใช่nativeinstancecapability. ไม่รวมnative20 tableกับcommon4 scores

## Artifacts, checks และข้อจำกัด

Raw root `Human_Parsing_Benchmark/outputs/common_view/sapiens1b-c4p-20261029T200113781375Z` เก็บ ENVIRONMENT/LAUNCH/STATE/EXECUTION/QUEUE/resource observations, pilot/full native29original-grid NPZ,per-person planes/extents/confidences/geometry,atomicCOMMITและscorehashes. Pilot6ภาพIDsตามที่กำหนด ไม่เลือกตามคะแนน; privategalleryสร้างจากsavedmasks. Fullmanifestreused/pendingต้องdisjointและครบ5,000unique;ไม่ครบmainnull,เก็บfailure/partial/orphanโดยไม่retry/fallbackหรือลดsettings. ข้อมูลภาพ/dataset/weights/bulkoutputsไม่ขึ้นGit

Common scorer/packet/routeที่ผ่านCPU acceptanceเดิมใช้ต่อเมื่อhashesตรง ไม่รันfulltest suiteซ้ำ. ตรวจเพิ่มเฉพาะ1Bcheckpoint/hash/native29header/source/configpipeline/eval strictload,resource-admissionfixturesและ7modelcallsตามpilotbudget. Resource admissionใช้observed0.4peak+historical1Bpeak(T4 native FP32 TRAIN pilot)+largestpopulationmapback+context/growth/headroom+หลายsnapshot ไม่ตัดสินจากutilizationหรือfreeVRAMจุดเดียว; empirical budgetไม่รับรองทุกภาพ. Queue/exec clocks/resourcecapsมีledgerแยก

ไม่มีclean latency/FPS/VRAM-efficiency ranking, architecture-only causality หรือCCTV/สีข้อยืนยัน. ไม่เปลี่ยนmapping/settingsตามpilot/fullscores. ปัญหาเฉพาะ1Bหยุดเฉพาะstreamนี้ เก็บหลักฐาน ไม่แก้ผล0.4B/0.8B. [ผล0.4Bและสี่โมเดลเดิม](../../reports/CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md) และ[ผล0.8B](../../reports/CIHP_SAPIENS_08B_C4P_RESULTS_TH.md) เป็นรายงานแยก ไม่รันซ้ำ
