"""Validate committed artifacts and rebuild sufficient statistics without inference."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, sys
import numpy as np
P=Path(__file__).resolve().parents[1]; W=P.parent
sys.path.insert(0,str(P/'src'))
from cihp_benchmark.data import read_sample, file_hash
from cihp_benchmark.evaluation import score_frame, semantic_report

def write(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n');tmp.replace(path)

def validate_folder(folder, config, population, detector, output, config_digest, allow_noncomplete=False):
    """All source writes are forbidden; only the fresh reconciliation output is written."""
    mid=folder.name; spec=config['models'][mid]
    rows=[json.loads(l) for l in (folder/'FRAMES.jsonl').read_text().splitlines()] if (folder/'FRAMES.jsonl').exists() else []
    ids=[r['image_id'] for r in rows]
    if len(ids)!=len(set(ids)) or not set(ids)<=set(population):raise ValueError('Duplicate/out-of-population ledger '+mid)
    dirs={p.name:p for p in (folder/'packets').iterdir()} if (folder/'packets').exists() else {}
    orphan=sorted(set(dirs)-set(ids))
    inventory={'model_id':mid,'ledger_count':len(rows),'packet_directories':len(dirs),'orphan_ids':orphan,'non_complete_ledger':[r for r in rows if r['status']!='COMPLETE'],'source_folder':str(folder.relative_to(W))}
    output.mkdir(parents=True,exist_ok=False);write(output/'INVENTORY.json',inventory)
    if orphan or (inventory['non_complete_ledger'] and not allow_noncomplete):raise ValueError('Unreconciled orphan/failure: preserve and stop affected scope '+mid)
    rows=[r for r in rows if r['status']=='COMPLETE'];ids=[r['image_id'] for r in rows]
    hist=np.zeros((20,20),np.int64);nativehist=hist.copy();person={str(t):dict(G_loc=0,G_sem=0,TP=0,FP=0,FN=0,Q_numerator=0.) for t in [.5,.75]}
    with (output/'VERIFIED_FRAMES.jsonl').open('x') as audit:
      for index,row in enumerate(rows):
        iid=row['image_id']; sample=population[iid];packet=dirs[iid];meta=json.loads((packet/'packet.json').read_text());digest=file_hash(packet/'prediction.npz')
        assert digest==row['packet_sha256']==meta['packet_sha256'],('NPZ hash',mid,iid)
        for k,v in dict(model_id=mid,image_id=iid,checkpoint_sha256=spec['checkpoint_sha256'],source_commit=spec['source_commit'],original_wh=sample['wh'],input_sha256=sample['RGB_sha256'],label_space='CIHP_NATIVE_20',precision='FP32').items():assert meta[k]==v,(k,mid,iid)
        assert meta['config_sha256']==config_digest,('Config binding',mid,iid)
        expected_fp=hashlib.sha256(json.dumps({'model':spec,'input':meta['input_sha256'],'detector':detector[iid]['artifact_sha256'],'adapter_sha256':config['source_bindings']['Human_Parsing_Benchmark/src/cihp_benchmark/adapters.py'],'precision':'FP32','ownership':config['ROI_ownership'],'association':config['association']},sort_keys=True).encode()).hexdigest()
        assert meta['inference_fingerprint']==expected_fp and meta['detector_artifact_sha256']==detector[iid]['artifact_sha256'],('Inference binding',mid,iid)
        with np.load(packet/'prediction.npz',allow_pickle=False) as z:arrays={k:z[k] for k in z.files}
        truth,gtmeta=read_sample(W/'datasets/CIHP','Validation',iid)
        for k in ['Category_ids','Human_ids','Instance_ids']:assert gtmeta[k]['file_sha256']==sample['GT_sha256'][k],('GT drift',iid,k)
        expected_eval=hashlib.sha256(json.dumps({'GT':sample['GT_sha256'],'scorer_sha256':config['source_bindings']['Human_Parsing_Benchmark/src/cihp_benchmark/evaluation.py'],'metrics':config['metrics']},sort_keys=True).encode()).hexdigest()
        assert meta['evaluation_fingerprint']==expected_eval,('Evaluation binding',iid)
        score_hashes={}
        for t in [.5,.75]:
          sc=score_frame(truth['Category_ids'],truth['Human_ids'],arrays['person_semantic_masks'],arrays['person_extents'],arrays['person_scores'],t)
          f=packet/('score_'+str(t)+'.json');old=json.loads(f.read_text());assert sc==old,('Score mismatch',mid,iid,t)
          score_hashes[f.name]=file_hash(f)
          for k in person[str(t)]:person[str(t)][k]+=sc[k]
          if t==.5:hist+=np.asarray(sc['histogram'],np.int64)
        if spec['native_reference']:
          sc=score_frame(truth['Category_ids'],truth['Human_ids'],arrays['native_person_semantic_masks'],arrays['native_person_extents'],arrays['native_person_scores'],.5)
          f=packet/'native_reference_score.json';assert sc==json.loads(f.read_text()),('Reference score mismatch',mid,iid);nativehist+=np.asarray(sc['histogram'],np.int64);score_hashes[f.name]=file_hash(f)
        audit.write(json.dumps({'frame':row,'metadata_sha256':file_hash(packet/'packet.json'),'score_hashes':score_hashes,'NPZ_all_members_decoded_CRC_checked':True,'independent_saved_mask_rescore_matches':True})+'\n');audit.flush()
        if index%500==0:print(mid,index+1,'/',len(rows),flush=True)
    state={'model_id':mid,'verified_count':len(rows),'verified_ids':ids,'pending_ids':[i for i in population if i not in set(ids)],'histogram':hist.tolist(),'native_histogram':nativehist.tolist(),'person_sufficient_statistics':person,'source_ledger_sha256':file_hash(folder/'FRAMES.jsonl') if rows else None,'verified_ledger_sha256':file_hash(output/'VERIFIED_FRAMES.jsonl'),'source_root':str(folder.relative_to(W)),'completed_utc':datetime.now(timezone.utc).isoformat(),'new_inference':False}
    write(output/'RECONCILED.json',state);return state

def main():
    a=argparse.ArgumentParser();a.add_argument('--parent',required=True);a.add_argument('--output',required=True);args=a.parse_args();parent=Path(args.parent).resolve();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
    config=json.loads((parent/'FROZEN_CONFIG.json').read_text())
    assert file_hash(parent/'FROZEN_CONFIG.json')==json.loads((parent/'LAUNCH.json').read_text())['config_sha256']
    assert file_hash(parent/'FROZEN_POPULATION.json')==config['dataset']['population_sha256']
    for path,digest in config['source_bindings'].items():assert file_hash(W/path)==digest,('Frozen source changed',path)
    pop={s['id']:s for s in json.loads((parent/'FROZEN_POPULATION.json').read_text())['members']};det={d['image_id']:d for d in map(json.loads,(W/config['frozen_YOLO']['validation_ledger']).open())}
    models={}
    for mid in config['execution_models']:models[mid]=validate_folder(parent/'validation'/mid,config,pop,det,out/mid,file_hash(parent/'FROZEN_CONFIG.json'))
    write(out/'RECONCILIATION.json',{'parent_run':parent.name,'config_sha256':file_hash(parent/'FROZEN_CONFIG.json'),'models':{m:{k:v for k,v in s.items() if k not in ['histogram','native_histogram','person_sufficient_statistics','verified_ids','pending_ids']} for m,s in models.items()},'status':'VERIFIED','cause':'UNKNOWN; no model/OOM traceback; original controller/worker disappeared; monitor detected interruption','new_inference':False})
    print('RECONCILIATION VERIFIED',flush=True)
if __name__=='__main__':main()
