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


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();render(a.output.resolve())
