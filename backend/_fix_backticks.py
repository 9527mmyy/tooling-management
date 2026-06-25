import re

path = r'D:\tooling-management\backend\templates\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and count all `\`` (backslash-backtick) in the file
backtick_bad = [(m.start(), m.group()) for m in re.finditer(r'\\([`$])', content)]
print(f"Found {len(backtick_bad)} backslash-escaped template characters:")
for pos, match in backtick_bad:
    ctx_start = max(0, pos-30)
    ctx_end = min(len(content), pos+30)
    ctx = content[ctx_start:ctx_end].replace('\n', '\\n')
    print(f"  pos {pos}: ...{ctx}...")

# Replace all `\`` with `` ` `` and `\$` with `$` 
# But only in the JavaScript section (between <script> and </script>)
script_start = content.find('<script>', 360)
script_end = content.find('</script>', script_start)
js = content[script_start:script_end]

# Replace escaped backticks and dollars in JS
fixed_js = js.replace('\\`', '`').replace('\\$', '$')

if fixed_js != js:
    content = content[:script_start] + fixed_js + content[script_end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\nReplaced {sum(1 for c in fixed_js if c == '`') - sum(1 for c in js if c == '`')} escaped backticks")
    print("File updated successfully")
else:
    print("\nNo changes needed - no escaped backticks found in JS")
