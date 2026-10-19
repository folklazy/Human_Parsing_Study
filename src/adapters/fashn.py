"""Pinned official FASHN preprocessing/native model; no scoring or fusion."""
from pathlib import Path
import importlib
import sys
from .base import BaseParserAdapter


class FashnAdapter(BaseParserAdapter):
    def __init__(self,source_root,checkpoint_root):
        self.source_root=Path(source_root);self.checkpoint_root=Path(checkpoint_root);self.parser=None
    def load(self):
        sys.path.insert(0,str(self.source_root/'src'))
        from fashn_human_parser import FashnHumanParser
        # Official class accepts local from_pretrained directory; no implicit Hub revision.
        self.parser=FashnHumanParser(model_id=str(self.checkpoint_root),device='cuda')
        self.parser.model.float().eval()
    def describe_model(self):
        return {'mode':'SINGLE_SEMANTIC_IMAGE_OR_CROP','native_input_wh':[384,576],'native_ids':list(range(18)),
                'native_instances':False,'scores_available':False,'logits_available':True,'precision':'FP32'}
    def preprocess(self,sample):
        return self.parser._preprocess_single(sample)
    def infer(self,prepared_input):
        import torch
        with torch.inference_mode():
            return self.parser.model(pixel_values=prepared_input.unsqueeze(0).cuda().float()).logits
    def postprocess(self,raw_output,output_hw=None):
        import torch
        if output_hw is None: raise ValueError('Explicit original crop dimensions required')
        logits=torch.nn.functional.interpolate(raw_output,size=output_hw,mode='bilinear',align_corners=False)
        if not torch.isfinite(logits).all(): raise ValueError('Non-finite native logits')
        return logits.argmax(1).cpu().numpy().astype('uint8'),logits.cpu().numpy()
    def export_prediction(self,prediction):
        from src.contracts.prediction import export_prediction
        directory,record,masks,logits=prediction
        return export_prediction(directory,record,masks,logits)
    def cleanup(self):
        import torch
        self.parser=None;torch.cuda.empty_cache()
