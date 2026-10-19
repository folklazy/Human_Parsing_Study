# CPI — รับรอง standard CIHP mapping ตามนโยบายหลักฐานใหม่ และตรวจ saved TRAIN route

**สถานะ: ACCEPTED_WITH_INDIRECT_EVIDENCE · TRAIN preparation ผ่าน · ยังไม่ freeze / full benchmark**

รับคำตัดสินล่าสุดของผู้ใช้: คง CPI สอง checkpoints ใช้ standard CIHP order ที่ประกาศไว้ ประกอบหลักฐาน paper/repository → released weights/config → numeric processing → bounded TRAIN behavioral check ไม่บังคับรอ original annotation header/คำตอบผู้สร้าง และไม่ตั้งเงื่อนไขว่าต้องทำนายถูกครบทุกคลาส

## 1. สิ่งที่รับรองและสิ่งที่ยังไม่อ้าง

| เรื่อง | สถานะ |
|---|---|
| CPI_R50_CIHP / CPI_ConvNeXtB_CIHP native mapping | ACCEPTED_WITH_INDIRECT_EVIDENCE |
| Original training header / creator confirmation | ยังไม่มี; ไม่เรียก DIRECT_VERIFIED |
| Fixed six-target projection / released-annotation-relative domain / population roles / matching / quality-only | คงห้านโยบายที่รับรองไว้ ไม่เปิดรับรองซ้ำ |
| Numeric mappings และ GT projection | เหมือนเดิมทุกค่า; แยก CIHP6 Dress จาก CCIHP6 Face Mask |
| Runtime thresholds | คง R50 0.01 / ConvNeXt-B 0.05 ไม่ปรับตาม embedded snapshot หรือผลภาพ |
| Full benchmark / final validation inference | ยังไม่อนุญาตและไม่ได้เริ่ม |

[Config V8](../configs/application_v2_first_cohort_v8.yaml) ผูกกับ [decision V7](../provenance/APPLICATION_V2_DECISIONS_V7.json) และ [mapping V3](../taxonomy/APPLICATION_BODY_CLOTHING_CPI_ACCEPTED_V3.json) ขอบเขตการรับรอง mapping คือสอง CPI CIHP checkpoints เท่านั้น การคง LIP projection ใน bundle ไม่ใช่การรับรอง LIP เข้ากลุ่มนี้

[Source-to-target review V2](../taxonomy/FIRST_COHORT_CPI_SOURCE_TO_TARGET_ACCEPTED_V2.csv) อัปเดตสถานะการรับรองโดยไม่เปลี่ยน source IDs/targets ส่วน V1 ที่อ้างใน historical evidence snapshot ยังคงเดิม สถานะปัจจุบันอ้าง decision/config/evidence manifest ฉบับใหม่

Gate ใหม่ตรวจ evidence components ทั้งห้ากลุ่มและ hashes รวม checkpoint/source/native-order bindings ไม่ใช่รับเพียง status string เส้นทาง direct verification เดิมยังแยกไว้ และ historical V7 ยังคงไม่รับ indirect evidence ตามนโยบายเดิม

[Evidence manifest](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/CHANNEL_ORDER_EVIDENCE_V2.json) · [Paper/repository reassessment](CPI_PAPER_REPOSITORY_TAXONOMY_REASSESSMENT_TH_20261016.md)

## 2. ตรวจ saved TRAIN overlays หนึ่งรอบ

ใช้สาม IDs เดิมที่กำหนดไว้แล้ว ไม่ค้นภาพที่โมเดลทำคะแนนดี ไม่รันโมเดลเพิ่ม และไม่ reconstruct GT จาก ZIP ซ้ำ ใช้ cached GT ที่มี source-hash/round-trip evidence เดิมพร้อมตรวจ cache hashes แสดง full frame บนกริดเดิมทุก panel

### TRAIN 0021834 — Face / torso / garments

![Saved TRAIN 0021834 channel review](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/saved_train_review_v2/0021834_saved_channels.png)

**Observation:** ทั้งสองรุ่นวาง ID13 บริเวณใบหน้า, ID10 บริเวณผิวคอ/อก, ID2 บนผม, ID7 บนสูท และ ID5 บนเสื้อเชิ้ต มีความต่างของขอบ mask ตามปกติ

**Interpretation:** สอดคล้องกับ standard CIHP interpretation ในส่วนที่เห็น ไม่ใช่หลักฐานว่า masks เท่ากันหรือทำนายถูกทุกพิกเซล

