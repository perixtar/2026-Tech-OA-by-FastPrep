#!/usr/bin/env python3
"""Focused regression tests for practice-format synchronization."""

import importlib.util
import unittest
from collections import Counter
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


def readme_with_formats() -> str:
    return "\n".join(
        [
            sync.FORMAT_LINKS_START,
            "<sub><b>Formats:</b> stale</sub>",
            sync.FORMAT_LINKS_END,
            sync.TABLE_HEADER,
            sync.TABLE_DIVIDER,
            (
                "| Example | [Coding](https://www.fastprep.io/problems/coding-one) "
                "| Coding | [Practice](https://www.fastprep.io/problems/coding-one) "
                "| Jan 02, 2026 |"
            ),
            (
                "| Example | [SQL](https://www.fastprep.io/problems/sql-one) "
                "| SQL | [Practice](https://www.fastprep.io/problems/sql-one) "
                "| Jan 01, 2026 |"
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

    def test_legacy_practice_format_header_is_renamed(self) -> None:
        content = readme_row("coding-one", "Coding").replace(
            sync.TABLE_HEADER, sync.LEGACY_TABLE_HEADER
        )

        updated, _, _ = sync.sync_readme(content, {"coding-one": "Coding"})

        self.assertIn(sync.TABLE_HEADER, updated)
        self.assertNotIn(sync.LEGACY_TABLE_HEADER, updated)

    def test_format_links_include_only_formats_in_the_table(self) -> None:
        updated = sync.sync_format_links(
            readme_with_formats(), Counter({"Coding": 1_644, "SQL": 2})
        )

        self.assertIn("[Coding (1,644)](formats/coding.md)", updated)
        self.assertIn("[SQL (2)](formats/sql.md)", updated)
        self.assertNotIn("system-design.md", updated)

    def test_format_pages_contain_only_matching_rows(self) -> None:
        pages = sync.render_format_pages(
            readme_with_formats(), Counter({"Coding": 1, "SQL": 1})
        )
        coding = pages[sync.FORMATS_DIR / "coding.md"]
        sql = pages[sync.FORMATS_DIR / "sql.md"]

        self.assertIn("coding-one", coding)
        self.assertNotIn("sql-one", coding)
        self.assertIn("sql-one", sql)
        self.assertNotIn("coding-one", sql)
        self.assertIn("| Company | OA / Interview Question | Practice | Updated |", coding)
        self.assertNotIn("| Format |", coding)


if __name__ == "__main__":
    unittest.main()
