"""Stream GT-only C4 domains/eligibility; never reads model predictions or scores."""
import json
import os
from pathlib import Path
import sys
import shutil
import numpy as np
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'))
from common_view.core import load_spec,gt_domains,sha_file
from common_view.packets import atomic_json
from cihp_benchmark.data import read_image


def main():
    config=json.loads((P/'configs/cihp_sapiens_04b_pilot.json').read_text())
    spec=load_spec(W/config['protocol']);out=W/config['artifact_root']/'gt_bindings'
    out.mkdir(exist_ok=False)
    pop=json.loads((W/config['native_population']).read_text())
    if len(pop['members'])!=5000 or len({x['id'] for x in pop['members']})!=5000:
        raise ValueError('Population is not exact5000unique')
    total=dict(G_loc=0,G_sem_C4=0,owner_unknown_pixels=0,source_VOID_pixels=0)
    support=np.zeros(6,np.int64);rows=out/'BINDINGS.jsonl'
    with rows.open('x') as ledger:
        for i,r in enumerate(pop['members']):
            if shutil.disk_usage(out).free<config['minimum_free_gib']*2**30:
                raise RuntimeError('Free-space guard')
            iid=r['id'];base=W/'datasets/CIHP/Validation'
            category,cm=read_image(base/'Category_ids'/(iid+'.png'),mask=True)
            human,hm=read_image(base/'Human_ids'/(iid+'.png'),mask=True)
            if cm['file_sha256']!=r['GT_sha256']['Category_ids'] or hm['file_sha256']!=r['GT_sha256']['Human_ids']:
                raise ValueError('Source GT binding changed:'+iid)
            gt,v,vp,b=gt_domains(category,human,spec)
            if list(category.shape[::-1])!=r['wh']:
                raise ValueError('GT geometry binding changed')
            dst=out/(iid+'.npz');tmp=out/(iid+'.npz.tmp')
            with tmp.open('wb') as f:np.savez_compressed(f,projected=gt,valid=v,person_valid=vp)
            os.replace(tmp,dst)
            row=dict(image_id=iid,GT_sha256={k:r['GT_sha256'][k] for k in ['Category_ids','Human_ids']},
                     protocol_sha256=config['protocol_sha256'],derived_sha256=sha_file(dst),**b)
            ledger.write(json.dumps(row,allow_nan=False)+'\n')
            for k in ['G_loc','G_sem_C4','owner_unknown_pixels']:total[k]+=b[k]
            total['source_VOID_pixels']+=int((~v).sum());support+=np.array(b['global_support'])
            if (i+1)%1000==0:print('GT bindings',i+1,flush=True)
        ledger.flush();os.fsync(ledger.fileno())
    summary=dict(status='COMPLETE_GT_ONLY_NO_MODEL_SCORING',count=5000,
                 population_sha256=config['native_population_sha256'],protocol_sha256=config['protocol_sha256'],
                 manifest_sha256=sha_file(rows),manifest=str(rows.relative_to(W)),
                 global_support=support.tolist(),**total)
    atomic_json(out/'SUMMARY.json',summary)
    atomic_json(W/config['record_root']/'GT_BINDING_SUMMARY.json',summary)
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
