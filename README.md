# Email Breach Checker 🔐

Check if a list of email addresses has been exposed in known data breaches using the [Have I Been Pwned (HIBP) API](https://haveibeenpwned.com/). This Python script validates email formats, queries the HIBP API with proper rate-limiting, logs failures, and exports results to a CSV file for reporting or further analysis.

---

## 🚀 Features
- ✅ Email format validation (regex-based)
- ✅ API rate-limit handling (6s delay + retry on 429)
- ✅ CSV export (`results.csv`)
- ✅ Failed lookups logged to `failed_emails.log`
- ✅ Color-coded terminal output for readability
- ✅ Simple command-line interface

---

## 🛠 Requirements

- Python 3.6+
- An active HIBP API key → [Get one here](https://haveibeenpwned.com/API/Key)

Install required libraries:
```bash
pip install -r requirements.txt
