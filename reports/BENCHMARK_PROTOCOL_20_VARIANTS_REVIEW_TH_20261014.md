# ความเห็นต่อแผน Human Parsing 20 variants — ตรวจเทียบหลักฐานใน workspace

วันที่ตรวจ: 14 ตุลาคม 2026 UTC · สถานะ: **REVIEW ONLY — ยังไม่ freeze และไม่อนุมัติ benchmark**

แผนที่ตรวจ: [HUMAN_PARSING_BENCHMARK_PROTOCOL_20_VARIANTS_TH_20261014.md](../../HUMAN_PARSING_BENCHMARK_PROTOCOL_20_VARIANTS_TH_20261014.md)

**ความเห็นหลัก:** แผนมีหลักการเปรียบเทียบที่ดีและควรใช้ต่อ แต่ยังเป็นกรอบออกแบบ ต้องปรับสถานะหลักฐานให้ตรงกับงานที่ทำแล้ว และกำหนดเงื่อนไขการทดลองให้รันได้จริงก่อน freeze โดยเฉพาะ taxonomy, GT scoring domain, การส่งบุคคลเข้า parser และ runtime profile ไม่จำเป็นต้องเริ่ม Stage 0 ใหม่หรือทำทุก dataset/metric ให้ครบก่อนเริ่ม cohort ที่พร้อม

## 1. ส่วนที่ควรรักษาไว้

- เปรียบเทียบระบบ pretrained/checkpoint ที่มีอยู่จริง และเปิดเผย training exposure แทนการอ้างว่าพิสูจน์ architecture ใดเหนือกว่า
- มี roster กลาง 20 variants แต่แยกคะแนนตาม dataset, population, taxonomy, track, runtime และ evaluator ไม่บังคับทุกตัวเข้าตารางอันดับเดียว
- ให้ body/clothing และ person ownership อยู่ในโจทย์หลัก Foreground อย่างเดียวไม่ตอบว่าจะแยกส่วนร่างกายและเสื้อผ้าได้ดีเพียงใด
- แยก native system, oracle localization และ shared detector พร้อมรักษาคนที่ตรวจไม่พบใน denominator
- ไม่ใช้ GT เลือก prediction ที่ดีที่สุด ไม่เปลี่ยน unknown เป็น background และไม่ลด denominator ตามความสามารถของแต่ละโมเดล
- เก็บ original GT, raw predictions, failure ledger และ sensitivity populations โดยไม่เปลี่ยน source split
- ใช้ paired uncertainty และไม่อ้างผู้ชนะจากทศนิยมท้าย ๆ หรือคะแนนรวมที่กำหนดหลังเห็นผล

หลักการเหล่านี้เหมาะกับงานนี้ ความยากอยู่ที่การแปลงเป็น config, adapter และ evaluator ที่มีสูตรและ tests ชัดเจน

## 2. ข้อมูลในแผนที่ต้องอัปเดตก่อน

ตรวจ registry, active validation, ตัวอย่าง RUN/config และรายงาน audit ปัจจุบัน ไม่ได้โหลด checkpoints หรือประเมิน validation ใหม่ ผลตรวจรอบนี้ไม่ใช่การ revalidate numerical outputs ทุกไฟล์ซ้ำทั้งชุด

