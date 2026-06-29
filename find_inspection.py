with open(r'D:\tooling-management\backend\routes\tools.py', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if 'inspection' in line.lower() or '检定' in line or 'inspection' in line.lower():
        print(f'{i:4d}: {line.rstrip()[:120]}')