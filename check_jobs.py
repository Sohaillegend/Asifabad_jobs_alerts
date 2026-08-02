import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ==========================
# CONFIGURATION
# ==========================

HOME_URL = "https://asifabad.telangana.gov.in/"
RECRUITMENT_URL = "https://asifabad.telangana.gov.in/notice_category/recruitment/"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/127.0 Safari/537.36"
    )
}

SEEN_FILE = "seen_jobs.json"

KEYWORDS = [
    "computer operator",
    "data entry",
    "deo",
    "medical college",
    "gmc",
    "outsourcing",
    "collector",
    "collectorate",
    "agriculture",
    "assistant",
    "nhm",
    "recruitment",
    "walk in",
    "walk-in",
    "notification",
    "staff",
    "lab technician",
    "office",
]

# ==========================
# LOAD SAVED JOBS
# ==========================

def load_seen():

    if not os.path.exists(SEEN_FILE):
        return []

    try:

        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return []


def save_seen(data):

    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ==========================
# SEND TELEGRAM MESSAGE
# ==========================

def send_message(message):

    if not BOT_TOKEN or not CHAT_ID:
        print("BOT_TOKEN or CHAT_ID missing")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        requests.post(url, data=payload, timeout=30)

    except Exception as e:
        print(e)


# ==========================
# DOWNLOAD PAGE
# ==========================

def get_page(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        return BeautifulSoup(response.text, "html.parser")

    except Exception as e:

        print("Error:", e)

        return None
      # ==========================
# PARSE NOTICE CARDS
# ==========================

def clean_text(text):
    if not text:
        return ""
    return " ".join(text.strip().split())


def is_job_related(title):

    title = title.lower()

    for word in KEYWORDS:
        if word in title:
            return True

    return False


def absolute_link(link):

    if not link:
        return ""

    if link.startswith("http"):
        return link

    if link.startswith("/"):
        return "https://asifabad.telangana.gov.in" + link

    return "https://asifabad.telangana.gov.in/" + link


def parse_all_links(soup, source):

    jobs = []

    links = soup.find_all("a")

    for a in links:

        title = clean_text(a.get_text())

        href = absolute_link(a.get("href", ""))

        if len(title) < 10:
            continue

        if href == "":
            continue

        if is_job_related(title):

            jobs.append({
                "title": title,
                "link": href,
                "source": source,
                "date": datetime.now().strftime("%d-%m-%Y")
            })

    return jobs


# ==========================
# READ BOTH PAGES
# ==========================

# ==========================
# COLLECT ALL NOTICES
# ==========================

def collect_jobs():

    jobs = []

    home = get_page(HOME_URL)

    if home:

        ticker = home.find("div", class_="news-ticker-horizontal")

        if ticker:

            for li in ticker.find_all("li"):

                a = li.find("a")

                if not a:
                    continue

                title = clean_text(a.get_text())

                if len(title) < 8:
                    continue

                href = absolute_link(a.get("href", ""))

                jobs.append({

                    "title": title,

                    "link": href,

                    "source": "Latest News",

                    "date": datetime.now().strftime("%d-%m-%Y")

                })

    recruit = get_page(RECRUITMENT_URL)

    if recruit:

        for a in recruit.find_all("a"):

            title = clean_text(a.get_text())

            href = absolute_link(a.get("href", ""))

            if len(title) < 10:
                continue

            jobs.append({

                "title": title,

                "link": href,

                "source": "Recruitment",

                "date": datetime.now().strftime("%d-%m-%Y")

            })

    unique = {}

    for job in jobs:
        unique[job["title"]] = job

    return list(unique.values())
  # ==========================
# CHECK FOR NEW JOBS
# ==========================

def check_for_new_jobs():

    seen = load_seen()

    seen_links = set()

    for item in seen:

        if "link" in item:
            seen_links.add(item["link"])

    jobs = collect_jobs()

    print(f"Found {len(jobs)} possible notices")

    new_jobs = []

    for job in jobs:

        if job["link"] not in seen_links:

            new_jobs.append(job)

            seen.append(job)

    if len(new_jobs) == 0:

        print("No new jobs found.")

    else:

        print(f"Found {len(new_jobs)} NEW notices")

        for job in new_jobs:

            message = f"""
🔔 <b>NEW GOVERNMENT NOTICE</b>

📄 <b>Title:</b>
{job['title']}

🏢 <b>Source:</b>
{job['source']}

📅 <b>Date Checked:</b>
{job['date']}

🔗 <b>Link:</b>

{job['link']}
"""

            send_message(message)

    save_seen(seen)


# ==========================
# MAIN
# ==========================

if __name__ == "__main__":

    print("=" * 40)
    print("ASIFABAD JOB ALERT BOT")
    print("=" * 40)

    check_for_new_jobs()

    print("Finished.")
