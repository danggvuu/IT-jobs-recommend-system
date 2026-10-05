from DrissionPage import ChromiumPage, ChromiumOptions
import time

co = ChromiumOptions()
co.headless(False)
page = ChromiumPage(co)
page.get("https://www.vietnamworks.com/truong-phong-kinh-doanh-sale-manager-it-product-1688622-jv")
page.wait.load_start()
time.sleep(3)

print("Title:", page.ele("css:h1").text if page.ele("css:h1") else "")
print("Company:", page.ele("css:.company-name, .employer-info h2").text if page.ele("css:.company-name, .employer-info h2") else "")
for item in page.eles("css:.summary-item"):
    print("Item:", item.text.replace("\n", " "))
page.quit()
