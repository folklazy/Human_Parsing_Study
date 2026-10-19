# กลุ่มแรก — ปิดช่องว่าง scoring context หลายระบบและหลายภาพ

**ผลด้าน implementation: CPU TESTS PASS · ข้อมูลจริง: NOT FROZEN / SCORING BLOCKED**

ต่อจาก [รายงานรับรองนโยบายแบบมีเงื่อนไข](FIRST_COHORT_CONDITIONAL_POLICY_REVIEW_TH_20261015.md) โดยไม่เริ่ม audit ใหม่ ไม่เปลี่ยนสองนโยบายที่ผู้ใช้รับรอง และไม่รันโมเดลเพิ่มในรอบนี้

## 1. สิ่งที่ตรวจพบและแก้แล้ว

โค้ดก่อนรอบนี้รับ `scoring_context` เดียว ซึ่งผูกกับ checkpoint และ input image เดียว การให้คะแนนรายภาพทำงานตาม fixtures เดิม แต่ยังไม่เพียงพอสำหรับรวบผลหลาย checkpoint × หลายภาพผ่าน configured runner เดียว การผ่าน 160 tests เดิมจึงยังไม่ยืนยันเส้นทางนี้

เพิ่ม optional `scoring_contexts[system_id][image_id]` และ `scoring_population` ใน executable schema พร้อมเงื่อนไขต่อไปนี้:

- Context registry และ population ต้องผูก accepted decision โดยตรง การเพิ่ม field ลง draft config อย่างเดียวไม่เปิดการให้คะแนน
- ทุกระบบต้องมี context ของประชากรครบชุดก่อนรัน ไม่สร้าง eligibility จากภาพที่บังเอิญสำเร็จ
- ทุก context ใช้ mapping, GT domain, target-support policy, evaluation geometry/threshold และ failure policy เดียวกัน
- Checkpoint/config ของระบบหนึ่งต้องคงเดิมข้ามภาพ แต่แต่ละระบบมี checkpoint ของตนเองได้
- ภาพเดียวกันต้องมี input binding ตรงกันข้ามระบบ และ context ต้องระบุ image ID ถูกต้อง
- ผลคะแนนผูก system ID, image ID และ context digest; ย้ายคะแนนไปอีกระบบ/ภาพไม่ได้
- Reporter ต้องใช้ population ตรง accepted manifest ทั้ง ID, ลำดับและ G_loc/G_sem; ตัดภาพที่ล้มเหลวออกเพื่อรับคะแนนหลักไม่ได้
- Single-context แบบเดิมยังใช้กับ fixture รายงานเดียวได้ แต่ไม่ใช้แทน registry ใน comparison หลายระบบ/หลายภาพ

โค้ด: [contexts.py](../src/application_v2/contexts.py), [policy.py](../src/application_v2/policy.py), [runner.py](../src/application_v2/runner.py) และ [tests](../tests/test_application_v2_contexts.py)

## 2. สิ่งที่ทดสอบจริง

เพิ่ม 14 CPU tests รวมชุดล่าสุด **174 tests PASS** จาก 6 suite patterns โดย 107 tests อยู่ใน application V2 patterns

เส้นทาง integration fixture ใช้ 2 ระบบ × 2 ภาพ ผ่าน `ConfiguredRunner.score_frame` → `ConfiguredRunner.comparison_report` จริง แต่ใช้ masks/GT สังเคราะห์และ accepted decisions เฉพาะ temporary directory ไม่มีการรับรองข้อมูลจริงแฝงอยู่ใน tests

ทดสอบ valid empty ให้ execution สำเร็จและรับ FN, ระบบที่ขาดงานยังเป็น INCOMPLETE/main_metrics=null, context ผิด checkpoint/ภาพ, input hash ไม่ตรงข้ามระบบ, domain ต่างกันรายโมเดล, threshold ขัด config, population ถูกลดภายหลัง และ registry ที่ยังไม่ได้รับรอง

[Validation พร้อม commands/logs/source snapshot](../provenance/RUN_MANIFESTS/first-cohort-context-closure-20261016T030334073358Z/LATEST_VALIDATION.json) · [หลักฐาน run](../provenance/RUN_MANIFESTS/first-cohort-context-closure-20261016T030334073358Z/)

รันซ้ำจาก workspace root โดยไม่เรียกโมเดล:

```bash
.venvs/mhpv2-stage0/bin/python Human_Parsing_MHPv2_Study/scripts/validate_first_cohort_context_closure.py
```

นี่เป็นหลักฐานพฤติกรรมของ implementation ที่ทดสอบ ไม่ใช่ independent reviewer certification หรือการรับรอง production scoring/cached scoring ทั้งระบบ

## 3. สถานะข้อมูลจริงของกลุ่มแรก

ยังใช้ [config V5](../configs/application_v2_first_cohort_v5.yaml) และ [accepted decision V4](../provenance/APPLICATION_V2_DECISIONS_V4.json) เดิม ไม่สร้าง accepted context registry ของข้อมูลจริง

