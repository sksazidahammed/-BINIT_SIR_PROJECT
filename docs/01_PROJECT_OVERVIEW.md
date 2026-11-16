# 01 — Project Overview

> **Status: Phase 1 — Core Infrastructure · PLANNED**

---

## Purpose

This project builds a research-grade forensic tool that analyses a single digital image and produces an evidence-typed assessment report. The tool is designed to assist digital forensics researchers and media analysts who need to document image provenance and detect potential synthetic-image signals in a principled, auditable, and transparent way.

The tool is **not** a classifier and **never** outputs a "real" or "fake" label.

---

## Scope

**In scope:**
- JPEG and PNG input images
- Provenance verification: C2PA manifests, EXIF/IPTC/XMP metadata
- Image-signal analysis: compression, noise, geometry, pixel-level AI detection
- Structured JSON + human-readable text reports
- Transparent decision rules (D1–D8)
- Full reproducibility: same input → same output except timestamp

**Out of scope (this version):**
- Video, audio, or multi-image analysis
- Real-time or batch processing pipelines
- Network fetch of images
- Any cloud API calls
- Evidentiary or legal certification

---

## Design Principles

1. **Evidence typing** — every finding is separated into observation / interpretation / limitations.
2. **No binary verdict** — the system uses five typed states, not real/fake.
3. **Reproducibility** — all parameters, versions, and random seeds are recorded.
4. **Modularity** — each module is independent; no module reads another's internals.
5. **Transparency** — decision rules D1–D8 are defined as auditable data.
6. **Safety** — input files are never modified; output is always a new file.

---

## Phases

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | Core infrastructure, schema, CLI stub, M1–M4, M7 rules data, M8 report writers | PLANNED |
| Phase 2 | M5 Noise & Geometry; full test suite with known-answer files | PLANNED |
| Phase 3 | M6 AI Detection; model selection; threshold calibration on development split | PLANNED |
| Phase 4 | M7 rule engine implementation; integration tests | PLANNED |
| Phase 5 | Evaluation on held-out test data; academic report finalisation | PLANNED |

---

## Repository Layout

```
Single-Image Forensic Assessment _ version 1.0/
├── forensic/              # Main Python package
│   ├── core/              # Shared utilities
│   ├── modules/           # M1–M6
│   ├── correlate/         # M7
│   ├── report/            # M8
│   └── cli.py             # CLI entry point
├── tests/                 # pytest suite
│   └── data/              # Known-answer test images
├── docs/                  # This documentation set
├── development_logs/      # CHANGELOG, history, experiment log
├── reports/               # Generated outputs (gitignored)
├── .agents/rules/         # Build-agent rules
├── config.yaml            # Runtime configuration
├── requirements.txt       # Pinned dependencies
├── AGENTS.md              # Agent rules
└── README.md              # Quick-start guide
```
