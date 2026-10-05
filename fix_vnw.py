with open("scrapers/scraper_vnw.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "lines = [L.strip() for L in (card.text or" in line:
        lines[i] = "        lines = [L.strip() for L in (card.text or \"\").split('\\n') if L.strip()]\n"
    if "') if L.strip()]" in line:
        lines[i] = ""

with open("scrapers/scraper_vnw.py", "w") as f:
    f.writelines(lines)
