import re

with open('D:\\tooling-management\\backend\\templates\\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
for i, l in enumerate(lines):
    if '用户管理' in l or '角色' in l or 'addUser' in l or '新建用户' in l:
        print(f'L{i+1}: {l.strip()[:200]}')
