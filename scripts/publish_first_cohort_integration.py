"""Publish bounded integration evidence; preserve earlier scientific status records."""
from pathlib import Path
from datetime import datetime, timezone
import json
import platform
import sys

S=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(S))
from src.application_v2.artifacts import file_hash


def main():
    run=S/json.loads((S/'provenance/FIRST_COHORT_INTEGRATION_ACTIVE.json').read_text())['run']
    rel=str(run.relative_to(S))
    valid=json.loads((run/'VALIDATION.json').read_text())
    if valid['status']!='PASS':raise ValueError('Integration validation must pass before publication')
    timestamp=datetime.now(timezone.utc).isoformat()
    report='reports/FIRST_COHORT_FRESH_TRAIN_SCORING_CLOSURE_TH_20261016.md'
    text=f'''# ปิด integration ของ CPI สองระบบ — fresh TRAIN และ configured scoring

ตรวจจริงวันที่ 16 ตุลาคม 2026 — **PASS ในขอบเขต bounded integration; พร้อมเข้าสู่การพิจารณาอนุมัติ benchmark แยก**

รอบนี้ปิดสามงานที่ผู้ใช้ระบุ: ผูก validation packages เดิมกับ executable config/decision, รันโมเดลใหม่บน TRAIN สามภาพเดิม และนำ final packets เข้า configured scorer/report ทั้งสอง matching views สำเร็จ ไม่เปลี่ยน mapping, thresholds, ประชากร หรือห้านโยบายเดิม ไม่ค้น annotation header เพิ่ม และไม่เปิด taxonomy review ใหม่

## 1. Configuration และ validation packages

- [Executable config V9](../configs/application_v2_first_cohort_v9.yaml) / [Decision V8](../provenance/APPLICATION_V2_DECISIONS_V8.json)
- [Config lineage](../{rel}/CONFIG_LINEAGE.json) ยืนยัน mapping/domain/population/matching/runtime ทั้งห้าส่วนเหมือน V8 ทุกค่า
- [Dry-run ปัจจุบัน](../{rel}/DRY_RUN_PLAN.json) เลือก CPI_R50_CIHP และ CPI_ConvNeXtB_CIHP พร้อม YOLO26X_FROZEN dependency เท่านั้น ไม่ใช้ legacy FASHN/20-variant fields เป็น roster
- `validation_context_packages` ผูก manifest และ artifact SHA256 เดิม ตรวจ model templates, native model bindings, common projection, domain policy, population membership และตัวหารกับ config ไม่สร้าง GT packages ใหม่

| Population | Images | System-image contexts | G_loc ต่อระบบ | G_sem ต่อระบบ | การอนุญาตรัน |
|---|---:|---:|---:|---:|---|
| Main overlap-controlled | 4,961 | 9,922 | 17,434 | 17,390 | ไม่อนุญาตในรอบนี้ |
| Source reference | 5,000 | 10,000 | 17,548 | 17,504 | ไม่อนุญาตในรอบนี้ |

Main เป็น subset ของ reference; สองแถวไม่ใช่ประชากรอิสระ และไม่ควรรวมตัวหารเข้าด้วยกัน Controlled set ไม่ได้รับรองว่าปลอด checkpoint training exposure ทุกชนิด [ผล binding](../{rel}/fresh_train_v1/VALIDATION_PACKAGE_BINDINGS.json) เป็น metadata/hash validation ไม่ใช่ validation inference

## 2. Fresh route ที่รันจริง

ใช้ entry point เดียวกัน `scripts/first_cohort_entrypoint.py` กับ V9 และ `--fresh-train` การตรวจ dry-run ไม่โหลดโมเดล ส่วน fresh mode เปิดโหลดได้เฉพาะ TRAIN integration ที่รับรองไว้

**TRAIN IDs:** `0021834`, `0000930`, `0001368` ใช้ cached RGB และ GT ที่ผูก hash ไว้ ตรวจ original JPEG SHA256 และ strict decoded RGB เท่ากับ fixture ก่อน inference ไม่อ่าน validation RGB เพื่อรันโมเดล

| Component | Environment เดิม | Fresh inference | Precision | หน้าที่ |
|---|---|---|---|---|
| Frozen YOLO26x-Seg | `.venv` | 3/3 ภาพ | FP32 | สร้าง predicted person opportunities |
| CPI_R50_CIHP | `.venvs/parser-legacy-cu113` | 3/3 ภาพ | FP32 | Native full-frame parsing แล้ว associate กับ YOLO |
| CPI_ConvNeXtB_CIHP | `.venvs/parser-legacy-cu113` | 3/3 ภาพ | FP32 | Native full-frame parsing แล้ว associate กับ YOLO |

ตรวจ checkpoint hash ใหม่ทั้งสามตัว; CPI ตรวจ source commit/config hash และ strict checkpoint load Native score thresholds คง R50=0.01 / ConvNeXt-B=0.05; YOLO ใช้ imgsz640, conf0.25, IoU0.7, max_det200, retina masks ตาม config เดิม ปิด autocast/TF32 ไม่ติดตั้ง dependencies หรือดาวน์โหลดเพิ่ม

GPU ที่ตรวจจริงคือ Tesla T4 15,360 MiB, driver 580.178.04; ก่อนเริ่มไม่มี compute job อื่น ใช้ subprocess แยกและโหลดทีละโมเดล ไม่ใช่หลักฐาน joint-resident deployment memory หรือ clean timing comparison

| TRAIN image | YOLO opportunities | Native R50 | Native ConvNeXt-B | Final R50 / ConvNeXt-B |
|---|---:|---:|---:|---:|
| 0021834 | 6 | 2 | 2 | 2 / 2 |
| 0000930 | 2 | 2 | 2 | 2 / 2 |
| 0001368 | 2 | 8 | 3 | 2 / 2 |

จำนวน final เท่ากันไม่ได้แปลว่า mask quality หรือ GT coverage เท่ากัน ตารางนี้แสดง execution/identity accounting เท่านั้น Native instances ที่ไม่ associate ยังคงอยู่ใน retained native inventory ไม่ลบเพื่อทำให้จำนวนดูเท่ากัน

[Process attempts](../{rel}/fresh_train_v1/PROCESS_ATTEMPTS.json) / [Worker plan](../{rel}/fresh_train_v1/WORKER_PLAN.json) / [Entry-point log](../{rel}/FRESH_ENTRYPOINT.log) / [Integration result](../{rel}/fresh_train_v1/INTEGRATION.json)

## 3. เส้นทางถึงคะแนนและ report ที่พิสูจน์แล้ว

1. Native API คืน masks บน original grid ตรวจขนาด/label IDs/counts/finite boxes โดยไม่ resize GT
2. Prediction-only association ใช้ YOLO bbox ↔ native parser bbox ที่ IoU0.50 โดยไม่รับ GT
3. Final records รักษา native ID และ YOLO opportunity ID พร้อมกัน เก็บ conditioning bbox แยกจาก evaluation bbox (`NATIVE_PARSER_BOX`)
4. Commit lossless packets จาก fresh outputs และอ่านกลับผ่าน packet integrity validation ก่อน scoring เก็บ native masks/boxes ทั้งชุดไว้ด้วย
5. Project native CIHP labels ด้วย accepted explicit mapping แล้วเรียก `ConfiguredRunner.score_frame` กับ registered TRAIN context และ GT cache เดิม
6. `ConfiguredRunner.comparison_report` รับผลครบ 2 ระบบ × 3 ภาพ ใช้ STRICT_COMPLETE และรายงาน stage rates/denominators ทั้งสองระบบครบ 3/3, G_loc=7 และ G_sem=7 ต่อระบบ

Primary matching0.50 และ secondary0.75 ใช้ config เดียวกัน แต่คนละ effective context fingerprint และ comparison revision ทดสอบว่า secondary scores ไม่สามารถสวมเป็น primary report ได้ Thresholds ไม่ถูกเลือกจากคะแนน

- [Primary frame scores](../{rel}/fresh_train_v1/PRIMARY_FRAME_SCORES.json) / [Primary reporter output](../{rel}/fresh_train_v1/PRIMARY_REPORT.json)
- [Secondary frame scores](../{rel}/fresh_train_v1/SECONDARY_FRAME_SCORES.json) / [Secondary reporter output](../{rel}/fresh_train_v1/SECONDARY_REPORT.json)

ตัวเลขในไฟล์เหล่านี้มีไว้ตรวจ integration บน TRAIN เท่านั้น ไม่ใช้จัดอันดับ เลือกโมเดล ปรับ mapping หรือ threshold ยังไม่มีคะแนน validation และไม่มีผล benchmark ทั้งประชากร การอ่าน packets ที่เพิ่งสร้างไม่ใช่การรับรอง standalone cached re-scoring หรือ full workflow resume

## 4. ชี้แจง 190/131 tests และ 126/37 protected files

| หลักฐาน | ขอบเขตจริง | การใช้ในรอบนี้ |
|---|---|---|
| เดิม 190 tests | Application123 + foundation67 จากอีกห้า suites | ใช้ประวัติเดิมตาม scope |
| ล่าสุดก่อนรอบนี้ 131 | Application เท่านั้น: 123เดิม +8 ข้อสำหรับ evidence/replay | ไม่ใช่ full-suite regression เหลือเพียง131 |
| รอบนี้ {valid['CPU_application_tests']} tests | Application131 +7 checks สำหรับ package binding, dry-run/fresh separation และ secondary scoring binding | รันใหม่ผ่าน พร้อม [log](../{rel}/CPU_APPLICATION_TESTS.log) |
| Foundation67 | MHP-v2 reader/contracts/common metrics25; official compatibility19; reassessment7; CCIHP GT8; quality8 | ไม่รันซ้ำ: test files5 และ production modules9 ไม่เปลี่ยนจากหลักฐานเดิม |
| Protected126 เดิม | YOLO six repositories59 + study67 ซึ่งรวม foundation production modules9 | ตรวจ hash ซ้ำครบ126 ตรงทั้งหมด |
| Protected37 ล่าสุด | Historical configs/taxonomy/records อีกชุด; intersection กับ126เท่ากับ0 | ไม่ใช่ subset และแทน126ไม่ได้ ตรวจซ้ำ35ที่ไม่เกี่ยวPPSS |

สองไฟล์ PPSS ในชุด37ไม่เปิดอ่านหรือ hash ใหม่เพราะพัก PPSS ไว้ อ้างผลเดิมเท่านั้น ไม่อ้างว่าตรวจ37ใหม่ครบในรอบนี้ ชุด126ไม่รวม PPSS [Scope reconciliation พร้อมรายชื่อ/hash](../{rel}/EVIDENCE_SCOPE_RECONCILIATION.json)

Foundation tests อ้างผลผ่าน67จาก revision ก่อน ไม่รวมเป็นจำนวน tests ที่รันใหม่ครั้งนี้ Snapshot test files สำหรับเทียบมาจาก context-closure validation ก่อนหน้า; production modules อยู่ใน original126 baseline ไม่ใช่การอนุมานจากจำนวน tests อย่างเดียว

ตรวจขนาด/mtime ของ CCIHP ZIP และ DatasetNinja TAR ตรง baseline ไม่อ่าน hash archive ใหญ่ซ้ำ และไม่อ้างว่า stat check เท่ากับ cryptographic audit ใหม่ Original measured YOLO CSVs ใน protected list ไม่เปลี่ยน Hash assurance มีขอบเขตเฉพาะไฟล์ที่บันทึก ไม่ใช่การรับรองทุกไฟล์ใน workspace

## 5. ข้อจำกัดและ readiness

**ปิดแล้ว:** validation preparation binding, fresh two-CPI/YOLO TRAIN path, original-coordinate packets, primary/secondary configured scoring และ strict reporting ทั้งหกงาน

**สถานะพร้อม:** เข้าสู่ separate full-benchmark approval review ของกลุ่มแรก quality-only ได้ โดยไม่ต้องวนห้า policies, channel header หรือความถูกต้องครบทุกคลาสใหม่

**ยังไม่อ้าง:** full-validation inference/capacity, production resume/cached scoring, semantic accuracy certification, statistical comparison, cost ranking หรือความเหนือกว่าสำหรับ CCTV Mapping ยังเป็น ACCEPTED_WITH_INDIRECT_EVIDENCE; ข้อจำกัดหลักฐานภาพขา/รองเท้าเดิมยังเปิดเผย แต่ไม่สร้าง gate ใหม่

`full_benchmark=false` และ scientific freeze=false; current executable entry point รับเฉพาะ TRAIN bounded route Validation packages ผูกใน config แล้วแต่ยังไม่ได้เปิด launch บน validation การขยาย execution scope สำหรับประชากรจริงต้องอยู่ในงานที่ได้รับอนุมัติแยก ไม่ถือว่าผ่าน TRAIN สามภาพเท่ากับรันประชากรเต็มสำเร็จ

## 6. ไฟล์และการรักษางานเดิม

เพิ่ม `validation_packages.py`, `first_cohort_fresh.py`, isolated GPU worker และ preparation/validation scripts; แก้ entry point และ runner/context เฉพาะการเชื่อม fresh TRAIN/secondary configured view คง evaluator math และ numeric projections เดิม

[Validation](../{rel}/VALIDATION.json) / [Source changes](../{rel}/SOURCE_REVISIONS.json) / [Source diff](../{rel}/SOURCE.diff) / [Before archive](../{rel}/BEFORE.json) / [Git status](../{rel}/GIT_STATUS_AFTER.json)

Workspace root และ study ยังไม่มี Git repository; จึงเก็บ before/after hashes, source snapshots และ diff แทน ไม่มี commit/push ไม่เปลี่ยน remote ของ YOLO repositories ไม่มี training, downloads, PPSS, CCTV, hybrid หรือ full benchmark

**หยุดที่ WAITING_FOR_USER_APPROVAL — ยังไม่เริ่ม benchmark**
'''
    with (S/report).open('x') as stream:stream.write(text)
    readme=S/'README.md'
    old=readme.read_text();cut=old.index('## หลักฐานก่อนปรับนโยบาย')
    readme.write_text('''# Human Parsing Study — Implementation V2

**ล่าสุด 16 ตุลาคม 2026: fresh TRAIN integration ของ YOLO26x + CPI สองระบบ และ configured scoring/reporting ผ่านแล้ว; รออนุมัติ benchmark แยก**

'''+f'''- [รายงานปิด integration พร้อมขอบเขตหลักฐาน]({report})
- [Executable config V9](configs/application_v2_first_cohort_v9.yaml) · [Decision V8](provenance/APPLICATION_V2_DECISIONS_V8.json)
- [ผล validation]({rel}/VALIDATION.json) · [Scope ของ tests / protected hashes]({rel}/EVIDENCE_SCOPE_RECONCILIATION.json)
- [Accepted CPI mapping V3](taxonomy/APPLICATION_BODY_CLOTHING_CPI_ACCEPTED_V3.json) · [หลักฐาน mapping/ภาพ TRAIN เดิม](reports/CPI_STANDARD_MAPPING_ACCEPTANCE_AND_TRAIN_REPLAY_TH_20261016.md)
- [Current artifact index](provenance/CURRENT_STUDY_ARTIFACTS.json) · [Model registry V6](provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv)

ใช้เฉพาะ CPI_R50_CIHP และ CPI_ConvNeXtB_CIHP ใน T3b, TRAIN3ภาพ/ระบบ: โหลด official weights เดิม → native inference → YOLO association → lossless original-grid packets → configured scorer/report ที่ IoU0.50/0.75 ครบ6งาน ไม่จัดอันดับหรือปรับค่าจากผล คง mapping ACCEPTED_WITH_INDIRECT_EVIDENCE และห้านโยบายเดิม

ผูก validation packages main4,961 / reference5,000 กับ config แล้วโดยไม่สร้าง GT ใหม่ ยังไม่เปิด validation inference และ `full_benchmark=false` Application tests138ผ่านใหม่; foundation67อ้างหลักฐานเดิมพร้อม hashes ไม่อ้างว่ารัน205ข้อใหม่ ตรวจ protected126ครบและชุดล่าสุด35/37โดยไม่เปิดสองไฟล์PPSS

Current readiness ครอบคลุมกลุ่มแรกเท่านั้น Historical Stage0/roster blockers ใน records เก่ายังคงอยู่ ไม่ใช้ผลสองระบบรับรองทั้ง20variants ไม่มี scientific freeze, full benchmark หรือ CCTV test

'''+old[cut:])
    next_path=S/'reports/STAGE0_NEXT_ACTIONS.md'
    next_path.write_text(f'''# ขั้นตอนถัดไป — ปิด integration กลุ่มแรกแล้ว

16 ตุลาคม 2026 — [รายงานล่าสุด](FIRST_COHORT_FRESH_TRAIN_SCORING_CLOSURE_TH_20261016.md)

1. **เสร็จแล้ว:** mapping accepted with indirect evidence; ห้านโยบายเดิมไม่เปลี่ยน ไม่ต้องค้น header หรือรับรองซ้ำ
2. **เสร็จแล้ว:** validation packages เดิมผูก [V9](../configs/application_v2_first_cohort_v9.yaml) / [Decision V8](../provenance/APPLICATION_V2_DECISIONS_V8.json), exact main/reference counts และ hashes ผ่าน ไม่มี GT rebuild
3. **เสร็จแล้ว:** fresh FP32 TRAIN3ภาพ × CPI2ระบบ พร้อม YOLO26x dependency ผ่าน weights→inference→association→original-grid packets→configured scoring/report primary0.50 และ secondary0.75
4. **ขั้นต่อไป:** ผู้ใช้พิจารณาอนุมัติ full benchmark ของสอง CPI ใน T3b แบบ quality-only แยก Current TRAIN entry point ยังไม่เปิด validation launch ห้ามเริ่มจากรายงาน PASS เพียงอย่างเดียว

Application138 testsผ่านใหม่ Foundation67ใช้หลักฐานเดิมพร้อม unchanged dependencies รายละเอียด [evidence scope](../{rel}/EVIDENCE_SCOPE_RECONCILIATION.json) ไม่ใช้131แทน190หรือ37แทน126

ยังไม่ต้องขยาย roster, metrics, taxonomy, smoke ทั้ง21รายการ หรือวัด FPS/VRAM ranking ไม่ทำ PPSS, CCTV, hybrid, training หรือดาวน์โหลดเพิ่ม Original datasets/GT/YOLO results คงเดิม

สถานะ: **WAITING_FOR_USER_APPROVAL**
''')
    schema=S/'DATA_SCHEMA.md'
    text=schema.read_text()
    text=text.replace('full validation packages are materialized/validated but execution activation and fresh execute readiness remain pending.',
        'full validation packages are now config-bound for preparation only; fresh TRAIN execution and configured scoring/reporting passed under V9. Validation execution remains unauthorized.')
    text=text.replace('## Accepted CPI evidence policy and saved TRAIN route — 16 October 2026',
        '''## Current V9 fresh TRAIN integration contract — 16 October 2026

[V9](configs/application_v2_first_cohort_v9.yaml) / [Decision V8](provenance/APPLICATION_V2_DECISIONS_V8.json) authorizes `FRESH_TRAIN_INTEGRATION` for the exact three TRAIN IDs and two CPI systems plus frozen YOLO only. `--dry-run` never loads models; `--fresh-train` uses isolated existing environments and verifies checkpoint/config/input hashes. Validation packages bind hashes, roster, model templates, population memberships and denominators with `role=PREPARATION_ONLY`, `execution_authorized=false`.

Fresh final native packets are committed losslessly, verified on read, then explicitly projected into the accepted target space before configured scoring. `matching_view=primary|secondary` selects only the configured0.50/0.75 values. Effective context fingerprints prevent secondary scores from supplying a primary report. Immediate scoring of just-created packets is tested; standalone cached re-scoring and full workflow resume remain disabled. The six TRAIN contexts do not activate validation execution. Full benchmark and freeze remain false.

## Historical V8 evidence policy and saved TRAIN route — 16 October 2026''')
    schema.write_text(text)
    index_path=S/'provenance/CURRENT_STUDY_ARTIFACTS.json';index=json.loads(index_path.read_text())
    index.update(updated_utc=timestamp,executable_config='configs/application_v2_first_cohort_v9.yaml',
        decision_record='provenance/APPLICATION_V2_DECISIONS_V8.json',CPU_validation=rel+'/VALIDATION.json',
        scientific_freeze='NOT_FROZEN_WAITING_FOR_SEPARATE_BENCHMARK_APPROVAL',
        context_registry='SIX_TRAIN_CONTEXTS_SCORING_TESTED_VALIDATION_PACKAGES_BOUND_PREPARATION_ONLY',
        current_entry_point_mode='DRY_RUN_AND_FRESH_TRAIN_INTEGRATION',
        accepted_population_contexts='TRAIN_ACTIVE_VALIDATION_BOUND_NOT_EXECUTION_AUTHORIZED',
        runner_wiring_preparation='FRESH_TRAIN_AND_CONFIGURED_SCORING_REPORTING_PASS',
        first_cohort_dry_run=rel+'/DRY_RUN_PLAN.json',first_cohort_fresh_integration=rel+'/fresh_train_v1/INTEGRATION.json',
        first_cohort_integration_report=report,evidence_scope=rel+'/EVIDENCE_SCOPE_RECONCILIATION.json',
        first_cohort_policy_status='UNCHANGED_ACCEPTED_INDIRECT_EVIDENCE_INTEGRATION_CLOSED_NOT_FROZEN')
    index_path.write_text(json.dumps(index,indent=2)+'\n')
    state_path=S/'STUDY_STATE.json';state=json.loads(state_path.read_text())
    state.update(last_updated_utc=timestamp,stage='WAITING_FOR_USER_APPROVAL',
        stage0_overall_status_scope='HISTORICAL_FULL_ROSTER_ASSESSMENT_NOT_CURRENT_TWO_CPI_INTEGRATION',
        current_scope='TWO_CPI_T3B_QUALITY_ONLY_INTEGRATION',
        review_gate='BOUNDED_INTEGRATION_CLOSED_WAITING_FOR_SEPARATE_FULL_BENCHMARK_APPROVAL')
    state['current_artifacts'].update(CPU_tests_last_executed=138,CPU_tests_last_executed_scope='APPLICATION_V2_ONLY_67_FOUNDATION_TESTS_REUSED',
        integration_report=report,integration_evidence=rel,executable_config=index['executable_config'],decision_record=index['decision_record'])
    state['first_cohort_fresh_integration_closure_20261016']=dict(status='PASS_BOUNDED_INTEGRATION_WAITING_FOR_USER_APPROVAL',
        report=report,run=rel,config=index['executable_config'],decision_record=index['decision_record'],
        mapping_policy='UNCHANGED_ACCEPTED_WITH_INDIRECT_EVIDENCE',validation_packages='BOUND_PREPARATION_ONLY',
        GT_regenerated=False,new_TRAIN_inference=True,fresh_route='PASS',scorer_reporter='PASS_PRIMARY_AND_SECONDARY',
        CPU_application_tests=138,foundation_67_tests='REUSED_UNCHANGED_DEPENDENCIES',
        protected126_unchanged=True,scientific_freeze=False,full_benchmark=False)
    state_path.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n')
    import numpy,scipy,yaml
    (run/'ENVIRONMENT_CPU.json').write_text(json.dumps(dict(python=sys.version,platform=platform.platform(),
        numpy=numpy.__version__,scipy=scipy.__version__,yaml=yaml.__version__,packages_installed=False),indent=2)+'\n')
    revisions=[]
    for row in json.loads((run/'BEFORE.json').read_text()):
        current=file_hash(S/row['path'])
        if current!=row['before_sha256']:
            revisions.append(dict(row,after_sha256=current,reason='Close current first-cohort integration and update evidence navigation',timestamp_utc=timestamp))
    (run/'DOCUMENT_AND_SOURCE_REVISIONS.json').write_text(json.dumps(revisions,indent=2)+'\n')
    print(report)


if __name__=='__main__':main()
