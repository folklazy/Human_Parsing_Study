"""Synchronize current navigation and additive status, preserving dated evidence.

No model inference, dataset inspection, package changes or benchmark execution.
"""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import os
import shutil

S = Path(__file__).resolve().parents[1]
W = S.parent
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
R = S / 'provenance/RUN_MANIFESTS' / ('current-status-sync-' + stamp)
R.mkdir(parents=True)
archive = S / 'reports/archive' / ('current_status_sync_' + stamp)
archive.mkdir()

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def atomic(p, value):
    temporary = p.with_suffix(p.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    os.replace(temporary, p)

names = ['README.md', 'DATA_SCHEMA.md', 'STUDY_STATE.json',
         'reports/MODEL_COMPATIBILITY_REPORT.md', 'reports/STAGE0_NEXT_ACTIONS.md',
         'reports/STAGE0_FEASIBILITY_REPORT.md', 'reports/PROTOCOL_REVIEW.md',
         'reports/TAXONOMY_AUDIT.md', 'reports/APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md']
before = []
for name in names:
    p = S / name
    q = archive / name
    q.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, q)
    before.append({'path': name, 'before_sha256': sha(p), 'archive': str(q.relative_to(S))})

handoff = S / json.loads((S / 'provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json').read_text())['run']
cdg = S / json.loads((S / 'provenance/CDGNET_ACQUISITION_ACTIVE.json').read_text())['run']
final = json.loads((handoff / 'FINAL.json').read_text())
validation = json.loads((S / final['validation']).read_text())
smokes = json.loads((handoff / 'SMOKE_SUMMARY.json').read_text())
old_inventory = json.loads((handoff / 'CHECKPOINT_MANIFEST.json').read_text())
cdg_manifest = json.loads((S / 'provenance/CDGNET_CHECKPOINT_MANIFEST_V1.json').read_text())
assert sha(W / cdg_manifest['destination']) == cdg_manifest['sha256']

# Preserve the old registry and add the technical evidence from the prior pilot,
# separately from current execution permission and license eligibility.
registry = list(csv.DictReader((S / 'provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V5.csv').open()))
pilot = W / 'Human_Parsing_CCIHP_10_Image_Pilot'
pilot_rows = {r['model_id'].casefold(): r for r in csv.DictReader((pilot / 'metrics/MODEL_PILOT_STATUS.csv').open())}
for row in registry:
    prior = pilot_rows.get(row['model_id'].casefold())
    row['historical_pilot_status'] = prior['status'] if prior else 'NO_ACTIVE_PILOT_ROW'
    row['historical_pilot_completed_images'] = prior['completed_images'] if prior else ''
    row['historical_pilot_precision'] = prior['precision'] if prior else ''
    row['historical_pilot_manifest'] = '../Human_Parsing_CCIHP_10_Image_Pilot/' + prior['run_manifest'] if prior else ''
    row['historical_pilot_reason'] = prior['reason'] if prior else ''
    if prior:
        assert (pilot / prior['run_manifest']).exists()
    if row['model_id'].startswith('Sapiens2'):
        row['technical_status_note'] = 'Historical technical feasibility retained; use eligibility is a separate field; no new execution in this revision'
        if row['model_id'].casefold() == 'sapiens2_5b':
            row['technical_status_note'] = 'Excluded from execution by user due to resource size; checkpoint retained; not retested'
    elif row['model_id'] == 'CDGNet_LIP':
        row['technical_status_note'] = 'Checkpoint tensor inspection PASS; architecture load/GPU inference NOT_TESTED'
        row['backbone_initialization_required_for_official_evaluation'] = 'False'
    else:
        row['technical_status_note'] = 'See dated native smoke evidence; this synchronization runs no models'
registry_path = S / 'provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv'
fields = sorted(set().union(*(r.keys() for r in registry)))
with registry_path.open('x') as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(registry)

files = list(old_inventory['files'])
files.append({'path': cdg_manifest['destination'], 'bytes': cdg_manifest['bytes'],
              'sha256': cdg_manifest['sha256'], 'role': 'PARSER_CHECKPOINT',
              'source_url': next(m['source_url'] for m in cdg_manifest['folder_members'] if m['filename'] == 'LIP_epoch_149.pth'),
              'original_filename': 'LIP_epoch_149.pth', 'evidence': str((cdg / 'ACQUISITION.json').relative_to(S))})
