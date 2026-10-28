"""Controlled continuation: reconcile once, execute disjoint work, assemble references."""
from pathlib import Path
from datetime import datetime, timezone
import argparse,difflib,hashlib,json,subprocess,sys,time,traceback,os
import numpy as np
from reconcile_cihp_continuation import validate_folder,write
from run_cihp_segment import derive,validate_partition
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'))
from cihp_benchmark.data import file_hash
from cihp_benchmark.evaluation import semantic_report

LIMITATIONS=[
 'Primary results are YOLO ROI/association pipelines on native CIHP labels, not an official native-parser benchmark for all models.',
 'Timing is adapter diagnostics with unequal I/O boundaries; not clean parser-only or end-to-end speed ranking. CPI native file reads/writes are timed; global semantic composition/scoring is outside the timer.',
 'Historical RPR/CPI TRAIN inference fingerprints repeat across models; never use them alone as cache identity. Reuse here is exclusively hash-validated VAL packets with current model/checkpoint/input/source/config bindings.',
 'Artifacts support hard-label remapping under stored ownership, not every probability/native-confidence evaluation. M2FP/D2FP overlap arbitration precedes export.',
]

def assemble_model(parent,root,config,mid,audits):
    folder=root/'validation'/mid;folder.mkdir(parents=True,exist_ok=False);(folder/'packets').mkdir()
    hist=np.zeros((20,20),np.int64);native=hist.copy();ps={str(t):dict(G_loc=0,G_sem=0,TP=0,FP=0,FN=0,Q_numerator=0.) for t in [.5,.75]};frames=[];failures=[]
    for audit in audits:
        d=json.loads((audit/'RECONCILED.json').read_text());hist+=np.asarray(d['histogram'],np.int64);native+=np.asarray(d['native_histogram'],np.int64)
        for t in ps:
            for k in ps[t]:ps[t][k]+=d['person_sufficient_statistics'][t][k]
        frames.extend(json.loads(line)['frame'] for line in (audit/'VERIFIED_FRAMES.jsonl').open());failures.extend(json.loads((audit/'INVENTORY.json').read_text())['non_complete_ledger'])
    ids=[r['image_id'] for r in frames];assert len(ids)==len(set(ids)),'Duplicate inferred/reused image '+mid
    pop=json.loads((parent/'FROZEN_POPULATION.json').read_text());ordered={r['id']:i for i,r in enumerate(pop['members'])};assert set(ids)<=set(ordered)
    for r in frames:(folder/'packets'/r['image_id']).symlink_to(W/r['packet'],target_is_directory=True)
    ledger=sorted(frames+failures,key=lambda r:ordered[r['image_id']]);assert len({r['image_id'] for r in ledger})==len(ledger)
    with (folder/'FRAMES.jsonl').open('x') as f:
        for r in ledger:f.write(json.dumps(r)+'\n')
    complete=len(ids)==5000 and set(ids)==set(ordered) and not failures
    bad=sum(r['status']=='FAILED' for r in failures);invalid=sum(r['status']=='INVALID' for r in failures)
    status={'model_id':mid,'status':'COMPLETE' if complete else 'INCOMPLETE','expected':5000,'complete':len(ids),'failed':bad,'invalid':invalid,'not_attempted':5000-len(ids)-bad-invalid,'parent_run_id':parent.name,'assembled_from_verified_artifacts':True,'no_reinference_of_reused_ids':True,'audit_locations':[str(d.relative_to(W)) for d in audits]}
    ms=[r['parser_pipeline_seconds']*1000 for r in frames]
    metrics={'primary':semantic_report(hist) if complete else None,'native_reference_primary':semantic_report(native) if complete and config['models'][mid]['native_reference'] else None,'person_metrics':{},'parser_pipeline_ms_mean':float(np.mean(ms)) if complete else None,'parser_pipeline_ms_P50':float(np.median(ms)) if complete else None,'parser_pipeline_ms_P95':float(np.percentile(ms,95)) if complete else None,'timing_scope':'Adapter diagnostics, unequal native I/O; no speed ranking','limitations':LIMITATIONS}
    for t,v in ps.items():
        v.update(extent_precision=v['TP']/(v['TP']+v['FP']) if v['TP']+v['FP'] else None,extent_recall=v['TP']/v['G_loc'] if v['G_loc'] else None,extent_F1=2*v['TP']/(2*v['TP']+v['FP']+v['FN']) if 2*v['TP']+v['FP']+v['FN'] else None,Q_person_sem_GT=v['Q_numerator']/v['G_sem'] if v['G_sem'] else None);metrics['person_metrics'][t]=v if complete else None
    write(folder/'RUN.json',status);write(folder/'METRICS.json',metrics);np.save(folder/'CONFUSION.npy',hist);np.save(folder/'NATIVE_REFERENCE_CONFUSION.npy',native)
    return status

