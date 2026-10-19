# Human Parsing Study — Implementation V2

**ล่าสุด 16 ตุลาคม 2026: bounded integration ปิดแล้ว; validation launch candidate เตรียมครบ รอคำอนุมัติ benchmark แยก**

- [Launch readiness และขอบเขตคำอนุมัติ](reports/FIRST_COHORT_VALIDATION_LAUNCH_READY_TH_20261016.md)
- [Config V10 — launch candidate](configs/application_v2_first_cohort_v10.yaml) · [Decision V9 — launch PROPOSED](provenance/APPLICATION_V2_DECISIONS_V9.json)
- [Launch plan](provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/LAUNCH_PLAN.json) · [Candidate hashes](provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/LAUNCH_FREEZE_CANDIDATE.json) · [Validation](provenance/RUN_MANIFESTS/first-cohort-validation-launch-20261016T091821919536Z/VALIDATION.json)
- [Fresh TRAIN/scoring closure เดิม](reports/FIRST_COHORT_FRESH_TRAIN_SCORING_CLOSURE_TH_20261016.md) · [Current artifacts](provenance/CURRENT_STUDY_ARTIFACTS.json)

ใช้ CPI_R50_CIHP/CPI_ConvNeXtB_CIHP+frozen YOLO26x ใน T3b แบบ quality-only เตรียม reference 5,000 ภาพเป็น inference ชุดเดียว; main 4,961 ภาพสะสมคะแนนแยกตาม membership คง mapping/domain/threshold/failure policies เดิมทั้งหมด ไม่ต้องรับรองซ้ำ

CPUapplication 147tests ผ่าน Protected126hash ตรง; ไม่มี model loading หรือ validation inference ในรอบนี้ `full_benchmark=false`, launch PROPOSED, config ยังไม่ FROZEN การยอมรับรายงานไม่ใช่คำอนุมัติรัน

Current readiness เฉพาะกลุ่มแรก ไม่รับรองทั้ง 20variants หรือ full-population resource feasibility รายงานและ states ย้อนหลังยังเก็บไว้ตามเดิม

## หลักฐานก่อนปรับนโยบาย — เก็บเป็นประวัติ

[Policy V7 / decision V6](reports/FIRST_COHORT_POLICY_ACCEPTANCE_AND_READINESS_TH_20261016.md), [source investigation ที่ปิดแล้ว](reports/CPI_CHANNEL_ORDER_SOURCE_BLOCKER_TH_20261016.md), [independent preparation](reports/CPI_INDEPENDENT_PREPARATION_TH_20261016.md) และ [context implementation](reports/FIRST_COHORT_CONTEXT_CLOSURE_TH_20261016.md) บันทึกสถานะ ณ เวลานั้น ข้อกำหนด direct-header-only ในเอกสารเก่าไม่ใช่นโยบายปัจจุบัน

## Checkpoint update — CDGNet

ดาวน์โหลด trained CDGNet LIP สำเร็จและ CPU weights-only inspection ผ่าน; ยังไม่รัน inference ดู [ผลตรวจ CDGNet](reports/CDGNET_ACQUISITION_TH_20261015.md) และ [current registry V6](provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv)

## หลักฐาน implementation ก่อนรอบล่าสุด


Independent noncommercial student academic research สำหรับ body/clothing และ accessories ที่โมเดลรองรับ Full benchmark และ company CCTV test **ยังไม่เริ่ม**

## สถานะที่บันทึกไว้ ณ 14 ตุลาคม 2026

**Implementation + bounded TRAIN integration: PASS WITH DRAFT SCIENTIFIC POLICIES**

สามข้อที่ผู้ใช้ยอมรับถูกผูกกับ code/config แล้ว: native identity แยกจาก conditioning identity, rate มี stage/numerator/denominator และ runner อ่าน executable config ที่ตรวจ accepted decisions โดยตรง

ผ่าน 109 tests จาก 6 suites; ตรวจ lossless packets 18 รายการและ protected hashes 126 รายการ Live YOLO26x → FASHN ทดลอง TRAIN 3 ภาพ/10 opportunities แล้ว ไม่ใช่ full benchmark หรือผลจัดอันดับ การจับคู่ T3b ใช้ actual YOLO และ saved native CPI outputs โดยไม่ใช้ GT

