# Changelog

All notable changes to the Single-Image Forensic Assessment project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

## [0.1.0] - 2026-11-15 (Phase 1 Baseline)

### Added
- **Repository Architecture & Governance**:
  - `AGENTS.md` and `.agents/rules/project.md` with permanent product rules, safety guidelines, and verification loops.
  - Complete project documentation suite in `docs/` (`00` through `09` plus `PHASE1_PLAN.md`).
  - Pinned `requirements.txt` with license documentation.
  - Standard `pyproject.toml` exposing the `forensic` console entry point.
- **Core Pipeline (`forensic.core`)**:
  - `validate.py`: Stage 0 magic byte identification, size and pixel limit enforcement.
  - `hashing.py`: Forensically immutable SHA-256 computation via 64KB chunking.
  - `record.py`: Standard `EvidenceRecord` dataclass adhering strictly to brief Section 6.
  - `config.py`: YAML-driven limit and executable path configuration.
- **Forensic Modules (`forensic.modules`)**:
  - `m1_identity.py`: Module M1 computing byte SHA-256 and physical image dimensions.
  - `m2_metadata.py`: Module M2 integrating ExifTool 13.61 via subprocess with timeout, timestamp checks, and GPS flags.
  - `m3_c2pa.py`: Module M3 validating C2PA Content Credentials using `c2pa-python 0.39.0`.
  - `m4_compression.py`: Module M4 parsing raw JPEG DQT markers, un-zigzagging into 8×8 raster tables, cross-checking against Pillow, estimating quality factor, and extracting colour statistics.
  - `m5_classical.py`: Tested stub for Phase 2 classical manipulation indicators.
  - `m6_synthetic.py`: Tested stub for Phase 3 synthetic image detection.
- **Correlation & Reporting (`forensic.correlate`, `forensic.report`)**:
  - `rules.py`: Correlation rules D1–D8 encoded as an auditable data structure.
  - `json_report.py`: Deterministic JSON assessment report generator with mandatory limitations and no real/fake label.
  - `text_report.py`: Human-readable plain text report writer.
- **Command-Line Interface (`forensic.cli`)**:
  - `forensic analyze <image> [--out report.json] [--text-out report.txt] [--verbose]` using Typer.
- **Automated Test Suite (`tests/`)**:
  - 92 unit and integration tests covering all Phase 1 components.
  - Programmatic test image generator (`create_test_images.py`).
  - C2PA test fixture suite in `tests/data/c2pa/` (`C.jpg`, `cloud.jpg`, `C_altered.jpg`).
