"""
Job Search Agent v2 — Multi-Source Deep Search
Sources: Naukri · LinkedIn · Indeed India · Google Jobs
Sends daily digest via Telegram Bot.
"""

import requests
import os
import re
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────────
SERPAPI_KEY      = os.getenv("SERPAPI_KEY", "YOUR_SERPAPI_KEY_HERE")
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID_HERE")

# ─── PROFILE (edit this section to customise for anyone) ─────────────────────
PROFILE = {
    "name":        "Mano",
    "role":        ".NET + React Full Stack Developer",
    "location":    "Bangalore, Karnataka, India",
    "min_lpa":     7,
    "max_lpa":     10,
    "exp_min":     2,
    "exp_max":     5,
    "max_jobs":    10,          # max jobs to send per digest
    "date_filter": "3days",     # how recent: 1day / 3days / week / month
}

# Search queries run on EVERY source
SEARCH_QUERIES = [
    ".NET React Full Stack Developer Bangalore",
    "C# ASP.NET Core React TypeScript Developer Bangalore",
    "Dotnet Full Stack Software Engineer Bangalore",
    "React TypeScript .NET Web API Developer Bangalore",
    "Full Stack Developer C# React Bangalore 2 3 years",
]

# ─── FILTERS ─────────────────────────────────────────────────────────────────
MUST_HAVE_ANY = [".net", "dotnet", "dot net", "c#", "asp.net", "asp net"]
FRONTEND_ANY  = ["react", "reactjs", "typescript", "frontend", "front-end",
                 "full stack", "fullstack", "full-stack"]
EXCLUDE_TITLES = [
    "senior", "lead", "architect", "manager", "principal", "staff",
    "head", "director", "vp ", "healthcare", "hipaa", "data scientist",
    "devops", "qa ", "test ", "testing", "intern", "trainee"
]
SKIP_PHRASES = [
    "immediate joiner", "immediate joining",
    "notice period: 0", "0 days notice", "no notice period"
]

# ─── SERPAPI SOURCES ─────────────────────────────────────────────────────────
# Each source: (engine_name, display_label, extra_params)
SOURCES = [
    (
        "google_jobs",
        "Google Jobs",
        {
            "location": PROFILE["location"],
            "hl": "en",
            "gl": "in",
            "chips": f"date_posted:{PROFILE['date_filter']}",
        }
    ),
    (
        "linkedin_jobs",
        "LinkedIn",
        {
            "location": "Bangalore, Karnataka, India",
            "date_posted": PROFILE["date_filter"],   # 1day / 1week / 1month
            "job_type":   "full_time",
            "experience": "2,3",                     # mid-level
            "sort_by":    "date",
        }
    ),
    (
        "indeed_jobs",
        "Indeed",
        {
            "location": "Bangalore, Karnataka",
            "country":  "in",
            "fromage":  "3",       # days — Indeed uses fromage param
            "sort":     "date",
        }
    ),
    (
        "naukri_jobs",          # SerpAPI Naukri engine
        "Naukri",
        {
            "location": "Bangalore",
            "experience": f"{PROFILE['exp_min']},{PROFILE['exp_max']}",
        }
    ),
]

# ─── JOB SEARCH ──────────────────────────────────────────────────────────────

def _jobs_key(engine):
    """Different SerpAPI engines use different result keys."""
    return {
        "google_jobs":   "jobs_results",
        "linkedin_jobs": "jobs",
        "indeed_jobs":   "jobs",
        "naukri_jobs":   "jobs",
    }.get(engine, "jobs_results")


def _normalise(job, source_label):
    """Normalise a job dict from any engine into a common schema."""
    # Each engine uses slightly different field names
    title   = (job.get("title") or job.get("job_title") or "").strip()
    company = (job.get("company_name") or job.get("company") or "").strip()
    location= (job.get("location") or job.get("job_location") or PROFILE["location"]).strip()
    description = (
        job.get("description") or
        job.get("job_description") or
        job.get("snippet") or ""
    ).strip()

    # Salary — lives in different places per engine
    exts   = job.get("detected_extensions") or {}
    salary = (
        exts.get("salary") or
        job.get("salary") or
        job.get("salary_info", {}).get("salary") if isinstance(job.get("salary_info"), dict) else None or
        ""
    )

    posted = (
        exts.get("posted_at") or
        job.get("date") or
        job.get("job_age") or
        ""
    )

    # Apply link
    links = job.get("apply_options") or []
    apply_link = ""
    if links:
        apply_link = links[0].get("link", "")
    if not apply_link:
        apply_link = job.get("job_link") or job.get("link") or ""

    return {
        "title":       title,
        "company":     company,
        "location":    location,
        "description": description,
        "salary":      salary,
        "posted":      posted,
        "apply_link":  apply_link,
        "source":      source_label,
    }


