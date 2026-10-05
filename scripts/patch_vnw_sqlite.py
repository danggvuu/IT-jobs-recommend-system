import re
import os

with open('scrapers/scraper_vnw.py', 'r') as f:
    content = f.read()

# Add sqlite3 imports and retry function
imports_to_add = """import sqlite3
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "job_market.sqlite")

def execute_with_retry(cursor, conn, query, params=(), max_retries=15):
    import time
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
"""
if 'import sqlite3' not in content:
    content = re.sub(r'(import json\n)', r'\1' + imports_to_add, content, count=1)


# Modify _scrape_page to check DB and insert/update
# We need to replace the loop body
old_loop = """                job = self._extract_job(card)

                # Chỉ lưu nếu có thông tin hữu ích
                if job["title"] or job["url"]:
                    logger.debug("  🔍 Đang cào chi tiết JD cho: %s", job["url"])
                    details = self._extract_job_details(job["url"])
                    job["job_description"] = details["job_description"]
                    job["requirements"] = details.get("requirements", "")
                    job["benefits"] = details.get("benefits", "")
                        
                    job["job_date_str"] = job.get("job_date").strftime("%Y-%m-%d") if job.get("job_date") else ""
                    job.pop("job_date", None)
                    self.jobs.append(job)
                    page_jobs += 1
                    logger.debug(
                        "  📋 [%d/%d] %s — %s (JD: %s chars)",
                        idx, len(cards),
                        job["title"][:50] if job["title"] else "(no title)",
                        job["company"][:30] if job["company"] else "(no company)",
                        len(job["job_description"])
                    )
                else:
                    logger.debug("  ⏭️  [%d/%d] Bỏ qua card trống", idx, len(cards))"""

new_loop = """                job = self._extract_job(card)
                if not job["url"]:
                    logger.debug("  ⏭️  [%d/%d] Bỏ qua card trống URL", idx, len(cards))
                    continue
                    
                import hashlib
                job_id = hashlib.md5(job["url"].encode()).hexdigest()[:15]
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Kết nối DB
                conn = sqlite3.connect(DB_PATH, timeout=15.0)
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                
                cursor.execute("SELECT job_description, requirements, benefits, experience_required, level FROM jobs WHERE url = ? OR job_id = ?", (job["url"], job_id))
                existing = cursor.fetchone()
                
                if existing and existing[0] and len(existing[0]) > 10:
                    # Đã có trong DB
                    logger.info(f"    [~] DB đã có: {job['title'][:50]}")
                    execute_with_retry(cursor, conn, '''
                        UPDATE jobs SET
                            salary = COALESCE(NULLIF(?, ''), salary),
                            last_seen_at = ?,
                            job_status = 'OPEN'
                        WHERE url = ? OR job_id = ?
                    ''', (job.get("salary", ""), now_str, job["url"], job_id))
                else:
                    # Chưa có, đi cào chi tiết
                    logger.debug("  🔍 Đang cào chi tiết JD cho: %s", job["url"])
                    details = self._extract_job_details(job["url"])
                    jd = details.get("job_description", "")
                    req = details.get("requirements", "")
                    ben = details.get("benefits", "")
                    exp = details.get("experience", "")
                    level = details.get("level", "")
                    
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
                    ''', (
                        job_id, job.get("title", ""), job.get("company", ""), "", job.get("location", ""),
                        exp, level, job.get("salary", ""), 'OPEN',
                        now_str, now_str, 'VietnamWorks', job["url"],
                        jd, req, ben, ""
                    ))
                    logger.info(f"    [+] Mới cào: {job['title'][:50]}")
                    
                conn.close()
                page_jobs += 1"""

content = content.replace(old_loop, new_loop)

# Replace _save_results to not do anything, or just log
content = content.replace("def _save_results(self) -> str:", "def _save_results(self) -> str:\n        return 'Database: job_market.sqlite'\n        ")

with open('scrapers/scraper_vnw.py', 'w') as f:
    f.write(content)

print("VietnamWorks scraper patched!")
