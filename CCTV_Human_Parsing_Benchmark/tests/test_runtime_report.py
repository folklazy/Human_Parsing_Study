"""Independent expectations for log-only statistics and event reconciliation."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from report_runtime import describe_seconds, forward_pairs


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
