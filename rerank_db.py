import os
import yaml
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

from src.reranker import LLMEvaluator
from src.scrapers.base import Job
from src.utils.logger import get_logger

load_dotenv()
logger = get_logger()

with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Force the config settings
config["scoring"]["weights"] = {"money": 0.15, "passion": 0.25, "location": 0.20, "llm": 0.40}
config["scoring"]["llm_evaluator"]["enabled"] = True
config["scoring"]["llm_evaluator"]["top_k_to_evaluate"] = 200

db_path = "jobs.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

query = """
    SELECT id, job_hash, title, company, location, url, platform,
           description, requirements, tags,
           salary_min, salary_max, salary_currency, salary_text,
           posted_date, scraped_at,
           money_score, passion_score, location_score, total_score,
           years_experience_required, filtered_out, filter_reason,
           llm_score, llm_reasoning
    FROM jobs 
    WHERE filtered_out = 0 AND (llm_score IS NULL OR llm_score = 0)
    ORDER BY total_score DESC
"""
cursor.execute(query)
rows = cursor.fetchall()

jobs_to_eval = []
for row in rows:
    j = Job(
        title=row['title'], company=row['company'], location=row['location'],
        url=row['url'], platform=row['platform'], description=row['description'],
        requirements=row['requirements'],
        salary_min=row['salary_min'], salary_max=row['salary_max'],
        salary_currency=row['salary_currency'], salary_text=row['salary_text'],
        posted_date=row['posted_date']
    )
    j.money_score = row['money_score']
    j.passion_score = row['passion_score']
    j.location_score = row['location_score']
    j.total_score = row['total_score']
    
    j.db_id = row['id']
    jobs_to_eval.append(j)

# Top 200 only
jobs_to_eval = jobs_to_eval[:200]
logger.info(f"Loaded {len(jobs_to_eval)} non-evaluated top jobs from DB.")

evaluator = LLMEvaluator(config)
evaluated = evaluator.evaluate_jobs(jobs_to_eval)

for j in evaluated:
    cursor.execute("""
        UPDATE jobs
        SET llm_score = ?, llm_reasoning = ?, total_score = ?
        WHERE id = ?
    """, (j.llm_score, j.llm_reasoning, j.total_score, j.db_id))

conn.commit()
conn.close()
logger.info("Successfully pushed 200 LLM evaluations to the web app database!")
