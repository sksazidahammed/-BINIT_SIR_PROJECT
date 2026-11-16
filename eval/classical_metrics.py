# Evaluation script for Module M5 Classical Indicators on labelled ground-truth benchmark samples.
# Computes True Positives, False Positives, True Negatives, False Negatives,
# Accuracy, Precision, Recall, F1 score, False Positive Rate (FPR), and False Negative Rate (FNR).
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any, Dict
import numpy as np

# Ensure project root is on sys.path
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from forensic.core.config import Config
from forensic.modules import m5_classical

BENCHMARK_DIR = Path(__file__).parent.parent / "tests" / "data" / "classical_benchmark"
MANIFEST_PATH = BENCHMARK_DIR / "manifest.json"


def evaluate_classical_indicators(manifest_path: Path = MANIFEST_PATH) -> Dict[str, Any]:
    """
    Run M5 across all labelled samples in manifest.json and compute empirical metrics.
    No hard-coded metrics; every figure is derived directly from execution.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Benchmark manifest not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    cfg = Config()
    indicators = ["double_jpeg", "resampling", "copy_move"]
    stats = {
        ind: {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
        for ind in indicators
    }
    stats["overall"] = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}

    results_log = []

    for item in samples:
        fpath = manifest_path.parent / item["filename"]
        record = m5_classical.run(fpath, cfg)

        interp = record.interpretation
        is_manipulated_gt = item["label_overall"] == "manipulated"
        is_manipulated_pred = interp.get("classical_indicators_summary") == "indicated"

        # Overall tracking
        if is_manipulated_gt and is_manipulated_pred:
            stats["overall"]["tp"] += 1
        elif not is_manipulated_gt and is_manipulated_pred:
            stats["overall"]["fp"] += 1
        elif not is_manipulated_gt and not is_manipulated_pred:
            stats["overall"]["tn"] += 1
        else:
            stats["overall"]["fn"] += 1

        # Per-indicator tracking
        per_ind_results = {}
        for ind in indicators:
            # Handle manifest naming: 'resampled' vs 'resampling'
            if ind == "resampling":
                gt = bool(item.get("resampled", item.get("resampling", False)))
            else:
                gt = bool(item.get(ind, False))

            pred = interp.get(ind) == "indicated"
            if gt and pred:
                stats[ind]["tp"] += 1
            elif not gt and pred:
                stats[ind]["fp"] += 1
            elif not gt and not pred:
                stats[ind]["tn"] += 1
            else:
                stats[ind]["fn"] += 1
            per_ind_results[ind] = {"gt": gt, "pred": pred}

        results_log.append({
            "filename": item["filename"],
            "sha256": record.input_sha256,
            "overall_gt": item["label_overall"],
            "overall_pred": interp.get("classical_indicators_summary"),
            "indicators": per_ind_results
        })

    # Calculate metrics
    # Recall = TP / (TP + FN) [fraction of truly manipulated images correctly detected]
    # Precision = TP / (TP + FP) [fraction of predicted detections that are actually manipulated]
    metrics = {}
    for key, counts in stats.items():
        tp = counts["tp"]
        fp = counts["fp"]
        tn = counts["tn"]
        fn = counts["fn"]
        total = tp + fp + tn + fn

        acc = (tp + tn) / total if total > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        metrics[key] = {
            "counts": counts,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
        }

    output = {
        "dataset_size": len(samples),
        "metrics": metrics,
        "sample_evaluations": results_log
    }

    # Save to eval/results/classical_benchmark_results.json
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "classical_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    return output


def print_metrics_summary(results: Dict[str, Any]):
    print("=" * 72)
    print("MODULE M5 CLASSICAL INDICATORS: EMPIRICAL BENCHMARK EVALUATION")
    print(f"Total Labelled Samples: {results['dataset_size']}")
    print("=" * 72)
    header = f"{'Indicator':<15} | {'TP':<4} {'FP':<4} {'TN':<4} {'FN':<4} | {'Accuracy':<8} {'Precision':<9} {'Recall':<8} {'F1':<6} {'FPR':<6}"
    print(header)
    print("-" * 72)
    for ind, data in results["metrics"].items():
        c = data["counts"]
        print(
            f"{ind:<15} | {c['tp']:<4} {c['fp']:<4} {c['tn']:<4} {c['fn']:<4} | "
            f"{data['accuracy']:<8.4f} {data['precision']:<9.4f} {data['recall']:<8.4f} {data['f1']:<6.4f} {data['false_positive_rate']:<6.4f}"
        )
    print("=" * 72)


if __name__ == "__main__":
    res = evaluate_classical_indicators()
    print_metrics_summary(res)
