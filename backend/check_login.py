"""检查登录问题"""
import sqlite3
import hashlib
from werkzeug.security import check_password_hash

db = sqlite3.connect('tooling.db')
cur = db.execute('SELECT id, username, role, password_hash FROM users')
users = cur.fetchall()
print('用户数:', len(users))
for u in users:
    print(f'  id={u[0]} name={u[1]} role={u[2]} hash={u[3][:40]}...')
    # 测试密码
    for pw in ['admin', '123456', 'admin123', 'moy']:
        if check_password_hash(u[3], pw):
            print(f'    ✅ 密码匹配: {pw}')
            break
    else:
        print('    ❌ 常用密码都不匹配')

cur = db.execute('PRAGMA table_info(users)')
print('\nusers表字段:')
for c in cur.fetchall():
    print(f'  {c[1]} ({c[2]})')

# 检查登录接口
from app import app
with app.test_client() as cli:
    r = cli.post('/api/auth/login', json={'username': 'admin', 'password': 'admin'})
    print(f'\n登录接口响应: status={r.status_code}, body={r.get_data(as_text=True)}')

db.close()
