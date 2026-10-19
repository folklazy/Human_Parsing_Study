# ข้อเสนอ dataset สำหรับคัดเลือก Human Parsing หลัง pilot 20 variants

วันที่ 14 ตุลาคม 2026 · **ข้อเสนอ DRAFT สำหรับ review** ไม่ freeze dataset roles, taxonomy หรือ protocol และไม่เริ่ม benchmark/download/inference

## ข้อเสนอที่เลือก

**จากทรัพยากรที่มีอยู่ แนะนำ CCIHP validation เป็นชุดคัดเลือกหลักของงาน custom person-level body/clothing parsing และ MHP-v2 เป็นชุดเสริมสำหรับรายละเอียดที่ละเอียดกว่า จากนั้นประเมิน finalists บน CCTV ที่แยกไว้และมี GT หากต้องการคะแนนเชิงตัวเลข**

หากเป้าหมายสำคัญคือการเทียบกับผลตีพิมพ์ของ CIHP โดยตรง แนะนำ **native CIHP validation พร้อม GT ดั้งเดิม** เป็น primary public benchmark แทน CCIHP. ต้องมี native person/part GT ที่ตรวจยืนยันแล้วก่อนใช้ track นี้; DatasetNinja ที่มีอยู่สูญเสีย ownership metadata และ CCIHP ไม่ใช่ native CIHP GT ที่ใช้แทนกันได้

นี่เป็นข้อเสนอด้านความเหมาะสมของงานและความพร้อมของ assets ไม่ใช่หลักฐานว่า CCIHP มี annotation quality สูงที่สุดหรือว่าโมเดลใดเป็นผู้ชนะ

## 1. ผล pilot บอกอะไรสำหรับการเลือก dataset

Active pilot มี 20 variants / 200 image outputs จาก CCIHP TRAIN สิบภาพเดิม. ตรวจ checkpoint loading, output geometry, finite values และ native classes ได้ แต่ยังไม่มี dataset-level accuracy evaluation

- บางรุ่นรับภาพเต็มและทำนายหลายคน บางรุ่นรับ GT crop ของคนที่มี mask ใหญ่ที่สุดเพียงหนึ่งคน. ภาพที่ดูดีกว่าจึงยังไม่ใช่ผลจากเงื่อนไขเดียวกัน
- ภาพ CCIHP อ้างอิงภาพ CIHP. Checkpoints ที่ฝึก CIHP TRAIN อาจเคยเห็นสิบภาพนี้; เปลี่ยน annotation ไม่ทำให้ RGB เป็นข้อมูลใหม่
- จำนวน class ที่พบเป็น prediction support ไม่ใช่ correctness. Mask แนบกว่าในภาพหนึ่งก็ยังไม่เพียงพอจัดอันดับทั้งชุด
- เลือก dataset จาก body/clothing concepts, person identity, annotation quality และ evaluation population ที่ต้องการ แล้วตรึงก่อนอ่านผล validation. ไม่เลือก dataset เพราะโมเดลที่สนใจทำคะแนนสูงกว่าในชุดนั้น

[ผล pilot และ taxonomy](../../Human_Parsing_CCIHP_10_Image_Pilot/reports/PILOT_RESULTS_TH.md) · [Active variants](../../Human_Parsing_CCIHP_10_Image_Pilot/metrics/MODEL_PILOT_STATUS.csv)

## 2. Dataset ที่แนะนำและบทบาท

