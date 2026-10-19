"""Publish a reviewable launch candidate without recording benchmark approval."""
from pathlib import Path
from datetime import datetime,timezone
import difflib
import json
import re
import shutil
import subprocess
import sys

S=Path(__file__).resolve().parents[1];W=S.parent
sys.path.insert(0,str(S))
from src.application_v2.policy import load_config,digest
from src.application_v2.artifacts import file_hash
from src.application_v2.validation_launch import validation_plan,require_validation_authorization


def write(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def main():
    run=S/json.loads((S/'provenance/FIRST_COHORT_VALIDATION_LAUNCH_ACTIVE.json').read_text())['run'];rel=str(run.relative_to(S))
    cfg_path=S/'configs/application_v2_first_cohort_v10.yaml';cfg=load_config(cfg_path)
    plan=validation_plan(cfg,S)
    log=(run/'CPU_APPLICATION_TESTS.log').read_text();match=re.search(r'Ran (\d+) tests?',log)
    if not match or int(match[1])!=147 or not log.rstrip().endswith('OK'):raise ValueError('Application tests not verified')
    previous=load_config(S/'configs/application_v2_first_cohort_v9.yaml')
    assert previous['first_cohort']['protocol']==cfg['first_cohort']['protocol']
    original=S/'provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/ORIGINAL_126_BASELINE.json'
    baseline=json.loads(original.read_text());changed=[p for p,h in baseline['protected_hashes_before'].items() if file_hash(W/p)!=h]
    if changed:raise ValueError('Protected artifacts changed: '+str(changed))
    archive_changes=[]
    for name,expected in baseline['original_archive_stats_before'].items():
        stat=(W/name).stat()
        if (stat.st_size,stat.st_mtime_ns)!=(expected['size'],expected['mtime_ns']):archive_changes.append(name)
    if archive_changes:raise ValueError('Original archive stat changed')
    try:require_validation_authorization(cfg,S)
    except ValueError as error:rejected=str(error)
    else:raise ValueError('Launch should be unapproved')
    # Invoke the actual public entry point to prove refusal before output creation.
    output=run/'MUST_NOT_BE_CREATED'
    command=[sys.executable,str(S/'scripts/first_cohort_entrypoint.py'),'--config',str(cfg_path),'--validation-run','--output',str(output)]
    process=subprocess.run(command,cwd=S,capture_output=True,text=True)
    (run/'UNAPPROVED_LAUNCH.log').write_text(process.stdout+process.stderr)
    assert process.returncode!=0 and not output.exists()
    old_run=S/'provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z'
    old_worker=json.loads((old_run/'fresh_train_v1/YOLO26X_FROZEN/RUN.json').read_text())['worker_sha256']
    old_packet=json.loads(next((old_run/'fresh_train_v1/packets/CPI_R50_CIHP').glob('*/record.json')).read_text())
    reused=dict(fresh_TRAIN_worker_unchanged=file_hash(S/'scripts/first_cohort_gpu_worker.py')==old_worker,
        fresh_TRAIN_assembly_scoring_unchanged=file_hash(S/'src/application_v2/first_cohort_fresh.py')==old_packet['adapter_revision'],
        original_fresh_evidence='provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/VALIDATION.json',
        runner_extension='Optional benchmark/population arguments; existing TRAIN defaults unchanged; current application tests rerun',
        new_validation_worker_actual_GPU_execution='NOT_RUN_NO_BENCHMARK_APPROVAL')
    assert reused['fresh_TRAIN_worker_unchanged'] and reused['fresh_TRAIN_assembly_scoring_unchanged']
    freeze=dict(status='CANDIDATE_LOCKED_PENDING_EXPLICIT_USER_APPROVAL',scientific_freeze=False,
        config_path=str(cfg_path.relative_to(S)),config_file_sha256=file_hash(cfg_path),config_content_sha256=digest(cfg),
        decision_record=cfg['decision_record'],decision_file_sha256=file_hash(S/cfg['decision_record']),
        code_hashes=cfg['validation_launch']['code_hashes'],inputs=cfg['validation_launch']['inputs'],
        validation_package=cfg['validation_context_packages'],launch_plan_sha256=file_hash(run/'LAUNCH_PLAN.json'),
        execution_authorized=False,full_benchmark=False,approval='NOT_GRANTED',
        future_activation='Separate explicit approval; new accepted decision/config revision; revalidate plan/hashes before any model loading')
    write(run/'LAUNCH_FREEZE_CANDIDATE.json',freeze)
    validation=dict(status='PASS_PREPARATION_ONLY',timestamp_utc=datetime.now(timezone.utc).isoformat(),
        CPU_application_tests=147,new_launch_tests=9,foundation67='REUSED_PRIOR_UNCHANGED_MODULES_NOT_RERUN',
        protected126_checked=126,protected126_changed=changed,archive_stat_changes=archive_changes,
        mapping_and_five_policies_unchanged=True,launch_plan=plan,
        actual_entrypoint_unapproved_launch_rejected=process.returncode!=0 and not output.exists(),
        authorization_rejection=rejected,prior_fresh_evidence_reuse=reused,
        validation_pixels_read=False,validation_scores_computed=False,GT_packages_regenerated=False,
        model_loading=False,new_inference=False,full_benchmark=False,scientific_freeze=False,
        PPSS_activity=False,new_downloads=False)
    write(run/'VALIDATION.json',validation)
    report='reports/FIRST_COHORT_VALIDATION_LAUNCH_READY_TH_20261016.md'
    (S/report).write_text(f'''# เตรียม launch benchmark กลุ่มแรก — รออนุมัติแยก

16 ตุลาคม 2026 — **PASS_PREPARATION_ONLY**

ปิด bounded integration แล้ว ไม่เปิดประเด็น mapping หรือห้านโยบายเดิมใหม่ รอบนี้เตรียม execution scope ของ validation, ตรวจ launch plan และผูก reproducibility candidate ให้ review ได้ ข้อความความคืบหน้าของผู้ใช้ **ไม่ถือเป็นคำอนุมัติ benchmark** จึงคง `full_benchmark=false`, `execution_authorized=false` และยังไม่ตั้ง config เป็น FROZEN

## ขอบเขตคำอนุมัติที่ขอ

| รายการ | ค่าเดิมที่คงไว้ |
|---|---|
| ระบบ | CPI_R50_CIHP และ CPI_ConvNeXtB_CIHP ใน T3b พร้อม frozen YOLO26x |
| Precision | FP32; native model processing เดิม ไม่ bypass internal detection |
| Main | 4,961 ภาพ; G_loc17,434 / G_sem17,390 ต่อระบบ |
| Reference | 5,000 ภาพ; G_loc17,548 / G_sem17,504 ต่อระบบ |
| Mapping / domain | Accepted V3, ACCEPTED_WITH_INDIRECT_EVIDENCE, released-annotation-relative |
| Association | Prediction-only bbox IoU0.50; YOLO box ↔ native parser box ไม่ใช้ GT |
| Final GT matching | Native parser bbox เป็น evaluation box; IoU0.50 หลัก /0.75 เสริม |
| Native confidence | R50=0.01 / ConvNeXt-B=0.05 ไม่ปรับให้เท่ากันหรือ tune จาก VAL |
| Failure | STRICT_COMPLETE; INCOMPLETE rows และ diagnostics ต้องอยู่ใน report; valid empty เป็น execution success |
| การตีความ | Quality-only; ไม่จัดอันดับเวลา/FPS/VRAM ไม่อ้าง backbone causality หรือ CCTV superiority |

## 1. Inference ครั้งเดียว แล้วรายงานสองประชากร

ใช้ ordered reference manifest5,000 เป็น inference population เดียว Main4,961เป็น subsetเดิม ไม่สั่งรันซ้ำอีกชุด

- YOLO: **5,000 frame jobs** ใช้ detector artifacts ร่วมกับทั้งสอง CPI
- CPI: **10,000 frame jobs** =2 checkpoints ×5,000ภาพ ไม่ใช่19,922งานจากการบวกสอง scoring populations
- Scoring contexts: main9,922 / reference10,000 ผูก membership, original RGB hash, GT/domain และ checkpoint ตาม population
- Shared image/context และ threshold ต้องตรงกันก่อนใช้ per-frame score ร่วมกัน Reporter สร้างคนละ population fingerprint และ comparison revision

หากภาพที่อยู่นอก main แต่ยังอยู่ reference ล้มเหลว mainอาจยังครบได้ ส่วนreferenceต้องคง INCOMPLETE และไม่มี main scoreภายใต้STRICT_COMPLETE ห้ามเปลี่ยนmembershipหลังเห็นผล Mainไม่ใช่การรับรองว่าปลอดtraining exposureทั้งหมด และสอง population ไม่ใช่ independent samples

## 2. สิ่งที่เชื่อมเพิ่ม

- [Config V10](../configs/application_v2_first_cohort_v10.yaml) / [Decision V9](../provenance/APPLICATION_V2_DECISIONS_V9.json): เพิ่ม `validation_launch` เป็น **PROPOSED**; accepted bindings เดิมไม่เปลี่ยน
- [Launch plan](../{rel}/LAUNCH_PLAN.json) ตรวจ exact ordered IDs/roster/settings/counts และใช้ inventoryที่มีhashแล้วจับRGBจากDatasetNinja TARกับGTของCCIHPด้วยbyte SHA ไม่อาศัยชื่อไฟล์อย่างเดียว ไม่มีการอ่านdataset pixelsในรอบนี้
- เพิ่ม `--validation-plan` และ approval-gated `--validation-run` ใน entry point เดิม พร้อม isolated workerสำหรับvalidation; ไม่มีการดาวน์โหลดหรือติดตั้งenvironmentใหม่
- Lazy readerเตรียมตรวจJPEG bytes/strict decoded RGB/dimensions และคืนGTทีละภาพโดยเทียบdecoded contract/person hashesเดิม ไม่มีการสร้างGTpackagesทั้งชุดใหม่
- รักษาnative ID/YOLO opportunityแยกกัน, lossless native/final masks, original-coordinate geometry และconfigured scorer/report เดิม
- Failure ledgerเก็บแต่ละภาพ รวมload failures/worker aborts/unattempted work; ไม่ retryภาพหรือปรับthresholdเพื่อให้ครบ การปล่อยGPU cacheหลังfailureไม่ใช่การรันภาพนั้นซ้ำ

ใหม่ `first_cohort_validation_worker.py` ยัง **NOT_RUN บนGPU** เพราะยังไม่มีคำอนุมัติvalidation inference ไม่ใช้CPUfixturesอ้างว่าvalidationประชากรเต็มรันผ่านแล้ว Model API/processing อิงเส้นทางnativeเดิมที่มีfresh TRAIN evidence; workerและassembly/scoringสำหรับTRAINเดิมยังมีhashตรงหลักฐานรอบก่อน ส่วนrunnerเพิ่มoptional benchmark/population pathและผ่านCPUregressionปัจจุบัน

## 3. ผลตรวจจริงรอบนี้

| ตรวจ | ผลและขอบเขต |
|---|---|
| Application tests | **147ผ่าน** =138เดิม+9สำหรับvalidation launch; [log](../{rel}/CPU_APPLICATION_TESTS.log) |
| Population fixtures | Perfect output, distinct population revisions, excluded-reference failure, context mismatch, threshold-view mismatch ผ่านด้วยsynthetic arrays ไม่ใช่VAL predictions |
| Source readers | Synthetic JPEG/ZIP: strict decode, coordinate mismatch, decoded GT/person contract ผ่าน ไม่ใช้ภาพVALมาตั้งค่า |
| Approval gate | Public `--validation-run` ถูกปฏิเสธก่อนสร้างrun directoryหรือเรียกGPU process; [log](../{rel}/UNAPPROVED_LAUNCH.log) |
| Syntax | ตรวจnew route/workerใช้syntaxที่Python3.9เดิมรองรับ |
| Protected artifacts |126รายการเดิมhashตรงทั้งหมด; archive statตรงbaseline ไม่hasharchiveใหญ่ซ้ำ |
| Foundation67 | ใช้หลักฐานรอบก่อนต่อ; production modulesไม่เปลี่ยน ไม่อ้างว่าเพิ่งรันครบ214tests |
| Mapping/five policies | เหมือนV9ทั้งหมด ไม่ขอรับรองใหม่ |
| GPU/model inference | **ไม่รันในรอบนี้** |

รายละเอียด [validation](../{rel}/VALIDATION.json) / [fixtures](../{rel}/LAUNCH_FIXTURES.log) / [reproducibility candidate](../{rel}/LAUNCH_FREEZE_CANDIDATE.json)

## 4. การล็อก candidate และการอนุมัติ

`LAUNCH_FREEZE_CANDIDATE.json` บันทึกconfig,decision,code,input inventory,GTpackage และlaunch-plan hashesไว้แล้ว เป็น **candidate lockเพื่อreview ไม่ใช่scientific freezeหรือexecution permission**

เมื่อได้รับคำอนุมัติขอบเขตในตารางข้างต้น จึงออกaccepted execution decision/config revision, คงค่าทางวิทยาศาสตร์เดิม ตรวจplan/hashesอีกครั้งและfreezeก่อนเริ่มvalidation inference ไม่ต้องย้อนหาheader รับรองห้านโยบาย หรือขยายroster ปัจจุบันการแก้flagในYAMLอย่างเดียวไม่ผ่านgate

Stage0 integration success ไม่รับรองว่าfull populationจะไม่มีOOM/contract errors หากไม่ครบให้รายงานตามSTRICT_COMPLETE ไม่มีsilent fallbackหรือsuccess-only scoreแทนคะแนนหลัก และไม่เปลี่ยนmetric/denominatorหลังเห็นVAL

## 5. สถานะและคำขออนุมัติ

พร้อมให้พิจารณาอนุมัติ benchmark กลุ่มแรกตามตาราง โดยใช้existing local assetsเท่านั้น ไม่มี checkpoint downloadใหม่ ไม่แตะPPSS, datasetsต้นฉบับ, frozen YOLO weights/results, company CCTV, training, hybridหรือcolor study ไม่commit/push

**WAITING_FOR_USER_APPROVAL — ยังไม่เริ่ม validation inference หรือ full benchmark**
''')
    readme=S/'README.md';old=readme.read_text()
    marker='## หลักฐานก่อนปรับนโยบาย'
    cut=old.index(marker)
    readme.write_text(f'''# Human Parsing Study — Implementation V2

**ล่าสุด16ตุลาคม2026: bounded integrationปิดแล้ว; validation launch candidateเตรียมครบ รอคำอนุมัติbenchmarkแยก**

- [Launch readiness และขอบเขตคำอนุมัติ]({report})
- [Config V10 — launch candidate](configs/application_v2_first_cohort_v10.yaml) · [Decision V9 — launch PROPOSED](provenance/APPLICATION_V2_DECISIONS_V9.json)
- [Launch plan]({rel}/LAUNCH_PLAN.json) · [Candidate hashes]({rel}/LAUNCH_FREEZE_CANDIDATE.json) · [Validation]({rel}/VALIDATION.json)
- [Fresh TRAIN/scoring closureเดิม](reports/FIRST_COHORT_FRESH_TRAIN_SCORING_CLOSURE_TH_20261016.md) · [Current artifacts](provenance/CURRENT_STUDY_ARTIFACTS.json)

ใช้CPI_R50_CIHP/CPI_ConvNeXtB_CIHP+frozen YOLO26xในT3bแบบquality-only เตรียมreference5,000ภาพเป็นinferenceชุดเดียว; main4,961ภาพสะสมคะแนนแยกตามmembership คงmapping/domain/threshold/failure policiesเดิมทั้งหมด ไม่ต้องรับรองซ้ำ

CPUapplication147testsผ่าน Protected126hashตรง; ไม่มีmodel loadingหรือvalidation inferenceในรอบนี้ `full_benchmark=false`, launch PROPOSED, configยังไม่FROZEN การยอมรับรายงานไม่ใช่คำอนุมัติรัน

Current readinessเฉพาะกลุ่มแรก ไม่รับรองทั้ง20variantsหรือfull-population resource feasibility รายงานและstatesย้อนหลังยังเก็บไว้ตามเดิม

'''+old[cut:])
    (S/'reports/STAGE0_NEXT_ACTIONS.md').write_text(f'''# ขั้นตอนถัดไป — รออนุมัติ benchmark กลุ่มแรก

ดู [launch readiness](FIRST_COHORT_VALIDATION_LAUNCH_READY_TH_20261016.md) และ [launch plan](../{rel}/LAUNCH_PLAN.json)

1. Bounded integrationปิดแล้ว ไม่เปิดmapping/five-policy reviewใหม่
2. Validation route/main-reference population bindingเตรียมแล้ว; CPU147testsผ่าน; executionยังปิด
3. **รอคำอนุมัติแยก:** CPI_R50_CIHP/CPI_ConvNeXtB_CIHP+frozen YOLO26x T3b, reference5,000รันครั้งเดียวแล้วรายงานmain4,961แยก, matching0.50/0.75, STRICT_COMPLETE, quality-only ไม่tuneVALหรือจัดอันดับเวลา/VRAM
4. หลังอนุมัติจึงversion accepted execution config/decision ตรวจcandidate hashesและlaunch plan และfreezeก่อนinference ไม่แก้flagอย่างเดียวหรือถือข้อความความคืบหน้าเป็นคำอนุมัติ

ยังไม่รันvalidation, full benchmark, CCTV, PPSS, training, hybridหรือcolor ไม่มีdownloads/remote push
''')
    schema=S/'DATA_SCHEMA.md';old=schema.read_text()
    schema.write_text('''# Human Parsing — Application Output Schema V2

## V10 validation launch candidate — preparation only

`validation_launch` is PROPOSED and bound to Decision V9 without changing the accepted first-cohort protocol. Reference5,000 provides one inference population; main4,961 is a scoring membership subset. Population-specific context expansion preserves the exact image/model/domain bindings from existing packages. A shared score is admissible only if its effective context and matching view match each report. Comparison revisions bind the population role/membership and threshold separately.

`--validation-plan` is metadata-only. `--validation-run` and the isolated validation worker require a separately accepted launch/full-execution decision and FROZEN execution config before dataset/model execution. Current flags remain false. Candidate code/config/input/package hashes do not grant execution permission. Lazy RGB reads verify byte hash plus the prior decoded RGB hash convention (big-endian W/H prefix + RGB bytes); GT reads verify original members and existing decoded person/domain contracts.

'''+old.split('\n',1)[1])
    index_path=S/'provenance/CURRENT_STUDY_ARTIFACTS.json';index=json.loads(index_path.read_text())
    index.update(updated_utc=validation['timestamp_utc'],executable_config='configs/application_v2_first_cohort_v10.yaml',
        decision_record='provenance/APPLICATION_V2_DECISIONS_V9.json',CPU_validation=rel+'/VALIDATION.json',
        current_entry_point_mode='TRAIN_ROUTE_RETAINED_VALIDATION_LAUNCH_PREPARED_NOT_AUTHORIZED',
        validation_launch_report=report,validation_launch_evidence=rel,validation_launch_plan=rel+'/LAUNCH_PLAN.json',
        validation_launch_candidate=rel+'/LAUNCH_FREEZE_CANDIDATE.json',
        scientific_freeze='CANDIDATE_LOCKED_NOT_FROZEN_WAITING_FOR_BENCHMARK_APPROVAL',full_benchmark=False)
    write(index_path,index)
    state_path=S/'STUDY_STATE.json';state=json.loads(state_path.read_text())
    state.update(last_updated_utc=validation['timestamp_utc'],stage='WAITING_FOR_USER_APPROVAL',
        review_gate='VALIDATION_LAUNCH_PREPARED_PENDING_EXPLICIT_BENCHMARK_APPROVAL',current_scope='FIRST_COHORT_VALIDATION_LAUNCH_PREPARATION_ONLY')
    state['current_artifacts'].update(CPU_tests_last_executed=147,CPU_tests_last_executed_scope='APPLICATION_V2_ONLY_67_FOUNDATION_TESTS_REUSED',
        executable_config=index['executable_config'],decision_record=index['decision_record'],validation_launch_report=report)
    state['first_cohort_validation_launch_20261016']=dict(status='PREPARED_NOT_APPROVED',run=rel,report=report,
        main_images=4961,reference_images=5000,one_inference_per_system_image=True,new_model_loading=False,
        new_inference=False,full_benchmark=False,scientific_freeze=False,CPU_application_tests=147,
        current_validation_worker_GPU='NOT_RUN_PENDING_APPROVAL',mapping_and_five_policies='UNCHANGED_ACCEPTED')
    write(state_path,state)
    before=json.loads((run/'BEFORE.json').read_text());oldrows={r['path']:r for r in before};changes=[];patch=[]
    paths=[*S.glob('src/application_v2/*.py'),*S.glob('tests/test_application_v2*.py'),*[S/p for p in [
        'scripts/first_cohort_entrypoint.py','scripts/first_cohort_validation_worker.py','scripts/prepare_first_cohort_validation_launch.py',
        'scripts/publish_first_cohort_validation_launch.py','configs/application_v2_first_cohort_v10.yaml','provenance/APPLICATION_V2_DECISIONS_V9.json',
        'README.md','DATA_SCHEMA.md','STUDY_STATE.json','reports/STAGE0_NEXT_ACTIONS.md','provenance/CURRENT_STUDY_ARTIFACTS.json',report]]]
    for path in paths:
        name=str(path.relative_to(S));dest=run/'source_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        old=oldrows.get(name);checksum=file_hash(path)
        if old and old['sha256']==checksum:continue
        original=(S/old['archive']).read_text() if old else ''
        changes.append(dict(path=name,before_sha256=old['sha256'] if old else None,after_sha256=checksum,archive=old['archive'] if old else None))
        patch.append(''.join(difflib.unified_diff(original.splitlines(True),path.read_text().splitlines(True),fromfile='before/'+name,tofile=name)))
    write(run/'REVISIONS.json',changes);(run/'SOURCE_AND_DOCS.diff').write_text('\n'.join(patch))
    print(json.dumps(dict(status=validation['status'],tests=147,full_benchmark=False,report=report)))


if __name__=='__main__':main()
