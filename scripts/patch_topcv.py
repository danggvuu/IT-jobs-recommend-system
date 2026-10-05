import re

with open('scrapers/scraper_topcv.py', 'r') as f:
    lines = f.readlines()

out_lines = []
in_execute = False
execute_statement = []
has_retry = False

for line in lines:
    if "def execute_with_retry" in line:
        has_retry = True
        break

if not has_retry:
    imports_done = False
    for i, line in enumerate(lines):
        if line.startswith('def wait_for_cf'):
            # insert before this
            lines.insert(i, """
def execute_with_retry(cursor, conn, query, params=(), max_retries=15):
    import time, sqlite3, random
    for attempt in range(max_retries):
        try:
            cursor.execute(query, params)
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            if 'locked' in str(e).lower() or 'busy' in str(e).lower():
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(0.5, 1.5) * (1.5 ** attempt))
                else:
                    raise
            else:
                raise
""")
            break

# Now we need to manually replace the DB write blocks.
code = "".join(lines)

code = code.replace("""                        cursor.execute('''
                            UPDATE jobs SET
                                company_logo = COALESCE(NULLIF(?, ''), company_logo),
                                salary = COALESCE(NULLIF(?, ''), salary),
                                last_seen_at = ?,
                                job_status = 'OPEN'
                            WHERE job_id = ?
                        ''', (company_logo, salary, now_str, job_id))
                        conn.commit()""", """                        execute_with_retry(cursor, conn, '''
                            UPDATE jobs SET
                                company_logo = COALESCE(NULLIF(?, ''), company_logo),
                                salary = COALESCE(NULLIF(?, ''), salary),
                                last_seen_at = ?,
                                job_status = 'OPEN'
                            WHERE job_id = ?
                        ''', (company_logo, salary, now_str, job_id))""")

code = code.replace("""                    # Ghi DB
                    cursor.execute('''
                        INSERT INTO jobs (
                            job_id, title, company, company_logo, location,
                            experience_required, level, salary, job_status, 
                            scraped_at, last_seen_at, industry, url, 
                            job_description, requirements, benefits, skills
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(job_id) DO UPDATE SET
                            title=excluded.title,
                            company=excluded.company,
                            company_logo=COALESCE(NULLIF(excluded.company_logo, ''), jobs.company_logo),
                            location=excluded.location,
                            experience_required=excluded.experience_required,
                            level=excluded.level,
                            salary=COALESCE(NULLIF(excluded.salary, ''), jobs.salary),
                            job_status=excluded.job_status,
                            last_seen_at=excluded.last_seen_at,
                            url=excluded.url,
                            job_description=excluded.job_description,
                            requirements=excluded.requirements,
                            benefits=excluded.benefits,
                            skills=excluded.skills
                    ''', (
                        job_id, title, company, company_logo, location,
                        experience, level, salary, 'OPEN', 
                        now_str, now_str, industry, job_url, 
                        jd, req, ben, skills_str
                    ))
                    conn.commit()""", """                    # Ghi DB
                    execute_with_retry(cursor, conn, '''
                        INSERT INTO jobs (
                            job_id, title, company, company_logo, location,
                            experience_required, level, salary, job_status, 
                            scraped_at, last_seen_at, industry, url, 
                            job_description, requirements, benefits, skills
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(job_id) DO UPDATE SET
                            title=excluded.title,
                            company=excluded.company,
                            company_logo=COALESCE(NULLIF(excluded.company_logo, ''), jobs.company_logo),
                            location=excluded.location,
                            experience_required=excluded.experience_required,
                            level=excluded.level,
                            salary=COALESCE(NULLIF(excluded.salary, ''), jobs.salary),
                            job_status=excluded.job_status,
                            last_seen_at=excluded.last_seen_at,
                            url=excluded.url,
                            job_description=excluded.job_description,
                            requirements=excluded.requirements,
                            benefits=excluded.benefits,
                            skills=excluded.skills
                    ''', (
                        job_id, title, company, company_logo, location,
                        experience, level, salary, 'OPEN', 
                        now_str, now_str, industry, job_url, 
                        jd, req, ben, skills_str
                    ))""")

code = code.replace("""    cursor.execute("UPDATE jobs SET job_status = 'CLOSED' WHERE last_seen_at < datetime('now', '-3 days')")
    print(f"✅ Đã đánh dấu CLOSED {cursor.rowcount} jobs không còn xuất hiện.")
    conn.commit()""", """    execute_with_retry(cursor, conn, "UPDATE jobs SET job_status = 'CLOSED' WHERE last_seen_at < datetime('now', '-3 days')")
    print(f"✅ Đã dọn dẹp các jobs cũ.")""")

with open('scrapers/scraper_topcv.py', 'w') as f:
    f.write(code)

print("Patched successfully")
