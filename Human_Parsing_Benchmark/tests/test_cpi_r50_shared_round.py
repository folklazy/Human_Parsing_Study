"""CPU-only binding/scope/metadata checks for the CPI-specific control path."""
from pathlib import Path
import sys,unittest,ast,tempfile,json,hashlib,copy
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from run_cpi_r50_shared_segment import validate_policy,derive_shared
from run_cpi_r50_quality_round import MID
from rpr_progress import snapshot
from refresh_cpi_r50_overview import refresh

class CPISharedTests(unittest.TestCase):
    def test_exact_CPI_R50_scope(self):
        self.assertEqual(MID,'CPI_R50_CIHP');policy=dict(mode='SHARED_GPU_QUALITY_ONLY',authorized_models=[MID],quality_only=True,timing_ranking_allowed=False);validate_policy(policy,MID)
        for model in ['RPR_CIHP','CPI_ConvNeXtB_CIHP']:
            with self.assertRaises(ValueError):validate_policy(policy,model)

    def test_frozen_scientific_blocks_and_CPI_IO_label(self):
        original=(P/'scripts/run_cihp_system.py').read_text();derived=derive_shared(original);ast.parse(derived)
        for start,end in [("stage='MODEL_INFERENCE'","stage='EXPORT'"),("stage='SCORING';truth","packet_bytes=sum")]:self.assertEqual(original.split(start,1)[1].split(end,1)[0],derived.split(start,1)[1].split(end,1)[0])
        self.assertIn('CPI internal file I/O IS included',derived);self.assertNotIn('RPR native preprocessing',derived)

    def test_progress_uses_CPI_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'segments'/MID).mkdir(parents=True);(root/'ROUND_STATUS.json').write_text(json.dumps({'status':'RUNNING','expected':5000,'controller_PID':1,'worker_PID':2}));(root/'segments'/MID/'RUN.json').write_text(json.dumps({'complete':12}));s=snapshot(root,lambda *_:True,model=MID,controller_script='run_cpi_r50_quality_round.py',worker_script='run_cpi_r50_shared_segment.py');self.assertEqual(s['inference_complete'],12);self.assertEqual(s['model_id'],MID)

    def test_overview_copies_only_authorized_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'manifests').mkdir();(root/'metrics').mkdir();(root/'runs').mkdir();rows=[]
            for i,mid in enumerate(['Q','M','D','R',MID,'CPI_ConvNeXtB_CIHP']):
                f=root/'runs'/(mid+'.json');f.write_text('{}');rows.append(dict(model_id=mid,status='COMPLETE' if i<4 else 'INCOMPLETE',expected_IDs=5000,complete=5000 if i<4 else 0,failed_VAL=0,invalid_VAL=0,not_attempted_VAL=0 if i<4 else 5000,mIoU_20_including_BG=.4 if i<4 else None,mIoU_19_foreground=.3 if i<4 else None,resource_policy='old',execution_segment_or_record='old',canonical_source=str(f.relative_to(root)),canonical_source_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),timing_rank_eligible=False))
            old=copy.deepcopy(rows);index=dict(models=rows,CSV='metrics/overview.csv',frozen_scientific_config_sha256='hash');(root/'manifests/CIHP_NATIVE_COHORT_INDEX.json').write_text(json.dumps(index));source=root/'runs/new.json';source.write_text(json.dumps(dict(model_id=MID,expected=5000,frozen_config_sha256='hash',status='COMPLETE',complete=5000,missing_IDs=0,duplicate_IDs=0,round_id='new',metrics={'primary':{'mIoU_20_including_BG':.5,'mIoU_19_foreground':.45}})));text=refresh(source,'prefix\n## Current cohort overview\nold\n## unrelated\npreserved',root);got=json.loads((root/'manifests/CIHP_NATIVE_COHORT_INDEX.json').read_text());self.assertEqual(got['complete_models'],5);self.assertEqual(got['models'][:4],old[:4]);self.assertEqual(got['models'][5],old[5]);self.assertEqual(got['models'][4]['mIoU_20_including_BG'],.5);self.assertIn('## unrelated\npreserved',text)

if __name__=='__main__':unittest.main()
