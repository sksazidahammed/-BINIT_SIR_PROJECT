# Inspect per-sample classical indicator ground truth and predictions
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from forensic.core.config import Config
from forensic.modules import m5_classical

BENCHMARK_DIR = Path("tests/data/classical_benchmark")
with open(BENCHMARK_DIR / "manifest.json") as f:
    samples = json.load(f)

cfg = Config()
print(f"{'Filename':<26} | {'Overall GT':<10} {'Pred':<5} | {'DJ GT':<5} {'Pred':<5} | {'Resamp GT':<9} {'Pred':<5} | {'CM GT':<5} {'Pred':<5}")
print("-" * 88)

for s in samples:
    p = BENCHMARK_DIR / s["filename"]
    rec = m5_classical.run(p, cfg)
    interp = rec.interpretation

    gt_ovr = s["label_overall"]
    pr_ovr = interp.get("classical_indicators_summary")

    gt_dj = s.get("double_jpeg", False)
    pr_dj = interp.get("double_jpeg") == "indicated"

    gt_res = s.get("resampled", s.get("resampling", False))
    pr_res = interp.get("resampling") == "indicated"

    gt_cm = s.get("copy_move", False)
    pr_cm = interp.get("copy_move") == "indicated"

    print(f"{s['filename']:<26} | {gt_ovr:<10} {pr_ovr:<5} | {str(gt_dj):<5} {str(pr_dj):<5} | {str(gt_res):<9} {str(pr_res):<5} | {str(gt_cm):<5} {str(pr_cm):<5}")
