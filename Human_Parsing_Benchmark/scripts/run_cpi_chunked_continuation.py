"""One-model CPI controlled continuation with explicit memory implementation.

Default reconciliation only. --execute is a fresh manual attempt, never a retry
loop. The legacy controller/scientific config stay unchanged on disk.
"""
from pathlib import Path
import hashlib
import json
import sys

import run_cpi_continuation as base

HERE = Path(__file__).resolve()
P = HERE.parents[1]
W = P.parent
MID = 'CPI_ConvNeXtB_CIHP'
HEAD_SHA = '85b75e0fe38465ec460107c11111702345a6de091a8ba3d399ca266878ca7573'
REVISION = 'CPI_PERSON_CHUNK_RESTORATION_1'
original_expand = base.expanded_worker
original_prepare = base.prepare
original_clocks = base.elapsed_seconds


def dependencies():
    paths = ['src/cihp_benchmark/cpi_memory.py', 'scripts/run_cpi_continuation.py',
             'scripts/run_cihp_segment.py', 'scripts/run_rpr_shared_segment.py',
             'scripts/run_cpi_r50_shared_segment.py', 'scripts/run_cpi_convnext_shared_segment.py']
    return {str((P / rel).relative_to(W)): base.file_hash(P / rel) for rel in paths}


def expanded(mid):
    if mid != MID:
        raise ValueError('Continuation model differs from selected model')
    text = original_expand(mid)
    patch_rel = 'Human_Parsing_Benchmark/src/cihp_benchmark/cpi_memory.py'
    patch_sha = base.file_hash(W / patch_rel)
    anchor = "adapter=NativeAdapter(W,spec,out/'adapter');result['model_details']=adapter.details;atomic(out/'RUN.json',result)"
    if text.count(anchor) != 1:
        raise ValueError('Frozen model-construction anchor changed')
    insert = (f"\n  if file_hash(W/{patch_rel!r})!={patch_sha!r}:raise ValueError('Memory implementation changed')"
              "\n  from cihp_benchmark.cpi_memory import install as install_memory_repair"
              f"\n  result['memory_implementation']=install_memory_repair(adapter.model.bbox_head,{HEAD_SHA!r})"
              "\n  atomic(out/'RUN.json',result)")
    text = text.replace(anchor, anchor + insert)
    marker = 'metadata.update(actual_resource_mode='
    if text.count(marker) != 1:
        raise ValueError('Frozen packet metadata anchor changed')
    provenance = (
        f"metadata['memory_implementation_revision']={REVISION!r};"
        f"metadata['memory_implementation_sha256']={patch_sha!r};"
        "metadata['base_inference_fingerprint']=metadata['inference_fingerprint'];"
        "metadata['implementation_fingerprint']=hashlib.sha256(json.dumps("
        "{'base':metadata['base_inference_fingerprint'],'revision':metadata['memory_implementation_revision'],"
        "'source':metadata['memory_implementation_sha256']},sort_keys=True).encode()).hexdigest();")
    packet_commit = "atomic(packet/'packet.json',metadata)"
    if text.count(packet_commit) != 2:
        raise ValueError('Frozen packet commit anchors changed')
    # The native metadata.update creates inference_fingerprint first.
    return text.replace(packet_commit, provenance + packet_commit, 1)


def diagnostic_records():
    records = []
    for path in (P / 'outputs/cpi_memory_diagnostics').glob('*/RUN.json'):
        value = json.loads(path.read_text())
        if value.get('model_id') == MID:
            if 'end_utc' not in value:
                raise ValueError('An existing diagnostic clock remains open: ' + str(path))
            records.append(path)
    return records


def clocks(records):
    return original_clocks(list(set(records) | set(diagnostic_records())))


