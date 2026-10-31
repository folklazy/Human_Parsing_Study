# ตรวจผล CCTV 90 ภาพ: ทำไมไม่มี full-image IoU และวัดอะไรย้อนหลังได้จริง

สถานะ: **AUDIT_PASS_WITH_GT_SCOPE_LIMITATION** · Run `cctv-partial-20261031T1800Z` · Protocol เดิม `CCTV_PARTIAL_TARGET_RECALL_V1`

## คำตอบหลัก

**ทั้งเก้า parsing configurations รันครบจริงตัวละ90ภาพ แต่รอบนี้เป็น partial-annotation benchmark** ตามคำยืนยันเดิมของผู้ใช้ว่า annotate “เลือกเฉพาะบางคนหรือบางส่วน” และยังไม่มีกติกา Dress ที่ชัดเจน Scorer จึงตั้งใจรายงาน recall บน pixels ที่ทราบ label และเว้น full-image IoU/precision/person F1 เป็น null ไม่ได้เป็นเพราะไม่มี prediction masks หรือโมเดลรันไม่สำเร็จ

ควรแยกสามเรื่องออกจากกัน:

1. **สูตร metric:** IoU, Dice, precision และ recall คำนวณได้ตามนิยามมาตรฐาน
2. **GT domain:** ตัวเลขจะหมายถึงพื้นที่ใด และพื้นที่ที่ไม่มี annotation ใช้เป็น negative ได้หรือไม่
3. **ความครบของ execution:** รันครบ90ภาพ ไม่ได้ยืนยันว่า annotation ครบทุกคนและทุกส่วนของ90ภาพ

การอธิบายว่า “ไม่มีทางคำนวณ IoU เลย” จะกว้างเกินไป ข้อมูลเดิมมี confusion matrix เพียงพอให้คำนวณ **IoU เฉพาะพื้นที่ที่มี target annotation** ได้ รายงานนี้จึงเพิ่มการตรวจเลขดังกล่าวเป็น **post-hoc diagnostic แยกจากผล canonical** ไม่เปลี่ยน primary metric ไม่ปรับ mapping/settings และไม่รันโมเดลใหม่

## 1. ตรวจอะไรจริงในรอบนี้

| สายหลักฐาน | สิ่งที่ตรวจ | ผลและขอบเขต |
|---|---|---|
| Protocol/config | อ่าน source `partial_confusion` และ `summarize` พร้อม frozen config/source hashes | Domain จำกัด GT native2/5/9/13; null ของ full-image metrics ถูกกำหนดโดยตั้งใจ |
| Population/ledger | ตรวจ expected IDs กับ FRAMES และ packet directories ของ9ระบบ | ระบบละ90 IDs ไม่ซ้ำ ไม่มี missing/partial/orphan packet directory ใน accepted view |
| GT bindings | เทียบ hashes ของ Category/Human/Instance maps และ canonical annotation JSON รวม360ไฟล์กับ launch bindings | ตรงทั้งหมด; ใช้ audit support เดิมต่อ ไม่ re-audit dataset/weights ทั้งโครงการ |
| Saved scoring | ตรวจ atomic hashes ของ score/metadata810packets แล้วบวก histograms รายภาพแยก overall/day/night | ตรง canonical METRICS ทุกระบบ; GT support ต่อภาพตรงกันข้ามโมเดล |
| Saved native masks | อ่าน NPZ/atomic hashes และ replay compose→project→partial scorer อย่างละ1packet ของ QANet, CPI ConvNeXt-B และ Sapiens0.4B ตาม first frozen member | ทั้ง3ตัวอย่างตรง saved scoring; ไม่อ้างว่า rehash NPZ ครบ810ไฟล์ใหม่ |
| สูตร diagnostic | ใช้ fixture นับมือที่ IoU=(0.5,0.25,1,0), Dice=(2/3,0.4,1,0) และตรวจ null เมื่อไม่มี predictions | ผ่าน; ตรวจ arithmetic ไม่ใช่ semantic QA ของ annotations |
| Process | ตรวจ PID เดิมของ controller/worker และ terminal record | งานเดิมหยุดแล้ว; ไม่มีการเปิด inference/retry ใหม่ |