| ประเด็นในแผน | หลักฐานที่มีจริง | ข้อเสนอ |
|---|---|---|
| §1: roster และ 200 outputs เป็น USER_REPORTED | Active validation และ registry มี 20 variants × 10 TRAIN images พร้อม RUN pointers และสถานะข้อจำกัด | เปลี่ยนเป็น LOCAL_EVIDENCE_VERIFIED พร้อมลิงก์หลักฐาน; แยก pilot ผ่านจาก benchmark eligibility |
| §2: QANet/RP-R-CNN ยังไม่ทราบ backbone | QANet-CIHP config ใช้ ResNet50c; QANet-LIP ใช้ HRNet-W48; RP-R-CNN ทั้งสองชุดใช้ ResNet50-FPN | ผูก HP IDs กับ model_id/config/checkpoint hash เดิม ไม่สร้าง roster ซ้ำอีกชุด |
| §4.1: CCIHP strict checks เพียง 30 ภาพ | Full audit โหลด RGB 33,280 ภาพและ required PNG 99,840 ไฟล์ ครบ; decode/dimension errors 0 | อ้าง full audit ปัจจุบันและทำต่อเฉพาะ unresolved GT policy |
| §4.1: Category22 สองพิกเซล | พบ 322 ภาพ / 8,268 พิกเซล; TRAIN0033810 เป็นเพียงตัวอย่างสองพิกเซล | คง raw22; กำหนด unknown domain เดียวกันทั้ง cohort และรายงาน support |
| §4.1: decoded/near leakage ยังไม่ครบ | Exact decoded TRAIN–VAL reuse 39 VAL IDs; within-VAL มีหนึ่งกลุ่มสอง IDs; pHash screen มี 114 non-exact candidate pairs | ใช้ ledger เดิม; near candidates ยังไม่ใช่ confirmed leakage และไม่ตัดออกอัตโนมัติ |
| §4.1: MHP readable/sensitivity counts เป็นเพียง historical proposals | Versioned readable manifests และ tests มีแล้ว: VAL 4,999/13,257 native persons; controlled readable 4,347/11,408 | ใช้ manifests เป็นฐาน; การอนุมัติอ่าน subset ไม่ใช่การอนุมัติ benchmark |
| §4.1/§10: empty-prediction wrapper ยังต้องเริ่มตรวจ | มี separate MHP wrapper และ synthetic reference-parity tests แล้ว; รอบนี้รันผ่าน 19 tests | รักษา wrapper/source pins; เพิ่มเฉพาะ fixtures ของ CCIHP/common evaluation ไม่อ้าง MHP tests ว่ารับรอง CCIHP evaluator |

หลักฐาน: [Active pilot validation](../../Human_Parsing_CCIHP_10_Image_Pilot/provenance/ACTIVE_PILOT_VALIDATION.json), [Model status](../../Human_Parsing_CCIHP_10_Image_Pilot/metrics/MODEL_PILOT_STATUS.csv), [CCIHP full audit](CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md), [Leakage audit](CCIHP_SPLIT_LEAKAGE_STAGE0F.md), [MHP population tests](../tests/test_dataset_reassessment.py), [MHP evaluator tests](../tests/test_official_mhp_compat.py)

แผนอ้างชื่อไฟล์บางส่วนที่ลงท้าย `(1).md` และชื่อ basename ที่ไม่อยู่ข้างแผน ควรแทนด้วย root-relative Markdown links ไปยัง canonical reports จริง เพื่อไม่ให้ใช้งานเอกสารเก่าผิดฉบับ

## 3. ทำให้เส้นทางเข้า parser ตอบโจทย์ครบ

T1/T2/T3 ของแผนถูกหลัก แต่ T3 แบบ supplied boxes อาจรับ native multi-human parsers ได้ไม่ครบ ข้อนี้เป็นข้อจำกัดของ interface ไม่ใช่หลักฐานว่าโมเดลเหล่านั้น parsing ไม่ดี

แนะนำขยายรายละเอียดภายใน application track:

| เงื่อนไข | เส้นทาง | บอกอะไรได้ |
|---|---|---|
| T1 native reference | ภาพเต็ม → ระบบ native ตาม checkpoint | คุณภาพระบบเดิม รวม internal detector เมื่อมี |
| T2 oracle diagnostic | GT person geometry → parser ที่รองรับ | คุณภาพเมื่อทราบตำแหน่ง; ยังต้องจัดการเพื่อนบ้านใน crop |
| T3a detector-conditioned crop | Frozen YOLO26x → bbox/ROI → compatible parser → target ownership | คุณภาพ pipeline ที่ใช้ YOLO เป็น person source |
| T3b full-frame integrated alternative | Frozen YOLO26x และ native full-frame parser → deterministic instance association | ทางเลือก pipeline สำหรับ parser ที่ไม่รับ external proposals โดยตรง |

T3a/T3b เป็น **ข้อเสนอที่ยังไม่ได้ทดสอบ** ไม่ใช่ข้อรับรองว่าทุกรุ่นรองรับ T3b ต้องระบุ output instance/semantic ownership และ association ที่ทำได้จริง โดยไม่ใช้ GT ขณะ inference

เปรียบเทียบ T3a กับ T3b ได้ในฐานะ complete systems เมื่อ final task, GT/domain, population และ runtime boundaries ตรงกัน แต่ต้องเปิดเผย routing ต่างกัน และนับ internal detector ที่ซ้ำกับ YOLO ไม่อ้างว่า parser-only conditions เหมือนกัน

