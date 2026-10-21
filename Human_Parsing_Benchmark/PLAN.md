# Human Parsing Benchmark — แผนทดลอง authoritative

**REVIEWED_PROPOSAL — Revision 1 — 21 ตุลาคม 2026 UTC**  
นี่คือผลตรวจ/ข้อเสนอของ Prompt A ไม่ใช่ accepted executable configuration, DESIGN_READY หรือ LAUNCH_READY และยังไม่อนุมัติ implementation/inference/smoke/full benchmark

แผนปัจจุบันมีที่เดียวที่ไฟล์นี้ ใช้ชื่อ `PLAN.md` ต่อจาก SETUP ตามข้อกำหนด reuse จึงไม่สร้าง `HUMAN_PARSING_EXPERIMENT_DESIGN_TH.md` อีกชุด root file ชื่อเดิมเป็น historical proposal เท่านั้น [ผลตรวจและเหตุผล](reports/HUMAN_PARSING_PROTOCOL_REVIEW_TH.md) · [สถานะ](STATUS.md) · [decisions](docs/DECISIONS.md) · [draft specification](protocol/REVIEWED_SPECIFICATION.json)

## 1. คำถามวิจัยและสิ่งที่ส่งต่อ

Phase 1 จบแล้ว ผู้ใช้เลือก frozen YOLO26x-Seg ไม่เลือก YOLO ใหม่ Phase 2–3 ต้องตอบว่า pretrained checkpoint/configuration ใดให้ body/clothing regions และ person ownership ที่มีประโยชน์ โดยพิจารณาคุณภาพและต้นทุนบน T4 การเปรียบเทียบเป็น off-the-shelf system/configuration comparison ไม่ใช่ controlled architecture experiment

Outputs ที่จำเป็น: original-grid per-person semantic regions, upper garment/lower garment/footwear ที่แยกกันได้, exposed body detail ตาม GT ที่รองรับ, person/conditioning/native IDs แยกกัน, native scores หรือสถานะ unavailable, crop/map-back transforms และ checkpoint/config/run identities เก็บ native hard outputs แยกจาก mapped outputs แบบ lossless

Phase 4 จะใช้ original RGB และ regions เพื่อทำสี/attributes เอง ไม่บังคับ parser ทำนายสี ลวดลาย หรือทุก attribute ภายในตัวโมเดล เสื้อคลุมหมายถึง category ของเสื้อคลุมทั้งชิ้น ไม่แปลว่าทุกพิกเซลอยู่เหนือเอว Accessories เป็น supplementary จนผู้ใช้ระบุ named mandatory set; ไม่มี model ใดในชุดนี้พิสูจน์ครบ Bag/FaceMask/อื่นทั้งหมด

ดู [requirements → targets → source labels → loss/limitations](registry/REQUIREMENTS_TARGETS.csv) ไม่ออกแบบ requirement ให้รุ่นใดผ่านโดยเฉพาะ Phase 4/5, hybrid, color/attributes และ CCTV ยังไม่ดำเนินการ

## 2. Candidate scope และการนับ

Prompt A ระบุว่า roster ล่าสุดยังไม่ authoritative แต่มีตารางเจ็ดรายการจาก user message ก่อน SETUP อยู่จริง ใช้เป็น **ฐานเสนอ** ไม่ให้ inventory19/29 หรือ QANet proposal สองตัวเก่าขยาย workload อัตโนมัติ Sapiens2 สามขนาดยังเป็น active candidates ตามคำสั่งปัจจุบัน ไม่ใช้ RESTRICTED ที่ค้างใน CSV เก่าบล็อก roster; ไม่ได้ให้ new inference/license clearance จากการอ่านแผน

| Checkpoint ที่เสนอ | Application route | Native reference | บทบาทหลัก/ช่องว่าง |
|---|---|---|---|
| QANet CIHP HRNet-W48, H512×W384 | YOLO opportunities → native ROI Align → ownership clipping | ไม่เพิ่ม native detector route เพราะไม่มี official proposal detector ที่ผูกกับชุดนี้ | PRIMARY body/clothing; TRAIN YOLO ROI มี evidence แล้ว |
| M2FP R101 CIHP | Full-frame native → prediction-only YOLO association | Native person parsing จาก inference เดียวกัน | PRIMARY body/clothing; new mask-scoring context ยังไม่มี |
| D2FP R101 CIHP | เช่นเดียวกับ M2FP | Native person parsing จาก inference เดียวกัน | PRIMARY body/clothing; explicit OOM fallback control ต้องปิด |
| RP-R-CNN R50 CIHP | Full-frame internal detector → YOLO association | Internal detector + native parser เดิม | PRIMARY body/clothing; ไม่ bypass detector |
| Sapiens2 0.4B segmentation | YOLO ROI → semantic parser → YOLO ownership | Existing full-frame semantic pilot เป็น feasibility reference เท่านั้น ไม่เพิ่ม full VAL pass | PRIMARY garment view; body mapping approximate เป็น supplementary |
| Sapiens2 0.8B segmentation | เช่นเดียวกับ 0.4B | เช่นเดียวกับ 0.4B | Active; crop/integration route ยัง NOT_TESTED |
| Sapiens2 1B segmentation | เช่นเดียวกับ 0.4B | เช่นเดียวกับ 0.4B | Native GPU-resident pilot ผ่าน; joint residency ยังไม่พิสูจน์ |

