"""Input-only diagnostic transforms; never modify frozen preprocessing/scorers."""
import numpy as np
import cv2
import torch
import torch.nn.functional as F


def letterbox(rgb, preprocessor, input_hw=(1024, 768)):
    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError('Expected RGB uint8 image')
    h, w = rgb.shape[:2]; ih, iw = input_hw
    ratio = min(iw / w, ih / h)
    nw, nh = max(1, round(w * ratio)), max(1, round(h * ratio))
    interpolation = cv2.INTER_AREA if ratio < 1 else cv2.INTER_CUBIC
    resized = cv2.resize(rgb, (nw, nh), interpolation=interpolation)
    left, top = (iw - nw) // 2, (ih - nh) // 2
    mean = preprocessor.mean.detach().cpu().numpy().ravel()
    canvas = np.broadcast_to(mean, (ih, iw, 3)).copy()
    canvas[top:top + nh, left:left + nw] = resized
    # Official normalizer receives BGR CHW, exactly once. Float mean-color padding
    # becomes normalized zero; no extra divide255 or crop/resize inside normalizer.
    inputs = torch.from_numpy(canvas[:, :, ::-1].copy().transpose(2, 0, 1)).contiguous()
    tensor = preprocessor(dict(inputs=inputs))['inputs'].float()
    geometry = dict(original_hw=[h, w], input_hw=[ih, iw], resized_hw=[nh, nw],
                    padding_ltrb=[left, top, iw - nw - left, ih - nh - top],
                    interpolation='AREA' if ratio < 1 else 'CUBIC',
                    normalized_padding=0, preserve_aspect_ratio=True)
    return tensor, geometry, np.rint(canvas).clip(0, 255).astype(np.uint8)


def restore_letterbox(logits, geometry):
    if logits.ndim != 4 or tuple(logits.shape[:2]) != (1, 29) or logits.dtype != torch.float32 or not torch.isfinite(logits).all():
        raise ValueError('Finite batch1 native29 FP32 logits required')
    ih, iw = geometry['input_hw']; nh, nw = geometry['resized_hw']
    left, top, _, _ = geometry['padding_ltrb']
    if tuple(logits.shape[-2:]) != (ih, iw):
        logits = F.interpolate(logits, size=(ih, iw), mode='bilinear', align_corners=False)
    unpadded = logits[:, :, top:top + nh, left:left + nw]
    mapped = F.interpolate(unpadded, size=geometry['original_hw'], mode='bilinear', align_corners=False)
    return mapped.argmax(1)[0].cpu().numpy().astype(np.uint8)


def detector_crop(rgb, bbox, extent, context=.1):
    """Predicted box +10% each side, expanded to contain frozen detector extent."""
    h, w = rgb.shape[:2]
    if extent.shape != (h, w) or not extent.any() or not np.isfinite(bbox).all():
        raise ValueError('Valid nonempty detector extent and finite bbox required')
    x0, y0, x1, y1 = map(float, bbox)
    if x1 <= x0 or y1 <= y0:
        raise ValueError('Invalid detector bbox')
    dx, dy = (x1 - x0) * context, (y1 - y0) * context
    yy, xx = np.where(extent)
    x0 = max(0, min(int(np.floor(x0 - dx)), int(xx.min())))
    y0 = max(0, min(int(np.floor(y0 - dy)), int(yy.min())))
    x1 = min(w, max(int(np.ceil(x1 + dx)), int(xx.max()) + 1))
    y1 = min(h, max(int(np.ceil(y1 + dy)), int(yy.max()) + 1))
    return rgb[y0:y1, x0:x1].copy(), [x0, y0, x1, y1]


def place_roi(native_crop, box, extent):
    x0, y0, x1, y1 = box
    if native_crop.shape != (y1 - y0, x1 - x0) or native_crop.dtype != np.uint8 or np.any(native_crop >= 29):
        raise ValueError('Invalid original-crop native29 hard labels')
    raw = np.zeros(extent.shape, np.uint8)
    raw[y0:y1, x0:x1] = native_crop
    return raw, np.where(extent, raw, 0).astype(np.uint8)