def prepare(parent,cont,config):
    reconciliation=json.loads((cont/'reconciliation/RECONCILIATION.json').read_text());assert reconciliation['status']=='VERIFIED'
    assert file_hash(parent/'FROZEN_CONFIG.json')==reconciliation['config_sha256']
    expanded=derive((P/'scripts/run_cihp_system.py').read_text());(cont/'EXPANDED_SEGMENT_WORKER.py').write_text(expanded)
    (cont/'WORKER_CONTROL_DIFF.patch').write_text(''.join(difflib.unified_diff((P/'scripts/run_cihp_system.py').read_text().splitlines(True),expanded.splitlines(True),fromfile='frozen_worker',tofile='segment_control_only')))
    plans={};(cont/'segment_plans').mkdir(exist_ok=False)
    oldlaunch=json.loads((parent/'LAUNCH.json').read_text())
    for mid in config['execution_models']:
        d=json.loads((cont/'reconciliation'/mid/'RECONCILED.json').read_text());oldfolder=parent/'validation'/mid;prior=0.
        population_ids=[r['id'] for r in json.loads((parent/'FROZEN_POPULATION.json').read_text())['members']]
        validate_partition(population_ids,d['pending_ids'],d['verified_ids'])
        for line in (cont/'reconciliation'/mid/'VERIFIED_FRAMES.jsonl').read_text().splitlines():
            row=json.loads(line)['frame'];assert (W/row['packet']).resolve()==(oldfolder/'packets'/row['image_id']).resolve()
        if mid in oldlaunch['models'] and d['verified_ids']:
            frames=[json.loads(l)['frame'] for l in (cont/'reconciliation'/mid/'VERIFIED_FRAMES.jsonl').open()];prior=(datetime.fromisoformat(frames[-1]['end_utc'])-datetime.fromisoformat(oldlaunch['models'][mid]['start_utc'])).total_seconds()+60
        plan={'parent_run_id':parent.name,'continuation_id':cont.name,'model_id':mid,'config':'Human_Parsing_Benchmark/configs/cihp_native_six.json','config_sha256':file_hash(parent/'FROZEN_CONFIG.json'),'pending_ids':d['pending_ids'],'reused_ids':d['verified_ids'],'prior_execution_seconds':prior,'prior_retained_bytes':sum(f.stat().st_size for f in oldfolder.rglob('*') if f.is_file()) if oldfolder.exists() else 0,'frozen_worker_sha256':file_hash(P/'scripts/run_cihp_system.py'),'expanded_worker_sha256':hashlib.sha256(expanded.encode()).hexdigest(),'wrapper_sha256':file_hash(P/'scripts/run_cihp_segment.py'),'authority':'User authorizes controlled continuation after reconciliation; no successful image reinference','model_retries':0,'additional_TRAIN_warmup':1 if d['pending_ids'] else 0,'lost_inflight_attempt':'Possible next D2FP image execution before interruption has no committed output; cannot prove whether forward completed; this is external-interruption recovery, not retrying a recorded model/OOM failure' if mid=='D2FP_R101_CIHP' else None}
        plan['reconciliation_state_sha256']=file_hash(cont/'reconciliation'/mid/'RECONCILED.json');plan['verified_frames_sha256']=file_hash(cont/'reconciliation'/mid/'VERIFIED_FRAMES.jsonl')
        write(cont/'segment_plans'/(mid+'.json'),plan);plans[mid]=plan
    write(cont/'CONTINUATION_PLAN.json',{'parent_run_id':parent.name,'continuation_id':cont.name,'frozen_config_sha256':file_hash(parent/'FROZEN_CONFIG.json'),'reconciliation_sha256':file_hash(cont/'reconciliation/RECONCILIATION.json'),'models':{m:{'reused':len(d['reused_ids']),'new_jobs':len(d['pending_ids']),'plan_sha256':file_hash(cont/'segment_plans'/(m+'.json'))} for m,d in plans.items()},'limitations':LIMITATIONS,'original_records_modified':False})
    return plans

