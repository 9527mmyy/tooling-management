import sqlite3

conn = sqlite3.connect('tooling.db')
cursor = conn.execute('PRAGMA table_info(tools)')
cols = [row[1] for row in cursor.fetchall()]
print('当前字段:', cols)

if 'category' not in cols:
    conn.execute('ALTER TABLE tools ADD COLUMN category VARCHAR(10) DEFAULT "A类"')
    conn.commit()
    print('✅ category 列已添加')
else:
    print('✅ category 列已存在')

conn.close()
