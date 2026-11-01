# ข้อเสนอ CCTV: เปรียบเทียบด้วย person ROI เดียวกันและแยก Face/Neck ให้ถูกงาน

> **CPU evaluation update — 2026-11-01:** [GT screen / three-target diagnostics](reports/CONTROLLED_ROI_GT_AND_PART_RESULTS_TH.md) now covers all nine saved-prediction systems. Face/Neck annotation remains unresolved; final macro4 stays null. No new inference. The design rationale below remains historical.

> **Operational update — 2026-11-01:** ผู้ใช้อนุมัติรันใหม่แล้ว. [Frozen prediction scope/launch report](reports/CONTROLLED_ROI_RUN_TH.md) แยก GT-independent ROI prediction collection ออกจาก final scoring; headline ยัง null จน GT Face/Neck และ QA ผ่าน. เนื้อหาข้อเสนอเดิมด้านล่างเก็บเป็น design rationale ไม่ใช่สถานะยังรออนุมัติ run.

สถานะ **PROPOSED_NOT_FROZEN — DESIGN_RECOMMENDATION_COMPLETE / GT_REVISION_AND_ROI_READINESS_PENDING**. จัดทำ 1 พฤศจิกายน 2026 หลังเห็นผลเก้าระบบและ Sapiens ROI diagnostics แล้ว จึงเป็น exploratory redesign ไม่ใช่ preregistration หรือ independent confirmation. ผู้ใช้มอบหมายให้ออกแบบวิธีที่เหมาะสม; การมอบหมายนี้ไม่ใช่การอนุมัติ inference หรือ full benchmark รอบใหม่. รอบจัดทำเอกสารนี้มี model calls **0** และไม่แก้ active execution config/source, GT หรือคะแนนเก่า.

## ข้อเสนอหลัก

ใช้ **controlled person-ROI application comparison** เป็นรอบใหม่ที่แนะนำ: ภาพคนจาก frozen YOLO ชุดเดียวกัน → crop ที่มี context เดียวกัน → preprocessing ที่ถูกต้องของแต่ละ checkpoint → คืนพิกัดเดิม → ownership ด้วย frozen YOLO mask เดียวกัน → scorer และ GT revision เดียวกัน. เก็บ native/full-frame results เก่าเป็น reference แยกตาราง.

แก้ owner labels และทบทวน contour reference ก่อน แล้ว annotate **Face และ Neck แยกกัน**. ตารางหลักสี่ targets ใช้ Hair, **Face on neck-excluded domain**, Upper non-one-piece และ Lower non-one-piece ด้วยน้ำหนักเท่ากัน. Face+Neck delivery และ neck coverage เป็นตารางประกอบที่ต้องรายงานด้วย. ไม่ให้โบนัส Sapiens ไม่ลดโทษเฉพาะโมเดล และไม่เรียก Face view ใหม่นี้ว่า strict face-only capability.

เหตุผลคือมีสามปัญหาคนละประเภท: input/conditioning ต่างกัน, target taxonomy ต่างกัน และ GT owner ผิดจริง. การปรับ scalar weight แก้ทั้งสามเรื่องนี้ไม่ได้. [หลักฐาน machine-readable](reports/CONTROLLED_ROI_DESIGN_REVIEW.json) บอกขอบเขตการตรวจครั้งนี้; [รายงานตรวจเดิม](reports/SAPIENS2_MEASUREMENT_REVIEW_TH.md) เก็บผลทดลองที่เกิดขึ้นจริง.

## 1. ครั้งก่อนใช้ YOLO crop หรือไม่

ตรวจ `scripts/benchmark.py` และ shared `cihp_benchmark/adapters.py` กับ source hashes ที่ผูก parent run `cctv-partial-20261031T1800Z` แล้วตรงกันทั้งเก้าไฟล์ที่ระบุใน frozen config. ไม่ได้ rehash checkpoints/dataset ทั้งชุดรอบนี้.

