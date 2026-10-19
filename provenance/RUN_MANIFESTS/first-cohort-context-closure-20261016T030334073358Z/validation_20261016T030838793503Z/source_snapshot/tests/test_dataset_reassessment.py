"""Population bookkeeping tests using original split metadata, not inference."""
from pathlib import Path
from hashlib import sha256
import json
import random
import unittest

STUDY=Path(__file__).resolve().parents[1]
ROOT=STUDY.parent/'datasets/LV-MHP-v2'


class PopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.views={p.stem:json.loads(p.read_text()) for p in (STUDY/'manifests/mhpv2_readable_v1').glob('*.json')}
        cls.official={s:set((ROOT/'list'/f).read_text().split()) for s,f in [('train','train.txt'),('val','val.txt')]}
        cls.leaked=set(json.loads((STUDY/'manifests/LEAKAGE_AUDIT.json').read_text())['validation_ids_with_exact_train_overlap'])
    def test_full_target_is_original_official_validation(self):
        v=self.views['VALIDATION_OFFICIAL_TARGET'];self.assertEqual(set(v['image_ids']),self.official['val'])
        self.assertEqual((v['image_count'],v['native_gt_person_count']),(5000,13260))
    def test_readable_training_excludes_only_authorized_bad_RGB(self):
        v=self.views['TRAIN_READABLE'];self.assertEqual(set(v['image_ids']),self.official['train']-{'1396','18613','24328'})
        self.assertEqual((v['image_count'],v['native_gt_person_count']),(15400,41043))
    def test_readable_validation_denominator_and_exclusion(self):
        v=self.views['VALIDATION_READABLE'];self.assertEqual(set(v['image_ids']),self.official['val']-{'17844'})
        self.assertEqual((v['image_count'],v['native_gt_person_count']),(4999,13257))
        self.assertEqual(v['excluded'][0]['native_gt_person_count'],3)
    def test_controlled_target_keeps_bad_RGB_as_target(self):
        v=self.views['VALIDATION_OVERLAP_CONTROLLED_TARGET']
        self.assertEqual(set(v['image_ids']),self.official['val']-self.leaked)
        self.assertIn('17844',v['image_ids']);self.assertEqual((v['image_count'],v['native_gt_person_count']),(4348,11411))
    def test_controlled_readable_population_has_exact_difference(self):
        v=self.views['VALIDATION_OVERLAP_CONTROLLED_READABLE'];ids=set(v['image_ids'])
        self.assertEqual(ids,self.official['val']-self.leaked-{'17844'})
        self.assertEqual((v['image_count'],v['native_gt_person_count']),(4347,11408))
        self.assertEqual(len(v['excluded']),653)
    def test_hashes_counts_and_no_evaluation_authorization(self):
        for v in self.views.values():
            ids=v['image_ids'];self.assertEqual(len(ids),len(set(ids)))
            self.assertEqual(v['ordered_ids_sha256'],sha256(('\n'.join(ids)+'\n').encode()).hexdigest())
            self.assertEqual(v['native_gt_person_count'],sum(r['native_gt_person_count'] for r in v['included_source_references']))
            self.assertFalse(v['benchmark_authorized']);self.assertFalse(v['original_split_modified'])
    def test_independent_SRS_reproducible_and_train_only(self):
        sample=json.loads((STUDY/'manifests/MHPV2_RANDOM_QUALITY_REVIEW_V1.json').read_text())
        expected=random.Random(sample['seed']).sample(sorted(self.official['train']-{'1396','18613','24328'},key=int),30)
        self.assertEqual(sample['image_ids_in_draw_order'],expected)
        self.assertFalse(sample['prior_anomaly_examples_excluded_from_sampling_frame'])
        self.assertFalse(sample['validation_used'])


if __name__=='__main__':unittest.main()