Pilot เดิมยังไม่มี YOLO26x และมีหลาย crop/ROI variants ที่ใช้เฉพาะคน GT ขนาดใหญ่สุด ส่วน QANet ใช้ GT proposals ผ่าน native ROI Align ไม่ได้รัน FCOS ดังนั้น pilot ผ่านไม่ได้แปลว่า T3 ผ่าน หรือรองรับทุกคนในภาพแล้ว การทดลองจริงต้องครอบคลุมทุก GT person / predicted person ที่กฎกำหนด รวมคนเล็ก เพื่อนบ้านและ detections ซ้ำ

## 4. กำหนด required outputs ก่อนพยายามรวมทั้ง 20 ตัว

ผมเห็นด้วยกับ master inventory 20 แถว แต่ไม่ควรให้ universal foreground score เป็นเงื่อนไขที่ทำให้ body/clothing benchmark ต้องรอทุกตัว

ควรมี requirement matrix ที่แยก body parts, clothing, accessories และ person identity แล้วสร้าง comparable cohorts ตาม semantics ที่ตรวจแล้ว โมเดล anatomy-only เช่น SCHP-Pascal มีประโยชน์เป็น body reference แต่ไม่ควรได้รับ clothing score ที่แต่งขึ้น หรือเป็นผู้ชนะรวมจากการเฉลี่ยเฉพาะงานที่ทำได้

ก่อน freeze ควรกำหนดหนึ่ง primary application endpoint ต่อ cohort เช่น common foreground-class mIoU สำหรับ body/clothing ที่นิยามร่วมกันได้ พร้อม coverage-aware person score และ person precision/recall เป็นผลร่วม รายงาน body และ clothing แยกเพื่อไม่ให้กลุ่มหนึ่งกลบอีกกลุ่ม ไม่ต้องสร้าง weighted overall score

จุดยากจริงคือ semantic granularity: Dress ของ CIHP checkpoint กับ UpperClothes/Skirt ของ CCIHP ไม่สามารถแยก dress mask เป็นสองส่วนด้วย lookup ได้ รวมถึง hand/arm, foot/shoe และ exposed skin/anatomical body part ที่อาจไม่ตรงกัน ให้ใช้ mapping ที่พิสูจน์ได้หรือแยก cohort และรายงาน GT classes/pixels ที่ retained การมีชื่อคล้ายกันหรือ channels เท่ากันยังไม่เพียงพอ

Native CCIHP category scores ต้องเรียกผล custom CCIHP ตาม release นี้ ไม่เรียก official native CIHP results

## 5. GT scoring policy เป็นจุดที่ต้องตัดสินจริง

Full audit ผ่านเรื่องไฟล์ แต่ไม่ได้ทำให้ semantic annotations สมบูรณ์ทุกคน:

- Human>0 แต่ Category0 มี 762 ภาพ / 94,856 พิกเซล
- 35 Human IDs มี Category0 ทั้ง mask และรวมกรณี unknown แล้วมี 42 IDs ไม่มี known foreground1..21
- TRAIN0014422/Human1 มีพื้นที่ 91,332 พิกเซลแต่ไม่มี semantic foreground จึงไม่ใช่ปัญหาเล็กระดับหนึ่งพิกเซลทุกกรณี

ต้องแยก **native ID count, localization-eligible GT count และ semantic-score-eligible GT count** พร้อมเหตุผล ไม่กำหนด semantic score เป็น 0 ให้คนที่ไม่มี semantic truth และไม่ตัดคนที่ parser ตรวจพลาดออกจาก eligible denominator

ข้อเสนอสำหรับ draft: raw GT ไม่เปลี่ยน; unknown GT ใช้ explicit unresolved/void policy เดียวกันทุกตัวใน cohort; GT ที่ semantic score undefined ให้รายงานแยก และยังพิจารณา localization coverage ตาม geometry eligibility ที่ประกาศ คนที่มี semantic GT ใช้ได้แต่ไม่มี prediction ต้องได้ miss/zero ตามสูตรที่ล็อกไว้ Unmatched predictions ต้องสะท้อนใน precision/FP reporting ด้วย เพราะ person-macro score เฉพาะ GT อย่างเดียวไม่ลงโทษ extra persons ครบ

