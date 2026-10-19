# Stage 0 — ทบทวน Blockers และข้อเสนอสำหรับตัดสินใจ

วันที่ตรวจ: 2026-10-08 UTC. **REVIEW ONLY — WAITING FOR USER DECISIONS.** รายงานนี้ไม่แก้ `STUDY_STATE.json`, protocol, evaluator, adapter, GT หรือผล YOLO เดิม ไม่อนุมัติดาวน์โหลด/รันโมเดลแทนผู้ใช้ ข้อมูลใหม่เป็นการตรวจ dataset/source และข้อเสนอ มิใช่ parser benchmark results

[หลักฐานการทบทวนและรายชื่อประชากรที่เสนอ](../provenance/STAGE0_BLOCKER_REVIEW_20261008T082918Z.json) เก็บ membership แบบครบถ้วนและผูกกับ manifest/index เดิม ส่วน [Stage 0 validation เดิม](../provenance/STAGE0_VALIDATION.json) คงอยู่ ไม่ถูกเขียนทับ

## A. Independent assessment

ข้อสรุปสำคัญคือ **ยังไม่พร้อม freeze Stage 1 แต่ไม่จำเป็นต้องหยุด model feasibility ทุกอย่าง** ภาพ RGB เสียและ ownership ที่น่าสงสัยขวางการอ้างความพร้อมของ benchmark เต็มชุด แต่สามารถแยก gate สำหรับ smoke test บน 1–3 ภาพ train ที่ตรวจ RGB/GT แล้วได้ หลังอนุมัติ weights/license และการปรับ guard เฉพาะ smoke

สิ่งที่ audit เดิมถูกต้องคือจำนวนไฟล์ การ decode PNG ช่องแรก การรักษา GT แต่ละคนแยกกัน ผล hash ตัวอย่าง RGB เสีย และการไม่อ้าง SMOKE_PASS จาก imports การแยก native/crop cohorts เหมาะสมกับสถาปัตยกรรมที่ต่างกัน

สิ่งที่ควรแก้ในการตีความ:

- “ไม่มี nvcc” เป็นข้อจำกัดของการ build source บางโมเดล ไม่ใช่หลักฐานว่า parser ทุกตัวรันไม่ได้ CPI มี official binary MMCV ops ให้ตรวจเส้นทางติดตั้งก่อน
- “มีแต่ face/hair ที่เป็น common classes” เป็นข้อเสนอเบื้องต้นที่เข้มเกินไป ไม่ใช่ข้อเท็จจริงที่พิสูจน์แล้ว matrix เดิมยังมี Pants, Skirt, Dress แบบ EXACT ใน source ของทุก candidate ที่มีสิทธิ์เข้าร่วม อย่างไรก็ตาม ชื่อ/label IDs ตรงกันยังไม่พิสูจน์ขอบเขต annotation ตรงกัน ต้องทบทวนเสื้อผ้าเหล่านี้ก่อนเลือก core
- “652 ภาพซ้ำ” ต้องระบุว่า RGB ซ้ำ ส่วน GT ส่วนใหญ่ไม่เหมือนกัน และไม่พิสูจน์ memorization
- “ทั้งสี่ไม่มี EOI marker” ต้องเจาะจงว่าไม่มี terminal EOI ที่ถูกต้อง `18613` มี byte sequence `FFD9` ภายในที่ offset 9,200 จึงไม่ควรใช้การค้น marker เพียงอย่างเดียวพิสูจน์สาเหตุ
- Native evaluator crash เป็น bug ที่เกิดเมื่อ prediction ทั้งชุดว่าง ไม่ได้แปลว่าทุกเฟรมที่ไม่มี detection ทำให้รันล้ม

## B. Blocker-by-blocker recommendations

