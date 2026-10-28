"""One CPI ConvNeXt-B worker, automatic validation/report, then exit without another model."""
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import argparse,csv,hashlib,json,os,subprocess,sys,time,traceback,difflib
from reconcile_cihp_continuation import validate_folder,write
from continue_cihp_batch import assemble_model,LIMITATIONS
from run_cpi_convnext_shared_segment import derive_shared,validate_policy
P=Path(__file__).resolve().parents[1];W=P.parent;MID='CPI_ConvNeXtB_CIHP'
sys.path.insert(0,str(P/'src'))
from cihp_benchmark.data import file_hash,LABELS

def stamp():return datetime.now(timezone.utc).isoformat()
def gpu():
    return {'utc':stamp(),'GPU':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.used,memory.free,utilization.gpu','--format=csv,noheader'],text=True).strip(),'compute_PIDs':subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).split()}

def prepare(parent,root):
    cfg=json.loads((parent/'FROZEN_CONFIG.json').read_text());digest=file_hash(parent/'FROZEN_CONFIG.json');assert file_hash(P/'configs/cihp_native_six.json')==digest
    for path,h in cfg['source_bindings'].items():assert file_hash(W/path)==h
    spec=cfg['models'][MID];assert file_hash(W/spec['checkpoint'])==spec['checkpoint_sha256'];assert file_hash(W/spec['native_config'])==spec['native_config_sha256'];assert subprocess.check_output(['git','-C',str(W/spec['source']),'rev-parse','HEAD'],text=True).strip()==spec['source_commit']
    population={r['id']:r for r in json.loads((parent/'FROZEN_POPULATION.json').read_text())['members']};assert len(population)==5000;assert file_hash(parent/'FROZEN_POPULATION.json')==cfg['dataset']['population_sha256'];detector={r['image_id']:r for r in map(json.loads,(W/cfg['frozen_YOLO']['validation_ledger']).read_text().splitlines())}
    root.mkdir(parents=True,exist_ok=False);history=[parent/'validation'/MID]+list(parent.glob('continuations/*/segments/'+MID))+list(parent.glob('rounds/*/segments/'+MID));audits=[];seen=set();prior_bytes=0
    for i,folder in enumerate(history):
        audit=root/'reuse_audits'/str(i);d=validate_folder(folder,cfg,population,detector,audit,digest)
        if seen&set(d['verified_ids']):raise ValueError('Duplicate prior CPI ConvNeXt-B output; no score-based choice permitted')
        seen.update(d['verified_ids']);audits.append(str(audit.relative_to(W)));prior_bytes+=sum(f.stat().st_size for f in folder.rglob('*') if f.is_file()) if folder.exists() else 0
    pending=[i for i in population if i not in seen]
    if not pending:raise ValueError('No remaining CPI ConvNeXt-B work; close from existing artifacts without launch')
    policy={'mode':'SHARED_GPU_QUALITY_ONLY','authorized_models':[MID],'quality_only':True,'timing_ranking_allowed':False,'authorization':'User explicitly authorizes SHARED_GPU_QUALITY_ONLY for this CPI ConvNeXt-B round, prioritizing quality/completeness over speed; supersedes previous admission gate only','changes':['Allow other compute PIDs at admission; resource policy override only, not model/scoring changes'],'unchanged':['FP32','checkpoint','population','preprocessing/TTA','YOLO cache','ownership/association','scorer','24h cap','80GiB stream cap','50GiB disk guard','model/OOM retries0','no CPU/FP16 fallback'],'limitations':['Shared execution can affect latency/free VRAM and may cause OOM; no guarantee of identical numerical outcomes','No clean speed or joint-residency VRAM ranking','No process of another project is modified'],'admission_snapshot':gpu(),'controller_wallclock_cap_hours':cfg['max_system_hours']}
    policy.update(diagnostic_required=True,diagnostic_ID='0000018',diagnostic_canonical_reuse=False,R50_paused=True,authority='Current user explicitly authorizes ConvNeXt-B shared-quality warmup, one VAL0000018 diagnostic, then canonical5000 only if diagnostic passes; no retries or settings changes')
    validate_policy(policy,MID);write(root/'RESOURCE_POLICY.json',policy)
    expanded=derive_shared((P/'scripts/run_cihp_system.py').read_text());(root/'EXPANDED_WORKER.py').write_text(expanded);(root/'CONTROL_DIFF.patch').write_text(''.join(difflib.unified_diff((P/'scripts/run_cihp_system.py').read_text().splitlines(True),expanded.splitlines(True),fromfile='frozen_worker',tofile='CPI ConvNeXt-B_shared_resource_and_segment_control',n=0)))
    manifest={'parent_run_id':parent.name,'continuation_id':root.name,'model_id':MID,'config':'Human_Parsing_Benchmark/configs/cihp_native_six.json','config_sha256':digest,'pending_ids':pending,'reused_ids':[i for i in population if i in seen],'prior_execution_seconds':0,'prior_retained_bytes':prior_bytes,'frozen_worker_sha256':file_hash(P/'scripts/run_cihp_system.py'),'base_segment_wrapper_sha256':file_hash(P/'scripts/run_cihp_segment.py'),'expanded_worker_sha256':hashlib.sha256(expanded.encode()).hexdigest(),'wrapper_sha256':file_hash(P/'scripts/run_cpi_convnext_shared_segment.py'),'CPI_resource_template_sha256':file_hash(P/'scripts/run_cpi_r50_shared_segment.py'),'resource_policy':str((root/'RESOURCE_POLICY.json').relative_to(W)),'resource_policy_sha256':file_hash(root/'RESOURCE_POLICY.json'),'shared_GPU_quality_only':True,'reuse_audits':audits,'model_retries':0,'extra_TRAIN_warmup_ID':'0000930'}
    if seen:raise ValueError('Prior completed CPI ConvNeXt-B found: cumulative execution time must be reconciled before a new launch')
    manifest['controller_sha256']=file_hash(__file__)
    manifest['resource_control_template_sha256']=file_hash(P/'scripts/run_rpr_shared_segment.py')
    write(root/'SEGMENT_PLAN.json',manifest);write(root/'ROUND_STATUS.json',{'status':'READY_NOT_LAUNCHED','model_id':MID,'parent_run_id':parent.name,'round_id':root.name,'reused':len(seen),'remaining':len(pending),'expected':5000,'resource_policy':policy['mode'],'queue':[MID]})

def report(root,parent,state,metric,checks):
    now=stamp();ict=datetime.now(ZoneInfo('Asia/Bangkok')).isoformat();unit=root.name;out=P/'runs'/parent.name/unit;out.mkdir(parents=True,exist_ok=True);summary={**state,'closure_utc':now,'closure_Bangkok':ict,'checks':checks,'metrics':metric,'raw_root':str(root.relative_to(W)),'limitations':LIMITATIONS+['Shared GPU quality-only execution; latency/free VRAM/other workloads can vary. No timing ranking.'],'new_other_model_jobs':0,'diagnostic':json.loads((root/'DIAGNOSTIC_RESULT.json').read_text())};write(out/'COMPLETION.json',summary)
    metricsdir=P/'metrics'/unit;metricsdir.mkdir(parents=True,exist_ok=False)
    with (metricsdir/'SUMMARY.csv').open('x',newline='') as f:
        row={k:state.get(k) for k in ['status','expected','complete','failed','invalid','not_attempted','duplicate_IDs','missing_IDs']};row.update(model_id=MID,mIoU_20=metric.get('primary',{}).get('mIoU_20_including_BG') if metric.get('primary') else None,mIoU_FG19=metric.get('primary',{}).get('mIoU_19_foreground') if metric.get('primary') else None,timing_rank_eligible=False);writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader();writer.writerow(row)
    with (metricsdir/'PER_CLASS.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['class_id','class_name','IoU','GT_pixels']);writer.writeheader();primary=metric.get('primary');gt_support=json.loads((parent/'DATA_READINESS.json').read_text())['semantic_values']
        for i,name in enumerate(LABELS):writer.writerow({'class_id':i,'class_name':name,'IoU':primary['IoU'][i] if primary else None,'GT_pixels':primary['GT_pixel_support'][i] if primary else gt_support.get(str(i),0)})
    spec=json.loads((parent/'FROZEN_CONFIG.json').read_text())['models'][MID];primary=metric.get('primary');fmt=lambda v:'null / STRICT_COMPLETE not met' if v is None else f'{100*v:.4f}%'
    text=f'''\n## CPI-Parser ConvNeXt-B CIHP shared-GPU round — terminal {ict}\n\n**{state['status']}**, model `{MID}` (CPI-Parser ConvNeXt-B CIHP). Parent `{parent.name}` / segment `{unit}`. Launch commit `{state.get('launch_commit')}`. Checkpoint `{spec['checkpoint']}`, SHA256 `{spec['checkpoint_sha256']}`; native config `{spec['native_config']}` / SHA256 `{spec['native_config_sha256']}`; source commit `{spec['source_commit']}`; environment `{spec['environment']}`. Frozen scientific config unchanged; effective resource policy is explicit **SHARED_GPU_QUALITY_ONLY** override.\n\nStartedUTC `{state.get('start_utc')}`, endedUTC `{state.get('end_utc')}`, checkedUTC `{now}` / Bangkok `{ict}`. Completed/expected {state.get('complete',0)}/5000; failed {state.get('failed',0)}, invalid {state.get('invalid',0)}, not-attempted {state.get('not_attempted',5000)}, missing IDs {state.get('missing_IDs')}, duplicate IDs {state.get('duplicate_IDs')}. Main native20mIoU inclBG **{fmt(primary['mIoU_20_including_BG'] if primary else None)}**, FG19 **{fmt(primary['mIoU_19_foreground'] if primary else None)}**. No cross-model ranking.\n\n[Canonical completion](../runs/{parent.name}/{unit}/COMPLETION.json), [summary](../metrics/{unit}/SUMMARY.csv), [per-class](../metrics/{unit}/PER_CLASS.csv). Person metrics at0.50/0.75 and native-reference metrics are in canonical completion when complete. Historical EXTERNAL_GPU_BUSY setup attempts are preserved separately; this segment setup status `{state.get('setup_status')}` is distinct from VAL failures. Error `{state.get('error_reason')}`.\n\nScientific policy: CIHP official5000IDs/native20, frozen YOLO cache, native preprocessing/TTA, FP32, association/ownership/scoring unchanged. Only GPU admission policy differs: coexistence allowed by current user direction; original frozen config is retained, not silently edited. This is a YOLO-associated application pipeline, not an official native-parser benchmark reproduction. Timing is shared-GPU adapter diagnostics, including CPI native JPEG decoding and PNG writes/re-reads inside the native API; GT scoring/global semantic composition and canonical packet export remain outside. Not clean parser-only/end-to-end speed ranking; no contention-free claim or quality transfer guarantee. Hard labels/stored ownership retained; full probabilities/native confidence outputs are not all recoverable.\n\nChecks: {checks}. Original model/OOM retry0, no CPU/FP16 fallback. Raw logs/packets/ledgers/audit under `{root.relative_to(W)}`; use ROUND_STATUS.json for terminal state. Queue contains only CPI ConvNeXt-B and has stopped; no R50/matrix/Sapiens/color/training. Next inspect failures if incomplete or review this model's canonical report if complete; no automatic retry or next-model launch.\n'''
    target=P/'reports/CIHP_CONTROLLED_CONTINUATION.md';guards=json.loads((root/'PUBLICATION_GUARDS.json').read_text());files=[str((out/'COMPLETION.json').relative_to(P))]+[str((out/name).relative_to(P)) for name in ['DIAGNOSTIC_RESULT.json','SEGMENT_PLAN.json']]+[str(f.relative_to(P)) for f in metricsdir.glob('*.csv')]
    if file_hash(target)==guards['report']:
        before=target.read_text()
        if file_hash(P/'manifests/CIHP_NATIVE_COHORT_INDEX.json')==guards['index'] and file_hash(P/'metrics/CIHP_NATIVE_COHORT_OVERVIEW.csv')==guards['overview']:
            try:
                from refresh_cpi_r50_overview import refresh
                before=refresh(out/'COMPLETION.json',before);files+=['manifests/CIHP_NATIVE_COHORT_INDEX.json','metrics/CIHP_NATIVE_COHORT_OVERVIEW.csv'];write(root/'OVERVIEW_UPDATE.json',{'status':'UPDATED_FROM_CANONICAL_COMPLETION'})
            except Exception:write(root/'OVERVIEW_UPDATE.json',{'status':'PENDING_REVIEW','error':traceback.format_exc()})
        else:write(root/'OVERVIEW_UPDATE.json',{'status':'PENDING_REVIEW','reason':'Navigation index changed independently; not overwritten'})
        target.write_text(before+text+diagnostic_report_text(root,parent,state))
        files.append(str(target.relative_to(P)))
    else:
        target=P/'reports'/unit/'REPORT_TH.md';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text+diagnostic_report_text(root,parent,state));files.append(str(target.relative_to(P)))
    if file_hash(P/'STATUS.md')==guards['status']:
        (P/'STATUS.md').write_text(f'# Human Parsing Benchmark — current status\n\nUpdated {ict} Bangkok\n\n**CPI_CONVNEXT_ROUND_{state["status"]}**. Queue stopped after CPI ConvNeXt-B only. Completed{state.get("complete",0)}/5000, failed{state.get("failed",0)}, invalid{state.get("invalid",0)}, missing{state.get("missing_IDs")}; STRICT_COMPLETE main metrics null if incomplete. [CPI ConvNeXt-B report]({target.relative_to(P)}) / [completion](runs/{parent.name}/{unit}/COMPLETION.json). Shared-GPU quality-only, no speed ranking. No automatic retry/ConvNeXt/matrix/Sapiens/color.\n');files.append('STATUS.md')
    if file_hash(P/'WORK_LOG.md')==guards['log']:
        with (P/'WORK_LOG.md').open('a') as f:f.write(f'\n## {ict} — {unit}: CPI ConvNeXt-B-only terminal\n\nStatus{state["status"]}, complete{state.get("complete",0)}/5000. Shared resource override explicit; original config/scientific sources unchanged. Canonical artifacts validated; strict null incomplete main scores. Queue stopped; no ConvNeXt/other-model inference. Report{target.relative_to(P)}. No cross-model ranking.\n')
        files.append('WORK_LOG.md')
    from monitor_cihp_batch import publish
    files=[rel for rel in files if not (W/'Human_Parsing_Study_Public/Human_Parsing_Benchmark'/rel).exists() or file_hash(P/rel)!=file_hash(W/'Human_Parsing_Study_Public/Human_Parsing_Benchmark'/rel)]
    try:receipt=publish(root,unit,files,scope='CPI_ConvNeXtB_CIHP-only shared-GPU quality round; compact summary/report/provenance, no masks/images/weights',message='results: close scoped CPI-Parser ConvNeXt-B CIHP shared-GPU quality round')
    except Exception:receipt={'status':'PENDING_SYNC','error':traceback.format_exc()}
    write(root/'PUBLICATION.json',receipt)

def execute_validation(parent,root):
    plan=json.loads((root/'SEGMENT_PLAN.json').read_text());policy=json.loads((root/'RESOURCE_POLICY.json').read_text());validate_policy(policy,MID);cfg=json.loads((parent/'FROZEN_CONFIG.json').read_text());assert file_hash(__file__)==plan['controller_sha256'];assert file_hash(root/'RESOURCE_POLICY.json')==plan['resource_policy_sha256'];assert file_hash(P/'configs/cihp_native_six.json')==plan['config_sha256'];assert not (root/'LAUNCH.json').exists()
    state={'status':'RUNNING','round_id':root.name,'parent_run_id':parent.name,'model_id':MID,'expected':5000,'controller_PID':os.getpid(),'start_utc':stamp(),'launch_commit':subprocess.check_output(['git','-C',str(W/'Human_Parsing_Study_Public'),'rev-parse','HEAD'],text=True).strip(),'frozen_config_sha256':plan['config_sha256'],'resource_policy_sha256':plan['resource_policy_sha256'],'segment_plan_sha256':file_hash(root/'SEGMENT_PLAN.json'),'checkpoint_sha256':cfg['models'][MID]['checkpoint_sha256'],'environment':cfg['models'][MID]['environment'],'resource_mode':policy['mode'],'queue':[MID],'model_retries':0};write(root/'ROUND_STATUS.json',state)
    folder=root/'segments'/MID;folder.parent.mkdir(exist_ok=False);cmd=[str(W/'.venvs/parser-legacy-cu113/bin/python'),'-B',str(P/'scripts/run_cpi_convnext_shared_segment.py'),'--config',str(W/plan['config']),'--model',MID,'--phase','validation','--output',str(folder),'--segment-manifest',str(root/'SEGMENT_PLAN.json')]
    with (root/'WORKER.log').open('x') as log:
        child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT);state.update(worker_PID=child.pid,command=cmd);write(root/'LAUNCH.json',state);write(root/'ROUND_STATUS.json',state);start=time.monotonic()
        with (root/'GPU_HEALTH.jsonl').open('x') as health:
            while child.poll() is None:
                health.write(json.dumps(gpu())+'\n');health.flush()
                if plan['prior_execution_seconds']+time.monotonic()-start>cfg['max_system_hours']*3600:
                    state['watchdog_stop']='24h controller wall-clock cap including setup; worker retains original24h loop cap';child.terminate()
                    try:child.wait(timeout=30)
                    except subprocess.TimeoutExpired:child.kill();child.wait()
                    break
                try:child.wait(timeout=60)
                except subprocess.TimeoutExpired:pass
    state.update(status='POSTFLIGHT',worker_exit_code=child.returncode,end_utc=stamp());write(root/'ROUND_STATUS.json',state);raw=json.loads((folder/'RUN.json').read_text()) if (folder/'RUN.json').exists() else {};metric={'primary':None};checks={}
    try:
        pop={r['id']:r for r in json.loads((parent/'FROZEN_POPULATION.json').read_text())['members']};det={r['image_id']:r for r in map(json.loads,(W/cfg['frozen_YOLO']['validation_ledger']).read_text().splitlines())}
        validate_folder(folder,cfg,pop,det,root/'final_audit'/MID,plan['config_sha256'],allow_noncomplete=True);audits=[W/p for p in plan['reuse_audits']]+[root/'final_audit'/MID];assembled=root/'assembled';assembled.mkdir();assembled_status=assemble_model(parent,assembled,cfg,MID,audits);metric=json.loads((assembled/'validation'/MID/'METRICS.json').read_text());state.update(assembled_status);state['duplicate_IDs']=0;state['missing_IDs']=5000-state['complete'];checks={'hashes_metadata_NPZ_CRC_GT_and_saved_mask_rescore':'PASS','exact_expected_ID_union':state['status']=='COMPLETE','no_duplicate_IDs':True,'source_artifacts_preserved':True}
    except Exception:
        state.update(status='INCOMPLETE_REQUIRES_RECONCILIATION',complete=0,failed=raw.get('failed',0),invalid=raw.get('invalid',0),not_attempted=raw.get('not_attempted',5000),duplicate_IDs=None,missing_IDs=None,error_reason=traceback.format_exc());checks={'artifact_reconciliation':'FAILED; inspect final_audit/raw artifacts; no automatic retry'}
    state['worker_terminal_status']=raw.get('status','NO_WORKER_RECORD');state['setup_status']='PASS' if raw.get('warmup_images') else 'BLOCKED_OR_FAILED_SETUP';state['error_reason']=state.get('error_reason',raw.get('error',raw.get('stop_reason')));state['queue_stopped']=True;write(root/'ROUND_STATUS.json',state);report(root,parent,state,metric,checks)

