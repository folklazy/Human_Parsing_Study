# Application V2 — ผล implementation และ bounded TRAIN integration

สถานะ: **ผ่านการทดสอบ implementation ในขอบเขตนี้; scientific policies ยังเป็น DRAFT** ไม่ใช่การอนุมัติ full benchmark หรือการรับรอง production pipeline ทั้ง 20 variants

## สิ่งที่ล็อกใน code/config แล้ว

| ข้อกำหนดที่ยอมรับ | Implementation | พฤติกรรมที่ตรวจแล้ว |
|---|---|---|
| แยก native identity กับ conditioning identity | [contracts.py](../src/application_v2/contracts.py) | Semantic parser รับ YOLO/oracle identity ได้โดยไม่กลายเป็น native instance parser; T3b เก็บทั้งสอง ID |
| Native count: N/A ต่างจาก 0 | `native_instance_count` | ไม่รองรับใช้ `null / N/A_UNSUPPORTED`; รองรับแต่ไม่มี output ใช้ `0 / DEFINED` |
| Rate ระบุ stage และ denominator | `stage_rate` และ [runner.py](../src/application_v2/runner.py) | Zero denominator เป็น undefined; routing skip เก็บแยก; failed eligible units ยังอยู่ใน denominator |
| Executable config เป็นแหล่งค่า runtime | [policy.py](../src/application_v2/policy.py) | Accepted decision ขัดกับ config หรือ source hash เปลี่ยน → validation ไม่ผ่าน |

[Accepted decision record V2](../provenance/APPLICATION_V2_DECISIONS_V2.json) อ้างคำสั่งผู้ใช้และผูก field ใน [application_v2.yaml](../configs/application_v2.yaml) โดยตรง Decision V1 และเอกสาร V2/appendix/handoff เดิมยังถูกเก็บไว้ ไม่ได้เขียน protocol ใหม่

อนุญาตเฉพาะ CPU fixtures, saved TRAIN replay และ bounded TRAIN integration 3 ภาพ/สูงสุด 10 person jobs ของ YOLO26x กับ FASHN ที่มีอยู่แล้ว ส่วน taxonomy, primary population, matching thresholds และ full-benchmark permission ยังไม่ได้รับการ freeze ผ่าน config นี้

## Evaluator และ lifecycle ที่ทำจริง

[evaluation.py](../src/application_v2/evaluation.py) ใช้ half-open bbox, threshold-eligible one-to-one assignment โดยเพิ่มจำนวนคู่ที่เข้าเกณฑ์ก่อนรวม IoU แล้ว sort immutable IDs ก่อนใช้ SciPy ที่ pin ไว้ ไม่อ้างว่าเป็น lexicographic optimum สำหรับ solver ทุก version

G_loc และ G_sem แยกกัน จับคู่ G_loc ครั้งเดียวก่อน semantic scoring ไม่มี class-guided rematching คนที่พลาดยังอยู่ใน miss-inclusive denominator; duplicate/unmatched final output เป็น FP ส่วน GT ที่ไม่มี target support มี semantic score undefined

Foreground diagnostics ใช้ทั้ง cohort target catalog รวม UNMAPPED; จึงนับ contamination จากคลาสที่มีเฉพาะใน prediction ได้ แม้ GT-supported semantic mean อาจไม่ลดลงใน fixture เดียวกัน บันทึก predicted-only-class FP แยกและสะสม global confusion ก่อนหาร ไม่เฉลี่ย per-image score แล้วเรียก global mIoU

Unknown raw decoder ID ถูกปฏิเสธ; UNMAPPED ที่นิยามไว้เป็น prediction-error column ไม่ใช่การ void GT เพื่อนบ้านที่มี ownership ชัดเป็น known negatives; foreground ที่ไม่มี Human ID เป็น void ตาม draft GT domain ส่วนนี้ยังต้อง review ก่อน freeze

[runner.py](../src/application_v2/runner.py) ตรวจ contract ก่อน completion, เก็บ valid partial outputs ใน PERSON scope, ทิ้ง provisional output เมื่อ global finalizer ล้มเหลวหรือส่ง output ผิด contract External/unresolved events ทำ trial incomplete ไม่ตีความเป็นความผิดโมเดลหรือ retry เพื่อเลือกผลที่ดีขึ้น

