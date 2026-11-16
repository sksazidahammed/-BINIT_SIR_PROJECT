# Evidence record schema: defines the standard structure every module must return.
# Why: a common schema lets M8 (report) and M7 (correlation) handle all modules uniformly.
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

VALID_STATUSES = frozenset({"completed", "failed", "not_run", "not_assessed"})


@dataclass
class EvidenceRecord:
    """
    Standard evidence record returned by every forensic module.
    Fields match brief Section 6 exactly.
    """
    input_sha256: str               # SHA-256 hex digest of the input file bytes
    engine: str                     # module name, e.g. "m1_identity"
    version: str                    # module version string
    method: str                     # algorithm/method used, e.g. "hashlib-sha256"
    parameters: Dict[str, Any]      # all parameters including random seeds
    status: str                     # one of VALID_STATUSES
    observations: Dict[str, Any]    # what was measured (no interpretation mixed in)
    interpretation: Dict[str, Any]  # what the observations may mean
    regions: Optional[List[Dict]]   # M5 only: region maps; None for other modules
    confidence: Optional[Dict]      # calibrated confidence if applicable; None otherwise
    limitations: List[str]          # list of limitation strings for this module's output

    def __post_init__(self):
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{self.status}'. Must be one of {VALID_STATUSES}")

    def to_dict(self) -> Dict[str, Any]:
        """Return the record as a plain dict for JSON serialisation."""
        return asdict(self)


def make_failed_record(engine: str, version: str, sha256: str, reason: str) -> EvidenceRecord:
    """Helper: build a failed record when a module cannot run."""
    return EvidenceRecord(
        input_sha256=sha256,
        engine=engine,
        version=version,
        method="n/a",
        parameters={},
        status="failed",
        observations={"error": reason},
        interpretation={},
        regions=None,
        confidence=None,
        limitations=[reason],
    )


def make_not_assessed_record(engine: str, version: str, sha256: str, reason: str) -> EvidenceRecord:
    """Helper: build a not_assessed record when a module is skipped for a known reason."""
    return EvidenceRecord(
        input_sha256=sha256,
        engine=engine,
        version=version,
        method="n/a",
        parameters={},
        status="not_assessed",
        observations={"reason": reason},
        interpretation={},
        regions=None,
        confidence=None,
        limitations=[reason],
    )
