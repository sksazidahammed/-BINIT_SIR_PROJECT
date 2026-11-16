# 09. Limitations and Future Work

## 1. Mandatory System-Wide Limitations
The following 9 limitations are fundamental to digital image forensics and are required to be stated in every assessment report produced by this system:

1. **Absent metadata is not proof of manipulation**: Stripping metadata is standard practice across messaging apps (WhatsApp, Telegram, Signal) and social media platforms for privacy protection and bandwidth savings.
2. **Detectors can be wrong, especially on unseen generators and processed images**: Pretrained machine learning models degrade significantly when exposed to architectures, upscalers, or generative diffusion models outside their training distribution.
3. **Screenshots and repeated processing can erase traces**: Taking a screenshot or re-compressing an image discards camera sensor noise (PRNU), quantisation artefacts, and original metadata signatures.
4. **A valid C2PA manifest does not prove an event**: A cryptographically signed manifest proves that the signing key signed the digital file; it cannot verify whether the scene captured in front of the lens actually took place in physical reality.
5. **A hash does not prove authenticity**: An exact SHA-256 match proves only that the current bytes match the reference bytes; it does not establish that the original image was unmanipulated prior to hash generation.
6. **Heatmaps are indications, not exact pixels**: Spatial localization heatmaps (such as Error Level Analysis or patch detector scores) highlight statistical discrepancies and must not be interpreted as definitive per-pixel edit boundaries.
7. **Results hold only for our evaluation data**: Any empirical performance metrics, false-positive rates, or error bounds apply strictly to the evaluated benchmark splits and may not generalize to in-the-wild internet imagery.
8. **The system is not approved for evidentiary use**: The software is designed for investigative assistance and research analysis; it does not meet the legal threshold for automated courtroom or forensic evidentiary certification.
9. **The benefit of combining the two functions is unproven until tested**: Combining provenance verification with synthetic trace detection is a working hypothesis; its error-reduction benefit remains unproven until empirical ablation experiments (Phase 5) are completed.

---

## 2. Out of Scope
In accordance with Brief Section 9, the following capabilities are explicitly out of scope for this project:
- User accounts, authentication databases, multi-tenant billing, and cloud job queues.
- Multi-image comparison, reverse-image search scraping, and transformation tree graph generation.
- Photo Response Non-Uniformity (PRNU) sensor attribution.
- Face-manipulation, deepfake video, or audio forensics.
- Training novel synthetic detection neural network architectures from scratch.
- Commercial or closed-source detector APIs (non-reproducible).
- Adversarial attack and demographic fairness benchmarking.

---

## 3. Implementation Status Across Phases
- **Phase 1 — Core Infrastructure (M1, M2, M3, M4, M8, CLI)**: **COMPLETE & TESTED**.
- **Phase 2 — Classical Indicators (M5)**: **COMPLETE & TESTED** (Double JPEG, Gallagher resampling, SIFT+DBSCAN copy-move, ELA).
- **Phase 3 — Synthetic Detection Integration (M6)**: **COMPLETE & TESTED** (Open PyTorch detector wrapper, Nelder-Mead temperature scaling calibration, hold-out generator evaluation).
- **Phase 4 — Correlation Engine (M7)**: **COMPLETE & TESTED** (Decision table D1–D8 as audited data table, contradiction flags, principled abstention).
- **Phase 5 — Evaluation Harness & Ablation**: **COMPLETE & TESTED** (Transformations T0–T7, signal survival matrix, risk-coverage curves, paired bootstrap hypothesis test).
- **Phase 6 — Local Report Viewer**: **COMPLETE & TESTED** (Thin HTML exporter co-locating limitations beside each finding with zero analysis logic).

---

## 4. Future Work (Beyond Current Milestone)
- **Multi-Image Provenance Graphs**: Reconstructing the ancestral edit tree across collections of related images.
- **Physical Camera Sensor Attribution (PRNU)**: Camera device identification using Photo Response Non-Uniformity sensor noise finger-printing.
- **Video & Audio Forensic Modalities**: Extending single-image trace and provenance analysis into containerized video streams and speech synthesis detection.
- **Hardware-Accelerated Scalability**: Optimizing PyTorch tensor inference pipelines for multi-threaded batch auditing of massive archival image repositories.
