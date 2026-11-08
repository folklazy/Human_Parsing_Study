"""Publish aggregate shared-view tables only after the CPU cohort is terminal."""
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import argparse
import hashlib
import json
import shutil

H=Path(__file__).resolve().parents[1];W=H.parent;C=W/'CCTV_Human_Parsing_Benchmark'
LABELS=['QANet','M2FP','D2FP','RP-R-CNN','CPI R50','CPI ConvNeXt-B','Sapiens2 0.4B','Sapiens2 0.8B','Sapiens2 1B']
START='<!-- SHARED_REFERENCE_CURRENT_START -->';END='<!-- SHARED_REFERENCE_CURRENT_END -->'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pct(v):return f'{v*100:.3f}' if v is not None else 'null'


def render(root):
    status=read(root/'STATUS.json')
    if status['status'] not in ['COMPLETE','INCOMPLETE']:raise ValueError('Never analyze ranks while CPU batch is running')
    result=read(root/'RESULTS.json');cfg=read(root/'CONFIG.json');sources=read(root/'SOURCES.json')
    order=cfg['model_order'];names=dict(zip(order,LABELS));now=datetime.now(timezone.utc).astimezone(ZoneInfo('Asia/Bangkok')).isoformat()
    public=dict(result,artifact_root=str(root.relative_to(W)),GT_summary=cfg['GT_summary'],protocol=cfg['protocol'],
        scorer_source_hashes=cfg['source_hashes'],result_sha256=sha(root/'RESULTS.json'),
        sources_manifest_sha256=cfg['sources_sha256'],CPU_integration=read(root/'CPU_INTEGRATION.json'),
        report_source_sha256=sha(__file__),source_configuration_references={d:{mid:{k:v for k,v in m.items() if k!='packets'} for mid,m in s['models'].items()} for d,s in sources.items()})
    (H/'reports/SHARED_REFERENCE_RESULT_INDEX.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
    for filename,dest in [('SUMMARY.csv','SHARED_REFERENCE_SUMMARY.csv'),('TARGET_COUNTS.csv','SHARED_REFERENCE_TARGET_COUNTS.csv')]:
        shutil.copyfile(root/filename,H/'metrics'/dest)
    lines=[f'## ผลล่าสุด: สามคลาสหลัก + Face-local — {now}',
        f'**{result["status"]}** — run `{root.name}`. ใช้ saved predictions ของ controlled YOLO person-ROI ทั้งเก้า checkpoints; **ไม่มี inference ใหม่**. ผล CIHP/CCTV อยู่คนละตารางและไม่รวมเป็นคะแนนเดียว. กติกาใหม่ตรึงก่อนคำนวณ แต่จัดทำหลังเห็นผลเดิมแล้ว จึงเป็นการวิเคราะห์ exploratory ไม่ใช่ preregistered confirmation.',
        '### นิยามที่ใช้อธิบายร่วมกัน',
        '**สามคลาสหลัก:** วัด IoU ของส่วน Hair/Upper/Lower ของ GT แต่ละคนที่มี annotation แล้วเฉลี่ยภายในคลาส จากนั้นเฉลี่ยสามคลาสเท่ากัน เรียก **mIoU3 (part-mean)**. ตัวนี้ไม่ใช่ global C3 เดิม และไม่ใช่ full-scene semantic mIoU. ขอบเขตที่ส่งออกของโมเดลยังเป็น native classes ทั้งหมด; Upper/Lower projection ไม่รวม Dress/Apparel.',
        '**Face-local:** รวม Face ของ CIHP หรือ Face_Neck+รายละเอียดใบหน้าของ Sapiens เป็น face candidate แล้วคิด IoU ภายในกรอบสี่เหลี่ยมครอบ GT Face พอดี ใช้กรอบเดียวกันทุกโมเดลในคน/ภาพเดียวกัน ไม่มี margin. **ภายในกรอบส่วนเกินยังเป็น FP; GT ที่ทายขาดเป็น FN; นอกกรอบไม่ประเมิน**. เฉลี่ยราย GT Face ที่มีสิทธิ์ทุกคน รวมคนที่ระบบพลาดเป็นศูนย์ ไม่ได้ตัด prediction ตามรูปทรง GT.',
        'การจับคู่คนใช้ mask IoU0.50 แบบ one-to-one, maximum cardinality→sum IoU→geometry-canonical ties เหมือนกันทั้งสองชุด;0.75เป็นdiagnostic. Extentแยกจากsemantic-valid domain. Missingtargetpolygonไม่ถูกนับว่าconfirmedabsentและไม่สร้างnegative taskใหม่. GT-onlyVOID/ownerambiguityใช้เหมือนกันทุกโมเดล ไม่มีการยกเว้นคอเฉพาะSapiens.',
        '### ประชากรและตัวหารที่อ่านจาก GT จริง',
        '| Dataset | ภาพ/โมเดล | GT persons | Hair parts | Upper parts | Lower parts | Face parts |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for d in ['CIHP','CCTV']:
        g=cfg['GT_summary'][d];n=g['eligible_positive_parts']
        lines.append(f'| {d} | {g["images"]:,} | {g["GT_persons"]:,} | {n.get("2",0):,} | {n.get("3",0):,} | {n.get("4",0):,} | {n.get("1",0):,} |')
    lines+=['CCTVใช้ annotation90ภาพที่ผู้ใช้ตรวจรับแล้ว และ owner corrections ที่มีหลักฐาน ไม่ใช้ชุดคัด269non-Face/21Faceหรือกติกายกเว้นNeckของรายงานเก่า. Pixel ambiguity ระหว่างperson/targetsถูกกำหนดเป็นsharedVOIDจากGTก่อนคำนวณ ไม่เลือกจากคะแนนโมเดล. GTคนและGTpartsของทั้งสองdatasetต่างกัน จึงเปรียบเทียบอันดับภายในแต่ละชุด ไม่อ้างว่าคะแนนต่างข้ามชุดเป็นdomain gapล้วนๆ.',
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
            lines.append('**คะแนนสูงสุดในชุดนี้:** '+'; '.join(f'{t}: {names[v["model_id"]]} ({pct(v["score"])}%, ต่างอันดับสอง {v["delta_percentage_points"]:.3f} pp)' for t,v in leaders[d].items())+'.')
    lines+=['### การจับคู่คน — diagnostic ของ GT reference และ YOLO extents',
        'คะแนนต่อส่วนไม่ได้ลงโทษ unmatched predictions โดยตรง จึงต้องอ่านจำนวนการจับคู่ควบคู่. ตัวเลขนี้ไม่ใช่native instance capabilityของparser;extentsมาจากYOLOที่ตรึงไว้. CCTVเป็นGTของคนที่annotate ไม่ใช่คำรับรองscene-level detectorprecision.',
        '| Dataset | Model | threshold | TP | FP | FN | F1 % |', '|---|---|---:|---:|---:|---:|---:|']
    for d in ['CIHP','CCTV']:
        for mid in order:
            for threshold,v in result['models'][d][mid]['localization'].items():
                lines.append(f'| {d} | {names[mid]} | {threshold} | {v["TP"]:,} | {v["FP"]:,} | {v["FN"]:,} | {pct(v["F1"])} |')
    lines+=['### สูตร วิธีอ่าน และไฟล์ตรวจตัวเลข',
        '- **IoUต่อส่วน = TP/(TP+FP+FN)**; ค่าmean-partIoUเฉลี่ยแต่ละGTpartเท่ากัน ส่วนpooledIoUรวมพิกเซลก่อนหาร จึงอาจต่างกันมาก.',
        '- **Precision = TP/(TP+FP)**, **Recall = TP/(TP+FN)**, **F1/Dice = 2TP/(2TP+FP+FN)**. P/R/F1ในCSVคำนวณจากpooledcountsภายในdomainเดียวกัน ไม่ใช่แปลงจากmeanIoU.',
        '- ไม่มีGTpositiveให้targetนั้นไม่สร้างparttask; denominator0เป็นnull. GTpositiveที่จับคู่คนไม่ได้ให้IoU0. KnownDress/Apparelเป็นOTHER; unknownnativeID/255เป็นcontractfailure ไม่ใช่ignore.',
        '- [ตารางสรุปก่อนปัดเศษ](../metrics/SHARED_REFERENCE_SUMMARY.csv), [TP/FP/FN,GTsupport,union,P/R/F1ครบ72รายการ](../metrics/SHARED_REFERENCE_TARGET_COUNTS.csv), [canonical aggregateและprovenance](SHARED_REFERENCE_RESULT_INDEX.json), [protocolที่ตรึง](../protocol/SHARED_C3_FACE_LOCAL_V1.json).',
        '### การตรวจและข้อจำกัด',
        f'CPU acceptance13กรณีผ่าน รวมactualpacket→scorer→reporter และexpectedFP/FNจากtinyfixtures. Bounded actualCCTV63recordsผ่าน;ตรวจCIHPsavedpacketจริง9โมเดลหนึ่งภาพและC3countsตรงscorerเดิม;resumeรักษา63recordsเดิมและเพิ่ม9โดยไม่ซ้ำ. Fullrunใช้SQLiteunique(dataset,model,image),atomicimage transactions,source/protocolfingerprintsและimmutableevents. CanonicalCPUresultsอยู่private `{root.relative_to(W)}/`.',
        'STRICT_COMPLETEตรวจexact5,000CIHP/90CCTV IDsต่อcheckpoint; primarynullหากขาด/ซ้ำ/fail. ไม่ใช้subsetแทนชุดเต็มและไม่เลือกoutputจากคะแนนดีที่สุด. HistoricalOOM/interrupt/timeguardของinferenceเดิมยังเก็บไว้;CPUcompleteไม่ได้แปลว่าไม่เคยล้มเหลว.',
        'Face-localไม่ลงโทษผลเกินนอกกรอบ จึงไม่ใช่full-imageFaceIoUหรือการรับรองface-onlyแยกคอสมบูรณ์. ชื่อFace/Face_Neckและannotationpartitionยังต่างกันได้;ใช้การวัดreference-localเดียวกัน ไม่อ้างtaxonomy equivalent. CCTVGTเป็นuser-reviewed/model-assistedreference ไม่ใช่independentexpertgold;ส่วนmissingannotationไม่ได้กลายเป็นscenebackground.',
        'ผลเป็นpretrainedcheckpoint+applicationconfiguration บนแต่ละdataset ไม่แยกarchitecture/trainingdata/adapterได้ทั้งหมด. ไม่อ้างstatisticalsignificanceหรือdeployment/colorperformance. Native/C4/globalC3/oldCCTVFace-domainresultsคงเดิมและใช้เป็นhistoricalreferences ไม่เปลี่ยนชื่อคะแนนเก่าให้ดูเป็นคะแนนใหม่นี้. Timingเก่าและCPUwalltimeไม่ใช้จัดlatency/FPS/VRAMefficiencyranking.',
        '### ข้อเสนอสำหรับพรีเซนต์',
        '> เราใช้ YOLO person-ROI pipeline ที่ตรึงไว้ เปรียบเทียบ Hair/Upper/Lower ด้วยค่าเฉลี่ย IoU รายส่วน และวัด Face แยกด้วย IoU ภายในกรอบ Face GT เดียวกันทุกโมเดล โดยใช้กติกาเดียวกันใน CIHP และ CCTV.',
        'รายงานตัวที่ได้คะแนนสูงสุดรายtarget/สามคลาสและFaceแยกกัน ไม่สร้างผู้ชนะสี่คลาสรวมใหม่. ตัวเลือกที่แนะนำเป็นหลักฐานจากreferenceชุดนี้ ยังไม่ใช่deploymentacceptance.']
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
    (root/'REPORT_TH.md').write_text('# ผล shared C3-part / Face-local\n\n'+text+'\n')
    public['leaders']=leaders
    (H/'reports/SHARED_REFERENCE_RESULT_INDEX.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],report=str(report.relative_to(W)),datasets=list(result['models']),model_calls=0)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();render(a.output.resolve())