def search_source(engine, label, extra_params, query):
    """Query one SerpAPI engine with one search term."""
    try:
        params = {
            "engine":  engine,
            "q":       query,
            "api_key": SERPAPI_KEY,
        }
        params.update(extra_params)

        resp = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=20
        )
        resp.raise_for_status()
        raw = resp.json().get(_jobs_key(engine), [])
        return [_normalise(j, label) for j in raw]

    except Exception as e:
        print(f"   ⚠️  [{label}] Error: {e}")
        return []


def search_all_sources():
    """Run every query across every source with a small delay to avoid rate-limits."""
    all_jobs = []
    total_calls = 0

    for engine, label, extra in SOURCES:
        print(f"\n{'─'*40}")
        print(f"📡 Source: {label}")
        for query in SEARCH_QUERIES:
            print(f"   🔍 {query}")
            jobs = search_source(engine, label, extra, query)
            print(f"      → {len(jobs)} results")
            all_jobs.extend(jobs)
            total_calls += 1
            time.sleep(0.5)   # be polite to the API

    print(f"\n📦 Total raw results across all sources: {len(all_jobs)}")
    print(f"   (API calls made: {total_calls})")
    return all_jobs


# ─── FILTERS ─────────────────────────────────────────────────────────────────

def extract_lpa(text):
    """Parse salary text → (min_lpa, max_lpa) or None."""
    if not text:
        return None
    text = str(text).lower().replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac|l\b)", text)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac|l\b)", text)
    if m:
        v = float(m.group(1))
        return v, v
    # Handle "₹X - ₹Y" or "INR X" style
    m = re.search(r"(?:₹|inr\s*)(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:to|-|–)\s*(?:₹|inr\s*)(\d+(?:,\d+)*(?:\.\d+)?)", text)
    if m:
        lo = float(m.group(1).replace(",", ""))
        hi = float(m.group(2).replace(",", ""))
        # If values are > 100 they're probably monthly — convert to annual LPA
        if lo > 100:
            lo = round(lo * 12 / 100000, 1)
            hi = round(hi * 12 / 100000, 1)
        return lo, hi
    return None


def salary_ok(salary_text):
    if not salary_text:
        return True
    result = extract_lpa(salary_text)
    if not result:
        return True
    lo, hi = result
    return lo <= PROFILE["max_lpa"] and hi >= PROFILE["min_lpa"]


def is_relevant(job):
    title       = job["title"].lower()
    description = job["description"].lower()
    salary      = job["salary"]
    combined    = title + " " + description

    if not any(kw in combined for kw in MUST_HAVE_ANY):
        return False
    if not any(kw in combined for kw in FRONTEND_ANY):
        return False
    if any(kw in title for kw in EXCLUDE_TITLES):
        return False
    if any(phrase in combined for phrase in SKIP_PHRASES):
        return False
    if not salary_ok(salary):
        return False
    return True


