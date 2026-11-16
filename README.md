# Single-Image Forensic Assessment

> ⚖️ **Mandatory Rule: This system NEVER returns a "real" or "fake" label.**  
> In real life, images can be partially edited, recaptured from a computer screen, or re-saved by messaging apps. Output states are strictly:  
> `indicated` · `not indicated` · `inconclusive` · `verified` · `not assessed`

---

## 🌟 Start Here for Non-Programmers

Welcome! If you have never written a line of code in your life, this section was written specifically for you.

### What is this tool?
Think of this software as a **forensic laboratory for a single digital picture**. 

Normally, if you want to know about a photo, people use separate tools: one tool to read camera metadata, another to check digital signatures (like C2PA Content Credentials), another to look for spliced patches, and another AI detector. 

This project combines all of those tools into **one unified pipeline**. It checks:
1. **The Digital Fingerprint (M1)**: Computes a unique cryptographic fingerprint (SHA-256) of the exact file bytes.
2. **The Camera Passport (M2)**: Reads the camera make, lens, date, and software history using the industry-standard ExifTool.
3. **The Content Credentials (M3)**: Checks if the image has a tamper-proof digital signature (C2PA) from a camera or software tool.
4. **The Compression Fingerprint (M4)**: Inspects how the image was saved, measuring JPEG quality and colour distribution.
5. **Physical Manipulation Traces (M5)**: Looks for cloned regions (copy-move), double-saving traces, and resampling artifacts.
6. **AI Generator Detection (M6)**: Evaluates whether the pixel textures resemble known AI image generators, calibrated so it never guesses wildly.
7. **The Cross-Checker (M7)**: Compares all findings against each other to look for contradictions (for example, a camera signature on a picture of an AI-generated image displayed on a computer screen!).
8. **The Report & Viewer (M8 & Phase 6)**: Produces an easy-to-read report and interactive web viewer where every finding has its limitations printed right beside it.

### How to Understand the Five Possible Answers
When you look at an assessment report, you will never see a "real" or "fake" badge. Instead, each test answers with one of five honest states:
- **`verified`**: A concrete mathematical fact was confirmed (e.g. the file's hash was computed).
- **`indicated`**: Measurable traces of a phenomenon were detected (e.g. a cloned object or AI generator textures).
- **`not indicated`**: No traces of that phenomenon were found. **Important: "Not indicated" does NOT mean "real" or "unmanipulated"**—someone could have erased the traces with a simple screenshot!
- **`inconclusive`**: The signals conflict, or the image was re-saved at low quality so the tools cannot be certain. **Inconclusive is a valid and preferred answer over an unsupported guess.**
- **`not assessed`**: That specific module was skipped (for example, if a tool was not installed or offline).

---

## 🚀 Quick Start (Running in 3 Steps)

### Step 1: Install Dependencies
Open your command terminal (in Windows PowerShell or Mac/Linux Terminal) and run:
```bash
pip install -r requirements.txt
```

*(Note: Metadata inspection requires ExifTool. On Windows, install with `winget install OliverBetz.ExifTool`; on macOS, `brew install exiftool`; on Linux, `apt install libimage-exiftool-perl`.)*

### Step 2: Analyze an Image
Run the forensic analyzer on any image:
```bash
python -m forensic.cli analyze path/to/your_image.jpg --out report.json --text-out report.txt
```
This produces a detailed JSON assessment file (`report.json`) and a readable text summary (`report.txt`).

### Step 3: View the Report in Your Web Browser
Open the clean local report viewer:
```bash
python -m forensic.cli view report.json --out report.html --open
```
This opens an interactive webpage showing your image findings with limitations co-located beside each module.

---

## 📂 Plain-Language Folder Guide

| Folder / File | What it does in simple terms |
|---|---|
| `forensic/` | The engine room. Contains all the code that runs the analysis modules. |
| `forensic/modules/` | The individual specialists: M1 (file identity), M2 (metadata), M3 (C2PA credentials), M4 (compression), M5 (classical indicators), M6 (synthetic detection). |
| `forensic/correlate/` | The cross-checker (M7). Holds decision rules D1–D8 to detect contradictions. |
| `forensic/viewer.py` | The report viewer (Phase 6). Turns raw JSON into a readable web page with zero analysis logic. |
| `eval/` | The scientific testing laboratory. Measures accuracy, robustness across transformations (T0–T7), and runs the C0 vs C1 ablation study. |
| `tests/` | Automated quality checks. 138 automated unit tests verifying that every single part works without bugs. |
| `docs/` | Comprehensive technical documentation, architecture blueprints, algorithm design, and decision logs. |
| `development_logs/` | Detailed chronological lab notebooks: every code change, test result, and real experiment. |
| `reports/` | Academic project report documenting the theoretical foundation, empirical results, and findings. |
| `config.yaml` | The configuration file where you can adjust file size limits or paths. |
| `AGENTS.md` | Strict rules that any AI software developer or human must follow when editing this code. |

---

## 🔬 Core Scientific Finding (Ablation C0 vs C1)

During Phase 5, we tested the central scientific question of this project:  
*Does combining provenance and metadata with an AI detector actually improve performance over an AI detector alone?*

Our empirical findings on 72 benchmark test images revealed:
1. **On clean, uncompressed images**: Both the detector alone (C0) and the combined rules system (C1) achieve identical accuracy ($\Delta \text{Accuracy} = 0.0000, p = 1.0000$). Combining tools does not magically make a clean prediction better.
2. **On degraded and contradictory images**:
   - The detector alone (C0) suffered a **13.89% error rate** because it was easily fooled by screen recaptures and heavy compression.
   - The combined system (C1) activated Rule D2 (flagging contradictory recaptures) and Rule D6 (flagging degraded compression) and **abstained to `inconclusive`**.
   - By abstaining instead of guessing on compromised pictures, the combined system achieved a **0.0% error rate (risk)** on decided cases.

**Bottom line**: Combining provenance with trace analysis and synthetic detection does not boost accuracy on easy cases; its true power is **preventing dangerous mistakes by refusing to guess when evidence is compromised**.

---

## 🛡️ Mandatory Limitations (Always Kept in Mind)

Every report and experiment adheres strictly to the 9 mandatory limits from Brief Section 9:
1. Absent metadata is not proof of manipulation.
2. Detectors can be wrong, especially on unseen generators and processed images.
3. Screenshots and repeated processing can erase traces.
4. A valid C2PA manifest does not prove an event occurred in the real world.
5. A matching hash does not prove authenticity.
6. Heatmaps are indications, not exact pixels.
7. Results hold only for our evaluation benchmark data.
8. The system is not approved for evidentiary or legal use.
9. The benefit of combining the two functions is unproven until tested.

---

## 🧪 Verification Commands

To verify all 138 automated tests:
```powershell
python -m pytest -v
```

To run the evaluation ablation study:
```powershell
python -m eval.ablation
```

To audit every mapped file path in the repository:
```powershell
python tools/audit_mapping.py
```
