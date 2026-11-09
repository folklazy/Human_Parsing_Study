"""Publish aggregate shared-view tables only after the CPU cohort is terminal."""
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import argparse
import hashlib
import json
import shutil
import sqlite3

H=Path(__file__).resolve().parents[1];W=H.parent;C=W/'CCTV_Human_Parsing_Benchmark'
LABELS=['QANet','M2FP','D2FP','RP-R-CNN','CPI R50','CPI ConvNeXt-B','Sapiens2 0.4B','Sapiens2 0.8B','Sapiens2 1B']
START='<!-- SHARED_REFERENCE_CURRENT_START -->';END='<!-- SHARED_REFERENCE_CURRENT_END -->'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pct(v):return f'{v*100:.3f}' if v is not None else 'null'


def validate_terminal(root,result,cfg,sources):
    """Check stored integer arithmetic/membership; do not read/score masks again."""
    if result['CONFIG_sha256']!=sha(root/'CONFIG.json'):raise ValueError('Result config differs')
    for mid in cfg['model_order']:
        if sources['CIHP']['models'][mid]['checkpoint_sha256']!=sources['CCTV']['models'][mid]['checkpoint_sha256']:
            raise ValueError('Different checkpoint across dataset comparison')
    con=sqlite3.connect(root/'RESULTS.sqlite3');checked=0
    for dataset,source in sources.items():
        for mid in cfg['model_order']:
            m=result['models'][dataset][mid]
            rows=con.execute('SELECT image_id,result FROM results WHERE dataset=? AND model=?',(dataset,mid)).fetchall()
            if m['strict_complete'] and {r[0] for r in rows}!=set(source['expected']):raise ValueError('Exact membership mismatch')
            sums={t:dict(n=0,TP=0,FP=0,FN=0,IoU=0.) for t in range(1,5)}
            for iid,value in rows:
                f=json.loads(value)
                if f['image_id']!=iid:raise ValueError('Ledger/frame ID mismatch')
                for p in f['parts']:
                    tp,fp,fn=(p[k] for k in ['TP','FP','FN'])
                    if min(tp,fp,fn)<0 or tp+fn!=p['GT_pixels'] or tp+fp+fn!=p['union']:
                        raise ValueError('Invalid integer support/union')
                    iou=tp/(tp+fp+fn)
                    if abs(iou-p['IoU'])>1e-12:raise ValueError('Per-part IoU formula mismatch')
                    a=sums[p['target']];a['n']+=1;a['IoU']+=iou
                    for k in ['TP','FP','FN']:a[k]+=p[k]
                    checked+=1
            for tid,name in [(1,'Face_local'),(2,'Hair'),(3,'Upper'),(4,'Lower')]:
                a=sums[tid];v=m['targets'][name]
                if a['n']!=v['GT_parts'] or any(a[k]!=v[k] for k in ['TP','FP','FN']):raise ValueError('Target aggregate mismatch')
                if m['strict_complete']:
                    if a['n']!=cfg['GT_summary'][dataset]['eligible_positive_parts'][str(tid)]:raise ValueError('GT denominator mismatch')
                    if v['GT_pixels']!=cfg['GT_summary'][dataset]['GT_support'][str(tid)]:raise ValueError('GT support differs by model')
                    if abs(a['IoU']/a['n']-v['mean_part_IoU'])>1e-12:raise ValueError('Mean-part aggregation mismatch')
            for threshold,v in m['localization'].items():
                if v['TP']+v['FN']!=cfg['GT_summary'][dataset]['GT_persons'] and m['strict_complete']:
                    raise ValueError('Person denominator mismatch')
    con.close()
    verification=dict(status='PASS',part_records_checked=checked,checks=['Exact membership per dataset/model',
        'Same checkpoint hashes across datasets','TP/FP/FN/union and per-part IoU from integers',
        'Aggregate supports and GT denominators independent of model','Mean-part arithmetic',
        'GT-person matching denominator'],new_mask_rescoring=False)
    (root/'ARITHMETIC_MEMBERSHIP_VERIFICATION.json').write_text(json.dumps(verification,indent=2)+'\n')
    return verification


