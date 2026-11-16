# 04. Algorithm Design

This document details the algorithms and mathematical implementations of Phase 1 modules.

## Stage 0: File Validation and Limits Enforcement (`forensic.core.validate`)
### Purpose
Safeguard subsequent decoders from malformed payloads, zip bombs, or unsupported file formats by validating files at the byte stream level without executing complex image parsers.

### Algorithm
1. **Existence and Size Check**:
   - Verify `path.exists()`.
   - Measure byte length via `stat().st_size`.
   - If `size == 0`, return `valid=False, reason="File is empty"`.
   - If `size > config.max_file_bytes` (default 50MB), return `valid=False, reason="Size exceeds limit"`.
2. **Magic Byte Identification**:
   - Read the first 16 bytes directly from disk.
   - Match leading bytes against known binary signatures:
     - JPEG: `\xFF\xD8\xFF`
     - PNG: `\x89PNG\r\n\x1a\n` (`0x89 0x50 0x4E 0x47 0x0D 0x0A 0x1A 0x0A`)
   - Reject unrecognised signatures immediately without invoking Pillow or OpenCV.
3. **Format Support**:
   - Verify detected format belongs to `config.supported_formats`.

---

## Module M1: File Identity (`forensic.modules.m1_identity`)
### Purpose
Establish immutable file identity and measure physical pixel dimensions without modifying or re-encoding the file.

### Algorithm
1. **Raw Byte Digest**:
   - Stream file bytes in 64 KB chunks through `hashlib.sha256()`.
   - Never decode or normalize pixels for identity calculation.
2. **Dimension Extraction**:
   - Use Pillow context manager `Image.open(image_path)` to extract image headers.
   - Read `width, height = img.size` and `img.format`.
   - Total pixels = `width * height`.
3. **Output**:
   - Store SHA-256 and dimensions in observations.
   - Interpretation: `file_identity="verified"`.

---

## Module M2: Metadata Analysis (`forensic.modules.m2_metadata`)
### Purpose
Extract comprehensive EXIF, IPTC, and XMP metadata using ExifTool via isolated subprocess with execution timeout.

### Algorithm
1. **Binary Discovery**:
   - Locate ExifTool executable: check `config.exiftool_path` -> system `PATH` -> standard Windows winget directory (`%LOCALAPPDATA%/Programs/ExifTool/ExifTool.exe`).
   - If not found, return `status="not_assessed"` with clear installation instructions.
2. **Isolated Subprocess Invocation**:
   - Execute: `[exiftool_bin, "-json", "-all", str(image_path)]`.
   - Apply strict process timeout (`config.timeout_seconds`, default 30s) to prevent hangs on malicious inputs.
3. **Information Parsing & Consistency**:
   - Parse JSON response array.
   - Check presence of GPS metadata: flag `has_gps` as boolean (never output precise coordinates to protect privacy).
   - Evaluate timestamp consistency: compare `DateTimeOriginal`, `DateTimeDigitized`, and `ModifyDate`.
   - Compare declared image dimensions (`ExifImageWidth`, `ImageWidth`) against actual parsed dimensions.
4. **Output**:
   - State: `present`, `absent`, or `inconsistent`.

---

## Module M3: C2PA Provenance Verification (`forensic.modules.m3_c2pa`)
### Purpose
Validate Content Authenticity Initiative (C2PA) manifests, signatures, and certificate chains using `c2pa-python`.

### Algorithm
1. **Manifest Store Ingestion**:
   - Call `c2pa.Reader.try_create(format_or_path=str(image_path))`.
   - If `reader is None`: File contains no C2PA claim -> output `c2pa_state="absent"`.
2. **Cryptographic Validation**:
   - Query `reader.get_validation_state()`.
   - If state is `"Valid"`: output `c2pa_state="present_validated"`.
   - If state is `"Invalid"`: output `c2pa_state="present_invalid"`.
3. **Assertion Inspection**:
   - Inspect active manifest assertions for generative AI tags (e.g. `c2pa.actions.v2` with `created`, `trainedAlgorithmicMedia`).
4. **Disclaimers**:
   - State clearly that test fixtures rely on test certificates which are not real-world trust anchors.
   - Reiterate that absent manifest is uninformative and never implies manipulation.

---

## Module M4: Compression & Colour Analysis (`forensic.modules.m4_compression`)
### Purpose
Extract low-level JPEG Quantisation Tables (DQT), compute quality factor estimates, and characterize colour distribution.

### Algorithm
1. **Direct JPEG DQT Byte Parsing**:
   - Scan raw JPEG markers for `0xFF 0xDB` (Define Quantization Table).
   - Extract 64-element quantisation arrays in stream (zig-zag) order.
2. **Raster Transformation & Verification**:
   - Map zig-zag ordered tables to standard 8×8 row-major matrices using permutation lookup:
     $$\text{raster}[i] = \text{stream}[\text{ZIGZAG}[i]]$$
   - Cross-verify `raster` table against Pillow's internal `img.quantization` dictionary.
3. **Quality Factor Estimation**:
   - Apply IJG (Independent JPEG Group) empirical quality estimation on the luminance table:
     $$S = \sum_{k=0}^{63} Q_L(k)$$
     $$\text{Quality} = \max\left(1, \min\left(100, \left\lfloor\frac{200 - \lfloor S / 32 \rfloor}{2}\right\rfloor\right)\right)$$
