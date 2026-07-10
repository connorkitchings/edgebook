#!/usr/bin/env python3
"""
Interactive Project Setup Script

This script helps you customize the Vibe Coding Template for your new project.
It will prompt you for project details and automatically update all template files.

Usage:
    python scripts/setup_project.py
"""

import re
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

app = typer.Typer(help="Vibe Coding Project Setup")
console = Console()

PROJECT_ROOT = Path(__file__).parent.parent

# Template variables and their replacements
REPLACEMENTS = {
    "{{PROJECT_NAME}}": "project_name",
    "{{PROJECT_TYPE}}": "project_type",
    "{{AUTHOR_NAME}}": "author_name",
    "{{PROJECT_DESCRIPTION}}": "project_description",
}


def update_file_content(file_path: Path, replacements: dict) -> bool:
    """Update file content with project-specific values."""
    if not file_path.exists():
        console.print(f"[yellow]Warning:[/yellow] File not found: {file_path}")
        return False

    try:
        content = file_path.read_text()
        original_content = content

        for template_var, value in replacements.items():
            if value:  # Only replace if value is not empty
                content = content.replace(template_var, value)

        if content != original_content:
            file_path.write_text(content)
            return True
        return False
    except Exception as e:
        console.print(f"[red]Error updating {file_path}:[/red] {e}")
        return False


def update_pyproject_toml(
    project_name: str, project_description: str, author_name: str
) -> None:
    """Update pyproject.toml with project details."""
    pyproject_file = PROJECT_ROOT / "pyproject.toml"

    if not pyproject_file.exists():
        console.print("[yellow]Warning:[/yellow] pyproject.toml not found")
        return

    try:
        content = pyproject_file.read_text()

        # Update project name
        content = re.sub(r'name = "[^"]+"', f'name = "{project_name}"', content)

        # Update description
        content = re.sub(
            r'description = "[^"]+"', f'description = "{project_description}"', content
        )

        # Update author
        content = re.sub(
            r'authors = \[\{ name = "[^"]+"',
            f'authors = [{{ name = "{author_name}"',
            content,
        )

        pyproject_file.write_text(content)
        console.print("[green]✓[/green] Updated pyproject.toml")

    except Exception as e:
        console.print(f"[red]Error updating pyproject.toml:[/red] {e}")


def update_readme(project_name: str, project_description: str) -> None:
    """Update README.md with project details."""
    readme_file = PROJECT_ROOT / "README.md"

    if not readme_file.exists():
        console.print("[yellow]Warning:[/yellow] README.md not found")
        return

    try:
        content = readme_file.read_text()

        # Replace title
        content = re.sub(
            r"^# Vibe Coding Template", f"# {project_name}", content, flags=re.MULTILINE
        )

        # Replace description line
        content = re.sub(
            r"> \*\*A lean, practical template for AI-assisted development.*",
            f"> **{project_description}**",
            content,
        )

        readme_file.write_text(content)
        console.print("[green]✓[/green] Updated README.md")

    except Exception as e:
        console.print(f"[red]Error updating README.md:[/red] {e}")


def update_context_md(project_name: str, project_type: str) -> None:
    """Update .agent/CONTEXT.md with project details."""
    context_file = PROJECT_ROOT / ".agent" / "CONTEXT.md"

    if not context_file.exists():
        console.print("[yellow]Warning:[/yellow] CONTEXT.md not found")
        return

    try:
        content = context_file.read_text()

        # Update project snapshot
        content = re.sub(
            r"\*\*Vibe Coding Template\*\*.*",
            f"**{project_name}**: {project_type} project",
            content,
        )

        context_file.write_text(content)
        console.print("[green]✓[/green] Updated CONTEXT.md")

    except Exception as e:
        console.print(f"[red]Error updating CONTEXT.md:[/red] {e}")


