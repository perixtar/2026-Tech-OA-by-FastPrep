#!/usr/bin/env python3
"""Focused regression tests for practice-format synchronization."""

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("sync-practice-formats.py")
SPEC = importlib.util.spec_from_file_location("sync_practice_formats", SCRIPT)
assert SPEC and SPEC.loader
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


def readme_row(route: str, current_label: str = "Unknown") -> str:
    return "\n".join(
        [
            sync.TABLE_HEADER,
            sync.TABLE_DIVIDER,
            (
                "| Example | "
                f"[Question](https://www.fastprep.io/problems/{route}) | "
                f"{current_label} | "
                f"[Practice](https://www.fastprep.io/problems/{route}) | "
                "Jan 01, 2026 |"
            ),
            sync.BOTTOM_ANCHOR,
            "",
        ]
    )


class SyncPracticeFormatsTest(unittest.TestCase):
    def test_missing_catalog_entry_uses_coding_route_fallback(self) -> None:
        updated, counts, catalog_missing = sync.sync_readme(
            readme_row("legacy-coding-problem"), {}
        )

        self.assertIn("| Coding |", updated)
        self.assertNotIn("| Unknown |", updated)
        self.assertEqual(counts, {"Coding": 1})
        self.assertEqual(catalog_missing, ["legacy-coding-problem"])

    def test_catalog_format_overrides_coding_route_fallback(self) -> None:
        updated, counts, catalog_missing = sync.sync_readme(
            readme_row("sql-problem", "Coding"), {"sql-problem": "SQL"}
        )

        self.assertIn("| SQL |", updated)
        self.assertEqual(counts, {"SQL": 1})
        self.assertEqual(catalog_missing, [])


if __name__ == "__main__":
    unittest.main()
