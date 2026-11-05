"""Controlled continuation of the frozen CIHP worker with verified parent reuse.

The original runner/config and parent evidence stay byte-identical. Exact source
substitutions generate a reviewable worker snapshot, reusing its scoring and
export implementation. The RP-R-CNN empty decoder is the accepted CCTV repair.
"""
from pathlib import Path
import argparse
import inspect
import json
import os
import subprocess
import sys
import time
import numpy as np
from PIL import Image

import controlled_cihp as base
from controlled_roi_core import atomic, read, sha, pixel_sha, validate_native
from common_view.packets import read_packet
from controlled_roi_continuation import continuation_model, empty_rpr_prediction

H, W = base.H, base.W


def verify_reuse(reference):
    packet = W/reference['packet']
    for name, digest in reference['members'].items():
        if sha(packet/name) != digest:
            raise ValueError('Parent committed observation changed: '+str(packet/name))
    return read_packet(packet)


def accumulate(evaluation, iid, accumulator, part_sums):
    accumulator.add(iid, evaluation['scores'])
    accumulator.hist += np.asarray(evaluation['scores']['0.5']['histogram'], np.int64)
    for part in evaluation['parts']:
        target = part_sums[str(part['target'])]
        target['count'] += 1
        target['IoU_sum'] += part['IoU']
        for key in ['TP','FP','FN']:
            target[key] += part[key]
        target['unmatched'] += int(part['unmatched'])


def model_factory(workspace, spec, output):
    return continuation_model(workspace, spec, output)


def generated_worker():
    source = inspect.getsource(base.worker)
    patches = [
        ('    from controlled_roi_models import CropModel',
         '    CropModel = model_factory'),
        ("if time.monotonic()-started > config['max_hours']*3600:",
         "if time.monotonic()-started+config['prior_execution_seconds'].get(mid,0) > config['max_hours']*3600:"),
        ("if max(bytes_written, measured_storage[0]) > config['max_stream_gib']*2**30:",
         "if max(bytes_written, measured_storage[0])+config['prior_stream_bytes'].get(mid,0) > config['max_stream_gib']*2**30:"),
        ("calls >= config['model_call_limit_per_model']:",
         "calls >= config['pending_call_limits'][mid]:"),
        ("            result = model.infer(rgb, path, box)",
         "            from controlled_roi_models import CropModel as OriginalModel\n            result = OriginalModel.infer(model, rgb, path, box)"),
        ("            m, d = frame['member'], frame['detector']\n            iid = m['id']",
         """            m, d = frame['member'], frame['detector']
            iid = m['id']
            reused_frame = config['reuse_frames'].get(mid, {}).get(iid)
            if reused_frame:
                verify_reuse(reused_frame)
                score_path = W/reused_frame['score_path']
                if sha(score_path) != reused_frame['score_sha256']:
                    raise ValueError('Parent saved scores changed')
                evaluation = read(score_path)
                accumulate(evaluation, iid, accumulator, part_sums)
                state['completed'] += 1
                state['reused_frames'] = state.get('reused_frames',0)+1
                emit(ledger, event='PARENT_FRAME_REUSED', image_id=iid,
                     parent_packet=reused_frame['packet'], parent_score_sha256=sha(score_path))
                save()
                continue"""),
        ("                (native, candidates, details), timing = infer(crop, path, designated, 'VAL')",
         """                key = iid+'_%03d'%j
                reference = config['reuse_ROIs'].get(mid, {}).get(key)
                if reference:
                    reused_meta, reused_arrays = verify_reuse(reference)
                    native = reused_arrays['native_crop_mask']
                    candidates = reused_arrays['native_candidate_masks']
                    details = dict(reused_meta['geometry'])
                    details['parent_reuse_reference'] = reference['packet']
                    timing = dict(reused_meta['timing'], origin='PARENT_OBSERVATION',
                                  current_frame_wall_includes_this_forward=False)
                    state['reused_partial_ROIs'] = state.get('reused_partial_ROIs',0)+1
                else:
                    (native, candidates, details), timing = infer(crop, path, designated, 'VAL')"""),
        ("                roi = write_packet(output/'roi_packets', iid+'_%03d'%j,",
         "                roi = (W/reference['packet']) if reference else write_packet(output/'roi_packets', iid+'_%03d'%j,"),
        ("                bytes_written += sum(p.stat().st_size for p in roi.iterdir() if p.is_file())",
         "                if not reference:\n                    bytes_written += sum(p.stat().st_size for p in roi.iterdir() if p.is_file())"),
        ("        if actual_ids != set(manifest['expected_ids']) or state['ROI_calls'] != config['ROI_count']:",
         "        actual_ids |= set(config['reuse_frames'].get(mid,{}))\n        reused_ROI_count = len(config['reuse_ROIs'].get(mid,{}))\n        if actual_ids != set(manifest['expected_ids']) or state['ROI_calls']+reused_ROI_count != config['ROI_count']:"),
        ("        state.update(status='COMPLETE', primary=result['primary'], ended_utc=utc())",
         """        assembled = dict(parent_config=config['parent_config'], config_sha256=sha(cp),
                         expected_ids=manifest['expected_ids'],
                         parent_frames=config['reuse_frames'].get(mid,{}),
                         new_packet_root=rel(output/'packets'),
                         effective_implementation='RPR_ROI_EMPTY_OUTPUT_1' if mid=='RPR_CIHP' else 'PARENT_MODEL_BEHAVIOR',
                         accepted_ROIs_by_revision={'PARENT':len(config['reuse_ROIs'].get(mid,{})),
                                                    'CONTINUATION':state['ROI_calls']})
        atomic(output/'ASSEMBLED_INDEX.json', assembled)
        state.update(status='COMPLETE', primary=result['primary'], ended_utc=utc())"""),
    ]
    for original, replacement in patches:
        if source.count(original) != 1:
            raise ValueError('Frozen worker source substitution does not match: '+original)
        source = source.replace(original, replacement)
    compile(source, '<controlled-cihp-continuation-worker>', 'exec')
    return source, patches


