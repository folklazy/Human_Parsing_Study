# ข้อเสนอ common view สำหรับ CIHP–Sapiens2: face, hair, uppercloth, lowercloth

สถานะ common full evaluation **NOT_AUTHORIZED**; revision **`revision-2-pilot` ACCEPTED_SCOPED_PILOT_ONLY** · Protocol `CIHP_SAPIENS_C4P` (proposal-1 history ที่commit7218282) · Work unit `common-view-proposal-20261029T004437Z` · 29 ตุลาคม 2026 (เวลาไทย UTC+07)

เอกสารนี้เป็นทางเข้าหลักของ common-view definitions: ผู้ใช้อนุมัติ implementation/CPU acceptance และ conditional0.4Bpilot≤7calls ในรอบใหม่แล้ว แต่ **ไม่อนุมัติ full common evaluation** อ่าน [รายงาน implementation/pilot](CIHP_SAPIENS_04B_PILOT_TH.md) สำหรับสถานะจริง ข้อเสนอเดิมที่commit7218282ไม่ใช่คำอนุมัติรันย้อนหลัง งานนี้ทำหลังเห็นผลสี่ระบบแล้ว จึง **ไม่ใช่ preregistered/confirmatory protocol** เลือก projection จากนิยามและข้อจำกัดของข้อมูล ไม่ใช้คะแนน VAL เลือก mapping, thresholds หรือวิธี postprocess

อ่านประกอบ: [ผล native CIHP สี่ระบบ](CIHP_FOUR_MODEL_RESULTS_TH.md), [revision-2 pilot specification](../protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json), [mapping ครบ 49 native IDs](../protocol/CIHP_SAPIENS_COMMON_VIEW_LABELS.csv), [หลักฐานที่ตรวจจริง](../runs/common-view-proposal-20261029T004437Z/EVIDENCE.json)

## 1. ข้อเสนอหลักที่แนะนำ

ใช้ **C4-P — projected application target-output agreement กับ released CIHP annotations** เป็นการทดลองร่วมขั้นถัดไป วัดสี่ช่องที่งานต้องการบน GT domain เดียวกัน: **Face ตาม CIHP reference / Hair / กลุ่มเสื้อผ้าบนที่ไม่ใช่ Dress / กลุ่มเสื้อผ้าล่างที่ไม่ใช่ Dress**

- GT และ CIHP predictions: Face13, Hair2, UpperClothes5 ∪ Coat7, Pants9 ∪ Skirt12
- Sapiens predictions: Face_Neck3 ∪ facial subparts24–28 เป็น **Face proxy ที่ยังรวมคอ**, Hair4, Upper_Clothing23, Lower_Clothing13
- Dress6 ของ CIHP และ Apparel1 ของ Sapiens เป็น **OTHER ที่ยัง valid** ไม่มีการแบ่งเดรส ไม่มีการตัดคอ ไม่มี model-specific ignore
- คะแนนหลักที่เสนอคือ macro IoU ของสี่ target จาก global confusion พร้อม IoU/support ของแต่ละ target เสมอ ให้ Face proxy มีป้าย approximate ในทุกตาราง นำเสนอ C3 (hair/upper/lower) เป็น sensitivity view แยก ไม่เปลี่ยนให้กลายเป็นข้อกำหนดขั้นต่ำสามช่อง

**เหตุผล:** วิธีนี้ implement ได้จาก hard masks เดิมและ semantic output มาตรฐานของ Sapiens วัดว่า application configuration ส่ง target ตาม reference ของงานได้เพียงใด โดยไม่ต้องสร้าง prediction จาก GT และไม่ต้องรอ taxonomy ทั้งสองเทียบเท่ากันทุกพิกเซล การที่ native label ถูกตามนิยามต้นทางแต่เสียคะแนนกับ task นี้เป็น *ข้อจำกัดในการส่งมอบ target* ซึ่งต้องเปิดเผย ไม่ใช่หลักฐานว่า native segmentation ผิดเสมอไป

**ขอบเขตคำอ้าง:** C4-P ไม่ใช่ strict semantic/annotation equivalence ของสี่คลาส ไม่ใช่ official CIHP reproduction ของ Sapiens และไม่รับรองว่า parser ส่ง face-only หรือ upper/lower ของเดรสได้ คะแนน C4-P สูงหรือ pilot ผ่าน **ยังไม่เท่ากับผ่าน minimum สี่ target แบบ strict** หากต้องใช้ face-only ที่แยกคอ หรือเสื้อผ้าบน/ล่างของเดรสจริง ต้องเพิ่มข้อมูล/โมดูลและประเมินเป็น task/configuration ใหม่

คำแนะนำนี้เลือกวิธีดำเนินการให้แล้ว ไม่ปล่อยแต่ละแถวเป็น UNKNOWN เพื่อรอผู้ใช้เลือกทั้งหมด: ผู้ใช้อนุมัติ implementation verification และ conditionalpilot ตามข้อ10ในรอบปัจจุบันแล้ว ให้ดูactualสถานะในpilotreport; ไม่รื้อ native benchmark ไม่ rerun สี่โมเดลเพื่อเปลี่ยน input route และไม่เพิ่ม auxiliary model ในข้อเสนอหลัก

## 2. Baseline และสิ่งที่ยังคงเดิม

ตรวจ public staging Git: `main`, HEAD ก่อนงานนี้ `6fa6d8e2aea67f3cd6ccf5e26aa4078eaac3af3c`, working tree สะอาด; canonical working directory คือ `Human_Parsing_Benchmark/` ระดับ workspace ส่วน Git publication checkout แยกอยู่ `Human_Parsing_Study_Public/` ใช้ explicit path/hash sync เดิม

ผล QANet/M2FP/D2FP/RP-R-CNN คง COMPLETE ตัวละ 5,000 official CIHP VAL IDs จาก canonical completion เดิม CPI R50/ConvNeXt-B **พัก ไม่ได้ยกเลิก** ผลสำเร็จ 3/113 IDs และ OOM history คงเดิม คะแนนหลัก null ตาม STRICT_COMPLETE ไม่ใช้ subset มารวม comparison นี้ ไม่มี current worker/controller ของ CIHP/CPI ตรงกับ process scan ตอนเริ่มงาน; ไม่ได้อ้างว่า GPU หรือ server ทั้งเครื่องว่าง

Frozen config `configs/cihp_native_six.json`, adapters/scorer/worker, native results, source GT, population, checkpoint bindings และ draft matrix เดิมไม่เปลี่ยน รอบproposal-1ไม่มี inference/pilot/implementation;รอบrevision2อนุมัติแยกcommonimplementationและpilotเท่านั้น ยังไม่มีfullcommonscoringหรือแก้nativeconfig/source รายละเอียดตรวจซ้ำอยู่ [consistency receipt](../runs/common-view-proposal-20261029T004437Z/CONSISTENCY_CHECKS.json)

ประชากรของข้อเสนอคือ [native CIHP Validation 5,000 IDs](../manifests/CIHP_NATIVE_VALIDATION.json), SHA256 `0bf366ae6fcde0967f915e1803bc08dbce94de5753e3dea9f0dbe5aa570083d7` ไม่ใช่ CCIHP main4,961/Ninja ประชากร VAL นี้ใช้เปรียบเทียบ/คัดเลือก application configurations ได้ตามแผนปัจจุบัน แต่ไม่ใช่ independent unseen final test และห้าม tune จากคะแนน VAL

## 3. แยกหลักฐานสี่ชั้น ไม่ใช้ชื่อคลาสแทน boundary evidence

