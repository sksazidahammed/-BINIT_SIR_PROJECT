# Independent audit tool: verifies that every path listed in 03_FOLDER_AND_FILE_MAPPING.md exists on disk.
from pathlib import Path

mapping = Path("docs/03_FOLDER_AND_FILE_MAPPING.md").read_text(encoding="utf-8").splitlines()
missing = []
found = []

for line in mapping:
    if line.startswith("| `"):
        path_str = line.split("`")[1]
        p = Path(path_str)
        if not p.exists():
            missing.append(path_str)
        else:
            found.append(path_str)

print(f"Total checked: {len(found) + len(missing)}")
print(f"Found on disk: {len(found)}")
for p in found:
    print(f"  [OK] {p}")

if missing:
    print(f"Missing from disk ({len(missing)}):")
    for m in missing:
        print(f"  [MISSING] {m}")
else:
    print("ALL PATHS VERIFIED ON DISK!")
