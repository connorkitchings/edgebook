#!/usr/bin/env python3
"""
Context Audit Skill
===================
Scans the current directory to estimate token counts for files, helping agents
manage their context budget.

Usage:
    python .agents/skills/context-audit.py [path]

Methodology:
    - Heuristic: 4 characters ~= 1 token (approximate for English text/code).
    - Ignores: .git, __pycache__, .DS_Store, common binary extensions, and lock files.
"""

import os
import sys
from pathlib import Path

# Configuration
TOKEN_RATIO = 4.0  # chars per token
WARNING_THRESHOLD = 5000  # tokens
CRITICAL_THRESHOLD = 10000  # tokens
TOP_N = 10

# Ignore patterns (simple substring matching for now)
IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "site",
    ".gemini",
}
IGNORE_EXTS = {
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp4",
    ".mov",
    ".zip",
    ".tar",
    ".gz",
    ".lock",
    ".pdf",
}
IGNORE_FILES = {"uv.lock", "package-lock.json", "yarn.lock", ".DS_Store"}


def estimate_tokens(file_path: Path) -> int:
    try:
        # read as text, ignore encoding errors (e.g. slight binary content)
        content = file_path.read_text(errors="ignore")
        return int(len(content) / TOKEN_RATIO)
    except Exception:
        return 0


def scan_repository(root_path: Path):
    file_stats = []
    dir_stats = {}

    print(f"🔎 Scanning {root_path} for context heavy files...\n")

    for root, dirs, files in os.walk(root_path):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        rel_root = Path(root).relative_to(root_path)

        # Aggregate directory stats (top level only for simplicity)
        top_level_dir = rel_root.parts[0] if rel_root.parts else "."
        if top_level_dir not in dir_stats:
            dir_stats[top_level_dir] = 0

        for file in files:
            if file in IGNORE_FILES:
                continue
            if any(file.endswith(ext) for ext in IGNORE_EXTS):
                continue

            file_path = Path(root) / file
            tokens = estimate_tokens(file_path)

            if tokens > 0:
                file_stats.append((str(file_path.relative_to(root_path)), tokens))
                dir_stats[top_level_dir] += tokens

    # Sort files by size
    file_stats.sort(key=lambda x: x[1], reverse=True)

    # Output Reports
    print(f"{'TOKENS':<10} | {'FILE PATH'}")
    print("-" * 60)

    # Print Top N
    for path, tokens in file_stats[:TOP_N]:
        prefix = (
            "🔴"
            if tokens > CRITICAL_THRESHOLD
            else ("🟡" if tokens > WARNING_THRESHOLD else "  ")
        )
        print(f"{tokens:<10} | {prefix} {path}")

    print("\n" + "=" * 60 + "\n")

    print(f"{'TOKENS':<10} | {'DIRECTORY OVERVIEW'}")
    print("-" * 60)

    # Sort dirs by size
    sorted_dirs = sorted(dir_stats.items(), key=lambda x: x[1], reverse=True)
    for dir_name, tokens in sorted_dirs:
        if tokens > 100:  # Filter empty/tiny dirs
            print(f"{tokens:<10} | {dir_name}/")

    print("Example Action:")
    print(
        "If a single file is > 10k tokens, consider breaking it up or moving "
        "archival content to `docs/archive/`."
    )


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    scan_repository(path)
