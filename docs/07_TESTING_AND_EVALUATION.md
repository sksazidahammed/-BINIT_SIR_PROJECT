# 07. Testing and Evaluation

This document outlines the testing strategy, independent reference tools, and empirical results across all project modules, strictly distinguishing between **REAL-MEASURED** empirical results, **SIMULATED** pipeline demonstrations, and **NOT RUN** components.

---

## 1. Test Strategy Overview

| Module / Component | Independent Reference Tool / Method | Verification Target | Status | Evidence Level |
|---|---|---|:---:|:---:|
| **Stage 0 (`validate.py`)** | Magic byte binary matching (RFC constants for JPEG/PNG) | Rejection of malformed, oversized, and empty files without decoding | **PASS** | REAL-MEASURED |
| **M1 File Identity** | Python built-in `hashlib.sha256()` stream computation | Exact hex digest match, accurate dimension reporting | **PASS** | REAL-MEASURED |
| **M2 Metadata** | Direct ExifTool 13.61 binary execution output | Correct JSON parsing, dimension matching, GPS detection | **PASS** | REAL-MEASURED |
| **M3 C2PA Provenance** | Official Rust `c2pa-python` 0.39.0 reader against signed/altered test assets | Detection of valid manifest vs altered signature (`present_validated` vs `present_invalid` vs `absent`) | **PASS** | REAL-MEASURED |
| **M4 Compression** | Pillow `_getexif()` and raw JPEG marker parser (SOF0, DQT 0xFFDB markers) | Extracted luminance/chrominance DQT tables, estimated quality | **PASS** | REAL-MEASURED |
| **M5 Classical Indicators** | Automated test suite with $N=10$ labelled fixture set | Detection execution for Double JPEG, Resampling, Copy-Move | **PASS** | REAL-MEASURED (Smoke test) |
| **M6 Synthetic Detection** | Official OpenAI CLIP ViT-L-14 backbone + UnivFD linear probe executed on CPU on $N=30$ real images | Inference speed, decision coverage, accuracy on modern unseen generators | **PARTIAL** | REAL-MEASURED (Real inference) / SIMULATED (Calibration figures) |
| **M7 Correlation Engine** | Pure decision table unit tests (`tests/test_m7_rules.py`) | Rules D1–D8 trigger correctly, detect contradictions, enforce abstentions | **PASS** | REAL-MEASURED |
| **Eval Harness (Ablation)** | Paired bootstrap test, risk-coverage curves over 72 simulated test profiles | Rule-behaviour validation and equal-coverage comparison C0 vs C1 | **PASS** | SIMULATED (Pipeline smoke test) |
| **Eval Harness (Transforms)** | Real transforms T0–T3, T5–T6 applied to real signed fixtures (`C.jpg`, `cloud.jpg`) | Cryptographic and structural signal persistence across lossy transforms | **PASS** | REAL-MEASURED (Pillow 11.1.0) |
| **M8 Report Generation** | Schema validation, determinism tests, forbidden word assertion | Exact reproducible JSON, typed evidence records, zero real/fake labels | **PASS** | REAL-MEASURED |
| **Phase 6 Viewer** | HTML rendering assertions, limitation co-location assertion | Clean visual report display, limitations co-located with findings | **PASS** | REAL-MEASURED |

---

## 2. Hardware Environment & Resource Measurements (2026-11-16)

Measured live on the execution host:
- **Operating System**: Windows 11 (AMD64)
- **Python**: Python 3.14.2 (64-bit), PyTorch 2.10.0+cpu, Torchvision 0.25.0+cpu
- **Total Storage**: 237.18 GB
- **Used Storage**: 152.90 GB
- **Free Storage**: 84.28 GB
- **Total Memory**: 7.75 GB
- **Available Memory**: 1.65 GB (78.8% in use)
- **Download Speed (Azure CDN Range Test)**: 10 MB in 1.59s -> **6.30 MB/s (50.39 Mbps)**
- **Download Speed (Official ViT-L-14 Backbone)**: 932.77 MB in 94.59s -> **9.40 MB/s**
- **Download Speed (Hugging Face Parquet Dataset)**: 76.77 MB in 10.22s -> **7.51 MB/s**

---

## 3. Module M6: Live Empirical Evaluation on Real Images (REAL-MEASURED)

