# M3 C2PA: finds and validates a C2PA manifest using c2pa-python; lists declared assertions.
# Why c2pa-python: pure Python wheel, no Rust binary needed; see docs/06_TECHNICAL_DECISIONS.md
# API verified against c2pa-python 0.39.0: Reader.try_create(format_or_path=<path>)
# returns None when no manifest is present; get_validation_state() returns "Valid"/"Invalid".
from __future__ import annotations
from pathlib import Path
from ..core.config import Config
from ..core.record import EvidenceRecord, make_not_assessed_record, make_failed_record

MODULE_NAME = "m3_c2pa"
MODULE_VERSION = "0.1.0"

_LIMITATIONS = [
    "A valid C2PA manifest does not prove the depicted event occurred.",
    "A valid manifest does not prove the image was not edited before signing.",
    "A missing manifest is 'absent' — it is not evidence of manipulation.",
    "Validation uses the trust list at the time of running; revoked certificates may "
    "not be detected if CRL is unavailable.",
    "Test certificates (c2pa-python test assets, Apache-2.0) are NOT real-world trust "
    "anchors. Results for test assets do not reflect real-world provenance.",
    "c2pa-python version 0.39.0: see requirements.txt.",
]


def run(image_path: Path, config: Config) -> EvidenceRecord:
    """
    Run M3: attempt to read a C2PA manifest from the image using c2pa-python 0.39.0.

    API (verified 2026-11-15):
        Reader.try_create(format_or_path=<str>) -> Reader | None
        None  → no manifest present
        Reader.get_validation_state() → str "Valid" | "Invalid"

    Returns:
      - status=completed, c2pa_state="absent"             if no manifest found
      - status=completed, c2pa_state="present_validated"  if manifest passes validation
      - status=completed, c2pa_state="present_invalid"    if manifest fails validation
      - status=not_assessed if c2pa-python not installed
      - status=failed on other library error

    Never modifies the input file.
    """
    image_path = Path(image_path)
    from ..core.hashing import compute_sha256
    try:
        sha256 = compute_sha256(image_path)
    except Exception as exc:
        return make_failed_record(MODULE_NAME, MODULE_VERSION, "unknown", str(exc))

    try:
        import c2pa
    except ImportError:
        return make_not_assessed_record(
            MODULE_NAME, MODULE_VERSION, sha256,
            "c2pa-python is not installed. Run: pip install c2pa-python==0.39.0"
        )

    try:
        import json as _json

        # try_create returns None when file has no C2PA manifest (not an error)
        reader = c2pa.Reader.try_create(format_or_path=str(image_path))

        if reader is None:
            observations = {"c2pa_state": "absent", "manifest_count": 0}
            interpretation = {
                "c2pa_state": "absent",
                "note": (
                    "No C2PA manifest present. Absence is uninformative — "
                    "it does not indicate manipulation."
                ),
            }
        else:
            store_dict = _json.loads(reader.json()) if reader.json() else {}
            active_manifest = store_dict.get("active_manifest")
            manifests = store_dict.get("manifests", {})
            manifest_count = len(manifests)

            validation_state_raw = reader.get_validation_state()
            is_validated = str(validation_state_raw).lower() == "valid"
            c2pa_state = "present_validated" if is_validated else "present_invalid"

            assertions = []
            ai_declared = False
            if active_manifest and active_manifest in manifests:
                for a in manifests[active_manifest].get("assertions", []):
                    lbl = a.get("label", "unknown")
                    assertions.append(lbl)
                    if "ai" in lbl.lower() or "generative" in lbl.lower():
                        ai_declared = True

            observations = {
                "c2pa_state": c2pa_state,
                "manifest_count": manifest_count,
                "active_manifest": active_manifest,
                "assertions": assertions,
                "ai_generative_declared": ai_declared,
                "validation_state": str(validation_state_raw),
                "trust_list": "c2pa-python 0.39.0 built-in",
                "trust_anchor_note": (
                    "Test certificates are NOT real-world trust anchors. "
                    "Do not treat test-asset results as real-world provenance."
                ),
            }
            interpretation = {
                "c2pa_state": c2pa_state,
                "note": (
                    "Manifest validated by c2pa-python internal verification."
                    if is_validated
                    else "Manifest present but failed cryptographic validation."
                ),
                "ai_declaration": "declared" if ai_declared else "not_declared",
            }

        return EvidenceRecord(
            input_sha256=sha256,
            engine=MODULE_NAME,
            version=MODULE_VERSION,
            method="c2pa-python-reader-try_create",
            parameters={"library": "c2pa-python", "library_version": "0.39.0"},
            status="completed",
            observations=observations,
            interpretation=interpretation,
            regions=None,
            confidence=None,
            limitations=_LIMITATIONS,
        )

    except Exception as exc:
        return make_failed_record(
            MODULE_NAME, MODULE_VERSION, sha256, f"c2pa-python error: {exc}"
        )
