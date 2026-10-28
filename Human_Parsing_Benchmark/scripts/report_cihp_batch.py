"""Finalize only a terminal native CIHP batch; no inference and no subset ranking."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,csv,hashlib,argparse
P=Path(__file__).resolve().parents[1];W=P.parent

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--run-root',required=True);a=parser.parse_args();out=Path(a.run_root).resolve();launch=json.loads((out/'LAUNCH.json').read_text())
 if launch['status']=='RUNNING':raise RuntimeError('Do not analyze comparative quality while batch active')
 config=json.loads((out/'FROZEN_CONFIG.json').read_text());unit=config['run_id'];expected_ids={x['id'] for x in json.loads((W/config['dataset']['population']).read_text())['members']};audit=json.loads((out/'DATA_READINESS.json').read_text());expected_pixels=sum(audit['semantic_values'].values());summary=[];perclass=[];person=[];failures=[];native=[];verification=[]
 metricsdir=P/'metrics'/unit;metricsdir.mkdir(parents=True,exist_ok=True)
 for mid in config['execution_models']:
  folder=out/'validation'/mid;run=json.loads((folder/'RUN.json').read_text()) if (folder/'RUN.json').exists() else {'status':'NOT_ATTEMPTED','complete':0,'failed':0,'invalid':0,'not_attempted':5000};metrics=json.loads((folder/'METRICS.json').read_text()) if (folder/'METRICS.json').exists() else {};ledger=list(map(json.loads,(folder/'FRAMES.jsonl').open())) if (folder/'FRAMES.jsonl').exists() else []
  ids={x['image_id'] for x in ledger};complete=run['status']=='COMPLETE' and run['complete']==5000 and len(ledger)==5000 and len(ids)==5000 and ids==expected_ids and all(x['status']=='COMPLETE' for x in ledger)
  if run['status']=='COMPLETE' and not complete:raise ValueError('Completeness contradiction '+mid)
  primary=metrics.get('primary') if complete else None
  if complete and primary is None:raise ValueError('Missing strict complete metrics '+mid)
  if primary and sum(primary['GT_pixel_support'])!=expected_pixels:raise ValueError('Pixel denominator mismatch '+mid)
  pm=metrics.get('person_metrics',{}).get('0.5') if complete else None
  if pm and pm['G_loc']!=17520:raise ValueError('Person denominator mismatch '+mid)
  peaks=[x['peak_allocated_MiB'] for x in ledger if x.get('status')=='COMPLETE'];reserved=[x['peak_reserved_MiB'] for x in ledger if x.get('status')=='COMPLETE'];row={'run_id':unit,'model_id':mid,'route':config['models'][mid]['route'],'population':'CIHP_NATIVE_OFFICIAL_VALIDATION_5000','status':'COMPLETE' if complete else 'INCOMPLETE','expected':5000,'complete':run['complete'],'failed':run['failed'],'invalid':run['invalid'],'not_attempted':run['not_attempted'],'mIoU_20_including_BG':primary['mIoU_20_including_BG'] if primary else None,'mIoU_19_foreground':primary['mIoU_19_foreground'] if primary else None,'person_extent_F1_at0.50':pm['extent_F1'] if pm else None,'FP_at0.50':pm['FP'] if pm else None,'FN_at0.50':pm['FN'] if pm else None,'parser_pipeline_ms_mean_complete_population':metrics.get('parser_pipeline_ms_mean') if complete else None,'parser_pipeline_ms_P50_complete_population':metrics.get('parser_pipeline_ms_P50') if complete else None,'parser_pipeline_ms_P95_complete_population':metrics.get('parser_pipeline_ms_P95') if complete else None,'peak_completed_frame_parser_allocated_MiB':max(peaks) if peaks else None,'peak_completed_frame_parser_reserved_MiB':max(reserved) if reserved else None,'full_route_FPS':None,'null_reason':None if complete else 'STRICT_COMPLETE not satisfied; success-only subsets not main scores','resource_scope':'parser-only residency; cachedYOLO, not total pipeline memory/FPS'};summary.append(row)
  for label in range(20):perclass.append({'model_id':mid,'class_id':label,'label':primary['labels'][label] if primary else ['Background','Hat','Hair','Glove','Sunglasses','UpperClothes','Dress','Coat','Socks','Pants','Torso-skin','Scarf','Skirt','Face','Left-arm','Right-arm','Left-leg','Right-leg','Left-shoe','Right-shoe'][label],'IoU':primary['IoU'][label] if primary else None,'GT_pixels':primary['GT_pixel_support'][label] if primary else audit['semantic_values'].get(str(label),0),'predicted_pixels':primary['predicted_pixel_support'][label] if primary else None,'union':primary['union'][label] if primary else None,'status':row['status']})
  for threshold in ['0.5','0.75']:
   values=metrics.get('person_metrics',{}).get(threshold) if complete else None;person.append({'model_id':mid,'threshold':threshold,'status':row['status'],**{k:values.get(k) if values else None for k in ['G_loc','G_sem','TP','FP','FN','extent_precision','extent_recall','extent_F1','Q_person_sem_GT']}})
  ref=metrics.get('native_reference_primary') if complete else None
  if config['models'][mid]['native_reference']:native.append({'model_id':mid,'role':'UNGATED_NATIVE_REFERENCE_NOT_APPLICATION_WINNER','status':row['status'],'mIoU_20_including_BG':ref['mIoU_20_including_BG'] if ref else None,'mIoU_19_foreground':ref['mIoU_19_foreground'] if ref else None})
  for frame in ledger:
   if frame['status']!='COMPLETE':failures.append({'model_id':mid,'image_id':frame['image_id'],'status':frame['status'],'stage':frame.get('failure_stage'),'error_last_line':frame.get('error','').strip().splitlines()[-1] if frame.get('error') else None,'external_log':str((folder/'FRAMES.jsonl').relative_to(W))})
  if run.get('error'):failures.append({'model_id':mid,'image_id':None,'status':run['status'],'stage':'MODEL_LOAD_OR_SETUP','error_last_line':run['error'].strip().splitlines()[-1],'external_log':str((folder/'RUN.json').relative_to(W))})
  verification.append({'model_id':mid,'strict_completeness_verified':complete,'unique_terminal_frames':len(ids),'histogram_support_verified':bool(primary),'packet_files_from_terminal_ledger':'Preserved with per-packet SHA256; not a second full bulk rehash in finalizer'})
 def write_csv(name,rows,fields=None):
  if not rows:fields=fields or ['model_id','image_id','status','stage','error_last_line','external_log']
  else:fields=list(rows[0])
  with (metricsdir/name).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
 write_csv('SUMMARY.csv',summary);write_csv('PER_CLASS.csv',perclass);write_csv('PERSON_METRICS.csv',person);write_csv('FAILURES.csv',failures);write_csv('NATIVE_REFERENCE.csv',native)
 complete_all=all(x['status']=='COMPLETE' for x in summary);status='FINISHED_COMPLETE' if complete_all else 'FINISHED_WITH_INCOMPLETE_SYSTEMS';report=P/'reports'/unit;report.mkdir(parents=True,exist_ok=True)
 text=f'''# ผลทดสอบ CIHP native — หก checkpoints แรก

Status: **{status}** · {datetime.now(timezone.utc).isoformat()}
Run `{unit}`. Actual launch codecommit `{launch['code_publication_commit']}`. Frozen configSHA256 `{launch['config_sha256']}`. Source [PLAN](../../PLAN.md), compact [completion](../../runs/{unit}/COMPLETION.json). Dataset officialCIHPnativeVAL5000, nativeGT17520persons. This is a configured-system/YOLO-conditioned comparison using native labelspace, not architecture-only causality or an official parsingAP reproduction.

| System | Status | Complete/5000 | Failed | Invalid | Pending | mIoU20 inclBG | FG19mIoU |
|---|---|---:|---:|---:|---:|---:|---:|
'''
 for row in summary:
  def fmt(v):return 'N/A' if v is None else f'{100*v:.3f}%'
  text+=f"|{row['model_id']}|{row['status']}|{row['complete']}|{row['failed']}|{row['invalid']}|{row['not_attempted']}|{fmt(row['mIoU_20_including_BG'])}|{fmt(row['mIoU_19_foreground'])}|\n"
 text+='''
## วิธีอ่านผลและข้อจำกัด

- ใช้ STRICT_COMPLETE: ระบบที่ไม่ครบประชากรมีคะแนนหลัก null ไม่จัดอันดับจากชุดภาพสำเร็จที่ต่างกัน จะเรียกหกตัวครบได้เมื่อทุกแถว COMPLETE เท่านั้น ยังไม่ใช่ผลครบเก้าตัว และยังไม่รัน Sapiens หรือปรับ mapping/threshold/precision จาก VAL
- รายงาน IoU/support รายคลาส และ person-mask FP/FN/F1 ที่ threshold 0.50/0.75 แยกจาก semantic mIoU เพราะ semantic Q ไม่ลงโทษ unmatched FP โดยตรง Native references ห้าระบบใช้ผล inference เดียวกัน ไม่เพิ่มผู้สมัคร application หรือรันซ้ำ
- คะแนนหลัก native20 รวม background; FG19 เป็นคะแนนรอง ใช้ zero-union=0 ตาม reference ที่ประกาศไว้ Native Dress6 ไม่ใช่ CCIHP FaceMask6 เก็บ Face/Hair/เสื้อผ้าครบ native classes และไม่แบ่ง Dress เป็น upper/lower ด้วย heuristic
- คง 39 กลุ่มภาพ train–VAL ที่ bytes ซ้ำและหนึ่งกลุ่มซ้ำภายใน VAL ตาม official population ประวัติ training/selection exposure บางส่วนยัง UNKNOWN ไม่ใช่ NO GT native CIHP ต่างจาก CCIHP จึงไม่เทียบ raw scores กับผล taxonomy เดิมโดยตรง ทุกคะแนนอ้างอิง released annotations รวมข้อจำกัดคนพื้นหลังที่ไม่ได้ annotate
- Latency เป็น inline parser pipeline บนประชากรที่รันครบ หลัง TRAIN warmup และ CUDA synchronization ไม่ใช่ fresh YOLO end-to-end FPS คอลัมน์ peak memory เป็น parser allocated/reserved ของ frames ที่สำเร็จ ไม่ใช่หน่วยความจำระบบทั้งหมดหรือ peak ของ frame ที่ OOM ส่วน GPU monitor ใช้บันทึก contention ไม่ใช่หลักฐาน clean repeated timing
- เก็บ integer masks/extents/person scores/unowned outputs/geometry และ hashes ของ input/checkpoint/source/environment พร้อม attempt ledger ภายนอก Git ไม่เก็บ full logits จึงไม่อ้าง probability re-scoring Native confidence export รอบนี้จำกัดที่ canonical person-score outputs; quality-head scores เพิ่มเติมไม่ได้อ้างว่าเก็บครบ และ AP/PCP parity เป็น N/A

## หลักฐานและงานที่เหลือ

Canonical CSV/JSON tables under metrics/runID andruns/runID;externalbulkrootshownincompletionmanifest.Failed/incompletecandidatesremainvisible;errortracesandpendingIDsareintact.NoautoOOMretry/CPU/FP16fallbackoroldCPIresultrepair.Ninja/Sapiens/color/CCTV/traininguntouched.
'''
 text+= ('\nหกตัวรันครบประชากรนี้แล้ว ขั้นถัดไปคือ semantic matrix ระหว่าง native CIHP กับ Sapiens ก่อนเปรียบเทียบ Sapiens ไม่ใช่การยืนยันความพร้อมบน CCTV อิสระ\n' if complete_all else '\nงานที่เหลือ: ตรวจสาเหตุ failure/contract/resource ที่บันทึกไว้ และกำหนดการแก้แบบมี version แยก ไม่ retry failed images อัตโนมัติหรือเรียกว่าหกตัวครบ ผลของระบบอิสระที่รันครบยังคงเก็บไว้ตาม protocol เดิม\n')
 with (report/'REPORT_TH.md').open('x') as f:f.write(text)
 state={'run_id':unit,'status':status,'end_utc':datetime.now(timezone.utc).isoformat(),'launch_commit':launch['code_publication_commit'],'launch_config_sha256':launch['config_sha256'],'expected_models':6,'complete_models':sum(x['status']=='COMPLETE' for x in summary),'summary':summary,'verification':verification,'artifact_root':str(out.relative_to(W)),'source_authority':config['authority'],'report':str((report/'REPORT_TH.md').relative_to(P)),'full_nine_completed':False,'Sapiens_started':False,'model_retries':0,'source_GT_or_previous_results_modified':False}
 rp=P/'runs'/unit;rp.mkdir(parents=True,exist_ok=True)
 with (rp/'COMPLETION.json').open('x') as f:json.dump(state,f,indent=2);f.write('\n')
 with (P/'WORK_LOG.md').open('a') as f:f.write(f'\n## {state["end_utc"]} — {unit}:nativefirstsixterminal\n\nActualstatus{status};complete_models{state["complete_models"]}/6,official5000each.Mainmetricsnullforincompleterows;perclass/person/native-reference/failuretablesgeneratedfromterminalledgersonly.NoSapiens/Ninja/color/training/CCTV.Nonewinferencefromfinalizer.Launchcommit{launch["code_publication_commit"]}.Nextreviewreportandremainingfailures/matrix,notautomaticfailed-image retry.\n')
 print(status,'complete_models',state['complete_models'],flush=True)
if __name__=='__main__':main()
