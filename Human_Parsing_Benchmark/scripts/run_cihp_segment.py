"""Execute a disjoint continuation segment from the byte-bound frozen worker.

Only orchestration changes are applied. The original file/config are never edited.
The expanded source and exact diff are archived before execution and hash-bound.
"""
from pathlib import Path
import argparse, hashlib, json, sys
P=Path(__file__).resolve().parents[1];W=P.parent

def validate_partition(population,pending,reused):
    if len(set(pending))!=len(pending) or len(set(reused))!=len(reused):raise ValueError('Duplicate continuation identity')
    if set(pending)&set(reused):raise ValueError('Reinference of reused image forbidden')
    if set(pending)|set(reused)!=set(population):raise ValueError('Missing/extra continuation identity')
    if [i for i in population if i in set(pending)]!=pending:raise ValueError('Source input order must be preserved')

def derive(source):
    replacements=[
      ("parser.add_argument('--output',required=True);a=parser.parse_args();", "parser.add_argument('--output',required=True);parser.add_argument('--segment-manifest',required=True);a=parser.parse_args();segment=json.loads(Path(a.segment_manifest).read_text());assert a.phase=='validation' and a.model==segment['model_id'];assert file_hash(a.segment_manifest)==segment_bind;"),
      ("'expected':3 if a.phase=='readiness' else 5000", "'expected':3 if a.phase=='readiness' else len(segment['pending_ids'])"),
      ("'not_attempted':3 if a.phase=='readiness' else 5000", "'not_attempted':3 if a.phase=='readiness' else len(segment['pending_ids'])"),
      ("atomic(out/'RUN.json',result)\n try:", "result.update(parent_run_id=segment['parent_run_id'],continuation_id=segment['continuation_id'],segment_manifest_sha256=segment_bind,scope='CONTINUATION_SEGMENT_NOT_FULL_POPULATION');atomic(out/'RUN.json',result)\n try:"),
      ("rows=pop['members'];detector=", "rows=[r for r in pop['members'] if r['id'] in set(segment['pending_ids'])];assert [r['id'] for r in rows]==segment['pending_ids'];detector="),
      ("retained_bytes=sum(f.stat().st_size for f in out.rglob('*') if f.is_file())", "retained_bytes=segment['prior_retained_bytes']+sum(f.stat().st_size for f in out.rglob('*') if f.is_file())"),
      ("time.monotonic()-execution_start>config['max_system_hours']*3600", "segment['prior_execution_seconds']+time.monotonic()-execution_start>config['max_system_hours']*3600"),
      ("'attempt_id':iid+':1'", "'attempt_id':segment['continuation_id']+':'+iid+':1'"),
      ("metadata.update(model_id=a.model", "metadata.update(parent_run_id=segment['parent_run_id'],continuation_id=segment['continuation_id'],segment_manifest_sha256=segment_bind,model_id=a.model"),
    ]
    for old,new in replacements:
        if source.count(old)!=1:raise ValueError('Frozen worker patch anchor is not unique: '+old)
        source=source.replace(old,new)
    return source

def main():
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--segment-manifest',required=True);known,_=parser.parse_known_args();path=Path(known.segment_manifest);s=json.loads(path.read_text());digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if s['wrapper_sha256']!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():raise ValueError('Segment wrapper changed')
    original=P/'scripts/run_cihp_system.py'
    if hashlib.sha256(original.read_bytes()).hexdigest()!=s['frozen_worker_sha256']:raise ValueError('Original worker drift')
    expanded=derive(original.read_text())
    if hashlib.sha256(expanded.encode()).hexdigest()!=s['expanded_worker_sha256']:raise ValueError('Expanded worker drift')
    config=json.loads((W/s['config']).read_text());assert hashlib.sha256((W/s['config']).read_bytes()).hexdigest()==s['config_sha256']
    population=[r['id'] for r in json.loads((W/config['dataset']['population']).read_text())['members']]
    validate_partition(population,s['pending_ids'],s['reused_ids'])
    if not s['pending_ids']:raise ValueError('Completed model has no continuation inference work')
    namespace={'__name__':'__main__','__file__':str(Path(__file__).resolve()),'segment_bind':digest}
    exec(compile(expanded,str(Path(__file__).resolve()),'exec'),namespace)

if __name__=='__main__':main()
