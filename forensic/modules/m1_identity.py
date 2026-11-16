# M1 File Identity: computes SHA-256, detects file format by content, measures size and dimensions.
# This is the foundational module — its SHA-256 is used as the record key for all other modules.
from __future__ import annotations
import datetime
from pathlib import Path
from typing import Optional
from PIL import Image
from ..core.config import Config
from ..core.hashing import compute_sha256
from ..core.record import EvidenceRecord, make_failed_record

MODULE_NAME = "m1_identity"
MODULE_VERSION = "0.1.0"

_LIMITATIONS = [
    "SHA-256 identifies the file bytes, not the depicted content.",
    "A hash does not prove authenticity or capture date.",
    "Format detection is by magic bytes; a deliberately crafted file could fool it.",
]


def run(image_path: Path, config: Config) -> EvidenceRecord:
    """
    Run M1: compute SHA-256 of the original bytes; detect format by magic bytes;
    measure file size and image dimensions using Pillow.
    Returns an EvidenceRecord. Never modifies the input file.
    """
    image_path = Path(image_path)
    sha256 = "unknown"
    try:
        sha256 = compute_sha256(image_path)
        stat = image_path.stat()
        file_size_bytes = stat.st_size
        # Open with Pillow to get dimensions — do NOT save or modify
        with Image.open(image_path) as img:
            width, height = img.size
            pil_format = img.format  # Pillow's format string, e.g. "JPEG"
            mode = img.mode
            n_frames = getattr(img, "n_frames", 1)
        return EvidenceRecord(
            input_sha256=sha256,
            engine=MODULE_NAME,
            version=MODULE_VERSION,
            method="hashlib-sha256 + pillow-format-detection",
            parameters={"chunk_size_bytes": 65536},
            status="completed",
            observations={
                "sha256": sha256,
                "file_size_bytes": file_size_bytes,
                "width_px": width,
                "height_px": height,
                "total_pixels": width * height,
                "pillow_format": pil_format,
                "pillow_mode": mode,
                "n_frames": n_frames,
            },
            interpretation={
                "file_identity": "verified",
                "note": "Hash computed from original bytes. Format detected by Pillow.",
            },
            regions=None,
            confidence=None,
            limitations=_LIMITATIONS,
        )
    except Exception as exc:
        return make_failed_record(MODULE_NAME, MODULE_VERSION, sha256, str(exc))
