# ผลสรุป CCTV90: selected annotated-part IoU/Dice ของ parsing 9 ระบบ

ปิดการคำนวณและตรวจผล 2026-11-01T08:50:54.244052+07:00 (Asia/Bangkok, UTC+07:00). สถานะ **COMPLETE 9/9 ระบบ × exact90ภาพ**, failed/invalid/missing0 ใน derived evaluation. ใช้ predictions เดิมทั้งหมด **model inference ใหม่0ครั้ง**.

**ข้อเสนอจากผลรอบนี้: เลือก QANet_CIHP_HRNetW48_512x384 เป็น configuration หลักสำหรับงาน selected-part task นี้**: macro mean selected-part IoU4 **61.773%**, mean-part Dice4 **69.203%**. สูงสุดทั้ง4targetsตาม primary ที่กำหนดก่อนคำนวณคะแนนชุดใหม่; นำอันดับถัดไป CPI_ConvNeXtB_CIHP 14.196 percentage points. เป็น observed leader ของ checkpoint+application configuration บน reference ชุดนี้ ไม่ใช่คำรับรอง full-scene CCTV/deployment accuracy หรือ statistical significance.

## 1. แก้ช่องว่างเดิมอย่างไร

ผลเดิมวัด recall และ IoU เฉพาะ known-positive pixels จึงไม่ลงโทษการทายล้นออกนอก annotation. รอบนี้ใช้ **mask เต็มของคนที่จับคู่แล้ว** เทียบ contour ของ target ที่ annotate: ส่วนเกินเป็น FP, ส่วนขาดเป็น FN. คนอื่นที่ไม่ถูกเลือก annotate ไม่กลายเป็น negative ทั้งภาพ. รักษา native masks/GT/configs/คะแนนเดิม และแยก protocol/output directory ใหม่.

นี่เป็นวิธีประเมินแบบ selected-instance/part ที่มีสูตร IoU/Dice มาตรฐาน แต่ขอบเขตและตัวหารต่างจาก global semantic mIoU/CIHP C4-P. ไม่เรียกคะแนนนี้ว่า full-image mIoU และไม่เปรียบเปอร์เซ็นต์ข้ามนิยามโดยตรง. [Protocol](../SELECTED_PART_PROTOCOL.md) / [machine specification](../configs/SELECTED_PART_PROTOCOL.json).

## 2. ประชากรและการตรวจ reference

|รายการ|จำนวน/วิธี|
|---|---|
|Input population|90ภาพ:48day/42night; ทุกระบบต้องครบ90ภาพ|
|Source annotations|127person-image records,324annotated parts; เลือกบางคน/บางส่วน|
|GT-only visual screen|ตรวจ127recordsครบ16หน้าและซูม10กรณี โดยซ่อน parser predictions|
|Reviewer|Codex visual assistant; ไม่มี expert certification หรือ inter-rater agreement|
|Primary subset|315parts: Face34,Hair69,Upper115,Lower97;126คนใน89ภาพที่มี eligible parts|
|Sensitivity|324partsเดิมครบ; ไม่แก้/ลบ source GT หรือทิ้งภาพจาก execution population|
|เก้าส่วนที่กันออก|Upper5/Lower4: contourไม่ครบ/interior patch, exposed torso, garment/objectกำกวม, one-piece splitที่ไม่มีกติกา|

การตรวจภาพช่วยคัดกรองข้อผิดพลาดที่เห็นได้ แต่ **ไม่พิสูจน์ว่า contour ที่เหลือเป็น gold standard สมบูรณ์**. ส่วนเล็ก ภาพมืด/เบลอ/ถูกบังยังคงไว้เมื่อไม่พบข้อผิดพลาดเชิงนิยามชัดเจน. ใช้ผลทั้ง315และ324ส่วนแสดง sensitivity ไม่เลือก subset เพื่อช่วยโมเดล. Face อาจรวม neck; Upper/Lower วัดตาม reference ของชุดนี้ ไม่อ้างยืนยัน non-Dress taxonomy ทั้งชุด. [QA summary](SELECTED_PART_QA_SUMMARY.json).

## 3. Protocol และสูตรที่ใช้จริง

GT-person part union ใช้เฉพาะ evaluation matching กับ frozen YOLO boxes แบบ class/model blind: coverage≥0.50, maximum cardinality แล้ว sum coverage; equal optimaเลือก detector confidence/bbox/stable opportunity ID. มี duplicate-detection tie1กรณีที่เปิดภาพตรวจโดยไม่ดู parser semantics. GT ไม่มี full-person silhouette จึงไม่ใช้ส่วน union นี้คำนวณ detector mask-IoU/F1.

