with open(r'D:\tooling-management\backend\templates\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the three pages content sections
for page in ['tools', 'borrows', 'inspections']:
    idx = content.find(f"currentPage === '{page}'")
    if idx < 0:
        idx = content.find(f'currentPage==="{page}"')
    if idx >= 0:
        print(f'=== {page} at pos {idx} ===')
        # show 500 chars
        snippet = content[idx:idx+500]
        print(snippet)
        print()