| เรื่อง | สถานะ |
|---|---|
| STRICT_COMPLETE + retained incomplete rows | รับรองแบบมีเงื่อนไขแล้ว; code/tests รองรับ |
| Checkpoint-specific cohorts | รับรองแล้ว; ไม่ใช้ชื่อ CIHP/LIP ให้สิทธิ์อัตโนมัติ |
| กลุ่มแรก | CPI_R50_CIHP / CPI_ConvNeXtB_CIHP, T3b |
| Actual model route | หลักฐานก่อนรอบนี้: actual YOLO26x + CPI ทั้งสองบน TRAIN `0000930`; แต่ละระบบได้ 2 final persons; ไม่มี quality ranking |
| Context registry หลายระบบ/ภาพ | ผ่าน synthetic CPU integration; ยังไม่มี accepted registry ข้อมูลจริง |
| Mapping / semantic support | DRAFT; structural checkpoint binding ไม่เท่ากับ semantic acceptance |
| Population | manifests/counts ตรวจแล้ว; main/reference roles ยัง DRAFT |
| GT domain / annotation completeness | ยังต้องตัดสินขอบเขตข้ออ้างจากหลักฐาน ไม่ใช้การตอบรับแทนหลักฐาน |
| Matching / evaluation bbox source | กลไกผ่าน tests; threshold/geometry policy ของงานจริงยังไม่รับรอง |
| Runtime | มี engineering profile; ยังไม่ใช่ steady-state หรือ joint-resident benchmark |
| Cached scorer / workflow resume | NOT_IMPLEMENTED_DISABLED; packet integrity resume เป็นคนละความสามารถ |

Original-source population: **5,000 images / G_loc structural 17,548 / candidate G_sem 17,504**; overlap-controlled population: **4,961 / 17,434 / 17,390** รักษาแยกกัน ไม่มี exclusions ใหม่หรือการคำนวณคะแนน validation

## 4. ข้อที่ต้องปิดก่อน freeze

1. **Target semantics:** review coarse garment union, face/torso/naked limbs/footwear และ unsupported labels จาก mapping evidence ของสอง checkpoint จริง ไม่ยอมรับ checkpoint อื่นเพราะชื่อ dataset เหมือนกัน
2. **GT domain:** Category0/Human0 เป็น released background แต่ยังไม่มีหลักฐานรับรอง physical known-negative ทุกพิกเซล รวมถึง unknown22 และ human-without-category เดิม ต้องระบุ shared domain/void policy และขอบเขตคำอ้างให้ตรงหลักฐาน
3. **Population:** เลือก main/reference roles ของ manifests ที่ตรวจแล้ว พร้อม G_loc/G_sem และเหตุผลของ native IDs ที่ไม่มี semantic support; ห้ามลบ localization denominator ตามผลโมเดล
4. **Matching:** รับรอง prediction-only association แยกจาก final prediction↔GT matching และระบุ evaluation bbox/native box แยกจาก conditioning YOLO box
5. **Runtime:** กำหนด workload, จำนวนคน, residency, warmups, synchronization และ repeated clean rounds สำหรับข้ออ้างเวลา/VRAM โดยไม่ใช้ cold smoke timing จัดอันดับ

ข้อเสนอสำหรับ domain review: แยกการประเมิน **เทียบ released annotations** ออกจากข้ออ้าง **เทียบ physical person completeness** การกำหนด annotation-relative domain อาจทำ benchmark ที่ระบุข้อจำกัดชัดเจนได้ แต่ไม่พิสูจน์ว่าคนทุกคนถูก annotate และไม่ทำให้ unmatched prediction ทุกชิ้นเป็นคนที่ไม่มีอยู่จริง ข้อนี้ยังเป็น proposal ไม่ได้เปลี่ยน active domain หรือถือว่าผ่าน gate แล้ว

ไม่ต้องรับรองสองนโยบายเดิมซ้ำ ไม่ต้องวนหา patch ZIP และไม่จำเป็นต้องรอ universal shared view อย่างไรก็ตาม tests/actual smoke ไม่แทนหลักฐาน mapping/domain ของกลุ่มจริง

## 5. Preservation และขอบเขต

- Protected hashes **126 รายการตรงเดิม** และ frozen YOLO26x checkpoint ตรงเดิม
- เดิม V5 canonical packet fingerprints ทั้งสองยังตรวจผ่านหลังแก้โค้ด
- เก็บ source/docs ก่อนแก้, source diff, snapshots และ before/after hashes ไว้ใน run นี้
- ไม่มี model inference เพิ่ม, VAL inference, package install, checkpoint download, training, hybrid, color, CCTV หรือ PPSS activity ในรอบ continuation นี้
- ไม่มีการสร้าง Git repository หรือ push; workspace root และ study directory ไม่ใช่ Git repositories

**ยังไม่ freeze และยังไม่เริ่ม full benchmark** งานต่อคือ review ข้อสอบจริงห้าข้อข้างต้น จากหลักฐานที่มีอยู่ แล้วสร้าง versioned accepted context เฉพาะเมื่อได้รับรองครบ
