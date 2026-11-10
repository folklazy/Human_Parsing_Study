"""Lightweight sequential queue: one controller at a time; no model imports."""
from pathlib import Path
import argparse
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

H=Path(__file__).resolve().parents[1];W=H.parent


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def atomic(p,value):
    p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp')
    with tmp.open('w') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)


def may_advance(controller,closure):
    return (controller.get('status')=='BATCH_TERMINAL' and controller.get('queue_stopped') is True
            and closure.get('status')=='COMPLETE' and closure.get('strict_complete') is True
            and closure.get('unique_frame_ids')==5000 and closure.get('missing')==0
            and closure.get('duplicate')==0 and closure.get('failed')==closure.get('invalid')==0)


def run(cp):
    c=read(cp);root=Path(cp).parent
    lock=(root/'QUEUE.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (root/'QUEUE_STATE.json').exists():raise FileExistsError('Queue already attempted; never auto-restart')
    if sha(__file__)!=c['queue_source_sha256']:raise ValueError('Queue source changed')
    for job in c['jobs']:
        if sha(W/job['config'])!=job['config_sha256']:raise ValueError('Prepared job config changed')
    s=dict(status='STARTING',pid=os.getpid(),started_utc=datetime.now(timezone.utc).isoformat(),jobs=[],current=None)
    atomic(root/'QUEUE_STATE.json',s)
    for job in c['jobs']:
        spec=read(W/job['config']);out=W/spec['artifact_root']
        command=[str(W/c['controller_python']),'-u',str(W/c['runner']),'controller','--config',str(W/job['config'])]
        s.update(status='MODEL_RUNNING',current=job['model_id'],current_config=job['config'])
        with (root/(job['model_id']+'.controller.log')).open('x') as log:
            child=subprocess.Popen(command,cwd=W,stdout=log,stderr=subprocess.STDOUT)
            s.update(child_controller_pid=child.pid);atomic(root/'QUEUE_STATE.json',s)
            code=child.wait()  # Kernel wait, no GPU/context/model loading or polling.
        control=read(out/'CONTROLLER.json') if (out/'CONTROLLER.json').exists() else {}
        closure=read(out/'ROUND_CLOSURE.json') if (out/'ROUND_CLOSURE.json').exists() else {}
        row=dict(model_id=job['model_id'],returncode=code,controller=control.get('status'),
                 closure=closure.get('status'),config=job['config'])
        s['jobs'].append(row);s['child_controller_pid']=None
        if code or not may_advance(control,closure):
            s.update(status='STOPPED_INCOMPLETE',ended_utc=datetime.now(timezone.utc).isoformat())
            atomic(root/'QUEUE_STATE.json',s);return
        # Controller exits after waiting for its worker; no overlap at transition.
        atomic(root/'QUEUE_STATE.json',s)
    s.update(status='COMPLETE',current=None,ended_utc=datetime.now(timezone.utc).isoformat())
    atomic(root/'QUEUE_STATE.json',s)


def progress(cp):
    c=read(cp);root=Path(cp).parent;s=read(root/'QUEUE_STATE.json') if (root/'QUEUE_STATE.json').exists() else {'status':'PREPARED'}
    print(c['queue_id'],datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Bangkok')).isoformat(),s['status'])
    print('Queue PID',s.get('pid'),'controller',s.get('child_controller_pid'),'current',s.get('current'))
    for job in c['jobs']:
        out=W/job['artifact_root'];sp=out/job['model_id']/'STATE.json'
        model=read(sp) if sp.exists() else {};accepted=job['accepted_frames']
        done=max(accepted,model.get('completed',0))
        control=read(out/'CONTROLLER.json') if (out/'CONTROLLER.json').exists() else {}
        print(job['model_id'],model.get('status','QUEUED'),str(done)+'/5000',
              'accepted_parent',accepted,'new_completed',max(0,done-accepted),
              'new_VAL_calls',model.get('ROI_calls',0),'failed',model.get('failed',0),
              'invalid',model.get('invalid',0),'worker',control.get('worker_pid'))
    print('CPI_R50_CIHP COMPLETE5000 reused; not queued. No concurrent GPU workers; no automatic retry.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['run','progress']);p.add_argument('--config',type=Path,required=True)
    a=p.parse_args();run(a.config) if a.action=='run' else progress(a.config)
