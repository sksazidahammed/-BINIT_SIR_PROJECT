# Tests for the EvidenceRecord schema: validates all fields, status values, and serialisation.
"""
Tests for forensic.core.record — EvidenceRecord schema.
"""
import pytest
import sys
from pathlib import Path
ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))
from forensic.core.record import EvidenceRecord, make_failed_record, make_not_assessed_record, VALID_STATUSES

def _make_valid_record(**kwargs):
    defaults = dict(
        input_sha256="abc123",
        engine="test_engine",
        version="0.1.0",
        method="test",
        parameters={},
        status="completed",
        observations={"x": 1},
        interpretation={"y": "z"},
        regions=None,
        confidence=None,
        limitations=["limit 1"],
    )
    defaults.update(kwargs)
    return EvidenceRecord(**defaults)

def test_valid_record_created():
    r = _make_valid_record()
    assert r.status == "completed"

def test_invalid_status_raises():
    with pytest.raises(ValueError):
        _make_valid_record(status="invalid_status")

def test_all_valid_statuses_accepted():
    for s in VALID_STATUSES:
        r = _make_valid_record(status=s)
        assert r.status == s

def test_to_dict_has_all_fields():
    r = _make_valid_record()
    d = r.to_dict()
    for field in ["input_sha256", "engine", "version", "method", "parameters",
                  "status", "observations", "interpretation", "regions", "confidence", "limitations"]:
        assert field in d

def test_make_failed_record():
    r = make_failed_record("m_test", "0.1.0", "sha256abc", "some error")
    assert r.status == "failed"
    assert r.engine == "m_test"
    assert "some error" in r.observations.get("error", "")

def test_make_not_assessed_record():
    r = make_not_assessed_record("m_test", "0.1.0", "sha256abc", "tool not found")
    assert r.status == "not_assessed"
    assert "tool not found" in r.observations.get("reason", "")

def test_record_serialisable_to_json():
    import json
    r = _make_valid_record()
    d = r.to_dict()
    # Must be JSON serialisable
    s = json.dumps(d)
    assert isinstance(s, str)
    assert len(s) > 0
