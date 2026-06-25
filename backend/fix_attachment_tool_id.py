import sqlite3

conn = sqlite3.connect('tooling.db')
cursor = conn.execute('PRAGMA table_info(attachments)')
cols = [row[1] for row in cursor.fetchall()]
print('当前字段:', cols)

# SQLite不支持直接ALTER COLUMN，需要重建表
# 检查是否有NOT NULL约束
cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='attachments'")
sql = cursor.fetchone()[0]
print('表结构:', sql)

if 'tool_id INTEGER NOT NULL' in sql or '"tool_id" INTEGER NOT NULL' in sql:
    print('需要修改 tool_id 为可空...')
    # 备份数据
    conn.execute('CREATE TABLE attachments_backup AS SELECT * FROM attachments')
    
    # 重建表
    conn.execute('DROP TABLE attachments')
    conn.execute('''
        CREATE TABLE attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id INTEGER REFERENCES tools(id),
            file_name VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_type VARCHAR(50),
            file_size INTEGER,
            upload_time DATETIME,
            uploader VARCHAR(80)
        )
    ''')
    
    # 恢复数据
    conn.execute('''
        INSERT INTO attachments 
        SELECT id, tool_id, file_name, file_path, file_type, file_size, upload_time, uploader 
        FROM attachments_backup
    ''')
    
    # 删除备份表
    conn.execute('DROP TABLE attachments_backup')
    conn.commit()
    print('✅ tool_id 已改为可空')
else:
    print('✅ tool_id 已是可空')

conn.close()
