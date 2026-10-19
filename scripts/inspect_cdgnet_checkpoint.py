"""CPU weights-only inspection. Does not build/run the CDGNet model."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import zipfile
import torch

STUDY = Path(__file__).resolve().parents[1]
WORKSPACE = STUDY.parent
RUN = STUDY / json.loads((STUDY / 'provenance/CDGNET_ACQUISITION_ACTIVE.json').read_text())['run']
record = json.loads((RUN / 'ACQUISITION.json').read_text())
checkpoint = WORKSPACE / record['destination']
result = {'started_utc': datetime.now(timezone.utc).isoformat(), 'checkpoint_sha256': record['sha256'],
          'torch': torch.__version__, 'device': 'CPU', 'weights_only': True,
          'model_built': False, 'model_inference': False, 'status': 'INSPECTING'}
try:
    value = hashlib.sha256()
    with checkpoint.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            value.update(block)
    assert value.hexdigest() == record['sha256']
    if zipfile.is_zipfile(checkpoint):
        with zipfile.ZipFile(checkpoint) as archive:
            assert archive.testzip() is None
        result['pytorch_zip_crc'] = 'PASS'
    else:
        result['pytorch_zip_crc'] = 'NOT_ZIP_SERIALIZATION'
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    if isinstance(state, dict) and 'state_dict' in state:
        state = state['state_dict']
    assert isinstance(state, dict) and state
    assert all(isinstance(key, str) and torch.is_tensor(tensor) for key, tensor in state.items())
    heads = {}
    total = 0
    dtypes = set()
    for key, tensor in state.items():
        total += tensor.numel()
        dtypes.add(str(tensor.dtype))
        if tensor.is_floating_point():
            assert torch.isfinite(tensor).all().item(), key
        normalized = key.removeprefix('module.')
        if normalized in {'layer6.conv4.weight', 'layer6.conv4.bias', 'layer7.2.weight', 'L.weight', 'L.bias'}:
            heads[key] = list(tensor.shape)
    assert any(key.endswith('layer6.conv4.weight') and shape[0] == 20 for key, shape in heads.items())
    result.update(status='PASS_WEIGHTS_ONLY_STRUCTURAL_INSPECTION', tensor_entries=len(state),
                  tensor_elements_including_buffers=total, dtypes=sorted(dtypes), finite_tensors=True,
                  parser_head_shapes=heads, parsing_classes_in_head=20,
                  limitations='Structural inspection only; strict architecture load and inference NOT_TESTED')
except Exception as error:
    result.update(status='INSPECTION_FAILED', error_type=type(error).__name__, error=str(error))
result['completed_utc'] = datetime.now(timezone.utc).isoformat()
temporary = RUN / 'WEIGHTS_INSPECTION.json.tmp'
temporary.write_text(json.dumps(result, indent=2) + '\n')
os.replace(temporary, RUN / 'WEIGHTS_INSPECTION.json')
print(json.dumps(result, indent=2))
if result['status'] == 'INSPECTION_FAILED':
    raise SystemExit(1)
