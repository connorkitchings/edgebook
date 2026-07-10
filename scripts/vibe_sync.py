#!/usr/bin/env python3
"""
Vibe-Sync Controller CLI
"""

import datetime
import re
import subprocess
from pathlib import Path

import pyperclip
import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="Vibe-Coding Session Manager")
console = Console()

PROJECT_ROOT = Path(__file__).parent.parent
SESSION_LOGS_DIR = PROJECT_ROOT / "session_logs"
CONTEXT_FILE = PROJECT_ROOT / ".agent" / "CONTEXT.md"


def get_context_section(content: str, section_name: str) -> str:
    """Extract a specific markdown section from CONTEXT.md."""
    lines = content.splitlines()
    section_content = []
    in_section = False

    # Normalize section name for matching (e.g., "## Recent" -> "Recent")
    target_header = f"## {section_name}"

    for line in lines:
        if line.strip().startswith("## "):
            if line.strip().startswith(target_header):
                in_section = True
                continue
            elif in_section:
                break  # Reached next section

        if in_section:
            section_content.append(line)

    return "\n".join(section_content).strip()


def get_last_handoff(logs) -> str:
    """Extract handoff notes from the most recent session log."""
    if not logs:
        return "No previous logs found."

    last_log = logs[0]["path"].read_text()

    # Look for "## Handoff Notes"
    # Simple heuristic parsing
    if "## Handoff Notes" in last_log:
        parts = last_log.split("## Handoff Notes")
        if len(parts) > 1:
            handoff_section = parts[1].split("## ")[0].strip()
            return handoff_section

    return "No handoff notes found in last log."


class ContextManager:
    def __init__(self, context_path: Path, logs_dir: Path):
        self.context_path = context_path
        self.logs_dir = logs_dir
        self.context_content = (
            self.context_path.read_text() if self.context_path.exists() else ""
        )

    def get_latest_log(self):
        """Retrieve the most recent session log."""
        if not self.logs_dir.exists():
            return None

        all_logs = []
        for date_dir in self.logs_dir.iterdir():
            if date_dir.is_dir() and date_dir.name != "telemetry":
                try:
                    date_obj = datetime.datetime.strptime(
                        date_dir.name, "%m-%d-%Y"
                    ).date()
                    for log_file in date_dir.glob("*.md"):
                        all_logs.append(
                            {"path": log_file, "date": date_obj, "name": log_file.name}
                        )
                except ValueError:
                    continue

        all_logs.sort(key=lambda x: (x["date"], x["name"]), reverse=True)
        return all_logs[0] if all_logs else None

    def extract_section(self, content: str, header: str) -> str:
        """Extracts content under a specific markdown header."""
        lines = content.splitlines()
        section_content = []
        in_section = False
        target_header = f"## {header}"

        for line in lines:
            if line.strip().startswith("## "):
                if line.strip().startswith(target_header):
                    in_section = True
                    continue
                elif in_section:
                    break

            if in_section:
                section_content.append(line)

        return "\n".join(section_content).strip()

    def generate_prime_directive(self, start_mode: str) -> str:
        """Assembles the High-Density Handoff string."""
        snapshot = (
            self.extract_section(self.context_content, "Project Snapshot")
            or "No snapshot available."
        )

        last_log = self.get_latest_log()
        if last_log:
            log_content = last_log["path"].read_text()
            # Extract Blockers (Crucial)
            blockers = self.extract_section(log_content, "Blockers")
            if not blockers or "None" in blockers:
                blockers = None  # Don't show if empty/none

            next_steps = (
                self.extract_section(log_content, "Next Steps")
                or "No next steps defined."
            )
        else:
            blockers = None
            next_steps = "Initialize project structure."

        # Skeptical Researcher: Check for stale context
        if "No next steps defined" in next_steps:
            next_steps = "REVIEW REQUIRED: Last session ended without clear next steps."

        # Assemble Directive
        directive = f"""
VIBE-SYNC HANDOFF
---
MODE: {start_mode}
SNAPSHOT: {snapshot.splitlines()[0] if snapshot else "N/A"}
"""
        if blockers:
            directive += f"BLOCKERS: {blockers}\n"

        directive += f"""IMMEDIATE_NEXT:
{next_steps}
---
"""
        return directive.strip()

    def copy_to_clipboard(self, text: str):
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            return False

    def update_recent_activity(self, activity: str):
        """Overwrites '## Recent Activity' in CONTEXT.md."""
        if not self.context_path.exists():
            return False

        content = self.context_path.read_text()

        # Regex to find Recent Activity section
        # Finds start of section and everything until next ## header or end of string
        pattern = r"(## Recent Activity\n)(.*?)(\n## |\Z)"

        if re.search(pattern, content, re.DOTALL):
            # Replace logic: group 1 (header), new activity, group 3 (next header/end)
            # We need to construct the replacement string carefully
            # re.sub calls a function or uses string formatting

            def replacement(match):
                header = match.group(1)
                # content = match.group(2) # existing content (ignored)
                next_part = match.group(3)

                # Format as bullet point
                new_entry = f"- {activity}"
                return f"{header}{new_entry}\n{next_part}"

            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            self.context_path.write_text(new_content)
            return True
        else:
            # Section doesn't exist, try to append it after Project Snapshot?
            # Or just fail since we expect the structure from template?
            # Let's try to append to "Current State" if "Recent Activity" is missing
            # (Migration)
            return False


