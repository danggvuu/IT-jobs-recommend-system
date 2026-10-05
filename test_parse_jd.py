from DrissionPage import WebPage, ChromiumOptions
import os, sys, time
from bs4 import BeautifulSoup

def scrape_jd(page, job_url: str):
    page.get(job_url)
    time.sleep(3)
    html = page.html
    soup = BeautifulSoup(html, 'html.parser')

    jd = ''
    req = ''
    ben = ''

    for section in soup.select('.box-job-information-detail-item'):
        t_el = section.select_one('.box-job-information-detail-item__title--title') or section.select_one('h2')
        if not t_el:
            print("No title element found in a section")
            continue
        t = t_el.get_text(strip=True).lower()
        print(f"DEBUG: Found title '{t}'")

        if t in ('tổng quan', 'job details'):
            continue

        c_el = section.select_one('.box-job-information-detail-item__text')
        if c_el:
            content = c_el.get_text(separator='\n', strip=True)
            if 'mô tả' in t or 'job description' in t:
                jd = content
                print("-> Matched JD")
            elif 'yêu cầu' in t or 'candidate requirement' in t or 'requirements' in t:
                req = content
                print("-> Matched REQ")
            elif 'quyền lợi' in t or 'benefits' in t:
                ben = content
                print("-> Matched BEN")
        else:
            print("No content element (.box-job-information-detail-item__text) found for this section")
            
    print(f"JD len: {len(jd)}, REQ len: {len(req)}, BEN len: {len(ben)}")

def main():
    co = ChromiumOptions()
    co.headless(False)
    co.set_argument("--disable-blink-features=AutomationControlled")
    if sys.platform == 'darwin':
        co.set_browser_path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    co.set_user_data_path(os.path.join(os.path.dirname(__file__), 'scrapers', 'chrome_profile'))
    
    page = WebPage(mode='d', chromium_options=co)
    scrape_jd(page, 'https://www.topcv.vn/viec-lam/erp-consultant-sales/2043202.html')
    page.quit()

if __name__ == '__main__':
    main()
