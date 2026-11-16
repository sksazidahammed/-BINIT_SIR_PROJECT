# 02 — System Architecture

> **Status: PLANNED — architecture is defined; implementation is in progress.**

---

## High-Level Data Flow

```
Input Image (JPEG/PNG)
        │
        ▼
  ┌─────────────┐
  │  Stage 0    │  validate_image(): magic-byte check, size/pixel limits
  │  Validation │
  └──────┬──────┘
         │ valid
         ▼
  ┌─────────────┐
  │  M1         │  File identity: SHA-256, format, dimensions
  └──────┬──────┘
         │ sha256 → passed to all modules
         ├──────────────────────────────────────┐
         │                                      │
         ▼                                      ▼
  ┌─────────────┐                       ┌─────────────┐
  │  M2         │                       │  M3         │
  │  Metadata   │                       │  C2PA       │
  │  (ExifTool) │                       │  Provenance │
  └──────┬──────┘                       └──────┬──────┘
         │                                     │
         └──────────────┬──────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
  ┌─────────────┐ ┌──────────┐ ┌──────────────┐
  │  M4         │ │  M5      │ │  M6          │
  │ Compression │ │  Noise & │ │  AI Detector │
  │  & Colour   │ │ Geometry │ │  (PLANNED)   │
  └──────┬──────┘ └────┬─────┘ └──────┬───────┘
         │             │              │
         └─────────────┼──────────────┘
                        │
                        ▼
                 ┌─────────────┐
                 │  M7         │  Apply rules D1–D8 (PLANNED)
                 │ Correlation │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │  M8         │  Write JSON + text report
                 │  Report     │
                 └─────────────┘
```

---

## Module Independence Rule

No module may import from another module's file. All modules share:
- `forensic.core.config` — `Config` dataclass
- `forensic.core.hashing` — `compute_sha256`
- `forensic.core.record` — `EvidenceRecord`, `make_failed_record`, `make_not_assessed_record`
- `forensic.core.validate` — `validate_image`

M7 and M8 receive a list of `EvidenceRecord` objects from outside — they do not call module `run()` functions themselves.

---

## EvidenceRecord Flow

```python
EvidenceRecord(
    input_sha256 = "abc123...",   # ties all records to the same file
    engine       = "m1_identity",
    version      = "0.1.0",
    method       = "hashlib-sha256 + pillow-format-detection",
    parameters   = {"chunk_size_bytes": 65536},
    status       = "completed",   # completed | failed | not_run | not_assessed
    observations = {...},          # raw measurements only
    interpretation = {...},        # what measurements may mean
    regions      = None,           # M5 only: list of region dicts
    confidence   = None,           # calibrated confidence if applicable
    limitations  = [...],          # module-specific limitation strings
)
```

---

## Configuration

All runtime limits live in `config.yaml`, loaded via `forensic.core.config.load_config()`. Code never hard-codes limits. Defaults:

| Parameter | Default | Note |
|---|---|---|
| `max_file_bytes` | 52,428,800 (50 MB) | Reject oversized files before decode |
| `max_pixels` | 100,000,000 (100 MP) | Reject images that would OOM |
| `timeout_seconds` | 30 | ExifTool subprocess timeout |
| `supported_formats` | `[JPEG, PNG]` | Checked by magic bytes |
| `exiftool_path` | `null` | `null` = use system PATH |

---

## External Dependencies

| Dependency | Type | Why | Status |
|---|---|---|---|
| ExifTool | External binary | Most complete metadata extraction | NOT INSTALLED — see docs/06 |
| Pillow | Python package | Image open/decode, format detection | INSTALLED 12.1.0 |
| OpenCV | Python package | Noise analysis (M5) | INSTALLED 4.13.0.92 |
| NumPy | Python package | Colour/noise statistics | INSTALLED 2.4.2 |
| scikit-image | Python package | Resampling artefact detection (M5) | INSTALLED 0.26.0 |
| c2pa-python | Python package | C2PA manifest read/validation | INSTALLED 0.39.0 |
| typer | Python package | CLI | INSTALLED 0.29.1 |
| pytest | Python package | Test suite | INSTALLED 9.2.0 |
