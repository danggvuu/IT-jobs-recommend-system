from DrissionPage import WebPage, ChromiumOptions
import os, sys, time
from bs4 import BeautifulSoup

def main():
    co = ChromiumOptions()
    co.headless(False)
    co.set_argument("--disable-blink-features=AutomationControlled")
    if sys.platform == 'darwin':
        co.set_browser_path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    co.set_user_data_path(os.path.join(os.path.dirname(__file__), 'scrapers', 'chrome_profile'))
    
    page = WebPage(mode='d', chromium_options=co)
    page.get('https://www.topcv.vn/viec-lam/erp-consultant-sales/2043202.html')
    time.sleep(3)
    
    soup = BeautifulSoup(page.html, 'html.parser')
    
    sections = soup.select('.box-job-information-detail-item')
    print(f"Found {len(sections)} sections")
    for idx, s in enumerate(sections):
        title = s.select_one('h2') or s.select_one('h3') or s.select_one('.box-job-information-detail-item__title')
        title_text = title.get_text(strip=True) if title else 'No title'
        print(f"Section {idx}: {title_text}")
        
    # Also dump all h2 and h3
    print("All h2:")
    for h2 in soup.find_all('h2'):
        print(h2.get_text(strip=True))
    print("All h3:")
    for h3 in soup.find_all('h3'):
        print(h3.get_text(strip=True))
        
    page.quit()

if __name__ == '__main__':
    main()
