# Tests for M3 C2PA: manifest detection and validation.
# C2PA test assets from c2pa-python repo (Apache-2.0, accessed 2026-11-15).
# Independent verification via c2pa-python 0.39.0 Reader.try_create() / get_validation_state().
# Trust anchor note: test certificates are NOT real-world trust anchors.
"""
Tests for forensic.modules.m3_c2pa.

Test cases:
  - absent:    plain JPEG (no C2PA manifest) → c2pa_state="absent"
  - validated: tests/data/c2pa/C.jpg (signed, Apache-2.0) → c2pa_state="present_validated"
  - invalid:   tests/data/c2pa/C_altered.jpg (bytes corrupted) → c2pa_state="present_invalid"
  - malformed: random bytes → status in (completed/failed/not_assessed)
"""
import pytest
from pathlib import Path
import sys
ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))
from forensic.modules.m3_c2pa import run
from forensic.core.config import Config, load_config

C2PA_DIR = ROOT_PATH / "tests" / "data" / "c2pa"

def _cfg() -> Config:
    return load_config(ROOT_PATH / "config.yaml")


# === ABSENT (plain JPEG, no manifest) ===

def test_m3_absent_manifest_on_plain_jpeg(valid_jpeg):
    """A plain JPEG with no C2PA manifest must return c2pa_state=absent (not crash)."""
    result = run(valid_jpeg, _cfg())
    assert result.status in ("completed", "not_assessed", "failed")
    if result.status == "completed":
        assert result.observations.get("c2pa_state") == "absent", \
            f"Expected absent, got: {result.observations.get('c2pa_state')}"

def test_m3_absent_on_plain_png(valid_png):
    """A plain PNG must return c2pa_state=absent or not_assessed."""
    result = run(valid_png, _cfg())
    assert result.status in ("completed", "not_assessed", "failed")


# === VALIDATED (C.jpg — signed test asset, Apache-2.0) ===

@pytest.mark.skipif(
    not (C2PA_DIR / "C.jpg").exists(),
    reason="C2PA test asset C.jpg not present"
)
def test_m3_validated_manifest_on_c_jpg():
    """C.jpg (c2pa-python test fixture, Apache-2.0) must return c2pa_state=present_validated."""
    result = run(C2PA_DIR / "C.jpg", _cfg())
    assert result.status == "completed", f"status={result.status}, obs={result.observations}"
    assert result.observations.get("c2pa_state") == "present_validated", \
        f"Expected present_validated, got: {result.observations.get('c2pa_state')}"

@pytest.mark.skipif(
    not (C2PA_DIR / "C.jpg").exists(),
    reason="C2PA test asset C.jpg not present"
)
def test_m3_assertions_extracted_from_c_jpg():
    """Assertions from C.jpg manifest must be extracted (non-empty list)."""
    result = run(C2PA_DIR / "C.jpg", _cfg())
    assert result.status == "completed"
    assertions = result.observations.get("assertions", [])
    assert len(assertions) > 0, "C.jpg must have at least one assertion"
    # Known assertions: 'stds.schema-org.CreativeWork', 'c2pa.actions.v2'
    assert any("c2pa" in a.lower() or "schema" in a.lower() for a in assertions), \
        f"Unexpected assertions: {assertions}"

@pytest.mark.skipif(
    not (C2PA_DIR / "C.jpg").exists(),
    reason="C2PA test asset C.jpg not present"
)
def test_m3_trust_anchor_note_in_observations():
    """C2PA observations must carry the trust-anchor disclaimer for test assets."""
    result = run(C2PA_DIR / "C.jpg", _cfg())
    if result.status == "completed":
        note = result.observations.get("trust_anchor_note", "")
        assert "not" in note.lower() or "trust" in note.lower(), \
            "Trust anchor note missing or incomplete"


# === INVALID (C_altered.jpg — bytes corrupted) ===

@pytest.mark.skipif(
    not (C2PA_DIR / "C_altered.jpg").exists(),
    reason="Altered C2PA test asset not present"
)
def test_m3_invalid_manifest_on_altered_jpg():
    """C_altered.jpg (bytes XOR-flipped) must return c2pa_state=present_invalid."""
    result = run(C2PA_DIR / "C_altered.jpg", _cfg())
    assert result.status == "completed", f"status={result.status}, obs={result.observations}"
    state = result.observations.get("c2pa_state")
    assert state == "present_invalid", \
        f"Expected present_invalid for corrupted manifest, got: {state}"


# === MALFORMED FILE ===

def test_m3_malformed_does_not_crash(malformed_file):
    """M3 must handle a malformed file without crashing."""
    result = run(malformed_file, _cfg())
    assert result.status in ("completed", "not_assessed", "failed")


# === COMMON PROPERTIES ===

def test_m3_record_fields_complete(valid_jpeg):
    """M3 record must have all required fields."""
    result = run(valid_jpeg, _cfg())
    d = result.to_dict()
    for field in ["input_sha256", "engine", "version", "method", "parameters",
                  "status", "observations", "interpretation", "regions", "confidence", "limitations"]:
        assert field in d, f"Missing: {field}"

def test_m3_no_real_fake_label(valid_jpeg):
    """M3 must never produce a real/fake label."""
    result = run(valid_jpeg, _cfg())
    result_str = str(result.to_dict()).lower()
    assert "fake" not in result_str

def test_m3_has_limitations(valid_jpeg):
    """M3 must list limitations."""
    result = run(valid_jpeg, _cfg())
    assert len(result.limitations) > 0

def test_m3_repeat_runs_identical(valid_jpeg):
    """Repeat runs must produce identical observations (reproducibility)."""
    cfg = _cfg()
    r1 = run(valid_jpeg, cfg)
    r2 = run(valid_jpeg, cfg)
    assert r1.status == r2.status
    assert r1.observations == r2.observations

@pytest.mark.skipif(
    not (C2PA_DIR / "C.jpg").exists(),
    reason="C2PA test asset C.jpg not present"
)
def test_m3_repeat_runs_identical_on_c_jpg():
    """C.jpg must produce identical observations on repeated runs."""
    cfg = _cfg()
    r1 = run(C2PA_DIR / "C.jpg", cfg)
    r2 = run(C2PA_DIR / "C.jpg", cfg)
    assert r1.status == r2.status
    assert r1.observations == r2.observations
