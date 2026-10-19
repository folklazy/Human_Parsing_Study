"""Synthetic converted-annotation fixtures; no parser or original-GT mutation."""
import base64
from io import BytesIO
from pathlib import Path
import sys
import unittest
import zlib
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.data.cihp_datasetninja import decode_bitmap,reconstruct_semantic,NATIVE_IDS


def object_fixture(mask,origin=(0,0),name='face',palette=False):
    f=BytesIO()
    if palette:
        image=Image.fromarray(mask.astype(np.uint8),'P');image.putpalette([0,0,0,255,255,255]+[0]*762)
        image.save(f,format='PNG',transparency=0)
    else:
        rgba=np.zeros((*mask.shape,4),np.uint8);rgba[...,3]=mask.astype(np.uint8)*255
        Image.fromarray(rgba).save(f,format='PNG')
    return {'id':1,'geometryType':'bitmap','classTitle':name,'tags':[],
            'bitmap':{'origin':list(origin),'data':base64.b64encode(zlib.compress(f.getvalue())).decode()}}


class ConvertedCIHPTests(unittest.TestCase):
    def test_RGBA_alpha_support(self):
        mask=np.array([[1,0],[0,1]],bool);tile,xy,label=decode_bitmap(object_fixture(mask),(2,2))
        np.testing.assert_array_equal(mask,tile);self.assertEqual((xy,label),((0,0),13))
    def test_palette_transparency_support(self):
        mask=np.array([[1,0],[1,1]],bool);tile,_,_=decode_bitmap(object_fixture(mask,palette=True),(2,2))
        np.testing.assert_array_equal(mask,tile)
    def test_origin_places_pixels_in_original_grid(self):
        mask=np.array([[1,0],[0,1]],bool)
        result,diag=reconstruct_semantic({'size':{'width':5,'height':4},'objects':[object_fixture(mask,(2,1))]})
        expected=np.zeros((4,5),np.uint8);expected[1,2]=13;expected[2,3]=13
        np.testing.assert_array_equal(result,expected);self.assertEqual(diag['person_identity'],'NOT_AVAILABLE')
    def test_person_ID_not_derived_from_part_object_ID(self):
        result,diag=reconstruct_semantic({'size':{'width':1,'height':1},'objects':[object_fixture(np.ones((1,1),bool))]})
        self.assertEqual(diag['person_identity'],'NOT_AVAILABLE');self.assertEqual(result[0,0],13)
    def test_conflicting_part_masks_report_ambiguity(self):
        objects=[object_fixture(np.ones((1,1),bool),name=n) for n in ['face','hair']]
        _,diag=reconstruct_semantic({'size':{'width':1,'height':1},'objects':objects})
        self.assertEqual(diag['overlap_pixels'],1);self.assertEqual(diag['cross_class_overwrite_events'],1)
    def test_reject_out_of_bounds_and_negative_origin(self):
        for origin in [(-1,0),(1,0)]:
            with self.assertRaises(ValueError):decode_bitmap(object_fixture(np.ones((2,2),bool),origin),(2,2))
    def test_reject_unknown_class_and_empty_support(self):
        for obj in [object_fixture(np.ones((1,1),bool),name='Human'),object_fixture(np.zeros((1,1),bool))]:
            with self.assertRaises(ValueError):decode_bitmap(obj,(1,1))
    def test_reject_corrupt_encoding_and_compression(self):
        for data in ['!notbase64!',base64.b64encode(b'not-zlib').decode()]:
            obj=object_fixture(np.ones((1,1),bool));obj['bitmap']['data']=data
            with self.assertRaises((ValueError,zlib.error)):decode_bitmap(obj,(1,1))
    def test_native_IDs_are_not_datasetninja_numeric_class_IDs(self):
        self.assertEqual(set(NATIVE_IDS.values()),set(range(1,20)))
        self.assertEqual(NATIVE_IDS['torso_skin'],10);self.assertNotIn('Human',NATIVE_IDS)


if __name__=='__main__':unittest.main()
