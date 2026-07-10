"""
CLI entrypoint for Vibe Coding utility scripts.

This script aggregates subcommands from init_session, init_template, and check_links.

Usage:
    python scripts/cli.py [subcommand]

Subcommands:
    init-session
    init-template
    check-links
"""

import typer

from scripts.check_links import main as check_links_main
from scripts.init_session import main as init_session_main
from scripts.init_template import main as init_template_main

app = typer.Typer(help="Vibe Coding Utility CLI")


@app.command("init-session")
def init_session():
    """Initialize a new session."""
    init_session_main()


@app.command("init-template")
def init_template():
    """Initialize a new template."""
    init_template_main()


@app.command("check-links")
def check_links():
    """Check documentation links for validity."""
    check_links_main()


if __name__ == "__main__":
    app()
