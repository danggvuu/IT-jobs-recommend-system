import sqlite3

conn = sqlite3.connect('database/job_market.sqlite')
cursor = conn.cursor()

cursor.execute("SELECT job_id, job_description FROM jobs WHERE industry = 'ITviec'")
jobs = cursor.fetchall()

found_why = 0

for jid, jd in jobs:
    jd = jd.lower()
    if "why you'll love working here" in jd:
        found_why += 1
        
print(f"Total: {len(jobs)}")
print(f"Why You'll Love Working Here: {found_why}")