def deduplicate(jobs):
    """Deduplicate by (title, company) — case-insensitive."""
    seen, unique = set(), []
    for job in jobs:
        key = (job["title"].lower().strip(), job["company"].lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique


def collect_jobs():
    raw      = search_all_sources()
    filtered = [j for j in raw if is_relevant(j)]
    print(f"✅ After filter: {len(filtered)}")
    unique   = deduplicate(filtered)
    print(f"🧹 After dedup:  {len(unique)}")
    # Sort: prefer jobs with salary disclosed first
    unique.sort(key=lambda j: (0 if j["salary"] else 1))
    return unique[:PROFILE["max_jobs"]]


# ─── SOURCE ICON MAP ─────────────────────────────────────────────────────────
SOURCE_ICON = {
    "LinkedIn":   "🔵",
    "Naukri":     "🟠",
    "Indeed":     "🟣",
    "Google Jobs":"🔴",
}

# ─── TELEGRAM MESSAGE ─────────────────────────────────────────────────────────

def format_job(index, job):
    icon  = SOURCE_ICON.get(job["source"], "📋")
    lines = [f"<b>{index}. {job['title']}</b>  {icon} {job['source']}"]
    lines.append(f"🏢 {job['company']}")
    lines.append(f"📍 {job['location']}")
    lines.append(f"💰 {job['salary'] or 'Salary not disclosed'}")
    if job["posted"]:
        lines.append(f"🕐 {job['posted']}")
    if job["apply_link"]:
        lines.append(f'🔗 <a href="{job["apply_link"]}">Apply Now</a>')
    return "\n".join(lines)


def build_message(jobs):
    today = datetime.now().strftime("%d %b %Y, %I:%M %p")
    p = PROFILE

    header = (
        f"🚀 <b>Daily Job Digest — {p['name']}</b>\n"
        f"📅 {today}\n"
        f"🎯 .NET + React | Bangalore | {p['min_lpa']}–{p['max_lpa']} LPA | {p['exp_min']}–{p['exp_max']} yrs\n"
        f"📡 Sources: LinkedIn · Naukri · Indeed · Google Jobs\n"
        f"{'─' * 30}"
    )

    if not jobs:
        return (
            f"{header}\n\n"
            "😔 No new matching jobs found today across all portals.\n\n"
            "Try searching manually:\n"
            '🔗 <a href="https://www.naukri.com/dotnet-react-jobs-in-bangalore">Naukri</a>  |  '
            '<a href="https://in.linkedin.com/jobs/dotnet-developer-jobs-bengaluru">LinkedIn</a>  |  '
            '<a href="https://www.indeed.co.in/jobs?q=dotnet+react&l=Bangalore">Indeed</a>'
        )

    # Group by source for the summary line
    from collections import Counter
    src_count = Counter(j["source"] for j in jobs)
    src_summary = "  ".join(f"{SOURCE_ICON.get(k,'📋')} {k}: {v}" for k, v in src_count.items())

    job_blocks = [format_job(i + 1, job) for i, job in enumerate(jobs)]

    footer = (
        f"{'─' * 30}\n"
        f"{src_summary}\n\n"
        f"🔎 Search more manually:\n"
        f'• <a href="https://www.naukri.com/dotnet-react-jobs-in-bangalore">Naukri — .NET React BLR</a>\n'
        f'• <a href="https://in.linkedin.com/jobs/dotnet-developer-jobs-bengaluru">LinkedIn — Dotnet BLR</a>\n'
        f'• <a href="https://www.indeed.co.in/jobs?q=dotnet+react&l=Bangalore">Indeed — Dotnet React BLR</a>\n'
        f'• <a href="https://cutshort.io/jobs/dotnet-jobs-in-bangalore">Cutshort — Product Cos</a>\n\n'
        f"<i>🤖 Job Agent v2 | {len(jobs)} jobs today | Multi-source</i>"
    )

    return header + "\n\n" + "\n\n".join(job_blocks) + "\n\n" + footer


# ─── TELEGRAM SEND (split if > 4096 chars) ───────────────────────────────────

def _send_one(text):
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id":                 TELEGRAM_CHAT_ID,
            "text":                    text,
            "parse_mode":              "HTML",
            "disable_web_page_preview": False,
        },
        timeout=15
    )
    data = resp.json()
    if not data.get("ok"):
        print(f"   ❌ Telegram error: {data.get('description')}")
        return False
    return True


def send_telegram(message):
    """Send message, splitting into chunks if it exceeds Telegram's 4096-char limit."""
    print("\n📲 Sending Telegram message...")
    MAX = 4000  # leave buffer

    if len(message) <= MAX:
        ok = _send_one(message)
    else:
        # Split on double newline (job blocks) to avoid breaking HTML tags
        chunks, current = [], ""
        for block in message.split("\n\n"):
            candidate = current + "\n\n" + block if current else block
            if len(candidate) > MAX:
                if current:
                    _send_one(current)
                    time.sleep(0.5)
                current = block
            else:
                current = candidate
        if current:
            ok = _send_one(current)

    if ok:
        print("✅ Telegram message sent!")
    return ok


# ─── SETUP HELPER ─────────────────────────────────────────────────────────────

def get_chat_id():
    """Print your Telegram chat ID — run once during setup."""
    print("Fetching Chat ID from recent bot messages...")
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
            timeout=10
        )
        updates = resp.json().get("result", [])
        if not updates:
            print("❌ No messages found.")
            print("   → Open Telegram, find your bot, send it any message, then run this again.")
            return
        for update in updates:
            msg  = update.get("message", {})
            chat = msg.get("chat", {})
            cid  = chat.get("id")
            name = f"{chat.get('first_name','')} {chat.get('last_name','')}".strip()
            print(f"✅ Chat ID: {cid}  ({name})")
            print(f"   Add to .env:  TELEGRAM_CHAT_ID={cid}")
            return cid
    except Exception as e:
        print(f"❌ Error: {e}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def run():
    print("=" * 52)
    print("  Job Search Agent v2 — Multi-Source Edition")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 52)

    if any("YOUR_" in v for v in [SERPAPI_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        print("\n❌ ERROR: Fill in your API keys in .env first.")
        print("   → Get SerpAPI key:  https://serpapi.com")
        print("   → Create bot:       https://t.me/BotFather")
        print("   → Get Chat ID:      python job_agent.py --setup\n")
        return

    jobs    = collect_jobs()
    message = build_message(jobs)

    print("\n📝 Message preview:")
    print("─" * 40)
    print(message[:800] + ("..." if len(message) > 800 else ""))
    print("─" * 40)

    send_telegram(message)
    print("\n✅ Done.\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        get_chat_id()
    else:
        run()
