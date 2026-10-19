"""Prepare an explicit local publication candidate; never create a remote or run models."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import re
import shutil
import subprocess

STUDY = Path(__file__).resolve().parents[1]
WORKSPACE = STUDY.parent
DEST = WORKSPACE / 'Human_Parsing_Study_Public'
RUN = Path('provenance/RUN_MANIFESTS/first-cohort-benchmark-20261016T094257313856Z')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def main():
    if DEST.exists():
        raise SystemExit('Use the existing candidate; this builder never replaces it.')
    final = json.loads((STUDY / RUN / 'FINAL_BENCHMARK_VALIDATION.json').read_text())
    assert final['status'] == 'FINISHED_WITH_INCOMPLETE_SYSTEMS'
    assert (STUDY / RUN / 'CONTINUATION_FINALIZATION_STATUS.json').is_file()
    DEST.mkdir()
    copied, excluded = {}, {}
    def copy(relative):
        relative = Path(relative)
        p = (STUDY / relative).resolve()
        if not p.is_relative_to(STUDY) or not p.is_file() or p.is_symlink():
            return False
        name = str(relative)
        if name in copied:
            return False
        lower = name.lower()
        if 'ppss' in lower:
            return False
        if name == 'provenance/MODEL_SOURCE_AUDIT.json':
            excluded[name] = 'Raw historical HTTP/cookie headers retained privately; scientific source identities are recorded separately'
            return False
        if '/local_sources/' in lower or '/sources/' in lower or '/reference_fixtures/' in lower:
            excluded[name] = 'Paused PPSS or third-party/source dataset content retained externally'
            return False
        if p.suffix.lower() not in {'.py', '.json', '.jsonl', '.yaml', '.yml', '.csv', '.md', '.txt', '.log'}:
            excluded[name] = 'External image/mask/weight/binary artifact'
            return False
        if p.name in {'PERSON_GT_BINDINGS.jsonl', 'IMAGE_BINDINGS.jsonl', 'FRAMES.jsonl', 'PRIMARY_FRAME_SCORES.jsonl', 'SECONDARY_FRAME_SCORES.jsonl', 'PRIMARY_FRAME_SCORES.json', 'SECONDARY_FRAME_SCORES.json'} or p.stat().st_size > 2_000_000:
            excluded[name] = 'Bulk artifact or detailed GT annotation bindings; source hash retained, no redistribution grant inferred'
            return False
        if any(x in relative.parts for x in ['packets', 'predictions', 'outputs', '__pycache__']):
            excluded[name] = 'Bulk output or cache retained externally'
            return False
        out = DEST / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, out)
        copied[name] = dict(source_path=name, public_path=name, bytes=p.stat().st_size, sha256=sha(p), transformation='BYTE_IDENTICAL_COPY')
        return True
    for directory in ['src', 'tests', 'scripts', 'configs', 'taxonomy', 'env_specs']:
        for p in (STUDY / directory).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                copy(p.relative_to(STUDY))
    for p in (STUDY / 'reports').glob('*.md'):
        copy(p.relative_to(STUDY))
    for p in (STUDY / 'provenance').iterdir():
        if p.is_file():
            copy(p.relative_to(STUDY))
    for p in (STUDY / 'manifests').iterdir():
        if p.is_file():
            copy(p.relative_to(STUDY))
    for p in (STUDY / RUN).iterdir():
        if p.is_file():
            copy(p.relative_to(STUDY))
    for part in ['execution/CPI_R50_CIHP/RUN.json', 'continuation_20261019/CPI_ConvNeXtB_CIHP_COMBINED/RUN.json',
                 'execution_restored_detector_v1/YOLO26X_FROZEN/RUN.json', 'execution_restored_detector_v1/BENCHMARK_EXECUTION.json',
                 'execution_restored_detector_v1/MAIN_PRIMARY_REPORT.json', 'execution_restored_detector_v1/MAIN_SECONDARY_REPORT.json',
                 'execution_restored_detector_v1/REFERENCE_PRIMARY_REPORT.json', 'execution_restored_detector_v1/REFERENCE_SECONDARY_REPORT.json']:
        copy(RUN / part)
    for p in (STUDY / 'metrics' / RUN.name).iterdir():
        copy(p.relative_to(STUDY))
    for name in ['RESEARCH_SCOPE.md', 'REFERENCES.md']:
        copy(name)
    # Preserve previous landing/schema/standard documents without rewriting their historical assertions.
    for name in ['README.md', 'STUDY_STANDARD.md', 'DATA_SCHEMA.md', 'REPRODUCIBILITY.md', 'EXPERIMENT_PROTOCOL_DRAFT.md', 'STUDY_STATE.json']:
        p = STUDY / name; out = DEST / 'reports/archive/pre_public_snapshot' / name
        out.parent.mkdir(parents=True, exist_ok=True);shutil.copyfile(p, out)
        copied['archive:' + name] = dict(source_path=name, public_path=str(out.relative_to(DEST)), bytes=p.stat().st_size, sha256=sha(p), transformation='BYTE_IDENTICAL_ARCHIVE')
    # Resolve small metadata references without collecting raw GT or prediction arrays.
    pattern = re.compile(r'(?:provenance|reports|manifests|configs|taxonomy|scripts|src|env_specs)/[A-Za-z0-9_./+\-]+\.(?:jsonl|json|yaml|yml|csv|md|txt|py|log)')
    queue = list(copied.values()); seen = set()
    while queue:
        row = queue.pop(); name = row['public_path']
        if name in seen: continue
        seen.add(name)
        text = (DEST / name).read_text(errors='replace')
        for target in set(pattern.findall(text)):
            if copy(target): queue.append(copied[target])
    # Public output metadata lists external paths; it does not redistribute dataset-derived pixel annotations.
    external = []
    for name, reason in sorted(excluded.items()):
        p = STUDY / name
        if p.is_file():
            external.append(dict(path=name, bytes=p.stat().st_size, sha256=sha(p), reason=reason,
                                 public_download_url=None, availability='LOCAL_CUSTODIAN_ONLY_OR_REBUILD_WITH_AUTHORIZED_ASSETS'))
    write(DEST / 'publication/SOURCE_COPY_MANIFEST.json', dict(schema_version='1.0', source_root_role='ORIGINAL_NON_GIT_WORKING_COPY',
          original_working_copy_workspace_relative=STUDY.name, candidate_workspace_relative=DEST.name,
          snapshot_type='POST_RUN_SNAPSHOT_NOT_LAUNCH_COMMIT', created_utc=datetime.now(timezone.utc).isoformat(), files=list(copied.values())))
    write(DEST / 'publication/EXTERNAL_ARTIFACTS.json', dict(no_public_artifact_host_created=True, files=external))
    write(DEST / 'publication/PUBLICATION_STATE.json', dict(status='LOCAL_CANDIDATE_PUBLICATION_NOT_AUTHORIZED',
          proposed_owner='folklazy', proposed_repository='Human_Parsing_Study', proposed_visibility='public',
          remote_created=False, public_url=None, publish_approval_required=True, full_benchmark_authorized=False))
    baseline=[]
    for directory in sorted(WORKSPACE.glob('YOLO*')):
        if (directory/'.git').exists():
            result=subprocess.run(['git','status','--porcelain'],cwd=directory,capture_output=True,text=True,check=True)
            baseline.append(dict(repository=directory.name,status=result.stdout,
                head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=directory,text=True).strip()))
    write(DEST / 'publication/YOLO_READ_ONLY_BASELINE.json',baseline)
    print(json.dumps(dict(candidate=str(DEST),copied_files=len(copied),external_entries=len(external),remote_created=False)))


if __name__ == '__main__':
    main()
