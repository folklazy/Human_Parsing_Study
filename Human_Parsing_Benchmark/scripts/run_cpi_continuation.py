"""Operator-requested CPI continuation; default is reconciliation only, never inference.

One model, fresh segment, shared-quality admission, immutable prior attempts.
The frozen scientific worker is expanded with existing segment/resource controls;
only its allowed output location is additionally changed to this project's outputs.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import difflib
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback

P = Path(__file__).resolve().parents[1]
W = P.parent
ART = P / 'outputs/cpi_continuations'
MODELS = {'r50': 'CPI_R50_CIHP', 'convnext': 'CPI_ConvNeXtB_CIHP'}
sys.path.insert(0, str(P / 'src'))
from reconcile_cihp_continuation import validate_folder, write
from cihp_benchmark.data import file_hash
from cihp_benchmark.evaluation import semantic_report


def now():
    return datetime.now(timezone.utc).isoformat()


def expanded_worker(mid):
    if mid == MODELS['r50']:
        from run_cpi_r50_shared_segment import derive_shared
    else:
        from run_cpi_convnext_shared_segment import derive_shared
    source = derive_shared((P / 'scripts/run_cihp_system.py').read_text())
    old = "out.is_relative_to(W/'Human_Parsing_MHPv2_Study/outputs/cihp_native')"
    if source.count(old) != 1:
        raise ValueError('Output guard anchor changed')
    return source.replace(old, "out.is_relative_to(P/'outputs/cpi_continuations')")


def reject_existing_worker():
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            argv = (proc / 'cmdline').read_bytes().split(b'\0')
        except FileNotFoundError:
            continue
        names = [Path(os.fsdecode(v)).name for v in argv if v]
        guarded = {'run_cpi_r50_quality_round.py', 'run_cpi_convnext_quality_round.py',
                   'run_cpi_r50_shared_segment.py', 'run_cpi_convnext_shared_segment.py',
                   'run_cpi_continuation.py'}
        if (guarded.intersection(names) and b'--status' not in argv) or (
                'run_cihp_system.py' in names and any(m.encode() in argv for m in MODELS.values())):
            raise RuntimeError('CPI process already exists: PID ' + proc.name)


def history_folders(parent, mid):
    paths = [parent / 'validation' / mid]
    paths += list(parent.glob('continuations/*/segments/' + mid))
    paths += list(parent.glob('rounds/*/segments/' + mid))
    paths += list(ART.glob('*/segments/' + mid))
    return sorted({p.resolve() for p in paths if p.exists()})


def elapsed_seconds(records):
    """Account every unique actual worker attempt, not overlapping controller clocks."""
    total = 0.0
    evidence = []
    for path in sorted(set(records)):
        record = json.loads(path.read_text())
        if 'start_utc' not in record or 'end_utc' not in record:
            raise ValueError('Unclosed prior worker clock: ' + str(path))
        seconds = (datetime.fromisoformat(record['end_utc']) -
                   datetime.fromisoformat(record['start_utc'])).total_seconds()
        if seconds < 0:
            raise ValueError('Negative prior worker duration')
        total += seconds
        evidence.append({'record': str(path.relative_to(W)), 'sha256': file_hash(path),
                         'seconds': seconds})
    return total, evidence


def prepare(mid, root):
    cfgpath = P / 'configs/cihp_native_six.json'
    cfg = json.loads(cfgpath.read_text())
    parent = W / cfg['artifact_root']
    digest = file_hash(cfgpath)
    if file_hash(parent / 'FROZEN_CONFIG.json') != digest:
        raise ValueError('Frozen config differs')
    for path, expected in cfg['source_bindings'].items():
        if file_hash(W / path) != expected:
            raise ValueError('Frozen source differs: ' + path)
    spec = cfg['models'][mid]
    if Path(sys.prefix).resolve() != (W / spec['environment']).resolve():
        raise ValueError('Use the frozen model environment for exact saved-score reconciliation: ' +
                         spec['environment'] + '/bin/python')
    for path, expected in [(spec['checkpoint'], spec['checkpoint_sha256']),
                           (spec['native_config'], spec['native_config_sha256']),
                           (cfg['authority'], cfg['authority_sha256'])]:
        if file_hash(W / path) != expected:
            raise ValueError('Identity mismatch: ' + path)
    if subprocess.check_output(['git', '-C', str(W / spec['source']), 'rev-parse', 'HEAD'],
                               text=True).strip() != spec['source_commit']:
        raise ValueError('Third-party source revision differs')
    if file_hash(parent / 'FROZEN_POPULATION.json') != cfg['dataset']['population_sha256']:
        raise ValueError('Frozen population differs')
    if file_hash(W / cfg['dataset']['population']) != cfg['dataset']['population_sha256']:
        raise ValueError('Active population differs')
    pop = {r['id']: r for r in json.loads((parent / 'FROZEN_POPULATION.json').read_text())['members']}
    if len(pop) != 5000:
        raise ValueError('Expected 5,000 unique IDs')
    det = {r['image_id']: r for r in map(json.loads,
           (W / cfg['frozen_YOLO']['validation_ledger']).read_text().splitlines())}
    folders = history_folders(parent, mid)
    seen, audits = set(), []
    for i, folder in enumerate(folders):
        audit = root / 'reuse_audits' / str(i)
        result = validate_folder(folder, cfg, pop, det, audit, digest, allow_noncomplete=True)
        if seen.intersection(result['verified_ids']):
            raise ValueError('Duplicate successful IDs across segments; no output choice allowed')
        seen.update(result['verified_ids'])
        audits.append(audit)
    records = [f / 'RUN.json' for f in folders if (f / 'RUN.json').exists()]
    # Readiness diagnostic calls count toward resources, never toward canonical IDs.
    records += list(parent.glob('rounds/*/diagnostic/' + mid + '/RUN.json'))
    seconds, clocks = elapsed_seconds(records)
    retained = sum(f.stat().st_size for folder in folders for f in folder.rglob('*') if f.is_file())
    retained += sum(f.stat().st_size for run in records if 'diagnostic' in run.parts
                    for f in run.parent.rglob('*') if f.is_file())
    pending = [i for i in pop if i not in seen]
    if not pending:
        raise ValueError('Already complete; no inference needed')
    if seconds >= cfg['max_system_hours'] * 3600:
        raise ValueError('Cumulative time cap consumed')
    if retained >= cfg['max_per_system_artifact_gib'] * 2**30:
        raise ValueError('Cumulative artifact cap consumed')
    if shutil.disk_usage(root).free < cfg['minimum_free_gib'] * 2**30:
        raise ValueError('Free-space guard')
    policy = {'mode': 'SHARED_GPU_QUALITY_ONLY', 'authorized_models': [mid],
              'quality_only': True, 'timing_ranking_allowed': False,
              'authority': 'Explicit operator invocation of requested CPI continuation command',
              'model_retries': 0, 'fallback': False, 'same_scientific_settings': True}
    write(root / 'RESOURCE_POLICY.json', policy)
    source = expanded_worker(mid)
    (root / 'EXPANDED_WORKER.py').write_text(source)
    (root / 'CONTROL_DIFF.patch').write_text(''.join(difflib.unified_diff(
        (P / 'scripts/run_cihp_system.py').read_text().splitlines(True), source.splitlines(True),
        fromfile='frozen_worker', tofile='operator_continuation_worker')))
    retained += sum(f.stat().st_size for f in root.rglob('*') if f.is_file())
    plan = {'parent_run_id': parent.name, 'parent_artifact_root': str(parent.relative_to(W)),
            'continuation_id': root.name, 'model_id': mid,
            'config': str(cfgpath.relative_to(W)), 'config_sha256': digest,
            'pending_ids': pending, 'reused_ids': [i for i in pop if i in seen],
            'prior_execution_seconds': seconds, 'prior_retained_bytes': retained,
            'attempt_clocks': clocks, 'reuse_audits': [str(a.relative_to(W)) for a in audits],
            'wrapper_sha256': file_hash(__file__),
            'frozen_worker_sha256': file_hash(P / 'scripts/run_cihp_system.py'),
            'expanded_worker_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'resource_policy': str((root / 'RESOURCE_POLICY.json').relative_to(W)),
            'resource_policy_sha256': file_hash(root / 'RESOURCE_POLICY.json'),
            'shared_GPU_quality_only': True, 'model_retries': 0,
            'manual_failed_ID_attempt_authorized_by_invocation': True,
            'extra_TRAIN_warmup_ID': '0000930',
            'changes': ['fresh segment and explicit pending IDs', 'shared quality resource admission',
                        'new outputs location; historical artifacts stay in place'],
            'diagnostic': 'Prior ConvNeXt readiness diagnostic remains historical; not reused as canonical'}
    write(root / 'SEGMENT_PLAN.json', plan)
    return cfg, pop, det, plan


def aggregate(audits, population):
    """Only current unresolved IDs affect completeness; preserve all failed attempts."""
    import numpy as np
    hist = np.zeros((20, 20), np.int64)
    native = hist.copy()
    people = {str(t): dict(G_loc=0, G_sem=0, TP=0, FP=0, FN=0, Q_numerator=0.) for t in [.5, .75]}
    ids, attempts = set(), []
    for audit in audits:
        rec = json.loads((audit / 'RECONCILED.json').read_text())
        if ids.intersection(rec['verified_ids']):
            raise ValueError('Duplicate completed ID during assembly')
        ids.update(rec['verified_ids'])
        hist += np.asarray(rec['histogram'], np.int64)
        native += np.asarray(rec['native_histogram'], np.int64)
        for t, values in people.items():
            for key in values:
                values[key] += rec['person_sufficient_statistics'][t][key]
        attempts += json.loads((audit / 'INVENTORY.json').read_text())['non_complete_ledger']
    if not ids <= set(population):
        raise ValueError('Out-of-population committed packet')
    invalid = {a['image_id'] for a in attempts if a['status'] == 'INVALID'} - ids
    failed = {a['image_id'] for a in attempts if a['status'] == 'FAILED'} - ids - invalid
    missing = set(population) - ids
    complete = not missing
    for v in people.values():
        v.update(extent_precision=v['TP'] / (v['TP'] + v['FP']) if v['TP'] + v['FP'] else None,
                 extent_recall=v['TP'] / v['G_loc'] if v['G_loc'] else None,
                 extent_F1=2*v['TP']/(2*v['TP']+v['FP']+v['FN']) if 2*v['TP']+v['FP']+v['FN'] else None,
                 Q_person_sem_GT=v['Q_numerator']/v['G_sem'] if v['G_sem'] else None)
    return {'status': 'COMPLETE' if complete else 'INCOMPLETE', 'expected': len(population),
            'complete': len(ids), 'missing_IDs': len(missing), 'duplicate_IDs': 0,
            'failed': len(failed), 'invalid': len(invalid),
            'not_attempted': len(missing - failed - invalid), 'historical_failure_attempts': attempts,
            'metrics': {'primary': semantic_report(hist) if complete else None,
                        'native_reference_primary': semantic_report(native) if complete else None,
                        'person_metrics': people if complete else None},
            'missing_ids': sorted(missing)}


def execute(root, cfg, pop, det, plan):
    started = now()
    state = {'status': 'RUNNING', 'round_id': root.name, 'model_id': plan['model_id'],
             'expected': len(pop), 'controller_PID': os.getpid(), 'start_utc': started,
             'resource_mode': 'SHARED_GPU_QUALITY_ONLY', 'reused': len(plan['reused_ids'])}
    state['controller_start_ticks'] = int(Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19])
    state['GPU_at_launch'] = subprocess.check_output(
        ['nvidia-smi', '--query-gpu=name,memory.used,memory.free,utilization.gpu',
         '--format=csv,noheader'], text=True).strip()
    state['external_GPU_PIDs_at_launch'] = subprocess.check_output(
        ['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).split()
    state['launch_commit'] = subprocess.check_output(
        ['git', '-C', str(W / 'Human_Parsing_Study_Public'), 'rev-parse', 'HEAD'], text=True).strip()
    write(root / 'ROUND_STATUS.json', state)
    folder = root / 'segments' / plan['model_id']
    cmd = [str(W / cfg['models'][plan['model_id']]['environment'] / 'bin/python'), '-B',
           str(Path(__file__).resolve()), '--worker', '--segment-manifest', str(root / 'SEGMENT_PLAN.json'),
           '--config', str(W / plan['config']), '--model', plan['model_id'],
           '--phase', 'validation', '--output', str(folder)]
    with (root / 'WORKER.log').open('x') as log:
        child = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        state.update(worker_PID=child.pid, command=cmd)
        write(root / 'LAUNCH.json', state)
        write(root / 'ROUND_STATUS.json', state)
        began = time.monotonic()
        try:
            while child.poll() is None:
                if plan['prior_execution_seconds'] + time.monotonic() - began > cfg['max_system_hours']*3600:
                    state['watchdog_stop'] = 'CUMULATIVE_TIME_CAP'
                    child.terminate()
                    try:
                        child.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        child.kill()
                    break
                try:
                    child.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    pass
        finally:
            if child.poll() is None:
                child.wait()
    state.update(status='POSTFLIGHT', worker_exit_code=child.returncode)
    write(root / 'ROUND_STATUS.json', state)
    audit = root / 'final_audit' / plan['model_id']
    validate_folder(folder, cfg, pop, det, audit, plan['config_sha256'], allow_noncomplete=True)
    combined = aggregate([W / a for a in plan['reuse_audits']] + [audit], pop)
    state.update(combined, end_utc=now(), queue_stopped=True, next_model_started=False)
    write(root / 'COMPLETION.json', state)
    write(root / 'ROUND_STATUS.json', state)
    compact = P / 'runs' / root.name
    for name in ['SEGMENT_PLAN.json', 'RESOURCE_POLICY.json', 'LAUNCH.json', 'COMPLETION.json']:
        write(compact / name, json.loads((root / name).read_text()))
    report = P / 'reports' / (root.name + '.md')
    report.write_text('# CPI manual continuation\n\n' +
        f"Model `{plan['model_id']}`; segment `{root.name}`.\n\n" +
        f"StartUTC `{started}`, endUTC `{state['end_utc']}`. Status **{state['status']}**; " +
        f"complete {state['complete']}/{state['expected']}, failed {state['failed']}, " +
        f"invalid {state['invalid']}, missing {state['missing_IDs']}.\n\n" +
        f"Canonical completion: [COMPLETION](../runs/{root.name}/COMPLETION.json). " +
        f"Raw artifacts: `{root.relative_to(W)}`.\n\n" +
        'Frozen CIHP native scientific settings; YOLO-associated application pipeline. ' +
        'STRICT_COMPLETE: primary null unless complete. Historical attempts retained; ' +
        'shared-GPU adapter timing only, no speed ranking. No next model or automatic retry.\n')
    print(json.dumps({k: v for k, v in state.items() if k != 'metrics'}), flush=True)
    return 0 if state['status'] == 'COMPLETE' else 1


def worker():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--segment-manifest', required=True)
    a, _ = parser.parse_known_args()
    planpath = Path(a.segment_manifest)
    plan = json.loads(planpath.read_text())
    if file_hash(__file__) != plan['wrapper_sha256']:
        raise ValueError('Continuation source differs')
    if file_hash(P / 'scripts/run_cihp_system.py') != plan['frozen_worker_sha256']:
        raise ValueError('Frozen worker differs')
    if file_hash(W / plan['resource_policy']) != plan['resource_policy_sha256']:
        raise ValueError('Resource policy differs')
    if file_hash(W / plan['config']) != plan['config_sha256']:
        raise ValueError('Scientific config differs')
    from run_cihp_segment import validate_partition
    cfg = json.loads((W / plan['config']).read_text())
    pop = [r['id'] for r in json.loads((W / cfg['dataset']['population']).read_text())['members']]
    validate_partition(pop, plan['pending_ids'], plan['reused_ids'])
    source = expanded_worker(plan['model_id'])
    if hashlib.sha256(source.encode()).hexdigest() != plan['expanded_worker_sha256']:
        raise ValueError('Expanded worker differs')
    sys.argv.remove('--worker')
    exec(compile(source, __file__, 'exec'), {'__name__': '__main__', '__file__': __file__,
                                         'segment_bind': file_hash(planpath)})


def main():
    if '--worker' in sys.argv:
        return worker()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=MODELS, required=True)
    parser.add_argument('--execute', action='store_true', help='Explicitly start one manual attempt after reconciliation')
    parser.add_argument('--status', action='store_true')
    parser.add_argument('--watch', action='store_true')
    a = parser.parse_args()
    ART.mkdir(parents=True, exist_ok=True)
    pointer = ART / ('CURRENT_' + a.model + '.txt')
    if a.status:
        from rpr_progress import snapshot, render, alive
        root = W / pointer.read_text().strip()
        def controller_alive(pid, script, location):
            state = json.loads((location / 'ROUND_STATUS.json').read_text())
            if pid != state.get('controller_PID'):
                return alive(pid, script, location)
            if not pid:
                return False
            try:
                proc = Path('/proc') / str(pid)
                argv = (proc / 'cmdline').read_bytes().split(b'\0')
                ticks = int((proc / 'stat').read_text().rsplit(')', 1)[1].split()[19])
                return (state.get('controller_start_ticks') == ticks and
                        any(Path(os.fsdecode(v)).name == script for v in argv if v) and
                        b'--model' in argv and argv[argv.index(b'--model')+1] == a.model.encode())
            except FileNotFoundError:
                return False
        while True:
            status = snapshot(root, liveness=controller_alive, model=MODELS[a.model], controller_script=Path(__file__).name,
                              worker_script=Path(__file__).name)
            print(render(status), flush=True)
            if not a.watch or status['terminal'] or status['phase'].startswith('INTERRUPTED'):
                return
            time.sleep(5)
    if a.watch:
        parser.error('--watch requires --status')
    with (ART / 'CPI.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        reject_existing_worker()
        root = ART / (a.model + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        root.mkdir(exist_ok=False)
        pointer.write_text(str(root.relative_to(W)) + '\n')
        try:
            cfg, pop, det, plan = prepare(MODELS[a.model], root)
            write(root / 'ROUND_STATUS.json', {'status': 'READY_NOT_LAUNCHED', 'expected': len(pop),
                  'reused': len(plan['reused_ids']), 'remaining': len(plan['pending_ids']),
                  'model_id': plan['model_id'], 'round_id': root.name})
            print(f"Verified {len(plan['reused_ids'])}; pending {len(plan['pending_ids'])}; {root}", flush=True)
            if a.execute:
                return execute(root, cfg, pop, det, plan)
        except Exception:
            failure = {'status': 'INCOMPLETE_REQUIRES_RECONCILIATION' if (root / 'LAUNCH.json').exists()
                       else 'BLOCKED_SETUP', 'queue_stopped': True,
                       'model_id': MODELS[a.model], 'end_utc': now(), 'error': traceback.format_exc()}
            write(root / 'CONTROLLER_FAILURE.json', failure)
            previous = json.loads((root / 'ROUND_STATUS.json').read_text()) if (root / 'ROUND_STATUS.json').exists() else {}
            write(root / 'ROUND_STATUS.json', {**previous, **failure})
            raise


if __name__ == '__main__':
    raise SystemExit(main())