def render(root):
    status=read(root/'STATUS.json')
    if status['status'] not in ['COMPLETE','INCOMPLETE']:raise ValueError('Never analyze ranks while CPU batch is running')
    result=read(root/'RESULTS.json');cfg=read(root/'CONFIG.json');sources=read(root/'SOURCES.json')
    verification=validate_terminal(root,result,cfg,sources)
    order=cfg['model_order'];names=dict(zip(order,LABELS));now=datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Bangkok')).isoformat()
    public=dict(result,artifact_root=str(root.relative_to(W)),GT_summary=cfg['GT_summary'],protocol=cfg['protocol'],
        scorer_source_hashes=cfg['source_hashes'],result_sha256=sha(root/'RESULTS.json'),
        sources_manifest_sha256=cfg['sources_sha256'],CPU_integration=read(root/'CPU_INTEGRATION.json'),
        report_source_sha256=sha(__file__),verification=verification,source_configuration_references={d:{mid:{k:v for k,v in m.items() if k!='packets'} for mid,m in s['models'].items()} for d,s in sources.items()})
    (H/'reports/SHARED_REFERENCE_RESULT_INDEX.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
    for filename,dest in [('SUMMARY.csv','SHARED_REFERENCE_SUMMARY.csv'),('TARGET_COUNTS.csv','SHARED_REFERENCE_TARGET_COUNTS.csv')]:
        shutil.copyfile(root/filename,H/'metrics'/dest)
    lines=[f'## ผลล่าสุด: สามคลาสหลัก + Face-local — {now}',
        f'**{result["status"]}** — run `{root.name}`. ใช้ saved predictions ของ controlled YOLO person-ROI ทั้งเก้า checkpoints; **ไม่มี inference ใหม่**. ผล CIHP/CCTV อยู่คนละตารางและไม่รวมเป็นคะแนนเดียว. กติกาใหม่ตรึงก่อนคำนวณ แต่จัดทำหลังเห็นผลเดิมแล้ว จึงเป็นการวิเคราะห์ exploratory ไม่ใช่ preregistered confirmation.',
        '### นิยามที่ใช้อธิบายร่วมกัน',
        '**สามคลาสหลัก:** วัด IoU ของส่วน Hair/Upper/Lower ของ GT แต่ละคนที่มี annotation แล้วเฉลี่ยภายในคลาส จากนั้นเฉลี่ยสามคลาสเท่ากัน เรียก **mIoU3 (part-mean)**. ตัวนี้ไม่ใช่ global C3 เดิม และไม่ใช่ full-scene semantic mIoU. ขอบเขตที่ส่งออกของโมเดลยังเป็น native classes ทั้งหมด; Upper/Lower projection ไม่รวม Dress/Apparel.',
        '**Face-local:** รวม Face ของ CIHP หรือ Face_Neck+รายละเอียดใบหน้าของ Sapiens เป็น face candidate แล้วคิด IoU ภายในกรอบสี่เหลี่ยมครอบ GT Face พอดี ใช้กรอบเดียวกันทุกโมเดลในคน/ภาพเดียวกัน ไม่มี margin. **ภายในกรอบส่วนเกินยังเป็น FP; GT ที่ทายขาดเป็น FN; นอกกรอบไม่ประเมิน**. เฉลี่ยราย GT Face ที่มีสิทธิ์ทุกคน รวมคนที่ระบบพลาดเป็นศูนย์ ไม่ได้ตัด prediction ตามรูปทรง GT.',
        'กรอบ Face GT ใช้หลังจากได้ saved prediction แล้วสำหรับให้คะแนนเท่านั้น ไม่ได้ใช้เปลี่ยน input/crop หรือช่วยโมเดลสร้าง prediction. เก็บ output หน้าและคอต้นฉบับไว้ครบ.',
        '![ภาพสมมติอธิบายกรอบให้คะแนน Face-local ไม่ใช่ผลโมเดลจริง](figures/FACE_LOCAL_PROTOCOL_EXAMPLE.png)',
        'จับคู่คนแบบหนึ่งต่อหนึ่งด้วย mask IoU ตั้งแต่ 0.50 ขึ้นไป: เลือกให้จับคู่ได้มากที่สุดก่อน จากนั้นเลือกผลรวม IoU สูงสุด และใช้ลำดับจากรูปทรง mask ตัดสินกรณีเสมอ โดยไม่ใช้ความถูกต้องของคลาสช่วยเลือกคู่ ส่วน threshold 0.75 ใช้รายงานประกอบ ทั้งสองชุดใช้กติกานี้เหมือนกัน ขอบเขตคนสำหรับจับคู่แยกจากพื้นที่พิกเซลที่ให้คะแนนคลาส พื้นที่ GT ที่ระบุเป็น VOID หรือกำกวมเรื่องเจ้าของถูกยกเว้นเหมือนกันทุกโมเดล ไม่มีการยกเว้นคอเฉพาะ Sapiens.',
        'สำหรับ Hair/Upper/Lower ของคนที่จับคู่แล้ว ใช้ prediction ของคนนั้นเทียบ GT ของคนนั้นบนพื้นที่ valid ทั้งภาพ ดังนั้นหากทายคลาสนั้นเกินไปบน OTHER หรือส่วนอื่น จะเป็น FP และหากทาย OTHER บน GT ของคลาสนั้น จะเป็น FN ส่วนคนที่พลาดให้คะแนนศูนย์ ไม่ตัดออกจากตัวหาร การไม่มี GT ของคลาสใดไม่สร้างงานของคลาสนั้น จึงเป็นการวัดส่วนที่มี annotation ไม่ใช่การให้คะแนนทุกพิกเซลทั้งฉาก.',
        '### ประชากรและตัวหารที่อ่านจาก GT จริง',
        '| Dataset | ภาพ/โมเดล | GT persons | Hair parts | Upper parts | Lower parts | Face parts |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for d in ['CIHP','CCTV']:
        g=cfg['GT_summary'][d];n=g['eligible_positive_parts']
        lines.append(f'| {d} | {g["images"]:,} | {g["GT_persons"]:,} | {n.get("2",0):,} | {n.get("3",0):,} | {n.get("4",0):,} | {n.get("1",0):,} |')
    lines+=['CCTV ใช้ annotation 90 ภาพที่ผู้ใช้ตรวจรับ พร้อมการแก้เจ้าของส่วนร่างกายตามหลักฐานเดิม ไม่ใช้ชุดคัดเลือก 269 ส่วนที่ไม่ใช่หน้า/21 ส่วนหน้า หรือกติกายกเว้นคอของรายงานเก่า พื้นที่ GT ที่คนหรือคลาสทับกันอย่างกำกวมเป็น VOID ร่วมกันก่อนคำนวณ ทั้งสอง dataset มีคนและส่วนที่ติดป้ายกำกับต่างกัน จึงเปรียบเทียบโมเดลภายในแต่ละชุด ไม่สรุปว่าคะแนนที่ต่างข้ามชุดเกิดจากสภาพภาพเพียงอย่างเดียว.',
        '### ผลคุณภาพ — หน่วยเปอร์เซ็นต์',
        'เรียง frozen roster ไม่ใช่เรียงอันดับ. ค่าเฉลี่ยสามคลาสและ Face-local แสดงแยกกัน ไม่มีคะแนนถ่วงน้ำหนักรวมสี่คลาสใหม่.']
    leaders={}
    for d in ['CIHP','CCTV']:
        lines += [f'#### {d}', '| Checkpoint + configuration | Hair IoU | Upper IoU | Lower IoU | mIoU3 part-mean | Face-local IoU | ครบภาพ |', '|---|---:|---:|---:|---:|---:|---:|']
        for mid in order:
            m=result['models'][d][mid];t=m['targets']
            lines.append(f'| {names[mid]} | {pct(t["Hair"]["mean_part_IoU"])} | {pct(t["Upper"]["mean_part_IoU"])} | {pct(t["Lower"]["mean_part_IoU"])} | {pct(m["primary_mIoU3_part_mean"])} | {pct(m["Face_local_IoU"])} | {m["completed"]:,}/{m["expected"]:,} |')
        if all(m['strict_complete'] for m in result['models'][d].values()):
            leaders[d]={}
            for target in ['Hair','Upper','Lower','mIoU3_part_mean','Face_local']:
                def value(mid):
                    m=result['models'][d][mid]
                    return m['primary_mIoU3_part_mean'] if target=='mIoU3_part_mean' else m['Face_local_IoU'] if target=='Face_local' else m['targets'][target]['mean_part_IoU']
                ranked=sorted(order,key=value,reverse=True);winner,second=ranked[:2]
                leaders[d][target]=dict(model_id=winner,score=value(winner),runner_up=second,delta_percentage_points=100*(value(winner)-value(second)))
            lines.append('**คะแนนสูงสุดในชุดนี้:** '+'; '.join(f'{dict(mIoU3_part_mean="mIoU3 (part-mean)",Face_local="Face-local").get(t,t)}: {names[v["model_id"]]} ({pct(v["score"])}%, ต่างอันดับสอง {v["delta_percentage_points"]:.3f} pp)' for t,v in leaders[d].items())+'.')
    lines+=['### การจับคู่คน — diagnostic ของ GT reference และ YOLO extents',
        'คะแนน IoU รายส่วนไม่ลงโทษคนที่ทำนายเกินแต่จับคู่ GT ไม่ได้โดยตรง จึงต้องอ่าน TP/FP/FN ของการจับคู่ประกอบ ตัวเลขส่วนนี้สะท้อน YOLO extents ที่ตรึงไว้ ไม่ใช่ความสามารถแยก instance โดยตัว parser เอง สำหรับ CCTV คนที่ทำนายแต่ไม่มีคู่ GT อาจเป็นคนที่ไม่ได้ annotate จึงใช้เป็น diagnostic ภายใต้ GT ที่มี ไม่ใช่ precision ของการตรวจจับคนทั้งฉาก.',
        '| Dataset | Model | threshold | TP | FP | FN | F1 % |', '|---|---|---:|---:|---:|---:|---:|']
    for d in ['CIHP','CCTV']:
        for mid in order:
            for threshold,v in result['models'][d][mid]['localization'].items():
                lines.append(f'| {d} | {names[mid]} | {threshold} | {v["TP"]:,} | {v["FP"]:,} | {v["FN"]:,} | {pct(v["F1"])} |')
    lines+=['### สูตร วิธีอ่าน และไฟล์ตรวจตัวเลข',
        '- **IoU ต่อส่วน = TP/(TP+FP+FN)**: TP คือพิกเซลที่ทายถูก, FP คือทายเกิน, FN คือ GT ที่ทายขาด ค่า mean-part IoU ให้แต่ละส่วนของแต่ละคนมีน้ำหนักเท่ากัน ส่วน pooled IoU รวมพิกเซลของทุกส่วนก่อนหาร จึงให้น้ำหนักส่วนขนาดใหญ่มากกว่า.',
        '- **Precision = TP/(TP+FP)** บอกว่าที่ทายมาถูกเท่าไร; **Recall = TP/(TP+FN)** บอกว่าเก็บ GT ได้ครบเท่าไร; **F1/Dice = 2TP/(2TP+FP+FN)** สรุปทั้งการทายเกินและทายขาด P/R/F1 ใน CSV รวมจำนวนพิกเซลจากงานรายส่วนก่อนคำนวณ ไม่ใช่แปลงจาก mean IoU และไม่ใช่คะแนนทั้งฉาก.',
        '- ประเมินเฉพาะคน–คลาสที่มี GT ของคลาสนั้น ถ้าไม่มี polygon จะไม่ถือว่าเป็นส่วนที่ยืนยันว่าไม่มี และไม่สร้างงาน negative เพิ่ม หากไม่มีส่วนที่มีสิทธิ์เลย คะแนนเป็น null ส่วนที่มี GT แต่จับคู่คนไม่ได้ให้ IoU = 0 คลาส Dress/Apparel ที่รู้จักเป็น OTHER; prediction ID ที่ไม่รู้จักหรือ 255 เป็น output ผิดข้อกำหนด ไม่ใช่ ignore.',
        '- ช่องว่างใน CSV หมายถึง null เช่น ไม่มีตัวหารหรือประเมินไม่ครบ ไม่ใช่คะแนน 0 ส่วน JSON เก็บ null โดยตรง.',
        '- [ตารางสรุปก่อนปัดเศษ](../metrics/SHARED_REFERENCE_SUMMARY.csv), [TP/FP/FN, support, union และ P/R/F1 ครบ 72 รายการ](../metrics/SHARED_REFERENCE_TARGET_COUNTS.csv), [ผลรวม canonical และแหล่งที่มา](SHARED_REFERENCE_RESULT_INDEX.json), [ข้อกำหนดที่ตรึงไว้](../protocol/SHARED_C3_FACE_LOCAL_V1.json).',
        '### การตรวจและข้อจำกัด',
        f'ผ่าน CPU acceptance 13 กรณี โดยใช้ผลคาดหวังจากตัวอย่างขนาดเล็กที่คำนวณแยกจาก implementation และทดสอบเส้นทาง packet → scorer → reporter ตรวจ saved packets จริงของ CIHP ทั้ง 9 โมเดลบนภาพเดียวกัน และจำนวน TP/FP/FN ของ C3 ตรงกับ scorer เดิม ตรวจ CCTV 63 รายการก่อนรันเต็ม และทดสอบ resume โดยรักษา 63 รายการเดิมแล้วเพิ่ม 9 รายการโดยไม่ซ้ำ งานเต็มใช้ SQLite ที่บังคับ dataset/model/image ไม่ซ้ำ บันทึกแต่ละภาพแบบ atomic และเก็บประวัติเหตุการณ์พร้อม source/protocol hashes ผล CPU ฉบับละเอียดเก็บเป็น private ที่ `{root.relative_to(W)}/`.',
        'STRICT_COMPLETE ตรวจว่าแต่ละ checkpoint มี CIHP ครบ 5,000 IDs และ CCTV ครบ 90 IDs ตรงประชากรโดยไม่ซ้ำ คะแนนหลักเป็น null หากขาด ซ้ำ หรือมี failure ไม่ใช้ subset แทนชุดเต็มและไม่เลือก output จากคะแนนที่ดีที่สุด ประวัติ OOM, interruption และ time guard ของ inference เดิมยังอยู่ครบ การประเมินบน CPU สำเร็จไม่ได้หมายความว่าไม่เคยเกิดข้อผิดพลาดมาก่อน.',
        'Face-local ไม่ลงโทษผลเกินนอกกรอบ จึงไม่ใช่ Face IoU ทั้งภาพ หรือหลักฐานว่าแยกหน้าออกจากคอได้สมบูรณ์ แม้ใช้วิธีให้คะแนนเดียวกัน ขอบเขต Face/Face_Neck ตาม annotation ยังต่างกันได้ GT ของ CCTV เป็น reference ที่ผู้ใช้ตรวจรับและมีเครื่องมือโมเดลช่วยจัดทำ ไม่ใช่ชุด gold standard ที่ผู้เชี่ยวชาญอิสระตรวจรับ การไม่มี annotation ไม่ทำให้พื้นที่นั้นกลายเป็น background ที่ยืนยันแล้ว.',
        'CCTV ใช้ป้าย Upper/Lower ที่ผู้ใช้ตรวจรับเป็น reference ไม่อนุมานจากชื่อคลาสใน metadata ว่าทุก polygon แยก Dress/ผิวหนังเหมือน CIHP ทุกพิกเซล การแปลง prediction ไม่รวม Dress/Apparel เข้า Upper/Lower และเก็บเป็น OTHER ตามเดิม ไม่มี ignore เฉพาะโมเดลเพื่อช่วยคะแนน แม้ใช้แหล่ง ROI และ scorer ร่วมกัน การ resize/decoder และ implementation revision ยังเป็นคุณสมบัติของแต่ละ configuration.',
        'ผลนี้เปรียบเทียบ pretrained checkpoint พร้อม application configuration บนแต่ละ dataset ไม่สามารถแยกผลของ architecture, ข้อมูลฝึก และ adapter ออกจากกันทั้งหมด ไม่อ้างนัยสำคัญทางสถิติ ความพร้อม deploy หรือความแม่นของงานสี ผล native/C4/global C3 และ Face-domain ของ CCTV เดิมยังเก็บเป็นประวัติ ไม่เปลี่ยนชื่อให้เป็นคะแนนใหม่นี้ และไม่ใช้ timing เดิมหรือเวลาประเมินบน CPU จัดอันดับ latency/FPS/ประสิทธิภาพ VRAM.',
        '### ข้อเสนอสำหรับพรีเซนต์',
        '> เราใช้ YOLO person-ROI pipeline ที่ตรึงไว้ เปรียบเทียบ Hair/Upper/Lower ด้วยค่าเฉลี่ย IoU รายส่วน และวัด Face แยกด้วย IoU ภายในกรอบ Face GT เดียวกันทุกโมเดล โดยใช้กติกาเดียวกันใน CIHP และ CCTV.',
        'รายงานคะแนนสูงสุดราย target ค่าเฉลี่ยสามคลาส และ Face แยกกัน ไม่มีคะแนนรวมสี่คลาสใหม่ ตัวเลือกที่แนะนำอ้างอิง reference ชุดนี้ ยังไม่ใช่การรับรองสำหรับใช้งานจริง.']
    formatted=[]
    previous=None
    for line in lines:
        kind='table' if line.startswith('|') else 'list' if line.startswith('- ') else 'paragraph'
        if formatted and not (kind==previous and kind in ['table','list']):formatted.append('')
        formatted.append(line);previous=kind
    text='\n'.join(formatted)
    block=START+'\n\n'+text+'\n\n'+END
    report=H/'reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md';old=report.read_text()
    if START in old:
        a=old.index(START);b=old.index(END,a)+len(END);new=old[:a]+block+old[b:]
    else:
        title,body=old.split('\n',1);new=title+'\n\n'+block+'\n\n## ประวัติการตรวจและข้อเสนอก่อนรอบ shared view (historical)\n\n'+body.lstrip('\n')
    report.write_text(new)
    private_text=(text.replace('(../metrics/SHARED_REFERENCE_SUMMARY.csv)','(SUMMARY.csv)')
        .replace('(../metrics/SHARED_REFERENCE_TARGET_COUNTS.csv)','(TARGET_COUNTS.csv)')
        .replace('(SHARED_REFERENCE_RESULT_INDEX.json)','(../../reports/SHARED_REFERENCE_RESULT_INDEX.json)')
        .replace('(../protocol/SHARED_C3_FACE_LOCAL_V1.json)','(../../protocol/SHARED_C3_FACE_LOCAL_V1.json)')
        .replace('(figures/FACE_LOCAL_PROTOCOL_EXAMPLE.png)','(../../reports/figures/FACE_LOCAL_PROTOCOL_EXAMPLE.png)'))
    (root/'REPORT_TH.md').write_text('# ผล shared C3-part / Face-local\n\n'+private_text+'\n')
    public['leaders']=leaders
    (H/'reports/SHARED_REFERENCE_RESULT_INDEX.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],report=str(report.relative_to(W)),datasets=list(result['models']),model_calls=0)),flush=True)



def timing_statistics(values):
    """Summarize measured intervals. Missing observations retain null values."""
    import math
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError('Invalid saved duration')
    return dict(n=len(values), total_seconds=math.fsum(values) if values else None,
                mean_ms=math.fsum(values)*1000/len(values) if values else None)


def collect_cihp_timing(models):
    """Bind committed frame timers to the accepted packet metadata, without masks."""
    result = {}
    inputs = {}
    for model_id, model in models.items():
        packet_paths = model['packets']
        roots = sorted({str(Path(path).parents[1]) for path in packet_paths.values()})
        accepted = {}
        for relative_root in roots:
            ledger = W/relative_root/'ATTEMPTS.jsonl'
            inputs[str(ledger.relative_to(W))] = sha(ledger)
            with ledger.open() as stream:
                for line in stream:
                    event = json.loads(line)
                    image_id = event.get('image_id')
                    if event.get('event') != 'FRAME_COMMITTED' or image_id not in packet_paths:
                        continue
                    if str(Path(packet_paths[image_id]).parents[1]) != relative_root:
                        continue
                    if image_id in accepted:
                        raise ValueError('Duplicate accepted frame timing')
                    metadata = read(W/packet_paths[image_id]/'packet.json')
                    if (metadata['packet_sha256'] != event['packet_sha256'] or
                            metadata['model_id'] != model_id or
                            metadata['checkpoint_sha256'] != model['checkpoint_sha256']):
                        raise ValueError('Timer does not bind to accepted packet')
                    accepted[image_id] = event
        if set(accepted) != set(packet_paths):
            raise ValueError('Accepted population lacks frame ledger records')
        adapter, image_times = [], []
        stages = {}
        roi_count = 0
        for event in accepted.values():
            count = event['ROI_count']
            roi_count += count
            observed = []
            identities = set()
            for roi in event['ROI_timings']:
                identity = roi['opportunity_id']
                if identity in identities:
                    raise ValueError('Duplicate ROI timing')
                identities.add(identity)
                values = {}
                for span in roi.get('measurements', {}).get('spans', []):
                    if span['status'] == 'COMPLETE':
                        values.setdefault(span['stage'], []).append(span['seconds'])
                if 'adapter_total' in values:
                    if len(values['adapter_total']) != 1:
                        raise ValueError('Ambiguous adapter interval')
                    observed.extend(values['adapter_total'])
                for stage, intervals in values.items():
                    stages.setdefault(stage, []).append(sum(intervals))
            if len(observed) > count:
                raise ValueError('More timers than accepted ROI opportunities')
            adapter.extend(observed)
            if len(observed) == count:
                image_times.append(sum(observed))
        full = len(image_times) == len(packet_paths)
        result[model_id] = dict(expected_images=len(packet_paths), ROI_population=roi_count,
            timed_ROIs=len(adapter), adapter=timing_statistics(adapter),
            images_with_complete_timing=len(image_times), complete_images=timing_statistics(image_times),
            full_population_mean_ms_per_image=timing_statistics(image_times)['mean_ms'] if full else None,
            full_population_parsing_work_seconds=timing_statistics(image_times)['total_seconds'] if full else None,
            recorded_interval_sum_seconds=timing_statistics(adapter)['total_seconds'],
            stages={name: timing_statistics(values) for name, values in stages.items()},
            accepted_segments=roots, speed_ranking_eligible=False)
    return result, inputs


def supplement(root):
    """Add user-requested equal four-target summary and existing timing evidence."""
    import csv
    index_path = H/'reports/SHARED_REFERENCE_RESULT_INDEX.json'
    public = read(index_path)
    if public['status'] != 'COMPLETE' or public['result_sha256'] != sha(root/'RESULTS.json'):
        raise ValueError('Complete accepted score binding required')
    sources = read(root/'SOURCES.json')
    if sha(root/'SOURCES.json') != public['sources_manifest_sha256']:
        raise ValueError('Source manifest drift')
    cihp, timer_inputs = collect_cihp_timing(sources['CIHP']['models'])
    state_path = C/'STUDY_STATE.json'
    state = read(state_path)
    cctv = {model['model_id']: model for model in state['historical_four_target_state']['runtime_reporting']['models']}
    order = list(public['models']['CIHP'])
    names = dict(zip(order, LABELS))
    now = datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Bangkok')).isoformat()
    lines = ['## ค่าเฉลี่ยสี่คลาสและเวลาจากการรันที่บันทึกไว้',
        f'เพิ่มตามคำขอผู้ใช้เมื่อ {now} โดยใช้คะแนนและ timing ที่บันทึกแล้ว',
        '**Macro4-local = (Hair mean-part IoU + Face-local IoU + Upper mean-part IoU + Lower mean-part IoU) ÷ 4** แต่ละคลาสมีน้ำหนัก 25% คำนวณจากค่าก่อนปัดเศษ โดย Face ใช้พื้นที่ภายในกรอบ GT Face ส่วนอีกสามคลาสใช้พื้นที่ valid ของงานรายส่วน ผลรวมนี้สรุปคุณภาพสี่ target ตามขอบเขตดังกล่าว ผู้ใช้ขอเพิ่มค่าเฉลี่ยหลังเห็นผลแล้ว จึงบันทึกเป็น derived summary แยกจาก primary mIoU3 ที่ตรึงไว้',
        '| Dataset | โมเดล | Hair % | Face-local % | Upper % | Lower % | Macro4-local % |',
        '|---|---|---:|---:|---:|---:|---:|']
    leaders = {}
    summary_rows = []
    for dataset in ['CIHP', 'CCTV']:
        for model_id in order:
            model = public['models'][dataset][model_id]
            values = [model['targets'][target]['mean_part_IoU'] for target in ['Hair','Face_local','Upper','Lower']]
            score = sum(values)/4 if model['strict_complete'] and all(value is not None for value in values) else None
            model['derived_Macro4_local'] = score
            lines.append(f'| {dataset} | {names[model_id]} | '+ ' | '.join(pct(value) for value in values)+f' | {pct(score)} |')
            if dataset == 'CIHP':
                timing = cihp[model_id]
            else:
                previous = cctv[model_id]
                timing = dict(previous['per_image_summary'], ROI_population=previous['ROI_population'],
                    timed_ROIs=previous['time_accounting']['timed_ROIs'],
                    worker_elapsed_seconds=previous['time_accounting']['worker_elapsed_sum_seconds'])
            summary_rows.append(dict(dataset=dataset, model_id=model_id, completed=model['completed'],
                expected=model['expected'], strict_complete=model['strict_complete'],
                Hair=values[0], Upper=values[2], Lower=values[3],
                mIoU3_part_mean=model['primary_mIoU3_part_mean'], Face_local_IoU=values[1],
                Macro4_local=score, timing_complete_images=timing['images_with_complete_timing'],
                timing_mean_ms_per_image=timing['full_population_mean_ms_per_image'],
                timing_total_seconds=timing['full_population_parsing_work_seconds']))
        winner = max(order, key=lambda mid: public['models'][dataset][mid]['derived_Macro4_local'])
        leaders[dataset] = dict(model_id=winner, score=public['models'][dataset][winner]['derived_Macro4_local'])
    lines += ['', 'ค่าเฉลี่ยสี่คลาสสูงสุดใน CIHP คือ '+names[leaders['CIHP']['model_id']]+' '+pct(leaders['CIHP']['score'])+'% และใน CCTV คือ '+names[leaders['CCTV']['model_id']]+' '+pct(leaders['CCTV']['score'])+'%',
        '', '### เวลาต่อภาพและเวลารวม', '',
        'ROI คือภาพย่อยของบุคคลหนึ่งรายการ เวลา parsing ต่อภาพได้จากผลรวม adapter ของทุก ROI ในภาพนั้น ค่าเฉลี่ยต่อภาพทั้งชุดนำผลรวมนี้หารจำนวนภาพ รวมภาพที่ YOLO ให้ศูนย์ ROI ซึ่งมีเวลาเรียก parser เท่ากับศูนย์ ส่วนภาพที่มี ROI แต่ขาด timer เก็บเป็น null แต่ละ call ทำนาย native classes พร้อมกัน แล้วจึงแปลงเป็นสี่ target จึงมีเวลารวมต่อ ROI', '',
        '| Dataset | โมเดล | ภาพที่มีเวลาครบ | ROI ที่มีเวลา | เฉลี่ยต่อภาพทั้งชุด ms | รวม parsing ทั้งชุด s | รวมช่วงที่มี log s |',
        '|---|---|---:|---:|---:|---:|---:|']
    def number(value):
        return f'{value:.3f}' if value is not None else 'null'
    for dataset in ['CIHP', 'CCTV']:
        for model_id in order:
            if dataset == 'CIHP':
                t = cihp[model_id]
            else:
                t = dict(cctv[model_id]['per_image_summary'],
                    ROI_population=cctv[model_id]['ROI_population'],
                    timed_ROIs=cctv[model_id]['time_accounting']['timed_ROIs'])
            lines.append(f'| {dataset} | {names[model_id]} | {t["images_with_complete_timing"]}/{t["expected_images"]} | {t["timed_ROIs"]}/{t["ROI_population"]} | '+
                ' | '.join(number(t[k]) for k in ['full_population_mean_ms_per_image','full_population_parsing_work_seconds','recorded_interval_sum_seconds'])+' |')
    lines += ['', 'CIHP ใช้ synchronized adapter_total จาก FRAME_COMMITTED ของ accepted segments จับเวลาด้วยนาฬิกาวัดระยะเวลาและรอ CUDA ที่ขอบ span ตรวจเวลาได้ครบ 5,000 ภาพและ 24,062 ROI ต่อโมเดล โดยใช้เฉพาะ frame record ที่ผูกกับ accepted packet ของภาพนั้น ผลรวมนี้นับช่วง adapter ที่สำเร็จของแต่ละ ROI หนึ่งครั้ง', '',
        'CCTV ใช้สถิติ runtime ที่ตรวจรับเดิม เวลา A จับรอบ adapter ด้วยนาฬิกาวัดระยะเวลา เวลา B ใช้ event จบลบ event เริ่มของ continuation ซึ่งรวมการรอ GPU และการเขียน resource log ด้วย ผลรวม A+B ใช้เป็นบัญชีช่วงเวลาที่บันทึกได้ Sapiens นำผลเดิม 15 ROI จาก 6 ภาพกลับมาใช้ จึงมี timing ครบ 84/90 ภาพ เวลา native forward จากรอบเก่ามีขอบเขตอีกแบบและเก็บแยกไว้', '',
        'ภายใน adapter รวม preprocessing การส่งข้อมูล การคำนวณโมเดล และ map-back ตาม implementation ของแต่ละตัว CPI รวม native file I/O ด้วย ช่วงนี้อยู่หลัง YOLO cache/crop ที่ใช้ร่วมกัน ขั้นนำ mask ไปวางบนภาพ กำหนด ownership ส่งออก packet ให้คะแนน และสกัดสีอยู่ภายนอก adapter การใช้ GPU ร่วมและหลาย segments มีผลต่อเวลาที่สังเกต จึงรายงานเป็น timing diagnostics', '',
        '### รายละเอียดช่วงเวลาที่ CIHP บันทึกได้', '',
        'แต่ละช่องแสดงค่าเฉลี่ย ms ต่อ ROI ที่มี timer ของช่วงนั้น พร้อมจำนวน ROI ในวงเล็บ ช่วงย่อยอยู่ภายใน adapter_total และบางช่วงซ้อนกัน ตารางคงช่วง native call แบบ inclusive ตามที่ instrument ไว้', '',
        '| โมเดล | เตรียม input | native call หรือ backbone+head | map-back | adapter รวม |',
        '|---|---:|---:|---:|---:|']
    for model_id in order:
        stages = cihp[model_id]['stages']
        def cell(stage):
            row = stages.get(stage)
            return f'{row["mean_ms"]:.3f} ({row["n"]:,})' if row else 'null'
        native = cell('native_model_call') if 'native_model_call' in stages else cell('native_model_call_inclusive')
        if 'parser_backbone' in stages and 'parser_head' in stages:
            native = cell('parser_backbone')+' + '+cell('parser_head')
        lines.append(f'| {names[model_id]} | {cell("parser_preprocess")} | {native} | {cell("parser_mapback")} | {cell("adapter_total")} |')
    lines += ['', '[ขอบเขตเวลาและบัญชี worker ของ CCTV](../../CCTV_Human_Parsing_Benchmark/reports/CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md#ความเร็วและเวลาประมวลผลจาก-log-เดิม) · [การจับเวลา CIHP](../src/controlled_ci_hp/measurement.py) · [จุดบันทึกต่อภาพ](../scripts/controlled_cihp.py)', '',
        'ไฟล์ aggregate index เก็บ hash ของ ledgers และผลสรุปแยกตาม stage ส่วน summary CSV เพิ่ม Macro4-local และเวลาต่อภาพพร้อม coverage ให้ตรวจค่าก่อนปัดเศษได้']
    formatted = []
    previous_table = False
    for line in lines:
        is_table = line.startswith('|')
        if formatted and line and formatted[-1] and not (is_table and previous_table):
            formatted.append('')
        formatted.append(line)
        previous_table = is_table
    block = '\n'.join(formatted)
    report = H/'reports/CIHP_CCTV_COMPARABILITY_REVIEW_TH.md'
    text = report.read_text()
    marker_start = '<!-- FOUR_TARGET_RUNTIME_START -->'
    marker_end = '<!-- FOUR_TARGET_RUNTIME_END -->'
    if marker_start in text:
        start = text.index(marker_start)
        end = text.index(marker_end, start)+len(marker_end)
        text = text[:start]+text[end:]
    text = text.replace('ค่าเฉลี่ยสามคลาสและ Face-local แสดงแยกกัน ไม่มีคะแนนถ่วงน้ำหนักรวมสี่คลาสใหม่.',
        'ตารางนี้แสดงค่าเฉลี่ยสามคลาสและ Face-local แยกกัน ส่วน Macro4-local ที่ผู้ใช้ขอเพิ่มอยู่ในตารางถัดไป')
    text = text.replace('รายงานคะแนนสูงสุดราย target ค่าเฉลี่ยสามคลาส และ Face แยกกัน ไม่มีคะแนนรวมสี่คลาสใหม่ ตัวเลือกที่แนะนำอ้างอิง reference ชุดนี้ ยังไม่ใช่การรับรองสำหรับใช้งานจริง.',
        'อ่านคะแนนราย target และค่าเฉลี่ยสามคลาสประกอบ Macro4-local ที่เพิ่มตามคำขอผู้ใช้ เพื่อพิจารณา configuration ตามเป้าหมายงาน')
    text = text.replace(END, marker_start+'\n\n'+block+'\n\n'+marker_end+'\n\n'+END)
    report.write_text(text)
    csv_path = H/'metrics/SHARED_REFERENCE_SUMMARY.csv'
    with csv_path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary_rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(summary_rows)
    public['reporting_supplement'] = dict(created_thai=now,
        Macro4_local_definition='Equal mean of Hair, Face-local, Upper, Lower mean-part IoUs',
        user_requested_post_results=True, leaders=leaders,
        CIHP_timing=cihp, CCTV_timing=cctv, timing_input_hashes=timer_inputs,
        CCTV_runtime_snapshot_sha256=hashlib.sha256(json.dumps(state['historical_four_target_state']['runtime_reporting'], sort_keys=True).encode()).hexdigest(),
        report_source_sha256=sha(__file__),
        score_statistics_sha256=sha(root/'RESULTS.json'), new_model_calls=0)
    index_path.write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status='REPORT_SUPPLEMENT_COMPLETE', leaders=leaders,
        CIHP_timing_coverage={mid:[t['images_with_complete_timing'],t['timed_ROIs']] for mid,t in cihp.items()})))



