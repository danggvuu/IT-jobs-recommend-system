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

def scrape_jd(page, job_url: str):
    page.get(job_url)
    time.sleep(1.5)
    soup = BeautifulSoup(page.html, 'html.parser')

    jd, req, ben = '', '', ''
    for section in soup.select('.box-job-information-detail-item'):
        t_el = section.select_one('.box-job-information-detail-item__title--title') or section.select_one('h2')
        if not t_el:
            continue
        t = t_el.get_text(strip=True).lower()
        if t in ('tổng quan', 'job details'):
            continue

        c_el = section.select_one('.box-job-information-detail-item__text')
        if c_el:
            content = c_el.get_text(separator='\n', strip=True)
            if 'mô tả' in t or 'job description' in t:
                jd = content
            elif 'yêu cầu' in t or 'candidate requirement' in t or 'requirements' in t:
                req = content
            elif 'quyền lợi' in t or 'benefits' in t:
                ben = content
    return jd, req, ben

def main():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    cursor.execute("SELECT job_id, url FROM jobs WHERE industry='IT Phần mềm' AND (job_description IS NULL OR job_description = '' OR length(job_description) < 10)")
    jobs = cursor.fetchall()
    
    if not jobs:
        print("Không có job nào rỗng.")
        return
        
    print(f"Bắt đầu backfill JD cho {len(jobs)} jobs...")
    page = init_browser()
    
    for job_id, url in jobs:
        print(f"Đang cào lại: {url}")
        jd, req, ben = scrape_jd(page, url)
        if jd:
            cursor.execute("UPDATE jobs SET job_description=?, requirements=?, benefits=? WHERE job_id=?", (jd, req, ben, job_id))
            conn.commit()
            print(f"-> Đã vá thành công {job_id}")
        else:
            print(f"-> Vẫn không cào được {job_id} (Có thể bị block hoặc JD thực sự rỗng)")
        time.sleep(2)
        
    page.quit()
    conn.close()

if __name__ == '__main__':
    main()
