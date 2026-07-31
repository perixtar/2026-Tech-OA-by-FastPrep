# Contributing

Thanks for helping keep the 2026 Tech OA tracker current. The repo is useful only if reports are specific, source-safe, and easy to verify.

## What To Submit

Good submissions include one or more of the following:

- A newly seen Online Assessment or interview question.
- A correction to a company name, question title, practice link, or update date.
- A missing FastPrep practice link for an existing row.
- A stale or duplicate row that should be reviewed.

## Submission Checklist

When opening an issue, include:

- Company name.
- Role, location, and recruiting season if known.
- Question title or a short source-safe summary.
- Date seen.
- Source context, such as public post, candidate report, or your own anonymized experience.
- FastPrep problem link if one already exists.

Practice format is maintained from FastPrep's problem metadata. Please do not
guess it from a title or company; maintainers run
`python3 scripts/sync-practice-formats.py` after updating the question table.

Please do not submit confidential screenshots, private recruiter messages, account-only assessment pages, or full proprietary problem statements. A short summary is enough for maintainers to verify the report and create a practice-safe entry.

## How Updates Are Reviewed

Maintainers check whether the report is specific, plausible, and safe to
publish. Once verified, the README table should be updated with the company,
question link, practice link, and update date. Then sync the practice-format
column from the public FastPrep catalog and run
`python3 scripts/refresh-freshness.py`.

Prefer one issue per company/question so each report can be tracked independently.

## Corrections

For corrections, link the current README row and explain the exact change needed. Examples:

- Broken practice link.
- Typo in the question title.
- Duplicate question row.
- Incorrect company attribution.

## Community

For quick discussion or follow-up context, join the FastPrep Discord: https://discord.gg/kSbWpSGUTH