| Dataset | บทบาทที่เสนอ | เหตุผล | ขอบเขตและข้อจำกัด |
|---|---|---|---|
| **CCIHP ที่มีอยู่** | Primary custom application-task evaluation แบบมีเงื่อนไข | มี Human_ids และ semantic GT สำหรับภาพหลายคน; มี local integrity/provenance และการตรวจภาพแล้ว | นิยามต่างจาก native CIHP; Dress ถูกแยก UpperClothes/Skirt, มี Face Mask และมี labels/semantic-support warnings ที่ต้องกำหนด scoring policy |
| **Native CIHP** | Primary หากต้องการ standard benchmark / native checkpoint comparability | เป็น instance-level multi-person parsing benchmark และตรงกับ CIHP checkpoints หลายรุ่น | ต้องใช้ GT ดั้งเดิมที่ครบ; ไม่ถือ conversion หรือ CCIHP เป็นของเทียบเท่าโดยอัตโนมัติ และยังต้อง audit split/GT |
| **MHP-v2** | Secondary fine-grained body/clothing/accessory evaluation | มี 58 foreground categories และ per-person annotation planes | Local RGB เสียสี่ไฟล์ มี train/validation exact reuse และ ownership risks; ใช้ readable populations และ sensitivity ที่แยกกัน |
| **LIP** | Optional single-person parser reference | มี body/clothing parsing labels และสอดคล้องกับ LIP checkpoints | ไม่แทน full-frame multi-person coverage test; ต้อง audit assets/exposure/labels ก่อนเพิ่ม และไม่จำเป็นต้องเพิ่มเพื่อเริ่มตรวจ protocol ด้วย assets เดิม |
| **Fashionpedia** | Optional clothing/accessory-region diagnostic หลัง shortlist | เน้น garment/object masks และ ontology เครื่องแต่งกาย | ไม่ใช่ GT person-instance/body-part benchmark สำหรับทุกคน; ตรวจ ownership/semantic compatibility แยก ไม่ทำ color/attribute evaluation |
| **CCTV ที่กันไว้** | Finalist field evaluation ภายหลัง | ตรงกับภาพการใช้งานจริงมากกว่า public parsing datasets | ปัจจุบันไม่มี labels จึงยังให้ mIoU หรือ quantitative winner ไม่ได้; ต้องมี annotation/held-out design และสิทธิ์ใช้ข้อมูล/โมเดลที่เกี่ยวข้อง |

