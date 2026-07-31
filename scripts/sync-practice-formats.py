#!/usr/bin/env python3
"""Sync README practice-format labels from FastPrep's public problem catalog.

The production Firestore ``problem.practiceFormat`` field is the source of
truth. The anonymous catalog API exposes its public projection and applies the
application's backward-compatible default: a coding problem without the field
is an algorithm problem. Legacy ``/problems/`` routes that predate the public
catalog use the same coding-route fallback; explicit catalog metadata always
wins, including for SQL problems.

Run after adding or updating question-bank rows:

    python3 scripts/sync-practice-formats.py
    python3 scripts/sync-practice-formats.py --check

Use ``--catalog-file`` only with a reviewed export containing public-safe
metadata (``id``, optional ``url``, and optional ``practiceFormat``).
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

README = Path(__file__).resolve().parent.parent / "README.md"
CATALOG_URL = "https://www.fastprep.io/api/problems?v=1"
OLD_TABLE_HEADER = "| Company | OA / Interview Question | Practice | Updated |"
TABLE_HEADER = (
    "| Company | OA / Interview Question | Practice format | Practice | Updated |"
)
OLD_TABLE_DIVIDER = "| :-- | :-- | :-: | :-- |"
TABLE_DIVIDER = "| :-- | :-- | :-- | :-: | :-- |"
BOTTOM_ANCHOR = '<a id="bottom"></a>'

FORMAT_LABELS = {
    "algorithm": "Coding",
    "tabular": "SQL",
    "system_design": "System design",
    "low_level_design": "Low-level design",
    "project_coding": "AI coding",
}
KNOWN_LABELS = {*FORMAT_LABELS.values(), "Unknown"}
ROUTE_PREFIXES = {
    "https://www.fastprep.io/problems/": "Coding",
    "https://www.fastprep.io/system-design/": "System design",
    "https://www.fastprep.io/low-level-design/": "Low-level design",
    "https://www.fastprep.io/project-coding/": "AI coding",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog-file",
        type=Path,
        help="Read a reviewed public-safe catalog JSON file instead of the public API.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero if README practice-format labels are not current.",
    )
    return parser.parse_args()


def load_catalog(catalog_file: Path | None) -> list[dict]:
    if catalog_file:
        try:
            payload = json.loads(catalog_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"could not read catalog file: {error}") from error
    else:
        request = Request(
            CATALOG_URL,
            headers={"User-Agent": "FastPrep-practice-format-sync/1"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise ValueError(f"could not read FastPrep public catalog: {error}") from error

    if not isinstance(payload, list) or not all(
        isinstance(item, dict) for item in payload
    ):
        raise ValueError("catalog must be a JSON array of objects")
    return payload


def build_format_index(catalog: list[dict]) -> dict[str, str]:
    formats: dict[str, str] = {}
    for index, item in enumerate(catalog):
        problem_id = item.get("id")
        route_alias = item.get("url")
        if not isinstance(problem_id, str) or not problem_id.strip():
            raise ValueError(f"catalog item {index} has no usable id or url")

        raw_format = item.get("practiceFormat", "algorithm")
        if raw_format not in FORMAT_LABELS:
            raise ValueError(
                f'catalog route "{route_alias or problem_id}" has unsupported '
                f"practiceFormat {raw_format!r}"
            )
        label = FORMAT_LABELS[raw_format]
        routes = [problem_id]
        if isinstance(route_alias, str) and route_alias.strip():
            routes.append(route_alias)
        for route in routes:
            if route in formats and formats[route] != label:
                raise ValueError(f'catalog route "{route}" has conflicting formats')
            formats[route] = label
    return formats


def row_route_and_namespace(question_cell: str) -> tuple[str, str]:
    for prefix, namespace_label in ROUTE_PREFIXES.items():
        marker = question_cell.find(prefix)
        if marker == -1:
            continue
        route_start = marker + len(prefix)
        route_end = question_cell.find(")", route_start)
        if route_end == -1:
            break
        route = question_cell[route_start:route_end]
        if route:
            return route, namespace_label
    raise ValueError("question cell has no supported FastPrep practice route")


def sync_readme(
    content: str,
    formats: dict[str, str],
) -> tuple[str, Counter, list[str]]:
    lines = content.splitlines()
    try:
        header_index = lines.index(TABLE_HEADER)
        has_format_column = True
    except ValueError:
        try:
            header_index = lines.index(OLD_TABLE_HEADER)
            has_format_column = False
        except ValueError as error:
            raise ValueError("question table header not found") from error

    expected_divider = TABLE_DIVIDER if has_format_column else OLD_TABLE_DIVIDER
    if header_index + 1 >= len(lines) or lines[header_index + 1] != expected_divider:
        raise ValueError("question table divider is missing or malformed")
    try:
        bottom_index = lines.index(BOTTOM_ANCHOR, header_index + 2)
    except ValueError as error:
        raise ValueError("question table bottom anchor not found") from error
    if bottom_index == header_index + 2:
        raise ValueError("question table has no rows")

    lines[header_index] = TABLE_HEADER
    lines[header_index + 1] = TABLE_DIVIDER
    counts: Counter[str] = Counter()
    catalog_missing: list[str] = []

    for line_index in range(header_index + 2, bottom_index):
        parts = lines[line_index].split("|")
        expected_parts = 7 if has_format_column else 6
        if len(parts) != expected_parts or parts[0] or parts[-1]:
            raise ValueError(f"row {line_index + 1} is malformed")

        route, namespace_label = row_route_and_namespace(parts[2])
        existing_label = parts[3].strip() if has_format_column else None
        if existing_label is not None and existing_label not in KNOWN_LABELS:
            raise ValueError(
                f"row {line_index + 1} has unsupported practice format {existing_label!r}"
            )

        catalog_label = formats.get(route)
        if catalog_label is None and namespace_label == "Coding":
            catalog_missing.append(route)
        label = catalog_label or namespace_label

        if has_format_column:
            parts[3] = f" {label} "
        else:
            parts.insert(3, f" {label} ")
        lines[line_index] = "|".join(parts)
        counts[label] += 1

    return "\n".join(lines) + "\n", counts, catalog_missing


def main() -> int:
    args = parse_args()
    try:
        formats = build_format_index(load_catalog(args.catalog_file))
        original = README.read_text(encoding="utf-8")
        updated, counts, catalog_missing = sync_readme(original, formats)
    except (OSError, ValueError) as error:
        print(f"practice-format sync failed: {error}", file=sys.stderr)
        return 2

    changed = updated != original
    unknown = counts["Unknown"]
    summary = ", ".join(f"{label}={counts[label]}" for label in sorted(counts))
    print(
        f"practice formats: {summary}; catalog-missing={len(catalog_missing)}; "
        f"unclassified={unknown}"
    )
    if catalog_missing:
        print("catalog-missing routes: " + ", ".join(catalog_missing))

    if unknown:
        print("practice-format sync produced an unclassified row", file=sys.stderr)
        return 2

    if args.check:
        if changed:
            print("README practice formats are not current", file=sys.stderr)
            return 1
        return 0

    if changed:
        README.write_text(updated, encoding="utf-8")
        print("updated README practice-format column")
    else:
        print("README practice-format column already current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
