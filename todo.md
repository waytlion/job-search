## Job Scraper Status

✅ COMPLETED:
- All code created and pushed to GitHub
- 3 scrapers: Bundesagentur, Arbeitnow, RemoteOK  
- Filters: relevance + experience
- Scoring system (money/passion/location)
- SQLite database
- Telegram notifier with chunking
- GitHub Actions workflows


# Implement better scoring via Encoder - Plan:
@workspace
We need to implement two critical improvements to our job scraper pipeline: fixing substring false positives and implementing a semantic LLM Re-Ranker using a Cross-Encoder.

Please review the following architectural updates. Ask clarifying questions before you start. Think also if/how this may be improved before we start:

1. REGEX WORD BOUNDARY FIX (The "ai" / "ml" problem)
In our keyword matching logic (likely in `scorer.py` or `filters.py`), replace all basic substring checks (e.g., `if keyword in text`) with pre-compiled regular expressions using word boundaries.
- Convert keyword lists to compiled regex patterns: `re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)`
- Apply this specifically to the Passion Score keywords (energy, ML/AI, tech) to prevent "ml" from matching "html" and "ai" from matching "training".

2. DEPENDENCY UPDATES FOR RE-RANKING
Update `requirements.txt` to include the CPU-only versions of PyTorch and the `sentence-transformers` library, which are optimized for GitHub Actions standard runners.
Add:
sentence-transformers==2.5.1
torch==2.2.1+cpu --extra-index-url https://download.pytorch.org/whl/cpu

3. CROSS-ENCODER IMPLEMENTATION
Create a new module `src/reranker.py`. Implement a class `SemanticReranker` with the following specifications:
- Model: Use `cross-encoder/ms-marco-MiniLM-L-6-v2`. It is extremely lightweight (~90MB) and fast on CPU.
- Query Formulation: Define a static query string representing the ideal candidate profile: "Data Scientist or Machine Learning Engineer in the Energy Sector or Smart Grids. Junior or Master Thesis level. Experience with Python, PyTorch, Spatio-Temporal Graph Neural Networks (ST-GNNs), and time-series forecasting."
- Document Formulation: Concatenate the job title and description: `f"{job.title} - {job.description}"`.
- Scoring Math: The model outputs raw logits. Implement a sigmoid normalization to scale these logits to a 0-10 score:
  `normalized_score = (1 / (1 + math.exp(-raw_logit))) * 10`

4. PIPELINE INTEGRATION (Top-K Re-ranking)
Running the Cross-Encoder on 2,000 jobs will exceed the GitHub Actions time limit. We must use a Two-Stage Retrieval architecture:
- Stage 1: Keep the existing heuristic scoring (Money, Location, base Passion) to score all raw jobs.
- Stage 2: Select only the Top $K$ jobs (e.g., $K=500$) based on the Stage 1 score.
- Pass these Top 50 jobs through the `SemanticReranker`.
- Calculate the Final Score by computing a weighted average of the Heuristic Score (e.g., 40%) and the Semantic Cross-Encoder Score (e.g., 60%).

Please review my existing code and provide the exact implementations for `reranker.py`, the regex updates in the scoring engine, and the integration step in `main.py`.