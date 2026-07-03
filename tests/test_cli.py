import csv
from pathlib import Path
from unittest.mock import MagicMock

from email_breach_checker.cli import EXIT_RUNTIME_ERROR, EXIT_SUCCESS, EXIT_USAGE_ERROR, run
from email_breach_checker.hibp import Breach


def _args(tmp_path: Path, **overrides):
    if "input_file" in overrides:
        input_file = overrides.pop("input_file")
    else:
        input_file = tmp_path / "emails.txt"
        input_file.write_text("user@example.com\nclean@example.com\n")
    defaults = {
        "input_file": input_file,
        "output": tmp_path / "results.csv",
        "failed_log": tmp_path / "failed.log",
        "delay": 0.0,
        "api_key": "test-key",
        "quiet": True,
    }
    defaults.update(overrides)
    return type("Args", (), defaults)()


def test_run_missing_api_key(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("HIBP_API_KEY", raising=False)
    args = _args(tmp_path, api_key=None)
    assert run(args) == EXIT_USAGE_ERROR


def test_run_missing_input_file(tmp_path: Path):
    missing = tmp_path / "missing.txt"
    args = _args(tmp_path, input_file=missing)
    assert run(args) == EXIT_USAGE_ERROR


def test_run_no_valid_emails(tmp_path: Path):
    input_file = tmp_path / "emails.txt"
    input_file.write_text("not-an-email\n")
    args = _args(tmp_path, input_file=input_file)
    assert run(args) == EXIT_USAGE_ERROR


def test_run_success(monkeypatch, tmp_path: Path):
    breach = Breach(
        title="Example",
        domain="example.com",
        breach_date="2020-01-01",
        is_verified=True,
        pwn_count=1,
        data_classes=("Email addresses",),
        description="desc",
    )
    client = MagicMock()
    client.check_email.side_effect = [[breach], []]
    monkeypatch.setattr("email_breach_checker.cli.HibpClient", lambda api_key: client)
    monkeypatch.setattr("email_breach_checker.cli.time.sleep", lambda _: None)

    args = _args(tmp_path)
    assert run(args) == EXIT_SUCCESS

    with open(args.output, newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert len(rows) == 3


def test_run_records_failures(monkeypatch, tmp_path: Path):
    from email_breach_checker.hibp import HibpError

    client = MagicMock()
    client.check_email.side_effect = HibpError("HTTP 500")
    monkeypatch.setattr("email_breach_checker.cli.HibpClient", lambda api_key: client)
    monkeypatch.setattr("email_breach_checker.cli.time.sleep", lambda _: None)

    args = _args(tmp_path)
    assert run(args) == EXIT_RUNTIME_ERROR
    assert "HTTP 500" in args.failed_log.read_text(encoding="utf-8")
