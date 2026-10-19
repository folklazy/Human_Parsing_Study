"""Synthetic population integration and the real disabled launch boundary, CPU only."""
from pathlib import Path
from io import BytesIO
import copy
import hashlib
import json
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import numpy as np
from PIL import Image

S=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(S))
from src.application_v2.policy import load_config,digest
from src.application_v2.validation_launch import validation_plan,population_view,population_reports,package_data,require_validation_authorization
from src.application_v2.scoring import score_frame
from src.application_v2.validation_data import read_rgb,read_gt,pixels_hash


class ValidationLaunchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=load_config(S/'configs/application_v2_first_cohort_v11.yaml',benchmark=True)

    def synthetic(self):
        cfg=copy.deepcopy(self.cfg)
        cfg.pop('validation_launch')
        template={model:copy.deepcopy(next(iter(rows.values()))) for model,rows in cfg['scoring_contexts'].items()}
        for row in template.values():
            row.pop('input_binding');row['domain'].pop('image_binding')
        images=[]
        for iid in ['a','b','c']:
            images.append(dict(image_id=iid,G_loc=1,G_sem=1,main=iid!='c',
                input_binding=dict(status='VERIFIED',image_id=iid,input_sha256=digest(iid),original_wh=[2,2]),
                image_domain_binding=dict(image_id=iid,G_loc=1,G_sem=1,GT_domain_recipe_sha256=digest(['GT',iid]))))
        reference=population_view(cfg,images,template,'reference')
        mapping=json.loads((S/cfg['cohort']['mapping']).read_text())
        gt=[dict(id='gt:1',bbox=[0,0,2,2],loc_eligible=True,sem_eligible=True,
            semantic=np.ones((2,2),np.int16),valid=np.ones((2,2),bool))]
        predictions=[dict(id='pred:1',score=.9,evaluation_bbox=dict(xyxy=[0,0,2,2],source='NATIVE_PARSER_BOX',
            coordinate_convention='XYXY_HALF_OPEN',derivation_revision='SYNTHETIC_FIXTURE'),semantic=np.ones((2,2),np.int16))]
        frames=[]
        for model in cfg['first_cohort']['models']:
            for iid,context in reference['scoring_contexts'][model].items():
                scored=score_frame(context,mapping,context['model_binding'],context['input_binding'],gt,predictions,lifecycle=dict(status='COMPLETE',events=[]))
                scored.update(system_id=model,image_id=iid)
                frames.append(dict(system_id=model,image_id=iid,execution_status='COMPLETE',failure_events=[],score_result=scored))
        return cfg,images,template,frames

    def test_real_plan_one_reference_inference_population(self):
        plan=validation_plan(self.cfg,S)
        self.assertEqual((plan['unique_RGB_inputs'],plan['detector_frame_jobs'],plan['parser_frame_jobs']),(5000,5000,10000))
        self.assertEqual(plan['populations']['main']['images'],4961)
        self.assertFalse(plan['model_loading']);self.assertTrue(plan['full_benchmark'])

    def test_shared_scores_admitted_with_distinct_population_revisions(self):
        cfg,images,templates,frames=self.synthetic()
        reports=population_reports(cfg,images,templates,frames)
        self.assertEqual([r['population']['frames'] for r in reports['main']['systems']],[2,2])
        self.assertEqual([r['population']['frames'] for r in reports['reference']['systems']],[3,3])
        self.assertNotEqual(reports['main']['comparison'],reports['reference']['comparison'])
        self.assertTrue(all(r['main_metrics']['Q_person_sem_GT']==1 for report in reports.values() for r in report['systems']))

    def test_failure_outside_main_does_not_invalidate_main(self):
        cfg,images,templates,frames=self.synthetic()
        failure=next(r for r in frames if r['image_id']=='c')
        failure.update(execution_status='FAILED',score_result=None,failure_events=[dict(status='MODEL_SYSTEM_FAILURE')])
        reports=population_reports(cfg,images,templates,frames)
        self.assertEqual(reports['main']['systems'][0]['status'],'COMPLETE')
        self.assertEqual(reports['reference']['systems'][0]['status'],'INCOMPLETE')
        self.assertIsNone(reports['reference']['systems'][0]['main_metrics'])
        self.assertEqual(reports['reference']['systems'][0]['execution']['denominator'],3)

    def test_changed_image_context_rejects_score_reuse(self):
        cfg,images,templates,frames=self.synthetic()
        images[0]['input_binding']['input_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'bound scoring'):
            population_reports(cfg,images,templates,frames)

    def test_secondary_cannot_be_labelled_primary_or_vice_versa(self):
        cfg,images,templates,frames=self.synthetic()
        with self.assertRaisesRegex(ValueError,'bound scoring'):
            population_reports(cfg,images,templates,frames,matching_view='secondary')

    def test_launch_rejected_before_process_or_output_creation(self):
        from src.application_v2.first_cohort_validation import execute_validation
        with tempfile.TemporaryDirectory() as directory,patch('subprocess.run',side_effect=AssertionError('GPU/process must not start')):
            output=Path(directory)/'not-created'
            with self.assertRaises(ValueError):
                execute_validation(S/'configs/application_v2_first_cohort_v10.yaml',output)
            self.assertFalse(output.exists())

    def test_setting_flags_is_not_user_approval(self):
        config=load_config(S/'configs/application_v2_first_cohort_v10.yaml')
        config['status']='FROZEN';config['authorization']['full_benchmark']=True
        config['authorization']['allowed_modes'].append('VALIDATION_BENCHMARK')
        config['validation_launch'].update(status='ACCEPTED',execution_authorized=True)
        with self.assertRaisesRegex(ValueError,'accepted execution decision'):
            require_validation_authorization(config,S)

    def test_source_rgb_byte_and_decoded_geometry_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            out=BytesIO();Image.fromarray(np.full((2,3,3),128,np.uint8)).save(out,format='JPEG');raw=out.getvalue()
            with Image.open(BytesIO(raw)) as image:rgb=np.asarray(image.convert('RGB')).copy()
            archive=Path(directory)/'fixture.tar';archive.write_bytes(b'padding'+raw)
            sample=dict(RGB_tar_data_offset=7,RGB_bytes=len(raw),RGB_sha256=hashlib.sha256(raw).hexdigest(),wh=[3,2],
                decoded_RGB_sha256=hashlib.sha256(struct.pack('>II',3,2)+rgb.tobytes()).hexdigest())
            _,decoded=read_rgb(archive,sample);np.testing.assert_array_equal(rgb,decoded)
            sample['wh']=[2,3]
            with self.assertRaisesRegex(ValueError,'geometry'):read_rgb(archive,sample)

    def test_lazy_gt_reader_matches_existing_contract_semantics(self):
        mapping=json.loads((S/self.cfg['cohort']['mapping']).read_text())
        category=np.array([[13,0],[0,0]],np.uint8);human=np.array([[1,0],[0,0]],np.uint8)
        target=np.array([[1,0],[0,0]],np.int16);valid=np.ones((2,2),bool)
        source=[];payload={}
        for name,array in [('Category_ids',category),('Human_ids',human),('Instance_ids',human.astype(np.uint16))]:
            stream=BytesIO();Image.fromarray(array).save(stream,format='PNG');raw=stream.getvalue();payload[name+'.png']=raw
            source.append(dict(component=name,member=name+'.png',sha256=hashlib.sha256(raw).hexdigest(),dtype=str(array.dtype),wh=[2,2]))
        persons=[dict(image_id='fixture',person_id=1,bbox_xyxy_half_open=[0,0,1,1],G_loc=True,G_sem=True,
            semantic_sha256=pixels_hash(target),valid_sha256=pixels_hash(valid))]
        protocol=self.cfg['first_cohort']['protocol']
        recipe=dict(image_id='fixture',source_maps=source,original_wh=[2,2],GT_projection_sha256=protocol['mapping']['GT_projection_sha256'],domain_policy_sha256=protocol['domain']['policy_sha256'])
        contract=digest(dict(category=pixels_hash(category),human=pixels_hash(human),target=pixels_hash(target),global_valid=pixels_hash(valid),persons=persons))
        binding=dict(image_id='fixture',source_GT=source,input_binding=dict(original_wh=[2,2]),
            image_domain_binding=dict(GT_domain_recipe_sha256=digest(recipe),decoded_GT_contract_sha256=contract))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.zip'
            with zipfile.ZipFile(path,'w') as archive:
                for name,raw in payload.items():archive.writestr(name,raw)
            with zipfile.ZipFile(path) as archive:
                gt=read_gt(archive,binding,persons,mapping,protocol)
                np.testing.assert_array_equal(gt[0]['semantic'],target)
                bad=copy.deepcopy(persons);bad[0]['bbox_xyxy_half_open']=[0,0,2,2]
                with self.assertRaisesRegex(ValueError,'decoded GT'):read_gt(archive,binding,bad,mapping,protocol)


if __name__=='__main__':unittest.main()
