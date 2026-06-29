import sqlite3
import os

db_path = 'tooling.db'
if not os.path.exists(db_path):
    print(f'❌ 数据库文件不存在: {db_path}')
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查tools表结构
cursor.execute('PRAGMA table_info(tools)')
columns = cursor.fetchall()

print('=' * 60)
print('tools 表字段结构')
print('=' * 60)
print(f'共 {len(columns)} 个字段:\n')

has_drawing_no = False
has_category = False
has_level = False

for col in columns:
    cid, name, ctype, notnull, default, pk = col
    print(f'  [{cid:2d}] {name:20s} 类型:{ctype:10s} {"NOT NULL" if notnull else "NULL":10s} 默认:{default}')

    if name == 'drawing_no':
        has_drawing_no = True
    if name == 'category':
        has_category = True
    if name == 'level':
        has_level = True

print('\n' + '=' * 60)
print('关键字段检查结果:')
print(f'  drawing_no (图号): {"✅ 存在" if has_drawing_no else "❌ 不存在"}')
print(f'  category (分类):   {"✅ 存在" if has_category else "❌ 不存在"}')
print(f'  level (等级):      {"✅ 存在" if has_level else "❌ 不存在"}')
print('=' * 60)

# 检查实际数据
print('\n样本数据检查（前3条）:')
cursor.execute('SELECT id, code, drawing_no, category, level, name FROM tools LIMIT 3')
rows = cursor.fetchall()
for row in rows:
    print(f'  ID={row[0]} code={row[1]} drawing_no={row[2]} category={row[3]} level={row[4]} name={row[5]}')

conn.close()
print('\n检查完成')