- **Script**: `eval/real_m6_eval.py`
- **Execution Mode**: CPU execution via native PyTorch `nn.Module` (`models/clip_model.py`)
- **Visual Backbone**: OpenAI CLIP ViT-L-14 (`models/ViT-L-14.pt`, 932.77 MB, SHA-256: `b8cca3fd...`, MIT License)
- **Linear Probe**: UnivFD `models/fc_weights.pth` (4,083 bytes, MIT License)
- **Benchmark Dataset**: `tellif/ai_vs_real_image_semantically_similar_eval` (`eval/data/tellif_test.parquet`, 76.77 MB)
- **Sample Evaluated**: $N=30$ real images (15 authentic camera images, 15 synthetic AI images from `bytedance-seedream-v4-text-to-image`)
- **Frozen Thresholds**: $\theta_{\text{low}} = 0.35, \theta_{\text{high}} = 0.65$

### Measured Results:
- **Mean Inference Time**: 1.71 seconds per image on CPU
- **Decision Coverage**: 100.0% (30/30 decided)
- **Inconclusive / Abstention**: 0 (0.0%)
- **Confusion Matrix**:
  - True Positives (TP): 0
  - True Negatives (TN): 15 (All authentic camera images classified as `not_indicated`)
  - False Positives (FP): 0 (FPR = 0.00%)
  - False Negatives (FN): 15 (All modern synthetic images classified as `not_indicated`!)
- **False Negative Rate (FNR)**: **100.00%**
- **Accuracy**: 50.00% (arising solely from correct negative predictions on authentic images)
- **Precision**: 0.00%
- **Recall**: 0.00%
- **F1 Score**: 0.0000

> [!WARNING]
> **Empirical Finding on Detector Generalization**:
> UnivFD's linear probe (trained in 2023 on ProGAN) achieves a **100.0% false negative rate** on modern 2024–2026 diffusion/autoregressive models (`bytedance-seedream-v4`), predicting probabilities $P < 0.05$ (`not_indicated`) for every synthetic image. This empirically proves:
> 1. Product Rule 1: *"Not indicated" never means "real"*.
> 2. Brief Section 9 Limit: *Detectors can be wrong, especially on unseen generators*.

---

## 4. Signal Survival Under Real Image Transformations (REAL-MEASURED)

Measured directly on real signed fixtures (`tests/data/c2pa/C.jpg` and `tests/data/c2pa/cloud.jpg`) using `tools/run_real_transforms.py`. Output recorded in `eval/results/real_survival_results.json`.

**Transformation Libraries & Execution Settings**:
- **T0 (Original)**: Identity baseline.
- **T1 (JPEG Q=70)**: Pillow 11.1.0 `JpegImagePlugin`, `quality=70`, `optimize=False`.
- **T2 (Resize 0.5x)**: Pillow 11.1.0 `Image.Resampling.BILINEAR`, save `quality=90`.
- **T3 (Center Crop 75%)**: Pillow 11.1.0 center crop 75% dimensions, save `quality=90`.
- **T4 (Screen Recapture)**: **NOT RUN**.
- **T5 (Metadata Strip)**: NumPy raw RGB array reconstruction (`Image.fromarray(np.array(im))`), save `quality=90`.
- **T6 (Color Adjustment)**: Pillow 11.1.0 `ImageEnhance.Contrast(im).enhance(1.2)`, save `quality=90`.
- **T7 (Social Platform Upload)**: **NOT RUN**.

### Multi-Fixture Measured Signal Survival Table:
| Transform ID | Transformation Description | SHA-256 Hash | EXIF Metadata | C2PA Manifest | JPEG DQT Tables | Evidence Level |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **T0** | Original baseline | retained | retained | retained | retained | **REAL-MEASURED** |
| **T1** | JPEG recompression ($Q=70$) | altered | retained | lost | altered | **REAL-MEASURED** |
| **T2** | Bilinear resize ($0.5\times$) | altered | retained | lost | altered | **REAL-MEASURED** |
| **T3** | Center crop ($75\%$) | altered | retained | lost | altered | **REAL-MEASURED** |
| **T4** | Screen recapture | NOT RUN | NOT RUN | NOT RUN | NOT RUN | **NOT RUN** |
| **T5** | Metadata stripping | altered | altered | lost | altered | **REAL-MEASURED** |
| **T6** | Contrast enhancement ($1.2\times$) | altered | retained | lost | altered | **REAL-MEASURED** |
| **T7** | Platform re-upload | NOT RUN | NOT RUN | NOT RUN | NOT RUN | **NOT RUN** |

*Note: These survival results hold strictly for Pillow 11.1.0 default behavior and the specified parameters. When Pillow re-saves a C2PA-signed image, it omits the JUMBF APP11 metadata segment, resulting in `c2pa_state = lost` (`absent`).*

