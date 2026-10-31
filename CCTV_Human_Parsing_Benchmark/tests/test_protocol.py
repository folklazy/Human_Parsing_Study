"""Independent hand-counted partial-label, composition and channel contracts."""
import unittest,sys,tempfile,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from benchmark import partial_confusion,summarize,yolo_input,load_spec,project,compose_native,H
from common_view.packets import write_packet,read_packet

class Acceptance(unittest.TestCase):
    def test_unknown_pixels_do_not_become_background_negatives(self):
        gt=np.array([[13,2,5,9,0,0]],np.uint8)
        pred=np.array([[1,2,3,4,1,3]],np.uint8)
        h=partial_confusion(gt,pred)
        self.assertEqual(h.sum(),4);self.assertEqual(summarize(h)['macro_recall4'],1.)
        self.assertIsNone(summarize(h)['full_image_mIoU'])
    def test_wrong_class_and_other_are_known_positive_misses(self):
        h=partial_confusion(np.array([[13,2,5,9]],np.uint8),np.array([[2,2,5,0]],np.uint8))
        self.assertEqual(summarize(h)['per_target_recall'],[0.,1.,0.,0.])
        self.assertEqual(summarize(h)['macro_recall4'],.25)
    def test_absent_class_null_not_perfect_or_zero_score(self):
        h=partial_confusion(np.array([[2,0]],np.uint8),np.array([[2,1]],np.uint8))
        self.assertEqual(summarize(h)['per_target_recall'],[None,1.,None,None])
        self.assertIsNone(summarize(h)['macro_recall4'])
    def test_other_preserved_before_overlap_and_total_label_mapping(self):
        spec=load_spec(H/'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json')
        planes=np.array([[[5,2]],[[6,0]]],np.uint8)
        pred=project(compose_native(planes,[.2,.9],(1,2)),'CIHP_GT_AND_NATIVE_PRED',spec)
        self.assertEqual(pred.tolist(),[[5,2]])
        for space,n in [('CIHP_GT_AND_NATIVE_PRED',20),('SAPIENS2_DOME29_PRED',29)]:
            self.assertEqual(project(np.arange(n,dtype=np.uint8),space,spec).shape,(n,))
        with self.assertRaises(ValueError):project(np.array([255],np.uint8),'CIHP_GT_AND_NATIVE_PRED',spec)
    def test_asymmetric_rgb_to_ultralytics_bgr(self):
        rgb=np.zeros((3,5,3),np.uint8);rgb[1,4]=[10,20,90]
        out=yolo_input(rgb);self.assertEqual(out[1,4].tolist(),[90,20,10]);self.assertTrue(out.flags.c_contiguous)
        self.assertEqual(rgb[1,4].tolist(),[10,20,90])
    def test_atomic_packet_to_partial_scorer_to_json_null_report(self):
        gt=np.array([[13,2,5,9,0]],np.uint8)
        planes=np.array([[[13,2,6,9,13]]],np.uint8)
        spec=load_spec(H/'protocol/CIHP_SAPIENS_COMMON_VIEW_REVISION2.json')
        with tempfile.TemporaryDirectory() as temp:
            path=write_packet(temp,'synthetic',{'person_semantic_masks':planes,'person_extents':np.ones_like(planes,bool),'person_scores':np.array([.8],np.float32)},
                              {'image_id':'synthetic'}, {'partial':{}})
            _,a=read_packet(path)
            pred=project(compose_native(a['person_semantic_masks'],a['person_scores'],gt.shape),'CIHP_GT_AND_NATIVE_PRED',spec)
            result=summarize(partial_confusion(gt,pred))
            serialized=json.loads(json.dumps(result,allow_nan=False))
            self.assertEqual(serialized['per_target_recall'],[1.,1.,0.,1.])
            self.assertEqual(serialized['macro_recall4'],.75)
            self.assertIsNone(serialized['full_image_precision'])

if __name__=='__main__':unittest.main()
