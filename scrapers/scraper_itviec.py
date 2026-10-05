import requests
from bs4 import BeautifulSoup
import json
import sqlite3
import time
import random
import re
import os
from datetime import datetime

# ═══════════ CẤU HÌNH ═══════════
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "job_market.sqlite")
BASE_URL = "https://itviec.com/it-jobs"
MAX_PAGES = 100
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
    "Referer": "https://itviec.com/"
}

# ═══════════ FUNCTIONS ═══════════

def setup_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company_name TEXT,
            company_logo TEXT,
            industry TEXT,
            salary TEXT,
            location TEXT,
            experience_required TEXT,
            level TEXT,
            job_status TEXT,
            scraped_at DATETIME,
            last_seen_at DATETIME,
            url TEXT,
            job_description TEXT,
            requirements TEXT,
            benefits TEXT,
            skills TEXT
        )
    ''')
    conn.commit()
    return conn

def fetch_page(url, session, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = session.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"      [!] Lỗi fetch {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None

def extract_jobs_from_list(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    for card in soup.select('div.job-card'):
        job_slug = card.get('data-search--job-selection-job-slug-value')
        if not job_slug:
            continue
            
        a_tag = card.select_one('h3 a')
        if not a_tag:
            continue
            
        raw_url = a_tag.get('href', '').split('?')[0]
        if not raw_url.startswith("http"):
            job_url = "https://itviec.com" + raw_url
        else:
            job_url = raw_url
        title = a_tag.get_text(strip=True)
        
        company_tag = card.select_one('span.ims-2 a')
        company_name = company_tag.get_text(strip=True) if company_tag else ''
        
        logo_tag = card.select_one('.logo-employer-card img') or card.select_one('.logo-employer-card source')
        company_logo = ''
        if logo_tag:
            company_logo = logo_tag.get('data-src') or logo_tag.get('data-srcset') or logo_tag.get('src') or ''
            if company_logo:
                company_logo = company_logo.split(',')[0].split(' ')[0] # Handle srcset
                
        working_model_tag = card.select_one('div.text-rich-grey.flex-shrink-0')
        working_model = working_model_tag.get_text(strip=True) if working_model_tag else ''
        
        location_tag = card.select_one('div[title]')
        location = location_tag.get('title') if location_tag else ''
        
        # Skill tags
        skills = []
        for tag in card.select('div[data-controller="responsive-tag-list"] a.itag'):
            skills.append(tag.get_text(strip=True))
            
        # Optional: Label (HOT)
        label_tag = card.select_one('div.ilabel')
        label = label_tag.get_text(strip=True) if label_tag else ''
        
        level = "N/A" # Will parse from title or detail later
        
        results.append({
            'job_id': job_slug,
            'job_url': job_url,
            'title': title,
            'company_name': company_name,
            'company_logo': company_logo,
            'location': location,
            'skills': ", ".join(skills) if skills else None,
            'working_model': working_model,
            'label': label,
            'level': level
        })
    return results


def execute_with_retry(cursor, conn, query, params, max_retries=10):
    import sqlite3, time, random
    for attempt in range(max_retries):
        try:
            if params is None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                wait_time = random.uniform(1.0, 3.0)
                print(f"    [⚠️] Database bị lock, thử lại sau {wait_time:.2f}s (Lần {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise e
    print("    [❌] Không thể ghi vào database do bị lock quá nhiều lần.")

def strip_html(html_str):
    if not html_str:
        return ""
    soup = BeautifulSoup(html_str, 'html.parser')
    return soup.get_text(separator='\n', strip=True)

def extract_jd_from_detail(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    salary = ""
    description = ""
    requirements = "" # ITviec usually merges description and requirements in JSON-LD
    benefits = ""
    experience = ""
    skills_json = []
    
    # Try JSON-LD first
    scripts = soup.find_all('script', type='application/ld+json')
    job_data = None
    for script in scripts:
        try:
            data = json.loads(script.string)
            if data.get('@type') == 'JobPosting':
                job_data = data
                break
        except:
            continue
            
    if job_data:
        # Salary
        try:
            min_sal = job_data.get('baseSalary', {}).get('value', {}).get('minValue')
            max_sal = job_data.get('baseSalary', {}).get('value', {}).get('maxValue')
            currency = job_data.get('baseSalary', {}).get('currency', 'USD')
            if min_sal and max_sal:
                salary = f"{min_sal:,.0f} - {max_sal:,.0f} {currency}"
            elif min_sal:
                salary = f"Từ {min_sal:,.0f} {currency}"
            elif max_sal:
                salary = f"Đến {max_sal:,.0f} {currency}"
        except:
            pass
            
        # Description and Requirements split
        raw_desc = job_data.get('description', '')
        full_desc = strip_html(raw_desc)
        import re
        skills_match = re.search(r'(?i)Your Skills and Experience', full_desc)
        why_match = re.search(r"(?i)Why You'll Love Working Here", full_desc)
        
        if skills_match:
            description = full_desc[:skills_match.start()].strip()
            if why_match and why_match.start() > skills_match.end():
                requirements = full_desc[skills_match.end():why_match.start()].strip()
            else:
                requirements = full_desc[skills_match.end():].strip()
        else:
            description = full_desc
        
        # Benefits
        raw_ben = job_data.get('jobBenefits', '')
        benefits = strip_html(raw_ben)
        
        # Experience
        try:
            months = job_data.get('experienceRequirements', {}).get('monthsOfExperience')
            if months:
                years = int(months) // 12
                experience = f"{years} năm" if years > 0 else f"{months} tháng"
        except:
            pass
            
        # Skills
        skills_raw = job_data.get('skills', [])
        if isinstance(skills_raw, list):
            skills_json = skills_raw
        elif isinstance(skills_raw, str):
            skills_json = [s.strip() for s in skills_raw.split(',')]
            
    # Fallback to HTML if JSON-LD missing or incomplete
    if not description:
        desc_div = soup.select_one('div.job-description')
        if desc_div:
            description = desc_div.get_text(separator='\n', strip=True)
            
    if not experience:
        # Try to parse from HTML if needed, though JSON-LD is usually reliable
        pass

    return salary, description, requirements, benefits, experience, skills_json

# ═══════════ MAIN ═══════════

def main():
    conn = setup_db()
    cursor = conn.cursor()
    session = requests.Session()
    
    print("🚀 Bắt đầu cào data từ ITviec (HTTP-first)...")
    
    jd_scraped_count = 0
    total_jobs_scraped = 0
    
    for page_num in range(1, MAX_PAGES + 1):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        url = f"{BASE_URL}?page={page_num}"
        print(f"\n👉 Đang cào trang {page_num}...")
        
        html_list = fetch_page(url, session)
        if not html_list:
            print(f"  ⚠️ Lỗi khi tải trang {page_num}, bỏ qua.")
            continue
            
        jobs_info = extract_jobs_from_list(html_list)
        if not jobs_info:
            print(f"  ✅ Không tìm thấy job nào trên trang {page_num}. Đã đến trang cuối.")
            break
            
        print(f"  📋 Tìm thấy {len(jobs_info)} jobs, bắt đầu xử lý...")
        
        for job in jobs_info:
            job_id = job['job_id']
            
            # Check DB
            cursor.execute("SELECT job_description, skills FROM jobs WHERE job_id = ?", (job_id,))
            existing = cursor.fetchone()
            
            if existing and existing[0] and len(existing[0]) > 10:
                print(f"    [~] DB đã có: {job['title']}")
                execute_with_retry(cursor, conn, '''
                    UPDATE jobs SET
                        company_logo = COALESCE(NULLIF(?, ''), company_logo),
                        last_seen_at = ?,
                        job_status = 'OPEN',
                        skills = COALESCE(NULLIF(?, ''), skills)
                    WHERE job_id = ?
                ''', (job['company_logo'], now_str, job['skills'], job_id))
                continue
                
            # Fetch detail
            html_detail = fetch_page(job['job_url'], session)
            if not html_detail:
                print(f"    [!] Lỗi tải chi tiết: {job['title']}")
                continue
                
            salary, jd, req, ben, exp, skills_json = extract_jd_from_detail(html_detail)
            
            # Combine skills from list and json-ld
            all_skills = []
            if job['skills']:
                all_skills.extend(job['skills'].split(', '))
            if skills_json:
                all_skills.extend(skills_json)
            final_skills = ", ".join(sorted(list(set(all_skills)))) if all_skills else None
            
            jd_scraped_count += 1
            total_jobs_scraped += 1
            
            # Insert / Update
            execute_with_retry(cursor, conn, '''
                INSERT INTO jobs (
                    job_id, title, company_name, company_logo, industry, salary,
                    location, experience_required, level,
                    job_status, scraped_at, last_seen_at, url,
                    job_description, requirements, benefits, skills
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    company_logo = COALESCE(NULLIF(excluded.company_logo,''), company_logo),
                    salary = excluded.salary,
                    experience_required = excluded.experience_required,
                    level = excluded.level,
                    job_description = excluded.job_description,
                    requirements = excluded.requirements,
                    benefits = excluded.benefits,
                    last_seen_at = excluded.last_seen_at,
                    job_status = 'OPEN',
                    skills = excluded.skills
            ''', (
                job_id, job['title'], job['company_name'], job['company_logo'], 'ITviec', salary,
                job['location'], exp, job['level'],
                now_str, now_str, job['job_url'], jd, req, ben, final_skills
            ))
            
            print(f"    [+] {job['title']} | Sal: {salary} | Exp: {exp}")
            
            # Rate limiting
            if jd_scraped_count % 10 == 0:
                print(f"    [⏸] Nghỉ 5s sau {jd_scraped_count} JDs...")
                time.sleep(random.uniform(4.0, 6.0))
            else:
                time.sleep(random.uniform(1.0, 2.0))
                
    # Cleanup closed jobs for ITviec
    print("\n🧹 Đang dọn dẹp các Job đã đóng...")
    execute_with_retry(cursor, conn, "UPDATE jobs SET job_status = 'CLOSED' WHERE last_seen_at < datetime('now', '-3 days') AND industry = 'ITviec'", None)
    print(f"✅ Đã đánh dấu CLOSED các jobs ITviec không còn xuất hiện.")
    conn.close()
    print(f"\n🎉 HOÀN THÀNH TOÀN BỘ QUÁ TRÌNH CÀO! (Đã cào mới: {total_jobs_scraped} JDs)")

if __name__ == "__main__":
    main()
