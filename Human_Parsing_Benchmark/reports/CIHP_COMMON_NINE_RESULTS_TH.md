# ผล Human Parsing common C4-P ครบเก้า checkpoints — สรุปสำหรับตรวจต่อ

อัปเดต **2026-10-30T11:11:02.674074+07:00 (เวลาไทย UTC+07)** · **COMMON_C4P_COMPLETE_9_OF_9** · งานเพิ่มรอบนี้คือ saved-only CPI สองระบบ ไม่มี model inference ใหม่

## ผลที่ครบแล้วและคำตอบหลัก

checkpoint ทั้งเก้าตัวมีคะแนน common C4-P revision2 บน **official CIHP Validation ชุดเดียวกัน 5,000 unique IDs ต่อระบบ** แล้ว ตารางหลักใช้ full-precision canonical statistics ก่อนปัดเศษ ไม่ใช่ค่าจากแชท คะแนนสูงสุด global C4-P ในกลุ่มนี้คือ **M2FP_R101_CIHP** เป็น semantic quality leader ของ checkpoint พร้อม application configuration นี้ ไม่ใช่ architecture-only winner หรือการรับรองพร้อมใช้งาน CCTV

|Metric|คะแนนสูงสุด|IoU/mean %|อันดับถัดไป|ส่วนต่าง pp|
|---|---|---|---|---|
|Hair|M2FP_R101_CIHP|82.760|D2FP_R101_CIHP|0.754|
|Face ตาม CIHP reference|M2FP_R101_CIHP|88.111|QANet_CIHP_HRNetW48_512x384|0.416|
|Upper non-Dress|M2FP_R101_CIHP|85.563|D2FP_R101_CIHP|1.260|
|Lower non-Dress|M2FP_R101_CIHP|78.056|D2FP_R101_CIHP|1.351|
|C4-P mean|M2FP_R101_CIHP|83.623|D2FP_R101_CIHP|1.013|

ส่วนต่างเป็น **percentage points (pp)** ไม่ใช่ relative percent; เป็น descriptive comparison ไม่มี uncertainty interval/statistical-significance claim ไม่สร้าง weighted overall score เพิ่ม การเลือก deployment ยังต้องดู person Q/FP/coverage และ capabilities ที่งานต่อไปต้องใช้

## 1. ตารางหลัก — frozen roster order

|ระบบ|Hair IoU %|Face ref. IoU %|Upper %|Lower %|C4-P %|C3 %|ครบ|
|---|---|---|---|---|---|---|---|
|QANet_CIHP_HRNetW48_512x384|79.919|87.695|81.870|74.452|80.984|78.747|5,000/5,000|
|M2FP_R101_CIHP|82.760|88.111|85.563|78.056|83.623|82.127|5,000/5,000|
|D2FP_R101_CIHP|82.006|87.423|84.303|76.706|82.610|81.005|5,000/5,000|
|RPR_CIHP|77.708|84.794|81.356|71.131|78.747|76.732|5,000/5,000|
|CPI_R50_CIHP|79.344|85.794|79.259|69.983|78.595|76.195|5,000/5,000|
|CPI_ConvNeXtB_CIHP|81.220|87.023|83.777|75.824|81.961|80.274|5,000/5,000|
|Sapiens2_0.4b|80.101|72.196|76.736|74.278|75.827|77.038|5,000/5,000|
|Sapiens2_0.8b|78.942|72.648|75.867|71.015|74.618|75.275|5,000/5,000|
|Sapiens2_1b|77.427|70.175|71.778|71.657|72.759|73.621|5,000/5,000|

Face คือ agreement กับ **CIHP reference Face**; Sapiens ใช้ Face_Neck รวม facial subparts เป็น proxy ซึ่งแยก neck จาก hard mask ไม่ได้ Hair/Upper/Lower ใช้ mapping revision2 เดิม Upper = CIHP UpperClothes+Coat, Lower = Pants+Skirt; Sapiens Upper_Clothing/Lower_Clothing ไม่รับรอง annotation-boundary equivalence Dress/Apparel เป็น valid OTHER ไม่แบ่งด้วย heuristic และไม่ ignore รายโมเดล

