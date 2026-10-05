import sqlite3
import os
import time
from bs4 import BeautifulSoup
from DrissionPage import WebPage, ChromiumOptions
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "job_market.sqlite")

def init_browser():
    co = ChromiumOptions()
    co.headless(False)
    co.set_argument("--disable-blink-features=AutomationControlled")
    if sys.platform == 'darwin':
        co.set_browser_path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    co.set_user_data_path(os.path.join(os.path.dirname(__file__), '..', 'scrapers', 'chrome_profile'))
    return WebPage(mode='d', chromium_options=co)

def get_skills_from_url(page, url):
    page.get(url)
    time.sleep(1.5)
    soup = BeautifulSoup(page.html, 'html.parser')
    
    skills = []
    for tag_content in soup.select('.required-tag__content'):
        text = tag_content.get_text(separator=', ', strip=True)
        if text:
            clean_text = text
            for prefix in ['Kiến thức ngành', 'Kỹ năng cần có', 'Kỹ năng nên có', 'Phúc lợi']:
                if clean_text.startswith(prefix):
                    clean_text = clean_text[len(prefix):].strip(', ')
            if clean_text:
                skills.append(clean_text)
    return ", ".join(skills) if skills else None

def main():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()
    
    # Enable WAL mode for concurrency
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    cursor.execute("SELECT job_id, url FROM jobs WHERE skills IS NULL AND url LIKE '%topcv.vn%'")
    jobs = cursor.fetchall()
    
    if not jobs:
        print("Không có job nào cần update skills.")
        return
        
    print(f"Bắt đầu backfill skills cho {len(jobs)} jobs...")
    page = init_browser()
    
    count = 0
    for job_id, url in jobs:
        skills = get_skills_from_url(page, url)
        if skills:
            try:
                cursor.execute("UPDATE jobs SET skills = ? WHERE job_id = ?", (skills, job_id))
                conn.commit()
                print(f"Cập nhật {job_id}: {skills}")
            except sqlite3.OperationalError as e:
                print(f"Lỗi DB khi cập nhật {job_id}: {e}")
                # Wait and retry once
                time.sleep(3)
                try:
                    cursor.execute("UPDATE jobs SET skills = ? WHERE job_id = ?", (skills, job_id))
                    conn.commit()
                except Exception as e2:
                    print(f"Vẫn lỗi DB: {e2}")
        else:
            print(f"Không tìm thấy skills cho {job_id}")
            
        count += 1
        if count % 10 == 0:
            time.sleep(2)
        
    page.quit()
    conn.close()
    print("Hoàn thành!")

if __name__ == '__main__':
    main()
