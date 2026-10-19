"""Approval-gated reference inference, then separate population/view reports."""
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess
import zipfile
import numpy as np
from .policy import load_config,digest,fingerprints
from .artifacts import file_hash,commit_packet
from .validation_launch import require_validation_authorization,package_data,population_reports


def _write(path,data):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');temporary.replace(path)


def execute_validation(config_path, output):
    config_path=Path(config_path).resolve();study=config_path.parents[1];workspace=study.parent
    cfg=load_config(config_path,benchmark=True)
    require_validation_authorization(cfg,study)  # No dataset/model reads or outputs before this gate.
    from .runner import ConfiguredRunner
    from .first_cohort_fresh import _idle,score_committed_packet
    from .first_cohort_replay import _arrays
    from .validation_data import read_gt
    from .evaluation import associate_native
    from .contracts import stage_rate
    images,templates=package_data(cfg,study)
    output=Path(output).resolve()
    if not output.is_relative_to(study) or output.exists():raise ValueError('Fresh study-owned benchmark output required')
    output.mkdir(parents=True)
    launch=cfg['validation_launch'];spec=cfg['first_cohort']['execution_spec']
    dependencies=spec['dependencies'];models=cfg['first_cohort']['models']
    order=list(dependencies)+models;attempts=[];ledgers={}
    worker=study/launch['worker']
    for model in order:
        _idle()
        system=(dependencies if model in dependencies else spec['parser_systems'])[model]
        command=[str(workspace/system['environment_workspace_relative']/'bin/python'),str(worker),
                 '--config',str(config_path),'--model',model,'--output',str(output/model)]
        with (output/(model+'.log')).open('x') as log:
            done=subprocess.run(command,cwd=study,stdout=log,stderr=subprocess.STDOUT)
        manifest=output/model/'RUN.json'
        state=json.loads(manifest.read_text()) if manifest.exists() else dict(status='WORKER_ABORT')
        ledger=output/model/'FRAMES.jsonl'
        rows=[json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
        expected={r['image_id'] for r in images}
        if len({r['image_id'] for r in rows})!=len(rows) or any(r['image_id'] not in expected for r in rows):
            raise ValueError('Worker ledger contains duplicate or unexpected image IDs')
        if state.get('config_sha256') not in {None,digest(cfg)}:raise ValueError('Worker configuration mismatch')
        ledgers[model]={r['image_id']:r for r in rows}
        attempts.append(dict(model_id=model,exit_code=done.returncode,worker_status=state['status'],
            completed=sum(r['status']=='COMPLETE' for r in rows),expected_frames=len(images),retries=0,
            run_manifest=str(manifest.relative_to(study))))
        _write(output/'PROCESS_ATTEMPTS.json',attempts)
    runner=ConfiguredRunner(config_path,mode='VALIDATION_BENCHMARK',benchmark=True,population_role='reference')
    package_dir=(study/cfg['validation_context_packages']['manifest']).parent
    person_groups={}
    for line in (package_dir/'PERSON_GT_BINDINGS.jsonl').read_text().splitlines():
        row=json.loads(line);person_groups.setdefault(row['image_id'],[]).append(row)
    mapping=json.loads((study/cfg['cohort']['mapping']).read_text())
    scores={view:[] for view in ['primary','secondary']}
    detector=next(iter(dependencies));source_zip=workspace/launch['GT_archive_workspace_relative']
    with zipfile.ZipFile(source_zip) as archive:
        for binding in images:
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
