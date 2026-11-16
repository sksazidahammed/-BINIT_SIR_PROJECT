# Tests for M7 Correlation rules D1-D8: individual unit test per rule, table tests, and integration.
from __future__ import annotations

import sys
from pathlib import Path
import pytest

ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))

from forensic.correlate.rules import (
    RULES,
    evaluate_rules,
    correlate,
    check_c2pa_ai_declaration,
    DEFAULT_THRESHOLDS,
)
from forensic.core.record import EvidenceRecord

REQUIRED_RULE_FIELDS = {"id", "condition_description", "output", "status"}
EXPECTED_RULE_IDS = {"D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"}


def test_all_eight_rules_present():
    """All eight rules D1-D8 must be defined."""
    ids = {r["id"] for r in RULES}
    assert ids == EXPECTED_RULE_IDS, f"Missing rules: {EXPECTED_RULE_IDS - ids}"


def test_each_rule_has_required_fields():
    """Each rule must have id, condition_description, output, status fields."""
    for rule in RULES:
        for field in REQUIRED_RULE_FIELDS:
            assert field in rule, f"Rule {rule.get('id','?')} missing field: {field}"


@pytest.mark.parametrize("rule_id,expected_keyword", [
    ("D1", "generative"),
    ("D2", "conflict"),
    ("D3", "not_indicated"),
    ("D4", "not_verifiable"),
    ("D5", "absent"),
    ("D6", "inconclusive"),
    ("D7", "indicator"),
    ("D8", "inconclusive"),
])
def test_rule_output_contains_expected_keyword(rule_id, expected_keyword):
    """Each rule's output description must contain the expected keyword."""
    rule = next((r for r in RULES if r["id"] == rule_id), None)
    assert rule is not None, f"Rule {rule_id} not found"
    assert expected_keyword.lower() in rule["output"].lower()


def test_rule_d1_generative_ai_declared_in_c2pa():
    """D1: Validated C2PA declaring generative-AI gives synthetic_origin=indicated (declared by provenance)."""
    features = {
        "c2pa_state": "present_validated",
        "c2pa_ai_declared": True,
        "detector_state": "synthetic not indicated",
        "detector_prob": 0.10,
        "jpeg_quality": 95,
        "resampling_state": "not indicated",
        "resampling_peak": 1.1,
        "m2_state": "present",
        "m2_inconsistent": False,
    }
    result = evaluate_rules(features)
    assert "D1" in result["fired_rules"]
    assert result["synthetic_origin"] == "indicated"
    assert "provenance" in result["synthetic_origin_detail"].lower()
    assert result["abstention_invoked"] is False


def test_rule_d2_provenance_detector_conflict():
    """D2: Validated non-AI C2PA + high detector score -> inconclusive + conflict_flag."""
    features = {
        "c2pa_state": "present_validated",
        "c2pa_ai_declared": False,
        "detector_state": "synthetic indicated",
        "detector_prob": 0.88,
        "jpeg_quality": 92,
        "resampling_state": "not indicated",
        "resampling_peak": 1.2,
        "m2_state": "present",
        "m2_inconsistent": False,
    }
    result = evaluate_rules(features)
    assert "D2" in result["fired_rules"]
    assert result["synthetic_origin"] == "inconclusive"
    assert "conflict_flag" in result["flags"]
    assert result["contradiction_detected"] is True
    assert result["abstention_invoked"] is True


def test_rule_d3_validated_capture_not_indicated():
    """D3: Validated non-AI C2PA + low detector score -> synthetic not indicated."""
    features = {
        "c2pa_state": "present_validated",
        "c2pa_ai_declared": False,
        "detector_state": "synthetic not indicated",
        "detector_prob": 0.15,
        "jpeg_quality": 90,
        "resampling_state": "not indicated",
        "resampling_peak": 1.0,
        "m2_state": "present",
        "m2_inconsistent": False,
    }
    result = evaluate_rules(features)
    assert "D3" in result["fired_rules"]
    assert result["synthetic_origin"] == "not indicated"
    assert "conflict_flag" not in result["flags"]
    assert result["contradiction_detected"] is False
    assert result["abstention_invoked"] is False


def test_rule_d4_invalid_c2pa_manifest():
    """D4: Invalid C2PA manifest -> provenance 'not verifiable' + flag."""
    features = {
        "c2pa_state": "present_invalid",
        "c2pa_ai_declared": False,
        "detector_state": "synthetic indicated",
        "detector_prob": 0.85,
        "jpeg_quality": 90,
        "resampling_state": "not indicated",
        "resampling_peak": 1.0,
        "m2_state": "present",
        "m2_inconsistent": False,
    }
    result = evaluate_rules(features)
    assert "D4" in result["fired_rules"]
    assert result["provenance_state"] == "not verifiable"
    assert "provenance_invalid_flag" in result["flags"]


