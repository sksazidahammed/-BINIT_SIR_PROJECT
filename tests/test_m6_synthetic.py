# Tests for Module M6 Synthetic Detection: wrapper, calibration, two-threshold policy, and limitations.
"""
Tests for forensic.modules.m6_synthetic.
Verifies:
- Graceful not_assessed status when weights not supplied (verified open interface).
- calibrate_and_classify maps logits to 3 distinct states.
- Output adheres to EvidenceRecord schema.
- No binary real/fake label.
- Mandatory limitations present.
"""
import pytest
from pathlib import Path
import sys

ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))

from forensic.modules import m6_synthetic
from forensic.core.config import Config, load_config


def _cfg() -> Config:
    return load_config(ROOT_PATH / "config.yaml")


def test_m6_without_weights_returns_not_assessed(valid_jpeg):
    """When no weights are provided, M6 must return status='not_assessed' (tested empty interface)."""
    result = m6_synthetic.run(valid_jpeg, _cfg(), model_weights_path=None)
    assert result.status == "not_assessed"
    assert result.engine == "m6_synthetic"
    assert "not configured" in result.observations.get("reason", "").lower() or "interface" in result.observations.get("reason", "").lower()


def test_m6_schema_completeness(valid_jpeg):
    """M6 record must contain all required EvidenceRecord fields."""
    result = m6_synthetic.run(valid_jpeg, _cfg(), model_weights_path=None)
    d = result.to_dict()
    for field in [
        "input_sha256", "engine", "version", "method", "parameters",
        "status", "observations", "interpretation", "regions", "confidence", "limitations"
    ]:
        assert field in d, f"Missing field: {field}"


def test_m6_calibrate_and_classify_three_states():
    """calibrate_and_classify must produce exactly three states across logit spectrum."""
    # High logit -> synthetic indicated
    p_high, s_high = m6_synthetic.calibrate_and_classify(4.0, temperature=1.0, theta_low=0.35, theta_high=0.65)
    assert s_high == "synthetic indicated"
    assert p_high > 0.65

    # Low logit -> synthetic not indicated
    p_low, s_low = m6_synthetic.calibrate_and_classify(-4.0, temperature=1.0, theta_low=0.35, theta_high=0.65)
    assert s_low == "synthetic not indicated"
    assert p_low < 0.35

    # Intermediate logit -> inconclusive
    p_mid, s_mid = m6_synthetic.calibrate_and_classify(0.0, temperature=1.0, theta_low=0.35, theta_high=0.65)
    assert s_mid == "inconclusive"
    assert 0.35 <= p_mid <= 0.65


def test_m6_limitations_present(valid_jpeg):
    """M6 must list specific limitations regarding unseen generators and compression."""
    result = m6_synthetic.run(valid_jpeg, _cfg(), model_weights_path=None)
    assert len(result.limitations) >= 3
    assert any("unseen generator" in lim.lower() for lim in result.limitations)
    assert any("screenshot" in lim.lower() or "compression" in lim.lower() for lim in result.limitations)


def test_m6_no_real_fake_label(valid_jpeg):
    """M6 must never produce a real/fake verdict."""
    result = m6_synthetic.run(valid_jpeg, _cfg(), model_weights_path=None)
    rec_str = str(result.to_dict()).lower()
    for forbidden in ["'real'", "'fake'", "'authentic'", "'manipulated'"]:
        assert forbidden not in rec_str, f"Forbidden label {forbidden} in output"
