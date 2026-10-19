"""Derive metadata under a DRAFT mapping. No predictions or validation inference.

Reuse audited image/person ledgers. Decode only Category/Human grids needed for
new per-person target support; do not repeat RGB, Instance, ZIP or TAR audits.
"""
from pathlib import Path
import sys
import io
import json
import hashlib
import zipfile
from collections import Counter
import numpy as np
from PIL import Image

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))
from src.application_v2.policy import load_config
from src.application_v2.taxonomy import project_gt
from src.application_v2.artifacts import file_hash


def main():
    config = load_config(STUDY / 'configs/application_v2.yaml')
    active = json.loads((STUDY / 'provenance/APPLICATION_V2_IMPLEMENTATION_ACTIVE.json').read_text())
    output = STUDY / active['run_path'] / 'gt_sidecars'
    output.mkdir(exist_ok=False)
    audit = STUDY / 'provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z'
    populations = json.loads((STUDY / config['populations']['manifest']).read_text())
    wanted = {p['population']: set(p['ids']) for p in populations['populations']
              if p['population'] in {'original_source_target', 'overlap_controlled_source_target'}}
    native = json.loads((STUDY / config['cohort']['native_reference']).read_text())
    candidate = json.loads((STUDY / config['cohort']['mapping']).read_text())
    persons = {}
    with (audit / 'PERSON_AUDIT.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            if row['split'] == 'Validation':
                persons.setdefault(row['image_id'], []).append(row)
    summaries = {key: {'images': 0, 'G_native': 0, 'G_loc_structural_draft': 0,
                      'G_sem_native_known_draft': 0, 'G_sem_common_candidate_draft': 0,
                      'native_known_gt_pixels': 0, 'candidate_gt_pixels': 0,
                      'candidate_class_support': Counter()} for key in wanted}
    files = {key: (output / (key + '_persons.jsonl')).open('x') for key in wanted}
    archive = STUDY.parent / 'datasets/CCIHP_icip.zip'
    source_stat = archive.stat()
    try:
        with zipfile.ZipFile(archive) as source, (audit / 'IMAGE_AUDIT.jsonl').open() as stream:
            for line in stream:
                row = json.loads(line)
                if row['split'] != 'Validation' or row['image_id'] not in wanted['original_source_target']:
                    continue
                arrays = {}
                for component in ['Category_ids', 'Human_ids']:
                    reference = next(v for v in row['source_maps'] if v['component'] == component)
                    data = source.read(reference['member'])
                    if hashlib.sha256(data).hexdigest() != reference['sha256']:
                        raise ValueError('Original GT differs from audited hash')
                    with Image.open(io.BytesIO(data)) as image:
                        image.load(); arrays[component] = np.asarray(image).copy()
                category, human = arrays['Category_ids'], arrays['Human_ids']
                native_gt, native_valid = project_gt(category, human, native)
                common_gt, common_valid = project_gt(category, human, candidate)
                if category.shape != (row['wh'][1], row['wh'][0]):
                    raise ValueError('GT original coordinate grid changed')
                rows = []
                # Exact category support per original Human ID. No GT modification.
                joint = np.bincount((human.astype(np.int64) * 256 + category).ravel(), minlength=65536).reshape(256, 256)
                for person in persons[row['image_id']]:
                    pid = person['person_id']; support = human == pid
                    if int(support.sum()) != person['area_pixels']:
                        raise ValueError('Per-person source area differs from audit')
                    common_support = Counter({str(c): int(np.count_nonzero(support & common_valid & (common_gt == c)))
                                              for c in range(1, len(candidate['target_catalog']))})
                    known = int(np.count_nonzero(support & native_valid & (native_gt > 0)))
                    common = sum(common_support.values())
                    rows.append({'person_key': ['CCIHP', 'Validation', row['image_id'], pid],
                                 'bbox_xyxy_half_open': person['bbox_xyxy_half_open'],
                                 'native_human_pixels': person['area_pixels'],
                                 'native_category_support': {str(c): int(v) for c, v in enumerate(joint[pid]) if v},
                                 'G_loc_structural_draft': True,
                                 'G_sem_native_known_draft': known > 0,
                                 'G_sem_common_candidate_draft': common > 0,
                                 'native_known_pixels': known, 'candidate_target_pixels': common,
                                 'candidate_class_support': dict(common_support),
                                 'candidate_labeled_fraction': common / person['area_pixels'],
                                 'source_maps': row['source_maps'], 'status': 'DRAFT_NOT_SCORING_AUTHORIZATION',
                                 'physical_person_identity_certified': False})
                for key, ids in wanted.items():
                    if row['image_id'] not in ids:
                        continue
                    total = summaries[key]; total['images'] += 1
                    for person in rows:
                        files[key].write(json.dumps(person, separators=(',', ':')) + '\n')
                        total['G_native'] += 1; total['G_loc_structural_draft'] += 1
                        total['G_sem_native_known_draft'] += int(person['G_sem_native_known_draft'])
                        total['G_sem_common_candidate_draft'] += int(person['G_sem_common_candidate_draft'])
                        total['native_known_gt_pixels'] += person['native_known_pixels']
                        total['candidate_gt_pixels'] += person['candidate_target_pixels']
                        total['candidate_class_support'].update(person['candidate_class_support'])
    finally:
        for stream in files.values(): stream.close()
    after = archive.stat()
    if (source_stat.st_size, source_stat.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Source archive changed during read-only derivation')
    for p in populations['populations']:
        if p['population'] in wanted:
            actual = summaries[p['population']]
            if (actual['images'], actual['G_native']) != (p['image_count'], p['native_GT_persons']):
                raise ValueError('Source population denominator mismatch')
    manifest = {'schema_version': '2.0', 'status': 'DRAFT_DERIVED_GT_SUPPORT', 'benchmark_authorized': False,
                'mapping_accepted': False, 'population_roles_accepted': False,
                'source_audit_sha256': file_hash(audit / 'IMAGE_AUDIT.jsonl'),
                'population_manifest_sha256': file_hash(STUDY / config['populations']['manifest']),
                'candidate_mapping_sha256': file_hash(STUDY / config['cohort']['mapping']),
                'native_mapping_sha256': file_hash(STUDY / config['cohort']['native_reference']),
                'scope': 'GT metadata only. No model scores or validation inference. Structural G_loc is not human-certified identity.',
                'populations': {key: {**value, 'candidate_class_support': dict(value['candidate_class_support']),
                                     'sidecar': str((output / (key + '_persons.jsonl')).relative_to(STUDY)),
                                     'sidecar_sha256': file_hash(output / (key + '_persons.jsonl'))}
                                for key, value in summaries.items()}}
    (output / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({key: {k: v for k, v in value.items() if k in ['images', 'G_native', 'G_sem_native_known_draft', 'G_sem_common_candidate_draft']}
                      for key, value in summaries.items()}))


if __name__ == '__main__': main()