**7 checkpoints / 10 proposed configurations = 7 application + 3 native-reference configurations** มี quality parser inference streams 7 ชุด Native reference สามตัวใช้ native artifacts เดียวกับ application association จึงไม่มี full native inference ซ้ำ Sapiens full-frame semantic ไม่ใช่ native instance parser และ QANet oracle pilot ไม่ใช่ native full-frame detector performance

Exact source/config/weights SHA256, sizes, pinned commits, load/smoke evidence และข้อจำกัดอยู่ใน [checkpoint matrix](registry/CHECKPOINT_ROUTE_REVIEW.csv) / [route matrix](registry/ROUTES_PROPOSED.csv) Hash ของ weights อ้าง existing verification ไม่ได้ rehash และ local fingerprint ไม่พิสูจน์ authenticity จากผู้สร้างเอง

[Diff ครบทุก historical inventory entry](registry/ROSTER_DIFF.csv): 7 proposed retained; 12 ตัวนอก proposed set เปลี่ยนเป็น HOLD เฉพาะแผนนี้ ไม่สรุปว่าแม่นน้อยกว่าและไม่ลบ assets CPI CIHP สองตัวเป็น closed historical INCOMPLETE ไม่ retry/เรียงคะแนนใหม่ Pascal body-only ไม่ตอบ upper/lower clothing; 5B ยังคง excluded ตาม user resource decision Optional checkpoint ที่ยังหาไม่ได้/ไม่มี inference evidence คงเหตุผลเดิม ไม่คืนเข้ารอบเงียบ ๆ ต้องรับ roster ที่เสนอไว้ก่อนยืนยัน scope ใหม่

## 3. Dataset, selection population และ exposure

CCIHP เป็น public selection benchmark หลัก ใช้ Category_ids semantic labels กับ Human_ids ภายในภาพ Instance_ids ของ CCIHP เป็น attribute-oriented region instances ไม่ใช่ native CIHP part IDs และไม่ใช้เป็น person IDs DatasetNinja CIHP เป็น RGB source/converted annotations; ห้ามผสม numeric IDs กับ CCIHP โดยตรง

Existing audit ครอบคลุม TRAIN28,280/VAL5,000 ชุด PNG ที่ต้องอ่าน 99,840 ไฟล์: structural PASS_WITH_WARNINGS ไม่ใช่ physical-person correctness certification Category22 มี 8,268pixels/322images ทั้งชุด ใน VAL310pixels/61images; H>0/C0 ใน VAL638pixels/144images; C>0/H0 พบ 0 Source GT คงเดิม ไม่เติมคนหรือแก้ ownership ด้วยโมเดล

Main **4,961 images** ตัด 39 VAL IDs ที่ exact byte/decoded RGB ซ้ำ TRAIN ตาม manifests เดิม; reference **5,000 images** เก็บไว้รายงานแยก inference shared ไม่คัดจาก scores มี within-VAL exact duplicate group1 และ near-duplicate candidate pairs114 ซึ่งยังไม่ยืนยัน จึงไม่เรียก main ว่า exposure-free สำหรับ checkpoint ใด

**นโยบายเปลี่ยนโดยคำสั่ง Prompt A ปัจจุบัน:** อนุญาตใช้ CCIHP VAL เพื่อคัดเลือก pretrained checkpoints/configurations ในแผนใหม่นี้ ต่างจาก policy เก่าที่ห้าม VAL selection แต่ยังห้าม tune mappings, thresholds, preprocessing, precision, TTA, retry policy หรือเลือก exclusions จาก VAL performance ผลต้องเรียกว่า selection-set results ไม่ใช่ independent final confirmation ประวัติ/accepted decisions/configs ของ CPI เดิมไม่ถูกแก้ย้อนหลัง

CIHP-trained checkpoints มี declared CIHP training exposure; การเลือก epoch/weights ด้วย original CIHP VAL และการซ้ำแบบอื่นยัง UNKNOWN หากไม่มี evidence Sapiens training config ชี้ Shutterstock/Goliath แต่ exact image overlap ไม่ทราบ ห้ามแปลง UNKNOWN เป็น NO และไม่อ้างว่า pretrained memorized ทุกภาพ

### GT/domain proposal

- C0/H0 = valid background; C0/H>0 = semantic void แต่ person location ยังอยู่
- C22 = fixed semantic void ทุกระบบ ไม่แปลงเป็น background
- Known C>0/H0 = global semantic valid; per-person owner unknown จึง void เฉพาะ per-person ปัจจุบันพบ 0pixels แต่ต้องนิยามไว้
- Known classes นอก target view = valid context-other ร่วมกันทุกโมเดล ไม่สร้าง per-model ignore masks
- G_loc ใช้ native Human_ids ที่ไม่ว่าง โดยไม่เรียกว่า identity ของ physical person ที่รับรองแล้ว G_sem(view) ต้องมี valid GT target pixel อย่างน้อยหนึ่งพิกเซล ไม่ขึ้นกับ prediction หรือ execution success