| Checkpoint | สิ่งที่เข้า parser ใน CCTV90 เดิม | ใช้ YOLO เมื่อใด | ผลเดิมบอกอะไรได้ |
|---|---|---|---|
| QANet_CIHP_HRNetW48_512x384 | YOLO box ผ่าน native aspect-ratio conversion/ROIAlign | ก่อน network; หลัง network clip ด้วย YOLO mask | QANet + ROI configuration |
| M2FP_R101_CIHP | ภาพเต็มและ native person/query outputs | association หลัง inference; คง native person extent | M2FP + full-frame/association configuration |
| D2FP_R101_CIHP | ภาพเต็มและ native person/query outputs | association หลัง inference; คง native person extent | D2FP + full-frame/association configuration |
| RPR_CIHP | ภาพเต็มพร้อม internal detector/ROI | association หลัง inference; คง native parsing foreground | RP-R-CNN + full-frame/association configuration |
| CPI_R50_CIHP | ภาพเต็มพร้อม internal detector/decoder | association หลัง inference; คง native parsing foreground | CPI R50 + full-frame/association configuration |
| CPI_ConvNeXtB_CIHP | ภาพเต็มพร้อม internal detector/decoder | association หลัง inference; คง native parsing foreground | CPI ConvNeXt-B + full-frame/association configuration |
| Sapiens2_0.4b | ภาพเต็ม stretch เป็น 768W × 1024H | หลัง full-frame semantics/map-back จึงใช้ YOLO mask เป็น ownership | Sapiens 0.4B + full-frame/ownership configuration |
| Sapiens2_0.8b | เช่นเดียวกัน ใช้ checkpoint ของตนเอง | หลัง network | Sapiens 0.8B + full-frame/ownership configuration |
| Sapiens2_1b | เช่นเดียวกัน ใช้ checkpoint ของตนเอง | หลัง network | Sapiens 1B + full-frame/ownership configuration |

ดังนั้น **Sapiens ในรอบ CCTV90 เดิมไม่ได้รับ person crop ก่อนเข้าโมเดล**. การมี YOLO ownership ไม่เท่ากับ YOLO-conditioned input. ตารางเก่าใช้เปรียบเทียบ application configurations ที่ระบุไว้ได้ภายใต้ข้อจำกัด GT แต่ใช้แยกผลของตัวโมเดลจาก input route ไม่ได้.

QANet เดิมไม่ได้ใช้ crop สูตรเดียวกับ Sapiens diagnostic: `InstanceBox.convert` ปรับ aspect ratio แล้วคูณ width/height 1.25 ก่อน ROIAlign. Source config ระบุ horizontal flip test; M2FP/D2FP leaf configs มี `TEST.AUG.ENABLED=True`. จึงห้ามอ้างว่าเก้าระบบเดิมมี geometric preprocessing หรือ external TTA เหมือนกันทั้งหมด. การเปลี่ยน external TTA ด้านล่างเป็นข้อเสนอ configuration ใหม่ ไม่แก้ผลเดิมย้อนหลัง.

Fresh Sapiens diagnostic ทั้งสามขนาดใช้ YOLO crop+10% context แล้วจริง แต่มีเพียง **6 ภาพ / 15 ROIs ต่อ checkpoint**. ห้ามใช้ผลนี้แทนผล ROI90 ทั้งประชากรหรือแทนการทดสอบของอีกหกระบบ.

## 2. เงื่อนไข input ของรอบใหม่ที่แนะนำ

| รายการ | เงื่อนไขร่วม | สิ่งที่ยังต่างและต้องรายงาน |
|---|---|---|
| Population | ทั้ง 90 source images, 48 day/42 night; frozen membership ไม่คัดตามคะแนน | มี partial annotations; จำนวน valid parts ต้องได้จาก GT revision ใหม่ |
| Detector | reuse frozen YOLO26x-Seg cache, boxes, masks, scores, opportunity IDs และ bindings เดิม; ไม่รัน YOLO ใหม่ | detector misses เป็นข้อจำกัดร่วม ไม่ใช่ native parser instance capability |
| Person crop | box ขยาย 10% ของ width/height **แต่ละข้าง**, floor ซ้าย/บน, ceil ขวา/ล่าง, ขยายให้ครอบ frozen mask, clip ที่ image bounds | เหมือน `detector_crop` ที่ diagnostic ทดสอบแล้ว; ไม่ใช้ GT box หรือเลือกเฉพาะคนที่ได้คะแนนดี |
| RGB content | decode ต้นฉบับครั้งเดียว; ทุกระบบได้รับ crop pixels เดียวกัน มี crop-coordinate และ decoded-array hash | CPI file API ต้องใช้ lossless RGB PNG หรือ direct-array bridge ที่ตรวจ readback แล้ว; ห้าม JPEG re-encode crop ต่างคุณภาพ |
| Model preprocessing | preserve aspect ratio; normalization/channel order ของ checkpoint นั้นครั้งเดียว; mean-value padding เมื่อจำเป็น | native resolutions ต่างกันโดยประกาศ เช่น QANet 512H×384W, Sapiens 1024H×768W; การเทียบนี้ไม่ใช่ equal tensor-size/compute-budget test |
| Precision/augmentation | FP32, batch1, eval/inference mode, no AMP/TF32, external flip/multiscale TTA ปิดทุกระบบในกลุ่มนี้ | internal feature pyramids/learned feature branches ไม่ใช่ external TTA; **ไม่ปิด CPI `use_aug` หรือเปลี่ยน architecture** เพื่อทำให้ชื่อ settings ดูเหมือนกัน |
| Native thresholds | ตรึงค่าของแต่ละ checkpoint/config ก่อน readiness; ไม่ tune จาก CCTV scores | ค่า confidence/NMS ของคนละ framework ไม่ใช่ calibrated probability เดียวกัน; การเทียบยังเป็น checkpoint+configuration |
| Map-back | แก้ padding/resize กลับ original-crop grid แล้ววางบน original-image grid; logits bilinear ก่อน argmax เมื่อมี logits | hard masks ใช้ nearest เท่านั้น; เลือก decoder ตาม contract ก่อนดูคะแนน ไม่สลับวิธีเพื่อเพิ่ม IoU |
| Ownership | final person extent/identity ใช้ frozen YOLO opportunity/mask เดียวกันทุกระบบ; เก็บ raw native prediction ก่อน clip ด้วย | ต้องประกาศว่าเป็น YOLO-constrained application comparison; clipping อาจตัดส่วนที่ parser ทายถูก |

