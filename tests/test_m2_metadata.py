# Tests for M2 Metadata extraction via ExifTool.
# ExifTool 13.61 installed at C:/Users/sksaz/AppData/Local/Programs/ExifTool/ExifTool.exe
# Independent reference: ExifTool JSON output is THE reference; this module wraps it.
# Tests verify: completed status with correct dimensions, graceful not_assessed when tool absent.
"""
Tests for forensic.modules.m2_metadata.
ExifTool 13.61 is available. Tests verify correct output on known files,
and graceful not_assessed handling when exiftool_path is set to a nonexistent path.
"""
import pytest
from pathlib import Path
import sys
ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))
from forensic.modules.m2_metadata import run
from forensic.core.config import Config, load_config

# --- helpers ---

def _real_config() -> Config:
    """Config that finds the real ExifTool."""
    cfg_path = ROOT_PATH / "config.yaml"
    return load_config(cfg_path)

def _absent_config() -> Config:
    """Config with a nonexistent ExifTool path — forces not_assessed."""
    return Config(exiftool_path="/nonexistent/exiftool_missing")


# --- tests: ExifTool present ---

def test_m2_completes_on_valid_jpeg(valid_jpeg):
    """M2 must return status=completed on a valid JPEG when ExifTool is available."""
    result = run(valid_jpeg, _real_config())
    assert result.status == "completed", f"Expected completed, got {result.status}: {result.observations}"

def test_m2_reports_correct_dimensions(valid_jpeg):
    """ExifTool-reported dimensions must match the known image size (100x100)."""
    result = run(valid_jpeg, _real_config())
    assert result.status == "completed"
    assert result.observations.get("image_width_declared") == 100
    assert result.observations.get("image_height_declared") == 100

def test_m2_reports_correct_file_type(valid_jpeg):
    """ExifTool must report FileType=JPEG."""
    result = run(valid_jpeg, _real_config())
    assert result.status == "completed"
    assert result.observations.get("file_type") == "JPEG"

def test_m2_records_exiftool_version(valid_jpeg):
    """ExifTool version must be recorded in observations."""
    result = run(valid_jpeg, _real_config())
    assert result.status == "completed"
    ver = result.observations.get("exiftool_version")
    assert ver is not None, "exiftool_version must be recorded"
    # Version is a float like 13.61 or string "13.61"
    assert float(str(ver)) >= 13.0, f"Unexpected ExifTool version: {ver}"

def test_m2_metadata_state_field_present(valid_jpeg):
    """M2 interpretation must have a metadata_state field."""
    result = run(valid_jpeg, _real_config())
    assert result.status == "completed"
    assert "metadata_state" in result.interpretation

def test_m2_no_gps_on_synthetic_test_image(valid_jpeg):
    """Programmatically created test image must have no GPS data."""
    result = run(valid_jpeg, _real_config())
    assert result.status == "completed"
    assert result.observations.get("has_gps") is False

def test_m2_png_completes(valid_png):
    """M2 must also complete for a valid PNG."""
    result = run(valid_png, _real_config())
    assert result.status == "completed"


# --- tests: ExifTool absent ---

def test_m2_no_exiftool_returns_not_assessed(valid_jpeg):
    """When ExifTool path is nonexistent, M2 must return status=not_assessed (not crash)."""
    result = run(valid_jpeg, _absent_config())
    assert result.status == "not_assessed"
    assert result.engine == "m2_metadata"

def test_m2_not_assessed_has_reason(valid_jpeg):
    """not_assessed record must include a human-readable reason."""
    result = run(valid_jpeg, _absent_config())
    assert result.status == "not_assessed"
    reason = result.observations.get("reason", "")
    assert len(reason) > 0, "not_assessed must include a reason"


# --- tests: common properties ---

def test_m2_record_fields_complete(valid_jpeg):
    """M2 record must have all required fields from brief Section 6."""
    result = run(valid_jpeg, _real_config())
    d = result.to_dict()
    for field in ["input_sha256", "engine", "version", "method", "parameters",
                  "status", "observations", "interpretation", "regions", "confidence", "limitations"]:
        assert field in d, f"Missing: {field}"

def test_m2_no_real_fake_label(valid_jpeg):
    """M2 must never output a 'real' or 'fake' label."""
    result = run(valid_jpeg, _real_config())
    for v in result.interpretation.values():
        if isinstance(v, str):
            assert v.lower() not in ("real", "fake")

def test_m2_has_limitations(valid_jpeg):
    """M2 must list at least one limitation."""
    result = run(valid_jpeg, _real_config())
    assert len(result.limitations) > 0

def test_m2_repeat_runs_identical(valid_jpeg):
    """M2 must be reproducible: same file + config → same observations."""
    cfg = _real_config()
    r1 = run(valid_jpeg, cfg)
    r2 = run(valid_jpeg, cfg)
    assert r1.status == r2.status
    # FileModifyDate can vary — exclude filesystem timestamps from comparison
    obs1 = {k: v for k, v in r1.observations.items()
            if k not in ("raw_field_count",)}  # raw_field_count is stable
    obs2 = {k: v for k, v in r2.observations.items()
            if k not in ("raw_field_count",)}
    assert obs1 == obs2, f"M2 not reproducible:\n{obs1}\nvs\n{obs2}"
