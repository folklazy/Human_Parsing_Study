"""Observe one existing CPI controller and publish its canonical terminal record.

This observer never launches, retries, stops, or changes inference. It does not
rescore predictions. A missing terminal record requires manual reconciliation.
"""
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse
import hashlib
import json
import os
import subprocess
import time

from monitor_cihp_batch import publish

P = Path(__file__).resolve().parents[1]
W = P.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def alive(process):
    try:
        node = Path('/proc') / str(process['PID'])
        ticks = int((node / 'stat').read_text().rsplit(')', 1)[1].split()[19])
        args = (node / 'cmdline').read_bytes().split(b'\0')
        return ticks == process['birth_ticks'] and any(
            os.fsdecode(v).endswith('/run_cpi_continuation.py') for v in args if v)
    except FileNotFoundError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operator-record', required=True)
    args = parser.parse_args()
    rec = Path(args.operator_record).resolve()
    if not rec.is_relative_to(P / 'runs'):
        raise ValueError('Existing project operator record required')
    process = json.loads((rec / 'PROCESS.json').read_text())
    link = json.loads((rec / 'SEGMENT_LINK.json').read_text())
    root = W / link['raw_segment']
    if not root.resolve().is_relative_to(P / 'outputs/cpi_continuations'):
        raise ValueError('Unexpected raw segment')
    guard = json.loads((rec / 'FINALIZER_GUARD.json').read_text())
    if guard['source_sha256'] != digest(Path(__file__)):
        raise ValueError('Observer source changed')
    while alive(process):
        time.sleep(30)
    stamp = datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Bangkok')).isoformat()
    terminal = root / 'COMPLETION.json'
    result = json.loads(terminal.read_text()) if terminal.exists() else {
        'status': 'INTERRUPTED_REQUIRES_RECONCILIATION', 'metrics': {'primary': None}}
    if terminal.exists():
        if result['model_id'] != 'CPI_ConvNeXtB_CIHP' or result['round_id'] != root.name:
            raise ValueError('Terminal model/segment binding mismatch')
        if result['status'] != 'COMPLETE' and result['metrics']['primary'] is not None:
            raise ValueError('Incomplete result must have null primary')
    modelrun = root / 'segments/CPI_ConvNeXtB_CIHP/RUN.json'
    run = json.loads(modelrun.read_text()) if modelrun.exists() else {}
    ledger = modelrun.parent / 'FRAMES.jsonl'
    failures = [json.loads(line) for line in ledger.read_text().splitlines()
                if json.loads(line)['status'] != 'COMPLETE'] if ledger.exists() else []
    receipt = {'checked_Bangkok': stamp, 'segment': root.name,
               'status': result['status'], 'canonical_completion_present': terminal.exists(),
               'completion_sha256': digest(terminal) if terminal.exists() else None,
               'observer_PID': os.getpid(), 'no_inference_or_rescore': True,
               'automatic_retry': False}
    write(rec / 'TERMINAL_OBSERVATION.json', receipt)
    report = P / 'reports' / (rec.name + '.md')
    report.write_text(f'''# CPI ConvNeXt-B — manual continuation หลัง Sapiens จบ

ตรวจปิดรอบเวลาไทย `{stamp}` · **{result['status']}** · segment `{root.name}`

ผู้ใช้ขอกลับมาทดสอบ CPI หลัง GPU ว่าง. เปิดเฉพาะ ConvNeXt-B หลัง Sapiens2 0.4B/0.8B ครบตัวละ 5,000. Frozen checkpoint/config/FP32/preprocessing/TTA/thresholds/YOLO/ownership/scorer เดิม ไม่เปลี่ยน. [Authorization](../runs/{rec.name}/AUTHORIZATION.json), [process](../runs/{rec.name}/PROCESS.json), [segment plan](../runs/{root.name}/SEGMENT_PLAN.json).

|รายการ|จำนวน|
|---|---:|
|Expected|5,000|
|Reuse ที่ตรวจผ่านก่อนเปิด|{result.get('reused', 'N/A')}|
|Complete รวม|{result.get('complete', 'N/A')}|
|Missing|{result.get('missing_IDs', 'N/A')}|
|Failed / invalid|{result.get('failed', 'N/A')} / {result.get('invalid', 'N/A')}|
|Duplicate successes|{result.get('duplicate_IDs', 'N/A')}|

Primary native20 metrics: `{json.dumps(result.get('metrics', {}).get('primary'), ensure_ascii=False)}`. คะแนนหลักเป็น null หากไม่ครบตาม STRICT_COMPLETE ไม่ใช้ subset เทียบกับชุดเต็ม. Canonical source: [completion](../runs/{root.name}/COMPLETION.json). Start UTC `{result.get('start_utc', 'N/A')}`, end UTC `{result.get('end_utc', 'N/A')}`; TRAIN warmup `{run.get('warmup_images', [])}`; launch commit `{result.get('launch_commit', process['launch_commit'])}`.

Packet แรกและ first-packet contract checks อยู่ใน [หลักฐาน](../runs/{rec.name}/FIRST_PACKET_CHECK.json). Controller ตรวจ NPZ/hash/metadata/GT และ saved-mask scores ด้วย verifier เดิมก่อนรวมผล ไม่พึ่ง counters ค้าง. Observer นี้อ่าน canonical results เท่านั้น ไม่ rescore หรือ inference. Raw artifacts `{root.relative_to(W)}` เก็บภายนอก Git; historical OOM/attempts และผลสำเร็จเดิมไม่ลบหรือเขียนทับ.

Failure records ของ segment นี้ (N/A เมื่อไม่มี):
```json
{json.dumps(failures, ensure_ascii=False, indent=2)}
```

ผลเป็น YOLO-associated application pipeline บน native CIHP20 ไม่ใช่ official native-parser reproduction หรือ C4-P. Timing เป็น adapter diagnostics รวม CPI native file I/O ภายใต้ shared-quality authorization แม้ GPU ว่างตอน launch; ไม่ใช้จัดอันดับ latency/FPS/VRAM efficiency. Free VRAM ตอน launch ไม่รับประกันครบทุกภาพ. คง24h/80GiB/free50GiB, stop-on-error, no automatic OOM/model retry/fallback/next model. CPI R50 ยังพัก. ไม่มี 1B/training/color/CCTV.
''')
    files = [str(report.relative_to(P)), f'runs/{rec.name}/TERMINAL_OBSERVATION.json']
    compact = P / 'runs' / root.name
    if terminal.exists():
        files += [str(f.relative_to(P)) for f in compact.glob('*.json')]
    if digest(P / 'STATUS.md') == guard['status_sha256']:
        (P / 'STATUS.md').write_text(
            f'# Human Parsing Benchmark — current status\n\nUpdated: {stamp} (Asia/Bangkok)\n\n'
            f'**CPI_CONVNEXT_{result["status"]}** · [current report](reports/{rec.name}.md). '
            f'Complete {result.get("complete", "N/A")}/5000; primary is null unless STRICT_COMPLETE. '
            'Controller stopped; no automatic next model/retry.\n\n'
            'Sapiens2 0.4B and 0.8B each COMPLETE5000: '
            '[0.4B/common cohort](reports/CIHP_SAPIENS_C4P_FULL_RESULTS_TH.md), '
            '[0.8B](reports/CIHP_SAPIENS_08B_C4P_RESULTS_TH.md). '
            'Four native/common systems preserved. CPI R50 paused; no new experiment.\n')
        files.append('STATUS.md')
    with (P / 'WORK_LOG.md').open('a') as out:
        out.write(f'\n## {stamp} — {rec.name}: automatic terminal observation\n\n'
                  f'Controller exited; canonical {result["status"]}, '
                  f'{result.get("complete", "N/A")}/5000. Existing controller reconciled packets '
                  'and saved-mask scores; this observer only assembled report/navigation. '
                  'Failure/attempt history retained; no retry/next model/inference/rescore.\n')
    files.append('WORK_LOG.md')
    pub = W / 'Human_Parsing_Study_Public' / 'Human_Parsing_Benchmark'
    changed = [f for f in files if not (pub / f).exists() or (pub / f).read_bytes() != (P / f).read_bytes()]
    synced = publish(root, rec.name + '-closure', changed,
                     scope='CPI ConvNeXt terminal canonical records and Thai report only; no raw masks/logs',
                     message='results: record CPI ConvNeXt manual continuation closure')
    write(rec / 'TERMINAL_PUBLICATION.json', synced)
    print(json.dumps(synced), flush=True)


if __name__ == '__main__':
    main()
