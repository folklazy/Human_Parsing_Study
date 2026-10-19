"""Record the reviewed Decision 5A evidence; never download assets or run models.

Assessment strings are reviewed findings, not an automated legal clearance system.
Source snapshots remain pinned to their original collection dates.
"""
from pathlib import Path
import csv
import difflib
import hashlib
import io
import json
import shutil
import struct
import subprocess
from datetime import datetime, timezone

import numpy as np
from PIL import Image, ImageFile
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
NOW = datetime.now(timezone.utc)
RUN_ID = 'decision5a-license-finalization-' + NOW.strftime('%Y%m%dT%H%M%SZ')
RUN = ROOT / 'provenance' / 'RUN_MANIFESTS' / RUN_ID
RUN.mkdir(parents=True, exist_ok=False)
OLD_RUN = ROOT / 'provenance/RUN_MANIFESTS/decision5a-license-review-20261008T105228Z'
ARCHIVE = ROOT / 'reports/archive' / RUN_ID
REVISIONS = []
CREATED = []


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def publish(relative, text, reason='Record clarified academic scope and current license assessment'):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_bytes() if path.exists() else None
    new = text.encode('utf-8')
    if old == new:
        return
    if old is not None:
        backup = ARCHIVE / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        with backup.open('xb') as f:
            f.write(old)
        diff = ''.join(difflib.unified_diff(old.decode().splitlines(True), text.splitlines(True),
                                           fromfile=relative + ' BEFORE', tofile=relative + ' AFTER'))
        backup.with_name(backup.name + '.diff').write_text(diff)
        REVISIONS.append(dict(original_relative=relative, archived_relative=str(backup.relative_to(ROOT)),
                              sha256_before=hashlib.sha256(old).hexdigest(), sha256_after=hashlib.sha256(new).hexdigest(),
                              reason=reason, timestamp_utc=NOW.isoformat()))
    else:
        CREATED.append(relative)
    temp = path.with_name(path.name + '.tmp-' + RUN_ID)
    with temp.open('xb') as f:
        f.write(new)
    temp.replace(path)


