"""Bounded CPU input-tensor parity audit; never build/forward a parser model.

Private previews/IDs stay in outputs/. Export only the sanitized aggregate result.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import sys

import cv2
import numpy as np
from PIL import Image
import torch

P = Path(__file__).resolve().parents[1]
W = P.parent
sys.path.insert(0, str(W / 'Human_Parsing_Benchmark/src'))
from common_view.sapiens_route import make_cpu_pipeline, prepare_rgb, logits_to_native
from common_view.core import sha_file


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def audit(config_path, out):
    if torch.cuda.is_initialized():
        raise RuntimeError('CPU-only audit required')
    torch.set_num_threads(2)
    c = json.loads(config_path.read_text()); raw = config_path.parent
    out.mkdir(parents=True, exist_ok=False)
    # Fixed examples already selected from GT coverage before selected-part scores;
    # no new choice based on which model performs well or poorly.
    selection = json.loads((P / 'outputs/selected-part-scores-20261101/gallery/MANIFEST.json').read_text())
    ids = [r['image_id'] for r in selection['panels']]
    samples = []
    fixture = np.zeros((8, 12, 3), np.uint8)
    fixture[:4, :6] = [255, 0, 0]; fixture[:4, 6:] = [0, 255, 0]
    fixture[4:, :6] = [0, 0, 255]; fixture[4:, 6:] = [255, 255, 0]
    samples.append(('asymmetric_quadrants', fixture, None))
    yy, xx = np.indices((1080, 1920))
    gradient = np.stack([xx % 256, yy % 256, (3 * xx + 7 * yy) % 256], -1).astype(np.uint8)
    samples.append(('asymmetric_gradient', gradient, None))
    for iid in ids:
        member = next(r for r in c['members'] if r['id'] == iid)
        image = W / c['dataset_root'] / 'Images' / (member['stem'] + '.jpg')
        if sha_file(image) != member['RGB_sha256']:
            raise ValueError('Source input changed')
        rgb = np.array(Image.open(image).convert('RGB'))
        samples.append(('fixed_' + member['condition'] + '_CCTV', rgb, image))
    results = []; private = []
    mean = np.array([123.675, 116.28, 103.53], np.float32)
    std = np.array([58.395, 57.12, 57.375], np.float32)
    for mid, model in c['models'].items():
        if model['family'] != 'Sapiens2':
            continue
        config = W / model['native_config']
        assert sha_file(config) == model['native_config_sha256']
        cfg, pipeline, pre = make_cpu_pipeline(config)
        assert cfg.model_name == mid.replace('Sapiens2_', 'sapiens2_')
        assert pre._channel_conversion and pre._enable_normalize
        assert np.array_equal(pre.mean.numpy().ravel(), mean)
        assert np.array_equal(pre.std.numpy().ravel(), std)
        for kind, rgb, image in samples:
            original = rgb.copy()
            actual, geometry = prepare_rgb(rgb, pipeline, pre)
            # Independent direct RGB calculation: no wrapper or pipeline call.
            interpolation = cv2.INTER_AREA if 768 < rgb.shape[1] else cv2.INTER_CUBIC
            resized = cv2.resize(rgb, (768, 1024), interpolation=interpolation)
            expected = ((resized.astype(np.float32) - mean) / std).transpose(2, 0, 1)[None]
            manual_error = float(np.max(np.abs(actual.numpy() - expected)))
            assert manual_error <= 1e-6 and np.array_equal(rgb, original)
            # Official demo path: cv2.imread(BGR) -> config pipeline -> preprocessor.
            # Synthetic fixtures bypass only the on-disk decoder, not preprocessing.
            bgr = cv2.imread(str(image)) if image is not None else rgb[:, :, ::-1].copy()
            official = pre(pipeline(dict(img=bgr)))['inputs']
            official_error = float(torch.max(torch.abs(actual - official)))
            decoded_equal = bool(np.array_equal(bgr[:, :, ::-1], rgb))
            if decoded_equal:
                assert torch.equal(actual, official)
            unnormalized = actual[0].numpy().transpose(1, 2, 0) * std + mean
            recovered = np.rint(unnormalized).clip(0, 255).astype(np.uint8)
            assert np.array_equal(recovered, resized)
            row = dict(model_id=mid, case=kind, input_wh=[rgb.shape[1], rgb.shape[0]],
                tensor_shape=list(actual.shape), tensor_dtype=str(actual.dtype),
                tensor_min=float(actual.min()), tensor_max=float(actual.max()),
                manual_RGB_normalization_max_abs_error=manual_error,
                official_demo_tensor_max_abs_error=official_error,
                PIL_RGB_equals_OpenCV_BGR_reversed=decoded_equal,
                input_array_unmodified=True, inverse_normalized_preview_equals_resized_RGB=True,
                tensor_sha256=hashlib.sha256(actual.numpy().tobytes()).hexdigest())
            results.append(row)
            if image is not None and mid == 'Sapiens2_0.4b':
                name = kind + '_model_input_RGB.png'; Image.fromarray(recovered).save(out / name)
                private.append(dict(case=kind, input_relative_path=str(image.relative_to(W)),
                    input_sha256=sha_file(image), preview=name, preview_sha256=sha_file(out / name), geometry=geometry))
    # Independent asymmetric output-grid check with no neural-network forward.
    logits = torch.zeros((1, 29, 4, 6), dtype=torch.float32)
    for label, ys, xs in [(3, slice(0, 2), slice(0, 3)), (4, slice(0, 2), slice(3, 6)),
                           (23, slice(2, 4), slice(0, 3)), (13, slice(2, 4), slice(3, 6))]:
        logits[0, label, ys, xs] = 10
    mapped = logits_to_native(logits, (8, 12))
    expected = np.array([[3] * 6 + [4] * 6] * 4 + [[23] * 6 + [13] * 6] * 4, np.uint8)
    assert np.array_equal(mapped, expected)
    result = dict(status='INPUT_PREPROCESSING_PARITY_PASS_ON_BOUNDED_CPU_CASES',
        created_utc=datetime.now(timezone.utc).isoformat(), model_forward_calls=0,
        model_or_checkpoint_loaded=False, CUDA_initialized=torch.cuda.is_initialized(),
        source_run=c['run_id'], source_config_sha256=sha_file(config_path),
        wrapper_sha256=sha_file(W / 'Human_Parsing_Benchmark/src/common_view/sapiens_route.py'),
        audit_script_sha256=sha_file(__file__),
        reference_revision='7e5bae88456ac418ff0e58e74106c9fe192055d4',
        official_demo='sapiens/dense/tools/vis/vis_seg.py',
        library_paths=dict(sapiens=__import__('sapiens').__file__, torch=torch.__version__, cv2=cv2.__version__),
        cases=results, asymmetric_logits_original_grid_test='PASS_WITH_SYNTHETIC_LOGITS_ONLY',
        limitations=['CPU reconstruction from bound source/input/environment; historical GPU input tensors were not saved',
            'No learned model forward, checkpoint-output parity or alternative route tested',
            'Full-frame stretch and small-person resolution are retained scientific configuration choices, not a proven channel bug',
            'Scores cannot establish that the implementation is bug-free'])
    assert not result['CUDA_initialized']
    # Keep absolute module location private. Public export uses a relative identity.
    write(out / 'PRIVATE_INPUTS.json', dict(inputs=private, library_paths=result.pop('library_paths')))
    write(out / 'EVIDENCE.json', result)
    print(json.dumps(dict(status=result['status'], cases=len(results), model_calls=0,
        max_manual_error=max(r['manual_RGB_normalization_max_abs_error'] for r in results),
        max_official_error=max(r['official_demo_tensor_max_abs_error'] for r in results), output=str(out))))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(); audit(args.config, args.out)