unique = {r['sha256']: r['bytes'] for r in files}
inodes = set()
for item in files:
    st = (W / item['path']).stat()
    assert st.st_size == item['bytes']
    inodes.add((st.st_dev, st.st_ino))
inventory = {'created_utc': datetime.now(timezone.utc).isoformat(),
             'derivation': 'Prior immutable handoff checkpoint inventory plus verified CDGNet acquisition; no old evidence rewritten',
             'checkpoint_path_entries_including_aliases': len(files), 'unique_checkpoint_artifacts': len(unique),
             'unique_physical_inode_files': len(inodes), 'unique_checkpoint_bytes': sum(unique.values()),
             'native_smoke_passes_current_handoff': len(smokes), 'canonical_CPI_packets': 8,
             'CDGNet_model_inference': 'NOT_TESTED', 'files': files,
             'author_authenticity': 'Local SHA256 alone does not establish author authenticity'}
atomic(S / 'provenance/CHECKPOINT_INVENTORY_CURRENT_V1.json', inventory)

current = {'schema_version': '1.0', 'updated_utc': datetime.now(timezone.utc).isoformat(),
           'purpose': 'Current evidence navigation, not a replacement for executable runner configuration',
           'registry': str(registry_path.relative_to(S)),
           'checkpoint_inventory': 'provenance/CHECKPOINT_INVENTORY_CURRENT_V1.json',
           'CDGNet_manifest': 'provenance/CDGNET_CHECKPOINT_MANIFEST_V1.json',
           'executable_config': 'configs/application_v2_handoff_v3.yaml',
           'decision_record': 'provenance/APPLICATION_V2_DECISIONS_V3.json',
           'numeric_mapping': 'taxonomy/APPLICATION_BODY_CLOTHING_CANDIDATE_V2.json',
           'CPU_validation': final['validation'], 'acceptance_matrix': final['acceptance'],
           'handoff_report': 'reports/APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md',
           'CDGNet_report': 'reports/CDGNET_ACQUISITION_TH_20261015.md',
           'scientific_freeze': 'BLOCKED_PENDING_ACCEPTANCE_AND_EVIDENCE', 'full_benchmark': False}
atomic(S / 'provenance/CURRENT_STUDY_ARTIFACTS.json', current)

p = S / 'README.md'
t = p.read_text().replace('[Model/checkpoint registry V4](provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V4.csv)', '[Current model/checkpoint registry V6](provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv)')
t = t.replace('[registry V5](provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V5.csv)', '[current registry V6](provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv)')
t = t.replace('- [Evidence pointer](provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json)', '- [Current artifact index](provenance/CURRENT_STUDY_ARTIFACTS.json)\n- [Current checkpoint inventory](provenance/CHECKPOINT_INVENTORY_CURRENT_V1.json)\n- [Handoff evidence pointer](provenance/IMPLEMENTATION_HANDOFF_ACTIVE.json)')
p.write_text(t)

