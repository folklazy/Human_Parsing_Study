"""Checkpoint-specific capability membership. Dataset names are not evidence."""
from .policy import digest


def verify_channel_header(record, model_binding, *, study_root=None):
    """Verify direct header bytes/order and explicit release provenance, not head size."""
    from pathlib import Path
    import hashlib
    import json
    if not isinstance(record, dict) or record.get('status') != 'DIRECT_VERIFIED':
        raise ValueError('Channel order gate blocked: direct official header/release evidence missing')
    if record.get('proof_kind') not in {'OFFICIAL_ANNOTATION_JSON_HEADER', 'OFFICIAL_AUTHOR_CLASS_ORDER'}:
        raise ValueError('Indirect class catalogs cannot satisfy the channel order gate')
    if record.get('checkpoint_sha256') != model_binding['checkpoint_sha256'] or record.get('source_commit') != model_binding['source_commit']:
        raise ValueError('Channel order evidence is not linked to this checkpoint/source release')
    if record.get('provenance_review') != 'VERIFIED' or not record.get('official_source_url') or not record.get('release_relationship_evidence'):
        raise ValueError('Official provenance and checkpoint-release relationship must be reviewed')
    root = Path(study_root) if study_root is not None else Path(__file__).resolve().parents[2]
    document = (root / record.get('document', '')).resolve()
    if not document.is_relative_to(root.resolve()) or not document.is_file():
        raise ValueError('Direct channel evidence document is missing or outside the study')
    data = document.read_bytes()
    if hashlib.sha256(data).hexdigest() != record.get('document_sha256'):
        raise ValueError('Direct channel evidence document hash mismatch')
    payload = json.loads(data)
    names = (payload['categories'][0]['parsing'] if record['proof_kind'] == 'OFFICIAL_ANNOTATION_JSON_HEADER'
             else payload['native_class_order'])
    if names != model_binding['native_class_order']:
        raise ValueError('Official channel header differs from the bound native class order')
    return True