การเลือก assignment, threshold, tie-breaking, absent-class rule, overlap domain และ target ownership ต้องเป็น executable definitions พร้อม fixtures ไม่ควรเหลือเพียงข้อความว่า “matching ผ่าน” หรือ “coverage-aware”

ผมไม่ได้แนะนำให้ทวนการดู 200 ภาพใหม่ทั้งหมด Assistant review ตรวจครบ 200 ภาพแล้วและผู้ใช้ยอมรับให้ใช้ข้อมูล ควรบันทึก user acceptance แยกจาก independent human checklist ที่ยัง PENDING และเลือก adjudicate เฉพาะข้อสงสัยที่กระทบ scoring ไม่อ้าง annotation-error prevalence หรือความสะอาดทั้ง dataset โดยไม่มีหลักฐานเพิ่ม

หลักฐาน: [Assistant visual review](CCIHP_ASSISTANT_ANNOTATION_REVIEW_TH.md)

## 6. แก้คำว่า FP32 และ execution profile ให้ตรงผลจริง

### Sapiens2

Native source และรายงาน run ระบุว่า parameters/logits เป็น FP32 แต่ RoPE ภายในใช้ BF16 ก่อน cast กลับ FP32 จึงไม่ควรเรียก all-operations FP32 ชื่อ profile ควรอธิบายว่า **FP32 parameters/logits with native BF16 RoPE** และบันทึก intermediate policy นี้ไว้

ถ้าต้องการ strict FP32 ทุก operation ต้องเป็น profile ใหม่พร้อม numerical/functional checks ไม่เปลี่ยน native behavior แล้วอ้างว่าเหมือน pilot เดิมโดยอัตโนมัติ และไม่จำเป็นต้องทำเช่นนั้นเพียงเพื่อให้ชื่อ precision เหมือนกันทุกระบบ หากโจทย์คือเปรียบเทียบ native pretrained systems ที่เปิดเผยเงื่อนไข

Sapiens2-1B ทำ native GPU inference ครบสิบภาพแล้ว Warning ที่มีเป็น optional CPU-offload control ซึ่ง masks เท่ากันแต่ logits ต่างเล็กน้อย ไม่ควรเขียนว่า 1B native inference ล้มเหลว หรือใช้ warning นี้อ้างว่า native run ต้อง CPU offload

หลักฐาน: [Sapiens execution report](../../Human_Parsing_CCIHP_10_Image_Pilot/reports/SAPIENS2_1B_5B_EXECUTION_TH.md), [Native RoPE implementation](../../third_party/human_parsing/sapiens2/sapiens/backbones/sapiens2.py)

### CPI-R50-CIHP

Native unmodified run สำเร็จ 8/10 ก่อน OOM; ten-image completion ใช้ independent-person chunks of 10 มี saved control ตรวจ masks/boxes/scores ตรงหนึ่งภาพ ข้อจำกัดนี้ต้องอยู่ใน profile และผล resource ต้องวัดวิธีที่ใช้จริง ไม่อ้าง native-unmodified latency/VRAM

One-image parity เป็นหลักฐานที่มีประโยชน์ แต่ยังไม่รับรองทุกภาพ ควรเพิ่ม bounded development checks เฉพาะกรณีที่จำเป็นภายใต้การอนุมัติรอบถัดไป

หลักฐาน: [CPI resource adaptation RUN](../../Human_Parsing_CCIHP_10_Image_Pilot/outputs/cpi_r50_cihp-20261012T094956Z/RUN.json)

ตรวจ hardware รอบนี้พบ Tesla T4 15,360 MiB, driver580.178.04 และ free VRAM 8,421 MiB ณ เวลาตรวจ เป็น snapshot ไม่ใช่ข้อรับรองว่ามีทรัพยากรว่างพอสำหรับ benchmark ต้องวัดในช่วงไม่มี external contention ไม่หยุดงานผู้อื่น

## 7. บทบาท VAL: wording ต้องไม่ทำให้เลือกโมเดลไม่ได้

§14 มีคำว่าไม่ใช้ VAL สำหรับ model selection/tuning “ในขอบเขตปัจจุบัน” และภายหลังอนุญาต descriptive comparison + confirmatory holdout หลักการนี้ไม่ผิด แต่ควรแยก phases ให้ชัดเพื่อไม่ตีความว่าห้าม shortlist จากผล benchmark ตลอดไป

ข้อเสนอ:

1. TRAIN development ใช้เลือก mapping, crops, thresholds และ implementation; เก็บ history ว่าเคยดู pilot ใดแล้ว
2. เมื่ออนุมัติ benchmark ใช้ fixed public VAL เพื่อเปรียบเทียบและ shortlist ภายใต้ protocol ที่ freeze โดยไม่แก้กติกาจาก VAL scores
3. ยืนยัน finalists ใน independent holdout ที่ไม่ใช้เลือกรุ่น หากจะอ้าง generalization ของรุ่นที่เลือกอย่างหนักแน่น

หากต้องการให้ VAL เป็น untouched confirmatory set จริง ก็ต้องแยก selection population อีกชุดก่อน ห้ามให้ชุดเดียวทำทั้งสองบทบาทแล้วอ้าง unbiased final-winner performance

บริษัทมี CCTV ที่ยังไม่มี labels จึงใช้ดู feasibility/visual behavior ได้ภายใต้การอนุมัติภายหลัง แต่ยังไม่มี quantitative final accuracy โดยอัตโนมัติ ถ้าต้องการผลนั้น ต้องมี GT และ evaluation plan แยก ไม่เริ่มงานนี้ในรอบ review

## 8. Runtime และสถิติ: ลดงานที่ไม่จำเป็นแต่คงความถูกต้อง

- Accuracy ใช้ shared YOLO cache ได้ แต่ end-to-end latency ต้องวัด pipeline จริงใน workload เดียวกัน ไม่บวก mean/p95 จากคนละ manifest แล้วเรียก measured frame latency
- Freeze timing frame/person manifests, warmups, measured rounds, CPU/GPU boundaries, N persons และ failure policy เป็น config ที่รันได้ ไม่วัดเวลารวม model load หรือ overlay โดยไม่ตั้งชื่อแยก
- Duplicate/content clusters เป็น resampling units เมื่อมี image reuse; persons หรือ pixels ในภาพเดียวกันไม่ใช่ independent samples
- คำนวณ global confusion/AP ใหม่ใน bootstrap replicate ถูกหลัก แต่ 2,000 replicates ไม่จำเป็นต้องทำทุก metric × ทั้ง190คู่ตั้งแต่ต้น กำหนด primary contrasts และใช้ per-image sufficient statistics เมื่อรองรับ
- อย่าทำ class set เปลี่ยนใน replicate แบบเงียบ ๆ เมื่อ rare class หาย; กำหนด undefined/support rule และรายงานเหตุผล
- Union-of-known-training-overlap sensitivity เป็นแนวทางที่ดี แต่ UNKNOWN pretraining ไม่ใช่เหตุให้ทั้งงานต้องรอการพิสูจน์ข้อมูลที่เข้าถึงไม่ได้ เริ่มจาก CCIHP39 และ MHP652 IDs ที่มี ledger แล้ว และเปิดเผยข้อจำกัดที่เหลือ
- เก็บ original source population กับ sensitivity population แยกกัน ไม่อ้างว่าชุด overlap-controlled ขจัด leakage ทั้งหมด

| Dataset/population ที่มี evidence | Images | Native GT person IDs/planes |
|---|---:|---:|
| CCIHP source VAL | 5,000 | 17,548 |
| CCIHP exact TRAIN-overlap-controlled draft | 4,961 | 17,434 |
| MHP readable VAL ที่อนุมัติแล้ว | 4,999 | 13,257 |
| MHP exact TRAIN-overlap-controlled readable | 4,347 | 11,408 |

ตัวเลขนี้เป็น source populations ไม่ใช่การ freeze semantic-score denominator การกำหนด GT eligibility อาจทำให้จำนวน semantic-evaluable persons ต่างออกไปและต้องแสดงแยก

## 9. สิทธิ์ใช้งานและขอบเขต

ผลการรันจริงกับ eligibility เป็นคนละเรื่อง แผนถูกต้องที่ไม่ลบ Sapiens2 outputs หรืออ้างว่าการรันผ่านพิสูจน์สิทธิ์ ขณะเดียวกันควรเปลี่ยน technical evidence จาก USER_REPORTED เป็น actual pilot evidence ที่มีแล้ว

