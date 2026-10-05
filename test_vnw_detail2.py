from DrissionPage import ChromiumPage, ChromiumOptions
import time

co = ChromiumOptions()
co.headless(False)
co.set_argument("--disable-blink-features=AutomationControlled")
page = ChromiumPage(co)
page.get("https://www.vietnamworks.com/truong-phong-kinh-doanh-sale-manager-it-product-1688622-jv")
page.wait.load_start()
time.sleep(4)

print("Title:", page.ele("css:h1").text if page.ele("css:h1") else "Not found")

# Try to dump the whole text to see where salary/location is
text = page.html
if "Thương lượng" in text:
    print("Found salary string in HTML!")
if "Mô tả công việc" in text:
    print("Found JD string in HTML!")
    
# Let's find elements by text
for e in page.eles('xpath://*[contains(text(), "Thương lượng")]'):
    print("Salary element:", e.tag, e.attr("class"), e.text)

for e in page.eles('xpath://*[contains(text(), "Hồ Chí Minh")]'):
    print("Location element:", e.tag, e.attr("class"), e.text)
    
page.quit()
