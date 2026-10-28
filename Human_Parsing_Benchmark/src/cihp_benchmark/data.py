"""Strict, non-mutating CIHP native reader. PNG palette indices remain labels."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES=False
LABELS=['Background','Hat','Hair','Glove','Sunglasses','UpperClothes','Dress','Coat','Socks','Pants','Torso-skin','Scarf','Skirt','Face','Left-arm','Right-arm','Left-leg','Right-leg','Left-shoe','Right-shoe']
def file_hash(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read_image(path,mask=False):
 with Image.open(path) as im:
  im.load();mode=im.mode;orientation=im.getexif().get(274,1)
  if orientation not in [None,1]:raise ValueError('Unresolved EXIF orientation '+str(orientation))
  a=np.array(im if mask else im.convert('RGB'),copy=True)
 if mask and (a.ndim!=2 or a.dtype.kind not in 'ui'):raise ValueError('Integer 2D native label plane required: '+str((mode,a.dtype,a.shape)))
 return a,{'mode':mode,'dtype':str(a.dtype),'shape':list(a.shape),'file_sha256':file_hash(path)}
def read_sample(root,split,iid):
 base=Path(root)/split;rgb,info=read_image(base/'Images'/(iid+'.jpg'));arrays={'rgb':rgb};meta={'RGB':info}
 for kind in ['Category_ids','Human_ids','Instance_ids']:
  arrays[kind],meta[kind]=read_image(base/kind/(iid+'.png'),mask=True)
  if arrays[kind].shape!=rgb.shape[:2]:raise ValueError('RGB/GT dimensions differ: '+kind)
 c=arrays['Category_ids']
 if np.any((c>=20)&(c!=255)):raise ValueError('Out-of-schema semantic IDs '+str(np.unique(c[(c>=20)&(c!=255)])))
 meta['decoded_RGB_sha256']=hashlib.sha256(rgb.tobytes()).hexdigest();meta['wh']=[rgb.shape[1],rgb.shape[0]]
 return arrays,meta
