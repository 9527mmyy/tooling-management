#!/usr/bin/env python3
"""
同步所有数据库，确保包含新字段（drawing_no, category, level）
"""
import os
import sqlite3

def check_and_add_columns(db_path):
    """检查数据库表结构，添加缺失的列"""
    if not os.path.exists(db_path):
        print(f"数据库不存在: {db_path}")
        return False
    
    print(f"\n检查数据库: {db_path}")
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查tools表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tools'")
    if not cursor.fetchone():
        print("  tools表不存在，跳过")
        conn.close()
        return False
    
    # 获取当前表结构
    cursor.execute("PRAGMA table_info(tools)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"  当前字段: {columns}")
    
    # 需要添加的字段
    new_columns = {
        'drawing_no': 'TEXT',
        'category': 'TEXT',
        'level': 'TEXT'
    }
    
    # 添加缺失的字段
    added = []
    for col_name, col_type in new_columns.items():
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE tools ADD COLUMN {col_name} {col_type}")
                added.append(col_name)
                print(f"  ✓ 已添加字段: {col_name}")
            except Exception as e:
                print(f"  ✗ 添加字段失败 {col_name}: {e}")
        else:
            print(f"  - 字段已存在: {col_name}")
    
    conn.commit()
    conn.close()
    
    if added:
        print(f"  成功添加 {len(added)} 个字段: {added}")
    else:
        print("  无需添加字段")
    
    return True

def main():
    # 可能的数据库路径
    db_paths = [
        r'D:\tooling-management\tooling.db',  # 根目录
        r'D:\tooling-management\backend\tooling.db',  # backend目录
    ]
    
    print("=" * 60)
    print("数据库同步工具")
    print("=" * 60)
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            check_and_add_columns(db_path)
        else:
            print(f"\n数据库不存在: {db_path}")
    
    print("\n" + "=" * 60)
    print("同步完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
