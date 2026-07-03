"""CSV summary and failed-lookup log writers."""

from __future__ import annotations

import csv
from pathlib import Path

from email_breach_checker.hibp import Breach

SUMMARY_HEADERS = [
    "Email",
    "Breach Count",
    "Breach Titles",
    "Domains",
    "Breach Dates",
    "Verified",
    "PwnCounts",
    "Compromised Data",
    "Descriptions",
]


def init_summary_csv(path: Path) -> None:
    """Create or overwrite the summary CSV with headers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(SUMMARY_HEADERS)


def write_summary_row(path: Path, email: str, breaches: list[Breach]) -> None:
    """Append one grouped summary row for an email address."""
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if breaches:
            titles = "; ".join(b.title for b in breaches)
            domains = "; ".join(b.domain for b in breaches)
            dates = "; ".join(b.breach_date for b in breaches)
            verified = "; ".join("Yes" if b.is_verified else "No" for b in breaches)
            pwn_counts = "; ".join(str(b.pwn_count) for b in breaches)
            data_classes = "; ".join(sorted({dc for b in breaches for dc in b.data_classes}))
            descriptions = "; ".join(b.description[:100] for b in breaches)
            writer.writerow(
                [
                    email,
                    len(breaches),
                    titles,
                    domains,
                    dates,
                    verified,
                    pwn_counts,
                    data_classes,
                    descriptions,
                ]
            )
        else:
            writer.writerow([email, 0, "", "", "", "", "", "", ""])


def log_failed_lookup(path: Path, email: str, status_code: int, detail: str = "") -> None:
    """Append a failed lookup entry to the log file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        if detail:
            handle.write(f"{email} - HTTP {status_code} - {detail}\n")
        else:
            handle.write(f"{email} - HTTP {status_code}\n")
