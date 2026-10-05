import sqlite3
import pandas as pd
import numpy as np
import re
import os

def clean_data():
    db_path = "database/job_market.sqlite"
    if not os.path.exists(db_path):
        print(f"Không tìm thấy file DB tại {db_path}")
        return

    # 1. Đọc dữ liệu từ SQLite
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM jobs WHERE job_status='OPEN'", conn)
    conn.close()

    initial_count = len(df)
    print(f"Số jobs ban đầu (OPEN): {initial_count}")

    # 2. Lọc bỏ job_description ngắn
    df = df[df['job_description'].str.len() >= 50]
    print(f"Số jobs sau khi lọc JD < 50 ký tự: {len(df)}")

    # 3. Chuẩn hóa các cột
    # Title & Company
    df['title'] = df['title'].str.strip().str.lower().str.title()
    df['company_name'] = df['company_name'].str.strip().str.title()

    # Salary extraction
    def extract_salary(salary_str):
        if pd.isna(salary_str) or salary_str.strip() == "":
            return None, None
        
        salary_str = str(salary_str).lower()
        if "thương lượng" in salary_str or "thỏa thuận" in salary_str:
            return None, None
        
        # Tìm các con số (có thể là thập phân)
        numbers = re.findall(r'(\d+(?:\.\d+)?|\d+(?:,\d+)?)', salary_str.replace(',', ''))
        numbers = [float(n) for n in numbers if n]
        
        if not numbers:
            return None, None
            
        min_sal = numbers[0]
        max_sal = numbers[-1] if len(numbers) > 1 else numbers[0]
        
        # Check đơn vị
        if "$" in salary_str or "usd" in salary_str:
            # Quy đổi ra VND (xấp xỉ 24.5k)
            min_sal = min_sal * 24.5 / 1000 if min_sal > 100 else min_sal * 24.5
            max_sal = max_sal * 24.5 / 1000 if max_sal > 100 else max_sal * 24.5
        elif "triệu" in salary_str or "tr" in salary_str:
            pass # Đã chuẩn triệu
        else:
            # VND thường số lớn (triệu -> triệu)
            if min_sal > 1000000:
                min_sal = min_sal / 1000000
                max_sal = max_sal / 1000000
                
        return min_sal, max_sal

    df['salary_min'], df['salary_max'] = zip(*df['salary'].apply(extract_salary))

    # Location mapping
    def map_location(loc):
        if pd.isna(loc): return "Khác"
        loc = str(loc).lower()
        if "hà nội" in loc or "ha noi" in loc: return "Hà Nội"
        if "hồ chí minh" in loc or "ho chi minh" in loc or "hcm" in loc or "tp.hcm" in loc: return "TP.HCM"
        if "đà nẵng" in loc or "da nang" in loc: return "Đà Nẵng"
        if "remote" in loc: return "Remote"
        return "Khác"
    df['location'] = df['location'].apply(map_location)

    # Level mapping
    def map_level(lvl):
        if pd.isna(lvl): return "Khác"
        lvl = str(lvl).lower()
        if re.search(r'manager|trưởng phòng|giám đốc|quản lý|giám sát', lvl): return "Manager"
        if re.search(r'senior|chuyên gia|trưởng nhóm', lvl): return "Senior"
        if re.search(r'middle', lvl): return "Middle"
        if re.search(r'fresher|intern|thực tập', lvl): return "Fresher"
        if re.search(r'junior|nhân viên|chuyên viên', lvl): return "Junior"
        return "Khác"
    df['level'] = df['level'].apply(map_level)

    # Experience required
    def extract_exp(exp_str):
        if pd.isna(exp_str): return 0
        exp_str = str(exp_str).lower()
        if "không yêu cầu" in exp_str or "chưa có" in exp_str: return 0
        match = re.search(r'(\d+)\s*năm', exp_str)
        if match:
            return int(match.group(1))
        return 0
    df['experience_required'] = df['experience_required'].apply(extract_exp)

    # 4. Cột mới
    df['full_text'] = df['job_description'].fillna('') + " " + df['requirements'].fillna('') + " " + df['benefits'].fillna('')
    df['full_text'] = df['full_text'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    def parse_skills(s):
        if pd.isna(s): return []
        parts = re.split(r'[,;]', str(s))
        return [p.strip().lower() for p in parts if p.strip()]
    df['skills_list'] = df['skills'].apply(parse_skills)

    # 5. Deduplication
    df['title_normalized'] = df['title'].str.lower().str.strip()
    df['company_normalized'] = df['company_name'].str.lower().str.strip()
    
    # Sort by full_text length (descending) to keep the most detailed job description
    df['text_len'] = df['full_text'].str.len()
    df = df.sort_values('text_len', ascending=False)
    
    # Group and aggregate
    dedup_df = df.groupby(['title_normalized', 'company_normalized'], as_index=False).agg({
        'job_id': 'first',
        'title': 'first',
        'company_name': 'first',
        'industry': lambda x: list(set(x)), # 'platforms'
        'salary_min': 'first',
        'salary_max': 'first',
        'location': 'first',
        'experience_required': 'first',
        'level': 'first',
        'full_text': 'first',
        'skills_list': 'first'
    })
    dedup_df.rename(columns={'industry': 'platforms'}, inplace=True)
    
    final_count = len(dedup_df)
    dedup_count = len(df) - final_count

    # 6. Lưu kết quả
    os.makedirs("database", exist_ok=True)
    dedup_df.to_pickle("database/jobs_cleaned.pkl")
    dedup_df.to_csv("database/jobs_cleaned.csv", index=False)

    # 7. In tóm tắt
    print(f"Số jobs sau khi dedup: {final_count}")
    print(f"Số jobs bị loại do trùng lặp nền tảng: {dedup_count}")
    
    print("\n--- Phân bố Location ---")
    print(dedup_df['location'].value_counts().head())
    
    print("\n--- Phân bố Level ---")
    print(dedup_df['level'].value_counts().head())

if __name__ == "__main__":
    clean_data()
