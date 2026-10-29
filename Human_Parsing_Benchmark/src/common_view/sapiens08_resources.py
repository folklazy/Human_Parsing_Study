"""Read-only, model-specific concurrent admission; no utilization gate or system changes."""
import json,os,subprocess,time
from pathlib import Path


def peak_from_ledger(path):
    peak=0.;count=0
    if Path(path).exists():
        for line in Path(path).open():
            try:row=json.loads(line)
            except json.JSONDecodeError:continue  # last active append may be incomplete
            r=row.get('resource',{})
            if 'peak_reserved_MiB' in r:
                peak=max(peak,float(r['peak_reserved_MiB']));count+=1
    return peak,count


def admission(total_mib,used_mib,processes,peer_pid,own_pid,peer_peak,own_peak,mapback_mib,
              context_mib=512,growth_mib=1024,global_headroom_mib=1024):
    """Conservative empirical bound, not proof of all-image VRAM feasibility.

    Uses peak plus whole largest original-grid map-back allocation as additional
    margin, although the empirical peak already includes some map-back memory.
    """
    peer_current=float(processes.get(peer_pid,0))
    own_current=float(processes.get(own_pid,0))
    other=max(0.,used_mib-peer_current-own_current)
    peer_budget=max(peer_current,peer_peak+context_mib+mapback_mib) if peer_current else 0.
    own_budget=max(own_current,own_peak+context_mib+mapback_mib+growth_mib)
    required=other+peer_budget+own_budget+global_headroom_mib
    return dict(admitted=required<=total_mib,usable_total_MiB=total_mib,
                observed_used_MiB=used_mib,observed_peer_MiB=peer_current,other_MiB=other,
                protected_peer_budget_MiB=peer_budget,requested_08_budget_MiB=own_budget,
                global_headroom_MiB=global_headroom_mib,estimated_combined_MiB=required,
                remaining_after_budgets_MiB=total_mib-required,
                basis='historical08peak + observed04peak + fullpopulationmapback + contexts + growth + headroom',
                all_image_feasibility_guaranteed=False)


_PEER_CACHE={}

def snapshot(c,workspace,own_peak,own_pid=None):
    w=Path(workspace);own_pid=own_pid or os.getpid();peerroot=w/c['peer04_artifact_root']
    try:peer=json.loads((peerroot/'models/Sapiens2_0.4b/RUN.json').read_text())
    except FileNotFoundError:peer={}
    lines=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.total,memory.used,memory.free','--format=csv,noheader,nounits'],text=True).strip().splitlines()
    chosen=[l for l in lines if l.split(',')[1].strip()==c['gpu_uuid']]
    if len(chosen)!=1:raise RuntimeError('Assigned GPU identity unavailable')
    _,_,physical,used,free=[s.strip() for s in chosen[0].split(',')]
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_gpu_memory','--format=csv,noheader,nounits'],text=True).strip().splitlines()
    processes={}
    for line in apps:
        if not line.strip():continue
        pid,uuid,value=[s.strip() for s in line.split(',')]
        if uuid!=c['gpu_uuid']:continue
        try:processes[int(pid)]=float(value)
        except ValueError:raise RuntimeError('GPU memory accounting unavailable')
    key=str(peerroot)
    cached=_PEER_CACHE.get(key)
    if cached is None or time.monotonic()-cached[0]>=60:
        peak,n=peak_from_ledger(peerroot/'models/Sapiens2_0.4b/EXECUTION.jsonl')
        _PEER_CACHE[key]=(time.monotonic(),peak,n)
    else:_,peak,n=cached
    peak=max(peak,c['admission']['peer04_peak_reserved_MiB_at_prepare'])
    out=admission(min(float(physical),c['admission']['usable_cuda_total_MiB']),float(used),processes,
                  peer.get('pid'),own_pid,peak,own_peak,c['admission']['largest_mapback_MiB'],
                  c['admission']['context_allowance_MiB'],c['admission']['growth_allowance_MiB'],
                  c['admission']['global_headroom_MiB'])
    available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))/1024
    out['RAM_available_MiB']=available
    out['RAM_admitted']=available>=c.get('minimum_available_RAM_MiB',0)
    out['admitted']=out['admitted'] and out['RAM_admitted']
    out.update(utc=time.time(),observed_free_MiB=float(free),peer04_complete=peer.get('complete',0),
               peer04_state=peer.get('status'),peer04_peak_reserved_MiB=peak,peer04_peak_samples=n,
               own_peak_reference_MiB=own_peak,GPU_processes=processes)
    return out


def execution_seconds(start,wait_seconds,now):
    return max(0.,now-start-wait_seconds)
