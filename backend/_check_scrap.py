with open(r'D:\tooling-management\backend\templates\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Find scrapTool-related confirm areas
for keyword in ['确定报废', '批准报废', '拒绝报废']:
    idx = text.find(keyword)
    if idx >= 0:
        print(f"\n=== Found '{keyword}' at pos {idx} ===")
        # Show surrounding 100 chars with Unicode info
        start = max(0, idx - 15)
        end = min(len(text), idx + 100)
        block = text[start:end]
        for pos, c in enumerate(block):
            actual_pos = start + pos
            if c in ('`', '\\', '$') or ord(c) > 127:
                print(f"  {actual_pos}: U+{ord(c):04X} {repr(c)}", end="")
                # Show context line
                line_start = max(0, text.rfind('\n', 0, actual_pos) + 1)
                line_end = text.find('\n', actual_pos)
                if line_end < 0: line_end = len(text)
                print(f"  Line: {text[line_start:line_end].strip()[:100]}")
