import sqlite3
import re
import os
import time
import random
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from DrissionPage import WebPage, ChromiumOptions
from DrissionPage.errors import PageDisconnectedError

# ================= CẤU HÌNH =================
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "job_market.sqlite")

CATEGORIES = {
    "IT Phần mềm": "https://www.topcv.vn/tim-viec-lam-it?type_keyword=1&sba=1",
    "Marketing": "https://www.topcv.vn/tim-viec-lam-marketing-pr-c10008",
    "Sales": "https://www.topcv.vn/tim-viec-lam-kinh-doanh-ban-hang-c10011"
}

MAX_PAGES_PER_CATEGORY = 500  # Cào tối đa 500 trang mỗi ngành. Gặp trang trống tự động dừng.

# ================= THIẾT LẬP DATABASE =================
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


def init_browser():
    """Khởi tạo lại trình duyệt Chromium"""
    co = ChromiumOptions()
    co.headless(False)  # Hiện giao diện
    co.set_argument("--disable-blink-features=AutomationControlled")
    if sys.platform == 'darwin':
        co.set_browser_path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    co.set_user_data_path(os.path.join(os.path.dirname(__file__), 'chrome_profile'))
    return WebPage(mode='d', chromium_options=co)

def minimize_browser(page):
    try:
        page.set.window.mini()
        if sys.platform == 'darwin':
            os.system('''osascript -e 'tell application "System Events" to set visible of process "Google Chrome" to false' ''')
    except Exception:
        pass



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
def wait_for_cf(page, timeout=20):
    """Đợi trang vượt qua Cloudflare - kiểm tra có job item chưa."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            html = page.html
            if 'job-item-search-result' in html or 'job-item-default' in html:
                return True
        except Exception:
            pass
        # Còn đang ở CF challenge
        time.sleep(1)
    return False


def extract_jobs_from_html(html: str):
    """Dùng BeautifulSoup để bóc tách thông tin cơ bản từ HTML trang list."""
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    for card in soup.select('.job-item-search-result, .job-item-default, .job-item'):
        # URL & title
        a_tag = card.select_one('h3.title a, .title a')
        if not a_tag:
            continue
        job_url = a_tag.get('href', '')
        if not job_url or '/viec-lam/' not in job_url:
            continue
        # Bỏ query string (ta_source=...) nếu có
        job_url = job_url.split('?')[0]
        job_id = job_url.split('/')[-1].split('.')[0]
        title = a_tag.get_text(strip=True)

        # Logo công ty: ưu tiên src (đã load) > data-src (lazy)
        img = card.select_one('.avatar img, .box-company-logo img')
        company_logo = ''
        if img:
            company_logo = img.get('src') or img.get('data-src') or ''

        # Tên công ty
        company_tag = card.select_one('a.company, .company-name, .company-title')
        company_name = company_tag.get_text(strip=True) if company_tag else ''

        # Lương
        salary_tag = card.select_one('label.title-salary, .salary, .title-salary')
        salary = salary_tag.get_text(strip=True) if salary_tag else ''

        # Địa điểm
        loc_tag = card.select_one('label.address, .address, .title-address')
        location = loc_tag.get_text(strip=True) if loc_tag else ''

        results.append({
            'job_id': job_id,
            'job_url': job_url,
            'title': title,
            'company_name': company_name,
            'company_logo': company_logo,
            'salary': salary,
            'location': location,
        })
    return results


def scrape_jd(page, job_url: str):
    """
    Điều hướng tab CHÍNH (đã vượt CF) đến trang JD và bóc tách nội dung.
    Trả về (experience, level, jd, req, ben).
    """
    page.get(job_url)
    
    # Chờ trang JD load xong - sửa lại dùng eles_loaded thay vì ele_loaded cho đúng version
    try:
        page.wait.eles_loaded('css:.box-header-job-list-info__item, .box-job-information-detail', timeout=12)
    except Exception:
        pass
    
    time.sleep(random.uniform(0.5, 1.2))
    html = page.html
    soup = BeautifulSoup(html, 'html.parser')

    experience = ''
    level = ''
    jd = ''
    req = ''
    ben = ''

    # --- Kinh nghiệm từ header ---
    for hi in soup.select('.box-header-job-list-info__item'):
        title_el = hi.select_one('.list-info__content__title')
        if title_el and ('kinh nghiệm' in title_el.text.lower() or 'experience' in title_el.text.lower()):
            desc_el = hi.select_one('.list-info__content__desc')
            if desc_el:
                experience = desc_el.get_text(strip=True)
            break

    # --- Mô tả / Yêu cầu / Quyền lợi ---
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

        # Cấp bậc
        if 'thông tin chung' in t or 'general info' in t:
            for info in section.select('.box-job-information-general-info-list__item'):
                it = info.select_one('.box-job-information-general-info-list__item--content-title')
                if it and ('cấp bậc' in it.text.lower() or 'level' in it.text.lower()):
                    id_el = info.select_one('.box-job-information-general-info-list__item--content-desc')
                    if id_el:
                        level = id_el.get_text(strip=True)
                    break

    # Lấy skills từ required-tags
    skills = []
    for tag_content in soup.select('.required-tag__content'):
        text = tag_content.get_text(separator=', ', strip=True)
        # Loại bỏ các tiêu đề như 'Kiến thức ngành', 'Kỹ năng cần có', v.v. nếu cần, 
        # nhưng text lấy được thường có dạng "Kỹ năng cần có Git, MySQL..." 
        # Ta có thể lấy hết và gom lại. 
        # Để sạch hơn, thay vì lấy thẳng text, ta lấy các text node sau khi loại bỏ thẻ h3 hoặc tiêu đề.
        # Thực ra the html structure is: text node inside div.
        # Just simple append for now.
        if text:
            # Loại bỏ 'Kiến thức ngành', 'Kỹ năng cần có', 'Kỹ năng nên có', 'Phúc lợi'
            clean_text = text
            for prefix in ['Kiến thức ngành', 'Kỹ năng cần có', 'Kỹ năng nên có', 'Phúc lợi']:
                if clean_text.startswith(prefix):
                    clean_text = clean_text[len(prefix):].strip(', ')
            if clean_text:
                skills.append(clean_text)
                
    skills_str = ", ".join(skills) if skills else ""

    # Fallback nếu không tìm thấy
    if not jd and not req and not ben:
        parent = soup.select_one('.box-job-information-detail')
        if parent:
            jd = parent.get_text(separator='\n', strip=True)

    return experience, level, jd, req, ben, skills_str


# ================= HÀM CHÍNH =================
def main():
    conn = setup_db()
    cursor = conn.cursor()

    print("🚀 Đang khởi động DrissionPage WebPage để vượt Cloudflare...")
    page = init_browser()

    # Warm-up: load trang chủ để CF nhận ra "user bình thường"
    try:
        page.get("https://www.topcv.vn/tim-viec-lam-it-phan-mem-c10026")
        time.sleep(4)  # Đợi mượt qua CF
        print("✅ Đã vượt Cloudflare thành công bằng Trình duyệt thật!")
    except Exception as e:
        print(f"Lỗi khi warm-up: {e}")

    minimize_browser(page)

    for industry, base_url in CATEGORIES.items():
        print(f"\n🌟 Bắt đầu cào ngành: {industry}")
        jd_scraped_count = 0

        for page_num in range(1, MAX_PAGES_PER_CATEGORY + 1):
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            url = f"{base_url}&page={page_num}" if "?" in base_url else f"{base_url}?page={page_num}"
            print(f"  👉 Đang cào {industry} - Trang {page_num}...")

            # ── Load trang list ── (Bọc Try Catch phòng khi page crashed)
            try:
                page.get(url)
            except Exception as e:
                print(f"  [!] Trình duyệt bị văng (Disconnect/Crash). Đang khởi động lại... ({e})")
                try: page.quit() 
                except: pass
                time.sleep(3)
                page = init_browser()
                minimize_browser(page)
                page.get(url)
                
            # Đợi CF qua và job list hiện ra
            cf_ok = wait_for_cf(page, timeout=20)
            if not cf_ok:
                print(f"  ⚠️ Trang {page_num} bị CF chặn quá lâu, thử sleep 10s...")
                time.sleep(10)
                cf_ok = wait_for_cf(page, timeout=15)
                if not cf_ok:
                    print(f"  ⛔ Bỏ qua trang {page_num} do CF.")
                    continue

            minimize_browser(page)
            
            try:
                html_list = page.html
            except Exception:
                # Page crashed while getting HTML
                continue

            # ── Phase 1: Extract metadata từ HTML bằng BS4 (không cần tab phụ) ──
            jobs_info = extract_jobs_from_html(html_list)
            if not jobs_info:
                print(f"  ⚠️ Trang {page_num} không có data hoặc đã hết trang.")
                break

            print(f"  📋 Tìm thấy {len(jobs_info)} jobs, bắt đầu cào chi tiết...")

            # ── Phase 2: Cào JD bằng tab CHÍNH (đã vượt CF) ──
            for job_info in jobs_info:
                job_id = job_info['job_id']
                job_url = job_info['job_url']
                title = job_info['title']
                company_name = job_info['company_name']
                company_logo = job_info['company_logo']
                salary = job_info['salary']
                location = job_info['location']

                try:
                    # Kiểm tra xem đã có JD chưa
                    cursor.execute(
                        "SELECT job_description, requirements, benefits, experience_required, level FROM jobs WHERE job_id = ?",
                        (job_id,)
                    )
                    existing = cursor.fetchone()

                    if existing and existing[0] and len(existing[0]) > 10:
                        # Đã có JD đầy đủ → chỉ cập nhật logo/lương/last_seen
                        jd, req, ben, experience, level = existing
                        print(f"    [~] DB đã có: {title}")
                        # Vẫn update logo/salary/last_seen phòng thay đổi
                        execute_with_retry(cursor, conn, '''
                            UPDATE jobs SET
                                company_logo = COALESCE(NULLIF(?, ''), company_logo),
                                salary = COALESCE(NULLIF(?, ''), salary),
                                last_seen_at = ?,
                                job_status = 'OPEN'
                            WHERE job_id = ?
                        ''', (company_logo, salary, now_str, job_id))
                        continue

                    # ── Cần cào JD: dùng tab CHÍNH ──
                    experience, level, jd, req, ben, skills_str = scrape_jd(page, job_url)

                    jd_scraped_count += 1
                    minimize_browser(page)

                    # Delay chống rate limit
                    if jd_scraped_count % 5 == 0:
                        print(f"    [⏸] Nghỉ dài sau {jd_scraped_count} JDs đã cào...")
                        time.sleep(random.uniform(3.0, 5.0))
                    else:
                        time.sleep(random.uniform(0.5, 1.5))

                    # Ghi DB
                    cursor.execute('''
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
                            skills = COALESCE(NULLIF(excluded.skills, ''), skills),
                            last_seen_at = excluded.last_seen_at,
                            job_status = 'OPEN'
                    ''', (
                        job_id, title, company_name, company_logo, industry, salary,
                        location, experience, level,
                        now_str, now_str, job_url, jd, req, ben, skills_str
                    ))
                    conn.commit()
                    print(f"    [+] {title} | Exp: {experience} | Level: {level}")

                except PageDisconnectedError as e:
                    # Bắt riêng lỗi Page Disconnected (Crash trình duyệt)
                    print(f"    [!] Trình duyệt bị văng ở job {title}. Đang tự động khôi phục...")
                    try: page.quit()
                    except: pass
                    time.sleep(3)
                    page = init_browser()
                    minimize_browser(page)
                except Exception as e:
                    err = str(e)
                    print(f"    [!] Lỗi job {title}: {err[:80]}")
                    time.sleep(5)
                    try:
                        page.get(url)
                        wait_for_cf(page, timeout=15)
                    except Exception:
                        pass

            print(f"  ✅ Hoàn thành trang {page_num} ({len(jobs_info)} jobs).")

    # Dọn dẹp Job cũ
    print("\n🧹 Đang dọn dẹp các Job đã đóng...")
    execute_with_retry(cursor, conn, "UPDATE jobs SET job_status = 'CLOSED' WHERE last_seen_at < datetime('now', '-3 days')")
    print(f"✅ Đã dọn dẹp các jobs cũ.")
    conn.close()
    try: page.quit() 
    except: pass
    print("\n🎉 HOÀN THÀNH TOÀN BỘ QUÁ TRÌNH CÀO!")


if __name__ == "__main__":
    main()