def collect_confusion_rows(root, public):
    """Aggregate saved task counts, preserving the accepted domains and pairing."""
    import math
    con = sqlite3.connect('file:'+str(root/'RESULTS.sqlite3')+'?mode=ro', uri=True)
    totals = {}
    membership = {}
    checked = 0
    for dataset, model_id, image_id, value in con.execute(
            'SELECT dataset,model,image_id,result FROM results ORDER BY dataset,model,image_id'):
        frame = json.loads(value)
        if frame['image_id'] != image_id:
            raise ValueError('Frame membership differs')
        membership.setdefault((dataset, model_id), set()).add(image_id)
        for part in frame['parts']:
            key = (dataset, model_id, part['target'])
            row = totals.setdefault(key, dict(GT_parts=0, TP=0, FP=0, FN=0, TN=0,
                zero_overlap_parts=0, unmatched_GT_parts=0, perfect_parts=0, IoU_sum=0.))
            if min(part[k] for k in ['TP','FP','FN','TN']) < 0:
                raise ValueError('Negative confusion count')
            expected_iou = part['TP']/(part['TP']+part['FP']+part['FN'])
            if not math.isclose(expected_iou, part['IoU'], abs_tol=1e-14):
                raise ValueError('Stored part formula differs')
            row['GT_parts'] += 1
            for name in ['TP','FP','FN','TN']:
                row[name] += part[name]
            row['zero_overlap_parts'] += int(part['TP'] == 0)
            row['unmatched_GT_parts'] += int(part['unmatched'])
            row['perfect_parts'] += int(part['FP'] == part['FN'] == 0)
            row['IoU_sum'] += expected_iou
            checked += 1
    con.close()
    sources = read(root/'SOURCES.json')
    rows = []
    for dataset in ['CIHP','CCTV']:
        for model_id, model in public['models'][dataset].items():
            if (not model['strict_complete'] or
                    membership[dataset, model_id] != set(sources[dataset]['expected'])):
                raise ValueError('Exact accepted population required')
            for target_id, target in [(2,'Hair'),(1,'Face_local'),(3,'Upper'),(4,'Lower')]:
                derived = totals[dataset, model_id, target_id]
                accepted = model['targets'][target]
                for name in ['GT_parts','TP','FP','FN','unmatched_GT_parts']:
                    if derived[name] != accepted[name]:
                        raise ValueError('Stored confusion differs from accepted result')
                if not math.isclose(derived['IoU_sum']/derived['GT_parts'],
                                    accepted['mean_part_IoU'], abs_tol=1e-12):
                    raise ValueError('Mean-part IoU differs')
                row = dict(dataset=dataset, model_id=model_id, target=target, **accepted,
                    TN=derived['TN'], valid_task_pixels=sum(derived[k] for k in ['TP','FP','FN','TN']),
                    zero_overlap_parts=derived['zero_overlap_parts'], perfect_parts=derived['perfect_parts'])
                row['missed_GT_pixel_fraction'] = row['FN']/row['GT_pixels']
                rows.append(row)
        for target in ['Hair','Face_local','Upper','Lower']:
            domains = {(r['GT_parts'],r['GT_pixels'],r['valid_task_pixels']) for r in rows
                       if r['dataset']==dataset and r['target']==target}
            if len(domains) != 1:
                raise ValueError('Evaluation domain depends on model')
    return rows, checked


