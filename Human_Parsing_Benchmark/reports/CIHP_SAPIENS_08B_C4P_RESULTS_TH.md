# Sapiens2 segmentation 0.8B — CIHP C4-P

อัปเดต 2026-10-29T15:17:20.281451+07:00 · run `sapiens08-c4p-20261029T081254180014Z` · **FULL_READY**

## สถานะและขอบเขต

|ระบบ|สถานะ|Complete/5,000|
|---|---|---:|
|Sapiens2 0.4B (รอบเดิม)|INFERENCE|3357/5000|
|Sapiens2 0.8B|FULL_READY|6/5000|

Pilot0.8B 6/6; model-frame callsรวม 7; warmup 1; reused 6; queue 0.0s แยกจาก execution 148.9s. ค่า complete ของ0.8Bนับ canonical หลัง pilot ผ่าน/manifestfreezeเท่านั้น. ทั้งสองค่าเวลานี้เป็น operational accounting ไม่ใช่ speed ranking

ผู้ใช้อนุมัติ pilotหนึ่งTRAINwarmup+6fixedVAL แล้ว full validation5,000 เมื่อผ่าน โดยไม่ถามซ้ำ; shared-GPU quality-only พร้อม0.4Bได้เมื่อadmissionผ่าน มิฉะนั้นqueueไม่หยุด0.4B. รอคิวสูงสุด24hแยกจากexecution24h,stream80GiB/free50GiBเดิม. ไม่มี1B/CPI/training/color/YOLO inference และไม่คำนวณ common view สี่โมเดลเดิมซ้ำ

## Identity และ protocol

Checkpoint `models/human_parsing/sapiens2/0.8b/sapiens2_0.8b_seg.safetensors` SHA256 `e7c1655b7e11678ba200d4ce743be13aeb97eb5ce0a0907f8e6817aabe6b2eec`; nativeconfig `third_party/human_parsing/sapiens2/sapiens/dense/configs/seg/shutterstock_goliath/sapiens2_0.8b_seg_shutterstock_goliath-1024x768.py` SHA256 `967f27e2a596da57cb87598412197138eb73674d4e83c12ccab73e41c0df738a`; source `7e5bae88456ac418ff0e58e74106c9fe192055d4`. Strict model loadingและ827,531,997parameters/native29headตรวจในworkerก่อนforward ไม่ใช้ binding/weights0.4B. Environment `.venvs/sapiens2-pilot` versions/hashของรอบนี้บันทึกแยก

[Pilot config](../configs/cihp_sapiens_08b_pilot.json), [readiness](../runs/sapiens08-c4p-20261029T081254180014Z/READINESS.json), [resource readiness](../runs/sapiens08-c4p-20261029T081254180014Z/RESOURCE_READINESS.json). Full config/compatibilityจะสร้างหลังpilotผ่านโดย scientific identityเดิม ไม่แก้ fingerprintย้อนหลังและไม่เลือก predictions จากคะแนน

ใช้ C4-P revision2 SHA256 `7fb101672407d465885efcc00202af927e93cd422daeae42bf215cbe504cd33d` เหมือน0.4B: full-frame semantic29/1024×768/FP32/batch1/eval/inference/noAMP/TF32/extraTTA; native logits map-backก่อนargmax แล้ว frozenYOLOmaskownership; compose nativeก่อนproject. BG/OTHER valid,GT255 sharedVOID,predictionunknown/255fail. Face proxyไม่ใช่strictface-only; Upper/Lower non-Dress; Dress/ApparelOTHER ไม่splitด้วยgeometry. G_loc=17,520/G_sem_C4=17,454 จากexact GTmanifest; geometry-canonical matching0.50/0.75,C3global-only,noQ_C3

## ผลคุณภาพ

**C4-P mIoU4 = null**; ไม่ใช้คะแนน subset แทนชุดเต็ม. ตาราง IoU เป็นเปอร์เซ็นต์ JSONเก็บfraction0–1

|Target|IoU (%)|GT support|Prediction support|Union|
|---|---:|---:|---:|---:|
|ผลยังไม่ครบตาม STRICT_COMPLETE|null|N/A|N/A|N/A|


Person Q_C4_GT/TP/FP/FN/precision/recall/extentF1/contamination/denominators และnativeGT×prediction discordanceอยู่ใน canonical METRICSเมื่อครบเท่านั้น. Qไม่ลงโทษunmatchedpredictionsโดยตรงจึงต้องอ่านFP/F1ร่วม ไม่อ้างoverallwinnerจากQตัวเดียว; extents/IDsมาจากYOLOไม่ใช่nativeinstancecapability. ไม่รวมnative20 tableกับcommon4 scores

## Artifacts, checks และข้อจำกัด

Raw root `Human_Parsing_Benchmark/outputs/common_view/sapiens08-c4p-20261029T081254180014Z` เก็บ ENVIRONMENT/LAUNCH/STATE/EXECUTION/QUEUE/resource observations, pilot/full native29original-grid NPZ,per-person planes/extents/confidences/geometry,atomicCOMMITและscorehashes. Pilot6ภาพIDsตามที่กำหนด ไม่เลือกตามคะแนน; privategalleryสร้างจากsavedmasks. Fullmanifestreused/pendingต้องdisjointและครบ5,000unique;ไม่ครบmainnull,เก็บfailure/partial/orphanโดยไม่retry/fallbackหรือลดsettings. ข้อมูลภาพ/dataset/weights/bulkoutputsไม่ขึ้นGit

Common scorer/packet/routeที่ผ่านCPU acceptanceเดิมใช้ต่อเมื่อhashesตรง ไม่รันfulltest suiteซ้ำ. ตรวจเพิ่มเฉพาะ0.8Bcheckpoint/hash/native29header/source/configpipeline/eval strictload,resource-admissionfixturesและ7modelcallsตามpilotbudget. Resource admissionใช้observed0.4peak+historical0.8peak+largestpopulationmapback+context/growth/headroom+หลายsnapshot ไม่ตัดสินจากutilizationหรือfreeVRAMจุดเดียว; empirical budgetไม่รับรองทุกภาพ. Queue/exec clocks/resourcecapsมีledgerแยก

ไม่มีclean latency/FPS/VRAM-efficiency ranking, architecture-only causality หรือCCTV/สีข้อยืนยัน. ไม่เปลี่ยนmapping/settingsตามpilot/fullscores. ปัญหาเฉพาะ0.8Bหยุดเฉพาะstreamนี้ เก็บหลักฐาน ไม่หยุด/แก้0.4B. [ผล0.4Bและสี่โมเดลเดิม](CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md) เป็นรายงานแยก ไม่รันซ้ำ
