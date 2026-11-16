# Tests for eval/classical_metrics.py to verify metric computation functions correctly.
from __future__ import annotations
import pytest
from pathlib import Path
import sys

ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))

from eval.classical_metrics import evaluate_classical_indicators


def test_classical_metrics_execution():
    """Verify classical metrics evaluation runs and computes all metrics on benchmark data."""
    results = evaluate_classical_indicators()
    assert results["dataset_size"] >= 10
    assert "metrics" in results
    assert "sample_evaluations" in results

    metrics = results["metrics"]
    for key in ["double_jpeg", "resampling", "copy_move", "overall"]:
        assert key in metrics
        data = metrics[key]
        assert "accuracy" in data
        assert "precision" in data
        assert "recall" in data
        assert "f1" in data
        assert "false_positive_rate" in data
        assert "false_negative_rate" in data
        assert 0.0 <= data["accuracy"] <= 1.0
