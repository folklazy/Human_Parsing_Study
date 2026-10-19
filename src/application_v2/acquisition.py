"""Completeness is an artifact-set property, never a filename/status shortcut."""
from pathlib import Path
from .artifacts import file_hash


def verify_asset_set(root, required_files):
    root=Path(root).resolve()
    if not required_files:
        raise ValueError('A required artifact set must be declared')
    names=[r['path'] for r in required_files]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate artifact paths')
    rows=[]
    for entry in required_files:
        p=(root/entry['path']).resolve()
        if not p.is_relative_to(root) or not p.is_file() or p.name.endswith('.part'):
            raise ValueError('Missing, partial, or unsafe required artifact')
        if p.stat().st_size != entry['bytes'] or file_hash(p) != entry['sha256']:
            raise ValueError('Required artifact size/hash mismatch')
        rows.append(dict(path=entry['path'],sha256=entry['sha256'],bytes=entry['bytes']))
    return {'status':'VERIFIED_COMPLETE_DECLARED_SET','files':rows,
            'unique_content_artifacts':len(set(r['sha256'] for r in rows)),
            'author_authenticity':'NOT_ESTABLISHED_BY_LOCAL_SHA256_ALONE'}
