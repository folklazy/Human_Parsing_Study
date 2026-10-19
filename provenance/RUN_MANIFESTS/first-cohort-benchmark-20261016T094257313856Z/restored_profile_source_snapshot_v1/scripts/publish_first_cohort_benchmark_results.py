"""Publish only completed execution artifacts; incomplete systems retain null main scores."""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,sys,collections

S=Path(__file__).resolve().parents[1];W=S.parent;sys.path.insert(0,str(S))
from src.application_v2.artifacts import file_hash
from src.application_v2.policy import load_config


def write(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def main():
    run=S/json.loads((S/'provenance/FIRST_COHORT_BENCHMARK_ACTIVE.json').read_text())['run'];rel=str(run.relative_to(S))
    output=run/'execution_restored_detector_v1'
    if not (output/'BENCHMARK_EXECUTION.json').exists():raise ValueError('Execution is not terminal; do not publish final metrics')
    cfg=load_config(S/'configs/application_v2_first_cohort_v12.yaml',benchmark=True)
    metrics=S/'metrics'/run.name;metrics.mkdir(parents=True,exist_ok=False)
    rows=[];diagnostics=[];report_sources=[]
    for role in ['main','reference']:
        for view in ['primary','secondary']:
            path=output/(role.upper()+'_'+view.upper()+'_REPORT.json');report=json.loads(path.read_text());report_sources.append(dict(path=str(path.relative_to(S)),sha256=file_hash(path)))
            for system in report['systems']:
                m=system['main_metrics'];execution=system['execution'];population=system['population']
                row=dict(system_id=system['system_id'],population=role,matching_view=view,IoU_threshold=report['GT_matching_threshold'],status=system['status'],
                    main_score_eligible=system['main_score_eligible'],frames=population['frames'],G_loc=population['G_loc'],G_sem=population['G_sem'],
                    frames_complete=execution['completed'],frames_failed=execution['failed'],frames_invalid=execution['invalid'],frames_not_attempted=execution['not_attempted_or_unscheduled'],
                    Q_person_sem_GT=m['Q_person_sem_GT'] if m else None,TP=m['TP'] if m else None,FP=m['FP'] if m else None,FN=m['FN'] if m else None,
                    localization_recall=m['localization_recall'] if m else None,localization_precision=m['localization_precision'] if m else None)
                if not system['main_score_eligible'] and m is not None:raise ValueError('Incomplete system cannot supply main metrics')
                rows.append(row)
                diagnostic=system['success_only_diagnostic']
                diagnostics.append(dict(system_id=system['system_id'],population=role,matching_view=view,label=diagnostic['label'],**{k:v for k,v in diagnostic.items() if k!='label'}))
    for name,data in [('QUALITY_RESULTS.csv',rows),('OPERATIONAL_SUCCESS_ONLY_DIAGNOSTICS.csv',diagnostics)]:
        with (metrics/name).open('x',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    failure_rows=[];component_summary=[]
    native_components=cfg['validation_launch']['detector_infrastructure_restoration']['native_components']
    for model,directory in [('YOLO26X_FROZEN',output/'YOLO26X_FROZEN'),*[(model,(S/native_components[model]['manifest']).parent) for model in cfg['first_cohort']['models']]]:
        state=json.loads((directory/'RUN.json').read_text());ledger=[json.loads(line) for line in (directory/'FRAMES.jsonl').read_text().splitlines()]
        if len(ledger)!=5000 or len({row['image_id'] for row in ledger})!=5000:raise ValueError('Final source component population incomplete')
        counts=collections.Counter(row['status'] for row in ledger);types=collections.Counter()
        for row in ledger:
            if row['status']=='COMPLETE':continue
            error=row.get('error','');kind='CUDA_OOM' if 'out of memory' in error.lower() else row.get('failure_type','UNKNOWN');types[kind]+=1
            failure_rows.append(dict(component=model,image_id=row['image_id'],status=row['status'],failure_stage=row.get('failure_stage'),failure_kind=kind,
                error_last_line=error.splitlines()[-1] if error else '',retries=row.get('retries',0),source_ledger=str((directory/'FRAMES.jsonl').relative_to(S))))
        component_summary.append(dict(component=model,frames=len(ledger),status=state['status'],complete=counts['COMPLETE'],failed=counts['FAILED'],invalid=counts['INVALID'],failure_types=dict(types)))
    with (metrics/'FAILURES.csv').open('x',newline='') as stream:
        fields=['component','image_id','status','failure_stage','failure_kind','error_last_line','retries','source_ledger'];writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(failure_rows)
    baseline=json.loads((S/'provenance/RUN_MANIFESTS/first-cohort-integration-closure-20261016T084320790538Z/ORIGINAL_126_BASELINE.json').read_text());changed=[p for p,h in baseline['protected_hashes_before'].items() if file_hash(W/p)!=h]
    if changed:raise ValueError('Original protected artifact changed: '+str(changed))
    archive_changes=[]
    for name,expected in baseline['original_archive_stats_before'].items():
        stat=(W/name).stat()
        if (stat.st_size,stat.st_mtime_ns)!=(expected['size'],expected['mtime_ns']):archive_changes.append(name)
    if archive_changes:raise ValueError('Source archive stat changed')
    complete=all(row['main_score_eligible'] for row in rows)
    status='COMPLETE' if complete else 'FINISHED_WITH_INCOMPLETE_SYSTEMS'
    validation=dict(status=status,timestamp_utc=datetime.now(timezone.utc).isoformat(),systems=2,reference_images=5000,main_images=4961,
        original_invalid_shared_detector_trial_retained=True,YOLO_image_inference_passes=1,CPI_image_inference_passes_per_checkpoint=1,
        failed_image_retries=0,mapping_and_thresholds_changed=False,protected126_changed=changed,source_archive_stat_changes=archive_changes,
        original_YOLO_benchmark_modified=False,source_datasets_modified=False,PPSS_activity=False,CCTV_inference=False,
        training=False,hybrid=False,downloads=False,timing_ranking=False,rows=rows,components=component_summary,
        report_sources=report_sources,metrics={p.name:file_hash(p) for p in metrics.iterdir()},
        interpretation='Null main metrics are required by STRICT_COMPLETE; success-only diagnostics do not permit model ranking on differing successful subsets')
    write(run/'FINAL_BENCHMARK_VALIDATION.json',validation)
    report_date=datetime.now(timezone.utc).strftime('%Y%m%d')
    report_path=S/('reports/FIRST_COHORT_T3B_BENCHMARK_REPORT_TH_'+report_date+'.md')
    lines=['# ผล benchmark กลุ่มแรก — CPI สองระบบ + Frozen YOLO26x บน CCIHP','',f'**สถานะ: {status}**','',
        'รันตามคำอนุมัติบน reference 5,000 ภาพหนึ่งครั้งต่อ component แล้วแยกรายงาน main 4,961 / reference 5,000 ตาม membership เดิม ใช้ T3b FP32, coarse body/clothing mapping ที่รับรองด้วยหลักฐานทางอ้อม, association0.50 และ final GT matching0.50/0.75 ไม่มีการ tune จาก VAL หรือเปลี่ยนตัวหารหลังเห็นผล','',
        '## 1. Execution และความล้มเหลว','',
        '| Component | ภาพทั้งหมด | สำเร็จ | Failed | Invalid | สาเหตุที่บันทึก |','|---|---:|---:|---:|---:|---|']
    for component in component_summary:lines.append(f"| {component['component']} | {component['frames']:,} | {component['complete']:,} | {component['failed']:,} | {component['invalid']:,} | {component['failure_types']} |")
    lines.extend(['','YOLO attempt แรกหยุดก่อนโหลดโมเดลเนื่องจาก config validator ดึง SciPy ที่ไม่มีใน YOLO environment จึงคง invalid trial เดิมไว้ และแยก CPU authorization receipt ออกจาก detector worker โดยไม่ติดตั้งหรือแก้ environment เดิม YOLO จึงทำ image inference เพียงครั้งเดียว ไม่ใช่การ retry ภาพที่เคยล้มเหลว ส่วน native CPI outputs และทุก failure ใช้จากการรันเดิมโดยไม่รันภาพซ้ำ','',
        f'[Initial environment event](../{rel}/SHARED_ENVIRONMENT_EVENT.json) · [Original interruption evidence](../{rel}/INITIAL_TRIAL_TERMINATION.json) · [Restored profile freeze](../{rel}/RESTORED_PROFILE_FREEZE.json)','',
        '## 2. คะแนนหลักภายใต้ STRICT_COMPLETE','',
        '| Population | Model | GT IoU | Complete frames | Failed / Invalid | G_loc / G_sem | Status | Q_person_sem_GT หลัก |','|---|---|---:|---:|---:|---:|---|---:|'])
    for row in rows:
        quality=f"{row['Q_person_sem_GT']:.6f}" if row['Q_person_sem_GT'] is not None else 'N/A — INCOMPLETE'
        lines.append(f"| {row['population']} | {row['system_id']} | {row['IoU_threshold']:.2f} | {row['frames_complete']:,}/{row['frames']:,} | {row['frames_failed']:,} / {row['frames_invalid']:,} | {row['G_loc']:,} / {row['G_sem']:,} | {row['status']} | {quality} |")
    lines.extend(['','**N/A ไม่ใช่ศูนย์และไม่ใช่คะแนนคุณภาพต่ำ** หมายถึงระบบไม่มีคะแนนหลักที่ครบประชากรตาม STRICT_COMPLETE รายงานยังคงแถว INCOMPLETE และ diagnostics ตามข้อตกลง','',
        'ภาพที่ไม่อยู่ main แต่ยังอยู่ reference ไม่ทำให้ main ล้มเหลวโดยอัตโนมัติ แต่ทุก failure ภายใน main ยังคงนับตาม population ของ main ไม่มี post-hoc exclusion','',
        'ConvNeXt-B มี ledger เดิม3,779ภาพ ก่อน process หยุดโดยไม่มี terminal manifest พบ output ของภาพ0034896เขียน NPZ ไม่สมบูรณ์ จึงเก็บเป็น INVALID/UNRESOLVED_INTERRUPTION ไม่ซ่อมหรือรันซ้ำ จากนั้นทำเฉพาะ1,220ภาพที่ยังไม่เคยเริ่มด้วย weights/settings เดิม และรวม ledger ตาม reference membership โดยไม่เปลี่ยน source files การโหลดโมเดลเพิ่มเพื่อทำภาพที่ยังไม่เริ่มไม่ใช่การ retryภาพที่ล้มเหลว','',
        '## 3. สิ่งที่ผลนี้บอกได้','',
        '- Observation: ตารางข้างต้นแสดงการรันจริงและ failures ภายใต้ native FP32 configuration บน Tesla T4 ไม่ใช่การรับรองทุกภาพจาก TRAIN smoke สามภาพ','- Interpretation: CUDA OOM เป็นข้อจำกัดของ configuration/resource path ที่รัน ไม่ใช่หลักฐานว่าโมเดลมี semantic accuracy ต่ำ หรือด้อยกว่าด้าน architecture/CCTV robustness','- คะแนน success-only เก็บไว้เพื่อวิเคราะห์การทำงานเท่านั้น หากชุดภาพสำเร็จต่างกัน ห้ามใช้จัดอันดับระบบหรือแทนคะแนนหลัก','- ไม่ปรับ confidence, resolution, precision, taxonomy หรือ chunk native processing หลังดู VAL เพื่อทำให้รอบนี้ผ่าน','',
        '## 4. วิธีการและข้อจำกัด','',
        'เป็น custom CCIHP coarse body/clothing evaluation ไม่ใช่ official native CIHP leaderboard; CIHP prediction taxonomy ถูก project อย่าง explicit ไปยัง CCIHP-derived common targets GT domain เป็น released-annotation-relative, unknown/unsupported GT void ตาม policy เดิม และ native identity แยกจาก YOLO opportunity identity','',
        'TP/FP/FN เป็นผลเทียบ released annotations ภายใต้ bbox matching ที่รับรอง FP ไม่ได้พิสูจน์ว่าไม่มีคนจริง ภาพ main/reference มี membership ซ้อนกันและไม่ใช่ประชากรอิสระ Controlled set ไม่ได้รับรองว่าปลอด checkpoint training exposure ทั้งหมด Mapping confidence ยังคง ACCEPTED_WITH_INDIRECT_EVIDENCE ไม่ใช่ DIRECT_VERIFIED','',
        'ไม่ได้วัด clean repeated timing/FPS/VRAM และไม่สร้าง cost ranking ไม่มีการประเมิน CCTV, training, fine-tuning, hybrid, สีหรือ attributes','',
        '## 5. หลักฐานและขั้นตอนถัดไป','',
        f'- [Canonical quality results](../{metrics.relative_to(S)}/QUALITY_RESULTS.csv)',
        f'- [Operational success-only diagnostics](../{metrics.relative_to(S)}/OPERATIONAL_SUCCESS_ONLY_DIAGNOSTICS.csv) — ไม่ใช่คะแนนหลักและไม่ใช้จัดอันดับ',
        f'- [Failure inventory](../{metrics.relative_to(S)}/FAILURES.csv)',
        f'- [Final validation](../{rel}/FINAL_BENCHMARK_VALIDATION.json)',
        f'- [User approval](../{rel}/USER_APPROVAL.json) · [Original freeze](../{rel}/FREEZE.json)',
        '- หากจะทดลอง precision/resolution/chunking/resource policy ใหม่ ต้องกำหนดเป็น configuration revision และขออนุมัติแยก ไม่เริ่มต่ออัตโนมัติ','',
        '**จบรอบที่อนุมัติ — ไม่เริ่ม experiment เพิ่ม**'])
    with report_path.open('x') as stream:stream.write('\n'.join(lines)+'\n')
    state=json.loads((S/'STUDY_STATE.json').read_text());state.update(stage='FIRST_COHORT_EXECUTION_FINISHED',benchmark_status=status,last_updated_utc=validation['timestamp_utc'],review_gate='FIRST_COHORT_FINISHED_NO_FURTHER_EXPERIMENT_AUTHORIZED')
    state['first_cohort_benchmark_execution_20261016'].update(status=status,restored_config='configs/application_v2_first_cohort_v12.yaml',report=str(report_path.relative_to(S)),metrics=str(metrics.relative_to(S)),validation=str((run/'FINAL_BENCHMARK_VALIDATION.json').relative_to(S)),model_frame_retries=0)
    write(S/'STUDY_STATE.json',state)
    index=json.loads((S/'provenance/CURRENT_STUDY_ARTIFACTS.json').read_text());index.update(executable_config='configs/application_v2_first_cohort_v12.yaml',decision_record='provenance/APPLICATION_V2_DECISIONS_V11.json',benchmark_status=status,benchmark_report=str(report_path.relative_to(S)),benchmark_metrics=str(metrics.relative_to(S)),benchmark_validation=str((run/'FINAL_BENCHMARK_VALIDATION.json').relative_to(S)),current_entry_point_mode='FROZEN_EXECUTION_FINISHED_NO_NEW_EXPERIMENT',benchmark_execution_finished=True)
    write(S/'provenance/CURRENT_STUDY_ARTIFACTS.json',index)
    readme=S/'README.md';old=readme.read_text();head='# Human Parsing Study — Implementation V2\n\n'
    history=old[old.index('## หลักฐานก่อนปรับนโยบาย'):]
    readme.write_text(head+f"**ผลรอบแรก: {status}**\n\n[รายงาน benchmark](reports/{report_path.name}) · [ผลเชิงตัวเลข]({metrics.relative_to(S)}/QUALITY_RESULTS.csv) · [Failures]({metrics.relative_to(S)}/FAILURES.csv) · [Validation]({rel}/FINAL_BENCHMARK_VALIDATION.json)\n\nรัน reference 5,000 ภาพต่อ component ครั้งเดียวและรายงาน main 4,961 แยกตาม membership เดิม ภายใต้ T3b FP32 / matching0.50และ0.75 / STRICT_COMPLETE แถว INCOMPLETE ไม่มีคะแนนหลัก ไม่ใช้ success-only diagnostics จัดอันดับ ระบบและ failures คงอยู่ครบ\n\nแก้ shared detector environment failure ที่เกิดก่อนโหลดโมเดลด้วย isolated receipt bootstrap ไม่แก้ environment/weights/settings และไม่ retry CPI ภาพใด ไม่มี timing ranking, CCTV, training หรือ experiment ถัดไป\n\n"+history)
    (S/'reports/STAGE0_NEXT_ACTIONS.md').write_text('# ขั้นตอนถัดไปหลัง benchmark กลุ่มแรก\n\n'+f'รอบที่อนุมัติสิ้นสุดแล้ว: {status}\n\nดู [รายงานผล]({report_path.name}) และ failure inventory ห้ามใช้ success-only diagnostics แทนคะแนนหลักหรือจัดอันดับข้ามชุดภาพที่สำเร็จต่างกัน\n\nหากต้องการแก้ข้อจำกัด resource ด้วย precision/resolution/native chunking หรือระบบใหม่ ให้พิจารณาเป็น revision ที่ต้องอนุมัติแยก ยังไม่เริ่มงานเหล่านั้น\n')
    print(json.dumps(dict(status=status,report=str(report_path.relative_to(S)),metrics=str(metrics.relative_to(S)),components=component_summary)))


if __name__=='__main__':main()
