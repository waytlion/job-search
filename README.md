# 🔍 Job Scraper

Automated job scraper that fetches opportunities from **7 platforms**, scores them based on your preferences, and sends a **daily Top-15 Telegram digest**. All jobs are browsable in a full-featured web dashboard.

## ✨ Features

- **7 Job Sources**: Bundesagentur für Arbeit, Arbeitnow, RemoteOK, Jobicy, The Muse, WeWorkRemotely, Adzuna (optional)
- **Smart Filtering**: Removes irrelevant jobs (drivers, retail, etc.)
- **Experience Parsing**: Filters/penalizes jobs requiring too much experience
- **Custom Scoring**: Ranks jobs by money, passion (energy/ML), and location (0–10 scale)
- **Telegram Top-N Digest**: Only the top 15 highest-scored new jobs per day — no more notification spam
- **Web Dashboard**: Browse, filter, and rank all jobs with score breakdowns and rank badges
- **Resilient Pipeline**: Each scraper is isolated — one failing/blocked platform never crashes the others
- **Duplicate Detection**: SQLite database tracks seen jobs
- **GitHub Actions**: Fully automated daily runs at 8 AM UTC

## 🚀 Quick Start

### Local Development

1. **Clone and setup:**
   ```bash
   git clone <your-repo>
   cd job-scraper
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Telegram:**
   - Create a bot via [@BotFather](https://t.me/BotFather)
   - Get your chat ID via [@userinfobot](https://t.me/userinfobot)
   - Copy `.env.example` to `.env` and fill in your credentials

3. **Run locally:**
   ```bash
   # Test mode (limited results, max 5 Telegram notifications)
   python main.py --test
   
   # Full run
   python main.py
   ```

### Web Dashboard

```bash
# Start backend (from project root)
cd webapp/backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Start frontend (in another terminal)
cd webapp/frontend
npm install
npm run dev
```

Open `http://localhost:3000` to browse all jobs ranked by score with `#1`, `#2`, `#3` badges.

### GitHub Actions Setup

1. **Add secrets** to your repository:
   - Go to Settings → Secrets and variables → Actions
   - Add `TELEGRAM_BOT_TOKEN`
   - Add `TELEGRAM_CHAT_ID`

2. **Enable Actions:**
   - The daily scrape runs automatically at 8 AM UTC
   - Use "Manual Test Run" workflow for testing

## 📁 Project Structure

```
job-scraper/
├── config/
│   └── config.yaml              # Main configuration (scrapers, scoring, filters)
├── src/
│   ├── scrapers/
│   │   ├── base.py              # Resilient base: retry, backoff, safe_scrape()
│   │   ├── bundesagentur.py     # Bundesagentur für Arbeit API
│   │   ├── arbeitnow.py         # Arbeitnow API
│   │   ├── remoteok.py          # RemoteOK API
│   │   ├── jobicy.py            # Jobicy API (remote jobs)
│   │   ├── themuse.py           # The Muse API (tech companies)
│   │   ├── weworkremotely.py    # WeWorkRemotely RSS
│   │   └── adzuna.py            # Adzuna API (optional, needs key)
│   ├── filters/                 # Relevance & experience filters
│   ├── scorer.py                # Job scoring engine (money/passion/location)
│   ├── database.py              # SQLite operations
│   ├── notifier.py              # Telegram Top-N digest
│   └── utils/                   # Logging utilities
├── webapp/
│   ├── backend/                 # FastAPI REST API
│   └── frontend/                # Next.js dashboard with rank badges
├── tests/                       # Test suite (29 tests)
├── .github/workflows/           # GitHub Actions (daily + manual)
├── main.py                      # Entry point
└── jobs.db                      # SQLite database
```

## 🔌 Job Sources