GT21person records ไม่มี detector opportunityผ่านเงื่อนไข; primary46partsที่เกี่ยวข้องยังอยู่ในตัวหารและได้ predictionว่าง (Face6/Hair9/Upper16/Lower15). Native parser ที่ไม่ associate มาคนที่จับคู่ได้ ก็ให้ predictionว่าง ไม่ตัด GT item. ไม่ใช้ semantics เลือกคู่ให้ได้คะแนนสูงสุด.

ต่อ selected person i / target c: TP=|G∩P|, FP=|P\G|, FN=|G\P|; **IoU=TP/(TP+FP+FN), Dice=2TP/(2TP+FP+FN)**. P ใช้ whole original-grid final person plane, ไม่ clipด้วย GT/positive domain/bbox. Missing prediction IoU/Dice/recall0; precision nullถ้าไม่มี predicted pixels. Target ที่ไม่ได้ annotate สำหรับคนนั้นไม่ถูกสร้างเป็น negative item.

**Primary** เฉลี่ย IoU ราย annotated part ภายใน target แล้วเฉลี่ย4targetsเท่ากัน. นับทุก GT part รวม detector/association misses. Secondary ใช้ Diceแบบเดียวกัน, pooledTP/FP/FN/P/R/IoUรายtarget, day/night. Pooled IoUให้น้ำหนักพื้นที่มากกว่า mean-part IoU จึงต้องแยกชื่อและไม่แทนกัน.

ใช้ hard-label mapping revision2 เดิม: CIHP Hair2,Face13,Upper5+7,Lower9+12; Sapiens Hair4,Face3+24–28(proxy),Upper23,Lower13. Dress/Apparel→OTHERไม่แบ่งด้วยheuristic. Native labelsอื่น/OTHERไม่ถูกลบก่อนประเมิน; ไม่กำหนด ignoreแยกตามโมเดล.

## 4. ตารางหลัก — mean annotated-part IoU (%)

ตารางเรียง frozen roster order; ทุกแถว COMPLETE90/90. ตัวเลขจาก CSV full precision ก่อนปัด3ตำแหน่ง. Faceหมายถึง referenceชุดนี้/Sapiensproxy.

|Configuration|Face|Hair|Upper|Lower|Macro IoU4|Macro Dice4|All324 IoU4|
|---|---:|---:|---:|---:|---:|---:|---:|
|QANet_CIHP_HRNetW48_512x384|56.075|61.048|68.684|61.283|61.773|69.203|61.023|
|M2FP_R101_CIHP|48.600|46.183|51.868|43.513|47.541|52.624|46.827|
|D2FP_R101_CIHP|32.707|37.309|45.233|38.417|38.417|43.398|37.989|
|RPR_CIHP|45.411|43.391|49.063|40.862|44.682|51.468|44.256|
|CPI_R50_CIHP|38.997|41.243|44.289|35.932|40.115|47.151|39.654|
|CPI_ConvNeXtB_CIHP|46.988|46.648|52.699|43.972|47.577|55.005|46.859|
|Sapiens2_0.4b|34.804|49.022|49.593|34.675|42.023|50.347|41.519|
|Sapiens2_0.8b|37.035|46.553|41.022|34.286|39.724|46.372|39.265|
|Sapiens2_1b|35.826|43.652|47.065|39.221|41.441|48.186|40.856|

QANet ยังสูงสุดเมื่อใช้324partsเดิมทั้งหมด จึงไม่ได้เป็นผู้นำเฉพาะหลังคัด9ส่วนออก. ความต่างอันดับรองบางคู่เล็กมาก เช่น CPI ConvNeXt-B กับ M2FP; ไม่ตีความว่าแตกต่างอย่างมีนัยสำคัญ. ไม่มีการวัด uncertainty เพิ่มในรอบนี้.

### ผล QANet แบบ pooled pixels — ตัวหารอีกแบบหนึ่ง

|Target|GT parts|GT pixels|TP|FP|FN|Union|Pooled IoU%|Pooled Dice%|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|Face|34|54044|43504|3127|10540|57171|76.095|86.425|
|Hair|69|246971|209545|10950|37426|257921|81.244|89.651|
|Upper|115|869541|773744|78462|95797|948003|81.618|89.879|
|Lower|97|353540|258942|19048|94598|372588|69.498|82.005|

Pooled metrics ไม่ใช่คะแนนหลักที่ใช้เลือก. เช่น Face mean-part IoUต่ำกว่า pooled IoU เพราะส่วนเล็ก/คนที่พลาดมีน้ำหนักเท่ากันใน mean-part; pooledให้น้ำหนัก pixelsจำนวนมาก. ไฟล์ [PER_TARGET](../metrics/SELECTED_PART_PER_TARGET.csv) เก็บ pooled precision/recall, union และ support ของทุกระบบเต็มความละเอียด.

