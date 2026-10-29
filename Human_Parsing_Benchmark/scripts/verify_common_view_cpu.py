"""Scoped CPU oracle fixtures plus four saved-packet integrations; no model forward."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json,sys,time,unittest,subprocess
import numpy as np
P=Path(__file__).resolve().parents[1];W=P.parent
sys.path.insert(0,str(P/'src'))
from common_view.core import load_spec,sha_file,score_packet
from common_view.detector_cache import normalize_detector_masks
from common_view.packets import atomic_json,score_saved_packet,reporter
from cihp_benchmark.data import read_image


def main():
    config=json.loads((P/'configs/cihp_sapiens_04b_pilot.json').read_text());raw=W/config['artifact_root'];record=W/config['record_root']
    spec=load_spec(W/config['protocol']);t0=time.perf_counter()
    loader=importlib.util.spec_from_file_location('common_view_oracle_tests',P/'tests/test_common_view.py')
    module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
    suite=unittest.defaultTestLoader.loadTestsFromModule(module)
    with (raw/'CPU_TESTS.log').open('w') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not result.wasSuccessful():raise RuntimeError('CPU expected-value tests failed; seeCPU_TESTS.log')
    manifest=json.loads((P/'runs/cihp-native-six-20261028T034103254470Z/presentation-four-20261028T184321049969Z/VISUALIZATION_MANIFEST.json').read_text())
    r=next(x for x in manifest['records'] if x['image_id']=='0021448')
    category,_=read_image(W/'datasets/CIHP/Validation/Category_ids/0021448.png',mask=True)
    human,_=read_image(W/'datasets/CIHP/Validation/Human_ids/0021448.png',mask=True)
    native=json.loads((P/'configs/cihp_native_six.json').read_text());integrations=[]
    for x in r['packets']:
        packet=W/x['packet'];expected=dict(image_id='0021448',model_id=x['model_id'],
           checkpoint_sha256=native['models'][x['model_id']]['checkpoint_sha256'],
           source_commit=native['models'][x['model_id']]['source_commit'],input_sha256=r['RGB_sha256'],
           config_sha256=sha_file(P/'configs/cihp_native_six.json'))
        before={p.name:sha_file(p) for p in packet.iterdir() if p.is_file()}
        row=score_saved_packet(packet,category,human,'CIHP_GT_AND_NATIVE_PRED',spec,expected,legacy=True)
        path=raw/'cpu_integration'/x['model_id']/'REPORT.json'
        report=reporter(path,[row],['0021448'])
        assert report['complete'] and report['full_population_primary'] is None
        assert all(sha_file(packet/n)==h for n,h in before.items())
        integrations.append({'model_id':x['model_id'],'image_id':'0021448','source_packet':x['packet'],
                             'packet_sha256':before['prediction.npz'],'source_members_unchanged':True,
                             'packet_scorer_reporter':'PASS','scope':'one saved frame only; not fullbenchmark'})
    cache_probes=[]
    val={r['image_id']:r for r in map(json.loads,(W/config['YOLO']['validation_ledger']).open())}
    training=json.loads((W/config['YOLO']['training_run']).read_text())
    warm=next(r for r in training['images'] if r['image_id']==config['warmup_id'])
    for iid,d in [(config['warmup_id'],warm)]+[(iid,val[iid]) for iid in config['pilot_ids']]:
        path=W/'Human_Parsing_MHPv2_Study'/d['artifact'];assert sha_file(path)==d['artifact_sha256']
        wh=d.get('original_wh',d.get('wh'))
        with np.load(path,allow_pickle=False) as z:source=z['masks'].copy()
        mask=normalize_detector_masks(source,len(d['opportunities']),(wh[1],wh[0]))
        assert np.array_equal(source,mask)
        cache_probes.append(dict(image_id=iid,source_dtype=str(source.dtype),normalized_dtype=str(mask.dtype),same_binary_geometry=True,artifact_sha256=d['artifact_sha256']))
    # Evidence of the actual old-ID-dependent counterexample and the amended invariance.
    from cihp_benchmark.evaluation import score_frame
    c=np.array([[5,9]],np.uint8);p=np.array([[[5,0]],[[0,9]]],np.uint8);e=np.ones((2,1,2),bool);scores=np.ones(2)
    old=[];new=[]
    for h in [np.array([[1,2]],np.uint8),np.array([[2,1]],np.uint8)]:
        old.append(score_frame(c,h,p,e,scores,.5)['Q_person_sem_GT'])
        new.append(score_packet(c,h,p,e,scores,'CIHP_GT_AND_NATIVE_PRED',spec,.5)['Q_C4_GT'])
    assert old==[1.,0.] and new==[1.,1.]
    for path,digest in config['native_preserved'].items():assert sha_file(W/path)==digest,path
    sources=[*sorted((P/'src/common_view').glob('*.py')),P/'tests/test_common_view.py',Path(__file__)]
    receipt={'status':'PASS','checked_utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256':config['protocol_sha256'],
             'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
             'tests_scope':'independentrequirementsfixtures including actualCPUsourcepreprocessor and packet/scorer/reporter; not wholeprojecttestsuite',
             'counterexample':{'mask_IoU':[[.5,.5],[.5,.5]],'native_legacy_Q_before_after_GTID_rename':old,
                               'amended_geometry_Q_before_after_GTID_rename':new,'alternative_assignment_Q':[1.,0.],
                               'limitations':'identicalGTgeometryusesstableIDfallback;identicalpredgeometryusespacketindex;ambiguityreported,no unconditionalgeometryresolution'},
             'C3':'GLOBAL_ONLY_FACE_VALID_NEGATIVE_NO_SECOND_PERSON_DENOMINATOR',
             'saved_packet_integrations':integrations,'actual_frozen_detector_cache_probes':cache_probes,'model_forward_calls':0,'seconds':time.perf_counter()-t0,
             'source_hashes':{str(p.relative_to(W)):sha_file(p) for p in sources},'native_preserved':'PASS'}
    atomic_json(raw/'CPU_ACCEPTANCE.json',receipt);atomic_json(record/'CPU_ACCEPTANCE.json',receipt)
    print(json.dumps({'status':'PASS','tests':result.testsRun,'saved_packets':len(integrations),'counterexample':receipt['counterexample']}))

if __name__=='__main__':main()
