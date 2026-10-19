# ตรวจคุณภาพ CCIHP ด้วยภาพจริง — Assistant review

ตรวจวันที่ 12 ตุลาคม 2026 · Run: `ccihp-assistant-review-20261012T072037Z`

**ผลตรวจ: พบข้อจำกัดจริงบางกรณี แต่ยังไม่มีหลักฐานว่าปัญหา ownership ขนาดใหญ่เกิดแพร่หลายในชุดที่ตรวจ** คนหลักในภาพส่วนใหญ่ดูแยก Human ID และวาง semantic regions สอดคล้องกับ RGB ในระดับภาพคัดกรอง จึงไม่ควรเหมารวมว่า annotations ทั้งชุดใช้ไม่ได้ อย่างไรก็ตาม ภาพที่ดูเรียบร้อยอาจมี GT ขาด semantic labels หรือมี ID ขนาดหนึ่งพิกเซลซ่อนอยู่

ผมคัด **5 ภาพที่มีประเด็นชัดเจนหรือควรตัดสินนโยบาย** ไว้ด้านล่าง ไม่จำเป็นต้องไล่เปิด 200 ภาพเพื่อเห็นข้อจำกัดเหล่านี้ ภาพทั้งหมดเป็น TRAIN ไม่มี parser inference และไม่มีการแก้ GT หรือเปลี่ยน population การประเมิน

## ตรวจอะไรจริง

| งาน | ขอบเขตที่ทำแล้ว | สิ่งที่ยังยืนยันไม่ได้ |
|---|---|---|
| ดูภาพตามชุดสุ่มเดิม | 200 TRAIN images ครบ 50 contact sheets; RGB / Human / Category ครบทุกภาพ | ไม่รับรองขอบ mask รายพิกเซลจากภาพย่อ |
| ตรวจกรณีเจาะจง | 13 ภาพ เปิด diagnostic บนกริดต้นฉบับและอ่าน RGB/GT โดยตรง ตรวจ source SHA256 | กรณีที่เลือกเจาะจงไม่ใช่ตัวอย่างสำหรับประมาณ prevalence |
| ภาพขยาย | 5 กรณี ระบุ ROI ในพิกัดต้นฉบับและขยายด้วย nearest-neighbor เพื่อดูเท่านั้น | ภาพขยายไม่ใช่ GT ใหม่ |
| ตรวจข้อมูลตัวเลข | semantic support, unknown class, single-pixel ID และจุดอ้างอิงของคนที่ไม่มี labels | ไม่มี manual GT ใหม่สำหรับคนที่ตกหล่น |
| Independent human review | checklist เดิมยัง PENDING และไม่ได้แก้ | Assistant review ไม่ใช่การตัดสินจากผู้ตรวจอิสระ |

ชุด 200 ภาพยังใช้ sampling frame / strata / seed / inclusion probabilities จาก [TRAIN_REVIEW_SAMPLE.json](../provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/TRAIN_REVIEW_SAMPLE.json) โดยไม่เลือกใหม่ตามผลที่ต้องการ ภาพ warning นอกชุดสุ่มแยกเป็น purposive diagnostics

## วิธีอ่านภาพ

ซ้าย = RGB, กลาง = Human IDs, ขวา = Category IDs สีจาง/มืดในภาพ GT แสดงค่าศูนย์ ส่วนสี magenta ใน Category panel แสดง ID 22 **สีของ Human กับสีของ Category ไม่ได้มีความหมายเหมือนกัน** ให้ดูค่าตัวเลขประกอบ

Full-frame panels ใช้กริดต้นฉบับเดียวกัน ROI ใช้พิกัด `[x0,y0,x1,y1)` โดยไม่เปลี่ยน source arrays ภาพ ROI v2 ไม่ใส่ตัวอักษร Human ID ทับพิกเซล เพื่อไม่บังจุดเล็กที่กำลังตรวจ

## Case 1 — มีคนครบใน Human map แต่ semantic GT ของคนซ้ายหาย

**TRAIN/0014422 — ยืนยัน semantic support gap จากข้อมูลจริง** · purposive warning case

![คนซ้ายมี Human ID แต่ไม่มี semantic GT](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0014422_full.png)

**Observation:** ผู้หญิงด้านซ้ายมี Human ID 1 ครอบคลุม **91,332 พิกเซล** แต่ Category เป็น 0 ทุกพิกเซล และ Instance เป็น 0 ทุกพิกเซล ขณะที่ผู้หญิงด้านขวามี Hair, Face และ labels อื่นตามปกติ ขนาดภาพ 500×367

