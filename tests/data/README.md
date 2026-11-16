# tests/data/ — Test Data Documentation

## Programmatically Generated Files (tests/data/create_test_images.py)
These known-answer files are generated programmatically using Python and Pillow to avoid downloading untrusted binary images:
- `test_valid_jpeg.jpg`: 100×100 RGB JPEG (red, quality 85). Used for baseline JPEG pipeline validation.
- `test_valid_png.png`: 100×100 RGB PNG (green). Used for lossless format validation.
- `test_malformed.bin`: 50 bytes of arbitrary non-image header bytes. Used for Stage 0 rejection testing.
- `test_empty.jpg`: 0-byte file. Used for empty file rejection testing.
- `test_oversized.jpg`: Reference JPEG used with mock 1-byte config to verify size limit enforcement.

## C2PA Test Assets (tests/data/c2pa/)
Source: Official test fixtures from `c2pa-python` repository (`https://github.com/contentauth/c2pa-python/tree/main/tests/fixtures`).
Licence: Apache-2.0 / MIT (verified in repository).
Access Date: 2026-11-15.

| Filename | Type | Manifest Status | Notes |
|---|---|---|---|
| `C.jpg` | Valid signed C2PA asset | `present_validated` | Official signed fixture from c2pa-python test suite. Contains assertions: `stds.schema-org.CreativeWork`, `c2pa.actions.v2`. |
| `cloud.jpg` | Valid signed C2PA asset | `present_validated` | Official signed fixture from c2pa-python test suite. Contains manifest with 0 assertions. |
| `C_altered.jpg` | Altered copy of `C.jpg` | `present_invalid` | Derived copy of `C.jpg` created by flipping bits in the file body (XOR 0xFF on trailing bytes). The original `C.jpg` was never modified. `c2pa-python` reports validation state `Invalid`. |

### Trust Anchor Note
Test certificates used in `c2pa-python` test assets are not real-world trust anchors. Validation confirms cryptographic binding and manifest parsing only, not real-world institutional trust.