def plot_shared_confusion(rows, dataset, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    models = list(dict.fromkeys(r['model_id'] for r in rows if r['dataset']==dataset))
    lookup = {(r['model_id'],r['target']):r for r in rows if r['dataset']==dataset}
    targets = ['Hair','Face_local','Upper','Lower']
    fig, axes = plt.subplots(9, 4, figsize=(17, 26))
    for i, model in enumerate(models):
        for j, target in enumerate(targets):
            row = lookup[model,target]
            matrix = np.array([[row['TP'],row['FN']],[row['FP'],row['TN']]], dtype=np.int64)
            denominators = matrix.sum(axis=1, keepdims=True)
            percentages = np.divide(matrix*100., denominators,
                out=np.full((2,2),np.nan), where=denominators!=0)
            ax = axes[i,j]
            ax.imshow(percentages, vmin=0, vmax=100, cmap='Blues', aspect='auto')
            for y in range(2):
                for x in range(2):
                    label = [['TP','FN'],['FP','TN']][y][x]
                    percent = f'{percentages[y,x]:.2f}%' if np.isfinite(percentages[y,x]) else 'n/a'
                    ax.text(x,y,f'{label} {matrix[y,x]:,}\n{percent}',ha='center',va='center',
                            fontsize=8,color='white' if percentages[y,x]>55 else '#152238')
            ax.set_title(target.replace('_','-')+f' | parts={row["GT_parts"]:,}',fontsize=10)
            ax.set_xticks([0,1],['Pred target','Pred other'],fontsize=7)
            ax.set_yticks([0,1],['GT target','GT other'],fontsize=7)
            if j==0:
                ax.set_ylabel(LABELS[i], fontsize=11, fontweight='bold', labelpad=10)
    fig.suptitle(dataset+' | current shared-reference binary confusion | 9 models x 4 targets\n'+
        'Cell counts + row-normalized percentages. Face-local uses tight GT boxes.',fontsize=14,y=.998)
    fig.tight_layout(rect=[0,.025,1,.977],h_pad=1.1,w_pad=1.6)
    fig.text(.5,.007,'Counts pool positive-person-part tasks. Task domains can reuse image pixels. '
             'Hair/Upper/Lower use GT-valid task domains; Face uses local boxes.',
             ha='center',fontsize=8)
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=140,bbox_inches='tight',pad_inches=.15)
    plt.close(fig)


