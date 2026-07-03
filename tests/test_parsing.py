from pathlib import Path

import pytest

from email_breach_checker.parsing import (
    extract_emails_from_csv,
    extract_emails_from_txt,
    is_valid_email,
    load_emails,
)


def test_is_valid_email():
    assert is_valid_email("foo@example.com")
    assert not is_valid_email("not-an-email")
    assert not is_valid_email("foo@")


def test_extract_emails_from_csv(tmp_path: Path):
    csv_file = tmp_path / "emails.csv"
    csv_file.write_text("foo@example.com,invalid\nbar@test.org,foo@example.com\n")
    valid, skipped = extract_emails_from_csv(csv_file)
    assert valid == ["foo@example.com", "bar@test.org"]
    assert skipped == []


def test_extract_emails_from_txt(tmp_path: Path):
    txt_file = tmp_path / "emails.txt"
    txt_file.write_text("Foo@Example.com\nnot-an-email\nbar@test.org\n")
    valid, skipped = extract_emails_from_txt(txt_file)
    assert valid == ["foo@example.com", "bar@test.org"]
    assert skipped == ["not-an-email"]


def test_load_emails_txt(tmp_path: Path):
    txt_file = tmp_path / "emails.txt"
    txt_file.write_text("one@example.com\n")
    valid, skipped = load_emails(txt_file)
    assert valid == ["one@example.com"]
    assert skipped == []


def test_load_emails_unsupported_suffix(tmp_path: Path):
    bad_file = tmp_path / "emails.json"
    bad_file.write_text("{}")
    with pytest.raises(ValueError, match="Unsupported file type"):
        load_emails(bad_file)