Taxonomy, primary population, matching policies และ joint-resident resource profiles ยังต้อง freeze review เก็บ historical Stage 0 blocker reports ไว้ตามเดิม ไม่ยกผลทดสอบ implementation เป็นการรับรอง annotation ownership หรือ production pipeline ทั้ง 20 variants

## Implementation รุ่นก่อนและหลักฐาน

- [ผล implementation พร้อมข้อจำกัด](reports/APPLICATION_V2_IMPLEMENTATION_TH.md)
- [Executable config — DRAFT](configs/application_v2.yaml)
- [Accepted decisions + proposed decisions](provenance/APPLICATION_V2_DECISIONS_V2.json)
- [Code: contracts, policy, evaluator, runner, artifacts, taxonomy](src/application_v2/)
- [Actual-code fixtures](tests/test_application_v2.py)
- [Final validation pointer](provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/FINAL_VALIDATION_POINTER.json)
- [Source/config snapshots และ document revisions](provenance/APPLICATION_V2_IMPLEMENTATION_FINAL.json)
- [20-variant pilot registry](../Human_Parsing_CCIHP_10_Image_Pilot/metrics/MODEL_PILOT_STATUS.csv) — technical pilot status ไม่ใช่ final benchmark หรือ license clearance

## Dataset evidence ที่เก็บไว้

- [CCIHP full structural audit](reports/CCIHP_FULL_QUALITY_AUDIT_STAGE0F.md)
- [200-image review/checklist](reports/CCIHP_HUMAN_REVIEW_STAGE0F.md) และ [full-resolution gallery](outputs/visualizations/stage0f-ccihp-quality-20261012T062825Z/index.html)
- [Cross-source ownership discrepancies](reports/CCIHP_CROSS_SOURCE_WARNINGS_STAGE0F.md)
- [Split leakage / sensitivity population](reports/CCIHP_SPLIT_LEAKAGE_STAGE0F.md)
- [CCIHP GT support sidecars](provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/gt_sidecars/MANIFEST.json)
- [MHP-v2 readable policy](provenance/MHPV2_READABLE_POLICY_V1.json) และ [native sidecars](provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/mhp_native_sidecars/MANIFEST.json)

CCIHP GT เป็น CCIHP-specific ไม่ใช่ original native CIHP GT Automated structural checks ไม่ได้พิสูจน์ physical-person correctness ทุก sample และไม่มี annotation-error prevalence estimate จาก AI-only review Dataset/taxonomy roles ยังไม่ freeze

## Scientific foundation และขอบเขต

[Study standard](STUDY_STANDARD.md), [draft tracks](EXPERIMENT_PROTOCOL_DRAFT.md), [schema](DATA_SCHEMA.md), [study state](STUDY_STATE.json), [references](REFERENCES.md), [research scope](RESEARCH_SCOPE.md), [license assessment](reports/LICENSE_ELIGIBILITY_REASSESSMENT.md)

เอกสารและ registry ของ Stage 0 เดิมเป็น historical evidence; ข้อความ zero downloaded/smoke-passed ในบันทึกเดิมไม่ใช่สถานะ pilot ล่าสุด Technical feasibility ไม่เปลี่ยนสิทธิใช้ Sapiens2 ใน surveillance-related work; ไม่มีการใช้ Sapiens2 ใน integration รอบนี้ PPSS ยังคง paused

Shared assets อยู่ภายนอก study ใน workspace datasets/models/third_party/.venvs ไม่มีการแก้ต้นฉบับ GT, previous YOLO results หรือ YOLO environment ไม่มี downloads/installs/remote Git actions ใน implementation นี้

รัน application CPU regressions จาก workspace root (คำสั่งครบทั้งหก suites อยู่ใน validation ที่ลิงก์จากชุดเสนอรับรอง):

```bash
.venvs/mhpv2-stage0/bin/python -m unittest discover -s Human_Parsing_MHPv2_Study/tests -p 'test_application_v2*.py'
```

**Next:** ผูก validation context packages ที่ตรวจครบแล้วเข้ากับ execution config/decision ตาม manifests ที่รับรอง และตรวจ fresh execute route แบบ bounded TRAIN ก่อนขออนุมัติ full benchmark ไม่ค้นแหล่ง header หรือรัน smoke ทุกโมเดลซ้ำ
