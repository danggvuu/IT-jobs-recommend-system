from DrissionPage import ChromiumPage, ChromiumOptions
import time

co = ChromiumOptions()
co.headless(False)
page = ChromiumPage(co)
page.get("https://www.vietnamworks.com/truong-phong-kinh-doanh-sale-manager-it-product-1688622-jv")
page.wait.load_start()
time.sleep(3)

print("H1s:")
for e in page.eles('tag:h1'): print(e.text)
print("\nH2s:")
for e in page.eles('tag:h2'): print(e.text)
print("\nSummary items:")
for e in page.eles('.summary-item'): print(e.text)
page.quit()
