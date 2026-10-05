from DrissionPage import ChromiumPage, ChromiumOptions
import time
import re

co = ChromiumOptions()
co.headless(False)
co.set_argument("--disable-blink-features=AutomationControlled")
page = ChromiumPage(co)
page.get("https://www.vietnamworks.com/viec-lam?q=it-software")
page.wait.load_start()
time.sleep(3)

cards = page.eles("css:div[data-job-card-version]")
print(f"Found {len(cards)} cards")

for i, card in enumerate(cards[:2]):
    html = card.html
    title_el = card.ele("css:h2")
    title = title_el.text if title_el else ""
    # find salary
    salary_el = card.ele("css:span[class*='salary'], div[class*='salary']")
    salary = salary_el.text if salary_el else ""
    print(f"[{i}] Title: {title}")
    print(f"[{i}] Salary: {salary}")
    
    # regex for Mới
    clean_title = re.sub(r'^Mới\s+', '', title)
    print(f"[{i}] Clean Title: {clean_title}")
    
    # print all texts to see what's there
    print(f"[{i}] Texts:", card.text.replace('\n', ' | '))

page.quit()