def verify_channel_evidence(record, model_binding, *, study_root=None, accepted_statuses=None):
    """Keep direct verification distinct from explicitly accepted converging evidence."""
    from pathlib import Path
    import hashlib
    import json
    statuses = accepted_statuses if accepted_statuses is not None else ['DIRECT_VERIFIED']
    if not isinstance(record, dict) or record.get('status') not in statuses:
        raise ValueError('Channel order gate blocked: direct official header or accepted evidence policy required')
    if record['status'] == 'DIRECT_VERIFIED':
        return verify_channel_header(record, model_binding, study_root=study_root)
    if record['status'] != 'ACCEPTED_WITH_INDIRECT_EVIDENCE':
        raise ValueError('Unknown channel evidence confidence level')
    if record.get('proof_kind') != 'CONVERGING_PAPER_RELEASE_CONFIG_SOURCE_AND_TRAIN_REVIEW':
        raise ValueError('Converging channel evidence bundle required')
    if record.get('checkpoint_sha256') != model_binding['checkpoint_sha256'] or record.get('source_commit') != model_binding['source_commit']:
        raise ValueError('Channel order evidence is not linked to this checkpoint/source release')
    if record.get('expected_native_class_order') != model_binding['native_class_order']:
        raise ValueError('Accepted channel catalog differs from the bound native class order')
    if record.get('provenance_review') != 'ACCEPTED_WITH_INDIRECT_EVIDENCE' or not record.get('policy_decision_id'):
        raise ValueError('Explicit accepted evidence-policy provenance required')
    root = (Path(study_root) if study_root is not None else Path(__file__).resolve().parents[2]).resolve()
    required = {'PUBLISHED_PAPER_REPOSITORY_LINK', 'OFFICIAL_RELEASE_TABLE',
                'CHECKPOINT_EMBEDDED_CONFIG', 'NUMERIC_PROCESSING_SOURCE_TRACE',
                'SAVED_TRAIN_BEHAVIORAL_REVIEW'}
    components = record.get('components', {})
    if set(components) != required:
        raise ValueError('Incomplete converging channel evidence components')
    for name, artifact in components.items():
        path = (root / artifact['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Channel evidence component is missing or outside the study')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != artifact.get('sha256'):
            raise ValueError('Channel evidence component hash mismatch')
        if name == 'SAVED_TRAIN_BEHAVIORAL_REVIEW':
            review = json.loads(data)
            if review.get('status') != 'COMPLETED' or review.get('blocking_mapping_contradiction_found') is not False:
                raise ValueError('Bounded TRAIN mapping review is incomplete or contradictory')
            if review.get('all_classes_correct_required') is not False:
                raise ValueError('Mapping review must not become an accuracy-selection gate')
    return True


def read_channel_gate(config, study_root=None):
    from pathlib import Path
    import hashlib
    import json
    gate = config.get('first_cohort', {}).get('channel_order_evidence')
    if not gate or not gate.get('required'):
        return None
    root = Path(study_root) if study_root is not None else Path(__file__).resolve().parents[2]
    path = (root / gate['manifest']).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Channel evidence manifest must remain inside the study')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != gate['manifest_sha256']:
        raise ValueError('Channel evidence manifest changed without a versioned config')
    return json.loads(data)


def require_config_channel_order(config, model_binding, *, study_root=None):
    gate = read_channel_gate(config, study_root)
    if gate is None:
        return True
    records = [record for model, record in gate['models'].items()
               if model in config['first_cohort']['models'] and record['checkpoint_sha256'] == model_binding['checkpoint_sha256']]
    if len(records) != 1:
        raise ValueError('Channel evidence does not uniquely identify the selected checkpoint')
    policy = config['first_cohort']['channel_order_evidence']
    if records[0].get('status') == 'ACCEPTED_WITH_INDIRECT_EVIDENCE' and records[0].get('policy_decision_id') != policy.get('evidence_policy_decision_id'):
        raise ValueError('Channel evidence belongs to a different accepted evidence policy')
    return verify_channel_evidence(records[0], model_binding, study_root=study_root,
                                   accepted_statuses=policy.get('accepted_statuses', ['DIRECT_VERIFIED']))


def validate_support_binding(context, mapping, model_binding):
    support = context.get('support_binding')
    if not isinstance(support, dict) or support.get('status') != 'VERIFIED':
        raise ValueError('Verified checkpoint-specific support binding required')
    expected = {'checkpoint_sha256': model_binding['checkpoint_sha256'],
                'config_sha256': model_binding['config_sha256'],
                'source_commit': model_binding['source_commit'],
                'native_class_order_sha256': digest(model_binding['native_class_order']),
                'mapping_sha256': digest(mapping),
                'target_catalog_sha256': digest(mapping['target_catalog'])}
    if any(support.get(key) != value for key, value in expected.items()):
        raise ValueError('Checkpoint-specific capability evidence binding mismatch')
    if not support.get('evidence_references') or support.get('semantic_review') not in {'VERIFIED', 'ACCEPTED_WITH_INDIRECT_EVIDENCE'}:
        raise ValueError('Semantic support needs reviewed mapping/source evidence')
    if context.get('require_verified_channel_order') or context.get('require_channel_order_evidence'):
        record = support.get('channel_order_evidence')
        verify_channel_evidence(record, model_binding,
            accepted_statuses=context.get('accepted_channel_evidence_statuses', ['DIRECT_VERIFIED']))
        if record['status'] == 'ACCEPTED_WITH_INDIRECT_EVIDENCE' and support['semantic_review'] != record['status']:
            raise ValueError('Support confidence must preserve indirect-evidence limitations')
    targets = support.get('supported_target_ids')
    if not isinstance(targets, list) or any(type(i) is not int for i in targets) or len(targets) != len(set(targets)):
        raise ValueError('Explicit unique supported target IDs required')
    required = set(map(int, mapping['target_catalog'])) - {0}
    if context['target_support_policy'] == 'COMMON_CAPABILITY' and not required <= set(targets):
        raise ValueError('Checkpoint does not support the required cohort targets')
    return True
