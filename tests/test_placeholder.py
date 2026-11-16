# Placeholder test — verifies the Python environment and package imports are working.
# Purpose: a fast smoke-test that the installed packages are importable before running real tests.
import sys

def test_python_version():
    """Python 3.12+ required."""
    assert sys.version_info >= (3, 12), f"Python 3.12+ required, got {sys.version}"

def test_pillow_import():
    """Pillow must be importable."""
    from PIL import Image
    assert Image is not None

def test_numpy_import():
    """NumPy must be importable."""
    import numpy as np
    assert np is not None

def test_cv2_import():
    """OpenCV (cv2) must be importable."""
    import cv2
    assert cv2 is not None

def test_scikit_image_import():
    """scikit-image must be importable."""
    import skimage
    assert skimage is not None

def test_typer_import():
    """typer must be importable."""
    import typer
    assert typer is not None

def test_c2pa_import():
    """c2pa-python must be importable."""
    import c2pa
    assert c2pa is not None

def test_forensic_package():
    """The forensic package must be importable and expose __version__."""
    import forensic
    assert hasattr(forensic, "__version__")
    assert forensic.__version__.startswith("0.1.0")

def test_evidence_record_schema():
    """EvidenceRecord must enforce valid statuses."""
    from forensic.core.record import EvidenceRecord, VALID_STATUSES
    import pytest
    with pytest.raises(ValueError):
        EvidenceRecord(
            input_sha256="abc",
            engine="test",
            version="0.0.1",
            method="test",
            parameters={},
            status="invalid_status",
            observations={},
            interpretation={},
            regions=None,
            confidence=None,
            limitations=[],
        )

def test_config_defaults():
    """Config defaults must match documented values."""
    from forensic.core.config import Config
    c = Config()
    assert c.max_file_bytes == 52_428_800
    assert c.max_pixels == 100_000_000
    assert c.timeout_seconds == 30
    assert "JPEG" in c.supported_formats
    assert "PNG" in c.supported_formats
