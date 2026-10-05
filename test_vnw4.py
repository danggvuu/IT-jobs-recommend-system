from DrissionPage import ChromiumPage, ChromiumOptions
import time
import re

co = ChromiumOptions()
co.headless(True)
page = ChromiumPage(co)
page.get("https://www.vietnamworks.com/viec-lam?q=it-software")
page.wait.load_start()
time.sleep(3)

cards = page.eles("css:div[data-job-card-version]")
for i, card in enumerate(cards[:2]):
    lines = [L.strip() for L in (card.text or "").split('\n') if L.strip()]
    print("--- CARD ---")
    for j, L in enumerate(lines):
        print(f"[{j}]: {L}")
    salary = ""
    location = ""
    for k, line in enumerate(lines[1:6], 1):
        if re.search(r'thương lượng|triệu|\$|usd|vnd|lên đến|tới|thỏa thuận', line.lower()):
            salary = line
            if k + 1 < len(lines): location = lines[k+1]
            break
    print("EXTRACTED Salary:", salary)
    print("EXTRACTED Location:", location)

page.quit()
