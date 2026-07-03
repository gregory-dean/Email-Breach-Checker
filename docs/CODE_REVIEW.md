# Code Review Guide

This document is a structured review checklist for the Email Breach Checker project. It is written so automated or lower-capability models can perform consistent code reviews on this repository or its pull requests.

## Project Purpose

Batch-check email addresses from a `.txt` or `.csv` file against the Have I Been Pwned (HIBP) `breachedaccount` API. Write grouped per-email results to a summary CSV and log failed lookups separately.

## Project Conventions

Verify these rules across the codebase:

| Rule | How to verify |
|------|---------------|
| No emojis in code, docs, or CLI output | Search for Unicode emoji ranges; inspect `print` calls |
| No decorative output (ASCII art, colors, banners) | No `colorama`; no banner strings in `cli.py` |
| Library modules never print or call `sys.exit` | `hibp.py`, `parsing.py`, `output.py` must be side-effect free except file I/O in `output.py` |
| All HTTP calls use a timeout | `HibpClient` passes `timeout=` to `session.get` |
| User-facing errors are single-line and actionable | Messages in `cli.py` start with `error:` or `warning:` |
| Public functions have type hints | Check `src/email_breach_checker/*.py` |
| Email addresses are URL-encoded before API requests | `quote(email, safe="")` in `hibp.py` |
| Rate-limit handling honors `Retry-After` | `_parse_retry_after` in `hibp.py` |
| API key loaded at runtime, not import time | `resolve_api_key` called inside `run()`, not at module level |
| Tests do not stub dependencies via `sys.modules` hacks | `tests/` import real package modules |

## Repository Layout

```
src/email_breach_checker/
  __init__.py    version string only
  __main__.py    module entry point
  cli.py         argparse, orchestration, exit codes
  hibp.py        API client
  parsing.py     input file parsing
  output.py      CSV and log writers
tests/           unit tests per module
docs/            this file
examples/        sample input files
```

There must be only one implementation. Legacy standalone scripts (`email-breach-checker.py`, `email_breach_checker_V2.py`) must not exist.

## Per-Module Checklists

### `src/email_breach_checker/cli.py`

**Owns:** argument parsing, API key resolution, scan orchestration, progress output, exit codes.

**Must not:** contain HTTP logic, CSV formatting, or email regex parsing.

Checklist:

- [ ] `build_parser()` defines `input_file`, `--output`, `--failed-log`, `--delay`, `--api-key`, `--quiet`, `--version`
- [ ] Missing input file returns exit code `2`
- [ ] Missing API key returns exit code `2` with a single error message
- [ ] Unsupported or empty input returns exit code `2`
- [ ] Any failed lookup returns exit code `1`; all success returns `0`
- [ ] Progress and summary lines go to `stderr`
- [ ] `--delay` sleep runs between requests, not after the last one
- [ ] No interactive menus, no `input()` prompts

### `src/email_breach_checker/hibp.py`

**Owns:** HIBP API communication, retry logic, breach record parsing.

**Must not:** print, write files, read environment variables, or call `sys.exit`.

Checklist:

- [ ] `HibpClient.check_email` URL-encodes the email with `quote(email, safe="")`
- [ ] Request uses `truncateResponse=false`
- [ ] HTTP 200 returns `list[Breach]`
- [ ] HTTP 404 returns empty list (not an error)
- [ ] HTTP 429 retries up to `max_retries`, sleeping per `Retry-After` header
- [ ] Exhausted 429 raises `RateLimitExceeded`
- [ ] Other HTTP errors raise `HibpError`
- [ ] Connection failures raise `HibpError`
- [ ] `Breach.from_dict` uses `.get()` defaults (no bare `dict['key']` access)
- [ ] All requests pass `timeout=`

### `src/email_breach_checker/parsing.py`

**Owns:** reading `.txt` and `.csv` files, email validation, deduplication.

**Must not:** make HTTP calls, write output files, or print.

Checklist:

- [ ] `.txt` files read one email per line
- [ ] `.csv` files extract emails from all cells via regex
- [ ] Emails are lowercased and deduplicated
- [ ] Invalid emails collected in `skipped` list, not silently dropped without trace
- [ ] `load_emails` rejects unsupported suffixes with `ValueError`
- [ ] `is_valid_email` uses `EMAIL_REGEX.fullmatch`

### `src/email_breach_checker/output.py`

