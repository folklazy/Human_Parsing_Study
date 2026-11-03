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
    lines=['### F1 score แยก 4 คลาสต่อโมเดล','','**หนึ่งโมเดลมี F1 สี่ค่า** ได้แก่ Hair / Face-domain / Upper / Lower แสดงเป็น % โดยรวม TP/FP/FN ของส่วนที่ใช้ประเมินในแต่ละคลาสก่อนคำนวณ เรียกว่า pooled binary pixel F1 ไม่ใช่ F1 ของการตรวจจับบุคคลหรือค่าเฉลี่ย F1 รายคน','',
        '| โมเดล | Hair F1 (%) | Face-domain F1 (%) | Upper F1 (%) | Lower F1 (%) |',
        '|---|---:|---:|---:|---:|']
    for model in SHORT:
        scores=[lookup[model,t]['pooled_F1'] for t in TARGETS]
        lines.append('| '+SHORT[model]+' | '+' | '.join('null' if x is None else f'{100*x:.3f}' for x in scores)+' |')
    lines += ['', '| Metric ต่อคลาส | สูตรจาก pooled counts | ตอบคำถามอะไร |',
        '|---|---|---|',
        '| Precision | TP ÷ (TP + FP) | พิกเซลที่โมเดลระบุว่าเป็นคลาสนี้ถูกต้องเท่าไร; ลงโทษการทำนายเกิน |',
        '| Recall | TP ÷ (TP + FN) | เก็บพิกเซล GT ของคลาสนี้ได้เท่าไร; ลงโทษส่วนที่หายไป |',
        '| F1 | (2 × TP) ÷ (2 × TP + FP + FN) | สมดุล Precision กับ Recall; เป็นค่าเฉลี่ยฮาร์มอนิกของ Precision และ Recall หรือ 2 × Precision × Recall ÷ (Precision + Recall) เมื่อคำนวณตัวหารได้ |', '',
        'ใช้ [นิยาม F1 มาตรฐาน](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html) คำนวณจาก integer counts ก่อนปัดเศษ ไม่คำนวณจาก P/R ที่ปัดเศษแล้ว สำหรับ binary masks ที่มี domain/aggregation เดียวกัน **F1 เท่ากับ pooled Dice ที่มีอยู่เดิม** จึงเพิ่มชื่อ pooled_F1 ใน CSV ให้ค้นได้ตรงคำถาม ไม่ใช่หลักฐานคุณภาพอีกชุดที่เป็นอิสระ และไม่เท่ากับ mean-part Dice หรือ mean-part IoU/Macro4 ในตารางหลัก', '',
        'ถ้ามี GT แต่ไม่มีพิกเซลทำนายของคลาสนั้น: Recall=0 และ F1=0 ส่วน Precision=null เพราะไม่มี predicted support หากไม่มีทั้ง GT และ prediction จะให้ F1=null ตามกติกาตัวหารเป็นศูนย์เดิม ซึ่งเป็นตัวเลือกของ protocol ไม่ใช่ค่า default ของ sklearn ชุดจริงทั้ง 36 คู่โมเดล–คลาสมี GT และ prediction support จึงไม่มี null', '',
        'จำนวนส่วน GT ที่ใช้ประเมินคงเดิม: Hair 61 / Face-domain 21 / Upper 112 / Lower 96 ใช้ชุดเดียวกันทุกโมเดล ส่วนที่จับคู่ไม่ได้ยังถูกนับเป็น FN ไม่มีพื้นที่ ignore เพิ่มเฉพาะโมเดล Face ยังคงตัดคอและบริเวณไม่แน่นอนออกจากพื้นที่ประเมิน ส่วน Upper/Lower ใช้ mapping เดิม การรวมพิกเซลให้น้ำหนักตามขนาดส่วน จึงไม่ใช้ตาราง pooled F1 แทนอันดับ mean-part IoU/Macro4 เดิม', '',
        'Precision, Recall และ F1 ของทุกคู่โมเดล–คลาสอยู่ในตารางรายคลาสถัดไปและ [CSV เดิม](../metrics/CONTROLLED_ROI_TARGET_CONFUSION.csv) ใช้ชื่อคอลัมน์ pooled_precision / pooled_recall / pooled_F1 ตัวเลขใน CSV เป็นสัดส่วน 0–1 ส่วนตารางในรายงานแสดงเป็น %', '',
        'สร้างเฉพาะส่วน F1/P/R ซ้ำจาก aggregate CSV และ canonical index ที่อยู่บน public clone ได้ด้วย `python CCTV_Human_Parsing_Benchmark/scripts/report_target_confusion.py --f1-only --audit-dir CCTV_Human_Parsing_Benchmark/outputs/<fresh-audit-id>` ไม่ต้องมี weights, ภาพ หรือ prediction packets และไม่เปิด inference', '']
    return lines