---

## 5. Classical Indicators Benchmark (REAL-MEASURED Smoke Test, N=10)

- **Script**: `eval/classical_metrics.py`
- **Dataset**: `tests/data/classical_benchmark/` ($N=10$, derived from `skimage.data` BSD-3 photographic assets)
- **Status**: **REAL-MEASURED** (Miniature smoke test)

| Indicator | TP | FP | TN | FN | Accuracy | Precision | Recall | F1 Score | FPR | FNR |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Double JPEG** | 1 | 4 | 4 | 1 | 50.0% | 20.0% | 50.0% | 0.2857 | 50.0% | 50.0% |
| **Resampling** | 0 | 8 | 2 | 0 | 20.0% | 0.0% | 0.0% | 0.0000 | 80.0% | 0.0% |
| **Copy-Move** | 1 | 1 | 7 | 1 | 80.0% | 50.0% | 50.0% | 0.5000 | 12.5% | 50.0% |
| **Overall** | 5 | 4 | 0 | 1 | 50.0% | 55.6% | 83.3% | 0.6667 | **100.0%** | 16.7% |

> [!IMPORTANT]
> **Sample Size & False Positive Rate Limitation**:
> $N=10$ is strictly a miniature test-suite smoke test verifying code execution. It cannot support operational accuracy claims. Across the 4 authentic single-compressed camera images, classical indicators triggered false alarms on all 4 files (overall FPR = 100.0%). The observation of edge derivative peaks in JPEG-compressed files is an **untested exploratory hypothesis** requiring large-scale uncompressed camera validation (e.g. on RAISE).

---

## 6. Ablation Study: C0 vs C1 at Equal Coverage (SIMULATED Demonstration)

- **Script**: `eval/ablation.py`
- **Output Record**: `eval/results/ablation_results.json`
- **Dataset**: 72 simulated test profiles across 3 benchmark groups
- **Evidence Level**: **SIMULATED** (Software pipeline smoke test and rule-consistency validation)

### Equal-Coverage Comparison:
At equal decision coverage ($65.28\%$, matching C1's decision threshold margin $\Delta = 0.00$), both configurations yield zero classification errors on this simulated dataset:

| Configuration | Decision Policy | Decision Coverage | Error Rate (Risk) | Accuracy | 95% Bootstrap CI | Paired Test ($p$-value) |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **C0 (Calibrated Detector Alone)** | $\theta_{\text{low}} = 0.25, \theta_{\text{high}} = 0.75$ ($\Delta = 0.25$) | **65.28%** | **0.00%** | 100.0% | $[1.0, 1.0]$ | — |
| **C1 (Detector + Correlation Rules)** | Multi-modal rules D1–D8 ($\Delta = 0.00$) | **65.28%** | **0.00%** | 100.0% | $[1.0, 1.0]$ | $\Delta \text{Acc} = 0.00, p = 1.000$ |

**Scientific Interpretation**:
On this simulated benchmark dataset, adjusting C0's threshold margin allows C0 alone to achieve 0.00% error risk at 65.28%, 70.83%, and 75.0% coverage. Therefore, **the data does not show C1 beating C0**. This is a **null result on simulated profiles**. Limitation 9 stands in full: the benefit of combining provenance and detector analysis remains unproven.

---

## 7. Reconciliation of Historical Errata (Audit Record)

| Indicator / Metric | Initial Measured Value | Erroneous Figure in Audit Summary | Source Script | Root Cause Explanation |
|---|:---:|:---:|---|---|
| **Double JPEG Accuracy** | **50.0%** | 80% | `eval/classical_metrics.py` | Transcription error in narrative text; copy-move accuracy (80.0%) was erroneously copied into double-JPEG summary. Script output never changed. |
| **Resampling Accuracy** | **20.0%** | 60% | `eval/classical_metrics.py` | Hallucination / recollection error in narrative prose. Script output never changed from 20.0%. |
| **Midjourney Test Accuracy** | **73.91%** | 78% | `eval/synthetic_eval.py` | Conflation of unseen generator accuracy (73.91%) with overall test recall (78.57%), rounded to 78% in narrative text. |
| **Calibration ECE** | **0.1252** | 0.0540 | `eval/ablation.py` | Agent cited lower calibration errors from memory without re-running scripts. Logged value in `ablation_results.json` is 0.1252. |
| **Brier Score** | **0.0913** | 0.0461 | `eval/ablation.py` | Agent cited lower score from memory without re-running scripts. Logged value in `ablation_results.json` is 0.0913. |
