# Stage 0E — CCIHP / CIHP Native GT Compatibility Audit

**Stage 0E person-GT verification: BLOCKED. Decision C — NATIVE_CIHP_REQUIRED สำหรับ assets ที่มีอยู่ตอนนี้** ตรวจ source ตามที่ผู้ใช้ยืนยันจริง ไม่เริ่ม Stage 0 ใหม่ ไม่ download CIHP/CCIHP และไม่รัน parsing/attribute benchmark

## 1. ไฟล์จริงและความหมายของชื่อ dataset

ผู้ใช้ระบุ `datasets/cihp-DatasetNinja.tar` ว่าเป็น CCIHP แต่การอ่าน payload จริงยืนยันเป็น **CIHP DatasetNinja/Supervisely conversion** ไม่ใช่ CCIHP annotation release:

- Archive README ระบุ CIHP: Crowd Instance-level Human Parsing; LICENSE ระบุ CIHP/MIT
- `meta.json` มี **19 foreground labels** รวม `dress` และ `sunglasses`; ไม่มี Face Mask, Bag, Others
- Annotation เป็น per-image JSON + part bitmaps มี `classTitle`, object ID, bitmap origin; tags ว่าง ไม่มี person association
- Inventory เดิมครบ 76,563 regular members ไม่มี Category_ids/Human_ids/Instance_ids/Color_ids/Pattern_ids/Size_ids; **การไม่มี directories เพียงอย่างเดียวไม่ใช่ข้อพิสูจน์** แต่ metadata/schema/whole-JSON audit เดิมก็ไม่มี human grouping

ไม่พบ `datasets/CCIHP_icip.zip` หรือ CCIHP extracted source ใน workspace ที่ค้น รวม 620 directories ใน discovery แรก ค้นชื่อโดยไม่ลง environments/generated outputs/PPSS; ไม่อ้างว่าไฟล์บน Windows มีอยู่บน server [Actual payload identity](../provenance/RUN_MANIFESTS/stage0e-ccihp-cihp-20261012T043947Z/ARCHIVE_IDENTITY.json)

| รายการ | CCIHP ที่ร้องขอ | TAR ที่มีจริง |
|---|---|---|
| Local availability | MISSING | PASS |
| Size | NOT_AVAILABLE | 2,015,375,360 bytes |
| SHA256 | NOT_AVAILABLE | `085d2b694a8c4e0081292a905972e1f31af9d454c12698427b187c7af67a2793` **historical verified SHA** |
| ZIP central directory/CRC/safe paths | NOT_TESTED — source absent | ZIP checks ไม่ใช้กับ plain TAR; reuse verified TAR inventory |
| Train/Val/Test counts | Local counts NOT_TESTED | 28,280 / 5,000 / 5,000 |
| Person ground truth | NOT_TESTED | MISSING_NATIVE_HUMAN_OWNERSHIP_INFORMATION |

ไม่ rehash TAR ขนาด 2 GB ซ้ำ ใช้ inventory/annotation-summary cryptographic hashes เดิมที่ตรวจตรง และ reread 13 selected members **322,301 bytes** ทุก payload ตรง SHA256 เดิม ขอบเขตนี้ไม่อ้างว่า revalidated ทุก payload รอบใหม่

## 2. Native CIHP reference recheck ที่รันจริง

ตรวจ TRAIN demo IDs 0002190, 0005008, 0012008, 0026375, 0032190 จาก TAR เทียบ pinned official PGN RGB/semantic fixtures ที่ยังอยู่จริง RGB decode/pixels/bytes และ original-grid semantic maps ตรงกันทุกภาพ **semantic mismatch = 0 pixels; foreground/background mismatch = 0 pixels**

นี่คือ native **semantic-only reference** 5 ตัวอย่าง ไม่ใช่ full-release equivalence และไม่มี native Human_ids/part-instance reference ให้เทียบ อนุญาตให้ตรวจ validation counts จากหลักฐานเดิมได้ แต่ไม่มี validation model inference/tuning

[Bounded evidence](../provenance/RUN_MANIFESTS/stage0e-ccihp-cihp-20261012T043947Z/CIHP_BOUNDED_REFERENCE_RECHECK.json), [prior full preflight](CIHP_ARCHIVE_PREFLIGHT_AUDIT.md), [person verification](CCIHP_PERSON_INSTANCE_VERIFICATION.md)

## 3. CCIHP semantics ไม่ใช่ CIHP เดิม

