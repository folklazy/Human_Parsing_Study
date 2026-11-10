"""Independent expectations for log-only statistics and event reconciliation."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from report_runtime import describe_seconds, forward_pairs, time_accounting, group_image_times


def test_mean_median_and_linear_percentile():
    result = describe_seconds([4., 1., 3., 2.])
    assert result['n'] == 4
    assert result['mean_ms'] == result['median_ms'] == 2500
    assert result['p95_ms'] == pytest.approx(3850)
    assert result['total_seconds'] == 10
    assert describe_seconds([])['mean_ms'] is None
    assert describe_seconds([.2])['p95_ms'] == 200


def event(kind, job, stamp):
    return dict(event=kind, job_id=job, purpose='ROI_INFERENCE', utc='2026-11-01T00:00:'+stamp+'+00:00')


def test_success_and_failed_start_are_separate():
    complete, unfinished = forward_pairs([
        event('FORWARD_START', 'a', '00.000000'),
        event('FORWARD_END', 'a', '00.250000'),
        event('FORWARD_START', 'b', '01.000000'),
    ])
    assert complete['a']['UTC_interval_seconds'] == .25
    assert set(unfinished) == {'b'}  # Never invent zero duration for failure.


@pytest.mark.parametrize('events', [
    [event('FORWARD_END', 'a', '01')],
    [event('FORWARD_START', 'a', '02'), event('FORWARD_END', 'a', '01')],
    [event('FORWARD_START', 'a', '01'), event('FORWARD_START', 'a', '02')],
])
def test_invalid_or_duplicate_events_rejected(events):
    with pytest.raises(ValueError):
        forward_pairs(events)


@pytest.mark.parametrize('duration', [-1., float('nan'), float('inf')])
def test_invalid_durations_rejected(duration):
    with pytest.raises(ValueError):
        describe_seconds([duration])


def test_add_disjoint_logs_without_double_counting_worker_time():
    row = dict(monotonic_adapter=dict(n=2, total_seconds=1.),
               UTC_event_interval=dict(n=3, total_seconds=2.), ROI_population=5,
               segments=[dict(worker_elapsed_seconds=4.), dict(worker_elapsed_seconds=6.)])
    result = time_accounting(row)
    assert result['logged_interval_sum_seconds'] == 3
    assert result['worker_elapsed_sum_seconds'] == 10  # Not 3+10 or a sum of means.
    assert result['timed_ROIs'] == 5 and result['untimed_ROIs'] == 0
    assert result['timing_coverage'] == 1
    assert result['homogeneous_latency_metric'] is False


def test_untimed_ROI_does_not_become_zero_duration_or_full_coverage():
    row = dict(monotonic_adapter=dict(n=2, total_seconds=1.),
               UTC_event_interval=dict(n=0, total_seconds=None), ROI_population=3,
               segments=[dict(worker_elapsed_seconds=7.)])
    result = time_accounting(row)
    assert result['timed_ROIs'] == 2 and result['untimed_ROIs'] == 1
    assert result['timing_coverage'] == pytest.approx(2/3)
    assert result['logged_interval_sum_seconds'] == 1
    assert result['end_to_end'] is False


def test_time_coverage_cannot_exceed_population():
    row = dict(monotonic_adapter=dict(n=3, total_seconds=1.),
               UTC_event_interval=dict(n=2, total_seconds=2.), ROI_population=4,
               segments=[dict(worker_elapsed_seconds=7.)])
    with pytest.raises(ValueError):
        time_accounting(row)


def test_per_image_sum_and_true_no_parser_call_zero():
    # Two-person image =70+90ms; no-person image has no parser call.
    frames = [dict(image_id='first', jobs=['a', 'b']), dict(image_id='empty', jobs=[])]
    durations = {'a': dict(seconds=.07, clock='MONOTONIC'),
                 'b': dict(seconds=.09, clock='UTC_EVENT')}
    rows, summary = group_image_times(frames, durations)
    assert rows[0]['image_parsing_work_ms'] == 160
    assert rows[1]['image_parsing_work_ms'] == 0
    assert rows[1]['status'] == 'NO_PARSER_ROIS'
    assert summary['full_population_timing_complete']
    assert summary['full_population_mean_ms_per_image'] == 80
    assert summary['full_population_parsing_work_seconds'] == .16
    assert summary['complete_nonempty_statistics']['mean_ms'] == 160


def test_missing_roi_and_reused_image_remain_null_not_zero():
    frames = [dict(image_id='partial', jobs=['a', 'b']),
              dict(image_id='reused', jobs=['c']), dict(image_id='empty', jobs=[])]
    rows, summary = group_image_times(frames, {'a': dict(seconds=.07, clock='MONOTONIC')})
    assert rows[0]['observed_interval_ms'] == 70
    assert rows[0]['image_parsing_work_ms'] is None
    assert rows[0]['status'] == 'PARTIAL_TIMING'
    assert rows[1]['observed_interval_ms'] is None
    assert rows[1]['status'] == 'NO_CURRENT_TIMER'
    assert summary['full_population_mean_ms_per_image'] is None
    assert summary['full_population_parsing_work_seconds'] is None
    assert summary['recorded_interval_sum_seconds'] == .07
    assert summary['images_with_complete_timing'] == 1


@pytest.mark.parametrize('frames,durations', [
    ([dict(image_id='a', jobs=['x']), dict(image_id='b', jobs=['x'])], {}),
    ([dict(image_id='a', jobs=['x'])], {'other': dict(seconds=1., clock='MONOTONIC')}),
    ([dict(image_id='a', jobs=['x'])], {'x': dict(seconds=-1., clock='MONOTONIC')}),
])
def test_per_image_membership_and_duration_contract(frames, durations):
    with pytest.raises(ValueError):
        group_image_times(frames, durations)
