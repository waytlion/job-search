"""Quick script to view top jobs from the database."""
import sqlite3

conn = sqlite3.connect('jobs.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("\n" + "="*80)
print("🏆 TOP 20 JOBS BY SCORE")
print("="*80 + "\n")

cursor.execute('''
    SELECT title, company, location, total_score, money_score, passion_score, location_score, url, platform
    FROM jobs 
    WHERE filtered_out = 0 
    ORDER BY total_score DESC 
    LIMIT 20
''')

for i, row in enumerate(cursor.fetchall(), 1):
    print(f"#{i} - Score: {row['total_score']:.1f}/10 (💰{row['money_score']:.1f} ❤️{row['passion_score']:.1f} 📍{row['location_score']:.1f})")
    print(f"   {row['title']}")
    print(f"   🏢 {row['company']} | 📍 {row['location']}")
    print(f"   🔗 {row['url'][:70]}...")
    print(f"   Source: {row['platform']}")
    print()

# Stats
print("\n" + "="*80)
print("📊 DATABASE STATS")
print("="*80)

cursor.execute("SELECT COUNT(*) FROM jobs")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM jobs WHERE filtered_out = 0")
valid = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM jobs WHERE filtered_out = 1")
filtered = cursor.fetchone()[0]

cursor.execute("SELECT platform, COUNT(*) FROM jobs GROUP BY platform")
platforms = cursor.fetchall()

print(f"\nTotal jobs: {total}")
print(f"Valid jobs: {valid}")
print(f"Filtered out: {filtered}")
print(f"\nBy platform:")
for p in platforms:
    print(f"  - {p[0]}: {p[1]}")

conn.close()
