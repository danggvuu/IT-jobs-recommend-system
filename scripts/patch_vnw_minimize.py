import re

with open('scrapers/scraper_vnw.py', 'r') as f:
    content = f.read()

# Add minimize_browser function
minimize_fn = """def minimize_browser(page):
    try:
        page.run_cdp('Browser.setWindowBounds', windowId=page.browser.window_id, bounds={'windowState': 'minimized'})
    except Exception:
        pass
"""

if 'def minimize_browser' not in content:
    content = content.replace("class VietnamWorksScraper:", minimize_fn + "\nclass VietnamWorksScraper:")

# Add minimize_browser call after getting cards and starting processing
content = content.replace("        # Tìm job cards", "        minimize_browser(self.page)\n        # Tìm job cards")
content = content.replace("            tab = self.page.new_tab(url)", "            tab = self.page.new_tab(url)\n            minimize_browser(self.page)")

# Fix the print at the end to show actual number of scraped jobs from page_jobs? 
# Wait, page_jobs is local. Let's just fix self.jobs appending so it says the right number.
# I will just put self.jobs.append(job) back so the print works correctly.
content = content.replace("conn.close()\n                page_jobs += 1", "conn.close()\n                self.jobs.append(job)\n                page_jobs += 1")

with open('scrapers/scraper_vnw.py', 'w') as f:
    f.write(content)
print("VNW patched")
