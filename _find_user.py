with open('D:\\tooling-management\\backend\\templates\\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
for i, l in enumerate(lines):
    if '"普通员工"' in l or '普通员工' in l or 'formatRole' in l or 'userForm' in l or 'openUserDialog' in l or 'viewer' in l:
        l2 = l.strip()[:200]
        if l2:
            print(f'L{i+1}: {l2}')
