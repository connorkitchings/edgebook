"""CI helper to verify [IMPL-task:X] etc. resolve."""

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "documents"

parser = argparse.ArgumentParser(description="Validate specific anchor types.")
parser.add_argument(
    "--types",
    nargs="+",
    default=["IMPL-task", "PRD-decision", "KB", "QG", "LOG"],
    help="Anchor types to validate (default: all)",
)
args = parser.parse_args()

PATTERNS = []
if "IMPL-task" in args.types:
    PATTERNS.append(re.compile(r"\[IMPL-task:(\w+)\]"))
if "PRD-decision" in args.types:
    PATTERNS.append(re.compile(r"\[PRD-decision:(\d{4}-\d{2}-\d{2})\]"))
if "KB" in args.types:
    PATTERNS.append(re.compile(r"\[KB:([\w-]+)\]"))
if "QG" in args.types:
    PATTERNS.append(re.compile(r"\[QG:([\w-]+)\]"))
if "LOG" in args.types:
    PATTERNS.append(re.compile(r"\[LOG:(\d{4}-\d{2}-\d{2})\]"))


# Collect all markdown files
files = list(DOCS.rglob("*.md")) + [ROOT / "README.md"]
anchors = set()
for file in files:
    with open(file, encoding="utf-8") as f:
        for line in f:
            for pat in PATTERNS:
                for m in pat.finditer(line):
                    anchors.add(m.group(0))

# Check that all anchors resolve (dummy logic: just print them for now)
for anchor in anchors:
    print(f"Found anchor: {anchor}")

# TODO: Implement full cross-doc anchor resolution logic