### Coverage และ day/night

|Configuration|Shared detector-miss parts|Native-association-miss parts|Day macro IoU4%|Night macro IoU4%|
|---|---:|---:|---:|---:|
|QANet_CIHP_HRNetW48_512x384|46|0|58.102|64.505|
|M2FP_R101_CIHP|46|45|46.272|48.189|
|D2FP_R101_CIHP|46|66|36.280|40.061|
|RPR_CIHP|46|39|40.972|47.763|
|CPI_R50_CIHP|46|52|36.666|42.929|
|CPI_ConvNeXtB_CIHP|46|38|43.836|50.724|
|Sapiens2_0.4b|46|0|35.037|48.222|
|Sapiens2_0.8b|46|0|35.492|43.874|
|Sapiens2_1b|46|0|36.974|45.910|

46เป็นจำนวน GT partsจาก21GTperson records ไม่ใช่46คน. Association-miss partsคือ native parserไม่ได้ส่ง final personplaneสำหรับ detector opportunityที่จับคู่แล้ว; เป็น pipeline missที่ถูกลงโทษ ไม่ใช่ไฟล์เสียหรือ execution failure. Presenceของplaneไม่รับรองว่าทำนายtargetได้—semantic-emptyยังได้0. Day/nightเป็นsubsetdiagnosticsไม่ใช่สมมติฐานว่าชุดใดง่ายกว่า.

## 5. Fairness และความหมายของการเลือก

ทุกระบบใช้90input IDs, frozen detector cache, selected GT-person matching, GT eligibility, mapping และ metricเดียวกัน. แต่ conditioning ต่างกันตามที่รันจริง: QANetใช้YOLO ROIและmask clipping; Sapiens full-frame semantics+YOLO mask ownership; M2FP/D2FP/RPR/CPIใช้native instances+YOLO association. ไม่เปลี่ยน input/ownershipย้อนหลัง.

ดังนั้นคะแนนรวมทั้งความสามารถแบ่งส่วนกับความสามารถส่ง semantic mask ให้คนที่ต้องการ. การที่ QANet ไม่มี native-association misses ในชุดนี้เป็นคุณสมบัติของ route ไม่ใช่ข้อพิสูจน์ architecture ดีกว่าทุกตัว. FPนี้วัดการทายล้นของ selected person ไม่ครอบคลุม false people/targetsที่ไม่มีannotation. ยังสรุป full-scene precision/AP/personF1ไม่ได้.

ผลสนับสนุนการเลือก QANet+frozenYOLO configuration เป็น **ตัวเลือกหลักจากหลักฐาน selected-part CCTV90นี้**. ก่อน productionยังต้องให้ผู้ทำannotation/ผู้เชี่ยวชาญตรวจ contourและนิยามFace/Dress, ตรวจคน/ส่วนที่ไม่ได้annotateหากจะอ้าง full-scene metrics และประเมินบน independent annotated set. งานเหล่านี้ไม่จำเป็นต้อง rerunเก้าระบบเพื่อให้ได้ผลรอบนี้; คะแนนรอบนี้ปิดแล้วตามขอบเขตที่วัดได้.

ชุดนี้เป็น post-hoc/exploratory และอาจมี selection biasจากการเลือกannotateคน/ส่วน/กล้อง; ไม่รับรองความเป็นอิสระของframeหรือควบคุม training exposureทั้งหมด. ไม่มี architecture-only claim, statistical significance, latency/FPS/VRAMranking หรือคำยืนยันว่างานสี/attributesผ่านแล้ว.

## 6. ภาพและการตรวจจริง

Private GT review gallery: `CCTV_Human_Parsing_Benchmark/outputs/selected-part-review-20261101T013108Z/` (page_01.jpg…page_16.jpg และ10zoom; source review manifestอาจยังมีPENDINGเป็น intake snapshot ให้ใช้ LOCKED_GT_REVIEW/GT_BINDING เป็นข้อสรุป).

Private comparison gallery: `CCTV_Human_Parsing_Benchmark/outputs/selected-part-scores-20261101/gallery/` มี2panelsของ RGB/GT/ครบ9ระบบ. เลือก first source-order day/night personที่มี primaryGTครบ4targets ตามGT coverageก่อนอ่านคะแนนใหม่ ไม่เลือกตามโมเดลชนะ. `MANIFEST.json`เก็บprivateIDs/sourcepacketmodels/displaycropและhash. Cropใช้แสดงภาพเท่านั้น ไม่ใช้clipคะแนน.

