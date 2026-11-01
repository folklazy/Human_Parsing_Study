# CCTV selected annotated parts — protocol v1

สถานะ: **FROZEN_BEFORE_NEW_SELECTED_PART_SCORES**. เป็น post-hoc/exploratory extension หลังมีผล positive-domain recall เดิมแล้ว ไม่ใช่ preregistration และไม่เปลี่ยน [protocol เดิม](PROTOCOL.md), GT หรือ prediction packets. Machine specification: [SELECTED_PART_PROTOCOL.json](configs/SELECTED_PART_PROTOCOL.json).

## คำถามที่วัด

สำหรับคนและส่วนที่มี annotation ที่พอใช้เป็น contour reference ได้ pipeline ทำนายพื้นที่ Hair / Face-as-annotated / Upper / Lower ของคนนั้นครบและล้นเพียงใด? ใช้ **selected-annotated-part instance IoU/Dice** มี FP นอก polygon ของส่วนนั้นจริง ต่างจาก IoU บน known-positive domain เดิม แต่ไม่ใช่ full-scene semantic mIoU, detection AP หรือ person-silhouette F1.

## ตรวจ GT โดยไม่ดู parser predictions

ผู้ใช้ยืนยันว่าระบุเพียงบางคน/บางส่วน และมอบหมายให้ตรวจภาพเอง. ตรวจ RGB กับ GT ครบ90ภาพ/127person-image records/324parts ผ่าน16หน้า gallery และ10ภาพซูม. ผู้ตรวจคือ Codex visual assistant **ไม่ใช่ผู้เชี่ยวชาญอิสระหรือการวัด inter-rater agreement**. Polygon ส่วนใหญ่สื่อถึง visible part แต่มีความหยาบ ความเบลอ และขอบเขตที่ยังไม่ยืนยันอย่างสมบูรณ์ จึงเรียก annotation agreement.

หลักเกณฑ์ GT-only: คงส่วนเล็ก/ถูกบัง/ภาพยากไว้; กันเฉพาะกรณีที่เห็นว่าเป็น interior patch, ขาดส่วนที่มองเห็น, รวม exposed torso, มีความกำกวม garment/object หรือแบ่ง one-piece เป็น Upper/Lower โดยไม่มีกติกา. ไม่ตัดจากคะแนนโมเดล ไม่แก้ polygon. Primary เหลือ315parts: Face34/Hair69/Upper115/Lower97. All-source sensitivity เก็บ324parts:34/69/120/101. ดู [aggregate QA record](reports/SELECTED_PART_QA_SUMMARY.json); ภาพและ exclusion ledger รายคนอยู่ private outputs เท่านั้น. การกรองนี้อาจผิดได้ จึงต้องอ่าน sensitivity และข้อจำกัดร่วมกัน.

Face อาจรวม neck ตาม annotation; Sapiens ยังเป็น Face_Neck proxy. Upper/Lower วัดตาม reference ที่ให้มา ไม่อ้างยืนยัน non-Dress ontology ทั้งชุด. กรณี one-piece ที่ระบุได้กันออกจาก primary โดยไม่แบ่ง prediction ด้วย heuristic. กรณีอื่นที่ตรวจไม่พบอาจยังเหลืออยู่.

## การผูกคน: ใช้ frozen detector เหมือนกันทุกระบบ

ใช้ Human_ids เฉพาะ union ของ annotated parts เป็น geometry สำหรับ **evaluation matching** ไม่ถือเป็น full silhouette และไม่ป้อน GT เข้า inference. จับคู่หนึ่งต่อหนึ่งกับ frozen YOLO opportunities: GT-union coverage ใน detector bbox ต้อง ≥0.50; maximize cardinality ก่อน sum coverage. Bbox ใช้ floor(left/top), ceil(right/bottom) และ clip ที่ image bounds. ไม่ใช้ target class หรือ parser semantic agreement.

GT เรียง canonical geometry (bbox/area/mask hash; source ID เฉพาะ geometry ซ้ำ). เมื่อ objective เท่ากัน คง optimum แล้วเลือกตาม detector confidence สูงสุด, bbox coordinates และ stable opportunity ID. มี duplicate-detection tie1กรณี ตรวจภาพโดยซ่อน parser outputs; ใช้กติกา confidence ที่ประกาศเดียวกัน. ไม่อ้างว่า identical geometry มี identity ที่พิสูจน์ได้เสมอ. Threshold เป็น project-defined identity-association policy ไม่ใช่ segmentation pass threshold.

GT person21records ไม่มี opportunity ผ่านเงื่อนไข: **คง GT parts ในตัวหารและให้ prediction ว่าง** ไม่ตัดคนเหล่านี้ทิ้ง. หาก detector matched แต่ native parser ไม่ได้ associate มาที่ opportunity นั้น ให้ prediction ว่างเช่นกัน. รายงาน miss coverage แยกจาก execution failures.

## Prediction และ FP/FN

ใช้ final per-person planes ที่ export แล้วพร้อม native ownership เดิม. QANet ใช้ YOLO ROI/mask clipping; Sapiens full-frame semantics ถูกแบ่งด้วย YOLO masks; native instance parsers ใช้ prediction-only association ที่บันทึกไว้. Association list order ตรงกับ final array order; `prediction_index` ใน metadata อ้าง native array ก่อน selection **ห้ามนำมา index final array**. Sapiens ตรวจ extents/scores ตรง detector cache order. Duplicate opportunity หรือ invalid ID/geometry/binding เป็น contract failure.