| Issue | Verified status | Options | Recommended action | Approval needed |
|---|---|---|---|---|
| RGB 4 ภาพ | Strict Pillow fail ซ้ำ, SHA256 ตรง inventory; สาเหตุจากต้นทางยังไม่ยืนยัน | Source replacement / invalid-sample policy / รอ source | ค้นสำเนาที่ตรวจ provenance ได้ก่อน; ระหว่างรอหยุด full evaluation แต่แยก smoke gate | ใช่ ก่อนดาวน์โหลด/ใช้ replacement หรือเปลี่ยน denominator |
| Train/val RGB reuse | 628 groups, 652 val IDs; GT ต่างกันเป็นส่วนใหญ่ | Official only / official + sensitivity | รายงานสองประชากรแยกกัน พร้อม exposure disclosure | ใช่ ก่อนสร้าง active evaluation manifests |
| GT ownership | 9968 ผิดไปจากกติกา per-person; พบ comparable local anomalies เพิ่ม | เก็บ raw พร้อม flag / sensitivity quarantine / relabel | เก็บ raw, งดใช้เคสผิดชัดในการออกแบบ crop; sensitivity ต้องใช้กติกากลางที่อนุมัติล่วงหน้า | ใช่ สำหรับ quarantine/exclusion; ไม่แนะนำ relabel ตอนนี้ |
| Empty-prediction evaluator | Reproduced shape error; มีอีกจุด `np.max` เสี่ยง | Wrapper / แก้ต้นฉบับ / ไม่รองรับ | Compatibility wrapper แยกต่างหากพร้อม edge/parity tests | ใช่ เพราะเป็น scientific source change |
| AP^p_vol | นิยาม 9 thresholds ยืนยันแล้ว; executable parity ยังไม่ครบ | Port จาก source / สูตรใหม่ | ใช้ reference behavior เดิมและทดสอบทั้งเก้า thresholds | ใช่ ก่อน implementation |
| CUDA/native environments | FASHN imports ผ่าน; native stacks ยังไม่ติดตั้ง | Binary wheels / isolated user-space toolkit / รอ | FASHN ก่อน แล้ว CPI-R50 prebuilt route; M2FP ตามเมื่อ toolchain ผ่าน | ใช่ สำหรับ download/install/smoke |
| License scope | มี research-only restrictions; Sapiens2 surveillance R&D blocked | Research scope / deployment-eligible cohort | แยกสิทธิ์วิจัยจากสิทธิ์นำไปใช้จริง; ไม่ปลด Sapiens2 ด้วยคำว่า research | ผู้ใช้ระบุ intended use; permission ของเจ้าของสิทธิ์ยังจำเป็นตามเงื่อนไข |
| Taxonomy/ownership protocol | Draft ยังไม่ผ่าน checkpoint outputs จริง | Universal score / explicit cohorts | Cohorts ที่ตอบ body/clothing พร้อม denominator/coverage กลาง | ต้องทบทวนก่อน freeze; รอบนี้ไม่ freeze |

### 1. RGB failures: สิ่งที่ทราบและยังไม่ทราบ

| Split / ID | Bytes | ตรวจซ้ำ | รายละเอียดเพิ่มเติม |
|---|---:|---|---|
| train/1396 | 379,497 | Pillow fail; SHA256 ตรงเดิม | ไม่พบ `FFD9` จากการสแกน bytes |
| train/18613 | 577,978 | Pillow fail; SHA256 ตรงเดิม | ท้ายไฟล์เป็น zero bytes 315,834 bytes; มี `FFD9` ภายใน แต่ไม่ใช่ terminal completion ที่ยืนยันได้ |
| train/24328 | 320,069 | Pillow fail; SHA256 ตรงเดิม | ไม่พบ `FFD9` จากการสแกน bytes |
| val/17844 | 440,931 | Pillow fail; SHA256 ตรงเดิม | ท้ายไฟล์เป็น zero bytes 47,715 bytes |

**Verified:** decoder อ่าน RGB ไม่ครบจริง ไม่ใช่แค่รายงานผิด และไม่มีการเปลี่ยน bytes ตั้งแต่ audit เดิม **Interpretation:** มี truncation/corruption ของ JPEG stream; zero tails ทำให้ไม่ควรสรุปว่าเพียงขาดสอง byte EOI **Unknown:** เกิดก่อนดาวน์โหลด ใน archive ต้นทาง ระหว่างจัดเก็บ หรือหลัง import

Import record มี whole-ZIP SHA256 และผล CRC extraction แต่ไม่มี individual-member SHA256 ก่อน extraction ให้เทียบสี่ไฟล์ ปัจจุบัน ZIP local ไม่อยู่แล้ว ตรวจ official Google Drive metadata ได้ว่า ZIP มีขนาด **5,429,618,040 bytes** ตรง record แต่ **ขนาดตรงไม่ใช่หลักฐาน whole-archive หรือ member-byte identity** การดู importer source พบว่าอ่านสมาชิกผ่าน ZipFile พร้อม CRC/size checks จึงไม่มีหลักฐานพอจะโทษ offset recovery เป็นสาเหตุ และไม่มีหลักฐานพอจะยืนยันว่า official release เสียเหมือน local