4. **Colour Space Statistics**:
   - Convert image pixels to RGB NumPy array.
   - Mean brightness: $\mu = \frac{1}{3N} \sum_{c, i} P_{c, i}$.
   - Contrast: standard deviation $\sigma = \sqrt{\frac{1}{3N}\sum (P - \mu)^2}$.
   - Saturation: mean standard deviation across colour channels per pixel.
   - Clipping fractions: proportion of pixels hitting 0 or 255.

---

## Module M5: Classical Indicators (`forensic.modules.m5_classical`)
### Purpose
Detect spatial and frequency-domain physical artefacts from image manipulation: double JPEG compression, resampling (interpolation periodicities), copy-move forgery, and Error Level Analysis (ELA).

### Algorithms
1. **Double JPEG Detection**:
   - 8×8 block 2D-DCT performed on image luminance.
   - Histograms of low-to-mid frequency AC coefficients are detrended by mean subtraction.
   - 1D Discrete Fourier Transform (DFT) computed on the histogram. Peak-to-mean spectral energy ratio:
     $$\text{PeakRatio} = \frac{\max_{k \ge 2} |\text{DFT}(H - \bar{H})[k]|}{\text{mean}_{k \ge 2} |\text{DFT}(H - \bar{H})[k]| + \epsilon}$$
   - Spatial block boundary difference ratio measured:
     $$\text{BoundaryRatio} = \frac{\text{mean}(\text{boundary differences})}{\text{mean}(\text{interior differences}) + \epsilon}$$
   - Score $\ge 3.6$ or boundary ratio $> 1.35$ triggers `"indicated"`.
   - Generates 8×8 block AC variance energy heatmap normalized to $[0, 1]$.
2. **Resampling / Interpolation Detection**:
   - Gallagher second-order difference derivative computed horizontally and vertically:
     $$D^2_x[x, y] = I[x+1, y] - 2I[x, y] + I[x-1, y]$$
   - DFT of the 1D mean absolute energy signal across columns/rows reveals periodic interpolation variance peaks.
   - Spectral peak ratio $> 10.5$ triggers `"indicated"`.
   - Generates windowed residual variance heatmap normalized to $[0, 1]$.
3. **Copy-Move Forgery Detection**:
   - Keypoint and local descriptor extraction using SIFT (`cv2.SIFT_create(nfeatures=1500)`).
   - 2NN descriptor matching with Lowe's ratio test threshold $r < 0.75$.
   - Spatial distance constraint: keypoint pairs separated by $< 25$ pixels are discarded to avoid matching natural texture self-similarity.
   - Spatial displacement clustering via DBSCAN on canonical displacement vectors $(\Delta x, \Delta y)$ with $\epsilon = 18.0$, minimum samples $= 4$.
   - If $\ge 1$ cluster with $\ge 4$ consistent pairs is found, outputs `"indicated"`, draws keypoint circles on a binary region mask, and outputs bounding boxes for donor and recipient areas.
4. **Error Level Analysis (ELA)**:
   - In-memory recompression to JPEG quality 90.
   - Pixel absolute difference amplified by scale factor 15.
   - Explicitly documented: *"ELA is a visualisation only and must never be used as proof or decision criterion."*

---

## Module M6: Synthetic Detection Wrapper (`forensic.modules.m6_synthetic`)
### Purpose
Interface for deep neural network synthetic-image detectors, providing probability calibration and two-threshold decision policy.

### Algorithms
1. **Temperature Scaling Calibration**:
   - Scaled probability calculation on raw logit $z$:
     $$P(y = \text{synthetic} \mid x) = \frac{1}{1 + e^{-z / T}}$$
   - Temperature parameter $T > 0$ is optimized on the calibration split via Nelder-Mead simplex to minimize Negative Log Likelihood:
     $$\mathcal{L}_{\text{NLL}}(T) = -\frac{1}{N}\sum_{i=1}^N \left[ y_i \log \hat{p}_i(T) + (1 - y_i) \log(1 - \hat{p}_i(T)) \right]$$
   - Once fitted on the calibration split, $T$ is frozen for all evaluation inference.
2. **Two-Threshold Policy**:
   - Decision states produced:
     $$\text{State} = \begin{cases}
     \text{"synthetic indicated"} & \text{if } P \ge \theta_{\text{high}} \quad (\text{default: } 0.65) \\
     \text{"inconclusive"} & \text{if } \theta_{\text{low}} < P < \theta_{\text{high}} \\
     \text{"synthetic not indicated"} & \text{if } P \le \theta_{\text{low}} \quad (\text{default: } 0.35)
     \end{cases}$$
3. **Pluggable Architecture**:
   - Accepts open PyTorch model weights (UnivFD linear probe / ResNet-50).
   - In absence of local weights, runs as a tested open interface returning `status="not_assessed"` with full limitation annotations.

---

## Module M8: Report Generation (`forensic.report`)
### Purpose
Produce structured JSON and human-readable text representations with embedded limitations.

### Rules Enforced:
1. Every report includes the 9 mandatory system-wide limitations from Brief Section 9.
2. `verdict` field is strictly set to `null` with explicit note: "This system never returns a real/fake label."
3. JSON generation is deterministic: repeat runs yield byte-identical content except for `report_timestamp`.
