"""Private CCTV partial-label benchmark. No unlabeled pixels become negatives.

Shared frozen parsing implementations are imported, never copied or edited.
Every GPU stage runs in its existing environment in an isolated process.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse, csv, fcntl, json, os, shutil, subprocess, sys, time, traceback
import numpy as np
P=Path(__file__).resolve().parents[1];W=P.parent;H=W/'Human_Parsing_Benchmark'
sys.path.insert(0,str(H/'src'))
from common_view.core import sha_file, load_spec, compose_native, project, validate_prediction
from common_view.packets import atomic_json, write_packet
from cihp_benchmark.data import read_image

ORDER=['QANet_CIHP_HRNetW48_512x384','M2FP_R101_CIHP','D2FP_R101_CIHP','RPR_CIHP',
       'CPI_R50_CIHP','CPI_ConvNeXtB_CIHP','Sapiens2_0.4b','Sapiens2_0.8b','Sapiens2_1b']
def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def emit(f,row):f.write(json.dumps(row,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
def yolo_input(rgb):return np.ascontiguousarray(rgb[:,:,::-1])  # Ultralytics NumPy input is BGR.

def partial_confusion(category,prediction):
    """GT native IDs2/5/9/13 only; prediction already common IDs0..5."""
    if set(np.unique(category))-{0,2,5,9,13}:raise ValueError('Unexpected CCTV GT taxonomy')
    if prediction.shape!=category.shape or prediction.dtype.kind not in 'ui' or np.any(prediction>5):raise ValueError('Prediction contract')
    lut=np.zeros(20,np.uint8);lut[[13,2,5,9]]=[1,2,3,4]
    gt=lut[category];known=gt>0
    return np.bincount(6*gt[known].astype(np.int64)+prediction[known],minlength=36).reshape(6,6)

def summarize(hist):
    h=np.asarray(hist,np.int64);support=h.sum(1);tp=np.diag(h)
    recall=[float(tp[k]/support[k]) if support[k] else None for k in range(1,5)]
    return dict(per_target_recall=recall,GT_pixels=support[1:5].tolist(),correct_pixels=tp[1:5].tolist(),
      macro_recall4=float(np.mean(recall)) if all(v is not None for v in recall) else None,
      annotated_pixel_accuracy=float(tp.sum()/h.sum()) if h.sum() else None,
      full_image_mIoU=None,full_image_precision=None,person_extent_F1=None,
      null_reason='Unlabeled persons/parts and full-person silhouettes unavailable; negatives outside labels unknown.')

def prepare(run):
    raw=P/'outputs'/run;raw.mkdir(parents=True,exist_ok=False)
    ds=W/'datasets/CCTV_100_Evaluation';ids=[l.strip() for l in (ds/'val_id.txt').read_text().splitlines() if l.strip()]
    assert len(ids)==len(set(ids))
    native=read(H/'configs/cihp_native_six.json');specpath=H/'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json'
    members=[];counts=Counter();support=np.zeros(20,np.int64);duplicates={};seen={};shapes=Counter();people=0
    for index,stem in enumerate(ids):
        rgb,rm=read_image(ds/'Images'/(stem+'.jpg'));cat,cm=read_image(ds/'Category_ids'/(stem+'.png'),True)
        human,hm=read_image(ds/'Human_ids'/(stem+'.png'),True);instance,im=read_image(ds/'Instance_ids'/(stem+'.png'),True)
        assert cat.shape==human.shape==instance.shape==rgb.shape[:2]
        assert set(np.unique(cat))<={0,2,5,9,13}
        assert np.array_equal(cat>0,human>0)
        ann=read(ds/'Annotations_canonical'/(stem+'.json'))
        assert ann['imageWidth']==rgb.shape[1] and ann['imageHeight']==rgb.shape[0]
        assert all(s['label'].split('_')[-1] in ['hair','face','upper','lower'] for s in ann['shapes'])
        day='day' if stem.startswith('day_') else 'night';counts[day]+=1
        support+=np.bincount(cat.ravel(),minlength=20);shapes[str(list(rgb.shape[:2]))]+=1
        people+=len(set(np.unique(human))-{0})
        if rm['file_sha256'] in seen:duplicates[stem]=seen[rm['file_sha256']]
        seen[rm['file_sha256']]=stem
        members.append(dict(id='cctv_%04d'%(index+1),stem=stem,condition=day,wh=[rgb.shape[1],rgb.shape[0]],
          RGB_sha256=rm['file_sha256'],GT_sha256={'Category_ids':cm['file_sha256'],'Human_ids':hm['file_sha256'],'Instance_ids':im['file_sha256']},
          annotation_sha256=sha_file(ds/'Annotations_canonical'/(stem+'.json'))))
    assert not duplicates, 'Duplicate images require explicit population review'
    models=dict(native['models'])
    for mid,size,record in [('Sapiens2_0.4b','0.4b','common-c4p-full-20261029T063458522990Z'),('Sapiens2_0.8b','0.8b','sapiens08-c4p-20261029T081254180014Z'),('Sapiens2_1b','1b','sapiens1b-c4p-20261029T200113781375Z')]:
        cfg=read(H/'configs/cihp_sapiens_c4p_full.json') if size=='0.4b' else read(H/'runs'/record/'FULL_CONFIG.json')
        m=cfg['model'];models[mid]=dict(model_id=mid,family='Sapiens2',checkpoint=m['checkpoint'],checkpoint_sha256=m['checkpoint_sha256_from_frozen_registry'],
          native_config=m['native_config'],native_config_sha256=m['native_config_sha256'],source='third_party/human_parsing/sapiens2',source_commit=m['source_commit'],
          environment='.venvs/sapiens2-pilot',route='SAPIENS_FRAME_YOLO_MASK_OWNERSHIP')
    files=[Path(__file__),H/'src/cihp_benchmark/adapters.py',H/'src/cihp_benchmark/data.py',H/'src/common_view/core.py',H/'src/common_view/packets.py',H/'src/common_view/sapiens_route.py']
    files += list((H/'src/cihp_benchmark').glob('cpi*memory.py'))+[H/'src/cihp_benchmark/cpi_feature_schedule.py']
    for mid,m in models.items():
        assert sha_file(W/m['native_config'])==m['native_config_sha256']
        assert subprocess.check_output(['git','-C',str(W/m['source']),'rev-parse','HEAD'],text=True).strip()==m['source_commit']
        stat=(W/m['checkpoint']).stat();m['checkpoint_stat']={'size':stat.st_size,'mtime_ns':stat.st_mtime_ns}
    cfg=dict(run_id=run,dataset_root='datasets/CCTV_100_Evaluation',artifact_root=str(raw.relative_to(W)),members=members,models={k:models[k] for k in ORDER},
      protocol='CCTV_PARTIAL_TARGET_RECALL_V1',projection=str(specpath.relative_to(W)),projection_sha256=sha_file(specpath),
      user_annotation_scope='SELECTED_PEOPLE_OR_PARTS',dress_policy='UNSPECIFIED_BY_SOURCE; upper/lower label agreement only, no verified non-Dress claim',
      valid_domain='GT Category_ids in {2,5,9,13}; GT0 UNKNOWN and excluded for all models',
      no_GT_in_prediction=True,YOLO=dict(checkpoint='models/yolo26x-seg.pt',checkpoint_sha256='92b3de0065766a17180d6219858717dc9d03cdce8a3ca9576c97fd75aabb64f3',imgsz=640,conf=.25,iou=.7,max_det=200,retina_masks=True),
      precision='FP32',seed=native['seed'],automatic_retry=0,fallback=False,minimum_free_gib=50,max_model_gib=80,max_model_hours=24,
      resource_policy='SHARED_GPU_QUALITY_ONLY; sequential one worker, no cost ranking; preserve other processes',
      required_free_MiB={'YOLO26X':2048,'QANet_CIHP_HRNetW48_512x384':2560,'M2FP_R101_CIHP':8192,'D2FP_R101_CIHP':9216,'RPR_CIHP':6144,
      'CPI_R50_CIHP':14500,'CPI_ConvNeXtB_CIHP':13500,'Sapiens2_0.4b':4608,'Sapiens2_0.8b':6656,'Sapiens2_1b':9600},
      source_hashes={str(f.relative_to(W)):sha_file(f) for f in files},warmup='CIHP TRAIN0000930 once per parser process, excluded from CCTV score',
      dataset_mutation_forbidden=True,publication='No CCTV filenames/images/annotations/per-person metadata/masks in public Git')
    atomic_json(raw/'CONFIG.json',cfg)
    audit=dict(run_id=run,created_utc=utc(),declared_folder_count=100,actual_population=len(members),day_night=dict(counts),image_geometry=dict(shapes),
      GT_people_with_annotated_parts=people,GT_native_pixel_support=support.tolist(),GT_Human_extent='Union of annotated target parts, not complete person silhouette',
      source_annotations='90 canonical LabelMe polygon JSONs and corresponding integer PNGs; semantic accuracy/exhaustiveness not certified by file checks',
      user_confirmations={'annotation_scope':'Selected people or parts','Dress':'No established rule'},
      allowed_claim='Annotation-conditioned target recall and cross-class confusion, not whole-image IoU/FP/instance accuracy or overall deployment winner',
      existing_results='Separate exploratory scripts collapse OTHER toBG/use unconditioned routes and retain no sufficient native packet evidence; preserved, not canonical here')
    atomic_json(P/'reports/DATASET_AUDIT.json',audit)
    atomic_json(P/'configs/PROTOCOL.json',{k:cfg[k] for k in ['protocol','projection','projection_sha256','user_annotation_scope','dress_policy','valid_domain','precision','automatic_retry','fallback','resource_policy','publication']})
    (P/'CURRENT_RUN.txt').write_text(run+'\n');print(run)

def guard(c,root,start):
    if shutil.disk_usage(root).free<c['minimum_free_gib']*2**30:raise RuntimeError('DISK_FREE_GUARD')
    if time.monotonic()-start>c['max_model_hours']*3600:raise RuntimeError('TIME_GUARD')
    if sum(f.stat().st_size for f in root.rglob('*') if f.is_file())>c['max_model_gib']*2**30:raise RuntimeError('STORAGE_GUARD')
def check(c):
    for path,h in c['source_hashes'].items():
        if sha_file(W/path)!=h:raise RuntimeError('Scientific/source drift '+path)
    assert sha_file(W/c['projection'])==c['projection_sha256']
def resource():
    r=subprocess.check_output(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).splitlines()
    return float(r[0])

def worker(cp,mid):
    c=read(cp);root=W/c['artifact_root']/mid;root.mkdir(parents=True,exist_ok=False);start=time.monotonic();check(c)
    state=dict(model_id=mid,run_id=c['run_id'],status='INITIALIZING',expected=len(c['members']),complete=0,failed=0,invalid=0,
      start_utc=utc(),pid=os.getpid(),warmup_calls=0,model_frame_calls=0,precision='FP32',config_sha256=sha_file(cp))
    atomic_json(root/'STATE.json',state);ledger=(root/'FRAMES.jsonl').open('x',buffering=1)
    hist={k:np.zeros((6,6),np.int64) for k in ['overall','day','night']}
    try:
        import torch
        torch.manual_seed(c['seed']);np.random.seed(c['seed']);torch.set_num_threads(2)
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        state.update(torch=torch.__version__,CUDA_runtime=torch.version.cuda,python=sys.version,GPU=torch.cuda.get_device_name(0))
        if mid=='YOLO26X':
            assert sha_file(W/c['YOLO']['checkpoint'])==c['YOLO']['checkpoint_sha256']
            from ultralytics import YOLO
            model=YOLO(str(W/c['YOLO']['checkpoint']));model.model.float().eval()
        else:
            m=c['models'][mid];s=(W/m['checkpoint']).stat();assert {'size':s.st_size,'mtime_ns':s.st_mtime_ns}==m['checkpoint_stat']
            assert sha_file(W/m['checkpoint'])==m['checkpoint_sha256']
            sapiens=m['family']=='Sapiens2';space='SAPIENS2_DOME29_PRED' if sapiens else 'CIHP_GT_AND_NATIVE_PRED';spec=load_spec(W/c['projection'])
            if sapiens:
                from sapiens.dense.models import init_model
                from safetensors.torch import load_file
                from common_view.sapiens_route import prepare_rgb,logits_to_native,ownership_planes
                model=init_model(W/m['native_config'],checkpoint=None,device='cpu');weights=load_file(W/m['checkpoint'],device='cpu');model.load_state_dict(weights,strict=True);del weights
                model.float().eval().cuda()
            else:
                from cihp_benchmark.adapters import NativeAdapter
                adapter=NativeAdapter(W,m,root/'adapter')
                if mid.startswith('CPI_'):
                    if mid=='CPI_R50_CIHP':from cihp_benchmark.cpi_feature_schedule import install
                    else:from cihp_benchmark.cpi_memory import install
                    receipt=install(adapter.model.bbox_head,'85b75e0fe38465ec460107c11111702345a6de091a8ba3d399ca266878ca7573')
                    atomic_json(root/'MEMORY_IMPLEMENTATION.json',receipt)
            def infer(rgb,image,op,masks):
                if not sapiens:return adapter.infer(rgb,image,op,masks)
                tensor,geometry=prepare_rgb(rgb,model.pipeline,model.data_preprocessor)
                with torch.inference_mode():native=logits_to_native(model(tensor.cuda()),rgb.shape[:2])
                return ownership_planes(native,masks,np.array([o['score'] for o in op],np.float32)),dict(geometry=geometry,GT_used_in_prediction=False)
            old=read(H/'configs/cihp_native_six.json');tr=read(W/old['frozen_YOLO']['training_run']);warm=next(x for x in tr['images'] if x['image_id']=='0000930')
            rgb,_=read_image(W/'datasets/CIHP/Training/Images/0000930.jpg')
            from common_view.detector_cache import normalize_detector_masks
            with np.load(W/'Human_Parsing_MHPv2_Study'/warm['artifact'],allow_pickle=False) as z:mask=normalize_detector_masks(z['masks'],len(warm['opportunities']),rgb.shape[:2])
            guard(c,root,start);infer(rgb,W/'datasets/CIHP/Training/Images/0000930.jpg',warm['opportunities'],mask);state['warmup_calls']=1
        for sample in c['members']:
            iid=sample['id'];guard(c,root,start);check(c);state.update(status='RUNNING',current_id=iid)
            image=W/c['dataset_root']/'Images'/(sample['stem']+'.jpg');rgb,im=read_image(image);assert im['file_sha256']==sample['RGB_sha256'];h,w=rgb.shape[:2]
            if mid=='YOLO26X':
                with torch.inference_mode():r=model.predict(source=yolo_input(rgb),device=0,half=False,imgsz=640,conf=.25,iou=.7,max_det=200,retina_masks=True,classes=[0],save=False,verbose=False)[0]
                boxes=r.boxes.xyxy.cpu().numpy();scores=r.boxes.conf.cpu().numpy();masks=(r.masks.data.cpu().numpy()>0.5) if r.masks is not None else np.empty((0,h,w),bool)
                assert masks.shape==(len(boxes),h,w)
                ops=[dict(id=iid+':yolo:'+str(j),bbox=b.tolist(),score=float(scores[j])) for j,b in enumerate(boxes)]
                target=root/'packets'/iid;target.mkdir(parents=True,exist_ok=False);np.savez_compressed(target/'detector.npz',masks=masks,boxes=boxes,scores=scores)
                atomic_json(target/'COMMIT.json',dict(image_id=iid,input_sha256=sample['RGB_sha256'],original_wh=[w,h],opportunities=ops,artifact_sha256=sha_file(target/'detector.npz')))
            else:
                detector=W/c['artifact_root']/'YOLO26X/packets'/iid;d=read(detector/'COMMIT.json');assert d['input_sha256']==sample['RGB_sha256']
                assert sha_file(detector/'detector.npz')==d['artifact_sha256']
                with np.load(detector/'detector.npz',allow_pickle=False) as z:masks=z['masks']
                arrays,meta=infer(rgb,image,d['opportunities'],masks);state['model_frame_calls']+=1
                validate_prediction(arrays['person_semantic_masks'],arrays['person_extents'],arrays['person_scores'],(h,w),space)
                prediction=project(compose_native(arrays['person_semantic_masks'],arrays['person_scores'],(h,w)),space,spec)
                category,gt=read_image(W/c['dataset_root']/'Category_ids'/(sample['stem']+'.png'),True);assert gt['file_sha256']==sample['GT_sha256']['Category_ids']
                conf=partial_confusion(category,prediction);hist['overall']+=conf;hist[sample['condition']]+=conf
                metadata=dict(meta,model_id=mid,image_id=iid,input_sha256=sample['RGB_sha256'],original_wh=[w,h],checkpoint_sha256=m['checkpoint_sha256'],
                  source_commit=m['source_commit'],label_space=space,precision='FP32',protocol=c['protocol'],config_sha256=sha_file(cp),detector_sha256=d['artifact_sha256'])
                target=write_packet(root/'packets',iid,arrays,metadata,{'partial':dict(histogram=conf.tolist(),GT_sha256=sample['GT_sha256'])})
                with np.load(target/'prediction.npz',allow_pickle=False) as z:
                    again=project(compose_native(z['person_semantic_masks'],z['person_scores'],(h,w)),space,spec)
                assert np.array_equal(conf,partial_confusion(category,again))
            state['complete']+=1;emit(ledger,dict(image_id=iid,status='COMPLETE',end_utc=utc(),packet=str(target.relative_to(W))))
            atomic_json(root/'STATE.json',state)
        state.update(status='COMPLETE',end_utc=utc(),missing=0)
    except BaseException:
        state.update(status='INCOMPLETE',failed=1,end_utc=utc(),error=traceback.format_exc());atomic_json(root/'FAILURE.json',state)
    finally:
        ledger.close();atomic_json(root/'STATE.json',state)
        if mid!='YOLO26X':atomic_json(root/'METRICS.json',dict(status=state['status'],primary=summarize(hist['overall']) if state['status']=='COMPLETE' else None,
           groups={k:dict(histogram=v.tolist(),metrics=summarize(v)) for k,v in hist.items()} if state['status']=='COMPLETE' else None,protocol=c['protocol']))

def report(c):
    raw=W/c['artifact_root'];states={};metrics={}
    for mid in ORDER:
        f=raw/mid/'STATE.json';states[mid]=read(f) if f.exists() else dict(status='NOT_STARTED',complete=0)
        f=raw/mid/'METRICS.json'
        if f.exists():metrics[mid]=read(f)
    atomic_json(raw/'BATCH_STATUS.json',dict(run_id=c['run_id'],updated_utc=utc(),models=states))
    text='# CCTV partial-annotation benchmark — สถานะและผลจริง\n\n'
    text+='ชุดนี้มี '+str(len(c['members']))+' ภาพ ไม่ใช่100; annotateเฉพาะบางคน/บางส่วน และยังไม่มีกติกาDress. พื้นที่GT0เป็นUNKNOWNไม่ใช่negative. คะแนนหลักคือmacro recall4เฉพาะพิกเซลที่มีlabel; ไม่ใช่full-imageIoU/precision/personF1หรือคำรับรองผู้ชนะโดยรวม.\n\n'
    text+='|Model|Status|Complete|Face recall %|Hair recall %|Upper recall %|Lower recall %|Macro recall %|\n|---|---|---:|---:|---:|---:|---:|---:|\n'
    for mid,s in states.items():
        m=metrics.get(mid,{}).get('primary');values=m['per_target_recall']+[m['macro_recall4']] if m else [None]*5
        text+='|'+mid+'|'+s['status']+'|'+str(s['complete'])+'/'+str(len(c['members']))+'|'+'|'.join('N/A' if v is None else f'{v*100:.3f}' for v in values)+'|\n'
    text+='\nทุกระบบใช้inputpopulationเดียวกัน, frozenYOLOcheckpoint/settings/cacheเดียวกัน, nativeFP32settings/threshold/TTA/map-backเดิม. QANetYOLOROI, Sapiensfull-frame+YOLOmaskownership, nativeinstanceparsers+YOLOassociationเป็นapplicationconfigurationcomparison ไม่ใช่architecture-onlytest. ไม่มีGTช่วยinference.\n\n'
    text+='Face_Neckเป็นproxy; Upper/Lowerคือagreementกับannotationชุดนี้ ไม่ยืนยันnon-Dressboundary. OTHER/unknownpredictionclassesต้องไม่หายก่อนoverlap. Unlabeledpixelsไม่คิดFPหรือFN, ดังนั้นoversegmentationนอกlabelsไม่ถูกลงโทษและใช้recallเลือกdeploymentwinnerไม่ได้. ผลday/nightอยู่privatecanonicalMETRICS; ไม่มีspeed/VRAMranking.\n\n'
    text+='STRICT_COMPLETE: primaryเฉพาะระบบที่ครบexactpopulation; failed/blockedไม่เอาsubsetมาแทน. Model/OOMretry0 ไม่มีprecision/resolutionfallback. เก็บpackets/hash/metadata/attemptlogsในprivateoutputs; ไม่เผยแพร่CCTVassets/filenamesบนGit. รอบเดิมในdataset/resultsเป็นexploratoryคนละroute/scoring ไม่ใช้รวมคะแนน.\n\n'
    text+='ก่อนทำfullbenchmarkสำหรับเลือกผู้ชนะ ต้องมีsharednegative/ignore/complete-targetannotationpolicy, DressguidelineและQA/GTที่freezeแล้ว และfull-personextentsหากต้องการinstanceF1. การตั้งค่าประเมินไม่สร้างGTส่วนที่ขาดขึ้นมา.\n'
    (P/'reports/RESULTS_TH.md').write_text(text)
    complete=sum(s['status']=='COMPLETE' for s in states.values());blocked=[mid for mid,s in states.items() if s['status']=='BLOCKED_RESOURCE']
    current=read(raw/'CURRENT_WORKER.json') if (raw/'CURRENT_WORKER.json').exists() else {}
    live=False
    try:live='benchmark.py' in Path('/proc/'+str(current.get('pid'))+'/cmdline').read_bytes().decode().replace('\x00',' ')
    except OSError:pass
    (P/'STATUS.md').write_text('# Current CCTV partial benchmark\n\nUpdated '+utc()+' UTC. **'+str(complete)+'/9 COMPLETE**; active worker '+(current.get('model_id','N/A') if live else 'none')+'.\n\nBlocked resource: '+(', '.join(blocked) if blocked else 'none')+'. No automatic model/OOM retries.\n\n[Results](reports/RESULTS_TH.md) / [Protocol](PROTOCOL.md). Partial annotations: full-imageIoU/personF1/overallwinner not identifiable. Private run `'+c['run_id']+'`; `outputs/<run>/CURRENT_WORKER.json` and `<model>/STATE.json` show live progress; filesystem report is current, GitHub updates only after explicit sync.\n')

def controller(cp):
    c=read(cp);raw=W/c['artifact_root'];lock=(raw/'CONTROLLER.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    atomic_json(raw/'CONTROLLER.json',dict(pid=os.getpid(),SID=os.getsid(0),start_utc=utc(),config_sha256=sha_file(cp)))
    for mid in ['YOLO26X']+ORDER:
        statefile=raw/mid/'STATE.json'
        if statefile.exists():
            if read(statefile)['status']=='COMPLETE':continue
            raise RuntimeError('Previous attempt exists; reconcile explicitly, never overwrite')
        check(c);free=resource()
        if free<c['required_free_MiB'][mid]:
            (raw/mid).mkdir(parents=True,exist_ok=True);atomic_json(statefile,dict(status='BLOCKED_RESOURCE',complete=0,free_MiB=free,required_MiB=c['required_free_MiB'][mid],model_id=mid));report(c)
            if mid=='YOLO26X':break
            continue
        envname='.venv' if mid=='YOLO26X' else c['models'][mid]['environment']
        command=[str(W/envname/'bin/python'),'-u',str(Path(__file__)), '--worker',mid,'--config',str(cp)]
        env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
        logfile=raw/(mid+'.log')
        with logfile.open('ab') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,env=env)
            atomic_json(raw/'CURRENT_WORKER.json',dict(model_id=mid,pid=child.pid,command=command,log=str(logfile.relative_to(W))))
            report(c)
            child.wait()
        if not statefile.exists():
            (raw/mid).mkdir(parents=True,exist_ok=True);atomic_json(statefile,dict(status='SETUP_FAILED',complete=0,model_id=mid,exit_code=child.returncode))
        report(c)
        if mid=='YOLO26X' and read(statefile)['status']!='COMPLETE':break
    report(c);atomic_json(raw/'CONTROLLER_TERMINAL.json',dict(status='STOPPED_AFTER_SCOPED_BATCH',end_utc=utc(),no_automatic_retry=True))
    with (P/'WORK_LOG.md').open('a') as f:f.write('\n## '+utc()+' UTC — scoped controller terminal\n\nAutomatic private state/report updated. Read currentSTATUS/BATCH_STATUS; no automatic retries/next experiment. Public Git not synced automatically; publish only aggregate documents after review.\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--prepare');ap.add_argument('--config',type=Path);ap.add_argument('--worker');ap.add_argument('--run',action='store_true');a=ap.parse_args()
    if a.prepare:prepare(a.prepare)
    elif a.worker:worker(a.config.resolve(),a.worker)
    elif a.run:controller(a.config.resolve())
    else:report(read(a.config))