def write_json(relative, value):
    publish(relative, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_csv(relative, rows):
    out = io.StringIO(newline='')
    w = csv.DictWriter(out, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    publish(relative, out.getvalue())


old_before = json.loads((OLD_RUN / 'BEFORE.json').read_text())
assert all(sha(ROOT / p) == h for p, h in old_before['hashes_before'].items()), 'Concurrent changes: review before editing'
write_json(str((RUN / 'RESUME.json').relative_to(ROOT)), {
    'run_id': RUN_ID, 'resumed_utc': NOW.isoformat(), 'prior_review_run': str(OLD_RUN.relative_to(ROOT)),
    'prior_documents_unchanged_since_interruption': True, 'execution_authorized': False,
    'purpose': 'Decision 5A license/scope documentation and read-only smoke-input preparation only'})

# Capture actual source revisions and local license documents without executing repositories.
local_sources = []
repo_names = {'M2FP': 'soeaver/M2FP', 'CPI-Parser': 'HAG-uestc/CPI-Parser',
              'D2FP': 'cvlab-yongin/D2FP', 'SCHP': 'GoGoDuck912/Self-Correction-Human-Parsing',
              'fashn-human-parser': 'fashn-AI/fashn-human-parser'}
for folder, remote in repo_names.items():
    path = WORKSPACE / 'third_party/human_parsing' / folder
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path, text=True).strip()
    status = subprocess.check_output(['git', 'status', '--short'], cwd=path, text=True).strip()
    for filename in ['LICENSE', 'README.md']:
        source = path / filename
        target = RUN / 'local_sources' / folder / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        local_sources.append(dict(method=folder, repository='https://github.com/' + remote,
                                  source_commit=commit, git_status=status, source_workspace_relative=str(source.relative_to(WORKSPACE)),
                                  snapshot=str(target.relative_to(ROOT)), sha256=sha(source)))
write_json(str((RUN / 'LOCAL_SOURCE_MANIFEST.json').relative_to(ROOT)), local_sources)
sources = json.loads((OLD_RUN / 'sources/SOURCE_MANIFEST.json').read_text())
for row in sources.values():
    if row.get('snapshot'):
        assert sha(ROOT / row['snapshot']) == row['sha256']

scope = {
    'schema_version': '1.0', 'decision_id': '5A', 'decision_source': 'Explicit user clarification; continuation authorizes documentation only',
    'recorded_utc': NOW.isoformat(), 'intended_use': 'NONCOMMERCIAL_ACADEMIC_RESEARCH_EVALUATION',
    'independent_student_research': True, 'company_rd': False, 'commercial_product_development': False,
    'objective': 'Compare pretrained human parsing for body/clothing/supported accessories',
    'company_cctv': {'role': 'LATER_FINALIST_RESEARCH_EVALUATION_DATA_ONLY', 'provision_implies_sponsorship': False,
                    'owner_permission': 'NOT_VERIFIED_IN_THIS_REVIEW', 'privacy_safeguards': 'REQUIRED_BEFORE_LATER_FIELD_TEST',
                    'inference_authorized_now': False},
    'commercial_deployment': 'OUT_OF_SCOPE_SEPARATE_FUTURE_LICENSE_REVIEW',
    'academic_status_overrides_explicit_restrictions': False,
    'sapiens2': 'LICENSE_BLOCKED_PENDING_APPLICABLE_SURVEILLANCE_RESEARCH_PERMISSION',
    'ppss': 'PAUSED_DO_NOT_ACCESS', 'common_taxonomy': 'DRAFT_NOT_FROZEN',
    'fashn_checkpoint_download_authorized': False, 'fashn_checkpoint_inference_authorized': False,
    'heavyweight_dependency_install_authorized': False, 'full_benchmark_authorized': False,
    'stage1_authorized': False, 'training_authorized': False, 'hybrid_authorized': False}
publish('configs/research_scope.yaml', yaml.safe_dump(scope, allow_unicode=True, sort_keys=False))
publish('RESEARCH_SCOPE.md', '''# ขอบเขตงานวิจัย — Decision 5A

**NONCOMMERCIAL ACADEMIC RESEARCH / EVALUATION** — งานวิจัยอิสระของนักศึกษาเพื่อเปรียบเทียบ pretrained human parsing สำหรับ body/clothing/accessories ที่โมเดลรองรับ ผู้ใช้ยืนยันขอบเขตนี้โดยตรง งานพัฒนาผลิตภัณฑ์เชิงพาณิชย์และ company R&D อยู่นอกขอบเขตปัจจุบัน

ภาพ CCTV จากบริษัทเป็นข้อมูลสำหรับประเมิน finalist ในงานวิจัยภายหลัง การให้ข้อมูลเพียงอย่างเดียวไม่ได้ยืนยันการสนับสนุนเชิงพาณิชย์หรือการพัฒนาผลิตภัณฑ์ ต้องมีสิทธิ์จากเจ้าของข้อมูลและมาตรการความเป็นส่วนตัวที่เหมาะสมก่อน field test; รอบนี้ยังไม่ตรวจภาพหรือรัน CCTV inference

สถานะ academic ไม่ยกเว้นข้อห้ามเฉพาะของ license ตรวจ code, checkpoint, dependency และ dataset แยกกัน Sapiens2 ยัง blocked เพราะข้อห้ามครอบคลุม surveillance-related research ด้วย การเปลี่ยนภาพ smoke เป็น public dataset ไม่ได้ลบ intended-use restriction ของการศึกษานี้

FASHN เข้าเงื่อนไข research/evaluation ใน terms ที่ตรวจ แต่ **ยังไม่อนุมัติ checkpoint download หรือ inference** การอนุมัติ readable MHP-v2 views และคำสั่งให้ทำงานต่อไม่ใช่การอนุมัติ weights หรือ GPU execution ไม่มีการนำ budget 8 GB ที่เคยเสนอมาใช้เป็น permission

การใช้เชิงพาณิชย์ในอนาคตต้องตรวจสิทธิ์ใหม่ ไม่รับรอง commercial deployment จากผลการประเมินรอบนี้ CIHP/MHP-v2 roles และ common taxonomy ยัง draft; PPSS paused; full benchmark, Stage 1, training, fusion และ color study ยังไม่อนุมัติ

[ขอบเขต machine-readable](configs/research_scope.yaml), [รายงานตรวจสิทธิ์](reports/LICENSE_ELIGIBILITY_REASSESSMENT.md), [license matrix](provenance/LICENSE_MATRIX_DECISION5A_V1.csv), [ข้อเสนอ FASHN smoke](manifests/FASHN_SMOKE_PROPOSAL_V2.json)
''')

matrix = []


def entry(name, component, license_name, status, evidence, conditions, unresolved='', revision=''):
    matrix.append(dict(candidate=name, component=component, declared_license=license_name,
                       academic_5a_status=status, evidence=evidence, revision=revision,
                       conditions=conditions, unresolved=unresolved, download_execution_authorized=False,
                       commercial_deployment_assessed=False))


method_status = {
    'M2FP': 'ACADEMIC_RESEARCH_CONDITIONAL_WEIGHT_LICENSE_APPLICABILITY',
    'CPI-Parser': 'ACADEMIC_RESEARCH_CONDITIONAL_WEIGHT_LICENSE_APPLICABILITY',
    'D2FP': 'ACADEMIC_RESEARCH_CONDITIONAL_WEIGHT_AND_INHERITED_NOTICES',
    'SCHP': 'ACADEMIC_RESEARCH_CONDITIONAL_WEIGHT_LICENSE_APPLICABILITY',
    'fashn-human-parser': 'RESEARCH_LICENSE_COMPATIBLE_EXECUTION_APPROVAL_PENDING',
    'SAPIENS2_0_4B': 'LICENSE_BLOCKED_PENDING_APPLICABLE_PERMISSION',
    'QANet': 'OPTIONAL_RESEARCH_CONDITIONAL_WEIGHT_LICENSE_APPLICABILITY',
    'RP-R-CNN': 'OPTIONAL_RESEARCH_CONDITIONAL_WEIGHT_LICENSE_APPLICABILITY',
    'CDGNet': 'CODE_LICENSE_UNSPECIFIED_REVIEW_REQUIRED'}
conditions = 'Retain applicable attribution, copyright, license and modification notices; research scope only in this assessment'
for name, license_name in [('M2FP', 'Predominantly CC-BY-NC-4.0'), ('CPI-Parser', 'Apache-2.0'),
                           ('D2FP', 'Local MIT; inherited M2FP/Facebook notices require per-file review'), ('SCHP', 'MIT')]:
    source = next(x for x in local_sources if x['method'] == name and x['source_workspace_relative'].endswith('/LICENSE'))
    entry(name, 'CODE', license_name, 'ACADEMIC_SCOPE_COMPATIBLE_SUBJECT_TO_NOTICES', source['snapshot'], conditions,
          'D2FP inherited-file attribution/license scope not completely resolved' if name == 'D2FP' else '', source['source_commit'])
    readme = next(x for x in local_sources if x['method'] == name and x['source_workspace_relative'].endswith('/README.md'))
    entry(name, 'CHECKPOINT', 'Official release linked; separate explicit weight scope not established', method_status[name],
          readme['snapshot'] + ('; ' + sources['d2fp_release']['snapshot'] if name == 'D2FP' else ''),
          'Record applicability of release/project license to the selected asset before execution; do not infer blanket restrictions or permission from public access',
          'No separate terms found is uncertainty, not proof that every weight is prohibited', source['source_commit'])
entry('FASHN', 'CODE', 'Wrapper requires compliance with NVIDIA SegFormer terms', method_status['fashn-human-parser'],
      next(x['snapshot'] for x in local_sources if x['method'] == 'fashn-human-parser' and x['source_workspace_relative'].endswith('/LICENSE')),
      'Research/evaluation only; retain SegFormer license and notices', revision='f2771f2fb8655349e87e2869bbde7ace0bd06f2c')
entry('FASHN', 'CHECKPOINT', 'NVIDIA Source Code License for SegFormer inherited by official model card', method_status['fashn-human-parser'],
      sources['fashn_model_card']['snapshot'] + '; ' + sources['segformer_license']['snapshot'],
      'Section 3.3 research/evaluation; sections 3.1-3.2 notices and derivative limitations; no commercial clearance',
      'Actual checkpoint absent; T4 FP32 model feasibility untested; proprietary training-data composition/overlap unknown',
      '1f80c34dbab321c5730dda5c3fea279fd3e97498')
for component in ['CODE', 'CHECKPOINT']:
    entry('Sapiens2-0.4B', component, 'Sapiens2 custom license', method_status['SAPIENS2_0_4B'], sources['sapiens2_license']['snapshot'],
          'Section 1(b)(vi)(i): surveillance including related research/development prohibited; academic status does not override',
          'Applicable express permission not documented; no model download or execution', '7e5bae88456ac418ff0e58e74106c9fe192055d4')
for name, key in [('QANet', 'qanet_license'), ('RP-R-CNN', 'rprcnn_license')]:
    entry(name, 'CODE', 'MIT', 'OPTIONAL_CODE_RESEARCH_COMPATIBLE', sources[key]['snapshot'], conditions)
    entry(name, 'CHECKPOINT', 'Scope not separately established', method_status[name], 'provenance/MODEL_VARIANT_REGISTRY_V2.csv',
          'Metadata only; do not automatically install/download', 'Selected checkpoint terms and dependency stack not audited')
entry('CDGNet', 'CODE_AND_CHECKPOINT', 'License not established in inspected pinned tree', method_status['CDGNet'],
      str((OLD_RUN / 'sources/CDGNET_TREE.json').relative_to(ROOT)), 'Review explicit grant before executable roster; public repository is not permission',
      'No LICENSE/COPYING/NOTICE found; other possible grant not verified', '9daf7ddee6045c151c90a2e300946ea5f5717591')

deps = json.loads((OLD_RUN / 'INSTALLED_DEPENDENCY_LICENSES.json').read_text())
for row in deps:
    if not row['installed']:
        continue
    expr = row.get('license_expression') or row.get('license_field') or '; '.join(row.get('license_classifiers', [])) or 'UNKNOWN'
    entry('FASHN environment: ' + row['package'], 'DEPENDENCY_INSTALLED', expr,
          'PROPRIETARY_EULA_APPLIES_LOCAL_USE_SCOPE_REVIEWED' if row['package'].startswith('nvidia-') else 'INSTALLED_LICENSE_METADATA_AND_NOTICES_REVIEWED',
          str((OLD_RUN / 'INSTALLED_DEPENDENCY_LICENSES.json').relative_to(ROOT)),
          'Local research use subject to all bundled component terms; no redistribution or complete transitive SBOM certification',
          'Actual model compatibility not tested', row['version'])
for name, key, lic in [('Detectron2', 'detectron2_license', 'Apache-2.0'), ('MMCV', 'mmcv_license', 'Apache-2.0'),
                       ('MMDetection', 'mmdet_license', 'Apache-2.0'), ('InPlaceABN', 'abn_license', 'BSD-3-Clause')]:
    entry(name, 'DEPENDENCY_REFERENCE_ONLY', lic, 'REFERENCE_LICENSE_VERIFIED_STACK_NOT_INSTALLED', sources[key]['snapshot'], conditions,
          'Final candidate-specific environment and all transitive/build dependencies not installed/audited', sources[key]['url'])
entry('MHP-v2', 'DATASET', 'Official project noncommercial academic research terms', 'RESEARCH_SCOPE_COMPATIBLE_WITH_PROJECT_TERMS',
      sources['mhp_terms']['snapshot'], 'Retain citation; comply with stated use/distribution terms; approval does not fix annotation/leakage issues')
entry('CIHP DatasetNinja / original CIHP', 'DATASET', 'Provider declares MIT; source PGN software MIT does not establish original RGB/GT grant',
      'DATASET_RIGHTS_UNVERIFIED', 'provenance/CIHP_ARCHIVE_PREFLIGHT_V1.json',
      'Establish applicable original dataset research/use/publication terms before evaluation', 'Native Human GT absent in conversion; dataset license scope unresolved')
entry('Company CCTV', 'DATASET_FUTURE_ONLY', 'Owner research permission/privacy policy not verified here', 'LATER_DATA_PERMISSION_PENDING_NOT_AUTHORIZED',
      'RESEARCH_SCOPE.md', 'Research evaluation only; data provision is not commercial sponsorship; obtain owner permission/privacy safeguards', 'No CCTV access/inference in this review')
entry('Frozen YOLO26x / Ultralytics', 'CODE_CHECKPOINT_REFERENCE', 'Existing Ultralytics AGPL-3.0 / enterprise licensing path',
      'ACADEMIC_STATUS_DOES_NOT_WAIVE_APPLICABLE_AGPL_OBLIGATIONS', 'manifests/YOLO26X_SOURCE.json',
      'Keep frozen artifact/env unchanged; review obligations for any future distribution/network use; no commercial clearance',
      'This is a carried-forward licensing reference, not renewed complete upstream legal audit')
write_csv('provenance/LICENSE_MATRIX_DECISION5A_V1.csv', matrix)

# Current registry supersedes metadata only; original registries remain immutable.
rows = list(csv.DictReader((ROOT / 'provenance/MODEL_VARIANT_REGISTRY_V2.csv').open()))
for row in rows:
    row['intended_use'] = scope['intended_use']
    row['scope_decision'] = '5A'
    row['weight_eligibility'] = method_status[row['method']]
    row['execution_authorized'] = False
    row['license_matrix'] = 'provenance/LICENSE_MATRIX_DECISION5A_V1.csv'
    if row['model_id'] == 'FASHN_B4':
        row['training_dataset'] = 'PROPRIETARY_FASHN_CURATED_FINE_TUNING; NVIDIA_MIT_B4_BASE; EXACT_COMPOSITION_UNKNOWN'
        row['notes'] = 'Native W=384 H=576 (not HxW); MIT-B4 is architecture name, not MIT license; official card declares proprietary fine-tuning; MHP/CIHP content overlap UNKNOWN; no checkpoint inference'
    if row['model_id'] == 'D2FP_R101_LIP':
        config = 'third_party/human_parsing/D2FP/configs/lip/d2fp_R101_bs64_72k_prior100_dec9.yaml'
        assert config.split('/')[-1] in json.loads((ROOT / sources['d2fp_release']['snapshot']).read_text())['body']
        row['source_config'] = config
        row['source_config_sha256'] = sha(WORKSPACE / config)
        row['notes'] = 'Official weights release links dec9.yaml, not wo_enhance ablation; corrected metadata only; config-to-weight load remains untested'
    if row['method'] in ['QANet', 'RP-R-CNN']:
        row['code_license'] = 'MIT verified pinned LICENSE; selected weight scope pending'
    if row['method'] == 'CDGNet':
        row['code_license'] = 'NOT_ESTABLISHED_PINNED_TREE_NO_LICENSE_FILE'
write_csv('provenance/MODEL_VARIANT_REGISTRY_V3.csv', rows)

# Revalidate three previously selected TRAIN inputs, no parser/torch/model imports.
ImageFile.LOAD_TRUNCATED_IMAGES = False
dataset = json.loads((ROOT / 'manifests/DATASET_MANIFEST.json').read_text())
development = json.loads((ROOT / 'manifests/DEVELOPMENT_SET.json').read_text())
readable = json.loads((ROOT / 'manifests/mhpv2_readable_v1/TRAIN_READABLE.json').read_text())
ids = development['smoke_image_ids']
assert ids == ['967', '14282', '4480'] and len(ids) <= 3
index = {}
with (ROOT / dataset['canonical_gt_index']).open() as f:
    for line in f:
        record = json.loads(line)
        if record['split'] == 'train' and record['image_id'] in ids:
            index[record['image_id']] = record
input_evidence = []
for image_id in ids:
    assert image_id in readable['image_ids']
    record = index[image_id]
    rgb = WORKSPACE / dataset['root_workspace_relative'] / record['image_path']
    assert sha(rgb) == record['image_sha256']
    with Image.open(rgb) as im:
        im.load()
        assert list(im.size) == record['original_wh']
        # Canonical audit fingerprints include big-endian W/H before RGB bytes.
        assert hashlib.sha256(struct.pack('>II', *im.size) + np.asarray(im.convert('RGB')).tobytes()).hexdigest() == record['decoded_rgb_sha256']
    person = min(record['persons'], key=lambda p: p['person_file_id'])
    gt = WORKSPACE / dataset['root_workspace_relative'] / person['annotation_path']
    assert sha(gt) == person['source_sha256']
    with Image.open(gt) as im:
        im.load()
        array = np.asarray(im)
        if array.ndim == 3:
            array = array[:, :, 0]
        assert list(im.size) == record['original_wh'] and set(np.unique(array)).issubset(set(range(59)))
    input_evidence.append(dict(image_id=image_id, split='train', image_workspace_relative=str(rgb.relative_to(WORKSPACE)),
                               source_sha256=sha(rgb), decoded_rgb_sha256=record['decoded_rgb_sha256'], original_wh=record['original_wh'],
                               strict_pixel_load='PASS', gt_annotation_workspace_relative=str(gt.relative_to(WORKSPACE)),
                               gt_source_sha256=sha(gt), gt_dimensions_and_class_range='PASS',
                               native_person_file_id=person['person_file_id'], physical_ownership='NOT_CERTIFIED_BY_FILE_ID'))
cp = json.loads((ROOT / 'provenance/CHECKPOINT_MANIFEST.json').read_text())['FASHN']
proposal = dict(schema_version='2.0', run_id=RUN_ID, status='PROPOSED_NOT_AUTHORIZED', scope_decision='5A',
                download_authorized=False, inference_authorized=False, inputs=input_evidence,
                input_selection_source='manifests/DEVELOPMENT_SET.json', readable_source='manifests/mhpv2_readable_v1/TRAIN_READABLE.json',
                dataset_manifest_sha256=sha(ROOT / 'manifests/DATASET_MANIFEST.json'), checkpoint=cp,
                download_budget_bytes=300_000_000, checkpoint_expected_bytes=256_146_352,
                allowed_small_metadata='Same pinned official checkpoint config/card/license only; combined download cap 300 MB',
                dependency_install_authorized=False, environment_workspace_relative='.venvs/fashn-stage0',
                precision='FP32', native_wh=[384, 576], initial_images=1, maximum_images=3,
                maximum_model_forward_calls=4, additional_forward_reason='One native API parity check on first input',
                mode='GT geometry crop for feasibility only; no model quality metric/ranking',
                crop_margin_draft=0.10, crop_policy_frozen=False, crop_policy_is_benchmark_selection=False,
                runner_gate='Existing runner keeps raw DATASET_BLOCKED guard; approval-specific readable-view gate adaptation required after permission and before execution',
                stop_conditions=['Checkpoint hash/size mismatch', 'GPU contention', 'Dependency change/download needed',
                                 'License/identity mismatch', 'FP32 OOM or incompatible output'],
                full_benchmark=False, validation_inference=False, cctv_inference=False,
                available_disk_bytes_at_preparation=shutil.disk_usage(WORKSPACE).free)
write_json('manifests/FASHN_SMOKE_PROPOSAL_V2.json', proposal)

publish('reports/LICENSE_ELIGIBILITY_REASSESSMENT.md', '''# ตรวจสิทธิ์ใช้งานภายใต้ขอบเขตวิจัย — Decision 5A

สถานะการตรวจเอกสาร: **PASS_WITH_WARNINGS**; Stage 0 โดยรวมยัง **BLOCKED / WAITING_FOR_USER_APPROVAL** ไม่ใช่ model readiness หรือสิทธิ์ deployment ตรวจ source/license snapshots ที่เก็บ 2026-10-08 และทบทวนแหล่งหลักอีกครั้ง 2026-10-12 ไม่มี weights ดาวน์โหลด/โหลด/รัน

## ขอบเขตที่ยืนยันแล้ว

ผู้ใช้ยืนยัน **NONCOMMERCIAL ACADEMIC RESEARCH / EVALUATION** สำหรับงานอิสระของนักศึกษา ภาพ CCTV จากบริษัทเป็นข้อมูลประเมินในอนาคต ไม่ใช่หลักฐาน sponsorship/product development; commercial use อยู่นอกขอบเขต ต้องตรวจใหม่หากเปลี่ยนวัตถุประสงค์ [Research scope](../RESEARCH_SCOPE.md)

## โมเดล: code และ checkpoint แยกกัน

| Candidate | Code ที่ตรวจ | Checkpoint / เงื่อนไข | ข้อสรุปสำหรับ Decision 5A |
|---|---|---|---|
| FASHN | Wrapper กำหนดให้ปฏิบัติตาม SegFormer terms | Official pinned model card ยืนยัน weights สืบทอด NVIDIA SegFormer license | เข้าเงื่อนไข research/evaluation; **รออนุมัติ download/smoke** |
| M2FP | Predominantly CC-BY-NC-4.0 | Official checkpoints ถูกอ้างใน README; ขอบเขต grant ของ asset ที่เลือกยังไม่ยืนยันแยก | Research candidate แบบมีเงื่อนไข; ตรวจ applicability/attribution ก่อน execution |
| CPI R50 / ConvNeXt-B | Apache-2.0 | Official dataset-specific weights มีจริง; ไม่ได้ตรวจพบ weight-specific grant ที่ยืนยันได้แยก | Code เข้ากับ academic scope; checkpoint applicability ยัง pending |
| D2FP CIHP / LIP | MIT ที่ root; README รับรองการใช้ M2FP และ source มี inherited notices | Official full-parser release มี CIHP/LIP; weight terms และ inherited-file scope ต้องบันทึกต่อ | Research candidate แบบมีเงื่อนไข; ไม่เหมารวมว่า MIT เคลียร์ทุกไฟล์ |
| SCHP LIP / ATR / Pascal | MIT code | Official weights linked; applicability ของ code grant ต่อ weights ยังไม่ยืนยัน | Research candidate แบบมีเงื่อนไข; legacy environment ไม่พร้อม |
| Sapiens2-0.4B | Custom Sapiens2 license | ข้อห้าม surveillance ครอบคลุม related research/development | **LICENSE_BLOCKED_PENDING_APPLICABLE_PERMISSION** |

**Verified fact:** SegFormer §3.3 กำหนด noncommercial เป็น research/evaluation และ FASHN card เชื่อม license นี้อย่างชัดเจน **Assessment:** ขอบเขต Decision 5A ตรงกับการใช้ที่อนุญาตในข้อความนี้ โดยยังต้องปฏิบัติตาม license/notices และข้อกำหนด derivative/redistribution ไม่มีข้อห้าม surveillance-specific ที่พบใน SegFormer/FASHN terms ที่ตรวจ การที่ model card แสดงคำว่า production ไม่ได้ลบข้อจำกัด license ส่วน MIT-B4 เป็นชื่อ architecture ไม่ใช่ MIT license [Official model card](https://huggingface.co/fashn-ai/fashn-human-parser/blob/1f80c34dbab321c5730dda5c3fea279fd3e97498/README.md), [SegFormer license](https://github.com/NVlabs/SegFormer/blob/master/LICENSE)

**Verified fact:** Sapiens2 §1(b)(vi)(i) ห้าม surveillance รวมถึง research/development ที่เกี่ยวข้อง **Assessment:** academic scope ไม่ปลดข้อห้ามนี้ และการเริ่ม smoke บน MHP-v2 ไม่ใช่ช่องทางเลี่ยง intended-use restriction [Pinned Sapiens2 license](https://github.com/facebookresearch/sapiens2/blob/7e5bae88456ac418ff0e58e74106c9fe192055d4/LICENSE.md)

สำหรับ M2FP/CPI/D2FP/SCHP การไม่พบ separate weight license คือ **ความไม่แน่นอนเรื่อง applicability** ไม่ใช่ข้อพิสูจน์ว่า weights ทุกตัวถูกห้ามใช้หรือว่าต้องมี license อีกฉบับเสมอ ต้องเก็บหลักฐานว่าการเผยแพร่ asset ที่เลือกอยู่ภายใต้ grant ใดก่อน executing ไม่ตีความลิงก์สาธารณะเป็น blanket permission [M2FP](https://github.com/soeaver/M2FP/blob/17a89decacfca347ed18bed66baec7a5847ea43c/LICENSE), [CPI](https://github.com/HAG-uestc/CPI-Parser/blob/d62cae523ba913fec4a7fda5816bc1d96bbf644d/LICENSE), [D2FP release](https://github.com/cvlab-yongin/D2FP/releases/tag/weights), [SCHP](https://github.com/GoGoDuck912/Self-Correction-Human-Parsing/blob/eb84c432cc697f494d99662a05f2335eb2f26095/LICENSE)

Optional: QANet และ RP-R-CNN มี pinned MIT LICENSE; selected weights/dependencies ยังไม่ได้ตรวจครบ CDGNet pinned tree ไม่พบ LICENSE/COPYING/NOTICE และยังไม่ยืนยัน grant จากที่อื่น จัด CODE_LICENSE_UNSPECIFIED_REVIEW_REQUIRED ไม่ติดตั้งหรือเพิ่ม roster อัตโนมัติ

## Dependencies ตรวจแยกจากตัวโมเดล

ตรวจ metadata และไฟล์ license จริงใน existing FASHN environment โดยไม่ import/load โมเดล: torch 2.14.0 มีหลาย bundled licenses; torchvision 0.29.0 BSD, transformers 4.57.1 / huggingface-hub 0.36.2 / safetensors 0.6.2 / OpenCV 4.11.0.86 มี Apache terms, NumPy 2.5.3 มี bundled BSD/MIT/อื่น ๆ, Pillow 12.3.0 MIT-CMU/third-party notices, PyYAML 6.0.3 MIT และ NVIDIA CUDA runtime 13.0.96 มี **proprietary EULA** แยก ไม่เรียก CUDA ว่า BSD เพราะ PyTorch ใช้ OSS licenses

ขอบเขตหลักฐานคือ local research use และ inspected notices/metadata ไม่ใช่ complete transitive SBOM หรือ certification สำหรับ redistribution/deployment Reference Detectron2, MMCV 1.7.0, MMDetection 2.25.1 เป็น Apache-2.0 และ InPlaceABN เป็น BSD-3-Clause; native legacy stacks ยังไม่ installed จึงไม่อ้างว่า audit tested dependencies ครบหรือ model ใช้งานได้

## Dataset / upstream / data-owner rights

| Component | สิ่งที่ยืนยัน | สิ่งที่ยังเปิด |
|---|---|---|
| MHP-v2 | Official project อนุญาต noncommercial academic research ภายใต้ stated terms | Annotation quality/leakage เป็นคนละ gate; terms ไม่รับรองความสะอาดของข้อมูล |
| CIHP DatasetNinja / native CIHP | Provider ระบุ MIT; PGN repo software มี MIT | ยังไม่ยืนยัน grant ของ original RGB/GT; software/converter MIT ไม่ใช่หลักฐาน dataset-owner permission |
| Frozen YOLO26x | คง existing AGPL/enterprise licensing reference และ weights เดิม | Academic status ไม่ลบ AGPL obligations; review รอบนี้ไม่รับรอง future distribution/deployment |
| Company CCTV | ผู้ใช้กำหนดบทบาทเป็น later student research evaluation | Owner permission/privacy safeguards ยังไม่ตรวจในรอบนี้; ไม่มี access/inference |

[MHP project terms](https://lv-mhp.github.io/), [CIHP preflight](CIHP_ARCHIVE_PREFLIGHT_AUDIT.md), [frozen YOLO record](../manifests/YOLO26X_SOURCE.json) ไม่มี PPSS activity หรือ license recheck ของ PPSS

## Correction ที่ได้จากการตรวจ source

FASHN card ระบุ proprietary curated fine-tuning data แล้ว จึงแก้ current registry จาก training dataset UNKNOWN เป็น declared proprietary FASHN dataset แต่ **exact composition / MHP-v2 / CIHP content overlap ยัง UNKNOWN**; ไม่ตีความว่า zero exposure Native geometry คือ width 384 × height 576

D2FP official LIP release ชี้ `d2fp_R101_bs64_72k_prior100_dec9.yaml` ไม่ใช่ `wo_enhance` ablation จึงแก้เฉพาะ V3 metadata/config hash ไม่อ้าง load compatibility หรือผล accuracy ทะเบียน V1/V2 และ checkpoint manifests เดิมเก็บ unchanged

## ข้อเสนอ execution ที่ต้องอนุมัติ

FASHN official pinned safetensors **256,146,352 bytes (~256 MB)** และ same-revision small metadata; combined download cap **300 MB** ใช้ existing isolated environment ไม่ install dependencies เพิ่ม Initial 1 / สูงสุด 3 readable TRAIN IDs **967, 14282, 4480**; native FP32/T4, export/dimensions/class/coordinate/NaN checks, hashes/VRAM/errors; สูงสุด 4 forward calls รวม native API parity ครั้งแรก ไม่มี accuracy scoring, final timing, validation/CCTV inference หรือ model ranking

ภาพทั้งสามถูก strict-load และ source/decoded hashes เทียบ canonical evidence แล้ว การใช้ GT geometry เพื่อ feasibility ไม่ได้ freeze crop/ownership policy และไม่รับรอง GT physical ownership Existing runner ยังมี historical raw DATASET_BLOCKED gate: หลัง approval ต้องปรับ gate ให้ตรวจ approved readable view + run-specific execution permission ก่อนรัน ห้ามปลด gate เพื่อ Stage 1 หรือรันล่วงหน้า หากต้อง dependencies เพิ่ม/GPU contention/FP32 ไม่ผ่าน ให้หยุดพร้อม diagnostics ไม่เปลี่ยน precision อัตโนมัติ

[Reviewable smoke proposal](../manifests/FASHN_SMOKE_PROPOSAL_V2.json), [component matrix](../provenance/LICENSE_MATRIX_DECISION5A_V1.csv), [current registry V3](../provenance/MODEL_VARIANT_REGISTRY_V3.csv), [source evidence](../provenance/LICENSE_REASSESSMENT_DECISION5A_V1.json)

**WAIT FOR USER APPROVAL.** Scope clarification แก้ intended-use ambiguity เท่านั้น ไม่ได้อนุมัติ weights/GPU smoke, native CIHP acquisition/quality audit, Stage 1 หรือ CCTV field test
''')

report_link = '[Decision 5A license review](reports/LICENSE_ELIGIBILITY_REASSESSMENT.md)'
readme = (ROOT / 'README.md').read_text()
readme = readme.replace('[Variant registry V2](provenance/MODEL_VARIANT_REGISTRY_V2.csv)', '[Current variant registry V3](provenance/MODEL_VARIANT_REGISTRY_V3.csv) (V2 retained as historical evidence)')
readme = readme.replace('## Current evidence and decisions', '''## Research scope and current license decision — 2026-10-12

**Decision 5A: NONCOMMERCIAL ACADEMIC RESEARCH / EVALUATION.** Independent student study; company CCTV is future research evaluation data, not proof of commercial sponsorship. [Scope](RESEARCH_SCOPE.md), ''' + report_link + ''', [license matrix](provenance/LICENSE_MATRIX_DECISION5A_V1.csv).

FASHN research terms are compatible, but checkpoint download/inference is **not authorized yet**. Other released candidates retain separate code/weight applicability records; Sapiens2 remains surveillance-research license-blocked. [Bounded FASHN proposal](manifests/FASHN_SMOKE_PROPOSAL_V2.json): 256 MB checkpoint, combined cap 300 MB, 1–3 readable train images, no new dependency installation. No checkpoint inference, validation benchmark or CCTV execution has occurred.

## Current evidence and decisions''')
publish('README.md', readme)
for name in ['STUDY_STANDARD.md', 'EXPERIMENT_PROTOCOL_DRAFT.md']:
    text = (ROOT / name).read_text()
    text += '''\n## Research scope amendment — Decision 5A, 2026-10-12

Current intended use is **NONCOMMERCIAL ACADEMIC RESEARCH / EVALUATION**, explicitly confirmed by the user. Company CCTV provision is later student evaluation data, not evidence of commercial R&D or product deployment. Commercial use requires a separate future license review. [Scope](RESEARCH_SCOPE.md), [component license assessment](reports/LICENSE_ELIGIBILITY_REASSESSMENT.md).

Academic scope does not override license restrictions. FASHN matches inspected research/evaluation terms, but checkpoint download/inference still requires explicit authorization; Sapiens2 remains blocked for surveillance-related research absent applicable permission. Preserve code/weight/dependency/dataset eligibility separately. Dataset roles, taxonomy and protocol remain draft; no benchmark/CCTV/Stage 1 authorization is implied. Existing approved readable TRAIN views permit independent feasibility preparation, not automatic model execution.
'''
    publish(name, text)
text = (ROOT / 'reports/STAGE0_NEXT_ACTIONS.md').read_text()
text = text.replace('[MODEL_VARIANT_REGISTRY_V2.csv](../provenance/MODEL_VARIANT_REGISTRY_V2.csv)', '[MODEL_VARIANT_REGISTRY_V3.csv](../provenance/MODEL_VARIANT_REGISTRY_V3.csv) (V2 historical unchanged)')
text = text.replace('เสนอเป็นงานอิสระหลังยืนยัน **noncommercial research/evaluation scope**:', 'ผู้ใช้ยืนยัน **Decision 5A: noncommercial academic research/evaluation** แล้ว; scope ambiguity ปิดแล้ว แต่ยังไม่อนุมัติ download/inference เสนอเป็นงานอิสระ:')
text = text.replace('**License matters:** FASHN inherits SegFormer noncommercial research/evaluation terms; company development/deployment ต้องตรวจสิทธิ์แยก ห้ามรับรองว่า research label ครอบ company surveillance product R&D โดยอัตโนมัติ Sapiens2 ยังคง excluded ไม่ว่าจะเลือก research-only หรือ deployment direction',
                    '**Current license assessment:** FASHN เข้า research/evaluation terms สำหรับ independent student research นี้ Company CCTV เป็น future evaluation input ไม่ใช่หลักฐาน company R&D; commercial deployment อยู่นอกขอบเขต ไม่ต้องถาม scope ซ้ำ Sapiens2 ยังคง excluded เพราะข้อห้าม surveillance-related research ใช้บังคับ [Component review](LICENSE_ELIGIBILITY_REASSESSMENT.md), [scope](../RESEARCH_SCOPE.md), [fixed-input proposal](../manifests/FASHN_SMOKE_PROPOSAL_V2.json) cap 300 MB รวม metadata, TRAIN IDs 967/14282/4480, สูงสุด 4 forward รวม native parity ไม่มี dependencies ใหม่; ขอ execution/download approval แยก')
publish('reports/STAGE0_NEXT_ACTIONS.md', text)
text = (ROOT / 'reports/MODEL_COMPATIBILITY_REPORT.md').read_text()
text = text.replace("FASHN's fine-tuning dataset and MHP exposure remain UNKNOWN.", "FASHN's official card declares proprietary FASHN curated fine-tuning data; exact composition and MHP/CIHP content exposure remain UNKNOWN (current V3 correction).")
text += '''\n## Current intended-use reassessment — 2026-10-12

Decision 5A resolves research-scope ambiguity: independent **noncommercial academic research/evaluation**. Use the [component license report](LICENSE_ELIGIBILITY_REASSESSMENT.md), [matrix](../provenance/LICENSE_MATRIX_DECISION5A_V1.csv) and [V3 registry](../provenance/MODEL_VARIANT_REGISTRY_V3.csv) as current eligibility evidence. Earlier paragraphs describe the pre-clarification audit; they do not override the user's clarified scope.

FASHN is research-license compatible, execution approval pending. M2FP/CPI/D2FP/SCHP code is compatible with this scope subject to notices, while applicability to selected weights remains separately documented/pending; absence of a separate weight license is uncertainty, not a universal prohibition. Sapiens2 remains explicitly license-blocked for surveillance-related research. No checkpoint downloaded, loaded or inference passed; FP32 T4 feasibility remains NOT_TESTED for every checkpoint. D2FP LIP release-config metadata corrected in V3 only. Native/crop cohorts and ownership policies remain draft.
'''
publish('reports/MODEL_COMPATIBILITY_REPORT.md', text)
text = (ROOT / 'reports/PROTOCOL_REVIEW.md').read_text()
text = text.replace('| BLOCKED; no automatic repair or split change |', '| Approved versioned readable views prepared; original files/splits unchanged; no automatic repair |', 1)
text = text.replace('| Native evaluator edge | Source function raises IndexError with zero predictions | Add/test a reviewed compatibility guard; broader source/native parity required | Native official-style freeze blocked |',
                    '| Native evaluator edge | Upstream empty prediction bug preserved; separate wrapper passes 19 synthetic tests | Retain wrapper/reference separation; verify broader published/native parity before freeze | Wrapper preparation PASS; official benchmark parity not claimed |')
text = text.replace('| License scope | MHP/FASHN noncommercial restrictions; uncertain legacy weight grants; D2FP upstream code | Record applicable weight and intended-use terms before affected execution/deployment | Candidate-specific |',
                    '| License scope | User confirmed Decision 5A noncommercial academic research; FASHN matches research terms | Record code/weights/dependency/dataset terms separately; selected legacy-weight applicability pending | Scope ambiguity RESOLVED; execution permissions still candidate-specific |')
text += '''\n## Scope decision recorded — 2026-10-12

See [Decision 5A](../RESEARCH_SCOPE.md) and [license reassessment](LICENSE_ELIGIBILITY_REASSESSMENT.md). Commercial deployment is out of scope; company CCTV data supply does not establish product R&D. No repeat approval is needed for the scope or previously approved readable-view policy. FASHN checkpoint download/smoke remains unapproved; its bounded proposal can proceed independently of CIHP native GT once specifically authorized. Other scientific decisions, human GT review and dataset rights remain open. PPSS remains paused.
'''
publish('reports/PROTOCOL_REVIEW.md', text)
text = (ROOT / 'reports/DATASET_REASSESSMENT.md').read_text()
text += '''\n## Research-scope clarification — Decision 5A, 2026-10-12

User-confirmed independent **noncommercial academic research/evaluation** supersedes any earlier uncertainty about company R&D. [Scope](../RESEARCH_SCOPE.md), [separate dataset/model/dependency license review](LICENSE_ELIGIBILITY_REASSESSMENT.md). MHP project terms fit this scope; CIHP original RGB/GT permission remains unverified even though DatasetNinja/PGN software declares MIT. Scope clarification does not restore missing native Human GT, remove duplication or prove annotation ownership. Dataset roles remain provisional and no Full Quality Audit/benchmark/model inference has started. Bounded FASHN feasibility on verified readable TRAIN inputs is an independent proposed action, still awaiting download/execution approval.
'''
publish('reports/DATASET_REASSESSMENT.md', text)
config = yaml.safe_load((ROOT / 'configs/study.yaml').read_text())
config['research_scope'] = {'decision': '5A', 'intended_use': scope['intended_use'], 'config': 'configs/research_scope.yaml'}
publish('configs/study.yaml', yaml.safe_dump(config, allow_unicode=True, sort_keys=False))
state = json.loads((ROOT / 'STUDY_STATE.json').read_text())
state['last_updated_utc'] = NOW.isoformat()
state['research_scope'] = {'decision': '5A', 'intended_use': scope['intended_use'], 'status': 'USER_CONFIRMED', 'record': 'RESEARCH_SCOPE.md'}
state['license_reassessment'] = dict(run_id=RUN_ID, status='PASS_WITH_WARNINGS', model_status=method_status,
                                   checkpoint_downloaded=0, checkpoint_smoke_passed=0, execution_authorized=False,
                                   dataset_rights={'MHP-v2': 'RESEARCH_SCOPE_COMPATIBLE_WITH_PROJECT_TERMS', 'CIHP': 'UNVERIFIED'},
                                   report='reports/LICENSE_ELIGIBILITY_REASSESSMENT.md', registry='provenance/MODEL_VARIANT_REGISTRY_V3.csv',
                                   validation='provenance/LICENSE_REASSESSMENT_VALIDATION_V1.json')
write_json('STUDY_STATE.json', state)
write_json('provenance/LICENSE_REASSESSMENT_ACTIVE_RUN.json', {'run_id': RUN_ID, 'run_path': str(RUN.relative_to(ROOT)), 'prior_review_run': str(OLD_RUN.relative_to(ROOT))})
write_json('provenance/LICENSE_REASSESSMENT_DECISION5A_V1.json', dict(
    run_id=RUN_ID, finalized_utc=NOW.isoformat(), source_collection_utc='2026-10-08', online_recheck_date='2026-10-12',
    source_manifest=str((OLD_RUN / 'sources/SOURCE_MANIFEST.json').relative_to(ROOT)),
    local_source_manifest=str((RUN / 'LOCAL_SOURCE_MANIFEST.json').relative_to(ROOT)),
    installed_dependency_license_evidence=str((OLD_RUN / 'INSTALLED_DEPENDENCY_LICENSES.json').relative_to(ROOT)),
    scope='configs/research_scope.yaml', matrix='provenance/LICENSE_MATRIX_DECISION5A_V1.csv',
    registry='provenance/MODEL_VARIANT_REGISTRY_V3.csv', smoke_proposal='manifests/FASHN_SMOKE_PROPOSAL_V2.json',
    evidence_limits=['No full transitive SBOM certification', 'Legacy environments not installed', 'Weight-scope ambiguity separately retained',
                     'No model/checkpoint execution', 'No original dataset permission assumed from converter license'],
    checkpoint_downloads=0, heavy_dependency_installs=0, model_inference=0, full_benchmark=False, ppss_activity=False,
    stage0_overall='BLOCKED', review_gate='WAITING_FOR_USER_APPROVAL'))
write_json('provenance/LICENSE_REASSESSMENT_DOCUMENT_REVISIONS_V1.json', {'run_id': RUN_ID, 'documents': REVISIONS.copy(), 'created': CREATED.copy()})
print(json.dumps({'run_id': RUN_ID, 'archived_documents': len(REVISIONS), 'new_artifacts': len(CREATED),
                  'license_matrix_rows': len(matrix), 'registry_variants': len(rows), 'strict_readable_train_inputs': len(input_evidence),
                  'checkpoint_downloaded': 0, 'model_inference': 0, 'validation_pending': True}, ensure_ascii=False))
