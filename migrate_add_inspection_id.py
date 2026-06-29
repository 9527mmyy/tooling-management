import sqlite3, os, sys

db_path = r'D:\tooling-management\backend\tooling.db'
if not os.path.exists(db_path):
    db_path = r'D:\tooling-management\tooling.db'
print('数据库:', db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 检查 attachments 表是否有 inspection_id 列
cur.execute("PRAGMA table_info(attachments)")
columns = [c[1] for c in cur.fetchall()]
print('现有列:', columns)

if 'inspection_id' not in columns:
    cur.execute("ALTER TABLE attachments ADD COLUMN inspection_id INTEGER REFERENCES inspections(id)")
    print('✅ 已添加 inspection_id 列')
else:
    print('ℹ️  inspection_id 列已存在')

conn.commit()
conn.close()
print('迁移完成')
