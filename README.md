# 🔐 Email Breach Checker (EBC) by X3N0

**Email Breach Checker (EBC)** is a Python-based CLI tool that checks if any emails from a `.csv` file have been exposed in known data breaches using the Have I Been Pwned (HIBP) API.

---

## 🚀 Features

- 🎨 Stylized ASCII menu interface
- 📂 Auto-searches Desktop/Downloads for `.csv` files
- ✅ Smart validation for email format and input files
- 🧠 Graceful handling of empty, invalid, or malformed CSVs
- 🧹 Skips duplicates and filters junk data
- 💾 Saves grouped summary results in `output/summary_results.csv`
- 🧱 Logs failed email lookups to `output/failed_emails.log`
- 🌐 API rate-limit friendly with built-in delay

---

## 📦 Requirements

- Python 3.6+
- Internet connection
- Free HIBP API key ([get one here](https://haveibeenpwned.com/API/Key))

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file with your API key:

```bash
echo "HIBP_API_KEY=your_hibp_api_key" > .env
```

---

## 📂 How to Use

1. Place your `.csv` file with email addresses on your **Desktop** or **Downloads**
2. Run the tool (after installing or from source):

```bash
python3 email_breach_checker_V2.py
```

3. Follow the interactive menu to select or enter your file path
4. Review scan summary in terminal and detailed results in:

```
output/summary_results.csv
```

---

## 📄 Output Format

Each email scanned will show:
- Number of breaches found
- Names and domains of breached services
- Dates and verified status
- Type of compromised data (e.g., emails, passwords)
- Truncated descriptions of each breach

---

## 🔧 Example Input

Example contents of a `.csv`:
```
test@example.com
admin@yourcompany.com
someuser@gmail.com
```

---

## ❌ Invalid Input Handling

The script is designed to:
- Skip malformed or duplicate emails
- Warn if file is empty, missing, or not `.csv`
- Handle corrupt or non-CSV files
- Retry on rate-limit (429) errors
- Warn on internet/API key issues

---

## 📁 Files

| File | Description |
|------|-------------|
| `email_breach_checker/cli.py` | CLI implementation |
| `requirements.txt` | List of required packages |
| `emails.txt` | Example email list |
| `email_breach_checker_V2.py` | Updated standalone script |
| `README.md` | This file |
| `setup.py` | Packaging script |
| `output/summary_results.csv` | Results after scan |
| `output/failed_emails.log` | Emails that failed to process |

---

## 📦 Building a Debian Package

You can create a `.deb` package using `stdeb`:

```bash
pip install stdeb
python3 setup.py --command-packages=stdeb.command bdist_deb
```

The resulting package will be placed in the `deb_dist/` directory.

