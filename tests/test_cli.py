import os
import sys
import types

# Stub external packages so the module can be imported without them installed
sys.modules.setdefault("requests", types.ModuleType("requests"))
colorama_stub = types.ModuleType("colorama")
colorama_stub.Fore = types.SimpleNamespace(RED="", WHITE="", YELLOW="", GREEN="", MAGENTA="", CYAN="", BLUE="")
colorama_stub.init = lambda autoreset=True: None
sys.modules.setdefault("colorama", colorama_stub)
sys.modules.setdefault("dotenv", types.ModuleType("dotenv"))
dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda: None
sys.modules["dotenv"] = dotenv_stub


from email_breach_checker.cli import extract_emails_from_csv, load_api_key

def test_extract_emails_from_csv(tmp_path):
    data = "foo@example.com,invalid\nbar@test.org"
    csv_file = tmp_path / "emails.csv"
    csv_file.write_text(data)
    emails = extract_emails_from_csv(csv_file)
    assert set(emails) == {"foo@example.com", "bar@test.org"}


def test_load_api_key(monkeypatch):
    monkeypatch.setenv("HIBP_API_KEY", "dummy")
    assert load_api_key() == "dummy"
    monkeypatch.delenv("HIBP_API_KEY", raising=False)
