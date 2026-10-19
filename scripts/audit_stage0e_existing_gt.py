"""Bounded audit of the user-identified TAR; no inference or GT ownership guesses.

Use verified TAR member offsets for small source-parity checks. Reuse, rather
than repeat, the previous complete TAR/bitmap inventory. Missing CCIHP is an
explicit stop gate for all CCIHP-dependent checks.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import io
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFile

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
sys.path.insert(0, str(ROOT))
from src.data.cihp_datasetninja import reconstruct_semantic

ImageFile.LOAD_TRUNCATED_IMAGES = False
active = json.loads((ROOT / 'provenance/CCIHP_STAGE0E_ACTIVE_RUN.json').read_text())
RUN = ROOT / active['run_path']
prior = json.loads((ROOT / 'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json').read_text())
archive = WORKSPACE / prior['archive_workspace_relative']
cci_zip = WORKSPACE / 'datasets/CCIHP_icip.zip'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(name, data):
    path = RUN / name
    if path.exists():
        raise RuntimeError(f'Refusing to overwrite evidence: {path}')
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


search = []
visited = 0
for base, dirs, files in os.walk(WORKSPACE, followlinks=False):
    dirs[:] = [d for d in dirs if d not in {'.git', '.venv', '.venvs', 'parser_envs', 'node_modules',
                                           '__pycache__', 'outputs', 'predictions'}
               and 'ppss' not in d.lower() and not d.lower().startswith('pedestrian_parsing_dataset')]
    visited += 1
    for name in dirs + files:
        if 'ccihp' in name.lower():
            path = Path(base) / name
            if ROOT in path.parents:
                continue  # Audit reports/source snapshots are not dataset copies.
            search.append({'workspace_relative': str(path.relative_to(WORKSPACE)), 'is_directory': path.is_dir()})
save('DISCOVERY.json', {'root': '.', 'expected_ccihp_archive_exists': cci_zip.is_file(),
                        'ccihp_data_candidates': search, 'directories_visited': visited,
                        'excluded_roots': 'environments, git, generated outputs/predictions, PPSS directories',
                        'user_identified_archive': prior['archive_workspace_relative'],
                        'actual_target_exists': archive.is_file()})
if cci_zip.exists() or search:
    raise RuntimeError('CCIHP appeared: stop missing-input branch and inspect it before drawing conclusions')
assert archive.is_file() and archive.stat().st_size == prior['archive_bytes']
stat_before = archive.stat()
assert sha(ROOT / prior['member_inventory']) == prior['member_inventory_sha256']
assert sha(ROOT / prior['annotation_summary']) == prior['annotation_summary_sha256']
inventory = {}
with (ROOT / prior['member_inventory']).open() as stream:
    for line in stream:
        item = json.loads(line)
        inventory[item['path']] = item
assert len(inventory) == prior['counts']['regular_files']
native_root = ROOT / 'provenance/RUN_MANIFESTS/cihp-archive-preflight-20261008T102552Z/sources/reference_fixtures'
native_sources = json.loads((native_root / 'SOURCE_MANIFEST.json').read_text())
assert all(sha(ROOT / row['snapshot']) == row['sha256'] for row in native_sources.values())
reads = []


def read_member(name):
    row = inventory[name]
    with archive.open('rb') as f:
        f.seek(row['data_offset'])
        data = f.read(row['bytes'])
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
    reads.append({'member': name, 'bytes': len(data), 'sha256': row['sha256'], 'matches_prior_member_hash': True})
    return data


readme = read_member('README.md').decode()
license_text = read_member('LICENSE.md').decode()
meta = json.loads(read_member('meta.json'))
assert 'CIHP: Crowd Instance-level Human Parsing' in readme
assert 'CIHP: Crowd Instance-level Human Parsing' in license_text
classes = sorted(row['title'] for row in meta['classes'])
assert len(classes) == 19 and 'dress' in classes and 'sunglasses' in classes and 'mask' not in classes
identity = {'archive': prior['archive_workspace_relative'], 'publisher_metadata_identity': 'CIHP_CROWD_INSTANCE_LEVEL_HUMAN_PARSING',
            'container': 'PLAIN_TAR_DATASETNINJA_SUPERVISELY_CONVERSION',
            'is_verified_ccihp_release': False, 'readme': readme, 'provider_license_text': license_text,
            'foreground_class_count': len(classes), 'class_titles': classes, 'meta_person_tags': meta['tags'],
            'ccihp_expected_component_members': {folder: [p for p in inventory if folder.lower() in p.lower()]
                                                for folder in ['Category_ids', 'Human_ids', 'Instance_ids', 'Color_ids', 'Pattern_ids', 'Size_ids']}}
save('ARCHIVE_IDENTITY.json', identity)
cases = []
fields = set()
object_fields = set()
outputs = ROOT / 'outputs/visualizations' / active['run_id']
outputs.mkdir(parents=True, exist_ok=False)
palette = np.array([[0,0,0],[190,75,35],[125,60,160],[200,160,40],[45,140,160],[210,60,100],
                    [75,130,220],[160,90,40],[70,170,130],[180,45,70],[230,160,100],[100,140,60],
                    [210,100,175],[235,190,160],[65,125,195],[155,80,200],[40,165,200],[195,140,50],
                    [125,195,75],[190,75,130]], dtype=np.uint8)
for image_id in ['0002190', '0005008', '0012008', '0026375', '0032190']:
    image_bytes = read_member(f'training/img/{image_id}.jpg')
    annotation = json.loads(read_member(f'training/ann/{image_id}.jpg.json'))
    with Image.open(io.BytesIO(image_bytes)) as image:
        image.load()
        rgb = np.asarray(image.convert('RGB'))
    fields.update(annotation)
    for obj in annotation['objects']:
        object_fields.update(obj)
        assert not obj.get('tags')
    assert not annotation.get('tags')
    semantic, diagnostics = reconstruct_semantic(annotation)
    with Image.open(native_root / f'labels_{image_id}.png') as label:
        label.load()
        reference = np.asarray(label)
    with Image.open(native_root / f'images_{image_id}.jpg') as image:
        image.load()
        native_rgb = np.asarray(image.convert('RGB'))
    assert rgb.shape[:2] == semantic.shape == reference.shape
    assert np.array_equal(rgb, native_rgb)
    assert np.array_equal(semantic, reference)
    row = {'image_id': image_id, 'split': 'training', 'source_RGB_sha256': hashlib.sha256(image_bytes).hexdigest(),
           'wh': [rgb.shape[1], rgb.shape[0]], 'strict_full_RGB_load': 'PASS', 'bitmap_decode': 'PASS',
           'native_demo_RGB_bytes_match': image_bytes == (native_root / f'images_{image_id}.jpg').read_bytes(),
           'native_demo_RGB_pixels_match': True, 'semantic_pixel_differences': int(np.count_nonzero(semantic != reference)),
           'foreground_boundary_pixel_differences': int(np.count_nonzero((semantic > 0) != (reference > 0))),
           'part_objects': len(annotation['objects']), 'person_count': None, 'human_GT': 'NOT_AVAILABLE',
           'CCIHP_comparison': 'NOT_TESTED_MISSING_CCIHP_ARCHIVE', 'diagnostics': diagnostics,
           'reference_scope': 'Official PGN repository semantic demo only; no native Human_ids reference'}
    if image_id in ['0002190', '0005008', '0012008']:
        panels = []
        for title, mask in [('Original RGB', None), ('Official PGN semantic GT', reference), ('DatasetNinja semantic GT', semantic)]:
            array = rgb if mask is None else np.where((mask > 0)[...,None],
                                                      (0.55*rgb + 0.45*palette[mask]).astype(np.uint8), rgb)
            picture = Image.fromarray(array)
            width = 400
            picture = picture.resize((width, round(picture.height * width / picture.width)), Image.Resampling.LANCZOS)
            panel = Image.new('RGB', (width, picture.height + 34), 'white')
            panel.paste(picture, (0, 34))
            ImageDraw.Draw(panel).text((10, 10), title, fill='black')
            panels.append(panel)
        height = max(p.height for p in panels)
        canvas = Image.new('RGB', (1200, height + 42), 'white')
        for i, panel in enumerate(panels):
            canvas.paste(panel, (i*400, 0))
        ImageDraw.Draw(canvas).text((10, height+10), f'CIHP {image_id} | semantic parity only | Human_ids unavailable | CCIHP not supplied', fill='black')
        dest = outputs / f'cihp_{image_id}_semantic_reference.png'
        canvas.save(dest)
        row['diagnostic_image'] = str(dest.relative_to(ROOT))
        row['diagnostic_sha256'] = sha(dest)
        row['display_resampling'] = 'LANCZOS on completed RGB visualization only; original categorical arrays unresized for all checks'
    cases.append(row)
save('CIHP_BOUNDED_REFERENCE_RECHECK.json', {'actual_cases': cases, 'member_reads': reads,
                                          'member_bytes_read': sum(r['bytes'] for r in reads),
                                          'annotation_fields': sorted(fields), 'object_fields': sorted(object_fields),
                                          'full_dataset_rerun': False, 'CCIHP_checks_run': False,
                                          'GT_ownership_reconstruction': 'NOT_ATTEMPTED_NO_NATIVE_HUMAN_INFORMATION'})
stat_after = archive.stat()
save('EXECUTION.json', {'run_id': active['run_id'], 'end_utc': datetime.now(timezone.utc).isoformat(),
                       'target': prior['archive_workspace_relative'], 'target_identity': 'CIHP_DATASETNINJA_NOT_CCIHP',
                       'file_size': stat_after.st_size, 'size_mtime_inode_unchanged':
                       (stat_before.st_size, stat_before.st_mtime_ns, stat_before.st_ino) ==
                       (stat_after.st_size, stat_after.st_mtime_ns, stat_after.st_ino),
                       'new_archive_whole_SHA256': 'NOT_REHASHED_REUSED_PRIOR_VERIFIED_INVENTORY',
                       'new_CCIHP_inference_or_attribute_evaluation': False, 'model_inference': False,
                       'new_dataset_download': False, 'decision': 'C_NATIVE_CIHP_REQUIRED_FOR_AVAILABLE_ASSETS'})
print(json.dumps({'actual_target': prior['archive_workspace_relative'], 'identity': 'CIHP_DATASETNINJA_NOT_CCIHP',
                  'native_semantic_demo_cases': len(cases), 'semantic_pixel_differences': sum(x['semantic_pixel_differences'] for x in cases),
                  'human_GT': 'MISSING', 'ccihp_archive': 'MISSING', 'model_inference': 0}, ensure_ascii=False))
