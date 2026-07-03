"""Have I Been Pwned API client."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests

API_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/"
DEFAULT_TIMEOUT = 10.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RATE_LIMIT_DELAY = 6.0


class HibpError(Exception):
    """Base exception for HIBP API errors."""


class RateLimitExceeded(HibpError):
    """Raised when rate limit retries are exhausted."""


@dataclass(frozen=True)
class Breach:
    """A single breach record returned by the HIBP API."""

    title: str
    domain: str
    breach_date: str
    is_verified: bool
    pwn_count: int
    data_classes: tuple[str, ...]
    description: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Breach:
        raw_classes = data.get("DataClasses") or []
        return cls(
            title=str(data.get("Title", "")),
            domain=str(data.get("Domain", "")),
            breach_date=str(data.get("BreachDate", "")),
            is_verified=bool(data.get("IsVerified", False)),
            pwn_count=int(data.get("PwnCount", 0)),
            data_classes=tuple(str(dc) for dc in raw_classes),
            description=str(data.get("Description", "")),
        )


class HibpClient:
    """Client for the HIBP breachedaccount endpoint."""

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "hibp-api-key": api_key,
                "user-agent": "EmailBreachChecker",
            }
        )

    def check_email(self, email: str) -> list[Breach]:
        """Return breach records for an email address.

        Returns an empty list when the account has no known breaches (HTTP 404).
        Raises RateLimitExceeded when retries are exhausted on HTTP 429.
        Raises HibpError for other HTTP or connection failures.
        """
        encoded_email = quote(email, safe="")
        url = f"{API_URL}{encoded_email}"
        params = {"truncateResponse": "false"}

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                raise HibpError(f"Connection error: {exc}") from exc

            if response.status_code == 200:
                payload = response.json()
                if not isinstance(payload, list):
                    raise HibpError("Unexpected API response format")
                return [Breach.from_dict(item) for item in payload]

            if response.status_code == 404:
                return []

            if response.status_code == 429:
                retry_after = self._parse_retry_after(response)
                if attempt + 1 >= self.max_retries:
                    raise RateLimitExceeded(
                        f"Rate limit exceeded after {self.max_retries} attempts"
                    )
                time.sleep(retry_after)
                continue

            raise HibpError(
                f"HTTP {response.status_code}: {response.text.strip()[:200]}"
            )

        raise RateLimitExceeded(f"Rate limit exceeded after {self.max_retries} attempts")

    @staticmethod
    def _parse_retry_after(response: requests.Response) -> float:
        header = response.headers.get("Retry-After")
        if header is not None:
            try:
                return float(header)
            except ValueError:
                pass
        return DEFAULT_RATE_LIMIT_DELAY
