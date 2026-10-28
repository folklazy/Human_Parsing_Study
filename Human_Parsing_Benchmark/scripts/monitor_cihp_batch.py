"""Read-only job health monitor; finalize/publish first-party summaries at terminal state."""
from pathlib import Path
from datetime import datetime,timezone
import os,json,time,subprocess,sys,hashlib,argparse
P=Path(__file__).resolve().parents[1];W=P.parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def publish(out,unit,files):
 pub=W/'Human_Parsing_Study_Public'
 if subprocess.check_output(['git','-C',str(pub),'status','--porcelain'],text=True).strip():return {'status':'PENDING_SYNC','reason':'Public working tree has independent changes; not overwritten'}
 base=subprocess.check_output(['git','-C',str(pub),'rev-parse','HEAD'],text=True).strip();entries=[]
 for rel in files:
  src=P/rel;dst=pub/'Human_Parsing_Benchmark'/rel
  if src.is_symlink() or src.stat().st_size>5*1024**2 or src.suffix not in ['.md','.json','.csv']:raise ValueError('Unexpected public summary asset '+rel)
  dst.parent.mkdir(parents=True,exist_ok=True);before=sha(dst) if dst.exists() else None;dst.write_bytes(src.read_bytes());entries.append({'source_workspace_relative':'Human_Parsing_Benchmark/'+rel,'public_path':'Human_Parsing_Benchmark/'+rel,'sha256':sha(dst),'before_sha256':before,'bytes':dst.stat().st_size})
 mp='publication/CIHP_NATIVE_COMPLETION_'+unit.removeprefix('cihp-native-six-')+'.json';(pub/mp).write_text(json.dumps({'work_unit':unit,'base_commit':base,'scope':'Terminal first-six nativeCIHP metrics/report/provenance only; no masks/images/weights','files':entries,'launch_source_unchanged':True},indent=2)+'\n');paths=[x['public_path'] for x in entries]+[mp]
 idxp=pub/'publication/PUBLIC_FILE_MANIFEST.json';idx=json.loads(idxp.read_text());items={x['path']:x for x in idx['files']}
 for path in paths:items[path]={'path':path,'bytes':(pub/path).stat().st_size,'sha256':sha(pub/path)}
 idx['files']=[items[k] for k in sorted(items)];idx['updated_utc']=datetime.now(timezone.utc).isoformat();idxp.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n');fl=pub/'publication/PUBLISH_FILES.txt';fl.write_text('\n'.join(sorted(set(fl.read_text().splitlines())|set(paths)))+'\n');paths+=['publication/PUBLIC_FILE_MANIFEST.json','publication/PUBLISH_FILES.txt']
 subprocess.run(['git','-C',str(pub),'add','--',*paths],check=True);staged=subprocess.check_output(['git','-C',str(pub),'diff','--cached','--name-only'],text=True).splitlines()
 if set(staged)!=set(paths):return {'status':'PENDING_SYNC','reason':'Unexpected staged scope, preserved'}
 subprocess.run(['git','-C',str(pub),'commit','-m','results: record terminal native CIHP first-six batch'],check=True)
 if subprocess.check_output(['git','-C',str(pub),'remote','get-url','origin'],text=True).strip()!='https://github.com/folklazy/Human_Parsing_Study.git':return {'status':'PENDING_SYNC','reason':'Unexpected remote; local commit retained'}
 env=os.environ.copy();env['GIT_TERMINAL_PROMPT']='0'
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   node=Path(os.readlink(proc/'exe'));basepath=node.parent
   if node.name=='node' and '/.vscode-server/cli/servers/' in str(node) and (basepath/'extensions/git/dist/askpass.sh').is_file():env.update(GIT_ASKPASS=str(basepath/'extensions/git/dist/askpass.sh'),VSCODE_GIT_ASKPASS_NODE=str(node),VSCODE_GIT_ASKPASS_MAIN=str(basepath/'extensions/git/dist/askpass-main.js'));break
  except OSError:pass
 sent=subprocess.run(['git','-C',str(pub),'push','origin','main'],capture_output=True,text=True,env=env,timeout=45);commit=subprocess.check_output(['git','-C',str(pub),'rev-parse','HEAD'],text=True).strip();remote=subprocess.run(['git','-C',str(pub),'ls-remote','origin','refs/heads/main'],capture_output=True,text=True,timeout=30);rh=remote.stdout.split()[0] if remote.returncode==0 and remote.stdout else None
 return {'status':'SYNCED' if sent.returncode==0 and rh==commit else 'PENDING_SYNC','commit':commit,'remote_commit':rh,'push_exit':sent.returncode,'push_diagnostic':sent.stderr[-1200:]}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--run-root',required=True);parser.add_argument('--expected-status-sha256',required=True);parser.add_argument('--expected-work-log-sha256',required=True);parser.add_argument('--health-log',default='GPU_HEALTH.jsonl');args=parser.parse_args();out=Path(args.run_root).resolve();unit=out.name
 if Path(args.health_log).name!=args.health_log:raise ValueError('Health-log basename required')
 with (out/args.health_log).open('x') as monitor:
  while True:
   launch=json.loads((out/'LAUNCH.json').read_text());now=datetime.now(timezone.utc).isoformat();gpu=subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True);pids=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],capture_output=True,text=True)
   owned={str(v.get('PID')) for v in launch['models'].values()};actual=set(pids.stdout.split());monitor.write(json.dumps({'utc':now,'GPU_query':gpu.stdout.strip(),'GPU_compute_PIDs':sorted(actual),'external_PIDs':sorted(actual-owned),'quality_or_rank_analysis':False})+'\n');monitor.flush()
   if launch['status']!='RUNNING':break
   controller=Path('/proc')/str(launch['controller_PID']);live_child=any((Path('/proc')/pid).exists() for pid in owned if pid.isdigit())
   if not controller.exists() and not live_child:
    launch.update(status='INTERRUPTED_CONTROLLER_REQUIRES_RECONCILIATION',monitor_detected_utc=now);(out/'MONITOR_INTERRUPTION.json').write_text(json.dumps(launch,indent=2)+'\n');return
   time.sleep(30)
 worklog_unchanged=sha(P/'WORK_LOG.md')==args.expected_work_log_sha256
 envpython=W/'.venvs/mhpv2-stage0/bin/python';code=subprocess.run([str(envpython),str(P/'scripts/report_cihp_batch.py'),'--run-root',str(out)],capture_output=True,text=True);(out/'FINALIZER.log').write_text(code.stdout+'\n'+code.stderr)
 if code.returncode:raise RuntimeError('Finalization failed, evidence retained: '+code.stderr[-1000:])
 completion=json.loads((P/'runs'/unit/'COMPLETION.json').read_text());status=P/'STATUS.md';files=['runs/'+unit+'/COMPLETION.json','reports/'+unit+'/REPORT_TH.md']+[str(f.relative_to(P)) for f in sorted((P/'metrics'/unit).glob('*.csv'))]
 if worklog_unchanged:files.append('WORK_LOG.md')
 if sha(status)==args.expected_status_sha256:
  (out/'STATUS_BEFORE_TERMINAL.md').write_bytes(status.read_bytes())
  status.write_text(f'''# Human Parsing Benchmark — current status

Updated: {completion["end_utc"]} UTC

**{completion["status"]}** — official native CIHP validation 5,000 images per system, {completion["complete_models"]}/6 systems complete. Run `{unit}`. [Result report](reports/{unit}/REPORT_TH.md) / [completion](runs/{unit}/COMPLETION.json) / [PLAN](PLAN.md).

STRICT_COMPLETE: main scores remain null for incomplete systems; their failure/pending rows are retained. Launch commit `{completion["launch_commit"]}` identifies execution code, not the later reporting/publication commit. Original controller and model attempts are preserved; no automatic failed-image retries or changed inference settings.

Fixed 16-image original-grid comparisons are external under the run artifact root, `QUALITATIVE/index.html`. See completion for hashes and location. Cached YOLO means end-to-end FPS was not measured; parser timing/VRAM scopes remain explicit.

Next: review terminal results/failures and native CIHP-to-Sapiens semantic matrix before any Sapiens execution. No Ninja, color, training or CCTV processing was started. Old YOLO/CPI results and source GT remain unchanged.
''');files.append('STATUS.md')
 receipt=publish(out,unit,files);(out/'COMPLETION_PUBLICATION.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