**Verified published facts:** CCIHP paper §2 ระบุแก้ human masks และ semantic definitions, แยก Dress เข้า UpperClothes/Skirt, เพิ่ม facial-mask category, ขยาย hair/eyewear/neck clothing; human masks รวม accessories เพิ่ม จำนวนคนใน publication ต่างจาก CIHP +121 [Original paper](https://arxiv.org/html/2201.09594v1#S2)

Author card แยก Human_ids=person instances และ Instance_ids=attribute instances; ส่วน Category_ids เป็น semantic attributes **ต้องตรวจ masks/code ก่อนถือว่าเท่ากับ native CIHP part-instance encoding** [Author dataset documentation](https://www.kaggle.com/datasets/angeliqueloesch/ccihp-characterized-crowd-instancelevel-hp)

เอกสารมี version/count discrepancy: paper กล่าวถึง 19 foreground semantic classes; author card ระบุ 20 แต่ list เรียงถึง 21 พร้อม Bag/Others จึงเก็บเป็น **UNRESOLVED_RELEASE_TAXONOMY_VERSION** ไม่ใช้ค่า documentation เป็น local class inventory ไม่ผูก documentation ordinal เป็น PNG class ID ที่ตรวจแล้ว

[Class-by-class draft matrix](../taxonomy/CCIHP_CIHP_COMPATIBILITY_DRAFT.csv) แยก published incompatibilities กับ NOT_VERIFIED local equivalence ไม่มี EXACT/VERIFIED_EQUIVALENT ที่อ้างว่า CCIHP pixel-level ผ่านแล้ว ไม่ freeze mapping

## 4. GT recovery: native และ custom แยกกัน

Native CIHP benchmark: **BLOCKED** เพราะ Human GT ไม่มี และยังไม่มี independent original human-ID equivalence evidence การต่อ semantic CIHP กับ human maps ที่ถูกเปลี่ยนใน CCIHPจะเป็น mixed-source GT จนกว่าจะพิสูจน์ fidelity ห้ามเรียก official native GT

Custom semantic/common-taxonomy track: **CONDITIONAL** — existing CIHP conversion มี semantic parts ที่ใช้เสนอ track แยกได้หลัง quality/permission/common-domain review แต่ไม่ทำให้ person matching/person-macro/APp/coverage-aware instance tracks พร้อม

Custom CCIHP-person track: **NOT_TESTED/BLOCKED** เพราะ CCIHP data ยังไม่มีจริง ถ้าได้ภายหลังต้องทำ same-RGB/coordinate/semantic/person tests ใหม่; document-only taxonomy evidence ไม่แทน masks

## 5. Integrity, quality และ license

Reuse prior full audit: all 38,280 image/JSON pairs, 33,280 labeled images, 768,446 valid converted bitmaps; test JSON ว่าง 5,000 ตาม hidden GT design อย่างไรก็ดี full strict-RGB/physical ownership/near-duplicate quality ยังไม่ผ่าน Full Quality Audit Native demos ไม่เป็น representative quality sampling

Known reuse เดิม: **39 train–val JPEG-byte groups / 39 val IDs**, 83 cross-split groups; no exclusions/split edits ไม่อ่าน pixels ซ้ำทั้งชุดหรืออ้างว่า exact bytes audit ครอบ near duplicates

Reuse Decision 5A scope/license matrix; ไม่ audit parser licenses ใหม่ Author CCIHP card ประกาศ annotation CC-BY-NC-4.0 และ evaluation-code MIT ซึ่งเข้ากับ noncommercial academic scope ตามเงื่อนไข แต่ **ไม่มี local CCIHP LICENSE ให้ตรวจ** และสิทธิ์ CCIHP annotations ไม่โอน original CIHP RGB rights ส่วน TAR provider MIT ไม่ใช่ original RGB/GT owner grant [Prior license assessment](LICENSE_ELIGIBILITY_REASSESSMENT.md), [research scope](../RESEARCH_SCOPE.md)

## 6. ข้อสรุปและ stop gate

เลือก **C — NATIVE_CIHP_REQUIRED สำหรับข้อมูลที่มีปัจจุบัน** ขอ verified original CIHP Human_ids/Category_ids/Instance_ids/splits supplement หรือ native distribution ภายหลัง approval; ไม่จำเป็นต้อง download DatasetNinja TAR เดิมอีก

ถ้าต้องการใช้ CCIHP ใน custom track ต้องโอน actual CCIHP annotations มาแล้ว audit ต่างหาก ชื่อที่เรียก TAR ไม่เพิ่มข้อมูล person GT การโอน CCIHPอย่างเดียวไม่ทำให้ native equivalence อัตโนมัติ [Recovery decision](CIHP_GROUND_TRUTH_RECOVERY_DECISION.md)

Full Quality Audit / ~200 stratified TRAIN human review ยังรอ native-human input และ approval คง CIHP candidate-primary/MHP-v2 provisional-secondary, taxonomy DRAFT, benchmark NOT_STARTED ไม่มี PPSS/CCTV/models/training/color-pattern-size evaluation

## Tests ที่รันใน Stage 0E

Existing converted-part decoder unit tests **9/9 PASS** (bitmap CRC/alpha support, class IDs, invalid compression/origins/grid/empty support). [Test log](../provenance/RUN_MANIFESTS/stage0e-ccihp-cihp-20261012T043947Z/CIHP_DECODER_TESTS_V2.log), [execution record](../provenance/RUN_MANIFESTS/stage0e-ccihp-cihp-20261012T043947Z/CIHP_DECODER_TESTS_V2.json) Initial test launch เคยใช้ base Python จาก resolved venv symlink และ import NumPy ไม่ได้; เก็บ failure logไว้และแก้เฉพาะ interpreter invocation ไม่ install packages

Fresh actual-source checks: 13 member SHA matches, strict pixel loading และ original-grid native semantic parity **5/5**, inspection ของ semantic overlay **3 ภาพ** [Visual inspection](../provenance/RUN_MANIFESTS/stage0e-ccihp-cihp-20261012T043947Z/VISUAL_INSPECTION.json) CCIHP CRC/labels/Human_ids/person matching tests **NOT_TESTED**, ไม่มี model/evaluator benchmark scores
