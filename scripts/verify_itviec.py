import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "job_market.sqlite")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM jobs WHERE industry='ITviec'")
total_itviec = cursor.fetchone()[0]

print(f"Tổng số job ITviec: {total_itviec}")

conn.close()
