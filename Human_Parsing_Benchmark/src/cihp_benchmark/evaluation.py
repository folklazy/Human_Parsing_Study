"""Full native-label system evaluation; not official parsing AP/PCP."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
from .data import LABELS

def compose(planes,scores,shape):
 out=np.zeros(shape,np.uint8)
 for j in sorted(range(len(planes)),key=lambda i:(float(scores[i]),-i)):
  out=np.where(planes[j]>0,planes[j],out)
 return out

def histogram(gt,pred):
 if gt.shape!=pred.shape or pred.dtype.kind not in 'ui' or np.any(pred>=20):raise ValueError('Native semantic output contract invalid')
 valid=(gt>=0)&(gt<20)
 return np.bincount(20*gt[valid].astype(np.int64)+pred[valid],minlength=400).reshape(20,20)

def semantic_report(hist):
 h=np.asarray(hist,np.int64);tp=np.diag(h);union=h.sum(0)+h.sum(1)-tp
 # Reference M2FP CIHP evaluator includes all20 classes and uses epsilon, i.e.0 for empty union.
 iou=np.divide(tp,union,out=np.zeros(20,float),where=union>0)
 return {'mIoU_20_including_BG':float(iou.mean()),'mIoU_19_foreground':float(iou[1:].mean()),'IoU':iou.tolist(),'GT_pixel_support':h.sum(1).tolist(),'predicted_pixel_support':h.sum(0).tolist(),'union':union.tolist(),'pixel_accuracy':float(tp.sum()/h.sum()) if h.sum() else None,'absent_class_policy':'REFERENCE_EPSILON_ZERO_UNION_ZERO; support/union retained','labels':LABELS}

def match_masks(gt_masks,pred_masks,threshold):
 g,p=len(gt_masks),len(pred_masks)
 if not g or not p:return []
 ious=np.zeros((g,p))
 for i,a in enumerate(gt_masks):
  for j,b in enumerate(pred_masks):
   union=np.count_nonzero(a|b);ious[i,j]=np.count_nonzero(a&b)/union if union else 0
 eligible=ious>=threshold;utility=eligible*(min(g,p)+1)+ious*eligible
 rows,cols=linear_sum_assignment(-utility)
 return [(int(i),int(j),float(ious[i,j])) for i,j in zip(rows,cols) if eligible[i,j]]

def score_frame(category,human,planes,extents,scores,threshold=.5):
 planes=np.asarray(planes);extents=np.asarray(extents,dtype=bool)
 if planes.shape!=extents.shape or planes.ndim!=3 or planes.shape[1:]!=category.shape or len(scores)!=len(planes):raise ValueError('Person packet dimensions invalid')
 if planes.dtype.kind not in 'ui' or np.any(planes>=20) or not np.isfinite(scores).all():raise ValueError('Person packet class/score invalid')
 if any(not e.any() for e in extents):raise ValueError('Normalized person needs nonempty extent; retain raw empty entries separately')
 gids=[int(i) for i in np.unique(human) if i>0];gm=[human==i for i in gids];pairs=match_masks(gm,extents,threshold);by_gt={i:j for i,j,_ in pairs};totalq=0.;gsem=0;valid=(category<20)&~((category>0)&(human==0));contam_num=contam_den=0
 for i,pid in enumerate(gids):
  gt=np.where(gm[i],category,0);ks=set(np.unique(gt[valid]))-{0}
  if not ks:continue
  gsem+=1
  if i not in by_gt:continue
  pred=planes[by_gt[i]];ks|=set(np.unique(pred[valid]))-{0};q=[]
  for c in ks:
   a=(gt==c)&valid;b=(pred==c)&valid;u=(a|b).sum();q.append(float((a&b).sum()/u) if u else 0.)
  totalq+=sum(q)/len(q)
  mask=(pred>0)&valid;contam_den+=int(mask.sum());contam_num+=int((mask&(human>0)&(human!=pid)).sum())
 tp=len(pairs);fp=len(planes)-tp;fn=len(gids)-tp
 return {'histogram':histogram(category,compose(planes,scores,category.shape)).tolist(),'G_loc':len(gids),'G_sem':gsem,'TP':tp,'FP':fp,'FN':fn,'Q_numerator':totalq,'Q_person_sem_GT':totalq/gsem if gsem else None,'extent_F1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,'contamination_numerator_matched':contam_num,'contamination_denominator_matched':contam_den,'contamination_matched':contam_num/contam_den if contam_den else None,'matches':[{'gt_person_id':gids[i],'prediction_index':j,'mask_IoU':v} for i,j,v in pairs]}

def read_packet(directory):
 d=Path(directory);meta=json.loads((d/'packet.json').read_text());arrays=np.load(d/'prediction.npz',allow_pickle=False)
 return meta,{k:arrays[k].copy() for k in arrays.files}
