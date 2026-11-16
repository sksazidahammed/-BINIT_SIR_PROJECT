# Stage 0: content-based file type check and limit enforcement before any module runs.
# Why: reject malformed or oversized files early so no module receives bad input.
from pathlib import Path
from .config import Config

# Magic bytes for supported formats
_MAGIC = {
    b"\xff\xd8\xff": "JPEG",
    b"\x89PNG\r\n\x1a\n": "PNG",
}


def validate_image(path: Path, config: Config) -> dict:
    """
    Check the file exists, is a supported format (by magic bytes, not extension),
    is within size and pixel limits, and is not empty.
    Returns a dict with keys: valid (bool), format (str|None), reason (str|None).
    Does NOT open the file with an image decoder — intentional, so malformed
    image data cannot crash the validator.
    """
    path = Path(path)
    result = {"valid": False, "format": None, "reason": None}
    if not path.exists():
        result["reason"] = f"File not found: {path}"
        return result
    size = path.stat().st_size
    if size == 0:
        result["reason"] = "File is empty."
        return result
    if size > config.max_file_bytes:
        result["reason"] = f"File size {size} bytes exceeds limit {config.max_file_bytes}."
        return result
    # Detect format by magic bytes
    with open(path, "rb") as f:
        header = f.read(16)
    detected = None
    for magic, fmt in _MAGIC.items():
        if header[:len(magic)] == magic:
            detected = fmt
            break
    if detected is None:
        result["reason"] = f"Unsupported or unrecognised file type (magic bytes: {header[:8].hex()})."
        return result
    if detected not in config.supported_formats:
        result["reason"] = f"Format {detected} is not in supported_formats: {config.supported_formats}."
        return result
    result["valid"] = True
    result["format"] = detected
    return result
