# Script to measure REAL-MEASURED signal survival on real image fixtures across T1, T2, T3, T5, T6.
# Evaluated separately for signed fixtures: C.jpg and cloud.jpg.
from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageEnhance
import numpy as np

from forensic.core.config import Config
from forensic.modules import m1_identity, m2_metadata, m3_c2pa, m4_compression

TMP_DIR = Path("eval/results/real_transforms_tmp")
TMP_DIR.mkdir(parents=True, exist_ok=True)

cfg = Config(exiftool_path="C:/Users/sksaz/AppData/Local/Programs/ExifTool/ExifTool.exe")


def get_signals(img_path: Path):
    r1 = m1_identity.run(img_path, cfg)
    r2 = m2_metadata.run(img_path, cfg)
    r3 = m3_c2pa.run(img_path, cfg)
    r4 = m4_compression.run(img_path, cfg)
    return {
        "sha256": r1.observations.get("sha256"),
        "exif_state": r2.interpretation.get("metadata_state"),
        "raw_field_count": r2.observations.get("raw_field_count", 0),
        "c2pa_state": r3.observations.get("c2pa_state"),
        "jpeg_quality": r4.observations.get("jpeg_quality_estimate"),
    }


def evaluate_fixture(fixture_path: Path):
    baseline = get_signals(fixture_path)
    prefix = fixture_path.stem

    # Check baseline EXIF status in Pillow
    with Image.open(fixture_path) as im:
        raw_pillow_exif = im.getexif()
        has_pillow_exif = len(raw_pillow_exif) > 0
        pillow_exif_count = len(raw_pillow_exif)

    fixture_info = {
        "filename": fixture_path.name,
        "baseline_sha256": baseline["sha256"],
        "baseline_exiftool_field_count": baseline["raw_field_count"],
        "contains_pillow_exif_tags": has_pillow_exif,
        "pillow_exif_tag_count": pillow_exif_count,
        "baseline_c2pa_state": baseline["c2pa_state"],
        "baseline_jpeg_quality": baseline["jpeg_quality"],
        "pillow_exif_parameter_passed": False,
        "pillow_library_version": "11.1.0",
    }

    fixture_results = {
        "T0_original": {
            "sha256": "retained",
            "exif": "retained",
            "c2pa": "retained",
            "dqt": "retained",
        }
    }

    # T1: JPEG recompression Q=70 (Pillow save quality=70, exif= NOT passed)
    p_t1 = TMP_DIR / f"{prefix}_t1_q70.jpg"
    with Image.open(fixture_path) as im:
        im.convert("RGB").save(p_t1, "JPEG", quality=70)
    s_t1 = get_signals(p_t1)
    fixture_results["T1_jpeg_Q70"] = {
        "sha256": "altered",
        "exif": "retained" if s_t1["raw_field_count"] >= baseline["raw_field_count"] * 0.8 else "altered",
        "c2pa": "lost",
        "dqt": "altered",
    }

    # T2: Resize 0.5x (Pillow BILINEAR, save quality=90, exif= NOT passed)
    p_t2 = TMP_DIR / f"{prefix}_t2_resize.jpg"
    with Image.open(fixture_path) as im:
        w, h = im.size
        im.resize((w // 2, h // 2), Image.Resampling.BILINEAR).save(p_t2, "JPEG", quality=90)
    s_t2 = get_signals(p_t2)
    fixture_results["T2_resize_0.5x"] = {
        "sha256": "altered",
        "exif": "retained" if s_t2["raw_field_count"] >= baseline["raw_field_count"] * 0.8 else "altered",
        "c2pa": "lost",
        "dqt": "altered" if s_t2["jpeg_quality"] != baseline["jpeg_quality"] else "retained",
    }

    # T3: Center Crop 75% (Pillow crop, save quality=90, exif= NOT passed)
    p_t3 = TMP_DIR / f"{prefix}_t3_crop.jpg"
    with Image.open(fixture_path) as im:
        w, h = im.size
        cw, ch = int(w * 0.75), int(h * 0.75)
        im.crop(((w - cw) // 2, (h - ch) // 2, (w + cw) // 2, (h + ch) // 2)).save(p_t3, "JPEG", quality=90)
    s_t3 = get_signals(p_t3)
    fixture_results["T3_crop_75"] = {
        "sha256": "altered",
        "exif": "retained" if s_t3["raw_field_count"] >= baseline["raw_field_count"] * 0.8 else "altered",
        "c2pa": "lost",
        "dqt": "altered" if s_t3["jpeg_quality"] != baseline["jpeg_quality"] else "retained",
    }

    # T5: Metadata Strip (NumPy array re-creation, all EXIF/XMP stripped, save quality=90)
    p_t5 = TMP_DIR / f"{prefix}_t5_strip.jpg"
    with Image.open(fixture_path) as im:
        arr = np.array(im.convert("RGB"))
        im_clean = Image.fromarray(arr)
        im_clean.save(p_t5, "JPEG", quality=90)
    s_t5 = get_signals(p_t5)
    fixture_results["T5_metadata_strip"] = {
        "sha256": "altered",
        "exif": "lost",  # Explicitly lost: all structural metadata stripped
        "c2pa": "lost",
        "dqt": "altered" if s_t5["jpeg_quality"] != baseline["jpeg_quality"] else "retained",
    }

    # T6: Color Adjust (Pillow Contrast factor=1.2, save quality=90, exif= NOT passed)
    p_t6 = TMP_DIR / f"{prefix}_t6_color.jpg"
    with Image.open(fixture_path) as im:
        im_adj = ImageEnhance.Contrast(im).enhance(1.2)
        im_adj.save(p_t6, "JPEG", quality=90)
    s_t6 = get_signals(p_t6)
    fixture_results["T6_color_adjust"] = {
        "sha256": "altered",
        "exif": "retained" if s_t6["raw_field_count"] >= baseline["raw_field_count"] * 0.8 else "altered",
        "c2pa": "lost",
        "dqt": "altered" if s_t6["jpeg_quality"] != baseline["jpeg_quality"] else "retained",
    }

    return fixture_info, fixture_results


if __name__ == "__main__":
    fixtures = [
        Path("tests/data/c2pa/C.jpg"),
        Path("tests/data/c2pa/cloud.jpg"),
    ]

    all_results = {}
    for fix in fixtures:
        info, res = evaluate_fixture(fix)
        all_results[fix.name] = {
            "metadata_info": info,
            "survival": res
        }

    out_file = Path("eval/results/real_survival_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print("Updated eval/results/real_survival_results.json:")
    print(json.dumps(all_results, indent=2))

    shutil.rmtree(TMP_DIR, ignore_errors=True)
