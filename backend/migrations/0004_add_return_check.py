"""迁移 0004：为 borrow_records 表新增 return_check（退库检验结果）列。

取值：合格 / 维修 / 报废。退库动作需在时间线记录检验结果，故补此列。
重复执行安全（先判断列是否存在）。
"""
from sqlalchemy import text


def upgrade(db):
    with db.engine.begin() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(borrow_records)")).fetchall()]
        if 'return_check' not in cols:
            conn.execute(text("ALTER TABLE borrow_records ADD COLUMN return_check VARCHAR(20)"))
