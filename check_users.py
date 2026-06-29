import sqlite3
conn = sqlite3.connect(r'D:\tooling-management\backend\tooling.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in cur.fetchall()])
try:
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()
    print(f"Users count: {len(rows)}")
    for r in rows:
        print(f"  {r}")
except Exception as e:
    print(f"Error: {e}")
conn.close()
