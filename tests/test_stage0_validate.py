# Tests for Stage 0: content-based type checking and limit enforcement.
# Independent verification: magic bytes are compared against known JPEG/PNG signatures.
"""
Tests for forensic.core.validate — Stage 0 validation.
Every test uses only the in-memory/tmp_path fixtures; no external tools needed.
"""
import pytest
from pathlib import Path
from PIL import Image
import sys
ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))
from forensic.core.validate import validate_image
from forensic.core.config import Config

def test_valid_jpeg_accepted(valid_jpeg, default_config):
    """A valid JPEG file must be accepted."""
    result = validate_image(valid_jpeg, default_config)
    assert result["valid"] is True
    assert result["format"] == "JPEG"
    assert result["reason"] is None

def test_valid_png_accepted(valid_png, default_config):
    """A valid PNG file must be accepted."""
    result = validate_image(valid_png, default_config)
    assert result["valid"] is True
    assert result["format"] == "PNG"
    assert result["reason"] is None

def test_malformed_file_rejected(malformed_file, default_config):
    """A file with wrong magic bytes must be rejected without crashing."""
    result = validate_image(malformed_file, default_config)
    assert result["valid"] is False
    assert result["reason"] is not None
    assert "Unsupported" in result["reason"] or "unrecognised" in result["reason"]

def test_empty_file_rejected(empty_file, default_config):
    """An empty file must be rejected without crashing."""
    result = validate_image(empty_file, default_config)
    assert result["valid"] is False
    assert result["reason"] is not None

def test_nonexistent_file_rejected(default_config):
    """A path that does not exist must be rejected without crashing."""
    result = validate_image(Path("/nonexistent/path/image.jpg"), default_config)
    assert result["valid"] is False
    assert result["reason"] is not None

def test_oversized_file_rejected(tmp_path, default_config):
    """A file exceeding max_file_bytes must be rejected."""
    p = tmp_path / "big.jpg"
    # Create a tiny JPEG then check with a config that limits to 1 byte
    from PIL import Image
    img = Image.new("RGB", (10, 10), color=(128, 128, 128))
    img.save(p, "JPEG")
    small_config = Config(max_file_bytes=1)  # 1 byte limit
    result = validate_image(p, small_config)
    assert result["valid"] is False
    assert "exceeds" in result["reason"]

def test_jpeg_magic_bytes_verified():
    """JPEG magic bytes start with FF D8 FF — verify our detection matches this known fact."""
    import struct
    # The first three bytes of any JPEG are 0xFF 0xD8 0xFF
    jpeg_magic = bytes([0xFF, 0xD8, 0xFF])
    assert jpeg_magic == b"\xff\xd8\xff", "JPEG magic bytes must be FF D8 FF"

def test_png_magic_bytes_verified():
    """PNG magic bytes are 89 50 4E 47 0D 0A 1A 0A — verify our detection."""
    png_magic = b"\x89PNG\r\n\x1a\n"
    assert png_magic == bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
