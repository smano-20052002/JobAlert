# Job Search Agent 🤖 — Telegram Edition
Searches .NET + React jobs in Bangalore daily and sends a Telegram digest.
Safe, free, official Telegram Bot API — end-to-end encrypted.

---

## Setup in 3 steps (~10 minutes total)

### Step 1 — Create your Telegram Bot (2 minutes, free)
1. Open Telegram and search for **@BotFather**
2. Send: `/newbot`
3. Choose a name: e.g. `Mano Job Alert`
4. Choose a username: e.g. `mano_job_alert_bot`
5. BotFather sends you a **Bot Token** — copy it (looks like `123456:ABC-DEF...`)

### Step 2 — Get your Chat ID (1 minute)
1. Search for your new bot in Telegram and send it any message (e.g. "hi")
2. Run this command:
   ```bash
   python job_agent.py --setup
   ```
3. It prints your **Chat ID** — copy it (looks like `987654321`)

### Step 3 — Configure and run
```bash
# Install dependencies
pip install -r requirements.txt

# Set up config
cp .env.example .env
# Open .env and fill in SERPAPI_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

# Run the agent
python job_agent.py
```
You'll receive a Telegram message in under 10 seconds!

---

## Schedule daily runs FREE via GitHub Actions

1. Push this folder to a **private** GitHub repository
2. Go to repo → Settings → Secrets and variables → Actions
3. Add these 3 secrets:
   - `SERPAPI_KEY`
   - `TELEGRAM_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. The workflow file `.github/workflows/daily_jobs.yml` is already included
5. It runs automatically every day at **9:00 AM IST**
6. You can also trigger it manually anytime from the Actions tab

GitHub Actions free tier = 2000 min/month. Each run uses ~1 min. Completely free.

---

## What the Telegram message looks like

```
🚀 Daily Job Digest
📅 14 Jun 2026, 09:00 AM
🎯 .NET + React | Bangalore | 7–10 LPA
────────────────────────────

1. Software Engineer - Full Stack
🏢 Mphasis
📍 Bangalore, Karnataka
💰 7–9 LPA
🕐 1 day ago
📌 via Naukri
🔗 Apply Now

2. .NET Developer
🏢 LTIMindtree
📍 Bangalore
💰 8–10 LPA
🕐 Today
🔗 Apply Now

────────────────────────────
🔎 Search more:
• Naukri — .NET React Bangalore
• LinkedIn — Dotnet Bangalore
• Cutshort — Product Companies

Sent by your Job Agent 🤖 | 6 jobs found today
```

---

## Customise filters

Edit these values at the top of `job_agent.py`:

| Setting | Default | What it does |
|---|---|---|
| `MIN_LPA` | 7 | Minimum salary filter |
| `MAX_LPA` | 10 | Maximum salary filter |
| `MAX_JOBS` | 8 | Max jobs per message |
| `EXCLUDE_TITLES` | senior, lead... | Roles to skip |
| `SKIP_PHRASES` | immediate joiner... | Skip if found in description |
| `SEARCH_QUERIES` | 4 queries | Add/edit search terms |

---

## Why Telegram over WhatsApp / CallMeBot

| | Telegram Bot | CallMeBot | WhatsApp Business API |
|---|---|---|---|
| Cost | Free | Free | Paid |
| Official API | Yes | No | Yes |
| Encrypted | Yes | No | Yes |
| Personal use | Yes | Yes | No (businesses only) |
| Reliability | High | Medium | High |
| Setup time | 5 min | 2 min | 1–2 weeks |