def report_section(rows):
    section=['<!-- TARGET_CONFUSION_START -->','## Confusion matrix และการเก็บส่วนที่ต้องการครบแค่ไหน','',
        'อัปเดตจาก **สถิติที่ตรวจรับแล้ว** ของ CCTV ชุดล่าสุด 90 ภาพเท่านั้น ไม่มี inference หรือ rescore และไม่แก้ GT, mapping หรือคะแนนหลักเดิม ใช้ภาพเดียวรวม 36 binary matrices (9 โมเดล × 4 targets) และ CSV เดียวรวม 36 แถวพร้อมตัวหารและค่าก่อนปัดเศษ','',
        '[เปิดภาพ matrix ขนาดเต็ม](figures/CONTROLLED_ROI_TARGET_CONFUSION.png) · [CSV ตัวเลข/ตัวหาร/ส่วนที่พลาด](../metrics/CONTROLLED_ROI_TARGET_CONFUSION.csv)','','![36 binary confusion matrices](figures/CONTROLLED_ROI_TARGET_CONFUSION.png)','',
        '### อ่าน matrix และเข้าใจ domain','',
        '| GT / ผลทำนาย | ทำนายเป็นส่วนที่ประเมิน | ไม่ทำนายเป็นส่วนนั้น |','|---|---:|---:|',
        '| GT เป็นส่วนที่ประเมิน | TP: พิกเซลที่ทำนายถูก | FN: พิกเซล GT ที่พลาด |',
        '| GT ไม่ใช่ส่วนนี้ของคนที่ประเมิน ภายในพื้นที่ที่ให้คะแนน | FP: พิกเซลที่ทำนายเกิน | TN: พิกเซลที่เหลือในพื้นที่ประเมิน |','',
        '**เหตุผลที่ใช้ 2×2 ต่อคลาส:** Hair 61 / Face 21 / Upper 112 / Lower 96 ส่วน ใช้คนที่มีสิทธิ์และพื้นที่ประเมินต่างกันตาม selected-person part task เดิม สถิติ binary ไม่บอกว่า Hair ที่พลาดถูกทำนายเป็น Face, Upper, BG หรือ OTHER อย่างละเท่าไร จึงสร้างตาราง cross-class 4×4 จาก TP/FP/FN นี้ไม่ได้ การตอบคำถามนั้นต้องอ่าน native planes ภายใต้ joint-domain protocol เพิ่มเติม ซึ่งยังไม่ได้ทำในรอบนี้','',
        'Hair/Upper/Lower ให้คะแนน mask ของบุคคลที่จับคู่ได้บนพิกัดภาพต้นฉบับทั้งภาพ ส่วน Face กันคอที่ระบุได้และบริเวณไม่แน่นอนของเจ้าของส่วนนั้นออกก่อน โดยใช้พื้นที่เดียวกันทุกโมเดล วัตถุทึบที่บังหน้ายังเป็นพื้นที่ที่ทำนาย Face ทับแล้วเกิด FP ได้ ถ้าคอไม่ชัด ใช้บริเวณไม่แน่นอนที่ระบุจาก GT ไม่ตีความว่าไม่มีคอ\n\n**TN = จำนวนพิกเซลในพื้นที่ประเมิน − TP − FP − FN** เป็นจำนวนพิกเซลที่เหลือจากงานประเมินส่วนนั้น ไม่ใช่หลักฐานว่าทุกอย่างในฉากถูก annotate เป็น background จึงไม่ใช้ TN จำนวนมากหรือ pixel accuracy อ้างว่าตรวจคนได้ครบ พิกเซลเดียวกันอาจถูกนับในหลายงานรายส่วน เนื่องจากกำลังประเมินคนละบุคคลหรือคนละ target','',
        'ความเข้มสีในรูปคิดเป็นเปอร์เซ็นต์แยกแต่ละแถว แถวบนบอกสัดส่วนพิกเซล GT ที่ทำนายถูกและที่พลาด แถวล่างบอกสัดส่วน FP/TN ภายในพื้นที่ที่ไม่ใช่ส่วนของคนนี้ แต่ละช่องมีจำนวนพิกเซลจริงกำกับ สีเข้มจึงไม่ได้หมายถึงคุณภาพสูงเสมอ ต้องอ่านชื่อช่อง TP/FP/FN/TN ประกอบ และไม่ใช้สีแถวล่างเลือกผู้ชนะ','',
        '### Metric มาจากไหน คำนวณอย่างไร และตอบอะไร','',
        '| ตัวชี้วัด | สูตร/ตัวหาร | ความหมายและข้อจำกัด | ที่มา |','|---|---|---|---|',
        '| Recall / สัดส่วน GT ที่ทำนายได้ | TP รวม ÷ (TP รวม + FN รวม) | ทำนายครอบคลุมพิกเซล GT กี่เปอร์เซ็นต์ ไม่ลงโทษการทำนายเกิน และไม่ใช่เปอร์เซ็นต์คนที่ตรวจครบ | [นิยาม Recall](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.recall_score.html) |',
        '| สัดส่วนพิกเซลที่พลาด | FN รวม ÷ (TP รวม + FN รวม) หรือ 1 − Recall | พิกเซลของส่วนที่ต้องการซึ่งโมเดลทำนายไม่ครอบคลุม ไม่ใช่จำนวนคนที่ตรวจไม่พบ | ค่าที่เหลือจาก Recall บนพื้นที่ประเมินเดียวกัน |',
        '| Precision | TP รวม ÷ (TP รวม + FP รวม) | พิกเซลที่ทำนายเป็นส่วนนี้ถูกต้องตาม GT เท่าไร ภายใต้ขอบเขตของบุคคลและส่วนที่เลือกประเมิน | [นิยาม Precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_score.html) |',
        '| IoU / Jaccard | TP ÷ (TP + FP + FN) ของส่วนที่ประเมินแต่ละรายการ | ลงโทษทั้งการทำนายไม่ครบและการทำนายเกิน | [นิยาม Jaccard](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.jaccard_score.html), [การนับพิกเซลใน scorer](../scripts/controlled_roi_core.py) |',
        '| Dice / binary F1 | (2 × TP) ÷ (2 × TP + FP + FN) | วัดการซ้อนทับจาก counts เดียวกัน จึงไม่ใช่หลักฐานอิสระเพิ่ม และไม่ใช่ F1 ของการตรวจจับบุคคล | [นิยาม F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html) |',
        '| Mean-part IoU / Macro4 เดิม | บวก IoU รายส่วนในคลาสแล้วหารจำนวนส่วน จากนั้นเฉลี่ยสี่คลาส คลาสละ 25% | แต่ละ part น้ำหนักเท่ากันก่อนรวม targets; **ยังเป็นเกณฑ์หลักเดิม** | [protocol R2](../configs/CONTROLLED_ROI_FACE_NECK_PROTOCOL.json), [โค้ดรวมคะแนน Macro4](../scripts/face_neck_evaluation.py) |',
        '| Pooled IoU / Dice | รวมจำนวน TP/FP/FN ของทุกส่วนในคลาสก่อนเข้าสูตร | ส่วนที่มีพื้นที่มากมีน้ำหนักมากกว่า จึงต่างจาก mean-part; ไม่ใช้เปลี่ยนอันดับหลักเดิม | CSV และสูตรเดียวกัน |',
        '| ไม่ทับ GT เลย / ครอบคลุม GT ครบ | นับส่วนที่ TP=0 / ส่วนที่ FN=0 จากรายการที่ใช้ประเมิน | จำนวนส่วนที่ไม่ทับ GT แม้แต่พิกเซลเดียว / ครอบคลุมทุกพิกเซล GT; **FN=0 ยังมี FP ได้** จึงไม่ได้หมายถึง mask ถูกทุกจุด | สรุปจาก counts เดิม ไม่ตั้ง threshold เพิ่ม |',
        '| ผลทำนายว่าง / Mask ตรง GT ทุกพิกเซล | นับส่วนที่ไม่มีพิกเซลทำนาย / ส่วนที่ FP=0 และ FN=0 | ไม่มีพิกเซลของคลาสนั้น / ทุกพิกเซลตรงกับ GT อ้างอิง ไม่ใช่สถานะการรันล้มเหลวหรือเกณฑ์ผ่านใช้งานจริง | สรุปจาก counts เดิม |',
        '| ส่วนของบุคคลที่จับคู่ไม่ได้ (unmatched) | นับ detector_miss หรือ detector_unmatched ในรายการที่ตรวจรับแล้ว | GT ของส่วนที่ไม่มี predicted person จับคู่ได้ อาจมาจากไม่มี detection หรือการจับคู่แข่งขันกัน ไม่ใช่จำนวนคนทั้งฉากที่ YOLO มองไม่เห็น | [โค้ดให้คะแนนส่วนที่ไม่ใช่ใบหน้า](../scripts/controlled_roi_evaluation.py), [โค้ดให้คะแนนใบหน้า](../scripts/face_neck_evaluation.py) |','',
        'นิยาม matrix อิง [official confusion-matrix reference](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html) โดยเรียง labels [target, not-target] จึงเป็น [[TP,FN],[FP,TN]] คำนวณจาก canonical integer counts โดยตรง ไม่ได้เรียก sklearn มา rescore หากตัวหารเป็นศูนย์จะให้ null เพราะไม่มี support (CSV ใช้คำว่า null) ไม่แทนด้วยศูนย์อัตโนมัติ; ชุดนี้ทุก target มี positive GT การรวม native classes ใช้ union ตาม mapping เดิมแล้วจึงนับพิกเซล ไม่เฉลี่ย IoU ของคลาสย่อย','',
        '### รายโมเดลและรายคลาส: เก็บได้/พลาด/เกิน','',
        'ร้อยละในตารางคำนวณจาก **ผลรวมพิกเซลของทุกส่วนที่ใช้ประเมินในคลาสนั้น** (pooled pixels) ส่วนที่มีพื้นที่มากจึงมีน้ำหนักมากกว่า ต่างจาก mean-part IoU ที่ให้แต่ละส่วนมีน้ำหนักเท่ากัน “ไม่ทับ GT เลย” หมายถึง TP=0 รวมผลทำนายว่าง ผิดตำแหน่ง หรือจับคู่บุคคลไม่ได้ ไม่ใช่แค่ขอบ mask ไม่เรียบ ส่วน “ครอบคลุม GT ครบ” หมายถึง FN=0 เท่านั้น CSV มีจำนวนผลทำนายว่าง mask ที่ตรง GT ทุกพิกเซล ส่วนที่จับคู่ไม่ได้ และ TN เพิ่มเติม','']
    section += f1_section(rows)
    for target in TARGETS:
        chosen=[r for r in rows if r['target']==target];n=chosen[0]['GT_parts'];support=chosen[0]['GT_pixels']
        section += [f"#### {target}: GT {n} ส่วน รวม {support:,} พิกเซล",'',
            '| โมเดล | Recall (%) | พลาด (%) | Precision (%) | F1 (%) | TP (px) | FN (px) | FP (px) | ไม่ทับ GT เลย/ทั้งหมด | ครอบคลุม GT ครบ/ทั้งหมด |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for r in chosen:
            section.append(f"| {SHORT[r['model_id']]} | {r['pooled_recall']*100:.3f} | {r['missed_GT_fraction']*100:.3f} | {r['pooled_precision']*100:.3f} | {r['pooled_F1']*100:.3f} | {r['TP']:,} | {r['FN']:,} | {r['FP']:,} | {r['zero_overlap_parts']}/{n} | {r['full_GT_coverage_parts']}/{n} |")
        section.append('')
    section += ['### สรุปการทำนายครอบคลุมและการทำนายเกิน','']
    for target in TARGETS:
        chosen=[r for r in rows if r['target']==target];leader=max(chosen,key=lambda r:r['pooled_recall']);prec=max(chosen,key=lambda r:r['pooled_precision'])
        section.append(f"- **{target}:** Recall จากผลรวมพิกเซลสูงสุดคือ {SHORT[leader['model_id']]} {leader['pooled_recall']*100:.3f}% (พลาด {leader['FN']:,}/{leader['GT_pixels']:,} px); Precision จากผลรวมพิกเซลสูงสุดคือ {SHORT[prec['model_id']]} {prec['pooled_precision']*100:.3f}% ค่านี้อธิบายความครอบคลุมและการทำนายเกิน ไม่ได้เปลี่ยนอันดับ mean-part IoU เดิม")
    example=next(r for r in rows if r['model_id']=='Sapiens2_1b' and r['target']=='Hair')
    section += ['',f"**ตัวอย่างอ่านผลผมของ Sapiens2 1B:** เก็บถูก {example['TP']:,}/{example['GT_pixels']:,} พิกเซล = Recall {example['pooled_recall']*100:.3f}% พลาด {example['FN']:,} พิกเซล = {example['missed_GT_fraction']*100:.3f}% และทำนายเกิน {example['FP']:,} พิกเซล จึงได้ Precision {example['pooled_precision']*100:.3f}% แต่ยังมี {example['zero_overlap_parts']}/{example['GT_parts']} ส่วนที่ไม่ทับ GT เลย (ในจำนวนนี้จับคู่บุคคลไม่ได้ {example['unmatched_parts']} ส่วน) ขณะที่ mean-part IoU = {example['mean_part_IoU']*100:.3f}% คะแนน pooled ที่สูงไม่ได้หมายความว่าทำนายผมครบทุกคน เพราะส่วนที่มีพื้นที่มากมีน้ำหนักมากกว่าส่วนเล็ก และ Recall ไม่ลงโทษ FP",'']
    section += ['','จำนวนส่วนที่จับคู่บุคคลไม่ได้เท่ากันทุกระบบ: Hair 5/61, Face 2/21, Upper 15/112, Lower 14/96 รายการเหล่านี้ยังอยู่ในตัวหารและถูกนับเป็น FN ไม่ตัดออกเพื่อช่วยคะแนน กรณีที่ไม่ทับ GT เลยนอกเหนือจากนี้อาจมาจากผลทำนายว่าง ผิดคลาส ผิดตำแหน่ง หรือการกำหนดเจ้าของ mask จึงไม่ควรเหมารวมว่า YOLO ตรวจคนไม่พบ','',
        'การตอบว่า “แบ่งส่วนผมครบหรือไม่” ต้องดู Recall คู่กับ Precision/IoU และจำนวนส่วนที่ไม่ทับ GT เลย การครอบคลุม GT ได้ 100% เพียงอย่างเดียวอาจเกิดจาก mask ใหญ่เกินจริง ยังไม่มีเกณฑ์ผ่านแบบตายตัวสำหรับใช้งานจริง และไม่ได้เปลี่ยนน้ำหนักเพื่อให้โมเดลใดชนะ การไม่มี mask ที่ตรง GT ทุกพิกเซลก็ไม่ได้หมายความว่าทุกส่วนใช้งานไม่ได้ เพราะเกณฑ์นั้นเข้มถึงระดับทุกพิกเซล','',
        'Face ใช้ขอบเขตอ้างอิง 21/35 รายการที่ผู้ช่วยตรวจจากภาพ ไม่ใช่ GT ที่ผู้เชี่ยวชาญอิสระรับรอง ผล Face_Neck ของ Sapiens ยังประเมินบนพื้นที่ที่ตัดคอออกตามกติกาเดิม จึงไม่ได้รับรองการแยก Face-only, Dress หรือ Neck-only และไม่อธิบายผลจาก architecture/training เพียงอย่างเดียว ตารางนี้เพิ่มหลังเห็นผลแล้ว เป็นการสรุปเพิ่มเติม ไม่ใช่การวิเคราะห์ยืนยันที่ลงทะเบียนล่วงหน้า ไม่มีการรันโมเดล ให้คะแนนจาก masks ใหม่ ตรวจ GT เพิ่ม หรือปรับ mapping','',
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
