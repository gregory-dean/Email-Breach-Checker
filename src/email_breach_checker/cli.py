"""Command-line interface for the email breach checker."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from email_breach_checker import __version__
from email_breach_checker.hibp import (
    DEFAULT_RATE_LIMIT_DELAY,
    HibpClient,
    HibpError,
    RateLimitExceeded,
)
from email_breach_checker.output import init_summary_csv, log_failed_lookup, write_summary_row
from email_breach_checker.parsing import load_emails

EXIT_SUCCESS = 0
EXIT_RUNTIME_ERROR = 1
EXIT_USAGE_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="email-breach-checker",
        description="Check email addresses against the Have I Been Pwned API.",
    )
    parser.add_argument("input_file", type=Path, help="Path to a .txt or .csv file with emails")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results.csv"),
        help="Summary CSV destination (default: results.csv)",
    )
    parser.add_argument(
        "--failed-log",
        type=Path,
        default=Path("failed_emails.log"),
        help="Log file for failed lookups (default: failed_emails.log)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_RATE_LIMIT_DELAY,
        help=f"Pause between requests in seconds (default: {DEFAULT_RATE_LIMIT_DELAY})",
    )
    parser.add_argument(
        "--api-key",
        help="HIBP API key (overrides HIBP_API_KEY environment variable)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-email progress lines",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def resolve_api_key(cli_key: str | None) -> str:
    load_dotenv()
    return cli_key or os.getenv("HIBP_API_KEY", "")


def run(args: argparse.Namespace) -> int:
    if not args.input_file.exists():
        print(f"error: input file not found: {args.input_file}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print(
            "error: HIBP API key is required. Set HIBP_API_KEY or pass --api-key.",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    if args.delay < 0:
        print("error: --delay must be zero or positive", file=sys.stderr)
        return EXIT_USAGE_ERROR

    try:
        emails, skipped = load_emails(args.input_file)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE_ERROR
    except OSError as exc:
        print(f"error: failed to read input file: {exc}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    if skipped:
        print(f"warning: skipped {len(skipped)} invalid email(s)", file=sys.stderr)

    if not emails:
        print("error: no valid email addresses found in input file", file=sys.stderr)
        return EXIT_USAGE_ERROR

    client = HibpClient(api_key)
    init_summary_csv(args.output)

    checked = 0
    breached = 0
    clean = 0
    failed = 0

    for index, email in enumerate(emails):
        if not args.quiet:
            print(f"checking: {email}", file=sys.stderr)

        try:
            breaches = client.check_email(email)
        except RateLimitExceeded as exc:
            log_failed_lookup(args.failed_log, email, 429, str(exc))
            print(f"error: {email}: {exc}", file=sys.stderr)
            failed += 1
        except HibpError as exc:
            log_failed_lookup(args.failed_log, email, 0, str(exc))
            print(f"error: {email}: {exc}", file=sys.stderr)
            failed += 1
        else:
            write_summary_row(args.output, email, breaches)
            checked += 1
            if breaches:
                breached += 1
                if not args.quiet:
                    print(
                        f"result: {email} found in {len(breaches)} breach(es)",
                        file=sys.stderr,
                    )
            else:
                clean += 1
                if not args.quiet:
                    print(f"result: {email} not found in any breaches", file=sys.stderr)

        if index + 1 < len(emails):
            time.sleep(args.delay)

    print(
        f"scan complete: checked={checked} breached={breached} clean={clean} failed={failed}",
        file=sys.stderr,
    )
    print(f"results saved to: {args.output.resolve()}", file=sys.stderr)

    return EXIT_RUNTIME_ERROR if failed else EXIT_SUCCESS


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(run(args))
