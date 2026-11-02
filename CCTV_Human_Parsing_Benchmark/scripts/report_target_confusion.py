"""Derived per-target 2x2 diagnostics from accepted score JSON, not inference/rescoring.

One CSV + one aggregate figure, injected into the existing main Thai report.
Canonical predictions/GT/scorers/result indices/primary scores stay immutable.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, csv, hashlib, json, math
from collections import defaultdict

P = Path(__file__).resolve().parents[1]
W = P.parent
TARGETS = ('Hair', 'FaceDomain', 'Upper', 'Lower')
SHORT = {'QANet_CIHP_HRNetW48_512x384':'QANet', 'M2FP_R101_CIHP':'M2FP',
'D2FP_R101_CIHP':'D2FP', 'RPR_CIHP':'RP-R-CNN', 'CPI_R50_CIHP':'CPI R50',
'CPI_ConvNeXtB_CIHP':'CPI ConvNeXt-B', 'Sapiens2_0.4b':'Sapiens2 0.4B',
'Sapiens2_0.8b':'Sapiens2 0.8B', 'Sapiens2_1b':'Sapiens2 1B'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as file:
        for chunk in iter(lambda:file.read(4*1024**2),b''):h.update(chunk)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def ratio(a,b):return a/b if b else None


def binary_f1(tp,fp,fn):
    if any(type(value) is not int or value<0 for value in (tp,fp,fn)):
        raise ValueError('F1 requires nonnegative integer pixel counts')
    return ratio(2*tp,2*tp+fp+fn)


def face_domain_pixels(area, record):
    # REGION_UNCERTAIN carries Neck_pixels=null as an epistemic state. The
    # frozen scorer uses an empty *known-Neck mask* plus explicit uncertainty;
    # this does not assert that the anatomical Neck is absent.
    neck=record['Neck_pixels'];uncertainty=record['uncertainty_pixels']
    if record['Neck_status']=='REGION_UNCERTAIN':
        if neck is not None or uncertainty<=0 or record['FaceNeck_delivery_eligible']:
            raise ValueError('Uncertain Neck contract changed')
        excluded_neck=0
    elif record['Neck_status'] in ('VISIBLE_ANNOTATED','VERIFIED_NOT_VISIBLE'):
        if type(neck) is not int or neck<0 or not record['FaceNeck_delivery_eligible']:
            raise ValueError('Known Neck contract changed')
        excluded_neck=neck
    else:raise ValueError('Unreviewed Neck state')
    domain=area-excluded_neck-uncertainty
    if domain<=0:raise ValueError('Invalid Face domain')
    return domain


def summarize(rows):
    if not rows:raise ValueError('No eligible tasks')
    if any(any(type(r[key]) is not int or r[key]<0 for key in ('TP','FP','FN','valid_pixels','GT_pixels','prediction_pixels')) for r in rows):
        raise ValueError('Counts must be nonnegative integers')
    sums={key:sum(r[key] for r in rows) for key in ['TP','FP','FN','valid_pixels']}
    tp,fp,fn,area=(sums[k] for k in ['TP','FP','FN','valid_pixels'])
    tn=area-tp-fp-fn
    if tn<0 or any(r['valid_pixels']<r['TP']+r['FP']+r['FN'] for r in rows):
        raise ValueError('Negative TN/domain mismatch')
    if any(r['GT_pixels']!=r['TP']+r['FN'] or r['prediction_pixels']!=r['TP']+r['FP'] for r in rows):
        raise ValueError('Score support inconsistent')
    return dict(GT_parts=len(rows),GT_pixels=tp+fn,prediction_pixels=tp+fp,TP=tp,FP=fp,FN=fn,TN=tn,valid_pixels=area,
        pooled_recall=ratio(tp,tp+fn),missed_GT_fraction=ratio(fn,tp+fn),pooled_precision=ratio(tp,tp+fp),
        pooled_IoU=ratio(tp,tp+fp+fn),pooled_Dice=ratio(2*tp,2*tp+fp+fn),pooled_F1=binary_f1(tp,fp,fn),
        mean_part_IoU=sum(r['IoU'] for r in rows)/len(rows),
        zero_overlap_parts=sum(r['TP']==0 for r in rows),
        empty_prediction_parts=sum(r['prediction_pixels']==0 for r in rows),
        full_GT_coverage_parts=sum(r['FN']==0 for r in rows),
        exact_mask_parts=sum(r['FN']==0 and r['FP']==0 for r in rows),
        unmatched_parts=sum(r['unmatched'] for r in rows))


def load_verified(root,expected_images,observed):
    ledger=[json.loads(line) for line in (root/'FRAMES.jsonl').read_text().splitlines()]
    if len(ledger)!=len(expected_images) or {r['image_id'] for r in ledger}!=set(expected_images):
        raise ValueError('Scored-frame membership/duplicates')
    result=[]
    for line in ledger:
        path=root/(line['image_id']+'.json')
        if sha(path)!=line['record_sha256']:raise ValueError('Scored record hash changed')
        observed.append((str(path.relative_to(W)),line['record_sha256']))
        result.extend(read(path)['rows'])
    return result


def collect():
    index_path=P/'reports/CONTROLLED_ROI_FOUR_TARGET_INDEX.json'
    index=read(index_path);face_gt_path=P/index['GT_binding_location'];face_gt=read(face_gt_path)
    if index['status']!='FOUR_TARGET_EVALUATION_COMPLETE_ON_REVIEWED_GT' or list(index['models'])!=list(SHORT):
        raise ValueError('Incomplete accepted cohort')
    if sha(face_gt_path)!=index['frozen_inputs']['Face_GT_binding_sha256']:raise ValueError('Face GT drift')
    for filename,key in [('CONTROLLED_ROI_FACE_NECK_PROTOCOL.json','protocol_sha256'),
                         ('CONTROLLED_ROI_SCORING_PROTOCOL.json','projection_protocol_sha256')]:
        if sha(P/'configs'/filename)!=index['frozen_inputs'][key]:raise ValueError('Frozen protocol binding drift')
    base_gt_path=W/face_gt['base_GT_binding'];base_gt=read(base_gt_path)
    if sha(base_gt_path)!=face_gt['base_GT_binding_sha256']:raise ValueError('Parent GT drift')
    protected=[index_path,face_gt_path,base_gt_path,P/'configs/CONTROLLED_ROI_FACE_NECK_PROTOCOL.json',
        P/'configs/CONTROLLED_ROI_SCORING_PROTOCOL.json',P/'metrics/CONTROLLED_ROI_FOUR_TARGET_RESULTS.csv',
        P/'metrics/CONTROLLED_ROI_PER_TARGET.csv',P/'metrics/CONTROLLED_ROI_FACE_VIEWS.csv',
        P/'reports/MODEL_RECOMMENDATION.json',P/index['source_run']/'RESULTS.json']
    before={str(path.relative_to(W)):sha(path) for path in protected}
    if sha(P/index['source_run']/'RESULTS.json')!=index['source_results_sha256']:raise ValueError('Final results drift')
    frames={r['image_id']:r for r in base_gt['frames']}
    eligible={(r['image_id'],r['person_id'],r['target']) for r in base_gt['part_records'] if r['eligible'] and r['target'] in ('Hair','Upper','Lower')}
    faces={(r['image_id'],r['person_id']):r for r in face_gt['records'] if r['disposition']=='ELIGIBLE'}
    if len(frames)!=90 or len(eligible)!=269 or len(faces)!=21:raise ValueError('GT population changed')
    rows=[];record_hashes=[];example=None
    for model,accepted in index['models'].items():
        if accepted['status']!='COMPLETE_ON_REVIEWED_GT' or not accepted['prior_prediction_strict_complete']:
            raise ValueError('Incomplete model')
        face_root=P/index['source_run']/model
        non_path=W/accepted['source_non_Face_metrics_path']
        for path,digest in [(face_root/'METRICS.json',accepted['canonical_metrics_sha256']),(non_path,accepted['source_non_Face_metrics_sha256'])]:
            if sha(path)!=digest:raise ValueError('Canonical metrics hash changed')
            before[str(path.relative_to(W))]=digest
        tasks=defaultdict(list);seen=set()
        for r in load_verified(non_path.parent,frames,record_hashes):
            if not r['eligible'] or r['target'] not in ('Hair','Upper','Lower'):continue
            key=(r['image_id'],r['person_id'],r['target'])
            if key not in eligible or key in seen:raise ValueError('Non-Face eligibility/duplicate')
            seen.add(key)
            width,height=frames[r['image_id']]['original_wh']
            tasks[r['target']].append(dict(**r,valid_pixels=width*height,unmatched=r['detector_miss']))
        if seen!=eligible:raise ValueError('Non-Face membership')
        seen=set()
        for r in load_verified(face_root,{key[0] for key in faces},record_hashes):
            key=(r['image_id'],r['person_id'])
            if key not in faces or key in seen:raise ValueError('Face membership/duplicate')
            seen.add(key);gt=faces[key];width,height=frames[r['image_id']]['original_wh']
            domain=face_domain_pixels(width*height,gt)
            tasks['FaceDomain'].append(dict(**r['FaceDomain'],valid_pixels=domain,unmatched=r['detector_unmatched']))
        if seen!=set(faces):raise ValueError('Missing Face task')
        for target in TARGETS:
            result=summarize(tasks[target]);canonical=accepted['FaceDomain'] if target=='FaceDomain' else accepted['non_Face_targets'][target]
            for field in ['GT_parts','GT_pixels','prediction_pixels','TP','FP','FN']:
                if result[field]!=canonical[field]:raise ValueError('Canonical pooled statistic mismatch')
            for field in ['mean_part_IoU','pooled_IoU','pooled_Dice']:
                if not math.isclose(result[field],canonical[field],rel_tol=0,abs_tol=1e-14):raise ValueError('Canonical metric mismatch')
            rows.append(dict(model_id=model,target=target,**result))
            if model=='Sapiens2_1b' and target=='Hair':example=dict(result)
        expected=sum(row['mean_part_IoU'] for row in rows if row['model_id']==model)/4
        if not math.isclose(expected,accepted['primary'],rel_tol=0,abs_tol=1e-14):raise ValueError('Primary score changed')
    for target in TARGETS:
        domains={(r['GT_parts'],r['GT_pixels'],r['valid_pixels']) for r in rows if r['target']==target}
        if len(domains)!=1:raise ValueError('Model-dependent evaluation domain')
    audit=dict(status='DERIVED_REPORTING_ONLY_COMPLETE',model_calls=0,prediction_masks_read=0,
        scored_JSON_records=len(record_hashes),selected_tasks=9*290,protected_hashes=before,
        score_records_digest=hashlib.sha256(json.dumps(record_hashes,separators=(',',':')).encode()).hexdigest(),
        source_index_sha256=sha(index_path),script_sha256=sha(__file__),example=example)
    return rows,audit


def plot(rows,path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    models=list(dict.fromkeys(r['model_id'] for r in rows));lookup={(r['model_id'],r['target']):r for r in rows}
    figure,axes=plt.subplots(len(models),4,figsize=(17,26))
    for i,model in enumerate(models):
        for j,target in enumerate(TARGETS):
            ax=axes[i,j];r=lookup[model,target]
            counts=np.array([[r['TP'],r['FN']],[r['FP'],r['TN']]],dtype=np.int64)
            normalized=counts/counts.sum(1)[:,None]*100
            ax.imshow(normalized,vmin=0,vmax=100,cmap='Blues',aspect='auto')
            for y in range(2):
                for x in range(2):
                    name=[['TP','FN'],['FP','TN']][y][x]
                    ax.text(x,y,f"{name} {counts[y,x]:,}\n{normalized[y,x]:.2f}%",ha='center',va='center',
                        color='white' if normalized[y,x]>55 else '#152238',fontsize=8)
            ax.set_title(('Face domain' if target=='FaceDomain' else target)+f" | n={r['GT_parts']}",fontsize=10)
            ax.set_xticks([0,1],['Pred target','Pred not-target'],fontsize=7)
            ax.set_yticks([0,1],['GT target','GT not-this-part'],fontsize=7)
            if j==0:ax.set_ylabel(SHORT[model],fontsize=12,fontweight='bold',labelpad=11)
    figure.suptitle('CCTV 90 | 9 models x 4 selected-part binary confusion matrices\nCell = pooled pixel count + row-normalized %. Different target domains; no full-scene accuracy claim.',fontsize=14,y=.998)
    figure.tight_layout(rect=[0,0.018,1,.98],h_pad=1.1,w_pad=1.6)
    figure.text(.5,.004,'Rows = GT; columns = prediction. TN is a derived task-domain complement and dominates the grid: do not use pixel accuracy. Hair61 / Face21 / Upper112 / Lower96.',ha='center',fontsize=9)
    path.parent.mkdir(exist_ok=True,parents=True);figure.savefig(path,dpi=150);plt.close(figure)


def f1_section(rows):
    lookup={(r['model_id'],r['target']):r for r in rows}
    lines=['### F1 score แยก 4 คลาสต่อโมเดล','','**หนึ่งโมเดลมี F1 สี่ค่า**: Hair / Face-domain / Upper / Lower หน่วย % ตารางนี้เป็น **pixel-level pooled binary F1 ต่อ target** รวม TP/FP/FN จาก eligible person-part tasks ของ target นั้นก่อนคำนวณ ไม่ใช่ person-detection F1 หรือการเฉลี่ย F1 รายคน','',
        '| Model | Hair F1 % | Face-domain F1 % | Upper F1 % | Lower F1 % |',
        '|---|---:|---:|---:|---:|']
    for model in SHORT:
        scores=[lookup[model,t]['pooled_F1'] for t in TARGETS]
        lines.append('| '+SHORT[model]+' | '+' | '.join('null' if x is None else f'{100*x:.3f}' for x in scores)+' |')
    lines += ['', '| Metric ต่อคลาส | สูตรจาก pooled counts | ตอบคำถามอะไร |',
        '|---|---|---|',
        '| Precision | TP/(TP+FP) | พิกเซลที่โมเดลระบุว่าเป็นคลาสนี้ถูกต้องเท่าไร; ลงโทษการทำนายเกิน |',
        '| Recall | TP/(TP+FN) | เก็บพิกเซล GT ของคลาสนี้ได้เท่าไร; ลงโทษส่วนที่หายไป |',
        '| F1 | 2TP/(2TP+FP+FN) | สมดุล Precision กับ Recall; เท่ากับ harmonic mean 2PR/(P+R) เมื่อ P/R และตัวหารนิยามได้ |', '',
        'ใช้ [นิยาม F1 มาตรฐาน](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html) คำนวณจาก integer counts ก่อนปัดเศษ ไม่คำนวณจาก P/R ที่ปัดเศษแล้ว สำหรับ binary masks ที่มี domain/aggregation เดียวกัน **F1 เท่ากับ pooled Dice ที่มีอยู่เดิม** จึงเพิ่มชื่อ pooled_F1 ใน CSV ให้ค้นได้ตรงคำถาม ไม่ใช่หลักฐานคุณภาพอีกชุดที่เป็นอิสระ และไม่เท่ากับ mean-part Dice หรือ mean-part IoU/Macro4 ในตารางหลัก', '',
        'ถ้ามี GT แต่ไม่มี target prediction: Recall=0, F1=0 ส่วน Precision=null เพราะไม่มี predicted support หากไม่มีทั้ง GT และ prediction จะให้ F1=null ตาม zero-denominator policy เดิม ซึ่งเป็นตัวเลือกของ protocol ไม่ใช่ค่า default ของ sklearn ชุดจริงนี้ทั้ง 36 model-target pairs มี GT และ prediction support จึงไม่มี null', '',
        'ตัวหาร GT parts คงเดิม: Hair61 / Face-domain21 / Upper112 / Lower96 เท่ากันข้ามโมเดล เก็บ missed/unmatched parts เป็น FN ตามเดิม ไม่มี model-specific ignore เพิ่ม Face ยังคงเป็น neck-excluded reference domain และ Upper/Lower ใช้ mapping เดิม การรวม counts ให้น้ำหนักตามขนาดส่วน จึงไม่ใช้ตาราง pooled F1 นี้แทนอันดับ mean-part IoU/Macro4 เดิม', '',
        'Precision และ Recall พร้อม F1 ของทุก model-target pair อยู่ในตารางรายคลาสถัดไป และ [CSV เดิม](../metrics/CONTROLLED_ROI_TARGET_CONFUSION.csv): pooled_precision / pooled_recall / pooled_F1 คอลัมน์ตัวเลขเป็นสัดส่วน 0–1 ส่วนตาราง Markdown แสดง %', '',
        'สร้างเฉพาะส่วน F1/P/R ซ้ำจาก aggregate CSV และ canonical index ที่อยู่บน public clone ได้ด้วย `python CCTV_Human_Parsing_Benchmark/scripts/report_target_confusion.py --f1-only --audit-dir CCTV_Human_Parsing_Benchmark/outputs/<fresh-audit-id>` ไม่ต้องมี weights, ภาพ หรือ prediction packets และไม่เปิด inference', '']
    return lines


def report_section(rows):
    section=['<!-- TARGET_CONFUSION_START -->','## Confusion matrix และการเก็บส่วนที่ต้องการครบแค่ไหน','',
        'อัปเดตจาก **สถิติที่ตรวจรับแล้ว** ของ CCTV ชุดล่าสุด 90 ภาพเท่านั้น ไม่มี inference หรือ rescore และไม่แก้ GT, mapping หรือคะแนนหลักเดิม ใช้ภาพเดียวรวม 36 binary matrices (9 โมเดล × 4 targets) และ CSV เดียวรวม 36 แถวพร้อมตัวหารและค่าก่อนปัดเศษ','',
        '[เปิดภาพ matrix ขนาดเต็ม](figures/CONTROLLED_ROI_TARGET_CONFUSION.png) · [CSV ตัวเลข/ตัวหาร/ส่วนที่พลาด](../metrics/CONTROLLED_ROI_TARGET_CONFUSION.csv)','','![36 binary confusion matrices](figures/CONTROLLED_ROI_TARGET_CONFUSION.png)','',
        '### อ่าน matrix และเข้าใจ domain','',
        '| GT / Prediction | เป็น target ของคนที่ประเมิน | ไม่เป็น target ของคนนั้น |','|---|---:|---:|',
        '| GT เป็น target | TP: พิกเซลที่เก็บถูก | FN: พิกเซล GT ที่พลาด |',
        '| GT ไม่เป็นส่วนนี้ของคนที่ประเมิน ภายใน V | FP: พิกเซลที่ทำนายเกิน | TN: ส่วนเติมเต็มของ domain |','',
        '**เหตุผลที่ใช้ 2×2 ต่อคลาส:** Hair 61 / Face 21 / Upper 112 / Lower 96 ส่วน ใช้คนที่มีสิทธิ์และพื้นที่ประเมินต่างกันตาม selected-person part task เดิม สถิติ binary ไม่บอกว่า Hair ที่พลาดถูกทำนายเป็น Face, Upper, BG หรือ OTHER อย่างละเท่าไร จึงสร้างตาราง cross-class 4×4 จาก TP/FP/FN นี้ไม่ได้ การตอบคำถามนั้นต้องอ่าน native planes ภายใต้ joint-domain protocol เพิ่มเติม ซึ่งยังไม่ได้ทำในรอบนี้','',
        'Hair/Upper/Lower ใช้พิกัดภาพต้นฉบับทั้งกริดต่อ eligible part ตาม scorer เดิม ส่วน Face ใช้ V = original grid − known own Neck − GT-only uncertainty โดย known occluder ยังเป็น valid negative กรณี Neck ไม่ทราบ ใช้ uncertainty ที่ระบุไว้ ไม่ตีความ unknown ว่าไม่มีคอ **TN = |V| − TP − FP − FN** เป็นส่วนเติมเต็มทางคณิตศาสตร์จาก dimensions และ GT counts ที่ตรึงแล้ว ไม่ใช่ annotation ยืนยันว่าฉากที่เหลือเป็น background จึงไม่ใช้ accuracy/specificity หรือ TN จำนวนมากอ้างว่าแยกทุกคนถูกครบ Negative ในที่นี้หมายถึง “ไม่ใช่ส่วนนี้ของคนที่กำลังประเมิน” ไม่ใช่ full-scene GT และการรวม person-part tasks อาจนับพิกัดภาพเดียวกันซ้ำ','',
        'สีในรูป normalize แยกแถว: แถว GT-target คือ Recall และ Miss fraction; แถว GT-not-this-part คือ FP/TN ต่อ negative-domain support แต่ละช่องแสดงจำนวนพิกเซลจริงด้วย ไม่ใช้สีแถวล่างหรือ pixel accuracy เลือกผู้ชนะ','',
        '### Metric มาจากไหน คำนวณอย่างไร และตอบอะไร','',
        '| ตัวชี้วัด | สูตร/ตัวหาร | ความหมายและข้อจำกัด | ที่มา |','|---|---|---|---|',
        '| Recall / GT coverage | ΣTP/(ΣTP+ΣFN) | เก็บพิกเซล GTได้กี่%; ไม่ลงโทษการทำนายเกิน และไม่ใช่%คนที่ตรวจครบ | [นิยาม Recall](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.recall_score.html) |',
        '| Miss fraction | ΣFN/(ΣTP+ΣFN)=1−Recall | พิกเซลส่วนที่ต้องการซึ่งหายไป; ไม่ใช่จำนวน person misses | ComplementของRecallบนdomainเดียวกัน |',
        '| Precision | ΣTP/(ΣTP+ΣFP) | พิกเซลที่ทำนายว่าเป็นส่วนนี้ถูกจริงเท่าไร; จำกัด selected-person/GT-reference domain | [นิยาม Precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_score.html) |',
        '| IoU / Jaccard | TP/(TP+FP+FN) ต่อpart | ลงโทษทั้งเก็บไม่ครบและทำนายเกิน | [นิยาม Jaccard](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.jaccard_score.html), [scorer counts](../scripts/controlled_roi_core.py) |',
        '| Dice / binary F1 | 2TP/(2TP+FP+FN) | overlapอีกสเกลหนึ่งจากcountsเดียวกัน; ไม่ใช่หลักฐานอิสระเพิ่ม และไม่เท่ากับperson-detectionF1 | [นิยาม F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html) |',
        '| Mean-part IoU / Macro4 เดิม | mean_i IoU_i ใน target แล้วเฉลี่ย 4 targets เท่ากัน 25% | แต่ละ part น้ำหนักเท่ากันก่อนรวม targets; **ยังเป็นเกณฑ์หลักเดิม** | [protocol R2](../configs/CONTROLLED_ROI_FACE_NECK_PROTOCOL.json), [aggregate/macro source](../scripts/face_neck_evaluation.py) |',
        '| Pooled IoU / Dice | รวมintegercountsทุกpartก่อนratio | partใหญ่มีน้ำหนักมาก จึงต่างจากmean-part; ไม่เอาpooledRecall/IoUมาเปลี่ยนอันดับหลัก | CSVและformulaเดียวกัน |',
        '| Zero overlap / Full GT coverage | นับ TP_i=0 / FN_i=0 จาก eligible parts | ส่วนที่ไม่ทับ GT เลย / เก็บ GT pixels ครบ; **FN=0 ยังมี FP ได้** จึงไม่เท่ากับ mask ถูกทั้งหมด | Diagnostics จาก counts เดิม ไม่มีตั้ง threshold เพิ่มภายหลัง |',
        '| Empty prediction / Exact mask | นับ prediction_pixels_i=0 / (FP_i=0 และ FN_i=0) | ไม่มี target prediction / ทุกพิกเซลตรง reference; ไม่ใช่ execution failure หรือเกณฑ์ผ่านการใช้งาน | Diagnostics จาก counts เดิม |',
        '| Unmatched parts | นับ detector_miss หรือ detector_unmatched ของ accepted task rows | GT part ที่ไม่มี assigned candidate; อาจเกิดจากไม่มี detection หรือ assignment competition ไม่ใช่จำนวนคนทั้งฉากที่ detector พลาด | [non-Face scorer](../scripts/controlled_roi_evaluation.py), [Face scorer](../scripts/face_neck_evaluation.py) |','',
        'นิยาม matrix อิง [official confusion-matrix reference](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html) โดยเรียง labels [target, not-target] จึงเป็น [[TP,FN],[FP,TN]] คำนวณจาก canonical integer counts โดยตรง ไม่ได้เรียก sklearn มา rescore หากตัวหารเป็นศูนย์จะให้ null เพราะไม่มี support (CSV ใช้คำว่า null) ไม่แทนด้วยศูนย์อัตโนมัติ; ชุดนี้ทุก target มี positive GT การรวม native classes ใช้ union ตาม mapping เดิมแล้วจึงนับพิกเซล ไม่เฉลี่ย IoU ของคลาสย่อย','',
        '### รายโมเดลและรายคลาส: เก็บได้/พลาด/เกิน','',
        'ร้อยละในตารางเป็น **pooled pixels** จากทุก eligible part ของ target จึงมีน้ำหนักตามขนาดส่วน ต่างจาก mean-part IoU ในตารางหลัก “ไม่ทับเลย” คือ TP=0 รวมกรณี empty/wrong-place และ unmatched GT ซึ่งไม่ใช่ execution failure ส่วน “เก็บ GT ครบ” คือ FN=0 เท่านั้น CSV มี empty-prediction, exact-mask, unmatched counts และ TN เพิ่มเติม','']
    section += f1_section(rows)
    for target in TARGETS:
        chosen=[r for r in rows if r['target']==target];n=chosen[0]['GT_parts'];support=chosen[0]['GT_pixels']
        section += [f"#### {target}: n={n} parts, GT support={support:,} pixels",'',
            '| Model | Recall % | พลาด % | Precision % | F1 % | TP px | FN px | FP px | ไม่ทับเลย/ทั้งหมด | เก็บ GT ครบ/ทั้งหมด |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for r in chosen:
            section.append(f"| {SHORT[r['model_id']]} | {r['pooled_recall']*100:.3f} | {r['missed_GT_fraction']*100:.3f} | {r['pooled_precision']*100:.3f} | {r['pooled_F1']*100:.3f} | {r['TP']:,} | {r['FN']:,} | {r['FP']:,} | {r['zero_overlap_parts']}/{n} | {r['full_GT_coverage_parts']}/{n} |")
        section.append('')
    section += ['### สรุปสิ่งที่ตอบได้จาก diagnostics','']
    for target in TARGETS:
        chosen=[r for r in rows if r['target']==target];leader=max(chosen,key=lambda r:r['pooled_recall']);prec=max(chosen,key=lambda r:r['pooled_precision'])
        section.append(f"- **{target}:** pooled GT coverage สูงสุด {SHORT[leader['model_id']]} {leader['pooled_recall']*100:.3f}% (พลาด {leader['FN']:,}/{leader['GT_pixels']:,} px); pooled precision สูงสุด {SHORT[prec['model_id']]} {prec['pooled_precision']*100:.3f}% ค่านี้อธิบาย coverage/overprediction ไม่ได้เปลี่ยนอันดับ mean-part IoU เดิม")
    example=next(r for r in rows if r['model_id']=='Sapiens2_1b' and r['target']=='Hair')
    section += ['',f"**ตัวอย่างอ่านผลผมของ Sapiens2 1B:** เก็บถูก {example['TP']:,}/{example['GT_pixels']:,} พิกเซล = Recall {example['pooled_recall']*100:.3f}% พลาด {example['FN']:,} พิกเซล = {example['missed_GT_fraction']*100:.3f}% และทำนายเกิน {example['FP']:,} พิกเซล จึงได้ Precision {example['pooled_precision']*100:.3f}% แต่ยังมี {example['zero_overlap_parts']}/{example['GT_parts']} ส่วนที่ไม่ทับ GT เลย (ในนั้นเป็น unmatched {example['unmatched_parts']} ส่วน) ขณะที่ mean-part IoU = {example['mean_part_IoU']*100:.3f}% คะแนน pooled ที่สูงไม่ใช่หลักฐานว่าเก็บผมครบทุกคน เพราะส่วนใหญ่มีน้ำหนักมากกว่าส่วนเล็กใน pooled metric และ Recall ไม่ลงโทษ FP",'']
    section += ['','Detector-unmatchedคงเดิมร่วมทุกระบบ: Hair5/61,Face2/21,Upper15/112,Lower14/96; GTเหล่านี้ยังอยู่ในdenominatorและถูกคิดFN ไม่ตัดภาพล้มเหลวเพื่อช่วยคะแนน. Zero-overlapที่มากกว่านี้ยังอาจเกิดจากsemanticempty/wrongpart/ownership ไม่ควรเรียกทุกกรณีว่าYOLOไม่เห็นคน.','',
        'คำตอบว่า “ทำผมครบไหม” จึงต้องอ่าน Recallคู่Precision/IoUและจำนวนส่วนที่ไม่ทับเลย; coverage100%อย่างเดียวอาจเป็นmaskใหญ่เกินจริง. ยังไม่มีเกณฑ์ผ่านแบบabsolute และไม่เปลี่ยนน้ำหนักเพื่อให้โมเดลใดชนะ. การไม่มีpartใดexact-maskไม่ได้หมายถึงทุกpartใช้งานไม่ได้—เกณฑ์exactคือทุกpixelตรงreference.','',
        'Faceยังเป็น21/35referencecontoursที่ผ่านagent-assistedreview ไม่ใช่expertgold; SapiensFace_Neckcandidateยังคงเดิมบนneck-excludeddomain. Diagnosticsไม่สร้างstrictFace-only/Dress/Neck-onlycapabilityขึ้นมา และไม่ใช้พิสูจน์training/architectureเพียงอย่างเดียว. Matrixเพิ่มหลังเห็นผลแล้ว เป็นpost-hoc reporting ไม่ใช่preregisteredconfirmatoryanalysis. ไม่เพิ่มGPU/CPUfullrescore/GTreview/mappingtuning.','',
        'หลักฐานการสร้างภาพ/CSV และการตรวจว่า canonical results คงเดิม: [STUDY_STATE.json](../STUDY_STATE.json) → target_confusion_reporting เก็บเฉพาะ aggregate counts บน public Git ไม่มีภาพ CCTV, person IDs, annotation vertices หรือ prediction packets','',
        'สร้างซ้ำจาก private accepted scoring artifacts ที่ตรวจรับแล้วได้ด้วย environment เดิมที่มี matplotlib (ไม่โหลดโมเดล): `python CCTV_Human_Parsing_Benchmark/scripts/report_target_confusion.py --audit-dir CCTV_Human_Parsing_Benchmark/outputs/<fresh-audit-id>` คำสั่งสร้างเฉพาะภาพ/CSV/ส่วน diagnostics ในรายงานนี้ และเก็บ verification ใน private outputs; public clone ไม่มี private inputs จึงยังสร้างซ้ำไม่ได้จนกว่าจะจัดเตรียม artifacts ที่มีสิทธิ์เข้าถึง','<!-- TARGET_CONFUSION_END -->']
    return '\n'.join(section)+'\n'


def update_report(rows):
    report=P/'reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md'
    text=report.read_text();start='<!-- TARGET_CONFUSION_START -->';end='<!-- TARGET_CONFUSION_END -->'
    section=report_section(rows)
    if start in text:
        before,tail=text.split(start,1);_,after=tail.split(end,1)
        text=before+section.rstrip('\n')+after
    else:text=text.rstrip()+'\n\n'+section
    report.write_text(text)
    return report


def f1_only(audit_dir):
    """Use published sufficient statistics, not raw predictions or GT masks."""
    audit_dir.mkdir(parents=True,exist_ok=False)
    source=P/'metrics/CONTROLLED_ROI_TARGET_CONFUSION.csv'
    index_path=P/'reports/CONTROLLED_ROI_FOUR_TARGET_INDEX.json'
    index=read(index_path);state=read(P/'STUDY_STATE.json')
    if sha(index_path)!=state['target_confusion_reporting']['source_index_sha256']:
        raise ValueError('Canonical source index changed')
    protected=[index_path,P/'reports/figures/CONTROLLED_ROI_TARGET_CONFUSION.png',
        P/'metrics/CONTROLLED_ROI_FOUR_TARGET_RESULTS.csv',P/'metrics/CONTROLLED_ROI_PER_TARGET.csv',
        P/'metrics/CONTROLLED_ROI_FACE_VIEWS.csv',P/'reports/MODEL_RECOMMENDATION.json',
        P/'configs/CONTROLLED_ROI_FACE_NECK_PROTOCOL.json',P/'configs/CONTROLLED_ROI_SCORING_PROTOCOL.json']
    before={str(path.relative_to(W)):sha(path) for path in protected};source_sha=sha(source)
    with source.open(newline='') as file:
        reader=csv.DictReader(file);fields=list(reader.fieldnames);original=list(reader)
    if [(r['model_id'],r['target']) for r in original]!=[(m,t) for m in SHORT for t in TARGETS]:
        raise ValueError('Expected nine models x four targets in frozen order')
    integer_fields={'GT_parts','GT_pixels','prediction_pixels','TP','FP','FN','TN','valid_pixels',
        'zero_overlap_parts','empty_prediction_parts','full_GT_coverage_parts','exact_mask_parts','unmatched_parts'}
    typed=[];output=[]
    for raw in original:
        row={k:(v if k in ('model_id','target') else int(v) if k in integer_fields else None if v=='null' else float(v)) for k,v in raw.items()}
        accepted=index['models'][row['model_id']]
        if accepted['status']!='COMPLETE_ON_REVIEWED_GT':raise ValueError('Incomplete accepted model')
        canonical=accepted['FaceDomain'] if row['target']=='FaceDomain' else accepted['non_Face_targets'][row['target']]
        for key in ['GT_parts','GT_pixels','prediction_pixels','TP','FP','FN']:
            if row[key]!=canonical[key]:raise ValueError('Counts differ from canonical target statistics')
        for key in ['pooled_Dice','pooled_IoU','mean_part_IoU']:
            if not math.isclose(row[key],canonical[key],rel_tol=0,abs_tol=1e-14):raise ValueError('Canonical metric changed')
        tp,fp,fn=(row[k] for k in ['TP','FP','FN']);score=binary_f1(tp,fp,fn)
        if not math.isclose(score,row['pooled_Dice'],rel_tol=0,abs_tol=1e-14):raise ValueError('Binary F1/Dice mismatch')
        for key,value in [('pooled_precision',ratio(tp,tp+fp)),('pooled_recall',ratio(tp,tp+fn))]:
            if row[key]!=value:raise ValueError('Stored precision/recall mismatch')
        if 'pooled_F1' in row and row['pooled_F1']!=score:raise ValueError('Existing F1 changed')
        row['pooled_F1']=score;typed.append(row);output.append(dict(raw,pooled_F1='null' if score is None else repr(score)))
    if 'pooled_F1' not in fields:fields.append('pooled_F1')
    with source.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(output)
    report=update_report(typed)
    if not all(sha(W/path)==digest for path,digest in before.items()):raise ValueError('Protected artifact changed')
    audit=dict(status='PER_CLASS_PIXEL_PRF_COMPLETE',created_utc=datetime.now(timezone.utc).isoformat(),
        model_count=9,targets=list(TARGETS),model_target_pairs=36,model_calls=0,prediction_masks_read=0,
        source_index_sha256=sha(index_path),previous_CSV_sha256=source_sha,CSV_sha256=sha(source),
        original_columns_preserved=True,protected_hashes=before,report_sha256=sha(report),script_sha256=sha(__file__),
        pooled_F1_equals_existing_pooled_Dice=True,undefined_F1_count=sum(r['pooled_F1'] is None for r in typed))
    (audit_dir/'VERIFICATION.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k!='protected_hashes'},indent=2))


def main(audit_dir):
    audit_dir.mkdir(parents=True,exist_ok=False)
    rows,audit=collect()
    output=P/'metrics/CONTROLLED_ROI_TARGET_CONFUSION.csv'
    with output.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader()
        writer.writerows({k:('null' if v is None else v) for k,v in row.items()} for row in rows)
    figure=P/'reports/figures/CONTROLLED_ROI_TARGET_CONFUSION.png';plot(rows,figure)
    update_report(rows)
    for name,digest in audit['protected_hashes'].items():
        if sha(W/name)!=digest:raise ValueError('Protected canonical artifact changed')
    audit.update(created_utc=datetime.now(timezone.utc).isoformat(),CSV_sha256=sha(output),figure_sha256=sha(figure),
        figure_bytes=figure.stat().st_size,model_count=9,targets=list(TARGETS),rows=36,
        domain_TN='selected-person part-task complement, not full-scene background truth')
    (audit_dir/'VERIFICATION.json').write_text(json.dumps(audit,indent=2))
    print(json.dumps({k:v for k,v in audit.items() if k not in ['protected_hashes','example']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--audit-dir',type=Path,required=True)
    parser.add_argument('--f1-only',action='store_true',help='Use aggregate CSV/index only; preserve the existing figure')
    args=parser.parse_args()
    (f1_only if args.f1_only else main)(args.audit_dir)
