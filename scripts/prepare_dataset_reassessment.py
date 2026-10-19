"""Build authorized immutable-source readable views and TRAIN quality diagnostics.

No benchmark/inference. Reuses the exhaustive prior content inventory, verifies
its hash, and directly rechecks only the fixed diagnostic sample and exclusions.
Outputs refuse overwrite; reruns require a new version/run.
"""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import csv
import json
import random
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.io import loadmat

STUDY = Path(__file__).resolve().parents[1]
WORKSPACE = STUDY.parent
sys.path.insert(0, str(STUDY))
from src.data.mhpv2 import decode_native


def digest(path):
    with path.open('rb') as stream:
        h = sha256()
        for block in iter(lambda: stream.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def publish(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def main():
    active = json.loads((STUDY/'provenance/DATASET_REASSESSMENT_ACTIVE_RUN.json').read_text())
    manifest_path = STUDY/'manifests/DATASET_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    root = WORKSPACE/manifest['root_workspace_relative']
    index = STUDY/manifest['canonical_gt_index']
    assert digest(index) == '81358626da696ae2ec552f195fcc318df0d5c22011fe120d97cc038095cf2f54'
    rows = [json.loads(line) for line in index.open()]
    by_split = {split: {r['image_id']: r for r in rows if r['split'] == split}
                for split in ['train', 'val', 'test']}
    assert [len(by_split[s]) for s in ['train', 'val', 'test']] == [15403, 5000, 5000]
    leakage_path = STUDY/'manifests/LEAKAGE_AUDIT.json'
    leaked = set(json.loads(leakage_path.read_text())['validation_ids_with_exact_train_overlap'])
    train_hashes = {r['decoded_rgb_sha256'] for r in by_split['train'].values() if r.get('decoded_rgb_sha256')}
    independently_leaked = {r['image_id'] for r in by_split['val'].values()
                            if r.get('decoded_rgb_sha256') and r['decoded_rgb_sha256'] in train_hashes}
    assert leaked == independently_leaked and len(leaked) == 652
    failed = {'train': {'1396', '18613', '24328'}, 'val': {'17844'}}
    for split in failed:
        assert {i for i, r in by_split[split].items() if not r.get('decoded_rgb_sha256')} == failed[split]
        for i in failed[split]:
            assert digest(root/by_split[split][i]['image_path']) == by_split[split][i]['image_sha256']
    sources = {str(p.relative_to(STUDY)): digest(p) for p in [manifest_path, index, leakage_path,
               STUDY/'provenance/MHPV2_NEW_ZIP_RGB_VERIFICATION.json']}
    specs = [
        ('TRAIN_READABLE', 'train', set(by_split['train'])-failed['train'], 15400, 41043),
        ('VALIDATION_OFFICIAL_TARGET', 'val', set(by_split['val']), 5000, 13260),
        ('VALIDATION_READABLE', 'val', set(by_split['val'])-failed['val'], 4999, 13257),
        ('VALIDATION_OVERLAP_CONTROLLED_TARGET', 'val', set(by_split['val'])-leaked, 4348, 11411),
        ('VALIDATION_OVERLAP_CONTROLLED_READABLE', 'val', set(by_split['val'])-leaked-failed['val'], 4347, 11408),
    ]
    summaries = []
    for name, split, ids, expected_images, expected_people in specs:
        ids = sorted(ids, key=int)
        selected = [by_split[split][i] for i in ids]
        person_count = sum(len(r['persons']) for r in selected)
        assert (len(ids), person_count) == (expected_images, expected_people)
        excluded = []
        for i in sorted(set(by_split[split])-set(ids), key=int):
            r = by_split[split][i]
            excluded.append({'image_id': i, 'image_sha256': r['image_sha256'],
                             'native_gt_person_count': len(r['persons']),
                             'reasons': [reason for reason, condition in
                                [('STRICT_RGB_DECODE_FAILURE', i in failed[split]),
                                 ('EXACT_DECODED_TRAIN_OVERLAP', split == 'val' and i in leaked)] if condition]})
        out = STUDY/f'manifests/mhpv2_readable_v1/{name}.json'
        obj = {'schema_version': '1.0', 'policy_version': 'mhpv2-readable-v1',
               'run_id': active['run_id'], 'population': name, 'split': split,
               'view_preparation_authorized': True, 'benchmark_authorized': False,
               'source_dataset_modified': False, 'original_split_modified': False,
               'status': 'TARGET_ONLY_CONTAINS_UNREADABLE_RGB' if 'TARGET' in name else 'READABLE_INPUTS_WITH_QUALITY_WARNINGS',
               'image_count': len(ids), 'native_gt_person_count': person_count,
               'image_ids': ids, 'ordered_ids_sha256': sha256(('\n'.join(ids)+'\n').encode()).hexdigest(),
               'included_source_references': [{'image_id': r['image_id'], 'image_sha256': r['image_sha256'],
                                              'native_gt_person_count': len(r['persons'])} for r in selected],
               'excluded': excluded, 'source_artifacts': sources,
               'gt_reference': 'Each ID resolves to independent native planes and SHA256 in canonical_gt_index',
               'score_requirement': 'Report exact view/denominators. Readable scores are not unqualified full official scores.',
               'limitations': ['Exact train-overlap removal does not remove within-validation repetition, near duplicates, or unknown checkpoint exposure.',
                              'RGB decoding success does not establish semantic annotation correctness.']}
        publish(out, obj)
        summaries.append({'population': name, 'manifest': str(out.relative_to(STUDY)),
                          'sha256': digest(out), 'images': len(ids), 'persons': person_count,
                          'ordered_ids_sha256': obj['ordered_ids_sha256']})
    # Freeze a simple random image sample before reading RGB/GT pixels.
    population = sorted(set(by_split['train'])-failed['train'], key=int)
    seed = 20261008
    ids = random.Random(seed).sample(population, 30)
    sample_path = STUDY/'manifests/MHPV2_RANDOM_QUALITY_REVIEW_V1.json'
    sample = {'schema_version': '1.0', 'seed': seed, 'rng': 'Python random.Random.sample over numeric-sorted IDs',
              'python_version': sys.version.split()[0], 'sampling': 'SIMPLE_RANDOM_WITHOUT_REPLACEMENT',
              'sampling_frame': summaries[0], 'image_inclusion_probability': 30/15400,
              'image_ids_in_draw_order': ids, 'sample_images': 30, 'selected_before_visual_review': True,
              'prior_anomaly_examples_excluded_from_sampling_frame': False,
              'model_inference': False, 'validation_used': False,
              'review_status': 'HUMAN_REVIEW_PENDING_NO_PREVALENCE_ESTIMATE'}
    publish(sample_path, sample)
    palette = np.rint(loadmat(root/'LV-MHP-v2_colormap.mat')['MHP_colormap']*255).astype(np.uint8)
    output = STUDY/'outputs/visualizations'/active['run_id']/'mhpv2_random_quality'
    output.mkdir(parents=True, exist_ok=False)
    evidence = []; thumbs = []
    for order, i in enumerate(ids, 1):
        r = by_split['train'][i]
        rgb_path = root/r['image_path']
        assert digest(rgb_path) == r['image_sha256']
        with Image.open(rgb_path) as image:
            image.load(); rgb = image.convert('RGB')
        assert list(rgb.size) == r['original_wh']
        panels = [('Original RGB', rgb)]
        hashes = []
        for p in r['persons']:
            path = root/p['annotation_path']; assert digest(path) == p['source_sha256']
            labels = decode_native(path)
            assert labels.shape == (rgb.height, rgb.width) and labels.max() <= 58
            assert sha256(labels.tobytes()).hexdigest() == p['semantic_array_sha256']
            foreground = labels > 0
            colored = palette[labels]
            overlay = np.array(rgb)
            overlay[foreground] = np.rint(.45*overlay[foreground]+.55*colored[foreground]).astype(np.uint8)
            panels.append((f"GT parsing ID {p['person_file_id']}; area={p['foreground_area']}", Image.fromarray(overlay)))
            panels.append((f"Native labels ID {p['person_file_id']} (0=black)", Image.fromarray(colored)))
            hashes.append({'annotation_path': p['annotation_path'], 'sha256': p['source_sha256']})
        cell_w, cell_h = 380, 330
        canvas = Image.new('RGB', (cell_w*3, 40+((len(panels)+2)//3)*cell_h), 'white')
        draw = ImageDraw.Draw(canvas)
        draw.text((5, 5), f"SRS {order:02d}; train/{i}; N={len(r['persons'])}; {rgb.width}x{rgb.height}; native independent planes", fill='black')
        for n, (title, panel) in enumerate(panels):
            x, y = (n%3)*cell_w, 40+(n//3)*cell_h
            draw.text((x+5,y+5),title,fill='black')
            factor = min((cell_w-10)/panel.width,(cell_h-30)/panel.height)
            wh = (max(1,int(panel.width*factor)),max(1,int(panel.height*factor)))
            # Both GT labels and overlays use nearest resampling in display.
            resize = Image.Resampling.BILINEAR if n==0 else Image.Resampling.NEAREST
            canvas.paste(panel.resize(wh,resize),(x+(cell_w-wh[0])//2,y+25))
        path = output/f'{order:02d}_train_{i}.png'; canvas.save(path)
        evidence.append({'image_id': i, 'image_path': r['image_path'], 'image_sha256': r['image_sha256'],
                         'original_wh': r['original_wh'], 'native_gt_person_count': len(r['persons']),
                         'source_annotations': hashes, 'diagnostic': str(path.relative_to(STUDY)),
                         'diagnostic_sha256': digest(path), 'alignment_grid_validation': 'PASS',
                         'native_array_fidelity': 'PASS', 'semantic_ownership_review': 'PENDING'})
        thumb = canvas.copy(); thumb.thumbnail((570,650),Image.Resampling.NEAREST);thumbs.append(thumb)
    contacts = []
    for page in range(5):
        sheet = Image.new('RGB',(1140,1950),'white')
        for n,thumb in enumerate(thumbs[page*6:page*6+6]):
            sheet.paste(thumb,((n%2)*570,(n//2)*650))
        path = output/f'contact_{page+1:02d}.png';sheet.save(path)
        contacts.append({'path':str(path.relative_to(STUDY)),'sha256':digest(path)})
    checklist = STUDY/'reports/MHPV2_RANDOM_QUALITY_REVIEW_V1.csv'
    with checklist.open('x',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=['image_id','split','native_gt_person_count','diagnostic','reviewer',
            'physical_person_ownership','missing_visible_person','boundary_alignment','class_semantics','severity',
            'status','notes'])
        writer.writeheader()
        for e in evidence:
            writer.writerow({'image_id':e['image_id'],'split':'train','native_gt_person_count':e['native_gt_person_count'],
                             'diagnostic':e['diagnostic'],'status':'PENDING'})
    publish(STUDY/'provenance/MHPV2_READABLE_POLICY_V1.json',{
        'status':'PREPARATION_PASS_WITH_WARNINGS','populations':summaries,'sources':sources,
        'approved_by':'Explicit user instruction: versioned non-destructive readable-subset policy',
        'exclusions_are_views_only':True,'dataset_modified':False,'source_files_rehashed_exhaustively':False,
        'prior_exhaustive_hash_inventory_reused':True,'random_sample_manifest':str(sample_path.relative_to(STUDY)),
        'random_sample':evidence,'contact_sheets':contacts,'class_palette_source_sha256':digest(root/'LV-MHP-v2_colormap.mat'),
        'human_review':'PENDING','population_error_prevalence':'NOT_ESTIMATED',
        'numerical_alignment_is_not_physical_ownership_validation':True,
        'tool_sha256':digest(Path(__file__)),'model_inference':False})
    print('[REASSESSMENT] five population manifests validated; 30 TRAIN GT diagnostics generated; human review pending')


if __name__ == '__main__':
    main()
