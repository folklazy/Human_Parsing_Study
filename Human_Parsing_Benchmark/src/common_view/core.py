"""C4-P revision-2: hard-label projection and geometry-only person matching.

No model imports, inference, GT-guided prediction construction or native-file writes.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment

TARGETS = (1, 2, 3, 4)
SPACES = {'CIHP_GT_AND_NATIVE_PRED': 20, 'SAPIENS2_DOME29_PRED': 29}


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def array_hash(a):
    a = np.ascontiguousarray(a)
    return hashlib.sha256(str((a.dtype.str, a.shape)).encode() + a.tobytes()).hexdigest()


def load_spec(path):
    spec = json.loads(Path(path).read_text())
    if spec['revision'] != 'revision-2-pilot':
        raise ValueError('Unsupported common-view revision')
    for space, n in SPACES.items():
        mapping = spec['mapping'][space]
        if set(mapping) != {str(i) for i in range(n)} or set(mapping.values()) - set(range(6)):
            raise ValueError('Total native-ID mapping required')
    return spec


def project(labels, space, spec):
    labels = np.asarray(labels)
    n = SPACES[space]
    if labels.dtype.kind not in 'ui' or np.any(labels < 0) or np.any(labels >= n):
        raise ValueError('Invalid native prediction IDs/dtype; prediction255 is not VOID')
    lut = np.array([spec['mapping'][space][str(i)] for i in range(n)], np.uint8)
    return lut[labels]


def gt_domains(category, human, spec):
    c, h = np.asarray(category), np.asarray(human)
    if c.ndim != 2 or h.shape != c.shape or c.dtype.kind not in 'ui' or h.dtype.kind not in 'ui':
        raise ValueError('GT grids must be 2D unsigned integer planes')
    if np.any(h < 0) or np.any(c < 0) or np.any((c >= 20) & (c != 255)):
        raise ValueError('Unknown GT label; source bytes must not be repaired')
    valid = c < 20
    projected = np.full(c.shape, 255, np.uint8)
    projected[valid] = project(c[valid], 'CIHP_GT_AND_NATIVE_PRED', spec)
    vp = valid & ~((c > 0) & (h == 0))
    persons = []
    for pid in sorted(int(i) for i in np.unique(h) if i > 0):
        extent = (h == pid) & valid
        if not extent.any():
            continue
        counts = np.bincount(projected[vp & (h == pid)], minlength=6)[:6]
        persons.append({'id': pid, 'extent_sha256': array_hash(extent),
                        'target_pixels': int(counts[1:5].sum()),
                        'target_support': counts[1:5].tolist(),
                        'eligible_C4': bool(counts[1:5].sum())})
    binding = {'shape': list(c.shape), 'projected_sha256': array_hash(projected),
               'valid_sha256': array_hash(valid), 'person_valid_sha256': array_hash(vp),
               'G_loc': len(persons), 'G_sem_C4': sum(x['eligible_C4'] for x in persons),
               'global_support': np.bincount(projected[valid], minlength=6).tolist(),
               'owner_unknown_pixels': int((valid & (c > 0) & (h == 0)).sum()),
               'persons': persons}
    return projected, valid, vp, binding


def geometry_key(mask):
    """Ordering by the complete boolean geometry, never IDs or semantic labels."""
    y, x = np.where(mask)
    if not len(x):
        raise ValueError('Matching extent must be nonempty')
    return (int(y.min()), int(x.min()), int(y.max()), int(x.max()),
            len(x), int(y.sum()), int(x.sum()), np.packbits(mask.ravel()).tobytes())


def match_geometry(gt_masks, pred_masks, gt_ids, threshold):
    """Maximum cardinality, then IoU, then canonical geometry lexicographic optimum.

    Distinct GT masks guarantee GT-ID renaming invariance. Identical GT geometry
    falls back to stable ID; identical prediction geometry uses packet index.
    Such unresolved geometry equivalences and alternative optima are reported.
    """
    g, p = len(gt_masks), len(pred_masks)
    gkeys = [geometry_key(m) for m in gt_masks]
    pkeys = [geometry_key(m) for m in pred_masks]
    go = sorted(range(g), key=lambda i: (gkeys[i], gt_ids[i]))
    po = sorted(range(p), key=lambda j: (pkeys[j], j))
    iou = np.zeros((g, p), float)
    for i, gi in enumerate(go):
        for j, pj in enumerate(po):
            a, b = gt_masks[gi], pred_masks[pj]
            iou[i, j] = np.count_nonzero(a & b) / np.count_nonzero(a | b)
    eligible = iou >= threshold

    def optimum(rows, cols):
        if not rows or not cols:
            return 0, 0.
        a = iou[np.ix_(rows, cols)]
        e = eligible[np.ix_(rows, cols)]
        # Cardinality bonus exceeds every possible difference in total IoU.
        rr, cc = linear_sum_assignment(-(e * (min(g, p) + 1) + e * a))
        selected = [(r, c) for r, c in zip(rr, cc) if e[r, c]]
        return len(selected), sum(float(a[r, c]) for r, c in selected)

    needed, target = optimum(list(range(g)), list(range(p)))
    columns = list(range(p))
    pairs, ambiguous = [], False
    for i in range(g):
        possible = []
        for candidate in [j for j in columns if eligible[i, j]] + [None]:
            cols = [j for j in columns if j != candidate]
            k, value = optimum(list(range(i + 1, g)), cols)
            contribution = 0. if candidate is None else float(iou[i, candidate])
            taken = int(candidate is not None)
            if k + taken == needed and abs(value + contribution - target) <= 1e-12:
                possible.append(candidate)
        if not possible:
            raise ValueError('Matching objective reconciliation failed')
        ambiguous |= len(possible) > 1
        chosen = possible[0]
        if chosen is not None:
            pairs.append((go[i], po[chosen], float(iou[i, chosen])))
            columns.remove(chosen)
            needed -= 1
            target -= float(iou[i, chosen])
    if needed:
        raise ValueError('Matching cardinality incomplete')
    return pairs, {'alternative_optimum': ambiguous,
                   'identical_GT_geometry_groups': sum(n > 1 for n in Counter(gkeys).values()),
                   'identical_prediction_geometry_groups': sum(n > 1 for n in Counter(pkeys).values()),
                   'tie_policy': 'geometry_canonical_then_stable_fallback_only_identical_geometry',
                   'ID_renaming_invariance_guaranteed': len(set(gkeys)) == g}


def validate_prediction(planes, extents, scores, shape, space):
    planes, extents, scores = np.asarray(planes), np.asarray(extents), np.asarray(scores)
    if planes.ndim != 3 or planes.shape[1:] != tuple(shape) or planes.shape != extents.shape:
        raise ValueError('Original-grid person mask dimensions invalid')
    if extents.dtype != np.bool_ or scores.shape != (len(planes),) or not np.isfinite(scores).all():
        raise ValueError('Extent/score contract invalid')
    if planes.dtype.kind not in 'ui' or np.any(planes < 0) or np.any(planes >= SPACES[space]):
        raise ValueError('Native prediction IDs invalid')
    if any(not e.any() for e in extents) or np.any((planes > 0) & ~extents):
        raise ValueError('Raw extent empty or semantics outside recorded ownership')


def compose_native(planes, scores, shape):
    out = np.zeros(shape, np.uint8)
    for j in sorted(range(len(planes)), key=lambda j: (float(scores[j]), -j)):
        out = np.where(planes[j] > 0, planes[j], out)
    return out


def semantic_metrics(hist):
    h = np.asarray(hist)
    if h.shape != (6, 6) or h.dtype.kind not in 'ui' or np.any(h < 0):
        raise ValueError('Integer 6x6 confusion required')
    tp = np.diag(h); gs = h.sum(1); ps = h.sum(0); union = gs + ps - tp
    iou = np.divide(tp, union, out=np.zeros(6, float), where=union > 0)
    return {'mIoU4': float(iou[1:5].mean()),
            'C3_global_mean_only': float(iou[[2, 3, 4]].mean()),
            'IoU': iou.tolist(), 'GT_support': gs.tolist(), 'pred_support': ps.tolist(),
            'union': union.tolist(), 'zero_union': (union == 0).tolist(),
            'precision': [float(tp[c] / ps[c]) if ps[c] else None for c in range(6)],
            'recall': [float(tp[c] / gs[c]) if gs[c] else None for c in range(6)]}


def score_packet(category, human, planes, extents, scores, space, spec, threshold=.5):
    validate_prediction(planes, extents, scores, category.shape, space)
    gt, valid, vp, binding = gt_domains(category, human, spec)
    pred = project(compose_native(planes, scores, category.shape), space, spec)
    h6 = np.bincount(6 * gt[valid].astype(np.int64) + pred[valid], minlength=36).reshape(6, 6)
    gids = [r['id'] for r in binding['persons']]
    gm = [(human == pid) & valid for pid in gids]
    pred_indices = [j for j, e in enumerate(extents) if (e & valid).any()]
    pm = [extents[j] & valid for j in pred_indices]
    pairs, ambiguity = match_geometry(gm, pm, gids, threshold)
    by_gt = {i: pred_indices[j] for i, j, _ in pairs}
    projected_planes = project(planes, space, spec)
    qtotal = 0.; contam = denom = bg_leakage = 0
    for i, pid in enumerate(gids):
        if i not in by_gt:
            continue
        person_pred = projected_planes[by_gt[i]]
        targetmask = (person_pred >= 1) & (person_pred <= 4) & vp
        denom += int(targetmask.sum())
        contam += int((targetmask & (human > 0) & (human != pid)).sum())
        bg_leakage += int((targetmask & (human == 0)).sum())
        if not binding['persons'][i]['eligible_C4']:
            continue
        person_gt = np.where(human == pid, gt, 0)
        ks = (set(np.unique(person_gt[vp])) | set(np.unique(person_pred[vp]))) & set(TARGETS)
        q = []
        for c in sorted(ks):
            a, b = (person_gt == c) & vp, (person_pred == c) & vp
            u = int((a | b).sum())
            q.append(float((a & b).sum() / u) if u else 0.)
        qtotal += sum(q) / len(q)
    tp = len(pairs); fp = len(pm) - tp; fn = len(gids) - tp
    gsem = binding['G_sem_C4']
    native = compose_native(planes, scores, category.shape)
    n = SPACES[space]
    discordance = np.bincount(n * category[valid].astype(np.int64) + native[valid],
                             minlength=20 * n).reshape(20, n)
    return {'histogram': h6.tolist(), 'semantic': semantic_metrics(h6),
            'native_GT_prediction_histogram': discordance.tolist(), 'threshold': threshold,
            'G_loc': len(gids), 'G_sem_C4': gsem, 'TP': tp, 'FP': fp, 'FN': fn,
            'predicted_persons_including_semantic_empty': len(planes),
            'void_only_predicted_extents': len(planes) - len(pm),
            'Q_numerator': qtotal, 'Q_C4_GT': qtotal / gsem if gsem else None,
            'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tp / len(gids) if gids else None,
            'extent_F1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
            'contamination_numerator': contam, 'matched_target_denominator': denom,
            'contamination': contam / denom if denom else None,
            'background_leakage_numerator': bg_leakage,
            'background_leakage': bg_leakage / denom if denom else None,
            'matches': [{'gt_id': gids[i], 'pred_index': pred_indices[j], 'IoU': v}
                        for i, j, v in pairs], 'matching_ambiguity': ambiguity,
            'GT_binding': binding}


def aggregate(rows, expected_ids, scope='PILOT_DIAGNOSTICS_ONLY'):
    ids = [r['image_id'] for r in rows]
    complete = len(ids) == len(set(ids)) and set(ids) == set(expected_ids)
    hist = np.zeros((6, 6), np.int64)
    people = {}
    for threshold in ('0.5', '0.75'):
        sums = dict(G_loc=0, G_sem_C4=0, TP=0, FP=0, FN=0, Q_numerator=0.,
                    contamination_numerator=0, matched_target_denominator=0,
                    background_leakage_numerator=0)
        ambiguity = 0
        for row in rows:
            sc = row['scores'][threshold]
            for k in sums:
                sums[k] += sc[k]
            ambiguity += int(sc['matching_ambiguity']['alternative_optimum'])
        tp, fp, fn, gs, den = (sums[k] for k in ('TP', 'FP', 'FN', 'G_sem_C4', 'matched_target_denominator'))
        sums.update(Q_C4_GT=sums['Q_numerator'] / gs if gs else None,
                    precision=tp / (tp + fp) if tp + fp else None,
                    recall=tp / sums['G_loc'] if sums['G_loc'] else None,
                    extent_F1=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
                    contamination=sums['contamination_numerator'] / den if den else None,
                    ambiguous_matching_frames=ambiguity)
        people[threshold] = sums
    for row in rows:
        hist += np.asarray(row['scores']['0.5']['histogram'], np.int64)
    return {'scope': scope, 'complete': complete, 'expected': len(expected_ids),
            'committed_unique': len(set(ids)), 'missing': sorted(set(expected_ids) - set(ids)),
            'duplicate_ids': sorted(k for k, v in Counter(ids).items() if v > 1),
            'full_population_primary': None, 'full_population_reason': 'NOT_A_5000_ID_COMMON_VIEW_RUN',
            'diagnostics': semantic_metrics(hist) if complete else None,
            'partial_diagnostics_not_main': semantic_metrics(hist) if not complete else None,
            'person_C4_diagnostics': people, 'histogram': hist.tolist()}
