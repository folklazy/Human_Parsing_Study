# CPI channel evidence — ทางเลือกเมื่อไม่ต้องการรอผู้สร้าง

**เอกสารปรึกษาการตัดสินใจ: ยังไม่เปลี่ยน gate/config ไม่รับรอง mapping และไม่อนุญาต benchmark**

ข้อเสนอของผมคือ **ยังไม่ตัด CPI ออกจากโครงการ** เพราะสิ่งที่พบคือช่องว่างของ semantic provenance ไม่ใช่หลักฐานว่า checkpoint ใช้ไม่ได้หรือ class order ผิด มีทางเลือกทั้งการรับหลักฐานทางอ้อมอย่างเปิดเผยและการพัก CPI จากคะแนนหลัก โดยไม่ต้องรอจนทั้งโครงการหยุด

## สิ่งที่ตรวจเพิ่มในรอบนี้

ตรวจ metadata จากไฟล์ weights ที่มีอยู่โดยอ่านเฉพาะ `archive/data.pkl` และแยก pickle opcodes ไม่ deserialize pickle ไม่ import torch และไม่โหลดโมเดล:

| Checkpoint | Metadata bytes | สิ่งที่พบ | ผลต่อ blocker |
|---|---:|---|---|
| CPI_R50_CIHP | 283,823 | `meta.CLASSES=('person',)`; ไม่พบ ordered parsing names ใน string scan | ยังไม่ปิด channel-order evidence |
| CPI_ConvNeXtB_CIHP | 379,959 | `meta.CLASSES=('person',)`; ไม่พบ ordered parsing names ใน string scan | ยังไม่ปิด channel-order evidence |

`person` เป็น detection-class metadata ไม่ใช่รายชื่อ body/clothing channels การตรวจนี้ไม่อ้างว่าพิสูจน์การไม่มีข้อมูลทุก encoding ที่เป็นไปได้ ไม่มีการค้น README หรือ external annotation sources เพิ่ม

[รายละเอียดวิธีตรวจ/metadata hashes/opcodes](../provenance/RUN_MANIFESTS/cpi-evidence-alternatives-20261016T062257159176Z/CHECKPOINT_METADATA_STATIC_INSPECTION.json)

## ทางเลือกและสิ่งที่ต้องยอมรับ

| ทางเลือก | ข้อดี | สิ่งที่แลก | ความเห็น |
|---|---|---|---|
| คง direct-evidence gate แล้วรอผู้สร้าง | รักษาระดับหลักฐานเดิม | เวลาไม่แน่นอน; คู่นี้ยังไม่มีคะแนน semantic หลัก | ทำคู่ขนานได้ แต่ไม่ควรให้หยุดทุกงาน |
| ยอมรับ standard-CIHP mapping จากหลักฐานประกอบ พร้อม TRAIN consistency review | ใช้ checkpoint เดิมและงาน integration ที่เตรียมไว้ | ยังมี semantic provenance uncertainty; ต้องแก้นโยบายอย่างเปิดเผยก่อน final evaluation | ทางที่เสนอ หากผู้ใช้ยอมรับข้อจำกัดนี้ |
| พัก CPI จาก primary scored cohort แต่คงใน registry/technical evidence | เดินระบบอื่นโดยรักษา direct-evidence gate | ต้องตรวจ mappings และ route ของกลุ่มใหม่; ไม่ใช่เปลี่ยนชื่อโมเดลใน config แล้วรันได้ทันที | ทางสำรองหากต้องการระดับความมั่นใจเดิม |
| ตัด CPI ออกจากโครงการทั้งหมด | ลดขอบเขตงาน | เสียตัวเปรียบเทียบที่รันจริงได้ โดยยังไม่พบหลักฐานว่า mapping ผิด | ยังไม่แนะนำจากเหตุผลนี้เพียงอย่างเดียว |

## ถ้าเลือกใช้หลักฐานประกอบ ต้องทำอย่างไร

