# CIHP DatasetNinja — Archive Preflight Audit

Run `cihp-archive-preflight-20261008T102552Z`, 2026-10-08. **Container / converted bitmap integrity: PASS. Native human-instance GT readiness: BLOCKED. CIHP primary promotion: NO.** ต่อจาก Stage 0 เดิม ไม่มี model inference หรือ Full Quality Audit

## 1. ไฟล์ที่ตรวจจริง

Workspace-relative path: `datasets/cihp-DatasetNinja.tar` — POSIX TAR แบบไม่บีบอัด ขนาด **2,015,375,360 bytes**

SHA256 ก่อนและหลัง audit ตรงกัน:

```text
085d2b694a8c4e0081292a905972e1f31af9d454c12698427b187c7af67a2793
```

ตรวจครบ **76,573 members**: regular files 76,563 และ directories 10 อ่าน payload ของทุก regular file และสร้าง member SHA256 inventory ตรวจ header checksums, member bounds, duplicate names, unsafe paths/links และ zero-block trailer ผ่าน ไม่มี full extraction หรือเขียนเข้า archive

**ขอบเขต:** TAR ไม่มี payload CRC แบบ ZIP SHA256 เป็น local fingerprint ยังไม่มี publisher checksum ให้เทียบ จึงไม่เท่ากับ verified byte-identical official release ภาพ JPEG ทุกภาพตรวจ header/dimensions; strict full-pixel JPEG decoding ทำเฉพาะ sample **20 ภาพและผ่านทั้งหมด** ยังไม่ใช่ complete RGB decoding audit

## 2. โครงสร้างและจำนวน

```text
meta.json
README.md
LICENSE.md
training/{img/*.jpg,ann/*.jpg.json}
validation/{img/*.jpg,ann/*.jpg.json}
testing/{img/*.jpg,ann/*.jpg.json}
```

| Split | Images | JSON annotations | Bitmap part objects | หมายเหตุ |
|---|---:|---:|---:|---|
| training | 28,280 | 28,280 | 647,072 | มี converted GT |
| validation | 5,000 | 5,000 | 121,374 | มี converted GT |
| testing | 5,000 | 5,000 | 0 | JSON placeholders; hidden test GT ไม่ได้ supplied |
| Total | **38,280** | **38,280** | **768,446** | Part count ไม่ใช่ person count |

ไม่พบ missing/orphan image–JSON pairs หรือ RGB-header/annotation dimension mismatch ทุก split IDs ไม่ซ้ำกันข้าม split และ union ครบ numeric IDs 1…38,280 จำนวน labeled images จริงคือ **33,280** ไม่ใช่ 38,280 ภาพที่มี GT

อ่าน JSON ทุกไฟล์ ตรวจทุก bitmap ทั้ง base64, zlib checksum, PNG chunk CRC, complete decoded pixels, nonempty support, dimensions และ origin bounds ผ่าน **768,446/768,446** พร้อม binary round-trip fidelity checks ไม่พบ malformed bitmap ข้อสรุปนี้เป็น integrity ของ converted artifacts ไม่ใช่ความถูกต้องด้าน semantic/physical-person annotation

## 3. Official split compatibility

