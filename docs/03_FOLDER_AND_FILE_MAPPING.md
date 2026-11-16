# 03. Folder and File Mapping

This document provides a complete map of all folders and important files in the repository.

| Exact Path | Job in Simple Language | Inputs | Outputs | Depends On | Used By | Status |
|---|---|---|---|---|---|---|
| `forensic/` | Root Python package containing all assessment modules and core utilities. | N/A | Python package | Python 3.11+ | End users, tests | IMPLEMENTED |
| `forensic/cli.py` | Command-line interface providing `forensic analyze` to run the analysis pipeline. | CLI flags, image path | Exit code, console messages, reports | `typer`, `forensic.core`, `forensic.modules` | Terminal users | TESTED |
| `forensic/core/config.py` | Loads and encapsulates system configuration limits and tool paths from YAML. | `config.yaml` or parameters | `Config` dataclass instance | `pyyaml` | All modules, CLI | TESTED |
| `forensic/core/validate.py` | Stage 0 validator checking file magic bytes, existence, and size limits without decoding image. | File path, `Config` | Validation status dictionary | Standard library | CLI, pipeline | TESTED |
| `forensic/core/hashing.py` | Computes raw byte SHA-256 hex digest using 64KB chunking to avoid RAM spikes. | File path | 64-char SHA-256 hex string | `hashlib` | Modules, CLI | TESTED |
| `forensic/core/record.py` | Defines standard `EvidenceRecord` dataclass and constructors for failed/not-assessed states. | Assessment data | `EvidenceRecord` instances | Standard library | All modules, M8 | TESTED |
| `forensic/modules/m1_identity.py` | Module M1 computing file size, extension, dimensions, and SHA-256 digest. | File path, `Config` | `EvidenceRecord` | `Pillow`, `hashing` | Pipeline, CLI | TESTED |
| `forensic/modules/m2_metadata.py` | Module M2 wrapping ExifTool to parse structural EXIF, GPS, camera, and editing tags. | File path, `Config` | `EvidenceRecord` | `exiftool` binary | Pipeline, CLI | TESTED |
| `forensic/modules/m3_c2pa.py` | Module M3 wrapping Rust `c2pa-python` to verify C2PA JUMBF cryptographic manifests. | File path, `Config` | `EvidenceRecord` | `c2pa-python` | Pipeline, CLI | TESTED |
| `forensic/modules/m4_compression.py` | Module M4 parsing JPEG markers to extract DQT quantization tables and estimate quality. | File path, `Config` | `EvidenceRecord` | `Pillow` | Pipeline, CLI | TESTED |
| `forensic/modules/m5_classical.py` | Module M5 running Double JPEG, Resampling, and Copy-Move detection with spatial maps. | File path, `Config` | `EvidenceRecord` | `numpy`, `scipy`, `cv2` | Pipeline, CLI | TESTED |
| `forensic/modules/m6_synthetic.py` | Module M6 wrapping pretrained synthetic image detector with calibration scaling. | File path, `Config` | `EvidenceRecord` | `torch`, `torchvision` | Pipeline, CLI | TESTED |
| `eval/classical_metrics.py` | Script evaluating confusion matrices and metrics for M5 on labelled benchmark files. | Labelled images | Benchmark metrics table | `m5_classical`, `numpy` | Developers | TESTED |
| `eval/partitions.py` | Splits datasets into train/calib/test with de-duplication via SHA-256 and dHash. | Dataset list | Partition splits dictionary | `hashlib`, `PIL` | Evaluation | TESTED |
| `eval/transforms.py` | Implements image perturbation suite (T0–T6: JPEG, resize, crop, strip, color shift). | Input image | Transformed images | `PIL`, `numpy` | Evaluation | TESTED |
| `eval/metrics.py` | Computes classification metrics, ROC-AUC, Brier score, ECE, and bootstrap CIs. | Scores, labels | Metrics dictionary | `scikit-learn`, `scipy` | Evaluation | TESTED |
| `eval/ablation.py` | Phase 5 ablation study comparing C0 (detector alone) vs C1 (detector + rules) at equal coverage. | Profile dataset | Risk-coverage curves, JSON | `rules`, `metrics` | Developers | TESTED |
| `eval/calibration.py` | Implements temperature scaling calibration and two-threshold decision policy. | Logits, labels | Calibrated probabilities | `scipy.optimize` | Evaluation, M6 | TESTED |
| `eval/synthetic_eval.py` | Evaluates M6 synthetic detector calibration and generalization across generators. | Generator splits | Calibration metrics | `calibration`, `numpy` | Developers | TESTED |
| `eval/real_m6_eval.py` | Executes M6 live on CPU using official CLIP ViT-L-14 backbone on 30 real images. | `tellif_test.parquet` | Confusion matrix, FNR, JSON | `torch`, `clip_model` | Developers | TESTED |
| `eval/run_tellif_full.py` | Evaluates M6 live on CPU across all 245 images in tellif dataset. | `tellif_test.parquet` | ROC-AUC, score distributions | `torch`, `clip_model` | Developers | TESTED |
| `eval/results/` | Output directory storing evaluation benchmark JSON records and plots. | Evaluation runs | JSON / text records | Evaluators | Documentation | IMPLEMENTED |
| `models/ViT-L-14.pt` | Official OpenAI CLIP ViT-L-14 TorchScript archive (932.77 MB, MIT License). | Web download | Pretrained weights | `urllib` | Module M6 CPU run | VERIFIED |
| `models/clip_model.py` | OpenAI native PyTorch CLIP architecture definition (MIT License). | Model state_dict | PyTorch `nn.Module` | `torch` | Module M6 CPU run | VERIFIED |
| `models/fc_weights.pth` | Official UnivFD linear probe checkpoint (4 KB, MIT License). | Web download | FC weight & bias | `torch` | Module M6 CPU run | VERIFIED |
| `eval/data/tellif_test.parquet` | Real-vs-synthetic test dataset from Hugging Face (76.77 MB, 245 images). | Web download | Raw images & labels | `pyarrow`, `pandas` | Module M6 evaluation | VERIFIED |
| `forensic/correlate/rules.py` | Module M7 correlation rules table (D1–D8), contradiction flags, and priority logic. | Module records | Correlated assessment | Standard library | Pipeline, CLI | TESTED |
| `forensic/viewer.py` | Phase 6 thin report viewer rendering JSON assessment reports into standalone HTML. | Assessment JSON | HTML report | Standard library | CLI, end users | TESTED |
| `forensic/report/json_report.py` | Generates final assessment JSON ensuring null verdict and mandatory limitations. | Assessment record | Serialized JSON file | `json` | Pipeline, CLI | TESTED |
| `forensic/report/text_report.py` | Generates human-readable plain text summary of observations and interpretations. | Assessment record | Formatted text string | Standard library | Pipeline, CLI | TESTED |
| `tools/build_report_tables.py` | Extracts markdown tables for project_report.md from eval/results/*.json. | Evaluation JSONs | Markdown tables | Standard library | Documentation | TESTED |
| `tools/inspect_classical.py` | Displays per-sample ground truth vs predictions for classical indicators. | `manifest.json` | Console table | `forensic` | Quality audit | TESTED |
| `tools/run_real_transforms.py` | Measures signal survival on real signed fixtures across T0, T1, T2, T3, T5, T6. | `C.jpg`, `cloud.jpg` | `real_survival_results.json` | `PIL`, `forensic` | Verification | TESTED |
| `tools/verify_determinism.py` | Verifies bit-for-bit JSON reproducibility across repeat runs and absence of real/fake. | Valid image fixture | Verification pass/fail | `forensic` | Quality audit | TESTED |
| `tools/audit_mapping.py` | Audits every path in `03_FOLDER_AND_FILE_MAPPING.md` against real disk. | Folder mapping doc | Path verification log | Standard library | Quality audit | TESTED |
| `config.yaml` | System configuration file specifying tool paths, timeouts, and thresholds. | User edits | Configuration options | YAML parser | `Config` loader | IMPLEMENTED |
| `requirements.txt` | Explicit Python dependency specifications. | PIP package manager | Installed environment | PIP | Developers | COMPLETE |
| `pyproject.toml` | Project build configuration, tool settings, and pytest configuration. | Build systems | Packaging metadata | Standard Python | Developers | COMPLETE |
| `AGENTS.md` | Mandatory permanent agent build rules, product rules, and accuracy guidelines. | Project brief | Operating constraints | Text reader | Build agent, humans | COMPLETE |
| `.agents/rules/project.md` | Antigravity IDE project rules copy matching AGENTS.md. | Project brief | IDE rule constraints | IDE parser | Antigravity Agent | COMPLETE |
| `tests/` | Comprehensive automated test suite containing 138 unit and integration tests. | Pytest harness | Test results | `pytest` | Continuous verification| TESTED |
| `tests/data/` | Fixed test assets, programmatic fixtures, and classical benchmark files. | File system | Sample images | Test runner | Tests | IMPLEMENTED |
| `tests/data/c2pa/` | Cryptographic C2PA test fixtures (`C.jpg`, `cloud.jpg`, `C_altered.jpg`). | C2PA SDK repo | Valid/altered assets | C2PA reader | Tests, verification | IMPLEMENTED |
| `tests/data/progan_control/` | Positive control assets (`progan_fake.png`, `lsun_real.png` from Wang et al.). | CNNDetection repo | ProGAN/LSUN images | M6 verification | Tests, verification | IMPLEMENTED |
| `docs/` | Comprehensive project documentation (`01` through `09`). | Technical notes | Markdown documentation| Documentation reader| Developers, auditors | COMPLETE |
| `development_logs/` | Detailed chronological development history and empirical experiment logs. | Operational logs | Markdown log records | Text reader | Auditors, developers | COMPLETE |
| `reports/` | Academic and technical report (`project_report.md`). | Empirical findings | Formal project report | Markdown reader | Academic evaluation | COMPLETE |
