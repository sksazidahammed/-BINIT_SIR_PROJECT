# 00 — Input Brief

> **Status: REFERENCE DOCUMENT — describes the original project specification as given.**

This document records the original brief for the Single-Image Forensic Assessment project, verbatim where possible, so that future workers and reviewers can audit whether the implementation matches the specification.

---

## Project Goal

Build a **single-image forensic assessment tool** that:

1. Takes one JPEG or PNG image as input.
2. Runs a battery of forensic modules (M1–M6).
3. Applies provenance-aware decision rules (M7, D1–D8).
4. Produces a structured JSON report and a human-readable text report (M8).

The system must **never** return a binary "real/fake" label.

---

## Output States (brief Section 2)

| State | Meaning |
|---|---|
| `indicated` | Evidence supports the stated property |
| `not_indicated` | Evidence does not support it — does NOT mean "real" |
| `inconclusive` | Evidence is insufficient to decide |
| `verified` | Cryptographic or hash check passed |
| `not_assessed` | Module could not run (missing dependency, etc.) |

---

## Modules (brief Section 5)

| ID | Name | Purpose |
|---|---|---|
| M1 | File Identity | SHA-256, format detection, dimensions |
| M2 | Metadata | EXIF/IPTC/XMP via ExifTool; timestamp consistency; thumbnail check |
| M3 | C2PA Provenance | Manifest presence, validation, AI-use assertions |
| M4 | Compression & Colour | JPEG quantisation tables, quality estimate, colour stats |
| M5 | Noise & Geometry | Error-level analysis, noise floor, resampling artefacts |
| M6 | AI Detection | Pixel-level synthetic-image detector (PLANNED — model selection pending evaluation) |
| M7 | Correlation | Applies D1–D8 decision rules across module results |
| M8 | Report | Writes JSON + text reports; always includes mandatory limitations |

---

## Evidence Record Schema (brief Section 6)

Every module returns an `EvidenceRecord` with:
- `input_sha256` — hash of the original file bytes
- `engine` — module name
- `version` — module version
- `method` — algorithm used
- `parameters` — all parameters including random seeds
- `status` — one of `{completed, failed, not_run, not_assessed}`
- `observations` — what was measured
- `interpretation` — what it may mean
- `regions` — M5 only: heatmap region data
- `confidence` — calibrated confidence if applicable
- `limitations` — module-specific limitations

---

## Decision Rules (brief Section 7)

| Rule | Condition | Output |
|---|---|---|
| D1 | C2PA validated + AI declared | `synthetic_origin=indicated` |
| D2 | C2PA validated, no AI decl, detector high | `inconclusive + conflict_flag` |
| D3 | C2PA validated, no AI decl, detector low | `synthetic_origin=not_indicated` |
| D4 | C2PA manifest present but validation failed | `provenance=not_verifiable` |
| D5 | C2PA and metadata absent/stripped | `provenance=absent` (uninformative) |
| D6 | Low JPEG quality / heavy resampling | Downgrade detector to `inconclusive` |
| D7 | M2 internal inconsistency | Raise processing-history indicator |
| D8 | Detector score between thresholds | `inconclusive` |

---

## Mandatory Limitations (brief Section 9)

These must appear in every report output:

1. Absent metadata is not proof of manipulation.
2. Detectors can be wrong, especially on unseen generators and processed images.
3. Screenshots and repeated processing can erase traces.
4. A valid C2PA manifest does not prove an event.
5. A hash does not prove authenticity.
6. Heatmaps are indications, not exact pixels.
7. Results hold only for our evaluation data.
8. The system is not approved for evidentiary use.
9. The benefit of combining the two functions is unproven until tested.
