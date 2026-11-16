# Tests for Evaluation Harness (eval/: transforms.py, metrics.py, ablation.py)
from __future__ import annotations

import sys
from pathlib import Path
import pytest
from PIL import Image
import numpy as np

ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))

from eval.transforms import (
    transform_t0_original,
    transform_t1_jpeg_recompress,
    transform_t2_resize,
    transform_t3_crop,
    transform_t4_screenshot,
    transform_t5_strip_metadata,
    transform_t6_color_adjust,
    transform_t7_platform_reupload,
    apply_sequence,
    get_standard_transformation_suite,
)
from eval.metrics import (
    compute_confusion_matrix,
    compute_classification_metrics,
    compute_roc_auc,
    compute_calibration_metrics,
    compute_bootstrap_ci,
    paired_bootstrap_test,
    assess_signal_survival,
)
from eval.ablation import (
    generate_evaluation_benchmark_data,
    evaluate_c0_detector_alone,
    evaluate_c1_detector_plus_rules,
    compute_risk_coverage_curve,
    run_signal_survival_suite,
    run_ablation_experiment,
)


@pytest.fixture
def sample_pil_image():
    """Create a sample 100x100 test PIL Image."""
    arr = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    return Image.fromarray(arr, "RGB")


def test_transforms_t0_to_t7(sample_pil_image):
    """Test all transformations T0-T7 execute and produce valid image outputs."""
    # T0
    img0, meta0 = transform_t0_original(sample_pil_image)
    assert img0.size == (100, 100)
    assert meta0["transform"] == "T0_original"

    # T1
    img1, meta1 = transform_t1_jpeg_recompress(sample_pil_image, quality=70)
    assert img1.size == (100, 100)
    assert meta1["parameters"]["quality"] == 70

    # T2
    img2, meta2 = transform_t2_resize(sample_pil_image, scale=0.5)
    assert img2.size == (50, 50)

    # T3
    img3, meta3 = transform_t3_crop(sample_pil_image, crop_fraction=0.8)
    assert img3.size == (80, 80)

    # T4
    img4, meta4 = transform_t4_screenshot(sample_pil_image, scale=0.8)
    assert img4.size == (80, 80)

    # T5
    img5, meta5 = transform_t5_strip_metadata(sample_pil_image)
    assert img5.size == (100, 100)

    # T6
    img6, meta6 = transform_t6_color_adjust(sample_pil_image, contrast=1.2)
    assert img6.size == (100, 100)

    # T7
    img7, meta7 = transform_t7_platform_reupload(sample_pil_image, max_dimension=60, quality=75)
    assert max(img7.size) <= 60


def test_transform_sequence(sample_pil_image):
    """Test composition of transformations in sequences (e.g. crop then recompress)."""
    img_seq, hist = apply_sequence(sample_pil_image, ["T3_crop_75", "T1_jpeg_70"])
    assert len(hist) == 2
    assert img_seq.size == (75, 75)


def test_metrics_computation():
    """Test precision, recall, F1, FPR, FNR, accuracy."""
    y_true = [1, 1, 0, 0, 1]
    y_pred = [1, 0, 0, 1, 1]
    # TP=2, FP=1, TN=1, FN=1
    m = compute_classification_metrics(y_true, y_pred)
    assert m["TP"] == 2
    assert m["FP"] == 1
    assert m["TN"] == 1
    assert m["FN"] == 1
    assert m["accuracy"] == 0.6
    assert m["precision"] == round(2 / 3, 4)
    assert m["recall"] == round(2 / 3, 4)


def test_roc_auc_continuous_scores():
    """Test continuous ROC-AUC rank-sum implementation."""
    y_true = [0, 0, 1, 1]
    scores_perfect = [0.1, 0.2, 0.8, 0.9]
    assert compute_roc_auc(y_true, scores_perfect) == 1.0

    scores_inverse = [0.9, 0.8, 0.2, 0.1]
    assert compute_roc_auc(y_true, scores_inverse) == 0.0


def test_calibration_metrics():
    """Test Brier score and ECE calculation."""
    y_true = [0, 0, 1, 1]
    probs = [0.1, 0.2, 0.8, 0.9]
    cal = compute_calibration_metrics(y_true, probs, n_bins=5)
    assert "brier_score" in cal
    assert "ece" in cal
    assert cal["brier_score"] < 0.05  # Well calibrated
    assert len(cal["bins"]) == 5


def test_bootstrap_confidence_intervals():
    """Test non-parametric bootstrap CI."""
    y_true = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    y_pred = [0, 1, 0, 1, 0, 1, 0, 0, 0, 1]
    pe, lower, upper = compute_bootstrap_ci(
        y_true, y_pred,
        lambda yt, yp: compute_classification_metrics(yt, yp)["accuracy"],
        n_bootstrap=200,
        ci=0.95,
        seed=42
    )
    assert lower <= pe <= upper


def test_paired_bootstrap_test():
    """Test paired bootstrap comparison between C0 and C1."""
    y_true = [0, 1, 0, 1, 0, 1, 0, 1, 1, 1]
    p_c0 = [0, 0, 0, 1, 0, 1, 0, 0, 1, 1]  # 80% acc
    p_c1 = [0, 1, 0, 1, 0, 1, 0, 1, 1, 1]  # 100% acc
    res = paired_bootstrap_test(y_true, p_c0, p_c1, n_bootstrap=200, seed=42)
    assert res["delta_observed"] > 0
    assert res["ci_lower"] >= 0
    assert "p_value" in res


def test_signal_survival_assessment():
    """Test tracking survival states: retained, altered, lost, invalid."""
    orig = {
        "sha256": "hashA",
        "m2_state": "present",
        "c2pa_state": "present_validated",
        "jpeg_quality": 90,
        "detector_prob": 0.2,
    }
    # Case 1: Identical -> retained
    surv1 = assess_signal_survival(orig, orig)
    assert surv1["sha256_hash"] == "retained"
    assert surv1["c2pa_manifest"] == "retained"

    # Case 2: Altered bytes -> altered hash, invalid c2pa
    trans = {
        "sha256": "hashB",
        "m2_state": "absent",
        "c2pa_state": "present_invalid",
        "jpeg_quality": 70,
        "detector_prob": 0.22,
    }
    surv2 = assess_signal_survival(orig, trans)
    assert surv2["sha256_hash"] == "altered"
    assert surv2["exif_metadata"] == "lost"
    assert surv2["c2pa_manifest"] == "invalid"
    assert surv2["jpeg_dqt_tables"] == "altered"


def test_ablation_study_runs_end_to_end():
    """Test full execution of ablation study across the three image groups."""
    results = run_ablation_experiment()
    assert "summary" in results
    assert "C0_detector_alone" in results
    assert "C1_detector_plus_rules" in results
    assert "paired_bootstrap" in results
    assert "group_breakdowns" in results
    assert "survival_table" in results
    assert len(results["group_breakdowns"]) == 3
    # Check output json was written
    out_file = ROOT_PATH / "eval" / "results" / "ablation_results.json"
    assert out_file.exists()
