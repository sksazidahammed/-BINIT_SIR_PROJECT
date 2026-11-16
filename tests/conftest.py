# Pytest configuration and shared fixtures for the forensic test suite.
import pytest
from pathlib import Path
import sys
# Ensure the project root is on sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

TEST_DATA = Path(__file__).parent / "data"

@pytest.fixture
def valid_jpeg(tmp_path):
    """Create a fresh small JPEG for each test (avoids shared-state issues)."""
    from PIL import Image
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    p = tmp_path / "test.jpg"
    img.save(p, "JPEG", quality=85)
    return p

@pytest.fixture
def valid_png(tmp_path):
    """Create a fresh small PNG for each test."""
    from PIL import Image
    img = Image.new("RGB", (100, 100), color=(0, 255, 0))
    p = tmp_path / "test.png"
    img.save(p, "PNG")
    return p

@pytest.fixture
def malformed_file(tmp_path):
    """A file with invalid magic bytes — not a valid image."""
    p = tmp_path / "malformed.bin"
    p.write_bytes(b"\x00\x01\x02\x03\x04This is not an image file at all")
    return p

@pytest.fixture
def empty_file(tmp_path):
    """A zero-byte file."""
    p = tmp_path / "empty.jpg"
    p.write_bytes(b"")
    return p

@pytest.fixture
def default_config():
    """Default Config object for testing."""
    import sys
    sys.path.insert(0, str(ROOT))
    from forensic.core.config import Config
    return Config()
