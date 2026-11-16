# Tests for Module M5 Classical Indicators: Double JPEG, Resampling, Copy-Move, and ELA.
# Verifies compliance with EvidenceRecord schema, state constraints, and limitations.
"""
Tests for forensic.modules.m5_classical.
Tests verify:
- Output record schema completeness.
- State values strictly within {"indicated", "not_indicated", "not_assessed"}.
- ELA is labelled as visualisation only.
- Region maps and heatmaps are produced.
- Limitations are present.
- Repeat runs are deterministic.
- Malformed inputs do not crash.
"""
import pytest
from pathlib import Path
import sys

ROOT_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_PATH))

from forensic.modules import m5_classical
from forensic.core.config import Config, load_config

BENCHMARK_DIR = ROOT_PATH / "tests" / "data" / "classical_benchmark"


def _cfg() -> Config:
    return load_config(ROOT_PATH / "config.yaml")


def test_m5_completes_on_valid_jpeg(valid_jpeg):
    """M5 must return status='completed' on a valid JPEG image."""
    result = m5_classical.run(valid_jpeg, _cfg())
    assert result.status == "completed", f"Status was {result.status}: {result.observations}"
    assert result.engine == "m5_classical"


def test_m5_schema_completeness(valid_jpeg):
    """M5 record must contain all required EvidenceRecord fields."""
    result = m5_classical.run(valid_jpeg, _cfg())
    d = result.to_dict()
    required = [
        "input_sha256", "engine", "version", "method", "parameters",
        "status", "observations", "interpretation", "regions", "confidence", "limitations"
    ]
    for req in required:
        assert req in d, f"Missing field: {req}"


def test_m5_observations_has_all_indicators(valid_jpeg):
    """M5 observations must report double_jpeg, resampling, copy_move, and ela."""
    result = m5_classical.run(valid_jpeg, _cfg())
    obs = result.observations
    assert "double_jpeg" in obs
    assert "resampling" in obs
    assert "copy_move" in obs
    assert "ela" in obs


def test_m5_states_strictly_typed(valid_jpeg):
    """Output states must strictly be one of: indicated, not_indicated, not_assessed."""
    allowed = {"indicated", "not_indicated", "not_assessed"}
    result = m5_classical.run(valid_jpeg, _cfg())
    interp = result.interpretation

    for ind in ["double_jpeg", "resampling", "copy_move", "classical_indicators_summary"]:
        state = interp.get(ind)
        assert state in allowed, f"Invalid state '{state}' for {ind}"


def test_m5_ela_is_visualisation_only(valid_jpeg):
    """ELA observation and region map must explicitly state visualisation only."""
    result = m5_classical.run(valid_jpeg, _cfg())
    obs = result.observations
    assert "visualisation only" in obs["ela"]["note"].lower() or "visualization only" in obs["ela"]["note"].lower()


def test_m5_regions_present(valid_jpeg):
    """M5 must return region maps / heatmaps in the regions field."""
    result = m5_classical.run(valid_jpeg, _cfg())
    assert result.regions is not None
    assert len(result.regions) >= 3  # double_jpeg, resampling, copy_move, ela
    indicators = [r.get("indicator") for r in result.regions]
    assert "double_jpeg" in indicators
    assert "resampling" in indicators
    assert "copy_move" in indicators


def test_m5_no_real_fake_label(valid_jpeg):
    """M5 must never produce a binary real/fake label."""
    result = m5_classical.run(valid_jpeg, _cfg())
    rec_str = str(result.to_dict()).lower()
    for forbidden in ["'real'", "'fake'", "'authentic'", "'manipulated'"]:
        assert forbidden not in rec_str, f"Forbidden label {forbidden} in output"


def test_m5_limitations_present(valid_jpeg):
    """M5 must provide module-specific limitations."""
    result = m5_classical.run(valid_jpeg, _cfg())
    assert len(result.limitations) >= 3
    assert any("double jpeg" in lim.lower() for lim in result.limitations)
    assert any("resampling" in lim.lower() for lim in result.limitations)


def test_m5_reproducibility(valid_jpeg):
    """Repeat runs on identical input must yield identical observations."""
    cfg = _cfg()
    r1 = m5_classical.run(valid_jpeg, cfg)
    r2 = m5_classical.run(valid_jpeg, cfg)
    assert r1.status == r2.status
    assert r1.observations == r2.observations


def test_m5_malformed_file_handling(malformed_file):
    """M5 must handle malformed input gracefully without crashing."""
    result = m5_classical.run(malformed_file, _cfg())
    assert result.status in ("failed", "completed", "not_assessed")


def test_m5_detects_copy_move_on_known_benchmark_sample():
    """M5 must detect copy-move on the benchmark copy-move image."""
    cm_file = BENCHMARK_DIR / "copymove_coffee.png"
    if not cm_file.exists():
        pytest.skip("Benchmark copy-move sample not found")
    result = m5_classical.run(cm_file, _cfg())
    assert result.status == "completed"
    assert result.observations["copy_move"]["spatial_clusters_count"] >= 1
    assert result.interpretation["copy_move"] == "indicated"
