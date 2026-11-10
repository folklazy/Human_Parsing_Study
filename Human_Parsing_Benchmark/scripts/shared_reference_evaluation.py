"""CPU-only shared C3 person-part + Face-local scoring of accepted packets.

Preparation freezes sources/protocol/GT. SQLite transactions make an entire
image's new model results atomic. Resume never replaces committed observations.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse
import csv
import fcntl
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
import traceback

import numpy as np
from PIL import Image

H=Path(__file__).resolve().parents[1]; W=H.parent; C=W/'CCTV_Human_Parsing_Benchmark'
sys.path.insert(0,str(H/'src'))
from common_view.core import gt_domains
from common_view.reference_parts import score_frame,summarize
from common_view.packets import atomic_json


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(W))
def utc():return datetime.now(timezone.utc).isoformat()


def load_gt(dataset,iid,source,spec):
    frame=source['frames'][iid]
    if dataset=='CIHP':
        base=W/'datasets/CIHP/Validation'
        cp,hp=base/'Category_ids'/(iid+'.png'),base/'Human_ids'/(iid+'.png')
        for name,path in [('Category_ids',cp),('Human_ids',hp)]:
            if sha(path)!=frame['GT_sha256'][name]:raise ValueError('GT PNG binding changed')
        category,human=np.array(Image.open(cp)),np.array(Image.open(hp))
        projected,global_valid,valid,binding=gt_domains(category,human,spec)
        ids=[r['id'] for r in binding['persons']]
        extents=[(human==pid)&global_valid for pid in ids]
        parts={(pid,t):(human==pid)&(projected==t) for pid in ids for t in range(1,5)
               if np.any((human==pid)&(projected==t)&valid)}
    else:
        path=W/frame['GT_packet']
        if sha(path)!=frame['GT_packet_sha256'] or sha(W/frame['annotation'])!=frame['annotation_sha256']:
            raise ValueError('Accepted CCTV GT binding changed')
        with np.load(path,allow_pickle=False) as z:
            ids=[int(p) for p in z['person_ids']];extents=[m.copy() for m in z['person_masks']]
            valid=~(z['person_overlap']|z['semantic_overlap'])
            parts={(int(p),int(t)):m.copy() for p,t,m in zip(z['part_person_ids'],z['part_target_ids'],z['part_masks'])}
    return dict(ids=ids,extents=extents,parts=parts,valid=valid,shape=valid.shape)


def prepare(output):
    output.mkdir(parents=True,exist_ok=False)
    protocol=read(H/'protocol/SHARED_C3_FACE_LOCAL_V1.json')
    spec=read(H/'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json')
    terminal=read(H/'runs/cihp-sequential-finish-20261106T105503Z/TERMINAL_VERIFICATION.json')
    manifest_path=H/'outputs/cihp-controlled-roi-20261102T120403Z/INPUTS.json';manifest=read(manifest_path)
    ci=dict(expected=manifest['expected_ids'],frames={f['member']['id']:dict(GT_sha256=f['member']['GT_sha256'],RGB_sha256=f['member']['RGB_sha256'],detector_sha256=f['detector']['artifact_sha256']) for f in manifest['frames']},models={})
    if len(ci['expected'])!=5000 or len(set(ci['expected']))!=5000:raise ValueError('Expected exact CIHP 5000')
    for row in terminal['models']:
        mid=row['model_id'];root=(W/row['metrics_path']).parent;completion=read(root/'COMPLETION.json')
        if not completion['strict_complete'] or sha(root/'METRICS.json')!=row['metrics_sha256']:
            raise ValueError('Accepted CIHP completion differs')
        assembly=read(root/'ASSEMBLED_INDEX.json') if (root/'ASSEMBLED_INDEX.json').exists() else {}
        parent=assembly.get('parent_frames',{})
        fresh={p.name for p in (root/'packets').iterdir() if p.is_dir()}
        if set(parent)&fresh or set(parent)|fresh!=set(ci['expected']):raise ValueError('CIHP membership differs')
        config_path=root.parent/'CONFIG.json';cfg=read(config_path)
        ci['models'][mid]=dict(packets={iid:(parent[iid]['packet'] if iid in parent else rel(root/'packets'/iid)) for iid in ci['expected']},
            checkpoint_sha256=cfg['models'][mid]['checkpoint_sha256'],canonical_metrics=rel(root/'METRICS.json'),
            canonical_metrics_sha256=row['metrics_sha256'],implementation=assembly.get('implementation_history',assembly.get('effective_implementation','original accepted source')))
    accept_path=C/'outputs/gt-user-acceptance-20261107T201524Z/ACCEPTANCE.json';accept=read(accept_path)
    gtroot=C/'outputs/master-gt-repair-20261107T191020Z';gtbind=read(gtroot/'PRIVATE_BINDINGS.json')
    old_config=read(C/'outputs/cctv-partial-20261031T1800Z/CONFIG.json')
    members={m['id']:m for m in old_config['members']}
    ct=dict(expected=[f['image_id'] for f in gtbind['frames']],frames={},models={})
    accepted={f['image_id']:f for f in accept['files']}
    for f in gtbind['frames']:
        iid=f['image_id']
        if f['annotation_sha256']!=accepted[iid]['sha256'] or sha(W/f['annotation'])!=accepted[iid]['sha256']:
            raise ValueError('CCTV annotation no longer equals user acceptance')
        ct['frames'][iid]=dict(GT_packet=f['packet'],GT_packet_sha256=f['packet_sha256'],annotation=f['annotation'],
            annotation_sha256=f['annotation_sha256'],RGB_sha256=members[iid]['RGB_sha256'],
            detector_sha256=read(C/'outputs/cctv-partial-20261031T1800Z/YOLO26X/packets'/iid/'COMMIT.json')['artifact_sha256'])
    if len(ct['expected'])!=90 or len(set(ct['expected']))!=90:raise ValueError('Expected exact CCTV 90')
    base=read(C/'reports/CONTROLLED_ROI_DIAGNOSTIC_INDEX.json')
    for mid in ci['models']:
        m=base['models'][mid];root=W/m['source_packet_root']
        if {p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith('.')}!=set(ct['expected']):
            raise ValueError('CCTV prediction membership differs')
        ct['models'][mid]=dict(packets={iid:rel(root/iid) for iid in ct['expected']},
            checkpoint_sha256=old_config['models'][mid]['checkpoint_sha256'],
            source_config_sha256=m['source_run_config_sha256'],canonical_reference=m['accepted_metrics_path'])
    datasets={'CCTV':ct,'CIHP':ci}
    GT_summary={}
    for dataset,s in datasets.items():
        count=Counter();support=Counter();raw=Counter();loc=0;void=0
        for iid in s['expected']:
            gt=load_gt(dataset,iid,s,spec);loc+=len(gt['ids']);void+=int((~gt['valid']).sum())
            for (_,t),mask in gt['parts'].items():
                raw[str(t)]+=1;n=int((mask & gt['valid']).sum())
                if n:count[str(t)]+=1;support[str(t)]+=n
        GT_summary[dataset]=dict(images=len(s['expected']),GT_persons=loc,raw_positive_parts=dict(raw),
            eligible_positive_parts=dict(count),GT_support=dict(support),semantic_VOID_or_unknown_owner_pixels=void)
    atomic_json(output/'SOURCES.json',datasets)
    cfg=dict(run_id=output.name,created_utc=utc(),status='FROZEN_BEFORE_NEW_SCORES',
        protocol=rel(H/'protocol/SHARED_C3_FACE_LOCAL_V1.json'),protocol_sha256=sha(H/'protocol/SHARED_C3_FACE_LOCAL_V1.json'),
        mapping=rel(H/'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json'),mapping_sha256=sha(H/'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json'),
        sources_sha256=sha(output/'SOURCES.json'),source_hashes={rel(p):sha(p) for p in [Path(__file__),H/'src/common_view/reference_parts.py',H/'src/common_view/core.py']},
        tests_sha256=sha(H/'tests/test_reference_parts.py'),CPU_acceptance_cases=13,GT_summary=GT_summary,
        model_order=list(ci['models']),user_acceptance_sha256=sha(accept_path),minimum_free_GiB=50,
        precision_and_native_inference='Unchanged saved observations; zero inference calls',new_model_calls=0)
    atomic_json(output/'CONFIG.json',cfg)
    atomic_json(output/'STATUS.json',dict(status='PREPARED',updated_utc=utc(),completed_image_model_records=0,expected_image_model_records=9*5090))
    print(json.dumps(dict(run=output.name,GT_summary=GT_summary),ensure_ascii=False),flush=True)
    return cfg


def load_prediction(path,mid,iid,model,frame,config_cache):
    p=W/path;meta=read(p/'packet.json');commit=read(p/'COMMIT.json')
    for k,v in dict(model_id=mid,image_id=iid,route='CONTROLLED_YOLO_PERSON_ROI',
                    checkpoint_sha256=model['checkpoint_sha256'],input_sha256=frame['RGB_sha256'],
                    detector_sha256=frame['detector_sha256'],GT_used_in_prediction=False,
                    label_space='SAPIENS2_DOME29_PRED' if mid.startswith('Sapiens2_') else 'CIHP_GT_AND_NATIVE_PRED').items():
        if meta.get(k)!=v:raise ValueError('Prediction binding differs: '+k)
    cp=p.parents[2]/'CONFIG.json'
    if str(cp) not in config_cache:config_cache[str(cp)]=sha(cp)
    if meta['config_sha256']!=config_cache[str(cp)]:raise ValueError('Source segment config hash differs')
    for name in ['packet.json','prediction.npz']:
        if sha(p/name)!=commit['members'][name]:raise ValueError('Atomic source packet hash differs')
    if meta['packet_sha256']!=commit['members']['prediction.npz']:raise ValueError('NPZ binding differs')
    with np.load(p/'prediction.npz',allow_pickle=False) as z:
        a={k:z[k] for k in ['person_semantic_masks','person_extents','person_scores']}
    return a,meta


def report(output,config,source,connection):
    final={};table=[];counts=[]
    for dataset,s in source.items():
        final[dataset]={}
        for mid in config['model_order']:
            frames=[json.loads(r[0]) for r in connection.execute('SELECT result FROM results WHERE dataset=? AND model=? ORDER BY image_id',(dataset,mid))]
            m=summarize(frames,s['expected']);m['failed']=connection.execute('SELECT count(*) FROM errors WHERE dataset=? AND model=?',(dataset,mid)).fetchone()[0]
            if m['failed']:m.update(strict_complete=False,primary_mIoU3_part_mean=None,Face_local_IoU=None)
            final[dataset][mid]=m
            table.append(dict(dataset=dataset,model_id=mid,completed=m['completed'],expected=m['expected'],strict_complete=m['strict_complete'],
                Hair=m['targets']['Hair']['mean_part_IoU'],Upper=m['targets']['Upper']['mean_part_IoU'],Lower=m['targets']['Lower']['mean_part_IoU'],
                mIoU3_part_mean=m['primary_mIoU3_part_mean'],Face_local_IoU=m['Face_local_IoU']))
            for name,v in m['targets'].items():counts.append(dict(dataset=dataset,model_id=mid,target=name,**v))
    atomic_json(output/'RESULTS.json',dict(status='COMPLETE' if all(v['strict_complete'] for ds in final.values() for v in ds.values()) else 'INCOMPLETE',
        created_utc=utc(),protocol_sha256=config['protocol_sha256'],CONFIG_sha256=sha(output/'CONFIG.json'),models=final,GT_summary=config['GT_summary'],model_calls=0))
    for filename,rows in [('SUMMARY.csv',table),('TARGET_COUNTS.csv',counts)]:
        with (output/filename).open('w',newline='') as f:
            wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
    return final


def run(output,resume=False,limit=None):
    lock=(output/'SCORING.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cfg=read(output/'CONFIG.json')
    for name,h in cfg['source_hashes'].items():
        if sha(W/name)!=h:raise ValueError('Frozen scoring source changed')
    for field,key in [('protocol','protocol_sha256'),('mapping','mapping_sha256')]:
        if sha(W/cfg[field])!=cfg[key]:raise ValueError('Frozen specification changed')
    if sha(output/'SOURCES.json')!=cfg['sources_sha256']:raise ValueError('Source manifest changed')
    db=output/'RESULTS.sqlite3'
    if db.exists() and not resume:raise FileExistsError('Explicit resume required for an attempted CPU run')
    con=sqlite3.connect(db);con.execute('PRAGMA journal_mode=WAL');con.execute('PRAGMA synchronous=FULL')
    con.execute('CREATE TABLE IF NOT EXISTS results(dataset TEXT,model TEXT,image_id TEXT,result TEXT,PRIMARY KEY(dataset,model,image_id))')
    con.execute('CREATE TABLE IF NOT EXISTS errors(dataset TEXT,model TEXT,image_id TEXT,error TEXT,created_utc TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS events(created_utc TEXT,event TEXT,detail TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS binding(hash TEXT)')
    bound=con.execute('SELECT hash FROM binding').fetchone()
    if bound and bound[0]!=sha(output/'CONFIG.json'):raise ValueError('CPU resume fingerprint differs')
    if not bound:con.execute('INSERT INTO binding VALUES (?)',(sha(output/'CONFIG.json'),))
    con.execute('INSERT INTO events VALUES (?,?,?)',(utc(),'ATTEMPT_START',str(os.getpid())));con.commit()
    source=read(output/'SOURCES.json');spec=read(W/cfg['mapping']);start=time.monotonic();done=con.execute('SELECT count(*) FROM results').fetchone()[0];cache={};new=0
    expected=sum(len(d['expected']) for d in source.values())*len(cfg['model_order'])
    try:
        for dataset,s in source.items():
            for i,iid in enumerate(s['expected']):
                present={r[0] for r in con.execute('SELECT model FROM results WHERE dataset=? AND image_id=?',(dataset,iid))}
                failed={r[0] for r in con.execute('SELECT DISTINCT model FROM errors WHERE dataset=?',(dataset,))}
                pending=[mid for mid in cfg['model_order'] if mid not in present and mid not in failed]
                if not pending:continue
                if shutil.disk_usage(output).free<cfg['minimum_free_GiB']*2**30:raise RuntimeError('FREE_SPACE_GUARD')
                gt=load_gt(dataset,iid,s,spec);geometry_cache={}
                with con:
                    for mid in pending:
                        try:
                            arrays,meta=load_prediction(s['models'][mid]['packets'][iid],mid,iid,s['models'][mid],s['frames'][iid],cache)
                            if meta['original_wh']!=list(gt['shape'][::-1]):raise ValueError('Original-grid metadata differs')
                            result=dict(image_id=iid,source_packet_sha256=meta['packet_sha256'],
                                **score_frame(gt,arrays,meta['label_space'],spec,geometry_cache))
                            con.execute('INSERT INTO results VALUES (?,?,?,?)',(dataset,mid,iid,json.dumps(result,allow_nan=False,separators=(',',':'))));done+=1;new+=1
                        except Exception:
                            con.execute('INSERT INTO errors VALUES (?,?,?,?,?)',(dataset,mid,iid,traceback.format_exc(),utc()))
                            print('MODEL_ERROR',dataset,mid,iid,traceback.format_exc(),flush=True)
                if i%25==0 or i+1==len(s['expected']):
                    atomic_json(output/'STATUS.json',dict(status='CPU_SCORING',dataset=dataset,current_id=iid,pid=os.getpid(),updated_utc=utc(),
                        completed_image_model_records=done,expected_image_model_records=expected,wall_seconds=time.monotonic()-start,new_model_calls=0))
                    print(dataset,i+1,'/',len(s['expected']),done,'/',expected,flush=True)
                if limit and new>=limit:
                    con.execute('INSERT INTO events VALUES (?,?,?)',(utc(),'BOUNDED_INTEGRATION_STOP','Committed results retained for explicit resume'));con.commit()
                    atomic_json(output/'STATUS.json',dict(status='INTEGRATION_STOP',completed_image_model_records=done,expected_image_model_records=expected,updated_utc=utc(),new_model_calls=0))
                    return
        final=report(output,cfg,source,con)
        complete=all(v['strict_complete'] for d in final.values() for v in d.values())
        con.execute('INSERT INTO events VALUES (?,?,?)',(utc(),'COMPLETE' if complete else 'INCOMPLETE',str(done)));con.commit()
        atomic_json(output/'STATUS.json',dict(status='COMPLETE' if complete else 'INCOMPLETE',updated_utc=utc(),completed_image_model_records=done,
            expected_image_model_records=expected,wall_seconds=time.monotonic()-start,new_model_calls=0))
    except BaseException:
        con.rollback();con.execute('INSERT INTO events VALUES (?,?,?)',(utc(),'INTERRUPTED',traceback.format_exc()));con.commit()
        atomic_json(output/'STATUS.json',dict(status='INTERRUPTED_RECONCILIATION_REQUIRED',updated_utc=utc(),completed_image_model_records=con.execute('SELECT count(*) FROM results').fetchone()[0],expected_image_model_records=expected,new_model_calls=0))
        raise
    finally:con.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','run','status']);p.add_argument('--output',type=Path,required=True);p.add_argument('--resume',action='store_true');p.add_argument('--limit-records',type=int)
    a=p.parse_args();root=a.output.resolve()
    if a.action=='prepare':prepare(root)
    elif a.action=='run':run(root,a.resume,a.limit_records)
    else:print(json.dumps(read(root/'STATUS.json'),ensure_ascii=False,indent=2))
