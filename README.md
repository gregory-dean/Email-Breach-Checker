# Email Breach Checker

Check email addresses from a file against the [Have I Been Pwned](https://haveibeenpwned.com/) API and write grouped summary results to CSV.

## Requirements

- Python 3.10+
- Internet connection
- HIBP API key ([request one here](https://haveibeenpwned.com/API/Key))

## Installation

```bash
pip install .
```

For development:

```bash
pip install -e ".[dev]"
```

## Configuration

Set your API key via environment variable or `.env` file:

```bash
export HIBP_API_KEY=your_api_key
```

Or copy `.env.example` to `.env` and edit it.

## Usage

```bash
email-breach-checker INPUT_FILE [options]
```

Arguments:

| Option | Description | Default |
|--------|-------------|---------|
| `INPUT_FILE` | Path to `.txt` or `.csv` file with emails | required |
| `--output PATH` | Summary CSV destination | `results.csv` |
| `--failed-log PATH` | Log file for failed lookups | `failed_emails.log` |
| `--delay SECONDS` | Pause between requests | `6.0` |
| `--api-key KEY` | Override `HIBP_API_KEY` | from env |
| `--quiet` | Suppress per-email progress lines | off |
| `--version` | Print version and exit | |
| `--help` | Show help and exit | |

Example:

```bash
email-breach-checker examples/emails.txt --output results.csv
```

You can also run as a module:

```bash
python -m email_breach_checker examples/emails.txt
```

## Input Formats

**Text (`.txt`)**: one email address per line.

**CSV (`.csv`)**: emails are extracted from all cells using pattern matching. Duplicates are removed.

See [examples/emails.txt](examples/emails.txt) for a sample text input file.

## Output

The summary CSV contains one row per email with breach count, titles, domains, dates, verification status, pwn counts, compromised data types, and truncated descriptions.

Failed lookups are appended to the failed-log file with the HTTP status and error detail.

Exit codes:

| Code | Meaning |
|------|---------|
| `0` | All lookups succeeded |
| `1` | One or more lookups failed |
| `2` | Usage error (missing file, invalid arguments, missing API key) |

## Development

Run tests and lint:

```bash
pytest
ruff check src tests
```

## License

MIT. See [LICENSE](LICENSE).
