with open('recommendation/01_cleaning.py', 'r') as f:
    content = f.read()
    
old_loc = 'if "hà nội" in loc: return "Hà Nội"'
new_loc = 'if "hà nội" in loc or "ha noi" in loc: return "Hà Nội"'
content = content.replace(old_loc, new_loc)

old_loc2 = 'if "hồ chí minh" in loc or "hcm" in loc or "tp.hcm" in loc: return "TP.HCM"'
new_loc2 = 'if "hồ chí minh" in loc or "ho chi minh" in loc or "hcm" in loc or "tp.hcm" in loc: return "TP.HCM"'
content = content.replace(old_loc2, new_loc2)

old_loc3 = 'if "đà nẵng" in loc: return "Đà Nẵng"'
new_loc3 = 'if "đà nẵng" in loc or "da nang" in loc: return "Đà Nẵng"'
content = content.replace(old_loc3, new_loc3)

with open('recommendation/01_cleaning.py', 'w') as f:
    f.write(content)