def diagnostic_report_text(root,parent,state):
    d=json.loads((root/'DIAGNOSTIC_RESULT.json').read_text());base=f'../runs/{parent.name}/{root.name}'
    return f'''\n## CPI ConvNeXt-B — diagnostic และสถานะรอบนี้\n\nใช้ checkpoint/config ของ `{MID}` เท่านั้น ไม่ใช่ R50; R50พักไว้และเก็บ3successful IDs/สองfailure attempts/คะแนนหลักnullเหมือนเดิม รอบ `{root.name}` ใช้ SHARED_GPU_QUALITY_ONLY ที่ผู้ใช้อนุมัติโดยตรง ไม่เปลี่ยนFP32/resolution/TTA/threshold0.05/batch/YOLOcache/ownership/GT/scorer และไม่แตะGPUprocessอื่น\n\nDiagnostic0000018 **{d['status']}** หลังTRAINwarmupตามprotocol; เวลาไทยเริ่ม `{d['start_Bangkok']}` / จบ `{d['end_Bangkok']}`. Geometry `{d.get('geometry')}`; peak `{d.get('peak_memory')}` เป็นshared diagnostics ผลnative mask/NPZ/metadata contract `{d.get('contract_check')}`; error `{d.get('error')}`. [รายละเอียดdiagnostic]({base}/DIAGNOSTIC_RESULT.json) ระบุinput/transformedgeometryและtracebackที่ตรวจได้ ไม่ใช้คะแนนdiagnosticปรับsettingsหรือรวมcanonicalmetrics\n\nFull validation status **{state['status']}**, complete{state.get('complete',0)}/5000,failedVAL{state.get('failed',0)},invalid{state.get('invalid',0)},notattempted{state.get('not_attempted',5000)},missing{state.get('missing_IDs')},duplicate{state.get('duplicate_IDs')}. DiagnosticfailureแยกจากVALfailure; ถ้าdiagnosticไม่ผ่านไม่มีcanonicalVALinference ถ้าผ่านcanonical0000018ยังต้องรันตามลำดับpopulationปกติ ไม่reusepacketdiagnostic การผ่านหนึ่งภาพไม่รับรองทุกภาพ ค่าdiagnosticwallclock{d['wallclock_seconds']:.3f}s/bytes{d['retained_bytes']}ถูกคิดแยกและนำเข้าบัญชีresource24h/80GiB; คงfree-spaceguard50GiBและautomaticretry0\n\nผลเป็นYOLO-associated application pipelineบนnativeCIHPlabels ไม่ใช่officialnative-parser reproduction STRICT_COMPLETEคะแนนหลักnullหากไม่ครบ TimingรวมCPI internalJPEGdecode/nativePNGwrites/re-reads เป็นadapter diagnostics ไม่ใช่parser-only/end-to-end latency/FPS/VRAMranking No R50/matrix/Sapiens/color/training. Rawlogs/packets/geometry/peakอยู่ `{root.relative_to(W)}` และREPORT/STATUSนี้เป็นจุดเริ่มอ่าน ไม่รันแก้OOMยาวหรือเปลี่ยนวิธีคำนวณในรอบนี้\n'''