Primary C4-P = unweighted mean IoU ของสี่ target; C3 เป็น global mean Hair/Upper/Lower เท่านั้น ไม่มี Q_C3 ไม่รวม BG/OTHER ใน macro แต่ทั้งสองยังเป็น valid negatives: target บน OTHER เป็น FP และ OTHER บน target เป็น FN; Face ยังเป็น negative ที่ valid ใน C3 GT255 เป็น shared VOID, prediction unknown/255 contract failure ไม่มีเปลี่ยน policy หลังเห็นผล

สะสม global confusion ทั้งประชากรก่อนหาร IoU=TP_pixels/union ไม่เฉลี่ย IoU ของ native classes เพื่อรวมกลุ่ม zero-union=0 ตาม fixed-class definition พร้อม flags ใน CSV ค่าในตารางเป็นเปอร์เซ็นต์ ตัวเลขใน JSON/CSV เป็นfraction0–1 เก็บprecisionจริง

## 2. Person metrics และข้อเสนอการเลือก

G_loc = **17,520**, G_sem_C4 = **17,454** รวมจาก bound GT-only manifest ไม่ hardcodeแทนการตรวจ ใช้ geometry-canonical matcher revision2 ที่ mask IoU0.50/0.75 เหมือนทั้งเก้าระบบ นิยาม tie/identical-geometry limitation คงเดิม Q_C4_GT รวม target-only per-eligible-GT-person contributions โดย missed GT=0 แล้วหาร G_sem_C4; unmatched predicted persons ไม่ลงโทษ Q โดยตรง ต้องอ่าน FP/F1 ร่วม ไม่เรียกผู้ Q สูงสุดว่า overall winner

|ระบบ|Mask IoU|TP|FP|FN|F1 %|Q_C4_GT %|
|---|---|---|---|---|---|---|
|QANet_CIHP_HRNetW48_512x384|0.50|16906|7156|614|81.314|73.474|
|QANet_CIHP_HRNetW48_512x384|0.75|15304|8758|2216|73.609|67.937|
|M2FP_R101_CIHP|0.50|16163|2119|1357|90.291|69.591|
|M2FP_R101_CIHP|0.75|15318|2964|2202|85.571|67.101|
|D2FP_R101_CIHP|0.50|15972|2176|1548|89.559|68.018|
|D2FP_R101_CIHP|0.75|14817|3331|2703|83.083|64.566|
|RPR_CIHP|0.50|16214|3351|1306|87.442|68.640|
|RPR_CIHP|0.75|14470|5095|3050|78.037|62.987|
|CPI_R50_CIHP|0.50|15819|3896|1701|84.968|67.523|
|CPI_R50_CIHP|0.75|13855|5860|3665|74.419|61.131|
|CPI_ConvNeXtB_CIHP|0.50|16288|2880|1232|88.792|71.938|
|CPI_ConvNeXtB_CIHP|0.75|15026|4142|2494|81.912|67.692|
|Sapiens2_0.4b|0.50|16906|7156|614|81.314|57.789|
|Sapiens2_0.4b|0.75|15304|8758|2216|73.609|53.966|
|Sapiens2_0.8b|0.50|16906|7156|614|81.314|55.106|
|Sapiens2_0.8b|0.75|15304|8758|2216|73.609|51.579|
|Sapiens2_1b|0.50|16906|7156|614|81.314|49.242|
|Sapiens2_1b|0.75|15304|8758|2216|73.609|46.466|

