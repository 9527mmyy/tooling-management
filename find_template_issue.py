import re

with open(r'D:\tooling-management\backend\templates\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取 <div id="app"> 到 </div> 之间的内容
m = re.search(r'<div id="app">(.*?)</div>\s*<script>', content, re.DOTALL)
if not m:
    print('NO MATCH')
    exit(1)
template = m.group(1)
print(f'Template length: {len(template)}')

# 查找所有 v-for, v-if, :attr, @event 等
# 重点查找含 ] 的属性值
pattern = re.compile(r'(=")([^"]*)(")')
bracket_attrs = []
for match in pattern.finditer(template):
    val = match.group(2)
    if ']' in val or '[' in val:
        # 计算行号
        start = match.start()
        line_no = template[:start].count('\n') + 1
        bracket_attrs.append((line_no, val))

print(f'Found {len(bracket_attrs)} attrs with brackets:')
for ln, val in bracket_attrs:
    print(f'  Line {ln}: {val[:100]}')
