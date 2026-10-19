"""Atomic immutable packets; partial output semantics are decided by runner."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import hashlib
import numpy as np
from .contracts import validate_frame


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def commit_packet(directory, record, masks, fingerprints, *, native_arrays=None, fault=None):
    validate_frame(record, masks)
    directory = Path(directory)
    directory.parent.mkdir(parents=True, exist_ok=True)
    if directory.exists():
        raise FileExistsError('Completed packets are immutable')
    temporary = Path(tempfile.mkdtemp(prefix='.uncommitted-', dir=directory.parent))
    try:
        arrays = {'canonical_semantic_masks': np.asarray(masks)}
        for key, value in (native_arrays or {}).items():
            array = np.asarray(value)
            if array.dtype.kind not in 'biuf' or not np.isfinite(array).all():
                raise ValueError('Native arrays must be numeric, finite and lossless')
            if not key.isidentifier() or key in arrays:
                raise ValueError('Invalid/duplicate array key')
            arrays[key] = array
        with (temporary / 'arrays.npz').open('xb') as stream:
            np.savez_compressed(stream, **arrays)
            stream.flush(); os.fsync(stream.fileno())
        if fault:
            fault('after_arrays')
        payload = {**record, 'fingerprints': fingerprints, 'array_sha256': file_hash(temporary / 'arrays.npz')}
        with (temporary / 'record.json').open('x') as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        manifest = {'record_sha256': file_hash(temporary / 'record.json'), 'array_sha256': payload['array_sha256']}
        with (temporary / 'COMMITTED.json').open('x') as stream:
            json.dump(manifest, stream); stream.flush(); os.fsync(stream.fileno())
        if fault:
            fault('before_publish')
        # Protocol runner has a single writer. Never use overwrite-style replacement.
        os.rename(temporary, directory)
        descriptor = os.open(directory.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary)  # Only this call's newly created temporary data.
        raise
    return directory


def resume_packet(directory, inference_fingerprint):
    directory = Path(directory)
    manifest = json.loads((directory / 'COMMITTED.json').read_text())
    if manifest['record_sha256'] != file_hash(directory / 'record.json') or manifest['array_sha256'] != file_hash(directory / 'arrays.npz'):
        raise ValueError('Artifact integrity failed; do not reuse partial/corrupted outputs')
    record = json.loads((directory / 'record.json').read_text())
    if record['fingerprints']['inference'] != inference_fingerprint:
        raise ValueError('Inference dependencies changed; cached outputs cannot be reused')
    with np.load(directory / 'arrays.npz', allow_pickle=False) as arrays:
        validate_frame(record, arrays['canonical_semantic_masks'])
    return record  # A changed scoring fingerprint may re-score sufficient native outputs.
