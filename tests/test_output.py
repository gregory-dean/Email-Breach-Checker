import csv
from pathlib import Path

from email_breach_checker.hibp import Breach
from email_breach_checker.output import init_summary_csv, log_failed_lookup, write_summary_row


def test_summary_csv_round_trip(tmp_path: Path):
    output = tmp_path / "results.csv"
    init_summary_csv(output)
    breach = Breach(
        title="Example",
        domain="example.com",
        breach_date="2020-01-01",
        is_verified=True,
        pwn_count=100,
        data_classes=("Email addresses",),
        description="Test breach description",
    )
    write_summary_row(output, "user@example.com", [breach])
    write_summary_row(output, "clean@example.com", [])

    with open(output, newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    assert rows[0][0] == "Email"
    assert rows[1][0] == "user@example.com"
    assert rows[1][1] == "1"
    assert "Example" in rows[1][2]
    assert rows[2] == ["clean@example.com", "0", "", "", "", "", "", "", ""]


def test_failed_lookup_log(tmp_path: Path):
    log_path = tmp_path / "failed.log"
    log_failed_lookup(log_path, "bad@example.com", 429, "too many requests")
    content = log_path.read_text(encoding="utf-8")
    assert content == "bad@example.com - HTTP 429 - too many requests\n"
