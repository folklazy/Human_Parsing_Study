"""Read-only terminal observer; publish only approved aggregate summaries.

No model imports, inference, scorer changes, retries, or private data publication.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,csv,hashlib,json,os,subprocess,time
P=Path(__file__).resolve().parents[1];W=P.parent;PUB=W/'Human_Parsing_Study_Public'
def read(f):return json.loads(f.read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def matches(pid,ticks=None):
    try:
        cmd=Path('/proc/'+str(pid)+'/cmdline').read_bytes().decode().replace('\x00',' ')
        birth=int(Path('/proc/'+str(pid)+'/stat').read_text().rsplit(')',1)[1].split()[19])
        return 'CCTV_Human_Parsing_Benchmark/scripts/benchmark.py' in cmd and (ticks is None or birth==ticks)
    except OSError:return False
def main():
    a=argparse.ArgumentParser();a.add_argument('--run',required=True);a.add_argument('--pid',type=int,required=True);a.add_argument('--ticks',type=int,required=True);args=a.parse_args()
    raw=P/'outputs'/args.run;c=read(raw/'CONFIG.json');guard=read(raw/'PUBLICATION_GUARD.json')
    while matches(args.pid,args.ticks):time.sleep(15)
    if (raw/'CURRENT_WORKER.json').exists():
        worker=read(raw/'CURRENT_WORKER.json')
        while matches(worker['pid']):time.sleep(15)
    data=[];evidence={};expected={s['id'] for s in c['members']}
    for mid in c['models']:
        root=raw/mid;s=read(root/'STATE.json') if (root/'STATE.json').exists() else {'status':'NOT_STARTED','complete':0}
        m=read(root/'METRICS.json') if (root/'METRICS.json').exists() else {};primary=m.get('primary')
        if s['status']=='COMPLETE':
            ledger=[json.loads(l) for l in (root/'FRAMES.jsonl').read_text().splitlines() if l.strip()]
            ids=[x['image_id'] for x in ledger if x['status']=='COMPLETE']
            assert len(ids)==len(set(ids))==len(expected) and set(ids)==expected
            assert primary is not None
            evidence[mid]={'exact_unique_membership':len(ids),'ledger_sha256':sha(root/'FRAMES.jsonl'),'metrics_sha256':sha(root/'METRICS.json')}
        else:primary=None;evidence[mid]={'status':s['status'],'complete':s['complete'],'primary_null':True}
        for group in ['overall','day','night']:
            metrics=m.get('groups',{}).get(group,{}).get('metrics') if primary else None
            data.append(dict(model_id=mid,group=group,status=s['status'],complete=s['complete'],expected=len(expected),
             Face_recall=metrics['per_target_recall'][0] if metrics else None,Hair_recall=metrics['per_target_recall'][1] if metrics else None,
             Upper_recall=metrics['per_target_recall'][2] if metrics else None,Lower_recall=metrics['per_target_recall'][3] if metrics else None,
             macro_recall4=metrics['macro_recall4'] if metrics else None,
             full_image_mIoU=None,full_image_precision=None,person_F1=None,
             limitation='partial annotations; outside known target pixels unknown; Dress boundary unspecified'))
    complete=sum(v.get('exact_unique_membership')==len(expected) for v in evidence.values())
    (P/'metrics').mkdir(exist_ok=True)
    with (P/'metrics/PARTIAL_RECALL.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
    state={'scope':'CCTV_PARTIAL_TARGET_RECALL_V1','run_id':args.run,'status':'PARTIAL_BENCHMARK_COMPLETE' if complete==9 else 'TERMINAL_WITH_INCOMPLETE_SYSTEMS',
     'complete_models':complete,'expected_models':9,'population':len(expected),'updated_utc':datetime.now(timezone.utc).isoformat(),
     'full_benchmark_ready':False,'reason':'Selected people/parts only; unknown negatives; no Dress rule or full-person silhouettes',
     'no_overall_deployment_winner':True,'new_experiment_started':False,'evidence':evidence,'config_sha256':sha(raw/'CONFIG.json')}
    (P/'STUDY_STATE.json').write_text(json.dumps(state,indent=2)+'\n')
    report=P/'reports/RESULTS_TH.md';report.write_text(report.read_text()+'\n## ตรวจปิดรอบอัตโนมัติ\n\n'+str(complete)+'/9ระบบครบexact'+str(len(expected))+'IDs; [CSV day/night/overall](../metrics/PARTIAL_RECALL.csv) / [machine state](../STUDY_STATE.json). ระบบไม่ครบprimarynull; full-imageIoU/precision/personF1คงnullเพราะGTไม่รองรับ ไม่ใช่0. ไม่มีoveralldeploymentwinnerหรือinference/retryใหม่จากตัวตรวจนี้.\n')
    f=P/'WORK_LOG.md';f.write_text(f.read_text()+'\n## '+state['updated_utc']+' UTC — aggregate terminal verification\n\n'+str(complete)+'/9 exactpopulationcomplete. DerivedCSV/statefromsavedmetrics/ledgers,norescore/inference. Privateidentifiers/images/masks/logsnotpublished. NextreviewpartialdiagnosticsandclosefullannotationQArequirements.\n')
    rels=['STATUS.md','WORK_LOG.md','reports/RESULTS_TH.md','metrics/PARTIAL_RECALL.csv','STUDY_STATE.json']
    receipt={'status':'PENDING_SYNC'}
    if subprocess.check_output(['git','-C',str(PUB),'status','--porcelain'],text=True).strip():receipt['reason']='Public working tree has independent changes'
    elif any(sha(PUB/'CCTV_Human_Parsing_Benchmark'/rel)!=h for rel,h in guard.items()):receipt['reason']='Public navigation changed after launch; preserve independent work'
    else:
        assert subprocess.check_output(['git','-C',str(PUB),'remote','get-url','origin'],text=True).strip()=='https://github.com/folklazy/Human_Parsing_Study.git'
        assert subprocess.check_output(['git','-C',str(PUB),'branch','--show-current'],text=True).strip()=='main'
        entries=[];paths=[]
        for rel in rels:
            src=P/rel;dst=PUB/'CCTV_Human_Parsing_Benchmark'/rel
            if dst.exists() and src.read_bytes()==dst.read_bytes():continue
            assert src.stat().st_size<1024**2 and not src.is_symlink()
            dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());path=str(dst.relative_to(PUB));paths.append(path)
            entries.append({'path':path,'bytes':dst.stat().st_size,'sha256':sha(dst)})
        mp=PUB/'publication'/('CCTV_PARTIAL_'+args.run+'_terminal.json')
        mp.write_text(json.dumps({'scope':'Aggregate private-CCTV partial benchmark only; no CCTV source identifiers/assets','files':entries,'run_id':args.run},indent=2)+'\n');paths.append(str(mp.relative_to(PUB)))
        idxfile=PUB/'publication/PUBLIC_FILE_MANIFEST.json';idx=read(idxfile);items={e['path']:e for e in idx['files']}
        for path in paths:items[path]={'path':path,'sha256':sha(PUB/path),'bytes':(PUB/path).stat().st_size}
        idx['files']=[items[k] for k in sorted(items)];idx['updated_utc']=state['updated_utc'];idxfile.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n')
        fl=PUB/'publication/PUBLISH_FILES.txt';fl.write_text('\n'.join(sorted(set(fl.read_text().splitlines())|set(paths)))+'\n');paths+=['publication/PUBLIC_FILE_MANIFEST.json','publication/PUBLISH_FILES.txt']
        subprocess.run(['git','-C',str(PUB),'add','--',*paths],check=True)
        assert set(subprocess.check_output(['git','-C',str(PUB),'diff','--cached','--name-only'],text=True).splitlines())==set(paths)
        subprocess.run(['git','-C',str(PUB),'diff','--cached','--check'],check=True)
        subprocess.run(['git','-C',str(PUB),'commit','-m','results: close scoped CCTV partial-annotation benchmark'],check=True)
        env=os.environ.copy();env['GIT_TERMINAL_PROMPT']='0'
        push=subprocess.run(['git','-C',str(PUB),'push','origin','main'],env=env,capture_output=True,text=True,timeout=45)
        commit=subprocess.check_output(['git','-C',str(PUB),'rev-parse','HEAD'],text=True).strip()
        remote=subprocess.check_output(['git','-C',str(PUB),'ls-remote','origin','refs/heads/main'],text=True,timeout=30).split()[0]
        receipt.update(status='SYNCED' if push.returncode==0 and commit==remote else 'PENDING_SYNC',commit=commit,remote_commit=remote,push_exit=push.returncode)
    (raw/'TERMINAL_PUBLICATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'complete_models':complete,'publication':receipt}),flush=True)
if __name__=='__main__':main()