**Interpretation:** นี่เป็นช่องว่างระหว่าง GT person identity กับ GT semantic parsing ที่มีขนาดใหญ่ ไม่ใช่แค่ขอบหนึ่งหรือสองพิกเซล หากนำ Category0 ไปใช้เป็น background โดยไม่ตรวจ Human map การทำนายใบหน้าหรือผมของคนซ้ายอาจถูกให้โทษจาก GT ที่ไม่ให้ class support เราตรวจยืนยันความไม่สอดคล้องนี้ได้ แต่ยังไม่ทราบสาเหตุการสร้าง annotation

**ให้ดูตรงไหน:** เปรียบเทียบผู้หญิงซ้ายระหว่าง panel กลางกับขวา คนเดียวกันมี Human mask แต่ไม่มี semantic colors เลย ดู [ภาพขยาย](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0014422_ROI_v2.png) ได้ด้วย

**ข้อเสนอสำหรับ review:** ต้องกำหนดวิธีรายงานคนที่ไม่มี semantic support แยกจาก native person count และทำ sensitivity analysis ที่ระบุ denominator ชัดเจน ก่อน freeze protocol ไม่เติม labels หรือทิ้ง Human ID อัตโนมัติ

## Case 2 — บริเวณผ้าใช้ Category22 ที่ไม่มีนิยาม

**TRAIN/0010505 — ยืนยัน undocumented category** · purposive warning case

![Category22 บนภาพเต็ม](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0010505_full.png)

![Category22 บนบริเวณผ้าที่ขยาย](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0010505_ROI_v2.png)

**Observation:** มี Category22 **2,938 พิกเซล** ทั้งหมดอยู่ใน Human ID 1 และ Instance0 ภาพเต็มแสดงทั้งบริเวณผ้าที่ห้อยลงกลางภาพและส่วนเล็กใกล้เครื่องประดับศีรษะ ROI เน้นบริเวณผ้า `[326,170,400,336)`; จำนวน 2,938 เป็นทั้งภาพ ไม่ใช่จำนวนเฉพาะ ROI

**Interpretation:** README ใน archive ให้ foreground definitions เฉพาะ 1–21 จึงยัง map 22 เข้ากับ class ที่มีชื่อไม่ได้ ภาพแสดงว่าอย่างน้อยส่วนใหญ่ในกรณีนี้เป็นบริเวณวัตถุที่มองเห็นจริง ไม่ควรถือเป็น background หรือเดาชื่อ class จากรูปลักษณ์

**ให้ดูตรงไหน:** สี magenta ใน Category panel ตรงผ้าแดงใต้มือที่จับกัน การเห็นว่าเป็นผ้าไม่ได้ยืนยันว่าผู้สร้าง dataset ตั้งใจเรียก class ใด

**ข้อเสนอสำหรับ review:** คง source22 แยกเป็น unresolved label เสนอ explicit unknown-pixel policy และรายงาน coverage ที่ได้รับผล ไม่เลือก mapping ตามผลคะแนนโมเดล

## Case 3 — Human ID ที่เป็นหนึ่งพิกเซลอยู่บนคนอื่น

**TRAIN/0000287 — ยืนยัน degenerate person identity** · purposive warning case

![Human ID หนึ่งพิกเซลในภาพเต็ม](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0000287_full.png)

![จุดหนึ่งพิกเซลบนเสื้อของคนซ้าย](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0000287_ROI_v2.png)

**Observation:** นอกจาก Human1 และ Human2 ที่มี mask ของนักวิ่งสองคนแล้ว Human3 มีเพียง **1 พิกเซลที่ `(x=70,y=257)`**, Category0 / Instance0 อยู่บนบริเวณเสื้อสีชมพูของคนซ้าย กล่องเหลืองใน ROI เป็นเส้นช่วยชี้ตำแหน่ง; ไม่ใช่การเพิ่ม mask

**Interpretation:** ID นี้ไม่มีพื้นที่ semantic ที่ใช้ประเมินคนหนึ่งคนได้ หากนับทุก positive Human ID เป็น person-macro denominator หรือ detector target โดยไม่แยกสถานะ จะเกิด target ที่ไม่มี usable semantic support ภาพนี้ไม่ได้พิสูจน์ว่าคนที่มองเห็นทั้งหมดควรมีเพียงสองคน และเราไม่ได้ลบ ID3

**ข้อเสนอสำหรับ review:** แยก native ID count จาก evaluable-person count ด้วยกฎที่ต้องอนุมัติและ sensitivity ที่โปร่งใส ไม่ตัดสินด้วย threshold พื้นที่โดยอัตโนมัติ

