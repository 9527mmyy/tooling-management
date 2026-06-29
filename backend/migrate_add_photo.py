"""迁移脚本：为 tools 表添加 photo_path 字段"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'tooling.db')

if not os.path.exists(db_path):
    print(f'❌ 数据库不存在: {db_path}')
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查字段是否已存在
cursor.execute("PRAGMA table_info(tools)")
columns = [col[1] for col in cursor.fetchall()]

if 'photo_path' not in columns:
    cursor.execute("ALTER TABLE tools ADD COLUMN photo_path VARCHAR(500)")
    conn.commit()
    print('✅ 已添加 photo_path 字段')
else:
    print('ℹ️ photo_path 字段已存在，跳过')

conn.close()