รายละเอียด hashes และขอบเขตตรวจ: [METRIC_AUDIT_EVIDENCE.json](METRIC_AUDIT_EVIDENCE.json) ส่วน utility สำหรับตรวจซ้ำจาก artifacts คือ [audit_saved_metrics.py](../scripts/audit_saved_metrics.py) ซึ่งไม่โหลดโมเดล ไม่แก้ GT และไม่เขียนทับ canonical run

## 2. Annotation ที่มีจริงและเหตุผลที่ GT0 ยังไม่เป็น negative

| รายการ | จำนวน/สถานะ |
|---|---:|
| ภาพจริง | 90: day48 / night42 |
| ขนาดภาพ | 87ภาพ1920×1080, 2ภาพ2688×1520, 1ภาพ1280×720 |
| Person-image records ที่มี annotated parts | 127; ไม่ได้ยืนยัน127บุคคลจริงที่ไม่ซ้ำกันข้ามภาพ |
| Face pixels | 54,044 |
| Hair pixels | 246,971 |
| Upper pixels | 892,697 |
| Lower pixels | 374,543 |
| Known annotated target pixels รวม | **1,568,255** |
| Pixels ของภาพทั้งหมด | 189,496,320 |
| Known target annotation / pixels ทั้งหมด | **0.827591%** |
| GT0 ภายใต้ policy ปัจจุบัน | 187,928,065 pixels: UNKNOWN |

**0.83% ไม่ได้แปลว่า annotation ทำเสร็จเพียง0.83%** คนอาจมีขนาดเล็กและฉากหลังอาจมีพื้นที่มากจริง ตัวเลขนี้บอกสัดส่วนพื้นที่ target ที่มี label เท่านั้น เหตุผลที่พื้นที่0ยังเป็น UNKNOWN มาจากคำยืนยัน partial scope และการไม่มี reviewed negative-domain specification ไม่ใช่จากสัดส่วนพื้นที่เพียงอย่างเดียว

Source conversion ที่ `scripts/ingest_cctv_poc_dataset.py` เริ่ม category/human/instance masks ด้วยศูนย์ แล้วระบาย polygons ที่ได้รับ ดังนั้นการพบ0ในPNG ไม่ได้พิสูจน์ว่ามนุษย์ตรวจทุก pixel นั้นแล้วว่าเป็น background ในขอบเขตที่ annotate เพียงบางคน/บางส่วน พื้นที่0อาจรวมฉากหลัง คนที่ไม่ได้เลือก หรือส่วนที่ยังไม่ระบุ

Human_ids เป็น union ของ parts ที่ annotate ไม่ใช่ full visible-person silhouette จึงยังใช้เป็น full-person extent GT เพื่ออ้าง person-mask F1/AP ไม่ได้ นอกจากนี้ global semantic agreement ไม่ตรวจจับการผูก masks กับ Person ID ผิดทุกกรณี

## 3. ทำไมรายงานเดิมมี recall แต่ไม่มี full-image IoU

Recall ตอบว่า **“จาก pixels ของ target ที่รู้คำตอบแล้ว โมเดลทายถูกกี่ส่วน”**:

$$Recall_c=\frac{TP_c}{TP_c+FN_c}$$

ส่วน IoU ต้องมี FP ด้วย:

$$IoU_c=\frac{TP_c}{TP_c+FP_c+FN_c}$$

หากโมเดลทาย Upper บนเสื้อของคนที่ไม่ได้ annotate การนับ pixel นั้นเป็น FP จะลงโทษคำตอบที่อาจถูกจริง แต่ถ้า ignore pixels นอก annotations ทั้งหมด ก็จะไม่ลงโทษโมเดลที่ทายล้นไปบนฉากหลังที่ยังไม่ได้รับรอง negative ดังนั้นยังอ้าง **full-image** precision/IoU ที่ระบุความผิดถูกครบพื้นที่ไม่ได้

