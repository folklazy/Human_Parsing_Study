# CPI CIHP channel order — ผลตรวจแหล่งที่เกี่ยวข้องและ blocker

**นโยบายปิดแล้ว · semantic acceptance ของสอง CPI พักไว้ · benchmark ยังไม่อนุญาต**

รอบนี้ติดตามเฉพาะ annotation/preparation/release links และสาย numeric label ของ CPI_R50_CIHP / CPI_ConvNeXtB_CIHP ไม่มี source-code/config changes, tests เพิ่ม/รันซ้ำ, GT reconstruction ซ้ำ, model inference หรือการส่งข้อความหาผู้สร้าง ไม่ใช้จำนวน tests ทดแทนหลักฐานที่ขาด

## 1. ผลสืบค้น: ไม่ใช่เพียงตรวจ Git tree/Releases

พบว่า preferred checkout `HAG-uestc/CPI-Parser` เป็น fork ของ [JosonChan1998/CPI-Parser](https://github.com/JosonChan1998/CPI-Parser) จึงตาม parent ที่ repository อ้างโดยตรง ไม่ใช้ fork ที่ไม่ทราบความสัมพันธ์แทนหลักฐาน ผู้ให้บริการ GitHub ระบุความสัมพันธ์นี้ใน metadata ที่บันทึกไว้ก่อนหน้า และ current README ทั้งสองแห่งมี bytes/SHA256 ตรงกัน

ตรวจ upstream README ทั้ง **4 revisions** ซึ่ง API ประวัติ README ส่งกลับมา ตั้งแต่ initial code ถึง pinned `d62cae523ba913fec4a7fda5816bc1d96bbf644d` ทุกฉบับมี dataset directory layout แต่ไม่มี annotation download URL/preparation script link ของ CIHP โดยตรง

| แหล่งที่ตรวจ | ผลเข้าถึง | สิ่งที่พบ / สิ่งที่ยังไม่ได้ |
|---|---|---|
| [HAG current README](https://raw.githubusercontent.com/HAG-uestc/CPI-Parser/master/README.md) | HTTP200 | ระบุ `train_parsing`, `val_parsing`, `annotations`; ไม่มี annotation URL |
| [Linked upstream README](https://raw.githubusercontent.com/JosonChan1998/CPI-Parser/master/README.md) | HTTP200 | เนื้อหาเหมือน preferred fork; ไม่มีลิงก์ annotation เพิ่ม |
| [README history API](https://api.github.com/repos/JosonChan1998/CPI-Parser/commits?path=README.md&per_page=10) และ raw README ของอีก 3 revisions | HTTP200 ทุกไฟล์ | ไม่มี annotation/preparation link ที่ถูกลบไปใน revisions ที่ตรวจ |
| `configs/_base_/datasets/cihp.py` ของ pinned source | Local read / hash recorded | อ้าง `data/CIHP/annotations/CIHP_train.json` และ `CIHP_val.json` เป็น local paths ไม่ใช่ download URLs |
| MMDetection links ใน README/README_zh-CN | ตรวจ destination จากข้อความ | เป็น framework installation/general documentation ไม่ใช่ CPI CIHP annotation release จึงไม่ถือเป็น source header |
| [R50 model link ใน README](https://drive.google.com/file/d/1uiqPVZNWIEIKquMNhZ7tv3OTZrc9WGt0/view) | HTTP200 preview | ชื่อ `r50-epoch_75.pth`; เป็น model release link ไม่พบ annotation/header link ในหน้าที่ตรวจ |
| [ConvNeXt-B model link](https://drive.google.com/file/d/117grkZS6Q-v5tbeTLdyENSI0fSRD09lK/view) | HTTP200 preview | ชื่อ `convnext-b-epoch_75`; เป็น model release link ไม่พบ annotation/header link ในหน้าที่ตรวจ |
| [Upstream public issue metadata](https://api.github.com/repos/JosonChan1998/CPI-Parser/issues?state=all&per_page=50) | HTTP200 / empty list | ไม่มี public annotation clarification ให้ติดตามจากผลตอบกลับนี้ |

[Access log](../provenance/RUN_MANIFESTS/cpi-channel-order-source-investigation-20261016T043120768600Z/ACCESS_LOG.json) เก็บ URL/status/bytes/SHA256 และสำเนาที่อ่านจริง รวม 9 server requests / 189,752 bytes เป็น metadata/README/preview เท่านั้น ไม่ดาวน์โหลด weight/archive ใหม่ [Tool access notes](../provenance/RUN_MANIFESTS/cpi-channel-order-source-investigation-20261016T043120768600Z/TOOL_ACCESS_NOTES.json) แยกกรณี web tool เข้าถึงไม่ได้แต่ server request สำเร็จ จึงไม่เรียก Drive ว่าดาวน์โหลดไม่ได้หรือสรุปว่าไม่มีสิทธิ์เข้าถึง

ข้อสรุปจำกัดอยู่ที่ **ไม่พบ annotation/header ที่ผูก release ได้จากแหล่งที่เกี่ยวข้องซึ่งตรวจแล้ว** ไม่อ้างว่าไม่มีไฟล์อยู่ภายนอกทุกแห่ง และไม่เดา private folder IDs หรือยืม JSON ของ parser อื่นมาใช้

## 2. สายสัมพันธ์ release → local weights: ระบุไฟล์ได้ แต่ยังขาด header

| ระบบ | README Drive ID | Local SHA256 ที่ตรวจไว้ก่อนหน้า |
|---|---|---|
| CPI_R50_CIHP | `1uiqPVZNWIEIKquMNhZ7tv3OTZrc9WGt0` | `e58f8cb4b4fb3b7513e4dd2efb2c8aece07fd237404789204b8b9863f2b7cf35` |
| CPI_ConvNeXtB_CIHP | `117grkZS6Q-v5tbeTLdyENSI0fSRD09lK` | `25b7b12527e550f161b7ad538bd9300a74a0ae73c59a2dfb392ad22161a318c5` |

URL เหล่านี้ตรงกับ [prior verified download manifest](../../Human_Parsing_CCIHP_10_Image_Pilot/provenance/CHECKPOINT_MANIFEST_FINAL.json) ซึ่งบันทึก destination/actual bytes/hash [Release linkage record](../provenance/RUN_MANIFESTS/cpi-channel-order-source-investigation-20261016T043120768600Z/RELEASE_LINKAGE.json) ใช้ hash ระบุ binary ที่กำลังพิจารณา **ไม่กำหนดว่าผู้สร้างต้องเผยแพร่ hash นี้เอง** และไม่ได้ rehash/load weights ซ้ำรอบนี้

Pinned source commit หมายถึง source ที่ใช้ review/runtime ของเรา ไม่ใช่หลักฐานว่าผู้สร้าง train ด้วย commit นั้นจริง ประวัติ training revision/annotation conversion ต้องยืนยันจาก release evidence ถ้าจะอ้าง ส่วนชื่อ CIHP/epoch75 กับ checkpoint load ผ่านยังไม่ให้ ordered semantic names โดยตัวมันเอง

## 3. Loader → training targets → decoder: ตรวจ source เฉพาะสายนี้แล้ว

| ขั้น | สิ่งที่ตรวจได้จาก pinned code | สิ่งที่ยังพิสูจน์ไม่ได้ |
|---|---|---|
| Dataset metadata | `CIHP` dataset อ่าน `categories[].parsing` จาก annotation JSON | ยังไม่มี header ที่เป็นของ release นี้ จึงยังไม่ทราบ ordered names โดยตรง |
| Parsing PNG load | `LoadAnnotations._load_parsing` อ่าน PNG แบบ unchanged และเก็บ uint8 | ไม่ทราบว่า preparation ภายนอกกำหนดเลขใน PNG เป็นชื่อใดโดย release evidence |
| Presence targets | `LoadParseAnnotations` วน numeric IDs 1..19; vector ตัด BG entry ออก | การตัด vector ไม่ใช่การลดเลข raw mask และไม่ได้ตั้งชื่อ class |
| Training mask targets | `loss_causal_forward` สร้าง masks ด้วย `parsing==class_id` ตาม 0..19 | Numeric ID order ยังไม่ใช่ semantic-name proof |
| Background/foreground outputs | Causal head นำ `inst_preds` ไว้หน้า foreground branches; loss target0 ใช้ raw class 0 | ชื่อของ channels 1..19 ยังต้องมาจาก dataset/release mapping |
| Decode/export | นำ background weight ไว้หน้า, weight logits ตาม channels, resize เชิงพื้นที่ แล้ว `argmax(dim=1)` บันทึก numeric-label PNG | ไม่พบขั้นตั้งชื่อ/remap semantic จากภายนอกในสายนี้; argmax ไม่บอกชื่อ class |
| Evaluation labels | `utils/eval.py:get_parsing` อ่านชื่อจาก JSON และพิมพ์ชื่อ index i คู่ IoU index i | การที่ชื่อถูกอ่านมาพิมพ์ไม่ยืนยันว่าตัว JSON นั้นตรงกับ training conversion ของ weights |
| Two model configs | สอง CIHP variants inherit shared CIHP/base และใช้ `CausalParserHead` เดียวกัน | Shared architecture/config ไม่พิสูจน์ว่าใช้ annotation release/order เดียวกันโดยอัตโนมัติ |

[Source trace พร้อม file hashes/line references](../provenance/RUN_MANIFESTS/cpi-channel-order-source-investigation-20261016T043120768600Z/SOURCE_TRACE.json) และ [source excerpts](../provenance/RUN_MANIFESTS/cpi-channel-order-source-investigation-20261016T043120768600Z/SOURCE_EXCERPTS.txt) เก็บสิ่งที่อ่าน ไม่มีการแก้ upstream code หรือรัน training/inference

การตรวจนี้สนับสนุนว่า **numeric IDs ถูกใช้ตาม training targets และส่งออกเป็น channel index โดยไม่มีขั้น name-based relabel ในสายที่ตรวจ** แต่ยังต่อข้ามช่องว่าง `release annotation semantics → numeric IDs` ไม่ได้ การใช้ flip pairs 14↔15 / 16↔17 / 18↔19 ก็ไม่ใช่หลักฐานรายชื่อครบ 20 classes

ชื่อที่ pilot เคยแสดงอาศัย standard CIHP catalog ของอีก implementation จึงยังเป็น indirect labeling evidence ไม่เปลี่ยนสถานะเป็น direct proof จากการตรวจ source ครั้งนี้

## 4. Blocker ที่ปลดได้ด้วยหลักฐานเฉพาะชิ้น

**ขาด:** ordered class-name→numeric-ID evidence ที่มีที่มาและความสัมพันธ์กับ CPI CIHP R50/ConvNeXt-B released checkpoints

รับหลักฐานอย่างใดอย่างหนึ่ง:

1. Header `categories[].parsing` ของ `data/CIHP/annotations/CIHP_train.json` และ `CIHP_val.json` ที่เกี่ยวข้อง พร้อม source/release หรือ preparation instructions ที่แสดงว่า conversion นี้ใช้กับสอง weights ดังกล่าว หรือ
2. คำยืนยันจากผู้สร้างที่ระบุ ordered output labels รวม background 0 และบอกชัดว่าใช้กับสอง CIHP checkpoints ที่ README links ข้างต้น พร้อมความสัมพันธ์กับ training annotation conversion

หนึ่ง shared header ใช้ครอบคลุมสอง checkpoints ได้ **เมื่อ** มีหลักฐานว่าทั้งคู่ใช้ order/conversion เดียวกัน ไม่ใช่เพียงตั้งชื่อไฟล์ว่า CIHP การเผยแพร่ publisher SHA256 ไม่ใช่เงื่อนไข; เราผูกข้อความ/ไฟล์กับ local binary hashes ที่มีอยู่ได้ ไม่ต้องขอ dataset ภาพทั้งหมด

ส่วนที่ยังไม่สมควรทำ: ส่งข้อความหาผู้สร้างโดยไม่ได้รับอนุญาต, เปลี่ยน gate ให้รับ catalog ของอีก model, เพิ่ม tests เพื่อชดเชย missingevidence, reconstruct GT3 ภาพซ้ำ, หรือทำ accepted parser contexts โดยอนุมานว่า head20 แปลว่า standardorder แน่นอน

**การตัดสินใจรอบนี้: พัก semantic acceptance ของคู่นี้ไว้ที่ INDIRECT_ONLY / BLOCKED_CHANNEL_ORDER** ไม่วนขอรับรองห้านโยบาย ไม่เปิด audit ใหม่ และไม่มี automated contact

## 5. Readiness หลังได้ header: ยังมีงานที่ต้องตรวจ

| ขั้น | สถานะตอนนี้ | หลังได้หลักฐาน |
|---|---|---|
| Five policies | ACCEPTED | ไม่ต้องรับรองซ้ำ |
| Channel semantics / checkpoint binding | BLOCKED | ตรวจ provenance/order/release relationship ก่อน semantic acceptance |
| Bounded TRAIN GT reconstruction | PASS ตามหลักฐานเดิม 3 ภาพ | Reuse เมื่อ dependencies ไม่เปลี่ยน; ไม่ใช้แทน population ทั้งชุด |
| Accepted contexts ของ main/reference population | NOT_MATERIALIZED | สร้างตาม manifests/policy และตรวจ GT reconstruction/bindings ของประชากรจริง |
| Actual execution route ของกลุ่มแรก | CURRENT ENTRY POINT = DRY_RUN_ONLY | เชื่อมและตรวจ execute path ที่จะใช้จริง อาจใช้ runner เดิม ไม่จำเป็นต้องสร้าง runner ใหม่ |
| Full benchmark | NOT_AUTHORIZED | ต้องผ่าน readiness แล้วขออนุมัติแยก |

ได้ header เพียงอย่างเดียวจึงยังไม่เป็น benchmark-ready การตรวจทาง execute และ population contexts ต้องนับใน readiness ด้วย Historical smokes ไม่ทำให้ entry point ปัจจุบันมี execution mode อัตโนมัติ

งาน checkpoint acquisition ที่ได้รับอนุญาตอาจเดินแยกได้ แต่รอบนี้ไม่มี checkpoint downloads เพิ่ม และไม่ได้เปลี่ยนสิทธิ์ของ candidate อื่น

## 6. สิ่งที่เปลี่ยนในรอบนี้

เพิ่มรายงานและ evidence เฉพาะ source investigation แล้วอัปเดต navigation/state ไม่มีการเปลี่ยน [V7](../configs/application_v2_first_cohort_v7.yaml), accepted decisions, numeric mappings, evaluator/runner code หรือ direct-channel gate manifest เดิม ผล tests 190 รายการเป็นหลักฐานของรอบก่อน ไม่ได้รันซ้ำและไม่ถูกอ้างว่าปิด blocker นี้

ไม่มี inference, benchmark, GT modification, dataset extraction, training, hybrid, color, CCTV หรือ PPSS activity ไม่มี remote Git actions หรือข้อความส่งหาบุคคลอื่น
