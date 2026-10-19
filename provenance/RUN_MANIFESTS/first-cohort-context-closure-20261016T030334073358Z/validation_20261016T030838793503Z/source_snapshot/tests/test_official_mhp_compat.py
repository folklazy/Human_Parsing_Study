"""Synthetic fixtures only; tests do not open public validation or parser weights."""
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout
from io import StringIO
import sys
import unittest
import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.evaluation.official_mhp_compat import evaluate_native,evaluate_volume,reference_functions,THRESHOLDS


class OfficialCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(prefix='mhp-evaluator-fixture-')
        self.gt=np.array([[0,1,1],[0,2,2]],np.uint8)
        self.data=[self.item('fixture',[self.gt])]
    def tearDown(self):self.tmp.cleanup()
    def item(self,name,masks):
        boxes=[]
        for i,mask in enumerate(masks):
            path=Path(self.tmp.name)/f'{name}_{i}.png';Image.fromarray(mask).save(path)
            boxes.append({'ann_path':str(path),'x1':0,'y1':0,'x2':mask.shape[1]-1,'y2':mask.shape[0]-1})
        return {'filepath':name+'.jpg','bboxes':boxes}
    def predictions(self,masks,scores=None,name='fixture'):
        scores=scores or [.9]*len(masks)
        return {name:{'MASKS':masks,'DETS':[(0,0,m.shape[1]-1,m.shape[0]-1,s) for m,s in zip(masks,scores)]}}
    def reference(self,predictions,data,threshold):
        with redirect_stdout(StringIO()),np.errstate(divide='ignore',invalid='ignore'):
            return reference_functions()['eval_seg_ap'](predictions,data,nb_class=59,ovthresh_seg=threshold)
    def test_perfect_all_nine_thresholds(self):
        result=evaluate_volume(self.predictions([self.gt]),self.data)
        self.assertEqual(result['APp_vol'],1.);self.assertEqual(result['PCP50'],1.)
        self.assertEqual(len(result['per_threshold']),9)
    def test_global_empty_with_GT_zero_scores(self):
        for p in [{},self.predictions([])]:
            r=evaluate_volume(p,self.data);self.assertEqual(r['APp_vol'],0.);self.assertEqual(r['PCP50'],0.)
            self.assertEqual(r['per_threshold'][0]['GT_person_support'],1)
    def test_no_GT_is_undefined_even_with_predictions(self):
        for p in [{},self.predictions([self.gt])]:
            r=evaluate_volume(p,[self.item('fixture',[])]);self.assertIsNone(r['APp_vol']);self.assertIsNone(r['PCP50'])
    def test_one_missed_person_remains_in_PCP_denominator(self):
        other=np.array([[0,0,0],[3,3,0]],np.uint8)
        r=evaluate_native(self.predictions([self.gt]),[self.item('fixture',[self.gt,other])])
        self.assertEqual(r['GT_person_support'],2);self.assertEqual(r['PCP'],.5);self.assertEqual(r['APp'],.5)
    def test_duplicate_after_TP_preserves_reference_AP(self):
        r=evaluate_native(self.predictions([self.gt,self.gt],[.9,.8]),self.data)
        self.assertEqual(r['APp'],1.);self.assertEqual(r['PCP'],1.);self.assertEqual(r['prediction_person_count'],2)
    def test_confidence_order_changes_AP_without_changing_PCP(self):
        bad=np.where(self.gt>0,3,0).astype(np.uint8)
        first=evaluate_native(self.predictions([bad,self.gt],[.9,.8]),self.data)
        last=evaluate_native(self.predictions([bad,self.gt],[.7,.9]),self.data)
        self.assertEqual(first['APp'],.5);self.assertEqual(last['APp'],1.);self.assertEqual(first['PCP'],last['PCP'])
    def test_swapped_native_plane_order_matches_semantics(self):
        a=np.array([[1,1,0,0],[0,0,0,0]],np.uint8);b=np.array([[0,0,0,0],[0,0,2,2]],np.uint8)
        r=evaluate_native(self.predictions([b,a]),[self.item('fixture',[a,b])]);self.assertEqual(r['APp'],1.);self.assertEqual(r['PCP'],1.)
    def test_strict_threshold_and_known_volume(self):
        gt=np.array([[1,1,1,2,2,2]],np.uint8);pred=np.array([[1,1,2,2,2,1]],np.uint8)
        r=evaluate_volume(self.predictions([pred]),[self.item('fixture',[gt])])
        self.assertEqual(r['APp50'],0.);self.assertAlmostEqual(r['APp_vol'],4/9)
    def test_background_contribution_preserved(self):
        wrong=np.where(self.gt>0,3,0).astype(np.uint8)
        r=evaluate_volume(self.predictions([wrong]),self.data)
        self.assertAlmostEqual(r['APp_vol'],2/9);self.assertEqual(r['PCP50'],0.)
    def test_RGBA_first_channel_semantics(self):
        rgba=np.zeros((*self.gt.shape,4),np.uint8);rgba[...,0]=self.gt;rgba[...,3]=255
        r=evaluate_native(self.predictions([self.gt]),[self.item('fixture',[rgba])]);self.assertEqual(r['APp'],1.)
    def test_native_ignore_pixels_use_reference_domain(self):
        gt=self.gt.copy();gt[:,0]=255
        pred=self.gt.copy();pred[:,0]=4
        data=[self.item('fixture',[gt])];p=self.predictions([pred])
        for t in THRESHOLDS:
            r=evaluate_native(p,data,threshold=t)
            self.assertEqual((r['APp'],r['PCP']),self.reference(p,data,t))
            self.assertEqual(r['APp'],1.)
    def test_all_background_GT_plane_is_not_a_supported_person(self):
        data=[self.item('fixture',[np.zeros_like(self.gt)])]
        r=evaluate_volume({},data);self.assertIsNone(r['APp_vol'])
        self.assertEqual(r['per_threshold'][0]['GT_person_support'],0)
    def test_empty_image_predictions_are_FP_when_global_GT_exists(self):
        p=self.predictions([self.gt],[.8]);p.update(self.predictions([self.gt],[.9],'empty'))
        r=evaluate_native(p,self.data+[self.item('empty',[])]);self.assertEqual(r['APp'],.5);self.assertEqual(r['PCP'],1.)
    def test_one_empty_frame_does_not_crash(self):
        data=self.data+[self.item('empty',[])];p=self.predictions([self.gt]);p.update(self.predictions([] ,name='empty'))
        self.assertEqual(evaluate_native(p,data)['APp'],1.)
    def test_equal_confidence_reference_behavior(self):
        wrong=np.where(self.gt>0,3,0).astype(np.uint8);p=self.predictions([wrong,self.gt],[.9,.9])
        r=evaluate_native(p,self.data);ap,pcp=self.reference(p,self.data,.5);self.assertEqual((r['APp'],r['PCP']),(ap,pcp))
    def test_overlapping_individual_GT_planes_preserved(self):
        a=np.array([[1,1],[0,0]],np.uint8);b=np.array([[0,2],[0,2]],np.uint8)
        p=self.predictions([a,b]);data=[self.item('fixture',[a,b])]
        for t in THRESHOLDS:
            r=evaluate_native(p,data,threshold=t);self.assertEqual((r['APp'],r['PCP']),self.reference(p,data,t))
    def test_nonempty_reference_parity_all_thresholds(self):
        bad=np.where(self.gt>0,3,0).astype(np.uint8)
        for masks in [[self.gt],[bad],[self.gt,self.gt],[bad,self.gt]]:
            p=self.predictions(masks,[.9-i*.1 for i in range(len(masks))])
            for t in THRESHOLDS:
                r=evaluate_native(p,self.data,threshold=t);self.assertEqual((r['APp'],r['PCP']),self.reference(p,self.data,t))
    def test_matching_confidence_and_duplicate_fixtures_across_nine_thresholds(self):
        other=np.array([[0,0,0],[3,3,0]],np.uint8)
        wrong=np.where(self.gt>0,3,0).astype(np.uint8)
        fixtures=[(self.predictions([self.gt]),[self.item('fixture',[self.gt,other])]),
                  (self.predictions([wrong,self.gt],[.9,.8]),self.data),
                  (self.predictions([wrong,self.gt],[.7,.9]),self.data),
                  (self.predictions([self.gt,self.gt],[.9,.8]),self.data)]
        for p,data in fixtures:
            r=evaluate_volume(p,data)
            expected=[]
            for row,t in zip(r['per_threshold'],THRESHOLDS):
                ap,pcp=self.reference(p,data,t);expected.append(ap)
                self.assertEqual((row['APp'],row['PCP']),(ap,pcp))
            self.assertEqual(r['APp_vol'],float(np.mean(expected)))
    def test_reject_invalid_grid_labels_scores_and_ids(self):
        cases=[self.predictions([np.zeros((4,4),np.uint8)]),self.predictions([np.full_like(self.gt,255)]),
               self.predictions([self.gt],[float('nan')]),self.predictions([self.gt],name='unknown')]
        for p in cases:
            with self.assertRaises(ValueError):evaluate_native(p,self.data)
        with self.assertRaises(ValueError):evaluate_native(self.predictions([self.gt]),self.data+self.data)


if __name__=='__main__':unittest.main()
