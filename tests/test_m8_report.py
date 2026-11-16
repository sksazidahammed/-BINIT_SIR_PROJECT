# Tests for M8 Report: JSON and text report generation.
"""
Tests for forensic.report.json_report and forensic.report.text_report.
"""
import json
import pytest
from pathlib import Path
import sys
ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))

def _make_sample_records(valid_jpeg, default_config):
    """Helper: run M1 and M4 to get real records for report testing."""
    from forensic.modules.m1_identity import run as m1_run
    from forensic.modules.m4_compression import run as m4_run
    r1 = m1_run(valid_jpeg, default_config)
    r4 = m4_run(valid_jpeg, default_config)
    return [r1, r4]

def test_json_report_written(tmp_path, valid_jpeg, default_config):
    """JSON report must be written to the output path."""
    from forensic.report.json_report import write_json_report
    records = _make_sample_records(valid_jpeg, default_config)
    out = tmp_path / "report.json"
    write_json_report(records, out, valid_jpeg)
    assert out.exists()
    assert out.stat().st_size > 0

def test_json_report_valid_json(tmp_path, valid_jpeg, default_config):
    """JSON report must be valid JSON."""
    from forensic.report.json_report import write_json_report
    records = _make_sample_records(valid_jpeg, default_config)
    out = tmp_path / "report.json"
    write_json_report(records, out, valid_jpeg)
    with open(out) as f:
        data = json.load(f)
    assert isinstance(data, dict)

def test_json_report_has_mandatory_limitations(tmp_path, valid_jpeg, default_config):
    """JSON report must include the mandatory system-wide limitations (brief Section 9)."""
    from forensic.report.json_report import write_json_report
    records = _make_sample_records(valid_jpeg, default_config)
    out = tmp_path / "report.json"
    write_json_report(records, out, valid_jpeg)
    with open(out) as f:
        data = json.load(f)
    assert "mandatory_limitations" in data
    assert len(data["mandatory_limitations"]) >= 9

def test_json_report_no_real_fake_verdict(tmp_path, valid_jpeg, default_config):
    """JSON report must not contain a real/fake verdict."""
    from forensic.report.json_report import write_json_report
    records = _make_sample_records(valid_jpeg, default_config)
    out = tmp_path / "report.json"
    write_json_report(records, out, valid_jpeg)
    with open(out) as f:
        content = f.read().lower()
    # The verdict field must be null, not "real" or "fake"
    data = json.loads(content)
    assert data.get("verdict") is None

def test_json_report_repeat_runs_identical(tmp_path, valid_jpeg, default_config):
    """Two reports from the same input must be identical except for the timestamp field."""
    from forensic.report.json_report import write_json_report
    records = _make_sample_records(valid_jpeg, default_config)
    out1 = tmp_path / "r1.json"
    out2 = tmp_path / "r2.json"
    write_json_report(records, out1, valid_jpeg)
    write_json_report(records, out2, valid_jpeg)
    with open(out1) as f: d1 = json.load(f)
    with open(out2) as f: d2 = json.load(f)
    # Remove timestamp before comparison
    d1.pop("report_timestamp", None)
    d2.pop("report_timestamp", None)
    assert d1 == d2

def test_text_report_written(tmp_path, valid_jpeg, default_config):
    """Text report must be written to the output path."""
    from forensic.report.text_report import write_text_report
    records = _make_sample_records(valid_jpeg, default_config)
    out = tmp_path / "report.txt"
    write_text_report(records, out, valid_jpeg)
    assert out.exists()
    content = out.read_text()
    assert "FORENSIC ASSESSMENT REPORT" in content

def test_text_report_has_mandatory_limitations(tmp_path, valid_jpeg, default_config):
    """Text report must include mandatory limitations."""
    from forensic.report.text_report import write_text_report
    records = _make_sample_records(valid_jpeg, default_config)
    out = tmp_path / "report.txt"
    write_text_report(records, out, valid_jpeg)
    content = out.read_text()
    assert "MANDATORY SYSTEM-WIDE LIMITATIONS" in content
    assert "not approved for evidentiary use" in content
