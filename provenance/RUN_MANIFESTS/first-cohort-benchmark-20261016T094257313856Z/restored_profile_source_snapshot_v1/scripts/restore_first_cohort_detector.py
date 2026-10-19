"""Scoped infrastructure restoration: reuse unchanged native CPI runs; run YOLO once.

This driver is not a general cached re-scoring/resume feature. The scoring body
is copied without changes from the frozen approved validation route.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,subprocess,zipfile
import numpy as np
import sys
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S))
from src.application_v2.policy import load_config,digest,field,fingerprints
from src.application_v2.artifacts import file_hash,commit_packet
from src.application_v2.validation_launch import require_validation_authorization,package_data
from src.application_v2.runner import ConfiguredRunner
from src.application_v2.first_cohort_fresh import _idle,score_committed_packet
from src.application_v2.first_cohort_replay import _arrays
from src.application_v2.validation_data import read_gt
from src.application_v2.evaluation import associate_native
from src.application_v2.contracts import stage_rate
from src.application_v2.validation_launch import population_reports
from src.application_v2.first_cohort_validation import _write


def score_components(config_path,output,ledgers):
    config_path=Path(config_path).resolve();study=config_path.parents[1];workspace=study.parent
    cfg=load_config(config_path,benchmark=True);require_validation_authorization(cfg,study)
    images,templates=package_data(cfg,study)
    launch=cfg['validation_launch'];spec=cfg['first_cohort']['execution_spec']
    dependencies=spec['dependencies'];models=cfg['first_cohort']['models']
    runner=ConfiguredRunner(config_path,mode='VALIDATION_BENCHMARK',benchmark=True,population_role='reference')
    package_dir=(study/cfg['validation_context_packages']['manifest']).parent
    person_groups={}
    for line in (package_dir/'PERSON_GT_BINDINGS.jsonl').read_text().splitlines():
        row=json.loads(line);person_groups.setdefault(row['image_id'],[]).append(row)
    mapping=json.loads((study/cfg['cohort']['mapping']).read_text())
    scores={view:[] for view in ['primary','secondary']}
    detector=next(iter(dependencies));source_zip=workspace/launch['GT_archive_workspace_relative']
    with zipfile.ZipFile(source_zip) as archive:
        for image_index,binding in enumerate(images):
            iid=binding['image_id'];wh=binding['input_binding']['original_wh']
            try:
                gt=read_gt(archive,binding,person_groups[iid],mapping,cfg['first_cohort']['protocol'])
                gt_error=None
            except Exception as error:
                gt_error=dict(status='SHARED_DATA_ERROR',exception=str(error))
            for model in models:
                raw=ledgers[model].get(iid);yolo=ledgers[detector].get(iid)
                failing=[dict(component=name,**(row or dict(image_id=iid,status='NOT_ATTEMPTED')))
                         for name,row in [(detector,yolo),(model,raw)] if not row or row['status']!='COMPLETE']
                if gt_error or failing:
                    base=dict(system_id=model,image_id=iid,execution_status='INVALID' if gt_error or any(r['status']=='INVALID' for r in failing) else 'FAILED',
                        failure_events=([gt_error] if gt_error else [])+failing,score_result=None,
                        stage_rates=dict(native_observed=raw['status'] if raw else 'NOT_ATTEMPTED',detector_observed=yolo['status'] if yolo else 'NOT_ATTEMPTED'))
                    for view in scores:scores[view].append(base)
                    continue
                try:
                    if any(row.get('input_sha256')!=binding['input_binding']['input_sha256'] or row.get('original_wh')!=wh for row in [raw,yolo]):
                        raise ValueError('Native/detector source input differs from scoring context')
                    arrays=_arrays(study/raw['artifact'],raw['artifact_sha256'])
                    detector_arrays=_arrays(study/yolo['artifact'],yolo['artifact_sha256'])
                    masks,boxes=arrays['person_semantic_masks'],arrays['bboxes_xyxy_scores']
                    if masks.shape!=(len(boxes),wh[1],wh[0]) or boxes.shape!=(len(masks),5):raise ValueError('Native output geometry invalid')
                    opportunities=yolo['opportunities']
                    if len(opportunities)!=len(detector_arrays['boxes']):raise ValueError('Detector ledger/array count mismatch')
                    instances=[dict(id=f'native:{i}',bbox=b[:4].tolist()) for i,b in enumerate(boxes)]
                    association=associate_native(opportunities,instances,cfg['first_cohort']['protocol']['matching']['association']['threshold'])
                    persons=[];chosen=[]
                    for link in association['associations']:
                        index=int(link['native_instance_id'].split(':')[-1]);op=next(o for o in opportunities if o['id']==link['source_opportunity_id'])
                        if not np.any(masks[index]):continue
                        chosen.append(masks[index])
                        persons.append(dict(identity=dict(origin='NATIVE_AND_YOLO',native_identity_supported=True,native_instance_id=link['native_instance_id'],
                            conditioning_source='YOLO',source_opportunity_id=op['id'],final_person_id=f'{model}:{iid}:{link["native_instance_id"]}'),
                            conditioning_bbox=op['bbox'],score=float(boxes[index,4]),evaluation_bbox=dict(xyxy=boxes[index,:4].tolist(),source='NATIVE_PARSER_BOX',
                            coordinate_convention='XYXY_HALF_OPEN',derivation_revision=file_hash(Path(__file__)))))
                    record=dict(schema_version='2.0',study_id='human_parsing_mhpv2',run_id=output.name,system_id=model,model_id=model,image_id=iid,
                        source_track='T3B',mask_grid_space='ORIGINAL',original_wh=wh,label_catalog=list(range(20)),label_space='NATIVE',dataset_split='Validation',
                        adapter_revision=file_hash(Path(__file__)),execution_profile='APPROVED_FIRST_COHORT_QUALITY_ONLY',source_commit=spec['parser_systems'][model]['source_commit'],
                        checkpoint_sha256=spec['parser_systems'][model]['checkpoint_sha256'],config_sha256=digest(cfg),input_sha256=binding['input_binding']['input_sha256'],
                        precision_profile=dict(source_native='FP32',autocast=False,TF32=False,latency_claim='NONE'),
                        geometry_metadata=dict(association=association,native_to_original='NATIVE_API_ORIGINAL_GRID_NO_ADDITIONAL_RESIZE'),
                        native_identity_supported=True,native_instance_ids=[r['id'] for r in instances],persons=persons)
                    fp=fingerprints(cfg,dict(native=raw['artifact_sha256'],yolo=yolo['artifact_sha256'],RGB=record['input_sha256'],adapter=record['adapter_revision']))
                    packet=output/'packets'/model/iid
                    commit_packet(packet,record,np.stack(chosen) if chosen else np.empty((0,wh[1],wh[0]),'uint8'),fp,
                        native_arrays=dict(native_person_semantic_masks=masks,native_boxes_scores=boxes))
                    computed={view:score_committed_packet(runner,packet,fp,gt,model,iid,matching_view=view) for view in scores}
                    for view,score in computed.items():
                        scores[view].append(dict(system_id=model,image_id=iid,execution_status='COMPLETE',failure_events=[],score_result=score,
                            stage_rates=dict(native=stage_rate('native_parser','frame',[dict(unit_id=iid,eligible=True,status='COMPLETED')]),
                                association=stage_rate('T3B_association','YOLO_opportunity',[dict(unit_id=o['id'],eligible=True,status='COMPLETED') for o in opportunities]))))
                except Exception as error:
                    for view in scores:
                        scores[view].append(dict(system_id=model,image_id=iid,execution_status='INVALID',failure_events=[dict(status='CONTRACT_FAILURE',exception=str(error))],score_result=None))
            # Persist per-frame score evidence/progress without changing metric math.
            for view in scores:
                with (output/(view.upper()+'_FRAME_SCORES.jsonl')).open('a') as journal:
                    for completed_row in scores[view][-len(models):]:journal.write(json.dumps(completed_row,allow_nan=False)+'\n')
            if (image_index+1)%50==0 or image_index+1==len(images):
                _write(output/'SCORING_PROGRESS.json',dict(images_scored=image_index+1,expected_images=len(images),system_image_scores=len(scores['primary']),inference_rerun=False))
    for view,frames in scores.items():
        # Shared per-frame scores are admitted only against each population's exact context.
        reports=population_reports(cfg,images,templates,frames,matching_view=view)
        for role,report in reports.items():_write(output/(role.upper()+'_'+view.upper()+'_REPORT.json'),report)
        _write(output/(view.upper()+'_FRAME_SCORES.json'),frames)
    result=dict(status='COMPLETED_WITH_RETAINED_STATUS_ROWS',end_utc=datetime.now(timezone.utc).isoformat(),
        reference_images=len(images),detector_jobs=len(images),parser_jobs=len(images)*len(models),
        separate_populations=['main','reference'],config_sha256=digest(cfg),timing_ranking=False)
    _write(output/'BENCHMARK_EXECUTION.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();cfg=load_config(args.config,benchmark=True);require_validation_authorization(cfg,S)
    launch=cfg['validation_launch'];recovery=launch['detector_infrastructure_restoration']
    if recovery['CPI_inference_retries']!=0 or recovery['prior_YOLO_image_attempts']!=0:raise ValueError('No model/failed-frame retry permitted')
    output=args.output.resolve()
    if not output.is_relative_to(S) or output.exists():raise ValueError('Fresh restored-profile directory required')
    output.mkdir(parents=True);images,_=package_data(cfg,S);expected=[r['image_id'] for r in images];ledgers={}
    for model,component in recovery['native_components'].items():
        manifest=S/component['manifest'];ledger=S/component['ledger']
        if file_hash(manifest)!=component['manifest_sha256'] or file_hash(ledger)!=component['ledger_sha256']:raise ValueError('Original native evidence changed')
        state=json.loads(manifest.read_text());selected=cfg['first_cohort']['execution_spec']['parser_systems'][model]
        if (state['checkpoint_sha256'],state['native_config_sha256'],state['source_commit'],state['precision'],state['native_score_threshold'])!=(selected['checkpoint_sha256'],selected['native_config_sha256'],selected['source_commit'],'FP32',field(cfg,selected['score_threshold_source'])):raise ValueError('Native inference scientific configuration differs')
        rows=[json.loads(line) for line in ledger.read_text().splitlines()]
        if [r['image_id'] for r in rows]!=expected or state['config_sha256']!=recovery['native_source_config_sha256']:raise ValueError('Native input/config lineage mismatch')
        ledgers[model]={r['image_id']:r for r in rows}
    detector=cfg['first_cohort']['execution_spec']['dependencies']['YOLO26X_FROZEN'];worker=S/recovery['detector_worker'];receipt=dict(status='APPROVED_FROZEN_CPU_VALIDATED',model_id='YOLO26X_FROZEN',config_content_sha256=digest(cfg),
        worker_sha256=file_hash(worker),checkpoint_workspace_relative=detector['checkpoint_workspace_relative'],checkpoint_sha256=detector['checkpoint_sha256'],settings=field(cfg,detector['settings_source']),
        inputs_path=launch['inputs']['path'],RGB_archive_workspace_relative=launch['RGB_archive_workspace_relative'],
        frozen_files=[dict(path=str(args.config.resolve().relative_to(S)),sha256=file_hash(args.config)),dict(path=cfg['decision_record'],sha256=file_hash(S/cfg['decision_record'])),dict(path=launch['inputs']['path'],sha256=launch['inputs']['sha256'])])
    receipt_path=output/'YOLO_CPU_VALIDATION_RECEIPT.json';_write(receipt_path,receipt)
    _idle();command=[str(S.parent/detector['environment_workspace_relative']/'bin/python'),str(worker),'--receipt',str(receipt_path),'--receipt-sha256',file_hash(receipt_path),'--output',str(output/'YOLO26X_FROZEN')]
    with (output/'YOLO26X_FROZEN.log').open('x') as log:process=subprocess.run(command,cwd=S,stdout=log,stderr=subprocess.STDOUT)
    ledger=output/'YOLO26X_FROZEN/FRAMES.jsonl';rows=[json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
    if len({r['image_id'] for r in rows})!=len(rows) or any(r['image_id'] not in set(expected) for r in rows):raise ValueError('Detector ledger identity mismatch')
    ledgers['YOLO26X_FROZEN']={r['image_id']:r for r in rows}
    _write(output/'RESTORATION_PROCESS.json',dict(detector_exit_code=process.returncode,CPI_inference_rerun=False,prior_invalid_trial_retained=recovery['initial_trial'],all_failed_CPI_frames_retained=True))
    result=score_components(args.config,output,ledgers);print(json.dumps(result))


if __name__=='__main__':main()