[artifacts.py](../src/application_v2/artifacts.py) publish packet แบบ atomic, เก็บ NPZ lossless + JSON + committed hashes, ปฏิเสธ overwrite/corruption/inference fingerprint ที่เปลี่ยน Single-writer เป็นข้อสมมติของ runner นี้ ยังไม่ได้รับรอง concurrent multi-writer execution

## Numeric mapping และ GT sidecars

สร้าง [native CCIHP diagnostic mapping](../taxonomy/APPLICATION_CCIHP_NATIVE_DIAGNOSTIC_V1.json) และ [body/clothing candidate mapping](../taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V1.json) เป็น **DRAFT** ทั้งคู่ Candidate mapping เป็นข้อเสนอสำหรับ CIHP/LIP cohort ไม่ใช่ common taxonomy ของทุก 20 variants และไม่ใช่ original native CIHP GT

| Dataset/view | Images | Native GT identities | Native-known semantic support | Candidate common semantic support |
|---|---:|---:|---:|---:|
| CCIHP source validation | 5,000 | 17,548 | 17,539 | 17,504 |
| CCIHP exact-overlap-controlled | 4,961 | 17,434 | 17,425 | 17,390 |
| MHP-v2 readable validation | 4,999 | 13,257 | 13,257 | ยังไม่ตั้ง taxonomy |
| MHP-v2 overlap-controlled readable | 4,347 | 11,408 | 11,408 | ยังไม่ตั้ง taxonomy |

ตัวเลขนี้เป็น **derived GT support counts** ไม่ใช่คะแนนโมเดล G_loc ใน sidecar เป็น structural draft ไม่ใช่การยืนยันว่า Human ID ทุกตัวตรงกับ physical person และการมี manifest ไม่ได้แต่งตั้ง CCIHP เป็น primary

ใช้ GT/source ledgers เดิม ตรวจ hash และอ่าน Category/Human เฉพาะที่จำเป็นสำหรับ support ใหม่ ไม่ flatten overlapping MHP person planes ไม่มี RGB validation inference ไม่มีการแก้ต้นฉบับหรือ official splits

- [CCIHP sidecar manifest](../provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/gt_sidecars/MANIFEST.json)
- [MHP native sidecar manifest](../provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/mhp_native_sidecars/MANIFEST.json)
- [CCIHP builder](../scripts/build_application_v2_sidecars.py), [MHP metadata builder](../scripts/build_mhp_application_sidecars.py)

MHP builder รันซ้ำใน fresh directory แล้วได้ sidecar SHA256 ตรงเดิมทั้งสอง populations ทุก byte ไม่เปลี่ยน dependency versions เพื่อให้ version string เหมือน historical environment

## TRAIN integration ที่ตรวจแล้ว

ใช้ภาพ Training `0021834`, `0000930`, `0001368` จากชุดที่มีอยู่ ไม่ใช้ validation/test เพื่อพัฒนานโยบาย

| การตรวจ | Input | สิ่งที่ผ่าน | สิ่งที่ยังไม่รับรอง |
|---|---|---|---|
| Saved replay: FASHN T1, SCHP-LIP T2, CPI-R50-CIHP T1 | 9 saved cases | Source hashes, identity/coordinate contract, lossless packet round trip | Model inference ใหม่หรือ application accuracy |
| Synthetic T3b opportunity replay | 3 fixtures | Association และเก็บ identity สองที่มา | Actual YOLO-conditioned execution |
| Live YOLO26x → FASHN T3a | 3 TRAIN frames, 10 opportunities | Frozen weights, FP32, RGB crops, native output retention, original-grid map-back, draft ownership view | Final taxonomy, accuracy, deployment FPS หรือ joint memory |
| Actual YOLO + saved native CPI T3b | 3 TRAIN frames | GT-free predicted-bbox association, native + YOLO IDs, final packet export | Live CPI execution ภายใต้ runner ใหม่ |

Live T3a ใช้ 6/2/2 YOLO opportunities และ parser completion 6/2/2 แต่ final emission 5/2/2 ตามลำดับ Native-FG-empty output หนึ่งรายการไม่ได้กลายเป็น final person จึงห้ามเอา completion rate มาแทน availability/coverage

ใช้ YOLO instance-mask ownership **หลัง** FASHN inference เป็น draft view; RGB ไม่ถูก hard-mask ก่อน parser และ raw native crop masks ยังอยู่ครบ ไม่มี GT-guided ownership ยังไม่ได้พิสูจน์ว่าวิธีนี้ให้ quality ดีสุดหรือว่า cropping เหมาะกับทุกโมเดล

