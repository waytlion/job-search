## Job Scraper Status

✅ COMPLETED:
- All core code created and pushed to GitHub
- 3 independent scrapers: Bundesagentur, Arbeitnow, RemoteOK  
- Filters: relevance + experience
- Scoring system (money/passion/location)
- SQLite database
- Telegram notifier with chunking
- GitHub Actions workflows
- **AI Reranker**: Integrated NVIDIA API (moonshotai/kimi-k2-5) for semantic re-ranking of the Top 50 heuristic jobs. Extracted reasoning & scores natively.
- **Regex Word Boundaries**: Replaced substring false positives (e.g., 'ML' matching 'HTML') with `\b` regex parsing.
- **Web App**: Built a functional Next.js + FastAPI dashboard and successfully rendered LLM scoring reasoning cards directly on the frontend.

## TODO: 
### Big Stuff
- [ ] **Cross-platform deduplication** — Same job posted on multiple sites is currently stored twice. We should perhaps group these.
- [ ] **Job expiry detection** — Re-check if old jobs are still live, auto-archive expired ones instead of manually filtering them.
- [ ] **Email digest** — Alternative to Telegram with richer formatting.

### Small Stuff
- [ ] Links to role do not work for Bundesagentur Arbeit (always refers to main page, not direct posting). Needs investigation on how to extract deep links.
- [ ] Initial scraping loaded a lot of postings from the past, which seem to be outdated (cant find them on the BA platform anymore). Need stricter staleness limits.
- [ ] **Register Adzuna API key** — [developer.adzuna.com](https://developer.adzuna.com/) (free)