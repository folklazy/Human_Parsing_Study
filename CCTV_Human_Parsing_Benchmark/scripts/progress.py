"""Read-only CCTV progress. Never imports model code or starts a job."""
from pathlib import Path
import argparse,json,time
P=Path(__file__).resolve().parents[1]
def read(path,default=None):
    try:return json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return default
def main():
    a=argparse.ArgumentParser();a.add_argument('--run');a.add_argument('--watch',action='store_true');args=a.parse_args()
    run=args.run or (P/'CURRENT_RUN.txt').read_text().strip();root=P/'outputs'/run
    while True:
        c=read(root/'CONFIG.json',{});worker=read(root/'CURRENT_WORKER.json',{})
        print('\nRun:',run,'| controller terminal:',(root/'CONTROLLER_TERMINAL.json').exists(),flush=True)
        for mid in ['YOLO26X']+list(c.get('models',{})):
            s=read(root/mid/'STATE.json',{});print(f"{mid:30} {s.get('status','NOT_STARTED'):18} {s.get('complete',0):3}/{len(c.get('members',[]))}")
        print('Last worker PID:',worker.get('pid'),'|',worker.get('model_id'),'| partial-label recall only',flush=True)
        if not args.watch:return
        time.sleep(5)
if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:pass
