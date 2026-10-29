"""Bounded read-only closure of six common-view pilot packets; no new model calls."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'))
from common_view.core import sha_file,array_hash
from common_view.packets import read_packet,atomic_json


def main():
    c=json.loads((P/'configs/cihp_sapiens_04b_pilot.json').read_text());raw=W/c['artifact_root'];record=W/c['record_root']
    run=json.loads((raw/'RUN.json').read_text());parent=json.loads((W/c['parent_artifact_root']/'RUN.json').read_text())
    assert run['status']=='PILOT_PASS' and run['model_frame_calls']+parent['model_frame_calls']==7
    assert run['complete_ids']==c['pilot_ids'] and run['failed']==run['invalid']==0 and run['queue_stopped']
    ledger=[json.loads(l) for l in (raw/'EXECUTION.jsonl').read_text().splitlines()]
    starts=[r for r in ledger if r['status']=='STARTED'];ends=[r for r in ledger if r['status'].startswith('COMPLETE')]
    assert len(starts)==len(ends)==7 and len({r['image_id'] for r in starts})==7
    assert starts[0]['warmup'] and starts[0]['image_id']=='0000930'
    assert [r['image_id'] for r in starts[1:]]==c['pilot_ids']
    gtroot=W/c['GT_binding_root'];bindings={r['image_id']:r for r in map(json.loads,(gtroot/'BINDINGS.jsonl').open())}
    det={r['image_id']:r for r in map(json.loads,(W/c['YOLO']['validation_ledger']).open())}
    verify=[];hist=np.zeros((6,6),np.int64);metrics=json.loads((raw/'METRICS_DIAGNOSTICS.json').read_text())
    for iid in c['pilot_ids']:
        p=raw/'packets'/iid;meta,a=read_packet(p,{'model_id':'Sapiens2_0.4b','protocol_sha256':c['protocol_sha256']})
        H,Wid=a['native_full_frame_semantic_mask'].shape
        native=a['native_full_frame_semantic_mask']
        assert native.dtype==np.uint8 and int(native.max())<29
        assert meta['native_instance_count'] is None and meta['native_person_identity_supported'] is False
        assert meta['fallback_used'] is False and meta['GT_used_in_prediction'] is False
        d=det[iid];dp=W/'Human_Parsing_MHPv2_Study'/d['artifact']
        assert sha_file(dp)==meta['detector_artifact_sha256']==d['artifact_sha256']
        with np.load(dp,allow_pickle=False) as z:cached=z['masks'].copy()
        keep=[j for j,e in enumerate(cached) if e.any()];expected=cached[keep].astype(bool)
        assert np.array_equal(expected,a['person_extents'])
        assert np.array_equal(np.where(expected,native,0),a['person_semantic_masks'])
        assert meta['detector_opportunity_ids']==[d['opportunities'][j]['id'] for j in keep]
        assert np.array_equal(a['person_scores'],np.array([d['opportunities'][j]['score'] for j in keep],np.float32))
        src=W/'datasets/CIHP/Validation';rgb=src/'Images'/(iid+'.jpg')
        assert sha_file(rgb)==meta['input_sha256']==d['input_sha256']
        for kind in ['Category_ids','Human_ids']:assert sha_file(src/kind/(iid+'.png'))==bindings[iid]['GT_sha256'][kind]
        derived=gtroot/(iid+'.npz');assert sha_file(derived)==bindings[iid]['derived_sha256']
        with np.load(derived,allow_pickle=False) as z:
            for name,key in [('projected','projected_sha256'),('valid','valid_sha256'),('person_valid','person_valid_sha256')]:assert array_hash(z[name])==bindings[iid][key]
        sc=json.loads((p/'score_0.5.json').read_text());hist+=np.array(sc['histogram'],np.int64)
        assert sc['G_loc']==bindings[iid]['G_loc'] and sc['G_sem_C4']==bindings[iid]['G_sem_C4']
        figure=raw/'gallery'/(iid+'.png')
        with Image.open(figure) as im:im.load();assert im.size==(3*Wid,2*(H+30))
        verify.append({'image_id':iid,'original_wh':[Wid,H],'native_class_IDs_observed':np.unique(native).tolist(),
                       'native_shape_dtype_label_contract':'PASS','ownership_equal_exact_frozenYOLO':True,
                       'native29_clip_relation':'PASS','packet_readback_hash_commit':'PASS',
                       'GT_derived_bindings':'PASS','GT_persons':sc['G_loc'],'GT_semantic_eligible':sc['G_sem_C4'],
                       'native_output_sha256':meta['packet_sha256'],'figure_sha256':sha_file(figure)})
    assert hist.tolist()==metrics['histogram'] and metrics['full_population_primary'] is None
    assert metrics['complete'] and metrics['expected']==6 and not metrics['missing'] and not metrics['duplicate_ids']
    assert not any('Q_C3' in json.dumps(r) or 'G_sem_C3' in json.dumps(r) for r in [metrics])
    parity=json.loads((raw/'EXTENT_PARITY.json').read_text());assert len(parity)==6 and all(x['identical_cached_extent_arrays'] for x in parity)
    for f,h in c['native_preserved'].items():assert sha_file(W/f)==h,f
    ready=json.loads((raw/'READINESS.json').read_text())
    for f,h in ready['source_hashes'].items():assert sha_file(W/f)==h,f
    contents=(raw/'gallery/index.html').read_text()
    for r in verify:assert (raw/'gallery'/(r['image_id']+'.jpg')).exists()
    result={'status':'PASS','scope':'6-imagepilotonly_notfull5k_acceptance','checked_utc':datetime.now(timezone.utc).isoformat(),
            'run_id':c['run_id'],'parent_setup_status':parent['status'],'parent_model_calls':parent['model_frame_calls'],
            'current_model_calls':run['model_frame_calls'],'total_model_calls':7,'warmup_calls':1,'diagnostic_calls':6,
            'unique_expected_completed':6,'missing':0,'duplicates':0,'VAL_failed':0,'VAL_invalid':0,
            'retained_setup_invalid_before_forward':1,'saved_mask_rescore':run['saved_mask_rescore'],
            'QANet_extent_parity':'PASS_same6YOLOextents_boththresholds',
            'frozen_native_and_common_launch_source_hashes_unchanged':True,
            'full_population_primary':None,'full_common_scores_not_computed':True,
            'records':verify,'artifact_root':c['artifact_root'],'gallery':c['artifact_root']+'/gallery/index.html',
            'private_log':c['artifact_root']+'/worker.log','GT_manifest_sha256':ready['GT_manifest_sha256'],
            'readiness_source_commit':run['launch_public_commit'],'verifier_sha256':sha_file(__file__),
            'limitations':['source/maskscoringCPUexpectedcasesnotproofnativeannotationequivalence','sixdiagnosticimagesnotfullcohortquality/generalranking','no probabilitymetrics/logits recovered','sharedGPUtimingnotcleanranking']}
    atomic_json(raw/'ARTIFACT_VERIFICATION.json',result);atomic_json(record/'ARTIFACT_VERIFICATION.json',result)
    print(json.dumps({'status':'PASS','completed':6,'calls':7,'parity':result['QANet_extent_parity']}))

if __name__=='__main__':main()
