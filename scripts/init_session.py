"""Print handoff & sprint focus at shell startup."""

import datetime
import pathlib
import textwrap

import yaml

doc = pathlib.Path("documents/execution/dev_log.md")
last_entry = "Unknown"
try:
    text = doc.read_text()
    if "[" in text and "]" in text:
        last_entry = text.split("[")[-1].split("]")[0]
except Exception as e:
    last_entry = f"Error reading dev_log.md: {e}"

handoff_data = {
    "date": str(datetime.date.today()),
    "last_session": last_entry,
    "next_task": "see implementation_schedule.md",
}

print(
    textwrap.dedent(f"""
 {handoff_data["date"]} | Last session: {handoff_data["last_session"]}
Next task → {handoff_data["next_task"]}
""")
)
print("---\nYAML Handoff:")
print(yaml.dump(handoff_data, sort_keys=False))
