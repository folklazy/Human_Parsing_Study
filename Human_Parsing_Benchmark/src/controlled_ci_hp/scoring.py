"""C4-P revision2 plus per-GT-person-part counts on identical valid domains."""
import numpy as np
from common_view.core import gt_domains, project, score_packet


def evaluate(category, human, arrays, space, spec):
    planes = arrays['person_semantic_masks']
    scores = {str(t): score_packet(category, human, planes, arrays['person_extents'],
                                  arrays['person_scores'], space, spec, t) for t in (.5, .75)}
    gt, _, valid, binding = gt_domains(category, human, spec)
    projected = project(planes, space, spec)
    matches = {r['gt_id']: r['pred_index'] for r in scores['0.5']['matches']}
    parts = []
    for person in binding['persons']:
        pid = person['id']
        index = matches.get(pid)
        prediction = projected[index] if index is not None else np.zeros(gt.shape, np.uint8)
        for target in range(1, 5):
            positive = (human == pid) & (gt == target) & valid
            if not positive.any():
                continue
            predicted = (prediction == target) & valid
            tp = int((positive & predicted).sum())
            fp = int((~positive & predicted & valid).sum())
            fn = int((positive & ~predicted).sum())
            parts.append(dict(gt_id=pid, target=target, TP=tp, FP=fp, FN=fn,
                              IoU=tp/(tp+fp+fn), unmatched=index is None))
    return dict(scores=scores, parts=parts)