สตรีม `native_category_support` sidecar ที่มีอยู่แล้วเพื่อคำนวณตัวหารใหม่โดยไม่ decode GT อีกทั้งชุด ได้:

| Population | Images | G_loc | G_sem C3 garment | G_sem C7 body/clothing |
|---|---:|---:|---:|---:|
| Main | 4,961 | 17,434 | 17,085 | 17,390 |
| Reference | 5,000 | 17,548 | 17,199 | 17,504 |

C7 บังเอิญมี eligible-person union เท่า six-target เดิมเพราะแยก garment เดิมเป็น upper/lower แต่ไม่ได้ยกตัวหารมาใช้โดยสมมติ C3 ต่างชัดเจน ดู [derived population evidence](manifests/POPULATION_DOMAIN_PROPOSAL.json) นี่เป็น metadata-derived proposal ยังต้อง materialize/version ใหม่และทดสอบ pixel-level domain/context bindings ใน B ไม่แก้ source GT หรือ context เดิม

## 4. Target views และ mapping ที่เสนอ

ไม่ลด upper/lower ให้เหลือ garment เดียวเพื่อให้ทุกโมเดลเทียบง่าย:

| View | Targets | ใครเข้าตารางหลัก | ความหมาย |
|---|---|---|---|
| C3_GARMENT | Upper garment; Lower garment; Footwear | ทั้ง 7 checkpoints ทุก approved route ของ view เดียวกัน | ตอบหน้ากากเสื้อผ้าที่ส่ง Phase4 โดยยังเห็น upper/lower ต่างกัน |
| C7_BODY_CLOTHING | Face region; Exposed torso; Exposed arms; Exposed legs; Upper garment; Lower garment; Footwear | CIHP checkpoints4 ตัว: application4 + native reference3 แยก route tables | เพิ่ม exposed body detail ที่ catalog/GT รองรับ |
| Body semantic diagnostic | GT C7 เดียวกัน แต่ระบุ approximate mappings ของ Sapiens | Sapiens3 รายงานแยก ไม่มี C7 winner ร่วมกับ exact cohort | Face_Neck/Torso ไม่ตรง partition ของ CCIHP face/torso ที่พิสูจน์แล้ว |
| Accessories/native support | Hair/headwear/gloves/eyewear/socks/scarf และ unsupported FaceMask/Bag | Per-class diagnostics/capability ไม่ universal accessory leaderboard | ไม่ตีความว่าครบ accessories ที่ downstream อาจต้องการ |

Full [mapping72 rows](protocol/NATIVE_LABEL_MAPPING_DRAFT.csv) ระบุทุก native class: GT23 values รวม unknown 22, CIHP20 semantic labels, Sapiens29 semantic labels มาตรฐาน mapping types EXACT / MERGE / APPROXIMATE / UNSUPPORTED ส่วน auxiliary Human query ID20 ของ M2FP/D2FP ไม่ใช่ semantic class หรือ CCIHP Bag20; num_classes21 ใน head ไม่ได้หมายถึง 21 semantic targets

CCIHP5+7 → upper, 9+12 → lower,18+19 → footwear CIHP Dress6 ไม่สามารถ split เป็น dress-top/bottom โดยไม่มีข้อมูล จึงเป็น **UNRESOLVED_PRED** บน valid GT นับเป็นข้อผิดพลาด ไม่ ignore และไม่ส่งไป Background เพื่อซ่อนปัญหา Sapiens Apparel1 ใช้กติกาเดียวกัน Sapiens bare feet5/14 ไม่ใช่ shoes9/18; hands ต้อง merge กับ arms เมื่อ semantics รองรับ ไม่แปลงถุงมือเป็นมือหรือเอา Face_Neck ทั้งหมดไปถือ exact Face

Primary projection ใช้ **native hard labels หลัง native postprocess → deterministic lookup** เหตุผลคือ QANet/RP-R-CNN ไม่ได้เก็บ calibrated full-frame probabilities แบบเดียวกับทุกตัว การ aggregate probabilities ก่อน argmax เปลี่ยน inference decision และไม่ใช่สิ่งเดียวกับ remap labels จึงไม่เลือกวิธีตาม VAL score ถ้าภายหลังทดลอง probability aggregation ต้องเป็น config/revision แยก ไม่อ้างว่าหาได้จาก hard-label artifacts เดิม

C3/C7 ใช้ policy `FIXED_TASK_EXPLICIT_UNSUPPORTED`: เป็น fixed-task projected-output comparison ไม่ใช่การรับรอง native taxonomy equivalence; ใช้ target/domain เดียวกันสำหรับทุกระบบในตารางเดียว Unsupported native prediction อยู่ explicit error column; unexpected out-of-catalog IDs เป็น CONTRACT_INVALID Unknown GT void เป็นคนละเรื่องกับ unsupported predictions และไม่เกิดจาก model masks

## 5. Input, person ownership และ route fairness

