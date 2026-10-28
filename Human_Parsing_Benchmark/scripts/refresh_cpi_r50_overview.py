"""Copy this CPI round's canonical fields into the navigation index; never score."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,csv
P=Path(__file__).resolve().parents[1]

def refresh(source_path,report_text,project=P):
    project=Path(project);source_path=Path(source_path);s=json.loads(source_path.read_text());index_path=project/'manifests/CIHP_NATIVE_COHORT_INDEX.json';index=json.loads(index_path.read_text());mid='CPI_R50_CIHP'
    assert s['model_id']==mid and s['expected']==5000 and s['frozen_config_sha256']==index['frozen_scientific_config_sha256']
    rows=index['models'];assert len(rows)==6 and len({r['model_id'] for r in rows})==6
    for r in rows:
        if r['model_id']!=mid:assert hashlib.sha256((project/r['canonical_source']).read_bytes()).hexdigest()==r['canonical_source_sha256']
    row=next(r for r in rows if r['model_id']==mid);complete=s.get('complete',0);primary=s.get('metrics',{}).get('primary') if s['status']=='COMPLETE' else None
    if s['status']=='COMPLETE':assert complete==5000 and s['missing_IDs']==s['duplicate_IDs']==0 and primary is not None
    row.update(status=s['status'],complete=complete,failed_VAL=s.get('failed',0),invalid_VAL=s.get('invalid',0),not_attempted_VAL=s.get('not_attempted',5000-complete),mIoU_20_including_BG=primary['mIoU_20_including_BG'] if primary else None,mIoU_19_foreground=primary['mIoU_19_foreground'] if primary else None,resource_policy='SHARED_GPU_QUALITY_ONLY',execution_segment_or_record=s['round_id'],canonical_source=str(source_path.relative_to(project)),canonical_source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),timing_rank_eligible=False)
    index['updated_Bangkok']=datetime.now(ZoneInfo('Asia/Bangkok')).isoformat();index['complete_models']=sum(r['status']=='COMPLETE' for r in rows);index['current_round_status']=s['status'];index['current_authorized_model']=mid
    csvpath=project/index['CSV']
    with csvpath.open('w',newline='') as f:writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    index['CSV_sha256']=hashlib.sha256(csvpath.read_bytes()).hexdigest();index_path.write_text(json.dumps(index,indent=2,ensure_ascii=False)+'\n')
    header='## Current cohort overview\n';start=report_text.index(header);end=report_text.find('\n## ',start+len(header));end=len(report_text) if end<0 else end
    text=header+f"\nUpdated {index['updated_Bangkok']}. **{index['complete_models']}/6 complete**, fields copied from canonical records in frozen roster order; no inference/rescoring/ranking. Distinct segments/resource policies remain explicit. [Current CSV](../metrics/CIHP_NATIVE_COHORT_OVERVIEW.csv) / [source index](../manifests/CIHP_NATIVE_COHORT_INDEX.json).\n\n| Model | Status | Complete/5000 | mIoU20 inclBG | FG19 | Segment/resource |\n|---|---|---:|---:|---:|---|\n"
    fmt=lambda v:'null / unavailable' if v is None else f'{100*v:.3f}%'
    for r in rows:text+=f"|{r['model_id']}|{r['status']}|{r['complete']}|{fmt(r['mIoU_20_including_BG'])}|{fmt(r['mIoU_19_foreground'])}|{r['execution_segment_or_record']}; {r['resource_policy']}|\n"
    text+='\nNot a single execution segment or uncontended timing cohort. Native-label YOLO application scores are not official native-parser reproduction; no clean speed/VRAM ranking. Historical source reports and closed-model outputs are preserved.\n'
    return report_text[:start]+text+report_text[end:]
