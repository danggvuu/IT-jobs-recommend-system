import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "job_market.sqlite")

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    cursor.execute("SELECT job_id, job_description FROM jobs WHERE industry = 'ITviec'")
    jobs = cursor.fetchall()
    
    updated = 0
    for job_id, jd in jobs:
        if not jd:
            continue
            
        # Try to find "Your Skills and Experience" (case insensitive)
        skills_match = re.search(r'(?i)Your Skills and Experience', jd)
        why_match = re.search(r"(?i)Why You'll Love Working Here", jd)
        
        if skills_match:
            desc_part = jd[:skills_match.start()].strip()
            req_part = ""
            
            if why_match and why_match.start() > skills_match.end():
                req_part = jd[skills_match.end():why_match.start()].strip()
            else:
                req_part = jd[skills_match.end():].strip()
                
            cursor.execute('''
                UPDATE jobs 
                SET job_description = ?, requirements = ?
                WHERE job_id = ?
            ''', (desc_part, req_part, job_id))
            updated += 1
            
    conn.commit()
    conn.close()
    print(f"✅ Đã split thành công {updated} jobs từ ITviec!")

if __name__ == '__main__':
    main()
