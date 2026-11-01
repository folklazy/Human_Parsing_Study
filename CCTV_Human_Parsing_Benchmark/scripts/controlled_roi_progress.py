"""Read-only live progress. Ctrl+C never stops the actual batch."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import json
import os
import time

P=Path(__file__).resolve().parents[1]


def read(path):
    try:return json.loads(path.read_text())
    except FileNotFoundError:return {}


def alive(pid):
    if not pid:return False
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False


def display():
    run=(P/'outputs/CURRENT_CONTROLLED_ROI.txt').read_text().strip();root=P/'outputs'/run
    config=read(root/'CONFIG.json');controller=read(root/'CONTROLLER.json');worker=read(root/'CURRENT_WORKER.json')
    link=read(root/'CONTINUATION_LINK.json');continuation=P.parent/link['artifact_root'] if link else None
    continued=read(continuation/'CONTROLLER.json') if continuation else {}
    print(datetime.now(timezone(timedelta(hours=7))).isoformat(),'|',run)
    print('Controller:',controller.get('status','NOT_LAUNCHED'),'PID',controller.get('pid'),'alive',alive(controller.get('pid')))
    print('Model | frames/90 | ROI/130 | reused | new | state')
    for mid in config['models']:
        state=read(root/mid/'STATE.json')
        if continuation and (continuation/mid/'STATE.json').exists():
            state=read(continuation/mid/'STATE.json')
        print(mid,'|',str(state.get('complete_frames',0))+'/90','|',str(state.get('complete_ROIs',0))+'/130',
              '|',state.get('reused_ROIs',0),'|',state.get('new_ROIs',0),'|',state.get('status','NOT_STARTED'))
    print('Worker:',worker.get('model_id'),'PID',worker.get('pid'),'alive',alive(worker.get('pid')))
    if continuation:
        cw=read(continuation/'CURRENT_WORKER.json')
        print('Continuation:',continued.get('status','NOT_LAUNCHED'),'PID',continued.get('pid'),'alive',alive(continued.get('pid')),
              '| worker',cw.get('model_id'),cw.get('pid'),'alive',alive(cw.get('pid')))
        print('Assembled nine-model index ready =',(root/'ASSEMBLED_PREDICTION_INDEX.json').exists())
    print('New headline metrics remain null until reviewed Face/Neck GT is ready.')
    print('Finished prediction batch: BATCH_COMPLETION.json present =',(root/'BATCH_COMPLETION.json').exists())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--watch',action='store_true');args=parser.parse_args()
    try:
        while True:
            display()
            if not args.watch:break
            time.sleep(10)
    except KeyboardInterrupt:pass
