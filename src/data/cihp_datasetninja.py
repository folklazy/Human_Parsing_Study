"""Read converted CIHP part bitmaps; never invent person ownership.

Supervisely bitmap data is base64(zlib(PNG)), with support encoded by alpha.
Native CIHP IDs come from the reviewed converter, not Supervisely class IDs.
"""
from base64 import b64decode
from io import BytesIO
import zlib
import numpy as np
from PIL import Image

NATIVE_IDS = {'hat':1,'hair':2,'glove':3,'sunglasses':4,'upperclothes':5,
              'dress':6,'coat':7,'socks':8,'pants':9,'torso_skin':10,'scarf':11,
              'skirt':12,'face':13,'left_arm':14,'right_arm':15,'left_leg':16,
              'right_leg':17,'left_shoe':18,'right_shoe':19}


def decode_bitmap(obj, image_wh):
    if obj.get('geometryType')!='bitmap' or obj.get('classTitle') not in NATIVE_IDS:
        raise ValueError('Unknown bitmap class/geometry')
    xy=obj['bitmap']['origin']
    if len(xy)!=2 or any(type(v)!=int for v in xy) or min(xy)<0:
        raise ValueError('Invalid bitmap origin')
    compressed=b64decode(obj['bitmap']['data'],validate=True)
    decoder=zlib.decompressobj()
    png=decoder.decompress(compressed,16*1024*1024+1)
    if len(png)>16*1024*1024 or not decoder.eof or decoder.unused_data:
        raise ValueError('Invalid/oversized zlib bitmap')
    # Verify all PNG chunk CRCs, then fully load decoded pixels separately.
    with Image.open(BytesIO(png)) as image:
        if image.format!='PNG':raise ValueError('Bitmap is not PNG')
        image.verify()
    with Image.open(BytesIO(png)) as image:
        image.load()
        if 'transparency' not in image.info and 'A' not in image.getbands():
            raise ValueError('Bitmap has no alpha/transparency support convention')
        mask=np.asarray(image.convert('RGBA'))[...,3]>0
    w,h=image_wh;x,y=xy;mh,mw=mask.shape
    if mw<=0 or mh<=0 or x+mw>w or y+mh>h:
        raise ValueError('Bitmap outside original annotation grid')
    if not mask.any():raise ValueError('Empty bitmap object')
    return mask,(x,y),NATIVE_IDS[obj['classTitle']]


def reconstruct_semantic(annotation):
    """Return derived semantic map and ambiguity diagnostics, never person map."""
    w,h=annotation['size']['width'],annotation['size']['height']
    result=np.zeros((h,w),np.uint8)
    coverage=np.zeros((h,w),np.uint16)
    cross_class=0
    for obj in annotation['objects']:
        mask,(x,y),label=decode_bitmap(obj,(w,h));mh,mw=mask.shape
        region=result[y:y+mh,x:x+mw];count=coverage[y:y+mh,x:x+mw]
        cross_class+=int(np.count_nonzero(mask & (count>0) & (region!=label)))
        count[mask]+=1;region[mask]=label
    return result,{'overlap_pixels':int(np.count_nonzero(coverage>1)),
                   'cross_class_overwrite_events':cross_class,'person_identity':'NOT_AVAILABLE',
                   'uncovered_pixels':'implicit converted background; original void fidelity unverified'}