Frozen YOLO quality dependency เดิมใช้ imgsz640/conf0.25/NMS IoU0.70/max_det200/retina_masks=True และ original-grid masks/boxes มอง detector settings เป็น declared dependency ของ proposed configurations ไม่ใช่ผลเลือก YOLO ใหม่ ค่า threshold ใหม่ห้ามเปลี่ยนจาก VAL score

**Native3:** full-frame RGB → native preprocessing/TTA/internal detector หรือ human queries → native per-person assembly → (application only) association กับ YOLO predicted boxes ที่ IoU≥0.50 แบบ one-to-one, maximum eligible cardinality ตามด้วย total IoU และ immutable-ID tie-break ไม่มี GT ใน association เก็บ native IDs และ YOLO opportunity IDs ทั้งสองไว้ Native reference ข้าม YOLO gating แต่ใช้ inference artifacts เดียวกัน ไม่เอา final gated count ไปแทน native count

**QANet:** ใช้ native external-ROI API, RGB, H512×W384, native aspect W/H=3/4 และ expansion1.25, ROI Align + native flip ตาม pinned config ไม่เรียก wrapper นี้ว่า native person detection

**Sapiens ROI proposal:** ใช้ continuous YOLO box → center/aspect3/4/expansion1.25 ตาม QANet geometry → RGB ROI → official preprocessing H1024×W768 → native logits resize กลับ ROI แล้ว argmax → map back original grid Padding ที่ออกนอกภาพเสนอ ImageNet-mean RGB; QANet native ROI sampling ใช้ semantics ของ framework เดิม จึงต้องรายงาน padding/resampler difference และตรวจ geometry ไม่บอกว่าทุกพิกเซล input เท่ากัน ยังไม่มี actual Sapiens YOLO-crop evidence

ROI parsers ไม่ hard-mask RGB ก่อนรัน Post-parse ตัด semantics ด้วย YOLO instance mask เพื่อ target ownership แต่เก็บ unowned output/extent และ clipping statistics ด้วย Policy อาจตัด clothing regions ที่ YOLO พลาด ต้องนับเป็นข้อจำกัดระบบ ไม่อ้างว่าทั้งหมดเป็น parser error Native-associated routes คง native masks ไม่ clipping เพิ่มโดยอัตโนมัติ จึงเป็น configuration comparison ไม่ใช่ architecture-only experiment

Native M2FP/D2FP full-frame output มี semantic scores + human/part masks การประกอบ hard per-person labels ตาม human ownership/global semantics สอดคล้อง pattern upstream แต่ต้องทดสอบ tie/overlap parity และแยก human confidence จาก official parsing confidence RP-R-CNN retain internal Faster R-CNN, ROI parsing และ native postprocess ไม่ bypass detector เพื่อลดเวลา

Keep overlapping predictions as separate person planes สำหรับ instance metrics ไม่ flatten irreversibly Global semantic diagnostic ใช้ higher final-person score priority ภายในระบบเดียว ties ใช้ immutableID ไม่เปรียบเทียบ calibration ข้ามระบบ Empty semantic map กับ nonempty YOLO opportunity ยังเป็น valid parser output: localization extent คง YOLO source, semantic quality อาจ 0 ไม่แปลงเป็น failure เพื่อหนีคะแนนต่ำ

### Native settings ที่ต้อง bind ก่อน launch (ไม่ใช่ VAL tuning)

| Checkpoint/config family | Native settings จาก source/config ที่อ่าน | ขอบเขตความมั่นใจ |
|---|---|---|
| M2FP/D2FP CIHP | RGB, short-edge640; configured TTA640/max2048/flip; human score>0.1, human-mask logit>0; semantic paste threshold0.3 และ score-weighted probability>0.5 | Pinned source/config และ actual native TRAIN route ตรงกัน ต้อง capture resolved runtime config และควบคุม OOM fallback ใน B |
| QANet HRNet-W48 CIHP | RGB ImageNet means/std; TEST.SCALE=[384,512] คือ W384/H512; ROI aspect3/4/expansion1.25; H_FLIP=True; source defaults parsing score0.01/pixel0.2/semseg0.3/NMS0.6 | คง native TestEngine path ที่ผ่าน TRAIN ไม่เพิ่ม detector หรือสรุปว่าแต่ละ field ถูกใช้ทุก branch โดยไม่ตรวจ route |
| RP-R-CNN CIHP R50 | BGR/caffe means[102.9801,115.9465,122.7717], std1; resize short800/max1333; detector score0.05/NMS0.5/top100; parsing threshold0.001/semseg0.3 | Retain internal detector/ROI decoding; optional augment ที่ comment ใน YAML ไม่เท่ากับเปิดใช้งาน; dump actual profile ใน B |
| Sapiens2 สามขนาด | Native ImageNet preprocessing, H1024/W768, official resize and original-coordinate logits resizeก่อน argmax; no new confidence cut | Existing full-frame evidence; new crop/affine route และ joint-residency ยัง NOT_TESTED |