สำหรับ QANet adapter ใหม่ต้องนำ crop content ทั้งชิ้นเข้า native input canvas และหลีกเลี่ยงการ crop/ขยาย 1.25 ซ้ำโดยไม่ตั้งใจ. การ bypass/ผูก native ROI transform ต้องตรวจ CPU asymmetric coordinate fixtures และ bounded readiness ก่อน; **ยังไม่ได้ implement หรือรับรองเส้นทางนี้**. อีกห้า native instance parsers ต้องตรวจ crop-local internal detector/query และการคืนพิกัดเช่นกัน. ไม่อ้างว่าแค่เปลี่ยน image path แล้วผ่าน readiness.

### Person selection และ overlap

แต่ละ detector opportunity มี crop ของตนเองหนึ่ง logical task. ถ้า parser ให้หลาย native instances ให้เลือกด้วย **prediction-only bbox IoU กับ designated detector box** บน crop grid: IoU ≥0.50, สูงสุดก่อน, ตามด้วย native confidence, canonical bbox และ stable native index เมื่อเหมือนกันจริง. ไม่ใช้ GT/class agreement เลือก instance. ค่านี้เป็น proposed adapter association rule ไม่ใช่เกณฑ์ความแม่น; ต้องตรึงก่อนรัน. ไม่มี candidate ผ่านให้ semantic output ว่างสำหรับ opportunity นั้นและบันทึก association miss ห้ามสร้าง filled bbox มาทดแทน native semantics.

QANet/Sapiens ให้ semantic plane ต่อ designated opportunity โดยตรง. บันทึก native integer labels ครบ, raw/unclipped plane, YOLO-owned plane, extent, opportunity ID, crop/resize/padding/map-back และ model/input/config/source/environment/detector hashes. Confidence ต้องบอกว่า YOLO score หรือ native score; ไม่เรียก YOLO score ว่า semantic confidence.

Primary selected-part evaluation ใช้ per-person planes แยกกัน จึงไม่รวมคนซ้อนกันจน identity หาย. หากสร้าง global visualization/diagnostics ให้ compose บน native planes ก่อน target projection โดยคง OTHER ไว้; overlay order ใช้ frozen YOLO confidence/geometry/stable opportunity ID เดียวกัน ไม่ใช้คะแนน GT หรือ class preference. รูป global ไม่แทน per-person scorer.

ภาพที่ YOLO ไม่พบคนต้องมี completed empty packet. ถ้ามี eligible GT person แต่ไม่มี matched opportunity ให้ทุก part ของคนนั้นได้ 0; เป็น valid empty prediction ไม่ใช่ worker failure. Duplicate opportunities คงตาม frozen cache; evaluation matching เป็น one-to-one และรายงาน shared duplicate diagnostics ไม่ใช้ GT ลบ prediction ก่อน scoring.

## 3. GT: ต้องแก้ก่อนสรุปว่าใครดีที่สุด

