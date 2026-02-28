"""
One-time cleanup: remove Bundesagentur jobs with broken URLs from the database.

These jobs have URLs like 'https://www.arbeitsagentur.de/jobsuche/jobdetail/'
(no slug) that redirect to the landing page. The original BA hashId was not
stored, so URLs cannot be reconstructed.
"""
import sqlite3
import sys

DB_PATH = r'd:\Data\projects\2026\job-search\jobs.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Count broken BA URLs
    c.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE platform = 'bundesagentur' 
        AND (
            url LIKE '%/jobdetail/' 
            OR url LIKE '%/jobdetail'
            OR url LIKE '%/jobsuche/'
            OR url IS NULL 
            OR url = ''
        )
    """)
    broken_count = c.fetchone()[0]

    if broken_count == 0:
        print("No broken Bundesagentur URLs found. Nothing to do.")
        conn.close()
        return

    print(f"Found {broken_count} Bundesagentur jobs with broken URLs.")
    print("Deleting...")

    c.execute("""
        DELETE FROM jobs 
        WHERE platform = 'bundesagentur' 
        AND (
            url LIKE '%/jobdetail/' 
            OR url LIKE '%/jobdetail'
            OR url LIKE '%/jobsuche/'
            OR url IS NULL 
            OR url = ''
        )
    """)
    conn.commit()

    deleted = c.rowcount
    print(f"Deleted {deleted} jobs with broken URLs.")

    # Verify
    c.execute("SELECT COUNT(*) FROM jobs WHERE platform = 'bundesagentur'")
    remaining = c.fetchone()[0]
    print(f"Remaining Bundesagentur jobs: {remaining}")

    c.execute("SELECT COUNT(*) FROM jobs")
    total = c.fetchone()[0]
    print(f"Total jobs in database: {total}")

    conn.close()

if __name__ == "__main__":
    main()
