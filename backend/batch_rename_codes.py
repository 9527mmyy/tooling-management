"""批量更新工装编号
格式: GZ2026071501 ~ GZ2026071526
按ID顺序填充序号，01~26
"""
import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'tooling.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取所有工装，按ID正序
cursor.execute("SELECT id, code, name FROM tools ORDER BY id")
tools = cursor.fetchall()
print(f"共 {len(tools)} 条待更新\n")

# 生成新编号列表（用于检测冲突）
new_codes = [f"GZ20260715{i:02d}" for i in range(1, len(tools) + 1)]
print(f"新编号范围: {new_codes[0]} ~ {new_codes[-1]}\n")

# 预览变更
print(f"{'ID':<4} {'旧编号':<25} {'新编号':<15} {'名称'}")
print("-" * 80)
for i, (tid, old_code, name) in enumerate(tools):
    new_code = new_codes[i]
    changed = "✅" if old_code != new_code else "  (相同)"
    print(f"{tid:<4} {old_code:<25} {new_code:<15} {name}  {changed}")

# 确认无冲突（重复检测）
if len(new_codes) != len(set(new_codes)):
    print("❌ 错误：新编号存在重复！")
else:
    print(f"\n✅ 编号无重复，共 {len(new_codes)} 个")

# 执行更新
print("\n--- 执行更新 ---")
for i, (tid, old_code, name) in enumerate(tools):
    new_code = new_codes[i]
    if old_code != new_code:
        cursor.execute("UPDATE tools SET code = ? WHERE id = ?", (new_code, tid))
        print(f"  [{tid}] {old_code} → {new_code}")
    else:
        print(f"  [{tid}] {old_code} (无需修改)")

conn.commit()

# 验证
cursor.execute("SELECT id, code, name FROM tools ORDER BY id")
verify = cursor.fetchall()
print(f"\n--- 验证结果 (共 {len(verify)} 条) ---")
all_ok = True
for i, (tid, code, name) in enumerate(verify):
    expected = new_codes[i]
    status = "✅" if code == expected else f"❌ (期望{expected})"
    print(f"{i+1:02d}. [{tid}] {code}  {status}")
    if code != expected:
        all_ok = False

conn.close()
print(f"\n{'✅ 全部更新成功！' if all_ok else '❌ 有错误，请检查！'}")