ที่ matching 0.50 Q_C4_GT สูงสุดคือ **QANet_CIHP_HRNetW48_512x384 (73.474%)**; เทียบกับ M2FP_R101_CIHP มี Q 69.591% ส่วนต่าง 3.883 pp และ FP 7,156 เทียบ 2,119; extent F1 81.314% เทียบ 90.291%
ที่ matching 0.75 Q_C4_GT สูงสุดคือ **QANet_CIHP_HRNetW48_512x384 (67.937%)**; เทียบกับ M2FP_R101_CIHP มี Q 67.101% ส่วนต่าง 0.835 pp และ FP 8,758 เทียบ 2,964; extent F1 73.609% เทียบ 85.571%

**ข้อเสนอ shortlist จากหลักฐาน CIHP นี้:** ใช้ M2FP_R101_CIHP เป็นตัวเลือกหลักเมื่อให้ความสำคัญกับความถูกต้องของพื้นที่ Hair/Face-reference/Upper/Lower โดยรวม และพิจารณา QANet_CIHP_HRNetW48_512x384 เป็นทางเลือกสำหรับคุณภาพ semantic ต่อ GT person โดยยอมรับข้อแลกเปลี่ยน FP/extent F1 ตามตาราง ไม่ได้กำหนดน้ำหนัก/threshold ใหม่ ไม่ใช่ final deployment acceptance และไม่ใช่ ensemble ที่ทดสอบแล้ว

**CPI ConvNeXt-B เป็นอีกทางเลือกสำหรับข้อแลกเปลี่ยนนี้:** ที่ matching0.50 มี Q_C4_GT 71.938% สูงกว่า M2FP แต่ต่ำกว่า QANet ขณะที่ FP 2,880 ต่ำกว่า QANet และ F1 88.792% สูงกว่า QANet; global C4-P ยังต่ำกว่า M2FP จึงเสนอให้เก็บใน shortlist เมื่อการใช้งานให้น้ำหนัก semantic ต่อคนร่วมกับ FP โดยไม่สร้างคะแนนผสมหรือน้ำหนักใหม่ ไม่จำเป็นต้องเก็บทุกโมเดลเพียงเพราะอาจเหมาะกับ CCTV โดยยังไม่มีหลักฐาน

extent ของ QANet/Sapiens มาจาก frozen YOLO จึงไม่ใช้ F1 ที่เหมือนกันอ้าง native instance capability ของ parser; CPI และ native-frame ระบบอื่นคง extents/association ที่บันทึกไว้ ไม่มี remask ด้วย YOLO ในงานนี้ ข้อมูล input/conditioning ต่างกันยังเป็นข้อจำกัดของ application comparison

## 3. Support และตัวหารราย target

