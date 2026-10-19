from pathlib import Path
import sys,unittest,tempfile,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.application_v2.acquisition import verify_asset_set
class AcquisitionTests(unittest.TestCase):
 def test_a19_missing_shard_and_partial(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'shard1';p.write_bytes(b'abc');r={'path':'shard1','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}
   self.assertEqual(verify_asset_set(d,[r])['status'],'VERIFIED_COMPLETE_DECLARED_SET')
   with self.assertRaises(ValueError):verify_asset_set(d,[r,{**r,'path':'shard2'}])
   p.write_bytes(b'ab')
   with self.assertRaises(ValueError):verify_asset_set(d,[r])
 def test_a19_duplicate_content_not_extra_unique_artifact(self):
  with tempfile.TemporaryDirectory() as d:
   rows=[]
   for name in ['a','b']:
    (Path(d)/name).write_bytes(b'abc');rows.append({'path':name,'bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()})
   self.assertEqual(verify_asset_set(d,rows)['unique_content_artifacts'],1)
 def test_a19_partial_filename_never_complete(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/'a.part').write_bytes(b'abc')
   with self.assertRaises(ValueError):verify_asset_set(d,[{'path':'a.part','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}])