Framework ที่เคยผ่าน inference: CIHP4 ตัว PyTorch1.10.2+cu113 ใน isolated legacy profile; Sapiens pilot PyTorch2.14.0+cu130 Source revisions/compatibility records อยู่ใน registry/run evidence ไม่มีการ import/model load ใหม่เพื่อรับรอง environment ปัจจุบันใน A หาก framework คนละรุ่นให้ใช้ isolated workers ตาม actual dependency ไม่ติดตั้งรวมใน YOLO environment

## 6. Metrics ที่เสนอและสูตร

### 6.1 Matching และตัวหาร

Final prediction↔GT matching ใช้ **person-mask IoU** ที่ 0.50 หลัก/0.75 เสริม ไม่ใช่ bbox IoU และไม่เรียกว่า parsing AP ให้ G_i เป็น Human_ids region ของ GT คน i; P_j เป็น native human extent หรือ frozen YOLO instance extent สำหรับ ROI system ซึ่งเก็บแยกจาก semantic-success mask ใช้ eligible maximum-cardinality one-to-one แล้ว total IoU แล้ว deterministic IDs

สำหรับ M2FP/D2FP ใช้ human ownership mask จาก native queries ก่อน semantic-label composition; RP-R-CNN ไม่มี independent human-silhouette head ใน output ที่เก็บ จึงใช้ union ของ native non-background per-person parsing labels และไม่สร้าง filled-bbox mask มาทดแทน ส่วน ROI systems ใช้ frozen YOLO mask โดยไม่ผูก extent กับ semantic nonempty เงื่อนไขนี้เป็นความต่างของระบบที่ต้องแสดง ไม่แปลทุก localization failure ว่า detector ผิดเพียงอย่างเดียว

G_loc = จำนวน eligible native GT persons; TP = matched pairs; FN = G_loc−TP; FP = predicted persons−TP precision=TP/(TP+FP), recall=TP/G_loc, F1=2TP/(2TP+FP+FN) กรณีไม่มี predictions แต่มี GT precision=N/A (0 denominator), recall/F1=0 และ valid empty execution ส่วน empty population ไม่สร้างเลข 0 แทน N/A

ไม่ทิ้ง GT ที่ไม่มี target semantics จาก localization denominator G_sem(view) ที่ไม่มี valid target support ไม่ได้รับ semantic score แต่ยังเป็น personcoverage target Predict duplicates เป็น FP; swapping ID strings อย่างเดียวไม่ผิดเพราะ matching ใช้ geometry; transferring regions ไปคนผิดทำให้ mask/semanticownership เสีย

### 6.2 Primary: coverage-aware person-macro target IoU

สำหรับ GT คน i ที่มี targetpixel ให้ K_i = target classes ที่ปรากฏใน GT_i หรือ matched P_i; union0 ไม่เข้าค่าเฉลี่ย ไม่มี classes ว่างทั้งสองฝั่งที่เพิ่มคะแนนฟรี

`q_i = mean_{c in K_i} |GT_ic ∩ Pred_ic| / |GT_ic ∪ Pred_ic|`

`Q_person_sem_GT(view) = sum_i q_i / G_sem(view)`

Unmatched GT มี q_i=0 Valid GT pixels ของคนอื่นเป็น background/context เมื่อประเมิน target คน i จึงลงโทษ neighbor contamination Shared void recipe เหมือนกันทุกระบบ ไม่ใช้ GT เพื่อ clip prediction Unresolved predicted class บน GTtarget ลด intersection/เกิด FN ตามจริง คง rejection/error column ใน confusion ไม่ถูก ignore

Matched-only person mIoU รายงานแยกเป็น conditional metric พร้อม matched/G_sem ไม่แทน primary ที่รวม missedpersons Primary quality ไม่ลงโทษ unmatchedFP ด้วยตัวหารใหม่ที่แต่งทีหลัง จึงต้องแสดง mask precision/recall/F1 และ FP พร้อมกันและใช้ใน selection/Pareto เฉพาะ task/route เดียวกัน

### 6.3 Secondary และ support

Global per-class IoU สะสม TP_c/FP_c/FN_c ทั้ง population ก่อนคำนวณ `IoU_c=TP_c/(TP_c+FP_c+FN_c)` macro mIoU เฉลี่ย targetclasses ที่ support ได้และรายงาน class count คงที่ ไม่เรียก mean per-image/person ว่า metric เดียวกัน BG/context มีใน confusion เพื่อให้ falsepositive บน context ถูกลงโทษ แต่ไม่รวม BG ใน foreground macro ทุก target ของ primaryview มี GTsupport; union0=N/A พร้อม counts ไม่ให้ 1 หรือ 0 โดยไม่มีคำอธิบาย Pixel accuracy เป็น secondary เพราะ background dominance

รายงาน class pixel/person/image supports, per-class recall, masked contamination ratio (predicted labeled area ของคน j ที่ตกใน GT คนอื่น / predicted labeled valid area), prediction collision area และ source-opportunity completion แยก stage/numerator/denominator GT ใช้วัด contamination ใน scorer ได้ ไม่ช่วย prediction No YOLO opportunities → SKIPPED_BY_ROUTING, opportunity rate=N/A, finalpersons0 แต่ GTcoverage ยังรับ FN

