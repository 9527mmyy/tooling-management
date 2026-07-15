import sqlite3, os
db = os.path.join(os.path.dirname(__file__), 'tooling.db')
conn = sqlite3.connect(db)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cursor.fetchall()]
print('所有表:', tables)
for t in tables:
    cursor.execute(f'PRAGMA table_info({t})')
    cols = [r[1] for r in cursor.fetchall()]
    print(f'{t}: {cols}')
conn.close()
