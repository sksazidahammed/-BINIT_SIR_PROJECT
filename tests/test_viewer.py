# Tests for Phase 6 Thin Local Report Viewer (forensic/viewer.py)
from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest
from typer.testing import CliRunner

ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))

from forensic.viewer import load_report, render_html_report, export_html_report
from forensic.cli import app

runner = CliRunner()


@pytest.fixture
def sample_report_json(tmp_path):
    """Create a sample valid assessment report JSON."""
    report = {
        "report_version": "1.0",
        "report_timestamp": "2026-11-15T06:00:00Z",
        "input_file": "/path/to/test_image.jpg",
        "modules_run": ["m1_identity", "m2_metadata", "m7_correlation"],
        "records": [
            {
                "engine": "m1_identity",
                "status": "completed",
                "observations": {"sha256": "abcdef123456", "format": "JPEG"},
                "interpretation": {"identity_verified": True},
                "limitations": ["Hash matches bytes only, not real-world capture event."],
            },
            {
                "engine": "m7_correlation",
                "status": "completed",
                "observations": {"fired_rules": ["D5"], "c2pa_manifest_state": "absent"},
                "interpretation": {"synthetic_origin": "synthetic indicated", "provenance_state": "absent (uninformative)"},
                "limitations": [
                    "Correlation rules synthesize typed findings but do not prove ground-truth real-world events.",
                    "Absence of metadata or C2PA manifest is uninformative and never evidence of manipulation."
                ],
            }
        ],
        "mandatory_limitations": [
            "Absent metadata is not proof of manipulation.",
            "Detectors can be wrong, especially on unseen generators and processed images.",
            "Screenshots and repeated processing can erase traces.",
            "A valid C2PA manifest does not prove an event.",
            "A hash does not prove authenticity.",
            "Heatmaps are indications, not exact pixels.",
            "Results hold only for our evaluation data.",
            "The system is not approved for evidentiary use.",
            "The benefit of combining the two functions is unproven until tested."
        ],
        "verdict": None,
        "verdict_note": "This system never returns a real/fake label. See per-module states above."
    }
    json_path = tmp_path / "sample_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return json_path


def test_viewer_load_report(sample_report_json):
    """Test loading JSON report without analysis logic."""
    data = load_report(sample_report_json)
    assert data["report_version"] == "1.0"
    assert len(data["records"]) == 2


def test_viewer_nonexistent_report_raises():
    """Test loading nonexistent report raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_report("nonexistent_report_12345.json")


def test_viewer_render_html_contains_required_sections(sample_report_json):
    """Test rendered HTML displays co-located limitations, null verdict banner, and findings."""
    data = load_report(sample_report_json)
    html_out = render_html_report(data)

    # Co-located limitations present
    assert "Limitations For This Module" in html_out
    assert "Hash matches bytes only, not real-world capture event." in html_out
    assert "Absence of metadata or C2PA manifest is uninformative" in html_out

    # Mandatory limitations present
    assert "Mandatory System-Wide Limitations" in html_out
    assert "Absent metadata is not proof of manipulation." in html_out
    assert "The system is not approved for evidentiary use." in html_out

    # Null verdict banner
    assert "NO BINARY VERDICT" in html_out
    assert "This system never returns a real/fake label" in html_out

    # Findings present
    assert "m1_identity" in html_out
    assert "m7_correlation" in html_out
    assert "abcdef123456" in html_out


def test_viewer_strictly_no_real_fake_verdicts(sample_report_json):
    """Test viewer output never invents or renders binary real/fake verdicts."""
    data = load_report(sample_report_json)
    html_out = render_html_report(data).lower()
    for forbidden in ["verdict: real", "verdict: fake", "verdict: authentic", "is authentic"]:
        assert forbidden not in html_out


def test_viewer_export_html_file(sample_report_json, tmp_path):
    """Test exporting standalone HTML report to disk."""
    out_html = tmp_path / "custom_view.html"
    res_path = export_html_report(sample_report_json, out_html)
    assert res_path.exists()
    assert out_html.stat().st_size > 500


def test_cli_view_command(sample_report_json, tmp_path):
    """Test CLI command 'forensic view <report.json> --out <view.html>'."""
    out_html = tmp_path / "cli_view.html"
    result = runner.invoke(app, ["view", str(sample_report_json), "--out", str(out_html)])
    assert result.exit_code == 0
    assert out_html.exists()
    assert "HTML view generated" in result.output