Boundary IoU เป็น supplementary tight-mask diagnostic เมื่อจับคู่ได้: inner boundary `B_d(M)=M−erode(M,d)`, `d=max(1,round(.02*sqrt(H²+W²)))`; boundary intersection/union บน original-image grid ตัด fixed GTvoid-neighborhood ออกเหมือนกันทั้งระบบเพื่อไม่สร้างขอบปลอม ต้องเรียกว่า **study void-aware adaptation**, ไม่ official CIHP/COCO Boundary AP และ matched-only ต้องแสดง coverage ไม่มี AP^p/AP^p_vol/PCP headline ในแผนนี้ เพราะ GT/taxonomy/confidence/metric ไม่ใช่ officialnativeCIHP หากเพิ่มภายหลังต้องพิสูจน์ definition และ parity แยก

### 6.4 Completeness

STRICT_COMPLETE ต่อ configuration×population×view: ถ้า eligible input ใด FAILED/INVALID/UNRESOLVED/NOT_ATTEMPTED ให้ primarymetrics null และแถว INCOMPLETE อยู่ครบ ไม่ average เฉพาะ successfulimages เป็น main score หากล้มเหลวนอก main อย่างเดียว main อาจครบแต่ reference ยัง INCOMPLETE membership ไม่เปลี่ยนตามผล

Frame COMPLETE เมื่อทุก requiredROI ของ frame มี validpacket Valid empty output คือ success; load/OOM/invalidgeometry เป็น failure Shared data/contract errors หยุด dependentjobs Individualfailure คง diagnostics และทำงานอิสระต่อภายใต้ stopcaps Retry0 ไม่มี CPU/FP16 fallback เงียบ ๆ หลัง processinterruption resume ได้เฉพาะ never-attemptedjobs ด้วย frozenfingerprints และ explicitcontinuationdecision ไม่ซ่อม failedimages หรือ overwritepartialevidence

## 7. Runtime/VRAM proposal

ใช้ Tesla T4 GPU ที่ assigned, learnedparameters/logits FP32, autocast=False/TF32=False NativeSapiensRoPE มี internalsdtype ของผู้สร้าง ให้ label `FP32_PARAMS_NATIVE_INTERNAL_OPS` ไม่อ้าง strict-all-ops-FP32 หรือเปลี่ยน precision เอง รันทีละ configuration ไม่มี concurrentGPUcompute

| Profile | Included | Excluded / units |
|---|---|---|
| Parser component ใน application | Nativeparser preprocessing, transfers, forward, TTA, postprocess แยก stage; nested timers ใน route จริง | ไม่ใช่ standalone resource profile; ms/person-ROI สำหรับ QANet/Sapiens, ms/frame สำหรับ native3 |
| Native reference3 | Full-frame nativeparser อย่างเดียว รวม internaldetector/native assembly | ไม่มี YOLO model resident; ms/image |
| Full application7 | RGB ใน RAM→freshfrozenYOLO preprocess/forward/postprocess→IPC/crops→parser→association/map-back/composition | แยก modelinit, diskread/JPEGdecode, scoring, export/write/visualization; ms/frame และ FPS=1000/mean route ms เฉพาะ RAM-inputscope |

Quality ใช้ cachedYOLO ได้ แต่ runtime ต้อง freshYOLO บน workload เดียวกัน Cache read ไม่ใช่ detector inference และเวลา MOTS20 เดิมไม่ใช่ค่า route นี้ Primaryresourceprofile ให้ YOLO+parserco-resident แม้ต่าง Python/CUDAframework ต้องแยก workerprocess และรวม IPC ไว้ ไม่มี simultaneouscompute ถ้า 1B หรือ config ใด co-residentOOM คง candidate พร้อม profilefailure ไม่สลับ offload/unload/FP16 โดยเงียบ; sequential-residencyalternative ต้องเป็น configuration แยกอนุมัติใหม่

[Fixed timing draft](manifests/TIMING_WORKLOAD_DRAFT.json): 64mainimages, 8 จากแต่ละ stratum opportunity count {0–2,3–4,5–7,8+} × imagearea≤187,500/>187,500; เลือกด้วย smallestSHA256(seed:image_id), seed20261021 ก่อนดู parser quality/runtime มี 350YOLOopportunities ไม่ใช่ representativeunweightedsample รายงาน per-stratum และ population-weightedmean; P50/P95 ของ balancedfixedworkload ไม่ใช่ populationquantiles

3cleanrounds ต่อ configuration, warmup5fixedframes ต่อ round ไม่นับเวลา, effectivebatch1frame/1sequentialROI รักษา nativeTTA และ resolution Roundorder ใช้ seededconfigurationorder และ cyclicrotation; shuffleframeorder จาก frozenseed ต่อ round Modelreload/GC/allocatorreset, GPUidleness/driver/environmentcaptured ก่อน round CUDA synchronize รอบ GPUstage และ hostmonotonic ครอบ full route รวม IPC ไม่ใช้ sumcomponentmeans แทน full route เวลา

