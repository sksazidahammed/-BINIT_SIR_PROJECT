# SHA-256 hashing: computes and returns the hex digest of a file's raw bytes.
# Why: we hash the raw bytes, NOT the decoded image, so the hash is stable regardless
#      of how image libraries interpret the file.
import hashlib
from pathlib import Path

CHUNK_SIZE = 65_536  # 64 KB — read in chunks to handle large files without RAM spike


def compute_sha256(path: Path) -> str:
    """
    Read the file in binary chunks and return the lowercase hex SHA-256 digest.
    Never decodes the image — hash is of the original file bytes.
    Raises FileNotFoundError if the file does not exist.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()
