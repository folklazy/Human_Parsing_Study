"""Sequential bounded TRAIN native feasibility. No benchmark/scoring/model selection."""
from pathlib import Path
import json,subprocess,os
S=Path(__file__).resolve().parents[1];W=S.parent
R=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run'];B=R/'native_smoke';results=[]
for env,name,args in [('fashn-stage0','run_fashn.py',[]),('parser-legacy-cu113','run_cpi.py',[]),('parser-legacy-cu113','run_mask_transformer.py',['--family','M2FP']),('parser-legacy-cu113','run_mask_transformer.py',['--family','D2FP']),('parser-legacy-cu113','run_schp.py',[]),('parser-legacy-cu113','run_qanet.py',[]),('parser-legacy-cu113','run_rpr.py',[])]:
 tag=name.removesuffix('.py')+('_'+args[-1] if args else '')
 command=[str(W/'.venvs'/env/'bin/python'),str(S/'scripts/run_handoff_smoke_worker.py'),name,*args]
 with (B/'logs'/(tag+'_attempt2.log')).open('x') as f:
  try:r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=900);status=r.returncode
  except subprocess.TimeoutExpired:status='TIMEOUT'
 results.append(dict(command=command,exit_code=status,log=str((B/'logs'/(tag+'_attempt2.log')).relative_to(S))))
 (R/'NATIVE_SMOKE_PROCESSES_ATTEMPT2.json').write_text(json.dumps(results,indent=2));print(tag,status,flush=True)