def get_session_logs():
    """Retrieve all session logs, sorted by date and sequence."""
    logs = []
    if not SESSION_LOGS_DIR.exists():
        return logs

    for date_dir in SESSION_LOGS_DIR.iterdir():
        if date_dir.is_dir() and date_dir.name != "telemetry":
            # Ignore telemetry if it exists
            try:
                date_obj = datetime.datetime.strptime(date_dir.name, "%m-%d-%Y").date()
            except ValueError:
                continue

            for log_file in date_dir.glob("*.md"):
                logs.append({"path": log_file, "date": date_obj, "name": log_file.name})

    # Sort by date desc, then by name desc (assuming N - Title format)
    logs.sort(key=lambda x: (x["date"], x["name"]), reverse=True)
    return logs


@app.command()
def start(
    intent: str = typer.Option(..., prompt="What is the intent of this session?"),
    mode: str = typer.Option(
        "EXECUTION", prompt="Mode (PLANNING, EXECUTION, VERIFICATION)?"
    ),
):
    """
    Initialize a new development session.
    Generates a pruned context for the AI agent.
    """
    console.print(Panel.fit("Vibe-Sync: Initializing Session", style="bold blue"))

    # 1. Read Context
    if not CONTEXT_FILE.exists():
        console.print("[yellow]No CONTEXT.md found.[/yellow]")

    # 2. Get Recent Logs (Last 3)
    logs = get_session_logs()
    recent_logs = logs[:3]

    log_summaries = []
    for log in recent_logs:
        content = log["path"].read_text()
        # Extract TL;DR or first few lines
        lines = content.splitlines()
        summary = "\n".join(lines[:15]) + "\n..."  # Rough heuristic
        log_summaries.append(f"### {log['name']} ({log['name']})\n{summary}")

    # 3. Parse Context Sections
    # project_snapshot = get_context_section(context_content, "Project Snapshot")
    # critical_rules = get_context_section(context_content, "Critical Rules")

    # 4. Generate Prime Directive via Manager
    manager = ContextManager(CONTEXT_FILE, SESSION_LOGS_DIR)
    prime_directive = manager.generate_prime_directive(mode)

    # 5. Output and Copy
    console.print(Panel(prime_directive, title="Prime Directive", style="bold green"))

    if manager.copy_to_clipboard(prime_directive):
        console.print("[bold green]✓ Copied to clipboard![/bold green]")
    else:
        console.print("[yellow]Clipboard copy failed. Please copy manually.[/yellow]")