1. บันทึก decision revision ก่อนดู validation scores ว่ารับหลักฐานระดับใดและมี uncertainty อะไร สถานะเช่น `ACCEPTED_WITH_INDIRECT_EVIDENCE` ต้องแยกจาก `DIRECT_VERIFIED` โค้ดปัจจุบันยังไม่ยอมรับสถานะแรก จึงไม่ใช่เพียงแก้ข้อความในรายงานแล้วข้าม gate
2. รักษา proposed standard-CIHP numeric mapping ที่ประกาศไว้ก่อนหน้า ตรวจ source/config/decoder chain และผูก checkpoint hashes ของแต่ละตัว ห้ามค้น permutation ที่ทำคะแนนสูงสุดแล้วเรียกว่าค้นพบ official mapping
3. เริ่มจาก saved TRAIN predictions และ GT ที่มีอยู่ สร้างภาพแสดง **numeric channel IDs** และตารางความสอดคล้องของ GT regions กับ predicted channels เพื่อท้าทายสมมติฐานเดิม แยก model error ออกจากข้อสงสัยเรื่อง mapping ไม่ใช้ validation เลือก mapping หรือ thresholds
4. ตรวจหลักฐานให้ครอบคลุม target distinctions ที่นำมาให้คะแนนจริง โดยเฉพาะ Face, Torso-skin, arms, legs, selected garments และ footwear หากไม่มี torso support ในตัวอย่างเดิม ให้ระบุว่า NOT_COVERED ไม่ถือว่าภาพสวยหนึ่งภาพรับรองครบ หากต้องเพิ่ม TRAIN inference ต้องเสนอขอบเขตและได้รับอนุญาตก่อน
5. รายงานว่าเป็น mapping ที่โครงการยอมรับจากหลักฐานประกอบ ไม่อ้างว่าอ่าน original training header หรือได้รับคำยืนยันจากผู้สร้าง ผลที่ออกมาคือระบบภายใต้ mapping/configuration นี้ พร้อมข้อจำกัดของหลักฐาน

ภาพและ confusion table ช่วยตรวจความสอดคล้องเชิงพฤติกรรม แต่ไม่พิสูจน์ลำดับ channel ทางประวัติศาสตร์ได้แน่นอน หากพบความขัดแย้งเป็นระบบ ให้กลับไปพัก mapping ไม่ remap ตามคะแนนโดยอัตโนมัติ

โจทย์กลุ่มแรกเป็น coarse targets การสลับ left/right ภายใน arms หรือ legs และการสลับชนิดเสื้อผ้าภายใน garment union เดียวกันไม่เปลี่ยนคะแนน target projection นั้น จึงแยกได้ระหว่างหลักฐานของ **target mapping ที่ใช้จริง** กับหลักฐานของ **รายชื่อ native labels ทั้งหมด** แต่การรับรองแบบ target-level เป็นการเปลี่ยนขอบเขตหลักฐานที่ต้องบันทึก ไม่ทำให้ชื่อ native labels ทุกช่องถูกยืนยันตามไปด้วย

## ถ้าไม่ยอมรับ uncertainty นี้

ให้ใช้สถานะ **DEFERRED_FROM_PRIMARY_SCORING** สำหรับ CPI แทนการลบ weights/ผล smoke แล้วพิจารณาระบบอื่นเป็นกลุ่มแรก เช่น M2FP_R101_CIHP มี CIHP category catalog ใน [official implementation](https://github.com/soeaver/M2FP/blob/main/m2fp/data/datasets/register_cihp_parsing.py) ของตัวเอง จึงเป็น candidate ที่มีแหล่ง semantic declaration ต่างจากการอาศัย catalog ข้ามโมเดล อย่างไรก็ตาม ยังต้องตรวจ checkpoint-specific binding, adapter และ actual route ก่อนรับเข้ากลุ่ม ไม่ได้ benchmark-ready โดยอัตโนมัติ

FASHN และ parsers อื่นยังคงมีบทบาทตาม capability/cohort ที่รองรับจริง ไม่จำเป็นต้องบังคับเข้า six-target cohort เดิมหากรองรับไม่ครบ หรือเปลี่ยน void/domain เฉพาะโมเดลเพื่อให้เข้ากลุ่ม

## คำแนะนำ

สำหรับงานเปรียบเทียบ pretrained systems ของนักศึกษา ผมเสนอ **เก็บ CPI ไว้ และพิจารณายอมรับหลักฐานประกอบพร้อม TRAIN consistency review ที่ขอบเขตชัดเจน** เป็นทางที่พอเหมาะกับต้นทุน โดยต้องยอมรับความไม่แน่นอนในรายงาน หากต้องการคงความมั่นใจแบบ direct evidence เดิม ให้พัก CPI จาก primary scoring แล้วเดินระบบอื่นก่อน การติดต่อผู้สร้างเป็นงานคู่ขนานที่ไม่จำเป็นต้องเป็น critical path ของทั้งโครงการ

รอบนี้มีเพียง read-only inspection และข้อเสนอ ไม่มีการแก้ source/evaluator/config/decision/gate ไม่มี inference, accepted contexts หรือ benchmark ใหม่ ยังไม่มีการส่งข้อความหาผู้สร้าง