def current_diagnostics_section(public, rows, dataset, names, figure_link, csv_link, index_link):
    lines = ['## Confusion matrix และความครบของแต่ละส่วน', '',
        'ภาพชุดนี้สร้างจากสถิติรายส่วนของ shared-reference run ล่าสุด เก็บ binary confusion แยก target โดยแถวเป็น GT และคอลัมน์เป็น prediction เรียง target ก่อน other จึงได้ **[[TP, FN], [FP, TN]]** ตัวเลขในช่องเป็นจำนวนพิกเซล ส่วนสีและเปอร์เซ็นต์หารด้วยผลรวมของ GT แต่ละแถว', '',
        f'![{dataset} shared-reference confusion matrices]({figure_link})', '',
        'TP คือทายส่วนที่ต้องการถูก FN คือส่วน GT ที่ทายขาด FP คือทายเกินบนส่วนอื่นในพื้นที่ประเมิน และ TN คือพื้นที่อื่นที่ทายเป็นอื่น แต่ละ target มีงานราย GT person-part ของตนเอง พิกเซลของภาพเดียวกันอาจถูกประเมินในหลายงานตามเจ้าของ GT ตารางรวมพิกเซลตามงานเหล่านี้', '',
        '**Recall = TP/(TP+FN)** บอกว่าเก็บพิกเซล GT ได้ครบเท่าไร **Precision = TP/(TP+FP)** บอกว่าพิกเซลที่ทายมาถูกเท่าไร และ **F1/Dice = 2TP/(2TP+FP+FN)** สรุปทั้งการทายเกินและทายขาด ค่าด้านล่างรวม counts ก่อนหาร ส่วน mean-part IoU ในตารางคะแนนเฉลี่ยแต่ละส่วนเท่ากัน', '',
        '| โมเดล | Target | Precision % | Recall % | F1/Dice % | GT parts | ไม่ทับ GT เลย | ในจำนวนนั้นจับคู่คนไม่ได้ |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    selected = [r for r in rows if r['dataset']==dataset]
    for r in selected:
        lines.append(f'| {names[r["model_id"]]} | {r["target"]} | {pct(r["precision"])} | {pct(r["recall"])} | {pct(r["F1_Dice"])} | {r["GT_parts"]:,} | {r["zero_overlap_parts"]:,} | {r["unmatched_GT_parts"]:,} |')
    lines += ['', '“ไม่ทับ GT เลย” หมายถึง TP = 0 ของส่วนที่มี GT ส่วน “จับคู่คนไม่ได้” เป็นกลุ่มย่อยของรายการเหล่านั้นและยังนับพิกเซล GT เป็น FN กรณีที่จับคู่คนได้แต่ TP = 0 อาจเป็นผลว่าง ผิดคลาส ผิดตำแหน่ง หรือผิด ownership ต้องดู masks ประกอบเพื่อแยกสาเหตุ', '',
        '| โมเดล | Target | TP px | FP px | FN px | TN px | GT support px | Union px | GT พิกเซลที่พลาด % |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in selected:
        lines.append(f'| {names[r["model_id"]]} | {r["target"]} | '+
            ' | '.join(f'{r[k]:,}' for k in ['TP','FP','FN','TN','GT_pixels','union'])+
            f' | {pct(r["missed_GT_pixel_fraction"])} |')
    lines += ['', 'GT support = TP+FN และ union = TP+FP+FN สัดส่วน GT ที่พลาด = FN/(TP+FN) = 1−Recall ค่า TN อ้างอิงพื้นที่ valid ของงานนั้น และมีขนาดใหญ่มากในงานบางคลาส จึงอ่านความครบควบคู่กับ Precision/Recall/IoU ตามเป้าหมาย', '',
        '## การจับคู่คนและความครบถ้วนของผล', '',
        'ตารางนี้ใช้ YOLO extents ที่ตรึงไว้กับ common geometry matcher ทั้งเก้าโมเดล ค่า person TP คือคู่ที่ผ่าน threshold, FP คือ predicted extent ที่ไม่มีคู่ และ FN คือ GT extent ที่ไม่มีคู่ Person Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN)', '',
        '| โมเดล | Mask IoU threshold | GT คน | Pred คน | TP | FP | FN | Precision % | Recall % | F1 % | Ambiguous frames |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for model_id in names:
        for threshold, loc in public['models'][dataset][model_id]['localization'].items():
            precision = loc['TP']/(loc['TP']+loc['FP']) if loc['TP']+loc['FP'] else None
            recall = loc['TP']/(loc['TP']+loc['FN']) if loc['TP']+loc['FN'] else None
            lines.append(f'| {names[model_id]} | {threshold} | {loc["GT"]:,} | {loc["predictions"]:,} | {loc["TP"]:,} | {loc["FP"]:,} | {loc["FN"]:,} | {pct(precision)} | {pct(recall)} | {pct(loc["F1"])} | {loc["ambiguous"]:,} |')
    lines += ['', 'Person metrics เท่ากันข้ามโมเดลในแต่ละ dataset เพราะใช้ YOLO extents ชุดเดียวกัน ส่วน semantic masks และคะแนนรายส่วนยังต่างกัน สำหรับ CCTV จำนวนคนที่ทายมาแต่ไม่มีคู่ GT อ้างอิงเฉพาะคนที่ annotate ไว้', '',
        '| โมเดล | Expected | Completed | Missing | Duplicate | STRICT_COMPLETE |',
        '|---|---:|---:|---:|---:|---|']
    for model_id in names:
        m = public['models'][dataset][model_id]
        lines.append(f'| {names[model_id]} | {m["expected"]:,} | {m["completed"]:,} | {m["missing"]} | {m["duplicate"]} | {m["strict_complete"]} |')
    lines += ['', '## รายละเอียด timing ที่ตรวจได้', '',
        'ตารางขั้นตอนใช้หน่วย ms ต่อ ROI ที่มี timer ช่วงย่อยอาจอยู่ซ้อนภายใน adapter_total ของโมเดลหนึ่ง call รองรับ native classes ทั้งหมด แล้วจึงแปลงผลเป็นสี่ target', '',
        '| โมเดล | Preprocess ms/ROI | Native call ms/ROI | Map-back ms/ROI | Adapter A ms/ROI (n) | Event B ms/ROI (n) |',
        '|---|---:|---:|---:|---:|---:|']
    for model_id in names:
        if dataset=='CIHP':
            t=public['reporting_supplement']['CIHP_timing'][model_id]
            stages=t['stages']
            def stage(name):
                return f'{stages[name]["mean_ms"]:.3f}' if name in stages else 'null'
            native = stage('native_model_call') if 'native_model_call' in stages else stage('native_model_call_inclusive')
            if 'parser_backbone' in stages:
                native=stage('parser_backbone')+' + '+stage('parser_head')
            a=f'{t["adapter"]["mean_ms"]:.3f} ({t["adapter"]["n"]:,})'
            fields=[stage('parser_preprocess'),native,stage('parser_mapback'),a,'null (0)']
        else:
            t=public['reporting_supplement']['CCTV_timing'][model_id]
            a=t['monotonic_adapter'];b=t['UTC_event_interval']
            fields=['null','null','null',f'{a["mean_ms"]:.3f} ({a["n"]})' if a['n'] else 'null (0)',
                    f'{b["mean_ms"]:.3f} ({b["n"]})' if b['n'] else 'null (0)']
        lines.append(f'| {names[model_id]} | '+' | '.join(fields)+' |')
    lines += ['', 'null ของช่วงย่อยหมายถึง log ของรอบนั้นแยกขั้นตอนนี้ไม่ได้ ขอบเขต A และ B ของ CCTV อธิบายไว้ในตารางเวลาต่อภาพด้านบน CPI มี native file I/O ภายใน adapter และสภาพ GPU ร่วมถูกบันทึกไว้ใน resource policy ของ source run', '',
        '## ที่มาของ configuration และข้อจำกัด', '',
        '| โมเดล | Checkpoint SHA256 prefix | Canonical source reference | Implementation reference |',
        '|---|---|---|---|']
    for model_id in names:
        ref=public['source_configuration_references'][dataset][model_id]
        impl=ref.get('implementation','รายละเอียดใน source config hash '+ref.get('source_config_sha256',''))
        lines.append(f'| {names[model_id]} | `{ref["checkpoint_sha256"][:16]}` | `{ref.get("canonical_metrics",ref.get("canonical_reference"))}` | `{json.dumps(impl,ensure_ascii=False) if isinstance(impl,dict) else impl}` |')
    lines += ['', 'กติกาสี่ target, Face-local, VOID/OTHER, mask matching และวิธีเฉลี่ยใช้ร่วมกันใน CIHP/CCTV โดย GT และ annotation boundaries ยังเป็น reference ของแต่ละชุด การประเมินใช้ส่วนที่มี annotation และ Face ใช้กรอบ GT ของงานนั้น คำอ้างเกี่ยวกับขอบเขตหน้า/คอและ Dress จึงอิงนิยามเหล่านี้', '',
        'ผลเปรียบเทียบ checkpoint พร้อม application configuration ซึ่งรวมข้อมูลฝึก adapter และ implementation revision การแก้หน่วยความจำ CPI มีหลักฐาน parity ตาม revision ของแต่ละ segment ประวัติ OOM และ interruption ยังอยู่ใน source runs การปิดผลครบเป็นสถานะของ assembled cohort', '',
        f'[CSV ราย target พร้อม counts และตัวหาร]({csv_link}) · [Canonical index และหลักฐานการตรวจ]({index_link})']
    return '\n'.join(lines)


def audit_dataset_reports(root):
    import csv
    index_path=H/'reports/SHARED_REFERENCE_RESULT_INDEX.json'
    public=read(index_path)
    if public['result_sha256'] != sha(root/'RESULTS.json'):
        raise ValueError('Score bindings drifted')
    if sha(root/'SOURCES.json') != public['sources_manifest_sha256']:
        raise ValueError('Prediction-source bindings drifted')
    rows,checked=collect_confusion_rows(root,public)
    csv_path=H/'metrics/SHARED_REFERENCE_TARGET_COUNTS.csv'
    with csv_path.open() as stream:
        prior=list(csv.DictReader(stream))
    lookup={(r['dataset'],r['model_id'],r['target']):r for r in rows}
    fields=list(prior[0])+['TN','valid_task_pixels','zero_overlap_parts','perfect_parts','missed_GT_pixel_fraction']
    fields=list(dict.fromkeys(fields))
    with csv_path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
        writer.writeheader()
        for previous in prior:
            r=lookup[previous['dataset'],previous['model_id'],previous['target']]
            # Preserve all previously published aggregate values exactly.
            merged=dict(previous,**{k:r[k] for k in fields if k not in previous})
            writer.writerow(merged)
    names=dict(zip(public['models']['CIHP'],LABELS))
    figures={}
    for dataset,folder,filename in [('CIHP',H,'CIHP_COMMON_NINE_RESULTS_TH.md'),
                                     ('CCTV',C,'CONTROLLED_ROI_FOUR_TARGET_RESULTS_TH.md')]:
        figure=folder/'reports/figures/SHARED_REFERENCE_TARGET_CONFUSION.png'
        plot_shared_confusion(rows,dataset,figure)
        report=folder/'reports'/filename
        prefix='' if dataset=='CIHP' else '../../Human_Parsing_Benchmark/'
        csv_link='../metrics/SHARED_REFERENCE_TARGET_COUNTS.csv' if dataset=='CIHP' else prefix+'metrics/SHARED_REFERENCE_TARGET_COUNTS.csv'
        index_link='SHARED_REFERENCE_RESULT_INDEX.json' if dataset=='CIHP' else prefix+'reports/SHARED_REFERENCE_RESULT_INDEX.json'
        section=current_diagnostics_section(public,rows,dataset,names,
            'figures/SHARED_REFERENCE_TARGET_CONFUSION.png',csv_link,index_link)
        start='<!-- CURRENT_SHARED_DIAGNOSTICS_START -->'
        end='<!-- CURRENT_SHARED_DIAGNOSTICS_END -->'
        text=report.read_text()
        if start in text:
            a=text.index(start);b=text.index(end,a)+len(end)
            text=text[:a]+text[b:]
        insertion=text.index('<!-- SHARED_DATASET_CURRENT_END -->')
        text=text[:insertion]+start+'\n\n'+section+'\n\n'+end+'\n\n'+text[insertion:]
        report.write_text(text)
        figures[dataset]=dict(path=str(figure.relative_to(W)),sha256=sha(figure))
    public['confusion_reporting']=dict(status='CURRENT_SHARED_REFERENCE_72_TARGETS_COMPLETE',
        created_thai=datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Bangkok')).isoformat(),
        part_records_checked=checked, rows=rows, figures=figures,
        matrix_order='[[TP,FN],[FP,TN]]; rows GT, columns prediction; labels target/other',
        source_result_sha256=sha(root/'RESULTS.json'),source_config_sha256=sha(root/'CONFIG.json'),
        source_protocol_sha256=public['protocol_sha256'],report_source_sha256=sha(__file__),
        aggregate_CSV_sha256=sha(csv_path),new_model_calls=0,new_mask_scoring=False,
        checks=['Exact membership for all 18 jobs','72 per-target counts match accepted scores',
                '526086 per-task IoU formulas independently checked','Model-independent GT domains per target',
                'Shared templated report structure for both datasets'])
    index_path.write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status='REPORTS_UPDATED',part_records=checked,targets=len(rows),new_model_calls=0)))



