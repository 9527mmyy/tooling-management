import sqlite3

conn = sqlite3.connect('tooling.db')
cursor = conn.execute('PRAGMA table_info(tools)')
cols = [row[1] for row in cursor.fetchall()]
print('当前字段:', cols)

# 1. 重命名 category 为 level（如果存在旧的category）
if 'category' in cols and 'level' not in cols:
    conn.execute('ALTER TABLE tools RENAME COLUMN category TO level')
    conn.commit()
    print('✅ category 已重命名为 level')

# 2. 添加新字段
cursor = conn.execute('PRAGMA table_info(tools)')
cols = [row[1] for row in cursor.fetchall()]

if 'drawing_no' not in cols:
    conn.execute('ALTER TABLE tools ADD COLUMN drawing_no VARCHAR(100)')
    conn.commit()
    print('✅ drawing_no 列已添加')

if 'category' not in cols:
    conn.execute('ALTER TABLE tools ADD COLUMN category VARCHAR(50)')
    conn.commit()
    print('✅ category 列已添加(新)')

# 3. 确认最终字段
cursor = conn.execute('PRAGMA table_info(tools)')
final_cols = [row[1] for row in cursor.fetchall()]
print('最终字段:', final_cols)

conn.close()
