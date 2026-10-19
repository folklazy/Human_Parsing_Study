# การตัดสิน dataset หลัก — provisional evidence review

**Dataset roles ยังไม่ freeze** เป้าหมายคือ body/clothing/expressible accessories สำหรับเลือก configurations แล้วไปทดสอบ finalists บน company CCTV ภายหลัง ไม่ใช่ architecture-controlled comparison ที่กำหนด training exposures เท่ากัน

## Decision matrix

| เกณฑ์ | CIHP | MHP-v2 | ความหมายต่อการตัดสินใจ |
|---|---|---|---|
| Body parts | Source ระบุ face, torso-skin, L/R arms/legs; bare hands/feet ไม่แยก | ตรวจ native fine-grained labels รวม hands/feet แล้ว | CIHP อาจเพียงพอ coarse body; ความละเอียดเพิ่มเติมใช้ secondary |
| Clothing | Upper-clothes, coat, dress, pants, skirt, socks ตาม source | Fine-grained garments และ footwear ตรวจ native IDs แล้ว | เปรียบเทียบทั้ง utility และ semantic expressibility ไม่ดู class count อย่างเดียว |
| Accessories | Hat/gloves/sunglasses/scarf; limited native coverage | Carried/accessory labels มากกว่า แต่ไม่ใช่ anatomical silhouette | มีประโยชน์เมื่อ labels, sample support และ checkpoint semantics รองรับจริง |
| Multi-person identity | Native source มี human/part maps; local DatasetNinja lacks human ownership metadata | Per-person planes decode/hash/roundtrip 54,316 แล้ว; overlap retained | ทั้งคู่ต้อง physical-person review; data representation ต่างกัน |
| File integrity | Local TAR/bitmap integrity PASS; RGB strict decoding sampled 20 only | 4 RGB เสีย; approved readable manifests พร้อม denominator | Integrity ผ่านก็ไม่พอรับรอง GT truth |
| Annotation reliability | Professional QC ตาม paper; independent release review ไม่มี | Selected ownership anomalies; independent SRS checklist ยัง pending | ยังไม่มี comparative prevalence หรือ CIHP cleaner claim |
| Split independence | 39 exact JPEG-byte train–val groups confirmed; full decoded/near audit pending | 652 val IDs exact train reuse; within-val duplicates | CIHP ไม่ได้อิสระโดยอัตโนมัติ; MHP รายงาน sensitivity แยก |
| Checkpoint exposure | M2FP/CPI/D2FP มี declared CIHP weights | M2FP/CPI มี declared MHP-v2 weights | เป็น off-the-shelf configurations; ต้องระบุ training/selection exposure ไม่ claim architecture causality |
| Reproducibility | Local converted SHA256/reader tested; official demo semantic parity 5/5; human GT missing/full native parity pending | Dataset/GT/source manifests พร้อม, wrapper synthetic parity มี | CIHP acquisition ต้อง audit conversion โดยไม่ silently drop files |
| Licensing | Dataset grant UNKNOWN; PGN software MIT ไม่ครอบ dataset โดยอัตโนมัติ | Existing research-use evidence; deployment/use terms ยังต้องยืนยันรายองค์ประกอบ | Dataset, code, weights และ YOLO AGPL/enterprise แยกกัน |
| CCTV integration | Internet multi-person images ไม่ใช่ proof CCTV robustness | เช่นเดียวกัน | ต้อง finalist field test แยก; unlabeled CCTV ยังไม่มี quantitative GT score |

## Recommendation

**A — CIHP primary + MHP-v2 secondary เป็น provisional direction ที่ควรตรวจต่อ ไม่ใช่ final promotion** CIHP มี body/clothing concepts และ native full-frame checkpoints ที่สอดคล้องเป้าหมาย จึงคุ้มที่จะขอ dataset มาตรวจ ส่วน MHP-v2 เก็บรายละเอียดมากกว่าสำหรับ secondary diagnostic แต่มี reuse/ownership risks ที่ยืนยันบางส่วนแล้ว

สถานะพร้อม benchmark ขณะนี้: **ยังไม่มีหลักฐานพอให้ freeze primary dataset ใด** หาก CIHP review พบ serious ownership/leakage/license issues ต้องพิจารณา B/C/D ใหม่ การเลือก A ตอนนี้เป็นลำดับการหาหลักฐาน ไม่ได้แปลว่า CIHP ชนะด้านคุณภาพ

## เงื่อนไขก่อน promote CIHP

1. ตรวจ actual split/file/GT inventory และ source SHA256; hidden test GT ไม่ใช่ corruption
2. Verify semantic/human/part relationships และ lossless per-person reconstruction; resolve ignore/visibility/overlap policy
3. Exact decoded reuse audit ทั้ง train–val และ within-val; near-duplicate findings ระบุวิธี/limitations และไม่ claim absence จาก exact hash
4. Complete independent stratified train quality review ตาม checklist กับการ adjudicate critical/uncertain cases; เปรียบเทียบอย่างมี denominator กับ MHP review ไม่ใช้เฉพาะ selected anomalies
5. Dataset intended-use permission และ candidate weights/license clarity; actual bounded checkpoint smoke แยกจาก quality gate
6. Approve dataset-specific native evaluation และ common cohorts; COMMON_HP ยัง draft, disclose retained class/pixel support

## Comparison cohorts

Native instance cohort: M2FP/CPI/D2FP ที่มี weights ตรง dataset; architecture/native internal detection คงเดิม Common semantic crop cohort: FASHN/SCHP/eligible LIP weights ตาม taxonomy และ ownership policy ที่ร่วมกันได้ แยก native-reference จาก YOLO-conditioned applications

MHP fine-grained native score ไม่ควรจัดอันดับร่วมกับ CIHP 20-class raw mIoU; dataset distributions และ classes ต่างกัน แม้ common projection เหมือนกันก็รายงานแต่ละ dataset แยก ไม่ average ข้าม dataset เป็น leaderboard เดียวโดยไร้เหตุผลที่อนุมัติ

Hands ≠ gloves; bare feet ≠ shoes; torso-skin ≠ torso; LIP label10 ≠ CIHP label10 ต้องใช้ checkpoint-specific mappings unsupported GT ห้ามกลายเป็น background ทุก cohort ใช้ GT domain เดียวกันและเก็บ native outputs

Company CCTV ไม่มี labels: ก่อน quantitative field acceptance ต้องอนุมัติ annotation/evaluation design แยก ถ้าทำเพียง qualitative review ต้องระบุขอบเขตและไม่ claim mIoU, reliability หรือ deployment readiness

หลักฐาน: [CIHP audit](CIHP_QUALITY_AUDIT.md), [MHP review](MHPV2_QUALITY_RISK_REVIEW.md), [metadata registry](../provenance/MODEL_VARIANT_REGISTRY_V2.csv)

## Preflight amendment

CIHP archive exists; availability is no longer a blocker. Native-human ownership loss is a genuine input-contract blocker for this study's person-instance tracks, not proof that native CIHP is poor quality. Provisional A remains a direction conditional on obtaining native GT and completing an independent quality audit. DatasetNinja semantic-only track cannot substitute silently for native human parsing; no primary promotion or final role freeze.
