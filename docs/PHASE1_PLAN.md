# Phase 1 Plan: Core Infrastructure & Provenance Baseline

**Author**: Antigravity Build Agent  
**Date**: 2026-11-15  
**Status**: APPROVED & IMPLEMENTED  

---

## 1. Verified Tool Choices and Dependencies

All dependencies have been explicitly verified on the target operating system (Windows 11, Python 3.14.2) with licenses checked:

| Component | Choice | Exact Version | Licence | Verification Method |
|---|---|---|---|---|
| **Python** | System Python | 3.14.2 | PSF | Verified via `python --version` (Compatible with Python 3.11+ requirement) |
| **Image I/O** | Pillow | 12.1.0 | MIT-CMU | Verified via `import PIL; PIL.__version__` |
| **Array Computing** | NumPy | 2.4.2 | BSD-3-Clause | Verified via `import numpy; numpy.__version__` |
| **Computer Vision** | OpenCV | 4.13.0.92 | Apache-2.0 | Verified via `import cv2; cv2.__version__` |
| **Image Processing**| scikit-image | 0.26.0 | BSD-3-Clause | Installed and verified via `import skimage` |
| **CLI Framework** | Typer | 0.29.1 | MIT | Installed and verified via `import typer` |
| **Testing** | Pytest | 9.2.0 | MIT | Installed and verified via `pytest --version` |
| **C2PA Integration** | c2pa-python | 0.39.0 | MIT / Apache-2.0 | Pure Python wheel with native bindings; verified `c2pa.Reader.try_create` |
| **Metadata Engine** | ExifTool | 13.61 | Artistic-2.0 / GPL-1.0+ | Installed via winget `OliverBetz.ExifTool` at `%LOCALAPPDATA%/Programs/ExifTool/ExifTool.exe` |

---

## 2. Evidence Record Schema (`EvidenceRecord`)

Every module returns an instance of `EvidenceRecord` adhering strictly to Section 6 of the Project Brief:

```python
@dataclass
class EvidenceRecord:
    input_sha256: str               # 64-character lowercase SHA-256 hex digest of raw file bytes
    engine: str                     # Module identifier (e.g. "m1_identity", "m2_metadata")
    version: str                    # Module version string (e.g. "0.1.0")
    method: str                     # Specific algorithm/method used (e.g. "exiftool-subprocess-json")
    parameters: Dict[str, Any]      # Execution parameters, timeouts, seeds, and library versions
    status: str                     # One of: "completed", "failed", "not_run", "not_assessed"
    observations: Dict[str, Any]    # Pure empirical measurements (what was observed)
    interpretation: Dict[str, Any]  # Categorical assessments (what the observations may indicate)
    regions: Optional[List[Dict]]   # Spatial localization masks (M5 only; None for M1-M4)
    confidence: Optional[Dict]      # Calibrated statistical confidence (where applicable; None for M1-M4)
    limitations: List[str]          # Module-specific scientific limitations
```

---

## 3. Test Strategy and Independent Reference Tools

| Module | Test Objective | Independent Reference Tool | Known-Answer Files |
|---|---|---|---|
| **Stage 0** | Byte validation & limit rejection | Direct RFC magic byte constants | `test_valid_jpeg.jpg`, `test_valid_png.png`, `test_malformed.bin`, `test_empty.jpg` |
| **M1** | Exact file hash and dimensions | Python standard library `hashlib.sha256` | Programmatic JPEG/PNG images |
| **M2** | Metadata extraction & consistency | Direct execution of ExifTool 13.61 binary | `test_valid_jpeg.jpg` |
| **M3** | Manifest validity & corruption | Official Content Authenticity test fixtures | `C.jpg` (valid signed), `cloud.jpg` (valid), `C_altered.jpg` (altered copy) |
| **M4** | DQT extraction & colour statistics | Pillow `.quantization` with zig-zag mapping | `test_valid_jpeg.jpg`, `test_valid_png.png` |
| **M8** | Report schema, limits, no real/fake | JSON schema deserializer & text parser | In-memory generated `EvidenceRecord` instances |
| **CLI** | Subprocess invocation & exit codes | Typer `CliRunner` test environment | Synthetic & fixture test images |

---

## 4. Scope Questions and Resolution Log

1. **Question 1: ExifTool Availability**
   - *Question*: ExifTool was not initially present on system PATH.
   - *Resolution*: Installed ExifTool 13.61 using the Windows terminal via `winget install OliverBetz.ExifTool`. Configured `config.yaml` to point explicitly to `%LOCALAPPDATA%/Programs/ExifTool/ExifTool.exe`. M2 executes and passes all validation tests.
2. **Question 2: C2PA Test Assets**
   - *Question*: What test assets to use for positive, altered, and absent C2PA states?
   - *Resolution*: Downloaded official `c2pa-python` test assets (`C.jpg`, `cloud.jpg`) under Apache-2.0 licence. Created an altered copy `C_altered.jpg` by XOR-flipping the trailing bytes to test the negative validation path. Retained plain JPEG for the absent path.
3. **Question 3: Phase Scope Boundaries**
   - *Question*: Scope of M5 and M6 in Phase 1.
   - *Resolution*: Confirmed that M5 (`m5_classical.py`) and M6 (`m6_synthetic.py`) are created as tested stubs returning `status="not_assessed"` and marked `PLANNED`. Phase 2 and 3 work will not begin until Phase 1 is formally concluded.

---

## 5. Documented Assumptions
1. **Python 3.14 Compatibility**: Python 3.14.2 is newer than the brief's "Python 3.11 or later" specification; all required packages install and run without issue.
2. **Test Trust Anchors**: Test certificates in C2PA test fixtures are understood to be testing fixtures, not production trust anchors; this disclaimer is embedded in all relevant output records.
3. **Zero Modification Rule**: The input file is treated as read-only across all operations. Derived files for negative testing (such as `C_altered.jpg`) are stored strictly under `tests/data/` as independent files.
