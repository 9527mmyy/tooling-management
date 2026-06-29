"""检查数据库中的配置数据"""
import sqlite3

conn = sqlite3.connect('tooling.db')
cursor = conn.cursor()

# 检查 system_configs 表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_configs'")
if cursor.fetchone():
    print("system_configs 表存在")
    cursor.execute("SELECT * FROM system_configs")
    rows = cursor.fetchall()
    print(f"共有 {len(rows)} 条记录:")
    for row in rows:
        print(f"  {row}")
else:
    print("system_configs 表不存在")

conn.close()
