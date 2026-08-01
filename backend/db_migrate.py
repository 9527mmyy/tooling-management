#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
轻量数据库迁移运行器（无 Alembic 依赖）。

设计：
  - 数据库内建一张跟踪表 `schema_migrations`，记录已应用的迁移版本。
  - 所有变更脚本放在 `migrations/` 目录，按 `NNNN_描述.py` 命名（如 0003_add_keeper.py）。
  - 每个脚本需定义 `upgrade(db)` 函数，使用传入的 Flask-SQLAlchemy `db` 对象执行 DDL。
    建议写成幂等（先判断列/表是否存在再操作），重复执行不会报错。

用法：
  python db_migrate.py            # 执行所有【未应用】的迁移（已应用的自动跳过）
  python db_migrate.py --status   # 查看已应用 / 待应用清单
  python db_migrate.py --init     # 仅把当前所有脚本标记为“已应用”（不执行），用于老库引导

日常改库流程：
  1) 在 models.py 的模型上加字段；
  2) 在 migrations/ 新建 NNNN_xxx.py，写 upgrade(db)；
  3) 终端执行 `python db_migrate.py`。
"""
import os
import re
import sys
import argparse
import importlib.util

# 让脚本能直接 import 项目里的 app / db
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
TRACKING_TABLE = 'schema_migrations'


def ensure_tracking_table():
    with db.engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {TRACKING_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version VARCHAR(255) NOT NULL UNIQUE,
                name VARCHAR(255),
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))


def applied_versions():
    with db.engine.connect() as conn:
        rows = conn.execute(text(f"SELECT version FROM {TRACKING_TABLE}")).fetchall()
    return {r[0] for r in rows}


def discover_migrations():
    files = []
    if os.path.isdir(MIGRATIONS_DIR):
        for fn in os.listdir(MIGRATIONS_DIR):
            if fn.endswith('.py') and fn != '__init__.py' and re.match(r'^\d+_', fn):
                files.append(fn[:-3])
    return sorted(files)


def load_module(version):
    path = os.path.join(MIGRATIONS_DIR, version + '.py')
    spec = importlib.util.spec_from_file_location(version, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_status(versions, applied):
    print("迁移状态:")
    for v in versions:
        mark = 'x' if v in applied else ' '
        print(f"  [{mark}] {v}")
    pending = [v for v in versions if v not in applied]
    print(f"\n共 {len(versions)} 个 | 已应用 {len(applied & set(versions))} | 待应用 {len(pending)}")


def cmd_init(versions, applied):
    with db.engine.begin() as conn:
        for v in versions:
            if v not in applied:
                conn.execute(
                    text(f"INSERT OR IGNORE INTO {TRACKING_TABLE}(version, name) VALUES (:v, :n)"),
                    {'v': v, 'n': v},
                )
    print(f"已将 {len(versions)} 个迁移标记为已应用（老库引导，未执行 SQL）。")


def cmd_upgrade(versions, applied):
    pending = [v for v in versions if v not in applied]
    if not pending:
        print("✅ 数据库已是最新，没有待应用的迁移。")
        return
    for v in pending:
        print(f"→ 应用迁移: {v}")
        mod = load_module(v)
        if not hasattr(mod, 'upgrade'):
            print(f"  ⚠️ 跳过 {v}：缺少 upgrade(db) 函数")
            continue
        try:
            mod.upgrade(db)
        except Exception as e:
            print(f"  ❌ 迁移 {v} 执行失败: {e}")
            sys.exit(1)
        with db.engine.begin() as conn:
            conn.execute(
                text(f"INSERT OR IGNORE INTO {TRACKING_TABLE}(version, name) VALUES (:v, :n)"),
                {'v': v, 'n': v},
            )
        print(f"  ✓ {v} 完成")
    print("🎉 迁移完成。")


def main():
    parser = argparse.ArgumentParser(description='轻量数据库迁移运行器')
    parser.add_argument('--status', action='store_true', help='查看迁移状态')
    parser.add_argument('--init', action='store_true', help='将现有脚本标记为已应用（不执行，老库引导）')
    args = parser.parse_args()

    with app.app_context():
        ensure_tracking_table()
        versions = discover_migrations()
        applied = applied_versions()

        if args.status:
            cmd_status(versions, applied)
        elif args.init:
            cmd_init(versions, applied)
        else:
            cmd_upgrade(versions, applied)


if __name__ == '__main__':
    main()
