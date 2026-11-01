"""New per-crop adapters. Frozen native adapters/source/configs stay untouched."""
from pathlib import Path
import json
import os
import sys
import numpy as np
from PIL import Image
from controlled_roi_core import atomic, letterbox_canvas, select_instance, validate_native


def prepare_qanet_rgb(rgb, cfg):
    import torch
    hw=(cfg.TEST.SCALE[1],cfg.TEST.SCALE[0])
    canvas,geometry=letterbox_canvas(rgb,hw,np.asarray(cfg.PIXEL_MEANS)*255)
    tensor=torch.from_numpy(canvas.transpose(2,0,1).copy()).float()[None]
    means=torch.tensor(cfg.PIXEL_MEANS).view(1,3,1,1)
    stds=torch.tensor(cfg.PIXEL_STDS).view(1,3,1,1)
    return (tensor/255-means)/stds,geometry


def restore_qanet_probabilities(probs, geometry):
    import torch
    import torch.nn.functional as F
    if probs.shape[:2]!=(1,20) or probs.dtype!=torch.float32 or not torch.isfinite(probs).all():
        raise ValueError('QANet native probability contract')
    hw=tuple(geometry['input_hw'])
    if tuple(probs.shape[-2:])!=hw:
        probs=F.interpolate(probs,size=hw,mode='bilinear',align_corners=False)
    left,top,_,_=geometry['padding_ltrb'];nh,nw=geometry['resized_hw']
    probs=F.interpolate(probs[:,:,top:top+nh,left:left+nw],size=geometry['original_hw'],mode='bilinear',align_corners=False)
    confidence,labels=probs.max(1)
    return (labels*(confidence>=1/20)).cpu().numpy()[0].astype(np.uint8)


def cpi_native_files(directory, input_name):
    # Native exporter strips .jpg only. A PNG input intentionally produces
    # <crop>.png-<instance>.png. Keep lossless pixels and read the actual contract.
    prefix=Path(input_name).name.split('.jpg')[0]
    return sorted(Path(directory).glob(prefix+'-*.png'),key=lambda p:int(p.stem.rsplit('-',1)[1]))


def derived_config(workspace, model, destination):
    """Separate resolved overrides; never edit the original config or checkpoint."""
    import yaml
    src = workspace/model['native_config']; family = model['family']
    destination.mkdir(parents=True, exist_ok=False)
    if family in ('M2FP', 'D2FP'):
        out = destination/'single_view.yaml'
        out.write_text(yaml.safe_dump({'_BASE_': str(src), 'TEST': {'AUG': {'ENABLED': False}}}))
    elif family in ('QANet', 'RP-R-CNN'):
        data = yaml.safe_load(src.read_text())
        test = data.setdefault('TEST', {})
        if family == 'QANet':
            test.setdefault('AUG', {}).update(H_FLIP=False, SCALES=[])
        else:
            test.setdefault('BBOX_AUG', {}).update(ENABLED=False)
            test.setdefault('PARSING_AUG', {}).update(ENABLED=False)
        out = destination/'single_view.yaml'; out.write_text(yaml.safe_dump(data))
    else:
        # Original CPI test pipeline is already one resize and flip=False.
        out = src
    return str(out.relative_to(workspace))


