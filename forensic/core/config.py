# Configuration loader: reads per-run limits (file size, pixel count, timeout) from config.yaml.
# Why: limits are in a config file, not hard-coded, so they can change without code edits.
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class Config:
    max_file_bytes: int = 52_428_800   # 50 MB
    max_pixels: int = 100_000_000      # 100 megapixels
    timeout_seconds: int = 30
    supported_formats: List[str] = field(default_factory=lambda: ["JPEG", "PNG"])
    exiftool_path: Optional[str] = None  # None = use system PATH


def load_config(path: Optional[Path] = None) -> Config:
    """Load configuration from a YAML file, or return defaults if no file given."""
    if path is None or not Path(path).exists():
        return Config()
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    return Config(**{k: v for k, v in data.items() if hasattr(Config, k)})
