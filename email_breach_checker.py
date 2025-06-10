\
import os
import re
import csv
import time
import requests
import socket
from pathlib import Path
from typing import List
from colorama import Fore, init
init(autoreset=True)

# Configuration
API_KEY = 'API key here'
API_URL = 'https://haveibeenpwned.com/api/v3/breachedaccount/'
HEADERS = {
    'hibp-api-key': API_KEY,
    'user-agent': 'EmailBreachChecker'
}

OUTPUT_DIR = Path("output")
SUMMARY_OUTPUT = OUTPUT_DIR / 'summary_results.csv'
FAILED_LOG = OUTPUT_DIR / 'failed_emails.log'
EMAIL_REGEX = re.compile(r"[^@ \n\r\t]+@[^@ \n\r\t]+\.[^@ \n\r\t]+")

ascii_header = """
'########:'########:::'######::
 ##.....:: ##.... ##:'##... ##:
 ##::::::: ##:::: ##: ##:::..::
 ######::: ########:: ##:::::::
 ##...:::: ##.... ##: ##:::::::
 ##::::::: ##:::: ##: ##::: ##:
 ########: ########::. ######::
........::........::::......:::  
     Email Breach Checker by X3N0
"""

def ensure_output_dir():
    OUTPUT_DIR.mkdir(exist_ok=True)

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def find_csv_files():
    dirs = [Path.home() / "Downloads", Path.home() / "Desktop"]
    return [f for d in dirs if d.exists() for f in d.glob("*.csv")]

def extract_emails_from_csv(path: Path) -> List[str]:
    emails = set()
    try:
        with open(path, newline='', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                for cell in row:
                    match = EMAIL_REGEX.search(cell)
                    if match:
                        emails.add(match.group().strip().lower())
        return list(emails)
    except Exception as e:
        print(Fore.RED + f"❌ Failed to read CSV file: {e}")
        return []

def log_failed_email(email: str, status_code: int):
    with open(FAILED_LOG, 'a') as f:
        f.write(f"{email} - HTTP {status_code}\n")

def write_grouped_summary(email: str, breaches):
    with open(SUMMARY_OUTPUT, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if breaches:
            titles = "; ".join([b['Title'] for b in breaches])
            domains = "; ".join([b['Domain'] for b in breaches])
            dates = "; ".join([b['BreachDate'] for b in breaches])
            data_classes = "; ".join(set(dc for b in breaches for dc in b['DataClasses']))
            pwn_counts = "; ".join([str(b['PwnCount']) for b in breaches])
            verified = "; ".join(['Yes' if b['IsVerified'] else 'No' for b in breaches])
            descriptions = "; ".join([b['Description'][:100] for b in breaches])
            writer.writerow([
                email, len(breaches), titles, domains, dates,
                verified, pwn_counts, data_classes, descriptions
            ])
        else:
            writer.writerow([email, 0, "", "", "", "", "", "", ""])

def check_email(email: str):
    if not API_KEY or "your_hibp_api_key_here" in API_KEY:
        print(Fore.RED + "❌ API key is missing or invalid. Please update it in the script.")
        exit(1)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{API_URL}{email}", headers=HEADERS, params={"truncateResponse": False}, timeout=10)
        except requests.RequestException as e:
            print(Fore.RED + f"❌ Connection error while checking {email}: {e}")
            log_failed_email(email, 0)
            return None

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return []
        elif response.status_code == 429:
            print(Fore.MAGENTA + f"Rate limit hit. Waiting 6 seconds... ({attempt+1}/{max_retries})")
            time.sleep(6)
        else:
            log_failed_email(email, response.status_code)
            print(Fore.RED + f"Error checking {email}: HTTP {response.status_code}")
            return None
    return None

def scan_emails(emails: List[str]):
    ensure_output_dir()
    with open(SUMMARY_OUTPUT, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Email", "Breach Count", "Breach Titles", "Domains", "Breach Dates",
            "Verified", "PwnCounts", "Compromised Data", "Descriptions"
        ])

    checked, breached, failed = 0, 0, 0

    for email in emails:
        print(Fore.WHITE + f"Checking: {email}")
        result = check_email(email)
        if result is None:
            print(Fore.RED + f"❌ Failed to check {email}")
            failed += 1
        else:
            if result:
                print(Fore.YELLOW + f"🔐 {email} found in {len(result)} breach(es)")
                breached += 1
            else:
                print(Fore.GREEN + f"✅ {email} has not been found in any breaches.")
            write_grouped_summary(email, result)
            checked += 1
        time.sleep(6)

    print(Fore.CYAN + f"\nScan complete. Checked: {checked} | Breached: {breached} | Failed: {failed}")
    print(Fore.CYAN + f"Results saved to: {SUMMARY_OUTPUT.resolve()}")

def display_menu_and_get_file():
    print(ascii_header)
    print("===[ Main Menu ]===\n")
    print("[1] Scan emails from CSV (Desktop/Downloads)")
    print("[2] Manually enter path to file")
    print("[0] Exit\n")
    choice = input("Select an option: ").strip()

    if choice == "1":
        files = find_csv_files()
        if not files:
            print(Fore.RED + "No CSV files found in Downloads or Desktop.")
            return None
        print("\nFound CSV files:")
        for i, f in enumerate(files, 1):
            print(f"[{i}] {f.name} ({f.parent.name})")
        print(f"[{len(files)+1}] Enter path manually")
        selected = input("Choose a file: ").strip()
        if selected.isdigit() and 1 <= int(selected) <= len(files):
            return files[int(selected)-1]
        else:
            return Path(input("Enter full path to CSV: ").strip())
    elif choice == "2":
        return Path(input("Enter full path to CSV: ").strip())
    elif choice == "0":
        print("Exiting.")
        exit(0)
    else:
        print("Invalid choice.")
        return None

def main():
    if not is_connected():
        print(Fore.RED + "❌ No internet connection. Please check your network and try again.")
        return

    selected_file = display_menu_and_get_file()
    if selected_file and selected_file.exists():
        if not selected_file.suffix.lower().endswith(".csv"):
            print(Fore.RED + "❌ File must be a .csv format.")
            return

        emails = extract_emails_from_csv(selected_file)
        if emails:
            print(Fore.BLUE + f"Found {len(emails)} valid unique email(s). Starting scan...")
            scan_emails(emails)
        else:
            print(Fore.RED + "⚠️ No valid email addresses found in that file.")
    else:
        print(Fore.RED + "File not found or invalid path.")

if __name__ == "__main__":
    main()
