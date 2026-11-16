# Module M7: Correlation Rules (D1-D8) as Data Table and Evaluation Engine
# Why as data: Decision rules can be independently audited, versioned, and verified without hardcoded logic.
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union
from ..core.record import EvidenceRecord, make_failed_record

# Exact C2PA specification fields for generative AI declaration (verified against C2PA v1.3/v2.0 & IPTC standards):
# 1. digitalSourceType URI: http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia
# 2. composite AI URI: http://cv.iptc.org/newscodes/digitalsourcetype/compositeWithTrainedAlgorithmicMedia
# 3. Action assertions label: "c2pa.actions" with action "c2pa.created" or "c2pa.edited"
# 4. Secondary assertion labels: "c2pa.ai_generative", "com.adobe.generative-ai"
C2PA_AI_DIGITAL_SOURCE_TYPES = [
    "http://cv.iptc.org/newscodes/digitalsourcetype/trainedalgorithmicmedia",
    "http://cv.iptc.org/newscodes/digitalsourcetype/compositewithtrainedalgorithmicmedia",
    "trainedalgorithmicmedia",
    "compositewithtrainedalgorithmicmedia",
]

# Default frozen thresholds established on the development split:
DEFAULT_THRESHOLDS = {
    "theta_low": 0.35,
    "theta_high": 0.65,
    "quality_min_reliable": 65,
    "resampling_peak_threshold": 3.0,
}

MODULE_NAME = "m7_correlation"
MODULE_VERSION = "0.1.0"

_M7_LIMITATIONS = [
    "Correlation rules synthesize typed findings but do not prove ground-truth real-world events.",
    "A conflict flag indicates divergent signals between provenance and detector, which can arise from legitimate editing or recapture.",
    "Abstention ('inconclusive') is preferred to unsupported claims when evidence is degraded or conflicting.",
    "Thresholds are frozen from the development split and may require recalibration under severe domain shift.",
    "Never average across orthogonal evidence properties.",
]

RULES: List[Dict[str, Any]] = [
    {
        "id": "D1",
        "name": "C2PA Generative AI Declaration",
        "condition_description": "C2PA validated AND manifest declares generative-AI use (digitalSourceType=trainedAlgorithmicMedia).",
        "output": "synthetic_origin=indicated (generative AI declared by provenance). Detector result shown separately.",
        "note": "Exact manifest field confirmed from C2PA specification: c2pa.actions -> digitalSourceType.",
        "status": "IMPLEMENTED",
        "priority": 1,
    },
    {
        "id": "D2",
        "name": "Provenance vs Detector Conflict",
        "condition_description": "C2PA validated, no AI declaration, detector score high (synthetic indicated).",
        "output": "inconclusive + conflict_flag (signed capture of a displayed synthetic image is possible).",
        "note": "High threshold frozen on development split (theta_high=0.65).",
        "status": "IMPLEMENTED",
        "priority": 2,
    },
    {
        "id": "D3",
        "name": "Validated Camera Capture Without Synthetic Traces",
        "condition_description": "C2PA validated, no AI declaration, detector score low (synthetic not indicated).",
        "output": "synthetic_origin=not_indicated. Recapture limitation noted.",
        "note": "Low threshold frozen on development split (theta_low=0.35).",
        "status": "IMPLEMENTED",
        "priority": 3,
    },
    {
        "id": "D4",
        "name": "Invalid or Tampered Provenance",
        "condition_description": "C2PA manifest present but validation failed.",
        "output": "provenance=not_verifiable + flag. Synthetic origin decided from other evidence.",
        "note": "Do not infer cause of validation failure.",
        "status": "IMPLEMENTED",
        "priority": 4,
    },
    {
        "id": "D5",
        "name": "Absent Metadata and Provenance",
        "condition_description": "C2PA and metadata absent or stripped.",
        "output": "provenance=absent (uninformative). Synthetic origin follows detector alone, labelled detector-only.",
        "note": "Absence of metadata is never proof of manipulation.",
        "status": "IMPLEMENTED",
        "priority": 5,
    },
    {
        "id": "D6",
        "name": "Degraded Conditions Downgrade",
        "condition_description": "M4 or M5 shows low JPEG quality or resampling past reliability threshold.",
        "output": "Downgrade detector output to inconclusive with degraded-conditions note.",
        "note": "Thresholds: quality < 65 or resampling peak ratio > 3.0 set on development split.",
        "status": "IMPLEMENTED",
        "priority": 6,
    },
    {
        "id": "D7",
        "name": "Metadata Inconsistency Flag",
        "condition_description": "M2 reports internal inconsistency.",
        "output": "Raise processing-history indicator. Synthetic-origin state unchanged.",
        "note": "Flags metadata timestamp or dimension mismatches.",
        "status": "IMPLEMENTED",
        "priority": 7,
    },
    {
        "id": "D8",
        "name": "Detector Abstention Margin",
        "condition_description": "Calibrated score between the two thresholds (theta_low < P < theta_high).",
        "output": "inconclusive.",
        "note": "Thresholds [0.35, 0.65] frozen before testing.",
        "status": "IMPLEMENTED",
        "priority": 8,
    },
]