| Platform | Type | API Key | What it scrapes |
|----------|------|---------|-----------------|
| **Bundesagentur** | REST API | None | German job market (with full descriptions) |
| **Arbeitnow** | REST API | None | Germany-focused tech jobs |
| **RemoteOK** | REST API | None | Remote tech/data jobs worldwide |
| **Jobicy** | REST API | None | Remote data science, ML, Python jobs |
| **The Muse** | REST API | None | Data Science, Analytics, SWE at tech companies |
| **WeWorkRemotely** | RSS Feed | None | Remote programming & devops jobs |
| **Adzuna** | REST API | **Free key** | DE + UK jobs with salary estimates |

Each scraper can be toggled on/off via `config/config.yaml` → `scraping.<platform>.enabled`.

### Enabling Adzuna (TODO)

1. Register for a free API key at [developer.adzuna.com](https://developer.adzuna.com/)
2. Add to your `.env` file:
   ```
   ADZUNA_APP_ID=your_app_id
   ADZUNA_APP_KEY=your_app_key
   ```
3. The scraper will automatically use the key on the next run. If no key is set, Adzuna is silently skipped.

## 🛡️ Resilience

The pipeline is designed to **never crash** because of external platforms:

- **`resilient_request()`** — All HTTP calls use retry with exponential backoff
  - `403/401` (bot detection) → stops immediately, no retries
  - `429` (rate-limited) → waits and retries
  - `500+` (server error) → retries with backoff
  - Timeouts/connection errors → retries with backoff
- **`safe_scrape()`** — Every scraper is wrapped in a try/catch. If one platform explodes, the rest continue normally
- **Per-platform logging** — Clear `✅`/`⚠️` per scraper in the logs

## ⚙️ Configuration

Edit `config/config.yaml` to customize:

- **Search terms and locations** (per scraper)
- **Filtering keywords** (irrelevant jobs, senior roles)
- **Scoring weights and thresholds** (money/passion/location)
- **Telegram daily limit** (`daily_top_n: 15`)
- **Enable/disable scrapers** (`enabled: true/false`)

### Scoring System

Jobs are scored on a 0–10 scale across three dimensions:

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| 💰 Money | 33% | Salary + seniority level |
| ❤️ Passion | 34% | Energy sector + ML/AI keywords |
| 📍 Location | 33% | Bavaria > Germany > Remote |

### Telegram Digest

Only the top `daily_top_n` (default: 15) highest-scored jobs are sent to Telegram each day. All jobs are still saved to the database and visible on the web dashboard.

## 🧪 Testing

```bash
# Run all tests (29 tests)
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_scorer.py -v
```

## 🔧 Troubleshooting

### "No jobs found"
- Check if the APIs are accessible
- Review logs in `logs/` directory
- Try running with `--test` flag

### "Telegram message failed"
- Verify bot token and chat ID
- Ensure bot is added to chat (if group)
- Check Telegram API limits

### "Scraper shows ⚠️ in logs"
- The platform may be temporarily down or blocking requests
- The pipeline continues — other scrapers still run
- Check if `enabled: true` is set in config

### "Database locked"
- Only run one instance at a time
- Delete `jobs.db` to start fresh

## 📊 Database

The SQLite database tracks all scraped jobs:

```sql
-- View recent jobs
SELECT title, company, total_score 
FROM jobs 
ORDER BY scraped_at DESC 
LIMIT 10;

-- View top-scored jobs
SELECT title, company, total_score, platform
FROM jobs
WHERE filtered_out = 0
ORDER BY total_score DESC
LIMIT 20;
```

## 📝 TODO

- [ ] **Register Adzuna API key** — [developer.adzuna.com](https://developer.adzuna.com/) (free)
- [ ] **Cross-platform deduplication** — Same job posted on multiple sites is currently stored twice
- [ ] **Job expiry detection** — Re-check if old jobs are still live, auto-archive expired ones
- [ ] **Email digest** — Alternative to Telegram with richer formatting

## 📝 License

MIT License — feel free to use and modify!

---

Built with ❤️ for job seekers in tech