p = S / 'DATA_SCHEMA.md'
t = p.read_text().replace('[application_v2.yaml](configs/application_v2.yaml)', '[application_v2_handoff_v3.yaml](configs/application_v2_handoff_v3.yaml)', 1).replace('[decisions V2](provenance/APPLICATION_V2_DECISIONS_V2.json)', '[decisions V3](provenance/APPLICATION_V2_DECISIONS_V3.json)', 1)
section = '''## Current scoring and acquisition contracts — 15 October 2026

- Current evidence navigation: [CURRENT_STUDY_ARTIFACTS](provenance/CURRENT_STUDY_ARTIFACTS.json). This index does not authorize execution; runner values remain in accepted-bound executable config.
- `ConfiguredRunner.score_frame` and `score_person_result` share `scoring.score_frame`; absent/unaccepted context blocks scoring. Mapping fingerprint, checkpoint/config/head/native class order, support policy, accepted GT domain and evaluation-bbox provenance are checked before matching.
- `evaluate_persons(..., original_wh=[W,H])` validates every emitted integer semantic grid, unique identity and finite score even for unmatched/empty-GT cases. G_sem must be a subset of G_loc. Original W/H must come from trusted input evidence, not inferred from predictions.
- `conditioning_bbox` is separate from `evaluation_bbox={xyxy, source, coordinate_convention, derivation_revision}`. Only the configured evaluation source is used for scoring.
- Numeric mapping V2 requires `native_taxonomy` for prediction projection. CIHP10 Torso-skin and LIP10 Jumpsuits are distinct. All active mappings remain DRAFT; LIP does not support the exposed-torso target of the current common-capability candidate.
- Execution/acquisition dimensions are independent: downloaded, SHA256 verified, tensor-inspected, architecture-loaded, inference-passed, canonical-export-passed and intended-use eligibility must not collapse into one READY flag. CDGNet currently has acquisition/tensor inspection evidence only. Historical Sapiens technical runs remain separate from current intended-use eligibility; 5B remains excluded from execution for resources.
- Cached scoring and workflow resume are NOT_IMPLEMENTED/DISABLED. Packet hash/finalization/fingerprint validation is an artifact helper, not full workflow certification. Hard labels do not support probability aggregation.
- STRICT_COMPLETE versus OPERATIONAL_EMPTY_FALLBACK is implemented/tested as an explicit choice and remains pending acceptance. Failure events never independently add localization FN penalties.

'''
t = t.replace('## Active executable schema / accepted decisions', section + '## Active executable schema / accepted decisions', 1)
p.write_text(t)

p = S / 'DATA_SCHEMA.md'
p.write_text(p.read_text().replace('[Implementation report](reports/APPLICATION_V2_IMPLEMENTATION_TH.md)', '[Current implementation report](reports/APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md)', 1))

p = S / 'reports/MODEL_COMPATIBILITY_REPORT.md'
p.write_text(f'''# Model Compatibility — current evidence, 15 October 2026

**Native technical evidence exists; no final benchmark or universal READY roster is declared.** Current [registry V6](../provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv) records checkpoint acquisition, actual native execution, canonical export, historical pilot evidence and use eligibility separately.

CPU regression: {validation['tests']} tests passed in the [dated validation](../{final['validation']}). The last handoff executed FP32 on one fixed CCIHP TRAIN image per eligible checkpoint/component: 21 native passes. This status synchronization executes no models.

| Family | Actual technical evidence | Important operating-mode / readiness limit |
|---|---|---|
| FASHN B4 | Actual FP32 native smoke PASS; prior YOLO-conditioned bounded integration retained | Semantic parser; external YOLO/oracle identity is not native identity |
| M2FP R101 LIP / CIHP / MHP-v2 | 3 native checkpoint smokes PASS | LIP semantic mode versus CIHP/MHP multi-human mode must remain separate |
| CPI R50 / ConvNeXt-B, CIHP / MHP-v2 | 4 native smokes PASS; 8 T1/T3B canonical packets verified | T3B uses fresh parser plus saved verified YOLO; joint live runtime not certified; earlier R50-CIHP crowded-frame OOM warning retained |
| D2FP R101 CIHP / LIP | 2 native smokes PASS | Native instance versus semantic modes differ |
| SCHP LIP / ATR / Pascal | 3 native smokes PASS | Oracle-crop semantic tests, not native instance identity |
| SCHP CIHP global/local | 2 component smokes PASS; auxiliary detector downloaded | Full detector/global-local multi-person pipeline NOT_TESTED |
| QANet CIHP R50 / HRNet-W48 and LIP HRNet-W48 two resolutions | 4 native smokes PASS | Oracle proposal geometry; not detector-conditioned deployment proof |
| RP-R-CNN CIHP / MHP-v2 | 2 native smokes PASS | Internal detection cost remains part of native behavior |
| CDGNet R101 LIP | Downloaded; 603 finite FP32 tensor entries; 20-class head structurally verified | Architecture load / GPU inference / canonical adapter NOT_TESTED; prior code-license grant unresolved |
| Sapiens2 0.4B / 0.8B / 1B | Historical 10-image technical pilots recorded; 1B includes offload-control warning | Not re-executed in latest handoff; intended-use eligibility is separate from technical feasibility |
| Sapiens2 5B | Existing checkpoint retained | Excluded from execution by user due to resources; no new test |

{inventory['unique_checkpoint_artifacts']} unique checkpoint artifacts are catalogued, including one auxiliary detector and parser components; this is not the number of comparable standalone systems. [Current inventory](../provenance/CHECKPOINT_INVENTORY_CURRENT_V1.json). CDGNet trained weights came from the Google Drive folder linked by its official README, which also contains a separate ImageNet initializer. [Acquisition and inspection](CDGNET_ACQUISITION_TH_20261015.md).

No dependency reinstall was required to restore the tested legacy stack: source/toolchain/environment evidence is in the [handoff report](APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md). Sapiens permission questions and model-resource feasibility remain separate; downloading a checkpoint does not itself resolve use restrictions.

All model weights and environments remain outside the study. Scientific mappings/populations/matching/failure policy are still pending acceptance; full benchmark remains false. [Current protocol decisions](PROTOCOL_REVIEW.md) and [policy detail](APPLICATION_HANDOFF_POLICIES_TH_20261015.md).

The previous report describing zero downloaded weights was a dated Stage0B/0C snapshot; its byte-identical version is [archived](../{(archive/'reports/MODEL_COMPATIBILITY_REPORT.md').relative_to(S)}), not treated as current execution status. Prior license/source evidence remains under its original manifests.
''')

