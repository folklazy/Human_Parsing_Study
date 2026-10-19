"""Create a fresh, dataset-free review ZIP and test its isolated CPU closure."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
from importlib.metadata import version
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

STUDY = Path(__file__).resolve().parents[1]
WORKSPACE = STUDY.parent
SUITES = ['test_application_v2.py', 'test_mhpv2_stage0.py', 'test_ccihp_gt.py', 'test_ccihp_quality.py']
TEXT_EXTENSIONS = {'.py', '.json', '.jsonl', '.csv', '.yaml', '.yml', '.md', '.txt'}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = STUDY / 'outputs/handoff' / ('cpu_review_' + stamp)
    contents = out / 'contents'; contents.mkdir(parents=True, exist_ok=False)
    files = set()

    def select(path, recursive=False):
        candidates = path.rglob('*') if recursive else [path]
        for file in candidates:
            if ('ppss' in str(file.relative_to(WORKSPACE)).lower() or '__pycache__' in file.parts
                    or file.is_symlink() or not file.is_file() or file.suffix not in TEXT_EXTENSIONS):
                continue
            files.add(file)

    for folder in ['src', 'tests', 'scripts', 'configs', 'taxonomy', 'manifests', 'env_specs']:
        select(STUDY / folder, recursive=True)
    for path in STUDY.glob('*.md'): select(path)
    select(STUDY / 'STUDY_STATE.json')
    for path in (STUDY / 'provenance').iterdir():
        if path.is_file(): select(path)
    for path in (STUDY / 'reports').glob('*.md'): select(path)

    active = json.loads((STUDY / 'provenance/APPLICATION_V2_IMPLEMENTATION_ACTIVE.json').read_text())
    run = STUDY / active['run_path']
    for folder in ['gt_sidecars', 'mhp_native_sidecars', 'historical_execution_snapshots']:
        select(run / folder, recursive=True)
    for name in ['BEFORE.json', 'FINAL_VALIDATION_POINTER.json', 'FINAL_NATIVE_ASSOCIATION_POINTER.json',
                 'EXISTING_PILOT_RESOURCE_REFERENCES.json']: select(run / name)
    final = json.loads((STUDY / 'provenance/APPLICATION_V2_IMPLEMENTATION_FINAL.json').read_text())
    select((STUDY / final['evidence']).parent, recursive=True)
    validation_pointer = json.loads((run / 'FINAL_VALIDATION_POINTER.json').read_text())
    validation = STUDY / validation_pointer['validation']; select(validation)
    for row in json.loads(validation.read_text())['regression_suites']:
        select(STUDY / row['log'])  # .log omitted: original test counts remain in JSON evidence.
    for name in ['HUMAN_PARSING_BENCHMARK_PROTOCOL_20_VARIANTS_V2_TH_20261014.md',
                 'BENCHMARK_PROTOCOL_20_VARIANTS_V2_DECISIONS_APPENDIX_TH_20261014.md',
                 'BENCHMARK_PROTOCOL_V2_IMPLEMENTATION_HANDOFF_TH_20261014.md']:
        select(WORKSPACE / name)
    pilot = WORKSPACE / 'Human_Parsing_CCIHP_10_Image_Pilot'
    for name in ['taxonomy/NATIVE_CLASS_INVENTORY.json', 'metrics/MODEL_PILOT_STATUS.csv']:
        select(pilot / name)
    registry = pilot / 'metrics/MODEL_PILOT_STATUS.csv'
    for row in csv.DictReader(registry.open()):
        if row['run_manifest']: select(pilot / row['run_manifest'])  # metadata only, no prediction arrays.
    original_hashes = {}
    for path in sorted(files):
        relative = path.relative_to(WORKSPACE)
        target = contents / relative; target.parent.mkdir(parents=True, exist_ok=True)
        before = sha(path); shutil.copyfile(path, target)
        if sha(target) != before: raise ValueError('Source changed during copy')
        original_hashes[str(relative)] = before

    package = contents / STUDY.name
    deps = {name: version(name) for name in ['numpy', 'scipy', 'Pillow', 'PyYAML']}
    (package / 'requirements-cpu-handoff.txt').write_text(''.join(f'{name}=={value}\n' for name, value in deps.items()))
    readme = '''# CPU review handoff — Application V2

ชุดนี้สำหรับตรวจตารางคลาส กติกา GT และแก้ evaluator/fixtures บน CPU โดยต่อจาก implementation เดิม ไม่ใช่การอนุมัติ freeze หรือ full benchmark

## เริ่มอ่าน

1. `reports/APPLICATION_V2_IMPLEMENTATION_TH.md` — สถานะล่าสุด/ข้อจำกัด
2. `configs/application_v2.yaml` + `provenance/APPLICATION_V2_DECISIONS_V2.json` — accepted bindings กับ proposed policies
3. `taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V1.json`, `APPLICATION_CCIHP_NATIVE_DIAGNOSTIC_V1.json` และ native label inventories
4. `src/application_v2/{taxonomy,evaluation,contracts,policy,runner,artifacts}.py` + `tests/test_application_v2.py`
5. `provenance/RUN_MANIFESTS/application-v2-implementation-20261014T091346536200Z/{gt_sidecars,mhp_native_sidecars}/MANIFEST.json` — population/support counts และ per-person metadata

Candidate common mapping ยัง DRAFT และเป็น CIHP/LIP cohort ไม่ใช่ universal taxonomy ของทุก variants ห้ามเปลี่ยน proposed เป็น accepted โดยไม่มี decision record ที่รองรับ Native CCIHP ไม่ใช่ original CIHP GT และ structural Human IDs ไม่รับรอง physical-person correctness ทุกกรณี

## รัน CPU tests

ใช้ Python 3.10 ซึ่งเป็นรุ่นที่ตรวจในเครื่องต้นทาง dependencies ระบุใน `requirements-cpu-handoff.txt` ไม่มี PyTorch/CUDA requirement สำหรับสี่ชุดนี้ การติดตั้งในเครื่องปลายทางเป็นขั้นตอนของผู้รับ ชุดส่งต่อนี้ไม่ได้ติดตั้งอะไรเพิ่ม

จากโฟลเดอร์ `Human_Parsing_MHPv2_Study` หลังแตก ZIP:

```bash
python -m unittest discover -s tests -p test_application_v2.py -v
python -m unittest discover -s tests -p test_mhpv2_stage0.py -v
python -m unittest discover -s tests -p test_ccihp_gt.py -v
python -m unittest discover -s tests -p test_ccihp_quality.py -v
```

สี่ suites รวม 83 tests ตรวจแล้วจากชุดแตก ZIP แยกจาก workspace จริง ไม่โหลดโมเดลหรือ dataset ต้นฉบับ สิ่งนี้ต่างจาก historical 109-test workspace regression: อีก 19 official-MHP tests ต้องมี pinned third-party evaluator และอีก 7 population tests ต้องมี original dataset split lists ซึ่งไม่ได้แนบมา ห้ามเรียกว่าผ่านทั้ง 109 จากชุดนี้

ไม่ใช้ `validate_application_v2.py --all` ใน ZIP เป็นคำสั่ง portable เพราะตรวจ protected files/packets ใน original workspace ด้วย การ regenerate sidecars, saved prediction replay, live parser และ joint GPU resource profiles ต้องทำใน server โครงการเดิม

## สิ่งที่รวมและขอบเขต

- โค้ด/config/tests/scripts/taxonomy และ decision records เป็นสำเนา bytes เดิม
- GT sidecars เป็น JSONL metadata พร้อม original source hashes ไม่มี RGB หรือ GT mask pixels
- Pilot native class inventory, model registry และ RUN.json/resource metadata แนบไว้ โดยไม่แนบ checkpoint หรือ prediction NPZ
- `SOURCE_FILES_SHA256.json` ระบุ source files ที่คัดลอก; `BUNDLE_FILES_SHA256.json` ระบุทุก payload นอกตัว inventory เอง
- มี `EXTERNAL_DEPENDENCIES.json` แยกไฟล์ที่ยังอยู่นอก ZIP อย่าถือว่าทุกลิงก์ historical ในรายงานพา asset นั้นมาด้วย
- ไม่มี weights, dataset archives/images/masks, virtual environments, large predictions หรือ PPSS assets ไม่มี inference/download/install ในการสร้างชุดนี้

ข้ออนุญาต bounded GPU ใน config เป็นบริบทของ run เดิมบน server ไม่ใช่คำสั่งให้ผู้รับรัน GPU/full benchmark ตารางคลาส/GT/evaluator ที่แก้ต้อง version ให้ชัดและเพิ่ม actual-code fixtures ก่อนขอ freeze review
'''
    (package / 'HANDOFF_README_TH.md').write_text(readme)
    external = {'scope': 'REVIEW_AND_CPU_FIXTURES_ONLY', 'missing_by_design': [
        {'asset': 'datasets/', 'needed_for': 'Original RGB/GT reinspection and dataset-dependent tests'},
        {'asset': 'models/ and .venv/.venvs/', 'needed_for': 'Model/GPU inference; no runtime permission inferred'},
        {'asset': 'third_party/human_parsing/Multi-Human-Parsing/Evaluation/Multi-Human-Parsing/v2/',
         'needed_for': 'Pinned original official-MHP compatibility tests'},
        {'asset': 'pilot outputs/*.npz and completed application packet arrays.npz',
         'needed_for': 'Saved prediction replay and full workspace artifact validation'},
        {'asset': 'historical GT visualizations and complete audit per-file ledgers',
         'needed_for': 'Pixel/physical-ownership inspection, not metadata-only scoring fixtures'}],
        'portable_suites': SUITES, 'original_config_and_accepted_decisions_modified': False}
    (package / 'EXTERNAL_DEPENDENCIES.json').write_text(json.dumps(external, indent=2) + '\n')
    (package / 'SOURCE_FILES_SHA256.json').write_text(json.dumps(original_hashes, indent=2) + '\n')
    payload_hashes = {str(path.relative_to(contents)): sha(path) for path in sorted(contents.rglob('*')) if path.is_file()}
    (package / 'BUNDLE_FILES_SHA256.json').write_text(json.dumps(payload_hashes, indent=2) + '\n')
    archive = out / ('Human_Parsing_MHPv2_CPU_Review_' + stamp + '.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
        for path in sorted(contents.rglob('*')):
            if path.is_file(): zipped.write(path, path.relative_to(contents).as_posix())
    extracted = out / 'isolated_zip_check'; extracted.mkdir()
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None: raise ValueError('Created ZIP integrity failed')
        for entry in zipped.infolist():
            if Path(entry.filename).is_absolute() or '..' in Path(entry.filename).parts: raise ValueError('Unsafe generated ZIP member')
        zipped.extractall(extracted)
    for relative, expected in payload_hashes.items():
        if sha(extracted / relative) != expected: raise ValueError('Extracted byte hash differs')
    results = []; env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}; env.pop('PYTHONPATH', None)
    for pattern in SUITES:
        done = subprocess.run([sys.executable, '-I', '-m', 'unittest', 'discover', '-s', 'tests', '-p', pattern, '-q'],
                              cwd=extracted / STUDY.name, env=env, capture_output=True, text=True, timeout=120)
        # -I excludes cwd: tests with older imports require an explicit local path.
        if done.returncode and 'No module named \'src\'' in done.stderr:
            bootstrap = 'import sys,unittest;sys.path.insert(0,".");r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover("tests",pattern=sys.argv[1]));sys.exit(not r.wasSuccessful())'
            done = subprocess.run([sys.executable, '-I', '-c', bootstrap, pattern], cwd=extracted / STUDY.name,
                                  env=env, capture_output=True, text=True, timeout=120)
        log = out / (pattern + '.log'); log.write_text(done.stdout + done.stderr)
        count = re.search(r'Ran (\d+) tests?', done.stdout + done.stderr)
        if done.returncode or not count: raise RuntimeError(f'Isolated package test failed: {pattern}: {done.stderr}')
        results.append({'suite': pattern, 'tests_passed': int(count[1]), 'log': log.name, 'log_sha256': sha(log)})
    for relative, expected in original_hashes.items():
        if sha(WORKSPACE / relative) != expected: raise ValueError('Original file changed during packaging')
    result = {'status': 'PASS_ISOLATED_CPU_REVIEW_BUNDLE', 'archive': str(archive.relative_to(WORKSPACE)),
              'bytes': archive.stat().st_size, 'sha256': sha(archive), 'copied_source_files': len(original_hashes),
              'payload_files': len(payload_hashes) + 1, 'tests': results, 'tests_passed': sum(r['tests_passed'] for r in results),
              'python': sys.version, 'dependencies': deps, 'original_files_unchanged': True,
              'inference_run': False, 'dataset_included': False, 'weights_included': False,
              'PPSS_assets_included': False, 'scientific_policy_modified': False, 'downloads_or_installs': False}
    (out / 'BUNDLE_VALIDATION.json').write_text(json.dumps(result, indent=2) + '\n')
    (out / (archive.name + '.sha256')).write_text(result['sha256'] + '  ' + archive.name + '\n')
    print(json.dumps(result))


if __name__ == '__main__': main()