Worker YOLO กับ FASHN รันเรียงกันใน existing isolated environments จึงไม่ใช่ joint-resident pipeline resource profile ไม่มี checkpoint download, package installation หรือการแก้ YOLO environment ในงานนี้

- [Saved replay validation](../provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/saved_train_replay_20261014T093248277455Z/VALIDATION.json)
- [Bounded TRAIN validation](../provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/bounded_train_20261014T094329862740Z/VALIDATION.json)
- [Actual-source T3b packet pointer](../provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/FINAL_NATIVE_ASSOCIATION_POINTER.json)

## Test evidence และ preservation

ผ่าน **109 tests / 6 suites**: application V2 42, existing Stage 0 25, official-MHP compatibility 19, reassessment 7, CCIHP GT 8, CCIHP quality 8 โดยชุด V2 รัน code ใหม่จริง รวม decision conflicts, identity, matching/negative pixels, global accumulation, failure injection และ artifact integrity

การรัน regression ครั้งแรกพบ import path ของชุดเดิมผิดจาก workspace root แก้ cwd ที่ validator แล้วรันครบใหม่ ไม่ patch legacy scientific code เพื่อให้ผ่าน

ตรวจ packet integrity 18 รายการ และ protected hashes 126 รายการตรงเดิม รวม measured YOLO CSVs และ source/provenance เดิมที่ freeze ก่อนเริ่มงาน Dataset archives size/mtime ตรง before record; ไม่ได้ rehash archives ใหญ่ทั้งหมดซ้ำ และไม่อ้างว่า metadata check แทน SHA256

[Final validation pointer](../provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/FINAL_VALIDATION_POINTER.json) และ [before evidence](../provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/BEFORE.json) เก็บผลจริงไว้ การตรวจ replay กับ hash ยืนยันเฉพาะ contract/artifact/source scope นี้ ไม่เท่ากับ official-metric parity หรือ production pipeline ผ่านทั้งหมด

เก็บ executed config และ exact script snapshot ของ bounded run; ตรวจ digest/SHA ตรงกับ run records ก่อนเก็บ Original run outputs ไม่ถูกเขียนทับ Helper source bytes เก่าบางส่วนไม่ได้ snapshot ไว้ครบ จึงระบุข้อจำกัดนี้ใน [recovery record](../provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/historical_execution_snapshots/RECOVERY_VERIFICATION.json) และเก็บ final implementation snapshots แยก

## ก่อน freeze ยังเหลืออะไร

ตรวจ [existing pilot resource records ทั้ง 20 variants](../provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/EXISTING_PILOT_RESOURCE_REFERENCES.json) แล้ว เก็บ source SHA, native operating mode, precision และ recorded allocator peaks สำหรับ review โดยไม่รัน profiling ใหม่ CPI-R50-CIHP ยังมี memory adaptation ใน pilot เดิม จึงต้องแยก execution profile ให้ชัด Workload ของแต่ละ native parser ต่างกัน และ resource peaks นี้ไม่รับรอง joint-resident YOLO pipeline หรือเป็นตัวเลข deployment requirement

1. ยอมรับ numeric mappings/cohorts, unknown/void policy, population roles และ denominator eligibility จาก support counts และ semantic review
2. ตรวจ live T3b parser worker และช่องทาง application ของ variants ที่จะใช้จริง ไม่ถือว่า saved-output replay รับรอง runtime
3. วัด joint-resident memory/resources และกำหนด future timing workload; bounded workers รอบนี้ไม่ได้วัด benchmark latency/VRAM
4. ทดสอบ config ที่ freeze แล้วกับ support hashes และ acceptance records ก่อนขออนุมัติ full benchmark

ไม่เพิ่ม datasets หรือ metrics ใหม่ ไม่เริ่ม training, validation inference, full benchmark, CCTV test, fusion, color study หรือ PPSS activity ไม่มี commit/push; workspace root และ study ไม่ใช่ Git repositories ในเครื่องนี้

รัน regression ซ้ำแบบ **CPU-only** จาก workspace root:

```bash
.venvs/mhpv2-stage0/bin/python Human_Parsing_MHPv2_Study/scripts/validate_application_v2.py --all
```

คำสั่งนี้ไม่โหลดโมเดลและไม่เรียก bounded GPU runner
