"""Three predeclared TRAIN GT reconstructions; no parser/detector or metric scoring."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import sys
import zipfile
import numpy as np
from PIL import Image

S = Path(__file__).resolve().parents[1]
W = S.parent
sys.path.insert(0, str(S))
from src.application_v2.policy import load_config, digest
from src.application_v2.taxonomy import project_gt
from src.application_v2.evaluation import person_truth
from src.application_v2.artifacts import file_hash


def pixels_sha(array):
    return digest(dict(shape=list(array.shape), dtype=str(array.dtype), bytes_sha256=hashlib.sha256(array.tobytes()).hexdigest()))


def main():
    cfg = load_config(S / 'configs/application_v2_first_cohort_v7.yaml')
    run = S / json.loads((S / 'provenance/FIRST_COHORT_POLICY_ACCEPTANCE_ACTIVE.json').read_text())['run']
    out = run / 'GT_TRAIN_RECONSTRUCTION'
    out.mkdir()
    pilot = W / 'Human_Parsing_CCIHP_10_Image_Pilot'
    samples = json.loads((pilot / 'configs/TEN_IMAGE_MANIFEST.json').read_text())['images']
    ids = cfg['bounded_train']['input_ids']
    assert len(ids) == 3
    samples = [next(row for row in samples if row['image_id'] == image) for image in ids]
    assert all(row['split'] == 'Training' for row in samples)
    mapping = json.loads((S / cfg['cohort']['mapping']).read_text())
    projection_sha = digest({key: mapping[key] for key in ['target_catalog', 'gt_mapping']})
    assert projection_sha == cfg['first_cohort']['protocol']['mapping']['GT_projection_sha256']
    domain = cfg['first_cohort']['protocol']['domain']
    records = []
    with zipfile.ZipFile(W / 'datasets/CCIHP_icip.zip') as archive:
        for sample in samples:
            assert file_hash(pilot / sample['input']) == sample['input_sha256']
            with np.load(pilot / sample['input'], allow_pickle=False) as cached:
                rgb = cached['rgb'].copy()
                cached_maps = {key: cached[key].copy() for key in ['category', 'human', 'instance']}
            maps = {}
            for source in sample['source_gt']:
                data = archive.read(source['member'])  # ZIP validates member CRC; hash checks source identity.
                assert hashlib.sha256(data).hexdigest() == source['sha256']
                with Image.open(BytesIO(data)) as image:
                    image.load(); array = np.array(image)
                key = {'Category_ids': 'category', 'Human_ids': 'human', 'Instance_ids': 'instance'}[source['component']]
                assert np.array_equal(array, cached_maps[key]) and array.dtype == cached_maps[key].dtype
                assert array.shape == rgb.shape[:2] == (sample['wh'][1], sample['wh'][0])
                maps[key] = array
            target, global_valid = project_gt(maps['category'], maps['human'], mapping)
            persons = []
            semantics = []
            valid_masks = []
            for pid in sorted(int(v) for v in np.unique(maps['human']) if v > 0):
                truth, valid = person_truth(target, maps['human'], global_valid, pid)
                y, x = np.nonzero(maps['human'] == pid)
                sem_eligible = bool(((truth > 0) & valid).any())
                persons.append(dict(person_id=pid, bbox=[int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1],
                                    G_loc=True, G_sem=sem_eligible))
                semantics.append(truth); valid_masks.append(valid)
            recipe = dict(image_id=sample['image_id'], source_maps=sample['source_gt'], original_wh=sample['wh'],
                          GT_projection_sha256=projection_sha, domain_policy_sha256=domain['policy_sha256'])
            artifact = out / (sample['image_id'] + '.npz')
            arrays = dict(**maps, target=target, global_valid=global_valid,
                          person_semantic=np.stack(semantics), person_valid=np.stack(valid_masks))
            np.savez_compressed(artifact, **arrays)
            with np.load(artifact, allow_pickle=False) as roundtrip:
                assert all(np.array_equal(roundtrip[key], value) and roundtrip[key].dtype == value.dtype for key, value in arrays.items())
            records.append(dict(image_id=sample['image_id'], split='Training', original_wh=sample['wh'],
                status='GT_RECONSTRUCTION_VERIFIED_PARSER_CHANNEL_BINDING_BLOCKED', source_gt=sample['source_gt'],
                RGB_source='PRIOR_HASH_VERIFIED_RGB_INPUT_NO_NEW_ARCHIVE_RGB_DECODE', input_sha256=sample['input_sha256'],
                G_loc=len(persons), G_sem=sum(p['G_sem'] for p in persons), persons=persons,
                image_binding=dict(image_id=sample['image_id'], G_loc=len(persons), G_sem=sum(p['G_sem'] for p in persons),
                                   GT_domain_recipe_sha256=digest(recipe)),
                global_valid_pixels=int(global_valid.sum()), global_valid_pixels_sha256=pixels_sha(global_valid),
                artifact=str(artifact.relative_to(S)), artifact_sha256=file_hash(artifact),
                per_person_valid_pixels_sha256=[pixels_sha(v) for v in valid_masks],
                native_source_roundtrip='EXACT', original_grid_transform='IDENTITY_NO_RESAMPLING',
                target_display_names=cfg['cohort']['target_display_names'], accepted_parser_context=False))
    value = dict(status='PASS_GT_TRAIN_ONLY_PARSER_CONTEXTS_BLOCKED', scope='Three fixed TRAIN IDs; no validation reconstruction or model inference',
        images=records, total_images=len(records), total_G_loc=sum(r['G_loc'] for r in records),
        total_G_sem=sum(r['G_sem'] for r in records), model_contexts_accepted=0,
        channel_order_gate='INDIRECT_ONLY', quality_scores_computed=False, full_benchmark=False)
    (out / 'MANIFEST.json').write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps({key: value[key] for key in ['status', 'total_images', 'total_G_loc', 'total_G_sem', 'model_contexts_accepted']}))


if __name__ == '__main__':
    main()
