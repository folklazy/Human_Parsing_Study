# กลุ่มแรก T3b — รับรองนโยบายและแยก evidence gate

**ห้านโยบาย ACCEPTED · Channel order INDIRECT_ONLY/BLOCKED · ไม่ freeze / ไม่เริ่ม full benchmark**

ผู้ใช้รับรองชุดนโยบายหลังอ่านเอกสารและ YAML ไม่ใช่การรับรอง source, semantic binding หรือผล tests อย่างอิสระ รอบนี้บันทึกขอบเขตนั้นโดยตรง แล้วปิดสามจุดใน config/โค้ดเฉพาะ CPI_R50_CIHP และ CPI_ConvNeXtB_CIHP ไม่ขยาย roster หรือรันโมเดลซ้ำ

## 1. รับรองห้านโยบายแล้ว ไม่ต้องถามซ้ำ

[Config V7](../configs/application_v2_first_cohort_v7.yaml) ผูก [decision V6](../provenance/APPLICATION_V2_DECISIONS_V6.json) ด้วย content digest ค่าที่อนุมัติอยู่ใน `first_cohort.protocol` ไม่มีการอ่าน prose มาเลือกค่าที่ได้คะแนนดีกว่า

| นโยบาย | ค่าที่รับรอง |
|---|---|
| Target | 6 foreground targets + BG; coarse body/selected garments/footwear และ exclusions ตามชุดเดิม |
| Domain | Released-annotation-relative; ไม่อ้างว่าคนจริงทุกคนถูก annotate |
| Population | Main4,961 ภาพ / G_loc17,434 / G_sem17,390; reference5,000 /17,548 /17,504 แยกผล ไม่เรียก controlled ว่าปลอด exposure |
| Matching | Prediction-only association0.50 แยกจาก final prediction↔GT0.50 primary/0.75 secondary; native CPI evaluation box แยกจาก YOLO conditioning box |
| Runtime claim | Quality-only/FP32; ไม่มี latency/FPS/VRAM ranking หรือ cost Pareto |

Native score thresholds **R50=0.01 / ConvNeXt-B=0.05** คงเดิม เปรียบเทียบระบบตาม configuration ที่ประกาศ ไม่แปลงผลต่างเป็นผลของ backbone เพียงอย่างเดียว ไม่ปรับให้เท่ากันโดยอัตโนมัติ

Numeric catalog ID1 ยังคง `Exposed_face` เพื่อรักษา identity/hash เดิม แต่มี display name **Face region** ตามนิยาม source ไม่อ้าง independent skin extraction หรือเปลี่ยน numeric mapping

Mapping bundle ของ parser ยังไม่เปลี่ยนเป็น ACCEPTED เพราะการรับรอง target task/GT policy ไม่ใช่การยืนยัน channel identity ของ checkpoint

## 2. Channel-order gate: ตรวจได้และยังไม่ผ่าน

เพิ่ม `first_cohort.channel_order_evidence.required=true` พร้อม manifest/file SHA256, records แยกสอง checkpoint และข้อกำหนด `policy_acceptance_satisfies_gate=false` ดู [CHANNEL_ORDER_EVIDENCE.json](../provenance/RUN_MANIFESTS/first-cohort-policy-acceptance-20261016T034543760531Z/CHANNEL_ORDER_EVIDENCE.json)

Gate บังคับก่อน configured scoring และก่อน checkpoint support ที่ต้องการ direct channel evidence จะเป็น VERIFIED ต้องมี:

1. เอกสาร header ทางการ หรือ class-order statement ของผู้สร้าง พร้อม source URL และ provenance review
2. ความสัมพันธ์กับ checkpoint release ที่ชัดเจน รวม exact checkpoint SHA256 และ pinned source commit
3. เอกสาร local ที่ตรวจ SHA256 ได้ และลำดับชื่อคลาสตรงกับ bound native class order

การตั้ง `status=DIRECT_VERIFIED` อย่างเดียวไม่ผ่านหากไม่มีเอกสาร/ที่มา/ความสัมพันธ์กับ release การตรวจ bytes/order ในโค้ดไม่แทนการพิสูจน์ว่า source เป็นของผู้สร้าง; provenance review ยังต้องมีหลักฐานจริง

