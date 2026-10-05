from DrissionPage import ChromiumPage, ChromiumOptions
import time

co = ChromiumOptions()
co.headless(True)
page = ChromiumPage(co)
page.get("https://www.vietnamworks.com/viec-lam?q=it-software")
page.wait.load_start()
time.sleep(3)

cards = page.eles("css:div[data-job-card-version]")
for card in cards[:3]:
    print("---")
    print(repr(card.text))
page.quit()
