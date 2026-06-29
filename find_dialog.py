with open(r'D:\tooling-management\backend\templates\index.html', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in ['新增工装', '使用分厂', '使用班组', '领用人', '购置日期', '完工时间', 'el-dialog', 'toolForm']):
        print(f'{i:5d}: {line.rstrip()[:120]}')