License ที่ pin กับ source ของ Sapiens2 ยังระบุข้อจำกัด surveillance รวม research/development ที่เกี่ยวข้อง [Official license §1(b)(vi)(i)](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/LICENSE.md) จึงต้องมี scope applicability/permission ที่รองรับก่อนใช้ใน surveillance-oriented continuation ไม่อนุมานจากสถานะนักศึกษาหรือ public RGB และไม่ให้ข้อสรุปนี้หยุดการเตรียม cohort อื่นที่ eligible

4D-DRESS, native CIHP, LIP/ATR/Pascal และ metrics เสริมอย่าง PartPQ ควรแยกเป็น optional follow-up ที่ตอบคำถามเฉพาะ ไม่เพิ่มเป็น prerequisite ทั้งหมดของรอบแรก แผนเองระบุข้อจำกัด projection/annotation ของ [4D-DRESS](https://arxiv.org/html/2404.18630v1) ไว้เหมาะสมแล้ว จึงยังไม่ต้อง acquire เพิ่มเพียงเพื่อให้มีคำว่า external

## 10. ลำดับที่ผมแนะนำก่อน benchmark

1. **อัปเดตแผนจากหลักฐานเดิม:** roster/model IDs, source pins, checkpoints, current audit, readable manifests และสอง execution warnings ไม่รันใหม่ทั้ง20
2. **เลือกคำถามหลักและ cohort:** CCIHP custom body/clothing เป็น candidate application dataset; MHP fine-grained เป็น complementary track; native CIHP scores รอ original compatible GT ไม่จำเป็นต้องดาวน์โหลดเพื่อทำ custom CCIHP track
3. **ทำ mapping + scoring-domain specification:** class definitions, unsupported/unknown rules, retained support และ semantic/person eligibility ใช้ TRAIN development ไม่เลือกกติกาจาก VAL scores
4. **ทำ routing/ownership eligibility table:** T1/T2/T3a/T3b ตามจริง รวม GT neighbors, missed/extra persons และ native detector costs
5. **ทดสอบเฉพาะช่องว่าง:** CCIHP/common evaluator fixtures และ bounded application-adapter checks เมื่อได้รับอนุมัติ ไม่ทำ full validation หรือ repeated full structural audit
6. **Freeze executable configs/manifests และ review gate:** จึงขออนุมัติขอบเขต benchmark แยก ไม่แปลว่า review นี้เป็นคำอนุญาต

สิ่งที่ยังต้องตัดสินก่อน freeze คือ primary output requirements, common cohort/domain, GT unknown/no-semantic policy, eligible routing, runtime profiles และบทบาท selection/confirmation populations แผนยาวได้เพราะเป็น scientific reference แต่ควรมีหน้า run specification สั้น ๆ ที่ระบุค่าจริงและลิงก์ไป details แทนการให้ runner ตีความ prose

## 11. สิ่งที่ตรวจ/ทำในรอบนี้

- อ่านแผนและ cross-check local pilot registry/active validation, selected source/config/RUN evidence, CCIHP audit/leakage/visual-review reports และ MHP population/evaluator tests
- รัน `.venvs/mhpv2-stage0/bin/python -m unittest discover -s Human_Parsing_MHPv2_Study/tests -p test_official_mhp_compat.py -q`: **19 tests PASS**
- รัน `.venvs/mhpv2-stage0/bin/python -m unittest discover -s Human_Parsing_MHPv2_Study/tests -p test_dataset_reassessment.py -q`: **7 tests PASS**
- ตรวจ NVIDIA hardware snapshot และ pinned Sapiens2 license; ไม่โหลดโมเดล ไม่ rerun inference/timing
- เขียนเฉพาะ review แยกและ evidence record; ไม่แก้แผนต้นฉบับ, GT, benchmark metrics หรือ study state

Root และ Human_Parsing_MHPv2_Study ไม่ใช่ Git working trees ณ ตอนตรวจ จึงไม่มี commit/push ในงานนี้ ผลตรวจ tests เป็น bounded CPU fixtures/manifests ไม่ใช่ full dataset re-audit หรือ parser benchmark

**ข้อสรุปของผม:** ใช้แผนนี้ต่อได้ หลังแก้ stale evidence และกำหนด application track/GT domain/runtime profile ให้ชัด เรามี foundation จริงมากกว่าที่แผนสะท้อนแล้ว ควรทำให้พร้อมรัน cohort ที่ตอบโจทย์ ก่อนขยายเป็นทุก dataset และทุก metric ที่เป็นไปได้
