"""Merge disjoint native inference evidence, retaining interrupted and failed images."""
from pathlib import Path
from datetime import datetime,timezone
import copy,json,sys

S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S))
from src.application_v2.policy import load_config
from src.application_v2.artifacts import file_hash


def main():
    R=S/json.loads((S/'provenance/FIRST_COHORT_BENCHMARK_ACTIVE.json').read_text())['run'];C=R/'continuation_20261019'
    cfg=load_config(S/'configs/application_v2_first_cohort_v11.yaml',benchmark=True);manifest=json.loads((C/'CONTINUATION_MANIFEST.json').read_text())
    original=R/'execution/CPI_ConvNeXtB_CIHP';continuation=C/'CPI_ConvNeXtB_CIHP'
    if file_hash(original/'FRAMES.jsonl')!=manifest['original_ledger_sha256'] or file_hash(original/'RUN.json')!=manifest['original_RUN_sha256']:raise ValueError('Original evidence changed')
    old=json.loads((original/'RUN.json').read_text());new=json.loads((continuation/'RUN.json').read_text())
    if new['status'] not in {'COMPLETE','INCOMPLETE'}:raise ValueError('Continuation not terminal')
    for key in ['model_id','checkpoint_sha256','native_config_sha256','source_commit','precision','native_score_threshold','config_sha256','torch','cuda_runtime','GPU']:
        if old[key]!=new[key]:raise ValueError('Native profile changed: '+key)
    prefix=[json.loads(line) for line in (original/'FRAMES.jsonl').read_text().splitlines()]
    suffix=[json.loads(line) for line in (continuation/'FRAMES.jsonl').read_text().splitlines()]
    if [r['image_id'] for r in suffix]!=manifest['pending_image_ids']:raise ValueError('Pending population mismatch')
    orphan=manifest['unresolved_interrupted_ids']
    if len(orphan)!=1:raise ValueError('Expected one observed interrupted native output')
    interrupted=dict(image_id=orphan[0],status='INVALID',failure_stage='OUTPUT_CONTRACT',failure_type='UNRESOLVED_INTERRUPTION',
        error='Native PNG outputs exist but NPZ is incomplete (zipfile.BadZipFile). Process ended without a final ledger row. Original files preserved; no inference retry or bbox reconstruction.',
        retries=0,interrupted_artifact=str((original/(orphan[0]+'.npz')).relative_to(S)),interrupted_artifact_sha256=manifest['unresolved_artifact_sha256'])
    rows=prefix+[interrupted]+suffix
    expected=[json.loads(line)['image_id'] for line in (S/cfg['validation_launch']['inputs']['path']).read_text().splitlines()]
    if [r['image_id'] for r in rows]!=expected or len({r['image_id'] for r in rows})!=5000:raise ValueError('Merged reference population mismatch')
    destination=C/'CPI_ConvNeXtB_CIHP_COMBINED';destination.mkdir(exist_ok=False)
    with (destination/'FRAMES.jsonl').open('x') as stream:
        for row in rows:stream.write(json.dumps(row,allow_nan=False)+'\n')
    state=copy.deepcopy(old);state.update(status='INCOMPLETE',frames=5000,failed_frames=sum(r['status']=='FAILED' for r in rows),invalid_frames=sum(r['status']=='INVALID' for r in rows),
        end_utc=datetime.now(timezone.utc).isoformat(),native_model_initializations=2,image_retry_count=0,
        constituent_runs=[dict(manifest=str((d/'RUN.json').relative_to(S)),manifest_sha256=file_hash(d/'RUN.json'),ledger=str((d/'FRAMES.jsonl').relative_to(S)),ledger_sha256=file_hash(d/'FRAMES.jsonl')) for d in [original,continuation]],
        interrupted_native_output_ids=orphan,original_raw_outputs_unchanged=True)
    (destination/'RUN.json').write_text(json.dumps(state,indent=2)+'\n')
    components={}
    for model,d in [('CPI_R50_CIHP',R/'execution/CPI_R50_CIHP'),('CPI_ConvNeXtB_CIHP',destination)]:
        components[model]=dict(manifest=str((d/'RUN.json').relative_to(S)),manifest_sha256=file_hash(d/'RUN.json'),ledger=str((d/'FRAMES.jsonl').relative_to(S)),ledger_sha256=file_hash(d/'FRAMES.jsonl'))
    (R/'NATIVE_COMPONENTS_FOR_RESTORATION.json').write_text(json.dumps(components,indent=2)+'\n')
    print(json.dumps(dict(merged_frames=len(rows),original_frames=len(prefix),interrupted_invalid=1,continued_frames=len(suffix),CPI_image_retries=0)))


if __name__=='__main__':main()
