with open(r'D:\tooling-management\backend\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Check the scrapTool area for backslash-backtick
idx = text.find('MessageBox.confirm', 7500)
if idx >= 0:
    block = text[idx:idx+300]
    for pos, c in enumerate(block):
        actual_pos = idx + pos
        if ord(c) < 32 or ord(c) > 127 or c == '\\' or c == '`' or c == '$':
            print(f"  pos {actual_pos}: U+{ord(c):04X} repr={repr(c)}")
    print()
    print("Context:")
    print(block[:200])