สูตร IoU เป็น intersection/union ตาม [เอกสาร Jaccard ของ scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.jaccard_score.html) และ [TorchMetrics](https://lightning.ai/docs/torchmetrics/stable/classification/jaccard_index.html) ส่วนการเลือก valid/ignored domain เป็นข้อกำหนดของข้อมูลและ protocol โครงการ ไม่ใช่ข้อห้ามสากลว่าทุกงานที่มี ignore pixels จะใช้ IoU ไม่ได้

ใน source จริง:

- `partial_confusion` ใช้ `known = gt > 0` หลัง map GT2/5/9/13 ไป Hair/Upper/Lower/Face
- `summarize` คำนวณ recall4 และ annotated-pixel accuracy แล้วกำหนด `full_image_mIoU=None`, `full_image_precision=None`, `person_extent_F1=None` พร้อมเหตุผล
- Reporter/finalizer ส่งค่าตาม scope นี้ต่อเป็นช่องว่าง/null ไม่ได้แทนคะแนนที่หายด้วย0

นี่เป็นการวัด partial-label diagnostics ที่ตั้งใจไว้ และต้องเรียกชื่อตามนั้น การให้ recall เป็น primary มี blind spot เรื่อง over-segmentation จึงไม่พอใช้เลือกผู้ชนะ deployment โดยรวม

## 4. IoU/Dice ที่คำนวณย้อนหลังได้ — domain ต้องอยู่ในชื่อ

กำหนด domain เดิมเหมือนกันทุกระบบ:

$$D=\{x:GT_{native}(x)\in\{2,5,9,13\}\}$$

ใช้ saved confusion matrix $h$ ที่บันทึกเฉพาะ pixels ใน $D$ โดย rows เป็น GT และ columns เป็น BG/Face/Hair/Upper/Lower/OTHER สำหรับ target $c$:

$$TP_c=h_{cc},\quad GT_c=\sum_jh_{cj},\quad Pred_{c,D}=\sum_ih_{ic}$$

$$FP_{c,D}=Pred_{c,D}-TP_c,\quad FN_{c,D}=GT_c-TP_c$$

$$IoU_{c,D}=\frac{TP_c}{GT_c+Pred_{c,D}-TP_c},\qquad Dice_{c,D}=\frac{2TP_c}{GT_c+Pred_{c,D}}$$

`mean_IoU_known_annotation_domain` คือค่าเฉลี่ย IoU ของ4targets หลัง aggregate confusion ทั้ง population ไม่ใช่เฉลี่ย IoU native classes หรือเฉลี่ยเปอร์เซ็นต์รายภาพ ส่วน `precision_in_D` เป็นความแม่นภายใน $D$ เท่านั้น ไม่ใช่ความแม่นทุก predicted pixels

การทาย target ผิดชนิดบน known pixels นับเป็น FN ของ GT class และ FP_D ของ predicted class; การทาย BG/OTHER บน target นับ FN แต่ predictions นอก $D$ ยังไม่มีทั้งเครดิตหรือโทษ ภาพที่ทายล้นนอก annotation จึงอาจไม่เสียคะแนน ตัวเลขนี้ไม่ใช่ full-mask boundary quality, full-image IoU หรือ independent confirmation

### ผลรวมทั้งเก้าระบบ — frozen roster order

| Configuration | Complete | Macro recall4เดิม % | mIoU เฉพาะknown annotation domain % | Mean Dice บนdomainเดียวกัน % |
|---|---:|---:|---:|---:|
| QANet_CIHP_HRNetW48_512x384 | 90/90 | 82.22 | 79.00 | 88.15 |
| M2FP_R101_CIHP | 90/90 | 77.29 | 75.30 | 85.80 |
| D2FP_R101_CIHP | 90/90 | 70.09 | 68.16 | 80.90 |
| RPR_CIHP | 90/90 | 76.57 | 71.62 | 83.30 |
| CPI_R50_CIHP | 90/90 | 74.63 | 69.46 | 81.82 |
| CPI_ConvNeXtB_CIHP | 90/90 | 80.81 | 77.38 | 87.18 |
| Sapiens2_0.4b | 90/90 | 80.90 | 71.35 | 82.76 |
| Sapiens2_0.8b | 90/90 | 77.77 | 72.39 | 83.80 |
| Sapiens2_1b | 90/90 | 75.45 | 71.73 | 83.38 |

**IoU/Dice สองคอลัมน์ขวาเป็น diagnostic ที่คำนวณหลังเห็นผล ไม่ใช่ primary ของ frozen run** QANet สูงสุดในตัวเลขรวมเหล่านี้ แต่ยังไม่รับรองว่าเป็น parser ที่ดีที่สุดบน CCTV ทั้งภาพ เพราะไม่วัด FP นอก $D$, ownership ทั้งหมด หรือความครบทุกคน

ไฟล์ full precision แยก overall/day/night: [KNOWN_DOMAIN_DIAGNOSTICS.csv](../metrics/KNOWN_DOMAIN_DIAGNOSTICS.csv) ส่วน TP/FP_D/FN/support/union และ IoU/Dice/precision/recall ราย target: [KNOWN_DOMAIN_PER_TARGET.csv](../metrics/KNOWN_DOMAIN_PER_TARGET.csv) ภาพต่อกลุ่มจริงคือ90/48/42; `complete=90` ใน CSV เดิมหมายถึงความครบระบบ ไม่ใช่จำนวน day หรือ night images

### ตัวอย่างที่แสดงข้อจำกัดของ recall อย่างเป็นรูปธรรม

Sapiens0.4B มี Face recall **86.05%** แต่บน known domain มี TP46,506, FN7,538 และ FP_D27,093pixels จึงได้:

$$IoU_{Face,D}=\frac{46{,}506}{46{,}506+7{,}538+27{,}093}=57.32\%$$

FP_D ดังกล่าวมาจาก pixels ที่ GT เป็น Hair3,007 / Upper18,369 / Lower5,717 แต่ prediction เป็น Face ส่วนนี้เป็นข้อผิดพลาดตาม projection/reference ที่ใช้อยู่จริง อย่างไรก็ตาม ยังแยกสาเหตุเป็น segmentation error, Face_Neck proxy incompatibility หรือ annotation boundary issue ไม่ได้จาก confusion เพียงอย่างเดียว จึงไม่เดาสาเหตุแทนการตรวจภาพ/GT

Face_Neck ยังเป็น proxy และ Upper/Lower ยังไม่มีกติกา Dress ที่ยืนยันแล้ว ผลนี้เป็น checkpointพร้อมapplication route comparison: QANetใช้YOLO ROI, Sapiensใช้full-frame+YOLOownership และnativeinstanceparsersใช้YOLOassociation ไม่ได้แยกarchitecture/training/adapter effects

## 5. พบ IoU ในผลเก่าจริง แต่เป็นคนละการประเมิน

ใน `datasets/CCTV_100_Evaluation/results/` มี exploratory results ก่อน canonical partial run เช่น M2FP mIoU4=66.91, D2FP=66.30 และ Sapiens1B=53.33 ตาม JSON ที่อ่านได้ สคริปต์เก่า initialize projected GT/prediction เป็น0และใช้ `(gt<5)&(pred<5)` จึงรวมพื้นที่0ที่ยังไม่รับรอง negatives ด้วย แล้วคำนวณ IoU จาก FP/FN บน domain ดังกล่าว

สูตรหารไม่ได้ผิดเพียงเพราะเป็น IoU ปัญหาคือ **สมมติฐานว่า pixels ที่ไม่มี polygon เป็น background ทั้งหมด** ภายใต้ข้อมูลแบบ partial และ route/mapping บางส่วนต่างจาก canonical run จึงห้ามนำตัวเลขเหล่านั้นมาเทียบหรือเติมช่อง full-image IoU ของ run ใหม่

ยังพบ legacy `results/Sapiens2_0.4b.json` และ `results/Sapiens2_0.8b.json` อ่านด้วย JSON parser มาตรฐานไม่ผ่าน (`JSONDecodeError: Invalid escape`) ตรวจพบและเก็บไว้เดิม ไม่แก้ย้อนหลังเพื่อให้ดูเป็น canonical evidence

## 6. จะทำ benchmark มาตรฐานที่ใช้ตัดสินได้อย่างไร

**ข้อเสนอหลัก: ทำ manually reviewed evaluation domain ให้ครบ แล้วใช้ saved predictions เดิมคำนวณ IoU/Dice/precision/recall ภายใน domain นั้น** ไม่จำเป็นต้องเริ่มด้วยการ annotate ทุก pixel ของทั้ง90ภาพใหม่ทั้งหมด

ทางที่แนะนำคือกำหนด shared evaluation ROIs หรือ known-domain masks ที่ตรวจด้วยคนว่าภายในขอบเขตนั้นมี target labels/known negatives ครบ คนหรือส่วนที่ไม่ประเมินต้องเป็น explicit VOID เหมือนกันทุกโมเดล ไม่ใช้ prediction หรือคะแนนเลือก ROI และไม่ใช้ ROI ที่ตัดตาม polygonจนตัด spillover ออกจากการประเมิน

งานที่ต้องปิดให้ตรงคำถามมีดังนี้:

1. ตรวจว่าคน/target ที่เลือกมี contour ครบหรือเป็นเพียง interior scribble/partial polygon; ระบุ visible/absent/unknown/not-annotated ให้แยกกัน
2. รับรอง background/non-target ภายใน evaluation domain และระบุ ignored persons/occluded/uncertain regions ตาม GT-only policy
3. กำหนด Face/Hair/Upper/Lower และ Dress/one-piece boundary ให้สม่ำเสมอ เก็บ derived GT version ใหม่โดยไม่เขียนทับ source เดิม
4. Freeze domain, mapping, denominators และ metric definitions ก่อนคำนวณตารางใหม่ทุกระบบ ด้วย strict same-population completeness
5. Reuse original-grid native masks และ scoring bindings ที่ยังใช้ได้ ไม่มีเหตุให้ inference ทั้งเก้าระบบซ้ำเพียงเพื่อเพิ่ม metric

หากต้องการเฉพาะ **IoU ของ annotated part instances** ก็อาจทำได้โดยยืนยันว่า contours ของ selected instances ครบและกำหนด matching/ignore scope ให้ชัดก่อน แต่ยังใช้ผลแบบ matched/annotated-only ไปอ้าง full-scene false positives หรือ mask AP ของทุกคนไม่ได้

สำหรับ person F1/instance AP/ownership ต้องมี GT person extents และ identity/visibility scope ที่รองรับจริง ไม่ใช้ union ของpartsหรือfilledboundingboxแทนsilhouette ส่วน hard-label IoU/Dice ไม่จำเป็นต้องมี logits; probability metrics/AP ต้องตรวจ confidence และ matching contract เพิ่มตามคำอ้างที่ต้องการ

คำแนะนำเชิง annotation/QA ที่มีอยู่แล้วอยู่ใน [FULL_BENCHMARK_ACCEPTANCE_TH.md](FULL_BENCHMARK_ACCEPTANCE_TH.md) ใช้เอกสารนี้ต่อ ไม่เปิด plan หรือ dataset audit ใหม่ทั้งโครงการ ข้อมูลทางคณิตศาสตร์เพิ่มไม่ได้ชดเชย known-negative evidence ที่ยังไม่มี

## 7. แยกจากงานสีให้ชัด

- ตารางเก้าระบบนี้คือ **human parsing** บน CCTV90ภาพ การวัดหลักเกี่ยวกับ spatial masks
- ผล MLPสี68.73%เป็น **color classification** บน614oracle garment regions ของ CCIHP subset ไม่ใช่คะแนน CCTV90ภาพ โมดูลสีควรมี accuracy/macroF1/confusion และ referenceสีที่เป็นอิสระ; IoUไม่ใช่สิ่งทดแทนคะแนนจำแนกสีของregion
- Legacy CCTV color evaluation เคยใช้ M4=M3 และ M5=M3 และ color-label provenance บางส่วนอาจเกิดจากกฎอัตโนมัติ จึงยังไม่ใช่หลักฐานว่าทดสอบ M5/MLPสีครบ90ภาพกับ independent human color GT แล้ว

## ข้อสรุปสำหรับใช้งาน

ผลรันครบ9/9มีจริงและตรวจ arithmetic/bindings ได้ การขาด full-image IoU เป็นผลจาก annotation scope และการตั้ง metric มิใช่ขาด prediction masks ตัวเลขมาตรฐานแบบ **conditional on known annotation domain** คำนวณจาก artifacts เดิมได้แล้ว แต่ยังไม่ใช่ full-scene benchmark สำหรับเลือก deployment winner ขั้นถัดไปที่จำเป็นคือรับรอง evaluation domain/contours/negative labels ตามคำอ้างที่ต้องการ แล้ว reuse predictions เดิม ไม่ใช่รีบรันโมเดลใหม่

รอบ audit นี้ไม่มี inference, training, retry, label repair, mapping/threshold change หรือการแก้ canonical metrics ภาพ CCTV, source filenames, annotations, per-person records และ bulk masks/logs ยังคงอยู่นอก public Git
