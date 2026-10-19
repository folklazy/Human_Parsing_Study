"""Metadata-only registry expansion: dataset weights are not capacity variants."""
from pathlib import Path
from hashlib import sha256
import csv
import json

S=Path(__file__).resolve().parents[1]
W=S.parent


def main():
    sources=json.loads((S/'provenance/SOURCE_REVISIONS.json').read_text())
    old=list(csv.DictReader((S/'provenance/MODEL_REGISTRY.csv').open()))
    rows=[]
    fields=['model_id','method','backbone','variant_kind','training_dataset','checkpoint_source',
            'checkpoint_bytes_metadata','checkpoint_sha256_local','checkpoint_downloaded','model_loaded',
            'checkpoint_inference_passed','source_commit','source_config','source_config_sha256',
            'native_classes_including_background','auxiliary_model_classes','native_mode',
            'code_license','weight_eligibility','environment_status','FP32_T4_status','role','notes']
    def add(model,method,backbone,kind,data,url,size,classes,aux,mode,license,eligible,env,role,notes='',config=''):
        src=sources[method]
        path=W/src['local_path']/config if config else None
        rows.append(dict(zip(fields,[model,method,backbone,kind,data,url,size,'NOT_DOWNLOADED',False,False,False,
            src['commit'],str(path.relative_to(W)) if path else '',sha256(path.read_bytes()).hexdigest() if path else '',
            classes,aux,mode,license,eligible,env,'NOT_TESTED',role,notes])))
    modern='DETECTRON2_MSDEFORM_ENV_NOT_READY_USERSPACE_TOOLKIT_PROPOSAL_ONLY'
    for data,link,size,steps in [
        ('MHPV2','1n8Sg7UiBHlx8yB8lQPzsSP52mguWQAdR',757779078,'145k'),
        ('CIHP','151vmS7DYBTH6UT6GpqPRVmnnann1c_D3',757764792,'265k'),
        ('LIP','1A0V10NBfiqy6yRJQF_d9-xvV4NnlSFW-',757659590,'72k')]:
        config={'MHPV2':'configs/mhp-v2/m2fp_R101_bs16_145k.yaml',
                'CIHP':'configs/cihp/m2fp_R101_bs16_265k.yaml',
                'LIP':'configs/lip/m2fp_R101_bs64_72k.yaml'}[data]
        add(f'M2FP_R101_{data}','M2FP','ResNet101','DATASET_SPECIFIC_WEIGHT_SAME_BACKBONE',data,
            f'https://drive.google.com/file/d/{link}/view',size,59 if data=='MHPV2' else 20,
            'Human (not native GT class)' if data!='LIP' else 'NONE',
            'FULL_FRAME_INSTANCE' if data!='LIP' else 'SINGLE_PERSON_SEMANTIC',
            'predominantly CC-BY-NC-4.0','RESEARCH_CONDITIONAL_SEPARATE_WEIGHT_TERMS',modern,
            'NATIVE_REFERENCE' if data!='LIP' else 'CROP_COMPATIBILITY_PENDING',
            f'Config training schedule {steps}; not a capacity label; real checkpoint/config load untested',config)
    cpi='LEGACY_MMDET_ENV_NOT_READY_PREBUILT_MMCV_ROUTE_UNTESTED'
    for data,backbone,link,size in [
        ('MHPV2','R50','15yp_c5ZNFbvkFn5K3wVkHix7F-m-3FBZ',566676956),
        ('MHPV2','ConvNeXtB','1qpdS8dEdhdjcYUOiDEiTusIyjifBAYCy',1299250784),
        ('CIHP','R50','1uiqPVZNWIEIKquMNhZ7tv3OTZrc9WGt0',571901148),
        ('CIHP','ConvNeXtB','117grkZS6Q-v5tbeTLdyENSI0fSRD09lK',1301413296)]:
        add(f'CPI_{backbone}_{data}','CPI-Parser',backbone,'BACKBONE_CAPACITY_AND_DATASET_SPECIFIC_WEIGHT',data,
            f'https://drive.google.com/file/d/{link}/view',size,59 if data=='MHPV2' else 20,'NONE',
            'FULL_FRAME_INTERNAL_DETECTION_PARSING','Apache-2.0 code',
            'SEPARATE_WEIGHT_RESEARCH_GRANT_SCOPE_REVIEW',cpi,'NATIVE_REFERENCE',
            'R50 versus ConvNeXtB is a real backbone difference; CIHP versus MHP weights/epoch75 are not different model sizes')
    add('FASHN_B4','fashn-human-parser','SegFormerB4','ONE_OFFICIAL_CHECKPOINT_VERIFIED','UNKNOWN',
        'https://huggingface.co/fashn-ai/fashn-human-parser/resolve/1f80c34dbab321c5730dda5c3fea279fd3e97498/model.safetensors',
        256146352,18,'NONE','SEMANTIC_IMAGE_OR_CROP_NO_NATIVE_PERSON_OWNERSHIP',
        'inherits NVIDIA SegFormer terms','NONCOMMERCIAL_RESEARCH_EVALUATION_ONLY_NO_DEPLOYMENT_CLEARANCE',
        'IMPORTS_AND_SYNTHETIC_FP32_GPU_PASS_NO_CHECKPOINT','CROP_COMPATIBILITY_PENDING',
        '384x576 native HxW; no clothing-expert superiority inferred; logits supported; native training exposure unknown')
    for data,size,config in [('CIHP',958247405,'configs/cihp/d2fp_R101_bs4_1060k_prior100.yaml'),
                             ('LIP',958249837,'configs/lip/d2fp_R101_bs64_72k_prior100_dec9_wo_enhance.yaml')]:
        add(f'D2FP_R101_{data}','D2FP','ResNet101','DATASET_SPECIFIC_WEIGHT_SAME_BACKBONE',data,
            f'https://github.com/cvlab-yongin/D2FP/releases/download/weights/{data.lower()}.pth',size,
            20,'Human (CIHP only)' if data=='CIHP' else 'NONE',
            'FULL_FRAME_INSTANCE' if data=='CIHP' else 'SINGLE_PERSON_SEMANTIC',
            'MIT locally; inherited M2FP code restrictions require review','WEIGHT_AND_INHERITED_LICENSE_REVIEW',modern,
            'NATIVE_REFERENCE' if data=='CIHP' else 'CROP_COMPATIBILITY_PENDING',
            'Official parser release (not R-103.pkl backbone). Config-to-released-weight compatibility untested.',config)
    for data,link,size,classes,geometry in [
        ('LIP','1k4dllHpu0bdx38J7H28rVVLpU-kOHmnH',267449349,20,'473x473'),
        ('ATR','1ruJg4lqR_jgQPj-9K0PP-L2vJERYOxLP',267445237,18,'512x512'),
        ('PASCAL_PERSON_PART','1E5YwNKW2VOEayK9mWCS3Kpsxf-3z04ZE',267422621,7,'512x512')]:
        add(f'SCHP_R101_{data}','SCHP','ResNet101','DATASET_SPECIFIC_WEIGHT_SAME_BACKBONE',data,
            f'https://drive.google.com/file/d/{link}/view',size,classes,'NONE','SINGLE_PERSON_SEMANTIC',
            'MIT code','SEPARATE_WEIGHT_GRANT_NOT_VERIFIED','LEGACY_ABN_CUDA_ENV_NOT_READY',
            'CROP_COMPATIBILITY_PENDING',f'{geometry} native input; checkpoint date is not size. No official SCHP-CIHP release verified.')
    for r in old:
        if r['model_id'].startswith(('QANet','CDGNet','RP','SAPIENS')):
            rows.append(dict(zip(fields,[r['model_id'],r['model_id'],r['variant'],'OPTIONAL_METADATA_ONLY',
                r['native_training_dataset'],r['checkpoint_source'],'UNKNOWN','NOT_DOWNLOADED',False,False,False,
                r['repository_commit'],'','',r['native_class_count_source'],'UNKNOWN',r['native_operating_mode'],
                r['code_license'],r['intended_use_eligibility'],'NOT_INSTALLED','NOT_TESTED',
                'LICENSE_EXCLUDED' if r['model_id'].startswith('SAPIENS') else 'OPTIONAL_NOT_SELECTED',
                'Historical source metadata retained; no installation or checkpoint execution authorized'])))
    path=S/'provenance/MODEL_VARIANT_REGISTRY_V2.csv'
    with path.open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    print(f'[MODELS] {len(rows)} metadata variants recorded; actual checkpoint inference=0')


if __name__=='__main__':main()
