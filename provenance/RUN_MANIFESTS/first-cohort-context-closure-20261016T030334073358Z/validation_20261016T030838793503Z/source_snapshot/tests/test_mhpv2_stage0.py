"""Synthetic correctness fixtures only. No PPSS files or models imported."""
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
import sys
import unittest
import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.data.mhpv2 import decode_native, bounding_region, lossless_roundtrip, PersonGroundTruth
from src.evaluation.common_metrics import confusion_matrix, scores, person_macro, match_persons, target_ownership
from src.contracts.prediction import validate_prediction, export_prediction
from src.adapters.base import BaseParserAdapter


def record():
    return {'schema_version':'1.0','study_id':'human_parsing_mhpv2','run_id':'synthetic','model_id':'fixture',
            'source_commit':'0'*40,'checkpoint_sha256':'0'*64,'source_track':'SMOKE_SYNTHETIC',
            'image_id':'synthetic','original_wh':[4,3],'native_input_wh':[4,3], 'crop_xyxy':None,
            'native_labels':[0,1,2],'predicted_person_ids':['p1'],'source_person_id':None,
            'ownership_status':'NATIVE_INSTANCE','transforms':{'identity':True},'precision':'FP32',
            'environment':'synthetic_numpy','dataset_manifest_sha256':'0'*64,'scores':[.9],'logits_available':False}


class NativeGTTests(unittest.TestCase):
    def test_red_channel_and_alpha_are_distinct(self):
        with TemporaryDirectory() as directory:
            labels=np.array([[0,58],[3,50]],np.uint8)
            rgba=np.zeros((2,2,4),np.uint8);rgba[...,0]=labels;rgba[...,3]=255
            p=Path(directory)/'1_01_01.png';Image.fromarray(rgba).save(p)
            np.testing.assert_array_equal(decode_native(p),labels)
            self.assertFalse(np.array_equal(np.array(Image.open(p).convert('L')),labels))
    def test_roundtrip_and_background(self):
        labels=np.array([[0,58],[3,50]],np.uint8)
        self.assertTrue(lossless_roundtrip(labels));self.assertIsNone(bounding_region(np.zeros((2,2),bool)))
        self.assertEqual(bounding_region(labels>0),[0,0,2,2])
    def test_invalid_labels_rejected(self):
        with TemporaryDirectory() as directory:
            p=Path(directory)/'bad.png';Image.fromarray(np.array([[255]],np.uint8)).save(p)
            with self.assertRaises(ValueError):decode_native(p)
    def test_instance_identity_and_fingerprint(self):
        with TemporaryDirectory() as directory:
            p=Path(directory)/'12_02_01.png';Image.fromarray(np.array([[0,3],[58,0]],np.uint8)).save(p)
            gt=PersonGroundTruth('12',1,p.name,(2,2),sha256(p.read_bytes()).hexdigest())
            self.assertEqual(gt.canonical_id,'12:parsing:1');self.assertEqual(gt.foreground(directory).sum(),2)
            self.assertEqual(gt.body_clothing_support(directory).sum(),2)
            bad=PersonGroundTruth('12',1,p.name,(3,2),gt.annotation_sha256)
            with self.assertRaises(ValueError):bad.read(directory)
    def test_overlap_planes_not_flattened(self):
        a=np.array([[0,3],[4,0]],np.uint8);b=np.array([[0,5],[6,0]],np.uint8)
        planes=np.stack([a,b]);self.assertEqual(np.count_nonzero(np.sum(planes>0,axis=0)>1),2)
        self.assertTrue(lossless_roundtrip(planes[0]));self.assertTrue(lossless_roundtrip(planes[1]))


class MetricTests(unittest.TestCase):
    def setUp(self):self.gt=np.array([[0,1],[2,0]],np.int64)
    def test_perfect(self):self.assertEqual(scores(confusion_matrix(self.gt,self.gt,3))['miou'],1.)
    def test_wrong_class(self):
        pred=self.gt.copy();pred[0,1]=2
        self.assertLess(scores(confusion_matrix(self.gt,pred,3))['miou'],1.)
    def test_no_prediction_and_missing_person(self):
        empty=np.zeros_like(self.gt)
        self.assertEqual(person_macro([self.gt,self.gt],[self.gt,empty],3)['person_macro_miou'],.5)
    def test_absent_class_empty_union(self):
        result=scores(confusion_matrix(np.zeros((2,2),int),np.zeros((2,2),int),3))
        self.assertIsNone(result['miou']);self.assertTrue(np.isnan(result['iou'][1]))
    def test_ignore(self):
        gt=self.gt.copy();gt[0,0]=255;pred=self.gt.copy();pred[0,0]=2
        hist=confusion_matrix(gt,pred,3);self.assertEqual(hist.sum(),3);self.assertEqual(scores(hist)['miou'],1.)
    def test_unsupported_prediction_explicit(self):
        pred=self.gt.copy();pred[0,1]=99
        result=scores(confusion_matrix(self.gt,pred,3));self.assertEqual(result['unmapped_prediction_pixels'],1)
        self.assertEqual(result['gt_support'],[2,1,1]);self.assertLess(result['miou'],1.)
    def test_unsupported_gt_not_background(self):
        with self.assertRaises(ValueError):confusion_matrix(np.array([[99]]),np.array([[0]]),3)
    def test_wrong_dimensions(self):
        with self.assertRaises(ValueError):confusion_matrix(self.gt,np.zeros((4,4)),3)
    def test_global_versus_person_macro_are_named_separately(self):
        a=np.ones((2,2),int);b=np.ones((2,2),int);b[0,0]=2
        global_result=scores(confusion_matrix(a,a,3)+confusion_matrix(b,np.zeros_like(b),3))['miou']
        macro=person_macro([a,b],[a,np.zeros_like(b)],3)['person_macro_miou']
        self.assertNotEqual(global_result,macro)


class MatchingOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.a=np.array([[1,0],[0,0]],bool);self.b=np.array([[0,0],[0,1]],bool)
    def test_perfect_missing_duplicate(self):
        result=match_persons([self.a,self.b],[self.a,self.a]);self.assertEqual(len(result['matches']),1)
        self.assertEqual(result['unmatched_gt'],[1]);self.assertEqual(len(result['unmatched_predictions']),1)
    def test_swapped_list_order_uses_geometry(self):
        self.assertEqual(match_persons([self.a,self.b],[self.b,self.a])['matches'],[(0,1,1.),(1,0,1.)])
    def test_overlapping_people_remain_separate(self):
        self.assertEqual(len(match_persons([self.a,self.a],[self.a,self.a])['matches']),2)
    def test_empty_masks_not_perfect(self):
        empty=np.zeros_like(self.a);self.assertEqual(match_persons([empty],[empty])['matches'],[])
        with self.assertRaises(ValueError):match_persons([empty],[empty],threshold=0)
    def test_ignore_domain_matching(self):
        full=np.ones_like(self.a);self.assertEqual(len(match_persons([self.a],[full],valid=self.a)['matches']),1)
    def test_ownership_ambiguity_and_neighbors(self):
        semantic=np.ones((2,2),int);target=np.array([[1,1],[0,0]],bool);neighbor=np.array([[0,1],[1,0]],bool)
        result=target_ownership(semantic,target,[neighbor]);self.assertEqual(result['owned_labels'].tolist(),[[1,-1],[-1,-1]])
        self.assertEqual(result['native_foreground_outside_target_pixels'],2)
        np.testing.assert_array_equal(semantic,np.ones((2,2)))


class PredictionContractTests(unittest.TestCase):
    def test_valid_and_lossless_export(self):
        labels=np.zeros((1,3,4),np.uint8);labels[0,1,1]=2
        with TemporaryDirectory() as directory:
            exported=export_prediction(Path(directory)/'run',record(),labels)
            with np.load(Path(directory)/'run/native.npz',allow_pickle=False) as saved:
                np.testing.assert_array_equal(saved['native_semantic_maps'],labels)
            self.assertTrue(validate_prediction(exported,labels))
    def test_duplicate_identity_rejected(self):
        r=record();r['predicted_person_ids']=['a','a']
        with self.assertRaises(ValueError):validate_prediction(r)
    def test_bad_crop_map_back(self):
        r=record();r['crop_xyxy']=[1,0,4,3];r['transforms']={'crop_to_original':{'offset_xy':[0,0],'scale_xy':[1,1]}}
        with self.assertRaises(ValueError):validate_prediction(r)
        for field,bad in [('original_wh',[0,3]),('native_input_wh',[4,-1]),('source_commit','unversioned'),('native_labels',[0,1,1])]:
            invalid=record();invalid[field]=bad
            with self.assertRaises(ValueError):validate_prediction(invalid)
    def test_nonfinite_score(self):
        r=record();r['scores']=[float('nan')]
        with self.assertRaises(ValueError):validate_prediction(r)
        with TemporaryDirectory() as directory:
            labels=np.zeros((1,3,4),np.uint8);r=record();r['logits_available']=True
            with self.assertRaises(ValueError):export_prediction(Path(directory)/'missing',r,labels)
            with self.assertRaises(ValueError):export_prediction(Path(directory)/'wrong_grid',r,labels,np.zeros((1,3,2,4)))
            with self.assertRaises(ValueError):export_prediction(Path(directory)/'nonfinite',r,labels,np.full((1,3,3,4),np.nan))
    def test_abstract_adapter_cannot_claim_ready(self):
        with self.assertRaises(TypeError):BaseParserAdapter()


if __name__=='__main__':unittest.main()