เปิดดูทั้ง2panelแล้ว: ตำแหน่งmaskบนcropสอดคล้องกับreference; เห็นความต่างขอบเสื้อผ้า/ส่วนเล็กและการขาดtarget. ตัวอย่างdayหนึ่งมี fragmented labelsในSapiens บางขนาด; ตรวจ3packetsว่ามาจากnative full-frame referenceจริงหลังownership ไม่ใช่galleryสร้างlabelขึ้น แต่ยังแยกสาเหตุทางโมเดล/domainจากforwardimplementationด้วยภาพนี้อย่างเดียวไม่ได้. ไม่แก้settingsหรือใช้รูปเปลี่ยนผู้ชนะ.

ตรวจ exact90uniqueIDs×9, read/hash810atomic source NPZ+metadata+score packets, GTCategory/Human/input/checkpoint/config/detectorbindings, labelID ranges/original geometry, derivedrecord/ledgerhashesและday+night sums. Independent coordinate-set TP/FP/FN checksบน3packetsครอบคลุมROI/nativeassociated/Sapiens ตรงกับscorer. CPU7hand-calculatedcasesผ่าน รวม saved NPZ→mapping→IoU/Dice→CSV. Reused auditเดิมกับsourcehashที่ยังตรง ไม่ inference/fullnativeauditซ้ำ. [Verification evidence](SELECTED_PART_EVALUATION_EVIDENCE.json).

## 7. Artifacts, provenance และทำงานต่อ

- [SUMMARY.csv](../metrics/SELECTED_PART_SUMMARY.csv):54แถว=9ระบบ×2subsets×3groups; หน่วยfraction0–1.
- [PER_TARGET.csv](../metrics/SELECTED_PART_PER_TARGET.csv):216แถว=9×2×3×4; TP/FP/FN/support/unionหน่วยpixel, GT_partsหน่วยannotatedperson-targetitems. Missing numericcellคือnull/N/Aไม่ใช่0.
- [Protocol JSON](../configs/SELECTED_PART_PROTOCOL.json), [QA record](SELECTED_PART_QA_SUMMARY.json), [scorer](../scripts/selected_part_evaluation.py), [CPU cases](../tests/test_selected_parts.py).
- Parent inference run: `cctv-partial-20261031T1800Z`; fresh CPU derived run: `selected-part-scores-20261101`; private GT binding: `outputs/selected-part-bindings-20261101/GT_BINDING.json`.
- Freeze snapshotก่อนselected-partscoring: `9d7f5c854b39c5dc1bb507695cab2bf5f5b1a0e9`; ไม่ใช่commitที่launchinferenceเก่า. Source/protocol/GTbinding/derivedCSVs hashesอยู่ในevidence.
- Public Gitไม่มีCCTVimages/sourcefilenames/annotations/perpersonrecords/masks/logs/checkpoints. Privateoutputsและsourceworkingcopyอยู่workspaceเดิม; publiccheckoutเป็นselectedfilecopy. ต้องsyncเฉพาะsanitizedpathsตามpublication manifest ไม่wholesale-sync.

ทำซ้ำCPUsyntheticchecksจากworkspace: `.venv/bin/python -m unittest discover -s CCTV_Human_Parsing_Benchmark/tests -p test_selected_parts.py -v`. ต้องใช้environmentที่มีNumPy/Pillow/SciPy; publiccloneไม่มีenvironment/privateGT/YOLOcache/nativepackets/reviewbinding จึงไม่อ้างreproduceผลทั้งหมดได้ทันที. Scorer CLIบังคับfreshoutdir; มีatomicper-framecheckpointsสำหรับreconciliation แต่ไม่resume/inference/retryอัตโนมัติ.

ขั้นถัดไปสำหรับผู้ใช้: ใช้QANet configurationเป็นข้อเสนอหลักจากชุดนี้และส่งรายงาน/ตารางให้ตรวจ; หากต้องยกระดับคำอ้างเป็นfull-sceneหรือproduction ให้เริ่มannotationQA/negative-scopeและindependentconfirmationเป็นงานแยก. ไม่รันโมเดลหรือการทดลองเพิ่มโดยอัตโนมัติ.

แหล่งสูตร/เครื่องมือ: [scikit-learn Jaccard](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.jaccard_score.html), [SciPy assignment](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html). ไม่ใช้แหล่งเหล่านี้เป็นการรับรองGTหรือcustomprotocol.

## Sapiens2 input audit — ข้อจำกัดเพิ่มเติม

[ตรวจ preprocessing](SAPIENS2_PREPROCESSING_AUDIT_TH.md): CPU12casesตรงofficialinputทุกค่า; ยังไม่พบchannel/normalizationbug. Full-frame stretchเปลี่ยนสัดส่วนคนอย่างมากและต่างจากROIroute จึงยังไม่อ้างสาเหตุarchitectureหรือความด้อยของSapiensทุกรูปแบบ. ไม่มีlearnedforwardใหม่หรือคะแนนเปลี่ยน.
