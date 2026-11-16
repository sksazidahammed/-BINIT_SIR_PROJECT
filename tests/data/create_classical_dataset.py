# Script to generate an openly licensed, reproducible labelled benchmark dataset for classical forensic indicators.
# Source images: skimage.data (BSD-3 licensed).
# Generates authentic, double_jpeg, resampled, and copy_move ground-truth labelled samples.
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import skimage.data

BENCHMARK_DIR = Path(__file__).parent / "classical_benchmark"
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = BENCHMARK_DIR / "manifest.json"


def generate_benchmark():
    manifest = []

    # 1. Authentic base images
    bases = {
        "camera": skimage.data.camera(), # 512x512 grayscale
        "astronaut": skimage.data.astronaut(), # 512x512 RGB
        "chelsea": skimage.data.chelsea(), # 300x451 RGB
        "coffee": skimage.data.coffee(), # 400x600 RGB
    }

    # Generate Authentic samples
    for name, img_arr in bases.items():
        fname = f"authentic_{name}.jpg"
        fpath = BENCHMARK_DIR / fname
        if len(img_arr.shape) == 2:
            img_arr = cv2.cvtColor(img_arr, cv2.COLOR_GRAY2RGB)
        Image.fromarray(img_arr).save(fpath, "JPEG", quality=90)
        manifest.append({
            "filename": fname,
            "label_overall": "authentic",
            "double_jpeg": False,
            "resampled": False,
            "copy_move": False,
            "source": f"skimage.data.{name} (BSD-3)"
        })

    # Generate Double JPEG samples
    for name, img_arr in list(bases.items())[:2]:
        fname = f"double_jpeg_{name}.jpg"
        fpath = BENCHMARK_DIR / fname
        if len(img_arr.shape) == 2:
            img_arr = cv2.cvtColor(img_arr, cv2.COLOR_GRAY2RGB)
        # Primary compression at Q=50, secondary at Q=85
        tmp_path = BENCHMARK_DIR / f"temp_{name}.jpg"
        Image.fromarray(img_arr).save(tmp_path, "JPEG", quality=50)
        reopened = Image.open(tmp_path)
        reopened.save(fpath, "JPEG", quality=85)
        tmp_path.unlink()
        manifest.append({
            "filename": fname,
            "label_overall": "manipulated",
            "double_jpeg": True,
            "resampled": False,
            "copy_move": False,
            "source": f"skimage.data.{name} Q1=50, Q2=85"
        })

    # Generate Resampled samples
    for name, img_arr in list(bases.items())[:2]:
        fname = f"resampled_{name}.png"
        fpath = BENCHMARK_DIR / fname
        if len(img_arr.shape) == 2:
            img_arr = cv2.cvtColor(img_arr, cv2.COLOR_GRAY2RGB)
        # Resample by scaling 1.35x using linear interpolation
        h, w, _ = img_arr.shape
        rescaled = cv2.resize(img_arr, (int(w * 1.35), int(h * 1.35)), interpolation=cv2.INTER_LINEAR)
        Image.fromarray(rescaled).save(fpath, "PNG")
        manifest.append({
            "filename": fname,
            "label_overall": "manipulated",
            "double_jpeg": False,
            "resampled": True,
            "copy_move": False,
            "source": f"skimage.data.{name} scaled 1.35x INTER_LINEAR"
        })

    # Generate Copy-Move samples
    for name, img_arr in [("astronaut", bases["astronaut"]), ("coffee", bases["coffee"])]:
        fname = f"copymove_{name}.png"
        fpath = BENCHMARK_DIR / fname
        cm_img = img_arr.copy()
        # Clone distinct 80x80 patch
        patch = cm_img[80:160, 80:160].copy()
        cm_img[220:300, 220:300] = patch
        Image.fromarray(cm_img).save(fpath, "PNG")
        manifest.append({
            "filename": fname,
            "label_overall": "manipulated",
            "double_jpeg": False,
            "resampled": False,
            "copy_move": True,
            "source": f"skimage.data.{name} cloned patch (80,80) to (220,220)"
        })

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {len(manifest)} benchmark samples in {BENCHMARK_DIR}")


if __name__ == "__main__":
    generate_benchmark()