[Owner review](reports/GT_OWNER_BINDING_REVIEW.json) ยืนยัน source labels รวมส่วนของคนละคนอย่างน้อยสองภาพ. แก้เป็น **derived GT revision ใหม่** พร้อม polygon-to-person correction ledger, source hashes, เหตุผลและผู้ตรวจ; ไม่ทับ source annotations หรือทำให้รายงานเก่าดูเหมือนทราบแล้ว. การจัด owner ใหม่อาจเปลี่ยนจำนวน person/part items จึงไม่ hardcode 127/315/324 เป็นตัวหารใหม่.

ตรวจ owner และ visible contour ของคน/ส่วนที่เลือก annotate โดยดู RGB+GT และซ่อน parser outputs. ใส่สถานะ target ต่อ person เป็น `COMPLETE_VISIBLE`, `VERIFIED_NOT_VISIBLE`, `PARTIAL_UNSUITABLE` หรือ `UNCERTAIN`. เฉพาะ `COMPLETE_VISIBLE` ที่มี support ใช้เป็น positive contour item; absent/unknown ไม่กลายเป็น negative เต็มภาพ. ส่วนที่เคยกันออกเก้ารายการต้องมี provenance และทบทวนตาม guideline ใหม่ ไม่ลบทิ้งหรือคืนเข้าคะแนนอัตโนมัติ.

Guideline ที่แนะนำ:

- **Hair:** เส้นผมที่มองเห็น ไม่รวมหมวก/สิ่งบังหรือการเติมผมหลังวัตถุ.
- **Face:** visible face/องค์ประกอบใบหน้า จบที่ jaw/chin; แยก hair, neck และวัตถุทึบที่บังหน้า. ขอบเขตที่ตัดสินไม่ได้จาก RGB ให้ `UNCERTAIN` พร้อมเหตุผลโดยไม่ดู prediction; ไม่วาดเส้นตัดคอคงที่จาก geometry.
- **Neck:** ส่วนคอที่มองเห็นระหว่างขอบหน้าและเสื้อ/ลำตัว; ไม่รวม exposed chest/torso. Annotate แยกแม้จะใช้ union ในรายงานประกอบ. ถ้ามองไม่เห็นให้ verified-not-visible; ถ้าระบุไม่ได้ต้องบันทึก unknown ไม่สมมติว่าไม่มีคอ.
- **Upper/Lower:** visible separate garments; รวม Coat+UpperClothes และ Pants+Skirt ตาม target families เดิม. One-piece/Dress และกรณีแยกบนล่างไม่ได้เก็บเป็นสถานะ/target แยก ไม่แบ่งด้วยเส้นกลางลำตัว. ข้อกำกวมนี้กันจาก non-one-piece part eligibility ตาม GT เท่ากันทุกโมเดล ไม่ ignore ตาม native prediction Apparel/Dress.

ต้อง freeze eligible items, GT-only uncertain regions และ denominators ก่อนคำนวณคะแนน revision ใหม่. ข้อมูลยังเป็น selected people/parts; ยังไม่รองรับ full-scene FP/AP, full-image background IoU หรือ person-silhouette F1. การรับรองที่เข้มขึ้นต้องมีผู้ตรวจอิสระ/second review; agent-assisted QA ไม่เท่ากับ expert gold certification.

## 4. Face/Neck: วิธีที่แนะนำและขอบเขตคำอ้าง

Sapiens native label3 คือ `Face_Neck`; 24–28 เป็น mouth subparts. CIHP label13 คือ Face และไม่มี Neck class แยก. ชื่อคลาสไม่ได้ยืนยัน pixel annotation equivalence; **ไม่รวม CIHP Torso-skin10 เข้าหน้า/คอ** เพราะรวมส่วนอื่นกว้างกว่า และไม่ถือว่า Sapiens hard label3 แยกหน้าออกจากคอได้. หลักฐานชื่อ/IDs จาก [official Sapiens source ที่ตรึง revision](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/docs/SEG.md); annotation boundary equivalence ยังไม่ได้รับรอง.

ให้ใช้สอง views ที่คำนวณจาก native masks เดียวกัน ไม่เพิ่ม inference:

| View | GT / prediction / domain | คำถามที่ตอบได้ | คำอ้างที่ทำไม่ได้ |
|---|---|---|---|
| **Face on neck-excluded domain** — อยู่ใน headline4 | GT face `F_i`; prediction CIHP13 หรือ Sapiens3+24–28; `V_i = image grid − GT Neck_i − GT-only uncertain_i`. ใช้ V_i เดียวกันกับทุกระบบสำหรับ GT person i | ทำนายพื้นที่หน้าถูกเพียงใด เมื่อไม่นับบริเวณคอที่ taxonomy รวมไว้ต่างกัน | ไม่รับรอง strict face-only mask, ความสามารถแยกหน้า/คอ หรือความถูกต้องบน ignored neck |
| **Face+Neck delivery** — supplementary ที่ต้องแสดง | GT `F_i ∪ N_i`; prediction เหมือนข้างบน; domain ไม่ตัด neck ออก เหลือเฉพาะ GT uncertainty ที่ประกาศ | output ของ configuration ส่งมอบ visible face+neck ได้ครบและล้นเท่าใด | ไม่ใช่ native class-equivalence test; CIHP ไม่มี Neck class จึงอาจเสีย FN จาก capability gap |
| **Neck coverage by candidate mask** — diagnostic | recall ของ candidate mask บน GT neck; null ถ้า neck support0/unknown | มี output ครอบคอมากน้อยเพียงใด | ไม่ใช่ Neck-only IoU/precision หรือการพิสูจน์ว่าทำนายคอแยกเป็นคลาสได้ |
| **Strict Face-only / Neck-only output capability** | ตรวจ native output contract; ไม่มีการตัด mask ด้วย GT | แสดงว่าใครส่ง mask ที่แยกส่วนได้จริง/หลักฐานยังขาด | ห้ามเติมคะแนนของคลาสที่ split จาก hard labels ไม่ได้ |

การใช้ GT Neck เป็น ignore ใน **Face view เท่านั้น** เป็น evaluation domain ที่นิยามล่วงหน้าและเหมือนกันทุกโมเดล ไม่ได้ส่ง GT ให้ inference หรือสร้าง deployable face-only prediction. ใช้ neck ของ GT person ที่กำลังประเมิน ไม่ ignore neck ของคนอื่นทั้งหมดจนซ่อน cross-person contamination. False positives บน hair/torso/background และส่วนคนอื่นนอก shared ignore ยังนับตามจริง. ต้องมี neck annotation/verified absence ที่ทบทวนแล้วก่อน item นั้นเข้า Face view; GT neck ที่ยังไม่ทราบต้องไม่เดาให้ผ่าน.

ตัวอย่าง expected arithmetic สำหรับ B (ยังไม่ได้รัน tests รอบนี้): Face100pixels, Neck25pixels, ไม่มี error อื่น. CIHP prediction=Face100; Sapiens prediction=Face+Neck125.

| การวัด | Face-only candidate | Face+Neck candidate |
|---|---:|---:|
| IoU เทียบ face บน full grid แบบเดิม | 1.00 | 0.80 |
| Face on shared neck-excluded domain | 1.00 | 1.00 |
| Face+Neck delivery IoU | 0.80 | 1.00 |

ถ้า candidate ทายล้น torso อีก25pixels นอก Neck ต้องมี FP25 ใน Face view ด้วย; ignore ไม่ขยายตาม prediction. ผลสอง views จึงอธิบายทั้งความแม่นบนหน้าและความสามารถส่งคอ โดยไม่ให้ weight พิเศษกับโมเดลใด.

ค่าเริ่มต้นที่เลือกแนะนำคือ **Hair/Face-domain/Upper/Lower เป็น mandatory evaluation targets**, Neck delivery เป็น supplementary capability ที่ต้องเปิดเผย เพราะ requirement ขั้นต่ำปัจจุบันมีสี่ targets และยังไม่มีคำสั่งให้ Neck เป็น hard requirement. นี่เป็น design recommendation จากการมอบหมายล่าสุด ไม่ใช่คำรับรองว่า configurations ผ่าน deployment. หากงานปลายทางต้องการ strict face-only หรือ Neck เป็น mandatory จริง ให้ยกระดับ capability gate อย่างเปิดเผยก่อนเลือก configuration; ห้ามอาศัย Face-domain IoU เพื่ออ้างว่าผ่าน requirement นั้นแล้ว.

## 5. คะแนนและ weight ที่ใช้ร่วมกัน

สำหรับแต่ละ eligible GT part i,target c ใช้ matched predicted person plane บน original grid. จำกัดทั้ง G และ P ด้วย fixed `V_ic` ที่กำหนดจาก GT เท่านั้น; target อื่นไม่มีการ ignore neck โดยปริยาย. `TP=|G∩P|`, `FP=|P−G|`, `FN=|G−P|`, `IoU=TP/(TP+FP+FN)`, `Dice=2TP/(2TP+FP+FN)`. ไม่ clip prediction ด้วย GT polygon/bbox หรือเลือก instance ด้วย semantic score.

