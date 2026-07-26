#!/usr/bin/env python3
"""Sort and refresh the README question table.

Rows updated within the last 14 days get a fire marker, within 45 days a new
marker, older rows get none. Rows are kept newest-first by their Updated date.
Run this whenever the table is regenerated or on a schedule so ordering and
markers stay current:

    python3 scripts/refresh-freshness.py
"""
import re
import sys
from datetime import date
from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"
FIRE_DAYS, NEW_DAYS = 14, 45
MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}
CELL = re.compile(r"^(?P<head>\|.*\| )(?:🔥 |🆕 )?(?P<mon>[A-Z][a-z]{2}) (?P<day>\d{2}), (?P<year>\d{4}) \|$")

today = date.today()
changed = 0
question_rows = []
lines = README.read_text(encoding="utf-8").splitlines()
for i, line in enumerate(lines):
    if "fastprep.io/problems" not in line:
        continue
    m = CELL.match(line)
    if not m:
        sys.exit(f"row {i + 1} does not match the expected format: {line[:120]}")
    age = (today - date(int(m["year"]), MONTHS[m["mon"]], int(m["day"]))).days
    mark = "🔥 " if age <= FIRE_DAYS else ("🆕 " if age <= NEW_DAYS else "")
    new = f"{m['head']}{mark}{m['mon']} {m['day']}, {m['year']} |"
    if new != line:
        lines[i] = new
        changed += 1
    question_rows.append(
        (i, date(int(m["year"]), MONTHS[m["mon"]], int(m["day"])), new)
    )

sorted_rows = sorted(question_rows, key=lambda row: row[1], reverse=True)
target_indexes = [index for index, _, _ in question_rows]
sorted_lines = [row for _, _, row in sorted_rows]
moved = sum(
    lines[target_index] != row
    for target_index, row in zip(target_indexes, sorted_lines)
)
for target_index, row in zip(target_indexes, sorted_lines):
    lines[target_index] = row

README.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"refreshed markers on {changed} row(s); reordered {moved} row position(s)")
