# Stage 0E — Person Instance Verification

**Human_ids validation: BLOCKED / NOT_TESTED** Actual archive=`datasets/cihp-DatasetNinja.tar` เป็น CIHP conversion ไม่ใช่ CCIHP release ไม่มี source Human_ids, person-to-part metadata หรือ original human reference masks

| Requirement | ผล actual source | สิ่งที่ยังยืนยันไม่ได้ |
|---|---|---|
| หนึ่ง Human ID = หนึ่ง physical person | NOT_TESTED — Human_ids absent | Ownership, number/order/person support |
| Visible-person completeness | NOT_TESTED | Unannotated background people vs original policy |
| Semantic/human spatial relation | Semantic demo dimensions PASS; human relation unavailable | Exact person assignment / mixed-source differences |
| Multi-person ownership | BLOCKED | Part object IDs เป็น object IDs ไม่ใช่ person IDs |
| Ignore/overlap/occlusion conventions | Converted background implicit; native-human policy unresolved | ไม่ตีความ 255 เป็น ignore หรือ overlap เป็น error โดยไม่มี source definition |
| GT matching/person-macro | BLOCKED | Foreground union/connected components/YOLO แทน native GT ไม่ได้ |
| Within-image identity consistency | NOT_TESTED | Person namespaces/counts ไม่ปรากฏใน JSON |

Whole-archive schema audit เดิมพบ object/image tags ว่างและไม่มี ownership fields; fresh payload reads ยืนยันตัวอย่างเดียวกันอีกครั้ง ไม่มี person masks ถูกสร้างด้วย heuristics Person denominator จึง **null/unknown** ไม่ใช้ 768,446 part objects เป็นจำนวนคน

## ภาพที่ตรวจจริง: semantic alignment เท่านั้น

ภาพต่อไปนี้ใช้ RGB เดิม, pinned official PGN semantic demo และ DatasetNinja reconstruction; categorical arrays ไม่ resize สำหรับ metric parity ภาพแสดงผล resize หลังทำ overlay เท่านั้น ไม่เปลี่ยน GT ไม่มี CCIHP/human-mask panel สมมติ

### 0002190 — คนใกล้กันในภาพเดียว

![CIHP semantic comparison](../outputs/visualizations/stage0e-ccihp-cihp-20261012T043947Z/cihp_0002190_semantic_reference.png)

Observation: มองเห็นคนสองคนใกล้กันและ semantic regions ทั้งสองฝั่งตรงกัน ตัวเลข parity คือ 0 differing pixels

Interpretation: semantic correctness ไม่แสดงว่า hair/upperclothes pixels แต่ละส่วนผูกกับคนใด ห้ามใช้ shared class color เป็น human ID หรือเชื่อม ownership จาก connectivity

### 0005008 — กลุ่มคนหลายคนและหลาย part objects

![CIHP crowded semantic comparison](../outputs/visualizations/stage0e-ccihp-cihp-20261012T043947Z/cihp_0005008_semantic_reference.png)

Observation: คนหลายคนเรียงใกล้กันและมีขอบเขตเสื้อ/ส่วนร่างกายหลายส่วน JSON มี **53 part objects**; official/DatasetNinja semantic regions ตรงกันทุก pixel

Interpretation: part-object count ไม่ใช่ person count ภาพนี้ไม่พิสูจน์ visible-person completeness หรือ native ownership จึงไม่สร้าง person IDs จากการมองภาพ/สี overlay

### 0012008 — คนอยู่ใกล้กันและมีวัตถุร่วมในฉาก

![CIHP nearby people semantic comparison](../outputs/visualizations/stage0e-ccihp-cihp-20261012T043947Z/cihp_0012008_semantic_reference.png)

Observation: มีคน foreground หลายคนและร่มในภาพ ส่วนร่างกาย/เสื้อผ้าหลายบริเวณอยู่ชิดกัน; semantic parity ผ่านที่ original grid

Interpretation: shared semantic labels ไม่พอแยก ownership และ native human-mask support ของ accessories ต้องตรวจ source จริง ไม่เดาจาก parsing foreground union

## ขอบเขตหลักฐาน

Inspect ภาพทั้งสามจริงและทำ numeric parity รวม 5 train demos ไม่มี human-instance visual verification หรือ error-prevalence estimate CCIHP paper กล่าวถึง modified human masks เป็น warning เชิง compatibility ไม่ใช่ผล local masks ที่ตรวจแล้ว Source absent ห้ามแปลเป็น corruption ของ CCIHP

[Main audit](CCIHP_CIHP_COMPATIBILITY_AUDIT.md), [machine evidence](../provenance/CCIHP_ARCHIVE_AUDIT.json), [decision](CIHP_GROUND_TRUTH_RECOVERY_DECISION.md)
