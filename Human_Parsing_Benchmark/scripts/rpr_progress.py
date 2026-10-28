"""Read-only progress viewer. Watching/stopping this viewer never controls inference."""
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import argparse,json,sys,time
W=Path(__file__).resolve().parents[2]

def read_json(path):
    try:return json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return {}

def alive(pid,script,root):
    if not pid:return False
    try:
        args=(Path('/proc')/str(pid)/'cmdline').read_bytes()
        return script.encode() in args and str(root).encode() in args
    except FileNotFoundError:return False
    except PermissionError:return None

def last_frame(path):
    try:
        with path.open('rb') as stream:
            stream.seek(max(0,path.stat().st_size-32768));data=stream.read()
        if not data.endswith(b'\n'):data=data.rsplit(b'\n',1)[0]
        for line in reversed(data.splitlines()):
            try:return json.loads(line)
            except (json.JSONDecodeError,UnicodeDecodeError):continue
    except FileNotFoundError:pass
    return {}

def line_count(path):
    try:
        with path.open('rb') as stream:return sum(chunk.count(b'\n') for chunk in iter(lambda:stream.read(1024*1024),b''))
    except FileNotFoundError:return 0

def snapshot(root,liveness=alive,model='RPR_CIHP',controller_script='run_rpr_quality_round.py',worker_script='run_rpr_shared_segment.py'):
    state=read_json(root/'ROUND_STATUS.json');worker=read_json(root/'segments'/model/'RUN.json');last=last_frame(root/'segments'/model/'FRAMES.jsonl');raw=state.get('status','NO_STATUS')
    controller=liveness(state.get('controller_PID'),controller_script,root);wp=liveness(state.get('worker_PID'),worker_script,root)
    terminal=raw in {'COMPLETE','INCOMPLETE','INCOMPLETE_REQUIRES_RECONCILIATION'} or state.get('queue_stopped',False)
    if terminal:phase='COMPLETE' if raw=='COMPLETE' else 'STOPPED_INCOMPLETE'
    elif raw=='POSTFLIGHT':phase='VALIDATING_ARTIFACTS' if controller is not False else 'INTERRUPTED_DURING_VALIDATION'
    elif raw=='RUNNING':
        if controller is False:phase='WORKER_RUNNING_CONTROLLER_MISSING' if wp else 'INTERRUPTED'
        elif worker.get('status')=='COMPLETE':phase='INFERENCE_DONE_AWAITING_VALIDATION'
        elif wp is False:phase='WORKER_EXITED_AWAITING_CONTROLLER'
        elif worker.get('complete',0):phase='INFERENCE'
        else:phase='MODEL_LOAD_OR_TRAIN_WARMUP'
    else:phase=raw
    plan=read_json(root/'SEGMENT_PLAN.json');reused=len(plan.get('reused_ids',[]));segment_done=worker.get('complete',0)
    expected=state.get('expected',worker.get('expected',5000));done=state.get('complete',reused+segment_done) if terminal else reused+segment_done
    verified=reused+line_count(root/'final_audit'/model/'VERIFIED_FRAMES.jsonl')
    return {'model_id':model,'time_Bangkok':datetime.now(ZoneInfo('Asia/Bangkok')).isoformat(timespec='seconds'),'round_id':root.name,'phase':phase,'controller_recorded_status':raw,'inference_complete':done,'reused_complete':reused,'segment_inference_complete':segment_done,'expected':expected,'inference_percent':round(100*done/expected,1) if expected else None,'remaining_inference':max(0,expected-done),'failed':worker.get('failed',state.get('failed',0)),'invalid':worker.get('invalid',state.get('invalid',0)),'artifact_packets_verified':verified,'controller_PID':state.get('controller_PID'),'controller_alive':controller,'worker_PID':state.get('worker_PID'),'worker_alive':wp,'last_image_ID':last.get('image_id'),'last_frame_end_utc':last.get('end_utc'),'terminal':terminal,'queue_stopped':state.get('queue_stopped',False),'resource_mode':state.get('resource_mode'),'raw_root':str(root),'note':'100% inference is not round completion; wait for artifact validation and terminal COMPLETE. Counts include reused committed outputs; segment counts and prior failures remain separately recorded. No scores read, no new inference or GPU queries.'}

def bar(done,total):
    width=28;fill=min(width,int(width*done/total)) if total else 0
    return '['+'#'*fill+'-'*(width-fill)+f'] {done:,}/{total:,}'

def render(s):
    flag=lambda v:'alive' if v is True else 'exited/not found' if v is False else 'unknown'
    return '\n'.join([f"{s.get('model_id','RPR_CIHP')} | {s['time_Bangkok']}",f"Round: {s['round_id']}",f"Phase: {s['phase']}",f"Inference {bar(s['inference_complete'],s['expected'])} {s['inference_percent']}%",f"Reused: {s.get('reused_complete',0)} | New in segment: {s.get('segment_inference_complete',0)}",f"Artifact validation {bar(s['artifact_packets_verified'],s['expected'])}",f"Remaining inference: {s['remaining_inference']:,} | failed: {s['failed']} | invalid: {s['invalid']}",f"Controller PID {s['controller_PID']} ({flag(s['controller_alive'])}) | Worker PID {s['worker_PID']} ({flag(s['worker_alive'])})",f"Latest image: {s['last_image_ID']} | frame end UTC: {s['last_frame_end_utc']}",f"Queue stopped: {s['queue_stopped']} | {s['resource_mode']}","Read-only viewer; Ctrl+C stops only the viewer. 100% inference still needs artifact validation."])

def main(model='RPR_CIHP',pointer='CURRENT_RPR_ROUND.txt',controller_script='run_rpr_quality_round.py',worker_script='run_rpr_shared_segment.py'):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--round-root',type=Path);parser.add_argument('--watch',action='store_true');parser.add_argument('--interval',type=float,default=5);parser.add_argument('--json',action='store_true');a=parser.parse_args()
    if a.interval<1:parser.error('Use an interval of at least one second')
    if a.round_root:root=a.round_root.resolve()
    else:
        parent=W/'Human_Parsing_MHPv2_Study/outputs/cihp_native/cihp-native-six-20261028T034103254470Z';root=parent/'rounds'/(parent/pointer).read_text().strip()
    try:
        while True:
            s=snapshot(root,model=model,controller_script=controller_script,worker_script=worker_script)
            if a.watch and sys.stdout.isatty() and not a.json:print('\033[2J\033[H',end='')
            print(json.dumps(s,ensure_ascii=False) if a.json else render(s),flush=True)
            if not a.watch or s['terminal'] or s['phase'].startswith('INTERRUPTED'):break
            time.sleep(a.interval)
    except KeyboardInterrupt:pass

if __name__=='__main__':main()