Memory รายงาน per-process peakallocated/peakreservedMiB หลัง reset พร้อม residentweights; device-wideusedMiB sampled50ms รายงาน absolute/idlebaselinedelta **sampled peak** อาจพลาด spikes ห้าม sumprocesspeak เป็น simultaneousroutepeak RoutePareto ใช้ actualroutelatency และ device-sampledpeak ของ profile เดียวกัน Native-referencePareto แยกจาก application Modelparameter/checkpointsize เป็น complexity ไม่ใช่ deploymentVRAM

## 8. Selection rule ก่อนดูผล

นี่คือ relative checkpoint selection บน publicselection set ไม่ใช่ผ่านเกณฑ์ใช้งาน CCTV ยังไม่มี absoluteIoU/FPSacceptancethreshold ที่มีหลักฐานจาก requirements จึงไม่แต่งเลขผ่าน/ตกโดยอ้างว่าวัดมาแล้ว

Eligibility: acceptedtask/support/configbindings, readableinput/domainexact, STRICT_COMPLETEquality, nativeprecisionprofile ที่ประกาศ ทุก candidate/failure คงในตาราง Runtimeprofile ต้อง complete จึงเข้าตาราง cost/Pareto; qualitycomplete แต่ timingfail ให้แสดง quality ได้พร้อม resource-unavailable ไม่ลบคนละระบบเพื่อให้ครบ

ต่อ task และ route เดียวกัน เลือก bestobserved Q_person_sem_GT พร้อม per-class IoUs และ maskprecision/recall/F1 แยก C3allcandidates จาก C7compatiblecohort ไม่เลือก universalbody/clothingwinner ด้วย C3 เพียงอย่างเดียว รักษาระบบที่ non-dominated ใน **quality / instanceF1 / routelatency / routeVRAM** โดยไม่มี weightedscore หากขัดกันให้เก็บ suitableconfigurations หลายตัวตาม objectives ไม่ใช้ modelsize หรือ version ตัดสินแทนผล

เสนอ practicalnear-tie `|ΔQ|≤0.005` หรือ paired95%interval คร่อม 0 เป็น descriptiveflag ไม่ equivalence/statisticalsignificance ค่านี้เป็น proposedpracticalmargin ไม่ใช่ threshold จากการทดลอง ทำ pairedclusterbootstrap1,000resamples โดย knownexactdecodedRGBgroups (seed20261021), resampleclusters พร้อมทุก members แล้วคำนวณ ratioestimands ใหม่; unknownnear-duplicates/trainingexposure ยังจำกัด interpretation

Smallestlatency/memory ใช้เลือกภายใน near-tie เมื่อ runtimeevidencecomplete และ noimportantper-classregression โดยรายงานทุก trade-off ไม่สร้าง post-hocweightedwinner ถ้าต้องการ singledeploymentchoice หรือ absolutequality/resourcefloors ผู้ใช้ต้องกำหนดก่อนดู VAL; การรับ design ไม่ใช่อนุมัติ benchmark

## 9. Exact workload, resources และสิ่งที่ยังวัดไม่ได้

[Workload proposal](manifests/WORKLOAD_PROPOSAL.json) เป็น machine-readablecounts ไม่ใช่ jobs ที่อนุมัติ:

| งาน | Proposed count / basis |
|---|---:|
| Checkpoints / configurations | 7 / 10 |
| Quality parser frame-system jobs | 35,000 =7×5,000 |
| Native full-frame parser jobs | 15,000 =3×5,000; native-reference reuse ผล |
| ROI system frame dispatches | 20,000 =4×5,000 |
| ROI tasks | 96,248 =4×24,062; ไม่ใช่ neuralforwardcalls |
| New YOLO quality jobs | 0; reusefrozenartifacts หลัง dependencycheck |
| Timed application frame jobs | 1,344 =7×64×3; freshYOLO1,344jobs ใน routes เหล่านี้ |
| Timed native-reference frame jobs | 576 =3×64×3 |
| Timed ROI tasks | 4,200 =4×350×3; nestedcomponenttiming ไม่เพิ่ม passes |
| Warmup | 150configuration-framejobs; freshYOLO105jobs; ROI120tasks; excludedfromtimedstats |
| Ranked summary rows | 68 =(10C3+7C7configs)×2populations×2matchingthresholds; ไม่รวม diagnostic/per-classrows |

Readiness ใหม่จำเป็นเฉพาะ gaps: replayexistingTRAINpackets/scorercontexts ของ CIHP4 โดย CPU; ตรวจ actualSapiens ROIpath สูงสุด 3fixedTRAINimages ต่อ checkpoint (initial1 แล้ว 2 ถ้าผ่าน) =≤9frame-systemchecks และจำนวน ROIs ตาม frozenTRAINdetectoroutputs; ต้องอนุมัติ StageB แยก ห้ามรันเพื่อเติม report ใน A Jointresidency/device/fallbackchecks ต้องเป็น boundedTRAIN ก่อน VAL timing ไม่ต้อง smoke ทั้ง inventory ซ้ำ