def get_git_changes():
    """Get list of changed files using git."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return []

        changes = []
        for line in result.stdout.splitlines():
            if line.strip():
                changes.append(line.strip())
        return changes
    except Exception:
        return []


@app.command()
def end(
    title: str = typer.Option(..., prompt="Session Title"),
):
    """
    Conclude the current session and generate a session log.
    """
    console.print(Panel.fit("Vibe-Sync: Ending Session", style="bold red"))

    # 1. Gather Intelligence
    changes = get_git_changes()

    # 2. Prompt for Details
    goal = typer.prompt("Session Goal (TL;DR)")
    accomplished = typer.prompt("Accomplished")
    blockers = typer.prompt("Blockers", default="None")
    next_steps = typer.prompt("Next Steps")

    # 3. Create Log File
    today = datetime.datetime.now()
    date_str = today.strftime("%m-%d-%Y")
    date_dir = SESSION_LOGS_DIR / date_str
    date_dir.mkdir(parents=True, exist_ok=True)

    existing_logs = list(date_dir.glob("*.md"))
    seq = len(existing_logs) + 1
    filename = f"{seq} - {title}.md"
    filepath = date_dir / filename

    # 4. Generate Content (using template format)
    if changes:
        files_list = "\n".join([f"- `{c.split()[-1]}` - Modified" for c in changes])
    else:
        files_list = "- No file changes detected via git."

    content = f"""# Session Log — {date_str} ({seq} - {title})

> **File naming:** `session_logs/MM-DD-YYYY/N - Title.md`

---

## TL;DR (≤5 lines)
- **Goal**: {goal}
- **Accomplished**: {accomplished}
- **Blockers**: {blockers}
- **Next**: {next_steps}
- **Branch**: [Feature branch name]

**Tags**: []

---

## Context
- **Started**: {today.strftime("%H:%M")}
- **Ended**: {today.strftime("%H:%M")}
- **Duration**: ~X hours
- **User Request**: [Original user request]
- **AI Tool**: [Claude Code / Gemini CLI / Codex / Antigravity]

## Work Completed

### Files Modified
{files_list}

### Tests Added/Modified
- [Add test changes here]

### Commands Run
```bash
# Commands executed during session
```

## Decisions Made
- [Key decision 1 and rationale]
- [Key decision 2 and rationale]

## Issues Encountered
{blockers if blockers != "None" else "- No issues encountered"}

## Next Steps
{next_steps}

## Handoff Notes
- **For next session**: [Context needed]
- **Open questions**: [Unresolved questions]
- **Dependencies**: [Waiting on what?]

---

