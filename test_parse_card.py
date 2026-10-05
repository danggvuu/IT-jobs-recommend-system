import re
text = """Mới Trưởng Phòng Kinh Doanh (Sale Manager) – IT Product
Urgent
HDWEBSOFT Co., Ltd
Thương lượng
Hồ Chí Minh
Cập nhật hôm nay
Giải Pháp Công Nghệ"""

def parse_card_text(text):
    lines = [L.strip() for L in text.split('\n') if L.strip()]
    
    # Remove 'Mới' from title if it exists
    title = lines[0]
    if title.startswith("Mới "):
        title = title[4:]
        
    salary = ""
    location = ""
    company = ""
    
    # Salary often contains 'Thương lượng' or numbers with 'Triệu', '$', 'USD', 'VND'
    for i, line in enumerate(lines[1:5], 1): # check lines 1 to 4
        if re.search(r'thương lượng|triệu|\$|usd|vnd|lên đến|tới', line.lower()):
            salary = line
            # usually location is right after salary
            if i + 1 < len(lines):
                location = lines[i+1]
            # usually company is right before salary, skipping badges
            if i - 1 >= 1:
                company = lines[i-1]
            # if company is 'Urgent', then company is actually i-2?
            # Wait, if line 1 is 'Urgent', line 2 is company, line 3 is salary
            break
            
    return {"title": title, "company": company, "salary": salary, "location": location}

print(parse_card_text(text))