def execute_diagnostic_then_validation(parent,root):
    plan=json.loads((root/'SEGMENT_PLAN.json').read_text());cfg=json.loads((parent/'FROZEN_CONFIG.json').read_text());assert plan['model_id']==MID
    assert file_hash(__file__)==plan['controller_sha256'];assert not (root/'DIAGNOSTIC_RESULT.json').exists() and not (root/'LAUNCH.json').exists()
    started=stamp();began=time.monotonic();diagnostic=root/'diagnostic';diagplan={**plan,'pending_ids':['0000018'],'reused_ids':[],'diagnostic_only':True,'scope':'READINESS_DIAGNOSTIC_ONLY_NOT_CANONICAL','prior_execution_seconds':0}
    write(root/'DIAGNOSTIC_PLAN.json',diagplan)
    cmd=[str(W/'.venvs/parser-legacy-cu113/bin/python'),'-B',str(P/'scripts/run_cpi_convnext_shared_segment.py'),'--config',str(W/plan['config']),'--model',MID,'--phase','validation','--output',str(diagnostic),'--segment-manifest',str(root/'DIAGNOSTIC_PLAN.json')]
    state={'status':'RUNNING_DIAGNOSTIC','round_id':root.name,'parent_run_id':parent.name,'model_id':MID,'expected':5000,'complete':0,'controller_PID':os.getpid(),'start_utc':started,'resource_mode':'SHARED_GPU_QUALITY_ONLY','queue':[MID]};write(root/'ROUND_STATUS.json',state)
    with (root/'DIAGNOSTIC.log').open('x') as log:
        child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT);state['worker_PID']=child.pid;write(root/'ROUND_STATUS.json',state);write(root/'DIAGNOSTIC_LAUNCH.json',{'command':cmd,**state})
        try:child.wait(timeout=max(1,cfg['max_system_hours']*3600-plan['prior_execution_seconds']))
        except subprocess.TimeoutExpired:
            child.terminate()
            try:child.wait(timeout=30)
            except subprocess.TimeoutExpired:child.kill();child.wait()
    raw=json.loads((diagnostic/'RUN.json').read_text()) if (diagnostic/'RUN.json').exists() else {};ledger=[json.loads(x) for x in (diagnostic/'FRAMES.jsonl').read_text().splitlines()] if (diagnostic/'FRAMES.jsonl').exists() else []
    d={'status':'FAILED','model_id':MID,'image_id':'0000018','canonical_eligible':False,'start_utc':started,'start_Bangkok':datetime.fromisoformat(started).astimezone(ZoneInfo('Asia/Bangkok')).isoformat(),'end_Bangkok':datetime.now(ZoneInfo('Asia/Bangkok')).isoformat(),'wallclock_seconds':time.monotonic()-began,'worker_exit_code':child.returncode,'warmup_images':raw.get('warmup_images',[]),'error':raw.get('error',raw.get('stop_reason')),'traceback':next((x.get('error') for x in ledger if x['status']!='COMPLETE'),None),'contract_check':'NOT_TESTED_NO_COMPLETE_PACKET','native_score_threshold':raw.get('model_details',{}).get('native_score_threshold'),'geometry':[json.loads(l) for l in (diagnostic/'INPUT_GEOMETRY.jsonl').read_text().splitlines()] if (diagnostic/'INPUT_GEOMETRY.jsonl').exists() else [],'peak_memory':json.loads((diagnostic/'PEAK_MEMORY.json').read_text()) if (diagnostic/'PEAK_MEMORY.json').exists() else None}
    if child.returncode==0 and raw.get('status')=='COMPLETE' and raw.get('complete')==1 and [x['image_id'] for x in ledger]==['0000018']:
        try:
            import numpy as np
            pop={x['id']:x for x in json.loads((parent/'FROZEN_POPULATION.json').read_text())['members']};det={x['image_id']:x for x in map(json.loads,(W/cfg['frozen_YOLO']['validation_ledger']).read_text().splitlines())}
            audit=validate_folder(diagnostic,cfg,pop,det,root/'diagnostic_audit',plan['config_sha256']);assert audit['verified_ids']==['0000018'];packet=diagnostic/'packets/0000018';meta=json.loads((packet/'packet.json').read_text());schema={}
            with np.load(packet/'prediction.npz',allow_pickle=False) as arrays:
                for key in arrays.files:
                    a=arrays[key];schema[key]={'shape':list(a.shape),'dtype':str(a.dtype)}
                    if 'semantic_masks' in key:
                        assert a.dtype.kind in 'iu' and list(a.shape[-2:])==meta['original_wh'][::-1] and np.all((a>=0)&(a<20));schema[key]['labels']=[int(v) for v in np.unique(a)]
            assert meta['model_id']==MID and meta['checkpoint_sha256']==cfg['models'][MID]['checkpoint_sha256']
            d.update(status='PASS',error=None,contract_check='PASS_NPZ_CRC_HASH_METADATA_GEOMETRY_NATIVE20_GT_SAVED_SCORE',array_schema=schema,packet_sha256=meta['packet_sha256'],packet_metadata_sha256=file_hash(packet/'packet.json'),original_wh=meta['original_wh'])
        except Exception:d.update(error=traceback.format_exc(),contract_check='FAIL_PRESERVE_OUTPUT_NO_VALIDATION')
    d['wallclock_seconds']=time.monotonic()-began;d['end_Bangkok']=datetime.now(ZoneInfo('Asia/Bangkok')).isoformat();d['retained_bytes']=sum(f.stat().st_size for f in root.rglob('*') if f.is_file());write(root/'DIAGNOSTIC_RESULT.json',d);out=P/'runs'/parent.name/root.name;write(out/'DIAGNOSTIC_RESULT.json',d)
    if d['status']!='PASS':
        state.update(status='BLOCKED_DIAGNOSTIC_FAILED',failed=0,invalid=0,not_attempted=5000,missing_IDs=5000,duplicate_IDs=0,queue_stopped=True,setup_status='PASS' if raw.get('warmup_images') else 'FAILED_SETUP',diagnostic_failed=1,error_reason=d['error'],end_utc=stamp(),launch_commit=subprocess.check_output(['git','-C',str(W/'Human_Parsing_Study_Public'),'rev-parse','HEAD'],text=True).strip(),frozen_config_sha256=plan['config_sha256'],checkpoint_sha256=cfg['models'][MID]['checkpoint_sha256'],environment=cfg['models'][MID]['environment']);write(root/'ROUND_STATUS.json',state);report(root,parent,state,{'primary':None},{'diagnostic':d['status'],'canonical_validation':'NOT_STARTED','no_other_models':True});return
    # The diagnostic is never reused; retain all canonical IDs in their frozen order.
    assert len(plan['pending_ids'])+len(plan['reused_ids'])==5000 and '0000018' in plan['pending_ids']
    write(root/'PRE_DIAGNOSTIC_SEGMENT_PLAN.json',plan);plan['prior_execution_seconds']+=d['wallclock_seconds'];plan['prior_retained_bytes']+=d['retained_bytes'];plan['diagnostic_result_sha256']=file_hash(root/'DIAGNOSTIC_RESULT.json');write(root/'SEGMENT_PLAN.json',plan);write(out/'SEGMENT_PLAN.json',plan)
    execute_validation(parent,root)

def main():
    a=argparse.ArgumentParser();a.add_argument('--parent',required=True);a.add_argument('--round-root',required=True);a.add_argument('--prepare',action='store_true');args=a.parse_args();parent=Path(args.parent).resolve();root=Path(args.round_root).resolve();assert root.is_relative_to(parent/'rounds')
    if args.prepare:prepare(parent,root)
    else:execute_diagnostic_then_validation(parent,root)
if __name__=='__main__':main()