**Session Owner**: [AI tool / User name]
**Related**: [PR #123] [Issue #456] [Schedule Task]
"""

    filepath.write_text(content)

    console.print(f"[green]Created session log:[/green] {filepath}")
    console.print(
        "[dim]Remember to update .agent/CONTEXT.md with recent progress.[/dim]"
    )


@app.command()
def update(
    recent: str = typer.Option(
        ..., prompt="What is the recent activity/accomplishment?"
    ),
):
    """
    Update the 'Recent' status in CONTEXT.md.
    """
    manager = ContextManager(CONTEXT_FILE, SESSION_LOGS_DIR)
    if manager.update_recent_activity(recent):
        console.print(
            f"[green]Updated 'Recent Activity' in CONTEXT.md:[/green] {recent}"
        )
    else:
        # Fallback for migration or missing section
        console.print(
            "[yellow]Could not find '## Recent Activity' in CONTEXT.md. "
            "Please check file structure.[/yellow]"
        )

    # Also touch the file to ensure timestamp update if needed
    CONTEXT_FILE.touch()


@app.command()
def suggest():
    """
    Generate a commit message suggestion based on the latest session log.
    """
    console.print(Panel.fit("Vibe-Sync: Commit Message Suggestion", style="bold blue"))

    # Find the latest session log
    log_files = []
    for date_dir in SESSION_LOGS_DIR.iterdir():
        if date_dir.is_dir() and date_dir.name != "TEMPLATE.md":
            for log_file in date_dir.glob("*.md"):
                log_files.append((log_file.stat().st_mtime, log_file))

    if not log_files:
        console.print(
            "[yellow]No session logs found.[/yellow] "
            "Run 'vibe_sync end' first to create a session log."
        )
        raise typer.Exit(1)

    # Get most recent log
    log_files.sort(reverse=True)
    latest_log = log_files[0][1]

    try:
        content = latest_log.read_text()
    except Exception as e:
        console.print(f"[red]Error reading session log:[/red] {e}")
        raise typer.Exit(1)

    # Extract information from session log
    title = "Update"
    goal = ""
    accomplished = ""
    commit_type = "chore"

    # Parse title from first line
    first_line = content.split("\n")[0]
    if " - " in first_line:
        title = first_line.split(" - ", 1)[1].replace(")", "").strip()

    # Parse goal and accomplished from TL;DR section
    in_tldr = False
    for line in content.split("\n"):
        if "## TL;DR" in line:
            in_tldr = True
            continue
        if in_tldr and line.startswith("## "):
            break
        if in_tldr:
            if line.startswith("- **Goal**:"):
                goal = line.split(":", 1)[1].strip()
            elif line.startswith("- **Accomplished**:"):
                accomplished = line.split(":", 1)[1].strip()

    # Determine commit type based on content
    title_lower = title.lower()
    if any(word in title_lower for word in ["fix", "bug", "issue", "resolve"]):
        commit_type = "fix"
    elif any(word in title_lower for word in ["add", "create", "implement", "feature"]):
        commit_type = "feat"
    elif any(word in title_lower for word in ["doc", "readme", "guide"]):
        commit_type = "docs"
    elif any(word in title_lower for word in ["test", "testing"]):
        commit_type = "test"
    elif any(word in title_lower for word in ["refactor", "clean", "restructure"]):
        commit_type = "refactor"

    # Get git status
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        git_status = result.stdout.strip()
    except Exception:
        git_status = ""

    # Format the suggestion
    commit_message = f"{commit_type}: {title.lower()}"

    # Add body if we have goal/accomplished
    body_parts = []
    if goal and goal != "[What was the intended outcome]":
        body_parts.append(f"Goal: {goal}")
    if accomplished and accomplished != "[What was completed]":
        body_parts.append(f"Accomplished: {accomplished}")

    body = "\n".join(body_parts) if body_parts else ""

    # Display suggestion
    console.print("\n[bold]Suggested Commit Message:[/bold]\n")
    console.print(f"[green]{commit_message}[/green]")
    if body:
        console.print(f"\n{body}")

    # Show changed files
    if git_status:
        console.print("\n[bold]Changed Files:[/bold]")
        for line in git_status.split("\n")[:10]:  # Show first 10
            if line:
                status = line[:2]
                filename = line[3:]
                console.print(f"  [{status.strip()}] {filename}")

        num_files = len(git_status.split("\n"))
        if num_files > 10:
            console.print(f"  ... and {num_files - 10} more files")

    console.print(
        f"\n[dim]Based on session log:[/dim] {latest_log.relative_to(PROJECT_ROOT)}"
    )
    console.print("\n[bold]Suggested commands:[/bold]")
    console.print("  git add <files>")
    console.print(f'  git commit -m "{commit_message}"')
    if body:
        # Escape quotes for shell
        escaped_body = body.replace('"', '\\"')
        console.print(f'  git commit -m "{commit_message}" -m "{escaped_body}"')


if __name__ == "__main__":
    app()
