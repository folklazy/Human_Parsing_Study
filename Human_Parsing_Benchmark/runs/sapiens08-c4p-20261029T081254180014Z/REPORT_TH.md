# Sapiens2 segmentation 0.8B — CIHP C4-P

อัปเดต 2026-10-29T21:50:31.232468+07:00 · run `sapiens08-c4p-20261029T081254180014Z` · **COMPLETE**

## สถานะและขอบเขต

|ระบบ|สถานะ|Complete/5,000|
|---|---|---:|
|Sapiens2 0.4B (รอบเดิม)|COMPLETE|5000/5000|
|Sapiens2 0.8B|COMPLETE|5000/5000|

Pilot0.8B 6/6; model-frame callsรวม 5001; warmup 1; reused 6; queue 60.3s แยกจาก execution 16923.5s. ค่า complete ของ0.8Bนับ canonical หลัง pilot ผ่าน/manifestfreezeเท่านั้น. ทั้งสองค่าเวลานี้เป็น operational accounting ไม่ใช่ speed ranking

ผู้ใช้อนุมัติ pilotหนึ่งTRAINwarmup+6fixedVAL แล้ว full validation5,000 เมื่อผ่าน โดยไม่ถามซ้ำ; รันต่อหลังจาก Sapiens2 0.4B เสร็จสมบูรณ์ (Sequential Single-GPU Mode). ไม่มี1B/CPI/training/color/YOLO inference และไม่คำนวณ common view สี่โมเดลเดิมซ้ำ

## Identity และ protocol

Checkpoint `models/human_parsing/sapiens2/0.8b/sapiens2_0.8b_seg.safetensors` SHA256 `e7c1655b7e11678ba200d4ce743be13aeb97eb5ce0a0907f8e6817aabe6b2eec`; nativeconfig `third_party/human_parsing/sapiens2/sapiens/dense/configs/seg/shutterstock_goliath/sapiens2_0.8b_seg_shutterstock_goliath-1024x768.py` SHA256 `967f27e2a596da57cb87598412197138eb73674d4e83c12ccab73e41c0df738a`; source `7e5bae88456ac418ff0e58e74106c9fe192055d4`. Strict model loadingและ827,531,997parameters/native29headตรวจในworkerก่อนforward ไม่ใช้ binding/weights0.4B. Environment `.venvs/sapiens2-pilot` versions/hashของรอบนี้บันทึกแยก

[Pilot config](../../configs/cihp_sapiens_08b_pilot.json), [readiness](READINESS.json), [resource readiness](RESOURCE_READINESS.json). Full config/compatibilityสร้างหลังpilotผ่านโดย scientific identityเดิม ไม่แก้ fingerprintย้อนหลังและไม่เลือก predictions จากคะแนน

ใช้ C4-P revision2 SHA256 `7fb101672407d465885efcc00202af927e93cd422daeae42bf215cbe504cd33d` เหมือน0.4B: full-frame semantic29/1024×768/FP32/batch1/eval/inference/noAMP/TF32/extraTTA; native logits map-backก่อนargmax แล้ว frozenYOLOmaskownership; compose nativeก่อนproject. BG/OTHER valid,GT255 sharedVOID,predictionunknown/255fail. Face proxyไม่ใช่strictface-only; Upper/Lower non-Dress; Dress/ApparelOTHER ไม่splitด้วยgeometry. G_loc=17,520/G_sem_C4=17,454 จากexact GTmanifest; geometry-canonical matching0.50/0.75,C3global-only,noQ_C3

## ผลคุณภาพ

**C4-P mIoU4 = 74.618%**; ไม่ใช้คะแนน subset แทนชุดเต็ม. ตาราง IoU เป็นเปอร์เซ็นต์ JSONเก็บfraction0–1

|Target|IoU (%)|GT support|Prediction support|Union|
|---|---:|---:|---:|---:|
|Face proxy|72.648|37932488|43543016|47191691|
|Hair|78.942|40760850|37688175|43840371|
|Upper non-Dress|75.867|148199276|150280503|169719018|
|Lower non-Dress|71.015|38702345|33314437|42111273|

Person Q_C4_GT/TP/FP/FN/precision/recall/extentF1/contamination/denominators และnativeGT×prediction discordanceอยู่ใน canonical METRICSเมื่อครบเท่านั้น.
