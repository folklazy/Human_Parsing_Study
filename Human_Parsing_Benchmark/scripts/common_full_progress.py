"""Read-only common-view batch progress; Ctrl+C stops only this viewer."""
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import argparse,json,time
P=Path(__file__).resolve().parents[1];W=P.parent

def read(path):
    try:return json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return {}

def main():
    a=argparse.ArgumentParser();a.add_argument('--config',type=Path);a.add_argument('--watch',action='store_true');args=a.parse_args()
    cp=args.config or W/(P/'outputs/common_view/CURRENT_FULL.txt').read_text().strip()
    c=read(cp);root=W/c['artifact_root']
    try:
        while True:
            state=read(root/'STATE.json');launch=read(root/'LAUNCH.json')
            pid=launch.get('controller_PID');alive=bool(pid and (Path('/proc')/str(pid)).exists())
            print('\n'+datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Bangkok')).isoformat(timespec='seconds'),c['run_id'])
            print('Batch:',state.get('status','NOT_LAUNCHED'),'controller PID',pid,'alive',alive)
            for mid in c['models']:
                s=read(root/'models'/mid/'RUN.json')
                print(mid,s.get('status','PENDING'),str(s.get('complete',0))+'/5000',
                      'reused',s.get('reused',0),'new VAL calls',s.get('new_VAL_calls',0),
                      'failed',s.get('failed',0),'invalid',s.get('invalid',0),'PID',s.get('pid'))
            print('Run status:',root/'STATE.json','\nReport:',P/'reports/CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md',flush=True)
            if not args.watch or state.get('queue_stopped') or (pid and not alive):return
            time.sleep(5)
    except KeyboardInterrupt:pass
if __name__=='__main__':main()
