"""Strict-complete reporting over a predeclared population.

Numerical reporting utility, not benchmark authorization. Incomplete systems
remain visible; successful-frame diagnostics never become the main score.
"""
import math
from .policy import digest


def _count(value, name):
    if type(value) is not int or value < 0:
        raise ValueError(f'{name} must be a nonnegative integer')
    return value


def summarize_comparison(comparison, population, systems, frame_results, policy):
    if policy.get('main_score') != 'STRICT_COMPLETE':
        raise ValueError('This primary reporter implements STRICT_COMPLETE only')
    required = {'incomplete_systems_retained': True, 'incomplete_main_score': None,
                'success_only_is_main_score': False, 'operational_diagnostics_required': True,
                'valid_empty_is_execution_success': True, 'posthoc_population_exclusion': False,
                'posthoc_model_retries': False, 'eligibility_source': 'PREDECLARED_POPULATION'}
    if any(policy.get(k) != v for k, v in required.items()):
        raise ValueError('Strict-complete policy conditions changed')
    if not comparison.get('comparison_id') or not comparison.get('definition_sha256'):
        raise ValueError('Comparison identity and definition fingerprint required')
    if any(not isinstance(v, str) or not v for v in systems) or len(set(systems)) != len(systems):
        raise ValueError('Predeclared unique system IDs required')
    expected = {}
    for row in population:
        key = row['image_id']
        if not isinstance(key, str) or not key or key in expected:
            raise ValueError('Predeclared population image IDs must be unique')
        gloc, gsem = _count(row['G_loc'], 'G_loc'), _count(row['G_sem'], 'G_sem')
        if gsem > gloc:
            raise ValueError('G_sem must be a subset of G_loc')
        expected[key] = row
    if not expected:
        raise ValueError('Empty population cannot certify comparison completeness')
    indexed = {system: {} for system in systems}
    for row in frame_results:
        system, image = row['system_id'], row['image_id']
        if system not in indexed or image not in expected or image in indexed[system]:
            raise ValueError('Unexpected system/image or duplicate frame attempt')
        if row['execution_status'] not in {'COMPLETE', 'FAILED', 'INVALID', 'NOT_ATTEMPTED'}:
            raise ValueError('Unknown final-frame execution status')
        if row['execution_status'] == 'COMPLETE' and row.get('failure_events'):
            raise ValueError('Failed work cannot be declared a complete final frame')
        # A failed model job is retained once; post-hoc retries cannot overwrite it.
        indexed[system][image] = row
    gloc_total = sum(v['G_loc'] for v in population)
    gsem_total = sum(v['G_sem'] for v in population)
    rows = []
    for system in systems:
        observed = indexed[system]
        completed = sum(v['execution_status'] == 'COMPLETE' for v in observed.values())
        failed = sum(v['execution_status'] == 'FAILED' for v in observed.values())
        invalid = sum(v['execution_status'] == 'INVALID' for v in observed.values())
        unscheduled = len(expected) - len(observed) + sum(v['execution_status'] == 'NOT_ATTEMPTED' for v in observed.values())
        events = [event for v in observed.values() for event in v.get('failure_events', [])]
        scored, total_tp, total_fp, total_fn, quality_sum = [], 0, 0, 0, 0.0
        for image, frame in observed.items():
            score = frame.get('score_result')
            if frame['execution_status'] != 'COMPLETE' or not score or not score['score_eligible']:
                continue
            if score['status'] != 'COMPLETE' or score.get('failure_events'):
                raise ValueError('Incomplete/fallback frame cannot supply strict primary metrics')
            metrics = score['metrics']
            gt = expected[image]
            if metrics['G_loc'] != gt['G_loc'] or metrics['G_sem'] != gt['G_sem']:
                raise ValueError('Scored denominator differs from predeclared GT population')
            tp = len(metrics['matching']['matches'])
            fp, fn = _count(metrics['final_fp'], 'FP'), _count(metrics['final_fn'], 'FN')
            if tp + fn != gt['G_loc']:
                raise ValueError('Localization denominator mismatch')
            quality = metrics['Q_person_sem_GT']
            if gt['G_sem']:
                if not isinstance(quality, (int, float)) or not math.isfinite(quality) or not 0 <= quality <= 1:
                    raise ValueError('Defined GT-person semantic quality required')
                quality_sum += quality * gt['G_sem']
            elif quality is not None:
                raise ValueError('No semantic GT must remain undefined')
            total_tp += tp; total_fp += fp; total_fn += fn
            scored.append(image)
        scored_gloc = sum(expected[i]['G_loc'] for i in scored)
        scored_gsem = sum(expected[i]['G_sem'] for i in scored)
        diagnostic = {'label': 'SUCCESS_ONLY_DIAGNOSTIC_NOT_MAIN_SCORE',
                      'scored_frames': len(scored), 'G_loc_observed': scored_gloc,
                      'G_sem_observed': scored_gsem,
                      'Q_person_sem_GT': quality_sum / scored_gsem if scored_gsem else None,
                      'TP': total_tp, 'FP': total_fp, 'FN': total_fn}
        complete = completed == len(expected)
        eligible = complete and len(scored) == len(expected)
        main = None
        if eligible:
            main = {'G_loc': gloc_total, 'G_sem': gsem_total,
                    'Q_person_sem_GT': quality_sum / gsem_total if gsem_total else None,
                    'TP': total_tp, 'FP': total_fp, 'FN': total_fn,
                    'localization_recall': total_tp / gloc_total if gloc_total else None,
                    'localization_precision': total_tp / (total_tp + total_fp) if total_tp + total_fp else None}
        rows.append({'system_id': system,
                     'status': 'COMPLETE' if eligible else 'BLOCKED_SCORING_POLICY' if complete else 'INCOMPLETE',
                     'main_score_eligible': eligible, 'main_metrics': main,
                     'execution': {'stage': 'final_pipeline_frame', 'unit': 'frame',
                                   'completed': completed, 'failed': failed, 'invalid': invalid,
                                   'not_attempted_or_unscheduled': unscheduled,
                                   'numerator': completed, 'denominator': len(expected),
                                   'completion_rate': completed / len(expected)},
                     'population': {'frames': len(expected), 'G_loc': gloc_total, 'G_sem': gsem_total},
                     'operational_diagnostics': {'failure_events': events,
                                                 'failure_event_count': len(events),
                                                 'native_stage_ledgers': [v.get('stage_rates', {}) for v in observed.values()]},
                     'success_only_diagnostic': diagnostic})
    return {'comparison': comparison, 'policy': 'STRICT_COMPLETE',
            'population_sha256': digest(population), 'systems': rows,
            'cross_comparison_ranking': 'PROHIBITED_WHEN_VIEW_DOMAIN_OR_TARGET_DIFFER',
            'benchmark_authorization': False}
