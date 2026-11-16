# Tests for partitions, temperature calibration, and per-generator evaluation logic.
import pytest
import numpy as np
from pathlib import Path
import sys

ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))

from eval.partitions import create_partitions, deduplicate_dataset, compute_dhash, hamming_distance
from eval.calibration import TemperatureScaler, TwoThresholdClassifier, brier_score, expected_calibration_error
from eval.synthetic_eval import evaluate_synthetic_detector


def test_partitions_generator_holdout():
    """Verify that held-out generators are strictly excluded from calibration split."""
    items = [
        {"id": f"g1_{i}", "generator": "progan", "label": "synthetic", "raw_logit": 2.0}
        for i in range(20)
    ] + [
        {"id": f"g2_{i}", "generator": "midjourney", "label": "synthetic", "raw_logit": 1.0}
        for i in range(10)
    ] + [
        {"id": f"r_{i}", "generator": "real", "label": "real", "raw_logit": -2.0}
        for i in range(20)
    ]

    splits = create_partitions(items, dev_ratio=0.5, cal_ratio=0.25, test_ratio=0.25,
                               holdout_generators=["midjourney"], seed=42)

    cal_gens = {x["generator"] for x in splits["calibration"]}
    assert "midjourney" not in cal_gens, "Held-out generator 'midjourney' must NOT appear in calibration split"

    test_gens = {x["generator"] for x in splits["test"]}
    assert "midjourney" in test_gens, "Held-out generator must be present in test split"


def test_temperature_scaler_fitting():
    """Verify temperature scaler fits valid T > 0 and outputs normalized probabilities."""
    logits = np.array([-3.0, -1.0, 0.5, 2.0, 4.0])
    labels = np.array([0.0, 0.0, 1.0, 1.0, 1.0])

    scaler = TemperatureScaler().fit(logits, labels)
    assert scaler.temperature > 0.0

    probs = scaler.predict_proba(logits)
    assert len(probs) == len(logits)
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)
    # Check monotonicity
    assert np.all(np.diff(probs) >= 0.0)


def test_two_threshold_classifier():
    """Verify two-threshold classifier classifies correctly and measures coverage."""
    clf = TwoThresholdClassifier(theta_low=0.35, theta_high=0.65)
    assert clf.classify(0.8) == "synthetic indicated"
    assert clf.classify(0.2) == "synthetic not indicated"
    assert clf.classify(0.5) == "inconclusive"

    probs = np.array([0.1, 0.2, 0.5, 0.8, 0.9])
    cov = clf.evaluate_coverage(probs)
    assert cov["coverage"] == 0.8  # 4 out of 5 decided
    assert cov["abstention_rate"] == 0.2  # 1 out of 5 inconclusive


def test_synthetic_evaluation_pipeline_execution():
    """Verify synthetic evaluation pipeline runs and outputs per-generator metrics."""
    samples = [
        {"id": f"real_{i}", "generator": "camera", "label": "real", "raw_logit": -2.5}
        for i in range(20)
    ] + [
        {"id": f"prog_{i}", "generator": "progan", "label": "synthetic", "raw_logit": 3.0}
        for i in range(20)
    ] + [
        {"id": f"mj_{i}", "generator": "midjourney", "label": "synthetic", "raw_logit": 1.2}
        for i in range(15)
    ]

    res = evaluate_synthetic_detector(samples, holdout_generators=["midjourney"])
    assert "calibration" in res
    assert "per_generator_metrics" in res
    assert "midjourney" in res["per_generator_metrics"]
    assert res["per_generator_metrics"]["midjourney"]["held_out_from_calibration"] is True