|ระบบ|Target|GT pixels|Pred pixels|Union pixels|
|---|---|---|---|---|
|QANet_CIHP_HRNetW48_512x384|Face_CIHP_reference_proxy_for_Sapiens|37932488|38642800|40797724|
|QANet_CIHP_HRNetW48_512x384|Hair|40760850|40613642|45228484|
|QANet_CIHP_HRNetW48_512x384|Upper_non_Dress|148199276|150202863|164074286|
|QANet_CIHP_HRNetW48_512x384|Lower_non_Dress|38702345|38776880|44412874|
|M2FP_R101_CIHP|Face_CIHP_reference_proxy_for_Sapiens|37932488|36989348|39828625|
|M2FP_R101_CIHP|Hair|40760850|39858436|44112153|
|M2FP_R101_CIHP|Upper_non_Dress|148199276|146278992|158694160|
|M2FP_R101_CIHP|Lower_non_Dress|38702345|37747418|42935690|
|D2FP_R101_CIHP|Face_CIHP_reference_proxy_for_Sapiens|37932488|36776705|39861215|
|D2FP_R101_CIHP|Hair|40760850|39771557|44247146|
|D2FP_R101_CIHP|Upper_non_Dress|148199276|144252089|158679297|
|D2FP_R101_CIHP|Lower_non_Dress|38702345|37409975|43072876|
|RPR_CIHP|Face_CIHP_reference_proxy_for_Sapiens|37932488|37857687|41013316|
|RPR_CIHP|Hair|40760850|39831467|45351014|
|RPR_CIHP|Upper_non_Dress|148199276|148946509|163847047|
|RPR_CIHP|Lower_non_Dress|38702345|36446617|43913093|
|CPI_R50_CIHP|Face_CIHP_reference_proxy_for_Sapiens|37932488|37589325|40648058|
|CPI_R50_CIHP|Hair|40760850|40800080|45477427|
|CPI_R50_CIHP|Upper_non_Dress|148199276|146747496|164536535|
|CPI_R50_CIHP|Lower_non_Dress|38702345|37827129|45021753|
|CPI_ConvNeXtB_CIHP|Face_CIHP_reference_proxy_for_Sapiens|37932488|37837839|40513885|
|CPI_ConvNeXtB_CIHP|Hair|40760850|40733427|44969889|
|CPI_ConvNeXtB_CIHP|Upper_non_Dress|148199276|148684079|161545412|
|CPI_ConvNeXtB_CIHP|Lower_non_Dress|38702345|38965594|44173586|
|Sapiens2_0.4b|Face_CIHP_reference_proxy_for_Sapiens|37932488|43285474|47166135|
|Sapiens2_0.4b|Hair|40760850|40323588|45021687|
|Sapiens2_0.4b|Upper_non_Dress|148199276|154226412|171117447|
|Sapiens2_0.4b|Lower_non_Dress|38702345|35250001|42433580|
|Sapiens2_0.8b|Face_CIHP_reference_proxy_for_Sapiens|37932488|43543016|47191691|
|Sapiens2_0.8b|Hair|40760850|37688175|43840371|
|Sapiens2_0.8b|Upper_non_Dress|148199276|150280503|169719018|
|Sapiens2_0.8b|Lower_non_Dress|38702345|33314437|42111273|
|Sapiens2_1b|Face_CIHP_reference_proxy_for_Sapiens|37932488|41173601|46485085|
|Sapiens2_1b|Hair|40760850|36278027|43419971|
|Sapiens2_1b|Upper_non_Dress|148199276|138365260|166822127|
|Sapiens2_1b|Lower_non_Dress|38702345|33442478|42028557|

Support เป็นจำนวน pixels ไม่ใช่จำนวนภาพ/คน; union เป็นตัวหาร IoU และต่างจาก GT support แม้ทุกระบบมี GT support เดียวกัน [PER_TARGET.csv](../metrics/cpi-common-c4p-20261030/PER_TARGET.csv) เก็บ BG/OTHER ด้วย ส่วน [PERSON_METRICS.csv](../metrics/cpi-common-c4p-20261030/PERSON_METRICS.csv) มี precision/recall, Q numerator, contamination numerator/denominator และ matching ambiguity ครบ ไม่ใช้ null เป็น0

## 4. ข้อจำกัดด้าน Face และเสื้อผ้าที่เห็นจาก confusion

|ระบบ|Face FP pixels บน GT non-Face|Upper→OTHER pixels|Lower→OTHER pixels|GT Dress→Upper/Lower pixels|
|---|---|---|---|---|
|QANet_CIHP_HRNetW48_512x384|2865236|2991434|1018119|3948232|
|M2FP_R101_CIHP|1896137|3053261|1053519|3115798|
|D2FP_R101_CIHP|1928727|3609944|1090119|2774541|
|RPR_CIHP|3080828|3343522|1201098|3826108|
|CPI_R50_CIHP|2715570|3213152|1285456|4083556|
|CPI_ConvNeXtB_CIHP|2581397|2876661|907792|3646354|
|Sapiens2_0.4b|9233647|2433756|502121|14677291|
|Sapiens2_0.8b|9259203|2287420|446098|13567829|
|Sapiens2_1b|8552597|1801097|401253|13598352|

