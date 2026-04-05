import sqlite3

conn = sqlite3.connect('jobs.db')
cursor = conn.cursor()

def fetch_and_print(query, label):
    print(f"\n--- {label} ---")
    rows = cursor.execute(query).fetchall()
    for r in rows:
        print(f"[{r[2]}/10] {r[0]} @ {r[1]}")
        print(f"Reason: {r[3]}")
        print("")

fetch_and_print('SELECT title, company, llm_score, llm_reasoning FROM jobs WHERE llm_score IS NOT NULL ORDER BY llm_score DESC LIMIT 5', "TOP 5 LLM MATCHES")
fetch_and_print('SELECT title, company, llm_score, llm_reasoning FROM jobs WHERE llm_score IS NOT NULL ORDER BY llm_score ASC LIMIT 5', "BOTTOM 5 LLM MATCHES")
