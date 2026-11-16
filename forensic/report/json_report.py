# JSON report writer: assembles all evidence records into a structured assessment JSON file.
# Why: JSON is machine-readable and stable across runs (same input → same JSON except timestamp).
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Any

_REPORT_VERSION = "1.0"
_LIMITATIONS_MANDATORY = [
    "Absent metadata is not proof of manipulation.",
    "Detectors can be wrong, especially on unseen generators and processed images.",
    "Screenshots and repeated processing can erase traces.",
    "A valid C2PA manifest does not prove an event.",
    "A hash does not prove authenticity.",
    "Heatmaps are indications, not exact pixels.",
    "Results hold only for our evaluation data.",
    "The system is not approved for evidentiary use.",
    "The benefit of combining the two functions is unproven until tested.",
]

_MANDATORY_LIMITATIONS = _LIMITATIONS_MANDATORY  # alias for export


def write_json_report(records: List[Any], output_path: Path, input_path: Path) -> None:
    """
    Write a JSON assessment report from a list of EvidenceRecord objects.
    The report always includes the mandatory limitations from brief Section 9.
    Output is deterministic except for the 'report_timestamp' field.
    """
    output_path = Path(output_path)
    record_dicts = [r.to_dict() if hasattr(r, "to_dict") else r for r in records]
    report = {
        "report_version": _REPORT_VERSION,
        "report_timestamp": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path),
        "modules_run": [r.get("engine", "unknown") if isinstance(r, dict) else r.engine for r in records],
        "records": record_dicts,
        "mandatory_limitations": _MANDATORY_LIMITATIONS,
        "verdict": None,
        "verdict_note": "This system never returns a real/fake label. See per-module states above.",
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