**Primary:** `M_c = sum_i IoU_ic / n_c`; `macro_mean_selected_part_IoU4 = (M_Hair + M_FaceDomain + M_Upper + M_Lower)/4`. น้ำหนัก target ละ **25%** และใน target ให้น้ำหนัก valid selected part เท่ากัน. หาก target ใดไม่มี valid GT support หลัง QA ให้ headline4=null พร้อมเหตุผล ไม่ลดเหลือสามแล้วเรียก IoU4. Empty/missed prediction บน eligible positive GT ให้0; denominator-zero groups เป็น null ไม่แทน0หรือ1.

**Secondary:** Dice แบบเดียวกัน, per-target pooled TP/FP/FN/IoU, day/night และ GT-size bins ที่ freeze จาก GT ก่อนดูผล. Pooled aggregation ให้น้ำหนักส่วนใหญ่ตามพื้นที่มากกว่า mean-part จึงแสดงคู่กันโดยไม่สลับ primary เพราะผลโมเดลใดดูดีขึ้น. นี่ไม่ใช่ global semantic mIoU เต็มภาพหรือ Cityscapes iIoU.

Face+Neck supplementary ใช้ items ที่ QA ครบทั้งสองส่วนหรือ verified absent; รายงาน n/support แยกจาก Face-domain อย่างชัดเจน ไม่เฉลี่ยซ้ำเข้าคะแนนหลักจน head ได้สองเท่าน้ำหนัก. Known native Dress/Apparel/OTHER บน valid Upper/Lower ไม่เป็น ignore: ไม่มี target prediction จึงเป็น FN. Mapping คำนวณจาก union masks ก่อน counts ไม่เฉลี่ย native-class IoU แทน union. คง total native label mapping และ invalid-ID contract ของ revision2; view domain และ GT version ใหม่ต้องมี protocol ID/hash แยกจาก native/common CIHP results.

GT-person→frozen-opportunity matching ใช้ policy เดิมที่ class/model blind: coverage ของ GT annotated-parts union ใน detector bbox ≥0.50, one-to-one maximum cardinality ก่อน sum coverage, confidence/geometry/stable-ID ties ตาม [protocol เดิม](SELECTED_PART_PROTOCOL.md). คำนวณใหม่เมื่อ GT owner version เปลี่ยนแล้ว **freeze matching ร่วมทุกโมเดล**. เป็น association จาก partial geometry ไม่ใช่ full-person mask IoU หรือ AP. Unmatched GT parts คง0; extra predictions ของคนที่ไม่ annotate ไม่กลายเป็น detector FP ทั้งภาพ. Mask ของ matched selected person ที่ล้นไปคนอื่นยังเป็น part FP.

ไม่ใช้ training loss class weights มาแก้คะแนน, ไม่ใช้ per-model weight/ignore และไม่เพิ่ม inverse-frequency weights หลังเห็นผล. ไม่มี absolute pass-IoU หรือคะแนนผสม quality/speed ที่ประดิษฐ์ขึ้น. ผู้คะแนนสูงสุดเรียก observed leader ของ task/view นี้เมื่อ STRICT_COMPLETE และผ่าน capability eligibility เท่านั้น; ไม่มี uncertainty study จึงไม่อ้าง statistical significance.

