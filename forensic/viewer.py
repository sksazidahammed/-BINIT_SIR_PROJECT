# Module Phase 6: Thin Local Report Viewer
# Purpose: Load and display a structured forensic assessment JSON report as an accessible HTML view with limitations beside each finding.
# Rule: Contains ZERO analysis logic. Pure presentation only.
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_report(json_path: Union[str, Path]) -> Dict[str, Any]:
    """Load and parse JSON assessment report without performing any analysis."""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def render_html_report(report_data: Dict[str, Any]) -> str:
    """
    Render forensic assessment report to a clean, self-contained HTML document.
    Crucial requirement: Shows limitations directly beside findings, with zero analysis logic.
    """
    input_file = html.escape(str(report_data.get("input_file", "Unknown")))
    report_time = html.escape(str(report_data.get("report_timestamp", "Unknown")))
    report_ver = html.escape(str(report_data.get("report_version", "1.0")))
    verdict_note = html.escape(str(report_data.get("verdict_note", "This system never returns a real/fake label.")))
    mandatory_limits = report_data.get("mandatory_limitations", [])

    records: List[Dict[str, Any]] = report_data.get("records", [])

    # HTML building
    doc = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='utf-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        "  <title>Forensic Assessment Report</title>",
        "  <style>",
        "    :root {",
        "      --bg: #f8fafc; --card-bg: #ffffff; --text: #0f172a; --text-muted: #475569;",
        "      --border: #e2e8f0; --accent: #2563eb; --warning: #d97706; --warning-bg: #fffbeb;",
        "      --danger: #dc2626; --danger-bg: #fef2f2; --success: #16a34a; --success-bg: #f0fdf4;",
        "    }",
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 24px; line-height: 1.5; }",
        "    .container { max-width: 1100px; margin: 0 auto; }",
        "    .header { background: var(--card-bg); padding: 24px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 24px; }",
        "    .banner { background: var(--warning-bg); border-left: 4px solid var(--warning); padding: 16px; border-radius: 4px; margin-top: 16px; font-weight: 500; }",
        "    .mandatory-limits { background: #f1f5f9; border: 1px solid var(--border); padding: 18px; border-radius: 8px; margin-bottom: 24px; font-size: 0.9em; }",
        "    .mandatory-limits ul { margin: 8px 0 0 20px; padding: 0; }",
        "    .record-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 24px; overflow: hidden; }",
        "    .record-header { background: #f8fafc; padding: 14px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }",
        "    .record-title { font-size: 1.1em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }",
        "    .badge { padding: 4px 10px; border-radius: 9999px; font-size: 0.8em; font-weight: 600; text-transform: uppercase; }",
        "    .badge-completed { background: var(--success-bg); color: var(--success); }",
        "    .badge-not-assessed { background: #f1f5f9; color: var(--text-muted); }",
        "    .badge-failed { background: var(--danger-bg); color: var(--danger); }",
        "    .record-body { display: grid; grid-template-columns: 3fr 2fr; gap: 20px; padding: 20px; }",
        "    @media (max-width: 768px) { .record-body { grid-template-columns: 1fr; } }",
        "    .findings-pane { border-right: 1px solid var(--border); padding-right: 20px; }",
        "    @media (max-width: 768px) { .findings-pane { border-right: none; padding-right: 0; border-bottom: 1px solid var(--border); padding-bottom: 20px; } }",
        "    .limits-pane { background: #fafafa; padding: 14px; border-radius: 6px; border: 1px solid #eeeeee; }",
        "    .limits-title { font-weight: 600; color: #b45309; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; font-size: 0.9em; text-transform: uppercase; }",
        "    .limits-list { margin: 0; padding-left: 18px; font-size: 0.85em; color: var(--text-muted); }",
        "    .limits-list li { margin-bottom: 6px; }",
        "    .section-label { font-size: 0.85em; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; }",
        "    .kv-table { width: 100%; border-collapse: collapse; font-size: 0.9em; margin-bottom: 16px; }",
        "    .kv-table td { padding: 6px 8px; border-bottom: 1px solid #f1f5f9; }",
        "    .kv-key { font-weight: 500; color: #334155; width: 40%; word-break: break-all; }",
        "    .kv-val { color: var(--text); font-family: monospace; word-break: break-all; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <div class='container'>",
        "    <div class='header'>",
        "      <h1 style='margin:0 0 8px 0; font-size: 1.6em;'>Single-Image Forensic Assessment Report</h1>",
        f"      <div style='color: var(--text-muted); font-size: 0.9em;'>Input File: <strong>{input_file}</strong></div>",
        f"      <div style='color: var(--text-muted); font-size: 0.85em;'>Generated: {report_time} | Report Version: {report_ver}</div>",
        "      <div class='banner'>",
        f"        ⚖️ <strong>NO BINARY VERDICT:</strong> {verdict_note}",
        "      </div>",
        "    </div>",
        "",
        "    <div class='mandatory-limits'>",
        "      <strong style='color:#334155;'>⚠️ Mandatory System-Wide Limitations (apply to all findings below):</strong>",
        "      <ul>",
    ]

    for limit in mandatory_limits:
        doc.append(f"        <li>{html.escape(str(limit))}</li>")

    doc.extend([
        "      </ul>",
        "    </div>",
        "",
        "    <h2 style='font-size: 1.2em; margin-bottom: 16px; color: #334155;'>Module Evidence Records with Co-Located Limitations</h2>",
    ])

    for rec in records:
        engine = html.escape(str(rec.get("engine", "unknown")))
        status = html.escape(str(rec.get("status", "unknown")))
        badge_cls = "badge-completed" if status == "completed" else ("badge-failed" if status == "failed" else "badge-not-assessed")

        observations = rec.get("observations") or {}
        interpretation = rec.get("interpretation") or {}
        limitations = rec.get("limitations") or []

        doc.extend([
            "    <div class='record-card'>",
            "      <div class='record-header'>",
            f"        <span class='record-title'>{engine}</span>",
            f"        <span class='badge {badge_cls}'>{status}</span>",
            "      </div>",
            "      <div class='record-body'>",
            "        <div class='findings-pane'>",
            "          <div class='section-label'>Observations (What Was Measured)</div>",
            "          <table class='kv-table'>",
        ])

        if observations:
            for k, v in observations.items():
                k_esc = html.escape(str(k))
                v_esc = html.escape(json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v))
                doc.append(f"            <tr><td class='kv-key'>{k_esc}</td><td class='kv-val'>{v_esc}</td></tr>")
        else:
            doc.append("            <tr><td colspan='2' style='color:var(--text-muted);'>No observations recorded.</td></tr>")

        doc.extend([
            "          </table>",
            "",
            "          <div class='section-label' style='margin-top: 14px;'>Interpretation (What It May Mean)</div>",
            "          <table class='kv-table'>",
        ])

        if interpretation:
            for k, v in interpretation.items():
                k_esc = html.escape(str(k))
                v_esc = html.escape(json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v))
                doc.append(f"            <tr><td class='kv-key'>{k_esc}</td><td class='kv-val'>{v_esc}</td></tr>")
        else:
            doc.append("            <tr><td colspan='2' style='color:var(--text-muted);'>No interpretation recorded.</td></tr>")

        doc.extend([
            "          </table>",
            "        </div>",
            "",
            "        <div class='limits-pane'>",
            "          <div class='limits-title'><span>🛡️</span> Limitations For This Module</div>",
            "          <ul class='limits-list'>",
        ])

        if limitations:
            for lim in limitations:
                doc.append(f"            <li>{html.escape(str(lim))}</li>")
        else:
            doc.append("            <li>No specific limitations listed.</li>")

        doc.extend([
            "          </ul>",
            "        </div>",
            "      </div>",
            "    </div>",
        ])

    doc.extend([
        "  </div>",
        "</body>",
        "</html>",
    ])

    return "\n".join(doc)


def export_html_report(json_path: Union[str, Path], output_html_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Export a standalone HTML report file from a JSON report.
    Returns path to created HTML file.
    """
    json_p = Path(json_path)
    report_data = load_report(json_p)
    html_content = render_html_report(report_data)

    if output_html_path is None:
        out_p = json_p.with_suffix(".html")
    else:
        out_p = Path(output_html_path)

    with open(out_p, "w", encoding="utf-8") as f:
        f.write(html_content)

    return out_p