p = S / 'reports/STAGE0_NEXT_ACTIONS.md'
p.write_text(f'''# Stage 0 — current next actions, 15 October 2026

**Engineering evidence ready for review; scientific freeze and full benchmark remain blocked.** This index supersedes old checkpoint-absence/initial-download notes without changing historical evidence.

## Completed and linked

- Taxonomy-specific CIHP/LIP class10 correction, all-prediction/original-grid validation, runner scoring gates, failure lifecycle, deterministic matching and explicit dependency fingerprints implemented.
- {validation['tests']} CPU tests passed; 126 protected hashes unchanged at the recorded handoff validation.
- 21 native checkpoint/component FP32 smokes passed on one fixed TRAIN image each; CPI canonical packets verified in 8 cases. No model ranking from smoke.
- CDGNet `LIP_epoch_149.pth` downloaded from the author-linked Google Drive folder; SHA256 and CPU tensor inspection passed. GPU inference not performed; ImageNet initializer is not required by official evaluation.
- [Current registry V6](../provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv), [checkpoint inventory](../provenance/CHECKPOINT_INVENTORY_CURRENT_V1.json), [artifact index](../provenance/CURRENT_STUDY_ARTIFACTS.json).

## Next work and actual gates

| Work | Current state / next action |
|---|---|
| Primary population / GT semantics | Review accepted evidence and G_loc/G_sem/domain definitions; preserve official and overlap-controlled populations separately |
| Common body/clothing view | Mapping V2 remains DRAFT; keep CIHP/LIP support differences explicit; do not fabricate exposed-torso support for LIP |
| Failure scoring | Choose strict-complete versus explicit operational fallback before benchmark; both mechanisms tested |
| Matching / box source | Accept threshold, evaluation geometry source and deterministic matching definition; conditioning box stays separate |
| First comparison route | Verify only the actual route/profile needed for the first accepted cohort; native smoke alone is insufficient |
| CDGNet | Close architecture/environment and applicable-license gaps before live model execution; no duplicate checkpoint download needed |
| Cached scoring / workflow resume | Disabled; implement only if required, with actual-path validation |
| Sapiens2 | Retain historical technical passes independently from use eligibility; 5B excluded for resources |
| Benchmark / VAL / CCTV | Separate future authorization; not started by the current evidence |

[Implementation and A01–A20](APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md) · [Detailed policy choices](APPLICATION_HANDOFF_POLICIES_TH_20261015.md) · [Protocol review](PROTOCOL_REVIEW.md).

The earlier long chronology is [archived unchanged](../{(archive/'reports/STAGE0_NEXT_ACTIONS.md').relative_to(S)}). It is not an active instruction to repeat dataset downloads or old audits. PPSS remains paused, and datasets/YOLO results stay unchanged.
''')

