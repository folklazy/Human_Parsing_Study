"""Operator-authorized Sapiens interruption continuation; frozen worker reused."""
import argparse
import inspect
from pathlib import Path

import continue_controlled_cihp as previous
import continue_controlled_cihp_resources as resources

H, W = previous.H, previous.W


def prepare():
    source = inspect.getsource(previous.prepare)
    substitutions = [
        ("parentcp = H/'configs/controlled_cihp_quality.json'", "parentcp = H/'configs/controlled_cihp_resources.json'"),
        ("if controller['status'] != 'STOPPED_REQUIRES_RECONCILIATION':", "if controller['status'] not in ('MODEL_RUNNING','STOPPED_REQUIRES_RECONCILIATION'):"),
        ("pr/'RPR_CIHP/FAILURE.json'", "pr/'Sapiens2_0.8b/FAILURE.json'"),
        ("failure['error'] != \"KeyError('parsing')\"", "failure['error'] != 'KeyboardInterrupt()'"),
        ("root = H/'outputs'/('cihp-controlled-continuation-'", "root = H/'outputs'/('cihp-sapiens-resume-'"),
        ("continuation_reason='RPR zero-native-detection decoder repair; known CCTV implementation'", "continuation_reason='Operator-authorized KeyboardInterrupt recovery, identical scientific worker; CPI ConvNeXt held incomplete'"),
        ("completed = ['QANet_CIHP_HRNetW48_512x384','M2FP_R101_CIHP','D2FP_R101_CIHP']", "completed = ['QANet_CIHP_HRNetW48_512x384','M2FP_R101_CIHP','D2FP_R101_CIHP','RPR_CIHP','CPI_R50_CIHP','Sapiens2_0.4b']"),
        ("    mid = 'RPR_CIHP'", "    mid = 'Sapiens2_0.8b'"),
        ("config['reuse_frames'][mid]) != 22 or len(config['reuse_ROIs'][mid]) != 149", "config['reuse_frames'][mid]) != 4182 or len(config['reuse_ROIs'][mid]) != 19907"),
        ('validate_native(arrays[\'native_crop_mask\'],20,crop.shape[:2])', "validate_native(arrays['native_crop_mask'],29,crop.shape[:2])"),
        ('validate_native(value,20,crop.shape[:2])', 'validate_native(value,29,crop.shape[:2])'),
        ('successful_frames=22,\n        successful_ROIs=149, attempted_VAL_calls=150', 'successful_frames=4182,\n        successful_ROIs=19907, attempted_VAL_calls=19908'),
        ('accepted_frames=22,accepted_ROIs=149', 'accepted_frames=4182,accepted_ROIs=19907'),
        ("partial_frame='0000312',partial_frame_accepted_ROIs=2,missing_ROIs=parent['ROI_count']-149", "partial_frame='0036736',partial_frame_accepted_ROIs=0,missing_ROIs=parent['ROI_count']-19907"),
        ("source_revision='RPR_ROI_EMPTY_OUTPUT_1'", "source_revision='SAPIENS_INTERRUPTION_CONTINUATION_SAME_WORKER'"),
        ("config['prior_execution_seconds'][mid] = read(old/'STATE.json')['execution_wall_seconds']", "config['prior_execution_seconds'][mid] = read(old/'STATE.json')['execution_wall_seconds']"),
    ]
    for old, new in substitutions:
        if source.count(old) != 1:
            raise ValueError('Preparation source binding differs: '+old)
        source = source.replace(old, new)
    source = source.replace("old = pr/mid", "old = W/parent['completed_sources'][mid]['root'] if mid in parent.get('completed_sources',{}) else pr/mid")
    old = "        if iid not in decoded:\n            decoded[iid] = base.load_frame(frames[iid])"
    if source.count(old) != 1:
        raise ValueError('Reconciliation cache source differs')
    # Sorted ROI packets are grouped by image. Retain only one decoded image.
    source = source.replace(old,"        if iid not in decoded:\n            decoded.clear()\n            decoded[iid] = base.load_frame(frames[iid])")
    old = "    generated, changes = generated_worker()"
    replacement = """    config['model_order'] = completed + ['Sapiens2_0.8b','Sapiens2_1b']
    config['held_models'] = {'CPI_ConvNeXtB_CIHP':dict(root=base.rel(pr/'CPI_ConvNeXtB_CIHP'),status='STOPPED_INCOMPLETE',reason='MODEL_OOM; no new retry authorized by interruption recovery')}
    config['source_hashes'][base.rel(Path(__file__))] = sha(Path(__file__))
    generated, changes = generated_worker()"""
    if source.count(old) != 1:
        raise ValueError('Worker snapshot binding differs')
    source = source.replace(old,replacement)
    namespace = dict(vars(previous),generated_worker=resources.generated_worker,__file__=__file__)
    exec(compile(source,'<sapiens-interruption-prepare>','exec'),namespace)
    namespace['prepare']()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','worker','controller','progress'])
    parser.add_argument('--config',type=Path)
    parser.add_argument('--model')
    args = parser.parse_args()
    if args.action=='prepare':
        prepare()
        return
    if not args.config:
        raise ValueError('Explicit continuation config required')
    previous.__file__=__file__
    previous.generated_worker=resources.generated_worker
    if args.action=='progress':
        previous.progress(args.config)
        for model,ref in previous.read(args.config)['held_models'].items():
            s=previous.read(W/ref['root']/'STATE.json')
            print(model,'HELD_INCOMPLETE',str(s['completed'])+'/5000',ref['reason'])
    elif args.action=='worker':
        previous.worker(args.config,args.model)
    else:
        previous.controller(args.config)


if __name__=='__main__':
    main()
