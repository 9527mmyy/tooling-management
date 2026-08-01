"""迁移 0003：为 borrow_records 表新增 return_operator（退库人）、return_remark（退库备注）列。

用途：退库（归还）动作要作为独立事件在时间线展示，需记录"谁、何时、备注"退库。
仅回填不影响现有数据；重复执行安全（先判断列是否存在）。
"""
from sqlalchemy import text


def upgrade(db):
    with db.engine.begin() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(borrow_records)")).fetchall()]
        if 'return_operator' not in cols:
            conn.execute(text("ALTER TABLE borrow_records ADD COLUMN return_operator VARCHAR(80)"))
        if 'return_remark' not in cols:
            conn.execute(text("ALTER TABLE borrow_records ADD COLUMN return_remark TEXT"))
