"""Literal reporting expectations; no model, GT, prediction or scorer execution."""
import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    'target_confusion', Path(__file__).resolve().parents[1] / 'scripts/report_target_confusion.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_binary_counts_and_metric_denominators():
    # 20 pixels: six correct positives, two misses, four excess, eight negatives.
    result = module.summarize([dict(
        TP=6, FN=2, FP=4, valid_pixels=20, GT_pixels=8,
        prediction_pixels=10, IoU=0.5, unmatched=False,
    )])
    assert [result[k] for k in ('TP', 'FN', 'FP', 'TN')] == [6, 2, 4, 8]
    assert result['pooled_recall'] == 0.75
    assert result['missed_GT_fraction'] == 0.25
    assert result['pooled_precision'] == 0.6
    assert result['pooled_IoU'] == 0.5
    assert result['pooled_Dice'] == pytest.approx(2 / 3)
    assert result['pooled_F1'] == pytest.approx(2 / 3)
    assert result['pooled_F1'] == result['pooled_Dice']


def test_part_counts_are_not_pixel_coverage_or_exact_correctness():
    # Full coverage can include FP. Large missed part dominates pooled metrics,
    # but both parts have equal weight in mean-part IoU.
    result = module.summarize([
        dict(TP=1, FP=1, FN=0, valid_pixels=200, GT_pixels=1,
             prediction_pixels=2, IoU=0.5, unmatched=False),
        dict(TP=0, FP=0, FN=99, valid_pixels=200, GT_pixels=99,
             prediction_pixels=0, IoU=0.0, unmatched=True),
    ])
    assert result['mean_part_IoU'] == 0.25
    assert result['pooled_IoU'] == pytest.approx(1 / 101)
    assert result['pooled_recall'] == 0.01
    assert result['pooled_F1'] == pytest.approx(1 / 51)  # Not mean-part Dice 1/3.
    assert result['zero_overlap_parts'] == 1
    assert result['empty_prediction_parts'] == 1
    assert result['full_GT_coverage_parts'] == 1
    assert result['exact_mask_parts'] == 0
    assert result['unmatched_parts'] == 1
    assert result['TN'] == 299


def test_empty_prediction_has_null_precision_and_all_gt_missed():
    result = module.summarize([dict(
        TP=0, FP=0, FN=8, valid_pixels=20, GT_pixels=8,
        prediction_pixels=0, IoU=0.0, unmatched=False,
    )])
    assert result['pooled_precision'] is None
    assert result['pooled_recall'] == 0
    assert result['missed_GT_fraction'] == 1
    assert result['pooled_IoU'] == 0
    assert result['pooled_F1'] == 0
    assert result['zero_overlap_parts'] == result['empty_prediction_parts'] == 1
    assert result['unmatched_parts'] == 0


def test_unknown_neck_keeps_explicit_uncertainty_in_domain():
    # Null is an unknown anatomical state; only the annotated uncertain region
    # is excluded. This does not create a Face+Neck delivery observation.
    record = dict(Neck_status='REGION_UNCERTAIN', Neck_pixels=None,
                  uncertainty_pixels=17, FaceNeck_delivery_eligible=False)
    assert module.face_domain_pixels(100, record) == 83
    assert record['Neck_pixels'] is None
    known = dict(Neck_status='VISIBLE_ANNOTATED', Neck_pixels=11,
                 uncertainty_pixels=17, FaceNeck_delivery_eligible=True)
    assert module.face_domain_pixels(100, known) == 72


@pytest.mark.parametrize('change', [
    {'valid_pixels': 11},  # Union occupies 12 pixels.
    {'GT_pixels': 9},
    {'FP': -1},
    {'TP': 6.0},
])
def test_inconsistent_counts_fail_instead_of_filling_a_matrix(change):
    row = dict(TP=6, FN=2, FP=4, valid_pixels=20, GT_pixels=8,
               prediction_pixels=10, IoU=0.5, unmatched=False)
    row.update(change)
    with pytest.raises(ValueError):
        module.summarize([row])


def test_binary_f1_perfect_missed_spurious_and_absent_support():
    assert module.binary_f1(5, 0, 0) == 1
    assert module.binary_f1(0, 0, 5) == 0
    assert module.binary_f1(0, 5, 0) == 0
    assert module.binary_f1(0, 0, 0) is None


def test_binary_f1_rejects_invalid_counts():
    for counts in [(-1, 0, 0), (1.0, 0, 0), (True, 0, 0)]:
        with pytest.raises(ValueError):
            module.binary_f1(*counts)
