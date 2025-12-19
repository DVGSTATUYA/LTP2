# run_schema.py
import sqlite3
with open('schema.sql', 'r', encoding='utf-8') as f:
    sql = f.read()
conn = sqlite3.connect('repair_requests.db')
conn.executescript(sql)
conn.close()
