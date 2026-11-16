# Independent verification tool: verifies repeat JSON determinism and strict absence of real/fake binary labels.
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from forensic.cli import app
from typer.testing import CliRunner

runner = CliRunner()
img = "tests/data/test_valid_jpeg.jpg"

res1 = runner.invoke(app, ["analyze", img, "--out", "run1.json"])
res2 = runner.invoke(app, ["analyze", img, "--out", "run2.json"])

d1 = json.loads(Path("run1.json").read_text(encoding="utf-8"))
d2 = json.loads(Path("run2.json").read_text(encoding="utf-8"))

# Check real/fake label anywhere
s1 = json.dumps(d1).lower()
violations = []
for forbidden in ['"real"', '"fake"', '"authentic"', '"manipulated"']:
    if forbidden in s1:
        violations.append(forbidden)

if violations:
    print(f"VIOLATION: Found forbidden labels: {violations}")
else:
    print("PASS: No real/fake/authentic/manipulated labels found anywhere in JSON output!")

print(f"verdict field value: {d1.get('verdict')}")
print(f"verdict_note: {d1.get('verdict_note')}")

# Compare run1 and run2 ignoring report_timestamp
t1 = d1.pop("report_timestamp")
t2 = d2.pop("report_timestamp")
if d1 == d2:
    print("PASS: Repeat runs produce BIT-FOR-BIT IDENTICAL JSON (apart from report_timestamp)!")
else:
    print("FAIL: Mismatch between run1 and run2!")

# Clean up temporary test files
Path("run1.json").unlink(missing_ok=True)
Path("run2.json").unlink(missing_ok=True)
