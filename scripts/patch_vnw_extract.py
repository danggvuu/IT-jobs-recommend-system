import re

with open('scrapers/scraper_vnw.py', 'r') as f:
    content = f.read()

new_extract = """    def _extract_job(self, card) -> dict:
        url_el = card.ele("css:h2 a")
        url = url_el.link if url_el else ""
        
        lines = [L.strip() for L in (card.text or "").split('\\n') if L.strip()]
        title = lines[0] if lines else ""
        if title.startswith("Mới "):
            title = title[4:]
            
        salary = ""
        location = ""
        company = ""
        
        for i, line in enumerate(lines[1:6], 1):
            if re.search(r'thương lượng|triệu|\$|usd|vnd|lên đến|tới|thỏa thuận', line.lower()):
                salary = line
                if i + 1 < len(lines):
                    location = lines[i+1]
                if i - 1 >= 1:
                    company = lines[i-1]
                break

        return {
            "title": title,
            "company": company,
            "salary": salary,
            "location": location,
            "url": url,
            "job_date": "",
            "source": "vnw",
            "scraped_at": "",
            "job_description": "",
            "requirements": "",
            "benefits": "",
            "level": ""
        }
"""

content = re.sub(r'    def _extract_job\(self, card\) -> dict:.*?        \}', new_extract, content, flags=re.DOTALL)

with open('scrapers/scraper_vnw.py', 'w') as f:
    f.write(content)
print("Patched _extract_job")
