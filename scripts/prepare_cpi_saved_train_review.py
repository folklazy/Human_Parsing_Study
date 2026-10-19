"""One bounded saved-TRAIN channel/geometry review; no inference or scores."""
from pathlib import Path
import argparse
import colorsys
import json
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

S = Path(__file__).resolve().parents[1]
W = S.parent
sys.path.insert(0, str(S))
from src.application_v2.policy import load_config
from src.application_v2.artifacts import file_hash


def read_arrays(path, expected):
    if file_hash(path) != expected:
        raise ValueError('Saved input changed: ' + str(path))
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key].copy() for key in data.files}


def panel(rgb, title):
    h, w = rgb.shape[:2]
    image = Image.new('RGB', (w, h + 185), 'white')
    image.paste(Image.fromarray(rgb), (0, 45))
    ImageDraw.Draw(image).multiline_text((6, 3), title, fill='black', font=ImageFont.truetype('DejaVuSans.ttf', 13))
    return image


def overlay(rgb, labels, title, names):
    if labels.shape != rgb.shape[:2]:
        raise ValueError('Original-grid alignment mismatch')
    palette = np.array([colorsys.hsv_to_rgb((i * .618033989) % 1., .8, .95) for i in range(256)])
    colors = palette[labels]
    shown = rgb.astype(float) / 255.
    foreground = labels > 0
    shown[foreground] = .55 * shown[foreground] + .45 * colors[foreground]
    image = panel(np.clip(shown * 255, 0, 255).astype('uint8'), title)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('DejaVuSans.ttf', 13)
    present = []
    for value in np.unique(labels):
        value = int(value)
        if not value:
            continue
        y, x = np.nonzero(labels == value)
        if len(y) >= 30:
            draw.text((float(np.median(x)), 45 + float(np.median(y))), str(value),
                      fill='white', font=font, stroke_width=2, stroke_fill='black')
        present.append(f'{value}: {names.get(str(value), "UNKNOWN")}')
    draw.multiline_text((5, rgb.shape[0] + 50),
                        '\n'.join(', '.join(present[i:i + 2]) for i in range(0, len(present), 2)),
                        fill='black', font=font, spacing=2)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    pilot = W / 'Human_Parsing_CCIHP_10_Image_Pilot'
    samples = json.loads((pilot / 'configs/TEN_IMAGE_MANIFEST.json').read_text())['images']
    gt_manifest = S / 'provenance/RUN_MANIFESTS/first-cohort-policy-acceptance-20261016T034543760531Z/GT_TRAIN_RECONSTRUCTION/MANIFEST.json'
    gt_rows = {row['image_id']: row for row in json.loads(gt_manifest.read_text())['images']}
    native_runs = {
        'CPI_R50_CIHP': pilot / 'outputs/cpi_r50_cihp-20261012T094956Z/RUN.json',
        'CPI_ConvNeXtB_CIHP': pilot / 'outputs/cpi_convnextb_cihp-20261012T083010Z/RUN.json',
    }
    records = []
    for iid in cfg['bounded_train']['input_ids']:
        sample = next(row for row in samples if row['image_id'] == iid)
        if sample['split'] != 'Training':
            raise ValueError('Visual sanity review is TRAIN only')
        source = read_arrays(pilot / sample['input'], sample['input_sha256'])
        gt = gt_rows[iid]
        cached = read_arrays(S / gt['artifact'], gt['artifact_sha256'])
        if any(not np.array_equal(source[k], cached[k]) for k in ['category', 'human', 'instance']):
            raise ValueError('Cached GT/source mismatch; no new reconstruction performed')
        panels = [panel(source['rgb'], 'Original RGB')]
        ccihp_names = {str(i): str(i) for i in np.unique(cached['category'])}
        ccihp_names.update({'6': 'Face Mask (CCIHP)', '10': 'Torso-skin', '13': 'Face'})
        panels.append(overlay(source['rgb'], cached['category'], 'CCIHP GT native IDs (separate taxonomy)', ccihp_names))
        row = dict(image_id=iid, split='Training', input=sample, cached_gt=gt,
                   original_grid=True, native_predictions={})
        for model, manifest in native_runs.items():
            data = json.loads(manifest.read_text())
            case = next(c for c in data['cases'] if c['image_id'] == iid)
            arrays = read_arrays(pilot / case['artifact'], case['artifact_sha256'])
            masks, boxes = arrays['person_semantic_masks'], arrays['bboxes_xyxy_scores']
            if masks.shape[1:] != source['rgb'].shape[:2] or len(masks) != len(boxes):
                raise ValueError('Saved parser output geometry mismatch')
            composite = np.zeros(source['rgb'].shape[:2], np.uint8)
            for i in np.argsort(boxes[:, 4], kind='stable'):
                foreground = masks[i] > 0
                composite[foreground] = masks[i][foreground]
            panels.append(overlay(source['rgb'], composite, model + '\nraw IDs / standard CIHP display names', data['native_labels']))
            row['native_predictions'][model] = dict(
                manifest_workspace_relative=manifest.relative_to(W).as_posix(),
                manifest_sha256=file_hash(manifest),
                artifact_workspace_relative=(pilot / case['artifact']).relative_to(W).as_posix(),
                artifact_sha256=case['artifact_sha256'],
                checkpoint_sha256=data['checkpoint_sha256'], source_commit=data['source_commit'],
                present_ids=np.unique(masks).tolist(), native_instances=len(masks),
                source_precision=data['precision'],
                source_history='Existing pilot; retain original run memory-adapter/control notes; not a fresh runtime measurement')
        image = out / (iid + '_saved_channels.png')
        contact = Image.new('RGB', (sum(p.width for p in panels), panels[0].height + 35), 'white')
        ImageDraw.Draw(contact).text((6, 6), f'TRAIN {iid} | Same original grid | No new inference | Display-only overlap composition',
                                     fill='black', font=ImageFont.truetype('DejaVuSans.ttf', 15))
        left = 0
        for item in panels:
            contact.paste(item, (left, 35)); left += item.width
        contact.save(image)
        row.update(visualization=str(image.relative_to(S)), visualization_sha256=file_hash(image))
        records.append(row)
    value = dict(status='PREPARED_AWAITING_VISUAL_INSPECTION', images=records,
                 selection='Existing three predeclared TRAIN inputs, not chosen by model accuracy',
                 requirement='Check for conspicuous channel/geometry contradiction, not all-classes-correct prediction',
                 composite='All saved native predictions; highest score wins overlap for display only; no metric filtering',
                 GT_reconstructed_again=False, new_inference=False, metrics_computed=False,
                 script_sha256=file_hash(Path(__file__)))
    with (out / 'MANIFEST.json').open('x') as stream:
        json.dump(value, stream, indent=2)
    print(json.dumps(dict(images=len(records), new_inference=False, metrics_computed=False)))


if __name__ == '__main__':
    main()