Official repository ระบุ Google Drive และ Baidu เป็นแหล่งแจก v2 แต่ยังไม่ได้ดึงสมาชิกจาก independent release มาเทียบ ไม่พบ local RGB ที่อ่านได้และมีชุด GT ตรงกันทุก plane สำหรับสี่กรณีนี้ จึงยังไม่มี replacement ที่ยืนยันแล้ว [Official source links](https://github.com/ZhaoJ9014/Multi-Human-Parsing#multi-human-parsing-mhp-v20-dataset)

เปรียบเทียบทางเลือก:

| ทางเลือก | Reproducibility / denominator | Comparability / ข้อเสีย |
|---|---|---|
| A — Verified source replacement | เก็บ originals และเก็บ replacement สี่ไฟล์แยก พร้อม source/hash/geometry; target membership เดิม | ต้องยืนยันว่าเป็นภาพเดียวกันและ align กับ GT; ห้ามสังเคราะห์ pixels; เปลี่ยน source-input version จึงต้องเปิดเผย |
| B — Document invalid-sample policy | เก็บ official manifest แต่ scored readable view เป็น 4,999 ภาพ / 13,257 GT persons; train development ไม่ใช้สามภาพเสีย | ต้องเรียก readable subset ไม่ใช่ unqualified official-5,000 result; ทุกโมเดลใช้ denominator เดียว; input failure ไม่ใช่ parser FN โดยอัตโนมัติ |
| C — Block full evaluation | เก็บ target population 5,000 และยังไม่รายงาน accuracy | สะอาดด้าน claim แต่ต้องรอ; ไม่ควรใช้ C ห้าม readable-train smoke tests ที่แยก gate แล้ว |

**แนะนำ A แบบจำกัดงบค้น/ดึง source เฉพาะสี่ไฟล์ก่อน** หากไม่พบสำเนาที่พิสูจน์ได้ ให้กลับมาขออนุมัติ B ไม่ตัดไฟล์เอง ระหว่างรอใช้ C เฉพาะ full evaluation หาก archive ไม่รองรับ selective retrieval ต้องถามก่อนดาวน์โหลด ZIP 5.43 GB ห้ามซื้อเวลาโดย force decode หรือเติม EOI

### 2. Leakage: RGB, GT และตัวตนคนไม่ใช่สิ่งเดียวกัน

ตรวจใหม่จาก index/hash ที่ผูกกับ source โดยไม่ hash dataset ซ้ำทั้งชุด และ decode GT ของคู่ตัวอย่างจริงเพิ่มเติม:

- **628 train/val groups / 652 val IDs:** ยืนยันตรงกับ leakage record เดิม
- **651/652 val IDs:** JPEG file bytes ตรงกับอย่างน้อยหนึ่ง train copy; อีกหนึ่ง RGB pixels ตรงแต่ JPEG bytes ต่าง
- **42 val IDs:** ชุด GT ตรงทุก plane และลำดับคน
- **1 val ID:** ชุด GT ตรง แต่สลับ person suffix (`train/20799` ↔ `val/23556`)
- **609 val IDs:** ไม่มี train copy ในกลุ่ม RGB เดียวกันที่ชุด semantic GT ตรงทั้งหมด ไม่ควรตีความว่าทั้ง 609 แตกต่างรุนแรงหรือเป็น annotation error ทุกกรณี
- **6 val IDs:** จำนวน person planes ต่างจาก train copies ทุกตัวในกลุ่ม อีก 646 มี train copy ที่จำนวนคนเท่ากัน
- ภายใน validation เองมี **106 duplicate-content groups, 214 IDs, 108 extra repetitions**; มีเพียง 6 groups ที่ชุด GT เหมือนกันทุก record

ตัวอย่าง `train/1276` ↔ `val/1280`: คน 6 คนเท่ากัน แต่ขอบเขต/semantic pixels ต่าง; foreground IoU ของคู่ plane ที่ตรงตำแหน่งประมาณ 0.920–0.960 ตัวเลขนี้เป็น annotation agreement diagnostic ไม่ใช่ model metric ส่วน `1436` ↔ `20399` มีการเปลี่ยนลำดับคนและ parsing pixels ต่างด้วย การตีความว่าอาจ re-annotate/duplicate source เป็นสมมติฐาน ไม่ใช่ release history ที่ยืนยันแล้ว

#### สอง evaluation populations ที่เสนอ — ยังไม่อนุมัติใช้งาน

| Population | Membership | Images | Native GT persons | อ่าน RGB ได้ตอนนี้ |
|---|---|---:|---:|---:|
| Original official validation | ID ทั้งหมดใน original `val.txt` | 5,000 | 13,260 | 4,999 / 13,257 persons |
| Exact train-overlap-controlled sensitivity | Official IDs ลบเฉพาะ 652 IDs ที่ decoded RGB hash ตรง train | 4,348 | 11,411 | 4,347 / 11,408 persons |

`val/17844` ยังอยู่ในทั้งสอง target populations; ไม่ถูกลบเงียบ ๆ Overlap exclusion ลบ 1,849 person planes เฉพาะใน supplemental population รายชื่อ 652 exclusions และ 4,348 included IDs อยู่ใน JSON ของ review นี้ ภายใต้ `authorized_for_evaluation=false` Membership SHA256 สำหรับ included IDs เรียงเลขและปิดท้าย newline คือ `a99e6d455a656a79fad0d4fdd136c405c81547155193a87c6327d4e3ff6f6bb2`

Sensitivity นี้ยังมี **83 groups** ที่ซ้ำภายใน validation; ไม่ควรเรียกว่า fully deduplicated หรือ clean independent test set ยังไม่ลบ within-val repeats เพราะ GT อาจต่างกัน หากต้องการ unique-content population ต้องเป็นการตัดสินใจแยกพร้อมนโยบายเลือก annotation

M2FP/CPI source config ประกาศใช้ MHP train; จึงมี **potential exposure to the same RGB** ผ่าน train แต่ยังไม่มี weights/run-training manifest ที่ยืนยัน sample-level exposure และไม่รู้ผลต่อ memorization FASHN exposure ยัง UNKNOWN; CIHP/LIP-trained models ก็ไม่ได้พิสูจน์ว่า pretraining datasets ไม่ซ้ำ MHP

**แนะนำรายงานแยกสองตาราง/สองชื่อ population**, ให้ทุกโมเดลใช้ membership เดียวกันในแต่ละ cohort ระบุจำนวนภาพ/person/class support และ exposure state ไม่เฉลี่ยรวม scores ทั้งสองประชากร และไม่ถือ controlled score ว่า comparable ตรงกับ published full-validation scores

### 3. Person ownership: ข้อสรุปใหม่ที่เข้มขึ้น แต่ยังไม่แก้ GT

ดูภาพ `9968` ซ้ำและดูเพิ่มแบบ train-only: `11766`, `25373`, `16898` จาก high-overlap สองคน และ `train/1` เป็น low-overlap control ภาพเพิ่มสร้างเฉพาะ temporary visualization; ไม่เขียนทับ GT หรือ diagnostics เดิม

- `9968`: plane 1 รวม face และ garment บริเวณทั้งสองผู้ใหญ่ ขณะที่ plane 2 ส่วนใหญ่เป็นคนชาย ประเด็นอยู่ที่ visible body/clothing ไม่ใช่เพียง carried object หรือ boundary
- `11766`, `25373`: semantic planes 1 และ 2 ตรงกันทุก pixel และ overlay แสดงคนเดียวกันทั้งสอง files อีกคนใน RGB ไม่ปรากฏเป็น target ของ plane เหล่านี้
- `16898`: สอง planes เกือบตรงกันและชี้ไปที่คนหญิงคนเดียวกัน; ขอบเขต/labels ต่างเล็กน้อย
- `train/1`: planes แยกสองคนตาม RGB ได้ แม้มี support overlap เล็กน้อย

Paper section 3.1 กำหนด per-person annotation และให้คนอื่นเป็น background ดังนั้นเคสข้างต้นไม่สามารถอธิบายด้วย legitimate overlap อย่างเดียว การอ้าง occlusion/completion semantics เพื่อรับรอง masks เหล่านี้ก็ไม่มีหลักฐานเพียงพอ **ยืนยันว่า local GT ไม่สอดคล้องกับ intended per-person semantics ในเคสที่เห็น** แต่ยังไม่ยืนยันว่าเป็น official-release error หรือ local-copy issue และชุดเลือกนี้ไม่ใช้ประมาณ prevalence [MHP-v2 paper](https://arxiv.org/html/1804.03287#S3.SS1)

ผลกระทบต่างกันตามงาน:

| งาน | ผลของ uncertain ownership |
|---|---|
| Oracle crop | GT bbox ที่รวมสองคนไม่ใช่ oracle localization ของคนเดียวจริง |
| GT↔YOLO association | GT plane รวม/ซ้ำทำให้ one-to-one assignment และ unmatched counts หลอกได้ |
| Person-macro mIoU | คะแนนถูกเฉลี่ยต่อ annotated plane ที่อาจไม่ใช่ physical person distinct |
| Coverage-aware score | GT person denominator ยังอ้าง supplied annotations ได้ แต่ไม่ใช่ physical coverage ที่รับรองแล้ว |
| Official AP^p / PCP | Source evaluator คำนวณได้ตาม raw GT แต่ผลสะท้อนข้อจำกัด annotation; correct physical prediction อาจถูกลงโทษ |

**แนะนำคง raw GT สำหรับ native-reference reporting และ flag ให้เห็น**, กัน confirmed-anomaly train cases ออกจากการเลือก crop/matching defaults ใน development โดยมีเหตุผลและรายชื่อ ไม่ใช้ flags ตาม error ของโมเดล และไม่บังคับแก้คนตาม left/right เอง อนุมัติกติกากลางก่อนสร้าง GT-quality sensitivity cohort; หากอยู่ validation ต้องรายงาน raw กับ sensitivity แยก และทุกโมเดลใช้ exclusions เดียวกัน ไม่ quarantine ทุกภาพที่ overlap

### 4. Official evaluator: bug ที่แก้ได้โดยไม่เปลี่ยน metric design

ทำ bounded synthetic checks เพิ่มจาก function port ที่มีอยู่ ไม่แก้ third-party source:

1. `eval_seg_ap` สร้าง `BB=np.array([])` เป็น shape `(0,)`; indexing `BB[sorted_ind, :]` ที่ original source line 84 ทำให้ IndexError เมื่อทั้ง evaluation ไม่มี prediction
2. หลังแก้ shape ยังมี `np.max(tp_seg)` บน empty array ที่ต้องจัดการ ไม่ใช่แค่แก้ reshape แล้วจบ
3. Fixture ที่มีหนึ่ง image ว่างร่วมกับ prediction ของอีก image รันผ่าน จึงต้องแยก whole-population empty จาก per-frame empty
4. Helper `voc_ap([],[])` คืน 0 จริง ส่วน paper ระบุ PCP ของ missed GT เป็น 0

**ข้อเสนอ wrapper:** เมื่อ global `npos>0` และไม่มี predictions ทั้งชุด ให้ AP^p=0 และ PCP=0 ตาม empty PR helper และ all-missed PCP เมื่อ `npos=0` ให้ explicit undefined/NA + support counts ไม่บังคับ zero หากภาพหนึ่งไม่มี GT แต่ dataset มี GT อื่นอยู่ ต้องเก็บ unmatched predictions ของภาพนั้นเป็น FP ตาม aggregate policy ไม่ ignore ทั้งภาพ

ไม่พบหลักฐานผู้เขียน acknowledge bug นี้เป็น known issue การไม่พบ issue ไม่พิสูจน์ว่าไม่มีใครเคยพบ แต่ source และ executable failure เพียงพอให้เรียก implementation edge-case bug ได้ [Official source](https://github.com/ZhaoJ9014/Multi-Human-Parsing/blob/master/Evaluation/Multi-Human-Parsing/v2/eval_mhp.py)

AP^p_vol มีนิยามยืนยันแล้ว: mean ของ AP^p ที่ thresholds **0.1, 0.2, …, 0.9** จำนวน 9 ค่า ซึ่งตรงทั้ง paper และ CPI/M2FP evaluator source ความไม่พร้อมคือ **executable parity** ไม่ใช่ metric definition ที่ไม่รู้แล้ว ต้อง reset GT matching state ทุก threshold, คง strict `>` comparison, confidence sorting และ background treatment ตาม pinned reference ไม่ใช้ mask-IoU matching ของ common track มาแทน native AP

Reference tests ที่ต้องผ่านก่อน claim official parity: existing five fixtures; whole-empty + mixed-empty; no-GT domain; duplicate/high-score FP/confidence ordering/ties; exact-threshold cases; absent parts/background contribution; RGBA first-channel versus derived indexed PNG; overlap/identities; all 9 thresholds และ reference-vs-wrapper equality ใน nonempty cases บันทึก score scale 0–1 versus percent ให้ชัด source CPI ใช้ converted grayscale annotations จึงห้าม feed raw RGBA R-label PNG เข้า grayscale reader แล้วอ้าง parity ไม่มีการเขียน wrapper หรือรัน AP^p_vol parity ใน review นี้

### 5. Model readiness, nvcc และ resource priorities

ทุกโมเดลยัง **checkpoint downloaded=NO, loaded=NO, actual inference=NO, FP32 T4 feasibility=NOT_ESTABLISHED** Source revisions/official link metadata verified; Google Drive view page ไม่ใช่ successful weight-body download

| Candidate | Checkpoint declared bytes / MB decimal | Environment / native mode | License eligibility |
|---|---:|---|---|
| FASHN | 256,146,352 / 256.1 MB | Isolated dependencies/import/synthetic GPU pass; semantic image/crop; ไม่ต้อง build native CUDA extension | Official wrapper/model inherits SegFormer research/evaluation-only terms; commercial deployment ไม่ยืนยัน |
| CPI-R50 | 566,676,956 / 566.7 MB | Legacy Python/Torch/MMCV not installed; native internal detection+parsing; prebuilt MMCV route available to investigate | Apache-2.0 source; separate weight scope/complete dependency review ยังมีช่องว่าง |
| CPI-ConvNeXt-B | 1,299,250,784 / 1,299.3 MB | ใช้ legacy stack; ให้ R50 ผ่านก่อน ไม่ถือว่า checkpoint size=VRAM | เหมือน CPI; FP32 T4 memory ไม่ทราบ |
| M2FP R101 | 757,779,078 / 757.8 MB | Native full-frame multi-human; Detectron2 wheels อาจช่วย แต่ project MSDeformAttn ยังต้อง compile | Source majority CC-BY-NC-4.0; separate weight terms ต้องทบทวน |
| D2FP CIHP / LIP | 958,247,405 / 958.2 MB; 958,249,837 / 958.2 MB | Native CUDA extension source; CIHP instance / LIP semantic แยก variant | Local MIT ไม่รับรอง upstream M2FP files/weights ว่าไม่มีข้อจำกัด |
| SCHP-LIP | 267,449,349 / 267.4 MB | Native legacy InPlaceABNSync JIT build; crop semantic | MIT source; weight grant scope และ dependencies ทบทวนแยก |

Sizes มาจาก official Drive metadata หรือ pinned HF LFS/GitHub Release records ไม่ใช่ SHA256 ของไฟล์ downloaded locally ตัวเลข download accounting ใช้ MB/GB decimal; FASHN weights ประมาณ 244.3 MiB

**nvcc รายโมเดล:**

- FASHN: ไม่ใช่ blocker; ใช้ PyTorch binaries ที่มีอยู่แล้ว
- CPI: source ใช้ `mmcv.ops.MultiScaleDeformableAttention`; official index มี `mmcv_full` wheels ภายใน version range ของ project จึงมีเส้นทางไม่ compile local แต่ยังต้องเลือก Python/Torch/CUDA ABI ให้ตรง และทดสอบจริง ห้ามใช้ MMCV 2.x แทน 1.x เงียบ ๆ [Official MMCV install](https://mmcv.readthedocs.io/en/v1.7.0/get_started/installation.html)
- M2FP/D2FP: official Detectron2 wheels ไม่ครอบคลุม custom MSDeformAttn ของ project จึง native source path ยัง blocked แต่แก้ได้ด้วย isolated user-space compatible compiler/toolkit โดยไม่แก้ driver/system ไม่พบ official project-specific prebuilt extension ที่ตรวจยืนยันแล้ว [Detectron2 install](https://detectron2.readthedocs.io/en/latest/tutorials/install.html), [M2FP instructions](https://github.com/soeaver/M2FP/blob/main/INSTALL.md)
- SCHP: vendored module import เรียก JIT compile `.cu`; prebuilt generic package ไม่ใช่ drop-in proof ต้อง compile isolated หรือออกแบบ semantics-preserving implementation ที่ทดสอบ parity ก่อน ห้ามแทน InPlaceABN ด้วย ordinary BatchNorm โดยไม่มีหลักฐาน [Source](https://github.com/GoGoDuck912/Self-Correction-Human-Parsing/blob/master/modules/functions.py)
- User-space toolkit มีวิธี dedicated environment ตาม NVIDIA แต่ความเข้ากันได้ของ CUDA/GCC/Torch/SM7.5 สำหรับ legacy release ยังต้องพิสูจน์ ไม่เสนอ upgrade ระบบ [NVIDIA environment installation](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#conda-installation)

ตอนตรวจ GPU คือ Tesla T4, 15,360 MiB total / 14,912 MiB free, utilization 0%; disk free ประมาณ **626.4 GiB** ไม่มีปัญหาดิสก์เป็น blocker แต่ VRAM ของ intended checkpoints ยังไม่ทราบ

#### ข้อเสนองบและลำดับ — ยังไม่อนุมัติ

| ขั้น | Additional downloads ที่คาด | Disk reserve / เวลาโดยประมาณ | Stop condition |
|---|---|---|---|
| FASHN first smoke | weights 256.1 MB + small config; ขอ hard cap **300 MB**; ไม่มีแผนลง Torch ใหม่ | เผื่อ 1–2 GB; ประมาณ 15–45 นาทีหลังอนุมัติ ขึ้นกับ network/errors | มี dependency เพิ่มเกินงบ, license ไม่ผ่าน, GPU contention, FP32 failure |
| CPI-R50 native smoke | weights 566.7 MB + legacy binaries/deps ยังไม่ resolved; planning estimate รวม **2–4 GB**, ไม่ใช่ measured resolver total | เผื่อ 8–15 GB installed/cache; 1–3 ชั่วโมง engineering estimate | ตรวจ package manifest ก่อน download; hard cap ที่ผู้ใช้อนุมัติ; ไม่ switch FP16 |
| M2FP next | weights 757.8 MB + isolated toolkit/build dependencies; อาจเพิ่มหลาย GB ต้อง resolve ให้ทราบก่อน | เผื่อ 10–20 GB; อาจใช้เวลาหลายชั่วโมง | ขออนุมัติใหม่ก่อน heavy toolchain หรือ code compatibility changes |

แนะนำ FASHN → CPI-R50 → M2FP → SCHP / D2FP ตาม scientific role และ stack reuse; ConvNeXt-B รอ R50/memory evidence ไม่เลือกเพราะ paper score อย่างเดียว หากเป้าหมายรอบถัดไปเน้น native-MHP reference มากกว่า adapter validation สามารถเลือก CPI-R50 ก่อน แต่มี engineering cost สูงกว่า ไม่ควรรอ native stack จนหยุดการตรวจ FASHN ที่เป็นอิสระ

FASHN smoke ใช้ fixed readable train IDs เดิม `967`, `14282`, `4480`, เริ่มหนึ่งภาพแล้วไม่เกินสาม หลังตรวจ crop/GT target ของ sample และ license สิทธิ์ทดสอบไม่รวม final accuracy/timing/ranking ไม่รวม YOLO inference บน MHP และไม่รวม hybrid Outputs ต้องยืนยัน checkpoint hash, native labels/grid, original-coordinate mapping, FP32, actual VRAM และ canonical export ตัวเดียวกันต้องผ่าน official native API/adapter agreement ด้วย

### 6. License และ scientific fairness

แยก **code / weight / dependencies / intended use** ในแต่ละ candidate Public URL และ source license ไม่รับรองว่า standalone checkpoint ทุกชิ้นได้สิทธิ์ใช้งานทุกแบบ FASHN ระบุ inherited model terms ชัดเจน แต่ legacy candidates บางตัวต้องปิดช่องว่าง weights/upstream terms ก่อน execution ที่ได้รับอนุมัติ [FASHN terms](https://github.com/fashn-AI/fashn-human-parser/blob/main/LICENSE), [SegFormer terms](https://github.com/NVlabs/SegFormer/blob/master/LICENSE)

MHP dataset terms สนับสนุน noncommercial research สำหรับ academic/non-academic entities การอยู่ในบริษัทไม่ใช่คำตอบเรื่อง scope โดยตัวมันเอง ส่วน frozen YOLO AGPL/enterprise route ไม่ได้เปลี่ยนจากการ freeze weights และยังต้องทบทวนเมื่อจะ deploy [Dataset terms](https://lv-mhp.github.io/)

**Sapiens2 ยังคง license-blocked**: restriction ครอบคลุม surveillance-related R&D การเลือก research-only ไม่ปลดข้อห้ามนี้ ต้องมี permission ที่ใช้ได้จริง ไม่ bypass ด้วย wrapper/unofficial weights [Sapiens2 license](https://github.com/facebookresearch/sapiens2/blob/main/LICENSE.md)

การเปรียบเทียบ off-the-shelf candidates ยังมีคุณค่าเพื่อเลือกระบบ แม้ training exposure ต่างกัน แต่ห้ามตีความเป็น architecture-controlled superiority แนะนำแยก native MHP59 reference, crop-based common body/clothing cohort และ richer footwear/accessory-capable subsets อาจขยาย common clothing concepts หลังตรวจ semantic scope แทนการลด objective เหลือ face/hair อย่างเดียว ทุก cohort ใช้ GT projection/domain เดียวกัน และเปิดเผย retained body/clothing pixel/person support ที่เสียไป ไม่มี universal weighted score

Target ownership ควรเป็น deployment-available policy: รักษา raw semantic output, map-back ให้ถูก แล้วแยก target/neighbor ambiguity ด้วย YOLO/geometric information ที่อนุมัติ ไม่ส่ง GT foreground/class pixels ช่วย parser ใน deployment และไม่ ignore ambiguity เพื่อให้คะแนนดีขึ้นเฉพาะโมเดล ต้องมี conditional parser quality คู่กับ missed/unmatched/coverage-aware results

## C. Proposed next bounded execution

งานที่เป็นอิสระได้: source/license metadata review, draft denominator/cohort specification, evaluator synthetic parity tests, bounded FASHN feasibility บน verified train หลังอนุมัติ ไม่ต้องรอ repair ทั้ง dataset หรือ PPSS

ลำดับเล็กที่สุดที่มีประโยชน์หลังอนุมัติ:

1. บันทึก user decisions แยก benchmark readiness จาก bounded smoke permission; original study/data/protocol history คงอยู่
2. ตรวจ source เฉพาะสี่ RGB ภายในงบที่กำหนด ไม่โหลด full ZIP อัตโนมัติ และไม่ publish replacement view จน provenance/alignment ผ่าน
3. สร้าง supplemental population manifest จาก exact membership ที่รายงาน โดยคง original validation manifest และยังไม่รัน validation
4. สร้าง train anomaly flags/development view แบบไม่แก้ GT; ไม่กำหนด validation exclusions จากผลโมเดล
5. ทำ compatibility evaluator wrapper และ synthetic parity fixtures เมื่ออนุมัติ source changes; ไม่แก้ third-party source
6. ดาวน์โหลด pinned FASHN checkpoint/config ภายใน cap, hash จริง, ทำ FP32 smoke หนึ่งภาพก่อนและสูงสุดสามภาพ แล้วหยุดส่งผลให้ทบทวน
7. ขอการอนุมัติ CPI/toolchain เฉพาะขั้นถัดไปตามข้อมูลที่ได้ ไม่ถือว่า FASHN ผ่านคืออนุมัติ native/full benchmark

อันดับความสำคัญ: **license eligibility → GT ownership/cohort denominators → RGB input/fingerprint → exact reuse/exposure reporting → evaluator parity → native stack engineering** License หยุดเฉพาะ affected candidate; scientific ownership/domain gates สำคัญต่อ fairness สูง ส่วน RGB สี่ไฟล์เป็นปัญหา ingestion ที่จำกัดขอบเขต Native stacks ใช้เวลา/ดาวน์โหลดสูงสุด โดยไม่ควรขวาง independent low-cost checks

## D. Decisions required from the user

ตอบเป็นรหัสได้ แต่ทุกข้อยังเป็นข้อเสนอ ไม่ใช่การอนุมัติที่เกิดแล้ว:

| ข้อ | Default ที่แนะนำ | Alternatives / consequences | Download / protocol effect |
|---|---|---|---|
| 1 — RGB | **A:** ตรวจ/ดึง verified source copies แบบจำกัด ≤20 MB ก่อน; ไม่ใช้ replacement จนผ่าน provenance/alignment | **B:** readable-subset policy เปลี่ยน scored denominator; **C:** รอ source ก่อน full evaluation | A ไม่อนุมัติ ZIP 5.43 GB; B เปลี่ยน evaluation population; ยังไม่ freeze |
| 2 — Validation | **A:** official target + exact train-overlap sensitivity แยกผล | **B:** official only พร้อมข้อจำกัด; **C:** ยังไม่สร้าง supplemental manifest | ไม่มี download; A เพิ่ม reporting population ไม่แทน original split |
| 3 — Ownership | **A:** raw GT + flags, กัน confirmed train anomalies จาก protocol development; เตรียม sensitivity rule ให้ review | **B:** raw GT ใช้ทุกเคสพร้อม warnings; **C:** รอ source clarification ก่อน person-level protocol | ไม่มี download; A เปลี่ยน development selection แบบเปิดเผย ไม่ relabel และไม่อนุมัติ validation exclusion อัตโนมัติ |
| 4 — Actual smoke | **A:** FASHN-only ≤300 MB, 1–3 train images, existing isolated environment | **B:** FASHN + CPI-R50 staged cap ≤4 GB พร้อม dependency manifest ก่อน download; **C:** ไม่ download/smoke | Execution permission เฉพาะ Stage 0; ไม่มี benchmark/taxonomy freeze; งบ 8 GB เดิมไม่ถือว่าอนุมัติ |
| 5 — Intended use | **A:** noncommercial research/evaluation รอบนี้ และแยก deployment permission review | **B:** ต้องมี candidate ที่ eligible ต่อ deployment ตั้งแต่ต้น; **C:** scope ยังไม่ชัด ให้ metadata-only จนกำหนด | ไม่มี downloadโดยตัวเลือกนี้เอง; research ไม่ยกเว้น Sapiens surveillance ban และไม่รับรอง license ภายนอกแทนเจ้าของสิทธิ์ |
| 6 — Evaluator source | **A:** อนุมัติ minimal wrapper แยกและ synthetic parity tests | **B:** draft fix เท่านั้น ยังไม่แก้ code | ไม่มี heavy download; A เป็น source change แบบ versioned, ไม่เปลี่ยน metric design หรือแก้ third-party source; ไม่ถือว่าผ่าน parity ล่วงหน้า |

## E. Recommended next step

แนะนำ **1A, 2A, 3A, 4A, 5A, 6A** โดย smoke และ source retrieval จำกัดงบแยกกัน เริ่ม FASHN เพื่อให้ได้หลักฐาน checkpoint จริงเร็วที่สุดควบคู่กับแก้ metric edge cases ขณะที่ full evaluation ยัง gated ไม่มีขั้นใดเปลี่ยนคำแนะนำให้เป็น user approval

Review รอบนี้สร้างเพียงรายงาน/derived evidence ใหม่และ temporary GT inspection image ไม่แก้ scientific source, canonical state, benchmark results, original dataset, PPSS หรือ YOLO environments ไม่ติดตั้ง dependencies ไม่โหลด weights ไม่รัน parser inference ไม่มี remote/push

**STOP — WAIT FOR USER RESPONSES.**