จำนวน splits ตรง reference [CIHP paper](https://arxiv.org/html/1808.00157) Validation IDs ตรงครบ **5,000/5,000** กับชื่อ GT metadata `evaluation/Instance_part_val/*.txt` ใน [PGN official repository](https://github.com/Engineering-Course/CIHP_PGN) commit `0cf1cbe54a44fc86abe2023b0e762df3f9605242` ไม่มี extra/missing validation IDs ใน comparison นี้

Full official train/test ID lists ยังไม่ยืนยันจาก independent native release Repository `train_id.txt` และ `val_id.txt` ที่พบมี **5 demo IDs เหมือนกัน** จึงห้ามใช้สองไฟล์นั้นรับรอง official population ทั้งชุด ตัวอย่าง semantic GT ใน demo folder ไม่ใช่หลักฐานว่าภาพเหล่านั้นอยู่ validation; ใน TAR ทั้งห้าอยู่ training

**สถานะ:** counts compatible, validation membership verified against official GT metadata; full native-release train/test split parity ยัง pending

## 4. Taxonomy และ output semantics

`meta.json` มี bitmap classes **19 foreground concepts** ตรง converter mapping ไป native CIHP IDs 1–19: hat, hair, glove, sunglasses, upperclothes, dress, coat, socks, pants, torso_skin, scarf, skirt, face, left/right arm, left/right leg และ left/right shoe Native background 0 เป็น implicit uncovered pixels ของ conversion ไม่ใช่ bitmap class ที่แยกเก็บไว้

Supervisely `classId` เช่น `6462889` เป็น project identifier ไม่ใช่ native semantic ID ต้องแปลจาก verified class title ตาม converter Native ID 10 คือ torso-skin ไม่ใช่ LIP jumpsuit Auxiliary Human=20 ใน parser configs ไม่ใช่ GT class

Bitmap เป็น base64(zlib(PNG)) ที่ใช้ alpha/transparency เป็น support พร้อม `[x,y]` origin ไม่ตีความ RGB สีของ PNG เป็น semantic labels และไม่ใช้ bilinear resampling กับ categorical truth ไม่มี explicit native ignore/void map จึงยังไม่รับรองว่า original void/background fidelity คงเดิมทั่ว release

Native mapping สำหรับอ่าน archive ไม่ใช่ COMMON_HP protocol freeze และยังไม่อนุมัติ score ใด

## 5. ข้อมูล instance GT สูญหายหรือไม่

**Verified facts:** ทุก object มี fields `id,classId,description,geometryType,labelerLogin,createdAt,updatedAt,tags,classTitle,bitmap` ไม่มี person/human/group/parent association field ทั้ง annotation และ object tags ว่างทั้งหมด ไม่พบ `Human_ids`, original native category/person/part PNGs หรือ person-association sidecar ใน TAR

[Converter source](https://github.com/dataset-ninja/cihp/blob/5a2b59d64627665fca7dd72261789e4813c623a8/src/convert.py) อ่าน `Category_ids` และ colored `Instances` เพื่อสร้าง bitmap ต่อหนึ่ง part-color region ตั้ง path `Human_ids` ไว้แต่ไม่มี read/use ใน AST ที่ตรวจ ไม่ export original instance color/ID หรือ part→human relationship `object.id` ที่ export เป็น annotation object identity ไม่ใช่ GT person ID

**Conclusion:** conversion เก็บ semantic/part masks แต่ **ไม่ได้เก็บ native human ownership อย่าง explicit** ยัง reconstruct validated per-human GT จากชุดนี้อย่างเดียวไม่ได้ ห้ามสร้าง Human_ids จาก YOLO/connected components/heuristic clustering แล้วอ้างว่าเป็น original GT

| Future evaluation | Readiness จาก TAR นี้ |
|---|---|
| Global semantic body/clothing mIoU | CONDITIONAL: full native fidelity, quality, ignore policy และ license ยังต้องตรวจ |
| Part-instance analysis / official APr compatibility | CONDITIONAL: original part partition และ official-format parity ยังไม่ครบ |
| GT person crops / oracle-person track | BLOCKED: ไม่มี verified person geometry/identity |
| Person-macro / matched-person / detector coverage | BLOCKED: ขาด per-human GT และ association |
| Native human-instance APp / PCP | BLOCKED: ห้ามสร้าง person parsing planes โดยเดา ownership |

นี่เป็น conversion information gap ไม่ใช่หลักฐานว่า native CIHP annotation ต้นฉบับมี ownership error

## 6. Native reference fidelity และ visual spotcheck

ใช้ official repository fixtures **5 RGB + 5 semantic PNGs รวม 235,490 bytes** เป็น bounded reference-source inspection ไม่ได้ดาวน์โหลด native dataset ทั้งชุด Images `0002190,0005008,0012008,0026375,0032190`: JPEG bytes, decoded RGB, GT dimensions และ reconstructed semantic pixels ตรงทั้งหมด (**0 mismatched pixels ทั้งห้า**)

![Official demo semantic parity: 0005008](../outputs/visualizations/cihp-archive-preflight-20261008T102552Z/cihp_preflight/training_0005008_semantic_diagnostic.png)

**Observation:** `0005008` แสดงหลายคนและ parts ของแต่ละคน; derived semantic map กับ official demo GT ตรงกัน ทั้งภาพมี 53 bitmap objects ซึ่งไม่ได้หมายถึง 53 persons ส่วน `0032190` ที่ดูเพิ่มเป็นสอง visible people กับ semantic labels ของเสื้อผ้า/body regions โดยไม่มี person-group metadata

**Interpretation:** การ decode/coordinate mapping ถูกต้องสำหรับ fixtures เหล่านี้ แต่ global semantic equality ไม่พิสูจน์ person-identity fidelity หรือ correctness ของทุก pixel/ทุกภาพ ไม่มี representative quality-prevalence claim จากห้า demo examples

Converter ยังมี special handling ของ image `0035374`, row 158 / col 314 เมื่อ sampled native category เป็น 0 ให้ใช้ 10 ใน class-selection loop และเลือก class จาก sampled category ของแต่ละ part region ไม่ได้ตรวจ category uniformity ของทุก pixel ใน region Source นี้จึงไม่รองรับ universal lossless claim ต้องเทียบ native GT จริง โดยเฉพาะ special case ห้ามอ้างว่าเราแก้ source GT

## 7. Duplication findings — ยังไม่ใช่ full leakage audit

All-member SHA256 inventory พบ **224 exact JPEG-byte duplicate groups**: training-only 137, validation-only 1, testing-only 3; training–validation **39**, training–testing 38, validation–testing 6 รวม cross-split **83 groups** มี validation **39 IDs** ที่ JPEG bytes เหมือน train

Original splits ไม่เปลี่ยนและไม่มี exclusions ใหม่ ตัวเลขเหล่านี้เป็น **exact file bytes** เท่านั้น ยังไม่ตรวจ all decoded-RGB/near duplicates หรือ external training exposure จึงห้ามเปรียบเทียบ 39 กับ MHP-v2 652 เป็น equivalent leakage rates เพราะ audit methods/coverage ต่างกัน

## 8. Provenance และ licensing

Archive metadata/README, taxonomy, counts และรูปตัวอย่างสอดคล้องกับ [DatasetNinja CIHP](https://github.com/dataset-ninja/cihp) ตรวจ source reference ที่ commit `5a2b59d64627665fca7dd72261789e4813c623a8` แต่ actual export build commit และ original-native-archive hashes ไม่ embedded จึงยังไม่ verified full build provenance

Source มี local folder literal เริ่ม `CCIHP_icip` แต่เพียงชื่อ path ไม่พิสูจน์ว่าเป็น color dataset ข้อมูลที่ตรวจมี CIHP 19-class taxonomy, 38,280 IDs และ official-val metadata match ไม่มีการตรวจ CCIHP assets หรือเริ่ม color study

Archive `LICENSE.md` **declares MIT**; provider repository ขยายลิงก์ source ไป PGN ซึ่ง license ระบุ software/documentation grant ไม่ได้ยืนยัน RGB/GT dataset rights โดยเฉพาะ การกล่าวอ้าง MIT ของ provider ถูกบันทึกไว้ แต่ authoritative original dataset research/publication/deployment permission ยังต้องยืนยัน ไม่ถือ public TAR เป็นสิทธิ์เชิงพาณิชย์โดยอัตโนมัติ

## 9. Recommended next gate

แนะนำหา **original native CIHP GT โดยเฉพาะ Human_ids พร้อม Category_ids/Instance_ids และ full split lists** จาก local copy หรือ official release มาเสริมก่อน human-instance Full Quality Audit ไม่ต้องลบหรือแตก DatasetNinja TAR ทับอะไร ถ้าต้อง download native release ต้องขออนุมัติแยกก่อน

เมื่อครบแล้ว: strict-decode ทุก RGB, native per-human fidelity, exhaustive paired-map/ID validation, decoded/near-duplicate leakage audit, class/person statistics และ 200-image stratified TRAIN human review พร้อม checklist/ambiguity adjudication แยกจาก model evaluation และไม่ tune บน validation

Semantic-only quality audit ของ conversion อาจทำเป็น cohort แยกหลังอนุมัติ แต่ไม่แก้ human-instance gate และไม่ทำให้ CIHP เป็น primary โดยอัตโนมัติ

## Evidence และ tests

- [Archive manifest](../manifests/CIHP_DATASETNINJA_ARCHIVE_MANIFEST_V1.json)
- [Machine-readable preflight](../provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json)
- [Member SHA256 inventory](../provenance/RUN_MANIFESTS/cihp-archive-preflight-20261008T102552Z/TAR_MEMBER_SHA256.jsonl)
- [Byte duplicate groups / IDs](../provenance/CIHP_DATASETNINJA_BYTE_DUPLICATES_V1.json)
- [Converter AST audit](../provenance/RUN_MANIFESTS/cihp-archive-preflight-20261008T102552Z/CONVERTER_STATIC_AUDIT.json)
- [Supplement](../provenance/RUN_MANIFESTS/cihp-archive-preflight-20261008T102552Z/CONVERSION_SUPPLEMENT.json)
- [60 executed tests](../provenance/RUN_MANIFESTS/cihp-archive-preflight-20261008T102552Z/BOUNDED_TESTS.json): 9 new bitmap/coordinates/ownership/ambiguity fixtures + 51 existing tests; PASS, no model or validation inference

**STOP — Native person-GT readiness BLOCKED; no full benchmark, checkpoint download, training, fusion, color analysis or primary promotion.**
