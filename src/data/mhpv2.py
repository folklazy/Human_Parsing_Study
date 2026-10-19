"""Lossless MHP-v2 GT reader. Original files and instance planes stay separate."""
from dataclasses import dataclass
from pathlib import Path
from hashlib import sha256
from io import BytesIO
import re

import numpy as np
from PIL import Image

ANNOTATION_NAME = re.compile(r"^(?P<image_id>\d+)_(?P<person_count>\d+)_(?P<person_id>\d+)\.png$")
BODY_CLOTHING_IDS = frozenset(range(1, 39)) | {57, 58}


def decode_native(path):
    """Official v2 rule: first PNG channel; alpha is never an ignore plane."""
    with Image.open(path) as image:
        image.load()
        array = np.array(image)
    labels = array[..., 0] if array.ndim == 3 else array
    if labels.ndim != 2 or labels.dtype != np.uint8:
        raise ValueError("Expected two-dimensional uint8 native labels")
    if np.any(labels > 58):
        raise ValueError("Native first-channel class outside 0..58")
    return np.ascontiguousarray(labels)


def bounding_region(mask):
    rows = np.flatnonzero(np.any(mask, axis=1))
    columns = np.flatnonzero(np.any(mask, axis=0))
    if not len(rows):
        return None
    return [int(columns[0]), int(rows[0]), int(columns[-1] + 1), int(rows[-1] + 1)]


def lossless_roundtrip(labels):
    output = BytesIO()
    Image.fromarray(labels).save(output, format="PNG")
    output.seek(0)
    with Image.open(output) as image:
        restored = np.array(image)
    return np.array_equal(labels, restored)


@dataclass(frozen=True)
class PersonGroundTruth:
    image_id: str
    person_file_id: int
    annotation_path: str
    original_wh: tuple
    annotation_sha256: str

    @property
    def canonical_id(self):
        return f"{self.image_id}:parsing:{self.person_file_id}"

    def read(self, dataset_root):
        path = Path(dataset_root) / self.annotation_path
        if sha256(path.read_bytes()).hexdigest() != self.annotation_sha256:
            raise ValueError("Source annotation fingerprint changed")
        labels = decode_native(path)
        if labels.shape != (self.original_wh[1], self.original_wh[0]):
            raise ValueError("GT not in original image coordinates")
        return labels

    def foreground(self, dataset_root):
        # Parsing support includes carried objects; this is not anatomy.
        return self.read(dataset_root) > 0

    def body_clothing_support(self, dataset_root):
        # Draft localization support; attached accessories deliberately omitted.
        return np.isin(self.read(dataset_root), tuple(BODY_CLOTHING_IDS))
