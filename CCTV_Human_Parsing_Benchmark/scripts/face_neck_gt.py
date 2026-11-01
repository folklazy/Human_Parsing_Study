"""Private RGB-only Face/Neck refinement and explicit GT-only eligibility.

No model/detector predictions are opened. Source masks remain immutable.
Manual vertices and per-person records are private artifacts, never public Git.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse
import json
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from controlled_roi_core import read, atomic, sha

P = Path(__file__).resolve().parents[1]
W = P.parent


def font(size):
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
    except OSError:
        return ImageFont.load_default()


def review(reference_path, source_config, out):
    """Coordinate references, RGB and source-Face outline only, never predictions."""
    rows, config = read(reference_path), read(source_config)
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    members = {m['id']: m for m in config['members']}
    owner = read(P/'outputs/controlled-gt-owner-20261101/GT_REVISION.json')
    bindings = {r['image_id']: r for r in owner['bindings']}
    refs = []
    for row in rows:
        member = members[row['image_id']]; b = bindings[row['image_id']]
        path = W/config['dataset_root']/'Images'/(member['stem']+'.jpg')
        if sha(path) != member['RGB_sha256']:
            raise ValueError('RGB source drift')
        rgb = np.asarray(Image.open(path).convert('RGB'))
        category = np.asarray(Image.open(W/b['Category_ids']))
        human = np.asarray(Image.open(W/b['Human_ids']))
        face = ((category == 13) & (human == row['person_id'])).astype(np.uint8)
        x0, y0, x1, y1 = row['close_crop_xyxy']
        scale = max(3, min(12, 1000//max(x1-x0, y1-y0)))
        raw = Image.fromarray(rgb[y0:y1, x0:x1]).resize(((x1-x0)*scale, (y1-y0)*scale), Image.Resampling.NEAREST)
        overlay = rgb.copy()
        contours, _ = cv2.findContours(face, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, (255, 225, 0), 1)
        marked = Image.fromarray(overlay[y0:y1, x0:x1]).resize(raw.size, Image.Resampling.NEAREST)
        canvas = Image.new('RGB', (raw.width*2+120, raw.height+100), '#181818')
        draw = ImageDraw.Draw(canvas); f = font(14)
        draw.text((10, 3), f"F{row['face_index']:02d} {row['image_id']} person{row['person_id']}: RGB | SOURCE FACE OUTLINE; original coordinates", font=f, fill='white')
        for start, im in [(45, raw), (raw.width+100, marked)]:
            canvas.paste(im, (start, 65))
            step = 5 if scale >= 7 else 10
            for x in range((x0//step+1)*step, x1, step):
                px = start+(x-x0)*scale
                draw.line([(px, 53), (px, 64)], fill='white')
                draw.text((px-9, 34), str(x), font=f, fill='white')
            for y in range((y0//step+1)*step, y1, step):
                py = 65+(y-y0)*scale
                draw.text((start-43, py-8), str(y), font=f, fill='white')
        name = f"face_{row['face_index']:02d}.png"; canvas.save(out/name)
        refs.append(dict(**row, detail_figure=name, detail_sha256=sha(out/name), detail_scale=scale,
            RGB_sha256=member['RGB_sha256'], Category_sha256=b['Category_sha256'], Human_sha256=b['Human_sha256']))
    atomic(out/'MANIFEST.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
        source_reference_sha256=sha(reference_path), source_config_sha256=sha(source_config),
        reviewer_input='RGB/source GT only; no parser/detector output', figures=refs))


def polygons_mask(polygons, shape):
    out = np.zeros(shape, np.uint8)
    for vertices in polygons:
        points = np.asarray(vertices)
        if points.ndim != 2 or points.shape[1] != 2 or len(points) < 3 or not np.isfinite(points).all():
            raise ValueError('Manual polygon requires at least three finite original-grid vertices')
        if not np.equal(points, np.round(points)).all():
            raise ValueError('Integer original-grid vertices required')
        if np.any(points < 0) or np.any(points[:, 0] >= shape[1]) or np.any(points[:, 1] >= shape[0]):
            raise ValueError('Manual polygon outside image')
        cv2.fillPoly(out, [points.astype(np.int32)], 1)
    return out.astype(bool)


def materialize(base_binding_path, annotation_path, out):
    base, annotations = read(base_binding_path), read(annotation_path)
    if annotations['parser_predictions_used']:
        raise ValueError('Prediction-assisted GT is forbidden')
    if annotations['base_GT_binding_sha256'] != sha(base_binding_path):
        raise ValueError('Manual annotation/base GT binding mismatch')
    expected = {(r['image_id'], r['person_id']) for r in base['part_records'] if r['target'] == 'FaceDomain'}
    decisions = {(r['image_id'], r['person_id']): r for r in annotations['records']}
    if set(decisions) != expected or len(decisions) != len(annotations['records']):
        raise ValueError('Face review must resolve every source record exactly once')
    frames = {r['image_id']: r for r in base['frames']}
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    rows = []
    for key, row in decisions.items():
        frame = frames[key[0]]
        for field, digest in [('Category_ids','Category_sha256'),('Human_ids','Human_sha256')]:
            if sha(W/frame[field]) != frame[digest]:
                raise ValueError('Source GT changed')
        category = np.asarray(Image.open(W/frame['Category_ids']))
        human = np.asarray(Image.open(W/frame['Human_ids']))
        source_face = (category == 13) & (human == key[1])
        if row['disposition'] == 'ELIGIBLE':
            if row['Neck_status'] not in {'VISIBLE_ANNOTATED', 'VERIFIED_NOT_VISIBLE', 'REGION_UNCERTAIN'}:
                raise ValueError('Eligible Face requires actual Neck review')
            neck = polygons_mask(row['neck_polygons'], category.shape)
            uncertain = polygons_mask(row['uncertainty_polygons'], category.shape)
            occluder = polygons_mask(row.get('known_occluder_polygons', []), category.shape)
            # Visible opaque occluders are negative, not hidden/amodal Neck or
            # an ignored region. Uncertain edge bands may surround their cores.
            uncertain &= ~occluder
            if row['Neck_status'] == 'VISIBLE_ANNOTATED' and not neck.any():
                raise ValueError('Visible Neck needs positive vertices')
            if row['Neck_status'] == 'VERIFIED_NOT_VISIBLE' and neck.any():
                raise ValueError('Absent Neck contradicts positive Neck mask')
            if row['Neck_status'] == 'REGION_UNCERTAIN' and (neck.any() or not uncertain.any()):
                raise ValueError('Uncertain Neck needs a manually bounded uncertainty region, not a fake empty Neck truth')
            neck &= ~(uncertain | occluder)
            if row['Neck_status'] == 'VISIBLE_ANNOTATED' and not neck.any():
                raise ValueError('No known visible Neck remains after uncertainty/occlusion')
            face = source_face & ~neck & ~uncertain & ~occluder
            if not face.any():
                raise ValueError('Eligible Face has no positive valid pixels')
            target = out/(key[0]+f"_person{key[1]}.npz")
            with target.open('wb') as stream:
                np.savez_compressed(stream, Face=face, Neck=neck, uncertainty=uncertain, known_occluder=occluder)
            rows.append(dict(**row, masks=str(target.resolve().relative_to(W)), masks_sha256=sha(target),
                source_Face_pixels=int(source_face.sum()), Face_pixels=int(face.sum()),
                Neck_pixels=int(neck.sum()) if row['Neck_status'] != 'REGION_UNCERTAIN' else None,
                FaceNeck_delivery_eligible=row['Neck_status'] != 'REGION_UNCERTAIN',
                known_occluder_pixels=int(occluder.sum()),
                uncertainty_pixels=int(uncertain.sum()), source_Face_uncertain_pixels=int((source_face & uncertain).sum()),
                source_Face_reassigned_Neck_pixels=int((source_face & neck).sum())))
        elif row['disposition'] in {'INELIGIBLE_RGB_AMBIGUITY', 'INELIGIBLE_SOURCE_CONTOUR'}:
            if row['neck_polygons'] or row['uncertainty_polygons']:
                raise ValueError('Ineligible item must not invent anatomical masks')
            rows.append(dict(**row, masks=None, masks_sha256=None, source_Face_pixels=int(source_face.sum()),
                Face_pixels=None, Neck_pixels=None, uncertainty_pixels=None))
        else:
            raise ValueError('Unresolved Face decision is not a completed GT review')
    summary = dict(status='GT_ONLY_FACE_NECK_REVIEW_RESOLVED', created_utc=datetime.now(timezone.utc).isoformat(),
        base_GT_binding=str(Path(base_binding_path).resolve().relative_to(W)), base_GT_binding_sha256=sha(base_binding_path),
        manual_annotation_sha256=sha(annotation_path), materialization_source_sha256=sha(__file__),
        records=rows, source_annotations_modified=False, parser_predictions_used=False, expert_certified=False,
        review_scope='Agent-assisted original RGB/source-Face refinement; excluded ambiguities apply identically to every model',
        disposition_counts=dict(Counter(r['disposition'] for r in rows)),
        Neck_status_counts=dict(Counter(r['Neck_status'] for r in rows)),
        expected_eligible_Face_parts=sum(r['disposition']=='ELIGIBLE' for r in rows),
        expected_FaceNeck_delivery_parts=sum(r.get('FaceNeck_delivery_eligible', False) for r in rows),
        GT_review_resolved=True, Face_reference='source Face minus manually reviewed Neck and uncertainty; source Face contour otherwise retained',
        post_hoc=True)
    if not summary['expected_eligible_Face_parts']:
        raise ValueError('No eligible Face support; primary must remain null')
    atomic(out/'FACE_NECK_GT_BINDING.json', summary)
    print(json.dumps({k:summary[k] for k in ['status','disposition_counts','expected_eligible_Face_parts']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('review'); r.add_argument('--reference',type=Path,required=True); r.add_argument('--config',type=Path,required=True)
    m = sub.add_parser('materialize'); m.add_argument('--base-binding',type=Path,required=True); m.add_argument('--annotations',type=Path,required=True)
    for item in [r,m]: item.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.command == 'review': review(args.reference,args.config,args.out)
    else: materialize(args.base_binding,args.annotations,args.out)