ตัวเลขนี้ derive จาก native-GT×prediction sufficient statistics เดิม/ใหม่ ไม่เปิด inference หรือ full pixel-scoring เพิ่ม Face FP บน non-Face GT รวมความผิด semantic และความต่าง annotation partition ได้ จึงไม่ยกทั้งหมดว่าเป็น neck error; GT ไม่แยกคอเป็น class อิสระ การนับ GT Dress→Upper/Lower เป็น discordance กับนิยาม fixed task ซึ่งต้องได้ FP ตาม domain ไม่ใช่หลักฐานว่าเสื้อผ้านั้นไม่มีอยู่หรือ parser แย่ทุกtaxonomy

Sapiens native Apparel ID1 เป็น OTHER ไม่เท่ากับ Dress6 โดยอัตโนมัติ [DISCORDANCE.csv](../metrics/cpi-common-c4p-20261030/DISCORDANCE.csv) มี valid-GT pixels ที่ทำนาย Apparel และ Upper/Lower→OTHER เพื่อช่วยอ่านข้อจำกัด ไม่ลบ pixels เหล่านี้หรือเปลี่ยน mapping ให้คะแนนดีขึ้น Full native-GT×prediction histograms อยู่ใน canonical METRICS แต่ละระบบ

## 5. Compatibility ของ CPI และระดับหลักฐาน equivalence

|ระบบ|Implementation / accepted IDs|Route|Resource policy ของการได้ predictions|
|---|---|---|---|
|QANet_CIHP_HRNetW48_512x384|SOURCE_HASH_BOUND_ACCEPTED_CONFIGURATION: 5000|YOLO_ROI|Original admission; runtime exclusivity not certified|
|M2FP_R101_CIHP|SOURCE_HASH_BOUND_ACCEPTED_CONFIGURATION: 5000|YOLO_ASSOCIATED_NATIVE_FRAME|Original admission; runtime exclusivity not certified|
|D2FP_R101_CIHP|SOURCE_HASH_BOUND_ACCEPTED_CONFIGURATION: 5000|YOLO_ASSOCIATED_NATIVE_FRAME|Original admission; runtime exclusivity not certified|
|RPR_CIHP|SOURCE_HASH_BOUND_ACCEPTED_CONFIGURATION: 5000|YOLO_ASSOCIATED_NATIVE_FRAME|SHARED_GPU_QUALITY_ONLY|
|CPI_R50_CIHP|CPI_FEATURE_BUFFER_REUSE_2: 14; CPI_FEATURE_BRANCH_SCHEDULE_3: 4983; ORIGINAL_FROZEN_NATIVE: 3|YOLO_ASSOCIATED_NATIVE_FRAME|SHARED_GPU_QUALITY_ONLY|
|CPI_ConvNeXtB_CIHP|ORIGINAL_FROZEN_NATIVE: 337; CPI_PERSON_CHUNK_RESTORATION_1: 4663|YOLO_ASSOCIATED_NATIVE_FRAME|SHARED_GPU_QUALITY_ONLY|
|Sapiens2_0.4b|SOURCE_HASH_BOUND_ACCEPTED_CONFIGURATION: 5000|SAPIENS_FRAME_YOLO_MASK_OWNERSHIP|SHARED_GPU_QUALITY_ONLY|
|Sapiens2_0.8b|SOURCE_HASH_BOUND_ACCEPTED_CONFIGURATION: 5000|SAPIENS_FRAME_YOLO_MASK_OWNERSHIP|SHARED_GPU_QUALITY_ONLY|
|Sapiens2_1b|SOURCE_HASH_BOUND_ACCEPTED_CONFIGURATION: 5000|SAPIENS_FRAME_YOLO_MASK_OWNERSHIP|SHARED_GPU_QUALITY_ONLY|

