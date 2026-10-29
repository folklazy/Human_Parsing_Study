"""Read-only pilot/legacy reconciliation and explicit freeze for approved C4-P full run."""
from pathlib import Path
from datetime import datetime, timezone
import json,sys,os,shutil,subprocess,importlib.metadata,unittest
import numpy as np
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'));sys.path.insert(0,str(P/'scripts'))
from common_view.core import sha_file,load_spec,score_packet,project,compose_native
from common_view.full import score_people,project_confusion,native_confusion
from common_view.packets import atomic_json,read_packet,fingerprint
from common_view.detector_cache import normalize_detector_masks
from cihp_benchmark.data import read_image

MODELS=['QANet_CIHP_HRNetW48_512x384','M2FP_R101_CIHP','D2FP_R101_CIHP','RPR_CIHP']


def prepare():
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:args=(proc/'cmdline').read_bytes().split(b'\0')
        except FileNotFoundError:continue
        names=[Path(os.fsdecode(a)).name for a in args if a]
        if set(names)&{'run_common_full.py','run_common_sapiens_pilot.py','run_cpi_continuation.py','run_cpi_r50_quality_round.py','run_cpi_convnext_quality_round.py','run_cpi_r50_shared_segment.py','run_cpi_convnext_shared_segment.py'}:
            raise RuntimeError('Existing model/controller PID '+proc.name)
    pilotpath=P/'configs/cihp_sapiens_04b_pilot.json';pilot=json.loads(pilotpath.read_text());pr=W/pilot['artifact_root']
    ready=json.loads((pr/'READINESS.json').read_text());run=json.loads((pr/'RUN.json').read_text())
    assert run['status']=='PILOT_PASS' and run['model_frame_calls']==7
    assert sha_file(pilotpath)==ready['config_sha256']
    for f,h in ready['source_hashes'].items():assert sha_file(W/f)==h,f
    for f,h in pilot['native_preserved'].items():assert sha_file(W/f)==h,f
    spec=load_spec(W/pilot['protocol']);assert sha_file(W/pilot['protocol'])==pilot['protocol_sha256']
    ck=W/pilot['model']['checkpoint'];assert ready['checkpoint_stat']==dict(size=ck.stat().st_size,mtime_ns=ck.stat().st_mtime_ns)
    assert subprocess.check_output(['git','-C',str(W/'third_party/human_parsing/sapiens2'),'rev-parse','HEAD'],text=True).strip()==pilot['model']['source_commit']
    assert not subprocess.check_output(['git','-C',str(W/'third_party/human_parsing/sapiens2'),'status','--porcelain'],text=True).strip()
    env={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    assert env==json.loads((pr/'ENVIRONMENT.json').read_text()),'Environment versions differ from pilot'
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==ready['CUDA_VISIBLE_DEVICES']
    assert os.environ.get('PYTORCH_CUDA_ALLOC_CONF')==ready['allocator_environment_preserved']
    assert Path(sys.prefix).resolve()==(W/'.venvs/sapiens2-pilot').resolve()
    poppath=W/pilot['native_population'];assert sha_file(poppath)==pilot['native_population_sha256']
    pop=json.loads(poppath.read_text())['members'];ids=[r['id'] for r in pop];population={r['id']:r for r in pop}
    assert len(ids)==len(set(ids))==5000
    assert sha_file(W/pilot['YOLO']['checkpoint'])==pilot['YOLO']['checkpoint_sha256']
    gtroot=W/pilot['GT_binding_root'];summary=json.loads((gtroot/'SUMMARY.json').read_text())
    assert sha_file(gtroot/'BINDINGS.jsonl')==ready['GT_manifest_sha256']==summary['manifest_sha256']
    assert summary['population_sha256']==pilot['native_population_sha256'] and summary['protocol_sha256']==pilot['protocol_sha256']
    bindings={r['image_id']:r for r in map(json.loads,(gtroot/'BINDINGS.jsonl').open())};assert set(bindings)==set(ids)
    counts={k:sum(r[k] for r in bindings.values()) for k in ['G_loc','G_sem_C4']}
    support=np.sum([r['global_support'] for r in bindings.values()],axis=0).tolist()
    assert counts['G_loc']==summary['G_loc'] and counts['G_sem_C4']==summary['G_sem_C4'] and support==summary['global_support']
    unit='common-c4p-full-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    raw=P/'outputs/common_view'/unit;raw.mkdir(parents=True,exist_ok=False);record=P/'runs'/unit;record.mkdir(parents=True,exist_ok=False)
    gallery=json.loads((pr/'gallery/MANIFEST.json').read_text());checks=[]
    for row in gallery:
        actual=sha_file(pr/'gallery'/row['PNG'])
        checks.append(dict(image_id=row['image_id'],manifest_sha256=row['sha256'],actual_sha256=actual,original_matches=actual==row['sha256']))
    atomic_json(record/'GALLERY_RECONCILIATION.json',dict(
        original_artifacts='PASS' if all(r['original_matches'] for r in checks) else 'MISMATCH_RETAINED',records=checks,
        original_manifest_sha256=sha_file(pr/'gallery/MANIFEST.json'),
        reviewer_copy_observation={'not_byte_identical_reported':['0021448','0006909','0027897','0031248'],
                                  'matching_reported':['0001538','0001413'],
                                  'independently_inspected_copy_bytes':False,'transport_cause':'UNKNOWN_NOT_INFERRED'},
        prediction_packet_checks_separate=True,manifest_not_rewritten=True))
    detector={r['image_id']:r for r in map(json.loads,(W/pilot['YOLO']['validation_ledger']).open())}
    assert set(detector)==set(ids)
    nativecfg=json.loads((P/'configs/cihp_native_six.json').read_text());nativeconfigsha=sha_file(P/'configs/cihp_native_six.json')
    for f,h in nativecfg['source_bindings'].items():assert sha_file(W/f)==h,f
    legacy={};cpu_integrations=[];total_meta_bytes=0
    for mid in MODELS:
        proofpath=P/'metrics/presentation-four-20261028T184321049969Z'/(mid+'.json');proof=json.loads(proofpath.read_text())
        metrics=W/proof['source_metrics'];assert sha_file(metrics)==proof['source_metrics_sha256']
        folder=metrics.parent;closed=json.loads((folder/'RUN.json').read_text());assert closed['status']=='COMPLETE' and closed['complete']==5000
        frames=[json.loads(l) for l in (folder/'FRAMES.jsonl').open()];assert len(frames)==5000
        assert len({r['image_id'] for r in frames})==5000 and {r['image_id'] for r in frames}==set(ids) and all(r['status']=='COMPLETE' for r in frames)
        audited={};audit_refs=[];audited_hist=np.zeros((20,20),np.int64)
        for loc in closed['audit_locations']:
            a=W/loc;ar=json.loads((a/'RECONCILED.json').read_text());vf=a/'VERIFIED_FRAMES.jsonl'
            audited_hist+=np.asarray(ar['histogram'],np.int64)
            assert sha_file(vf)==ar['verified_ledger_sha256']
            source=W/ar['source_root']
            if ar['verified_count']:assert sha_file(source/'FRAMES.jsonl')==ar['source_ledger_sha256']
            audit_refs.append(dict(path=loc,reconciled_sha256=sha_file(a/'RECONCILED.json'),verified_ledger_sha256=sha_file(vf)))
            for line in vf.open():
                r=json.loads(line);iid=r['frame']['image_id'];assert iid not in audited;audited[iid]=r
        assert set(audited)==set(ids)
        inputs=raw/'source_manifests'/(mid+'.jsonl');inputs.parent.mkdir(exist_ok=True)
        entries={}
        with inputs.open('x') as out:
            for frame in frames:
                iid=frame['image_id'];a=audited[iid];assert frame['packet_sha256']==a['frame']['packet_sha256']
                packet=W/frame['packet'];assert packet.is_dir()
                entry=dict(image_id=iid,packet=frame['packet'],packet_sha256=frame['packet_sha256'],
                           metadata_sha256=a['metadata_sha256'],score_hashes=a['score_hashes'])
                entries[iid]=entry;out.write(json.dumps(entry)+'\n')
        confusion=folder/'CONFUSION.npy';h=np.load(confusion,allow_pickle=False)
        assert h.shape==(20,20) and int(h.sum())==sum(summary['global_support'])
        assert np.array_equal(h,audited_hist),'Canonical confusion differs from audited per-segment sufficient statistics'
        mapped=project_confusion(h,'CIHP_GT_AND_NATIVE_PRED',spec);assert mapped.sum(1).tolist()==support
        legacy[mid]=dict(source_model=nativecfg['models'][mid],input_manifest=str(inputs.relative_to(W)),input_manifest_sha256=sha_file(inputs),
                         source_metrics=proof['source_metrics'],source_metrics_sha256=proof['source_metrics_sha256'],
                         confusion=str(confusion.relative_to(W)),confusion_sha256=sha_file(confusion),
                         source_RUN_sha256=sha_file(folder/'RUN.json'),source_ledger_sha256=sha_file(folder/'FRAMES.jsonl'),
                         audits=audit_refs,source_route=nativecfg['models'][mid]['route'],native_config_sha256=nativeconfigsha)
        # Fixed ambiguity-coverage examples, not chosen by quality: ordinary crowd and Dress.
        for iid in ['0021448','0006909']:
            e=entries[iid];m,arr=read_packet(W/e['packet'],dict(model_id=mid,image_id=iid,config_sha256=nativeconfigsha),legacy=True)
            assert m['packet_sha256']==e['packet_sha256'] and sha_file(W/e['packet']/'packet.json')==e['metadata_sha256']
            category,_=read_image(W/'datasets/CIHP/Validation/Category_ids'/(iid+'.png'),True)
            human,_=read_image(W/'datasets/CIHP/Validation/Human_ids'/(iid+'.png'),True)
            results=score_people(category,human,arr['person_semantic_masks'],arr['person_extents'],arr['person_scores'],'CIHP_GT_AND_NATIVE_PRED',spec,bindings[iid])
            nh=native_confusion(category,arr['person_semantic_masks'],arr['person_scores'],'CIHP_GT_AND_NATIVE_PRED',spec)
            pg=project(category,'CIHP_GT_AND_NATIVE_PRED',spec);pp=project(compose_native(arr['person_semantic_masks'],arr['person_scores'],category.shape),'CIHP_GT_AND_NATIVE_PRED',spec)
            pixel=np.bincount(6*pg.ravel().astype(np.int64)+pp.ravel(),minlength=36).reshape(6,6)
            assert np.array_equal(pixel,project_confusion(nh,'CIHP_GT_AND_NATIVE_PRED',spec))
            for t in [.5,.75]:
                old=score_packet(category,human,arr['person_semantic_masks'],arr['person_extents'],arr['person_scores'],'CIHP_GT_AND_NATIVE_PRED',spec,t)
                assert all(old[k]==v for k,v in results[str(t)].items())
            cpu_integrations.append(dict(model_id=mid,image_id=iid,projection_confusion_vs_pixels='PASS',person_scorer_vs_frozen_revision2='PASS'))
            total_meta_bytes+=len(json.dumps(results))
    reused=[]
    for iid in pilot['pilot_ids']:
        packet=pr/'packets'/iid
        expected=dict(model_id='Sapiens2_0.4b',image_id=iid,protocol_sha256=pilot['protocol_sha256'],config_sha256=ready['config_sha256'],
                      checkpoint_sha256=ready['checkpoint_sha256'],source_commit=pilot['model']['source_commit'],environment_sha256=ready['environment_sha256'],
                      input_sha256=population[iid]['RGB_sha256'],detector_artifact_sha256=detector[iid]['artifact_sha256'],
                      precision=pilot['precision'],GT_used_in_prediction=False,fallback_used=False,label_space='SAPIENS2_DOME29_PRED')
        meta,arr=read_packet(packet,expected)
        assert meta['geometry']['input_hw']==pilot['input_hw'] and meta['geometry']['crop'] is None
        assert meta['geometry']['map_back']=='BILINEAR_ALIGN_CORNERS_FALSE_THEN_NATIVE29_ARGMAX'
        d=detector[iid];dp=W/'Human_Parsing_MHPv2_Study'/d['artifact'];assert sha_file(dp)==d['artifact_sha256']
        with np.load(dp,allow_pickle=False) as z:ext=normalize_detector_masks(z['masks'],len(d['opportunities']),bindings[iid]['shape'])
        keep=[j for j,e in enumerate(ext) if e.any()];ext=ext[keep]
        assert np.array_equal(ext,arr['person_extents'])
        assert np.array_equal(arr['person_semantic_masks'],np.where(ext,arr['native_full_frame_semantic_mask'],0))
        assert np.array_equal(arr['person_scores'],np.array([d['opportunities'][j]['score'] for j in keep],np.float32))
        bind=dict(model_id='Sapiens2_0.4b',checkpoint_sha256=ready['checkpoint_sha256'],input_sha256=population[iid]['RGB_sha256'],
                  detector_artifact_sha256=d['artifact_sha256'],protocol_sha256=pilot['protocol_sha256'],config_sha256=ready['config_sha256'],
                  source_hashes=ready['source_hashes'],route=pilot['route'],precision=pilot['precision'])
        assert fingerprint(bind)==meta['inference_fingerprint']
        category,_=read_image(W/'datasets/CIHP/Validation/Category_ids'/(iid+'.png'),True)
        human,_=read_image(W/'datasets/CIHP/Validation/Human_ids'/(iid+'.png'),True)
        sc=score_people(category,human,arr['person_semantic_masks'],ext,arr['person_scores'],'SAPIENS2_DOME29_PRED',spec,bindings[iid])
        for t in [.5,.75]:
            stored=json.loads((packet/('score_'+str(t)+'.json')).read_text());assert all(stored[k]==v for k,v in sc[str(t)].items())
        reused.append(dict(image_id=iid,packet=str(packet.relative_to(W)),packet_sha256=meta['packet_sha256'],metadata_sha256=sha_file(packet/'packet.json'),
                           old_inference_fingerprint_unchanged=meta['inference_fingerprint'],reuse='EXPLICIT_SCIENTIFIC_COMPATIBILITY_WITHOUT_REWRITING_OLD_CONFIG_FINGERPRINT'))
    pending=[i for i in ids if i not in {r['image_id'] for r in reused}]
    assert len(reused)==6 and len(pending)==4994 and set(pending).isdisjoint(r['image_id'] for r in reused)
    atomic_json(record/'REUSE_COMPATIBILITY.json',dict(status='PASS_EXPLICIT_COMPATIBILITY',
        pilot_config_sha256=ready['config_sha256'],protocol_sha256=pilot['protocol_sha256'],
        equal_scientific_bindings=['checkpoint SHA256 and unchanged file stat','native config and source commit',
            'full-frame 1024x768 preprocessing/channel order/normalization','bilinear mapback before native29 argmax',
            'FP32 batch1 eval/inference noAMP/noTF32/noextraTTA','identical YOLO masks, scores and IDs',
            'exact environment versions and allocator/device-visibility settings','revision2 scoring and GT domains'],
        differences=['full population/reporting/orchestration config identity','new output root and launch process'],
        old_fingerprints_not_rewritten=True,model_outputs_selected_by_score=False,reused=reused,
        pending_ids=pending,parent_setup_and_pilot_history_retained=True))
    # Conservative disk budget: raw arrays, per-frame JSON allowance, logs/references, atomic peak and headroom.
    estimate=json.loads((P/'runs'/pilot['run_id']/'FULL_WORKLOAD_METADATA_ESTIMATE.json').read_text())
    measured_json_per_frame=total_meta_bytes/len(cpu_integrations)
    array_gib=estimate['uncompressed_prediction_array_GiB_estimate']
    budget=dict(raw_prediction_arrays_GiB=array_gib,metadata_and_scores_allowance_GiB=max(2.,measured_json_per_frame*5000*5*4/2**30),
                logs_references_gallery_allowance_GiB=2.,atomic_temporary_allowance_GiB=1.,operational_headroom_GiB=8.,
                preexisting_GT_and_native_predictions='REFERENCED_NOT_COPIED',free_disk_GiB=shutil.disk_usage(raw).free/2**30,
                global_planning_envelope_GiB=200,per_checkpoint_stream_cap_GiB=80,minimum_free_GiB=50,
                actual_sample_score_JSON_bytes_mean=measured_json_per_frame,ETA=None,compression_not_assumed=True)
    budget['estimated_additional_total_GiB']=sum(budget[k] for k in ['raw_prediction_arrays_GiB','metadata_and_scores_allowance_GiB','logs_references_gallery_allowance_GiB','atomic_temporary_allowance_GiB','operational_headroom_GiB'])
    assert budget['estimated_additional_total_GiB']<80 and budget['free_disk_GiB']-budget['estimated_additional_total_GiB']>50
    atomic_json(record/'RESOURCE_BUDGET.json',budget)
    atomic_json(record/'CPU_ACCEPTANCE.json',dict(status='PASS',scope='new streaming/full reporting + reused pilot scorer equivalence, not GPU acceptance',
                new_streaming_CPU_fixture_cases=7,saved_integrations=cpu_integrations,pilot_reused_packets_checked=6,source_native_unchanged=True,model_calls=0))
    config={k:pilot[k] for k in ['model','protocol','protocol_sha256','YOLO','native_population','native_population_sha256','native_preserved',
                                 'precision','batch_size','input_hw','route','GT_binding_root','minimum_free_gib','max_stream_gib','max_hours']}
    config.update(run_id=unit,scope='CIHP_SAPIENS_C4P_FULL',status='FROZEN_USER_AUTHORIZED',artifact_root=str(raw.relative_to(W)),record_root=str(record.relative_to(W)),
                  pilot_config=str(pilotpath.relative_to(W)),pilot_config_sha256=sha_file(pilotpath),pilot_artifact_root=pilot['artifact_root'],
                  expected_ids=ids,reused=reused,pending_ids=pending,max_model_frame_calls=len(pending)+1,warmup_id='0000930',
                  resource_policy='SHARED_GPU_QUALITY_ONLY',automatic_model_OOM_retry=0,fallback=False,
                  prior_pilot_model_frame_calls=run['model_frame_calls'],
                  prior_pilot_operations_seconds=run['total_elapsed_seconds']+json.loads((W/pilot['parent_artifact_root']/'RUN.json').read_text())['total_elapsed_seconds'],
                  models=MODELS+['Sapiens2_0.4b'],legacy=legacy,GT_manifest_sha256=ready['GT_manifest_sha256'],GT_summary=summary,
                  environment_sha256=ready['environment_sha256'],checkpoint_stat=ready['checkpoint_stat'],
                  pilot_scientific_source_hashes=ready['source_hashes'],resource_budget=budget,
                  scientific_behavior='UNCHANGED_PILOT_REVISION2',full_reporter='STRICT_COMPLETE_5000_PER_SYSTEM',
                  orchestration_changes=['full population reporter and streaming aggregation','6 referenced pilot native predictions, 4994 new VAL calls plus at most1 TRAINwarmup',
                                         'one GPU worker and one sequential CPU saved-artifact rescorer','fresh output path under owning benchmark workspace'],
                  authority='User explicitly approves full CIHP_SAPIENS_C4P four saved-only systems + Sapiens2 0.4B officialVAL5000; stop thereafter',
                  timing_ranking_allowed=False,other_sizes=False,CPI=False,new_YOLO_inference=False,
                  CUDA_VISIBLE_DEVICES=ready['CUDA_VISIBLE_DEVICES'],allocator_environment_preserved=ready['allocator_environment_preserved'])
    sources=[P/'src/common_view/full.py',P/'scripts/prepare_common_full.py',P/'scripts/run_common_full.py',P/'scripts/common_full_progress.py',P/'scripts/render_common_full.py',P/'tests/test_common_full.py',P/'scripts/monitor_cihp_batch.py']
    config['source_hashes']={**nativecfg['source_bindings'],**{str(f.relative_to(W)):sha_file(f) for f in sources}}
    path=P/'configs/cihp_sapiens_c4p_full.json';atomic_json(path,config)
    atomic_json(record/'FREEZE.json',dict(status='FROZEN_USER_AUTHORIZED',created_utc=datetime.now(timezone.utc).isoformat(),
                config=str(path.relative_to(W)),config_sha256=sha_file(path),protocol_sha256=pilot['protocol_sha256'],source_hashes=config['source_hashes'],
                reused=6,pending=4994,GT_denominators_verified_from_bound_manifest=counts,
                source_identity_reuse='Pilot checkpoint SHA256 retained; unchanged size+mtime, exact source revisions/hashes/environment checked',
                launch_commit='TO_BE_RECORDED_BY_CONTROLLER_BEFORE_FORWARD'))
    atomic_json(raw/'FROZEN_CONFIG.json',config)
    (P/'outputs/common_view/CURRENT_FULL.txt').write_text(str(path.relative_to(W))+'\n')
    print(json.dumps(dict(config=str(path.relative_to(W)),run_id=unit,reused=6,pending=4994,G=counts,budget_GiB=budget['estimated_additional_total_GiB'])),flush=True)

if __name__=='__main__':prepare()