**Owns:** summary CSV initialization and row writing, failed-lookup logging.

**Must not:** make HTTP calls or parse input files.

Checklist:

- [ ] `init_summary_csv` writes the correct header row
- [ ] `write_summary_row` writes one grouped row per email (breached or clean)
- [ ] Breach fields joined with `"; "` separator
- [ ] Descriptions truncated to 100 characters
- [ ] `log_failed_lookup` creates parent directories as needed
- [ ] Output paths are passed explicitly (no hardcoded `output/` directory)

## Findings Log (Regression Checklist)

These issues existed in the pre-overhaul codebase. Confirm they are not reintroduced:

| ID | Issue | Fixed by |
|----|-------|----------|
| F1 | Duplicate implementations (`email-breach-checker.py` and packaged `cli.py`) | Single `src/` package; legacy scripts removed |
| F2 | Emojis and colorama in all output | Plain stderr messages; colorama removed |
| F3 | ASCII-art banner and interactive menu | argparse CLI with positional `INPUT_FILE` |
| F4 | Auto-scan of Desktop/Downloads for CSV files | Removed; user provides path |
| F5 | Connectivity probe to `8.8.8.8` | Removed |
| F6 | Stray `\` character at top of `cli.py` | File rewritten |
| F7 | Email not URL-encoded in API path | `quote()` in `hibp.py` |
| F8 | `sys.exit(1)` inside `check_email()` | Errors raised as exceptions; exit only in `main()` |
| F9 | API key resolved at import time | `resolve_api_key()` called in `run()` |
| F10 | `breach['Title']` KeyError risk | `Breach.from_dict` with `.get()` defaults |
| F11 | Rate limit ignores `Retry-After` header | `_parse_retry_after()` in `hibp.py` |
| F12 | README references nonexistent `email_breach_checker_V2.py` | README rewritten |
| F13 | Tests stub deps via `sys.modules` | Real imports with mocked HTTP session |
| F14 | Blanket `*.csv` in `.gitignore` blocks fixtures | Scoped ignores for output files only |

## Review Procedure

### Step 1: Read entry points

1. [src/email_breach_checker/cli.py](../src/email_breach_checker/cli.py) -- user-facing behavior
2. [pyproject.toml](../pyproject.toml) -- dependencies and entry point

### Step 2: Read library modules

3. [src/email_breach_checker/hibp.py](../src/email_breach_checker/hibp.py)
4. [src/email_breach_checker/parsing.py](../src/email_breach_checker/parsing.py)
5. [src/email_breach_checker/output.py](../src/email_breach_checker/output.py)

### Step 3: Read tests

6. [tests/test_hibp.py](../tests/test_hibp.py) -- API client behavior
7. [tests/test_parsing.py](../tests/test_parsing.py) -- input parsing
8. [tests/test_output.py](../tests/test_output.py) -- CSV and log output
9. [tests/test_cli.py](../tests/test_cli.py) -- exit codes and orchestration

### Step 4: Run automated checks

```bash
pip install -e ".[dev]"
ruff check src tests
pytest
```

Both must pass with zero errors.

### Step 5: Manual spot checks

- Confirm no legacy files exist at repo root (`email-breach-checker.py`, `setup.py`, `requirements.txt`)
- Confirm `examples/emails.txt` exists and root `emails.txt` does not
- Run `email-breach-checker --help` and verify options match this document

## Finding Report Template

When reporting a review finding, use this format:

```
File: src/email_breach_checker/<module>.py
Line: <line number or range>
Severity: critical | major | minor | nit
Rule: <convention or checklist item violated>
Description: <what is wrong>
Suggestion: <how to fix>
```

Example:

```
File: src/email_breach_checker/hibp.py
Line: 45
Severity: critical
Rule: Email addresses are URL-encoded before API requests
Description: Email is interpolated directly into the URL without encoding.
Suggestion: Use quote(email, safe="") before building the request path.
```

## Severity Guide

| Severity | Definition | Examples |
|----------|------------|----------|
| critical | Data loss, security issue, or crash in normal use | Missing URL encoding, unhandled KeyError, API key logged |
| major | Incorrect behavior or broken feature | Wrong exit code, rate limit not retried, CSV format wrong |
| minor | Maintainability or convention violation | Missing type hint, print in library module |
| nit | Style preference with no functional impact | Variable naming, comment wording |