R50 original3 + buffer-reuse2 14 + feature-scheduling3 4,983 =5,000; ConvNeXt original337 + person-chunk1 4,663 =5,000 source segments/revisions/dependencies ระบุใน [COMPATIBILITY](../runs/cpi-common-c4p-20261030/COMPATIBILITY.json) และ [PARITY_REVIEW](../runs/cpi-common-c4p-20261030/PARITY_REVIEW.json) ไม่เรียกผลรวมว่าใช้ implementation เดียวทุกภาพ

แยกหลักฐานสามเรื่อง:

- **Forward/output parity:** person-chunk1 มี CPU restoration cases/GPU synthetic labels/native-prefix checks และ known-image NPZ byte regression; buffer-reuse2 มี raw float32 feature fixturesและknown-image regression; schedule3 มี CPU/GPU raw float fixtures, native max-head shape stress และ actual diagnostic frames/known-output equality ที่แยกจาก proof ของperson-chunk1 รวม dependency hashesทั้งสามโมดูล หลักฐานนี้ไม่ยืนยัน bitwise equivalence เทียบ original native inference ครบ5,000ภาพหรือทุก input/resource layout
- **Packet integrity/identity:** final accepted RECONCILED audits ตรวจ NPZ/CRC/metadata/input/checkpoint/geometry/YOLO/config เดิมแล้ว รอบนี้ตรวจ small metadata bindings และอ่าน required arrays พร้อม CRC ระหว่าง scoring โดย reuse audits ไม่ bulk rehash weights/NPZ/datasetsซ้ำ เชื่อมแต่ละคะแนนกับsourcepacket hash/segment/revision
- **Scorer agreement:** native audits มี independent saved-mask native scorer agreement; งานนี้คำนวณ person Q ใหม่จากsaved planes/extents/scoresผ่าน common revision2 ไม่คัดลอก scalar native Q ส่วน global ใช้ผลรวม20×20 confusionจากaccepted auditsแล้วproject ตรวจ pixel-based equivalenceบนfixed ambiguity sampleและตัวแทนแต่ละsegmentก่อน aggregate

ดังนั้นคะแนนคือผลของ configuration พร้อม effective revisions ที่ระบุและ packet contractที่ใช้ได้ ไม่อ้าง native unmodified reproductionทั้งประชากร CPI taxonomy acceptance ยังคง ACCEPTED_WITH_INDIRECT_EVIDENCE ไม่ยกระดับ DIRECT_VERIFIED

## 6. Native CIHP20 — เก็บแยกจาก common C4-P

|ระบบ|mIoU20 รวม BG %|FG19 %|ครบ|
|---|---|---|---|
|QANet_CIHP_HRNetW48_512x384|64.866|63.449|5,000/5,000|
|M2FP_R101_CIHP|68.155|66.796|5,000/5,000|
|D2FP_R101_CIHP|64.352|62.827|5,000/5,000|
|RPR_CIHP|59.124|57.408|5,000/5,000|
|CPI_R50_CIHP|57.551|55.769|5,000/5,000|
|CPI_ConvNeXtB_CIHP|65.411|63.954|5,000/5,000|

ตารางนี้อ่าน native canonical summary ที่ตรวจรับแล้ว ไม่ rescore native ทั้งชุด ไม่เทียบตัวเลขmIoU20กับmIoU4โดยตรง; คนละclasses/denominators/matching interpretation ผล frozen native masks/metrics/confusions/configs ไม่เขียนทับ รายละเอียด native per-class/person อยู่ใน [handoff](CIHP_EVALUATION_HANDOFF_TH.md)

## 7. OOM/recovery และความครบถ้วน

CPI R50 มี historical failed attempts5รายการ และ ConvNeXt3รายการ เก็บแต่ละattemptไว้; successful observationsแต่ละIDเลือกจากacceptedreconciledmanifest ไม่เลือก outputตามคะแนน R50ปิดnativeล่าสุดด้วยreuse912+new4,088; ConvNeXtreuse337+new4,663 Sapiens0.8Bมี historical MODEL_LOAD OOM0006307 ก่อนปิดรอบครบ การมีcurrent failed=0ไม่แปลว่าไม่เคยOOM