## Case 4 — ผู้ป่วยกลางภาพมองเห็น แต่ไม่มี GT person

**TRAIN/0034455 — ยืนยัน coverage omission; สาเหตุยังไม่ทราบ** · มาจากชุดสุ่ม 200 ภาพ

![ผู้ป่วยไม่มี Human ID ระหว่างคนสองคนที่มี GT](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0034455_full.png)

![ใบหน้าและแขนผู้ป่วยในภาพขยาย](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0034455_ROI_v2.png)

**Observation:** มี Human IDs สองคนสำหรับบุคลากรทางซ้ายและผู้เยี่ยมทางขวา แต่ใบหน้าและส่วนแขนที่เห็นของผู้ป่วยตรงกลางไม่มี Human/Category overlay จุดอ้างอิงบนใบหน้า `(211,159)` มี Human0 / Category0 / Instance0

**Interpretation:** เป็นตัวอย่างที่การตรวจ label ranges หรือ image dimensions อย่างเดียวจับไม่ได้ การทำนายผู้ป่วยเพิ่มอาจถูกมองเป็น unmatched prediction ภายใต้ GT นี้ จึงต้องแยก “ไม่ตรงกับ GT” จาก “ไม่มีคนจริง” อย่างไรก็ตาม ยังไม่ยืนยันว่า dataset ต้อง annotate คนที่เห็นทุกคน เราจึงไม่สรุปสาเหตุว่าเป็นความผิดของผู้ annotate

**Counterexample:** ใน TRAIN/0019562 ผู้ป่วยบนเตียงมี **Human6 / 2,683 พิกเซล** และ semantic labels หลาย class ตาม [ภาพนี้](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0019562_full.png) จึงไม่ควรอธิบายว่า dataset ไม่ annotate ผู้ป่วยหรือคนใต้ผ้าห่มทั้งหมด

**ให้คุณช่วยตัดสิน:** เห็นว่า omission นี้มีผลต่อโจทย์คนทั้งภาพของเรามากน้อยเพียงใด ไม่ต้องสร้าง mask ใหม่จากภาพ เราจะคง GT และรายงาน annotation coverage limitation

## Case 5 — คนเดินแถวที่มองเห็นชัดไม่ได้รับ Human ID

**TRAIN/0008613 — ยืนยัน coverage omission; สาเหตุยังไม่ทราบ** · มาจากชุดสุ่ม 200 ภาพ

![มี Human IDs สี่คน แต่คนด้านขวาไม่มี GT](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0008613_full.png)

![คนด้านขวาที่ไม่ถูก annotate](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0008613_ROI_v2.png)

**Observation:** คนหลักบางคนมี Human IDs 1–4 แต่คนด้านขวาที่ยังเห็นใบหน้า เสื้อ กางเกง และรองเท้าไม่มี labels จุดอ้างอิงบนใบหน้า `(300,274)` เป็น Human0 / Category0 / Instance0

**Interpretation:** กรณีนี้ไม่ได้เป็นเพียงคนเล็กมากที่อยู่ไกล และแสดงข้อจำกัดของการใช้ native GT เป็น target สำหรับ “ทุกคนที่ปรากฏ” แต่ยังไม่ทราบว่าผู้สร้างตั้งใจเลือกเฉพาะ subset หรือเกิดการตกหล่น จึงแยก verified missing GT coverage ออกจาก confirmed annotation mistake

**ให้คุณช่วยดู:** ความสำคัญของคนที่ไม่มี GT ต่อ end-to-end person coverage และการอ่าน FP ไม่ควรเติม GT โดยเดา ownership หรือเอา YOLO มาสร้างแทน

## สิ่งที่ดูแปลกแต่ยังไม่ควรเรียก error

