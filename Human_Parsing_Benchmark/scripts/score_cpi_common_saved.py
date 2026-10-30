"""Saved-only CPI C4-P revision2 orchestration; imports no model or GPU framework.

Resume only explicit --resume, with immutable atomic score/ledger bindings.
Native results, packets, ownership and the accepted common scorer are read-only.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse, fcntl, json, os, sys, time, shutil, traceback
import numpy as np

P = Path(__file__).resolve().parents[1]
W = P.parent
sys.path[:0] = [str(P/'src'), str(P/'scripts')]
from common_view.core import sha_file, load_spec, project, compose_native, semantic_metrics
from common_view.full import Accumulator, score_people, project_confusion, native_confusion
from common_view.packets import atomic_json, fingerprint
from run_common_full import read_inputs, load_gt

SPACE = 'CIHP_GT_AND_NATIVE_PRED'
RUNS = {'CPI_R50_CIHP': 'r50-20261029T183615747685Z',
        'CPI_ConvNeXtB_CIHP': 'convnext-20261029T160359716460Z'}

def utc(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text())
def rows(p):
    with Path(p).open() as f:
        for line in f:
            if line.strip(): yield json.loads(line)
def emit(f, value):
    f.write(json.dumps(value, allow_nan=False)+'\n'); f.flush(); os.fsync(f.fileno())

def prepare(run):
    root=P/'outputs/common_view'/run; root.mkdir(parents=True, exist_ok=False)
    record=P/'runs'/run; record.mkdir(parents=True, exist_ok=False)
    old=read(P/'configs/cihp_sapiens_c4p_full.json')
    c={k:old[k] for k in ['protocol','protocol_sha256','native_population','native_population_sha256',
       'GT_binding_root','GT_manifest_sha256','GT_summary','YOLO','expected_ids','minimum_free_gib','max_stream_gib','max_hours']}
    assert sha_file(W/c['protocol'])==c['protocol_sha256']
    assert sha_file(W/c['native_population'])==c['native_population_sha256']
    bindings,spec=read_inputs(c)
    ids=c['expected_ids']; pop={x['id']:x for x in read(W/c['native_population'])['members']}
    assert len(ids)==len(set(ids))==5000 and set(ids)==set(pop)==set(bindings)
    actual={k:sum(b[k] for b in bindings.values()) for k in ['G_loc','G_sem_C4']}
    assert actual=={k:c['GT_summary'][k] for k in actual}
    c.update(run_id=run,artifact_root=str(root.relative_to(W)),record_root=str(record.relative_to(W)),
      scope='SAVED_ONLY_CPI_COMMON_C4P_REVISION2',models={},model_inference=False,
      resource_policy='CPU_SAVED_ARTIFACTS_ONLY; source GPU runs SHARED_GPU_QUALITY_ONLY',
      source_hashes={str(f.relative_to(W)):sha_file(f) for f in [Path(__file__),P/'src/common_view/core.py',P/'src/common_view/full.py',P/'src/common_view/packets.py',P/'scripts/run_common_full.py',P/'src/cihp_benchmark/data.py']})
    native=read(P/'configs/cihp_native_six.json'); nhash=sha_file(P/'configs/cihp_native_six.json')
    detector={x['image_id']:x for x in rows(W/c['YOLO']['validation_ledger'])}
    compatibility={'run_id':run,'created_utc':utc(),'status':'PACKET_CONTRACT_COMPATIBLE',
       'inference':False,'denominators_from_GT_bindings':actual,'models':{},
       'equivalence_limit':'Bounded CPU/GPU parity and sample output equality, not population-wide bitwise equivalence to unmodified native inference.',
       'different_evidence':{'forward':'CPU/GPU function fixtures and named model-image regressions',
       'integrity':'prior per-packet NPZ/CRC/metadata audits plus current small metadata bindings and required array decoding',
       'scorer':'prior native saved-mask scorer agreement; new common person metrics calculated with unchanged revision2'}}
    for mid,source_run in RUNS.items():
        sr=P/'outputs/cpi_continuations'/source_run; comp=read(sr/'COMPLETION.json');plan=read(sr/'SEGMENT_PLAN.json')
        assert comp['status']=='COMPLETE' and comp['complete']==5000
        assert comp==read(P/'runs'/source_run/'COMPLETION.json')
        assert plan['config_sha256']==nhash
        entries={}; hist=np.zeros((20,20),np.int64); segments=[]; revisions=Counter()
        audits=plan['reuse_audits']+[str((sr/'final_audit'/mid).relative_to(W))]
        for auditrel in audits:
            audit=W/auditrel; rr=read(audit/'RECONCILED.json')
            verified=audit/'VERIFIED_FRAMES.jsonl'
            assert sha_file(verified)==rr['verified_ledger_sha256']
            hist+=np.asarray(rr['histogram'],np.int64); segment_counts=Counter()
            count=0
            for v in rows(verified):
                assert v['NPZ_all_members_decoded_CRC_checked'] and v['independent_saved_mask_rescore_matches']
                frame=v['frame']; iid=frame['image_id']; packet=W/frame['packet']; meta=read(packet/'packet.json')
                assert iid not in entries and iid in pop
                assert sha_file(packet/'packet.json')==v['metadata_sha256']
                for k,value in dict(model_id=mid,image_id=iid,checkpoint_sha256=native['models'][mid]['checkpoint_sha256'],
                     source_commit=native['models'][mid]['source_commit'],config_sha256=nhash,original_wh=pop[iid]['wh'],
                     input_sha256=pop[iid]['RGB_sha256'],precision='FP32',label_space='CIHP_NATIVE_20',
                     detector_artifact_sha256=detector[iid]['artifact_sha256'],packet_sha256=frame['packet_sha256']).items():
                    assert meta[k]==value,(mid,iid,k)
                revision=meta.get('memory_implementation_revision','ORIGINAL_FROZEN_NATIVE')
                for path,digest in meta.get('memory_implementation_sources',{}).items():
                    assert sha_file(W/path)==digest,('implementation source drift',path)
                if revision=='CPI_PERSON_CHUNK_RESTORATION_1':
                    assert meta['memory_implementation_sha256']==sha_file(P/'src/cihp_benchmark/cpi_memory.py')
                stat=(packet/'prediction.npz').stat()
                entries[iid]=dict(image_id=iid,packet=frame['packet'],packet_sha256=frame['packet_sha256'],
                    metadata_sha256=v['metadata_sha256'],NPZ_bytes=stat.st_size,NPZ_mtime_ns=stat.st_mtime_ns,
                    implementation_revision=revision,implementation_sha256=meta.get('memory_implementation_sha256'),
                    implementation_fingerprint=meta.get('implementation_fingerprint'),source_audit=auditrel,
                    inference_fingerprint=meta['inference_fingerprint'])
                revisions[revision]+=1;segment_counts[revision]+=1;count+=1
            assert count==rr['verified_count'] and {e['image_id'] for e in entries.values()}<=set(ids)
            if count: segments.append(dict(source_root=rr['source_root'],accepted=count,revisions=dict(segment_counts),
                audit=auditrel,reconciled_sha256=sha_file(audit/'RECONCILED.json'),verified_ledger_sha256=sha_file(verified)))
        assert set(entries)==set(ids) and len(entries)==5000
        assert hist.sum(1).tolist()==comp['metrics']['primary']['GT_pixel_support']
        folder=root/mid;folder.mkdir()
        manifest=folder/'INPUTS.jsonl'
        with manifest.open('x') as f:
            for iid in ids: f.write(json.dumps(entries[iid],sort_keys=True)+'\n')
        atomic_json(folder/'SOURCE_CONFUSION.json',hist.tolist())
        samples=list(dict.fromkeys(['0021448','0006909','0001538','0001413','0027897','0031248']+
                    [next(i for i in ids if entries[i]['source_audit']==s['audit']) for s in segments]))
        c['models'][mid]=dict(source_run_id=source_run,source_completion=str((sr/'COMPLETION.json').relative_to(W)),
             source_completion_sha256=sha_file(sr/'COMPLETION.json'),input_manifest=str(manifest.relative_to(W)),
             input_manifest_sha256=sha_file(manifest),source_confusion=str((folder/'SOURCE_CONFUSION.json').relative_to(W)),
             source_confusion_sha256=sha_file(folder/'SOURCE_CONFUSION.json'),sample_ids=samples,revisions=dict(revisions),
             route='YOLO_ASSOCIATED_NATIVE_FRAME',native_model=native['models'][mid],native_config_sha256=nhash)
        compatibility['models'][mid]=dict(revisions=dict(revisions),segments=segments,
             checkpoint_sha256=native['models'][mid]['checkpoint_sha256'],source_commit=native['models'][mid]['source_commit'],
             native_config=native['models'][mid]['native_config'],native_config_sha256=native['models'][mid]['native_config_sha256'],
             geometry='native full-frame → original-grid native20 → unchanged saved YOLO-associated ownership; no remasking',
             environment='native parser-legacy-cu113 recorded in parent/segment LAUNCH/ENVIRONMENT; common scorer uses existing sapiens2-pilot CPU environment',
             historical_failed_attempts=len(comp['historical_failure_attempts']),population=5000)
    evidence=[]
    for name in ['cpi-memory-repair-20261029T153956552075Z','cpi-r50-feature-diagnostic-20261029T175338825178Z','cpi-r50-schedule-diagnostic-20261029T180852377295Z']:
        for fn in ['GPU_DIAGNOSTIC.json','CPU_ACCEPTANCE.json']:
            path=P/'runs'/name/fn; d=read(path)
            evidence.append(dict(path=str(path.relative_to(W)),sha256=sha_file(path),status=d['status'],
                revision=d.get('patch',{}).get('revision'),GPU_feature_native_vs_reuse=d.get('GPU_feature_native_vs_reuse'),
                GPU_synthetic_native_vs_chunked=d.get('GPU_synthetic_native_vs_chunked'),
                regression=d.get('regression'),observed_image_ids=[x.get('image_id') for x in d.get('observations',[])]))
            assert d['status'] in ['PASS','DIAGNOSTIC_PASS']
    compatibility['parity_evidence']=evidence
    atomic_json(record/'COMPATIBILITY.json',compatibility)
    atomic_json(record/'SCORING_CONFIG.json',c)
    atomic_json(root/'SCORING_CONFIG.json',c)
    print(str(record/'SCORING_CONFIG.json'))

def worker(cp,mid,resume):
    c=read(cp); digest=sha_file(cp); root=W/c['artifact_root']/mid;record=W/c['record_root']/mid
    root.mkdir(parents=True,exist_ok=True);record.mkdir(parents=True,exist_ok=True)
    lock=(root/'SCORING.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (record/'COMPLETION.json').exists() and read(record/'COMPLETION.json')['status']=='COMPLETE':
        print('Already complete; no rescoring',mid);return
    if (root/'ATTEMPTS.jsonl').exists() and not resume:raise RuntimeError('Existing attempt: explicit --resume required')
    attempt_history=lineslist(root/'ATTEMPTS.jsonl')
    starts={x['attempt_id']:x for x in attempt_history if x['status']=='STARTED'}
    ends={x['attempt_id']:x for x in attempt_history if x['status'] in ['COMPLETE','STOPPED']}
    now=datetime.now(timezone.utc)
    prior_seconds=sum(((datetime.fromisoformat(ends[k]['end_utc']) if k in ends else now)-datetime.fromisoformat(k)).total_seconds() for k in starts)
    def check():
        assert sha_file(cp)==digest and sha_file(W/c['protocol'])==c['protocol_sha256']
        for f,h in c['source_hashes'].items(): assert sha_file(W/f)==h,('source drift',f)
        assert shutil.disk_usage(root).free>c['minimum_free_gib']*2**30
        if time.monotonic()-start+prior_seconds>c['max_hours']*3600:raise RuntimeError('CPU_TIME_CAP')
        if sum(f.stat().st_size for f in root.rglob('*') if f.is_file())>c['max_stream_gib']*2**30:
            raise RuntimeError('CPU_STREAM_STORAGE_CAP')
    start=time.monotonic();check();s=c['models'][mid]
    assert sha_file(W/s['input_manifest'])==s['input_manifest_sha256']
    entries={e['image_id']:e for e in rows(W/s['input_manifest'])}
    assert sha_file(W/s['source_confusion'])==s['source_confusion_sha256']
    hist=np.asarray(read(W/s['source_confusion']),np.int64); bindings,spec=read_inputs(c)
    acc=Accumulator(c['expected_ids']);scoresroot=root/'scores';scoresroot.mkdir(exist_ok=True)
    logs=lineslist(root/'SCORING.jsonl'); committed={x['image_id']:x for x in logs if x['status']=='COMPLETE'}
    assert len(committed)==sum(x['status']=='COMPLETE' for x in logs)
    attempt_id=utc(); state=dict(run_id=c['run_id'],model_id=mid,status='SCORING',pid=os.getpid(),start_utc=utc(),expected=5000,
       complete=0,config_sha256=digest,protocol_sha256=c['protocol_sha256'],new_model_calls=0,resource_policy=c['resource_policy'])
    atomic_json(root/'STATE.json',state)
    ledger=(root/'SCORING.jsonl').open('a',buffering=1);attempts=(root/'ATTEMPTS.jsonl').open('a',buffering=1)
    emit(attempts,dict(attempt_id=attempt_id,status='STARTED',pid=os.getpid(),resume=resume))
    sample_results=[]
    try:
        for index,iid in enumerate(c['expected_ids']):
            if index%25==0:check()
            e=entries[iid]; source_id=fingerprint(e); f=scoresroot/(iid+'.json')
            if f.exists():
                row=read(f)
                assert row['config_sha256']==digest and row['source_fingerprint']==source_id and row['image_id']==iid
                if iid in committed:assert sha_file(f)==committed[iid]['score_sha256']
                else:emit(ledger,dict(image_id=iid,status='COMPLETE',reconciled_atomic_orphan=True,score_sha256=sha_file(f),source_fingerprint=source_id,end_utc=utc()))
                acc.add(iid,row['scores']);continue
            assert iid not in committed
            packet=W/e['packet'];assert sha_file(packet/'packet.json')==e['metadata_sha256']
            stat=(packet/'prediction.npz').stat();assert [stat.st_size,stat.st_mtime_ns]==[e['NPZ_bytes'],e['NPZ_mtime_ns']]
            with np.load(packet/'prediction.npz',allow_pickle=False) as z:
                planes=z['person_semantic_masks'];extents=z['person_extents'];scores=z['person_scores']
            category,human=load_gt(c,iid,bindings)
            sc=score_people(category,human,planes,extents,scores,SPACE,spec,bindings[iid])
            if iid in s['sample_ids']:
                nh=native_confusion(category,planes,scores,SPACE,spec)
                assert nh.tolist()==read(packet/'score_0.5.json')['histogram']
                gt=project(category,SPACE,spec) if not (category==255).any() else None
                if gt is None:
                    gt=np.full(category.shape,255,np.uint8);gt[category<20]=project(category[category<20],SPACE,spec)
                pred=project(compose_native(planes,scores,category.shape),SPACE,spec);valid=category<20
                pixel=np.bincount(6*gt[valid].astype(np.int64)+pred[valid],minlength=36).reshape(6,6)
                assert np.array_equal(pixel,project_confusion(nh,SPACE,spec))
                sample_results.append(dict(image_id=iid,source_fingerprint=source_id,native_and_mapped_pixel_confusion_exact=True))
            row=dict(image_id=iid,model_id=mid,scores=sc,config_sha256=digest,protocol_sha256=c['protocol_sha256'],
                    source_fingerprint=source_id,source_packet=e)
            atomic_json(f,row)
            emit(ledger,dict(image_id=iid,status='COMPLETE',score_sha256=sha_file(f),source_fingerprint=source_id,end_utc=utc()))
            acc.add(iid,sc)
            if index%25==0:
                state.update(complete=len(acc.ids),current_image=iid);atomic_json(root/'STATE.json',state)
            if index%500==0:print(mid,len(acc.ids),'/5000',flush=True)
        result=acc.report(project_confusion(hist,SPACE,spec),hist)
        assert result['status']=='COMPLETE' and result['primary']['GT_support']==c['GT_summary']['global_support']
        for pm in result['person_metrics'].values():
            assert all(pm[k]==c['GT_summary'][k] for k in ['G_loc','G_sem_C4'])
        result.update(run_id=c['run_id'],model_id=mid,config_sha256=digest,protocol_sha256=c['protocol_sha256'],
          route=s['route'],resource_policy=c['resource_policy'],source_implementation_revisions=s['revisions'],
          input_manifest_sha256=s['input_manifest_sha256'],source_completion_sha256=s['source_completion_sha256'],model_inference=False)
        state.update(status='COMPLETE',complete=len(acc.ids),missing=0,duplicate=0,invalid=0,failed=0,end_utc=utc(),queue_stopped=True,
          metrics_path=str((record/'METRICS.json').relative_to(W)),primary_source='METRICS.json.primary',source_implementation_revisions=s['revisions'])
        for folder in [root,record]:
            atomic_json(folder/'METRICS.json',result);atomic_json(folder/'COMPLETION.json',state)
        atomic_json(record/'PROJECTION_CHECK.json',dict(status='PASS',samples=sample_results,
          resume_note='Any samples committed by prior attempt remain evidenced in their score/provenance files; no source scores overwritten.'))
        emit(attempts,dict(attempt_id=attempt_id,status='COMPLETE',complete=len(acc.ids),end_utc=utc()))
    except BaseException:
        state.update(status='INCOMPLETE',complete=len(acc.ids),error=traceback.format_exc(),end_utc=utc(),queue_stopped=True)
        atomic_json(root/'FAILURE.json',state);atomic_json(record/'COMPLETION.json',state)
        emit(attempts,dict(attempt_id=attempt_id,status='STOPPED',complete=len(acc.ids),error=state['error'],end_utc=utc()))
        raise
    finally:
        atomic_json(root/'STATE.json',state);ledger.close();attempts.close()

def lineslist(path):return list(rows(path)) if Path(path).exists() else []

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--prepare');a.add_argument('--config',type=Path);a.add_argument('--model',choices=RUNS);a.add_argument('--resume',action='store_true');args=a.parse_args()
    if args.prepare:prepare(args.prepare)
    else:worker(args.config.resolve(),args.model,args.resume)