งานCPUรอบนี้มีsetup attemptก่อนimport scorerที่ launcher resolve venv symlinkเป็นsystemPythonจนไม่มีnumpy; scores/modelcalls0 เก็บ [SETUP_ATTEMPT_1](../runs/cpi-common-c4p-20261030/SETUP_ATTEMPT_1.json) แล้วแก้เฉพาะlaunch interpreterpath ไม่เปลี่ยนscorer/config/protocol ไม่มีmodel/OOMretryหรือfallbackใหม่ CPU streamsแยกdirectories/locks/atomic scores และimmutableattemptledger; resumeต้องexplicitและเช็คconfig/source/input/scorehash ไม่รันสำเร็จซ้ำหรือทับorphanโดยเงียบ

STRICT_COMPLETE แต่ละระบบต้อง exact5,000unique accepted IDs และscoremembershipตรงpopulation unresolvedinvalid/missing/failureให้primarynull รอบนี้ครบ9/9แล้ว [SCORING_CONFIG](../runs/cpi-common-c4p-20261030/SCORING_CONFIG.json) แยกจากnative frozenconfig เก็บCPUguards24h/80GiB/free50GiBและprovenance; GPU modelcallsใหม่=0 การถอดรหัสsavedNPZ/อ่านGTเพื่อscoringไม่ใช่modelinference

## 8. Canonical sources และ legacy null normalization

|ระบบ|Canonical metrics|Completion|Legacy primary null|
|---|---|---|---|
|QANet_CIHP_HRNetW48_512x384|[METRICS](../runs/common-c4p-full-20261029T063458522990Z/QANet_CIHP_HRNetW48_512x384/METRICS.json)|[COMPLETION](../runs/common-c4p-full-20261029T063458522990Z/QANet_CIHP_HRNetW48_512x384/COMPLETION.json)|True|
|M2FP_R101_CIHP|[METRICS](../runs/common-c4p-full-20261029T063458522990Z/M2FP_R101_CIHP/METRICS.json)|[COMPLETION](../runs/common-c4p-full-20261029T063458522990Z/M2FP_R101_CIHP/COMPLETION.json)|True|
|D2FP_R101_CIHP|[METRICS](../runs/common-c4p-full-20261029T063458522990Z/D2FP_R101_CIHP/METRICS.json)|[COMPLETION](../runs/common-c4p-full-20261029T063458522990Z/D2FP_R101_CIHP/COMPLETION.json)|True|
|RPR_CIHP|[METRICS](../runs/common-c4p-full-20261029T063458522990Z/RPR_CIHP/METRICS.json)|[COMPLETION](../runs/common-c4p-full-20261029T063458522990Z/RPR_CIHP/COMPLETION.json)|True|
|CPI_R50_CIHP|[METRICS](../runs/cpi-common-c4p-20261030/CPI_R50_CIHP/METRICS.json)|[COMPLETION](../runs/cpi-common-c4p-20261030/CPI_R50_CIHP/COMPLETION.json)|False|
|CPI_ConvNeXtB_CIHP|[METRICS](../runs/cpi-common-c4p-20261030/CPI_ConvNeXtB_CIHP/METRICS.json)|[COMPLETION](../runs/cpi-common-c4p-20261030/CPI_ConvNeXtB_CIHP/COMPLETION.json)|False|
|Sapiens2_0.4b|[METRICS](../runs/common-c4p-full-20261029T063458522990Z/Sapiens2_0.4b/METRICS.json)|[COMPLETION](../runs/common-c4p-full-20261029T063458522990Z/Sapiens2_0.4b/COMPLETION.json)|True|
|Sapiens2_0.8b|[METRICS](../runs/sapiens08-c4p-20261029T081254180014Z/METRICS.json)|[COMPLETION](../runs/sapiens08-c4p-20261029T081254180014Z/COMPLETION.json)|True|
|Sapiens2_1b|[METRICS](../runs/sapiens1b-c4p-20261029T200113781375Z/METRICS.json)|[COMPLETION](../runs/sapiens1b-c4p-20261029T200113781375Z/COMPLETION.json)|True|