Disk จาก existingmetadata: sumH×W=876,659,024; opportunity-weightedsumH×W=4,217,500,127 การเก็บ nativeunowned+finalowneduint8fullgrid ของ ROI 4 ระบบมี payload33,740,001,016bytes ก่อน headers/compression ไม่ใช่ totalstudyestimate Nativepredictedpersoncount/logit/caches ต่างกันยังไม่ทราบ ต้อง sampleartifactbytes ใน B แล้วคำนวณ bound ใหม่ ไม่สร้าง compressionfactor หรือ ETA เอง

เสนอ reserve200GiB, stopfree<50GiB, cap80GiB ต่อ system/24h ต่อ checkpoint ขณะตรวจ free ประมาณ 564.2GBdecimal(~525GiB) caps เป็น engineeringstoplimits ไม่ใช่ ETA และอาจทำให้ INCOMPLETE ไม่ลบผลเก่าเพื่อให้พอ ไม่มี newdownloads ใน scope นี้

Keepnativehardmasks/ownership/sourceIDs/scores/transforms และ finalpackets ที่ replayscoringdefinition นี้ได้; full float logits ไม่เก็บทั้ง VAL โดย default เพราะ hard-remapprimary และ diskcost ไม่อ้างว่าสามารถทำ probabilityaggregationre-score ภายหลังได้หากไม่มี probabilities เก็บ content-addressedartifacts ภายนอก Git, compactmanifests/ledgersummaries/metrics ใน Git ตาม artifactpolicy

## 10. Gates, readiness และ terminal states

MUST_FIX ก่อน launch: acceptproposedroster/task/selectionrules; new GT/viewmaskcontexts; checkpoint-specificsupport; maskmatching และ rejection-awareconfusion จริง; native assemblyparity; ownership/map-back; Sapiens ROIintegration; nohiddenfallback; full route joint-residency/runtime boundaries; immutableledger/manifestreconciliation

StageBtargetedfixtures: perfect/wrongclass, absent/zerounion, validempty/missing/duplicate, arbitraryIDswap versuswrongphysicalownership, overlappingpersons, C22/C0H+/C+H0, unexpectednativeID, Dress/Apparelrejection, crop/padding/rounding/fliprestore, bboxassociationversusmaskmatching, stage-rateundefined/skipped, OOM/internalretry/devicefallback, partialpacket/resume-only-unattempted Sharedfixtures ต้อง exerciseactualimplementation ไม่ใช่ referencepseudo-code เท่านั้น

States ของงาน: PROPOSED → ACCEPTED_DESIGN → IMPLEMENTATION_READY → LAUNCH_READY → USER_APPROVED_EXECUTION → RUNNING → FINISHED_COMPLETE / FINISHED_WITH_INCOMPLETE_SYSTEMS / STOPPED_RESOURCE / INVALID_SHARED_DATA พร้อม per-configuration COMPLETE/FAILED/INVALID/NOT_ATTEMPTED ไม่ใช้ oneREADYflag แทนโหลดโมเดล/route/scoring/runtime ทั้งหมด

A จบที่ REVIEWED_PROPOSAL จน userdecisions สำคัญปิด B จบที่ readiness+exactlaunchpackage; C เริ่มเฉพาะ explicitapprovedbatch; D วิเคราะห์ตาม frozenrules และ selection setdesignation ไม่กลับไป tune หรือเปิด CCTV/attributes เอง

## 11. การตัดสินใจที่ต้องการจากผู้ใช้ — รวบรวมครั้งเดียว

1. **Scope:** รับ 7checkpoints/10configurations ที่เสนอจากตารางเดิมหรือแก้รายชื่อ? แนะนำรับชุดนี้ ไม่มี inventoryvariants เพิ่มเติมและไม่ rerunCPI; เปลี่ยนรายการมีผลต่อ bindings/jobs ไม่ใช่ผลความแม่นที่วัดแล้ว
2. **Tasks:** รับ C3 upper/lower/shoes ร่วมกัน และ C7 body/clothing เฉพาะ compatibleCIHPcohort พร้อม Sapiens bodydiagnostic แยกหรือไม่? แนะนำแบบนี้เพื่อไม่ทำ Face_Neck/Torso เป็น exact โดยไม่มีหลักฐาน Accessories ยัง supplementary; ถ้ามี namedmandatoryaccessory ให้ระบุตอนนี้เพราะเปลี่ยน eligibility จริง
3. **Selection:** รับ relativequality+instancecoverage และ Pareto โดยไม่มี arbitraryabsolutefloor พร้อม near-tie0.005 และหลาย suitableconfigurations หรือมี minimumquality/FPS/VRAM ที่ต้องกำหนดก่อนผล? แนะนำ relativecomparison ก่อนเพราะยังไม่มี fieldvalidatedpasscriteria; ไม่เรียกว่า CCTVready

ตัวเลือกเหล่านี้เป็น designacceptance เท่านั้น ไม่อนุมัติ StageBnewGPUchecks หรือ StageCbenchmark ค่า engineering/timingdefaults ใน spec เป็นข้อเสนอที่ตรวจต่อใน B การอนุมัติ launch ต้องแยกจาก DESIGN_READY
