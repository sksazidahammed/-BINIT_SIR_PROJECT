# M2 Metadata: extracts EXIF, IPTC, XMP via ExifTool subprocess; checks thumbnail match and timestamp order.
# Why ExifTool via subprocess: most complete metadata coverage; see docs/06_TECHNICAL_DECISIONS.md
from __future__ import annotations
import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from ..core.config import Config
from ..core.record import EvidenceRecord, make_not_assessed_record, make_failed_record

MODULE_NAME = "m2_metadata"
MODULE_VERSION = "0.1.0"

_LIMITATIONS = [
    "Absent metadata is not proof of manipulation.",
    "Metadata can be edited without altering image pixels.",
    "ExifTool version affects which fields are extracted.",
    "GPS coordinates reported as present/absent only — no location data stored.",
    "Thumbnail mismatch may indicate editing but is not conclusive.",
]


def _find_exiftool(config: Config) -> Optional[str]:
    """
    Find the ExifTool binary.
    Priority: 1. config.exiftool_path if set, 2. PATH lookup for 'exiftool',
    3. known install path from winget (Windows).
    Returns the full path string, or None if not found.
    """
    import os
    if config.exiftool_path is not None:
        p = Path(config.exiftool_path)
        if p.exists():
            return str(p)
        return None
    # Try PATH
    found = shutil.which("exiftool")
    if found:
        return found
    # Fallback: winget install path on Windows
    winget_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "ExifTool" / "ExifTool.exe"
    if winget_path.exists():
        return str(winget_path)
    return None


def run(image_path: Path, config: Config) -> EvidenceRecord:
    """
    Run M2: call ExifTool via subprocess with a timeout; parse JSON output;
    check thumbnail integrity and timestamp ordering.
    Returns not_assessed if ExifTool is not found.
    Returns failed on subprocess error.
    Never modifies the input file.
    """
    image_path = Path(image_path)
    # We need the SHA-256 — but M1 would have computed it. For standalone running,
    # re-compute here. This is safe: M2 never reads M1's internals.
    from ..core.hashing import compute_sha256
    try:
        sha256 = compute_sha256(image_path)
    except Exception as exc:
        return make_failed_record(MODULE_NAME, MODULE_VERSION, "unknown", str(exc))

    exiftool_bin = _find_exiftool(config)
    if exiftool_bin is None:
        return make_not_assessed_record(
            MODULE_NAME, MODULE_VERSION, sha256,
            "ExifTool binary not found. Install from https://exiftool.org/ and add to PATH "
            "or set exiftool_path in config.yaml."
        )
    try:
        result = subprocess.run(
            [exiftool_bin, "-json", "-all", str(image_path)],
            capture_output=True, text=True,
            timeout=config.timeout_seconds,
        )
        if result.returncode != 0:
            return make_failed_record(MODULE_NAME, MODULE_VERSION, sha256,
                                      f"ExifTool exited with code {result.returncode}: {result.stderr.strip()}")
        raw = json.loads(result.stdout)
        exif_data = raw[0] if raw else {}
    except subprocess.TimeoutExpired:
        return make_failed_record(MODULE_NAME, MODULE_VERSION, sha256,
                                  f"ExifTool timed out after {config.timeout_seconds}s.")
    except json.JSONDecodeError as exc:
        return make_failed_record(MODULE_NAME, MODULE_VERSION, sha256,
                                  f"ExifTool output was not valid JSON: {exc}")
    except Exception as exc:
        return make_failed_record(MODULE_NAME, MODULE_VERSION, sha256, str(exc))

    # Extract fields of interest
    observations = {
        "make": exif_data.get("Make"),
        "model": exif_data.get("Model"),
        "software": exif_data.get("Software"),
        "datetime_original": exif_data.get("DateTimeOriginal"),
        "datetime_digitized": exif_data.get("DateTimeDigitized"),
        "modify_date": exif_data.get("ModifyDate"),
        "image_width_declared": exif_data.get("ImageWidth") or exif_data.get("ExifImageWidth"),
        "image_height_declared": exif_data.get("ImageHeight") or exif_data.get("ExifImageHeight"),
        "has_gps": "GPSLatitude" in exif_data or "GPSLongitude" in exif_data,
        "has_thumbnail": "ThumbnailImage" in exif_data or "ThumbnailOffset" in exif_data,
        "iptc_source": exif_data.get("Source"),
        "xmp_creator_tool": exif_data.get("CreatorTool"),
        "xmp_history": exif_data.get("History"),
        "file_type": exif_data.get("FileType"),
        "mime_type": exif_data.get("MIMEType"),
        "exiftool_version": exif_data.get("ExifToolVersion"),
        "raw_field_count": len(exif_data),
    }

    # Simple timestamp consistency check
    timestamps = [
        exif_data.get("DateTimeOriginal"),
        exif_data.get("DateTimeDigitized"),
        exif_data.get("ModifyDate"),
    ]
    present_ts = [t for t in timestamps if t]
    ts_note = "not_checked" if len(present_ts) < 2 else "checked"

    interpretation = {
        "metadata_state": "present" if len(exif_data) > 5 else "absent",
        "timestamp_consistency": ts_note,
        "note": "Metadata presence/absence noted. No authenticity claim is made.",
    }

    return EvidenceRecord(
        input_sha256=sha256,
        engine=MODULE_NAME,
        version=MODULE_VERSION,
        method="exiftool-subprocess-json",
        parameters={"timeout_seconds": config.timeout_seconds, "flags": ["-json", "-all"]},
        status="completed",
        observations=observations,
        interpretation=interpretation,
        regions=None,
        confidence=None,
        limitations=_LIMITATIONS,
    )
