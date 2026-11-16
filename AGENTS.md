# AGENTS.md — Build Agent Rules for Single-Image Forensic Assessment

## 1. Product Rules (brief Section 2 — never break these)

1. No binary label. Output states: "indicated", "not indicated", "inconclusive", "verified", "not assessed". "Not indicated" never means "real".
2. Keep evidence typed: observation (what was measured) / interpretation (what it may mean) / limitations. Never mix them.
3. No averaging across different properties. Only outputs measuring the same property may be combined numerically.
4. Absence is not evidence. Missing metadata or manifest is "absent", never manipulation.
5. A valid C2PA manifest or matching hash does not prove the scene is real or unedited before capture.
6. Inconclusive is a valid answer and is preferred to an unsupported one.
7. Reproducible. Same file + config → identical JSON except timestamp. Record input hash, module versions, parameters, random seeds.
8. No invented results. Never hard-code metrics, fabricate datasets, or claim a detector works without running evaluation.

## 2. Limits to State in Every Report (brief Section 9)

- Absent metadata is not proof of manipulation.
- Detectors can be wrong, especially on unseen generators and processed images.
- Screenshots and repeated processing can erase traces.
- A valid C2PA manifest does not prove an event.
- A hash does not prove authenticity.
- Heatmaps are indications, not exact pixels.
- Results hold only for our evaluation data.
- The system is not approved for evidentiary use.
- The benefit of combining the two functions is unproven until tested.

## 3. Working Instructions (brief Section 10)

1. Read the whole brief first. Ask if unclear or if a choice changes scope.
2. Write tests before or with each module. Use known-answer files with an independent reference tool.
3. Keep modules independent. No module may read another module's internals.
4. Verify current library/SDK documentation. Check licences before adding any dependency or model.
5. Log every operation and parameter. Never overwrite the input file.
6. When a module cannot run, return status "failed" or "not_assessed" with a reason. Do not guess.
7. Report results exactly as measured, including poor ones.

## 4. Documentation Rules

- Documentation is mandatory and simultaneous with coding. Never postpone it.
- Whenever a file is created, changed, moved or deleted, update the docs in the same step.

## 5. Accuracy Rules

- Never invent functionality, experiments, metrics, dataset statistics or sources.
- Never record an unverified operation as successful.
- Always distinguish PLANNED / IMPLEMENTED / TESTED / COMPLETE.
- Verify every file path before documenting it.
- Never silently delete history or documentation.

## 6. Milestone Verification Loop

For every module: implement → test → update folder map → append development history → update academic report → verify docs match code → only then mark COMPLETE.

## 7. Plain-Language Rule

Every source file starts with a one-line purpose comment. Comment the WHY and HOW, not the obvious. A non-programmer must understand what each file does.

## 8. Safety Rules

- Never modify an input image.
- Never run untrusted code.
- Check licences before adding any dependency, dataset or model.
- Pin all versions.
- Check current library documentation (ExifTool, C2PA SDK, Pillow, OpenCV, Typer) instead of relying on memory.
