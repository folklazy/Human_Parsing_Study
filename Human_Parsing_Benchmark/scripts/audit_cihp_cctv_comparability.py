"""Read-only audit of accepted aggregate records; never imports inference/scorers.

Writes a derived sensitivity CSV and evidence JSON. This is not a new benchmark.
"""
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

W = Path(__file__).resolve().parents[2]
H = W / 'Human_Parsing_Benchmark'
C = W / 'CCTV_Human_Parsing_Benchmark'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def rows(p): return list(csv.DictReader(p.open()))
def require(ok, message):
    if not ok: raise ValueError(message)
def close(a,b): require(math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-12), 'Arithmetic mismatch')

def main():
    paths = [H/'manifests/CIHP_COMMON_RESULT_INDEX.json', H/'metrics/cpi-common-c4p-20261030/COMMON_SUMMARY.csv',
             H/'metrics/cpi-common-c4p-20261030/PER_TARGET.csv', C/'reports/CONTROLLED_ROI_FOUR_TARGET_INDEX.json',
             C/'metrics/CONTROLLED_ROI_FOUR_TARGET_RESULTS.csv', C/'metrics/CONTROLLED_ROI_TARGET_CONFUSION.csv',
             H/'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json', C/'configs/CONTROLLED_ROI_SCORING_PROTOCOL.json',
             C/'configs/CONTROLLED_ROI_FACE_NECK_PROTOCOL.json', H/'src/common_view/core.py',
             H/'src/common_view/sapiens_route.py', C/'scripts/controlled_roi_models.py',
             C/'scripts/sapiens_input_variants.py', C/'scripts/controlled_roi_evaluation.py',
             C/'scripts/face_neck_evaluation.py', C/'scripts/controlled_roi_core.py']
    before={str(p.relative_to(W)):sha(p) for p in paths}
    ci=read(paths[0]); cs=rows(paths[1]); ct=rows(paths[2]); vi=read(paths[3]); vs=rows(paths[4]); vc=rows(paths[5])
    require(len(cs)==len(vs)==len(ci['models'])==len(vi['models'])==9,'Nine systems required')
    order=[r['model_id'] for r in cs]
    require(order==[r['model_id'] for r in vs]==list(vi['models']),'Roster/order mismatch')
    require(sha(paths[6])==ci['protocol_sha256'],'CIHP protocol drift')
    require(sha(paths[7])==vi['frozen_inputs']['projection_protocol_sha256'],'CCTV projection drift')
    require(sha(paths[8])==vi['frozen_inputs']['protocol_sha256'],'CCTV Face protocol drift')
    canonical=[]
    for m in ci['models']:
        require(m['complete']==m['expected']==5000 and m['exact_membership'],'Incomplete CIHP')
        p=H/m['canonical_metrics_path']; require(sha(p)==m['canonical_metrics_sha256'],'Canonical CIHP metrics drift')
        canonical.append({'model_id':m['model_id'],'path':str(p.relative_to(W)),'sha256':sha(p)})
    out=[]
    names=[('Hair','Hair','Hair_IoU','Hair_mean_part_IoU'),('Face','FaceDomain','Face_CIHP_reference_IoU','Face_domain_mean_part_IoU'),('Upper','Upper','Upper_non_Dress_IoU','Upper_mean_part_IoU'),('Lower','Lower','Lower_non_Dress_IoU','Lower_mean_part_IoU')]
    supports={}
    for cr,vr in zip(cs,vs):
        mid=cr['model_id']; require(int(vr['prediction_images'])==90 and int(vr['ROIs'])==130,'CCTV population mismatch')
        require(vi['models'][mid]['prior_prediction_strict_complete'],'CCTV not accepted')
        cm=[];vm=[];vp=[]
        for label,target,ck,vk in names:
            a=[r for r in vc if r['model_id']==mid and r['target']==target];require(len(a)==1,'Duplicate/missing target')
            a=a[0]; tp,fp,fn,tn,area=[int(a[k]) for k in ('TP','FP','FN','TN','valid_pixels')]
            require(min(tp,fp,fn,tn)>=0 and tp+fp+fn+tn==area,'Invalid counts/domain')
            require(tp+fn==int(a['GT_pixels']) and tp+fp==int(a['prediction_pixels']),'Support mismatch')
            close(tp/(tp+fp+fn),a['pooled_IoU']); close(2*tp/(2*tp+fp+fn),a['pooled_F1']); close(a['mean_part_IoU'],vr[vk])
            supports.setdefault(target,(int(a['GT_parts']),int(a['GT_pixels']),area))
            require(supports[target]==(int(a['GT_parts']),int(a['GT_pixels']),area),'Model-specific GT domain')
            target_id={'Face':1,'Hair':2,'Upper':3,'Lower':4}[label]
            b=[r for r in ct if r['model_id']==mid and int(r['target_id'])==target_id];require(len(b)==1,'CIHP target mismatch');b=b[0]
            gt,pred,union=[int(b[k]) for k in ('GT_support_pixels','prediction_support_pixels','union_pixels')]
            intersection=gt+pred-union;require(0<=intersection<=min(gt,pred),'Invalid CIHP counts')
            close(intersection/union,cr[ck]);close(b['IoU'],cr[ck])
            supports.setdefault('CIHP_'+target,gt);require(supports['CIHP_'+target]==gt,'CIHP model-specific GT')
            # Index statistics are independent of the reporting CSV.
            accepted=vi['models'][mid]['FaceDomain'] if target=='FaceDomain' else vi['models'][mid]['non_Face_targets'][target]
            for k in ('TP','FP','FN'):require(int(a[k])==accepted[k],'CCTV index/statistics mismatch')
            cm.append(float(cr[ck]));vm.append(float(vr[vk]));vp.append(tp/(tp+fp+fn))
            out.append(dict(model_id=mid,target=label,CIHP_global_IoU=cm[-1],CCTV_mean_part_IoU=vm[-1],CCTV_pooled_person_part_IoU=vp[-1],CCTV_GT_parts=int(a['GT_parts']),CCTV_TP=tp,CCTV_FP=fp,CCTV_FN=fn,cross_dataset_delta_valid=False))
        close(sum(cm)/4,cr['C4P_mIoU4']);close(sum(vm)/4,vr['macro_mean_selected_part_IoU4'])
        out.append(dict(model_id=mid,target='Macro4',CIHP_global_IoU=sum(cm)/4,CCTV_mean_part_IoU=sum(vm)/4,CCTV_pooled_person_part_IoU=sum(vp)/4,CCTV_GT_parts='',CCTV_TP='',CCTV_FP='',CCTV_FN='',cross_dataset_delta_valid=False))
    for p in paths: require(sha(p)==before[str(p.relative_to(W))],'Input mutated')
    dest=H/'metrics/CIHP_CCTV_AGGREGATION_SENSITIVITY.csv'
    with dest.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(out[0]),lineterminator="\n");writer.writeheader();writer.writerows(out)
    evidence=dict(status='AGGREGATE_BINDINGS_AND_ARITHMETIC_PASS',created_utc=datetime.now(timezone.utc).isoformat(),
        models=9,target_rows=36,summary_rows=9,model_calls=0,mask_rescores=0,
        inputs=before,canonical_CIHP_metrics=canonical,shared_GT_supports=supports,
        output={'path':str(dest.relative_to(W)),'sha256':sha(dest)},
        limitations=['Accepted exact-membership audit reused, no fresh packet rehash','CCTV pooled counts are person-part tasks, not global semantic confusion','No attribution of cross-dataset difference to model architecture or one input factor','No new GPU readiness or controlled CIHP inference performed'])
    (H/'reports/CIHP_CCTV_COMPARABILITY_EVIDENCE.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({k:evidence[k] for k in ('status','models','target_rows','summary_rows','model_calls','mask_rescores')}))

if __name__=='__main__': main()
