"""Acquire the author-linked trained CDGNet parser, never backbone-only weights.

No model inference, installation, dataset access, or benchmark execution.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import subprocess
import requests
import gdown

STUDY = Path(__file__).resolve().parents[1]
WORKSPACE = STUDY.parent
FOLDER_ID = '1rzLU-wK6rEorCNJfwrmIu5hY2wRMyKTK'
PARSER_ID = '1X9dWbu1jI8tYEX8T88luP_nI3myoxes-'
BACKBONE_ID = '16LuwD83iColELOZOcQk8o_a5QpDUKzNp'
RUN = STUDY / 'provenance/RUN_MANIFESTS' / ('cdgnet-acquisition-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
RUN.mkdir(parents=True)

def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()

def atomic(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    os.replace(temporary, path)

original_request = requests.sessions.Session.request

def bounded_request(self, *args, **kwargs):
    kwargs.setdefault('timeout', (20, 90))
    return original_request(self, *args, **kwargs)

requests.sessions.Session.request = bounded_request
source = WORKSPACE / 'third_party/human_parsing/CDGNet'
record = {
    'run_id': RUN.name,
    'created_utc': datetime.now(timezone.utc).isoformat(),
    'official_repository': subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=source, text=True).strip(),
    'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(),
    'author_link': 'https://drive.google.com/open?id=' + FOLDER_ID,
    'official_folder': 'https://drive.google.com/drive/folders/' + FOLDER_ID,
    'status': 'DISCOVERING',
    'model_inference': False,
    'full_benchmark': False,
    'code_execution_license': 'UNRESOLVED_PRIOR_CODE_LICENSE_REVIEW; acquisition does not establish execution eligibility',
}
atomic(RUN / 'ACQUISITION.json', record)
atomic(STUDY / 'provenance/CDGNET_ACQUISITION_ACTIVE.json', {'run': str(RUN.relative_to(STUDY))})
try:
    members = gdown.download_folder(id=FOLDER_ID, skip_download=True, quiet=True, use_cookies=False)
    record['folder_members'] = [{'file_id': member.id, 'filename': member.path} for member in members]
    assert any(member.id == PARSER_ID and member.path == 'LIP_epoch_149.pth' for member in members)
    assert any(member.id == BACKBONE_ID and member.path == 'resnet101-imagenet.pth' for member in members)
    for member in record['folder_members']:
        url = 'https://drive.google.com/file/d/' + member['file_id'] + '/view'
        response = requests.get(url)
        response.raise_for_status()
        metadata = json.JSONDecoder().raw_decode(response.text.split('itemJson: ', 1)[1])[0]
        assert metadata[1] == member['filename']
        member.update(source_url=url, expected_bytes=int(metadata[25][2]))
    target = next(member for member in record['folder_members'] if member['file_id'] == PARSER_ID)
    free = shutil.disk_usage(WORKSPACE).free
    record.update(free_bytes_before=free, planned_download_bytes=target['expected_bytes'],
                  backbone_action='NOT_DOWNLOADED_NOT_REQUIRED_BY_OFFICIAL_EVALUATION_PATH')
    if free < 2 * target['expected_bytes'] + 5 * 1024**3:
        raise RuntimeError('Insufficient disk headroom')
    destination = WORKSPACE / 'models/human_parsing/cdgnet/CDGNet_R101_LIP/LIP_epoch_149.pth'
    destination.parent.mkdir(parents=True, exist_ok=True)
    record['destination'] = str(destination.relative_to(WORKSPACE))
    if destination.exists():
        assert destination.stat().st_size == target['expected_bytes']
        record['acquisition'] = 'REUSED_EXISTING'
    else:
        # Google Drive IDs are mutable: never resume unbound content from an older version.
        temporary = destination.with_name(destination.name + '.' + RUN.name + '.part')
        record['status'] = 'DOWNLOADING'
        atomic(RUN / 'ACQUISITION.json', record)
        print('CDGNet parser download:', target['expected_bytes'], 'bytes', flush=True)
        downloaded = gdown.download(id=PARSER_ID, output=str(temporary), quiet=True, use_cookies=False, resume=False)
        if not downloaded or temporary.stat().st_size != target['expected_bytes']:
            raise ValueError('Incomplete or incorrect-size checkpoint')
        record['sha256'] = sha(temporary)
        os.rename(temporary, destination)
        record['acquisition'] = 'NEW_DOWNLOAD'
    record.update(status='DOWNLOADED_SIZE_AND_SHA256_VERIFIED', bytes=destination.stat().st_size,
                  sha256=sha(destination), author_checksum=None,
                  checksum_interpretation='Local content fingerprint; provenance from author-linked Drive folder',
                  torch_loaded=False, model_loaded=False, inference_status='NOT_TESTED')
except Exception as error:
    record.update(status='ACQUISITION_FAILED', error_type=type(error).__name__, error=str(error))
finally:
    record['completed_utc'] = datetime.now(timezone.utc).isoformat()
    atomic(RUN / 'ACQUISITION.json', record)
    print(json.dumps(record, ensure_ascii=False, indent=2), flush=True)
if record['status'] == 'ACQUISITION_FAILED':
    raise SystemExit(1)