def check_c2pa_ai_declaration(c2pa_record_or_obs: Dict[str, Any]) -> bool:
    """
    Check if a validated C2PA manifest declares generative AI use in accordance with the C2PA specification.
    Inspects digitalSourceType, actions assertions, and software agent strings.
    """
    obs = c2pa_record_or_obs.get("observations", c2pa_record_or_obs)
    if not isinstance(obs, dict):
        return False

    # Check direct flag if pre-parsed
    if obs.get("generative_ai_declared") is True:
        return True

    # Check assertions list
    assertions = obs.get("assertions", [])
    if isinstance(assertions, list):
        for ass in assertions:
            ass_str = str(ass).lower()
            if any(ai_type in ass_str for ai_type in C2PA_AI_DIGITAL_SOURCE_TYPES):
                return True
            if "ai_generative" in ass_str or "generative-ai" in ass_str:
                return True

    # Check raw manifest text / action items
    manifest_summary = obs.get("manifest_summary", {})
    if isinstance(manifest_summary, dict):
        actions = manifest_summary.get("actions", [])
        if isinstance(actions, list):
            for action in actions:
                dst = str(action.get("digitalSourceType", "")).lower()
                if any(ai_type in dst for ai_type in C2PA_AI_DIGITAL_SOURCE_TYPES):
                    return True

    return False


