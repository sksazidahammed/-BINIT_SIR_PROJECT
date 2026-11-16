# 08. Dataset Documentation

This document records the provenance, licensing, and composition of datasets and pretrained weights used across the project.

In accordance with Product Rule 8 ("Never fabricate datasets or claim a detector works without running evaluation") and AGENTS.md, all datasets and model weights are verified for licensing, hashes, and real acquisition status.

---

## 1. Cryptographic Provenance Test Assets (Phase 1 & 5)

### `c2pa-python` Test Fixtures
- **Dataset / Source**: Official `c2pa-python` test assets repository (`tests/fixtures/`).
- **Repository URL**: `https://github.com/contentauth/c2pa-python`
- **Release / Commit Tag**: `v0.39.0`
- **Licence**: Apache License 2.0 / MIT Dual License (Permissive open source).
- **Access Date**: 2026-11-15
- **Files Stored Locally in `tests/data/c2pa/`**:
  - `C.jpg` (137,886 bytes, SHA-256: `4cbac1af485155f878d12a610da851c2938f2ce886189c61d9da7a0a43bd00b5`): Valid C2PA-signed asset with self-signed test certificate (`present_validated`).
  - `cloud.jpg` (183,901 bytes, SHA-256: `e6ad9f51be5bb83f137322a3f260b5881738e3528aee208727e75b6daaba6092`): Valid C2PA-signed asset with self-signed test certificate (`present_validated`).
  - `C_altered.jpg` (137,886 bytes, SHA-256: `fa0ca345a16d7a46c1ae3b1fead5b8a07153da692997e2f5b4d7557813a84df4`): Byte-tampered copy of `C.jpg` (byte offset 50,000 modified from `0x7B` to `0xFF`). C2PA manifest present but cryptographic signature validation fails (`present_invalid`).
- **Cryptographic Trust Anchor Limitations**: Signed using self-signed development certificates (`C2PA Test Signing Cert`). Test certificates are not rooted in a public PKI trust anchor.

---

## 2. Classical Indicator Smoke Benchmark (Phase 2)

### `classical_benchmark` (N=10)
- **Source**: Derived locally from `skimage.data` BSD-3 licensed photographic assets (`camera`, `astronaut`, `chelsea`, `coffee`).
- **Licence**: BSD-3-Clause (Permissive).
- **Generation Date**: 2026-11-15
- **Location**: `tests/data/classical_benchmark/`
- **Composition**:
  - 4 Authentic camera images (`authentic_01.jpg` – `authentic_04.jpg`)
  - 2 Double JPEG recompressed images (`double_jpeg_01.jpg`, `double_jpeg_02.jpg`)
  - 2 Resampled / interpolated images (`resampled_01.jpg`, `resampled_02.jpg`)
  - 2 Copy-move spliced images (`copy_move_01.jpg`, `copy_move_02.jpg`)
- **Limitation**: $N=10$ is strictly a miniature smoke test for code execution; it cannot support operational accuracy claims.

---

## 3. Real Real-vs-Synthetic Evaluation Dataset (Phase 3 Live Run)

### `tellif/ai_vs_real_image_semantically_similar_eval`
- **Source URL**: `https://huggingface.co/datasets/tellif/ai_vs_real_image_semantically_similar_eval`
- **Hosting Platform**: Hugging Face Hub
- **Access Date**: 2026-11-16
- **Local File**: `eval/data/tellif_test.parquet` (76.77 MB, 80,495,473 bytes)
- **Licence**: Unspecified on Hugging Face dataset card (`license: None`). Used strictly for non-commercial empirical benchmark evaluation.
- **Dataset Composition**: 245 total examples (122 authentic camera images, 123 synthetic AI images across modern generators including ByteDance SeaDream-v4, Gemini Flash, Flux Pro 1.1, Ideogram v2, Imagen 4, Recraft v3, Stable Diffusion 3.5).
- **Empirical Evaluation Subset**: 30 sampled images evaluated live on CPU (15 authentic camera images, 15 synthetic AI images from `bytedance-seedream-v4-text-to-image`).

---

## 4. Pretrained Model Weights (Phase 3)

### OpenAI CLIP ViT-L-14 Visual Backbone
- **Source URL**: `https://openaipublic.azureedge.net/clip/models/b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836/ViT-L-14.pt`
- **Official Repository**: `https://github.com/openai/CLIP`
- **Licence**: MIT License
- **File**: `models/ViT-L-14.pt` (932,768,134 bytes, 889.56 MB)
- **Verified SHA-256**: `b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836` (exact bit-for-bit match with official OpenAI release).
- **Architecture**: Vision Transformer Large (ViT-L/14, 24 transformer layers, patch size 14x14, input resolution 224x224, 768-dimensional latent space).
- **Execution Note**: The official JIT archive hardcodes `cuda:0` in its TorchScript graph. For CPU execution, `state_dict` was extracted and instantiated via native PyTorch `models/clip_model.py` (MIT License).

### Universal Fake Detect (UnivFD) Linear Probe
- **Source URL**: `https://raw.githubusercontent.com/WisconsinAIVision/UniversalFakeDetect/main/pretrained_weights/fc_weights.pth`
- **Official Repository**: `https://github.com/WisconsinAIVision/UniversalFakeDetect`
- **Paper**: *Towards Universal Fake Image Detectors that Generalize Across Generative Models* (CVPR 2023)
- **Licence**: MIT License
- **File**: `models/fc_weights.pth` (4,083 bytes)
- **Verified SHA-256**: `955a15324ec8773e33f38c3be3df1d179aa0bce31b52bc0516fc8e4c0aa0418c`
- **Trained Scope**: 1-class ProGAN detection head on 768-dimensional CLIP ViT-L/14 embeddings.
- **Empirical Generalization Note**: Fails catastrophically ($FNR=100\%$) on modern diffusion/autoregressive models (ByteDance SeaDream-v4), verifying that 2023 probe weights do not transfer to unseen 2024–2026 generators.
