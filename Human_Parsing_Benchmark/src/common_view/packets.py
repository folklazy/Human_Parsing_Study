"""Atomic common-view packets, immutable input references and JSON reporting."""
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from .core import sha_file, validate_prediction, score_packet, aggregate


def atomic_json(path, value):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    with tmp.open('w') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, p)


def fingerprint(binding):
    return hashlib.sha256(json.dumps(binding, sort_keys=True, allow_nan=False).encode()).hexdigest()


def write_packet(root, iid, arrays, metadata, scores):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    target = root / iid
    tmp = root / ('.partial-' + iid)
    if target.exists() or tmp.exists():
        raise FileExistsError('Never overwrite or reuse orphan packet: ' + str(target))
    tmp.mkdir()
    with (tmp / 'prediction.npz').open('wb') as f:
        np.savez_compressed(f, **arrays); f.flush(); os.fsync(f.fileno())
    meta = dict(metadata, packet_sha256=sha_file(tmp / 'prediction.npz'))
    atomic_json(tmp / 'packet.json', meta)
    for t, sc in scores.items():
        atomic_json(tmp / ('score_' + t + '.json'), sc)
    members = {p.name: sha_file(p) for p in tmp.iterdir() if p.is_file()}
    atomic_json(tmp / 'COMMIT.json', {'members': members, 'image_id': iid})
    os.rename(tmp, target)
    fd = os.open(root, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return target


def read_packet(path, expected=None, legacy=False):
    p = Path(path); meta = json.loads((p / 'packet.json').read_text())
    if sha_file(p / 'prediction.npz') != meta['packet_sha256']:
        raise ValueError('NPZ hash mismatch')
    if not legacy:
        commit = json.loads((p / 'COMMIT.json').read_text())
        for name, digest in commit['members'].items():
            if sha_file(p / name) != digest:
                raise ValueError('Atomic packet member hash mismatch: ' + name)
    if expected:
        for k, value in expected.items():
            if meta.get(k) != value:
                raise ValueError('Packet binding mismatch: ' + k)
    with np.load(p / 'prediction.npz', allow_pickle=False) as data:
        arrays = {k: data[k].copy() for k in data.files}
    return meta, arrays


def score_saved_packet(path, category, human, space, spec, expected=None, legacy=False):
    meta, a = read_packet(path, expected, legacy)
    result = {str(t): score_packet(category, human, a['person_semantic_masks'],
                                  a['person_extents'], a['person_scores'], space, spec, t)
              for t in (.5, .75)}
    return {'image_id': meta['image_id'], 'scores': result}


def reporter(path, rows, expected_ids):
    report = aggregate(rows, expected_ids)
    atomic_json(path, report)
    return report