สูตร IoU/แนวคิด class averaging อ้าง [scikit-learn Jaccard](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.jaccard_score.html) และ [Cityscapes metric definitions](https://www.cityscapes-dataset.com/benchmarks/). แหล่งเหล่านี้ไม่รับรอง annotation, equal-part aggregation, crop10% หรือ neck-excluded protocol ของโครงการ; ส่วนเหล่านี้เป็น project design ที่ต้องตรวจรับต่างหาก.

## 6. ต้องรันอะไรใหม่ — และอะไรไม่ต้อง

| สิ่งที่เปลี่ยน | ใช้ผลเก่าได้หรือไม่ | งานที่จำเป็น |
|---|---|---|
| แก้ GT owner/contour/Face-Neck annotation | native predictions เดิมใช้ได้หาก bindings อื่นตรง | versioned derived GT + **CPU rescoring**; ไม่ต้อง GPU inference เพื่อแก้ GT |
| เพิ่ม Face-domain / Face+Neck views | native integer masks ครบคลาสเพียงพอ | project saved masks + fixed domains/scoring ใหม่; ไม่ต้อง full logits เพื่อ IoU/Dice นี้ |
| ต้องการ probability calibration/AP/native semantic confidence | packets hard masks/YOLO scores ไม่เพียงพอสำหรับทุกนิยาม | ระบุ unavailable; ไม่สร้าง confidence หรือเริ่ม inference เพิ่มในงานนี้ |
| เปลี่ยน full-frame เป็น shared person crop | forward context เปลี่ยนแล้ว hard masks เก่าแปลงย้อนหลังเป็นผล crop ไม่ได้ | inference configuration ใหม่หลัง readiness; native full-frame references เก็บแยก |
| QANet เดิม → crop/context/TTA ของกลุ่มใหม่ | ไม่เท่ากัน: native ROI1.25/flip เดิม | adapter/readiness และ inference ใหม่ ไม่อ้างว่า old ROI ถือว่าตรงแล้ว |
| Sapiens3ขนาด fresh6ภาพ/15ROIsต่อขนาด | **potential reuse** 45 ROI observations ถ้า crop/precision/preprocessing/source/checkpoint/YOLO bindings ตรง | compatibility record + rescore ภายใต้ GT/protocol ใหม่ ไม่แก้ fingerprint/คะแนนเดิมและไม่เลือก attempt ที่คะแนนสูงกว่า |

### Workload ที่คำนวณได้จาก cache จริง

อ่าน detector COMMIT metadata ทั้ง90รายการ ตรวจ image identity/original dimensions/opportunity IDs กับ parent config: **130 detector opportunities, 8 zero-detection images**. รอบนี้ไม่ได้ bulk revalidate detector NPZ arrays ซ้ำ; admission ของรอบจริงต้อง reuse audit ที่ตรง bindings หรือตรวจสิ่งที่เปลี่ยนโดยเฉพาะ.

- 9 checkpoints ×130 ROIs = **1,170 logical ROI jobs**; ทุก checkpoint ยังต้องมี frame completion90รายการ รวม empty frames8รายการ.
- หาก Sapiens reuse ผ่านครบ45 jobs: ต้องสร้าง predictions ใหม่ **1,125 ROI jobs** = หกระบบแรก780 + Sapiensที่เหลือ345. หาก reuse ไม่ผ่าน จำนวนใหม่สูงสุด1,170. นี่เป็น proposed execution workload **ไม่ใช่จำนวนที่ได้รับอนุมัติให้เริ่มแล้ว**.
- Logical ROI jobs ไม่ใช่ raw network-forward counter เสมอไป: native detector/query/decoder และ readiness/warmup มีต้นทุนแยก. จำนวน readiness forward ต้อง freeze ภายหลังตรวจ adapter ของแต่ละ family ไม่ใส่กรอบ forward budget ที่เดาจากชื่อโมเดล.
- ไม่ rerun CIHP5,000, YOLO หรือ CPU common results เก่าเพื่อจัดเอกสาร. ไม่มี ETA หรือ total storage ที่ยืนยันสำหรับ crop route ใหม่. ให้ B วัด actual packet bytes/temporary peak/VRAM/call structure ก่อนสรุป budget; ไม่อนุมานจากขนาด weights หรือ utilization.
- Resource limits เดิมเป็นขอบเขตตั้งต้นที่ยังห้ามขยายเงียบ ๆ: sequential worker, SHARED_GPU_QUALITY_ONLY, free-disk guard50GiB, stream80GiB/checkpoint, time24h/checkpoint, no model/OOM retry/fallback. ค่าขั้นต่ำ free VRAM ของ route เดิมไม่ใช่ peak requirement ที่ตรวจรับแล้วของ route ใหม่ ต้องทบทวน admission จาก actual readiness ก่อน launch โดยไม่ลด quality.

## 7. แผนส่งต่อ implementation และเกณฑ์รับ

| ลำดับ / ช่องว่าง | งานที่ต้องทำ | หลักฐานรับงาน / stop condition |
|---|---|---|
| 1 GT correctness | apply reviewed owner corrections เป็น derived copy, annotate Face/Neck และ review visible contour/one-piece โดยซ่อน model outputs | source immutable; correction+QA ledger; same eligible items/domains/support ทุกโมเดล. ยังมี owner/target ambiguity ที่เปลี่ยนคะแนน → ห้าม final selection |
| 2 Scorer revision | เพิ่ม fixed Face-neck exclusion/union views แยกจาก native scorer; reuse validated mask counting | independent literal cases: ตาราง100/25ด้านบน, outside-neck FP, wrong person, OTHER, empty/missed, zero-support/null; actual packet→scorer→reporter ตรง expected. ห้ามให้ expected values เรียก function ที่ทดสอบ |
| 3 Shared crop adapters | ทำ nine configuration specs โดย reuse checkpoints/environment เดิม; exact crop pixels, no hidden recrop/flip/CPU fallback | asymmetric RGB/coordinate/letterbox fixtures; native ID coverage; original-grid restore; CPI lossless decoder readback; explicit native-instance selection. ไม่เหมือน contract → หยุด route นั้น ไม่เรียกว่าพร้อมครบ9 |
| 4 Ownership / isolation | final extent และ opportunity ID จาก cacheชุดเดียว; เก็บ raw plane ก่อนclip; freeze GT matching | per-opportunity index checks, duplicate/empty/missed/overlap cases, no GT input, immutable native files; แยก label name mismatch จาก malformed output |
| 5 Reuse / resources | reconcile45potentialSapiensROIs และวัด bytes/peak บน bounded readiness ที่เสนอแยก | reused/pending disjoint และครบ130 opportunities/checkpoint; immutable attempt history; model-specific peaks/headroom; storage=retained+shared+temporary+headroom. ไม่มี GPU readiness เพิ่มอัตโนมัติในรอบเอกสารนี้ |
| 6 Freeze / run approval | ตรึง GT+crop+mapping+scorer+adapter/runtime hashes, IDs, budgets และ commands | **ขออนุมัติ batch ใหม่เป็นชุดเดียวเมื่อ reviewable**; ห้ามใช้การมอบหมายออกแบบเป็น launch approval |
| 7 Execution / report | detached sequential scoped batch, atomic packets+ledger; exact90images/130opportunitiesต่อระบบ | STRICT_COMPLETE: missing/duplicate/invalid/failure → primary=null; ไม่ใช้ subset เทียบ full population. ไม่ tune จาก partial scores; bug→stop affected scope/รักษาหลักฐานและrevisionสอดคล้องทุกระบบ |

ภาพ qualitative ใช้ fixed sample เดิมก่อน แล้ว coverage จาก GT-only สำหรับ day/night, small/occluded people, overlap และ Neck/one-piece ambiguity พร้อม manifest; ไม่เลือกจากผู้ชนะ. ภาพ/annotations/private per-person records อยู่ outputs ภายในเท่านั้น. Timing เก่าและ shared-GPU observations ไม่ใช้จัดอันดับ FPS/latency/VRAM efficiency; ถ้าต้องการ speed ranking ต้องเสนอนิยาม/measurement workload แยก ไม่เป็นเงื่อนไขให้แผนคุณภาพนี้เสร็จ.

## 8. สถานะและขั้นถัดไป

ข้อเสนอวิธีหลักปิดแล้ว ไม่ต้องให้ผู้ใช้ตัดสิน mapping ทุกคลาสหรือ weight ทุกตัว. **ยังไม่ใช่ LAUNCH_READY**: ต้องทำ derived GT revision และ controlled ROI/scorer readiness ตามตารางก่อน. ยังไม่มีการแก้ source GT/active config, CPU full rescore หรือ inference รอบใหม่ใน work unit นี้.

ขั้นถัดไปที่พร้อมมอบหมายคือ **GT revision + CPU acceptance ของ scorer ใหม่** แล้วเตรียม adapter readiness scope/manifest เพื่อขออนุมัติ GPU รอบเดียวอย่างมีขอบเขต. แก้ GT อย่างเดียวไม่ต้องรอ GPU และใช้ saved outputs ตรวจ scorer ได้. เมื่อครบจึงคำนวณคะแนนใหม่/รันเฉพาะ input configurations ที่ต้องเปลี่ยน; ไม่ทิ้งผลงานเก่าและไม่เริ่มทุกอย่างใหม่.

ทางเข้า/ประวัติ: [README](README.md), [STATUS](STATUS.md), [WORK_LOG](WORK_LOG.md), [selected-part protocol เก่า](SELECTED_PART_PROTOCOL.md), [ผลเดิม](reports/CCTV_SELECTED_PART_RESULTS_TH.md), [fresh input evidence](reports/SAPIENS2_MEASUREMENT_REVIEW_TH.md). Working copy อยู่ `CCTV_Human_Parsing_Benchmark/`; publication copy อยู่ `Human_Parsing_Study_Public/` และ sync เฉพาะ sanitized documents/manifests. Public clone ไม่มี CCTV assets/weights/environments จึงทำซ้ำทั้งงานจาก clone อย่างเดียวไม่ได้.
