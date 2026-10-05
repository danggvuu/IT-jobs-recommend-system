with open('recommendation/01_cleaning.py', 'r') as f:
    content = f.read()
    
old_mgr = "if re.search(r'manager|trưởng phòng|giám đốc|quản lý', lvl): return \"Manager\""
new_mgr = "if re.search(r'manager|trưởng phòng|giám đốc|quản lý|giám sát', lvl): return \"Manager\""
content = content.replace(old_mgr, new_mgr)

old_snr = "if re.search(r'senior|chuyên gia', lvl): return \"Senior\""
new_snr = "if re.search(r'senior|chuyên gia|trưởng nhóm', lvl): return \"Senior\""
content = content.replace(old_snr, new_snr)

with open('recommendation/01_cleaning.py', 'w') as f:
    f.write(content)
