#!/usr/bin/env python3
"""
Template Validation Script

Validates that the Vibe Coding template is properly configured and all
referenced files exist. This script can be run locally or in CI.

Usage:
    python scripts/validate_template.py

Exit codes:
    0 - All validations passed
    1 - One or more validations failed
"""

import re
import sys
from pathlib import Path
from typing import List


class Colors:
    """Terminal colors for output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


def print_success(message: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.END} {message}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.END} {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")


def print_info(message: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")


class Validator:
    """Template validation runner."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []

    def validate(self) -> bool:
        """Run all validations."""
        print_info("Starting template validation...\n")

        # Critical validations
        self._validate_agents_md()
        self._validate_required_files()
        self._validate_documentation_paths()

        # Optional validations
        self._check_placeholder_variables()
        self._validate_directory_structure()
        self._check_template_version()

        # Print summary
        print("\n" + "=" * 60)
        print_info("Validation Summary")
        print("=" * 60)

        if self.successes:
            print(f"\n{Colors.GREEN}Passed: {len(self.successes)}{Colors.END}")
            for success in self.successes:
                print(f"  ✓ {success}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.END}")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        if self.errors:
            print(f"\n{Colors.RED}Errors: {len(self.errors)}{Colors.END}")
            for error in self.errors:
                print(f"  ✗ {error}")

        return len(self.errors) == 0

    def _validate_agents_md(self) -> None:
        """Check that AGENTS.md is a redirect and .agent/AGENTS.md exists."""
        root_agents = self.project_root / "AGENTS.md"
        agent_agents = self.project_root / ".agent" / "AGENTS.md"

        # Check .agent/AGENTS.md exists
        if agent_agents.exists():
            self.successes.append(".agent/AGENTS.md exists")
        else:
            self.errors.append(".agent/AGENTS.md not found")
            return

        # Check root AGENTS.md is a redirect
        if root_agents.exists():
            content = root_agents.read_text()
            if "Redirect" in content or "redirects to" in content.lower():
                self.successes.append("Root AGENTS.md is a redirect")
            else:
                self.errors.append("Root AGENTS.md should be a redirect file")
        else:
            self.warnings.append(
                "Root AGENTS.md not found (should redirect to .agent/AGENTS.md)"
            )

    def _validate_required_files(self) -> None:
        """Check that required files exist."""
        required_files = [
            "README.md",
            "pyproject.toml",
            ".agent/CONTEXT.md",
            ".agent/skills/CATALOG.md",
            ".agent/skills/start-session/SKILL.md",
            ".agent/skills/end-session/SKILL.md",
            "docs/implementation_schedule.md",
            "docs/development_standards.md",
            "docs/checklists.md",
            "session_logs/TEMPLATE.md",
            ".pre-commit-config.yaml",
        ]

        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.successes.append(f"Required file exists: {file_path}")
            else:
                self.errors.append(f"Required file missing: {file_path}")

    def _validate_documentation_paths(self) -> None:
        """Check that paths referenced in docs actually exist."""
        docs_dir = self.project_root / "docs"
        if not docs_dir.exists():
            self.warnings.append("docs/ directory not found")
            return

        # Check for broken internal links in markdown files
        md_files = list(docs_dir.rglob("*.md"))
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        broken_links = 0
        for md_file in md_files:
            content = md_file.read_text()
            for match in link_pattern.finditer(content):
                link_text, link_path = match.groups()

                # Skip external links
                if link_path.startswith(("http://", "https://", "mailto:")):
                    continue

                # Skip anchors
                if link_path.startswith("#"):
                    continue

                # Resolve relative path
                if link_path.startswith("./"):
                    full_link_path = md_file.parent / link_path[2:]
                elif link_path.startswith("../"):
                    full_link_path = (md_file.parent / link_path).resolve()
                else:
                    full_link_path = self.project_root / link_path

                # Check if path exists
                if not full_link_path.exists():
                    # Don't count as error for template variables
                    if "{{" not in link_path:
                        broken_links += 1
                        if broken_links <= 5:  # Limit output
                            rel_path = md_file.relative_to(self.project_root)
                            self.warnings.append(
                                f"Broken link in {rel_path}: {link_path}"
                            )

        if broken_links == 0:
            self.successes.append("All documentation links valid")
        elif broken_links > 5:
            self.warnings.append(
                f"Found {broken_links} broken links in documentation (showing first 5)"
            )

    def _check_placeholder_variables(self) -> None:
        """Check for template placeholder variables that should be replaced."""
        placeholder_pattern = re.compile(r"\{\{[A-Z_]+\}\}")

        # Files that should have been customized
        customization_files = [
            "docs/implementation_schedule.md",
        ]

        placeholders_found = 0
        for file_path in customization_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                content = full_path.read_text()
                matches = placeholder_pattern.findall(content)
                if matches:
                    placeholders_found += len(matches)
                    ph_str = str(matches[:3])
                    self.warnings.append(
                        f"{file_path} has {len(matches)} placeholders: {ph_str}"
                    )

        if placeholders_found == 0:
            self.successes.append("No unresolved template placeholders")

    def _validate_directory_structure(self) -> None:
        """Check that expected directories exist."""
        expected_dirs = [
            "src",
            "tests",
            "docs",
            "scripts",
            "config",
            "session_logs",
            ".agent",
            ".agent/skills",
            ".agent/workflows",
        ]

        for dir_path in expected_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                self.successes.append(f"Directory exists: {dir_path}")
            else:
                self.warnings.append(f"Expected directory not found: {dir_path}")

    def _check_template_version(self) -> None:
        """Check and display template version."""
        version_file = self.project_root / "TEMPLATE_VERSION"
        if version_file.exists():
            version = version_file.read_text().strip()
            self.successes.append(f"Template version: {version}")
        else:
            self.warnings.append("TEMPLATE_VERSION file not found")


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent

    validator = Validator(project_root)
    success = validator.validate()

    print("\n" + "=" * 60)
    if success:
        print_success("Template validation passed!")
        sys.exit(0)
    else:
        print_error("Template validation failed!")
        print("\nFix the errors above to ensure the template is complete.")
        sys.exit(1)


if __name__ == "__main__":
    main()
