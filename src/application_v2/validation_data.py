"""Lazy verified source reads. Never used as a source of model conditioning GT."""
from io import BytesIO
import hashlib
import struct
import numpy as np
from PIL import Image
from .policy import digest
from .taxonomy import project_gt
from .evaluation import person_truth


def pixels_hash(array):
    return digest(dict(shape=list(array.shape),dtype=str(array.dtype),bytes_sha256=hashlib.sha256(array.tobytes()).hexdigest()))


def read_rgb(archive, sample):
    with archive.open('rb') as stream:
        stream.seek(sample['RGB_tar_data_offset'])
        raw=stream.read(sample['RGB_bytes'])
    if hashlib.sha256(raw).hexdigest()!=sample['RGB_sha256']:
        raise ValueError('Original RGB member bytes differ from bound source')
    with Image.open(BytesIO(raw)) as image:
        image.load();rgb=np.asarray(image.convert('RGB')).copy()
    if [rgb.shape[1],rgb.shape[0]]!=sample['wh']:
        raise ValueError('RGB geometry mismatch')
    if hashlib.sha256(struct.pack('>II',rgb.shape[1],rgb.shape[0])+rgb.tobytes()).hexdigest()!=sample['decoded_RGB_sha256']:
        raise ValueError('Decoded source RGB differs from prior audit')
    return raw,rgb


def read_gt(archive, binding, expected_persons, mapping, protocol):
    """Reconstruct just one scoring input and verify the existing decoded contract."""
    maps={}
    for source in binding['source_GT']:
        raw=archive.read(source['member'])
        if hashlib.sha256(raw).hexdigest()!=source['sha256']:
            raise ValueError('GT source member bytes changed')
        if source['component'] in ['Category_ids','Human_ids']:
            with Image.open(BytesIO(raw)) as image:
                image.load();array=np.asarray(image).copy()
            if str(array.dtype)!=source['dtype'] or [array.shape[1],array.shape[0]]!=source['wh']:
                raise ValueError('GT source geometry/dtype changed')
            maps[source['component']]=array
    category,human=maps['Category_ids'],maps['Human_ids']
    target,valid=project_gt(category,human,mapping)
    gt,persons=[],[]
    for pid in np.unique(human):
        if not pid:continue
        truth,per_valid=person_truth(target,human,valid,int(pid))
        y,x=np.nonzero(human==pid)
        box=[int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1]
        sem=bool(((truth>0)&per_valid).any())
        persons.append(dict(image_id=binding['image_id'],person_id=int(pid),bbox_xyxy_half_open=box,
            G_loc=True,G_sem=sem,semantic_sha256=pixels_hash(truth),valid_sha256=pixels_hash(per_valid)))
        gt.append(dict(id=str(int(pid)),bbox=box,loc_eligible=True,sem_eligible=sem,semantic=truth,valid=per_valid))
    if persons!=expected_persons:
        raise ValueError('Per-person decoded GT differs from frozen package')
    recipe=dict(image_id=binding['image_id'],source_maps=binding['source_GT'],original_wh=binding['input_binding']['original_wh'],
        GT_projection_sha256=protocol['mapping']['GT_projection_sha256'],domain_policy_sha256=protocol['domain']['policy_sha256'])
    domain=binding['image_domain_binding']
    if domain['GT_domain_recipe_sha256']!=digest(recipe):raise ValueError('GT recipe mismatch')
    contract=digest(dict(category=pixels_hash(category),human=pixels_hash(human),target=pixels_hash(target),
        global_valid=pixels_hash(valid),persons=persons))
    if domain['decoded_GT_contract_sha256']!=contract:raise ValueError('Decoded GT contract mismatch')
    return gt
