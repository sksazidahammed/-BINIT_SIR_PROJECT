# Command-line interface: `forensic analyze <image> [--out report.json] [--config config.yaml]`
# Why Typer: clean CLI with automatic --help generation and type checking.
# This module wires Stage 0 -> M1 -> M2 -> M3 -> M4 -> M8 (report).
# M5, M6, M7 are Phase 2/3/4 and not wired here.
from __future__ import annotations
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import typer

app = typer.Typer(
    help=(
        "Single-Image Forensic Assessment CLI\n\n"
        "Analyses a single image and writes a structured, uncertainty-aware report.\n"
        "NEVER returns a 'real' or 'fake' label.\n"
        "Output states: indicated / not_indicated / inconclusive / verified / not_assessed"
    )
)

def _load_project_root() -> Path:
    """Find the project root (directory containing forensic/ package)."""
    return Path(__file__).parent.parent

@app.command()
def version():
    """Print version and exit."""
    typer.echo("forensic 0.1.0-phase1")


@app.command()
def analyze(
    image: str = typer.Argument(..., help="Path to the image file to analyse."),
    out: str = typer.Option("report.json", "--out", "-o", help="Path for the JSON report output."),
    text_out: Optional[str] = typer.Option(None, "--text-out", "-t", help="Path for the human-readable text report (optional)."),
    config_path: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config.yaml (uses defaults if not given)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print module results to stdout."),
):
    """
    Analyse a single image file and write a forensic assessment report.

    Runs Stage 0 (validation), M1 (file identity), M2 (metadata via ExifTool),
    M3 (C2PA provenance), M4 (compression and colour), and M8 (report).

    The report never contains a real/fake verdict.
    """
    # Ensure imports work regardless of how the CLI is invoked
    root = _load_project_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from forensic.core.config import load_config
    from forensic.core.validate import validate_image
    from forensic.core.hashing import compute_sha256
    from forensic.core.record import make_not_assessed_record
    from forensic.modules import m1_identity, m2_metadata, m3_c2pa, m4_compression, m5_classical, m6_synthetic
    from forensic.correlate.rules import correlate
    from forensic.report.json_report import write_json_report
    from forensic.report.text_report import write_text_report

    image_path = Path(image)
    output_path = Path(out)
    cfg_path = Path(config_path) if config_path else None

    # Load configuration
    config = load_config(cfg_path)

    typer.echo(f"[forensic] Analysing: {image_path}")
    typer.echo(f"[forensic] Output:    {output_path}")

    # === Stage 0: Validate ===
    typer.echo("[forensic] Stage 0: validating file...")
    validation = validate_image(image_path, config)
    if not validation["valid"]:
        typer.echo(f"[forensic] REJECTED at Stage 0: {validation['reason']}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"[forensic] Stage 0 passed. Format: {validation['format']}")

    # === Run modules ===
    records = []

    # M1: File Identity
    typer.echo("[forensic] M1: file identity...")
    r1 = m1_identity.run(image_path, config)
    records.append(r1)
    if verbose:
        typer.echo(f"  M1 status: {r1.status}")

    # M2: Metadata (ExifTool)
    typer.echo("[forensic] M2: metadata (ExifTool)...")
    r2 = m2_metadata.run(image_path, config)
    records.append(r2)
    if verbose:
        typer.echo(f"  M2 status: {r2.status}")

    # M3: C2PA
    typer.echo("[forensic] M3: C2PA provenance...")
    r3 = m3_c2pa.run(image_path, config)
    records.append(r3)
    if verbose:
        typer.echo(f"  M3 status: {r3.status}")

    # M4: Compression and Colour
    typer.echo("[forensic] M4: compression and colour...")
    r4 = m4_compression.run(image_path, config)
    records.append(r4)
    if verbose:
        typer.echo(f"  M4 status: {r4.status}")

    # M5: Classical Indicators
    typer.echo("[forensic] M5: classical indicators...")
    r5 = m5_classical.run(image_path, config)
    records.append(r5)
    if verbose:
        typer.echo(f"  M5 status: {r5.status}")

    # M6: Synthetic Detection (tested open interface)
    typer.echo("[forensic] M6: synthetic detection...")
    r6 = m6_synthetic.run(image_path, config)
    records.append(r6)
    if verbose:
        typer.echo(f"  M6 status: {r6.status}")

    # === M7: Correlation Layer ===
    typer.echo("[forensic] M7: correlation rules (D1-D8)...")
    r7 = correlate(records)
    records.append(r7)
    if verbose:
        typer.echo(f"  M7 status: {r7.status}")
        typer.echo(f"  Fired rules: {r7.observations.get('fired_rules')}")

    # === M8: Report ===
    typer.echo("[forensic] M8: writing reports...")
    write_json_report(records, output_path, image_path)
    typer.echo(f"[forensic] JSON report written: {output_path}")

    if text_out:
        text_path = Path(text_out)
        write_text_report(records, text_path, image_path)
        typer.echo(f"[forensic] Text report written: {text_path}")

    # Print summary
    typer.echo("")
    typer.echo("=== ASSESSMENT SUMMARY ===")
    for r in records:
        typer.echo(f"  {r.engine:20s} | status: {r.status}")
    typer.echo("")
    typer.echo("VERDICT: This system does not return a real/fake label.")
    typer.echo("         See report for per-module states and limitations.")
    typer.echo(f"[forensic] Done. Report: {output_path}")


@app.command()
def view(
    report: str = typer.Argument(..., help="Path to JSON assessment report to view"),
    out: Optional[str] = typer.Option(None, "--out", "-o", help="Optional path to output HTML file"),
    open_browser: bool = typer.Option(False, "--open", help="Open generated HTML view in default web browser"),
):
    """
    Phase 6: Thin local viewer that loads a JSON assessment report and displays it as HTML.
    Contains no analysis logic. Shows module-specific limitations directly beside each finding.
    """
    root = _load_project_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from forensic.viewer import export_html_report
    import webbrowser

    report_p = Path(report)
    if not report_p.exists():
        typer.echo(f"Error: Report file not found: {report_p}", err=True)
        raise typer.Exit(code=1)

    out_p = export_html_report(report_p, out)
    typer.echo(f"[forensic] HTML view generated: {out_p}")

    if open_browser:
        webbrowser.open(out_p.as_uri())


if __name__ == "__main__":
    app()
