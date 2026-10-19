"""Archive and update active policy/navigation only; preserve historical evidence."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
from copy import deepcopy
import difflib
import json
import yaml

S=Path(__file__).resolve().parents[1]


def main():
    active=json.loads((S/'provenance/DATASET_REASSESSMENT_ACTIVE_RUN.json').read_text())
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive=S/'reports/archive'/f'dataset_reassessment_{stamp}'
    archive.mkdir(parents=True,exist_ok=False)
    entries=[]
    def replace(path,text,reason):
        previous=path.read_bytes()
        relative=path.relative_to(S) if path.is_relative_to(S) else Path('WORKSPACE_README.md')
        backup=archive/relative;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(previous)
        new=text.encode()
        temporary=path.with_suffix(path.suffix+'.reassessment.tmp');temporary.write_bytes(new);temporary.replace(path)
        diff=''.join(difflib.unified_diff(previous.decode().splitlines(True),text.splitlines(True),fromfile=str(relative),tofile=str(relative)))
        (backup.parent/(backup.name+'.diff')).write_text(diff)
        entries.append({'original_path':str(path.relative_to(S)) if path.is_relative_to(S) else '../README.md',
                        'archive':str(backup.relative_to(S)),'sha256_before':sha256(previous).hexdigest(),
                        'sha256_after':sha256(new).hexdigest(),'reason':reason,'timestamp_utc':stamp})
    replace(S/'README.md',"""# Human Parsing Study — Stage 0

**Dataset reassessment preparation: PASS_WITH_WARNINGS. Overall Stage 0: BLOCKED / WAITING_FOR_USER_APPROVAL. Stage 1 and benchmarks: NOT STARTED.**

CIHP is a **candidate primary** public body/clothing benchmark; MHP-v2 is a **provisional secondary** fine-grained benchmark. Roles and COMMON_HP are not frozen. PPSS remains paused; CCIHP/color/attributes are out of scope. Company CCTV images remain reserved for a later finalist field test. The existing directory/study ID is retained to preserve provenance.

## Current evidence and decisions

- [Dataset reassessment](reports/DATASET_REASSESSMENT.md): completed bounded preparation, exact populations and limitations.
- [CIHP availability / quality audit](reports/CIHP_QUALITY_AUDIT.md): absent locally; official archive metadata 2,033,753,964 bytes; acquisition and dataset permission pending.
- [MHP-v2 quality risks](reports/MHPV2_QUALITY_RISK_REVIEW.md): reuse, ownership uncertainty and independent train review.
- [Primary dataset decision](reports/PRIMARY_DATASET_DECISION.md): evidence matrix and provisional A direction, without claiming CIHP is cleaner.
- [Next bounded actions / approvals](reports/STAGE0_NEXT_ACTIONS.md): CIHP acquisition, research-only FASHN smoke proposal and open scientific decisions.
- [Current validation](provenance/DATASET_REASSESSMENT_VALIDATION.json), [51 executed tests](provenance/RUN_MANIFESTS/dataset-reassessment-20261008T095241Z/BOUNDED_TESTS_V2.json), [study state](STUDY_STATE.json).

## MHP-v2 readable views

Original data/splits remain unchanged. Train readable: **15,400 / 41,043 native GT persons**. Official-split readable validation: **4,999 / 13,257**. Exact train-overlap-controlled readable validation: **4,347 / 11,408**. Full official and controlled targets are retained separately. Readable-subset scores must disclose excluded files and denominators; no validation inference has run.

[Readable policy / fingerprints](provenance/MHPV2_READABLE_POLICY_V1.json), [official target](manifests/mhpv2_readable_v1/VALIDATION_OFFICIAL_TARGET.json), [readable validation](manifests/mhpv2_readable_v1/VALIDATION_READABLE.json), [controlled target](manifests/mhpv2_readable_v1/VALIDATION_OVERLAP_CONTROLLED_TARGET.json), [controlled readable view](manifests/mhpv2_readable_v1/VALIDATION_OVERLAP_CONTROLLED_READABLE.json).