### TRAIN 0000930 — แยก CIHP Dress จาก CCIHP Face Mask

![Saved TRAIN 0000930 channel review](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/saved_train_review_v2/0000930_saved_channels.png)

**Observation:** CPI ใช้ ID6 บนชุดยาว, ID13 บริเวณหน้ากากใบหน้า, ID1 บนหมวก และ ID3 บนถุงมือ ส่วน CCIHP GT ใช้ ID6 บน face mask และแยกเสื้อ/กระโปรงเป็นคนละ ID บางบริเวณกระเป๋า/เสื้อผ้ามี prediction ที่ไม่ละเอียด

**Interpretation:** ภาพนี้ช่วยตรวจว่าห้ามเทียบ GT/prediction ด้วยเลขเดียวกันตรง ๆ การที่ taxonomy ต่างกันตรง ID6 เป็นสิ่งที่ projection ต้องจัดการ ไม่ใช่เหตุสรุปว่า CPI สลับ channels

### TRAIN 0001368 — Torso / arms และรายละเอียด background

![Saved TRAIN 0001368 channel review](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/saved_train_review_v2/0001368_saved_channels.png)

**Observation:** ID10 อยู่บนหน้าท้องที่เปิดเผย, ID13 บนใบหน้า, IDs14/15 อยู่บนแขน/มือที่เห็น และ ID5 บนเสื้อท่อนบน พื้นที่เสื้อผ้าของคนด้านหลังและขอบ mask มีความต่างจาก GT

**Interpretation:** ไม่พบลักษณะที่ชี้ว่าทั้งระบบสลับ channel เป็นอีกกลุ่มความหมาย แต่ความผิดพลาดด้าน segmentation/classification ยังเป็นสิ่งที่ benchmark ภายหลังต้องวัด ไม่ใช้ความผิดพลาดรายพิกเซลเป็นเงื่อนไขตัดโมเดลใน sanity check นี้

**ขอบเขต:** ตรวจโดย assistant เพื่อ sanity check ไม่ใช่ independent human annotation-quality review ภาพชุดนี้ไม่ครอบคลุม exposed legs/footwear จึงไม่อ้าง visual certification ของกลุ่มเหล่านั้น และไม่ตั้งให้ต้องหา prediction ที่ถูกครบทุกคลาสเพื่อผ่าน การรวม overlapping masks ตาม score ใช้แสดงภาพเท่านั้น; native planes ต้นฉบับยังอยู่ครบ

[Observations / limitations / image hashes](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/TRAIN_BEHAVIORAL_REVIEW.json)

## 3. Contexts: ปิดได้เฉพาะขอบเขต TRAIN ที่ตรวจแล้ว

สร้าง **6 accepted contexts = 2 systems × 3 TRAIN images** ผูก checkpoint/config/native order/target support/input/domain recipe รายภาพกับนโยบายใหม่ มี G_loc/G_sem รวม **7/7 ต่อระบบ** จาก GT เดิม เมื่อเป็นภาพเดียวกัน bindings ฝั่ง input/GT ตรงกันข้ามระบบ ส่วน checkpoint ของสองระบบและ dimensions/GT counts ของคนละภาพแตกต่างได้ตามจริง

Context มี confidence `ACCEPTED_WITH_INDIRECT_EVIDENCE` แยกจาก structural/hash binding ที่ตรวจแล้ว ไม่ใช้คำว่า VERIFIED ทางเทคนิคเพื่อกลบข้อจำกัดเรื่อง original header

ต่อจาก TRAIN ได้ materialize และตรวจ schema ของ **validation context packages ครบประชากร** โดยอ่าน GT/domain แบบ read-only ใช้ numeric projection/policy เดิมก่อนดู predictions ไม่ใช้ validation เลือก mapping หรือ thresholds:

| Population | Images | System-image bindings | G_loc ต่อระบบ | G_sem ต่อระบบ |
|---|---:|---:|---:|---:|
| Main overlap-controlled | 4,961 | 9,922 | 17,434 | 17,390 |
| Source reference | 5,000 | 10,000 | 17,548 | 17,504 |

ตรวจ hashes ของ annotation members 15,000 ไฟล์ สร้าง GT/domain และ per-person fingerprints ครบ 17,548 native persons แล้วค่ารายภาพ/ผลรวมตรง manifests เดิมทั้งสอง populations ตรวจ registry ของสองระบบแยก input/model/domain bindings ผ่าน กริด GT เป็น identity transform ไม่มี categorical interpolation

