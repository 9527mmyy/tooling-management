"""
下次检定日期推算 —— 隔离环境端到端回归测试

用途
    验证「按等级 + 入库时间推算下次检定日期」这条链路的接口行为。
    覆盖：A 级半年 / B 级一年 / C 级不推算、加月后对齐月末、
          由 C 改为 A 后自动补算、已有检定记录不覆盖、显式传参优先。

原理
    复制 backend 的代码 + 用 SQLite .backup API 复制一份数据库到系统临时目录，
    加载该副本起 Flask test_client 跑接口，**完全不触碰生产库**。
    跑完自动删除临时目录。

用法
    cd D:\web_sys\tooling management system\backend
    venv\\Scripts\\python.exe devtools\\e2e_next_inspection_check.py

预期输出
    每个场景 [PASS]/[FAIL]，末尾汇总 "N / N 通过"。
"""
import os
import sys
import shutil
import sqlite3
import tempfile

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = tempfile.mkdtemp(prefix="tooling_e2e_")

# 无论正常结束还是中途崩溃，都清理临时目录。
# 之前只在脚本末尾 rmtree，运行中报错会留下一堆 tooling_e2e_* 残留目录。
import atexit
atexit.register(shutil.rmtree, T, True)

# 复制 backend 根目录下全部 .py 模块（含 login_guard.py 等）。
# 之前用写死的短名单，漏了 login_guard 导致 ModuleNotFoundError；
# 改为全量复制，此后新增模块无需再改这里。
for name in os.listdir(BACKEND):
    if name.endswith(".py"):
        shutil.copy2(os.path.join(BACKEND, name), os.path.join(T, name))


def copy_tree(src, dst):
    os.makedirs(dst, exist_ok=True)
    for name in os.listdir(src):
        if name == "__pycache__":
            continue
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if os.path.isdir(s):
            copy_tree(s, d)
        else:
            shutil.copy2(s, d)


for sub in ("routes", "templates", "static"):
    src = os.path.join(BACKEND, sub)
    if os.path.isdir(src):
        copy_tree(src, os.path.join(T, sub))

src = sqlite3.connect(os.path.join(BACKEND, "tooling.db"))
dst = sqlite3.connect(os.path.join(T, "tooling.db"))
src.backup(dst, pages=-1)
dst.close()
src.close()

sys.path.insert(0, T)
import app as appmod
from models import db, Tool

flask_app = appmod.app
flask_app.config["TESTING"] = True

c = flask_app.test_client()
r = c.post("/api/auth/login", json={"user_no": "admin", "password": "admin123"})
print("登录: HTTP %s  %s" % (r.status_code, (r.get_json() or {}).get("msg")))

results = []


def check(name, actual, expect):
    ok = (actual == expect)
    results.append(ok)
    print("  [%s] %s | 实际=%s 期望=%s" % ("PASS" if ok else "FAIL", name, actual, expect))


def new_tool(code, level, storage):
    r = c.post("/api/tools/", json={
        "code": code, "name": "E2E测试工装", "level": level,
        "storage_date": storage, "category": "其他类"
    })
    d = (r.get_json() or {}).get("data") or {}
    return d.get("id"), d.get("next_inspection_date")


def upd_tool(tid, payload):
    r = c.put("/api/tools/%d" % tid, json=payload)
    d = (r.get_json() or {}).get("data") or {}
    return d.get("next_inspection_date")


print("")
print("=== 场景测试（隔离库副本，不触碰生产数据）===")

tid1, nd1 = new_tool("E2E-A-001", "A", "2026-08-31")
check("新增 A 级 / 入库 2026-08-31 → 半年（月末对齐）", nd1, "2027-02-28")

tid2, nd2 = new_tool("E2E-C-001", "C", "2026-09-18")
check("新增 C 级 → 不推算", nd2, "")

tid3, nd3 = new_tool("E2E-B-001", "B", "2024-02-29")
check("新增 B 级 / 入库 2024-02-29 → 一年（闰日对齐）", nd3, "2025-02-28")

nd4 = upd_tool(tid2, {"level": "A"})
check("C 级改为 A 级 → 自动推算（核心场景）", nd4, "2027-03-18")

nd5 = upd_tool(tid1, {"remark": "只改备注"})
check("仅改其他字段 → 已有检定日期不被覆盖", nd5, "2027-02-28")

nd6 = upd_tool(tid1, {"next_inspection_date": "2030-01-01"})
check("显式传入下次检定日期 → 以其为准", nd6, "2030-01-01")

with flask_app.app_context():
    t457 = db.session.get(Tool, 457)
    before = t457.next_inspection_date.isoformat() if t457 and t457.next_inspection_date else ""
    insp_cnt = len(t457.inspections) if t457 else -1
nd7 = upd_tool(457, {"level": "B"})
check("已有 %d 条检定记录 → 不覆盖（原值 %s）" % (insp_cnt, before), nd7, before)

nd8 = upd_tool(tid3, {"storage_date": "2026-12-31", "level": "A"})
check("改入库时间为 2026-12-31 + A 级 → 重算", nd8, "2027-06-30")

print("")
print("=== 汇总: %d / %d 通过 ===" % (sum(1 for x in results if x), len(results)))

# 清理前必须先释放 SQLAlchemy 引擎，否则它持有沙箱 tooling.db 的文件句柄，
# Windows 上 rmtree 会静默失败、留下临时目录（曾观察到 tooling_e2e_* 残留）。
with flask_app.app_context():
    db.session.remove()
    db.engine.dispose()

shutil.rmtree(T, ignore_errors=True)
sys.exit(0 if all(results) else 1)
