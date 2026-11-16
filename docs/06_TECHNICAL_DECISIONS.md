# 06. Technical Decisions

This document records the architectural and engineering decisions made during Phase 1.

---

### Decision 1: ExifTool Integration via Isolated Subprocess
- **Problem**: Need comprehensive, forensically reliable extraction of EXIF, IPTC, and XMP metadata without crashing on malformed or proprietary tags.
- **Alternatives Considered**:
  1. Python `Pillow._getexif()`: Limited to basic EXIF; lacks IPTC/XMP and deep camera makernote support.
  2. Python `piexif`: Pure Python, but focused on EXIF editing; misses XMP and complex camera tags.
  3. External ExifTool binary: Comprehensive tag coverage across virtually all cameras and editing software.
- **Choice**: ExifTool 13.61 executed via `subprocess.run` with JSON output (`-json -all`) and a 30-second timeout.
- **Licence**: Artistic-2.0 / GPL-1.0+ (Free for both commercial and non-commercial use).
- **Pros**: Industry-standard reliability, full XMP/IPTC parsing, isolated process avoids Python crashes.
- **Cons**: External binary dependency requiring installation and path resolution.
- **Expected Impact**: Complete metadata extraction across all standard and proprietary image formats.

---

### Decision 2: C2PA Integration with `c2pa-python` Wheel
- **Problem**: Need to verify Content Credentials (C2PA manifests) without requiring developers or automated environments to compile Rust binaries.
- **Alternatives Considered**:
  1. `c2patool` CLI binary: Standalone binary, but requires downloading and managing external binaries per OS architecture or compiling from source with `cargo`.
  2. `c2pa-python` (version 0.39.0): Official Python package with precompiled native wheels supporting Windows, macOS, and Linux.
- **Choice**: `c2pa-python==0.39.0`.
- **Licence**: MIT / Apache-2.0.
- **API Resolution**: Verified that in version 0.39.0, `c2pa.Reader.try_create(format_or_path=...)` is the official factory method, returning `None` if no manifest is embedded, and `reader.get_validation_state()` returns `"Valid"` or `"Invalid"`.
- **Pros**: Direct in-process Python binding, fast execution, cross-platform wheels.
- **Cons**: Rapidly evolving API requiring version pinning.
- **Expected Impact**: Standardized C2PA provenance validation without external CLI toolchain.

---

### Decision 3: Independent Direct DQT Byte Parse vs Pillow Quantization Cross-Check
- **Problem**: Extract JPEG Quantisation Tables (DQT) and ensure values are forensically authentic rather than altered by library re-indexing.
- **Alternatives Considered**:
  1. Rely solely on `Pillow.Image.quantization`.
  2. Parse raw JPEG `0xFF 0xDB` markers directly from the file byte stream.
  3. Use both independently and verify correspondence.
- **Choice**: Implement raw binary DQT parser in `forensic.modules.m4_compression` and verify against Pillow's table using the standard 8×8 zig-zag to raster permutation mapping.
- **Pros**: True independent validation. Detects any parser anomalies or non-standard JPEG headers.
- **Cons**: Requires custom binary marker parsing logic.
- **Expected Impact**: High confidence in compression metrics; immunity to library-specific parsing quirks.

---

### Decision 4: Deterministic JSON Report Design
- **Problem**: Requirement that repeated analysis of the same file yields identical JSON output, preserving reproducibility for forensic auditing.
- **Alternatives Considered**:
  1. Standard `json.dump` with variable dictionary order and timestamp in payload.
  2. Normalized output with sorted keys, fixed precision rounding, and isolated timestamp header.
- **Choice**: Fixed schema with explicit ordering, deterministic data structures, and isolated `report_timestamp` field.
- **Pros**: Audit logs and test runners can verify exact JSON equivalence by comparing documents without timestamp.
- **Cons**: Minor formatting constraints.
- **Expected Impact**: Fully reproducible assessment results.

---

### Decision 5: CLI Architecture with Typer
- **Problem**: Provide an intuitive, production-grade CLI supporting command-line options, clear error exits, and structured logging.
- **Alternatives Considered**:
  1. `argparse`: Standard library, but verbose and lacking modern help formatting.
  2. `click`: Powerful, but requires manual type annotations.
  3. `typer` (0.29.1): Modern, type-driven CLI built on Click with automatic help formatting.
- **Choice**: `typer==0.29.1`.
- **Licence**: MIT.
- **Pros**: Automatic `--help` generation, robust exit codes (1 for rejection, 0 for success), simple testability via `CliRunner`.
- **Cons**: Additional dependency.
- **Expected Impact**: Clean, professional developer and analyst user experience.

---

