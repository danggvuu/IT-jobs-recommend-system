import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "job_market.sqlite")
conn = sqlite3.connect(DB_PATH, timeout=15.0)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")

query = '''
    INSERT INTO jobs (
        job_id, title, company_name, company_logo, location,
        experience_required, level, salary, job_status, 
        scraped_at, last_seen_at, industry, url, 
        job_description, requirements, benefits, skills
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(job_id) DO UPDATE SET
        title=excluded.title,
        company_name=excluded.company_name,
        location=excluded.location,
        experience_required=excluded.experience_required,
        level=excluded.level,
        salary=COALESCE(NULLIF(excluded.salary, ''), jobs.salary),
        job_status=excluded.job_status,
        last_seen_at=excluded.last_seen_at,
        url=excluded.url,
        job_description=excluded.job_description,
        requirements=excluded.requirements,
        benefits=excluded.benefits
'''
params = (
    'test_job_123', 'Test Job', 'Test Company', '', 'Hanoi',
    '1 year', 'Junior', '1000$', 'OPEN',
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
    'VietnamWorks', 'https://test.com',
    'Test JD', 'Test Req', 'Test Ben', ''
)

cursor.execute(query, params)
conn.commit()
conn.close()

# Verify
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT count(*) FROM jobs WHERE job_id='test_job_123'")
print("Found inserted job:", cursor.fetchone()[0])