def prepare():
    parentcp = H/'configs/controlled_cihp_quality.json'
    parent = base.verify_config(parentcp)
    pr = W/parent['artifact_root']
    controller = read(pr/'CONTROLLER.json')
    if controller['status'] != 'STOPPED_REQUIRES_RECONCILIATION':
        raise ValueError('Parent must be terminal before continuation')
    for pid in [controller.get('pid'), controller.get('worker_pid')]:
        if pid and Path('/proc',str(pid)).exists():
            raise RuntimeError('Parent process still alive')
    failure = read(pr/'RPR_CIHP/FAILURE.json')
    if failure['error'] != "KeyError('parsing')":
        raise ValueError('This repair is scoped only to missing parsing')
    root = H/'outputs'/('cihp-controlled-continuation-'+base.utc().replace('-','').replace(':','').split('.')[0]+'Z')
    root.mkdir(parents=True, exist_ok=False)
    config = dict(parent)
    config.update(run_id=root.name, artifact_root=base.rel(root), created_utc=base.utc(),
                  parent_config=base.rel(parentcp), parent_config_sha256=sha(parentcp),
                  status='FROZEN_CONTROLLED_CONTINUATION', completed_sources={}, reuse_frames={}, reuse_ROIs={},
                  prior_execution_seconds={}, prior_stream_bytes={}, pending_call_limits={},
                  continuation_reason='RPR zero-native-detection decoder repair; known CCTV implementation',
                  automatic_retry=0, automatic_recovery=0)
    frames = {f['member']['id']:f for f in read(W/parent['manifest'])['frames']}
    parent_digest = sha(parentcp)
    completed = ['QANet_CIHP_HRNetW48_512x384','M2FP_R101_CIHP','D2FP_R101_CIHP']
    for mid in completed:
        old = pr/mid
        completion = read(old/'COMPLETION.json')
        if not completion['strict_complete'] or completion['completed'] != 5000 or sha(old/'METRICS.json') != completion['metrics_sha256']:
            raise ValueError('Completed model binding mismatch')
        config['completed_sources'][mid] = dict(root=base.rel(old), completion_sha256=sha(old/'COMPLETION.json'), metrics_sha256=sha(old/'METRICS.json'))
    mid = 'RPR_CIHP'
    old = pr/mid
    config['prior_execution_seconds'][mid] = read(old/'STATE.json')['execution_wall_seconds']
    config['prior_stream_bytes'][mid] = sum(p.stat().st_size for p in old.rglob('*') if p.is_file())
    ledger = [json.loads(line) for line in (old/'ATTEMPTS.jsonl').read_text().splitlines()]
    accepted = {r['image_id']:r for r in ledger if r.get('event')=='FRAME_COMMITTED'}
    config['reuse_frames'][mid] = {}
    config['reuse_ROIs'][mid] = {}
    def record(packet):
        return dict(packet=base.rel(packet), members={p.name:sha(p) for p in packet.iterdir() if p.is_file()})
    for packet in sorted((old/'packets').iterdir()):
        if packet.name.startswith('.'):
            raise ValueError('Unresolved parent frame orphan')
        meta, arrays = read_packet(packet)
        iid = packet.name
        frame = frames[iid]
        _, _, extents, scores = base.load_frame(frame)
        if meta['config_sha256'] != parent_digest or meta['checkpoint_sha256'] != parent['models'][mid]['checkpoint_sha256'] or meta['input_sha256'] != frame['member']['RGB_sha256']:
            raise ValueError('Parent frame scientific identity mismatch')
        if not np.array_equal(arrays['person_extents'], extents) or not np.array_equal(arrays['person_scores'], scores):
            raise ValueError('Parent detector ownership changed')
        if not np.array_equal(arrays['person_semantic_masks'],np.where(extents,arrays['native_roi_unowned_semantic_masks'],0)):
            raise ValueError('Parent owned-mask contract')
        score = old/'scores'/(iid+'.json')
        if sha(score) != accepted[iid]['score_sha256'] or meta['packet_sha256'] != accepted[iid]['packet_sha256'] or read(score)['source_packet_sha256'] != meta['packet_sha256']:
            raise ValueError('Parent score ledger fingerprint changed')
        config['reuse_frames'][mid][iid] = dict(record(packet),score_path=base.rel(score),score_sha256=sha(score))
    if set(config['reuse_frames'][mid]) != set(accepted):
        raise ValueError('Parent frame packet/ledger mismatch')
    from sapiens_input_variants import detector_crop
    decoded = {}
    for packet in sorted((old/'roi_packets').iterdir()):
        if packet.name.startswith('.'):
            raise ValueError('Unresolved parent ROI orphan')
        meta, arrays = read_packet(packet)
        iid, number = packet.name.rsplit('_',1)
        j = int(number)
        if iid not in decoded:
            decoded[iid] = base.load_frame(frames[iid])
        _, rgb, extents, _ = decoded[iid]
        opportunity = frames[iid]['detector']['opportunities'][j]
        crop, box = detector_crop(rgb, opportunity['bbox'], extents[j], .1)
        if any(meta[k] != value for k,value in dict(config_sha256=parent_digest,model_id=mid,
                checkpoint_sha256=parent['models'][mid]['checkpoint_sha256'], input_sha256=frames[iid]['member']['RGB_sha256']).items()):
            raise ValueError('Parent ROI scientific identity mismatch')
        geometry = meta['geometry']
        if geometry['crop_xyxy'] != box or geometry['opportunity_id'] != opportunity['id'] or geometry['crop_pixel_sha256'] != pixel_sha(crop):
            raise ValueError('Parent crop geometry/content binding mismatch')
        validate_native(arrays['native_crop_mask'],20,crop.shape[:2])
        for value in arrays['native_candidate_masks']:
            validate_native(value,20,crop.shape[:2])
        config['reuse_ROIs'][mid][packet.name] = record(packet)
    if len(config['reuse_frames'][mid]) != 22 or len(config['reuse_ROIs'][mid]) != 149:
        raise ValueError('Reconciliation differs from frozen parent, review before launch')
    config['parent_failure_sha256'] = sha(old/'FAILURE.json')
    for model in config['model_order']:
        config['pending_call_limits'][model] = parent['ROI_count']-len(config['reuse_ROIs'].get(model,{}))+2
    # Preserve the original dependency closure and add the existing tested repair.
    config['source_hashes'] = dict(parent['source_hashes'])
    for p in [Path(__file__), W/'CCTV_Human_Parsing_Benchmark/scripts/controlled_roi_continuation.py']:
        config['source_hashes'][base.rel(p)] = sha(p)
    generated, changes = generated_worker()
    snapshot = root/'WORKER_REVISION2.py'
    snapshot.write_text(generated)
    config['generated_worker'] = base.rel(snapshot)
    config['generated_worker_sha256'] = sha(snapshot)
    config['source_substitutions'] = changes
    config['historical_attempt'] = dict(failed_image=failure['current_id'], successful_frames=22,
        successful_ROIs=149, attempted_VAL_calls=150, TRAIN_calls=2, retained=True)
    atomic(root/'CONFIG.json',config)
    atomic(root/'RECONCILIATION.json',dict(status='PASS',parent_run=parent['run_id'],
        completed_models_reused=completed, accepted_frames=22,accepted_ROIs=149,
        partial_frame='0000312',partial_frame_accepted_ROIs=2,missing_ROIs=parent['ROI_count']-149,
        failure_preserved=True,model_inference_calls=0,source_revision='RPR_ROI_EMPTY_OUTPUT_1'))
    print(base.rel(root/'CONFIG.json'))


