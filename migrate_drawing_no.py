import sqlite3
import os
from datetime import datetime

def check_and_migrate_db(db_path):
    """检查并迁移单个数据库"""
    print(f"\n{'='*70}")
    print(f"检查数据库: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"  ❌ 文件不存在")
        return False
    
    # 文件信息
    size = os.path.getsize(db_path)
    mtime = os.path.getmtime(db_path)
    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    print(f"  大小: {size:,} bytes")
    print(f"  修改时间: {mtime_str}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"  数据表: {tables}")
        
        if 'tools' not in tables:
            print(f"  ❌ tools表不存在")
            conn.close()
            return False
        
        # 检查tools表结构
        cursor.execute("PRAGMA table_info(tools)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"  tools表字段数: {len(columns)}")
        print(f"  字段列表: {columns}")
        
        # 需要添加的字段
        fields_to_add = [
            ('drawing_no', 'TEXT'),
            ('category', 'TEXT'),
            ('level', 'TEXT DEFAULT "A类"')
        ]
        
        added = []
        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                print(f"    ⚠️  {field_name} 不存在，正在添加...")
                try:
                    cursor.execute(f"ALTER TABLE tools ADD COLUMN {field_name} {field_type}")
                    conn.commit()
                    added.append(field_name)
                    print(f"    ✅  {field_name} 添加成功")
                except Exception as e:
                    print(f"    ❌  {field_name} 添加失败: {e}")
            else:
                print(f"    ✅  {field_name} 已存在")
        
        # 检查是否有数据
        cursor.execute("SELECT COUNT(*) FROM tools")
        count = cursor.fetchone()[0]
        print(f"  数据条数: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, code, drawing_no, category, level FROM tools LIMIT 3")
            rows = cursor.fetchall()
            print(f"  样本数据 (前3条):")
            for row in rows:
                print(f"    ID={row[0]} code={row[1]} drawing_no={row[2]} category={row[3]} level={row[4]}")
        
        conn.close()
        
        if added:
            print(f"  ✅ 迁移完成！添加了字段: {added}")
        else:
            print(f"  ✅ 所有字段已存在，无需迁移")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
        return False

# 主程序
if __name__ == '__main__':
    print("="*70)
    print("工装管理系统数据库迁移工具")
    print("="*70)
    
    dbs = [
        r'D:\tooling-management\tooling.db',
        r'D:\tooling-management\backend\tooling.db'
    ]
    
    for db_path in dbs:
        check_and_migrate_db(db_path)
    
    print("\n"+ "="*70)
    print("所有数据库检查完成！")
    print("="*70)