def extract_features_from_records(
    records: Union[List[EvidenceRecord], Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Extract normalized evaluation features from module evidence records.
    """
    rec_map: Dict[str, Any] = {}
    if isinstance(records, dict):
        rec_map = records
    elif isinstance(records, list):
        for r in records:
            if hasattr(r, "engine"):
                rec_map[r.engine] = r.to_dict() if hasattr(r, "to_dict") else r
            elif isinstance(r, dict) and "engine" in r:
                rec_map[r["engine"]] = r

    # M1 Identity
    m1 = rec_map.get("m1_identity", {})
    sha256 = m1.get("input_sha256", "unknown")

    # M2 Metadata
    m2 = rec_map.get("m2_metadata", {})
    m2_obs = m2.get("observations", {})
    m2_state = m2_obs.get("metadata_state", "absent")
    m2_inconsistent = (
        m2_state == "inconsistent"
        or m2_obs.get("timestamp_order_consistent") is False
        or m2_obs.get("declared_vs_actual_dimensions_match") is False
    )

    # M3 C2PA
    m3 = rec_map.get("m3_c2pa", {})
    m3_obs = m3.get("observations", {})
    c2pa_state = m3_obs.get("manifest_state", "absent")
    c2pa_ai_declared = check_c2pa_ai_declaration(m3_obs)

    # M4 Compression
    m4 = rec_map.get("m4_compression", {})
    m4_obs = m4.get("observations", {})
    jpeg_quality = m4_obs.get("jpeg_quality_estimate")

    # M5 Classical
    m5 = rec_map.get("m5_classical", {})
    m5_obs = m5.get("observations", {})
    resampling_ind = m5_obs.get("resampling", {})
    resampling_state = resampling_ind.get("state", "not assessed")
    spectral_peak = resampling_ind.get("spectral_peak_ratio", 1.0)
    double_jpeg_state = m5_obs.get("double_jpeg", {}).get("state", "not assessed")
    copy_move_state = m5_obs.get("copy_move", {}).get("state", "not assessed")

    # M6 Synthetic
    m6 = rec_map.get("m6_synthetic", {})
    m6_obs = m6.get("observations", {})
    m6_interp = m6.get("interpretation", {})
    detector_prob = m6_obs.get("calibrated_probability")
    detector_state = m6_interp.get("synthetic_indication", m6_obs.get("decision_state", "not assessed"))

    return {
        "sha256": sha256,
        "m2_state": m2_state,
        "m2_inconsistent": m2_inconsistent,
        "c2pa_state": c2pa_state,
        "c2pa_ai_declared": c2pa_ai_declared,
        "jpeg_quality": jpeg_quality,
        "resampling_state": resampling_state,
        "resampling_peak": spectral_peak,
        "double_jpeg_state": double_jpeg_state,
        "copy_move_state": copy_move_state,
        "detector_prob": detector_prob,
        "detector_state": detector_state,
        "m6_status": m6.get("status", "not_assessed")
    }


def evaluate_rules(
    features: Dict[str, Any],
    thresholds: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluate correlation decision rules D1-D8 on normalized features.
    Returns structured correlation assessment dictionary.
    """
    th = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        th.update(thresholds)

    c2pa_state = features.get("c2pa_state", "absent")
    c2pa_ai_declared = bool(features.get("c2pa_ai_declared", False))
    detector_state = features.get("detector_state", "not assessed")
    detector_prob = features.get("detector_prob")
    jpeg_quality = features.get("jpeg_quality")
    resampling_state = features.get("resampling_state", "not assessed")
    resampling_peak = float(features.get("resampling_peak", 1.0))
    m2_state = features.get("m2_state", "absent")
    m2_inconsistent = bool(features.get("m2_inconsistent", False))

    fired_rules: List[str] = []
    flags: List[str] = []
    notes: List[str] = []

    # Default synthetic origin from detector
    synthetic_origin = detector_state
    synthetic_origin_detail = "Determined by calibrated synthetic detector."
    provenance_state = c2pa_state

    # Check Rule D7: Metadata Inconsistency
    if m2_inconsistent:
        fired_rules.append("D7")
        flags.append("processing_history_indicator")
        notes.append("Metadata timestamps or declared dimensions are internally inconsistent, indicating post-capture processing.")

    # Check Rule D4: Invalid C2PA manifest
    if c2pa_state in ("present_invalid", "present but not validated", "invalid"):
        fired_rules.append("D4")
        provenance_state = "not verifiable"
        flags.append("provenance_invalid_flag")
        notes.append("C2PA manifest is present but failed cryptographic validation. Cause cannot be inferred; provenance is not verifiable.")

    # Check Rule D6: Degraded conditions (Low JPEG quality or severe resampling)
    degraded = False
    if jpeg_quality is not None and jpeg_quality < th["quality_min_reliable"]:
        degraded = True
    if resampling_state == "indicated" or resampling_peak > th["resampling_peak_threshold"]:
        degraded = True

    if degraded:
        fired_rules.append("D6")
        flags.append("degraded_conditions_flag")
        notes.append("Severe compression or resampling detected. Synthetic detector reliability is compromised; downgrading synthetic origin to inconclusive.")
        synthetic_origin = "inconclusive"
        synthetic_origin_detail = "Downgraded to inconclusive due to degraded conditions (low JPEG quality or resampling)."

    # If not already downgraded by D6, evaluate provenance vs detector rules D1, D2, D3
    if not degraded:
        if c2pa_state in ("present_validated", "present and validated", "Valid"):
            if c2pa_ai_declared:
                # Rule D1: Validated C2PA declares generative AI
                fired_rules.append("D1")
                synthetic_origin = "indicated"
                synthetic_origin_detail = "Generative AI declared by cryptographically validated provenance."
                notes.append("C2PA manifest cryptographically declares generative-AI origin.")
            else:
                # Validated C2PA without AI declaration
                if detector_state == "synthetic indicated" or (detector_prob is not None and detector_prob >= th["theta_high"]):
                    # Rule D2: Conflict between valid non-AI provenance and high detector score
                    fired_rules.append("D2")
                    synthetic_origin = "inconclusive"
                    flags.append("conflict_flag")
                    synthetic_origin_detail = "Inconclusive due to contradiction: validated camera provenance conflicts with high synthetic detector score."
                    notes.append("Contradiction detected: signed capture without AI declaration contradicts high synthetic detector indication. Recapture of displayed synthetic media is possible.")
                elif detector_state == "synthetic not indicated" or (detector_prob is not None and detector_prob <= th["theta_low"]):
                    # Rule D3: Valid non-AI provenance and low detector score
                    fired_rules.append("D3")
                    synthetic_origin = "not indicated"
                    synthetic_origin_detail = "Synthetic origin not indicated by validated provenance and detector."
                    notes.append("C2PA validated camera capture and low synthetic detector score. Note: screen recapture can bypass provenance.")
                else:
                    # Intermediate detector score with valid provenance
                    fired_rules.append("D8")
                    synthetic_origin = "inconclusive"
                    synthetic_origin_detail = "Inconclusive: detector score in abstention margin."

        elif c2pa_state in ("absent", "absent (uninformative)"):
            if m2_state == "absent":
                # Rule D5: Both metadata and C2PA absent
                fired_rules.append("D5")
                provenance_state = "absent (uninformative)"
                notes.append("Provenance and metadata are absent (uninformative; not proof of manipulation). Assessment follows detector alone.")
                if detector_state in ("synthetic indicated", "synthetic not indicated"):
                    synthetic_origin_detail = f"Follows detector alone ('{detector_state}', labelled detector-only)."
                else:
                    synthetic_origin_detail = "Detector-only assessment inconclusive or not assessed."

            # Detector abstention check (Rule D8)
            if detector_state == "inconclusive" or (detector_prob is not None and th["theta_low"] < detector_prob < th["theta_high"]):
                if "D8" not in fired_rules:
                    fired_rules.append("D8")
                synthetic_origin = "inconclusive"
                synthetic_origin_detail = "Detector calibrated score in abstention margin [0.35, 0.65]."

    # Ensure abstention flag is accurately typed
    abstention = (synthetic_origin == "inconclusive")
    contradiction = ("conflict_flag" in flags)

    return {
        "fired_rules": fired_rules,
        "synthetic_origin": synthetic_origin,
        "synthetic_origin_detail": synthetic_origin_detail,
        "provenance_state": provenance_state,
        "flags": flags,
        "contradiction_detected": contradiction,
        "abstention_invoked": abstention,
        "notes": notes,
        "thresholds_used": th,
    }


def correlate(
    records: Union[List[EvidenceRecord], Dict[str, Any]],
    thresholds: Optional[Dict[str, Any]] = None
) -> EvidenceRecord:
    """
    Execute M7 Correlation Layer:
    Synthesize all module evidence records into a structured M7 EvidenceRecord
    containing fired rules, contradiction flags, abstention state, and typed interpretation.
    """
    features = extract_features_from_records(records)
    eval_result = evaluate_rules(features, thresholds)

    observations = {
        "evaluated_modules": list(records.keys()) if isinstance(records, dict) else [r.engine for r in records if hasattr(r, "engine")],
        "c2pa_manifest_state": features["c2pa_state"],
        "c2pa_ai_declared": features["c2pa_ai_declared"],
        "metadata_state": features["m2_state"],
        "metadata_inconsistent": features["m2_inconsistent"],
        "jpeg_quality_estimate": features["jpeg_quality"],
        "resampling_state": features["resampling_state"],
        "detector_state": features["detector_state"],
        "detector_calibrated_prob": features["detector_prob"],
        "fired_rules": eval_result["fired_rules"],
        "contradiction_flags": eval_result["flags"],
    }

    interpretation = {
        "synthetic_origin": eval_result["synthetic_origin"],
        "synthetic_origin_detail": eval_result["synthetic_origin_detail"],
        "provenance_state": eval_result["provenance_state"],
        "contradiction_detected": eval_result["contradiction_detected"],
        "abstention_invoked": eval_result["abstention_invoked"],
        "correlation_notes": eval_result["notes"],
    }

    return EvidenceRecord(
        input_sha256=features["sha256"],
        engine=MODULE_NAME,
        version=MODULE_VERSION,
        method="rule_based_correlation_table (D1-D8)",
        parameters={
            "rules_defined": len(RULES),
            "thresholds": eval_result["thresholds_used"],
        },
        status="completed",
        observations=observations,
        interpretation=interpretation,
        regions=None,
        confidence=None,
        limitations=_M7_LIMITATIONS,
    )


def apply_rules(module_results: Dict[str, Any]) -> Dict[str, Any]:
    """Backward compatibility entry point for apply_rules."""
    features = extract_features_from_records(module_results)
    return evaluate_rules(features)