def recover_saved_timers():
    """Account for accepted old forward intervals, preserving timing scopes."""
    import csv
    import math
    index_path=H/'reports/SHARED_REFERENCE_RESULT_INDEX.json'
    public=read(index_path)
    state=read(C/'STUDY_STATE.json')
    historical=state['historical_four_target_state']
    source_csv=C/historical['per_image_timing_reporting']['private_CSV']['path']
    if sha(source_csv)!=historical['per_image_timing_reporting']['private_CSV']['sha256']:
        raise ValueError('Original per-image timing changed')
    closure=read(C/'reports/CONTROLLED_ROI_COMPLETION.json')
    config_path=C/'outputs'/closure['parent_run']/'CONFIG.json'
    config=read(config_path)
    with source_csv.open() as stream:
        frames=list(csv.DictReader(stream))
    observations={}
    input_hashes={str(source_csv.relative_to(W)):sha(source_csv),str(config_path.relative_to(W)):sha(config_path)}
    for model_id, reuse in config['reuse'].items():
        if not reuse:
            continue
        roots={str(Path(ref['packet']).parents[1]) for ref in reuse.values()}
        if len(roots)!=1:
            raise ValueError('Ambiguous original timer segment')
        ledger=W/next(iter(roots))/'ATTEMPTS.jsonl'
        input_hashes[str(ledger.relative_to(W))]=sha(ledger)
        pending={}
        recovered={}
        for line in ledger.read_text().splitlines():
            event=json.loads(line)
            if not str(event.get('purpose','')).startswith('ROI:'):
                continue
            roi_index=int(event['purpose'].split(':')[1])
            job=f'{event["image_id"]}_roi{roi_index:03d}'
            if job not in reuse:
                continue
            key=(event['call'],job)
            if event['event']=='FORWARD_START':
                if key in pending or job in recovered:
                    raise ValueError('Duplicate timer attempt')
                pending[key]=event
            elif event['event']=='FORWARD_END':
                start=pending.pop(key)
                ref=reuse[job]
                path=W/ref['packet']/'packet.json'
                if sha(path)!=ref['metadata_sha256']:
                    raise ValueError('Reused packet metadata drift')
                meta=read(path)
                if (meta['packet_sha256']!=ref['packet_sha256'] or
                        meta['model_id']!=model_id or meta['image_id']!=event['image_id'] or
                        meta['geometry'][roi_index]!=ref['original_geometry']):
                    raise ValueError('Timer/reused geometry binding differs')
                seconds=(datetime.fromisoformat(event['utc'])-datetime.fromisoformat(start['utc'])).total_seconds()
                if not math.isfinite(seconds) or seconds<0:
                    raise ValueError('Invalid original duration')
                recovered[job]=dict(image_id=event['image_id'],seconds=seconds)
        if pending or set(recovered)!=set(reuse):
            raise ValueError('Original timer membership incomplete')
        observations[model_id]=recovered
    totals={}
    for model_id in public['models']['CCTV']:
        selected=[frame for frame in frames if frame['model_id']==model_id]
        if len(selected)!=90 or len({frame['image_id'] for frame in selected})!=90:
            raise ValueError('Per-image population differs')
        original=observations.get(model_id,{})
        values=[]
        for frame in selected:
            restored=[row['seconds'] for row in original.values() if row['image_id']==frame['image_id']]
            if int(frame['timed_ROIs'])+len(restored)!=int(frame['ROI_count']):
                raise ValueError('Double counted or missing ROI timer')
            current=float(frame['observed_interval_ms'])/1000 if frame['observed_interval_ms'] not in ('','null') else 0.
            values.append(math.fsum([current,*restored]))
        old_seconds=math.fsum(row['seconds'] for row in original.values())
        total=math.fsum(values)
        t=public['reporting_supplement']['CCTV_timing'][model_id]
        if not math.isclose(total,t['per_image_summary']['recorded_interval_sum_seconds']+old_seconds,abs_tol=1e-9):
            raise ValueError('Timing accounting sum differs')
        totals[model_id]=dict(images=90,ROI_population=130,timed_ROIs=130,
            original_forward_ROIs=len(original),original_forward_seconds=old_seconds,
            original_forward_mean_ms=old_seconds*1000/len(original) if original else None,
            current_recorded_seconds=t['per_image_summary']['recorded_interval_sum_seconds'],
            all_recorded_intervals_seconds=total,mean_recorded_intervals_seconds_per_image=total/90,
            mean_recorded_intervals_ms_per_ROI=total*1000/130,
            timer_groups='A monotonic adapter + B continuation UTC interval + C original forward UTC interval',
            homogeneous_adapter_latency=False)
    public['complete_timing_accounting']=dict(status='ALL_ACCEPTED_ROIS_HAVE_A_RECORDED_INTERVAL',
        models=totals,input_hashes=input_hashes,source_script_sha256=sha(__file__),new_model_calls=0,
        original_forward_scope='FORWARD_START to FORWARD_END; preprocessing/map-back outside',
        original_adapter_fields_retained=True,
        verification='Exact 90 images/130 ROI per model, 15 original timers disjoint from 115 current Sapiens timers; packet metadata/geometry bindings match; arithmetic cross-check passed')
    index_path.write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
    csv_path=H/'metrics/SHARED_REFERENCE_SUMMARY.csv'
    with csv_path.open() as stream:rows=list(csv.DictReader(stream))
    for row in rows:
        if row['dataset']=='CCTV':
            t=totals[row['model_id']]
            row['recorded_interval_coverage_images']=90
            row['recorded_interval_accounting_mean_s_per_image']=t['mean_recorded_intervals_seconds_per_image']
            row['recorded_interval_accounting_total_s']=t['all_recorded_intervals_seconds']
            row['recorded_interval_scope']=t['timer_groups']
            row['recorded_interval_mean_ms_per_ROI']=t['mean_recorded_intervals_ms_per_ROI']
            row['recorded_interval_coverage_ROIs']=130
        else:
            row['recorded_interval_coverage_images']=5000
            row['recorded_interval_accounting_mean_s_per_image']=float(row['timing_mean_ms_per_image'])/1000
            row['recorded_interval_accounting_total_s']=row['timing_total_seconds']
            row['recorded_interval_scope']='A synchronized adapter_total'
            roi=public['reporting_supplement']['CIHP_timing'][row['model_id']]['ROI_population']
            row['recorded_interval_mean_ms_per_ROI']=float(row['timing_total_seconds'])*1000/roi
            row['recorded_interval_coverage_ROIs']=roi
    with csv_path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
    print(json.dumps(totals,ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--supplement', action='store_true', help='Add equal four-target mean and saved timing')
    mode.add_argument('--audit-reports', action='store_true', help='Publish current confusion and aligned dataset reports')
    mode.add_argument('--recover-timing', action='store_true', help='Recover original accepted ROI forward timers as separate accounting')
    args = parser.parse_args()
    if args.recover_timing:
        recover_saved_timers()
    elif args.audit_reports:
        audit_dataset_reports(args.output.resolve())
    elif args.supplement:
        supplement(args.output.resolve())
    else:
        render(args.output.resolve())
