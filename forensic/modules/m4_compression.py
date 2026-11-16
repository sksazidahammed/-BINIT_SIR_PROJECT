# M4 Compression and Colour: extracts JPEG quantisation tables, quality estimate, subsampling; colour characteristics.
# Why: JPEG quantisation tables are a forensic signal; colour histograms describe the image content.
from __future__ import annotations
import struct
from pathlib import Path
import numpy as np
from PIL import Image
from ..core.config import Config
from ..core.record import EvidenceRecord, make_failed_record

MODULE_NAME = "m4_compression"
MODULE_VERSION = "0.1.0"

_LIMITATIONS = [
    "JPEG quality estimate is an approximation based on quantisation tables.",
    "Colour histograms and statistics describe the image, not its provenance.",
    "No authenticity claim is made from compression characteristics alone.",
    "Quality metrics do not prove whether an image has been re-compressed.",
    "PNG analysis does not include quantisation tables (PNG is lossless).",
]

# Standard 8x8 zigzag to raster index mapping for JPEG quantisation tables
_ZIGZAG_TO_RASTER = [
     0,  1,  5,  6, 14, 15, 27, 28,
     2,  4,  7, 13, 16, 26, 29, 42,
     3,  8, 12, 17, 25, 30, 41, 43,
     9, 11, 18, 24, 31, 40, 44, 53,
    10, 19, 23, 32, 39, 45, 52, 54,
    20, 22, 33, 38, 46, 51, 55, 60,
    21, 34, 37, 47, 50, 56, 59, 61,
    35, 36, 48, 49, 57, 58, 62, 63
]

def _zigzag_to_raster(table: list) -> list:
    """Convert JPEG DQT table from zig-zag order to 8x8 row-major raster order."""
    if len(table) != 64:
        return table
    return [table[z] for z in _ZIGZAG_TO_RASTER]

# Standard JPEG luminance quantisation table (quality=100 baseline for comparison)
_JPEG_STD_LUM_QT = [
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99,
]