def test_rule_d5_absent_metadata_and_c2pa():
    """D5: Both C2PA and metadata absent -> uninformative provenance, follows detector alone."""
    features = {
        "c2pa_state": "absent",
        "c2pa_ai_declared": False,
        "detector_state": "synthetic indicated",
        "detector_prob": 0.80,
        "jpeg_quality": 85,
        "resampling_state": "not indicated",
        "resampling_peak": 1.1,
        "m2_state": "absent",
        "m2_inconsistent": False,
    }
    result = evaluate_rules(features)
    assert "D5" in result["fired_rules"]
    assert result["provenance_state"] == "absent (uninformative)"
    assert result["synthetic_origin"] == "synthetic indicated"
    assert "detector-only" in result["synthetic_origin_detail"]


def test_rule_d6_degraded_conditions_downgrade():
    """D6: Low JPEG quality (< 65) or resampling -> downgrade to inconclusive + degraded_conditions_flag."""
    features = {
        "c2pa_state": "absent",
        "c2pa_ai_declared": False,
        "detector_state": "synthetic indicated",
        "detector_prob": 0.90,
        "jpeg_quality": 45,  # heavily compressed
        "resampling_state": "not indicated",
        "resampling_peak": 1.2,
        "m2_state": "present",
        "m2_inconsistent": False,
    }
    result = evaluate_rules(features)
    assert "D6" in result["fired_rules"]
    assert result["synthetic_origin"] == "inconclusive"
    assert "degraded_conditions_flag" in result["flags"]
    assert result["abstention_invoked"] is True


def test_rule_d7_metadata_inconsistency_flag():
    """D7: Inconsistent metadata -> processing_history_indicator flag."""
    features = {
        "c2pa_state": "absent",
        "c2pa_ai_declared": False,
        "detector_state": "synthetic not indicated",
        "detector_prob": 0.20,
        "jpeg_quality": 85,
        "resampling_state": "not indicated",
        "resampling_peak": 1.0,
        "m2_state": "inconsistent",
        "m2_inconsistent": True,
    }
    result = evaluate_rules(features)
    assert "D7" in result["fired_rules"]
    assert "processing_history_indicator" in result["flags"]
    assert result["synthetic_origin"] == "synthetic not indicated"  # State preserved


def test_rule_d8_detector_abstention_margin():
    """D8: Detector score in margin [0.35, 0.65] -> inconclusive."""
    features = {
        "c2pa_state": "absent",
        "c2pa_ai_declared": False,
        "detector_state": "inconclusive",
        "detector_prob": 0.50,
        "jpeg_quality": 85,
        "resampling_state": "not indicated",
        "resampling_peak": 1.0,
        "m2_state": "present",
        "m2_inconsistent": False,
    }
    result = evaluate_rules(features)
    assert "D8" in result["fired_rules"]
    assert result["synthetic_origin"] == "inconclusive"
    assert result["abstention_invoked"] is True


def test_c2pa_ai_declaration_checker():
    """Test helper for recognizing generative AI declarations across C2PA specs."""
    # IPTC digitalSourceType URI
    obs1 = {"assertions": [{"label": "c2pa.actions", "data": {"actions": [{"digitalSourceType": "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"}]}}]}
    assert check_c2pa_ai_declaration(obs1) is True

    # Composite AI
    obs2 = {"assertions": ["http://cv.iptc.org/newscodes/digitalsourcetype/compositeWithTrainedAlgorithmicMedia"]}
    assert check_c2pa_ai_declaration(obs2) is True

    # Adobe generative AI
    obs3 = {"assertions": ["com.adobe.generative-ai"]}
    assert check_c2pa_ai_declaration(obs3) is True

    # Camera capture
    obs4 = {"assertions": ["c2pa.hash.data"]}
    assert check_c2pa_ai_declaration(obs4) is False


def test_correlate_produces_evidence_record():
    """M7 correlate() must return a complete EvidenceRecord with limitations and no real/fake label."""
    records = {
        "m1_identity": {"input_sha256": "abc123hash"},
        "m2_metadata": {"observations": {"metadata_state": "present", "timestamp_order_consistent": True}},
        "m3_c2pa": {"observations": {"manifest_state": "present_validated", "assertions": []}},
        "m4_compression": {"observations": {"jpeg_quality_estimate": 90}},
        "m5_classical": {"observations": {"resampling": {"state": "not indicated", "spectral_peak_ratio": 1.1}}},
        "m6_synthetic": {"observations": {"calibrated_probability": 0.20, "decision_state": "synthetic not indicated"}},
    }
    rec = correlate(records)
    assert isinstance(rec, EvidenceRecord)
    assert rec.engine == "m7_correlation"
    assert rec.status == "completed"
    assert "D3" in rec.observations["fired_rules"]
    assert len(rec.limitations) >= 4
    # Check no real/fake label
    rec_str = str(rec.to_dict()).lower()
    for forbidden in ["'real'", "'fake'", "'authentic'", "'manipulated'"]:
        assert forbidden not in rec_str, f"Forbidden verdict '{forbidden}' in record"
