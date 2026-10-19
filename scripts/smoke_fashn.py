"""Hard-bounded FP32 FASHN smoke: fixed train inputs only, no accuracy metric."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import argparse,json,sys,time,subprocess,traceback,shutil
import numpy as np
from PIL import Image
import torch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.adapters.fashn import FashnAdapter
from src.contracts.prediction import validate_prediction


def main():
    study=Path(__file__).resolve().parents[1];workspace=study.parent
    args=argparse.ArgumentParser();args.add_argument('--limit',type=int,default=3);args=args.parse_args()
    if not 1<=args.limit<=3:raise ValueError('Stage0 smoke limit is 1..3 fixed training images')
    manifest=json.loads((study/'manifests/DATASET_MANIFEST.json').read_text())
    if manifest['status']=='DATASET_BLOCKED':raise RuntimeError('MHP native GT gate blocked')
    development=json.loads((study/'manifests/DEVELOPMENT_SET.json').read_text())
    if development.get('execution_authorized_now') is not True:
        raise RuntimeError('Fixed smoke execution remains deferred pending user review')
    samples=development['smoke_image_ids'][:args.limit]
    index={}
    with (study/manifest['canonical_gt_index']).open() as stream:
        for line in stream:
            item=json.loads(line)
            if item['split']=='train' and item['image_id'] in samples:index[item['image_id']]=item
    assert set(index)==set(samples)
    checkpoint=workspace/'models/human_parsing/fashn'/json.loads((study/'provenance/CHECKPOINT_MANIFEST.json').read_text())['FASHN']['revision']
    expected=json.loads((study/'provenance/CHECKPOINT_MANIFEST.json').read_text())['FASHN']['sha256']
    if expected is None:
        raise RuntimeError('Intended local checkpoint has not been downloaded and verified')
    actual=sha256((checkpoint/'model.safetensors').read_bytes()).hexdigest();assert actual==expected
    source=json.loads((study/'provenance/SOURCE_REVISIONS.json').read_text())['fashn-human-parser']
    run_id='fashn-smoke-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run=study/'provenance/RUN_MANIFESTS'/run_id;run.mkdir(parents=True,exist_ok=False)
    before_gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],capture_output=True,text=True).stdout.strip()
    if before_gpu:raise RuntimeError('GPU contention; defer rather than interrupt another job')
    result={'run_id':run_id,'start_utc':datetime.now(timezone.utc).isoformat(),'model_id':'FASHN','source_commit':source['commit'],
            'checkpoint_sha256':actual,'dataset_manifest_sha256':sha256((study/'manifests/DATASET_MANIFEST.json').read_bytes()).hexdigest(),
            'input_ids':samples,'input_split':'train','precision':'FP32','torch':torch.__version__,'torch_cuda_runtime':torch.version.cuda,
            'python':sys.version,'environment_freeze':subprocess.run([shutil.which('uv'),'pip','freeze','--python',sys.executable],capture_output=True,text=True,check=True).stdout,
            'config':{'crop_margin_fraction':.10,'person_selection':'Lowest parsing person_file_id in each fixed train image',
                      'crop_geometry':'Body/clothing support bbox draft; no GT semantic pixels given to parser',
                      'hard_mask_rgb':False,'autocast':False,'native_wh':[384,576],'limit':args.limit},
            'benchmark':False,'ranking':False,'cases':[],'status':'INITIALIZING'}
    adapter=FashnAdapter(workspace/'third_party/human_parsing/fashn-human-parser',checkpoint)
    try:
        assert torch.cuda.is_available()
        result['gpu']=torch.cuda.get_device_name(0);result['compute_capability']=list(torch.cuda.get_device_capability(0))
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        torch.cuda.reset_peak_memory_stats();t0=time.perf_counter();adapter.load();torch.cuda.synchronize()
        result['load_seconds']=time.perf_counter()-t0
        assert all(parameter.dtype==torch.float32 for parameter in adapter.parser.model.parameters())
        result['parameters']=sum(p.numel() for p in adapter.parser.model.parameters())
        for image_id in samples:
            item=index[image_id];person=min(item['persons'],key=lambda p:p['person_file_id']);width,height=item['original_wh']
            box=person['body_clothing_bbox_draft']
            if box is None:raise ValueError('No verified localization support for smoke crop')
            x1,y1,x2,y2=box;mx=.1*(x2-x1);my=.1*(y2-y1)
            crop=[max(0,int(np.floor(x1-mx))),max(0,int(np.floor(y1-my))),min(width,int(np.ceil(x2+mx))),min(height,int(np.ceil(y2+my)))]
            with Image.open(workspace/manifest['root_workspace_relative']/item['image_path']) as image:rgb=np.array(image.convert('RGB').crop(tuple(crop)))
            torch.cuda.reset_peak_memory_stats();start=time.perf_counter();prepared=adapter.preprocess(rgb);raw=adapter.infer(prepared);masks,logits=adapter.postprocess(raw,rgb.shape[:2]);torch.cuda.synchronize()
            seconds=time.perf_counter()-start
            native_parity=None
            if not result['cases']:
                native_logits=adapter.parser.predict(rgb,return_logits=True).cpu().numpy()
                native_parity=float(np.max(np.abs(native_logits-logits)))
                assert np.allclose(native_logits,logits,rtol=1e-5,atol=1e-5)
            record={'schema_version':'1.0','study_id':'human_parsing_mhpv2','run_id':run_id,'model_id':'FASHN','source_commit':source['commit'],
                    'checkpoint_sha256':actual,'source_track':'ORACLE_PERSON','image_id':image_id,'original_wh':[width,height],
                    'native_input_wh':[384,576],'crop_xyxy':crop,'native_labels':list(range(18)), 'predicted_person_ids':None,
                    'source_person_id':person['canonical_person_id'],'ownership_status':'SEMANTIC_CROP_TARGET_NOT_NATIVE_INSTANCE',
                    'transforms':{'crop_to_original':{'offset_xy':crop[:2],'scale_xy':[1,1]},
                                  'rgb_resize':'cv2.INTER_AREA to 384x576; no RGB hard mask',
                                  'logits_to_crop':'bilinear align_corners=False before argmax'},
                    'precision':'FP32','environment':str(Path(sys.executable).relative_to(workspace)),
                    'dataset_manifest_sha256':result['dataset_manifest_sha256'],'scores':None,'logits_available':True}
            validate_prediction(record,masks)
            output=study/'predictions'/run_id/image_id;export=adapter.export_prediction((output,record,masks,logits))
            result['cases'].append({'image_id':image_id,'crop_xyxy':crop,'mask_shape':list(masks.shape),'observed_labels':np.unique(masks).tolist(),
                                    'nonempty_foreground':bool(np.any(masks>0)),'finite_logits':True,'canonical_contract':'PASS',
                                    'official_predict_api_max_logit_difference':native_parity,
                                    'artifact':str(output.relative_to(study)),'artifact_sha256':export['native_artifact_sha256'],
                                    'execution_seconds_smoke_only':seconds,'peak_allocated_vram_mib':torch.cuda.max_memory_allocated()/2**20,
                                    'peak_reserved_vram_mib':torch.cuda.max_memory_reserved()/2**20})
        assert all(case['nonempty_foreground'] for case in result['cases'])
        result['status']='SMOKE_PASS';result['fp32_t4']='PASS'
    except Exception:
        result['status']='SMOKE_FAIL';result['error']=traceback.format_exc();result['fp32_t4']='NOT_ESTABLISHED'
    finally:
        adapter.cleanup();result['end_utc']=datetime.now(timezone.utc).isoformat()
        result['adapter_sha256']=sha256((study/'src/adapters/fashn.py').read_bytes()).hexdigest()
        result['script_sha256']=sha256(Path(__file__).read_bytes()).hexdigest()
        result['config_sha256']=sha256(json.dumps(result['config'],sort_keys=True).encode()).hexdigest()
        (run/'SMOKE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
        print(f'[FASHN] {result["status"]}; {len(result["cases"])} fixed train images; no accuracy evaluation')
        if result['status']!='SMOKE_PASS':raise SystemExit(1)


if __name__=='__main__':main()
