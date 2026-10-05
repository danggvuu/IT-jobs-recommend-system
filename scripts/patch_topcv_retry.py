import re

with open('scrapers/scraper_topcv.py', 'r') as f:
    content = f.read()

retry_code = """
def execute_with_retry(cursor, conn, query, params=(), max_retries=10):
    import time
    import sqlite3
    for attempt in range(max_retries):
        try:
            cursor.execute(query, params)
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e).lower() or 'busy' in str(e).lower():
                if attempt < max_retries - 1:
                    sleep_time = 0.5 * (2 ** attempt)
                    time.sleep(sleep_time)
                else:
                    raise
            else:
                raise
"""

# Add function if not exists
if 'def execute_with_retry' not in content:
    # insert it after imports
    content = re.sub(r'(import .*?\n\n)', r'\1' + retry_code + '\n', content, count=1)

# replace cursor.execute followed by conn.commit() with execute_with_retry
# We have a few patterns in scraper_topcv.py
# Pattern 1:
# cursor.execute("UPDATE jobs SET job_status = 'CLOSED' ...")
# conn.commit()
content = content.replace("cursor.execute(\"UPDATE jobs SET job_status = 'CLOSED' WHERE last_seen_at < datetime('now', '-3 days')\")\n    print(f\"✅ Đã đánh dấu CLOSED {cursor.rowcount} jobs không còn xuất hiện.\")\n    conn.commit()", 
"execute_with_retry(cursor, conn, \"UPDATE jobs SET job_status = 'CLOSED' WHERE last_seen_at < datetime('now', '-3 days')\")\n    print(f\"✅ Đã đánh dấu CLOSED {cursor.rowcount} jobs không còn xuất hiện.\")")

# Pattern 2: (INSERT INTO jobs...)
# cursor.execute('''
#    INSERT INTO jobs ...
# ''', (...))
# conn.commit()
# This is hard to regex, let's write a simple python parser or replace manually
