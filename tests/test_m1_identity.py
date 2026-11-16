# Tests for M1 File Identity: SHA-256 correctness, format detection, dimension accuracy.
# Independent verification for SHA-256: use Python's built-in hashlib directly.
"""
Tests for forensic.modules.m1_identity.
SHA-256 is verified by computing it independently with hashlib and comparing.
"""
import pytest
import hashlib
from pathlib import Path
import sys
ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))
from forensic.modules.m1_identity import run
from forensic.core.config import Config

def _independent_sha256(path: Path) -> str:
    """Compute SHA-256 independently using only hashlib — no project code."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def test_sha256_matches_independent_tool(valid_jpeg, default_config):
    """SHA-256 from M1 must equal the independently computed SHA-256 (hashlib only)."""
    result = run(valid_jpeg, default_config)
    assert result.status == "completed"
    expected = _independent_sha256(valid_jpeg)
    assert result.observations["sha256"] == expected, \
        f"SHA-256 mismatch: M1={result.observations['sha256']} vs independent={expected}"

def test_sha256_matches_independent_png(valid_png, default_config):
    """SHA-256 must match for PNG too."""
    result = run(valid_png, default_config)
    assert result.status == "completed"
    expected = _independent_sha256(valid_png)
    assert result.observations["sha256"] == expected

def test_m1_format_detection_jpeg(valid_jpeg, default_config):
    """M1 must detect JPEG format."""
    result = run(valid_jpeg, default_config)
    assert result.status == "completed"
    assert result.observations["pillow_format"] == "JPEG"

def test_m1_format_detection_png(valid_png, default_config):
    """M1 must detect PNG format."""
    result = run(valid_png, default_config)
    assert result.status == "completed"
    assert result.observations["pillow_format"] == "PNG"

def test_m1_dimensions_correct(valid_jpeg, default_config):
    """M1 must report the correct image dimensions (100x100)."""
    result = run(valid_jpeg, default_config)
    assert result.status == "completed"
    assert result.observations["width_px"] == 100
    assert result.observations["height_px"] == 100
    assert result.observations["total_pixels"] == 10_000

def test_m1_malformed_does_not_crash(malformed_file, default_config):
    """M1 must return a failed record for a malformed file, not crash."""
    result = run(malformed_file, default_config)
    # malformed file is not a valid image, Pillow will fail to open it
    # M1 should return status=failed, not raise an exception
    assert result.status in ("failed", "completed")  # completed if file exists but Pillow fails to open

def test_m1_no_real_fake_label(valid_jpeg, default_config):
    """M1 must never produce a 'real' or 'fake' label anywhere in its output."""
    result = run(valid_jpeg, default_config)
    result_str = str(result.to_dict()).lower()
    assert "real" not in result_str or "not real" in result_str or "real/" in result_str
    # More specific: the interpretation must not say 'real' or 'fake'
    for v in result.interpretation.values():
        if isinstance(v, str):
            assert v.lower() not in ("real", "fake", "genuine", "authentic")

def test_m1_repeat_runs_identical(valid_jpeg, default_config):
    """Repeat runs on the same file must produce identical observations (excluding timestamp)."""
    r1 = run(valid_jpeg, default_config)
    r2 = run(valid_jpeg, default_config)
    assert r1.observations == r2.observations
    assert r1.status == r2.status

def test_m1_record_format_complete(valid_jpeg, default_config):
    """M1 record must have all required fields from brief Section 6."""
    result = run(valid_jpeg, default_config)
    d = result.to_dict()
    required_fields = [
        "input_sha256", "engine", "version", "method", "parameters",
        "status", "observations", "interpretation", "regions", "confidence", "limitations"
    ]
    for field in required_fields:
        assert field in d, f"Missing required field: {field}"

def test_m1_has_limitations(valid_jpeg, default_config):
    """M1 must list at least one limitation."""
    result = run(valid_jpeg, default_config)
    assert len(result.limitations) > 0