**การตรวจแหล่งทางการแบบจำกัด:** pinned tree ไม่มี CIHP annotation JSON/header, GitHub Releases API ไม่มี releases/assets และ repository metadata ระบุ `has_issues=false` ไม่อ้างว่า header ไม่มีอยู่ที่อื่น [ผลค้นพร้อม HTTP status/hash](../provenance/RUN_MANIFESTS/first-cohort-policy-acceptance-20261016T034543760531Z/CHANNEL_HEADER_SEARCH.json) · [repository ทางการ](https://github.com/HAG-uestc/CPI-Parser) · [Releases metadata](https://api.github.com/repos/HAG-uestc/CPI-Parser/releases?per_page=20)

ผู้ใช้แจ้งว่ายังไม่มีหลักฐานเพิ่มเติม จึงคงสอง checkpoint เป็น **INDIRECT_ONLY / semantic binding BLOCKED** ไม่ใช้ M2FP catalog, 20-class head หรือ loader ที่ไม่ remap เป็นหลักฐานทดแทน direct header และไม่เปิด audit ทั้งโครงการอีก

สิ่งที่ต้องหาเฉพาะจุดคือ `categories[].parsing` จาก annotation JSON ที่ใช้กับ CPI CIHP release หรือคำยืนยัน channel order จากผู้สร้างซึ่งระบุความสัมพันธ์กับสอง checkpoint ไม่ต้องดาวน์โหลดภาพ/GT ทั้งชุด ไม่ส่งข้อความหาผู้สร้างหรือดาวน์โหลด dataset โดยอัตโนมัติ

## 3. Entry point และ dry-run: เลือกสอง CPI จริง

Entry point ใหม่ [first_cohort_entrypoint.py](../scripts/first_cohort_entrypoint.py) บังคับ `--config` และ `--dry-run`; ไม่มีโหมด execute/model loading

```bash
.venvs/mhpv2-stage0/bin/python Human_Parsing_MHPv2_Study/scripts/first_cohort_entrypoint.py \
  --config Human_Parsing_MHPv2_Study/configs/application_v2_first_cohort_v7.yaml \
  --dry-run
```

[Dry-run plan](../provenance/RUN_MANIFESTS/first-cohort-policy-acceptance-20261016T034543760531Z/DRY_RUN_PLAN_V3.json) อ่าน roster จาก `first_cohort.models`, native checkpoint/config/environment จาก `first_cohort.execution_spec`, native thresholds จาก accepted protocol และ YOLO settings จาก explicit inference dependency ไม่อ่าน roster จาก catalog20 หรือ engineering permission เดิม

| Role | Selected | Settings |
|---|---|---|
| Parser system1 | CPI_R50_CIHP | exact checkpoint/config hash; score0.01; FP32 |
| Parser system2 | CPI_ConvNeXtB_CIHP | exact checkpoint/config hash; score0.05; FP32 |
| Shared dependency | YOLO26X_FROZEN | frozen hash; imgsz640/conf0.25/NMS0.70/maxDet200/retina_masks |

Plan แสดง `systems.variants=20`, `bounded_train.models=[YOLO26X_FROZEN,FASHN_B4]` และ `execution.model_loading=BOUNDED_TRAIN_ONLY` ใน **ignored legacy fields** เท่านั้น ขอบเขต engineering เดิมยังเก็บไว้ตาม accepted record แต่ไม่ถูกใช้แทน roster ของกลุ่มแรก ไม่แก้ script ที่สร้าง historical route ด้วย configV4 เพื่อให้ดูเสมือนเคยใช้ V7

Dry-run ไม่ import torch/Ultralytics/MMCV/MMDetection และไม่โหลด weights เอกสาร checksum ของ weights ใน plan อ้าง prior verified inventory โดยระบุว่าไม่ได้ rehash binary ผ่าน dry-run; native config files ตรวจ hash ตอนสร้าง plan

Validator ยังปฏิเสธ root matching/association/population settings ที่ขัด accepted protocol ป้องกันตัวเลขซ้ำใน compatibility fields กลายเป็นแหล่งค่าคนละชุด

นี่เป็น selection/config proof ไม่ใช่การอ้างว่ามี production full-benchmark execution entry point พร้อมแล้ว

## 4. Owner-unknown: global และ per-person แยกกัน

| กรณี | Global semantic | Per-person semantic |
|---|---|---|
| รู้ target semantic แต่ Human0 | **KEEP** บน shared global domain | **VOID_OWNER_UNKNOWN** เพราะไม่รู้เจ้าของ |
| Category0/Human0 | reference BG ตาม released annotations | reference BG ตาม shared policy |
| Human>0/Category0 | unknown/shared VOID | unknown/shared VOID แต่ Human ID ยังอยู่ G_loc |
| Category22 หรือ GT นอก fixed targets | shared VOID | shared VOID |

แยกเป็น `category_positive_human0_global` และ `category_positive_human0_per_person` ใน accepted domain ไม่มี field กำกวมที่เหมารวมสองกรณีอีก `project_gt` เก็บ known target สำหรับ global; `person_truth` void owner-unknown สำหรับรายคนตามพฤติกรรมเดิม **ไม่ใช่ policy change** และมี fixture ของกรณีที่มี pixel นี้จริงเพื่อไม่อาศัยเพียง count0

Audit เดิมพบ category-without-human0pixels ในข้อมูลที่ตรวจแล้ว จึงไม่มีการเปลี่ยน membership/denominators หรือ relabel source GT จาก clarification นี้

## 5. GT จริง: reconstruction ผ่านแบบ bounded TRAIN

ทำส่วน GT ที่ไม่ขึ้นกับ parser channels ได้โดยอิสระ อ่าน source PNG9members จาก CCIHP ZIP เฉพาะ TRAIN3IDs ที่กำหนดไว้ ตรวจ SHA256 กับ evidence เดิม, strict decode, เทียบ cached native arrays, original image dimensions และ lossless round-trip หลังบันทึก ไม่มี GT interpolation หรือแก้ source

| TRAIN ID | W×H | Native G_loc | G_sem ของ task |
|---|---|---:|---:|
| 0021834 | 500×321 | 2 | 2 |
| 0000930 | 500×346 | 2 | 2 |
| 0001368 | 500×375 | 3 | 3 |

รวม **3 ภาพ /7native Human IDs /7semantic-eligible IDs** ไม่ใช่ person count ทั้ง validation และไม่ใช่ model output counts

[GT reconstruction manifest](../provenance/RUN_MANIFESTS/first-cohort-policy-acceptance-20261016T034543760531Z/GT_TRAIN_RECONSTRUCTION/MANIFEST.json) เก็บ source hashes, original-grid transforms, per-image recipe binding, valid-mask pixel fingerprints, per-person boxes/eligibility และ artifact SHA256 Native Category/Human/Instance arrays ถูกเก็บใน derived artifact เพื่อเช็ก fidelity ได้ ไม่ flatten identities หรือใช้ YOLO สร้าง GT

RGB ใช้ prior hash-verified cached input ตรวจ NPZ hash และ dimensions ไม่อ้างว่าได้ decode RGB จาก TAR ใหม่หรือรับรอง physical ownership ทุกคน

**Accepted parser contexts =0** ข้อมูลนี้เป็น verified GT reconstruction evidence ไม่ใช่ accepted parser semantic context และไม่คำนวณ quality scores ไม่ reconstruct validation population ทั้งชุดในรอบนี้ ขั้น materialize accepted parser contexts ยังรอ direct channel evidence ก่อน

## 6. Readiness ของสองระบบ

| Gate | R50 CIHP | ConvNeXt-B CIHP |
|---|---|---|
| Five policies | ACCEPTED | ACCEPTED |
| Selected settings/roster | DRY_RUN_PASS | DRY_RUN_PASS |
| Native feasibility | ใช้หลักฐาน actual TRAIN FP32 เดิม | ใช้หลักฐาน actual TRAIN FP32 เดิม |
| Bounded GT reconstruction | PASS_SHARED_GT_EVIDENCE | PASS_SHARED_GT_EVIDENCE |
| Direct channel order | BLOCKED_INDIRECT_ONLY | BLOCKED_INDIRECT_ONLY |
| Semantic support VERIFIED | NO | NO |
| Accepted parser contexts |0|0|
| Scientific freeze/full benchmark | NOT READY / NOT AUTHORIZED | NOT READY / NOT AUTHORIZED |

ไม่ต้องรับรองห้านโยบายซ้ำ เมื่อมี direct source ที่ผูกกับ checkpoint release จึงตรวจเฉพาะ order/provenance gate แล้ว materialize contexts จาก GT จริงและตรวจ bindings/readiness ของกลุ่มนี้ ก่อนขออนุมัติ full benchmark แยก **ตอนนี้ยังไม่ขอเริ่ม benchmark เพราะ evidence gate ไม่ผ่าน**

## 7. Tests และ preservation

190 tests ผ่านหลังแก้: source/header binding และ invalid proofs, configuration conflicts, roster selection, dry-run requirement, owner-unknown สองขอบเขต และ display name ควบคู่ regression เดิม ดู [commands/logs/source snapshots](../provenance/RUN_MANIFESTS/first-cohort-policy-acceptance-20261016T034543760531Z/validation_v2/VALIDATION.json) และ [source diff](../provenance/RUN_MANIFESTS/first-cohort-policy-acceptance-20261016T034543760531Z/validation_v2/CHANGES.diff)

Protected hashes126 รายการและ frozen YOLO ตรงเดิม เอกสารก่อนแก้และ before/after hashes ถูกเก็บแยก ไม่มี dataset/checkpoint download, package install, parser/YOLO inference, VAL inference, training, hybrid, color, PPSS หรือ CCTV activity รอบนี้ มีเพียงการอ่าน official repository metadata ขนาดเล็กสำหรับ header search

Tests สนับสนุนเฉพาะพฤติกรรมที่ทดสอบ ไม่ทำให้ missing direct channel evidence ผ่าน และไม่ใช่ independent certification จากผู้ใช้
