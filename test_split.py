import sqlite3

conn = sqlite3.connect('database/job_market.sqlite')
cursor = conn.cursor()

cursor.execute("SELECT job_id, job_description FROM jobs WHERE industry = 'ITviec'")
jobs = cursor.fetchall()

found_skills = 0
found_yeucau = 0
found_requirement = 0
other = 0

for jid, jd in jobs:
    jd = jd.lower()
    if 'your skills and experience' in jd:
        found_skills += 1
    elif 'yêu cầu công việc' in jd:
        found_yeucau += 1
    elif 'requirements' in jd:
        found_requirement += 1
    else:
        other += 1
        
print(f"Total: {len(jobs)}")
print(f"Your Skills and Experience: {found_skills}")
print(f"Yêu cầu công việc: {found_yeucau}")
print(f"Requirements: {found_requirement}")
print(f"Other: {other}")

