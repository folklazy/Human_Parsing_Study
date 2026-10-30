"""Normalize declared canonical result sources and report nine saved C4-P results.

No inference, metric changes, prediction changes or scalar native-Q reuse.
"""
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import csv, json, sys, subprocess
import numpy as np
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'))
from common_view.core import sha_file, semantic_metrics, load_spec
from common_view.full import project_confusion
from common_view.packets import atomic_json, fingerprint

RUN='cpi-common-c4p-20261030'
ORDER=['QANet_CIHP_HRNetW48_512x384','M2FP_R101_CIHP','D2FP_R101_CIHP','RPR_CIHP',
       'CPI_R50_CIHP','CPI_ConvNeXtB_CIHP','Sapiens2_0.4b','Sapiens2_0.8b','Sapiens2_1b']
def read(path): return json.loads(Path(path).read_text())
def rows(path):
    with Path(path).open() as f: return [json.loads(l) for l in f if l.strip()]
def ratio(v):return 'N/A' if v is None else f'{100*v:.3f}'
def table(headers,data):
    return '|'+ '|'.join(headers)+'|\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join('|'+ '|'.join(str(v) for v in row)+'|\n' for row in data)
def csvout(path,data):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)

def build():
    rec=P/'runs'/RUN; cfg=read(rec/'SCORING_CONFIG.json');compat=read(rec/'COMPATIBILITY.json')
    spec=load_spec(W/cfg['protocol']);assert sha_file(W/cfg['protocol'])==cfg['protocol_sha256']
    expected=cfg['expected_ids']; expected_set=set(expected);previous=read(P/'runs/closure-review-20261030/VERIFICATION.json')
    sources=previous['sources']; results={}; entries=[]; metricsdir=P/'metrics'/RUN;metricsdir.mkdir(exist_ok=True)
    common_base='common-c4p-full-20261029T063458522990Z'
    for mid in ORDER:
        if mid in cfg['models']:
            modelrec=rec/mid;root=W/cfg['artifact_root']/mid;run=RUN
            ledger=root/'SCORING.jsonl';accepted=[r for r in rows(ledger) if r['status']=='COMPLETE']
            score_ids={p.stem for p in (root/'scores').glob('*.json')}
        else:
            if mid=='Sapiens2_0.8b':run='sapiens08-c4p-20261029T081254180014Z'
            elif mid=='Sapiens2_1b':run='sapiens1b-c4p-20261029T200113781375Z'
            else:run=common_base
            modelrec=P/'runs'/run
            if run==common_base:
                modelrec=modelrec/mid;root=P/'outputs/common_view'/run/'models'/mid
                ledger=root/('EXECUTION.jsonl' if mid.startswith('Sapiens') else 'SCORING.jsonl')
                accepted=[r for r in rows(ledger) if r['status'] in ['COMPLETE','REUSED']]
                score_ids={p.stem for p in (root/'scores').glob('*.json')}
            else:
                root=P/'outputs/common_view'/run;ledger=root/'EXECUTION.jsonl'
                accepted=[r for r in rows(ledger) if r['status']=='COMPLETE' and not r.get('warmup')]
                score_ids={p.stem for sub in ['pilot','full'] for p in (root/sub/'scores').glob('*.json')}
        cp=modelrec/'COMPLETION.json';mp=modelrec/'METRICS.json';c=read(cp);m=read(mp)
        if mid not in cfg['models']:
            for f in [cp,mp]:assert sha_file(f)==sources[str(f.relative_to(W))]['sha256'],('accepted source drift',f)
        ids=[r['image_id'] for r in accepted]
        assert len(ids)==len(set(ids))==5000 and set(ids)==score_ids==expected_set
        assert c['status']==m['status']=='COMPLETE' and c['complete']==m['complete']==5000
        assert m['primary'] is not None and m['person_metrics'] is not None
        assert m['protocol_sha256']==cfg['protocol_sha256']
        h=np.asarray(m['histogram'],np.int64);native=np.asarray(m['native_GT_prediction_histogram'],np.int64)
        space='SAPIENS2_DOME29_PRED' if mid.startswith('Sapiens') else 'CIHP_GT_AND_NATIVE_PRED'
        assert np.array_equal(h,project_confusion(native,space,spec))
        assert semantic_metrics(h)==m['primary']
        assert m['primary']['GT_support']==cfg['GT_summary']['global_support']
        for pm in m['person_metrics'].values():
            assert pm['G_loc']==cfg['GT_summary']['G_loc'] and pm['G_sem_C4']==cfg['GT_summary']['G_sem_C4']
            assert abs(pm['Q_numerator']/pm['G_sem_C4']-pm['Q_C4_GT'])<1e-12
            assert pm['TP']+pm['FN']==pm['G_loc']
        revision=compat['models'][mid]['revisions'] if mid in cfg['models'] else {'SOURCE_HASH_BOUND_ACCEPTED_CONFIGURATION':5000}
        configpath=(rec/'SCORING_CONFIG.json' if mid in cfg['models'] else
                    P/'configs/cihp_sapiens_c4p_full.json' if run==common_base else modelrec/'FULL_CONFIG.json')
        configdigest=sha_file(configpath)
        expected_config=(m['config_sha256'] if mid in cfg['models'] or run==common_base else c['full_config_sha256'])
        assert configdigest==expected_config
        e=dict(model_id=mid,status='COMPLETE',expected=5000,complete=5000,exact_membership=True,
          canonical_completion_path=str(cp.relative_to(P)),canonical_completion_sha256=sha_file(cp),
          canonical_metrics_path=str(mp.relative_to(P)),canonical_metrics_sha256=sha_file(mp),primary_location='canonical_metrics_path:primary',
          legacy_completion_primary_null='primary' in c and c['primary'] is None,
          legacy_null_reason=('Legacy completion field was not populated by its reporter; exact membership and canonical METRICS.primary determine eligibility. Historical file unchanged.' if 'primary' in c and c['primary'] is None else None),
          membership_ledger=str(ledger.relative_to(W)),membership_ledger_sha256=sha_file(ledger),
          membership_sha256=fingerprint(sorted(ids)),protocol_sha256=cfg['protocol_sha256'],source_run=run,
          source_implementation_revisions=revision,route=m.get('route',m.get('source_route')),
          resource_policy=m['resource_policy'],new_model_inference=False,
          source_configuration_path=str(configpath.relative_to(P)),source_configuration_sha256=configdigest,
          scientific_identity_sha256=m.get('scientific_identity_sha256'))
        entries.append(e);results[mid]=m
    index=dict(kind='NORMALIZED_DERIVED_RESULT_INDEX',created_utc=datetime.now(timezone.utc).isoformat(),
      status='COMMON_C4P_COMPLETE_9_OF_9',protocol_sha256=cfg['protocol_sha256'],GT_manifest_sha256=cfg['GT_manifest_sha256'],
      GT_denominators_from_bindings={k:cfg['GT_summary'][k] for k in ['G_loc','G_sem_C4']},
      models=entries,historical_completion_files_modified=False,null_policy='Missing score is null, never zero; read only the explicitly declared canonical primary source.')
    atomic_json(P/'manifests/CIHP_COMMON_RESULT_INDEX.json',index)
    main=[];per_target=[];people=[];discordance=[]
    names=['BACKGROUND','Face_CIHP_reference_proxy_for_Sapiens','Hair','Upper_non_Dress','Lower_non_Dress','OTHER']
    for e in entries:
        mid=e['model_id'];m=results[mid];p=m['primary'];h=np.asarray(m['histogram'],np.int64)
        main.append(dict(model_id=mid,Hair_IoU=p['IoU'][2],Face_CIHP_reference_IoU=p['IoU'][1],Upper_non_Dress_IoU=p['IoU'][3],
          Lower_non_Dress_IoU=p['IoU'][4],C4P_mIoU4=p['mIoU4'],C3_global=p['C3_global_mean_only'],status='COMPLETE',complete=5000,
          implementation_revision=json.dumps(e['source_implementation_revisions'],sort_keys=True),route=e['route'],
          resource_policy=e['resource_policy'],canonical_metrics_path=e['canonical_metrics_path'],canonical_metrics_sha256=e['canonical_metrics_sha256']))
        for k in range(6):
            per_target.append(dict(model_id=mid,target_id=k,target=names[k],IoU=p['IoU'][k],GT_support_pixels=p['GT_support'][k],
              prediction_support_pixels=p['pred_support'][k],union_pixels=p['union'][k],zero_union=p['zero_union'][k]))
        for t,pm in m['person_metrics'].items():
            people.append(dict(model_id=mid,matching_mask_IoU=float(t),G_loc=pm['G_loc'],G_sem_C4=pm['G_sem_C4'],TP=pm['TP'],FP=pm['FP'],FN=pm['FN'],
              precision=pm['precision'],recall=pm['recall'],F1=pm['extent_F1'],Q_C4_GT=pm['Q_C4_GT'],Q_numerator=pm['Q_numerator'],
              contamination=pm['contamination'],contamination_numerator=pm['contamination_numerator'],matched_target_denominator=pm['matched_target_denominator'],
              background_leakage=pm['background_leakage'],ambiguous_matching_frames=pm['ambiguous_matching_frames']))
        native=np.asarray(m['native_GT_prediction_histogram'],np.int64)
        discordance.append(dict(model_id=mid,Face_GT_predicted_Face=int(h[1,1]),Face_GT_pixels=int(h[1].sum()),
          predicted_Face_on_non_Face_GT_pixels=int(h[:,1].sum()-h[1,1]),
          Upper_GT_predicted_OTHER_pixels=int(h[3,5]),Lower_GT_predicted_OTHER_pixels=int(h[4,5]),
          Dress_GT_predicted_Upper_or_Lower_pixels=int(native[6,[j for j in range(native.shape[1]) if spec['mapping'][('SAPIENS2_DOME29_PRED' if mid.startswith('Sapiens') else 'CIHP_GT_AND_NATIVE_PRED')][str(j)] in [3,4]]].sum()),
          valid_GT_predicted_Apparel_pixels=int(native[:,1].sum()) if mid.startswith('Sapiens') else None))
    for n,data in [('COMMON_SUMMARY',main),('PER_TARGET',per_target),('PERSON_METRICS',people),('DISCORDANCE',discordance)]:csvout(metricsdir/(n+'.csv'),data)
    nativecsv=P/'metrics/closure-review-20261030/NATIVE_SUMMARY.csv'
    native_rows=list(csv.DictReader(nativecsv.open()))
    assert len(native_rows)==6
    for row in native_rows:
        src=read(W/row['canonical_source'])
        if 'metrics' in src: src=src['metrics']
        assert src['primary']['mIoU_20_including_BG']==float(row['mIoU20'])
        assert src['primary']['mIoU_19_foreground']==float(row['FG19'])
    leader_rows=[]
    for title,key in [('Hair','Hair_IoU'),('Face ตาม CIHP reference','Face_CIHP_reference_IoU'),('Upper non-Dress','Upper_non_Dress_IoU'),('Lower non-Dress','Lower_non_Dress_IoU'),('C4-P mean','C4P_mIoU4')]:
        rank=sorted(main,key=lambda x:-x[key]);a,b=rank[:2]
        leader_rows.append(dict(metric=title,leader=a['model_id'],score=a[key],runner_up=b['model_id'],runner_score=b[key],gap_percentage_points=100*(a[key]-b[key]),
           exact_leaders=[r['model_id'] for r in rank if r[key]==a[key]]))
    global_leader=max(main,key=lambda r:r['C4P_mIoU4'])['model_id']
    qleaders={t:max([r for r in people if r['matching_mask_IoU']==t],key=lambda r:r['Q_C4_GT']) for t in [.5,.75]}
    f1leaders={t:max([r for r in people if r['matching_mask_IoU']==t],key=lambda r:r['F1']) for t in [.5,.75]}
    atomic_json(metricsdir/'LEADERS.json',dict(derived_from_full_precision=True,global_targets=leader_rows,person_Q_leaders=qleaders,F1_leaders=f1leaders,
         no_uncertainty_test=True,no_new_weighted_score=True))
    primarytable=table(['ระบบ','Hair IoU %','Face ref. IoU %','Upper %','Lower %','C4-P %','C3 %','ครบ'],
       [[r['model_id'],*[ratio(r[k]) for k in ['Hair_IoU','Face_CIHP_reference_IoU','Upper_non_Dress_IoU','Lower_non_Dress_IoU','C4P_mIoU4','C3_global']],'5,000/5,000'] for r in main])
    leaders=table(['Metric','คะแนนสูงสุด','IoU/mean %','อันดับถัดไป','ส่วนต่าง pp'],[[r['metric'],r['leader'],ratio(r['score']),r['runner_up'],f"{r['gap_percentage_points']:.3f}"] for r in leader_rows])
    persontable=table(['ระบบ','Mask IoU','TP','FP','FN','F1 %','Q_C4_GT %'],[[r['model_id'],f"{r['matching_mask_IoU']:.2f}",r['TP'],r['FP'],r['FN'],ratio(r['F1']),ratio(r['Q_C4_GT'])] for r in people])
    revisiontable=table(['ระบบ','Implementation / accepted IDs','Route','Resource policy ของการได้ predictions'],[[e['model_id'],
       '; '.join(f'{k}: {v}' for k,v in e['source_implementation_revisions'].items()),e['route'],
       'SHARED_GPU_QUALITY_ONLY' if e['model_id'].startswith(('CPI','Sapiens')) or e['model_id']=='RPR_CIHP' else 'Original admission; runtime exclusivity not certified'] for e in entries])
    evidencetable=table(['ระบบ','Canonical metrics','Completion','Legacy primary null'],[[e['model_id'],
      f"[METRICS](../{e['canonical_metrics_path']})",f"[COMPLETION](../{e['canonical_completion_path']})",e['legacy_null_reason'] is not None] for e in entries])
    supporttable=table(['ระบบ','Target','GT pixels','Pred pixels','Union pixels'],[[r['model_id'],r['target'],r['GT_support_pixels'],r['prediction_support_pixels'],r['union_pixels']] for r in per_target if 1<=r['target_id']<=4])
    nativetable=table(['ระบบ','mIoU20 รวม BG %','FG19 %','ครบ'],[[r['model_id'],ratio(float(r['mIoU20'])),ratio(float(r['FG19'])),'5,000/5,000'] for r in native_rows])
    diagtable=table(['ระบบ','Face FP pixels บน GT non-Face','Upper→OTHER pixels','Lower→OTHER pixels','GT Dress→Upper/Lower pixels'],
      [[r['model_id'],r['predicted_Face_on_non_Face_GT_pixels'],r['Upper_GT_predicted_OTHER_pixels'],r['Lower_GT_predicted_OTHER_pixels'],r['Dress_GT_predicted_Upper_or_Lower_pixels']] for r in discordance])
    qt=[]
    for t in [.5,.75]:
        q=qleaders[t];g=next(r for r in people if r['model_id']==global_leader and r['matching_mask_IoU']==t)
        qt.append(f"ที่ matching {t:.2f} Q_C4_GT สูงสุดคือ **{q['model_id']} ({ratio(q['Q_C4_GT'])}%)**; เทียบกับ {global_leader} มี Q {ratio(g['Q_C4_GT'])}% ส่วนต่าง {100*(q['Q_C4_GT']-g['Q_C4_GT']):.3f} pp และ FP {q['FP']:,} เทียบ {g['FP']:,}; extent F1 {ratio(q['F1'])}% เทียบ {ratio(g['F1'])}%")
    now=datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Bangkok')).isoformat()
    report=f'''# ผล Human Parsing common C4-P ครบเก้า checkpoints — สรุปสำหรับตรวจต่อ

อัปเดต **{now} (เวลาไทย UTC+07)** · **COMMON_C4P_COMPLETE_9_OF_9** · งานเพิ่มรอบนี้คือ saved-only CPI สองระบบ ไม่มี model inference ใหม่

## ผลที่ครบแล้วและคำตอบหลัก

checkpoint ทั้งเก้าตัวมีคะแนน common C4-P revision2 บน **official CIHP Validation ชุดเดียวกัน 5,000 unique IDs ต่อระบบ** แล้ว ตารางหลักใช้ full-precision canonical statistics ก่อนปัดเศษ ไม่ใช่ค่าจากแชท คะแนนสูงสุด global C4-P ในกลุ่มนี้คือ **{global_leader}** เป็น semantic quality leader ของ checkpoint พร้อม application configuration นี้ ไม่ใช่ architecture-only winner หรือการรับรองพร้อมใช้งาน CCTV

{leaders}
ส่วนต่างเป็น **percentage points (pp)** ไม่ใช่ relative percent; เป็น descriptive comparison ไม่มี uncertainty interval/statistical-significance claim ไม่สร้าง weighted overall score เพิ่ม การเลือก deployment ยังต้องดู person Q/FP/coverage และ capabilities ที่งานต่อไปต้องใช้

## 1. ตารางหลัก — frozen roster order

{primarytable}
Face คือ agreement กับ **CIHP reference Face**; Sapiens ใช้ Face_Neck รวม facial subparts เป็น proxy ซึ่งแยก neck จาก hard mask ไม่ได้ Hair/Upper/Lower ใช้ mapping revision2 เดิม Upper = CIHP UpperClothes+Coat, Lower = Pants+Skirt; Sapiens Upper_Clothing/Lower_Clothing ไม่รับรอง annotation-boundary equivalence Dress/Apparel เป็น valid OTHER ไม่แบ่งด้วย heuristic และไม่ ignore รายโมเดล

Primary C4-P = unweighted mean IoU ของสี่ target; C3 เป็น global mean Hair/Upper/Lower เท่านั้น ไม่มี Q_C3 ไม่รวม BG/OTHER ใน macro แต่ทั้งสองยังเป็น valid negatives: target บน OTHER เป็น FP และ OTHER บน target เป็น FN; Face ยังเป็น negative ที่ valid ใน C3 GT255 เป็น shared VOID, prediction unknown/255 contract failure ไม่มีเปลี่ยน policy หลังเห็นผล

สะสม global confusion ทั้งประชากรก่อนหาร IoU=TP_pixels/union ไม่เฉลี่ย IoU ของ native classes เพื่อรวมกลุ่ม zero-union=0 ตาม fixed-class definition พร้อม flags ใน CSV ค่าในตารางเป็นเปอร์เซ็นต์ ตัวเลขใน JSON/CSV เป็นfraction0–1 เก็บprecisionจริง

## 2. Person metrics และข้อเสนอการเลือก

G_loc = **{cfg['GT_summary']['G_loc']:,}**, G_sem_C4 = **{cfg['GT_summary']['G_sem_C4']:,}** รวมจาก bound GT-only manifest ไม่ hardcodeแทนการตรวจ ใช้ geometry-canonical matcher revision2 ที่ mask IoU0.50/0.75 เหมือนทั้งเก้าระบบ นิยาม tie/identical-geometry limitation คงเดิม Q_C4_GT รวม target-only per-eligible-GT-person contributions โดย missed GT=0 แล้วหาร G_sem_C4; unmatched predicted persons ไม่ลงโทษ Q โดยตรง ต้องอ่าน FP/F1 ร่วม ไม่เรียกผู้ Q สูงสุดว่า overall winner

{persontable}
{chr(10).join(qt)}

**ข้อเสนอ shortlist จากหลักฐาน CIHP นี้:** ใช้ {global_leader} เป็นตัวเลือกหลักเมื่อให้ความสำคัญกับความถูกต้องของพื้นที่ Hair/Face-reference/Upper/Lower โดยรวม และพิจารณา {', '.join(dict.fromkeys(qleaders[t]['model_id'] for t in [.5,.75]))} เป็นทางเลือกสำหรับคุณภาพ semantic ต่อ GT person โดยยอมรับข้อแลกเปลี่ยน FP/extent F1 ตามตาราง ไม่ได้กำหนดน้ำหนัก/threshold ใหม่ ไม่ใช่ final deployment acceptance และไม่ใช่ ensemble ที่ทดสอบแล้ว

**CPI ConvNeXt-B เป็นอีกทางเลือกสำหรับข้อแลกเปลี่ยนนี้:** ที่ matching0.50 มี Q_C4_GT {ratio(results['CPI_ConvNeXtB_CIHP']['person_metrics']['0.5']['Q_C4_GT'])}% สูงกว่า M2FP แต่ต่ำกว่า QANet ขณะที่ FP {results['CPI_ConvNeXtB_CIHP']['person_metrics']['0.5']['FP']:,} ต่ำกว่า QANet และ F1 {ratio(results['CPI_ConvNeXtB_CIHP']['person_metrics']['0.5']['extent_F1'])}% สูงกว่า QANet; global C4-P ยังต่ำกว่า M2FP จึงเสนอให้เก็บใน shortlist เมื่อการใช้งานให้น้ำหนัก semantic ต่อคนร่วมกับ FP โดยไม่สร้างคะแนนผสมหรือน้ำหนักใหม่ ไม่จำเป็นต้องเก็บทุกโมเดลเพียงเพราะอาจเหมาะกับ CCTV โดยยังไม่มีหลักฐาน

extent ของ QANet/Sapiens มาจาก frozen YOLO จึงไม่ใช้ F1 ที่เหมือนกันอ้าง native instance capability ของ parser; CPI และ native-frame ระบบอื่นคง extents/association ที่บันทึกไว้ ไม่มี remask ด้วย YOLO ในงานนี้ ข้อมูล input/conditioning ต่างกันยังเป็นข้อจำกัดของ application comparison

## 3. Support และตัวหารราย target

{supporttable}
Support เป็นจำนวน pixels ไม่ใช่จำนวนภาพ/คน; union เป็นตัวหาร IoU และต่างจาก GT support แม้ทุกระบบมี GT support เดียวกัน [PER_TARGET.csv](../metrics/{RUN}/PER_TARGET.csv) เก็บ BG/OTHER ด้วย ส่วน [PERSON_METRICS.csv](../metrics/{RUN}/PERSON_METRICS.csv) มี precision/recall, Q numerator, contamination numerator/denominator และ matching ambiguity ครบ ไม่ใช้ null เป็น0

## 4. ข้อจำกัดด้าน Face และเสื้อผ้าที่เห็นจาก confusion

{diagtable}
ตัวเลขนี้ derive จาก native-GT×prediction sufficient statistics เดิม/ใหม่ ไม่เปิด inference หรือ full pixel-scoring เพิ่ม Face FP บน non-Face GT รวมความผิด semantic และความต่าง annotation partition ได้ จึงไม่ยกทั้งหมดว่าเป็น neck error; GT ไม่แยกคอเป็น class อิสระ การนับ GT Dress→Upper/Lower เป็น discordance กับนิยาม fixed task ซึ่งต้องได้ FP ตาม domain ไม่ใช่หลักฐานว่าเสื้อผ้านั้นไม่มีอยู่หรือ parser แย่ทุกtaxonomy

Sapiens native Apparel ID1 เป็น OTHER ไม่เท่ากับ Dress6 โดยอัตโนมัติ [DISCORDANCE.csv](../metrics/{RUN}/DISCORDANCE.csv) มี valid-GT pixels ที่ทำนาย Apparel และ Upper/Lower→OTHER เพื่อช่วยอ่านข้อจำกัด ไม่ลบ pixels เหล่านี้หรือเปลี่ยน mapping ให้คะแนนดีขึ้น Full native-GT×prediction histograms อยู่ใน canonical METRICS แต่ละระบบ

## 5. Compatibility ของ CPI และระดับหลักฐาน equivalence

{revisiontable}
R50 original3 + buffer-reuse2 14 + feature-scheduling3 4,983 =5,000; ConvNeXt original337 + person-chunk1 4,663 =5,000 source segments/revisions/dependencies ระบุใน [COMPATIBILITY](../runs/{RUN}/COMPATIBILITY.json) และ [PARITY_REVIEW](../runs/{RUN}/PARITY_REVIEW.json) ไม่เรียกผลรวมว่าใช้ implementation เดียวทุกภาพ

แยกหลักฐานสามเรื่อง:

- **Forward/output parity:** person-chunk1 มี CPU restoration cases/GPU synthetic labels/native-prefix checks และ known-image NPZ byte regression; buffer-reuse2 มี raw float32 feature fixturesและknown-image regression; schedule3 มี CPU/GPU raw float fixtures, native max-head shape stress และ actual diagnostic frames/known-output equality ที่แยกจาก proof ของperson-chunk1 รวม dependency hashesทั้งสามโมดูล หลักฐานนี้ไม่ยืนยัน bitwise equivalence เทียบ original native inference ครบ5,000ภาพหรือทุก input/resource layout
- **Packet integrity/identity:** final accepted RECONCILED audits ตรวจ NPZ/CRC/metadata/input/checkpoint/geometry/YOLO/config เดิมแล้ว รอบนี้ตรวจ small metadata bindings และอ่าน required arrays พร้อม CRC ระหว่าง scoring โดย reuse audits ไม่ bulk rehash weights/NPZ/datasetsซ้ำ เชื่อมแต่ละคะแนนกับsourcepacket hash/segment/revision
- **Scorer agreement:** native audits มี independent saved-mask native scorer agreement; งานนี้คำนวณ person Q ใหม่จากsaved planes/extents/scoresผ่าน common revision2 ไม่คัดลอก scalar native Q ส่วน global ใช้ผลรวม20×20 confusionจากaccepted auditsแล้วproject ตรวจ pixel-based equivalenceบนfixed ambiguity sampleและตัวแทนแต่ละsegmentก่อน aggregate

ดังนั้นคะแนนคือผลของ configuration พร้อม effective revisions ที่ระบุและ packet contractที่ใช้ได้ ไม่อ้าง native unmodified reproductionทั้งประชากร CPI taxonomy acceptance ยังคง ACCEPTED_WITH_INDIRECT_EVIDENCE ไม่ยกระดับ DIRECT_VERIFIED

## 6. Native CIHP20 — เก็บแยกจาก common C4-P

{nativetable}
ตารางนี้อ่าน native canonical summary ที่ตรวจรับแล้ว ไม่ rescore native ทั้งชุด ไม่เทียบตัวเลขmIoU20กับmIoU4โดยตรง; คนละclasses/denominators/matching interpretation ผล frozen native masks/metrics/confusions/configs ไม่เขียนทับ รายละเอียด native per-class/person อยู่ใน [handoff](CIHP_EVALUATION_HANDOFF_TH.md)

## 7. OOM/recovery และความครบถ้วน

CPI R50 มี historical failed attempts5รายการ และ ConvNeXt3รายการ เก็บแต่ละattemptไว้; successful observationsแต่ละIDเลือกจากacceptedreconciledmanifest ไม่เลือก outputตามคะแนน R50ปิดnativeล่าสุดด้วยreuse912+new4,088; ConvNeXtreuse337+new4,663 Sapiens0.8Bมี historical MODEL_LOAD OOM0006307 ก่อนปิดรอบครบ การมีcurrent failed=0ไม่แปลว่าไม่เคยOOM

งานCPUรอบนี้มีsetup attemptก่อนimport scorerที่ launcher resolve venv symlinkเป็นsystemPythonจนไม่มีnumpy; scores/modelcalls0 เก็บ [SETUP_ATTEMPT_1](../runs/{RUN}/SETUP_ATTEMPT_1.json) แล้วแก้เฉพาะlaunch interpreterpath ไม่เปลี่ยนscorer/config/protocol ไม่มีmodel/OOMretryหรือfallbackใหม่ CPU streamsแยกdirectories/locks/atomic scores และimmutableattemptledger; resumeต้องexplicitและเช็คconfig/source/input/scorehash ไม่รันสำเร็จซ้ำหรือทับorphanโดยเงียบ

STRICT_COMPLETE แต่ละระบบต้อง exact5,000unique accepted IDs และscoremembershipตรงpopulation unresolvedinvalid/missing/failureให้primarynull รอบนี้ครบ9/9แล้ว [SCORING_CONFIG](../runs/{RUN}/SCORING_CONFIG.json) แยกจากnative frozenconfig เก็บCPUguards24h/80GiB/free50GiBและprovenance; GPU modelcallsใหม่=0 การถอดรหัสsavedNPZ/อ่านGTเพื่อscoringไม่ใช่modelinference

## 8. Canonical sources และ legacy null normalization

{evidencetable}
[CIHP_COMMON_RESULT_INDEX.json](../manifests/CIHP_COMMON_RESULT_INDEX.json) เป็น normalized **derived** index เชื่อม status/exactmembership/metrics path/hash/protocol/source revision/route บางhistoricalCOMPLETION.primaryเป็นnullเพราะreporterเดิมไม่populate ใช้ประกาศcanonical METRICS.primaryหลังตรวจmembership/status มิใช่เติมผลย้อนหลังหรือแทนnullด้วย0 รอบนี้ตรวจแหล่งที่ประกาศไว้ก่อนใช้คะแนน ถ้าผลหายจริง reporterต้องหยุด ไม่ fallbackไปnative/subsetscore

Protocol SHA256 `{cfg['protocol_sha256']}`; GTbinding manifestSHA256 `{cfg['GT_manifest_sha256']}`; source/config/input manifestsและledger hashesอยู่runrecordและindex [VERIFICATION](../runs/{RUN}/FINAL_VERIFICATION.json) ระบุ arithmetic/membership/protocol/immutability checksที่ทำจริง ไม่ใช้จำนวนtestsแทนsemanticreview

ไฟล์เต็มprecisionขนาดเล็ก: [COMMON_SUMMARY.csv](../metrics/{RUN}/COMMON_SUMMARY.csv), [PER_TARGET.csv](../metrics/{RUN}/PER_TARGET.csv), [PERSON_METRICS.csv](../metrics/{RUN}/PERSON_METRICS.csv), [LEADERS.json](../metrics/{RUN}/LEADERS.json) ไม่มีrawlogs/images/weightsในGit การcloneอย่างเดียวไม่reproducebenchmarkโดยไม่มีexternaldataset/checkpoints/environment/savedpackets

## 9. ขอบเขตคำอ้างและงานถัดไป

ผลนี้ตอบว่าcheckpoint+application configurationใดได้global target agreementและGT-personsemantic qualityสูงสุด **บนCIHP selection populationนี้** ไม่ควบคุมtraining/pretrainingexposureทั้งหมด ไม่แยกผลarchitecture/training/adapterออกจากกัน Common mappingไม่ทำให้inputroutesfairสมบูรณ์และไม่มีCCTV/colorperformanceclaim

Commonprotocolออกแบบหลังเห็นnativeสี่ระบบแล้ว จึงไม่อ้างpreregistered/independentfinalconfirmation ไม่มีปรับmapping/threshold/conditioningจากคะแนน ไม่มีcleanlatency/FPS/VRAMefficiencyrankingเพราะtimingboundaries/resourceconditionsต่างกัน ไม่เพิ่มuncertaintytestsเป็นเงื่อนไขปิดงาน

ไม่ได้สร้างgalleryใหม่ในรอบนี้ ภาพเดิมเป็นprivatefixed-sample snapshotsพร้อมmodelmanifestตาม [handoff](CIHP_EVALUATION_HANDOFF_TH.md) ไม่อ้างว่ามีpanelครบ9ตัวหรือเผยแพร่datasetimagesอัตโนมัติ ขั้นถัดไปคือผู้ใช้reviewshortlist/เลือกconfigurationไปphaseถัดไปโดยระบุmandatorycapabilities ไม่เปิดinference/training/OOMrepair/color/CCTVอัตโนมัติจากรายงานนี้
'''
    (P/'reports/CIHP_COMMON_NINE_RESULTS_TH.md').write_text(report)
    atomic_json(rec/'FINAL_VERIFICATION.json',dict(status='PASS',checked_Bangkok=now,common_complete=9,exact_IDs_per_system=5000,
       accepted_seven_sources_unchanged=True,canonical_primary_normalized_without_mutation=True,
       aggregate_projection_matches_histograms=True,full_precision_arithmetic=True,
       denominators_from_bindings=cfg['GT_summary'],inference_calls=0,new_GPU_diagnostics=0,full_native_rescore=False,
       protocol_sha256=cfg['protocol_sha256'],note='New CPI person scoring; seven accepted common metrics reused. Source native metadata/audit identities checked; no population-wide forward-equivalence claim.'))
    print(json.dumps({'status':'COMPLETE_9_OF_9','global_leader':global_leader,'Q_leaders':{str(k):v['model_id'] for k,v in qleaders.items()},'report':'reports/CIHP_COMMON_NINE_RESULTS_TH.md'},ensure_ascii=False))

if __name__=='__main__':build()
