"""One frozen TRAIN frame: actual YOLO26x + two native CPI workers + association.
Engineering route test only. No GT scoring, validation inference or benchmark.
"""
from pathlib import Path
from datetime import datetime, timezone
import sys,os,json,shutil,subprocess,copy,time,argparse
S=Path(__file__).resolve().parents[1];W=S.parent;sys.path.insert(0,str(S))
from src.application_v2.policy import load_config,digest,fingerprints
from src.application_v2.artifacts import file_hash,commit_packet,resume_packet

def current_run():
    r=S/json.loads((S/'provenance/FIRST_COHORT_READINESS_ACTIVE.json').read_text())['run']
    return r

def load():
    c=load_config(S/'configs/application_v2_first_cohort_v4.yaml');p=c['first_cohort']['engineering']
    if p['split']!='Training' or p['precision']!='FP32' or p['maximum_frames']!=1 or p['full_benchmark'] or p['common_metrics_or_ranking']:
        raise ValueError('Engineering scope exceeded')
    if p['input_ids']!=['0000930']:raise ValueError('This fixed route test permits only its predeclared TRAIN image')
    return c

def idle():
    if subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():
        raise RuntimeError('GPU occupied; leave other jobs untouched')

def prepare():
    c=load();r=current_run();b=r/'live_route';b.mkdir()
    for name in ['scripts','outputs','configs','taxonomy','provenance','logs']:(b/name).mkdir()
    pilot=W/'Human_Parsing_CCIHP_10_Image_Pilot';manifest=json.loads((pilot/'configs/TEN_IMAGE_MANIFEST.json').read_text())
    manifest['images']=[x for x in manifest['images'] if x['image_id'] in c['first_cohort']['engineering']['input_ids']]
    assert len(manifest['images'])==1 and manifest['images'][0]['split']=='Training'
    rec=manifest['images'][0];assert file_hash(pilot/rec['input'])==rec['input_sha256']
    manifest['scope']='One TRAIN engineering route; no quality scores or selection';(b/'configs/TEN_IMAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
    (b/'outputs/inputs').symlink_to((pilot/'outputs/inputs').resolve(),target_is_directory=True)
    shutil.copy2(pilot/'taxonomy/NATIVE_CLASS_INVENTORY.json',b/'taxonomy/NATIVE_CLASS_INVENTORY.json')
    old=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run']/'native_smoke'
    worker=(old/'scripts/run_cpi.py').read_text();original=worker
    oldspec="[('CPI_R50_CIHP','r50','CIHP'),('CPI_R50_MHPV2','r50','MHPV2'),('CPI_ConvNeXtB_CIHP','convnext_b','CIHP'),('CPI_ConvNeXtB_MHPV2','convnext_b','MHPV2')]"
    assert oldspec in worker
    specs=[(model,'r50' if 'R50' in model else 'convnext_b','CIHP') for model in c['first_cohort']['models']]
    worker=worker.replace(oldspec,repr(specs));(b/'scripts/run_cpi.py').write_text(worker)
    wrapper=(S/'scripts/run_handoff_smoke_worker.py').read_text()
    wrapper=wrapper.replace("S=Path(__file__).resolve().parents[1];W=S.parent","S=Path(os.environ['FIRST_COHORT_STUDY']);W=S.parent")
    wrapper=wrapper.replace("B=S/json.loads((S/'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run']/'native_smoke'","B=Path(os.environ['FIRST_COHORT_ROUTE'])")
    (b/'scripts/worker_wrapper.py').write_text(wrapper)
    import difflib
    (b/'WORKER_DIFF.txt').write_text(''.join(difflib.unified_diff(original.splitlines(True),worker.splitlines(True),fromfile='previous_native_CPI_worker',tofile='first_cohort_CPI_worker')))
    (b/'PREPARED.json').write_text(json.dumps({'config_sha256':file_hash(S/'configs/application_v2_first_cohort_v4.yaml'),'fixed_input':rec,'worker_sha256':file_hash(b/'scripts/run_cpi.py'),'parent_worker_sha256':file_hash(old/'scripts/run_cpi.py'),'precision':'FP32','batch':1,'warmups':0,'measured_frames':1,'model_retries':0,'resident_models':'Separate sequential detector/parser processes; no joint memory claim','benchmark':False},indent=2))
    return b

def yolo(b):
    c=load();idle();os.environ['YOLO_CONFIG_DIR']=str(b/'yolo_settings')
    import numpy as np,torch
    from ultralytics import YOLO
    rec=json.loads((b/'configs/TEN_IMAGE_MANIFEST.json').read_text())['images'][0]
    source=b/rec['input'];assert file_hash(source)==rec['input_sha256']
    with np.load(source,allow_pickle=False) as z:rgb=z['rgb'].copy()
    frozen=json.loads((S/'manifests/YOLO26X_SOURCE.json').read_text());ck=W/frozen['checkpoint_workspace_relative'];assert file_hash(ck)==frozen['sha256']
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    model=YOLO(str(ck));assert model.task=='segment' and model.names[0].lower()=='person';model.model.float().eval()
    assert all(v.dtype==torch.float32 for v in model.model.parameters())
    options=c['bounded_train']['yolo'];torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
    with torch.inference_mode():
        pred=model.predict(rgb[...,::-1].copy(),device=0,classes=[0],half=False,verbose=False,imgsz=options['imgsz'],conf=options['conf'],iou=options['iou'],max_det=options['max_det'],retina_masks=options['retina_masks'],save=False,project=str(b/'outputs/yolo_native'))[0]
    torch.cuda.synchronize();seconds=time.perf_counter()-start
    boxes=pred.boxes.xyxy.cpu().numpy();scores=pred.boxes.conf.cpu().numpy();h,w=rgb.shape[:2]
    masks=pred.masks.data.cpu().numpy() if pred.masks is not None else np.empty((0,h,w),np.float32)
    assert masks.shape==(len(boxes),h,w) and np.isfinite(boxes).all() and np.isfinite(scores).all()
    artifact=b/'outputs/YOLO_NATIVE.npz';np.savez_compressed(artifact,masks=masks,boxes=boxes,scores=scores)
    opportunities=[{'id':rec['image_id']+':YOLO:'+str(i),'bbox':box.tolist(),'score':float(scores[i])} for i,box in enumerate(boxes)]
    output={'status':'COMPLETE','image_id':rec['image_id'],'original_wh':[w,h],'input_sha256':rec['input_sha256'],'checkpoint_sha256':frozen['sha256'],'opportunities':opportunities,'artifact':str(artifact.relative_to(S)),'artifact_sha256':file_hash(artifact),'torch':torch.__version__,'cuda_runtime':torch.version.cuda,'precision':'FP32','TF32':False,'warmups':0,'batch':1,'predict_call_seconds_engineering_only':seconds,'peak_allocated_mib':torch.cuda.max_memory_allocated()/2**20,'peak_reserved_mib':torch.cuda.max_memory_reserved()/2**20,'GT_used_for_inference':False,'source_sha256':file_hash(Path(__file__))}
    (b/'YOLO.json').write_text(json.dumps(output,indent=2))

def verify(b):
    import numpy as np
    from src.application_v2.evaluation import associate_native
    from src.application_v2.runner import ConfiguredRunner
    c=load();prepared=json.loads((b/'PREPARED.json').read_text());assert prepared['config_sha256']==file_hash(S/'configs/application_v2_first_cohort_v4.yaml')
    y=json.loads((b/'YOLO.json').read_text());assert file_hash(S/y['artifact'])==y['artifact_sha256']
    bindings={v['model_id']:v for v in json.loads((current_run()/'CHECKPOINT_SUPPORT_BINDINGS_DRAFT.json').read_text())}
    train=json.loads((current_run()/'TRAIN_DOMAIN_REVIEW.json').read_text());assert train['image_id']==y['image_id']
    rows=[];evidence=[]
    for model in c['first_cohort']['models']:
        paths=list(b.glob('outputs/'+model.lower()+'-*/RUN.json'))
        if not paths:
            rows.append({'system_id':model,'image_id':y['image_id'],'execution_status':'NOT_ATTEMPTED'});continue
        assert len(paths)==1;native=json.loads(paths[0].read_text())
        if native['status']!='BOUNDED_NATIVE_PASS':
            rows.append({'system_id':model,'image_id':y['image_id'],'execution_status':'FAILED','failure_events':[{'status':'MODEL_SYSTEM_FAILURE','exception':native.get('error','unknown native failure')}]});continue
        assert native['checkpoint_sha256']==bindings[model]['checkpoint_sha256'] and native['config_source_sha256']==bindings[model]['native_config_source_sha256']
        case=native['cases'][0];assert case['image_id']==y['image_id'];p=b/case['artifact'];assert file_hash(p)==case['artifact_sha256']
        with np.load(p,allow_pickle=False) as z:boxes=z['bboxes_xyxy_scores'].copy();masks=z['person_semantic_masks'].copy()
        instances=[{'id':f'native:{i}','bbox':box[:4].tolist()} for i,box in enumerate(boxes)]
        association=associate_native(y['opportunities'],instances,c['first_cohort']['draft_matching']['threshold'])
        persons=[];final=[]
        for match in association['associations']:
            index=int(match['native_instance_id'].split(':')[-1])
            if not np.any(masks[index]>0):continue
            op=next(o for o in y['opportunities'] if o['id']==match['source_opportunity_id'])
            final.append(masks[index]);persons.append({'identity':{'origin':'NATIVE_AND_YOLO','native_identity_supported':True,'native_instance_id':match['native_instance_id'],'conditioning_source':'YOLO','source_opportunity_id':match['source_opportunity_id'],'final_person_id':model+':'+match['source_opportunity_id']},'score':float(boxes[index,4]),'evaluation_bbox':{'xyxy':boxes[index,:4].tolist(),'source':'NATIVE_PARSER_BOX','coordinate_convention':'XYXY_HALF_OPEN','derivation_revision':file_hash(Path(__file__))},'conditioning_bbox':{'xyxy':op['bbox'],'source':'FROZEN_YOLO26X_BOX','coordinate_convention':'XYXY_HALF_OPEN','derivation_revision':y['source_sha256']}})
        w,h=y['original_wh'];final=np.stack(final) if final else np.empty((0,h,w),np.uint8)
        record={'schema_version':'2.0','study_id':'human_parsing_mhpv2','run_id':current_run().name,'system_id':model,'model_id':model,'image_id':y['image_id'],'source_track':'T3B','source_commit':native['source_commit'],'adapter_revision':file_hash(Path(__file__)),'execution_profile':'ACTUAL_YOLO_AND_NATIVE_CPI_SEQUENTIAL_PROCESS_TRAIN_ENGINEERING','geometry_metadata':{'association':association,'native_artifact_sha256':case['artifact_sha256'],'YOLO_artifact_sha256':y['artifact_sha256'],'GT_used_for_association':False},'precision_profile':{'detector':'FP32','parser':'FP32','joint_resident_memory':'NOT_MEASURED'},'checkpoint_sha256':native['checkpoint_sha256'],'config_sha256':digest(c),'input_sha256':y['input_sha256'],'original_wh':[w,h],'mask_grid_space':'ORIGINAL','label_space':'NATIVE','label_catalog':list(range(20)),'native_identity_supported':True,'native_instance_ids':[v['id'] for v in instances],'persons':persons,'dataset_split':'Training'}
        inputs={'input_sha256':y['input_sha256'],'native_artifact':case['artifact_sha256'],'YOLO_artifact':y['artifact_sha256'],'adapter_revision':file_hash(Path(__file__))};fp=fingerprints(c,inputs)
        packet=b/'canonical'/model;commit_packet(packet,record,final,fp,native_arrays={'native_person_masks':masks,'native_boxes_scores':boxes});resume_packet(packet,fp['inference'])
        stages={'native_parser':{'stage':'native_parser','unit':'frame','numerator':1,'denominator':1},'association':{'stage':'YOLO_opportunity_association','unit':'person_opportunity','numerator':len(y['opportunities']),'denominator':len(y['opportunities']),'value':1.0 if y['opportunities'] else None}}
        rows.append({'system_id':model,'image_id':y['image_id'],'execution_status':'COMPLETE','failure_events':[],'stage_rates':stages})
        evidence.append({'model':model,'image_id':y['image_id'],'YOLO_opportunities':len(y['opportunities']),'native_instances':len(instances),'final_instances':len(persons),'native_run':str(paths[0].relative_to(S)),'canonical_packet':str(packet.relative_to(S)),'all_components_actual_inference':True,'native_config_source_sha256':native['config_source_sha256'],'native_checkpoint_sha256':native['checkpoint_sha256'],'joint_resident_pipeline':False,'GT_metric_scores_computed':False})
    report=ConfiguredRunner(S/'configs/application_v2_first_cohort_v4.yaml').comparison_report([{'image_id':y['image_id'],'G_loc':train['G_loc'],'G_sem':train['G_sem']}],rows)
    (b/'COMPARISON_ENGINEERING_STATUS.json').write_text(json.dumps(report,indent=2));(b/'ROUTE_EVIDENCE.json').write_text(json.dumps(evidence,indent=2));print(json.dumps({'actual_route_models':len(evidence),'common_quality_scores':False,'full_benchmark':False}))

def all_phases():
    b=prepare();c=load();env=os.environ.copy();env.update(HUMAN_PARSING_WORKSPACE=str(W),FIRST_COHORT_STUDY=str(S),FIRST_COHORT_ROUTE=str(b))
    processes=[]
    for name,cmd in [('yolo',[str(W/'.venv/bin/python'),str(Path(__file__).resolve()),'--phase','yolo','--route',str(b)]),('cpi',[str(W/'.venvs/parser-legacy-cu113/bin/python'),str(b/'scripts/worker_wrapper.py'),'run_cpi.py'])]:
        idle();start=time.perf_counter()
        with (b/'logs'/(name+'.log')).open('x') as f:
            try:done=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=c['first_cohort']['engineering']['worker_timeout_seconds']);status=done.returncode
            except subprocess.TimeoutExpired:status='TIMEOUT'
        processes.append({'stage':name,'command':cmd,'exit_code':status,'cold_process_wall_seconds_not_benchmark':time.perf_counter()-start});(b/'PROCESS_LOG.json').write_text(json.dumps(processes,indent=2))
        print(name,status,flush=True)
        if status!=0:raise RuntimeError('Engineering worker failed; see retained logs; no automatic model retry')
    verify(b)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['all','yolo'],default='all');parser.add_argument('--route',type=Path);a=parser.parse_args()
    if a.phase=='all':all_phases()
    else:yolo(a.route)