### Decision 6: Candidate Detector Survey & Selection (Phase 3 - M6)
- **Problem**: Select and integrate a synthetic-image detector meeting all criteria from Brief Section 4:
  1. Open licence (permissive or academic non-commercial).
  2. Publicly available pretrained weights.
  3. Whole-image scope (not face-only).
  4. Documented training data (to prevent test set contamination).
  5. Strictly non-commercial API (reproducible offline).
- **Candidate Detectors Evaluated**:

| Detector | Authors & Venue | Architecture | Training Data | Pretrained Weights | Licence | Suitability & Status |
|---|---|---|---|---|---|---|
| **UnivFD** | Ojha et al., CVPR 2023 | Frozen CLIP ViT-L/14 + Linear Probe | ProGAN (20 classes) | Public (`fc_weights.pth`, 4 KB) | **MIT** | **RECOMMENDED & SUPPORTED**: Permissive licence, tiny classifier footprint, broad cross-generator generalization on unseen diffusion models. |
| **DMID** | Corvi et al., ICIP 2023 | ResNet-50 / ConvNeXt | Latent Diffusion (LDM) | Public on UNINA server (248 MB) | **Apache-2.0** | **APPROVED**: Highly compatible open licence, whole-image architecture. Requires downloading ~250MB weights archive. |
| **CNNDetection** | Wang et al., CVPR 2020 | ResNet-50 | ProGAN | Public (Google Drive) | **CC BY-NC-SA 4.0** | **RESTRICTED**: Non-commercial restrictive licence; weights hosted on interactive cloud drive without stable automated checksum. |
| **DIRE** | Ricker et al., CVPR 2023 | DDIM Inversion Error + ResNet-50 | ADM, Guided Diffusion | Public | **MIT** | **EXCLUDED**: Requires 20–50 full diffusion reconstruction steps per image. Computationally infeasible for interactive or CPU inference. |
| **Commercial APIs** | Various (Hive, Sensity, etc.) | Black-box cloud | Proprietary / Undisclosed | Closed / None | **Commercial** | **STRICTLY EXCLUDED** (Brief Section 4): Non-reproducible, closed-source, data exfiltration risk. |

- **Design Choice for M6**:
  - Implemented `forensic/modules/m6_synthetic.py` as an extensible open detector wrapper.
  - Supports loading open PyTorch checkpoints (e.g. UnivFD / ResNet-50) when provided.
  - Implements **Temperature Scaling** calibration: $P = \sigma(z / T)$ fitted on the calibration split.
  - Implements **Two-Threshold Decision Policy** ($\theta_{\text{low}}=0.35, \theta_{\text{high}}=0.65$), producing 3 distinct states:
    - `"synthetic indicated"` ($P \ge 0.65$)
    - `"inconclusive"` ($0.35 < P < 0.65$)
    - `"synthetic not indicated"` ($P \le 0.35$)
  - In absence of downloaded local weights files, M6 safely functions as a **verified open interface** returning `status="not_assessed"` with exact instructions, strictly preserving pipeline integrity.
- **Expected Impact**: Full mathematical and structural compliance with Brief Section 4 and 6, preventing false certainty or uncalibrated inferences.



---

### Decision 7: C2PA Generative-AI Declaration Field Specification (Phase 4 - Rule D1)
- **Problem**: Confirm the exact machine-readable C2PA manifest field for generative-AI declaration in accordance with the current C2PA specification (Rule D1 requirement).
- **Specification Finding**:
  - The C2PA specification (v1.3 / v2.0) defines generative-AI declarations using the IPTC Digital Source Type vocabulary embedded within signed actions assertions:
    - Assertion store label: `c2pa.actions`
    - Action item dictionary key: `digitalSourceType`
    - Standardized URI values:
      - `http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia` (Created algorithmically from a sampled model, i.e., pure generative-AI).
      - `http://cv.iptc.org/newscodes/digitalsourcetype/compositeWithTrainedAlgorithmicMedia` (Composited or edited with generative AI).
    - Associated action key: `action: "c2pa.created"` or `"c2pa.edited"`.
    - Associated software key: `softwareAgent: "<Model or Tool Name>"`.
  - Secondary / proprietary disclosure assertions: `c2pa.ai_generative` or `com.adobe.generative-ai`.
- **Implementation in M7 Rule D1**:
  - Parser inspects `m3_c2pa` observations. If manifest is validated (`present_validated`), it inspects actions assertions for `digitalSourceType` containing `trainedAlgorithmicMedia` or `compositeWithTrainedAlgorithmicMedia`, or action/assertion labels declaring generative AI.
- **Pros**: Exact adherence to official C2PA and IPTC standards. Prevents false positive AI flags on authenticated camera captures.
- **Expected Impact**: Cryptographic provenance signals accurately trigger Rule D1 without manual heuristics.