def execute(parent,cont,config):
    plans={m:json.loads((cont/'segment_plans'/(m+'.json')).read_text()) for m in config['execution_models']}
    binding=json.loads((cont/'CONTINUATION_PLAN.json').read_text())
    for mid,plan in plans.items():
        assert file_hash(cont/'segment_plans'/(mid+'.json'))==binding['models'][mid]['plan_sha256']
        assert file_hash(cont/'reconciliation'/mid/'RECONCILED.json')==plan['reconciliation_state_sha256']
        assert file_hash(cont/'reconciliation'/mid/'VERIFIED_FRAMES.jsonl')==plan['verified_frames_sha256']
    root=cont/'assembled';root.mkdir(exist_ok=False)
    for name in ['FROZEN_CONFIG.json','FROZEN_POPULATION.json','FROZEN_DIAGNOSTIC_SAMPLE.json']: (root/name).write_bytes((parent/name).read_bytes())
    (root/'DATA_READINESS.json').symlink_to(parent/'DATA_READINESS.json');(root/'validation').mkdir();(cont/'segments').mkdir();(cont/'segment_reconciliation').mkdir()
    commit=subprocess.check_output(['git','-C',str(W/'Human_Parsing_Study_Public'),'rev-parse','HEAD'],text=True).strip();old=json.loads((parent/'LAUNCH.json').read_text())
    launch={'run_id':parent.name,'continuation_id':cont.name,'status':'RUNNING','controller_PID':os.getpid(),'code_publication_commit':old['code_publication_commit'],'continuation_code_commit':commit,'config_sha256':file_hash(parent/'FROZEN_CONFIG.json'),'expected_models':config['execution_models'],'models':{},'start_utc':datetime.now(timezone.utc).isoformat()}
    write(root/'LAUNCH.json',launch);write(cont/'CONTINUATION_STATE.json',launch)
    write(root/'CONTINUATION_BINDING.json',{'parent_run_id':parent.name,'continuation_id':cont.name,'continuation_commit':commit,'original_launch_commit':old['code_publication_commit'],'plan_sha256':file_hash(cont/'CONTINUATION_PLAN.json'),'reconciliation':str((cont/'reconciliation/RECONCILIATION.json').relative_to(W)),'limitations':LIMITATIONS,'assembly':'Logical packet symlinks, rebuilt ledgers and recomputed sufficient statistics; no dataset/raw-prediction duplication','original_LAUNCH_RUN_preserved':True})
    population={x['id']:x for x in json.loads((parent/'FROZEN_POPULATION.json').read_text())['members']};detector={x['image_id']:x for x in map(json.loads,(W/config['frozen_YOLO']['validation_ledger']).open())};stop_shared=False
    for mid in config['execution_models']:
        audits=[cont/'reconciliation'/mid];plan=plans[mid];reconciliation_error=None
        if plan['pending_ids'] and not stop_shared:
            cmd=[str(W/'.venvs/parser-legacy-cu113/bin/python'),str(P/'scripts/run_cihp_segment.py'),'--config',str(W/plan['config']),'--model',mid,'--phase','validation','--output',str(cont/'segments'/mid),'--segment-manifest',str(cont/'segment_plans'/(mid+'.json'))]
            with (cont/'segments'/(mid+'.log')).open('x') as log:
                process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);launch['models'][mid]={'status':'RUNNING','PID':process.pid,'command':cmd};write(root/'LAUNCH.json',launch);write(cont/'CONTINUATION_STATE.json',launch);rc=process.wait()
            folder=cont/'segments'/mid
            try:
                validate_folder(folder,config,population,detector,cont/'segment_reconciliation'/mid,launch['config_sha256'],allow_noncomplete=True);audits.append(cont/'segment_reconciliation'/mid)
                run=json.loads((folder/'RUN.json').read_text()) if (folder/'RUN.json').exists() else {};launch['models'][mid].update(segment_status=run.get('status'),exit_code=rc)
                if (folder/'FRAMES.jsonl').exists():
                    bad=[json.loads(l) for l in (folder/'FRAMES.jsonl').open() if json.loads(l)['status']!='COMPLETE']
                    if any(r.get('failure_stage') in ['SCORING','SOURCE_VALIDATION'] and r['status']=='INVALID' for r in bad):stop_shared=True
            except Exception:
                reconciliation_error=traceback.format_exc();write(cont/(mid+'_RECONCILIATION_ERROR.json'),{'error':reconciliation_error});stop_shared=True
        status=assemble_model(parent,root,config,mid,audits)
        segment_run=cont/'segments'/mid/'RUN.json'
        if segment_run.exists():
            original_run=json.loads(segment_run.read_text());status['segment_status']=original_run['status']
            for key in ['error','stop_reason']:
                if key in original_run:status[key]=original_run[key]
            write(root/'validation'/mid/'RUN.json',status)
        if reconciliation_error:
            status.update(error=reconciliation_error,error_stage='ARTIFACT_RECONCILIATION');write(root/'validation'/mid/'RUN.json',status)
        launch['models'].setdefault(mid,{}).update(status);write(root/'LAUNCH.json',launch);write(cont/'CONTINUATION_STATE.json',launch)
    launch['status']='FINISHED_COMPLETE' if all(v['status']=='COMPLETE' for v in launch['models'].values()) else 'FINISHED_WITH_INCOMPLETE_SYSTEMS';launch['end_utc']=datetime.now(timezone.utc).isoformat();write(root/'LAUNCH.json',launch);write(cont/'CONTINUATION_STATE.json',launch)
    print(launch['status'],flush=True)

def main():
    a=argparse.ArgumentParser();a.add_argument('--parent',required=True);a.add_argument('--continuation',required=True);a.add_argument('--prepare',action='store_true');args=a.parse_args();parent=Path(args.parent).resolve();cont=Path(args.continuation).resolve();config=json.loads((parent/'FROZEN_CONFIG.json').read_text())
    if args.prepare:prepare(parent,cont,config)
    else:execute(parent,cont,config)
if __name__=='__main__':main()
