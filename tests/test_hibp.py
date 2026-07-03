from unittest.mock import MagicMock

import pytest
import requests

from email_breach_checker.hibp import Breach, HibpClient, HibpError, RateLimitExceeded


def _response(status_code: int, payload=None, headers=None, text=""):
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}
    response.text = text
    if payload is not None:
        response.json.return_value = payload
    return response


def test_breach_from_dict_defaults():
    breach = Breach.from_dict({})
    assert breach.title == ""
    assert breach.domain == ""
    assert breach.pwn_count == 0
    assert breach.data_classes == ()


def test_check_email_success():
    session = MagicMock()
    session.headers = {}
    session.get.return_value = _response(
        200,
        [
            {
                "Title": "Example",
                "Domain": "example.com",
                "BreachDate": "2020-01-01",
                "IsVerified": True,
                "PwnCount": 100,
                "DataClasses": ["Email addresses"],
                "Description": "Test breach",
            }
        ],
    )
    client = HibpClient("test-key", session=session)
    breaches = client.check_email("user@example.com")
    assert len(breaches) == 1
    assert breaches[0].title == "Example"
    session.get.assert_called_once()
    called_url = session.get.call_args.args[0]
    assert "user%40example.com" in called_url


def test_check_email_not_found():
    session = MagicMock()
    session.headers = {}
    session.get.return_value = _response(404)
    client = HibpClient("test-key", session=session)
    assert client.check_email("user@example.com") == []


def test_check_email_url_encodes_special_characters():
    session = MagicMock()
    session.headers = {}
    session.get.return_value = _response(404)
    client = HibpClient("test-key", session=session)
    client.check_email("user+tag@example.com")
    called_url = session.get.call_args.args[0]
    assert "user%2Btag%40example.com" in called_url


def test_check_email_retries_on_rate_limit(monkeypatch):
    session = MagicMock()
    session.headers = {}
    session.get.side_effect = [
        _response(429, headers={"Retry-After": "1"}),
        _response(404),
    ]
    sleeps: list[float] = []

    def record_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("email_breach_checker.hibp.time.sleep", record_sleep)
    client = HibpClient("test-key", session=session, max_retries=3)
    assert client.check_email("user@example.com") == []
    assert sleeps == [1.0]


def test_check_email_rate_limit_exhausted():
    session = MagicMock()
    session.headers = {}
    session.get.return_value = _response(429, headers={"Retry-After": "2"})
    client = HibpClient("test-key", session=session, max_retries=1)
    with pytest.raises(RateLimitExceeded):
        client.check_email("user@example.com")


def test_check_email_http_error():
    session = MagicMock()
    session.headers = {}
    session.get.return_value = _response(500, text="server error")
    client = HibpClient("test-key", session=session)
    with pytest.raises(HibpError, match="HTTP 500"):
        client.check_email("user@example.com")


def test_check_email_connection_error():
    session = MagicMock()
    session.headers = {}
    session.get.side_effect = requests.RequestException("timeout")
    client = HibpClient("test-key", session=session)
    with pytest.raises(HibpError, match="Connection error"):
        client.check_email("user@example.com")


def test_check_email_invalid_payload():
    session = MagicMock()
    session.headers = {}
    session.get.return_value = _response(200, payload={"not": "a list"})
    client = HibpClient("test-key", session=session)
    with pytest.raises(HibpError, match="Unexpected API response format"):
        client.check_email("user@example.com")
