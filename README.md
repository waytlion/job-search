# 🔍 Job Scraper

Automated job scraper that fetches opportunities from multiple sources, scores them based on your preferences, and sends daily Telegram notifications.

## ✨ Features

- **3 Job Sources**: Bundesagentur für Arbeit, Arbeitnow, RemoteOK
- **Smart Filtering**: Removes irrelevant jobs (drivers, retail, etc.)
- **Experience Parsing**: Filters/penalizes jobs requiring too much experience
- **Custom Scoring**: Ranks jobs by money, passion (energy/ML), and location
- **Telegram Notifications**: Daily digest with all new matching jobs
- **Duplicate Detection**: SQLite database tracks seen jobs
- **GitHub Actions**: Fully automated daily runs

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
   # Test mode (limited results)
   python main.py --test
   
   # Full run
   python main.py
   ```

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
│   └── config.yaml          # Main configuration
├── src/
│   ├── scrapers/            # API scrapers
│   ├── filters/             # Relevance & experience filters
│   ├── scorer.py            # Job scoring engine
│   ├── database.py          # SQLite operations
│   ├── notifier.py          # Telegram integration
│   └── utils/               # Logging utilities
├── tests/                   # Test suite
├── .github/workflows/       # GitHub Actions
├── main.py                  # Entry point
└── jobs.db                  # SQLite database
```

## ⚙️ Configuration

Edit `config/config.yaml` to customize:

- **Search terms and locations**
- **Filtering keywords**
- **Scoring weights and thresholds**
- **Notification preferences**

### Scoring System

Jobs are scored on a 0-10 scale across three dimensions:

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| 💰 Money | 33% | Salary + seniority level |
| ❤️ Passion | 34% | Energy sector + ML/AI keywords |
| 📍 Location | 33% | Bavaria > Germany > Remote |

## 🧪 Testing

```bash
# Run all tests
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

-- View unsent jobs
SELECT * FROM jobs 
WHERE sent_to_user = 0 AND filtered_out = 0;
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📝 License

MIT License - feel free to use and modify!

---

Built with ❤️ for job seekers in tech