def prepare(mid, root):
    cfg, pop, det, plan = original_prepare(mid, root)
    receipts = diagnostic_records()
    matched = []
    for receipt in receipts:
        state = json.loads(receipt.read_text())
        snapshot = P / 'runs' / state['run_id'] / 'DIAGNOSTIC_CONFIG.json'
        binding = json.loads(snapshot.read_text())
        if (state.get('status') == 'DIAGNOSTIC_PASS'
                and binding['model_id'] == mid
                and state['config_sha256'] == base.file_hash(snapshot)
                and binding['protected_hashes']['Human_Parsing_Benchmark/src/cihp_benchmark/cpi_memory.py'] == base.file_hash(P / 'src/cihp_benchmark/cpi_memory.py')
                and binding['protected_hashes']['Human_Parsing_Benchmark/configs/cihp_native_six.json'] == base.file_hash(P / 'configs/cihp_native_six.json')
                and state['patch']['original_head_sha256'] == HEAD_SHA
                and any(r.get('regression') == 'ALL_ARRAYS_EXACT_EQUAL_TO_SAVED_NATIVE_PACKET' for r in state['observations'])):
            matched.append(str(receipt.relative_to(W)))
    if not matched:
        raise ValueError('Bounded GPU repair diagnostic has not passed')
    additional = sum(f.stat().st_size for record in receipts for f in record.parent.rglob('*') if f.is_file())
    plan['prior_retained_bytes'] += additional
    if plan['prior_retained_bytes'] >= cfg['max_per_system_artifact_gib'] * 2**30:
        raise ValueError('Cumulative retained-artifact cap consumed')
    plan.update(implementation_revision=REVISION,
                implementation_dependencies=dependencies(),
                compatible_gpu_repair_evidence=matched,
                diagnostic_resources_included=[str(f.relative_to(W)) for f in receipts],
                reuse_compatibility={
                    'basis': 'All person-axis restoration operators are independent; four CPU cases, GPU fixture, actual native prefixes, exact known-success packet regression passed.',
                    'same_scientific_settings': True,
                    'old_base_fingerprint_alone_is_not_new_implementation_identity': True,
                    'diagnostic_predictions_reused_as_canonical': False})
    policy_path = W / plan['resource_policy']
    policy = json.loads(policy_path.read_text())
    policy.update(implementation_revision=REVISION,
                  authority='Explicit operator invocation of repaired ' + mid + ' continuation',
                  diagnostic_resource_accounting='Included in prior worker time and retained bytes')
    base.write(policy_path, policy)
    plan['resource_policy_sha256'] = base.file_hash(policy_path)
    base.write(root / 'SEGMENT_PLAN.json', plan)
    return cfg, pop, det, plan


def main():
    global MID
    if '--help' in sys.argv:
        print(__doc__ + '\nUse --model {convnext,r50} [--execute | --status [--watch]]. Each model requires its own matching GPU diagnostic.')
        return
    if '--model' in sys.argv:
        requested = sys.argv[sys.argv.index('--model') + 1]
        models = {'convnext': 'CPI_ConvNeXtB_CIHP', 'r50': 'CPI_R50_CIHP',
                  'CPI_ConvNeXtB_CIHP': 'CPI_ConvNeXtB_CIHP', 'CPI_R50_CIHP': 'CPI_R50_CIHP'}
        if requested not in models:
            raise ValueError('Explicit CPI model required')
        MID = models[requested]
    if '--worker' in sys.argv:
        path = Path(sys.argv[sys.argv.index('--segment-manifest') + 1])
        plan = json.loads(path.read_text())
        if plan.get('implementation_revision') != REVISION:
            raise ValueError('Explicit memory implementation binding required')
        for rel, expected in plan['implementation_dependencies'].items():
            if base.file_hash(W / rel) != expected:
                raise ValueError('Implementation dependency changed: ' + rel)
    base.__file__ = str(HERE)  # Child launch/hash checks identify this wrapper.
    base.expanded_worker = expanded
    base.prepare = prepare
    base.elapsed_seconds = clocks
    return base.main()


if __name__ == '__main__':
    raise SystemExit(main())