สำหรับ GT person i และ target c ที่ annotate: G_ic คือ pixel ของ Human_id i และ target c. P_ic คือ **target mask เต็ม original grid ของ final person plane ที่จับคู่แล้ว**. ไม่ clip P ด้วย GT polygon, GT bbox, positive domain หรือวาด prediction เพิ่ม. Predictions ของคนอื่นที่ไม่ได้ annotate ไม่เป็น negative instances; แต่ถ้า mask ของคนที่เลือกทายล้นไปคนอื่น/พื้นหลัง จะนับ FP ของคนนั้น.

CIHP0–19/Sapiens0–28 ใช้ total mapping revision2 เดิม: CIHP Face13; Hair2; Upper5+7; Lower9+12. Sapiens Face3+24–28; Hair4; Upper23; Lower13. Dress/Apparel และ native classes อื่นคง OTHER; BG คง BG. ไม่แยก coarse labels ด้วย geometry. ใน per-person evaluation ไม่ compose คนหลายคนเป็น global mask จน identity หาย; project แต่ละ final plane แล้วเลือก binary target. Unsupported→ไม่มี target prediction/FN เมื่อ GT ต้องการ, ไม่ใช่ execution failure. Unknown ID/255 ของ prediction เป็น contract failure. GT ชุดนี้ไม่มี255; ห้ามประดิษฐ์ ignore ตามโมเดล.

## Metrics, denominator และ selection

TP=|G∩P|, FP=|P\G|, FN=|G\P|; IoU=TP/(TP+FP+FN), Dice=2TP/(2TP+FP+FN), precision=TP/(TP+FP), recall=TP/(TP+FN). ทุก GT part ที่ให้คะแนนมี support>0. Empty prediction รวม detector/association miss ให้ IoU/Dice/recall0; precision null เมื่อไม่มี predicted pixels. ไม่มี annotated target สำหรับคนนั้น→ไม่มี evaluation item ไม่ตีความว่า absent negative. ไม่มี support ทั้งกลุ่ม→null ไม่แทน0หรือ1.

**Primary:** เฉลี่ย IoU ของ GT parts ภายในแต่ละ target แล้วเฉลี่ย4targetsเท่ากัน (`macro_mean_selected_part_IoU4`). Face ไม่ถูกกลบด้วย Upper ที่มีจำนวนหรือพื้นที่มากกว่า. Secondary: mean-part Dice แบบเดียวกัน; pooled TP/FP/FN/IoU/Dice/P/R ราย target; day/night และ coverage. Pooled metrics เป็นการสะสม selected instances ไม่ใช่ global confusion เต็มภาพ. ไม่เฉลี่ย IoU คลาสย่อยแทน garment union.

Selection: ระบบ STRICT_COMPLETE ที่ได้ primary สูงสุดคือ **observed leader ของ selected-part task นี้**. รายงานคะแนนทุกระบบใน frozen roster order พร้อม all324 sensitivity และ per-target trade-offs. ไม่สร้าง weighted score หลังเห็นผล ไม่อ้าง statistical significance, architecture-only superiority, full-CCTV winner หรือ final deployment acceptance. ไม่มี speed/VRAM ranking.

## Completeness, provenance และการรันซ้ำ

ทุกระบบต้องมี exact90unique source IDs แม้บางภาพไม่เหลือ eligible primary parts. ตรวจ atomic NPZ/metadata/score hashes ขณะอ่านเพื่อคำนวณคะแนนใหม่, GT Category/Human bindings, checkpoint/input/config/detector identities และ original-grid geometry. เก็บ fresh derived records/atomic writes/ledger ใน private output directory; native metrics และ packets read-only. Incomplete/invalid ระบบใด primary=null ไม่ใช้ subset เป็นผลเต็ม. Source/protocol/GT-binding hashes ตรึงก่อน scoring; commit เป็น snapshot ของข้อกำหนดใหม่นี้ ไม่ใช่ launch commit ของ inference เก่า.

CPU acceptance ใช้ hand-counted spill FP, wrong-class/empty/OTHER, source-native-index versus final-array order, duplicate opportunity rejection, detector misses, geometry/ID renaming, confidence tie และ JSON null. ทดสอบเฉพาะส่วนใหม่ ไม่ rerun GPU benchmark. ใช้ Python environment เดิมที่มี NumPy/Pillow/SciPy และ shared common_view code. Reproduction ต้องมี private GT, frozen detector/native packets และ GT-review binding ซึ่ง public clone ไม่มี; aggregate CSV และ hashes ตรวจเลขได้แต่สร้าง full experiment กลับมาเองไม่ได้.

อ้างอิงสูตร/เครื่องมือ: [scikit-learn Jaccard score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.jaccard_score.html), [SciPy bipartite assignment](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html). แหล่งเหล่านี้ยืนยันนิยาม/เครื่องมือ ไม่ได้รับรองคุณภาพ annotation, threshold0.50 หรือ protocol เฉพาะโครงการ.