def worker(cp, mid):
    config = base.verify_config(cp)
    source, _ = generated_worker()
    if source != base.checked(config['generated_worker'],config['generated_worker_sha256']).read_text():
        raise ValueError('Generated worker differs from frozen source snapshot')
    namespace = dict(vars(base), model_factory=model_factory, verify_reuse=verify_reuse, accumulate=accumulate)
    exec(compile(source, str(W/config['generated_worker']), 'exec'), namespace)
    namespace['worker'](cp,mid)


def controller(cp):
    config = base.verify_config(cp)
    root = W/config['artifact_root']
    if (root/'CONTROLLER.json').exists():
        raise FileExistsError('Continuation already has an attempt')
    import fcntl
    lock = (H/'outputs/CONTROLLED_CIHP_CONTROLLER.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    acceptance = read(H/'reports/CONTROLLED_CIHP_CONTINUATION_ACCEPTANCE.json')
    if acceptance['status'] != 'PASS':
        raise ValueError('Continuation acceptance missing')
    for path,digest in acceptance['source_hashes'].items():
        base.checked(path,digest)
    state = dict(status='RUNNING',pid=os.getpid(),started_utc=base.utc(),models={},worker_pid=None,
                 current_model=None,queue_stopped=False,parent_run=read(W/config['parent_config'])['run_id'])
    for mid in config['model_order']:
        if mid in config['completed_sources']:
            ref = config['completed_sources'][mid]
            base.checked(ref['root']+'/COMPLETION.json',ref['completion_sha256'])
            state['models'][mid] = dict(status='PARENT_COMPLETE_REUSED', returncode=0)
            continue
        state.update(status='QUEUED_RESOURCE',current_model=mid)
        atomic(root/'CONTROLLER.json',state)
        queued = time.monotonic()
        while float(subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).splitlines()[0]) < config['required_free_MiB'][mid]:
            if time.monotonic()-queued >= config['resource_queue_timeout_seconds']:
                state.update(status='STOPPED_RESOURCE',queue_stopped=True)
                atomic(root/'CONTROLLER.json',state)
                return
            time.sleep(15)
        env = os.environ.copy()
        if config['models'][mid]['family']=='Sapiens2':
            env['PYTHONPATH'] = str(W/config['models'][mid]['source'])
        command = [str(W/config['models'][mid]['environment']/'bin/python'),'-u',str(Path(__file__)),
                   'worker','--config',str(cp),'--model',mid]
        with (root/(mid+'.log')).open('x') as log:
            child = subprocess.Popen(command,cwd=W,env=env,stdout=log,stderr=subprocess.STDOUT)
            state.update(status='MODEL_RUNNING',worker_pid=child.pid,command=command,
                         queue_wait_seconds=time.monotonic()-queued)
            atomic(root/'CONTROLLER.json',state)
            code = child.wait()
        state['worker_pid'] = None
        state['models'][mid] = dict(returncode=code,ended_utc=base.utc())
        if code:
            failure = read(root/mid/'FAILURE.json') if (root/mid/'FAILURE.json').exists() else {}
            if failure.get('error_kind')!='MODEL_OOM':
                state.update(status='STOPPED_REQUIRES_RECONCILIATION',queue_stopped=True)
                atomic(root/'CONTROLLER.json',state)
                return
    state.update(status='BATCH_TERMINAL',queue_stopped=True,ended_utc=base.utc())
    atomic(root/'CONTROLLER.json',state)


def progress(cp):
    config = read(cp)
    root = W/config['artifact_root']
    state = read(root/'CONTROLLER.json') if (root/'CONTROLLER.json').exists() else dict(status='PREPARED')
    print(config['run_id'],base.utc(),state['status'])
    print('Controller',state.get('pid'),'Worker',state.get('worker_pid'),'Model',state.get('current_model'))
    for mid in config['model_order']:
        origin = W/config['completed_sources'][mid]['root'] if mid in config.get('completed_sources',{}) else root/mid
        s = read(origin/'STATE.json') if (origin/'STATE.json').exists() else {}
        print(mid,s.get('status','NOT_STARTED'),str(s.get('completed',0))+'/5000',
              'New_ROI_calls',s.get('ROI_calls',0),'Reused_parent_ROIs',len(config.get('reuse_ROIs',{}).get(mid,{})))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','worker','controller','progress'])
    parser.add_argument('--config',type=Path)
    parser.add_argument('--model')
    args = parser.parse_args()
    if args.action=='prepare':
        prepare()
        return
    cp = args.config or H/'configs/controlled_cihp_continuation.json'
    if args.action=='worker':worker(cp,args.model)
    elif args.action=='controller':controller(cp)
    else:progress(cp)

if __name__=='__main__':main()
