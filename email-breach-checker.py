import requests
import time
import os
import csv
import re
from typing import List
from colorama import Fore, Style, init
init(autoreset=True)

# -------------------- Configuration --------------------
API_KEY = 'API key here'  # Replace with your real HIBP API key
API_URL = 'https://haveibeenpwned.com/api/v3/breachedaccount/'

HEADERS = {
    'hibp-api-key': API_KEY,
    'user-agent': 'EmailBreachChecker'
}

CSV_OUTPUT = 'results.csv'
FAILED_LOG = 'failed_emails.log'

# -------------------- Helper Functions --------------------

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def read_emails_from_file(filename: str) -> List[str]:
    """Reads emails from file, one per line."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def is_valid_email(email: str) -> bool:
    """Basic email format validation using regex."""
    pattern = r"[^@]+@[^@]+\.[^@]+"
    return re.fullmatch(pattern, email) is not None


def log_failed_email(email: str, status_code: int):
    """Log failed lookups with HTTP status."""
    with open(FAILED_LOG, 'a') as f:
        f.write(f"{email} - HTTP {status_code}\n")


def write_to_csv(email: str, breaches):
    """Appends result to CSV output."""
    with open(CSV_OUTPUT, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        if breaches:
            for breach in breaches:
                writer.writerow([
                    email,
                    breach['Title'],
                    breach['Domain'],
                    breach['BreachDate'],
                    'Yes' if breach['IsVerified'] else 'No',
                    breach['PwnCount'],
                    ', '.join(breach['DataClasses'])
                ])
        else:
            writer.writerow([email, "No breach found", "", "", "", "", ""])


def check_email(email: str):
    """Calls HIBP API, handles retries and logging."""
    max_retries = 3
    for attempt in range(max_retries):
        response = requests.get(f"{API_URL}{email}", headers=HEADERS, params={"truncateResponse": False})

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        elif response.status_code == 429:
            print(Fore.MAGENTA + f"⏳ Rate limit hit. Waiting 6 seconds before retrying ({attempt+1}/{max_retries})...")
            time.sleep(6)
        else:
            log_failed_email(email, response.status_code)
            print(Fore.RED + f"⚠️ Error checking {email}: HTTP {response.status_code}")
            return None
    log_failed_email(email, 429)
    return None


def display_breach_info(email: str, breaches: List[dict]):
    """Displays results on screen."""
    print(Fore.YELLOW + f"\n🔐 {email} was found in {len(breaches)} breach(es):")
    for breach in breaches:
        print(Fore.RED + f"\n--- {breach['Title']} ---")
        print(Fore.CYAN + f"  Domain      : {breach['Domain']}")
        print(f"  Date        : {breach['BreachDate']}")
        print(f"  Verified    : {'Yes' if breach['IsVerified'] else 'No'}")
        print(f"  Pwn Count   : {breach['PwnCount']:,}")
        print(f"  Compromised : {', '.join(breach['DataClasses'])}")
        print(f"  Description : {breach['Description'][:100]}...")


def main():
    clear_screen()
    print(Fore.GREEN + "📧 Email Breach Checker (Using HIBP API)")
    print("-" * 60)

    filename = input("Enter the path to the file with email list: ").strip()

    try:
        emails = read_emails_from_file(filename)
        print(Fore.BLUE + f"\n🔎 Validating and checking {len(emails)} emails...\n")

        # Create CSV file with headers
        with open(CSV_OUTPUT, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Email", "Breach", "Domain", "Date", "Verified", "PwnCount", "CompromisedData"])

        for email in emails:
            if not is_valid_email(email):
                print(Fore.RED + f"❌ Invalid email skipped: {email}")
                continue

            print(Fore.WHITE + f"Checking: {email}...")
            breaches = check_email(email)

            if breaches:
                display_breach_info(email, breaches)
            else:
                print(Fore.GREEN + f"✅ {email} has not been found in any breaches.\n")

            write_to_csv(email, breaches)
            time.sleep(6)  # Always sleep to avoid 429 errors

    except FileNotFoundError:
        print(Fore.RED + f"❌ File not found: {filename}")
    except Exception as e:
        print(Fore.RED + f"❌ Unexpected error: {e}")


if __name__ == '__main__':
    main()
