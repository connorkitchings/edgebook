"""Enforce Edgebook's modular-monolith import rules without extra dependencies."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "src" / "edgebook"
DOMAIN_PACKAGES = {
    "analytics",
    "api",
    "application",
    "cfb",
    "core",
    "ingestion",
    "ledger",
    "wagering",
}
ALLOWED_IMPORTS = {
    "core": {"core"},
    "ledger": {"core", "ledger"},
    "cfb": {"cfb", "core"},
    "ingestion": {"cfb", "core", "ingestion"},
    "wagering": {"cfb", "core", "ledger", "wagering"},
    "analytics": {"analytics", "cfb", "core", "ledger", "wagering"},
    "application": {"application", "cfb", "core", "ingestion", "ledger", "wagering"},
    "api": DOMAIN_PACKAGES,
}
COMMAND_ADAPTER_ALLOWED_IMPORTS = {
    "ingestion/cli.py": ALLOWED_IMPORTS["ingestion"] | {"application"},
}


def edgebook_imports(path: Path) -> set[str]:
    """Return direct Edgebook package imports from a Python source file."""
    tree = ast.parse(path.read_text(), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            module = node.module.split(".")
            if module[0] == "edgebook" and len(module) > 1:
                imports.add(module[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")
                if module[0] == "edgebook" and len(module) > 1:
                    imports.add(module[1])
    return imports


def boundary_violations(package: str, imports: set[str]) -> set[str]:
    """Return imported Edgebook packages forbidden to one architecture layer."""
    return (imports & DOMAIN_PACKAGES) - ALLOWED_IMPORTS[package]


def test_project_modules_respect_import_boundaries():
    """Every production module follows the architecture documented in ADR-0002."""
    violations: dict[str, set[str]] = {}
    for path in SOURCE_ROOT.rglob("*.py"):
        relative = path.relative_to(SOURCE_ROOT)
        package = relative.parts[0] if len(relative.parts) > 1 else None
        if package not in ALLOWED_IMPORTS:
            continue
        imports = edgebook_imports(path)
        allowed = COMMAND_ADAPTER_ALLOWED_IMPORTS.get(
            str(relative), ALLOWED_IMPORTS[package]
        )
        found = (imports & DOMAIN_PACKAGES) - allowed
        if found:
            violations[str(relative)] = found
    assert violations == {}


@pytest.mark.parametrize(
    ("package", "forbidden"),
    [
        ("core", "ledger"),
        ("ledger", "cfb"),
        ("ingestion", "wagering"),
    ],
)
def test_boundary_validator_rejects_prohibited_imports(
    tmp_path: Path, package: str, forbidden: str
):
    """The validator itself catches representative forbidden dependencies."""
    module = tmp_path / "invalid_module.py"
    module.write_text(f"from edgebook.{forbidden} import models\n")
    assert boundary_violations(package, edgebook_imports(module)) == {forbidden}