| ภาพ | ผลตรวจต่อ | ข้อสรุปที่ใช้ได้ |
|---|---|---|
| [0004381 — กระเป๋าใบใหญ่](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0004381_full.png) | Human3 รวม Bag20 จำนวน 28,494 พิกเซล; README รวม shoulder bags | Silhouette กว้างไม่ได้แปลว่า person mask leakage; accessories อาจขยายเกินกายวิภาค |
| [0019700 — หนังศีรษะ](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0019700_full.png) | Scalp ถูกระบุ Hair2; README ระบุ Sparse/bald สำหรับ Hair | มีนิยามรองรับ จึงไม่จัดเป็นผิด class เพียงเพราะมองไม่เห็นเส้นผม |
| [0031399 — ทารกในผ้าห่ม](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0031399_full.png) | Human3 มีหัว/หมวก/เสื้อ แต่ผ้าห่มไม่รวม; 7,847 พิกเซลมี class support | ยังไม่ทราบข้อกำหนดผ้าห่ม/occlusion; ไม่ถือว่าต้องเติมร่างกายที่ถูกบัง |
| [0026977 — Human4 พื้นที่เล็ก](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0026977_full.png) | 1,716 พิกเซล; classes5/9/14; ส่วนที่เห็นอาจเป็นคนด้านหลังที่ถูกบัง | ไม่มีหลักฐานพอเรียกว่า duplicate person ID; ห้ามลบจากจำนวนหัวที่เห็น |
| [0002891 — พื้นที่สามเหลี่ยม](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0002891_full.png) | Category9 บริเวณใกล้ clipboard อาจเป็นเข่าที่งอ | ไม่ยืนยันว่าติดวัตถุผิดจากภาพเดียว |
| [0028338 — ตัวหนังสือทับภาพ](../outputs/visualizations/ccihp-assistant-review-20261012T072037Z/details/0028338_full.png) | GT หลักสิ้นสุดเหนือส่วนลำตัวด้านล่างที่มีแถบตัวหนังสือ | เป็น coverage/visibility-policy question; ไม่สรุป amodal semantics |

บันทึกระหว่าง contact screening ของ `0003009` เคยตั้งข้อสงสัยเรื่องเครื่องดนตรี แต่เมื่อเปิดต้นฉบับพบว่าเป็นภาพกลุ่มทหาร จึง **ถอนข้อสงสัยนั้น** และบันทึก correction ใน machine-readable adjudication ไม่ใช้เป็นหลักฐาน error

## ข้อสรุปและผลต่อการตัดสิน dataset

**Observation:** ภาพคนหลักส่วนใหญ่ใน contact screen ดูสอดคล้องกัน แต่มี semantic support gap, undocumented label และ degenerate Human ID ที่ตรวจค่าจริงได้ อีกสองตัวอย่างมีคนที่มองเห็นแต่ไม่มี annotation

**Interpretation:** CCIHP ยังมีข้อมูลที่ใช้ศึกษา body/clothing/person parsing ได้ และข้อจำกัดเหล่านี้ไม่ใช่หลักฐานว่าทั้ง dataset ใช้ไม่ได้ แต่การประเมินต้องมี semantic-support/unknown-label/coverage reporting ที่ชัดเจนก่อน freeze protocol โดยเฉพาะ person-macro และ detector-conditioned tracks

**สถานะ:** Assistant review เสร็จพร้อม warnings; independent human review ยังคง PENDING ไม่ได้เลื่อน CCIHP เป็น primary อัตโนมัติ ไม่ได้ประมาณอัตรา annotation errors ของ dataset และไม่อ้างว่าได้ตรวจละเอียดทุก boundary ของ 33,280 ภาพ

หากต้องการตัดสินว่า “กรณีเฉพาะเหล่านี้ยอมรับได้สำหรับโจทย์หรือไม่” ให้เริ่มดู Case1, Case4 และ Case5 ส่วนข้อผิดปกติเชิงข้อมูลใน Case1–3 ยืนยันได้โดยไม่ต้องเดาจากสี overlay หากต้องการประมาณ prevalence อย่างเป็นวิทยาศาสตร์ ยังต้องใช้ independent reviewed sample และเกณฑ์ adjudication ที่ชัดเจน

## หลักฐานและการตรวจสอบ

- [บันทึก assistant screen ครบ 200 ภาพ](../provenance/RUN_MANIFESTS/ccihp-assistant-review-20261012T072037Z/ASSISTANT_SCREEN_CHECKLIST.csv)
- [ข้อสังเกตและ numeric assertions รายกรณี](../provenance/RUN_MANIFESTS/ccihp-assistant-review-20261012T072037Z/DETAIL_ADJUDICATION.json)
- [Source hashes / masks / image dimensions](../provenance/RUN_MANIFESTS/ccihp-assistant-review-20261012T072037Z/DETAIL_SOURCE_MANIFEST.json)
- [ROI v2 พิกัดและ hashes](../provenance/RUN_MANIFESTS/ccihp-assistant-review-20261012T072037Z/ROI_DETAIL_V2.json)
- [Validation ของ run](../provenance/RUN_MANIFESTS/ccihp-assistant-review-20261012T072037Z/VALIDATION.json)
- [Full structural audit เดิม](CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md) และ [Human review เดิม](CCIHP_HUMAN_REVIEW_STAGE0F.md)

Dataset archives, source GT, original splits, previous scientific state และ human-review checklist เดิมคงไว้ ไม่มี inference / training / benchmark / taxonomy freeze ในงานนี้