def _estimate_jpeg_quality(quant_table: list) -> int:
    """
    Estimate JPEG quality (1-100) from the first quantisation table (luminance).
    Uses the standard IJG formula: quality = (200 - sum_of_table / 32) / 2
    This is an approximation. Returns -1 if table is unexpected length.
    """
    if len(quant_table) != 64:
        return -1
    s = sum(quant_table)
    quality = (200 - s // 32) // 2
    return max(1, min(100, quality))


def _extract_jpeg_quant_tables(path: Path) -> list:
    """
    Parse JPEG file bytes directly to extract all quantisation tables (DQT markers).
    Returns a list of tables, each a list of 64 integers.
    Why direct parse: Pillow exposes quantization in img.quantization but we also
    want an independent check; direct byte parsing is the reference method.
    """
    tables = []
    with open(path, "rb") as f:
        data = f.read()
    i = 0
    while i < len(data) - 1:
        if data[i] == 0xFF:
            marker = data[i + 1]
            if marker == 0xDB:  # DQT marker
                length = struct.unpack(">H", data[i + 2:i + 4])[0]
                seg = data[i + 4:i + 2 + length]
                j = 0
                while j < len(seg):
                    qt_info = seg[j]
                    precision = (qt_info >> 4) & 0xF  # 0=8bit, 1=16bit
                    j += 1
                    n = 128 if precision == 1 else 64
                    if j + n > len(seg):
                        break
                    if precision == 0:
                        table = list(seg[j:j + n])
                    else:
                        table = list(struct.unpack(f">{n // 2}H", seg[j:j + n]))
                    tables.append(table)
                    j += n
                i += 2 + length
            elif marker in (0xD8, 0xD9, 0xE0, 0xE1, 0xE2, 0xFE, 0xC0, 0xC4, 0xDA, 0xDD):
                if marker in (0xD8, 0xD9):
                    i += 2
                else:
                    if i + 4 <= len(data):
                        length = struct.unpack(">H", data[i + 2:i + 4])[0]
                        i += 2 + length
                    else:
                        break
            else:
                i += 1
        else:
            i += 1
    return tables


def run(image_path: Path, config: Config) -> EvidenceRecord:
    """
    Run M4: extract JPEG quantisation tables, estimate quality, detect subsampling;
    compute colour histograms and statistics. Returns EvidenceRecord.
    Never modifies the input file.
    """
    image_path = Path(image_path)
    from ..core.hashing import compute_sha256
    try:
        sha256 = compute_sha256(image_path)
    except Exception as exc:
        return make_failed_record(MODULE_NAME, MODULE_VERSION, "unknown", str(exc))

    try:
        with Image.open(image_path) as img:
            fmt = img.format
            mode = img.mode
            width, height = img.size
            # Colour statistics
            img_arr = np.array(img.convert("RGB"))
            brightness = float(np.mean(img_arr))
            contrast = float(np.std(img_arr))
            saturation = float(np.mean(np.std(img_arr, axis=2)))
            # Clipping: fraction of pixels at 0 or 255 in any channel
            clipping_low = float(np.mean((img_arr == 0).any(axis=2)))
            clipping_high = float(np.mean((img_arr == 255).any(axis=2)))
            # Pillow quantization tables (available for JPEG)
            pillow_quant = dict(img.quantization) if hasattr(img, "quantization") and img.quantization else {}

        observations: dict = {
            "format": fmt,
            "mode": mode,
            "width_px": width,
            "height_px": height,
            "brightness_mean": round(brightness, 4),
            "contrast_std": round(contrast, 4),
            "saturation_mean": round(saturation, 4),
            "clipping_fraction_low": round(clipping_low, 6),
            "clipping_fraction_high": round(clipping_high, 6),
        }

        if fmt == "JPEG":
            # Direct byte parse for quantisation tables (independent of Pillow)
            direct_tables = _extract_jpeg_quant_tables(image_path)
            quality_estimate = _estimate_jpeg_quality(direct_tables[0]) if direct_tables else -1
            pillow_table_0 = pillow_quant.get(0, [])
            raster_table_0 = _zigzag_to_raster(direct_tables[0]) if direct_tables else []
            tables_match = (
                raster_table_0 == list(pillow_table_0) if pillow_table_0 and direct_tables else None
            )
            observations.update({
                "jpeg_quant_tables_direct": direct_tables,
                "jpeg_quant_tables_raster": [_zigzag_to_raster(t) for t in direct_tables],
                "jpeg_quant_table_count_direct": len(direct_tables),
                "jpeg_quality_estimate": quality_estimate,
                "jpeg_pillow_quant_table_0": list(pillow_table_0),
                "jpeg_pillow_table_match_direct": tables_match,
            })
            interpretation = {
                "compression_characteristics": "recorded",
                "quality_estimate": quality_estimate,
                "note": "JPEG quality is an estimate. No authenticity claim is made.",
            }
        elif fmt == "PNG":
            observations.update({
                "png_format": True,
                "jpeg_quant_tables_direct": None,
                "jpeg_quality_estimate": None,
                "note": "PNG is lossless. No JPEG quantisation tables.",
            })
            interpretation = {
                "compression_characteristics": "recorded",
                "note": "PNG lossless format. No JPEG quantisation tables.",
            }
        else:
            interpretation = {
                "compression_characteristics": "partial",
                "note": f"Format {fmt}: JPEG-specific analysis not applicable.",
            }

        return EvidenceRecord(
            input_sha256=sha256,
            engine=MODULE_NAME,
            version=MODULE_VERSION,
            method="pillow-open + direct-jpeg-dqt-parse + numpy-colour-stats",
            parameters={"pillow_version": Image.__version__ if hasattr(Image, '__version__') else "unknown"},
            status="completed",
            observations=observations,
            interpretation=interpretation,
            regions=None,
            confidence=None,
            limitations=_LIMITATIONS,
        )
    except Exception as exc:
        return make_failed_record(MODULE_NAME, MODULE_VERSION, sha256, str(exc))
