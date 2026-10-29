"""Streaming full-population reporting, scientifically identical revision-2 scoring.

The pilot core/protocol remain untouched. Legacy global confusion is projected
once; per-person scoring uses the same fixed geometry matcher and target policy.
"""
import numpy as np
from .core import (TARGETS, gt_domains, match_geometry, project, validate_prediction,
                   compose_native, semantic_metrics)

PERSON_SUMS = ('G_loc', 'G_sem_C4', 'TP', 'FP', 'FN', 'Q_numerator',
               'contamination_numerator', 'matched_target_denominator',
               'background_leakage_numerator', 'predicted_persons_including_semantic_empty',
               'void_only_predicted_extents')


def project_confusion(hist, space, spec):
    h = np.asarray(hist)
    lut = np.array([spec['mapping'][space][str(i)] for i in range(h.shape[1])])
    gt = np.array([spec['mapping']['CIHP_GT_AND_NATIVE_PRED'][str(i)] for i in range(20)])
    if h.shape != (20, len(lut)) or h.dtype.kind not in 'ui' or np.any(h < 0):
        raise ValueError('Native integer confusion contract')
    result = np.zeros((6, 6), np.int64)
    for i in range(20):
        for j in range(len(lut)):
            result[gt[i], lut[j]] += int(h[i, j])
    return result


def score_people(category, human, planes, extents, scores, space, spec, binding=None):
    """Two thresholds, one GT projection; same arithmetic/order as pilot score_packet."""
    validate_prediction(planes, extents, scores, category.shape, space)
    gt, valid, vp, actual = gt_domains(category, human, spec)
    if binding:
        for k in ['projected_sha256', 'valid_sha256', 'person_valid_sha256', 'G_loc', 'G_sem_C4', 'persons']:
            if actual[k] != binding[k]:
                raise ValueError('GT binding drift: ' + k)
    gids = [p['id'] for p in actual['persons']]
    gm = [(human == pid) & valid for pid in gids]
    indices = [j for j, e in enumerate(extents) if (e & valid).any()]
    pm = [extents[j] & valid for j in indices]
    projected = project(planes, space, spec)
    result = {}
    for threshold in (.5, .75):
        pairs, ambiguity = match_geometry(gm, pm, gids, threshold)
        by_gt = {i: indices[j] for i, j, _ in pairs}
        qtotal = 0.; contam = den = bg_leak = 0
        for i, pid in enumerate(gids):
            if i not in by_gt:
                continue
            pp = projected[by_gt[i]]
            targets = (pp >= 1) & (pp <= 4) & vp
            den += int(targets.sum())
            contam += int((targets & (human > 0) & (human != pid)).sum())
            bg_leak += int((targets & (human == 0)).sum())
            if not actual['persons'][i]['eligible_C4']:
                continue
            pg = np.where(human == pid, gt, 0)
            ks = (set(np.unique(pg[vp])) | set(np.unique(pp[vp]))) & set(TARGETS)
            values = []
            for c in sorted(ks):
                a, b = (pg == c) & vp, (pp == c) & vp
                union = int((a | b).sum())
                values.append(float((a & b).sum() / union) if union else 0.)
            qtotal += sum(values) / len(values)
        tp = len(pairs); fp = len(pm) - tp; fn = len(gids) - tp; gs = actual['G_sem_C4']
        result[str(threshold)] = dict(
            threshold=threshold, G_loc=len(gids), G_sem_C4=gs, TP=tp, FP=fp, FN=fn,
            predicted_persons_including_semantic_empty=len(planes),
            void_only_predicted_extents=len(planes)-len(pm), Q_numerator=qtotal,
            Q_C4_GT=qtotal/gs if gs else None, precision=tp/(tp+fp) if tp+fp else None,
            recall=tp/len(gids) if gids else None,
            extent_F1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
            contamination_numerator=contam, matched_target_denominator=den,
            contamination=contam/den if den else None, background_leakage_numerator=bg_leak,
            background_leakage=bg_leak/den if den else None,
            matches=[dict(gt_id=gids[i], pred_index=indices[j], IoU=v) for i,j,v in pairs],
            matching_ambiguity=ambiguity, GT_binding=actual)
    return result


def native_confusion(category, planes, scores, space, spec):
    n = len(spec['mapping'][space]); valid = category < 20
    native = compose_native(planes, scores, category.shape)
    return np.bincount(n*category[valid].astype(np.int64)+native[valid],
                       minlength=20*n).reshape(20, n)


class Accumulator:
    def __init__(self, expected_ids):
        self.expected = set(expected_ids)
        if len(self.expected) != len(expected_ids):
            raise ValueError('Duplicate expected IDs')
        self.ids = set()
        self.people = {t: {k: 0. if k == 'Q_numerator' else 0 for k in PERSON_SUMS}
                       for t in ['0.5', '0.75']}
        self.ambiguity = {'0.5': 0, '0.75': 0}
        self.hist = np.zeros((6,6), np.int64)
        self.native = None

    def add(self, iid, scores, native_hist=None, space=None, spec=None):
        if iid in self.ids or iid not in self.expected:
            raise ValueError('Duplicate or out-of-population score: ' + iid)
        self.ids.add(iid)
        for t in self.people:
            for k in PERSON_SUMS:
                self.people[t][k] += scores[t][k]
            self.ambiguity[t] += int(scores[t]['matching_ambiguity']['alternative_optimum'])
        if native_hist is not None:
            if self.native is None:
                self.native = np.zeros_like(native_hist)
            self.native += native_hist
            self.hist += project_confusion(native_hist, space, spec)

    def report(self, global_hist=None, global_native=None):
        complete = self.ids == self.expected
        hist = self.hist if global_hist is None else global_hist
        people = {}
        for t, sums in self.people.items():
            v = dict(sums); tp,fp,fn,gs,den = [v[k] for k in ['TP','FP','FN','G_sem_C4','matched_target_denominator']]
            v.update(Q_C4_GT=v['Q_numerator']/gs if gs else None,
                     precision=tp/(tp+fp) if tp+fp else None,
                     recall=tp/v['G_loc'] if v['G_loc'] else None,
                     extent_F1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
                     contamination=v['contamination_numerator']/den if den else None,
                     background_leakage=v['background_leakage_numerator']/den if den else None,
                     ambiguous_matching_frames=self.ambiguity[t])
            people[t] = v
        native = self.native if global_native is None else global_native
        return dict(scope='CIHP_SAPIENS_C4P_FULL_REVISION2',
                    status='COMPLETE' if complete else 'INCOMPLETE', expected=len(self.expected),
                    complete=len(self.ids), missing=sorted(self.expected-self.ids), duplicate_ids=[],
                    failure_policy='STRICT_COMPLETE',
                    primary=semantic_metrics(hist) if complete else None,
                    person_metrics=people if complete else None,
                    partial_person_diagnostics_not_main=people if not complete else None,
                    histogram=hist.tolist() if complete else None,
                    native_GT_prediction_histogram=native.tolist() if complete and native is not None else None,
                    timing_ranking_allowed=False,
                    limitations=['Face proxy, not strict face-only equivalence',
                                 'Upper/Lower non-Dress; Dress/Apparel valid OTHER',
                                 'Application pipeline comparison, not architecture-only comparison',
                                 'Q_C4_GT does not directly penalize unmatched predicted persons; read FP/F1',
                                 'Shared GPU observations are not clean latency/FPS/VRAM rankings'])
