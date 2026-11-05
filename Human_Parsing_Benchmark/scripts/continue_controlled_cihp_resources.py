"""Continue the CIHP queue using existing own-cache memory accounting.

Frozen inference/score code and earlier controllers stay unchanged. Only the
pre-forward resource guard counts the process's reusable PyTorch reservation.
"""
import argparse
import inspect
from pathlib import Path

import continue_controlled_cihp as previous
from controlled_roi_continuation import reusable_memory

H, W = previous.H, previous.W
_parent_worker_source = previous.generated_worker


def generated_worker():
    source, changes = _parent_worker_source()
    original = "        if torch.cuda.mem_get_info()[0] < config['min_forward_free_MiB']*2**20:"
    replacement = """        from controlled_roi_continuation import reusable_memory
        memory = reusable_memory(torch.cuda.mem_get_info()[0], torch.cuda.memory_allocated(),
                                 torch.cuda.memory_reserved())
        state['last_memory_guard'] = memory
        if memory['effective_available_bytes'] < config['min_forward_free_MiB']*2**20:"""
    if source.count(original) != 1:
        raise ValueError('Frozen memory guard binding differs')
    source = source.replace(original,replacement)
    compile(source,'<controlled-cihp-own-cache-worker>','exec')
    return source, changes+[(original,replacement)]


def prepare():
    source = inspect.getsource(previous.prepare)
    replacements = [
        ("parentcp = H/'configs/controlled_cihp_quality.json'", "parentcp = H/'configs/controlled_cihp_continuation.json'"),
        ("pr/'RPR_CIHP/FAILURE.json'", "pr/'CPI_R50_CIHP/FAILURE.json'"),
        ('failure[\'error\'] != "KeyError(\'parsing\')"', 'failure[\'error\'] != "RuntimeError(\'RESOURCE_VRAM_HEADROOM_GUARD\')"'),
        ("root = H/'outputs'/('cihp-controlled-continuation-'", "root = H/'outputs'/('cihp-controlled-resources-'"),
        ("continuation_reason='RPR zero-native-detection decoder repair; known CCTV implementation'", "continuation_reason='Own reusable CUDA cache accounting; same1GiB headroom/no allocator or scientific changes'"),
        ("completed = ['QANet_CIHP_HRNetW48_512x384','M2FP_R101_CIHP','D2FP_R101_CIHP']", "completed = ['QANet_CIHP_HRNetW48_512x384','M2FP_R101_CIHP','D2FP_R101_CIHP','RPR_CIHP']"),
        ("    mid = 'RPR_CIHP'", "    mid = 'CPI_R50_CIHP'"),
        ("config['reuse_frames'][mid]) != 22 or len(config['reuse_ROIs'][mid]) != 149", "config['reuse_frames'][mid]) != 4 or len(config['reuse_ROIs'][mid]) != 34"),
        ("successful_frames=22,\n        successful_ROIs=149, attempted_VAL_calls=150", "successful_frames=4,\n        successful_ROIs=34, attempted_VAL_calls=34"),
        ("accepted_frames=22,accepted_ROIs=149", "accepted_frames=4,accepted_ROIs=34"),
        ("partial_frame='0000312',partial_frame_accepted_ROIs=2,missing_ROIs=parent['ROI_count']-149", "partial_frame='0000027',partial_frame_accepted_ROIs=3,missing_ROIs=parent['ROI_count']-34"),
        ("source_revision='RPR_ROI_EMPTY_OUTPUT_1'", "source_revision='OWN_REUSABLE_CUDA_CACHE_ACCOUNTING_1'"),
    ]
    for old,new in replacements:
        if source.count(old) != 1:
            raise ValueError('Continuation preparation source binding differs: '+old)
        source = source.replace(old,new)
    # Completed systems may reside in an earlier segment; verify those exact
    # references rather than looking for copied files in the latest segment.
    source = source.replace("old = pr/mid", "old = W/parent['completed_sources'][mid]['root'] if mid in parent.get('completed_sources',{}) else pr/mid")
    namespace = dict(vars(previous), generated_worker=generated_worker, __file__=__file__)
    exec(compile(source,'<controlled-cihp-resource-prepare>','exec'),namespace)
    namespace['prepare']()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','worker','controller','progress'])
    parser.add_argument('--config',type=Path)
    parser.add_argument('--model')
    args=parser.parse_args()
    if args.action=='prepare':
        prepare()
        return
    cp=args.config or H/'configs/controlled_cihp_resources.json'
    if args.action=='progress':
        previous.progress(cp)
        return
    # Commands spawned by the existing controller enter this revision explicitly.
    previous.__file__=__file__
    previous.generated_worker=generated_worker
    if args.action=='worker':previous.worker(cp,args.model)
    else:previous.controller(cp)


if __name__=='__main__':main()
