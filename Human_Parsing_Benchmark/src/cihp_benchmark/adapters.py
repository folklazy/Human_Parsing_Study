"""Isolated native API adapters; no GT inputs, no architecture or threshold tuning."""
from pathlib import Path
import importlib,sys
import numpy as np

def box_from_mask(mask):
 y,x=np.where(mask);return [int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1] if len(x) else None

class NativeAdapter:
 def __init__(self,workspace,spec,output):
  import torch
  self.torch=torch;self.w=Path(workspace);self.spec=spec;self.output=Path(output);self.output.mkdir(parents=True,exist_ok=True);self.family=spec['family'];self.details={};np.int=int;np.float=float;np.bool=bool
  sys.path.insert(0,str(self.w/spec['source']));ck=self.w/spec['checkpoint']
  if self.family in ['M2FP','D2FP']:
   sys.path.insert(0,str(self.w/'.venvs/parser-build-tools/m2fp_ops'))
   from detectron2.config import get_cfg
   from detectron2.projects.deeplab import add_deeplab_config
   from detectron2.modeling import build_model
   mod=importlib.import_module(self.family.lower());modelmod=importlib.import_module(self.family.lower()+'.'+self.family.lower()+'_model')
   # Process-local, documented isolation: zero hidden GPU retry and no CPU fallback.
   modelmod.retry_if_cuda_oom=lambda fn:fn
   cfg=get_cfg();add_deeplab_config(cfg);getattr(mod,'add_'+self.family.lower()+'_config')(cfg);cfg.merge_from_file(str(self.w/spec['native_config']));cfg.MODEL.WEIGHTS=str(ck);cfg.MODEL.DEVICE='cuda';cfg.OUTPUT_DIR=str(output);cfg.freeze()
   self.model=build_model(cfg).float().eval();state=torch.load(ck,map_location='cpu')['model'];self.model.load_state_dict(state,strict=True);del state
   self.predictor=mod.ParsingWithTTA(cfg,self.model) if cfg.TEST.AUG.ENABLED else self.model;self.cfg=cfg;self.details={'resolved_config':cfg.dump(),'OOM_retry_wrapper':'process-local identity, no retry or CPUfallback','native_TTA':bool(cfg.TEST.AUG.ENABLED)}
  elif self.family=='QANet':
   sys.path.insert(0,str(self.w/'.venvs/parser-build-tools/QANet'))
   from qanet.core.config import get_cfg,infer_cfg
   from qanet.modeling.model_builder import Generalized_CNN
   from qanet.core.test import TestEngine
   cfg=get_cfg();cfg.merge_from_file(str(self.w/spec['native_config']));cfg.CKPT=str(output);cfg.DEVICE='cuda';cfg=infer_cfg(cfg);self.cfg=cfg;self.model=Generalized_CNN(cfg)
   state=torch.load(ck,map_location='cpu');state=state.get('model',state);self.model.load_state_dict({k[7:] if k.startswith('module.') else k:v for k,v in state.items()},strict=True);del state
   self.model.cuda().float().eval();self.engine=TestEngine(cfg,self.model);self.details={'resolved_config':cfg.dump(),'native_instance_support':False,'executed_shim_root':'.venvs/parser-build-tools/QANet'}
   if cfg.IMAGE_FORMAT!='rgb' or cfg.TEST.AFFINE_MODE!='roi_align':raise ValueError('QANet native RGB/ROI Align binding changed')
  elif self.family=='RP-R-CNN':
   import yaml
   compat=self.w/'Human_Parsing_MHPv2_Study/provenance/RUN_MANIFESTS/implementation-handoff-20261015T063548Z/native_smoke/scripts'
   sys.path.insert(0,str(compat))
   sys.path.insert(0,str(self.w/'.venvs/parser-build-tools/RP-R-CNN'))
   from rcnn.core.config import cfg,_merge_a_into_b,assert_and_infer_cfg
   from utils.collections import AttrDict
   from rcnn.modeling.model_builder import Generalized_RCNN
   from utils.net import convert_bn2affine_model
   cfg.immutable(False)
   with (self.w/spec['native_config']).open() as f:_merge_a_into_b(AttrDict(yaml.load(f,Loader=yaml.FullLoader)),cfg)
   cfg.CKPT=str(output);cfg.DEVICE='cuda';assert_and_infer_cfg(make_immutable=False);self.model=Generalized_RCNN(is_train=False);state=torch.load(ck,map_location='cpu');state=state.get('model',state);state={k[7:] if k.startswith('module.') else k:v for k,v in state.items()};missing=set(self.model.state_dict())-set(state)
   if not all(k in ['Norm.weight','Norm.bias'] or k.endswith(('.running_mean','.running_var','.num_batches_tracked')) for k in missing):raise ValueError('Undocumented RPR state keys '+str(missing))
   defaults=self.model.state_dict();state.update({k:defaults[k] for k in missing});self.model.load_state_dict(state,strict=True);del state,defaults
   if cfg.MODEL.BATCH_NORM=='freeze':self.model=convert_bn2affine_model(self.model)
   self.model.cuda().float().eval();self.cfg=cfg;self.details={'resolved_config':repr(cfg),'native_generated_constant_keys':sorted(missing),'executed_shim_root':'.venvs/parser-build-tools/RP-R-CNN','FP32_amp_shim':str((compat/'pilot_fp32_amp.py').relative_to(self.w))}
  elif self.family=='CPI-Parser':
   from mmcv import Config
   from mmdet.apis import init_detector
   cfg=Config.fromfile(str(self.w/spec['native_config']));cfg.model.test_cfg.save_root=str(output/'native');cfg.work_dir=str(output);self.cfg=cfg;self.model=init_detector(cfg,str(ck),device='cuda:0');self.model.float().eval();state=torch.load(ck,map_location='cpu')['state_dict'];self.model.load_state_dict(state,strict=True);del state
   self.details={'resolved_config':cfg.pretty_text,'native_score_threshold':self.model.bbox_head.test_cfg.get('score_thr'),'native_instance_support':True}
  else:raise ValueError('Adapter outside firstsix')
  if not all(p.dtype==torch.float32 for p in self.model.parameters()):raise ValueError('FP32 learned parameters required')
  self.details['parameters']=sum(p.numel() for p in self.model.parameters());self.details['native_identity_supported']=self.family!='QANet'

 def infer(self,rgb,source_jpeg,opportunities,detector_masks):
  torch=self.torch;h,w=rgb.shape[:2];native_global=None;extra={};geometry=[]
  with torch.no_grad():
   if self.family in ['M2FP','D2FP']:
    from detectron2.data.transforms import ResizeShortestEdge
    prepared=ResizeShortestEdge(self.cfg.INPUT.MIN_SIZE_TEST,self.cfg.INPUT.MAX_SIZE_TEST).get_transform(rgb).apply_image(rgb)
    prediction=self.predictor([{'image':torch.as_tensor(np.ascontiguousarray(prepared.transpose(2,0,1))),'height':h,'width':w}])[0]['parsing'];sem=prediction['semantic_outputs']
    if not torch.isfinite(sem).all():raise ValueError('Nonfinite semantic output')
    native_global=sem.argmax(0).cpu().numpy().astype('uint8');people=prediction['human_outputs'];scores=np.array([r['score'] for r in people],np.float32);owners=np.full((h,w),-1,np.int32)
    for i in sorted(range(len(people)),key=lambda i:(float(scores[i]),-i)):
     mask=people[i]['mask']
     if not torch.isfinite(mask).all():raise ValueError('Nonfinite human mask')
     owners[mask.detach().cpu().numpy()>0]=i
    extents=np.asarray([owners==i for i in range(len(people))],bool).reshape(-1,h,w);planes=np.asarray([np.where(extents[i],native_global,0) for i in range(len(people))],np.uint8).reshape(-1,h,w);boxes=np.array([box_from_mask(e) or [0,0,0,0] for e in extents],float).reshape(-1,4);geometry=[{'native_hw':list(prepared.shape[:2]),'whole_frame':True}]
   elif self.family=='QANet':
    from lib.data.structures.instance_box import InstanceBox
    planes=[]
    for op in opportunities:
     b=op['bbox'];target=InstanceBox(torch.tensor([[b[0],b[1],b[2]-b[0],b[3]-b[1]]],dtype=torch.float32),torch.tensor([0]),(w,h));target.convert(self.cfg.TEST.SCALE[0]/self.cfg.TEST.SCALE[1],1.0)
     result=self.engine([rgb],[target])['parsing'];mask=result['ims_parsings'][0][0].cpu().numpy()
     if mask.shape!=(h,w) or mask.dtype.kind not in 'ui' or np.any(mask>=20):raise ValueError('QANet labels/original-grid restoration failed')
     planes.append(mask);geometry.append({'native_rotated_roi':target.ori_bbox.tolist(),'external_bbox':b})
    extra['native_unowned_semantic_masks']=np.asarray(planes,np.uint8).reshape(-1,h,w);extents=np.asarray(detector_masks,bool).reshape(-1,h,w);planes=np.where(extents,extra['native_unowned_semantic_masks'],0);boxes=np.array([op['bbox'] for op in opportunities],float).reshape(-1,4);scores=np.array([op['score'] for op in opportunities],np.float32)
   elif self.family=='RP-R-CNN':
    from rcnn.core.test import im_detect_bbox,im_detect_parsing
    from rcnn.modeling.parsing_rcnn.inference import parsing_results
    pred_boxes,features=im_detect_bbox(self.model,[rgb[:,:,::-1].copy()]);pred=im_detect_parsing(self.model,pred_boxes,features)[0].to('cpu').resize((w,h));parsing=pred.get_field('parsing');parsing=parsing.cpu().numpy() if torch.is_tensor(parsing) else np.asarray(parsing);sem=pred.get_field('semseg') if pred.has_field('semseg') else None
    if torch.is_tensor(sem):sem=sem.cpu().numpy()
    planes=np.asarray(parsing_results(parsing,pred,sem),np.uint8).reshape(-1,h,w) if len(pred) else np.empty((0,h,w),np.uint8);extents=planes>0;boxes=pred.bbox.numpy();scores=pred.get_field('scores').cpu().numpy();geometry=[{'whole_frame':True,'internal_detector':'retained','native_box_restore':True}]
   else:
    from mmdet.apis import inference_detector
    import os
    previous=Path.cwd()
    try:os.chdir(Path(source_jpeg).parent);raw=inference_detector(self.model,Path(source_jpeg).name)
    finally:os.chdir(previous)
    boxes_all=np.vstack(raw).astype('float32');iid=Path(source_jpeg).stem;files=sorted((self.output/'native/val_parsing').glob(iid+'-*.png'),key=lambda p:int(p.stem.rsplit('-',1)[1]));planes=[]
    from .data import read_image
    for f in files:
     a,_=read_image(f,mask=True)
     if a.shape!=(h,w) or np.any(a>=20):raise ValueError('CPI native mask labels/dimensions invalid')
     planes.append(a)
    if len(files)!=len(boxes_all):raise ValueError('Native CPI file/box count mismatch')
    planes=np.asarray(planes,np.uint8).reshape(-1,h,w);extents=planes>0;boxes=boxes_all[:,:4];scores=boxes_all[:,4];geometry=[{'whole_frame':True,'internal_detector':'retained','source_decoder':'MMCV native JPEG/BGR'}]
  if planes.shape!=(len(scores),h,w) or boxes.shape!=(len(scores),4) or extents.shape!=planes.shape or not np.isfinite(scores).all() or not np.isfinite(boxes).all() or np.any(planes>=20):raise ValueError('Native output contract invalid')
  raw_count=len(scores);keep=[i for i,e in enumerate(extents) if e.any()];raw_arrays={'raw_native_person_semantic_masks':planes,'raw_native_person_extents':extents,'raw_native_person_scores':scores,'raw_native_bboxes_xyxy':boxes,**extra}
  if native_global is not None:raw_arrays['native_full_frame_semantic_mask']=native_global
  planes=planes[keep];extents=extents[keep];boxes=boxes[keep];scores=scores[keep];native_ids=[str(i) for i in keep]
  if self.family=='QANet':chosen=list(range(len(planes)));association=[{'prediction_index':i,'YOLO_opportunity_id':opportunities[keep[i]]['id']} for i in chosen]
  else:
   # Reuse verified prediction-only association, independently of GT/scoring.
   sys.path.insert(0,str(self.w/'Human_Parsing_MHPv2_Study'))
   from src.application_v2.evaluation import associate_native
   assoc=associate_native(opportunities,[{'id':native_ids[i],'bbox':b.tolist()} for i,b in enumerate(boxes)],.5)
   association=[{'prediction_index':native_ids.index(a['native_instance_id']),'YOLO_opportunity_id':a['source_opportunity_id']} for a in assoc['associations']];chosen=[a['prediction_index'] for a in association]
  arrays={'person_semantic_masks':planes[chosen],'person_extents':extents[chosen],'person_scores':scores[chosen],'bboxes_xyxy':boxes[chosen],'native_person_semantic_masks':planes,'native_person_extents':extents,'native_person_scores':scores,**raw_arrays}
  metadata={'geometry':geometry,'associations':association,'native_raw_entry_count':None if self.family=='QANet' else raw_count,'empty_native_extent_count':raw_count-len(keep),'final_person_count':len(chosen),'native_identity_supported':self.family!='QANet','native_indices_after_normalization':native_ids,'GT_used_in_prediction':False}
  return arrays,metadata