class CropModel:
    def __init__(self, workspace, model, output):
        import torch
        self.torch, self.w, self.spec = torch, Path(workspace), model
        self.family = model['family']; self.output = Path(output)
        self.classes = 29 if self.family == 'Sapiens2' else 20
        if self.family == 'Sapiens2':
            from sapiens.dense.models import init_model
            from safetensors.torch import load_file
            self.model = init_model(self.w/model['native_config'], checkpoint=None, device='cpu')
            if self.model.cfg.num_classes != 29 or self.model.cfg.model_name != model['model_id'].replace('Sapiens2_', 'sapiens2_'):
                raise ValueError('Wrong Sapiens checkpoint/head/config binding')
            state = load_file(self.w/model['checkpoint'], device='cpu')
            self.model.load_state_dict(state, strict=True); del state
            self.model.float().eval().cuda()
            self.details = {'native_config': model['native_config'], 'native29': True, 'external_TTA': False}
        else:
            from cihp_benchmark.adapters import NativeAdapter
            effective = dict(model, native_config=derived_config(self.w, model, self.output/'derived_config'))
            self.adapter = NativeAdapter(self.w, effective, self.output/'native_adapter')
            self.model = self.adapter.model; self.details = dict(self.adapter.details)
            self.details['derived_config'] = effective['native_config']
            if self.family in ('M2FP', 'D2FP') and self.adapter.cfg.TEST.AUG.ENABLED:
                raise ValueError('External TTA unexpectedly enabled')
            if self.family == 'QANet':
                cfg = self.adapter.cfg
                if cfg.TEST.AUG.H_FLIP or len(cfg.TEST.AUG.SCALES) or cfg.IMAGE_FORMAT != 'rgb':
                    raise ValueError('QANet single RGB-view contract')
                self.details['crop_forward'] = 'native backbone/parsing head; whole shared crop letterboxed; no second1.25ROI expansion'
            if self.family == 'RP-R-CNN' and (self.adapter.cfg.TEST.BBOX_AUG.ENABLED or self.adapter.cfg.TEST.PARSING_AUG.ENABLED):
                raise ValueError('RP-R-CNN TTA unexpectedly enabled')
            if self.family == 'CPI-Parser':
                cfg = self.adapter.cfg
                aug = cfg.data.test.pipeline[1]
                if aug['type'] != 'MultiScaleFlipAug' or aug.get('flip', False) or not isinstance(aug['img_scale'], tuple):
                    raise ValueError('CPI single-view source pipeline changed')
                if model['model_id'] == 'CPI_R50_CIHP':
                    from cihp_benchmark.cpi_feature_schedule import install
                else:
                    from cihp_benchmark.cpi_memory import install
                self.details['memory_implementation'] = install(self.model.bbox_head, '85b75e0fe38465ec460107c11111702345a6de091a8ba3d399ca266878ca7573')
                # Exercise the actual framework PNG decoder before a learned forward.
                import mmcv
                probe = np.array([[[255, 13, 2], [9, 31, 200]]], np.uint8)
                p = self.output/'decoder_probe.png'; Image.fromarray(probe).save(p)
                if not np.array_equal(mmcv.imread(str(p))[:, :, ::-1], probe):
                    raise ValueError('CPI lossless PNG/BGR bridge mismatch')
                self.details['lossless_decoder_probe'] = 'EXACT_RGB_READBACK'
        if self.model.training or any(p.dtype != torch.float32 for p in self.model.parameters()):
            raise ValueError('FP32 eval model required')
        self.details['parameters'] = sum(p.numel() for p in self.model.parameters())
        atomic(self.output/'MODEL_DETAILS.json', self.details)

    def infer(self, rgb, image_path, designated_box):
        torch = self.torch; h, w = rgb.shape[:2]
        if self.family == 'Sapiens2':
            from sapiens_input_variants import letterbox, restore_letterbox
            tensor, geometry, _ = letterbox(rgb, self.model.data_preprocessor)
            with torch.inference_mode():
                output = self.model(tensor.cuda())
            if output.dtype != torch.float32:
                raise ValueError('Sapiens unexpected precision')
            native = restore_letterbox(output, geometry)
            details = dict(input_geometry=geometry, selection='DESIGNATED_SEMANTIC_ROI', semantic_confidence=None)
            candidates = native[None]
        elif self.family == 'QANet':
            tensor,geometry=prepare_qanet_rgb(rgb,self.adapter.cfg)
            with torch.inference_mode():
                features = self.model.conv_body_net(tensor.cuda())
                result = self.model.parsing_net(features)
                probs = result['probs']
            native=restore_qanet_probabilities(probs,geometry)
            details = dict(input_geometry=geometry, selection='DESIGNATED_SEMANTIC_ROI', native_value_threshold=1/20,
                           input_RGB=True, normalization_once=True, second_native_ROI_expansion=False,
                           probability_restore='bilinear before argmax; native1/C value threshold retained')
            candidates = native[None]
        elif self.family == 'CPI-Parser':
            from mmdet.apis import inference_detector
            previous=Path.cwd()
            try:
                os.chdir(Path(image_path).parent)
                raw=inference_detector(self.model,Path(image_path).name)
            finally:
                os.chdir(previous)
            boxes_all=np.vstack(raw).astype(np.float32)
            files=cpi_native_files(self.adapter.output/'native/val_parsing',Path(image_path).name)
            if len(files)!=len(boxes_all):raise ValueError('CPI native PNG output/box count mismatch')
            values=[]
            for path in files:
                value=np.asarray(Image.open(path))
                validate_native(value,20,(h,w));values.append(value)
            candidates=np.asarray(values,np.uint8).reshape(-1,h,w)
            boxes,scores=boxes_all[:,:4],boxes_all[:,4]
            usable=[i for i,a in enumerate(candidates) if (a>0).any()]
            selected,overlaps=select_instance(boxes[usable],scores[usable],designated_box)
            source_index=usable[selected] if selected is not None else None
            native=candidates[source_index] if source_index is not None else np.zeros((h,w),np.uint8)
            details=dict(selection='NATIVE_INSTANCE' if source_index is not None else 'NATIVE_ASSOCIATION_MISS',
                native_selected_index=source_index,native_boxes=boxes.tolist(),native_scores=scores.tolist(),
                nonempty_native_indices=usable,bbox_IoUs=overlaps,source_decoder='MMCV lossless PNG/BGR verified',
                native_PNG_filename_contract='input.png-index.png',whole_shared_crop=True,
                native_restoration='native align_corners preserved; memory implementation as MODEL_DETAILS')
        else:
            # Keep the native full crop inference/internal detector, then make the
            # declared deterministic prediction-only designated-instance choice.
            arrays, meta = self.adapter.infer(rgb, image_path, [], np.empty((0, h, w), bool))
            candidates = arrays['raw_native_person_semantic_masks']
            boxes = arrays['raw_native_bboxes_xyxy']; scores = arrays['raw_native_person_scores']
            usable = [i for i, a in enumerate(arrays['raw_native_person_extents']) if a.any()]
            selected, overlaps = select_instance(boxes[usable], scores[usable], designated_box)
            source_index = usable[selected] if selected is not None else None
            native = candidates[source_index] if source_index is not None else np.zeros((h, w), np.uint8)
            details = dict(selection='NATIVE_INSTANCE' if source_index is not None else 'NATIVE_ASSOCIATION_MISS',
                           native_selected_index=source_index, native_boxes=boxes.tolist(), native_scores=scores.tolist(),
                           nonempty_native_indices=usable, bbox_IoUs=overlaps, native_geometry=meta['geometry'])
        validate_native(native, self.classes, (h, w))
        if candidates.shape[1:] != (h, w) or candidates.dtype.kind not in 'ui' or (candidates.size and candidates.max() >= self.classes):
            raise ValueError('Candidate mask export contract')
        return native.astype(np.uint8), candidates.astype(np.uint8), details
