import re
with open(r'D:\tooling-management\backend\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Find all backtick positions in the main script block
script_start = text.find('<script>', 360)
script_end = text.find('</script>', script_start)
js = text[script_start:script_end]

# Find all backticks and their context
for i, c in enumerate(js):
    if c == '`':
        ctx_start = max(0, i-20)
        ctx_end = min(len(js), i+30)
        ctx = js[ctx_start:ctx_end].replace('\n', '\\n')
        print(f'Backtick at JS offset {i}: ...{ctx}...')
