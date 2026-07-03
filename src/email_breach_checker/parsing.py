"""Email extraction and validation from input files."""

from __future__ import annotations

import csv
import re
from pathlib import Path

EMAIL_REGEX = re.compile(r"[^@ \n\r\t]+@[^@ \n\r\t]+\.[^@ \n\r\t]+")


def is_valid_email(email: str) -> bool:
    """Return True when the email matches the supported format."""
    return EMAIL_REGEX.fullmatch(email) is not None


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def extract_emails_from_txt(path: Path) -> tuple[list[str], list[str]]:
    """Read one email per line from a text file."""
    valid: list[str] = []
    skipped: list[str] = []
    seen: set[str] = set()

    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            candidate = _normalize_email(line)
            if not candidate:
                continue
            if not is_valid_email(candidate):
                skipped.append(candidate)
                continue
            if candidate in seen:
                continue
            seen.add(candidate)
            valid.append(candidate)

    return valid, skipped


def extract_emails_from_csv(path: Path) -> tuple[list[str], list[str]]:
    """Extract email addresses from all cells in a CSV file."""
    valid: list[str] = []
    skipped: list[str] = []
    seen: set[str] = set()

    with open(path, newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.reader(handle)
        for row in reader:
            for cell in row:
                match = EMAIL_REGEX.search(cell)
                if not match:
                    continue
                candidate = _normalize_email(match.group())
                if not is_valid_email(candidate):
                    skipped.append(candidate)
                    continue
                if candidate in seen:
                    continue
                seen.add(candidate)
                valid.append(candidate)

    return valid, skipped


def load_emails(path: Path) -> tuple[list[str], list[str]]:
    """Load emails from a .txt or .csv file based on suffix."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return extract_emails_from_csv(path)
    if suffix == ".txt":
        return extract_emails_from_txt(path)
    raise ValueError(f"Unsupported file type: {suffix}. Use .txt or .csv")