|เรื่อง|ข้อเท็จจริงจาก source|สิ่งที่ยังไม่ทราบ/ห้ามสรุปเกิน|
|---|---|---|
|CIHP IDs|local `datasets/CIHP/README.md` ระบุ 19 foreground IDs; M2FP/D2FP registry ที่ pin ไว้ตรงกับ native20 semantic contract|README ไม่ใช่คู่มือขอบคอ/ชนิดเสื้อผ้าเต็มชุด; registry Human20 เป็น structured branch ไม่ใช่ semantic class20|
|CIHP annotation|[PGN paper §3.1–3.2](https://arxiv.org/pdf/1808.00157) ระบุ annotation/QA และใช้ semantic categories ตาม LIP โดยแทน Jumpsuit ด้วย Torso-skin|ไม่ได้พบคำสั่งกำหนด chin/neck และ Dress/Coat partition อย่างละเอียดจากแหล่งที่ตรวจครั้งนี้ จึงไม่อ้างว่า source รับรอง boundary equivalence|
|Sapiens29 IDs|[official SEG.md ที่ pin](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/docs/SEG.md) และ DOME_CLASSES_29 ระบุ IDs ตรงกัน; per-size config/header evidence เดิมตรวจ 0.4B/0.8B/1B แยกแล้ว|จำนวน 29 channels ไม่ยืนยันชื่อ/ขอบเขตด้วยตัวมันเอง ไม่ hash/load weights ใหม่ในงานนี้|
|Sapiens training vocabulary|[paper v1 §5/A.3](https://arxiv.org/html/2604.21681v1) อธิบาย 29-class body-part segmentation และตัวอย่าง annotation|ไม่ใช่ annotation manual สำหรับแยก Face_Neck หรือแจกแจง Apparel ทุกชนิด จึงไม่ใช้ paper figure เป็น GT-equivalence proof|
|Source remapping|[seg_utils.py ที่ pin](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/sapiens/dense/src/datasets/seg/seg_utils.py) แสดงการรวมชื่อ source labels จริงตามตารางถัดไป|ทราบสมาชิกที่ source เปิดเผย ไม่ได้ทราบ garment annotation policy ทั้งชุดจากคำว่า Upper/Lower|

Sapiens source revision **`7e5bae88456ac418ff0e58e74106c9fe192055d4`** ตรวจ `docs/SEG.md`, `seg_utils.py`, dataset loaders, per-size config ที่อ้างใน bindings, `tools/vis/vis_seg.py`, `SegResize` และ `ImagePreprocessor` แหล่ง official CIHP/PGN resolve revision `0cf1cbe54a44fc86abe2023b0e762df3f9605242`; ไม่โหลด dataset จากเว็บ รายการ path/SHA และ access result (CVF PDF fetch 403 ใช้ author arXiv paper แทน) อยู่ใน EVIDENCE.json

### 3.1 Decision matrix: ปัญหา → วิธีที่เลือก → สิ่งที่เสียไป

|Target/ปัญหา|หลักฐานและความสัมพันธ์|ทางเลือกที่พิจารณา|วิธีหลักที่เลือก|ข้อมูลที่เสีย/คำอ้างที่ยังทำไม่ได้|
|---|---|---|---|---|
|Hair: CIHP2 ↔ Sapiens4|named concept หนึ่งต่อหนึ่ง; pixel extent/occlusion policy ยังไม่ independently verified|จับคู่ตรง / annotate ใหม่ทั้งชุด|จับคู่ตรงเป็น Hair ใน C4-P พร้อม support/ขอบเขตจาก GT เดิม|EXACT ใน matrix เดิมหมายถึง concept correspondence ไม่ใช่ทุก boundary เท่ากัน; occluded hair ไม่กลายเป็น amodal GT|
|Face: CIHP13 ↔ Sapiens3,24–28|Face_Neck รวมคอ; facial subparts แยกจาก3; source52→29 รวม face/neck skin และบาง mouth/eyebrow regions เข้า3|ใช้3อย่างเดียว / union / ตัดคอ / ขยาย GT เป็น Face+Torso / annotation ใหม่|union3,24–28 เป็น approximate Face proxy เทียบ CIHP13; เก็บ Face IoU และ native-ID discordance แยก|กู้ face-only จาก label3 ไม่ได้; อาจ FP บริเวณคอแม้ native label ถูก; ไม่เรียกคะแนนนี้ pure facial-boundary accuracy|
|Upper: CIHP5+7 ↔ Sapiens23|CIHP แยก UpperClothes/Coat; Sapiens มี Upper_Clothing เดียว|เทียบ5อย่างเดียว / union5+7 / anatomical upper-body split / รวมเสื้อผ้าทุกชนิด|union5+7: กลุ่มประเภท upper garment ที่ไม่ใช่ Dress เป็น reference; S23 เป็น broad proxy|ไม่วัดแยก Coat vs UpperClothes; hem ของ coat ที่ยาวลงล่างยังอยู่กลุ่ม upper garment ตาม category ไม่ตัดที่เอว; การรวมไม่ได้พิสูจน์ S23 ครอบ coat ทุกชนิด|
|Lower: CIHP9+12 ↔ Sapiens13|Pants/Skirt แยกใน CIHP; source34→29 รวม Lower_Clothing และ Lower_Spandex เข้า13|เทียบ Pants อย่างเดียว / union9+12 / สร้าง anatomical lower split|union9+12 เป็น lower garment family reference; S13 เป็น broad proxy|ไม่วัด pants/skirt subtype; Lower_Clothing ไม่ใช่หลักฐานว่า annotation partition ตรงกับทุก pants/skirt; underwear/spandex boundary ไม่ครบ|
|Dress6 / Apparel1|CIHP มี Dress โดยเฉพาะ; source52→29 ของ Apparel1 รวม Hairnet1 และ Apparel34 เดิม|Apparel=Dress / split dress / ignore dress เฉพาะ Sapiens / OTHER valid / re-annotation|ทั้งคู่ OTHER valid, retain native-ID breakdown เพื่ออธิบายการปฏิเสธ target|Apparel ไม่ใช่ Dress/all-clothes; ไม่ประเมิน upper/lower components ภายใน Dress จาก GT ปัจจุบัน แต่ทำนาย target บน Dress ยังถูก FP ตาม task|

ตัวอย่างเชิงนิยาม ไม่ใช่ผลโมเดล: ถ้า GT มี face100 pixels และ neck20 pixels อยู่ OTHER แต่ native Sapiens ทำนาย Face_Neck ถูกทั้ง120 การใช้ proxy จะได้ Face IoU100/120 ไม่ใช่1 นี่เป็น *target incompatibility penalty* ไม่ใช่หลักฐานว่า Sapiens แบ่ง native class ผิด ถ้าพิกเซลใบหน้าจริงถูกทำนาย Hair นั่นเป็น disagreement ที่เกี่ยวกับ segmentation/label prediction ด้วย; hard masks อย่างเดียวไม่แยกสาเหตุทุกพิกเซลได้

### 3.2 เหตุใดไม่เลือกทางลัดอื่นเป็นข้อเสนอหลัก

|ทางเลือก|ผลต่อคำถาม/ต้นทุน|ข้อสรุป|
|---|---|---|
|ขยาย Face เป็น Face+Torso-skin เทียบ Face_Neck+Torso|รวมหน้า คอ หน้าอก/ลำตัว จนคำถามเปลี่ยน; exposed/covered torso convention ยังไม่ครบ|ไม่ใช้แทน face requirement; อาจเป็น task ใหม่ถ้าต้องการภายหลัง|
|รวม Upper+Lower+Dress เป็น Clothing ทั้งหมด|บดบัง upper/lower ที่จำเป็น; Apparel ยังไม่เท่ากับ clothes ทั้งหมด|ไม่ใช้เป็น headline แทนสี่ target|
|เอา Face ออกจาก headline ให้เหลือ C3|ลดอิทธิพล neck mismatch แต่ตอบข้อกำหนดเพียงสามช่อง|ใช้ C3 เป็น sensitivity เท่านั้น ต้องรายงาน Face proxy และสถานะยังไม่ strict-four เสมอ|
|Annotated common face/neck + garment-family reference เพิ่ม|ใช้ผู้ทำ annotation ที่ไม่เห็น prediction พร้อม second review, version source/derived GT และ fix rules ก่อน scoring; ต้องขออนุมัติและประเมินต้นทุนต่างหาก|เหมาะถ้าต้องตอบ strict boundary/capability แต่ไม่เป็น dependency ที่บังคับหยุด C4-P operational pilot; ไม่รับรองจำนวนภาพพอสำหรับ generalization โดยยังไม่ออกแบบ sample|
|ใช้ dataset อื่น|ต้องพิสูจน์ว่ามี face/neck/garment ownership ที่ต้องการและทบทวน split/exposure ใหม่|ไม่เพิ่ม dataset ในงานนี้; มี native CIHP อยู่แล้วจึงใช้ projected question ที่จำกัดคำอ้างก่อน|
|auxiliary face/neck model, pose/learned split หรือ postprocess|เปลี่ยน configuration และต้อง inference/GT/control เปรียบเทียบต้นทุน-คุณภาพใหม่|ไม่ใช้ในข้อเสนอหลัก; ห้าม GT ช่วยเลือก prediction และห้าม geometry heuristic แล้วอ้าง equivalent|

## 4. Sample evidence ที่ตรวจแบบจำกัด

ใช้ **16 IDs ที่ล็อกก่อน native scores** จาก [diagnostic manifest](../manifests/CIHP_NATIVE_DIAGNOSTIC_SAMPLE.json) ตรวจ Category_ids เพียง16 masks เพื่อหาประเภท ambiguity ไม่ค้นภาพตามคะแนนของโมเดล อ่านค่าจริงและเปิด saved figures/RGB ของ `0006909`, `0001538` ไม่มี inference/rescore

|ID / เหตุผลที่เลือก|สิ่งที่ตรวจพบจริง|ข้อจำกัด|
|---|---|---|
|0006909: เป็นภาพแรกใน frozen order ที่มี Dress และ Skirt พร้อม UpperClothes/Coat/Pants|GT Dress12,870 pixels, Skirt3,622; จุด original `(310,190)` และ `(310,290)` เป็น ID6 ทั้งสอง แสดง garment label เดียวที่บริเวณต่างระดับของเดรส|ไม่สามารถสร้างเส้น upper/lower ของ Dress จากสองจุดนี้ และไม่ใช้ส่วนของ prediction มาเลือกกรณี|
|0001538: close-up มี Face/Hair/Torso-skin และไม่มี lower garment labels|GT Face38,328, Hair61,144, Torso-skin33,552 pixels; `(130,240)`=Face13 และ `(170,310)`=Torso-skin10 บริเวณใต้คาง/คอส่วนที่เห็นใน RGB|ยืนยันเฉพาะตำแหน่งที่ดู ไม่ใช่คู่มือว่าคอทุกภาพถูกติด10 หรือหลักฐานว่า Sapiens face boundary ต้องเท่ากัน|

พิกัดเริ่ม0 รูป `(x,y)` หลักฐาน GT hash/counts และเหตุผล selection อยู่ใน EVIDENCE.json ความเห็นจากภาพเป็น AI spot inspection ไม่ใช่ independent human QA หรือ dataset-wide error estimate คงภาพ dataset ไว้ภายนอก Git ใช้ [ตำแหน่ง gallery เดิมในรายงาน](CIHP_FOUR_MODEL_RESULTS_TH.md); ไม่สร้างชุดภาพเพื่อเลือก mapping ที่ทำให้โมเดลชนะ

## 5. Protocol C4-P ที่พร้อมส่งให้ implement หลังรับรอง

### 5.1 Target IDs และ mapping ครบทุก native ID

|Common ID|ชื่อในผล|GT definition / CIHP prediction|Sapiens prediction|ระดับความสัมพันธ์|
|---|---|---|---|---|
|0|BACKGROUND|0|0|background concept; annotation foreground coverage ต่างได้|
|1|FACE_CIHP_REFERENCE|13|3 ∪24 ∪25 ∪26 ∪27 ∪28|reference vs approximate Face_Neck proxy ไม่ strict equivalent|
|2|HAIR|2|4|named concept one-to-one, extent unverified|
|3|UPPER_NON_DRESS_FAMILY|5 ∪7|23|reference union vs broad proxy, ไม่ใช่ anatomical upper half|
|4|LOWER_NON_DRESS_FAMILY|9 ∪12|13|reference union vs broad proxy, ไม่ใช่ anatomical lower half|
|5|OTHER|native foreground ที่เหลือ รวม Dress6|native foreground ที่เหลือ รวม Apparel1|valid negative evidence ไม่ใช่ background/ignore|

ตารางราย native ID แบบครบอยู่ต่อท้ายเอกสารและ [CSV](../protocol/CIHP_SAPIENS_COMMON_VIEW_LABELS.csv) แยก `projection_type`, `task_role`, `equivalence_evidence`, `rank_eligibility` ไม่ใช้ field EXACT แทนทั้งการรวมคลาส/semantic equivalence/สิทธิ์จัดอันดับ

### 5.2 Shared valid domain, background และ OTHER

ให้ `C(x)` เป็น native CIHP Category_ids, `H(x)` เป็น Human_ids, `g=projection(C)` และ `p` เป็น final projected prediction

- Global valid domain **V={x: C(x)∈0..19}**, GT255 เป็น VOID เท่ากันทุกระบบ Source GT ค่าอื่นนอก schema ต้องหยุดตรวจ contract ไม่เติมเป็น0 ไม่ ignore ตามโมเดล/prediction
- BG0 และ OTHER5 ยังคง valid ทั้งภาพ ไม่มี per-model ignore และไม่ลบ Dress/neck ที่ไม่ตรงกันออกจาก domain
- GT=OTHER,pred=target → FP ของ target; GT=target,pred=OTHER/BG → FN; GT=targetA,pred=targetB → FN ของA + FP ของB; GT=BG,pred=target → FP
- GT=OTHER,pred=OTHER ไม่นับเป็น target TP และไม่ได้คะแนนสำหรับ Dress accuracy; GT=BG,pred=OTHER ไม่ใช่ FP ของสี่ target แต่ confusion6×6 ยังเก็บความผิด BG↔OTHERไว้ นี่ไม่ใช่ foreground/person segmentation score
- Recognition ของ Dress/Apparel เป็น valid execution และ mapped OTHER ไม่ใช่ unresolved; **prediction255**, negative/out-of-range IDs, float-label/nonfinite/malformed geometry เป็น contract failure ไม่ใช่ VOID ของโมเดล
- Per-person semantic domain **Vp=V \ {x:C(x)>0 และ H(x)=0}** ใช้ร่วมกันทุกโมเดล Owner-unknown ที่ยังรู้ semantic target ใช้ global score ได้ แต่ void เฉพาะ person semantics ไม่อ้างว่า ownership ถูกกู้คืนแล้ว

### 5.3 Compose ก่อน project และ overlap

ใช้ final application planes, extents และ scores ที่ packet เก็บ ไม่เลือก planes ด้วย GT ไม่ unclip QANet เงียบ ๆ และไม่สร้าง ownership ใหม่ให้ native parsers

1. อ่าน native integer semantic planes กลับ original `(H,W)` ภายใต้ ownership ที่บันทึกไว้
2. เริ่ม global native map เป็น BG0 ใช้ frozen `compose`: เรียง `(score,-packet_index)` จากต่ำไปสูง; overwrite เฉพาะ `native_label>0` สูงสุดชนะ เมื่อ score เท่ากัน index ต่ำกว่าชนะ BG ใน plane เป็น transparent ตาม compose เดิม
3. **project ทุก native ID หลัง compose** เช่น Dress/Apparel ที่ชนะ overlap ต้องกลายเป็น OTHER ที่ valid ห้ามลบทิ้งก่อนแล้วปล่อย target ของคน score ต่ำกว่าโผล่ขึ้นมา
4. Per-person view project แต่ละ retained plane โดยคง extent/score/identity เดิม ไม่เอา global winner มาแทน semantics ของทุกคน ไม่แก้ person IDs ด้วย GT

Mapping เป็น **hard-label projection หลัง argmax** ไม่ใช่ sum probability ก่อน argmax เส้นทางนี้เทียบกันได้จาก artifacts ที่มี ส่วน probability aggregation เป็นอีกการทดลองที่ยังไม่พร้อมจาก hard masks ทั้ง cohort

### 5.4 Metrics, aggregation และ denominators

Primary: **`C4P_global_mIoU4`** และ IoU ของสี่ targetเสมอ สะสม integer confusion6×6 บน V ทั้งประชากรก่อนคำนวณ ให้ `TP_c=h[c,c]`, `GT_c=sum_j h[c,j]`, `Pred_c=sum_i h[i,c]`, `U_c=GT_c+Pred_c-TP_c`, `IoU_c=TP_c/U_c`, `mIoU4=(IoU_1+...+IoU_4)/4` BG/OTHER ไม่อยู่ในค่าเฉลี่ย แต่เป็น negative pixels ครบ

- Fixed scored class set={1,2,3,4} เหมือนกันทุกระบบ ไม่เปลี่ยน class eligibility ตาม prediction หาก U=0 ให้ IoU=0 ตาม convention ที่ประกาศ พร้อม flag zero_union/GT_support/pred_support; ไม่เติม1 ไม่ตัดคลาสของโมเดลที่ไม่ทำนายทิ้ง สำหรับสี่ targets ที่ full GT ไม่มี support ต้องรายงานว่าไม่ถูกประเมิน capability นั้น ห้ามอ้างผ่านเพราะเฉลี่ยได้
- Per-target precision=TP/Pred, recall=TP/GT; denominator0 ใช้ null พร้อมเหตุผล นอกจาก IoU zero-union convention ที่กำหนดต่างหาก Ratios เก็บเต็ม0..1 การแสดงร้อยละระบุหน่วย ไม่ average IoU รายภาพหรือ IoU native subclasses แทน confusion
- Secondary: C3 mean Hair/Upper/Lower เป็น sensitivity ไม่รวมคะแนนกับ C4-P; native20/FG19 อยู่คนละ protocol ไม่เอามาเรียงใน leaderboard เดียว
- รายงาน rejection/discordance เป็น native-GT label × native-pred label counts โดยเฉพาะ GT6→Sapiens1/13/23 และ GT10→Sapiens3 แทนการสรุปว่าทุก mismatch เป็น annotation/model error เป็นตารางdiscordanceสำหรับหาสาเหตุที่เป็นไปได้ ไม่ใช่proofว่าGT10→Sapiens3ทุกpixelเกิดจากneckdefinition (อาจเป็นsegmentationผิดจริงได้ด้วย) ไม่มีการลบ penalty หลังดู diagnostic
- รูปขอบเขต original-grid และ matched/missed/duplicate cases ใช้อธิบายเสริม งานนี้ไม่เพิ่ม Boundary IoU/AP/PCP เป็นคะแนนที่รับรองแล้ว; ไม่อ้าง quality ของ boundary จากชื่อโมเดลหรือ mIoU อย่างเดียว

**การรวมคลาสต้องได้ sufficient statistics:** ถ้ามี canonical global native20 confusion `H20`, mapping matrix `A[20,6]` แบบ one-hot ให้ `H6=Aᵀ H20 A` แล้วคำนวณ IoU ใหม่ การอ่าน IoU_UpperClothes กับ IoU_Coat มาเฉลี่ยไม่ใช่ union IoU การตรวจครั้งนี้พบ `CONFUSION.npy` canonicalครบทั้งสี่ระบบ shape20×20,GT margins ตรง canonical และ valid pixels876,659,024 เท่ากัน; **ยังไม่ได้ project หรือคำนวณ C4-P**

### 5.5 Person matching และ ownership

แยก prediction-only YOLO association ที่เกิดตอน inference ออกจาก scorer matching กับ GT ห้ามใช้ GT เพื่อเลือก native instance, crop หรือ resolve overlap

- GT extent ของคน i: `E_i=(H==i)∩V` ที่ไม่ว่าง; G_loc เป็นจำนวนดังกล่าวทั้งประชากร ผูก source Human_ids/population/valid-domain hashes ใหม่ แม้คาดว่าเลขเดิม17,520จะตรง ก็ไม่ใช้เลขนั้นแทนการ materialize bindings
- Predicted extent ใช้ **source extent ของ application** ตัดเฉพาะ source VOID เดียวกันขณะให้คะแนน ไม่ตัดตาม target semantics; raw extents ต้อง nonempty ถ้าเหลือเฉพาะ VOID หลังตัดให้บันทึก VOID_ONLY extent แยกและไม่นำมานับ extent FP ไม่เปลี่ยนผล global ซึ่ง VOID ถูกตัดอยู่แล้ว
- Matching แบบ one-to-one mask IoU ที่0.50หลัก/0.75เสริม: maximize จำนวน eligible pairs ก่อน แล้ว maximize sum IoU ใช้ geometry canonical ordering `(bbox y0,x0,y1,x1,area,sumY,sumX,packedbooleanmaskbytes)` แล้วเลือก lexicographic optimum บนลำดับนี้ใน sum-IoU tolerance1e-12 โดยไม่ใช้semanticclass/quality เลือกคู่ thresholdinclusive≥0.50/0.75; ถ้าGTgeometryเหมือนกันจริง fallbackstableGTID และถ้าpredgeometryเหมือนกัน fallbackpacketindex พร้อมรายงานalternativeoptimum/identicalgeometrygroups รับรองGT-IDrenaminginvarianceเฉพาะGTgeometryต่างกัน ไม่รับรองpredictionpermutationinvarianceเมื่อgeometryเหมือนกัน Native20matching/resultsคงเดิม
- Count TP=#pairs, FP=#evaluated pred extents−TP, FN=G_loc−TP; P=TP/(TP+FP),R=TP/G_loc,F1=2TP/(2TP+FP+FN) denominator0→null ไม่เรียก parsing AP หรือ parser-native ownership accuracy
- G_sem(C4) = จำนวน GT persons ที่มีอย่างน้อยหนึ่ง target1..4 บน Vp; derive GT-only รายภาพ/คนและ freeze ก่อนอ่านคะแนน เปลี่ยน target setแล้วต้อง **ไม่สร้าง G_sem(C3)/Q_C3**; C3เป็นglobalmean2/3/4เท่านั้น และFaceยังvalidnegative; ไม่สืบทอด17,520สำหรับC4หรือเลือกคนที่โมเดลทำนายสำเร็จ
- สำหรับ matched eligible GTi สร้าง GTperson plane เป็น projected category เฉพาะ H=i,ที่อื่น BG; เทียบ paired prediction บน **Vp ทั้งภาพ** ให้ K_i เป็น union ของ target IDs1..4 ที่มีใน GTperson หรือ paired prediction เฉลี่ย IoU ของ K_i เพื่อได้ q_i; OTHER/BG ไม่เป็น positive target แต่ยังเป็น negatives Unmatched eligible GT ให้ q_i=0 แล้ว `Q_C4_GT=sum q_i/G_sem`; G_sem0→null
- ไม่มี predicted person → GTคนถูกพลาดตามmatching มี valid extentแต่ semantic-empty/OTHER-only → retainและจับคู่ได้; ถ้า GTมีtarget,q_i=0 การใช้คำว่า empty prediction ต้องระบุ empty person list หรือ empty target semantics ไม่รวมเป็นกรณีเดียว
- Unmatched predictions เป็น extentFP และมีผล global semantic FP เมื่อทับ negative pixels แต่ไม่ถูกลงโทษโดยตรงใน GT-onlyQ จึงห้ามเรียก Q leader ว่า overall winnerโดยลำพัง ต้องเปิด FP/F1 และ per-target support/limitations พร้อมกัน
- Matched target-contamination numerator=`pred_target ∩ (H>0) ∩ (H≠matched_ID) ∩Vp`, denominator=`pred_target ∩Vp` ของ matched predictions รวมกัน; report background leakage `(H=0)` อีกช่อง Denominator0→null และรายงาน matched coverage เพราะไม่ครอบคลุม unmatched predictions ไม่อ้างว่า matched-only diagnostic ยืนยัน ownership ทั้งระบบ

### 5.6 STRICT_COMPLETE และ execution/prediction states

|กรณี|Execution|การให้คะแนน|
|---|---|---|
|Native IDsถูกต้อง แม้เป็น Dress/Apparel/OTHER-only|COMPLETE ถ้า artifacts/bindingsครบ|FP/FN/semantic-emptyตามนิยาม ไม่ทำให้ทั้งrun INCOMPLETEเพียงเพราะ unsupported target|
|ไม่มี predicted persons แต่ pipelineทำงานสำเร็จ|COMPLETE valid empty|globalBG, missedGT/targetFNตามจริง ไม่ถือ failure เพื่อหลบคะแนนต่ำ|
|Malformed packet/invalidID/nonfinite/geometryผิด|INVALID/contract failure|เก็บหลักฐาน ไม่นำ subsetมารายงานเป็นคะแนนชุดเต็ม|
|OOM/model error|FAILED/INCOMPLETE|เก็บatomic outputs/failedattempt; no automatic retry/fallback|
|External interruption หรือ missing/orphan|RECONCILIATION_REQUIRED/INCOMPLETEจนตรวจผ่าน|ใช้model/checkpoint/input/detector/source/protocol/GT bindings+atomiccommit ไม่เดาจากcounter/ชื่อTRAINfingerprint; ไม่อนุมัติrecoveryเพิ่มในเอกสารนี้|

Full-population primary metrics ของแต่ละ configurationพร้อมได้เมื่อ **exact5,000 unique expected IDs** และ predictions/scoring/provenanceครบตาม common protocol เท่านั้น งาน partialยังอยู่ในตารางพร้อม complete/failed/invalid/missing/not-attempted และmainnull ไม่ inferenceซ้ำเพื่อจัดเอกสาร Pilot6IDsมี completenessแยกจาก5,000 ไม่ทำให้fullbenchmark COMPLETEโดยปริยาย

Common runต้องมี protocol ID/revision+mapping+population/GT/evaluator/source/model/route hashes และ source packet refs ผลเขียนfresh common-view directory แยกจากnative20; ห้ามoverwrite source `prediction.npz`, `score_*.json`, `CONFUSION.npy` หรือ METRICS เดิม คงCPIพัก/nullจนมีคำสั่งแยก

## 6. Sapiens2 route ที่แนะนำ: full-frame semantic + frozen YOLO mask ownership

เสนอ **`SAPIENS_FRAME_YOLO_MASK_OWNERSHIP`** ไม่เรียก native person-instance parser และไม่ใช้ GT crop หลักฐานคือ [official full-frame vis_seg.py](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/sapiens/dense/tools/vis/vis_seg.py), native test pipeline และ historical local `Human_Parsing_CCIHP_10_Image_Pilot/scripts/run_sapiens2.py` ที่อ่านอย่างเดียว ใช้เป็น feasibility/design evidence ไม่ใช่การรับรอง route ใหม่บน CIHP cohort นี้

|ส่วน|ข้อเสนอที่ชัดเจน|
|---|---|
|Input/context|JPEG bytes/decodedRGBเดียวกับCIHP population; **full frame**ทั้งภาพ ไม่มีcropหรือขยายYOLO bbox ไม่มีROIpadding; YOLOไม่ได้ป้อนเข้าsemanticmodel ใช้เป็นownershipหลังforward|
|Resize|pinned SegResize: H1024×W768,keep_ratio=False (stretch); ใช้ code interpolationเดิม: INTER_AREA ถ้า newW<originalW ไม่เช่นนั้น INTER_CUBIC ไม่สลับเองตามquality|
|Normalize/padding|ส่งBGRเข้าofficialpreprocessorให้bgr_to_rgb=True; mean[123.675,116.28,103.53],std[58.395,57.12,57.375] ไม่double-swap; pad_size_divisor default1จึงไม่มีspatialpad; logactualpipeline/geometry|
|Execution|0.4Bสำหรับpilot; FP32parameters/input/logits,batch1,eval,inference mode,noAMP/autocast/TF32,noเพิ่มflip/multiscaleTTA/CPUoffload/FP16fallback; คงและบันทึกnativeinternalpositional-encodingdtype ไม่อ้างว่าfloatingpointทุกoperationเป็นFP32; training config warmup_iters500 และvalbatch4ไม่ใช่คำสั่งinferencepilot|
|Map-back|bilinear **logits29** กลับoriginalH,W,align_corners=False แล้วargmax; ไม่bilinearresizeintegerlabels ไม่cropGTเพื่อmapback|
|Ownership|อ่านfrozenYOLO ledger/cacheเดิมตามimage/detectorhash สร้างหนึ่งplaneต่อnonemptycachedmask E_j; L_j=where(E_j,nativeSemantic29,0); scores=YOLOconfidence,identity=YOLOopportunity ไม่มีnativepersonIDsให้เรียกเป็น0detectednativepeople (ใช้N/A)|
|Boxes/association|boxesเก็บเป็นmetadata/identityของopportunity ไม่ใช่GTหรือcrop; ไม่สร้างbbox-IoU associationกับSapiens nativeinstancesที่ไม่มี; finalpred↔GTmatchingอยู่เฉพาะscorer|
|Clipping/overlap|maskclipหลังargmaxตามcachedYOLOmasks คงextentsรวมถึงส่วนซ้อน ถ้ามี; globalnativepositivecomposeตามscore/indexแล้วproject ไม่มีnewNMS/GTguidedownerrepair Extentแม้semanticsไม่มีtargetยังเก็บ|
|ไม่มีYOLOdetections|ยังทำfullframeforwardหนึ่งครั้งตามrouteและเก็บnativeglobaldiagnostic; finalpersons=[]/globalBG validempty,eligibleGTFNตามจริง ไม่สร้างคนใหม่จากGT/semanticislands|

เสนอreuseenvironment `.venvs/sapiens2-pilot` ที่มีอยู่ ตรวจexactPython/package/sourcebindingsในreadinessก่อนexecute ไม่ติดตั้งเพิ่มจากข้อเสนอนี้

ใช้frozenYOLO26x weights/settings/cacheเดิม imgsz640/conf0.25/iou0.7/max_det200/retina_masks=True ตามbindingในdraftspec; ไม่inferenceYOLOใหม่ในpilotที่เสนอ IdentityของSapiens applicationมาจากYOLO; **extentF1จะพึ่งYOLOโดยตรง** และถ้าcache/matchingเหมือนQANetคาดว่าextentmetricsเท่ากันจากmasksource ไม่ใช่หลักฐานว่าความสามารถnativeinstancesเท่ากัน ต้องตรวจcontractด้วยCPU/savedmask ไม่ทดสอบด้วยการเพิ่มdetectorrun

## 7. ความเทียบกันได้กับสี่ route ที่รันจริง

|ระบบ|Inputและownershipที่เกิดจริง|Harmonizeย้อนหลังได้|สิ่งที่ทำให้เหมือนกันย้อนหลังไม่ได้|
|---|---|---|---|
|QANet|frozenYOLOboxes→nativeROIAlignปรับaspect; original-gridsemanticsclipด้วยYOLOmasks; finalextents/scoresจากYOLO|C4mapping/domain/metric, compose/tie,sourceidentity; Sapiensใช้cachedextentsชุดเดียวได้|cropcontext/ROIresolution/nativeTTAของQANetเทียบfullframeSapiensไม่เหมือนกัน; hardmaskแก้ข้อมูลinputย้อนหลังไม่ได้|
|M2FP/D2FP|nativefullframe/TTA; nativehumanscores resolveownershipก่อนexport; retainnativeinstancesที่prediction-onlybboxassociationกับYOLOIoU0.5ผ่าน; ไม่clipnativeextentด้วยYOLOmask|sameGT/mapping/metrics; retainstorednativeownership/association; hardmaskprojection|nativehumanproposal/overlap arbitration/nativeconfidenceและTTAไม่ใช่YOLOmaskownership; recoverpre-arbitrationprobabilitiesจากhardmaskไม่ได้|
|RP-R-CNN|nativeinternaldetector+parsingfullframe; extent=parsingforeground; YOLOassociation0.5gatesinstances; internaldetectorยังอยู่|sameGT/mapping/metrics, validOther/FPFN; emptyextentไม่สร้างfilledbbox|internaldetection/proposals/context/nativefilteringไม่เท่ากับmaskconditionedroute; ไม่มีสิทธิ์เพิ่มsilhouetteแทนempty parsing|
|Sapiens proposed|fullframe29semantic→YOLOmaskclip/identity; ไม่มีnativeinstances|sameGT/scoretask/YOLOcacheกับapplicationอื่น|inputไม่เท่าQANetROIและidentityไม่ใช่nativeprediction; routeนี้ยังไม่implemented/verifiedในcohort|

EligibilityของC4-Pให้configurationที่ส่งoutputcontractครบ/GTdomain/metricเดียวกันและรันครบเข้าตารางtaskนี้ได้; semantic-equivalenceยังไม่verifiedไม่ถูกแอบเปลี่ยนเป็นverifiedเพื่อจัดอันดับ ต้องแสดงชนิดprojection/claimlimitationsในแถวนั้น การรับC4-Pเป็นtaskยังไม่ใช่การรับรองว่าselectedconfigurationผ่านstrictfaceและDressrequirements

จึงเป็น **pretrained checkpoint + application-configuration comparison** ภายใต้ task/domain/metricsเดียวกัน รวมapplicationตารางเดียวได้เมื่อcontractผ่าน ไม่ใช่architecture-only/native-parser rankingหรือ zero-bias comparison Nativeungatedreferenceแยกตาราง ไม่กลายเป็นapplicationwinner

ถ้าต้องตอบผลของparserโดยควบคุมROIให้เท่ากันจริง ต้องทดลองSapiensYOLO-ROIและadaptersที่รับcropได้ด้วยcrop/context/resize/ownershipcostเดียวกัน หรือออกfullframeownershipcontrolledtaskใหม่ นั่นต้องinferenceเพิ่มและอาจเปลี่ยนธรรมชาติnativeinstanceparsers ไม่จำเป็นต่อคำอ้างapplicationconfigurationปัจจุบัน **จึงไม่สั่งrerunทุกตัว** การunclip/re-maskบางhardoutputsทำได้เชิงเทคนิคแต่เปลี่ยนconfiguration ต้องแยกprotocol ไม่แก้ผลเดิมเงียบ ๆ

Timing/VRAMเดิมยังเป็นadapter/shared-GPUdiagnostics มีขอบเขตต่างกัน ไม่ใช้จัดอันดับefficiencyของcommonview การmappingให้เหมือนกันไม่ได้ทำให้input/trainingexposure/runtimeเท่ากัน Training/pretrainingoverlapที่UNKNOWNยังเป็นUNKNOWN ไม่เรียกNOหรืออ้างควบคุมarchitecture/dataทั้งหมด

## 8. สิ่งที่ทำจาก artifacts ได้ กับสิ่งที่ต้องเพิ่ม

|งาน|จากข้อมูลที่มีทำได้หรือไม่|ข้อกำหนด/ผลกระทบ|
|---|---|---|
|GlobalC4ของสี่ระบบ|ทำได้โดยไม่inference จากcanonicalCONFUSION20×20ที่ตรวจพบ|ยังไม่ทำในรอบนี้; projectconfusionแล้วratioใหม่; preserveoriginals/derivefreshcommonrevision|
|รายpersonQ/G_sem/rejection/ownership|ทำได้จากsavednativehardplanes/extents/scores+GT+packetbindings|ต้องCPUscorer/domainmaterializationและอ่านsavedmasks ไม่ใช้scalarQเดิมหรือglobalconfusionแทนperpersonstats|
|Face/Dressdiagnosticsและภาพ|savedRGB/GT/nativehardlabelsเพียงพอสำหรับcounts/overlays/qualitative|ไม่ใช้native-classagreementเพียงอย่างเดียวยืนยันphysicaltruth ไม่เปลี่ยนmappingเพราะdiagnosticคะแนนต่ำ|
|SapiensCIHPcanonicalpackets|ยังไม่มีตามroute/cohortใหม่นี้|ต้องseparateauthorizedpilot/inference HistoricalCCIHP10ภาพไม่ใช่canonicalCIHPVAL5,000แม้เป็นภาพตระกูลเดียวกัน|
|Face-onlyจากFace_Neck หรือ upper/lowerจากDress|ทำไม่ได้losslesslyจากhardlabelsที่มี|ต้องannotation/additionalmodel/newtask ไม่heuristicsหรือGTช่วยprediction|
|Probability-union,calibration,softmetrics/APทุกแบบ|ไม่รองรับครบจากcanonicalhardmasks|nativepixelprobabilities/partconfidencesสูญไปแล้ว confidenceที่มีส่วนใหญ่ระดับperson/YOLO ไม่fabricateเป็นsemanticprobability; optionalpilotlogitrecordไม่ทำให้สี่ระบบเก่ากู้logitsได้|
|Timing/VRAMranking|ไม่รองรับจากชุดนี้|ต้องcleanmatchedprofileแยกหากได้รับอนุมัติ ไม่เอาYOLOcachedreadtimeเป็นYOLOinference|

## 9. เกณฑ์ตรวจ implementation (หลักฐาน actual revision2 อยู่ใน pilot report)

ให้ implement common projection/scorer/reporter **แยกmodule/config/outputversion** จาก frozennativepipeline เริ่มCPUexpectedcasesก่อนmodelpilot ใช้packetจริงเดิมเฉพาะread-onlygeometry/integration; ไม่รับรองevaluatorจากtestcount

|งาน|วิธีตรวจรับ/expected evidence|เพดาน/เงื่อนไขหยุด|
|---|---|---|
|Totalmapping/domain|CIHP0–19,Sapiens0–28ครบไม่ซ้ำ;255GTvoid/pred255invalid;validdomainhash/GTeligiblemanifestเหมือนทุกโมเดล|schema+smallsyntheticsก่อน; unknownID/bindingผิดหยุด ไม่เติมBG|
|Compose/project/union|independentoraclecasesด้านล่าง ผ่านactualpacket→scorer→reporter; compareHprojectionกับpixelprojectionบนtinyarrays|ไม่รัน5,000เพื่อdebug ไม่averageoldIoU|
|Geometry/ownership|originalgriddimensions,asymmetriccornermarkers/flip/channelorder/fullframe/cropmetadata; targetsemanticsอยู่withinrecordedextent; identityrenameinvariance|tinycases+savedpacket1caseต่อ4ระบบก่อน ใช้หลักฐานselected64เดิมต่อได้ ไม่fullauditscanซ้ำ|
|Denominators/empty/FPFN|materializeG_loc/G_semจากGTprojection;wrongclass,miss,duplicate,semanticempty,void/exacttiecasesพร้อมrationalexpectedvalues|ให้artifactscanGTeligibilityเมื่อได้รับอนุมัติimplementation ไม่claim17,520ล่วงหน้า|
|Route/export|newSapiensadapterตามข้อ6; strictnative29labels/geometry,model/checkpoint/config/source/env/detectorhashและstagecontractครบ;noGTinput|codeinspection/CPUfixtureก่อนGPU; nohiddenretry/fallback;pilotแยกคำสั่ง|
|Isolation/immutability|hashnativeconfig/source/resultsก่อนหลัง;uniqueprotocol/model/input/detector/route/GTfingerprints;newatomicdirectory;CPIpartialไม่เข้าcompletepopulation|ห้ามใช้TRAINfingerprintเดิมที่ซ้ำข้ามmodelเป็นidentityเดียว; collisions/staleoutputหยุด|
|Reconciliation/resources|firstcompletepacketreadback,atomiccommit+immutableattemptledger;simulateinterruption/orphanonlyCPUsynthetic; logstorageretained/temp/peak/attemptcost|ไม่อนุมัติautomaticexternal/modelretryเพิ่มจากเอกสารนี้; realOOMหยุดเก็บหลักฐาน|

### 9.1 Expected results ที่คำนวณได้โดยอิสระ

ค่าต่อไปนี้เป็น **expectedrequirementsfixtures**; การตรวจจริง22CPUcasesและsavedpacketintegrationระบุในpilotreport/CPU_ACCEPTANCE.json ไม่ใช้เพียงจำนวนtestsรับรองทุกเส้นทาง ใช้ arraysเล็กที่เขียนค่าตรงและexpectedfractionsคำนวณมือ ห้ามgenerateexpectedจากfunctionunder-test ยืนยันnumericresultsกับreporterไม่ใช่เพียงprocessreturn0

|กรณี|Expected results|
|---|---|
|Perfect6pixels GT=pred[Face,Hair,Upper,Lower,OTHER,BG]|confusiondiagonal6;IoUtargetsทั้ง4=1,mIoU4=1;person1perfectextent/targets→TP1FP0FN0,Q1|
|สลับUpper/Lowerบนสองtargetpixels ที่เหลือFace/Hairถูก|Upper/LowerIoU0,Face/Hair1,mIoU4=0.5 ไม่กลายเป็นperfectเพราะถือว่าเสื้อผ้าทั้งหมด|
|NativeCIHPGT[5,5,7,7,7],prediction[7,7,5,5,5]|nativeUpper/CoatIoUทั้งคู่0 แต่หลังunionUpperมีTP5,U5,IoU1; ส่วนfixedC4macroในfixtureนี้=1/4ตามabsentzero convention แสดงว่าห้ามaverageoldIoUแทนunion|
|OTHER→targetและtarget→OTHER: GT[OTHER,Upper],pred[Upper,OTHER]|UpperTP0,FP1,FN1,IoU0;recognizedDress/Apparelคือvalidexecution ไม่INCOMPLETE|
|Overlaplow-scoreUpper/high-scoreDressหรือApparelที่พิกเซลเดียว|nativewinnerเป็นDress/Apparel→OTHER;ไม่เหลือUpperให้คะแนน ห้ามdropOTHERก่อนcompose|
|UnionBG/OTHERไม่แอบเพิ่มคะแนน|GT[OTHER,BG],pred[OTHER,OTHER]ไม่มีtargetTP;allfourtargetIoU0/zero-unionflagsตามsupport;BG↔OTHERconfusionเก็บครบ|
|Semantic-emptyextent|GTpersonมีUpper,matchedvalidextentpredsemBGหรือOTHER-only→TP1,FP0,FN0,extentF1=1,Q0 ไม่ถือmissedextentหรือexecutionfailure|
|No-personoutput|GTperson1มีtarget,predpersons=[]→TP0FP0FN1,F1=0,Q0;globalBGทำtargetFN;validemptyCOMPLETE|
|Duplicatepersons|GT1personUpper,pred2identicalperfectpersons→TP1FP1FN0,F1=2/3,Q1,globalUpperIoU1;แสดงว่าQ/semanticIoUไม่ลงโทษduplicateครบจึงต้องมีpersonmetrics|
|สองGTpersonsคนละ1pixelมีUpper,predextent1ครอบ2pixels/predUpperทั้งสอง|ที่.50จับคู่ได้1,TP1FP0FN1,F1=2/3;matchedpersonUpperIoU1/2,unmatched0,Q=(1/2)/2=1/4;globalUpperIoU1;matchedtargetcontamination1/2 ที่.75ไม่มีmatch→TP0FP1FN2,Q0|
|IDrename/semanticownershipwrong|bijectionเปลี่ยนGT/predidentityชื่ออย่างเดียวไม่เปลี่ยนmetrics;สองextentถูกตำแหน่งแต่สลับUpper/Lowersemanticassignment→extentF1ยัง1แต่Q0 ห้ามใช้extentF1แทนsemanticownershipcorrectness|
|SharedVOID|เพิ่มGT255pixelพร้อมpredtargetที่จุดนั้นไม่เปลี่ยนconfusion/Q/extent-domainของทุกโมเดล;pred255บนanypixelยังinvalidตามoutputcontract|
|Ownerunknown|GTFace/Human0pixelเข้ากlobalFacecountsแต่ไม่เข้าG_sem/personsemanticdomain;sameVpทุกระบบ|
|Zeroeligibility/emptyclass|G_sem0→Qnullพร้อมreason;zero-unionclassIoU0fixedmacro,precision/recall0denominator→null;ไม่แทนmissingfailureด้วย0|
|Tie/ordering|equalIoUeligiblepairsเลือกlexicographicallyfirstoptimalgeometryorderและstablefallbackเฉพาะidenticalgeometry;scoretieglobalเลือกlowerpacketindex;เปลี่ยนfilesystemiterationorderไม่เปลี่ยนผลเมื่อpacketindicesคงเดิม|
|Contractfailure/partialoutput|unknownnativeID,shapeผิด,NaNscoreหรือmissingcommit→invalid/incomplete/mainnull;recognizedunsupportedยังCOMPLETE;interruptionเก็บorphanไม่reuseจนfingerprintsreconcile|
|Isolation|packet/GTsameแต่เปลี่ยนprotocol/source/checkpoint/detectorbindingต้องไม่reusewrongcache;ไม่overwriteoriginalnativeartifact;roundtripJSONใช้nullไม่NaN|

กรณีwrongclass/duplicateที่มีเพียงsubsettargetsให้แยกexpectedtargetIoUกับfixedfourmacroอย่างชัดเจน การทดสอบintegrationต้องครอบคลุมทั้งglobalและpersondefinitionsไม่ใช้scorerเฉพาะนาทีสุดท้ายที่wrapperเปลี่ยนค่าทิ้ง

## 10. Pilot ที่เสนอ: Sapiens2 0.4B เพียงหนึ่งขนาด

**AUTHORIZED_CONDITIONAL_ON_CPU_AND_READINESS — pilotเท่านั้น** actuallaunch/completionดูpilotreport ใช้6ภาพจากfrozen16เดิม ไม่ใช้modelscoreเลือก:

|ลำดับ|ID|เหตุผลcoverageที่ล็อกก่อนSapiensCIHPscore|
|---|---|---|
|1|0021448|firstseededstratumcase มีHair/Coat/Pantsและหลายคน;เริ่มตรวจnativegrid/ownership|
|2|0006909|firstfrozenDress+Skirtcase พร้อมUpper/Coat/Pantsและcrowd;ตรวจOTHERและunion|
|3|0001538|close-upFace/Hair/Torso-skin;ตรวจFace_Neckproxyและoriginalmapback|
|4|0001413|HairGTabsentในภาพ,มีHat/Coat/Face;ตรวจabsenttargetและrecognizedOTHER|
|5|0027897|wide831×300frame มีDress/Coat;ตรวจstretch/geometry/sizeและoverlap|
|6|0031248|portrait500×750frame มีDress/Pants;ทดสอบaspectoppositeของwidecase|

นี่เป็นcoveragepurposivesample ไม่ใช่randomperformanceestimate/annotationerrorprevalence และไม่ใช่independentconfirmationเพราะเป็นVALที่เลือกจากGTหลังผลสี่โมเดลมีแล้ว SyntheticzeroYOLO/duplicate/empty/VOIDcasesทดสอบCPU ไม่เพิ่มGPUเพื่อหาcornercaseโดยสุ่มไปเรื่อย ๆ

**เพดานที่เสนอ:** checkpoint `Sapiens2_0.4b` ที่bindเดิม เพียงหนึ่งconfiguration; ≤1TRAIN0000930warmupที่ไม่score +6VALdiagnosticframecalls = **≤7model-framecalls**, batch1,FP32,noextraTTA,oneattempt/image,automaticmodel/OOMretry0 ไม่รัน0.8B/1Bหรือ5,000ในpilot ไม่rerunสี่ระบบเดิม ถ้าหยุดก่อนครบretainpartialไม่relaunchเอง

- ตรวจGPU/process/freeVRAMจริงและsource/env/readinessเดิมก่อนlaunch; ขนาดweights/อดีตpilotไม่รับประกันpeakactivation/fragmentation/jointresidencyของserverขณะนั้น ไม่เพิ่มfreshYOLOtimingrunและไม่เปลี่ยนshared/exclusiveadmissionเงียบ ๆ
- ใช้24h/80GiBstream/free-spaceguard50GiBเป็น**ขอบบนที่เสนอสำหรับpilot** ไม่ใช่estimateว่าจะใช้เท่านั้นหรือรับรองพื้นที่รวมพอ ต้องวัดretainedbytes+sharedreferences+temporary/atomicpeak+headroom/ทุกattemptก่อนอนุมัติbatchใหญ่ ไม่มีETA/totalstorageที่แต่งขึ้นจากweights
- Stopครั้งแรกเมื่อOOM/CUDAerror/nonfinite/invalidlabel/geometryผิด/hashbindingผิด/free-spaceหรือtimeguardถึง เก็บtraceback/geometry/peakallocated+reserved/observeddeviceusageถ้าวัดได้ ไม่ลดresolution/precision/batch/fallbackหรือretryเพื่อให้ผ่าน
- บันทึกnative29originalhardmask,perpersonplanes/extents/scores/YOLOidentity,mapback/resize/padding/channelmetadata,source/checkpoint/config/env/detector/inputhashes,nativefullframereference,execution/scoringledgerและatomiccommits แยกdiagnosticrun/protocol ทุกframe
- Optionalpilotlogitsเฉพาะ6ภาพเป็นsidecarได้เมื่อวัดdiskbudgetก่อน;ไม่จำเป็นต่อhardlabelC4Pและไม่ทำให้ย้อนหลังทุกโมเดลรองรับsoftmetrics ห้ามเก็บonlymergedclasses/overlayแทนnative29
- **ผ่านpilotเชิงengineering:** expectedCPUcasesผ่านactualpacket→scorer→reporter,6/6artifacts/geometry/nativeIDs/readback/bindingsถูกต้อง,G_loc/G_semและsupportreconciled,ไม่มีhiddenfallback/retry,ไม่แก้sourceGT/nativeoutputs ไม่ตั้งminimumIoUเพื่อผ่านreadiness และไม่เรียกว่าทุกtaxonomyเทียบเท่าหรือfull5,000จะผ่านแน่
- ถ้าpilotพบimplementationbug ให้เก็บrevision/attemptเดิม ระบุreason+affectedscope แก้spec/codeแล้วออกrevisionใหม่และตรวจทุกระบบ/ภาพที่กระทบเหมือนกัน ห้ามเลือกrevision/settingที่VALscoreดีที่สุด หากเป็นเพียงคะแนนต่ำตามpolicy ห้ามแก้mappingเพื่อช่วยโมเดล

## 11. สิ่งที่ยังค้างจริงและผลต่อการตัดสิน

|ข้อค้าง|ผลต่อoperationalC4-P|ผลต่อstrictclaim/สิ่งที่ต้องทำเพิ่ม|
|---|---|---|
|CIHPFaceเทียบSapiensFace_Neckpartitionไม่มีdetailedmanualครบ|ยังทดลองFaceproxyagainstCIHPreferenceได้ โดยpenaltyทุกpixelคงเดิมพร้อมdiagnostics|ยังรับรองface-onlycapability/equivalenceไม่ได้;ถ้าเป็นharddeploymentrequirementต้องมีannotation/โมดูลใหม่ก่อนselectedstrictconfiguration|
|GarmentpartitionของSapiensและApparelทุกชนิดไม่ครบ|maptotalและOTHERpolicyทดลองได้ ไม่ต้องเดาApparel=Dress|ไม่อ้างallclothingcoverageหรือupper/lowerDress;เพิ่มgarmentboundaryreferenceหากต้องการคำถามนั้น|
|G_sem/commonbindingsยังไม่materialize|ห้ามเผยแพร่commonpersonscore/claimdenominatorตอนนี้;เป็นงานCPUimplementationถัดไป|ไม่ได้แก้ด้วยcopy17,520หรือเลือกเฉพาะmatchedpersons|
|Sapiensrouteยังไม่verifiedในcohortนี้|ต้องtargetedpilotก่อนrunproposalใหญ่|อดีตfullframepilotsไม่แทนapplicationcontract/VRAMverificationรอบนี้|
|Exposure/input/ownershipต่างกัน|controlsameGT/task/scoreและreportconfigurationdifferences|ไม่แยกผลarchitecture/trainingdata/adapterหรือรับรองunseenimage/generalCCTVperformance|

**ไม่ต้องให้ผู้ใช้ตัดสินทุกแถวใหม่:** ข้อเสนอหลักคือ C4-P operational question ตามนิยามด้านบน พร้อมFaceapproximation/C3sensitivity/rejectiondiagnostics;ถ้ารับแนวนี้ งานถัดไปที่มอบหมายได้คือ implementแยกmodule +independentCPUacceptancecases+GTdomainbindings คำอนุมัติpilot≤7calls/sharedGPUได้รับโดยตรงแล้วในrevision2; fullscoring/รุ่นอื่นยังไม่อนุมัติและต้องแยกคำสั่ง ไม่ขออนุมัติpilotขั้นตอนปกติซ้ำ

## 12. ประวัติ proposal-1 และการส่งต่อ (ก่อน implementation)

รอบนี้อ่านsource/config/report/bindingsที่เกี่ยวข้อง,ตรวจGT16masksแบบจำกัด/เปิด2ambiguityimages,ตรวจexistingpacketfieldsหนึ่งภาพต่อสี่ระบบและcanonicalglobalconfusion4ชุดเท่านั้น ไม่คำนวณcommonviewscores ไม่โหลดโมเดล ไม่รันtestsuiteหรือinference

แก้ถ้อยคำในรายงานสี่โมเดลให้ระบุว่า **QANet recallสูงกว่าที่matching0.50;ที่0.75 M2FPสูงกว่าเล็กน้อย** โดยไม่เปลี่ยนตัวเลขทดลอง การแก้reportgeneratorเฉพาะถ้อยคำป้องกันข้อความเดิมกลับมา ไม่แก้execution/scoringcode NativepresentationZIP/รูปเดิมเป็นhistoricalsnapshotของworkunitก่อน ไม่เขียนทับให้ดูเหมือนรู้ข้อเสนอนี้ก่อนrun

[Consistency checks](../runs/common-view-proposal-20261029T004437Z/CONSISTENCY_CHECKS.json) แยกdocumentation/schema/sourceidentitychecksออกจากexecutionacceptance; [WORK_LOG](../WORK_LOG.md), [STATUS](../STATUS.md), [PLAN](../PLAN.md) ระบุสถานะ **PROPOSED_NOT_FROZEN / NO_NEW_INFERENCE** เหมือนกัน Draftmatrix/bindingsเดิมยังอยู่ครบและไม่ยกระดับequivalenceเพราะมีข้อเสนอนี้

## ภาคผนวก: complete native-ID projection


### CIHP_GT_AND_NATIVE_PRED

|Native ID|Native label|Common ID/name|บทบาท|
|---|---|---|---|
|0|Background|0 BACKGROUND|VALID_BACKGROUND|
|1|Hat|5 OTHER|VALID_OTHER_NEGATIVE|
|2|Hair|2 HAIR|SCORED_TARGET|
|3|Glove|5 OTHER|VALID_OTHER_NEGATIVE|
|4|Sunglasses|5 OTHER|VALID_OTHER_NEGATIVE|
|5|UpperClothes|3 UPPER_NON_DRESS_FAMILY|SCORED_TARGET|
|6|Dress|5 OTHER|VALID_OTHER_NEGATIVE|
|7|Coat|3 UPPER_NON_DRESS_FAMILY|SCORED_TARGET|
|8|Socks|5 OTHER|VALID_OTHER_NEGATIVE|
|9|Pants|4 LOWER_NON_DRESS_FAMILY|SCORED_TARGET|
|10|Torso-skin|5 OTHER|VALID_OTHER_NEGATIVE|
|11|Scarf|5 OTHER|VALID_OTHER_NEGATIVE|
|12|Skirt|4 LOWER_NON_DRESS_FAMILY|SCORED_TARGET|
|13|Face|1 FACE_CIHP_REFERENCE|SCORED_TARGET|
|14|Left-arm|5 OTHER|VALID_OTHER_NEGATIVE|
|15|Right-arm|5 OTHER|VALID_OTHER_NEGATIVE|
|16|Left-leg|5 OTHER|VALID_OTHER_NEGATIVE|
|17|Right-leg|5 OTHER|VALID_OTHER_NEGATIVE|
|18|Left-shoe|5 OTHER|VALID_OTHER_NEGATIVE|
|19|Right-shoe|5 OTHER|VALID_OTHER_NEGATIVE|

### SAPIENS2_DOME29_PRED

|Native ID|Native label|Common ID/name|บทบาท|
|---|---|---|---|
|0|Background|0 BACKGROUND|VALID_BACKGROUND|
|1|Apparel|5 OTHER|VALID_OTHER_NEGATIVE|
|2|Eyeglass|5 OTHER|VALID_OTHER_NEGATIVE|
|3|Face_Neck|1 FACE_CIHP_REFERENCE|SCORED_TARGET|
|4|Hair|2 HAIR|SCORED_TARGET|
|5|Left_Foot|5 OTHER|VALID_OTHER_NEGATIVE|
|6|Left_Hand|5 OTHER|VALID_OTHER_NEGATIVE|
|7|Left_Lower_Arm|5 OTHER|VALID_OTHER_NEGATIVE|
|8|Left_Lower_Leg|5 OTHER|VALID_OTHER_NEGATIVE|
|9|Left_Shoe|5 OTHER|VALID_OTHER_NEGATIVE|
|10|Left_Sock|5 OTHER|VALID_OTHER_NEGATIVE|
|11|Left_Upper_Arm|5 OTHER|VALID_OTHER_NEGATIVE|
|12|Left_Upper_Leg|5 OTHER|VALID_OTHER_NEGATIVE|
|13|Lower_Clothing|4 LOWER_NON_DRESS_FAMILY|SCORED_TARGET|
|14|Right_Foot|5 OTHER|VALID_OTHER_NEGATIVE|
|15|Right_Hand|5 OTHER|VALID_OTHER_NEGATIVE|
|16|Right_Lower_Arm|5 OTHER|VALID_OTHER_NEGATIVE|
|17|Right_Lower_Leg|5 OTHER|VALID_OTHER_NEGATIVE|
|18|Right_Shoe|5 OTHER|VALID_OTHER_NEGATIVE|
|19|Right_Sock|5 OTHER|VALID_OTHER_NEGATIVE|
|20|Right_Upper_Arm|5 OTHER|VALID_OTHER_NEGATIVE|
|21|Right_Upper_Leg|5 OTHER|VALID_OTHER_NEGATIVE|
|22|Torso|5 OTHER|VALID_OTHER_NEGATIVE|
|23|Upper_Clothing|3 UPPER_NON_DRESS_FAMILY|SCORED_TARGET|
|24|Lower_Lip|1 FACE_CIHP_REFERENCE|SCORED_TARGET|
|25|Upper_Lip|1 FACE_CIHP_REFERENCE|SCORED_TARGET|
|26|Lower_Teeth|1 FACE_CIHP_REFERENCE|SCORED_TARGET|
|27|Upper_Teeth|1 FACE_CIHP_REFERENCE|SCORED_TARGET|
|28|Tongue|1 FACE_CIHP_REFERENCE|SCORED_TARGET|

GT255=sharedVOID; prediction255/unknownID=contractfailure. ชื่อtargetที่เท่ากันเป็นoutputtaskเดียวกัน ไม่ใช่หลักฐานว่าsourceannotationboundaryเท่ากัน รายละเอียดevidence/projection/eligibilityแยกคอลัมน์ในCSVและdraftspec

## Revision-2 ก่อน pilot scores — 2026-10-29T08:20:28.215191+07:00

ผู้ใช้รับรองให้แก้ties/C3และimplement+CPUacceptanceก่อนSapiens0.4Bpilot≤7calls/sharedGPUโดยตรง ไม่ต้องขอซ้ำ Nativepipeline/source/resultsไม่เปลี่ยน Counterexampleเดิมมี2GTpixels/2identicalpredextents (IoU.5ทุกคู่):stableGT-IDmatchingให้Q1ก่อนrenameและQ0หลังrename, geometrycanonicalให้Q1ทั้งสอง; identicalgeometryambiguityยังรายงานไม่ใช้semanticเลือกคู่ C3มีglobalmeanเท่านั้นไม่มีpersondenominatorอีกชุด. Currentbindings/acceptance/outcomeใน [pilotreport](CIHP_SAPIENS_04B_PILOT_TH.md); [amendment](../runs/common-c4p-pilot-20261029T010410394659Z/PROTOCOL_AMENDMENT.json). เก็บproposal-1specเดิมและGithistory; full5,000scoringและ0.8B/1Bยังไม่อนุมัติ
