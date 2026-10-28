"""Render fixed, original-grid diagnostics from committed packets; never infer."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import html
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

P = Path(__file__).resolve().parents[1]
W = P.parent
sys.path.insert(0, str(P / 'src'))
from cihp_benchmark.data import LABELS, read_sample
from cihp_benchmark.evaluation import compose


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def palette(n=256):
    colors = np.zeros((n, 3), dtype=np.uint8)
    for label in range(n):
        value = label
        for bit in range(8):
            for channel in range(3):
                colors[label, channel] |= ((value >> channel) & 1) << (7 - bit)
            value >>= 3
    return colors


def overlay(rgb, ids, person=False):
    colors = palette()
    foreground = ids > 0
    output = rgb.copy()
    output[foreground] = (0.35 * rgb[foreground] + 0.65 * colors[ids[foreground].astype(np.int64) % 256]).astype(np.uint8)
    image = Image.fromarray(output)
    if person:
        draw = ImageDraw.Draw(image)
        for label in np.unique(ids):
            if not label:
                continue
            y, x = np.where(ids == label)
            j = len(x) // 2
            draw.text((int(x[j]), int(y[j])), str(int(label)), fill='white', stroke_width=1, stroke_fill='black')
    return image


def render_image(out, image_id, model_ids, split='Validation', folders=None):
    truth, _ = read_sample(W / 'datasets/CIHP', split, image_id)
    rgb = truth['rgb']
    h, w = rgb.shape[:2]
    canvas = Image.new('RGB', (8 * w, 2 * (h + 32)), '#202020')
    draw = ImageDraw.Draw(canvas)

    def panel(column, row, image, label):
        x, y = column * w, row * (h + 32)
        draw.text((x + 4, y + 8), label, fill='white')
        if image is not None:
            canvas.paste(image, (x, y + 32))
        else:
            draw.text((x + 8, y + 56), 'NO COMMITTED OUTPUT / N/A', fill='white')

    panel(0, 0, Image.fromarray(rgb), 'Original RGB')
    panel(0, 1, Image.fromarray(rgb), 'Original RGB (same grid)')
    panel(1, 0, overlay(rgb, truth['Category_ids']), 'Native CIHP category GT')
    panel(1, 1, overlay(rgb, truth['Human_ids'], person=True), 'Native CIHP Human_ids GT')
    identities = []
    for column, mid in enumerate(model_ids, 2):
        folder = folders[mid] if folders else out / 'validation' / mid
        packet = folder / 'packets' / image_id
        meta_path, array_path = packet / 'packet.json', packet / 'prediction.npz'
        record = {'model_id': mid, 'status': 'NOT_AVAILABLE', 'image_id': image_id}
        # The terminal frame ledger, not the existence of a partial NPZ, commits an output.
        committed = False
        if (folder / 'FRAMES.jsonl').exists():
            with (folder / 'FRAMES.jsonl').open() as stream:
                committed = any((r := json.loads(line))['image_id'] == image_id and r['status'] == 'COMPLETE' for line in stream)
        if committed and meta_path.exists() and array_path.exists():
            meta = json.loads(meta_path.read_text())
            if sha(array_path) != meta['packet_sha256']:
                raise ValueError('Diagnostic packet digest mismatch: ' + mid + '/' + image_id)
            with np.load(array_path, allow_pickle=False) as arrays:
                planes = arrays['person_semantic_masks']
                extents = arrays['person_extents']
                scores = arrays['person_scores']
                sem = compose(planes, scores, (h, w))
                owners = np.zeros((h, w), dtype=np.int32)
                for j in sorted(range(len(scores)), key=lambda i: (float(scores[i]), -i)):
                    owners[extents[j]] = j + 1
            panel(column, 0, overlay(rgb, sem), mid + ' | application labels')
            panel(column, 1, overlay(rgb, owners, person=True), mid + ' | final person extents')
            record.update(status='COMMITTED', packet_sha256=meta['packet_sha256'], metadata_sha256=sha(meta_path), final_person_count=len(scores))
        else:
            panel(column, 0, None, mid + ' | application labels')
            panel(column, 1, None, mid + ' | final person extents')
        identities.append(record)
    return canvas, identities


def render_batch(out):
    out = Path(out)
    if json.loads((out / 'LAUNCH.json').read_text())['status'] == 'RUNNING':
        raise RuntimeError('Comparative VAL visualization waits for batch terminal')
    config = json.loads((out / 'FROZEN_CONFIG.json').read_text())
    sample_path = out / 'FROZEN_DIAGNOSTIC_SAMPLE.json'
    if not sample_path.exists():
        raise ValueError('Missing pre-score diagnostic sample snapshot')
    sample = json.loads(sample_path.read_text())
    destination = out / 'QUALITATIVE'
    destination.mkdir(exist_ok=False)
    records = []
    for image_id in sample['ids']:
        canvas, packet_records = render_image(out, image_id, config['execution_models'])
        path = destination / (image_id + '.png')
        canvas.save(path)
        records.append({'image_id': image_id, 'image': path.name, 'width': canvas.width, 'height': canvas.height, 'sha256': sha(path), 'packets': packet_records})
    legend = Image.new('RGB', (640, 28 * len(LABELS)), 'white')
    draw = ImageDraw.Draw(legend)
    colors = palette()
    for i, label in enumerate(LABELS):
        draw.rectangle((4, i * 28 + 2, 28, i * 28 + 24), fill=tuple(map(int, colors[i])))
        draw.text((38, i * 28 + 8), f'{i}: {label}', fill='black')
    legend.save(destination / 'LEGEND.png')
    links = ''.join(f'<li><a href="{html.escape(r["image"])}">{html.escape(r["image_id"])}</a></li>' for r in records)
    (destination / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>CIHP fixed diagnostic sample</title><h1>Fixed 16-image comparison</h1><p>Original grid in each panel. Top: RGB / native category GT / six application semantic outputs. Bottom: RGB / Human_ids GT / six final person extents. IDs are local to each panel, not cross-model identity matches. Missing committed packets remain N/A. These are annotation-relative illustrations, not an independent quality-review sample or a selection rule.</p><a href="LEGEND.png">Native CIHP 20-label legend</a><ul>' + links + '</ul>')
    manifest = {'run_id': config['run_id'], 'created_utc': datetime.now(timezone.utc).isoformat(), 'sampling': sample, 'sample_sha256': sha(sample_path), 'selection_before_VAL_scores': True, 'new_inference': False, 'source_GT_modified': False, 'mask_resampling': 'NONE: original grid for every diagnostic panel; categorical evaluation inputs unchanged', 'display_overlap': 'highest person score; same stable index tie ordering as composite; individual planes remain in NPZ', 'interpretation': 'Local person IDs are not predicted-to-GT matches. Inspect missed, merged, semantic-empty and cross-person cases; do not infer completeness of physical-person annotation.', 'source_sha256': sha(__file__), 'records': records}
    (destination / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return {'sample_count': len(records), 'external_manifest': str((destination / 'MANIFEST.json').relative_to(W)), 'manifest_sha256': sha(destination / 'MANIFEST.json'), 'external_index': str((destination / 'index.html').relative_to(W)), 'all_panels_original_grid': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-root', required=True)
    args = parser.parse_args()
    print(json.dumps(render_batch(Path(args.run_root))))
