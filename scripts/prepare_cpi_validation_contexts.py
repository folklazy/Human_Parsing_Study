"""Read-only full GT/domain binding materialization, no prediction/model evaluation."""
from pathlib import Path
from io import BytesIO
import argparse
import copy
import hashlib
import json
import sys
import zipfile
import numpy as np
from PIL import Image

S = Path(__file__).resolve().parents[1]
W = S.parent
sys.path.insert(0, str(S))
from src.application_v2.policy import load_config, digest
from src.application_v2.artifacts import file_hash
from src.application_v2.taxonomy import project_gt
from src.application_v2.evaluation import person_truth
from src.application_v2.contexts import validate_context_registry
from src.application_v2.scoring import check_context


def pixels_hash(array):
    return digest(dict(shape=list(array.shape), dtype=str(array.dtype),
                       bytes_sha256=hashlib.sha256(array.tobytes()).hexdigest()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    mapping = json.loads((S / cfg['cohort']['mapping']).read_text())
    projection = digest({key: mapping[key] for key in ['target_catalog', 'gt_mapping']})
    if projection != cfg['first_cohort']['protocol']['mapping']['GT_projection_sha256']:
        raise ValueError('Accepted GT projection changed')
    populations = cfg['first_cohort']['protocol']['population']
    main_path = S / populations['main_manifest']
    ref_path = S / populations['reference_manifest']
    for path, expected in [(main_path, populations['main_manifest_sha256']),
                           (ref_path, populations['reference_manifest_sha256'])]:
        if file_hash(path) != expected:
            raise ValueError('Accepted source population changed')
    main_rows = [json.loads(line) for line in main_path.open()]
    frames = [json.loads(line) for line in ref_path.open()]
    main_ids = {row['image_id'] for row in main_rows}
    if len(main_rows) != 4961 or len(frames) != 5000 or len(main_ids) != len(main_rows):
        raise ValueError('Declared fixed population size mismatch')
    audit_path = S / 'provenance/RUN_MANIFESTS/stage0f-ccihp-quality-20261012T062825Z/IMAGE_AUDIT.jsonl'
    audit = {row['image_id']: row for row in (json.loads(line) for line in audit_path.open()) if row['split'] == 'Validation'}
    templates = {model: copy.deepcopy(next(iter(rows.values()))) for model, rows in cfg['scoring_contexts'].items()}
    for context in templates.values():
        context.pop('input_binding')
        context['domain'].pop('image_binding')
        context['scope'] = 'MATERIALIZED_VALIDATION_BINDING_NOT_ACTIVE_EXECUTION_AUTHORIZATION'
    model_registry = {model: {} for model in templates}
    bindings, person_rows = [], 0
    archive = W / 'datasets/CCIHP_icip.zip'
    source_stat = dict(bytes=archive.stat().st_size, mtime_ns=archive.stat().st_mtime_ns)
    with zipfile.ZipFile(archive) as z, (out / 'PERSON_GT_BINDINGS.jsonl').open('x') as persons:
        for index, frame in enumerate(frames):
            iid, wh = frame['image_id'], frame['original_wh']
            previous = audit[iid]
            if previous['GT_decode'] != 'PASS' or previous['RGB_decode'] != 'PASS' or previous['RGB_wh'] != wh or previous['wh'] != wh or previous['source_maps'] != frame['source_maps']:
                raise ValueError('Prior image/GT audit binding differs: ' + iid)
            maps = {}
            for source in frame['source_maps']:
                raw = z.read(source['member'])
                if hashlib.sha256(raw).hexdigest() != source['sha256']:
                    raise ValueError('Original GT member hash mismatch: ' + source['member'])
                if source['component'] in ['Category_ids', 'Human_ids']:
                    with Image.open(BytesIO(raw)) as image:
                        image.load(); a = np.array(image)
                    if [a.shape[1], a.shape[0]] != wh or str(a.dtype) != source['dtype']:
                        raise ValueError('Source GT grid/encoding mismatch')
                    maps[source['component']] = a
            category, human = maps['Category_ids'], maps['Human_ids']
            target, valid = project_gt(category, human, mapping)
            gt = []
            for pid in np.unique(human):
                if not pid:
                    continue
                truth, per_valid = person_truth(target, human, valid, int(pid))
                y, x = np.nonzero(human == pid)
                row = dict(image_id=iid, person_id=int(pid),
                    bbox_xyxy_half_open=[int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1],
                    G_loc=True, G_sem=bool(((truth > 0) & per_valid).any()),
                    semantic_sha256=pixels_hash(truth), valid_sha256=pixels_hash(per_valid))
                persons.write(json.dumps(row, separators=(',', ':')) + '\n')
                gt.append(row); person_rows += 1
            G_loc, G_sem = len(gt), sum(row['G_sem'] for row in gt)
            if (G_loc, G_sem) != (frame['G_loc'], frame['G_sem']):
                raise ValueError('GT denominators differ from accepted manifest: ' + iid)
            recipe = dict(image_id=iid, source_maps=frame['source_maps'], original_wh=wh,
                GT_projection_sha256=projection, domain_policy_sha256=cfg['first_cohort']['protocol']['domain']['policy_sha256'])
            image_domain = dict(image_id=iid, G_loc=G_loc, G_sem=G_sem, GT_domain_recipe_sha256=digest(recipe),
                decoded_GT_contract_sha256=digest(dict(category=pixels_hash(category), human=pixels_hash(human),
                    target=pixels_hash(target), global_valid=pixels_hash(valid), persons=gt)))
            trusted = dict(status='VERIFIED', image_id=iid, original_wh=wh, dataset='CCIHP', split='Validation',
                input_sha256=previous['RGB_sha256'], input_hash_kind='ORIGINAL_RGB_JPEG_BYTES',
                decoded_RGB_sha256=previous['RGB_decoded_sha256'],
                verification='PRIOR_FULL_READONLY_RGB_AUDIT_REUSED_RECHECK_BYTES_BEFORE_FUTURE_INFERENCE')
            bound = dict(image_id=iid, G_loc=G_loc, G_sem=G_sem, main=iid in main_ids,
                input_binding=trusted, image_domain_binding=image_domain, source_GT=frame['source_maps'])
            bindings.append(bound)
            for model, template in templates.items():
                context = {**template, 'input_binding': trusted,
                           'domain': {**template['domain'], 'image_binding': image_domain}}
                model_registry[model][iid] = context
            if (index + 1) % 1000 == 0:
                print(f'[GT CONTEXTS] {index + 1}/5000: verified; no inference', flush=True)
    if source_stat != dict(bytes=archive.stat().st_size, mtime_ns=archive.stat().st_mtime_ns):
        raise ValueError('Original annotation archive stat changed during read-only processing')
    checks = {}
    for name, rows in [('reference', frames), ('main', main_rows)]:
        ids = [row['image_id'] for row in rows]
        candidate = copy.deepcopy(cfg)
        candidate['scoring_population'] = [{k: row[k] for k in ['image_id', 'G_loc', 'G_sem']} for row in rows]
        candidate['scoring_contexts'] = {model: {iid: registry[iid] for iid in ids} for model, registry in model_registry.items()}
        validate_context_registry(candidate)
        for model in templates:
            # All per-image fields are checked by the registry; shared evidence was
            # validated once by load_config, then check the full context contract.
            context = candidate['scoring_contexts'][model][ids[0]]
            check_context(context, mapping, context['model_binding'], context['input_binding'])
        checks[name] = dict(images=len(ids), contexts=len(ids) * len(templates),
            G_loc_per_system=sum(row['G_loc'] for row in rows), G_sem_per_system=sum(row['G_sem'] for row in rows),
            context_registry_validation='PASS')
    with (out / 'IMAGE_BINDINGS.jsonl').open('x') as stream:
        for row in bindings:
            stream.write(json.dumps(row, separators=(',', ':')) + '\n')
    with (out / 'MODEL_CONTEXT_TEMPLATES.json').open('x') as stream:
        json.dump(templates, stream, indent=2)
    result = dict(status='MATERIALIZED_AND_STRUCTURALLY_VALIDATED_NOT_ACTIVATED',
        storage='Lossless context templates + ordered per-image bindings; expand without changing content',
        context_status_scope='Derived from accepted policies, not a new full-benchmark execution decision',
        populations=checks, source_GT_member_hashes_checked=15000, person_bindings=person_rows,
        original_GT_archive_stat_unchanged=True, full_RGB_audit_reused=True, new_RGB_decode=False,
        new_GT_domain_reconstruction=True, predictions_read=False, new_inference=False, scores_computed=False,
        current_executable_config_unchanged=True, scoring_activation='PENDING_VERSIONED_CONFIG_DECISION_BINDING',
        GT_projection_sha256=projection, domain_policy_sha256=cfg['first_cohort']['protocol']['domain']['policy_sha256'],
        source_image_audit_sha256=file_hash(audit_path), source_manifests_sha256=dict(main=file_hash(main_path), reference=file_hash(ref_path)),
        artifacts={p.name: file_hash(p) for p in out.iterdir() if p.is_file()}, script_sha256=file_hash(Path(__file__)))
    with (out / 'MANIFEST.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(dict(status=result['status'], populations=checks, inference=False, scoring=False)), flush=True)


if __name__ == '__main__':
    main()
