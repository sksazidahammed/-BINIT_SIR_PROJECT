# Tests for the CLI: end-to-end pipeline test using pytest and typer's test client.
"""
End-to-end CLI tests for `forensic analyze <image>`.
Tests that the CLI runs without crashing and produces a valid JSON report.
"""
import json
import pytest
from pathlib import Path
import sys
ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))
from typer.testing import CliRunner
from forensic.cli import app

runner = CliRunner()

def test_cli_analyze_valid_jpeg(valid_jpeg, tmp_path):
    """CLI must run without error on a valid JPEG and produce a JSON report."""
    out = tmp_path / "report.json"
    result = runner.invoke(app, ["analyze", str(valid_jpeg), "--out", str(out)])
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert out.exists(), "JSON report was not written"

def test_cli_report_is_valid_json(valid_jpeg, tmp_path):
    """CLI output must be valid JSON."""
    out = tmp_path / "report.json"
    runner.invoke(app, ["analyze", str(valid_jpeg), "--out", str(out)])
    with open(out) as f:
        data = json.load(f)
    assert isinstance(data, dict)
    assert "records" in data

def test_cli_report_has_mandatory_limitations(valid_jpeg, tmp_path):
    """CLI report must include mandatory limitations."""
    out = tmp_path / "report.json"
    runner.invoke(app, ["analyze", str(valid_jpeg), "--out", str(out)])
    with open(out) as f:
        data = json.load(f)
    assert len(data.get("mandatory_limitations", [])) >= 9

def test_cli_report_no_real_fake_verdict(valid_jpeg, tmp_path):
    """CLI report must not contain a real/fake verdict."""
    out = tmp_path / "report.json"
    runner.invoke(app, ["analyze", str(valid_jpeg), "--out", str(out)])
    with open(out) as f:
        data = json.load(f)
    assert data.get("verdict") is None

def test_cli_malformed_file_exits_nonzero(malformed_file, tmp_path):
    """CLI must reject a malformed file with exit code 1."""
    out = tmp_path / "report.json"
    result = runner.invoke(app, ["analyze", str(malformed_file), "--out", str(out)])
    assert result.exit_code != 0, "CLI must exit non-zero for malformed files"

def test_cli_nonexistent_file_exits_nonzero(tmp_path):
    """CLI must handle a nonexistent path gracefully."""
    out = tmp_path / "report.json"
    result = runner.invoke(app, ["analyze", "/nonexistent/image.jpg", "--out", str(out)])
    assert result.exit_code != 0
