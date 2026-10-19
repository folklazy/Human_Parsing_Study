"""Reproduce native MHP metadata from an audited index, without decoding GT."""
from pathlib import Path
import argparse
import json
import sys

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))
from src.application_v2.artifacts import file_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, type=Path, help='Fresh directory inside the study')
    args = parser.parse_args(); out = args.out.resolve()
    if not out.is_relative_to(STUDY) or out.exists():
        raise ValueError('Fresh owning-study directory required; existing evidence is immutable')
    manifest = json.loads((STUDY / 'manifests/DATASET_MANIFEST.json').read_text())
    index = STUDY / manifest['canonical_gt_index']
    if file_hash(index) != manifest['canonical_gt_index_sha256']:
        raise ValueError('Audited GT index changed')
    names = ['VALIDATION_READABLE', 'VALIDATION_OVERLAP_CONTROLLED_READABLE']
    populations = {name: json.loads((STUDY / 'manifests/mhpv2_readable_v1' / (name + '.json')).read_text())
                   for name in names}
    wanted = {name: set(p['image_ids']) for name, p in populations.items()}
    out.mkdir(parents=True, exist_ok=False)
    files = {name: (out / (name + '.jsonl')).open('x') for name in names}
    counts = {name: {'images': 0, 'G_native': 0, 'G_loc_structural_draft': 0,
                     'G_sem_native_known_draft': 0} for name in names}
    try:
        with index.open() as stream:
            for line in stream:
                image = json.loads(line)
                if image['split'] != 'val': continue
                for name, ids in wanted.items():
                    if image['image_id'] not in ids: continue
                    counts[name]['images'] += 1
                    for person in image['persons']:
                        eligible = person['foreground_area'] > 0
                        semantic = eligible and any(1 <= c <= 58 for c in person['native_ids'])
                        row = {'person_key': ['MHP-v2', 'val', image['image_id'], person['canonical_person_id']],
                               'native_person_file_id': person['person_file_id'],
                               'source_annotation': person['annotation_path'], 'source_sha256': person['source_sha256'],
                               'semantic_array_sha256': person['semantic_array_sha256'], 'original_wh': image['original_wh'],
                               'native_ids': person['native_ids'], 'foreground_area': person['foreground_area'],
                               'bbox_xyxy_half_open': person['foreground_bbox_xyxy_half_open'],
                               'G_loc_structural_draft': eligible, 'G_sem_native_known_draft': semantic,
                               'common_taxonomy_eligibility': 'NOT_ESTABLISHED', 'overlapping_planes_preserved': True,
                               'status': 'DRAFT_METADATA_NOT_BENCHMARK'}
                        files[name].write(json.dumps(row, separators=(',', ':')) + '\n')
                        counts[name]['G_native'] += 1
                        counts[name]['G_loc_structural_draft'] += int(eligible)
                        counts[name]['G_sem_native_known_draft'] += int(semantic)
    finally:
        for stream in files.values(): stream.close()
    for name, values in counts.items():
        expected = populations[name]
        if (values['images'], values['G_native']) != (expected['image_count'], expected['native_gt_person_count']):
            raise ValueError('Population denominator differs from approved readable view')
        values.update(sidecar=str((out / (name + '.jsonl')).relative_to(STUDY)),
                      sidecar_sha256=file_hash(out / (name + '.jsonl')))
    result = {'status': 'DRAFT_NATIVE_MHP_GT_METADATA', 'source_index_sha256': file_hash(index),
              'benchmark_authorized': False, 'populations': counts,
              'scope': 'Existing verified index only; no original MHP images or masks redecoded; no flattening or common-taxonomy score.'}
    (out / 'MANIFEST.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({name: value['sidecar_sha256'] for name, value in counts.items()}))


if __name__ == '__main__': main()