Thirty independently sampled readable train images have native GT diagnostics and a [human checklist](reports/MHPV2_RANDOM_QUALITY_REVIEW_V1.csv), still pending. Pixel fidelity is verified; semantic ownership/error prevalence is not established. [CIHP's proposed 200-image stratified review](manifests/CIHP_QUALITY_REVIEW_PLAN_V1.json) has no IDs until the dataset exists.

## Contracts, environments and candidate metadata

[Scientific standard](STUDY_STANDARD.md), [draft tracks](EXPERIMENT_PROTOCOL_DRAFT.md), [schema](DATA_SCHEMA.md), [taxonomy audit](reports/TAXONOMY_AUDIT.md), [core](taxonomy/COMMON_HP_CORE_DRAFT.yaml) and [extended](taxonomy/COMMON_HP_EXTENDED_DRAFT.yaml) retain layer/cohort separation. [CIHP concept proposal](taxonomy/CIHP_COMMON_HP_PROPOSAL_V1.yaml) is not an executable mapping.

[Variant registry V2](provenance/MODEL_VARIANT_REGISTRY_V2.csv) distinguishes backbones, dataset weights and training schedules. There are **zero downloaded/loaded/smoke-passed parser checkpoints**. FASHN environment imports and a historical synthetic T4 FP32 check are not checkpoint inference. Sapiens2 remains excluded from surveillance-related execution pending applicable permission.

Shared assets stay outside the study: workspace `datasets/`, `models/human_parsing/`, `third_party/human_parsing/`, `.venvs/`. The YOLO environment, benchmark repositories and frozen YOLO26x checkpoint are preserved. No heavyweight packages/weights/datasets downloaded in this continuation; only bounded source/HTML metadata was fetched. No Git remote created or push performed.

## Historical evidence

[Original Stage 0 gates](provenance/STAGE0_VALIDATION.json), [feasibility report](reports/STAGE0_FEASIBILITY_REPORT.md), [original dataset audit](reports/MHPV2_DATASET_AUDIT.md), [raw dataset manifest](manifests/DATASET_MANIFEST.json), [model registry V1](provenance/MODEL_REGISTRY.csv), [original leakage audit](manifests/LEAKAGE_AUDIT.json) and [ZIP verification](reports/MHPV2_NEW_ZIP_RGB_VERIFICATION.md) are preserved. Their historical raw-data blockers are not rewritten as repaired inputs; current approved views and wrapper evidence supersede specific policies, without altering historical results.

[Archive/hash record](provenance/DATASET_REASSESSMENT_DOCUMENT_REVISIONS.json), [reproducibility](REPRODUCIBILITY.md) and [references](REFERENCES.md) support traceability. **STOP: wait for approval before acquisition, checkpoint execution, Stage 1 or any field test.**
""",'Reflect user-approved flexible dataset roles and bounded current evidence')
    standard=(S/'STUDY_STANDARD.md').read_text().replace('Version: `0.1-DRAFT`','Version: `0.2-DRAFT`')
    standard=standard.replace('Required RGB/GT decoding failures block MHP-dependent inference.',
        'Required decoding failures block use of the affected samples. The user-approved versioned readable views preserve originals and explicitly record exclusions/denominators. Bounded feasibility on verified readable TRAIN samples is scientifically independent of final benchmark readiness, but model licenses and execution approval are still required.')
    standard+='''
## Dataset reassessment amendment — 2026-10-08

Do not assume MHP-v2 must remain primary. CIHP is candidate primary; MHP-v2 provisional secondary; roles are not frozen. PPSS remains paused, CCIHP is future color/characteristics work, and unlabeled company CCTV is reserved for later authorized finalist field testing.

Keep full official and exact-overlap-controlled targets separate from their readable views. No source image/GT/list repair or deletion. A 4,999-image score must identify the readable subset; overlap-controlled sensitivity is a separate benchmark condition and does not guarantee content/pretraining independence.

File decode and lossless-coordinate fidelity do not prove GT physical ownership. Independent randomized/stratified quality samples retain uncertain outcomes; purposive anomaly examples do not estimate prevalence. No annotation relabel/exclusion beyond approved unreadable views without a documented decision.

Native and common-class metrics remain separate; dataset-specific raw mIoU scores are not pooled. The official evaluator compatibility wrapper is separate, pinned and synthetic-tested. Empty predictions with positive GT support give zero AP/PCP; zero GT support is undefined. Nine-threshold AP-volume is explicitly reference-derived; synthetic parity does not establish published-benchmark or CIHP evaluator parity.
'''
    replace(S/'STUDY_STANDARD.md',standard,'Accepted readable-view gate and unfrozen dataset suitability')
    protocol=(S/'EXPERIMENT_PROTOCOL_DRAFT.md').read_text().replace('Version `0.1-DRAFT`','Version `0.2-DRAFT`')
    protocol=protocol.replace('Dataset RGB corruption, GT ownership diagnostics, exact split overlap and unexecuted checkpoint smoke tests currently block Stage 1.',
        'Readable-view preparation is approved and completed; dataset-role selection, GT-quality review, exposure disclosure, candidate permissions and unexecuted checkpoint smoke tests still block Stage 1.')
    protocol=protocol.replace('Development and timing manifests are train-only and currently draft/blocked.',
        'Development and timing workloads remain train-only and draft; use approved readable input IDs where applicable, without authorizing inference.')
    protocol=protocol.replace('A separately approved train-overlap-excluded sensitivity result could supplement them;',
        'The user-approved exact train-overlap-controlled readable population is prepared for a future separately reported sensitivity result;')
    protocol=protocol.replace('Five synthetic fixtures passed through minimally ported official functions. The upstream empty-prediction path raises an IndexError; a reviewed zero-input compatibility fix and broader official/native parity tests are required before a native benchmark. No approximate custom metric is relabeled official.',
        'The original upstream empty-prediction path remains unchanged. A separate pinned compatibility wrapper now passes 19 synthetic evaluator tests, including nine-threshold AP-volume, native confidence/matching, duplicates, overlap and zero support. All 51 contract/evaluator/population tests pass. Nonempty cases delegate the original evaluator functions; no-GT is undefined and all-missed supported GT gives zero. Published-result and CIHP-specific official parity remain unclaimed.')
    protocol=protocol.replace('Resolve or explicitly approve a non-destructive handling policy for four unreadable RGB files;',
        'Use the approved readable views with named denominators;')
    protocol+='''
## Dataset populations and role selection amendment

CIHP is a candidate primary and MHP-v2 provisional secondary; no final role freeze or shared universal score is authorized. CIHP is absent locally: source taxonomy/archive metadata are not a GT-quality audit. Inspect native Human_ids versus part Instance_ids and preserve original pixel semantics before adopting any reader.

MHP full official validation target: 5,000 images / 13,260 native persons; official-split readable: 4,999 / 13,257. Exact train-overlap-controlled target: 4,348 / 11,411; controlled readable: 4,347 / 11,408. Train readable: 15,400 / 41,043. Keep each manifest and exposure/duplicate warning explicit. Do not present unreadable subsets as unqualified full official scores or merge scores across populations/datasets.

Random/stratified GT review belongs to TRAIN; final validation integrity/leakage audits are read-only and do not authorize threshold/taxonomy/crop tuning. Quality failures remain reported, with no silent source repairs or favorable class denominators. Company CCTV remains unlabeled and untested; quantitative field testing needs a separately approved annotation/evaluation design.

See reports/STAGE0_NEXT_ACTIONS.md for bounded acquisition/checkpoint proposals. Neither the readable policy nor evaluator tests authorize Stage 1, parser inference, downloads or field testing.
'''
    replace(S/'EXPERIMENT_PROTOCOL_DRAFT.md',protocol,'Draft protocol reflects approved populations, tested wrapper and pending primary selection')
    schema=(S/'DATA_SCHEMA.md').read_text()+'''
## Readable-population and reassessment schemas — v1

`manifests/mhpv2_readable_v1/` separates full targets and readable views. Each contains population/policy version, official split, ordered IDs and ID digest, RGB source hashes, native GT counts, explicit exclusion reasons, upstream manifest/index/evidence hashes, scope flags and score limitations. Per-person source annotation/array hashes resolve through the immutable canonical GT index. These are views, not modified original splits.

`MHPV2_RANDOM_QUALITY_REVIEW_V1.json` records seed, sampling frame/probability and draw order before viewing GT. Each diagnostic records source and output hashes. Human-review CSV status remains pending until actual reviewer decisions; numerical grid fidelity is distinct from physical-person correctness. CIHP review plan has no fabricated image IDs or measured quality fields while acquisition is pending.

`official_mhp_compat.py` pins both official evaluator and VOC helper hashes. Its fractional outputs record GT/prediction support, threshold, wrapper/source version and defined/undefined status. Zero GT support serializes as null; AP-volume averages nine fresh reference calls. No learned confidence or GT-guided prediction is manufactured. These tests are synthetic, not final dataset results.

`MODEL_VARIANT_REGISTRY_V2.csv` separates backbone capacity, dataset-specific weights and training schedules. Provider checkpoint bytes are metadata, local weight SHA256 is NOT_DOWNLOADED, and no import success is a checkpoint smoke pass. Current validation is separate from immutable historical Stage 0 validation.
'''
    replace(S/'DATA_SCHEMA.md',schema,'Document versioned population, quality-review and wrapper evidence contracts')
    config=yaml.safe_load((S/'configs/study.yaml').read_text())
    config['schema_version']='1.1';config['status']='STAGE0_REASSESSMENT_WAITING_FOR_APPROVAL'
    config['dataset_roles_draft']={'CIHP':'CANDIDATE_PRIMARY','MHP-v2':'PROVISIONAL_SECONDARY','CCIHP':'FUTURE_CHARACTERISTICS_COLOR','PPSS':'PAUSED'}
    config['primary_dataset_frozen']=False
    config['stage0']['readable_view_policy']='manifests/mhpv2_readable_v1/'
    config['review_required']=[r for r in config['review_required'] if not r.startswith(('Required RGB','Native evaluator empty'))]
    config['review_required']+=['CIHP acquisition/permission and independent quality audit','Primary dataset roles; native/common cohorts','Independent MHP GT-quality review; wrapper published/native parity limitations']
    replace(S/'configs/study.yaml',yaml.safe_dump(config,sort_keys=False),'Draft roles and approved readable preparation; inference flags remain false')
    config=yaml.safe_load((S/'configs/dataset.yaml').read_text())
    config['source_integrity_status']=config['status'];config['status']='READABLE_VIEWS_PREPARED_WITH_QUALITY_WARNINGS'
    config['readable_policy']='provenance/MHPV2_READABLE_POLICY_V1.json'
    config['readable_views']={'train':'manifests/mhpv2_readable_v1/TRAIN_READABLE.json',
        'validation':'manifests/mhpv2_readable_v1/VALIDATION_READABLE.json',
        'validation_exact_overlap_controlled':'manifests/mhpv2_readable_v1/VALIDATION_OVERLAP_CONTROLLED_READABLE.json'}
    config['source_originals_repaired']=False;config['benchmark_execution_authorized']=False
    replace(S/'configs/dataset.yaml',yaml.safe_dump(config,sort_keys=False),'Source remains defective; versioned approved views are explicit')
    state=json.loads((S/'STUDY_STATE.json').read_text());paused=deepcopy({k:v for k,v in state.items() if k.startswith('ppss')})
    state['primary_benchmark']='UNDECIDED';state['dataset_roles_draft']={'CIHP':'CANDIDATE_PRIMARY','MHP-v2':'PROVISIONAL_SECONDARY','CCIHP':'FUTURE_CHARACTERISTICS_COLOR'}
    state['last_updated_utc']=datetime.now(timezone.utc).isoformat()
    state['dataset_reassessment']={'run_id':active['run_id'],'preparation_status':'PASS_WITH_WARNINGS',
        'overall_stage0_status':'BLOCKED','primary_roles_frozen':False,'readable_policy_approved':True,
        'train_readable_images':15400,'validation_readable_images':4999,'validation_readable_native_persons':13257,
        'controlled_readable_images':4347,'controlled_readable_native_persons':11408,
        'original_validation_target_preserved':True,'CIHP_local_status':'ABSENT_ACQUISITION_AWAITING_APPROVAL',
        'random_MHP_quality_sample_images':30,'human_quality_review':'PENDING','annotation_error_prevalence':'NOT_ESTIMATED',
        'executed_tests_passed':51,'actual_checkpoint_smokes_passed':0,'taxonomy_status':'DRAFT',
        'benchmark_started':False,'validation_inference':False,'report':'reports/DATASET_REASSESSMENT.md',
        'validation':'provenance/DATASET_REASSESSMENT_VALIDATION.json'}
    assert {k:v for k,v in state.items() if k.startswith('ppss')}==paused
    replace(S/'STUDY_STATE.json',json.dumps(state,ensure_ascii=False,indent=2)+'\n','Append current reassessment; preserve historical/paused nodes')
    root=S.parent/'README.md';text=root.read_text();lines=text.splitlines(True)
    text=''.join(lines[:2])+'''## Human Parsing dataset reassessment — 2026-10-08

[Current reassessment](Human_Parsing_MHPv2_Study/reports/DATASET_REASSESSMENT.md) prepares approved MHP-v2 readable views (train 15,400; validation 4,999; exact-train-overlap-controlled validation 4,347), 30 random TRAIN GT diagnostics and a separately pinned evaluator wrapper. 51 bounded tests passed; no parser/checkpoint inference or full benchmark ran. CIHP is absent locally: its official archive metadata is 2,033,753,964 bytes; acquisition/quality/license review awaits approval. CIHP candidate-primary and MHP-v2 provisional-secondary roles are not frozen. PPSS remains paused; previous YOLO assets are unchanged. See the [study landing page](Human_Parsing_MHPv2_Study/README.md). Earlier sections below are historical and do not override the current review gate; the newly transferred ZIP now exists and matches its earlier recorded hash.

'''+''.join(lines[2:])
    replace(root,text,'Keep workspace navigation current without rewriting historical sections')
    p=S/'provenance/DATASET_REASSESSMENT_DOCUMENT_REVISIONS.json';assert not p.exists()
    p.write_text(json.dumps({'run_id':active['run_id'],'entries':entries,'historical_validation_and_datasets_modified':False},indent=2)+'\n')
    print(f'[DOCS] archived {len(entries)} active files; current roles/protocol/state updated; historical evidence retained')


if __name__=='__main__':main()