def create_gitignore() -> None:
    """Create .gitignore file if it doesn't exist."""
    gitignore_file = PROJECT_ROOT / ".gitignore"

    if gitignore_file.exists():
        return

    content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment variables
.env
.env.local

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# Documentation build
site/
docs/_build/

# Session logs (keep directory, ignore contents)
session_logs/*/
!session_logs/TEMPLATE.md
!session_logs/README.md

# OS
.DS_Store
Thumbs.db
"""

    gitignore_file.write_text(content)
    console.print("[green]✓[/green] Created .gitignore")


@app.command()
def run():
    """Run interactive project setup."""
    console.print(
        Panel.fit(
            "[bold blue]Vibe Coding Template Setup[/bold blue]\n"
            "Customize this template for your new project",
            title="Welcome",
            border_style="blue",
        )
    )

    console.print("\n[dim]Press Ctrl+C at any time to cancel[/dim]\n")

    # Gather project details
    console.print("[bold]Project Information[/bold]\n")

    project_name = Prompt.ask("Enter project name", default="My Project")
    project_type = Prompt.ask(
        "Project type",
        choices=["data-pipeline", "web-app", "cli-tool", "ml-model", "other"],
        default="data-pipeline",
    )
    project_description = Prompt.ask(
        "Short description", default=f"A {project_type} project"
    )
    author_name = Prompt.ask("Author name", default="Your Name")

    console.print("\n[bold]Git Configuration[/bold]\n")

    init_git = Confirm.ask("Initialize git repository?", default=True)
    create_branch = False

    if init_git:
        create_branch = Confirm.ask("Create initial feature branch?", default=True)

    # Show summary
    console.print("\n" + "=" * 60)
    console.print("[bold]Setup Summary[/bold]")
    console.print("=" * 60)
    console.print(f"Project Name: {project_name}")
    console.print(f"Project Type: {project_type}")
    console.print(f"Description: {project_description}")
    console.print(f"Author: {author_name}")
    console.print(f"Init Git: {init_git}")
    if create_branch:
        console.print("Branch: feat/initial-setup")
    console.print("=" * 60)

    if not Confirm.ask("\nProceed with setup?", default=True):
        console.print("[yellow]Setup cancelled[/yellow]")
        raise typer.Exit()

    # Perform updates
    console.print("\n[bold]Updating files...[/bold]\n")

    update_pyproject_toml(project_name, project_description, author_name)
    update_readme(project_name, project_description)
    update_context_md(project_name, project_type)
    create_gitignore()

    # Git operations
    if init_git:
        console.print("\n[bold]Git Operations[/bold]\n")
        import subprocess

        # Check if already a git repo
        git_dir = PROJECT_ROOT / ".git"
        if not git_dir.exists():
            result = subprocess.run(
                ["git", "init"], cwd=PROJECT_ROOT, capture_output=True, text=True
            )
            if result.returncode == 0:
                console.print("[green]✓[/green] Initialized git repository")
            else:
                console.print(f"[red]✗[/red] Failed to initialize git: {result.stderr}")
        else:
            console.print("[dim]ℹ[/dim] Git repository already exists")

        if create_branch:
            result = subprocess.run(
                ["git", "checkout", "-b", "feat/initial-setup"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                console.print("[green]✓[/green] Created branch: feat/initial-setup")
            else:
                console.print(f"[red]✗[/red] Failed to create branch: {result.stderr}")

    # Success message
    console.print("\n" + "=" * 60)
    console.print(
        Panel.fit(
            f"[bold green]Setup Complete![/bold green]\n\n"
            f"Your project '{project_name}' has been configured.\n\n"
            f"Next steps:\n"
            f"1. Review changes: git diff\n"
            f"2. Install dependencies: uv sync\n"
            f"3. Run validation: make validate\n"
            f"4. Start development: Read .agent/skills/start-session/SKILL.md",
            title="Success",
            border_style="green",
        )
    )


if __name__ == "__main__":
    app()
