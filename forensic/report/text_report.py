# Human-readable text report writer: formats evidence records into a readable plain-text report.
# Why: humans need a readable version alongside the machine-readable JSON.
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Any
from .json_report import _LIMITATIONS_MANDATORY

_DIVIDER = "=" * 72


def write_text_report(records: List[Any], output_path: Path, input_path: Path) -> None:
    """
    Write a human-readable text report from a list of EvidenceRecord objects.
    Every section ends with the module's specific limitations.
    The report ends with the mandatory limitations from brief Section 9.
    """
    output_path = Path(output_path)
    lines = []
    lines.append(_DIVIDER)
    lines.append("SINGLE-IMAGE FORENSIC ASSESSMENT REPORT")
    lines.append(_DIVIDER)
    lines.append(f"Input file   : {input_path}")
    lines.append(f"Report time  : {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Report ver   : 1.0")
    lines.append("")
    lines.append("IMPORTANT: This report never states whether an image is 'real' or 'fake'.")
    lines.append("           Output states: indicated / not_indicated / inconclusive / verified / not_assessed")
    lines.append("")

    for rec in records:
        d = rec.to_dict() if hasattr(rec, "to_dict") else rec
        lines.append(_DIVIDER)
        lines.append(f"MODULE: {d.get('engine', 'unknown').upper()}  |  Status: {d.get('status', 'unknown')}")
        lines.append(_DIVIDER)
        lines.append("OBSERVATIONS:")
        for k, v in (d.get("observations") or {}).items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("INTERPRETATION:")
        for k, v in (d.get("interpretation") or {}).items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("LIMITATIONS FOR THIS MODULE:")
        for lim in d.get("limitations") or []:
            lines.append(f"  - {lim}")
        lines.append("")

    lines.append(_DIVIDER)
    lines.append("MANDATORY SYSTEM-WIDE LIMITATIONS (apply to all findings above)")
    lines.append(_DIVIDER)
    for lim in _LIMITATIONS_MANDATORY:
        lines.append(f"  - {lim}")
    lines.append("")
    lines.append(_DIVIDER)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