แหล่งทางการ: [CIHP paper](https://www.ecva.net/papers/eccv_2018/papers_ECCV/papers/Ke_Gong_Instance-level_Human_Parsing_ECCV_2018_paper.pdf), [CIHP implementation](https://github.com/Engineering-Course/CIHP_PGN), [CCIHP publication §2](https://arxiv.org/html/2201.09594v1#S2), [MHP-v2 project](https://lv-mhp.github.io/), [LIP paper](https://openaccess.thecvf.com/content_cvpr_2017/html/Gong_Look_Into_Person_CVPR_2017_paper.html), [Fashionpedia official repository](https://github.com/cvdfoundation/fashionpedia)

CIHP และ CCIHP ใช้ภาพร่วมกัน จึงไม่ใช่สอง independent external datasets แม้ annotation targets ต่างกัน. MHP-v2/LIP/Fashionpedia ก็ไม่ถูกประกาศว่า unseen สำหรับทุก checkpoint; ต้องตรวจ declared exposure และ exact image overlap เพิ่มตาม cohort

## 3. ผูก dataset กับ weights โดยไม่ให้แต่ละรุ่นเลือกชุดที่ตัวเองได้เปรียบ

| Weights ใน active pilot | สิ่งที่เหมาะตรวจ | วิธีอ่านผล |
|---|---|---|
| M2FP/CPI/D2FP/QANet/RP-R-CNN — CIHP | Native CIHP reference หาก GT ครบ; custom CCIHP/common task เมื่อ mappings รองรับ | ไม่ถือ CCIHP เป็น unseen เพราะ RGB ร่วมกับ CIHP; native score กับ custom score แยกชื่อ |
| M2FP/CPI/RP-R-CNN — MHP-v2 | Native MHP-v2 reference และ body/clothing common task | Native taxonomy ละเอียดกว่าไม่ได้ทำให้ common score สูงกว่าโดยอัตโนมัติ; รายงาน exposure และ readable denominator |
| M2FP/D2FP/SCHP/QANet — LIP | Oracle-person parsing และ detector-conditioned crops เมื่อ interface/ownership ผ่าน | GT crop reference แยกจาก native full-frame prediction; LIP และ CIHP ID10 มีความหมายต่างกัน |
| SCHP — ATR | Clothing/accessory concepts ที่ native taxonomy รองรับ | Class count 18 ไม่เท่ากับ FASHN 18; ไม่มี label บางตัวที่ CIHP/LIP แยกไว้ |
| SCHP — Pascal-Person-Part | Body-part reference | ไม่มี clothing categories แยก จึงไม่ควรแข่งขันเป็นผู้ชนะด้าน clothing ด้วย score เดียวกับ garment parsers |
| FASHN | Body/clothing/accessory common task และรายละเอียดที่ GT รองรับ | มี hands/feet/torso/bag/belt/jewelry แต่ไม่อนุมานว่า GT มี concepts เหล่านี้ครบ; exact training composition ยังไม่ยืนยันทั้งหมด |
| Sapiens2 0.4B/0.8B/1B | Body regions และ clothing coarse task; native details ที่มี GT จริง | มี limb subdivisions/hands/feet/mouth details แต่ CIHP/CCIHP ไม่ใช่ GT สำหรับทุก native class; ยังไม่ preassign เป็น body expert |

รายละเอียดมือ/เท้าเปล่า, arms/limb subdivisions, torso skin และ footwear ต้องตรวจ semantics ไม่ map ด้วยชื่อหรือเลข ID อย่างเดียว. `hands` ไม่ใช่ `gloves`; bare feet ไม่ใช่ shoes; torso ไม่เท่ากับ torso-skin โดยอัตโนมัติ. CCIHP ไม่สามารถวัด lips/teeth/tongue ให้ Sapiens2 ได้จาก GT ที่ไม่มี labels ดังกล่าว

ข้อเสนอคือมี **common comparable cohorts** และ **native/detail reference cohorts**. ภายใน common cohort ต้องใช้ GT projection, class definitions และ pixel/person denominator เดียวกันทุกโมเดล. Unsupported concepts ไม่กลายเป็น background และไม่ให้แต่ละโมเดลเลือก ignore GT คนละชุดแล้วนำคะแนนมาเรียงร่วมกัน. หาก taxonomy กลางหยาบจนตอบเรื่องเสื้อผ้าไม่ได้ ให้แยก cohort ที่แสดงรายละเอียดได้จริงแทน

## 4. ข้อจำกัดของ datasets ที่ตรวจพบจริง

### CCIHP

Full structural audit ตรวจ TRAIN 28,280 และ VALIDATION 5,000 image/GT sets. Assistant ดูชุดสุ่ม TRAIN 200 ภาพใน contact sheets และตรวจบางกรณีละเอียด; มีหลักฐานใช้งานได้ในหลายภาพและมีข้อจำกัดจริงบางกรณี. การยอมรับใช้ข้อมูลโดยผู้ใช้ไม่ถูกแปลงเป็น independent quantitative annotation-error estimate

- Unknown Category22 พบ 322 ภาพ / 8,268 pixels ทั้งชุด. ต้องรักษาค่าเดิมและเสนอ known-label/void domain อย่างชัดเจน ไม่ assign เป็น background
- พบ source Human IDs บางตัวที่ไม่มี known semantic foreground. ต้องกำหนด eligibility/undefined-score policy และรายงานจำนวนคนตาม source กับจำนวนคนที่ scoring ใช้แยกกัน
- Exact decoded-RGB train overlap มี 39 validation IDs. เสนอรายงาน original population **5,000 ภาพ / 17,548 source GT persons** และ exact-overlap-controlled sensitivity **4,961 ภาพ / 17,434 persons** แยกกัน; manifests ยังเป็น draft ไม่เปลี่ยน split
- Within-validation มี exact duplicate group หนึ่งกลุ่ม และมี near-duplicate screening candidates. Controlled population ข้างต้นยังไม่ใช่ fully independent/fully deduplicated test

[Full audit](CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md) · [Assistant visual review](CCIHP_ASSISTANT_ANNOTATION_REVIEW_TH.md) · [Split evidence](CCIHP_SPLIT_LEAKAGE_STAGE0F.md)

### MHP-v2

Readable validation ที่อนุมัติไว้คือ **4,999 ภาพ / 13,257 source GT persons**. Exact train-overlap-controlled readable validation คือ **4,347 ภาพ / 11,408 persons**. เก็บสองเงื่อนไขแยกตาราง ไม่อ้าง score 4,999 ภาพเป็น unqualified official 5,000-image result. Ownership anomalies เป็นเหตุให้ disclose uncertainty/sensitivity ไม่ใช่หลักฐานว่า annotations ทุกภาพผิด

[MHP-v2 quality-risk review](MHPV2_QUALITY_RISK_REVIEW.md)

## 5. ขั้นตอนคัดเลือกที่เสนอ

1. **กำหนดสิ่งที่ต้องการให้ระบบแสดง**: body parts ระดับใด, garment distinctions ใด, accessories ใดสำคัญ. แยก required กับ optional เพื่อไม่ใช้คะแนนหยาบกลบสิ่งที่แอปต้องการ
2. ใช้ **TRAIN development subset ที่ตรึงไว้** เพื่อตรวจ mappings, crop policy, target-person ownership และ adapters. สิบภาพ pilot ใช้ debug ได้ แต่ไม่ใช่ accuracy shortlist evidence. ไม่ปรับ settings จาก validation
3. Freeze common cohorts, GT projection, unknown-label rules, matching/coverage และ timing boundaries หลัง review. เก็บ source GT และ original split ไม่เปลี่ยน
4. ประเมิน candidates ด้วย **validation protocol เดียวกันภายในแต่ละ cohort**. เสนอให้เริ่ม CCIHP custom task จาก assets เดิม; หากต้องการ native CIHP target ให้ตรวจ/acquire native GT ก่อนโดยขออนุมัติ acquisition แยก
5. แยก **Oracle person** เพื่อดู parser quality, **YOLO26x-conditioned** เพื่อดู pipeline จริง และ **native full-frame reference** สำหรับ multi-human architectures. การนำ native full-frame parser มาจับคู่ YOLO เป็นอีก system configuration ไม่ใช่การ bypass detector หรืออ้างว่าเป็น crop parser เหมือนกัน
6. รายงาน body/clothing scores, per-class support, missed-person coverage และ target-person contamination. Matched-only parsing quality ต้องอยู่คู่กับ coverage-aware quality; คนที่ YOLO พลาดไม่หายจากทุก denominator
7. คัดประมาณ **3–5 configurations** ด้วย measured accuracy/resource trade-offs และ diagnostic failure evidence. ประเมิน fine-grained concepts ที่มี GT ใน MHP-v2 เพิ่ม. ไม่รวม raw mIoU ข้าม datasets/taxonomies เป็นคะแนนเดียว และไม่มี weighted overall score
8. ใช้ CCTV held-out ที่แยกตาม camera/scene/time สำหรับ finalists ภายหลัง. หากมีแต่ภาพ unlabeled ให้รายงาน qualitative observations; หากต้องการ final numerical selection ให้มี GT และแยก development/test เพื่อป้องกันการเลือกค่าจาก final test

การเลือก finalists จาก validation เป็น model selection; final evidence ควรมาจากชุดที่กันไว้จริง. Public model releases อาจเคยใช้ validation เลือก checkpoints จึงไม่อ้างว่า training/selection exposure เท่ากันหรือพิสูจน์ architectural superiority

## 6. สิ่งที่ยังต้องตัดสินก่อนรันจริง

- ต้องการ primary แบบ **custom CCIHP task** หรือ **native CIHP target** เพื่อเทียบ literature
- Common concepts/cohorts ที่รักษารายละเอียด body/clothing เพียงพอและใช้ denominator ร่วมกันได้
- Known/unknown/semantic-support-gap policy และ original/controlled population reporting
- Adapters และ target-person ownership ของ detector-conditioned semantic crops โดยไม่ใช้ GT class masks ใน inference
- Timing workload/precision/memory ที่ใช้เทียบ system configurations และข้อจำกัด CPI memory adapter
- Final CCTV annotation design และ applicable permissions; PPSS คง paused, color/attribute/hybrid study ไม่เริ่ม

รายงานนี้เป็นการให้คำแนะนำจาก artifacts เดิมและ authoritative references. ไม่มี dataset/checkpoint download, parser inference, GT modification หรือการเปลี่ยน STUDY_STATE/primary dataset decision อัตโนมัติ
