# 02. Project Architecture

## System Overview
The Single-Image Forensic Assessment architecture combines digital image provenance and metadata verification with pixel-level trace analysis. The system strictly adheres to the principle that evidence is typed and never averaged across orthogonal domains. It never outputs a binary "real" or "fake" verdict.

```mermaid
flowchart TD
    In["Input Image File"] --> S0["Stage 0: Validation & Hash<br/>(Content type, Limits, SHA-256)"]
    
    subgraph Modules["Independent Forensic Modules (Phase 1)"]
        direction TB
        M1["M1: File Identity<br/>(Byte hash, dimensions, format)"]
        M2["M2: Metadata<br/>(ExifTool: EXIF, IPTC, XMP, GPS flag)"]
        M3["M3: C2PA Provenance<br/>(c2pa-python: Manifest verification)"]
        M4["M4: Compression & Colour<br/>(JPEG DQT, quality, colour stats)"]
        M5["M5: Classical Indicators<br/>(Double JPEG, Resampling - Phase 2)"]
        M6["M6: Synthetic Detection<br/>(Pretrained models - Phase 3)"]
    end

    S0 --> M1
    S0 --> M2
    S0 --> M3
    S0 --> M4
    S0 -.-> M5
    S0 -.-> M6

    M1 --> M7["M7: Correlation Layer<br/>(Rule Decision Table D1-D8 - Phase 4)"]
    M2 --> M7
    M3 --> M7
    M4 --> M7
    M5 -.-> M7
    M6 -.-> M7

    M7 --> M8["M8: Assessment Report Generation<br/>(JSON & Human-Readable Text)"]
    M8 --> OutJSON["report.json"]
    M8 --> OutTXT["report.txt"]
```

## Architectural Principles
1. **Module Independence**: Every module receives an immutable file path and configuration. No module reads or depends on another module's internal state.
2. **Unified Record Format**: All modules return the standard `EvidenceRecord` data structure containing typed observation, interpretation, and limitations.
3. **No Binary Labels**: Output states are strictly constrained to:
   - `indicated`
   - `not_indicated`
   - `inconclusive`
   - `verified`
   - `not_assessed`
4. **Fail-Safe Operation**: If a tool or external dependency fails or is unavailable, the module returns `failed` or `not_assessed` with a documented reason instead of crashing or guessing.
5. **Reproducibility**: Identical inputs with identical configurations yield byte-identical outputs, with the sole exception of the execution timestamp.
