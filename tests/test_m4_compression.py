# Tests for M4 Compression and Colour: JPEG quantisation tables, quality estimate, colour stats.
# Independent verification: compare direct DQT-parse against Pillow's built-in quantization dict.
"""
Tests for forensic.modules.m4_compression.
JPEG quantisation tables from M4's direct byte parser are compared against
Pillow's built-in .quantization attribute (independent reference).
"""
import pytest
from pathlib import Path
import sys
ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))
from forensic.modules.m4_compression import run
from forensic.core.config import Config

def test_m4_jpeg_quant_tables_present(valid_jpeg, default_config):
    """M4 must extract at least one JPEG quantisation table from a valid JPEG."""
    result = run(valid_jpeg, default_config)
    assert result.status == "completed"
    tables = result.observations.get("jpeg_quant_tables_direct", [])
    assert len(tables) >= 1, "JPEG must have at least one quantisation table"
    assert len(tables[0]) == 64, "Each quantisation table must have 64 entries"

def test_m4_quant_tables_match_pillow(valid_jpeg, default_config):
    """JPEG quantisation tables from direct byte parse must match Pillow's .quantization."""
    result = run(valid_jpeg, default_config)
    assert result.status == "completed"
    match = result.observations.get("jpeg_pillow_table_match_direct")
    # match may be None if Pillow doesn't expose the table, but if it's not None it must be True
    if match is not None:
        assert match is True, "Direct DQT parse must match Pillow's quantization table"

def test_m4_quality_estimate_in_range(valid_jpeg, default_config):
    """JPEG quality estimate must be between 1 and 100."""
    result = run(valid_jpeg, default_config)
    assert result.status == "completed"
    q = result.observations.get("jpeg_quality_estimate", -1)
    if q != -1:
        assert 1 <= q <= 100, f"Quality estimate {q} out of range [1, 100]"

def test_m4_png_no_quant_tables(valid_png, default_config):
    """PNG files must not have JPEG quantisation tables."""
    result = run(valid_png, default_config)
    assert result.status == "completed"
    assert result.observations.get("jpeg_quant_tables_direct") is None

def test_m4_colour_stats_present(valid_jpeg, default_config):
    """M4 must report colour statistics: brightness, contrast, saturation."""
    result = run(valid_jpeg, default_config)
    assert result.status == "completed"
    for key in ["brightness_mean", "contrast_std", "saturation_mean"]:
        assert key in result.observations, f"Missing colour stat: {key}"
        assert isinstance(result.observations[key], (int, float))

def test_m4_malformed_does_not_crash(malformed_file, default_config):
    """M4 must handle a malformed file without crashing."""
    result = run(malformed_file, default_config)
    assert result.status in ("completed", "failed")

def test_m4_no_authenticity_claim(valid_jpeg, default_config):
    """M4 interpretation must not make authenticity claims."""
    result = run(valid_jpeg, default_config)
    for v in result.interpretation.values():
        if isinstance(v, str):
            assert v.lower() not in ("real", "fake", "authentic", "manipulated")

def test_m4_has_limitations(valid_jpeg, default_config):
    """M4 must list at least one limitation."""
    result = run(valid_jpeg, default_config)
    assert len(result.limitations) > 0

def test_m4_repeat_runs_identical(valid_jpeg, default_config):
    """M4 must be reproducible: same file → same observations."""
    r1 = run(valid_jpeg, default_config)
    r2 = run(valid_jpeg, default_config)
    assert r1.status == r2.status
    assert r1.observations == r2.observations
