"""Verify existing validation bindings without activating validation execution."""
import json
from .artifacts import file_hash
from .policy import digest


def validate_packages(config, study):
    spec = config['validation_context_packages']
    if spec['execution_authorized'] or spec['role'] != 'PREPARATION_ONLY':
        raise ValueError('Validation package binding grants no execution permission')
    def read(relative, expected):
        path = (study / relative).resolve()
        if not path.is_relative_to(study.resolve()) or file_hash(path) != expected:
            raise ValueError('Validation package path/hash mismatch')
        return path
    manifest_path = read(spec['manifest'], spec['manifest_sha256'])
    manifest = json.loads(manifest_path.read_text())
    files = {}
    for name, checksum in manifest['artifacts'].items():
        # Historical manifest stores artifact hashes, with optional path metadata.
        expected = checksum if isinstance(checksum, str) else checksum['sha256']
        files[name] = read(str((manifest_path.parent / name).relative_to(study)), expected)
    templates = json.loads(files['MODEL_CONTEXT_TEMPLATES.json'].read_text())
    if set(templates) != set(config['first_cohort']['models']):
        raise ValueError('Validation package roster mismatch')
    for system, template in templates.items():
        train = next(iter(config['scoring_contexts'][system].values()))
        for key in ['model_binding', 'mapping_sha256', 'domain', 'support_binding', 'threshold',
                    'failure_policy', 'evaluation_bbox_source', 'target_support_policy']:
            left, right = template[key], train[key]
            if key == 'domain':
                right = {k: v for k, v in right.items() if k != 'image_binding'}
            if left != right:
                raise ValueError('Validation template differs from selected model/scoring policy: ' + key)
    protocol = config['first_cohort']['protocol']
    if manifest['GT_projection_sha256'] != protocol['mapping']['GT_projection_sha256'] or manifest['domain_policy_sha256'] != protocol['domain']['policy_sha256']:
        raise ValueError('Validation package GT projection/domain changed')
    images = [json.loads(line) for line in files['IMAGE_BINDINGS.jsonl'].read_text().splitlines()]
    if len({r['image_id'] for r in images}) != len(images):
        raise ValueError('Duplicate validation image binding')
    result = {}
    for role in ['main', 'reference']:
        source = read(protocol['population'][role + '_manifest'], protocol['population'][role + '_manifest_sha256'])
        declared = [json.loads(line) for line in source.read_text().splitlines()]
        rows = [r for r in images if role == 'reference' or r['main']]
        if {r['image_id']: (r['G_loc'], r['G_sem']) for r in rows} != {r['image_id']: (r['G_loc'], r['G_sem']) for r in declared}:
            raise ValueError('Validation population identity/denominator mismatch')
        counts = dict(images=len(rows), contexts=len(rows)*len(templates),
                      G_loc=sum(r['G_loc'] for r in rows), G_sem=sum(r['G_sem'] for r in rows))
        if any(counts[k] != spec['populations'][role][k] for k in counts):
            raise ValueError('Validation package population counts differ from accepted config')
        result[role] = counts
    return dict(status='PASS_BOUND_NOT_AUTHORIZED', populations=result,
                package_manifest_sha256=file_hash(manifest_path), config_sha256=digest(config),
                GT_regenerated=False, validation_inference=False)
