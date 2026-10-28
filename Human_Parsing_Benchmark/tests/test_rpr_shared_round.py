"""Targeted control checks; never import/load model or use a GPU."""
from pathlib import Path
import sys,unittest,ast
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from run_rpr_shared_segment import validate_policy,derive_shared

class RPRSharedTests(unittest.TestCase):
    def test_explicit_shared_RPR_only(self):
        policy=dict(mode='SHARED_GPU_QUALITY_ONLY',authorized_models=['RPR_CIHP'],quality_only=True,timing_ranking_allowed=False)
        validate_policy(policy,'RPR_CIHP')
        for model,changes in [('CPI_R50_CIHP',{}),('RPR_CIHP',{'authorized_models':['RPR_CIHP','CPI_R50_CIHP']}),('RPR_CIHP',{'timing_ranking_allowed':True}),('RPR_CIHP',{'mode':'EXCLUSIVE'})]:
            with self.assertRaises(ValueError):validate_policy({**policy,**changes},model)

    def test_scientific_blocks_and_frozen_source_unchanged(self):
        path=P/'scripts/run_cihp_system.py';original=path.read_text();derived=derive_shared(original);ast.parse(derived)
        for start,end in [("stage='MODEL_INFERENCE'","stage='EXPORT'"),("stage='SCORING';truth","packet_bytes=sum")]:
            self.assertEqual(original.split(start,1)[1].split(end,1)[0],derived.split(start,1)[1].split(end,1)[0])
        self.assertIn("if busy and not segment['shared_GPU_quality_only']",derived)
        self.assertIn("actual_resource_mode='SHARED_GPU_QUALITY_ONLY'",derived)
        self.assertEqual(path.read_text(),original)

if __name__=='__main__':unittest.main()