[CIHP_COMMON_RESULT_INDEX.json](../manifests/CIHP_COMMON_RESULT_INDEX.json) เป็น normalized **derived** index เชื่อม status/exactmembership/metrics path/hash/protocol/source revision/route บางhistoricalCOMPLETION.primaryเป็นnullเพราะreporterเดิมไม่populate ใช้ประกาศcanonical METRICS.primaryหลังตรวจmembership/status มิใช่เติมผลย้อนหลังหรือแทนnullด้วย0 รอบนี้ตรวจแหล่งที่ประกาศไว้ก่อนใช้คะแนน ถ้าผลหายจริง reporterต้องหยุด ไม่ fallbackไปnative/subsetscore

Protocol SHA256 `7fb101672407d465885efcc00202af927e93cd422daeae42bf215cbe504cd33d`; GTbinding manifestSHA256 `1a6f635ffdd0da1b767a6d7279e0437130bdfdd47e510fbfdaeb9b047cc82cc0`; source/config/input manifestsและledger hashesอยู่runrecordและindex [VERIFICATION](../runs/cpi-common-c4p-20261030/FINAL_VERIFICATION.json) ระบุ arithmetic/membership/protocol/immutability checksที่ทำจริง ไม่ใช้จำนวนtestsแทนsemanticreview

ไฟล์เต็มprecisionขนาดเล็ก: [COMMON_SUMMARY.csv](../metrics/cpi-common-c4p-20261030/COMMON_SUMMARY.csv), [PER_TARGET.csv](../metrics/cpi-common-c4p-20261030/PER_TARGET.csv), [PERSON_METRICS.csv](../metrics/cpi-common-c4p-20261030/PERSON_METRICS.csv), [LEADERS.json](../metrics/cpi-common-c4p-20261030/LEADERS.json) ไม่มีrawlogs/images/weightsในGit การcloneอย่างเดียวไม่reproducebenchmarkโดยไม่มีexternaldataset/checkpoints/environment/savedpackets

## 9. ขอบเขตคำอ้างและงานถัดไป

ผลนี้ตอบว่าcheckpoint+application configurationใดได้global target agreementและGT-personsemantic qualityสูงสุด **บนCIHP selection populationนี้** ไม่ควบคุมtraining/pretrainingexposureทั้งหมด ไม่แยกผลarchitecture/training/adapterออกจากกัน Common mappingไม่ทำให้inputroutesfairสมบูรณ์และไม่มีCCTV/colorperformanceclaim

Commonprotocolออกแบบหลังเห็นnativeสี่ระบบแล้ว จึงไม่อ้างpreregistered/independentfinalconfirmation ไม่มีปรับmapping/threshold/conditioningจากคะแนน ไม่มีcleanlatency/FPS/VRAMefficiencyrankingเพราะtimingboundaries/resourceconditionsต่างกัน ไม่เพิ่มuncertaintytestsเป็นเงื่อนไขปิดงาน

ไม่ได้สร้างgalleryใหม่ในรอบนี้ ภาพเดิมเป็นprivatefixed-sample snapshotsพร้อมmodelmanifestตาม [handoff](CIHP_EVALUATION_HANDOFF_TH.md) ไม่อ้างว่ามีpanelครบ9ตัวหรือเผยแพร่datasetimagesอัตโนมัติ ขั้นถัดไปคือผู้ใช้reviewshortlist/เลือกconfigurationไปphaseถัดไปโดยระบุmandatorycapabilities ไม่เปิดinference/training/OOMrepair/color/CCTVอัตโนมัติจากรายงานนี้