# Preserve detailed older reports, but clearly date their execution-status claims.
for name in ['reports/STAGE0_FEASIBILITY_REPORT.md', 'reports/TAXONOMY_AUDIT.md']:
    p = S / name
    t = p.read_text()
    title, body = t.split('\n', 1)
    banner = '\n\n> Current update — 15 October 2026: the body below is the historical initial audit. Current acquisition/inference status is in [Model Compatibility](MODEL_COMPATIBILITY_REPORT.md), [current artifact index](../provenance/CURRENT_STUDY_ARTIFACTS.json), and [handoff validation](APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md). Old zero-checkpoint/zero-smoke statements are historical; scientific taxonomy acceptance remains pending.\n\n## Historical initial-audit evidence\n'
    p.write_text(title + banner + body)

p = S / 'reports/PROTOCOL_REVIEW.md'
t = p.read_text()
t = t.replace('| Checkpoints | Official links inspected, zero weights downloaded; user deferred large files | Revisit explicit bounded download approval after source/dataset review | No model SMOKE_PASS |', '| Checkpoints | Current registry V6: native smokes exist for 21 checkpoints/components; CDGNet now downloaded and tensor-inspected | Review actual route/capability before cohort readiness; no duplicate acquisition | Native passes do not authorize full benchmark |')
t = t.replace('| Native CUDA stacks | nvcc absent; M2FP/D2FP/SCHP require CUDA compilation, CPI may support a compatible binary MMCV stack | Review one pinned isolated stack per candidate; no system driver/toolkit edits or arbitrary retries | Native environments not ready |', '| Native CUDA stacks | Existing isolated legacy stack executed the recorded native smokes; user-space toolchain and restored PATH used | Retain tested environment/profile; no system driver/toolkit changes | Per-model evidence in current compatibility report |')
t = t.replace('**Stage 1 freeze: BLOCKED.**', '**Stage 1 freeze: BLOCKED pending scientific decisions, not blanket absence of downloaded weights.** Current model status: [compatibility report](MODEL_COMPATIBILITY_REPORT.md), [registry V6](../provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv).')
p.write_text(t)

# Dated research report stays a run snapshot; annotate the later correction.
p = S / 'reports/APPLICATION_HANDOFF_IMPLEMENTATION_TH_20261015.md'
t = p.read_text();title, body = t.split('\n',1)
t = title + '\n\n> อัปเดตภายหลัง: CDGNet ดาวน์โหลดจาก Google Drive ทางการและตรวจ tensor แล้ว ดู [ผลล่าสุด](CDGNET_ACQUISITION_TH_20261015.md), [registry V6](../provenance/MODEL_VARIANT_REGISTRY_HANDOFF_V6.csv) และ [current artifact index](../provenance/CURRENT_STUDY_ARTIFACTS.json) จำนวนและสถานะ DOWNLOAD_NOT_OBTAINED ในเนื้อหารอบ handoff ด้านล่างเป็นหลักฐานก่อนการแก้ acquisition นี้\n' + body
p.write_text(t)

state_path = S / 'STUDY_STATE.json'
state = json.loads(state_path.read_text())
state['last_updated_utc'] = current['updated_utc']
state['current_artifacts'] = {'index': 'provenance/CURRENT_STUDY_ARTIFACTS.json',
                            'registry': str(registry_path.relative_to(S)),
                            'checkpoint_inventory': 'provenance/CHECKPOINT_INVENTORY_CURRENT_V1.json',
                            'CPU_tests_last_executed': validation['tests'],
                            'native_smokes_last_handoff': len(smokes),
                            'checkpoint_artifacts_unique': len(unique),
                            'CDGNet_downloaded': True, 'CDGNet_model_inference': False,
                            'full_benchmark': False}
atomic(state_path, state)
for item in before:
    item['after_sha256'] = sha(S / item['path'])
    item['reason'] = 'Synchronize active navigation/status; retain historical evidence and execution boundaries'
atomic(R / 'CHANGES.json', before)
atomic(S / 'provenance/CURRENT_STATUS_SYNC_ACTIVE.json', {'run': str(R.relative_to(S))})
print(json.dumps({'run': str(R.relative_to(S)), 'current_registry': str(registry_path.relative_to(S)),
                  'unique_checkpoint_artifacts': len(unique), 'documents_updated': len(names),
                  'CPU_tests_reexecuted': False, 'model_inference': False}, indent=2))
