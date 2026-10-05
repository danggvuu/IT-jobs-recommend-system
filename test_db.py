import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "job_market.sqlite")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT * FROM jobs WHERE industry='VietnamWorks'")
print("Found jobs:", len(cursor.fetchall()))