RGB hashes/dimensions/strict decode ใช้ผล full audit เดิม ไม่ decode RGB ทั้งชุดซ้ำ และต้องตรวจ loaded RGB bytes เทียบ binding อีกครั้งก่อน inference ภายหลัง เก็บ source-reference bindings 5,000 ภาพร่วมกับ model templates และ main-membership flag เพื่อไม่ทำสำเนา contexts ซ้ำ 99% ของข้อมูล

**สถานะ packages: MATERIALIZED_AND_STRUCTURALLY_VALIDATED_NOT_ACTIVATED** ยังไม่ผูกเข้า execution/scoring config ของ validation; active V8 ยังมีเพียง 6 TRAIN contexts และ scoring disabled จึงไม่อ้างว่าประชากร validation พร้อมเริ่ม benchmark โดยอัตโนมัติ ไม่มี predictions หรือ model scores ถูกอ่าน/คำนวณในขั้น materialization นี้

[Full validation binding manifest](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/validation_contexts_v1/MANIFEST.json) · [GT-only build log](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/VALIDATION_CONTEXTS_BUILD.log)

[TRAIN context registry](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/TRAIN_CONTEXTS.json) · [Acceptance record](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/ACCEPTANCE.json)

## 4. Execute path: saved TRAIN replay ผ่าน ไม่ใช่ fresh joint inference

ต่อ entry point เดิมเข้ากับ `ConfiguredRunner.native_frame`, prediction-only `associate_native` และ immutable packet export โดยให้ **V8 เป็นแหล่ง roster/settings จริง** ไม่เรียกสคริปต์ smoke ทุก family หรือใช้ YOLO/FASHN legacy roster แทน

รัน `--saved-train-replay` ผ่านครบ **6 system-image jobs** เก็บ native IDs ครบแม้ T3b จะเลือก final outputs เพียงบางส่วน รวม native ID และ YOLO opportunity ID ในแต่ละ final person ใช้ native parser box เป็น evaluation box และเก็บ YOLO conditioning box แยก ไม่มี GT เป็น input ของ association

ตัวอย่างที่ชี้ความต่างของ counters: TRAIN0001368 มี native instances R50=8 / ConvNeXt-B=3 แต่ YOLO opportunities=2 และ final associated persons=2 ทั้งสองรุ่น จำนวน final เท่ากันไม่ได้แปลว่า native outputs หรือ quality เท่ากัน และจำนวน native instances ไม่ใช่จำนวน physical persons ที่รับรองว่าถูกต้อง

ไม่มี torch/ultralytics/mmcv/mmdet imports ไม่มี model loading/inference และไม่มี semantic scores ตารางอันดับหรือ timing benchmark ค่า CPU cache-read/lifecycle time ใน replay ไม่ใช่ parser latency ผล smoke/model feasibility เดิมยังเก็บเป็นหลักฐานคนละส่วน

[Final replay evidence](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/saved_replay_final/REPLAY.json) · [Execution record](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/SAVED_REPLAY_EXECUTION.json)

## 5. การตรวจโค้ดและข้อจำกัดที่เหลือ

Application CPU regression **131 tests ผ่าน** รวม 8 tests เฉพาะ revision นี้ ตรวจ confidence-policy opt-in, ป้องกันการเลื่อน indirect เป็น direct, evidence hashes/bindings, numeric projection ที่ไม่เปลี่ยน และ scoring/full-benchmark gate ที่ยังปิด ผล tests รองรับพฤติกรรมโค้ด ไม่ได้พิสูจน์ชื่อ channel ทางประวัติศาสตร์หรือเพิ่มความแม่นของโมเดล

[Test log](../provenance/RUN_MANIFESTS/cpi-evidence-policy-acceptance-20261016T070730261321Z/CPU_TESTS_FINAL.log)

งานถัดไปคือผูก validation context packages ที่ตรวจแล้วเข้า versioned execution config/decision และตรวจ fresh execute route ที่จะใช้จริงก่อน readiness review การได้ saved replay PASS ไม่เท่ากับ fresh GPU joint pipeline ผ่าน ไม่จำเป็นต้องค้น header ซ้ำหรือรัน smoke ทั้ง roster ใหม่ Full benchmark ต้องได้รับอนุมัติแยก

ไม่มี dataset/GT/PPSS/YOLO/weights/environment changes, downloads/installs, training, fusion, CCTV หรือ remote Git actions ในรอบนี้ Config V7/decision V6/mapping V2 และ historical run records คงไว้ตามเดิม
